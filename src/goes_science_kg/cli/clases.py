"""Guiones completos: operaciones locales separadas de generación y publicación."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from goes_science_kg.config import ruta

app = typer.Typer(help="Guiones de clase V4 con cuatro revisiones y descarga verificable", no_args_is_help=True)


@app.command("edicion")
def edicion(plantilla: Path, parche: Path, destino: Annotated[Path, typer.Option()]):
    """Prepara un cambio de contenido trazable; no llama a modelos ni modifica dictámenes."""
    from goes_science_kg.archivos import destino_generado
    from goes_science_kg.clases.editorial import preparar
    from goes_science_kg.clases.preparacion import leer_preparacion
    from goes_science_kg.materiales.compilacion import serializar

    p = preparar(ruta("."), leer_preparacion(plantilla), parche.resolve())
    salida = destino_generado(destino, extension=".json")
    salida.parent.mkdir(parents=True, exist_ok=True)
    with salida.open("xb") as f:
        f.write(serializar(p))
    typer.echo(json.dumps({"preparacion_id": p["id"], "destino": str(salida), "requiere_cuatro_lecturas_nuevas": True}))


def _preparar_ejecucion(preparaciones, paralelas):
    from goes_science_kg.clases.corpora import cargar_corpus
    from goes_science_kg.clases.operacion import cargar_lotes
    from goes_science_kg.clases.proveedor import ProveedorClases
    from goes_science_kg.motor.registro import Registro

    base = ruta(".")
    ledger = base / "data/operaciones/registro.sqlite"
    if not ledger.is_file():
        raise typer.BadParameter("Falta el ledger acumulado; restaure el corpus completo antes de generar")
    from goes_science_kg.clases.presupuesto import configuracion

    cfg = configuracion()
    proveedor = ProveedorClases(
        Registro(ledger),
        concurrencia=paralelas,
        max_llamadas=cfg["max_llamadas_acumuladas"],
        max_usd=cfg["max_reserva_usd_acumulada"],
    )
    lotes = cargar_lotes(preparaciones)
    huellas = {p["corpus_sha256"] for p in lotes}
    if len(huellas) != 1:
        raise typer.BadParameter("La ejecución requiere preparaciones del mismo corpus científico")
    return lotes, proveedor, cargar_corpus(base, next(iter(huellas)))


@app.command("preflight")
def preflight(preparaciones: Path):
    """Calcula la cota de dos rondas y verifica el ledger anterior; cero invocaciones."""
    from goes_science_kg.clases.operacion import estimar

    lotes, proveedor, _ = _preparar_ejecucion(preparaciones, 1)
    typer.echo(json.dumps(estimar(lotes, proveedor), ensure_ascii=False, indent=2))


@app.command("ejecutar")
def ejecutar(
    preparaciones: Path,
    destino: Annotated[Path, typer.Option()],
    protocolo: Annotated[str, typer.Option()],
    concurrencia: Annotated[int, typer.Option(min=1, max=16)] = 3,
    paralelas: Annotated[int, typer.Option(min=1, max=24)] = 6,
    plan: Annotated[Path | None, typer.Option(help="protocolo.json del bloque exacto que se desea reanudar")] = None,
    confirmar: Annotated[bool, typer.Option(help="Ejecuta llamadas autorizadas dentro del ledger acumulado")] = False,
):
    """Reanuda los terminales sin gasto; cada cambio de entorno necesita otro protocolo explícito."""
    from collections import Counter

    from goes_science_kg.clases.operacion import ejecutar as generar
    from goes_science_kg.clases.operacion import estimar

    lotes, proveedor, corpus = _preparar_ejecucion(preparaciones, paralelas)
    if plan:
        ref = json.loads(plan.read_bytes())
        if ref["protocolo"] != protocolo:
            raise typer.BadParameter("El protocolo indicado no coincide con el plan")
        por_id = {p["id"]: p for p in lotes}
        ids = ref["preparaciones"]
        if len(set(ids)) != len(ids) or set(ids) - por_id.keys():
            raise typer.BadParameter("El plan contiene preparaciones repetidas o ausentes")
        lotes = [por_id[id_] for id_ in ids]
    if not confirmar:
        typer.echo(json.dumps(estimar(lotes, proveedor), ensure_ascii=False, indent=2))
        return
    resultados = generar(lotes, proveedor, corpus, destino, protocolo=protocolo, concurrencia=concurrencia)
    typer.echo(json.dumps(dict(Counter(f["estado"] for r in resultados for f in r["filas"].values()))))


@app.command("campana")
def campana(
    preparaciones: Path,
    plan: Annotated[Path, typer.Option(help="Plan congelado que fija el orden exacto de lotes")],
    destino: Annotated[Path, typer.Option()],
    control: Annotated[Path, typer.Option(help="Concurrencia ajustable entre bloques, sin cambiar los guiones")],
    protocolo: Annotated[str, typer.Option()] = "clases-p11",
    confirmar: Annotated[bool, typer.Option()] = False,
):
    import zipfile

    from goes_science_kg.clases.campana import ejecutar_campana, leer_control, planificar
    from goes_science_kg.materiales.compilacion import sha

    if protocolo not in {f"clases-p{n}" for n in range(5, 12)}:
        raise typer.BadParameter("La campaña requiere un protocolo P5–P11 congelado")
    numero = int(protocolo.removeprefix("clases-p"))
    cfg = leer_control(control)
    lotes, proveedor, corpus = _preparar_ejecucion(preparaciones, cfg["vertex"])
    ref = json.loads(plan.read_bytes())
    por_id = {p["id"]: p for p in lotes}
    ids = ref["lotes"]
    if len(set(ids)) != len(ids) or set(ids) - por_id.keys():
        raise typer.BadParameter("El plan contiene lotes repetidos o ausentes")
    codigo = ruta("data/clases_v4/protocolos/codigo_" + protocolo.replace("-", "_") + ".zip")
    if sha(codigo.read_bytes()) != ref["codigo_sha256"]:
        raise typer.BadParameter("El código congelado no corresponde al plan")
    with zipfile.ZipFile(codigo) as z:
        for nombre in (
            "contratos.py",
            "fuentes.py",
            "motor.py",
            "prompts.py",
            "preparacion.py",
            "validacion.py",
            "proveedor.py",
            "operacion.py",
            *(("edicion.py",) if numero >= 8 else ()),
            *(("editorial.py",) if numero >= 9 else ()),
            *(("contexto.py",) if numero >= 10 else ()),
        ):
            local = Path(__file__).parent.parent / "clases" / nombre
            if local.read_bytes() != z.read("src/goes_science_kg/clases/" + nombre):
                raise typer.BadParameter("El código instalado difiere del protocolo; no se inicia ninguna llamada")
    seleccion = [por_id[id_] for id_ in ids]
    if not confirmar:
        typer.echo(
            json.dumps(planificar(seleccion, proveedor, corpus, destino, tamano=ref["bloque"], protocolo=protocolo))
        )
        return
    resumen = ejecutar_campana(
        seleccion, proveedor, corpus, destino, control, tamano=ref["bloque"], protocolo=protocolo
    )
    typer.echo(json.dumps({"bloques": len(resumen), "ultimo": resumen[-1] if resumen else None}))


@app.command("compilar")
def compilar(
    seleccion: Path,
    biblioteca: Annotated[Path, typer.Option(help="Directorio nuevo de la biblioteca ampliada")],
    archivo: Annotated[Path, typer.Option(help="ZIP nuevo de guiones completos")],
    biblioteca_origen: Annotated[
        Path | None, typer.Option(help="Biblioteca de preparaciones fijada en los insumos")
    ] = None,
    pendientes: Annotated[
        Path | None, typer.Option(help="JSON de objetivos declarados sin guion liberado, con motivo y expediente")
    ] = None,
    revision_directa: Annotated[
        list[str] | None, typer.Option(help="Expedientes de revisión directa (rutas del repositorio)")
    ] = None,
):
    """Reconstruye los respaldos, conserva los materiales anteriores y exige cobertura exacta."""
    from goes_science_kg.clases.auditoria import cierre_presupuesto
    from goes_science_kg.clases.compilacion import compilar as reconstruir
    from goes_science_kg.clases.corpora import cargar_corpus
    from goes_science_kg.clases.paquete import construir as empaquetar
    from goes_science_kg.materiales.almacen import Biblioteca, construir
    from goes_science_kg.motor.registro import Registro

    base = ruta(".")
    # Las preparaciones de los guiones están fijadas a la biblioteca base, no a la ampliada que se publica.
    anterior = Biblioteca(biblioteca_origen or base / "data/materiales_preparaciones")
    corpus = cargar_corpus(base, todos=True)
    sel = json.loads(seleccion.read_bytes())
    registro = Registro(base / "data/operaciones/registro.sqlite")
    consumo = cierre_presupuesto(registro)
    declarados = json.loads(pendientes.read_bytes()) if pendientes else {}
    from goes_science_kg.clases.compilacion import cargar_revisiones_directas

    revisiones = cargar_revisiones_directas(base, revision_directa or [])
    nuevos, fuentes = reconstruir(
        base, anterior, corpus, sel, registro=registro, pendientes=declarados, revisiones_directas=revisiones
    )
    sin_guion = sorted(
        (
            p
            for u in nuevos
            if u["tipo"] == "guion_unidad"
            for p in u["documento"].get("objetivos_sin_guion_liberado", [])
        ),
        key=lambda p: p["fila_id"],
    )
    registros, originales = anterior.exportar()
    if set(originales) & set(fuentes):
        raise ValueError("Los expedientes nuevos no pueden sustituir originales existentes")
    procedencia = {
        **anterior.manifest["procedencia"],
        "biblioteca_anterior": anterior.manifest["id"],
        "corpus_cientifico_sha256": corpus.huella,
        "metodo_guiones": "reconstruccion_de_cuatro_dictamenes_por_huella_del_guion",
        "consumo_cierre_guiones": consumo,
        "objetivos_sin_guion_liberado": sin_guion,
    }
    entrega = empaquetar(nuevos, fuentes, archivo, procedencia=procedencia)
    m = construir(registros + nuevos, originales | fuentes, biblioteca, procedencia=procedencia)
    typer.echo(json.dumps({"biblioteca_id": m["id"], "entrega_id": entrega["id"], "por_tipo": entrega["por_tipo"]}))


@app.command("validar")
def validar(archivo: Path):
    """Comprueba todo el ZIP sin invocar modelos ni escribir en GCS."""
    from goes_science_kg.clases.paquete import validar as comprobar

    m = comprobar(archivo)
    typer.echo(json.dumps({"estado": "verificado", "id": m["id"], "materiales": m["materiales"]}))


@app.command("extraer")
def extraer(archivo: Path, destino: Annotated[Path, typer.Option()]):
    from goes_science_kg.clases.paquete import extraer as restaurar

    m = restaurar(archivo, destino)
    typer.echo(json.dumps({"estado": "verificado", "id": m["id"], "materiales": m["materiales"]}))


@app.command("publicar")
def publicar(archivo: Path, recibo: Annotated[Path, typer.Option()]):
    """Crea un objeto nuevo en el bucket de Ciencias aprobado y relee su generación exacta."""
    from goes_science_kg.clases.publicacion import publicar as subir
    from goes_science_kg.cli.materiales import _almacen

    r = subir(archivo, _almacen(), recibo)
    typer.echo(json.dumps({"entrega_id": r["entrega_id"], "objeto": r["objeto"]["uri"]}))


@app.command("descargar")
def descargar(
    destino: Annotated[Path, typer.Option()],
    recibo: Annotated[Path | None, typer.Option()] = None,
):
    """Recupera JSON y Markdown, fuentes y auditorías; no requiere Vertex ni el corpus completo."""
    from goes_science_kg.clases.publicacion import descargar as restaurar
    from goes_science_kg.cli.materiales import _almacen

    ref = json.loads((recibo or ruta("config/clases_ciencias.lock.json")).read_bytes())
    m = restaurar(ref, destino, _almacen())
    typer.echo(json.dumps({"estado": "verificado", "entrega_id": m["id"], "por_tipo": m["por_tipo"]}))


@app.command("complementaria")
def complementaria() -> None:
    """Compila la capa complementaria revisada y fija su recibo; no invoca modelos."""
    from goes_science_kg.clases.complementaria_publicacion import RECIBO, publicar

    recibo = publicar(ruta("."))
    destino = ruta(RECIBO.as_posix())
    temporal = destino.with_suffix(".tmp")
    temporal.write_text(json.dumps(recibo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporal.replace(destino)
    typer.echo(json.dumps(recibo, ensure_ascii=False))


@app.command("complementaria-estado")
def complementaria_estado() -> None:
    """Report pending, blocked, and approved units from verified on-disk reviews without model calls."""
    from goes_science_kg.clases.complementaria_revision import estado_revisiones

    typer.echo(json.dumps(estado_revisiones(ruta(".")), ensure_ascii=False, indent=2))


@app.command("complementaria-informe")
def complementaria_informe() -> None:
    """Consolidate potential original-script defects from every preserved independent review round."""
    from goes_science_kg.clases.complementaria_revision import CARPETA, informe_observaciones

    informe = informe_observaciones(ruta("."))
    destino = ruta((CARPETA / "informes/observaciones_guiones.json").as_posix())
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(informe, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lineas = ["# Observaciones sobre guiones publicados", "", informe["limite"], "", informe["deduplicacion"], ""]
    for i, obs in enumerate(informe["observaciones"], 1):
        lineas += [f"## {i}. Unidad {obs['unidad']}", "", obs["observacion"], "", "Estado: pendiente de contraste.", ""]
        lineas += [f"- {e['revision']} · SHA-256 `{e['sha256']}`" for e in obs["evidencias"]]
        lineas.append("")
    destino.with_suffix(".md").write_text("\n".join(lineas), encoding="utf-8")
    typer.echo(json.dumps({"observaciones": len(informe["observaciones"]), "ruta": str(destino)}))
