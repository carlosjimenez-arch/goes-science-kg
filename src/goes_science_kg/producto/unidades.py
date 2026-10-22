"""Paquetes docentes por unidad y ejecución durable del Motor existente por objetivo.

Una sesión por fila es una propuesta de organización, nunca una carga horaria normativa. Preparar
conserva el insumo; ejecutar distingue cada respaldo, abstención y objetivo todavía no ejecutado.
"""

from __future__ import annotations

import fcntl
import hashlib
import html
import json
import logging
import os
import re
import sqlite3
import time
from collections import Counter
from collections.abc import Sequence
from pathlib import Path
from typing import Literal
from uuid import uuid4

from pydantic import Field, field_validator

from goes_science_kg.archivos import PROTEGIDAS
from goes_science_kg.config import ruta
from goes_science_kg.curriculo.catalogacion import DECLARADAS, CatalogoDisciplinas, ClasificacionFila
from goes_science_kg.curriculo.contexto_fuentes import documento_de_fila
from goes_science_kg.curriculo.contratos import FASES, ContratoCurricular, Curriculo, FilaCurricular, FuenteCurricular
from goes_science_kg.motor.contratos import Evidencia, ResultadoMotor, Solicitud, huella
from goes_science_kg.motor.ejecuciones import ejecutar_durable
from goes_science_kg.motor.flujo import Motor
from goes_science_kg.motor.fuentes import FuentesVerificadas
from goes_science_kg.motor.registro import Registro
from goes_science_kg.producto.contratos import AlertaSolicitada
from goes_science_kg.recuperacion import huella_corpus

LOGGER = logging.getLogger(__name__)
LIMITE_ORGANIZACION = (
    "Se propone una sesión por fila para organizar solicitudes. No demuestra duración suficiente, "
    "secuenciación pedagógica, prerrequisitos ni carga normativa."
)


class ContextoAula(ContratoCurricular):
    minutos_por_sesion: int = Field(default=40, ge=5, le=120)
    recursos: tuple[str, ...] = ("papel", "lapiz")
    conectividad: Literal["sin_confirmar", "sin_conexion", "intermitente", "disponible"] = "sin_confirmar"
    apoyos: tuple[str, ...] = ()
    seguridad: tuple[str, ...] = ()

    @field_validator("recursos", "apoyos", "seguridad")
    @classmethod
    def _condiciones_explicitas(cls, valores: tuple[str, ...]) -> tuple[str, ...]:
        if len(valores) > 32 or any(not v.strip() or len(v) > 300 for v in valores):
            raise ValueError("Declare hasta 32 condiciones no vacías de hasta 300 caracteres cada una")
        return valores


class AlertaUnidad(ContratoCurricular):
    fila_id: str
    codigo: str
    descripcion: str
    estado: Literal["observacion_pendiente", "bloqueo_cientifico"] = "observacion_pendiente"


class SesionUnidad(ContratoCurricular):
    id: str
    numero_propuesto: int = Field(ge=1)
    fila_id: str
    solicitud: Solicitud | None
    motivos: tuple[str, ...] = ()


class PaqueteUnidad(ContratoCurricular):
    id: str
    estado: Literal["preparado"] = "preparado"
    version_curriculo: str
    huella_curriculo: str
    huella_catalogo: str
    procedencia_catalogo: dict
    catalogo_modo: Literal["piloto", "completo"]
    piloto_superado: bool
    grado: int
    asignatura_malla: str
    unidad: str
    contexto: ContextoAula
    filas: tuple[FilaCurricular, ...]
    fuentes: tuple[FuenteCurricular, ...]
    clasificaciones: tuple[ClasificacionFila, ...]
    evidencias: tuple[Evidencia, ...]
    alertas: tuple[AlertaUnidad, ...]
    sesiones: tuple[SesionUnidad, ...]
    limite_organizacion: str = LIMITE_ORGANIZACION


class SesionEjecutada(ContratoCurricular):
    sesion_id: str
    fila_id: str
    estado: Literal["respaldado_automaticamente", "abstencion", "no_ejecutada"]
    motivos: tuple[str, ...]
    thread_id: str | None = None
    checkpoint_reutilizado: bool = False
    latencia_ms: float = Field(default=0, ge=0)
    resultado_motor: ResultadoMotor | None = None


