"""Prepare documentary alignment locally and execute explicit, budgeted reviews."""

from __future__ import annotations

import hashlib
import json
import re
from contextlib import closing
from pathlib import Path
from typing import Annotated, Literal
from uuid import uuid4

import typer
from pydantic import BaseModel, ConfigDict, Field, model_validator

from goes_science_kg.archivos import destino_generado, escribir_texto_generado
from goes_science_kg.config import cargar, ruta
from goes_science_kg.ingesta.extraccion import PaginasConPerfil, cargar_perfiles
from goes_science_kg.ingesta.referencias import RepositorioReferencias
from goes_science_kg.ingesta.referentes_operativos import cargar_referentes, validar_referentes
from goes_science_kg.motor.alineacion import ROLES_ALINEACION, MotorAlineacion, SolicitudAlineacion
from goes_science_kg.motor.contratos import huella

app = typer.Typer(help="Alineación documental por fila y referente, con preparación local", no_args_is_help=True)


@app.command("coleccionar")
def coleccionar(
    ejecuciones: Annotated[list[str], typer.Argument(help="IDs originales de todos los casos de la cohorte")],
    salida: Annotated[Path, typer.Option()],
) -> None:
    """Revalidate terminal states and sources before exporting the complete review cohort."""
    import sqlite3

    from langgraph.checkpoint.sqlite import SqliteSaver

    from goes_science_kg.producto.alineaciones import coleccionar_alineaciones

    try:
        destino = _destino(salida, ".json")
        if len(set(ejecuciones)) != len(ejecuciones) or any(
            not re.fullmatch(r"[a-zA-Z0-9_-]{1,100}", id_) for id_ in ejecuciones
        ):
            raise ValueError("Indique IDs originales válidos y sin duplicados")
        cfg = _configuracion()
        curriculo, referentes, fuentes, paginas = _contexto(cfg)
        estados = []
        archivo = ruta(cfg.checkpoints).resolve()
        with closing(sqlite3.connect(archivo.as_uri() + "?mode=ro", uri=True)) as conexion, conexion:
            saver = SqliteSaver(conexion)
            # El lector de checkpoints no debe intentar crear tablas en el almacén de sólo lectura.
            saver.is_setup = True
            for id_ in ejecuciones:
                registro = saver.get_tuple({"configurable": {"thread_id": id_}})
                if registro is None:
                    raise ValueError(f"No existe el checkpoint {id_}")
                estado = registro.checkpoint["channel_values"]
                if estado.get("ejecucion_id") != id_ or "resultado" not in estado:
                    raise ValueError(f"La ejecución {id_} no conserva un cierre original")
                estados.append(estado)
        archivo_alineaciones = coleccionar_alineaciones(
            estados, curriculo, referentes.por_id, _vertex_config(cfg, None, None).modelos, fuentes, paginas
        )
        escribir_texto_generado(
            destino, archivo_alineaciones.model_dump_json(indent=2) + "\n", extension=".json", raiz=ruta(".")
        )
    except (ValueError, KeyError, OSError, sqlite3.Error) as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(
        json.dumps(
            {
                "archivo": str(destino),
                "id": archivo_alineaciones.id,
                "casos": len(archivo_alineaciones.casos),
                "admitidos": len(archivo_alineaciones.admitidos),
                "llamadas": 0,
            }
        )
    )


