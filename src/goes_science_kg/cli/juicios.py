"""Prepare local V4 knowledge dossiers before invoking four remote reviewers."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Annotated, Literal
from uuid import uuid4

import typer
from pydantic import Field, model_validator

from goes_science_kg.archivos import destino_generado, escribir_texto_generado
from goes_science_kg.config import cargar, ruta
from goes_science_kg.motor.contratos import Contrato, huella
from goes_science_kg.producto._juicios_contratos import ROLES_CONOCIMIENTO, SolicitudConocimiento, SoporteSemantico

app = typer.Typer(help="Juicios semánticos de conocimiento V4; sin modelos por defecto", no_args_is_help=True)


class ConfigJuicios(Contrato):
    """Configure trusted knowledge-review inputs, storage, models, and execution limits."""

    candidatos: Path
    grafo_historico: Path
    raiz_historica: Path
    raiz_v4: Path
    alertas: Path
    registro: Path
    checkpoints: Path
    log: Path
    max_caracteres: int = Field(ge=2000, le=40000, strict=True)
    max_concurrencia: int = Field(ge=1, le=4, strict=True)
    max_llamadas: int = Field(ge=4, le=200, strict=True)
    max_usd: float = Field(gt=0, le=20)
    reintentos: Literal[0] = 0
    roles_vertex: dict[str, str]

    @model_validator(mode="after")
    def _roles(self):
        if set(self.roles_vertex) != set(ROLES_CONOCIMIENTO) or any(not v for v in self.roles_vertex.values()):
            raise ValueError("Se requieren exactamente cuatro roles de conocimiento")
        return self


def _contexto(cfg: ConfigJuicios, soportes: Path | None):
    from goes_science_kg.curriculo import cargar_curriculo
    from goes_science_kg.curriculo.contexto_fuentes import fuentes_del_curriculo
    from goes_science_kg.modelos import TipoNodo
    from goes_science_kg.producto.conocimiento import InformeConocimiento
    from goes_science_kg.producto.garantias import bloqueos_cientificos
    from goes_science_kg.producto.juicios import PreparadorConocimiento
    from goes_science_kg.producto.referencias import cargar_referencias_historicas

    informe = InformeConocimiento.model_validate_json(ruta(cfg.candidatos).read_bytes())
    referencia = cargar_referencias_historicas(ruta(cfg.grafo_historico))
    catalogo = {n.id.removeprefix("DOC:"): n.props for n in referencia.nodos if n.tipo == TipoNodo.DOCUMENTO}
    complementos = ()
    if soportes:
        if soportes.suffix != ".json":
            raise ValueError("El archivo de soportes requiere extensión JSON")
        complementos = tuple(SoporteSemantico.model_validate(s) for s in json.loads(ruta(soportes).read_bytes()))
    nuevas = {s.documento.removeprefix("DOC:") for s in complementos} - catalogo.keys()
    if nuevas:
        from goes_science_kg.ingesta.referencias import RepositorioReferencias

        referencias = RepositorioReferencias(ruta("data/referencias_cientificas_2026")).manifiesto().referencias
        for id_ in sorted(nuevas):
            r = referencias[id_]
            catalogo[id_] = r.model_dump(mode="json") | {
                "archivo_local": r.archivo_pdf,
                "raiz_fuente": "referencias_cientificas_2026",
            }
    curriculo = cargar_curriculo()
    fuentes = fuentes_del_curriculo(
        curriculo,
        raiz_v4=ruta(cfg.raiz_v4),
        catalogo_historico=catalogo,
        raiz_historica=ruta(cfg.raiz_historica),
    )
    fuentes.bloqueos_curriculares = bloqueos_cientificos(curriculo, fuentes, ruta(cfg.alertas))
    return PreparadorConocimiento(
        curriculo,
        informe,
        referencia,
        fuentes,
        soportes=complementos,
        max_caracteres=cfg.max_caracteres,
    )


def _destino(archivo: Path) -> Path:
    return destino_generado(ruta(archivo), raiz=ruta("."))


def _guardar(datos: dict, salida: Path) -> None:
    escribir_texto_generado(
        salida,
        json.dumps(datos, ensure_ascii=False, indent=2) + "\n",
        extension=".json",
        raiz=ruta("."),
    )


def _vertex_config(cfg: ConfigJuicios):
    from goes_science_kg.motor.vertex import ConfiguracionVertex

    base = ConfiguracionVertex.model_validate(cargar("motor")["vertex"])
    config = ConfiguracionVertex.model_validate(
        base.model_dump(mode="json")
        | {
            "modelos": {r: base.modelos[o] for r, o in cfg.roles_vertex.items()},
            "niveles_razonamiento": {
                r: base.niveles_razonamiento[o] for r, o in cfg.roles_vertex.items() if o in base.niveles_razonamiento
            },
            "max_llamadas": cfg.max_llamadas,
            "max_usd": cfg.max_usd,
            "reintentos": cfg.reintentos,
        }
    )
    if set(config.modelos.values()) - config.tarifas.keys():
        raise ValueError("Cada modelo requiere una tarifa explícita")
    return config


class _IdentidadesConfiguradas:
    """Expose reviewer identities without any generation capability."""

    def __init__(self, configuracion):
        self.configuracion = configuracion

    def nombre_modelo(self, rol):
        """Expose the configured reviewer identity without initializing a provider."""

        return self.configuracion.modelos[rol]

    def generar(self, **kwargs):
        """Reject generation through the identity-only review adapter."""

        raise RuntimeError("La consolidación es una operación local sin generación")


@app.command("medir-contexto")
def medir_contexto(
    presupuesto: Annotated[list[int] | None, typer.Option(help="Repetible; por defecto 18000, 24000 y 40000")] = None,
    salida: Annotated[Path, typer.Option()] = Path("docs/investigacion/presupuesto_contexto_v4.json"),
) -> None:
    """Measure pinned-edition context availability without reference labels or model calls."""
    from goes_science_kg.producto.medicion_contexto import medir_contexto_paises

    try:
        cfg = ConfigJuicios.model_validate(cargar("juicios_conocimiento"))
        destino = _destino(salida)
        if destino.suffix != ".json" or destino == ruta(cfg.candidatos).resolve():
            raise ValueError("La medición requiere un JSON distinto del catálogo de candidatos")
        datos = medir_contexto_paises(
            _contexto(cfg, None), presupuesto if presupuesto is not None else (18000, 24000, 40000)
        )
        _guardar(datos, destino)
        typer.echo(
            json.dumps(
                {
                    "archivo": str(destino),
                    "candidatos": datos["candidatos"],
                    "llamadas": 0,
                    "presupuestos": [
                        {k: v for k, v in p.items() if k != "candidatos_sin_contexto"} for p in datos["presupuestos"]
                    ],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    except (ValueError, KeyError, OSError) as error:
        raise typer.BadParameter(str(error)) from error


@app.command("consolidar")
def consolidar(
    archivos: Annotated[list[Path], typer.Argument(help="Resultados terminales completos de esta configuración")],
    soportes: Annotated[Path | None, typer.Option()] = None,
    salida: Annotated[Path, typer.Option()] = Path("data/producto/juicios/relaciones.json"),
) -> None:
    """Revalidate all selected reviews and reject cyclic relationship admission."""
    from goes_science_kg.motor.conocimiento import MotorConocimiento
    from goes_science_kg.producto.conocimiento_publicado import crear_archivo_conocimiento

    try:
        cfg = ConfigJuicios.model_validate(cargar("juicios_conocimiento"))
        destino = _destino(salida)
        inputs = {ruta(a).resolve() for a in archivos} | {ruta(cfg.candidatos).resolve()}
        if soportes:
            inputs.add(ruta(soportes).resolve())
        if destino.suffix != ".json" or destino in inputs:
            raise ValueError("La colección requiere una salida JSON distinta de todos sus inputs")
        if len({ruta(a).resolve() for a in archivos}) != len(archivos):
            raise ValueError("Archivos repetidos en la consolidación")
        estados = []
        configuracion_modelo = None
        for archivo in archivos:
            if archivo.suffix != ".json" or ruta(archivo).stat().st_size > 4 * 1024 * 1024:
                raise ValueError("Cada resultado requiere JSON de hasta 4 MiB")
            datos = json.loads(ruta(archivo).read_bytes())
            if datos.get("fase") == "juicio_semantico_lote":
                from goes_science_kg.producto.lote_juicios import PlanLoteJuicios

                plan = PlanLoteJuicios.model_validate(datos["plan"])
                vigente = _vertex_config(
                    cfg.model_copy(update={"max_llamadas": plan.vertex.max_llamadas, "max_usd": plan.vertex.max_usd})
                )
                if plan.vertex != vigente or configuracion_modelo not in (None, vigente):
                    raise ValueError("Los resultados requieren la misma política de modelos y presupuesto")
                configuracion_modelo = vigente
                lote = datos["workflow"]
                if not isinstance(lote, list) or [e.get("solicitud") for e in lote] != [
                    s.model_dump(mode="json") for s in plan.solicitudes
                ]:
                    raise ValueError("El resultado del lote debe conservar todas sus solicitudes en orden")
                estados.extend(lote)
                continue
            if datos.get("fase") != "juicio_semantico" or not datos.get("workflow"):
                raise ValueError("Se necesita un resultado completo; preparar no equivale a juzgar")
            if datos.get("resultado") != datos["workflow"].get("resultado"):
                raise ValueError("El resultado visible y el workflow no corresponden")
            vigente = _vertex_config(cfg)
            if configuracion_modelo not in (None, vigente):
                raise ValueError("Los resultados requieren la misma política de modelos y presupuesto")
            configuracion_modelo = vigente
            estados.append(datos["workflow"])
        motor = MotorConocimiento(_contexto(cfg, soportes), _IdentidadesConfiguradas(configuracion_modelo))
        archivo = crear_archivo_conocimiento(motor, estados)
        coleccion = archivo.coleccion
        _guardar(archivo.model_dump(mode="json"), destino)
        typer.echo(
            json.dumps(
                {
                    "archivo": str(destino),
                    "juicios": len(coleccion.resultados),
                    "llamadas": 0,
                    "respaldadas": len(coleccion.relaciones_respaldadas),
                    "admisibles": len(coleccion.relaciones_admisibles),
                    "dependencias": coleccion.proyeccion_dependencias.estado,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    except (ValueError, KeyError, OSError) as error:
        raise typer.BadParameter(str(error)) from error


@app.command("componer")
def componer_cli(
    archivos: Annotated[list[Path], typer.Argument(help="Archivos originales completos; candidatos sin repetir")],
    salida: Annotated[Path, typer.Option()] = Path("data/producto/juicios/conocimiento_compuesto.json"),
) -> None:
    """Compose original protocols without repeating votes or selecting favorable rounds."""
    from goes_science_kg.curriculo import cargar_curriculo
    from goes_science_kg.producto.composicion import componer_archivos
    from goes_science_kg.producto.conocimiento_publicado import ArchivoConocimiento

    try:
        destino = _destino(salida)
        if destino.suffix != ".json" or destino in {ruta(a).resolve() for a in archivos}:
            raise ValueError("La composición necesita un destino JSON distinto de sus inputs")
        originales = []
        for a in archivos:
            if a.suffix != ".json" or ruta(a).stat().st_size > 16 * 1024 * 1024:
                raise ValueError("Cada componente necesita un JSON de hasta 16 MiB")
            originales.append(ArchivoConocimiento.model_validate_json(ruta(a).read_bytes()))
        cfg = ConfigJuicios.model_validate(cargar("juicios_conocimiento"))
        archivo = componer_archivos(originales, cargar_curriculo(), modelos_esperados=_vertex_config(cfg).modelos)
        _guardar(archivo.model_dump(mode="json"), destino)
        typer.echo(
            json.dumps(
                {
                    "archivo": str(destino),
                    "componentes": len(originales),
                    "resultados": len(archivo.coleccion.resultados),
                    "admisibles": len(archivo.coleccion.relaciones_admisibles),
                    "llamadas": 0,
                }
            )
        )
    except (ValueError, KeyError, OSError) as error:
        raise typer.BadParameter(str(error)) from error


@app.command("evaluar")
def evaluar(
    candidato_id: str,
    ejecutar: bool = typer.Option(False, "--ejecutar"),
    soportes: Annotated[
        Path | None, typer.Option(help="Localizadores primarios adicionales, sin texto factual")
    ] = None,
    ejecucion: Annotated[str | None, typer.Option()] = None,
    salida: Annotated[Path, typer.Option()] = Path("data/producto/juicios/resultado.json"),
) -> None:
    """Prepare a dossier unless explicit execution enables four budgeted blind readings."""
    from goes_science_kg.motor.conocimiento import MotorConocimiento

    try:
        cfg = ConfigJuicios.model_validate(cargar("juicios_conocimiento"))
        destino = _destino(salida)
        if destino.suffix != ".json":
            raise ValueError("La salida requiere extensión JSON")
        registro_path, checkpoints, log = map(_destino, (cfg.registro, cfg.checkpoints, cfg.log))
        outputs = {destino, registro_path, checkpoints, log}
        inputs = {
            ruta(cfg.candidatos).resolve(),
            ruta(soportes).resolve() if soportes else None,
        }
        if len(outputs) != 4 or outputs.intersection(inputs):
            raise ValueError("Inputs, resultado, ledger, checkpoints y log requieren destinos distintos")
        id_ejecucion = ejecucion or "conocimiento-" + uuid4().hex
        if not re.fullmatch(r"[a-zA-Z0-9_-]{1,100}", id_ejecucion):
            raise ValueError("El ID admite 1–100 caracteres alfanuméricos, guion o guion bajo")
        config = _vertex_config(cfg)
        preparador = _contexto(cfg, soportes)
        solicitud = SolicitudConocimiento(candidato_id=candidato_id)
        expediente = preparador.preparar(solicitud)
        datos = {
            "fase": "preparacion_local",
            "llamadas": 0,
            "ejecucion_id": id_ejecucion,
            "preparacion": expediente.model_dump(mode="json"),
            "plan_vertex": {
                "proyecto": config.proyecto,
                "region": config.region,
                "modelos": config.modelos,
                "max_llamadas": config.max_llamadas,
                "max_reserva_usd": config.max_usd,
            },
        }
        _guardar(datos, destino)
        if ejecutar and expediente.estado == "preparado":
            from goes_science_kg.motor.ejecuciones import ejecutar_durable
            from goes_science_kg.motor.registro import Registro
            from goes_science_kg.motor.vertex import Vertex
            from goes_science_kg.observabilidad import configurar_logging

            configurar_logging(archivo=log)
            registro = Registro(registro_path)
            modelo = Vertex(config, registro, id_ejecucion)
            motor = MotorConocimiento(preparador, modelo)
            try:
                estado = ejecutar_durable(
                    motor,
                    archivo=checkpoints,
                    solicitud=solicitud.model_dump(mode="json"),
                    thread_id=id_ejecucion,
                    ejecucion_id=id_ejecucion,
                    huella_entorno=huella(
                        {
                            "motor": motor.huella_entorno,
                            "config": cfg.model_dump(mode="json"),
                            "cli": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                        }
                    ),
                    max_concurrencia=cfg.max_concurrencia,
                )
            except (Exception, KeyboardInterrupt):
                _guardar(
                    {
                        "fase": "juicio_interrumpido",
                        "ejecucion_id": id_ejecucion,
                        "consumo": registro.resumen(id_ejecucion),
                        "preparacion": datos["preparacion"],
                    },
                    destino,
                )
                raise
            datos = {
                "fase": "juicio_semantico",
                "resultado": estado["resultado"],
                "workflow": estado,
                "consumo": registro.resumen(id_ejecucion),
                "preparacion": datos["preparacion"],
            }
            _guardar(datos, destino)
        typer.echo(
            json.dumps(
                {
                    "archivo": str(destino),
                    "fase": datos["fase"],
                    "estado_preparacion": expediente.estado,
                    "motivos": expediente.motivos,
                    "llamadas": datos.get("consumo", {}).get("llamadas", 0),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    except (ValueError, KeyError, OSError) as error:
        raise typer.BadParameter(str(error)) from error
    if expediente.estado == "abstencion":
        raise typer.Exit(2)


@app.command("preparar-lote")
def preparar_lote_cli(
    seleccion: Annotated[Path, typer.Argument(help="JSON con una lista de IDs candidatos, fijada antes de juzgar")],
    ejecucion: Annotated[str, typer.Option()],
    max_llamadas: Annotated[int, typer.Option(min=4, max=200)],
    max_usd: Annotated[float, typer.Option(min=0.01, max=20)],
    soportes: Annotated[Path | None, typer.Option()] = None,
    salida: Annotated[Path, typer.Option()] = Path("data/producto/juicios/plan_lote.json"),
) -> None:
    """Fix evidence, reviewer models, and one shared limit before execution."""
    from goes_science_kg.producto.lote_juicios import preparar_lote

    try:
        cfg = ConfigJuicios.model_validate(cargar("juicios_conocimiento"))
        cfg = cfg.model_copy(update={"max_llamadas": max_llamadas, "max_usd": max_usd})
        destino = _destino(salida)
        if destino.suffix != ".json" or destino in {
            ruta(seleccion).resolve(),
            ruta(cfg.candidatos).resolve(),
            ruta(soportes).resolve() if soportes else None,
        }:
            raise ValueError("El plan necesita un destino JSON distinto de sus inputs")
        ids = json.loads(ruta(seleccion).read_bytes())
        if not isinstance(ids, list) or any(not isinstance(i, str) for i in ids):
            raise ValueError("La selección debe ser una lista JSON de IDs")
        plan = preparar_lote(_contexto(cfg, soportes), ids, _vertex_config(cfg), ejecucion)
        _guardar(plan.model_dump(mode="json"), destino)
        typer.echo(json.dumps({"archivo": str(destino), "plan_id": plan.id, "casos": len(ids), "llamadas": 0}))
    except (ValueError, KeyError, OSError) as error:
        raise typer.BadParameter(str(error)) from error


@app.command("ejecutar-lote")
def ejecutar_lote_cli(
    plan: Path,
    ejecutar: bool = typer.Option(False, "--ejecutar"),
    soportes: Annotated[Path | None, typer.Option()] = None,
    salida: Annotated[Path, typer.Option()] = Path("data/producto/juicios/resultado_lote.json"),
) -> None:
    """Verify by default and share one ledger when execution is explicitly enabled."""
    from goes_science_kg.producto.lote_juicios import PlanLoteJuicios, ejecutar_lote, verificar_lote

    try:
        cfg = ConfigJuicios.model_validate(cargar("juicios_conocimiento"))
        destino = _destino(salida)
        registro_path, checkpoints, log = map(_destino, (cfg.registro, cfg.checkpoints, cfg.log))
        inputs = {ruta(plan).resolve(), ruta(cfg.candidatos).resolve()}
        if soportes:
            inputs.add(ruta(soportes).resolve())
        if (
            destino.suffix != ".json"
            or len({destino, registro_path, checkpoints, log}) != 4
            or inputs & {destino, registro_path, checkpoints, log}
        ):
            raise ValueError("Plan, inputs, resultado, ledger, checkpoints y log requieren destinos distintos")
        fijado = PlanLoteJuicios.model_validate_json(ruta(plan).read_bytes())
        cfg = cfg.model_copy(update={"max_llamadas": fijado.vertex.max_llamadas, "max_usd": fijado.vertex.max_usd})
        if _vertex_config(cfg) != fijado.vertex:
            raise ValueError("Proyecto, modelos o política actuales distintos del plan")
        preparador = _contexto(cfg, soportes)
        verificar_lote(fijado, preparador)
        if not ejecutar:
            typer.echo(json.dumps({"estado": "plan_verificado", "casos": len(fijado.solicitudes), "llamadas": 0}))
            return
        from goes_science_kg.motor.conocimiento import MotorConocimiento
        from goes_science_kg.motor.registro import Registro
        from goes_science_kg.motor.vertex import Vertex
        from goes_science_kg.observabilidad import configurar_logging

        configurar_logging(archivo=log)
        registro = Registro(registro_path)
        modelo = Vertex(fijado.vertex, registro, fijado.ejecucion_id)
        try:
            datos = ejecutar_lote(fijado, MotorConocimiento(preparador, modelo), checkpoints=checkpoints)
        except (Exception, KeyboardInterrupt):
            _guardar(
                {
                    "fase": "lote_interrumpido",
                    "plan": fijado.model_dump(mode="json"),
                    "consumo": registro.resumen(fijado.ejecucion_id),
                },
                destino,
            )
            raise
        _guardar(datos, destino)
        typer.echo(
            json.dumps(
                {
                    "archivo": str(destino),
                    "casos": len(datos["workflow"]),
                    "consumo": {k: datos["consumo"][k] for k in ("llamadas", "reserva_usd")},
                }
            )
        )
    except (ValueError, KeyError, OSError) as error:
        raise typer.BadParameter(str(error)) from error