class ResultadoUnidad(ContratoCurricular):
    paquete_id: str
    ejecucion_id: str
    huella_entorno: str
    estado: Literal["ejecutado"] = "ejecutado"
    sesiones: tuple[SesionEjecutada, ...]
    cobertura: dict[str, int]
    tiempo_ms: float
    consumo_antes: dict
    consumo_despues: dict
    consumo_incremental: dict
    limites_presupuesto: dict = Field(default_factory=dict)
    checkpoints: str


def _solicitud(fila: FilaCurricular, decision: ClasificacionFila, contexto: ContextoAula) -> Solicitud | None:
    if decision.estado not in {"declarado_malla", "coincidencia_automatica"} or len(decision.disciplinas) != 1:
        return None
    consulta = json.dumps(
        {
            "tarea": "Propón una sesión para este objetivo; conserva su evidencia de aprendizaje y respeta el aula.",
            "objetivo_original": fila.procedimental,
            "fuente_objetivo": {"fila_id": fila.id, "documento": fila.fuente_id, "hoja": fila.hoja, "fila": fila.fila},
            "contexto_aula": contexto.model_dump(mode="json"),
        },
        ensure_ascii=False,
    )
    if len(consulta) > 2000:
        return None
    return Solicitud(
        consulta=consulta,
        version_curriculo=fila.version,
        grado=fila.grado,
        asignatura=decision.disciplinas[0],
        minutos=contexto.minutos_por_sesion,
        recursos=contexto.recursos,
        fila_id=fila.id if fila.version == "V4" else None,
    )


def _verificar_fila(fila: FilaCurricular, fuentes: FuentesVerificadas) -> Evidencia | None:
    evidencia = fuentes.hidratar(documento_de_fila(fila))
    if evidencia is None:
        return None
    originales = evidencia.fuente.get("celdas_verificadas", [])
    if len(originales) != len(fila.celdas):
        raise ValueError("La fuente no conserva todas las celdas de la fila")
    for celda, original in zip(fila.celdas, originales, strict=True):
        origen = original["coordenada_origen"] if original["rango_combinado"] else None
        if (celda.coordenada, celda.origen_combinado, celda.tipo_excel) != (
            original["coordenada_solicitada"],
            origen,
            original["tipo_excel"],
        ) or any(
            (type(valor), valor) != (type(real), real)
            for valor, real in (
                (celda.valor_original, original["valor_original"]),
                (celda.valor, original["valor_real"]),
            )
        ):
            raise ValueError("Una celda del paquete difiere del archivo original")
        texto = "" if celda.valor is None else str(celda.valor).strip()
        if celda.campo and celda.campo != "unidad":
            declarado = (
                fila.fases[celda.campo.removeprefix("fase_")].texto
                if celda.campo.startswith("fase_")
                else getattr(fila, celda.campo)
            )
            if declarado != texto:
                raise ValueError("El campo curricular no coincide con su celda original")
    return evidencia