class ConfigAlineacion(BaseModel):
    """Configure trusted paths, versions, three reviewer roles, and execution limits."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    version_curriculo: str = Field(min_length=1)
    referentes: Path
    perfiles: Path
    repositorio: Path
    raiz_v4: Path
    alertas: Path
    registro: Path
    checkpoints: Path
    log: Path
    max_caracteres_contexto: int = Field(ge=1000, le=40000, strict=True)
    max_concurrencia: int = Field(ge=1, le=3, strict=True)
    max_llamadas: int = Field(ge=3, le=200, strict=True)
    max_usd: float = Field(gt=0, le=20)
    reintentos: Literal[0] = 0
    roles_vertex: dict[str, str]

    @model_validator(mode="after")
    def _tres_roles(self):
        if set(self.roles_vertex) != set(ROLES_ALINEACION) or any(not v.strip() for v in self.roles_vertex.values()):
            raise ValueError("La configuración requiere exactamente los tres roles de alineación")
        return self


def _configuracion() -> ConfigAlineacion:
    return ConfigAlineacion.model_validate(cargar("alineacion"))


def _destino(archivo: Path, extension: str) -> Path:
    return destino_generado(ruta(archivo), extension=extension, raiz=ruta("."))


def _emitir(datos: dict, salida: Path) -> None:
    escribir_texto_generado(
        salida,
        json.dumps(datos, ensure_ascii=False, indent=2) + "\n",
        extension=".json",
        raiz=ruta("."),
    )
    typer.echo(json.dumps(datos | {"archivo": str(salida)}, ensure_ascii=False, indent=2))


def _referentes(cfg: ConfigAlineacion):
    repo = RepositorioReferencias(ruta(cfg.repositorio))
    paginas = PaginasConPerfil(repo, cargar_perfiles(ruta(cfg.perfiles)))
    catalogo = cargar_referentes(ruta(cfg.referentes), paginas)
    return catalogo, paginas


def _contexto(cfg: ConfigAlineacion):
    from goes_science_kg.curriculo import cargar_curriculo
    from goes_science_kg.curriculo.contexto_fuentes import fuentes_del_curriculo
    from goes_science_kg.producto.garantias import bloqueos_cientificos

    catalogo, paginas = _referentes(cfg)
    curriculo = cargar_curriculo()
    if curriculo.version != cfg.version_curriculo:
        raise ValueError("El currículo cargado no corresponde a la versión de alineación configurada")
    fuentes = fuentes_del_curriculo(curriculo, raiz_v4=ruta(cfg.raiz_v4))
    fuentes.bloqueos_curriculares = bloqueos_cientificos(curriculo, fuentes, ruta(cfg.alertas))
    return curriculo, catalogo, fuentes, paginas


def _vertex_config(cfg: ConfigAlineacion, max_usd: float | None, max_llamadas: int | None):
    from goes_science_kg.motor.vertex import ConfiguracionVertex

    base = ConfiguracionVertex.model_validate(cargar("motor")["vertex"])
    modelos = {rol: base.modelos[origen] for rol, origen in cfg.roles_vertex.items()}
    if any(modelo not in base.tarifas for modelo in modelos.values()):
        raise ValueError("Cada modelo de alineación requiere una tarifa explícita")
    return ConfiguracionVertex.model_validate(
        base.model_dump(mode="json")
        | {
            "modelos": modelos,
            "max_llamadas": max_llamadas if max_llamadas is not None else cfg.max_llamadas,
            "max_usd": max_usd if max_usd is not None else cfg.max_usd,
            "reintentos": cfg.reintentos,
            "niveles_razonamiento": {
                rol: base.niveles_razonamiento[origen]
                for rol, origen in cfg.roles_vertex.items()
                if origen in base.niveles_razonamiento
            },
        }
    )


def _preparacion(fila_id: str, referente_id: str, cfg: ConfigAlineacion):
    curriculo, catalogo, fuentes, paginas = _contexto(cfg)
    motor = MotorAlineacion(
        curriculo,
        catalogo.por_id,
        fuentes,
        paginas,
        max_caracteres=cfg.max_caracteres_contexto,
    )
    solicitud = SolicitudAlineacion(fila_id=fila_id, referente_id=referente_id)
    preparacion = motor.preparar(solicitud)
    return motor, solicitud, preparacion, paginas


def _datos_preparados(preparacion, paginas, vertex=None) -> dict:
    datos = {
        "fase": "preparacion_local",
        "llamadas": 0,
        "huella_extraccion": paginas.huella_extraccion,
        "preparacion": preparacion.model_dump(mode="json"),
        "advertencia": "Contexto preparado no es un dictamen ni acredita cobertura o aprendizaje",
    }
    if vertex:
        datos["plan_vertex"] = {
            "proyecto": vertex.proyecto,
            "region": vertex.region,
            "modelos": vertex.modelos,
            "max_llamadas": vertex.max_llamadas,
            "max_reserva_usd": vertex.max_usd,
            "reintentos": vertex.reintentos,
        }
    return datos


@app.command("listar-referentes")
def listar_referentes(
    marco: Annotated[str | None, typer.Option(help="Filtra PISA o ERCE sin cambiar el catálogo")] = None,
    salida: Annotated[Path, typer.Option()] = Path("data/producto/alineaciones/referentes.json"),
) -> None:
    """List verified reference criteria without invoking models or activating a graph."""
    try:
        destino = _destino(salida, ".json")
        catalogo, paginas = _referentes(_configuracion())
        seleccion = [
            r.model_dump(mode="json")
            for r in catalogo.referentes
            if marco is None or r.marco.casefold() == marco.casefold()
        ]
        _emitir(
            {
                "estado": "referentes_documentales",
                "llamadas": 0,
                "huella_extraccion": paginas.huella_extraccion,
                "meta": catalogo.meta.model_dump(mode="json"),
                "total_catalogo": len(catalogo.referentes),
                "total_seleccion": len(seleccion),
                "referentes": seleccion,
            },
            destino,
        )
    except (ValueError, KeyError, OSError) as error:
        raise typer.BadParameter(str(error)) from error


@app.command("validar-referentes")
def validar_referentes_cli(
    salida: Annotated[Path, typer.Option()] = Path("data/producto/alineaciones/auditoria_referentes.json"),
) -> None:
    """Rehydrate documentary anchors and record the extraction fingerprint."""
    try:
        destino = _destino(salida, ".json")
        catalogo, paginas = _referentes(_configuracion())
        resultado = validar_referentes(catalogo, paginas)
        _emitir(
            resultado
            | {
                "llamadas": 0,
                "perfiles": paginas.perfiles.model_dump(mode="json"),
                "advertencia": "La validación de procedencia no acredita alineación de tareas ni aprendizaje",
            },
            destino,
        )
    except (ValueError, KeyError, OSError) as error:
        raise typer.BadParameter(str(error)) from error


@app.command("preparar")
def preparar(
    fila_id: str,
    referente_id: str,
    salida: Annotated[Path, typer.Option()] = Path("data/producto/alineaciones/par_preparado.json"),
) -> None:
    """Save one alignment pair's verified evidence without creating a model or ledger."""
    try:
        destino = _destino(salida, ".json")
        _, _, preparacion, paginas = _preparacion(fila_id, referente_id, _configuracion())
        _emitir(_datos_preparados(preparacion, paginas), destino)
    except (ValueError, KeyError, OSError) as error:
        raise typer.BadParameter(str(error)) from error
    if preparacion.estado == "abstencion":
        raise typer.Exit(2)


