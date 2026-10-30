"""Prepare V4 product use cases before any explicit remote-model execution."""

from __future__ import annotations

import hashlib
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
    """Evaluate declared classroom constraints without changing curricula or invoking models."""
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
    """Generate the offline explorer from verified sources and scientific alerts."""
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
    """Publish a complete verified V4 generation without remote calls."""
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
    """Validate a generation without changing its selection pointer."""
    from goes_science_kg.producto import cargar_producto

    producto = cargar_producto(destino)
    typer.echo(producto.manifest.model_dump_json(indent=2))


@app.command("comparar")
def comparar(
    grafo_v3: Annotated[Path, typer.Option()] = Path("data/grafo"),
    salida_json: Annotated[Path, typer.Option()] = Path("docs/investigacion/comparacion_v3_v4.json"),
    salida_markdown: Annotated[Path, typer.Option()] = Path("docs/investigacion/comparacion_v3_v4.md"),
) -> None:
    """Compare verifiable V3 and V4 records without transferring decisions."""
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
    """Validate all V4 sources and sheets without modifying the historical curriculum."""
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
    """Propose relationship hypotheses from original cells without admitting links or a DAG."""
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
    """Plan or explicitly execute two blind subject-classification readings."""
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


@app.command("preparar-conceptos")
def preparar_conceptos(
    destino: Annotated[Path, typer.Option()] = Path("data/producto/V4"),
    por_lote: Annotated[int, typer.Option(min=4, max=60)] = 24,
) -> None:
    """Prepare blind concept-tagging batches for V4 rows and refined proposals; no model is invoked."""
    from goes_science_kg import conceptos
    from goes_science_kg.producto import cargar_producto
    from goes_science_kg.producto import conceptos_v4 as c4

    producto = cargar_producto(ruta(str(destino)))
    items = c4.items_v4(producto)
    lotes = c4.armar_lotes(
        items,
        conceptos.vocabulario(),
        conceptos.practicas(),
        snapshot_id=producto.manifest.snapshot_id,
        por_lote=por_lote,
    )
    escritos = c4.escribir_lotes(lotes, ruta(c4.DIR_LOTES))
    origenes = Counter(i["origen"] for i in items)
    typer.echo(json.dumps({"lotes": len(escritos), "items": dict(origenes)}, ensure_ascii=False))


@app.command("unir-conceptos")
def unir_conceptos(destino: Annotated[Path, typer.Option()] = Path("data/producto/V4")) -> None:
    """Validate every V4 tagging output and write the joined labels to their derived destination."""
    from goes_science_kg import conceptos
    from goes_science_kg.producto import cargar_producto
    from goes_science_kg.producto import conceptos_v4 as c4

    producto = cargar_producto(ruta(str(destino)))
    datos = c4.unir(ruta(c4.DIR_LOTES), producto, conceptos.vocabulario(), conceptos.practicas())
    salida = ruta(c4.ARCHIVO_ETIQUETADO)
    escribir_texto_generado(salida, json.dumps(datos, ensure_ascii=False, indent=1) + "\n")
    confianza = Counter(e["confianza"] for e in datos["etiquetas"])
    typer.echo(json.dumps({"etiquetas": len(datos["etiquetas"]), "confianza": dict(confianza)}, ensure_ascii=False))