def preparar_unidad(
    curriculo: Curriculo,
    catalogo: CatalogoDisciplinas,
    *,
    grado: int,
    asignatura_malla: str,
    unidad: str,
    contexto: ContextoAula,
    fuentes: FuentesVerificadas,
    alertas: Sequence[AlertaSolicitada] = (),
) -> PaqueteUnidad:
    """Selección exacta y exhaustiva; no propone ciencia, actividades ni prerrequisitos nuevos."""
    if catalogo.version_curriculo != curriculo.version or catalogo.huella_curriculo != curriculo.huella:
        raise ValueError("El catálogo no corresponde al currículo seleccionado")
    if Counter(f.id for f in curriculo.filas) != Counter(f.fila_id for f in catalogo.filas) or len(
        {f.id for f in curriculo.filas}
    ) != len(curriculo.filas):
        raise ValueError("El catálogo debe representar exactamente las filas únicas del currículo")
    filas = tuple(
        sorted(
            (
                f
                for f in curriculo.filas
                if (f.grado, f.asignatura_malla, f.unidad) == (grado, asignatura_malla, unidad)
            ),
            key=lambda f: (f.hoja, f.fila, f.id),
        )
    )
    if not filas:
        raise ValueError("No existe una unidad con ese grado, asignatura de malla y nombre exactos")
    decisiones = {d.fila_id: d for d in catalogo.filas}
    por_fuente = {f.id: f for f in curriculo.fuentes}
    if len(por_fuente) != len(curriculo.fuentes) or any(f.fuente_id not in por_fuente for f in filas):
        raise ValueError("Las filas requieren identidades de fuente únicas y presentes en el currículo")
    registros, evidencias, sesiones = [], [], []
    por_fila = {f.id: f for f in filas}
    for alerta in alertas:
        if alerta.fila_id in por_fila:
            registros.append(AlertaUnidad(fila_id=alerta.fila_id, codigo=alerta.codigo, descripcion=alerta.descripcion))
    for numero, fila in enumerate(filas, 1):
        decision = ClasificacionFila.model_validate(decisiones[fila.id].model_dump())
        if decision.estado == "declarado_malla" and decision.disciplinas != (DECLARADAS.get(fila.asignatura_malla),):
            raise ValueError("La clasificación declarada no corresponde a la asignatura original")
        evidencia = _verificar_fila(fila, fuentes)
        motivos = []
        if evidencia is None:
            motivos.append("No existe evidencia original verificable de la fila")
        else:
            if evidencia.fuente.get("sha256") != por_fuente[fila.fuente_id].sha256:
                raise ValueError("La evidencia no coincide con la edición de fuente declarada en el currículo")
            evidencias.append(evidencia)
        if fila.id in fuentes.bloqueos_efectivos:
            descripcion = fuentes.bloqueos_efectivos[fila.id]
            registros.append(
                AlertaUnidad(
                    fila_id=fila.id,
                    codigo="error_cientifico_confirmado",
                    descripcion=descripcion,
                    estado="bloqueo_cientifico",
                )
            )
            motivos.append(descripcion)
        for fase in FASES:
            if not fila.fases[fase].presente_en_hoja:
                registros.append(
                    AlertaUnidad(
                        fila_id=fila.id,
                        codigo=f"fase_ausente:{fase}",
                        descripcion="La columna no existe en el insumo; no se completa por inferencia",
                    )
                )
        solicitud = _solicitud(fila, decision, contexto)
        if solicitud is None:
            motivos.append(
                "Clasificación no utilizable o ambigua"
                if len(decision.disciplinas) != 1
                else "La solicitud contextualizada excede 2.000 caracteres; no se trunca"
            )
        identidad = huella(
            {
                "fila": fila.id,
                "contexto": contexto.model_dump(mode="json"),
                "grado": grado,
                "asignatura_malla": asignatura_malla,
                "unidad": unidad,
            }
        )
        sesiones.append(
            SesionUnidad(
                id=identidad,
                numero_propuesto=numero,
                fila_id=fila.id,
                solicitud=None if motivos else solicitud,
                motivos=tuple(motivos),
            )
        )
    datos = dict(
        version_curriculo=curriculo.version,
        huella_curriculo=curriculo.huella,
        huella_catalogo=huella(catalogo),
        procedencia_catalogo=catalogo.model_dump(mode="json", exclude={"filas"}),
        catalogo_modo=catalogo.modo,
        piloto_superado=catalogo.piloto_superado,
        grado=grado,
        asignatura_malla=asignatura_malla,
        unidad=unidad,
        contexto=contexto,
        filas=filas,
        fuentes=tuple(f for f in curriculo.fuentes if f.id in {fila.fuente_id for fila in filas}),
        clasificaciones=tuple(decisiones[f.id] for f in filas),
        evidencias=tuple(evidencias),
        alertas=tuple(registros),
        sesiones=tuple(sesiones),
        estado="preparado",
        limite_organizacion=LIMITE_ORGANIZACION,
    )
    temporal = PaqueteUnidad(id="por_calcular", **datos)
    return temporal.model_copy(update={"id": huella(temporal.model_dump(mode="json", exclude={"id"}))})


def _comprobar_paquete(paquete: PaqueteUnidad) -> None:
    if paquete.id != huella(paquete.model_dump(mode="json", exclude={"id"})):
        raise ValueError("El paquete cambió después de prepararse")
    if Counter(f.id for f in paquete.filas) != Counter(s.fila_id for s in paquete.sesiones):
        raise ValueError("La organización debe conservar exactamente una sesión propuesta por fila")