@app.command("evaluar")
def evaluar(
    fila_id: str,
    referente_id: str,
    ejecutar: bool = typer.Option(False, "--ejecutar", help="Autoriza esta ejecución remota con los límites mostrados"),
    ejecucion: Annotated[str | None, typer.Option(help="ID para reanudar el mismo par y presupuesto")] = None,
    max_usd: Annotated[float | None, typer.Option(min=0.01, max=20)] = None,
    max_llamadas: Annotated[int | None, typer.Option(min=3, max=200)] = None,
    salida: Annotated[Path, typer.Option()] = Path("data/producto/alineaciones/resultado.json"),
) -> None:
    """Prepare locally unless explicit execution enables durable, budgeted reviews."""
    try:
        cfg = _configuracion()
        destino = _destino(salida, ".json")
        id_ejecucion = ejecucion or "alineacion-" + uuid4().hex
        if not re.fullmatch(r"[a-zA-Z0-9_-]{1,100}", id_ejecucion):
            raise ValueError("El ID admite 1–100 caracteres alfanuméricos, guion o guion bajo")
        # También ledger, checkpoints y log se comprueban antes de crear un proveedor.
        registro_path = _destino(cfg.registro, ".sqlite")
        checkpoints = _destino(cfg.checkpoints, ".sqlite")
        log = _destino(cfg.log, ".log")
        if len({destino, registro_path, checkpoints, log}) != 4:
            raise ValueError("Resultado, ledger, checkpoints y log deben tener destinos distintos")
        vertex_cfg = _vertex_config(cfg, max_usd, max_llamadas)
        motor_local, solicitud, preparacion, paginas = _preparacion(fila_id, referente_id, cfg)
        preparado = _datos_preparados(preparacion, paginas, vertex_cfg) | {"ejecucion_id": id_ejecucion}
        if not ejecutar or preparacion.estado == "abstencion":
            _emitir(preparado, destino)
            if preparacion.estado == "abstencion":
                raise typer.Exit(2)
            return
        # La preparación queda revisable en disco antes de cualquier llamada remota.
        escribir_texto_generado(
            destino, json.dumps(preparado, ensure_ascii=False, indent=2) + "\n", extension=".json", raiz=ruta(".")
        )
        from goes_science_kg.motor.ejecuciones import ejecutar_durable
        from goes_science_kg.motor.registro import Registro
        from goes_science_kg.motor.vertex import Vertex
        from goes_science_kg.observabilidad import configurar_logging

        configurar_logging(archivo=log)
        registro = Registro(registro_path)
        proveedor = Vertex(vertex_cfg, registro, id_ejecucion)
        motor = MotorAlineacion(
            motor_local.curriculo,
            motor_local.referentes,
            motor_local.fuentes,
            paginas,
            proveedor,
            max_caracteres=cfg.max_caracteres_contexto,
        )
        entorno = huella(
            {
                "motor": motor.huella_entorno,
                "configuracion_cli": cfg.model_dump(mode="json"),
                "codigo_cli": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            }
        )
        try:
            estado = ejecutar_durable(
                motor,
                archivo=checkpoints,
                solicitud=solicitud.model_dump(mode="json"),
                thread_id=id_ejecucion,
                ejecucion_id=id_ejecucion,
                huella_entorno=entorno,
                max_concurrencia=cfg.max_concurrencia,
            )
        except (Exception, KeyboardInterrupt):
            # Una interrupción del workflow no deja el archivo inicial afirmando cero consumo.
            _emitir(
                {
                    "fase": "evaluacion_interrumpida",
                    "ejecucion_id": id_ejecucion,
                    "preparacion": preparacion.model_dump(mode="json"),
                    "huella_extraccion": paginas.huella_extraccion,
                    "consumo": registro.resumen(id_ejecucion),
                    "advertencia": "No se obtuvo un resultado; el ID conserva presupuesto y checkpoints",
                },
                destino,
            )
            raise
        resultado = estado["resultado"]
        _emitir(
            {
                "fase": "evaluacion_documental",
                "resultado": resultado,
                "huella_extraccion": paginas.huella_extraccion,
                "consumo": registro.resumen(id_ejecucion),
            },
            destino,
        )
    except (ValueError, KeyError, OSError) as error:
        raise typer.BadParameter(str(error)) from error
    if resultado["estado"] == "abstencion":
        raise typer.Exit(2)