@app.command("progresion")
def progresion(destino: Annotated[Path, typer.Option()] = Path("data/producto/V4")) -> None:
    """Derive grade 2–11 concept and practice trajectories from the joined V4 labels; no model is invoked."""
    from goes_science_kg import conceptos
    from goes_science_kg.producto import cargar_producto
    from goes_science_kg.producto import conceptos_v4 as c4
    from goes_science_kg.producto import progresion_v4 as p4

    producto = cargar_producto(ruta(str(destino)))
    archivo = ruta(c4.ARCHIVO_ETIQUETADO)
    etiquetado = json.loads(archivo.read_text(encoding="utf-8"))
    if etiquetado["snapshot_id"] != producto.manifest.snapshot_id:
        raise typer.BadParameter("El etiquetado pertenece a otra publicación; vuelva a preparar y unir")
    vocabulario, practicas = conceptos.vocabulario(), conceptos.practicas()
    if etiquetado["vocabulario_sha256"] != c4.sha_json(
        sorted(vocabulario.values(), key=lambda c: c["id"])
    ) or etiquetado["practicas_sha256"] != c4.sha_json(sorted(practicas.values(), key=lambda p: p["id"])):
        raise typer.BadParameter("El vocabulario cambió después de etiquetar; vuelva a preparar y unir")
    catalogo = {f.fila_id: f.estado for f in producto.catalogo.filas}
    campos = ("contenido", "subcontenido", "procedimental", "indicadores_logro", "indicador_avanzado")
    campos += ("evidencia_aprendizaje",)
    propuestas = {
        f.fila_id: f"{f.objetivo_propuesto} {f.indicador_observable}"
        for u in (producto.mejoras.unidades if producto.mejoras else ())
        for f in (u.resultado.propuesta.filas if u.resultado.propuesta else ())
        if f.accion == "precisar_objetivo"
    }
    filas = {}
    for f in producto.curriculo.filas:
        if catalogo[f.id] == "fuera_alcance":
            continue
        texto = " ".join(getattr(f, c) or "" for c in campos)
        filas[f.id] = {
            "grado": f.grado,
            "asignatura_malla": f.asignatura_malla,
            "unidad": f.unidad,
            "dominios_timss": p4.dominios_timss(f.habilidad_timss or ""),
            "texto": p4.plano(texto),
            "texto_original": texto,
            "texto_propuesta": p4.plano(f"{texto} {propuestas.get(f.id, '')}"),
            "texto_propuesta_original": f"{texto} {propuestas.get(f.id, '')}",
        }
    grafo = ruta("data/grafo/aristas.jsonl")
    registros = [json.loads(linea) for linea in grafo.read_text(encoding="utf-8").splitlines()]
    aristas = [(a["origen"], a["destino"]) for a in registros if a["tipo"] == "PRERREQUISITO_DE"]
    equivalencias = [(a["origen"], a["destino"]) for a in registros if a["tipo"] == "EQUIVALE_A"]
    confianzas = {(a["origen"], a["destino"]): a.get("confianza") for a in registros if a["tipo"] == "PRERREQUISITO_DE"}
    comparacion = json.loads(ruta("docs/investigacion/comparacion_v3_v4.json").read_text(encoding="utf-8"))
    pares = [
        (c["anteriores"][0]["id"].removeprefix("TEMA:"), c["actuales"][0]["id"])
        for c in comparacion["coincidencias"]
        if len(c["anteriores"]) == 1 and len(c["actuales"]) == 1
    ]
    procedencia = {
        "etiquetado_sha256": c4.sha_json(etiquetado),
        "grafo_v3_aristas_sha256": hashlib.sha256(grafo.read_bytes()).hexdigest(),
        "comparacion_v3_v4_sha256": c4.sha_json(comparacion),
        "prerrequisitos_v3": len(aristas),
        "equivalencias_v3": len(equivalencias),
    }
    documento = p4.construir(
        filas,
        etiquetado,
        vocabulario,
        aristas,
        etiquetas_v3=conceptos.etiquetado(),
        pares_v3_v4=pares,
        procedencia=procedencia,
        equivalencias=equivalencias,
        confianzas=confianzas,
    )
    salida = ruta(p4.ARCHIVO)
    escribir_texto_generado(salida, json.dumps(documento, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
    vista = documento["vistas"]["original"]
    typer.echo(
        json.dumps(
            {"patrones": vista["patrones"], "prerrequisitos_ordenados": vista["prerrequisitos"]["proporcion_ordenada"]},
            ensure_ascii=False,
        )
    )