def _directorio(destino: Path) -> Path:
    if destino.is_symlink():
        raise ValueError("El directorio de paquetes u operaciones no puede ser un enlace")
    base = destino.resolve()
    for protegido in PROTEGIDAS:
        if base.is_relative_to(ruta(protegido).resolve()):
            raise ValueError("El directorio debe estar fuera de originales, código y configuración")
    base.mkdir(parents=True, exist_ok=True)
    return base


def _archivo_propio(base: Path, nombre: str) -> Path:
    archivo = base / nombre
    if archivo.is_symlink() or not archivo.resolve().is_relative_to(base):
        raise ValueError("El artefacto o checkpoint no puede ser un enlace ni salir del directorio")
    return archivo


def _entorno(motor: Motor, paquete: PaqueteUnidad) -> str:
    cfg = getattr(motor.modelo, "configuracion", None)
    return huella(
        {
            "paquete": paquete.id,
            "recuperador": motor.buscador.huella,
            "corpus": huella_corpus(motor.buscador.documentos.values()),
            "modelos": {
                r: motor.modelo.nombre_modelo(r) for r in ("redactor", "cientifico", "psicopedagogo", "adversarial")
            },
            "configuracion_modelo": cfg.model_dump(mode="json") if cfg is not None else None,
            "max_caracteres": motor.max_caracteres,
            "max_reparaciones": motor.max_reparaciones,
            "fuentes": motor.fuentes.catalogo,
            "bloqueos": motor.fuentes.bloqueos_efectivos,
            "codigo": {
                f"{p.parent.name}/{p.name}": hashlib.sha256(p.read_bytes()).hexdigest()
                for nombre in ("motor", "recuperacion", "curriculo", "producto", "ingesta")
                for p in sorted((Path(__file__).resolve().parents[1] / nombre).glob("*.py"))
            },
        }
    )


def _anclaje_exacto(resultado: ResultadoMotor, fila: FilaCurricular) -> bool:
    if resultado.propuesta is None:
        return False
    evidencias = {e.id: e for e in resultado.evidencias}
    for cita in resultado.propuesta.anclaje_curricular:
        evidencia = evidencias.get(cita.evidencia_id)
        if evidencia is not None and evidencia.version == fila.version:
            fuente = evidencia.fuente
            if (fuente.get("documento"), fuente.get("hoja"), fuente.get("fila")) == (
                fila.fuente_id,
                fila.hoja,
                fila.fila,
            ) and evidencia.id.partition("#CELDA:")[0] == fila.id:
                return True
    return False


