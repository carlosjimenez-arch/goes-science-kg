"""Edición final independiente: compilación documental y exportaciones reproducibles."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer
import yaml

from goes_science_kg.config import ruta

app = typer.Typer(help="Paquetes base de las mallas finales; estados de revisión explícitos", no_args_is_help=True)


@app.command("mejorar")
def mejorar(
    destino: Annotated[Path, typer.Option()],
    exportaciones: Annotated[Path, typer.Option()],
    origen: Annotated[Path, typer.Option()] = Path("data/materiales_produccion_v4"),
    referencias: Annotated[Path, typer.Option()] = Path("data/didactica_ciencias_20261026/referencias"),
):
    """Añade diseño de habilidades, apoyos, casos y auditoría, sin Vertex ni votos heredados."""
    from goes_science_kg.archivos import destino_generado
    from goes_science_kg.clases.presupuesto import comprobar_continuidad
    from goes_science_kg.curriculo.contratos import Curriculo
    from goes_science_kg.materiales.almacen import Biblioteca
    from goes_science_kg.materiales.almacen import construir as guardar
    from goes_science_kg.materiales.compilacion import serializar, sha
    from goes_science_kg.produccion.compilacion import exportar
    from goes_science_kg.produccion.didactica.compilacion import VERSION, enriquecer

    destino, exportaciones = ruta(destino), ruta(exportaciones)
    for p in (destino, exportaciones):
        destino_generado(p / "manifest.json")
        if p.exists() or p.is_symlink():
            raise typer.BadParameter("Los destinos deben ser directorios nuevos")
    if destino == exportaciones or destino in exportaciones.parents or exportaciones in destino.parents:
        raise typer.BadParameter("Los destinos deben ser independientes")
    ledger = ruta("data/operaciones/registro.sqlite")
    antes, consumo = sha(ledger.read_bytes()), comprobar_continuidad(ledger)
    biblioteca = Biblioteca(ruta(origen))
    biblioteca.validar()
    registros, archivos = biblioteca.exportar()
    curriculo = Curriculo.model_validate_json(archivos["curriculo.json"])
    historica = Biblioteca(ruta("data/materiales"))
    historica.validar()
    h, _ = historica.exportar()
    historicos = {r["id"]: r["documento"] for r in h if r["tipo"] == "paquete_objetivo"}
    reglas_raw = ruta("config/didactica_ciencias.yaml").read_bytes()
    casos_raw = ruta("config/casos_didacticos_ciencias.yaml").read_bytes()
    diseno_sha = sha(serializar({"reglas": sha(reglas_raw), "casos": sha(casos_raw)}))
    reglas = yaml.safe_load(reglas_raw)
    propuestas, auditoria, indice, grafo = enriquecer(
        registros,
        curriculo,
        reglas,
        sha_reglas=diseno_sha,
        biblioteca_base=biblioteca.manifest["id"],
        historicos=historicos,
        casos=yaml.safe_load(casos_raw),
    )
    originales = {p: b for p, b in archivos.items() if not p.startswith("paquetes/") and p != "informe.json"}
    originales["edicion_base/informe.json"] = archivos["informe.json"]
    originales["didactica/reglas.yaml"] = reglas_raw
    originales["didactica/casos.yaml"] = casos_raw
    originales["didactica/auditoria.json"] = serializar(auditoria)
    originales["didactica/indice.json"] = serializar(indice)
    originales["didactica/grafo.json"] = serializar(grafo)
    originales["informe.json"] = serializar(auditoria)
    fuentes = json.loads((ruta(referencias) / "manifest.json").read_bytes())
    originales["didactica/referencias/manifest.json"] = serializar(fuentes)
    for fuente in fuentes["fuentes"]:
        if fuente["estado"] != "descargado":
            continue
        nombre = fuente["archivo"]
        if Path(nombre).name != nombre:
            raise ValueError("La fuente debe identificar un archivo simple")
        archivo = ruta(referencias) / nombre
        if archivo.is_symlink():
            raise ValueError("La referencia debe ser un archivo propio")
        raw = archivo.read_bytes()
        if sha(raw) != fuente["sha256"] or len(raw) != fuente["bytes"]:
            raise ValueError("La referencia no conserva su huella")
        originales["didactica/referencias/" + nombre] = raw
    fuentes_casos = {s["id"]: {k: v for k, v in s.items() if k not in {"archivo"}} for s in fuentes["fuentes"]}
    for r in propuestas:
        if r["tipo"] == "paquete_objetivo" and (caso := r["documento"]["didactica"]["caso_resuelto"]):
            caso["fuentes"] = {id_: fuentes_casos[id_] for id_ in caso["referencias"]}
    comunes = {"didactica/referencias.json": serializar(fuentes_casos), "didactica/reglas.yaml": reglas_raw}
    comunes["didactica/casos.yaml"] = casos_raw
    zips = exportar(
        propuestas,
        originales,
        auditoria,
        exportaciones,
        version=VERSION,
        estado_revision="propuesta_didactica_pendiente_revision",
        archivos_comunes=comunes,
    )
    for p in [*(exportaciones / z["archivo"] for z in zips), exportaciones / "indice.json"]:
        originales["paquetes/" + p.name] = p.read_bytes()
    manifest = guardar(
        propuestas,
        originales,
        destino,
        procedencia={
            "snapshot_id": curriculo.huella,
            "edicion": "produccion-final-20261026",
            "version_diseno": VERSION,
            "biblioteca_base": biblioteca.manifest["id"],
            "metodo": "diseno_instruccional_con_curacion_explicita_y_compilacion_sin_modelos",
            "estado_revision": "propuesta_didactica_pendiente_revision",
            "consumo_acumulado": consumo,
            "ledger_sha256": antes,
        },
    )
    if sha(ledger.read_bytes()) != antes:
        raise ValueError("El ledger cambió durante el enriquecimiento")
    typer.echo(
        json.dumps(
            {
                "biblioteca_id": manifest["id"],
                "materiales": manifest["materiales"],
                "auditoria": auditoria,
                "llamadas_vertex": 0,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


@app.command("preparar")
def preparar(destino: Annotated[Path, typer.Option()]):
    """Contexto completo y reserva de las 108 unidades; no ejecuta Vertex ni aprueba el catálogo."""
    from goes_science_kg.clases.presupuesto import comprobar_continuidad, configuracion
    from goes_science_kg.config import cargar
    from goes_science_kg.curriculo.ingesta import cargar_curriculo
    from goes_science_kg.materiales.compilacion import sha
    from goes_science_kg.motor.vertex import ConfiguracionVertex
    from goes_science_kg.produccion.preparacion import preparar_preflight
    from goes_science_kg.producto.campana_mejoras import escribir_nuevo_o_igual

    ledger = ruta("data/operaciones/registro.sqlite")
    antes = sha(ledger.read_bytes())
    limites = configuracion()
    consumo = comprobar_continuidad(ledger, limites)
    cfg = ConfiguracionVertex.model_validate(cargar("mejoras_curriculares")["vertex"]).model_copy(
        update={
            "max_llamadas": limites["max_llamadas_acumuladas"],
            "max_usd": limites["max_reserva_usd_acumulada"],
        }
    )
    alertas = json.loads(ruta("docs/investigacion/alertas_v4.json").read_bytes())["alertas"]
    alertas += yaml.safe_load(ruta("config/alertas_derivadas_v4.yaml").read_text())["alertas"]
    preparaciones, plan = preparar_preflight(
        cargar_curriculo(ruta("config/mallas_v4_produccion.yaml")), alertas, ruta("."), cfg, consumo
    )
    for p in preparaciones:
        escribir_nuevo_o_igual(ruta(destino) / (p.id + ".json"), p.model_dump(mode="json"))
    escribir_nuevo_o_igual(ruta(destino) / "preflight.json", plan)
    if sha(ledger.read_bytes()) != antes:
        raise ValueError("El ledger cambió durante la preparación")
    typer.echo(
        json.dumps(
            {k: v for k, v in plan.items() if k not in {"unidades", "catalogo_provisional"}},
            ensure_ascii=False,
            indent=2,
        )
    )


@app.command("construir")
def construir(
    destino: Annotated[Path, typer.Option()] = Path("data/materiales_produccion_v4"),
    exportaciones: Annotated[Path, typer.Option()] = Path("data/produccion_v4_20261026/paquetes"),
):
    """Lee ambas ediciones, preserva los originales y genera todos los paquetes; cero Vertex."""
    from goes_science_kg.archivos import destino_generado
    from goes_science_kg.clases.presupuesto import comprobar_continuidad
    from goes_science_kg.curriculo.ingesta import cargar_curriculo
    from goes_science_kg.materiales.almacen import Biblioteca
    from goes_science_kg.materiales.almacen import construir as guardar
    from goes_science_kg.materiales.compilacion import serializar, sha
    from goes_science_kg.observabilidad import configurar_logging
    from goes_science_kg.produccion.compilacion import compilar, exportar

    configurar_logging()
    base = ruta(".")
    destino, exportaciones = ruta(destino), ruta(exportaciones)
    for carpeta in (destino, exportaciones):
        destino_generado(carpeta / "manifest.json")
        if carpeta.exists() or carpeta.is_symlink():
            raise typer.BadParameter("La biblioteca y las exportaciones requieren directorios nuevos")
    if destino == exportaciones or destino in exportaciones.parents or exportaciones in destino.parents:
        raise typer.BadParameter("La biblioteca y las exportaciones deben ser directorios independientes")
    ledger = ruta("data/operaciones/registro.sqlite")
    consumo = comprobar_continuidad(ledger)
    ledger_sha = sha(ledger.read_bytes())
    final = cargar_curriculo(ruta("config/mallas_v4_produccion.yaml"))
    anterior = cargar_curriculo()
    historica = Biblioteca(ruta("data/materiales"))
    historica.validar()
    alertas = json.loads(ruta("docs/investigacion/alertas_v4.json").read_bytes())["alertas"]
    alertas += yaml.safe_load(ruta("config/alertas_derivadas_v4.yaml").read_text())["alertas"]
    registros, informe = compilar(final, anterior, alertas, biblioteca_anterior=historica.manifest["id"])
    originales = {}
    for fuente in final.fuentes:
        raw = (base / fuente.archivo_local).read_bytes()
        if (len(raw), sha(raw)) != (fuente.bytes, fuente.sha256):
            raise ValueError("La fuente cambió después de la ingesta")
        originales[fuente.archivo_local] = raw
    originales["insumos/procedencia_v4_produccion_20261026.json"] = ruta(
        "insumos/procedencia_v4_produccion_20261026.json"
    ).read_bytes()
    originales["config/mallas_v4_produccion.yaml"] = ruta("config/mallas_v4_produccion.yaml").read_bytes()
    originales["curriculo.json"] = final.model_dump_json().encode()
    originales["informe.json"] = serializar(informe)
    archivos = exportar(registros, originales, informe, exportaciones)
    # Los ZIP también se pueden descargar individualmente desde la API por su SHA.
    for archivo in archivos:
        originales["paquetes/" + archivo["archivo"]] = (exportaciones / archivo["archivo"]).read_bytes()
    originales["paquetes/indice.json"] = (exportaciones / "indice.json").read_bytes()
    manifest = guardar(
        registros,
        originales,
        destino,
        procedencia={
            "snapshot_id": final.huella,
            "edicion": "produccion-final-20261026",
            "huella_curriculo_anterior": anterior.huella,
            "biblioteca_anterior": historica.manifest["id"],
            "metodo": "compilacion_documental_sin_generacion_ni_herencia_de_votos",
            "ledger_sha256": ledger_sha,
            "consumo_acumulado": consumo,
            "estado_revision": "pendiente_revision_nueva_edicion",
        },
    )
    if sha(ledger.read_bytes()) != ledger_sha:
        raise ValueError("El ledger cambió durante la compilación")
    typer.echo(
        json.dumps(
            {
                "biblioteca_id": manifest["id"],
                "paquetes": len(registros),
                "exportaciones": len(archivos),
                "comparacion": {k: v for k, v in informe.items() if k != "filas"},
                "llamadas_vertex": 0,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


@app.command("publicar")
def publicar(
    recibo: Annotated[Path, typer.Option()],
    directorio: Annotated[Path, typer.Option()] = Path("data/materiales_produccion_v4"),
    exportaciones: Annotated[Path, typer.Option()] = Path("data/produccion_v4_20261026/paquetes"),
):
    """Publica los ZIP en el bucket aprobado; cada objeto nuevo se relee por generación."""
    from goes_science_kg.cli.materiales import _almacen
    from goes_science_kg.materiales.almacen import Biblioteca
    from goes_science_kg.produccion.publicacion import publicar as subir

    r = subir(ruta(exportaciones), Biblioteca(ruta(directorio)), _almacen(), ruta(recibo))
    typer.echo(json.dumps({"biblioteca_id": r["biblioteca_id"], "objetos": len(r["objetos"])}))


@app.command("descargar")
def descargar(
    destino: Annotated[Path, typer.Option()],
    recibo: Annotated[Path, typer.Option()] = Path("config/paquetes_produccion_ciencias.lock.json"),
):
    """Descarga los ZIP finales en un directorio nuevo y comprueba todas sus generaciones."""
    from goes_science_kg.cli.materiales import _almacen
    from goes_science_kg.produccion.publicacion import descargar as recuperar

    resultado = recuperar(json.loads(ruta(recibo).read_bytes()), ruta(destino), _almacen())
    typer.echo(json.dumps({"estado": "integridad_verificada", "exportaciones": len(resultado["paquetes"])}))


@app.command("revision-preparar")
def revision_preparar(destino: Annotated[Path, typer.Option()]):
    """Congela la edición derivada, fuentes y presupuesto; no consume Vertex."""
    from goes_science_kg.archivos import destino_generado
    from goes_science_kg.produccion.revision_docente.preparacion import preparar

    destino = ruta(destino)
    destino_generado(destino / "preflight.json")
    if destino.exists():
        raise typer.BadParameter("Seleccione una captura nueva; no sobrescriba contextos ni votos")
    typer.echo(json.dumps(preparar(ruta("."), destino), ensure_ascii=False, indent=2))


@app.command("revision-ejecutar")
def revision_ejecutar(
    campana: Annotated[Path, typer.Option()],
    ronda: Annotated[int, typer.Option(min=1, max=2)] = 1,
    concurrencia: Annotated[int, typer.Option(min=1, max=4)] = 2,
):
    """Cuatro lectores con evidencia seleccionada; reanuda exactamente los checkpoints existentes."""
    from goes_science_kg.observabilidad import configurar_logging
    from goes_science_kg.produccion.revision_docente.ejecucion import ejecutar

    configurar_logging()
    destino = ruta(campana)
    solicitudes = json.loads((destino / f"ronda_{ronda}.json").read_bytes())
    errores = ejecutar(
        solicitudes, destino, ruta("data/operaciones/registro.sqlite"), ronda=ronda, concurrencia=concurrencia
    )
    typer.echo(json.dumps({"errores": errores}, ensure_ascii=False, indent=2))
    if errores:
        raise typer.Exit(1)


@app.command("revision-reparar")
def revision_reparar(campana: Annotated[Path, typer.Option()]):
    """Propone una única reparación derivada y exige cuatro lecturas nuevas sobre el resultado."""
    from goes_science_kg.materiales.compilacion import serializar, sha
    from goes_science_kg.produccion.revision_docente.correcciones import reparar
    from goes_science_kg.produccion.revision_docente.fuentes import complementarias
    from goes_science_kg.produccion.revision_docente.preparacion import biblioteca_origen

    destino = ruta(campana)
    biblioteca = biblioteca_origen(ruta("."))
    _, archivos = biblioteca.exportar()
    reglas = yaml.safe_load(archivos["didactica/reglas.yaml"])
    editorial = yaml.safe_load(ruta("config/enmiendas_revision_docente.yaml").read_bytes())
    registros = json.loads((destino / "candidato_1.json").read_bytes())
    por_id = {r["id"]: r["documento"]["edicion_docente"] for r in registros}
    if editorial["huella_curriculo"] != biblioteca.manifest["procedencia"]["snapshot_id"]:
        raise ValueError("Las enmiendas editoriales pertenecen a otra malla")
    if any(sha(serializar(por_id[e["item_id"]])) != e["edicion_base_sha256"] for e in editorial["enmiendas"]):
        raise ValueError("La enmienda editorial no corresponde al contenido inicial exacto")
    resoluciones = {e["item_id"] + "#" + e["ruta"]: e["texto"] for e in editorial["enmiendas"]}
    if len(resoluciones) != len(editorial["enmiendas"]):
        raise ValueError("Hay enmiendas repetidas para el mismo campo")
    _, solicitudes, cambios, conflictos = reparar(
        registros,
        json.loads((destino / "ronda_1.json").read_bytes()),
        destino,
        reglas,
        resoluciones=resoluciones,
        fuentes_adicionales=complementarias(ruta(".")),
    )
    from goes_science_kg.produccion.revision_docente.ejecucion import guardar

    guardar(destino / "enmiendas_editoriales.json", editorial)
    typer.echo(
        json.dumps(
            {"lotes_relectura": len(solicitudes), "cambios": len(cambios), "conflictos_conservados": len(conflictos)},
            ensure_ascii=False,
            indent=2,
        )
    )


@app.command("revision-compilar")
def revision_compilar(
    campana: Annotated[Path, typer.Option()],
    destino: Annotated[Path, typer.Option()],
    exportaciones: Annotated[Path, typer.Option()],
):
    """Construye SQLite y ZIP nuevos con votos exactos y pendientes visibles; sin gasto de modelos."""
    from goes_science_kg.archivos import destino_generado
    from goes_science_kg.produccion.revision_docente.entrega import guardar_entrega

    campana, destino, exportaciones = ruta(campana), ruta(destino), ruta(exportaciones)
    for p in (destino, exportaciones):
        destino_generado(p / "manifest.json")
    if destino == exportaciones or destino in exportaciones.parents or exportaciones in destino.parents:
        raise typer.BadParameter("Los destinos deben ser independientes")
    candidato = campana / ("candidato_2.json" if (campana / "candidato_2.json").exists() else "candidato_1.json")
    m, r = guardar_entrega(ruta("."), campana, json.loads(candidato.read_bytes()), destino, exportaciones)
    typer.echo(json.dumps({"biblioteca_id": m["id"], "por_estado": r["por_estado"]}, ensure_ascii=False, indent=2))


@app.command("revision-recuperar-parcial")
def revision_recuperar_parcial(
    campana: Annotated[Path, typer.Option()],
    lote: Annotated[int, typer.Option(min=0, max=99)],
    rol: Annotated[str, typer.Option()],
    ronda: Annotated[int, typer.Option(min=1, max=2)] = 1,
):
    """Extrae sólo decisiones JSON completas de una respuesta truncada ya recibida; cero Vertex."""
    from goes_science_kg.produccion.revision_docente.contratos import ROLES
    from goes_science_kg.produccion.revision_docente.recuperacion import recuperar

    if rol not in ROLES:
        raise typer.BadParameter("El rol debe pertenecer al protocolo de cuatro lectores")
    r = recuperar(ruta(campana), ruta("data/operaciones/registro.sqlite"), ronda=ronda, lote=lote, rol=rol)
    typer.echo(json.dumps(r, ensure_ascii=False, indent=2))
