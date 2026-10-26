"""Edición final independiente: compilación documental y exportaciones reproducibles."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer
import yaml

from goes_science_kg.config import ruta

app = typer.Typer(help="Paquetes base de las mallas finales; estados de revisión explícitos", no_args_is_help=True)


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