def ejecutar_unidad(
    paquete: PaqueteUnidad,
    *,
    motor: Motor,
    registro: Registro,
    ejecucion_id: str,
    directorio_operaciones: Path,
) -> ResultadoUnidad:
    """Reanuda el mismo Motor por sesión; un único ledger acota toda la unidad."""
    _comprobar_paquete(paquete)
    if paquete.catalogo_modo != "completo" or not paquete.piloto_superado:
        raise ValueError("La ejecución requiere un catálogo completo con piloto superado; preparación no es activación")
    if not re.fullmatch(r"[a-zA-Z0-9_-]{1,100}", ejecucion_id):
        raise ValueError("El ID de presupuesto debe tener entre uno y cien caracteres seguros")
    if (
        getattr(motor.modelo, "ejecucion_id", None) != ejecucion_id
        or getattr(motor.modelo, "registro", None) is None
        or motor.modelo.registro.archivo.resolve() != registro.archivo.resolve()
    ):
        raise ValueError("El proveedor debe compartir el mismo Registro e ID de presupuesto de toda la unidad")
    if motor.fuentes is None:
        raise ValueError("El Motor necesita fuentes verificadas")
    esperadas = {e.id: e for e in paquete.evidencias}
    for fila in paquete.filas:
        verificada = _verificar_fila(fila, motor.fuentes)
        if fila.id in esperadas and verificada != esperadas[fila.id]:
            raise ValueError("Cambió la evidencia original del paquete; se requiere preparar nuevamente")
    entorno = _entorno(motor, paquete)
    base = _directorio(directorio_operaciones)
    lock = _archivo_propio(base, f"{ejecucion_id}.lock")
    descriptor = os.open(lock, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise ValueError("La misma ejecución de unidad ya está en curso") from error
        return _ejecutar_con_bloqueo(
            paquete, motor, registro, ejecucion_id, entorno, _archivo_propio(base, "checkpoints_unidades.sqlite")
        )
    finally:
        os.close(descriptor)


def _ejecutar_con_bloqueo(paquete, motor, registro, ejecucion_id, entorno, archivo) -> ResultadoUnidad:
    inicio = time.perf_counter()
    antes = registro.resumen(ejecucion_id)
    resultados = []
    filas = {f.id: f for f in paquete.filas}
    with sqlite3.connect(archivo, check_same_thread=False, timeout=30) as db:
        db.execute(
            "CREATE TABLE IF NOT EXISTS unidades_ejecuciones (id TEXT PRIMARY KEY, paquete TEXT, "
            "entorno TEXT, ledger TEXT)"
        )
        db.execute("BEGIN IMMEDIATE")
        vinculo = (paquete.id, entorno, str(registro.archivo.resolve()))
        previo = db.execute(
            "SELECT paquete,entorno,ledger FROM unidades_ejecuciones WHERE id=?", (ejecucion_id,)
        ).fetchone()
        if previo is not None and tuple(previo) != vinculo:
            raise ValueError("Cambió el paquete, entorno o ledger de esta ejecución; no se reutilizan checkpoints")
        db.execute("INSERT OR IGNORE INTO unidades_ejecuciones VALUES(?,?,?,?)", (ejecucion_id, *vinculo))
        db.execute("CREATE TABLE IF NOT EXISTS unidades_sesiones (thread TEXT PRIMARY KEY, estado TEXT)")
        db.commit()
        for sesion in paquete.sesiones:
            inicio_sesion = time.perf_counter()
            if sesion.solicitud is None:
                resultados.append(
                    SesionEjecutada(
                        sesion_id=sesion.id, fila_id=sesion.fila_id, estado="no_ejecutada", motivos=sesion.motivos
                    )
                )
                continue
            thread = f"unidad:{ejecucion_id}:{sesion.id}"
            reutilizado = (
                db.execute("SELECT estado FROM unidades_sesiones WHERE thread=?", (thread,)).fetchone() is not None
            )
            uso = registro.resumen(ejecucion_id)
            cfg = getattr(motor.modelo, "configuracion", None)
            if (
                not reutilizado
                and cfg is not None
                and (uso["llamadas"] >= cfg.max_llamadas or uso["reserva_usd"] >= cfg.max_usd)
            ):
                resultados.append(
                    SesionEjecutada(
                        sesion_id=sesion.id,
                        fila_id=sesion.fila_id,
                        estado="no_ejecutada",
                        motivos=("Presupuesto compartido agotado",),
                    )
                )
                continue
            db.execute("INSERT OR IGNORE INTO unidades_sesiones VALUES(?,?)", (thread, "en_curso"))
            db.commit()
            resultado, errores = None, []
            try:
                LOGGER.info("Sesión %d: ejecutando objetivo %s", sesion.numero_propuesto, sesion.fila_id)
                salida = ejecutar_durable(
                    motor,
                    archivo=archivo,
                    solicitud=sesion.solicitud.model_dump(),
                    thread_id=thread,
                    ejecucion_id=ejecucion_id,
                    huella_entorno=entorno,
                )
                resultado = ResultadoMotor.model_validate(salida["resultado"])
                if resultado.ejecucion_id != ejecucion_id or resultado.version_curriculo != paquete.version_curriculo:
                    raise ValueError("El resultado del Motor pertenece a otro presupuesto o currículo")
                db.execute("UPDATE unidades_sesiones SET estado='terminal' WHERE thread=?", (thread,))
                db.commit()
                errores.extend(resultado.motivos)
                if resultado.estado == "respaldado_automaticamente" and not _anclaje_exacto(
                    resultado, filas[sesion.fila_id]
                ):
                    errores.append(
                        "El Motor no citó la fila objetivo exacta; no se cuenta como respaldo de esta sesión"
                    )
            except Exception as error:
                errores.append(f"Ejecución no disponible: {type(error).__name__}")
                LOGGER.warning("AMARILLO objetivo %s en abstención: %s", sesion.fila_id, type(error).__name__)
            respaldado = resultado is not None and resultado.estado == "respaldado_automaticamente" and not errores
            resultados.append(
                SesionEjecutada(
                    sesion_id=sesion.id,
                    fila_id=sesion.fila_id,
                    estado="respaldado_automaticamente" if respaldado else "abstencion",
                    motivos=tuple(errores),
                    thread_id=thread,
                    checkpoint_reutilizado=reutilizado,
                    latencia_ms=(time.perf_counter() - inicio_sesion) * 1000,
                    resultado_motor=resultado,
                )
            )
    despues = registro.resumen(ejecucion_id)
    conteos = Counter(r.estado for r in resultados)
    cfg = getattr(motor.modelo, "configuracion", None)
    return ResultadoUnidad(
        paquete_id=paquete.id,
        ejecucion_id=ejecucion_id,
        huella_entorno=entorno,
        sesiones=tuple(resultados),
        cobertura={
            "filas_totales": len(paquete.filas),
            "sesiones_propuestas": len(paquete.sesiones),
            "respaldadas": conteos["respaldado_automaticamente"],
            "abstenciones": conteos["abstencion"],
            "no_ejecutadas": conteos["no_ejecutada"],
        },
        tiempo_ms=(time.perf_counter() - inicio) * 1000,
        consumo_antes=antes,
        consumo_despues=despues,
        consumo_incremental={k: despues[k] - antes[k] for k in ("llamadas", "reserva_usd")},
        limites_presupuesto={"max_llamadas": cfg.max_llamadas, "max_usd": cfg.max_usd} if cfg else {},
        checkpoints=str(archivo),
    )


def _texto(valor) -> str:
    seguro = html.escape(str(valor), quote=True)
    return re.sub(r"([\\`*_{}\[\]()#+.!|])", r"\\\1", seguro).replace("\n", "  \n")


def exportar_unidad(paquete: PaqueteUnidad, destino: Path, *, resultado: ResultadoUnidad | None = None) -> dict:
    """JSON íntegro y ficha Markdown; fuentes originales y respuestas automáticas quedan rotuladas."""
    _comprobar_paquete(paquete)
    if resultado is not None and resultado.paquete_id != paquete.id:
        raise ValueError("El resultado no pertenece a este paquete")
    if resultado is not None and Counter(s.sesion_id for s in resultado.sesiones) != Counter(
        s.id for s in paquete.sesiones
    ):
        raise ValueError("El reporte debe conservar exactamente todas las sesiones propuestas")
    base = _directorio(destino)
    datos = {
        "paquete": paquete.model_dump(mode="json"),
        "ejecucion": resultado.model_dump(mode="json") if resultado else None,
    }
    lineas = [
        f"# Unidad: {_texto(paquete.unidad)}",
        "",
        f"Estado: **{paquete.estado}**. Preparación no equivale a respaldo automático ni aprobación oficial.",
        "",
        f"Grado {paquete.grado}; asignatura de malla: {_texto(paquete.asignatura_malla)}. "
        f"Catálogo: {paquete.catalogo_modo}; piloto superado: {paquete.piloto_superado}.",
        "",
        _texto(paquete.limite_organizacion),
        "",
        f"Sesiones propuestas: {len(paquete.sesiones)}; {paquete.contexto.minutos_por_sesion} minutos "
        "solicitados por sesión. No es una duración certificada por el currículo.",
        "",
        "## Contexto de aula",
        "",
        _texto(json.dumps(paquete.contexto.model_dump(mode="json"), ensure_ascii=False)),
    ]
    por_fila = {f.id: f for f in paquete.filas}
    por_fuente = {f.id: f for f in paquete.fuentes}
    clasificaciones = {c.fila_id: c for c in paquete.clasificaciones}
    evidencia = {e.id: e for e in paquete.evidencias}
    ejecuciones = {s.sesion_id: s for s in resultado.sesiones} if resultado else {}
    for sesion in paquete.sesiones:
        fila = por_fila[sesion.fila_id]
        lineas += [
            "",
            f"## Sesión propuesta {sesion.numero_propuesto}",
            "",
            f"Fila: `{fila.id}`; hoja {_texto(fila.hoja)}, fila física {fila.fila}.",
            "",
            "**Objetivo original:** " + _texto(fila.procedimental),
            "",
            "**Clasificación:** "
            + _texto(clasificaciones[fila.id].estado)
            + "; disciplinas: "
            + _texto(", ".join(clasificaciones[fila.id].disciplinas) or "Sin disciplina utilizable"),
            "",
            "**Indicador avanzado:** " + _texto(fila.indicador_avanzado or "No declarado"),
            "",
            "**Indicadores de logro:** " + _texto(fila.indicadores_logro or "No declarados"),
            "",
            "**Evidencia de aprendizaje original:** " + _texto(fila.evidencia_aprendizaje or "No declarada"),
        ]
        for nombre in FASES:
            fase = fila.fases[nombre]
            lineas += [
                "",
                f"**{nombre.capitalize()}:** "
                + _texto(
                    (fase.texto or "Columna presente; celda sin texto")
                    if fase.presente_en_hoja
                    else "Columna ausente; no se completa por inferencia"
                ),
            ]
        e = evidencia.get(fila.id)
        lineas += [
            "",
            f"Archivo original: {_texto(por_fuente[fila.fuente_id].archivo)}; fuente "
            f"{_texto(e.fuente['documento'])}; SHA-256 `{e.fuente['sha256']}`."
            if e
            else "Fuente original no verificable; no se ejecuta.",
        ]
        for alerta in paquete.alertas:
            if alerta.fila_id == fila.id:
                lineas += ["", f"Alerta ({alerta.estado}, {alerta.codigo}): {_texto(alerta.descripcion)}"]
        if sesion.motivos:
            lineas += ["", "No ejecutable: " + _texto(" | ".join(sesion.motivos))]
        if ejecutada := ejecuciones.get(sesion.id):
            lineas += ["", f"Ejecución: **{ejecutada.estado}**.", "", _texto(" | ".join(ejecutada.motivos))]
            if ejecutada.estado == "respaldado_automaticamente" and ejecutada.resultado_motor.propuesta:
                propuesta = ejecutada.resultado_motor.propuesta
                lineas += [
                    "",
                    "### Propuesta automática con revisiones del Motor",
                    "",
                    _texto(propuesta.actividad.objetivo),
                    "",
                    *[f"{i}. {_texto(paso)}" for i, paso in enumerate(propuesta.actividad.pasos, 1)],
                    "",
                    "Comprobación propuesta: " + _texto(propuesta.actividad.comprobacion),
                    "",
                    "Límites de la propuesta: " + _texto(" | ".join(propuesta.limites)),
                ]
    if resultado:
        lineas += [
            "",
            "## Cobertura y consumo",
            "",
            _texto(json.dumps(resultado.cobertura, ensure_ascii=False)),
            "",
            "Límites del presupuesto compartido: " + _texto(json.dumps(resultado.limites_presupuesto)),
            "",
            f"Tiempo observado: {resultado.tiempo_ms:.1f} ms. Llamadas incrementales: "
            f"{resultado.consumo_incremental['llamadas']}; reserva incremental USD "
            f"{resultado.consumo_incremental['reserva_usd']:.6f}. No es importe facturado.",
        ]
    contenidos = {
        "paquete.json": json.dumps(datos, ensure_ascii=False, indent=2) + "\n",
        "paquete.md": "\n".join(lineas) + "\n",
    }
    huellas = {}
    for nombre, contenido in contenidos.items():
        archivo = _archivo_propio(base, nombre)
        temporal = _archivo_propio(base, f".{nombre}.{uuid4().hex}.tmp")
        try:
            temporal.write_text(contenido, encoding="utf-8")
            temporal.replace(archivo)
        finally:
            temporal.unlink(missing_ok=True)
        huellas[nombre] = hashlib.sha256(contenido.encode()).hexdigest()
    return {
        "paquete_id": paquete.id,
        "estado": paquete.estado,
        "directorio": str(base),
        "sha256": huellas,
        "llamadas_preparacion": 0,
    }
