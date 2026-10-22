"""Comandos del motor curricular: versión explícita, ejecución durable y gasto acotado."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Annotated
from uuid import uuid4

import typer

from goes_science_kg.config import cargar, ruta

app = typer.Typer(help="Motor curricular con evidencia y revisión automática", no_args_is_help=True)


@app.command("estado")
def estado() -> None:
    """Disponibilidad de las mallas; no confunde versión de grafo con versión curricular."""
    cfg = cargar("motor")
    from goes_science_kg.curriculo import cargar_curriculo
    from goes_science_kg.producto.runtime import cargar_recursos

    configurada = cargar("mallas").get("version", "sin_version")
    error = None
    try:
        version = cargar_recursos(cfg["version_objetivo"])[0].version
    except (ValueError, OSError) as problema:
        version, error = None, str(problema)
    try:
        curriculo = cargar_curriculo()
        insumo_disponible = curriculo.version == cfg["version_objetivo"]
    except (ValueError, OSError):
        insumo_disponible = False
    typer.echo(
        json.dumps(
            {
                "version_materializada": version,
                "version_configurada": configurada,
                "error_materializacion": error,
                "version_objetivo": cfg["version_objetivo"],
                "insumo_objetivo_disponible": insumo_disponible,
                "publicacion_objetivo_disponible": version == cfg["version_objetivo"],
                "presupuesto_por_ejecucion": {k: cfg["vertex"][k] for k in ("max_llamadas", "max_usd")},
            },
            ensure_ascii=False,
            indent=2,
        )
    )


@app.command("buscar")
def buscar(
    consulta: str,
    grado: int = typer.Option(..., min=2, max=11),
    asignatura: str = typer.Option(...),
    version: str = typer.Option(None),
    k: int = typer.Option(10, min=1, max=60),
    fila_id: Annotated[str | None, typer.Option(help="Recupera sólo esta fila y sus fuentes admitidas")] = None,
) -> None:
    """Recuperación local sobre la publicación seleccionada; no consume GCP."""
    from goes_science_kg.producto.runtime import cargar_recursos

    version = version or cargar("motor")["version_objetivo"]
    buscador, _ = cargar_recursos(version)
    if fila_id is not None:
        if not hasattr(buscador, "buscar_fila"):
            raise typer.BadParameter("El recuperador no admite evidencia por fila explícita")
        resultados = buscador.buscar_fila(fila_id, version=version, grado=grado, asignatura=asignatura, k=k)
    else:
        resultados = buscador.buscar(consulta, version=version, grado=grado, asignatura=asignatura, k=k)
    typer.echo(json.dumps([r.model_dump(mode="json") for r in resultados], ensure_ascii=False, indent=2))


@app.command("responder")
def responder(
    consulta: str,
    grado: int = typer.Option(..., min=2, max=11),
    asignatura: str = typer.Option(...),
    version: str = typer.Option(None),
    minutos: int = typer.Option(40, min=5, max=120),
    recursos: str = typer.Option("papel,lapiz"),
    ejecutar: bool = typer.Option(False, "--ejecutar"),
    ejecucion: Annotated[str | None, typer.Option(help="Reutiliza checkpoints y presupuesto")] = None,
    fila_id: Annotated[str | None, typer.Option(help="Ancla el objetivo y conocimiento a una fila publicada")] = None,
    max_llamadas: Annotated[int | None, typer.Option(min=1, max=200)] = None,
    max_usd: Annotated[float | None, typer.Option(min=0.01, max=20)] = None,
    max_salida_tokens: Annotated[int | None, typer.Option(min=256, max=16384)] = None,
) -> None:
    """Por defecto prepara el contexto. --ejecutar usa Vertex con límites persistentes."""
    from goes_science_kg.motor.contexto import construir_contexto, grupos_obligatorios
    from goes_science_kg.motor.contratos import Solicitud
    from goes_science_kg.motor.fragmentos import datos_fragmentos, preparar_fragmentos
    from goes_science_kg.producto.runtime import cargar_recursos

    cfg = cargar("motor")
    ajustes = {
        k: v
        for k, v in {
            "max_llamadas": max_llamadas,
            "max_usd": max_usd,
            "max_salida_tokens": max_salida_tokens,
        }.items()
        if v is not None
    }
    cfg = cfg | {"vertex": cfg["vertex"] | ajustes}
    s = Solicitud(
        consulta=consulta,
        grado=grado,
        asignatura=asignatura,
        version_curriculo=version or cfg["version_objetivo"],
        minutos=minutos,
        recursos=tuple(r.strip() for r in recursos.split(",") if r.strip()),
        fila_id=fila_id,
    )
    try:
        buscador, fuentes = cargar_recursos(s.version_curriculo)
        if s.fila_id is not None:
            if not hasattr(buscador, "buscar_fila"):
                raise ValueError("El recuperador no admite evidencia por fila explícita")
            resultados = buscador.buscar_fila(
                s.fila_id, version=s.version_curriculo, grado=grado, asignatura=asignatura, k=16
            )
        else:
            resultados = buscador.buscar(
                consulta, version=s.version_curriculo, grado=grado, asignatura=asignatura, k=16
            )
    except (ValueError, OSError):
        resultados = []
        fuentes = None
    evidencias = construir_contexto(
        resultados, version=s.version_curriculo, max_caracteres=cfg["max_caracteres_contexto"], fuentes=fuentes
    )
    if fuentes and (bloqueos := fuentes.motivos_bloqueo(evidencias)):
        typer.echo(json.dumps({"estado": "abstencion", "motivos": bloqueos, "llamadas": 0}, ensure_ascii=False))
        raise typer.Exit(2)
    if not any(e.version == s.version_curriculo for e in evidencias):
        typer.echo(
            json.dumps(
                {"estado": "abstencion", "motivo": f"Falta evidencia de la malla {s.version_curriculo}", "llamadas": 0},
                ensure_ascii=False,
            )
        )
        raise typer.Exit(2)
    if not ejecutar:
        fragmentos = preparar_fragmentos(
            evidencias,
            s.consulta,
            max_caracteres=cfg["max_caracteres_contexto"],
            lectura_completa=True,
            grupos_obligatorios=grupos_obligatorios(resultados, evidencias),
        )
        typer.echo(
            json.dumps(
                {
                    "solicitud": s.model_dump(mode="json"),
                    "llamadas": 0,
                    **datos_fragmentos(fragmentos, evidencias, lectura_completa=True),
                    "limites_vertex": {k: cfg["vertex"][k] for k in ("max_llamadas", "max_usd")}
                    | {"max_salida_tokens": cfg["vertex"].get("max_salida_tokens", 4096)},
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return
    from goes_science_kg.motor.contratos import ESQUEMAS_REVISION, Propuesta, huella
    from goes_science_kg.motor.ejecuciones import ejecutar_durable
    from goes_science_kg.motor.flujo import Motor
    from goes_science_kg.motor.fragmentos import Borrador
    from goes_science_kg.motor.prompts import REDACTOR, VERSION_PROMPT, juez
    from goes_science_kg.motor.registro import Registro
    from goes_science_kg.motor.vertex import ConfiguracionVertex, Vertex
    from goes_science_kg.observabilidad import configurar_logging

    id_ejecucion = ejecucion or uuid4().hex
    if not re.fullmatch(r"[a-zA-Z0-9_-]{1,100}", id_ejecucion):
        raise typer.BadParameter("El ID admite 1–100 caracteres alfanuméricos, guion o guion bajo")
    base = ruta("data/operaciones")
    configurar_logging(archivo=base / "motor.log")
    registro = Registro(base / "registro.sqlite")
    proveedor = Vertex(ConfiguracionVertex.model_validate(cfg["vertex"]), registro, id_ejecucion)
    motor = Motor(
        buscador,
        proveedor,
        max_caracteres=cfg["max_caracteres_contexto"],
        max_reparaciones=cfg["max_reparaciones"],
        fuentes=fuentes,
    )
    huella_entorno = huella(
        {
            "configuracion": cfg,
            "recuperador": buscador.huella,
            "prompt": VERSION_PROMPT,
            "redactor": REDACTOR,
            "jueces": {r: juez(r) for r in ("cientifico", "psicopedagogo", "adversarial")},
            "contratos": [
                s.model_json_schema(),
                Propuesta.model_json_schema(),
                Borrador.model_json_schema(),
                *[e.model_json_schema() for e in ESQUEMAS_REVISION.values()],
            ],
            "codigo_motor": {
                f"{p.parent.name}/{p.name}": hashlib.sha256(p.read_bytes()).hexdigest()
                for paquete in ("motor", "recuperacion", "curriculo", "producto", "ingesta")
                for p in sorted((Path(__file__).resolve().parents[1] / paquete).glob("*.py"))
            },
        }
    )
    try:
        salida = ejecutar_durable(
            motor,
            archivo=base / "checkpoints.sqlite",
            solicitud=s.model_dump(mode="json"),
            thread_id=id_ejecucion,
            ejecucion_id=id_ejecucion,
            huella_entorno=huella_entorno,
            max_concurrencia=cfg["max_concurrencia"],
        )
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(
        json.dumps(salida["resultado"] | {"consumo": registro.resumen(id_ejecucion)}, ensure_ascii=False, indent=2)
    )
    if salida["resultado"]["estado"] == "abstencion":
        raise typer.Exit(2)
