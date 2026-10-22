"""Casos de uso del producto V4, con preparación local antes de modelos remotos."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Annotated
from uuid import uuid4

import typer

from goes_science_kg.archivos import destino_generado, escribir_texto_generado
from goes_science_kg.config import cargar, ruta

app = typer.Typer(help="Producto curricular V4: fuentes, catálogo y entregables", no_args_is_help=True)


@app.command("escenario")
def escenario_cli(
    paquete: Path,
    escenario: Path,
    salida: Annotated[Path, typer.Option()] = Path("data/producto/escenarios/resultado.json"),
) -> None:
    """Evalúa tiempo/recursos declarados sin modificar currículo ni ejecutar modelos."""
    from goes_science_kg.producto.escenarios import EscenarioUnidad, evaluar_escenario
    from goes_science_kg.producto.unidades import PaqueteUnidad

    try:
        destino = _destino_escritura(salida, extension=".json")
        if destino in {paquete.resolve(), escenario.resolve()}:
            raise ValueError("El resultado debe ser distinto del paquete y escenario")
        datos = json.loads(paquete.read_bytes())
        unidad = PaqueteUnidad.model_validate(datos.get("paquete", datos))
        propuesta = EscenarioUnidad.model_validate_json(escenario.read_bytes())
        resultado = evaluar_escenario(unidad, propuesta)
        escribir_texto_generado(destino, json.dumps(resultado, ensure_ascii=False, indent=2) + "\n")
        typer.echo(json.dumps({"archivo": str(destino), "estado": resultado["estado"], "llamadas": 0}))
    except (ValueError, OSError) as error:
        raise typer.BadParameter(str(error)) from error


def _leer_catalogo(archivo: Path):
    from goes_science_kg.curriculo.catalogacion import CatalogoDisciplinas

    datos = json.loads(archivo.read_text(encoding="utf-8"))
    return CatalogoDisciplinas.model_validate(datos.get("catalogo", datos))


def _destino_escritura(salida: Path, *, extension: str | None = None) -> Path:
    try:
        return destino_generado(salida, extension=extension, raiz=ruta("."))
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error


def _guardar_vista(salida: Path, texto: str) -> None:
    try:
        escribir_texto_generado(salida, texto, extension=".html", raiz=ruta("."))
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error


@app.command("explorar")
def explorar(
    salida: Annotated[Path, typer.Option()] = Path("data/producto/explorador_v4.html"),
    catalogo: Annotated[Path | None, typer.Option()] = None,
    alertas: Annotated[Path, typer.Option()] = Path("docs/investigacion/alertas_v4.json"),
) -> None:
    """Genera el explorador sin conexión con las fuentes verificadas y sus alertas."""
    from goes_science_kg.curriculo import cargar_curriculo
    from goes_science_kg.producto.vista import vista

    curriculo = cargar_curriculo()
    clasificaciones = _leer_catalogo(catalogo) if catalogo else None
    observaciones = json.loads(ruta(alertas).read_text(encoding="utf-8"))
    _guardar_vista(salida, vista(curriculo, clasificaciones, observaciones))
    typer.echo(json.dumps({"archivo": str(salida.resolve()), "filas": len(curriculo.filas), "llamadas": 0}))


@app.command("construir")
def construir(
    catalogo: Annotated[Path, typer.Option()] = Path("data/producto/V4/catalogo_disciplinas.json"),
    destino: Annotated[Path, typer.Option()] = Path("data/producto/V4"),
    referencias: bool = typer.Option(True, "--referencias/--sin-referencias"),
    conocimiento: Annotated[
        Path | None, typer.Option(help="Archivo completo de juicios, con evidencia y cierres")
    ] = None,
    alineaciones: Annotated[Path | None, typer.Option(help="Cohorte completa de tres lectores por criterio")] = None,
) -> None:
    """Publica una generación V4 completa y verificable, sin llamadas remotas."""
    from goes_science_kg.curriculo import cargar_curriculo
    from goes_science_kg.ingesta.dimensiones import CatalogoDimensiones
    from goes_science_kg.ingesta.referencias import RepositorioReferencias
    from goes_science_kg.producto import construir_producto
    from goes_science_kg.producto.conocimiento_publicado import ArchivoConocimiento
    from goes_science_kg.producto.referencias import referencias_documentales

    archivo_conocimiento, modelos_conocimiento = None, None
    if conocimiento:
        from goes_science_kg.cli.juicios import ConfigJuicios, _vertex_config

        archivo_conocimiento = ArchivoConocimiento.model_validate_json(conocimiento.read_bytes())
        modelos_conocimiento = _vertex_config(ConfigJuicios.model_validate(cargar("juicios_conocimiento"))).modelos

    archivo_alineaciones, paginas_alineacion, modelos_alineacion = None, None, None
    if alineaciones:
        from goes_science_kg.cli.alineacion import _configuracion, _referentes, _vertex_config
        from goes_science_kg.producto.alineaciones import ArchivoAlineaciones

        archivo_alineaciones = ArchivoAlineaciones.model_validate_json(alineaciones.read_bytes())
        cfg_alineacion = _configuracion()
        _, paginas_alineacion = _referentes(cfg_alineacion)
        modelos_alineacion = _vertex_config(cfg_alineacion, None, None).modelos
    curriculo = cargar_curriculo()
    disciplinas = _leer_catalogo(catalogo)
    documentales = (
        referencias_documentales(
            CatalogoDimensiones.model_validate(cargar("dimensiones_evaluativas_2026")),
            RepositorioReferencias(ruta("data/referencias_2026")),
        )
        if referencias
        else None
    )
    resultado = construir_producto(
        curriculo,
        disciplinas,
        destino=destino,
        referencias=documentales,
        raiz_v4=ruta("insumos/v4"),
        conocimiento=archivo_conocimiento,
        modelos_conocimiento=modelos_conocimiento,
        alineaciones=archivo_alineaciones,
        paginas_alineacion=paginas_alineacion,
        modelos_alineacion=modelos_alineacion,
    )
    typer.echo(json.dumps(resultado, ensure_ascii=False, indent=2, default=str))


@app.command("validar")
def validar(destino: Annotated[Path, typer.Option()] = Path("data/producto/V4")) -> None:
    """Comprueba una generación sin cambiar el puntero ni llamar a modelos."""
    from goes_science_kg.producto import cargar_producto

    producto = cargar_producto(destino)
    typer.echo(producto.manifest.model_dump_json(indent=2))


@app.command("comparar")
def comparar(
    grafo_v3: Annotated[Path, typer.Option()] = Path("data/grafo"),
    salida_json: Annotated[Path, typer.Option()] = Path("docs/investigacion/comparacion_v3_v4.json"),
    salida_markdown: Annotated[Path, typer.Option()] = Path("docs/investigacion/comparacion_v3_v4.md"),
) -> None:
    """Compara registros y campos verificables V3–V4 sin trasladar decisiones."""
    from goes_science_kg.curriculo import cargar_curriculo
    from goes_science_kg.curriculo.comparacion import comparar_curriculos, guardar_comparacion
    from goes_science_kg.producto.referencias import cargar_referencias_historicas

    salida_json = _destino_escritura(salida_json, extension=".json")
    salida_markdown = _destino_escritura(salida_markdown, extension=".md")
    resultado = comparar_curriculos(cargar_referencias_historicas(ruta(grafo_v3)), cargar_curriculo())
    guardar_comparacion(resultado, salida_json=salida_json, salida_markdown=salida_markdown)
    typer.echo(json.dumps(resultado.resumen, ensure_ascii=False, indent=2))


@app.command("insumo")
def insumo() -> None:
    """Valida todas las fuentes y hojas V4; no activa ni escribe la malla histórica."""
    from goes_science_kg.curriculo.ingesta import cargar_curriculo

    curriculo = cargar_curriculo()
    typer.echo(
        json.dumps(
            {
                "version": curriculo.version,
                "estado": curriculo.estado,
                "huella": curriculo.huella,
                "fuentes": len(curriculo.fuentes),
                "hojas": dict(Counter(h.tratamiento for h in curriculo.hojas)),
                "filas": len(curriculo.filas),
                "agrupaciones": len(curriculo.agrupaciones),
                "avisos": curriculo.avisos,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


@app.command("conocimiento")
def conocimiento(
    grafo_v3: Annotated[Path, typer.Option()] = Path("data/grafo"),
    salida: Annotated[Path, typer.Option()] = Path("data/producto/V4/candidatos_conocimiento.json"),
    politica: Annotated[Path | None, typer.Option(help="Ediciones y presupuestos explícitos, en YAML")] = None,
) -> None:
    """Propone hipótesis con celdas originales; no acepta enlaces ni un DAG."""
    import yaml

    from goes_science_kg.curriculo import cargar_curriculo
    from goes_science_kg.producto.conocimiento import PoliticaConocimiento, generar_candidatos_conocimiento
    from goes_science_kg.producto.referencias import cargar_referencias_historicas

    destino = _destino_escritura(salida, extension=".json")
    reglas = PoliticaConocimiento.model_validate(yaml.safe_load(ruta(politica).read_text())) if politica else None
    resultado = generar_candidatos_conocimiento(
        cargar_curriculo(), cargar_referencias_historicas(ruta(grafo_v3)), politica=reglas
    )
    escribir_texto_generado(destino, resultado.model_dump_json() + "\n", extension=".json", raiz=ruta("."))
    typer.echo(
        json.dumps(
            {"resumen": resultado.resumen, "metricas": resultado.metricas, "salida": str(destino), "llamadas": 0},
            ensure_ascii=False,
            indent=2,
        )
    )


@app.command("catalogar")
def catalogar(
    ejecutar: bool = typer.Option(False, "--ejecutar"),
    piloto: bool = typer.Option(False, "--piloto"),
    salida: Annotated[Path, typer.Option()] = Path("data/producto/V4/catalogo_disciplinas.json"),
    max_usd: float = typer.Option(8.0, min=0.01, max=20),
    max_llamadas: int = typer.Option(54, min=1, max=200),
    ejecucion: str = typer.Option(None),
) -> None:
    """Propone disciplinas con dos lecturas ciegas; por defecto muestra el plan sin GCP."""
    from goes_science_kg.curriculo.catalogacion import ROLES, clasificar_disciplinas, plan_catalogacion
    from goes_science_kg.curriculo.ingesta import cargar_curriculo
    from goes_science_kg.motor.registro import Registro
    from goes_science_kg.motor.vertex import ConfiguracionVertex, Vertex

    destino = _destino_escritura(salida, extension=".json")
    curriculo = cargar_curriculo()
    plan = plan_catalogacion(curriculo)
    if piloto:
        plan["llamadas_previstas"] = min(2, plan["llamadas_previstas"])
    cfg = ConfiguracionVertex.model_validate(cargar("motor")["vertex"])
    modelos = dict(zip(ROLES, ("gemini-3.8-flash", "gemini-4-argon"), strict=True))
    if not ejecutar:
        typer.echo(
            json.dumps(
                plan
                | {
                    "proyecto": cfg.proyecto,
                    "region": cfg.region,
                    "modelos": modelos,
                    "max_reserva_usd": max_usd,
                    "max_intentos_acumulados": max_llamadas,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return
    cfg = cfg.model_copy(
        update={
            "modelos": modelos,
            "max_llamadas": max_llamadas,
            "max_usd": max_usd,
            "reintentos": 0,
            "niveles_razonamiento": {"catalogador_a": "LOW"},
        }
    )
    registro = Registro(ruta("data/operaciones/registro.sqlite"))
    id_ejecucion = ejecucion or uuid4().hex
    if not re.fullmatch(r"[a-zA-Z0-9_-]{1,100}", id_ejecucion):
        raise typer.BadParameter("El ID admite 1–100 caracteres alfanuméricos, guion o guion bajo")
    modelo = Vertex(cfg, registro, id_ejecucion)
    resultado = clasificar_disciplinas(curriculo, modelo, max_concurrencia=3, solo_piloto=piloto)
    destino = _destino_escritura(destino, extension=".json")
    destino.parent.mkdir(parents=True, exist_ok=True)
    datos = {"catalogo": resultado.model_dump(mode="json")} | {
        "ejecucion_id": id_ejecucion,
        "consumo": registro.resumen(id_ejecucion),
    }
    temporal = destino.with_name(f".{destino.name}.{uuid4().hex}.tmp")
    try:
        temporal.write_text(json.dumps(datos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporal.replace(destino)
    finally:
        temporal.unlink(missing_ok=True)
    typer.echo(
        json.dumps(
            {
                "estados": dict(Counter(f.estado for f in resultado.filas)),
                "consumo": {k: datos["consumo"][k] for k in ("llamadas", "reserva_usd")},
                "salida": str(destino),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    if not resultado.piloto_superado:
        raise typer.Exit(2)
