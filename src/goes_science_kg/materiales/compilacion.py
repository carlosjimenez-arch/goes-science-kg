"""Compilación de propuestas revisadas y materiales históricos, sin equivalencias implícitas."""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path

from goes_science_kg.interfaz.consulta import ConsultaInterfaz
from goes_science_kg.producto.unidades import _verificar_fila

LOGGER = logging.getLogger(__name__)
LIMITE_V4 = (
    "Material para preparar clases compilado de propuestas curriculares revisadas automáticamente. "
    "Conserva el alcance de la revisión de la unidad. No agrega guiones cronometrados, datos, "
    "prerrequisitos, validación en aula ni aprobación institucional. Recursos sujetos a disponibilidad."
)
BANCOS = {
    "actividades": "actividad",
    "experimentos": "experimento",
    "microtemas": "microtema",
    "dificultades": "dificultad",
}


def serializar(valor) -> bytes:
    return (json.dumps(valor, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def sha(contenido: bytes) -> str:
    return hashlib.sha256(contenido).hexdigest()


def _entrada(id_, version, tipo, titulo, documento, *, grados=(), asignatura="", unidad="", fila_id="", estado=""):
    return {
        "id": id_,
        "version_curriculo": version,
        "tipo": tipo,
        "titulo": titulo,
        "grados": sorted(set(grados)),
        "asignatura": asignatura,
        "unidad": unidad,
        "fila_id": fila_id,
        "estado": estado,
        "documento": documento,
    }


def compilar_v4(runtime):
    """Cada propuesta se copia íntegra; los votos conservan explícitamente alcance de unidad."""
    consulta = ConsultaInterfaz(runtime)
    registros = []
    for fila in runtime.producto.curriculo.filas:
        evidencia_original = _verificar_fila(fila, runtime.fuentes)
        if evidencia_original is None:
            raise ValueError("La fila no tiene fuente física verificable")
        detalle = consulta.detalle(fila.id)
        propuesta = detalle["propuesta"]
        fuera = propuesta is None or propuesta["accion"] == "fuera_alcance"
        if propuesta is None:
            raise ValueError("La biblioteca requiere una propuesta explícita para cada fila del snapshot")
        if detalle["estado_revision"] != "respaldado_automaticamente":
            raise ValueError("No se publican preparaciones V4 sin el respaldo de su unidad")
        contenido = {
            **detalle,
            "limite_biblioteca": LIMITE_V4,
            "revision_alcance": "unidad_curricular",
            "duracion_minutos": None,
            "guion_cronometrado": False,
            "celdas_originales": [c.model_dump(mode="json") for c in fila.celdas],
            "fuente_original": evidencia_original.fuente,
            "version_contenido": "preparacion-docente-v4-1",
            "material_historico_trasladado": False,
        }
        registros.append(
            _entrada(
                fila.id,
                "V4",
                "fila_fuera_alcance" if fuera else "paquete_objetivo",
                propuesta["objetivo_propuesto"] or fila.procedimental,
                contenido,
                grados=[fila.grado],
                asignatura=fila.asignatura_malla,
                unidad=fila.unidad,
                fila_id=fila.id,
                estado="fuera_alcance" if fuera else "compilado_de_propuesta_respaldada",
            )
        )
    for caso in runtime.producto.mejoras.unidades:
        solicitud = caso.preparacion.solicitud
        filas = [f["id"] for f in caso.preparacion.filas_originales]
        registros.append(
            _entrada(
                "UNIDAD-DOCENTE:" + caso.preparacion.id,
                "V4",
                "paquete_unidad",
                solicitud.unidad,
                {
                    "snapshot_id": consulta.identidad["snapshot_id"],
                    "filas_ids": filas,
                    "preparacion_id": caso.preparacion.id,
                    "contexto_aula": caso.preparacion.contexto_aula,
                    "revisiones": consulta.revisiones(caso),
                    "estado_revision": caso.resultado.estado,
                    "limite_biblioteca": LIMITE_V4,
                    "orden": "orden documental; no secuencia pedagógica inferida",
                },
                grados=[solicitud.grado],
                asignatura=solicitud.asignatura_malla,
                unidad=solicitud.unidad,
                estado="compilado_de_propuesta_respaldada",
            )
        )
    return registros


def recoger_originales(base: Path) -> dict[str, bytes]:
    """Lista cerrada de materiales; nunca incorpora credenciales, estudiantes ni logs."""
    rutas = [
        *sorted((base / "entregas/paquetes_clase").glob("*.json")),
        *sorted((base / "entregas/paquetes_clase").glob("*.md")),
        *sorted((base / "aprendizaje/recorridos").glob("*.json")),
        *sorted((base / "aprendizaje/recorridos").glob("*.md")),
    ]
    rutas += [base / f"data/pedagogia/{b}.json" for b in BANCOS]
    rutas += [
        base / "data/pedagogia/REVISION_PENDIENTE.md",
        base / "data/interim/revisiones/2026-10-13_paquetes_clase.json",
    ]
    rutas += [base / f"data/producto/unidades/fisica-10-entrega-experimental/unidad.{ext}" for ext in ("json", "md")]
    archivos = {}
    for p in rutas:
        if p.is_symlink() or any((base / p_).is_symlink() for p_ in p.relative_to(base).parents):
            raise ValueError("Los originales deben ser archivos propios")
        # resolve también impide un enlace en cualquier directorio antecesor.
        if not p.resolve().is_relative_to(base.resolve()) or not p.is_file():
            raise ValueError(f"Falta un original regular: {p.name}")
        archivos[p.relative_to(base).as_posix()] = p.read_bytes()
    return archivos


def compilar_historicos(archivos):
    registros = []
    for ruta, contenido in sorted(archivos.items()):
        if ruta.startswith("entregas/paquetes_clase/") and ruta.endswith(".json"):
            paquete = json.loads(contenido)
            tema = paquete["tema"]
            registros.append(
                _entrada(
                    "V3:" + tema["id"],
                    "V3",
                    "paquete_historico",
                    tema["procedimental"],
                    {
                        "original": paquete,
                        "archivo_original": ruta,
                        "sha256_original": sha(contenido),
                        "revision_alcance": "historico_sin_migrar",
                        "migrado_a_v4": False,
                    },
                    grados=[tema["grado"]],
                    asignatura=tema["asignatura"],
                    unidad=tema["unidad"],
                    estado=paquete["completitud"]["revision_del_panel"],
                )
            )
    for banco, tipo in BANCOS.items():
        ruta = f"data/pedagogia/{banco}.json"
        for elemento in json.loads(archivos[ruta]):
            registros.append(
                _entrada(
                    "HIST:" + elemento["id"],
                    "historico",
                    tipo,
                    elemento.get("titulo", elemento.get("enunciado", elemento.get("descripcion", elemento["id"]))),
                    {
                        "original": elemento,
                        "archivo_original": ruta,
                        "sha256_original": sha(archivos[ruta]),
                        "revision_alcance": "historico_sin_migrar",
                        "migrado_a_v4": False,
                    },
                    grados=elemento.get("grados", []),
                    estado=elemento["estado"],
                )
            )
    recorridos = json.loads(archivos["aprendizaje/recorridos/recorridos.json"])
    for id_, valor in sorted(recorridos.items()):
        registros.append(
            _entrada(
                "RECORRIDO:" + id_,
                "historico",
                "recorrido",
                id_,
                {"original": valor, "revision_alcance": "demostracion_historica", "migrado_a_v4": False},
                estado="demostracion_historica",
            )
        )
    ruta = "data/producto/unidades/fisica-10-entrega-experimental/unidad.json"
    d = json.loads(archivos[ruta])
    registros.append(
        _entrada(
            "EXPERIMENTAL:" + d["paquete_origen_id"],
            "V4",
            "unidad_experimental",
            d["unidad"],
            {
                "original": d,
                "archivo_original": ruta,
                "sha256_original": sha(archivos[ruta]),
                "revision_alcance": "experimental_snapshot_de_origen",
                "snapshot_id_origen": d["snapshot_id"],
                "adopcion_snapshot_actual": False,
            },
            grados=[d["grado"]],
            asignatura=d["asignatura"],
            unidad=d["unidad"],
            estado=d["estado"],
        )
    )
    return registros


def markdown(material: dict) -> str:
    """Exportación legible sin ejecutar HTML, código ni instrucciones de documentos fuente."""
    d = material["documento"]
    if d.get("version_contenido") == "preparacion-malla-final-2":
        from goes_science_kg.produccion.didactica.lectura import markdown_didactica

        return markdown_didactica(material)
    if d.get("version_contenido") == "preparacion-malla-final-1":
        from goes_science_kg.produccion.lectura import markdown_produccion

        return markdown_produccion(material)
    if material["tipo"] in {"guion_clase", "guion_unidad"}:
        from goes_science_kg.clases.lectura import markdown_clase, markdown_unidad

        return (markdown_clase if material["tipo"] == "guion_clase" else markdown_unidad)(material)
    cabecera = (
        f"# {material['titulo']}\n\nVersión: {material['version_curriculo']} · "
        f"Tipo: {material['tipo']} · Estado: {material['estado']}\n\n"
    )
    if material["tipo"] == "paquete_objetivo":
        p = d["propuesta"]
        campos = {
            "objetivo_propuesto": "Objetivo",
            "orientacion_didactica": "Orientación didáctica",
            "indicador_observable": "Indicador",
            "producto_evaluable": "Producto evaluable",
            "criterio_evaluacion": "Criterios de evaluación",
            "andamiaje": "Apoyos",
            "contexto_salvador": "Contexto propuesto",
            "seguridad": "Seguridad",
        }
        texto = cabecera + d["limite_biblioteca"] + "\n\n"
        for campo, titulo in campos.items():
            texto += f"## {titulo}\n\n{p[campo]}\n\n"
        texto += "## Recursos condicionados\n\n" + "\n".join(f"- {r}" for r in p["recursos_condicionales"])
        texto += "\n\n## Evidencia y revisión\n\n"
        texto += json.dumps(
            {k: d[k] for k in ("snapshot_id", "original", "fragmentos", "revisiones", "alerta_original", "enmiendas")},
            ensure_ascii=False,
            indent=2,
        )
        return texto + "\n"
    return cabecera + "```json\n" + json.dumps(d, ensure_ascii=False, indent=2) + "\n```\n"
