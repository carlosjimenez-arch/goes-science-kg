"""Compilación exhaustiva de originales finales; no traslada propuestas ni votos."""

from __future__ import annotations

import logging
import re
import unicodedata
from collections import Counter
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from goes_science_kg.archivos import destino_generado
from goes_science_kg.curriculo.contratos import Curriculo
from goes_science_kg.materiales.compilacion import _entrada, markdown, serializar, sha

LOGGER = logging.getLogger(__name__)
VERSION = "preparacion-malla-final-1"
LIMITE = (
    "Paquete base construido de la malla final entregada el 26 de octubre de 2026. "
    "La integridad documental está comprobada. Pendiente de revisión científica, curricular, "
    "psicopedagógica y adversarial sobre esta edición; no hereda votos ni propuestas anteriores. "
    "No es un guion de clase ni acredita aprobación institucional. Los códigos PISA, TIMSS, MEN "
    "y DigComp son declaraciones de la malla, sin equivalencia ni alineación externa acreditada."
)


def _normalizar(texto):
    return " ".join(unicodedata.normalize("NFKC", str(texto)).casefold().split())


def _clave(fila, fuentes):
    return fuentes[fila.fuente_id].archivo, fila.hoja, fila.fila


def _contenido(fila):
    d = fila.model_dump(mode="json", exclude={"id", "fuente_id", "celdas", "version"})
    for fase in d["fases"].values():
        fase.pop("coordenadas")
    return d


def comparar(final: Curriculo, anterior: Curriculo) -> dict:
    """Compara localizadores exactos y valores lógicos; no supone equivalencias por similitud."""
    nuevas = {s.id: s for s in final.fuentes}
    viejas = {s.id: s for s in anterior.fuentes}
    por_clave = {_clave(f, viejas): f for f in anterior.filas}
    cambios = []
    for f in final.filas:
        previa = por_clave.get(_clave(f, nuevas))
        a, b = _contenido(previa) if previa else {}, _contenido(f)
        campos = [k for k in b if a.get(k) != b[k]]
        cambios.append(
            {
                "fila_id": f.id,
                "archivo": nuevas[f.fuente_id].archivo,
                "hoja": f.hoja,
                "fila": f.fila,
                "grado": f.grado,
                "asignatura": f.asignatura_malla,
                "unidad": f.unidad,
                "antecedente_localizador": previa.id if previa else None,
                "objetivo_identico": previa is not None and previa.procedimental == f.procedimental,
                "campos_modificados": campos,
                "contenido_logico_identico": previa is not None and not campos,
                "revision_heredada": False,
            }
        )
    actuales = {_clave(f, nuevas) for f in final.filas}
    return {
        "version": "comparacion-mallas-finales-1",
        "huella_final": final.huella,
        "huella_anterior": anterior.huella,
        "filas_finales": len(final.filas),
        "filas_anteriores": len(anterior.filas),
        "unidades_finales": len(final.agrupaciones),
        "objetivos_identicos": sum(c["objetivo_identico"] for c in cambios),
        "filas_con_cambios_logicos": sum(bool(c["campos_modificados"]) for c in cambios),
        "campos_modificados": dict(Counter(k for c in cambios for k in c["campos_modificados"])),
        "filas_retiradas": [f.id for f in anterior.filas if _clave(f, viejas) not in actuales],
        "filas": cambios,
        "limite": "Coincidencia de archivo, hoja y fila no acredita equivalencia ni conserva revisiones.",
    }


def alertas_de_fila(fila, fuente, antecedentes):
    """Reubica anclas históricas sólo por coincidencia literal en el archivo y hoja indicados."""
    alertas = []
    for a in antecedentes:
        origen = a["fuente"]
        ancla = _normalizar(a.get("ancla_original", ""))
        if (
            a.get("estado_verificacion") != "confirmada"
            or not ancla
            or Path(origen["archivo"]).name != fuente.archivo
            or origen["hoja"] != fila.hoja
        ):
            continue
        celdas = [c.coordenada for c in fila.celdas if ancla in _normalizar(c.valor or "")]
        if celdas:
            alertas.append(
                {
                    "codigo": "ANTECEDENTE_CIENTIFICO_PERSISTENTE:" + a["id"],
                    "descripcion": a["explicacion"],
                    "celdas_finales": celdas,
                    "sha256_final": fuente.sha256,
                    "contraste_historico": a.get("url_primaria_contraste", a.get("contraste_primario")),
                    "metodo": "Ancla literal localizada nuevamente; no constituye una nueva revisión externa.",
                }
            )
    sueltas = [c for c in fila.celdas if c.campo is None and c.valor is not None and str(c.valor).strip()]
    if sueltas:
        alertas.append(
            {
                "codigo": "CELDAS_SIN_ROL",
                "descripcion": "Hay contenido sin encabezado lógico. Se conserva íntegro, sin asignarle una fase.",
                "celdas_finales": [c.coordenada for c in sueltas],
            }
        )
    for nombre, fase in fila.fases.items():
        if fase.presente_en_hoja and not fase.texto:
            alertas.append(
                {
                    "codigo": "FASE_VACIA:" + nombre,
                    "descripcion": f"La fase {nombre} está declarada, pero su celda no contiene texto.",
                    "celdas_finales": list(fase.coordenadas),
                }
            )
    return alertas


def compilar(final: Curriculo, anterior: Curriculo, antecedentes: list[dict], *, biblioteca_anterior: str):
    fuentes = {s.id: s for s in final.fuentes}
    comparacion = comparar(final, anterior)
    cambios = {r["fila_id"]: r for r in comparacion["filas"]}
    registros = []
    comunes = {
        "version_contenido": VERSION,
        "snapshot_id": final.huella,
        "edicion": "produccion-final-20261026",
        "limite_biblioteca": LIMITE,
        "revision_alcance": "integridad_documental_exclusivamente",
        "estado_revision": "pendiente_revision_nueva_edicion",
        "revisiones": [],
        "propuesta": None,
        "guion_cronometrado": False,
        "duracion_minutos": None,
    }
    for f in final.filas:
        fuente = fuentes[f.fuente_id]
        incidencias = alertas_de_fila(f, fuente, antecedentes)
        previo = cambios[f.id]["antecedente_localizador"]
        documento = comunes | {
            "original": f.model_dump(mode="json"),
            "fuente_original": fuente.model_dump(mode="json"),
            "alertas": incidencias,
            "celdas_sin_rol": [c.model_dump(mode="json") for c in f.celdas if c.campo is None and c.valor is not None],
            "comparacion": cambios[f.id],
            "antecedente": {
                "biblioteca_id": biblioteca_anterior,
                "fila_id": previo,
                "uso": "Consulta histórica separada; contenido, clasificaciones y votos sin trasladar.",
            },
        }
        registros.append(
            _entrada(
                f.id,
                "V4",
                "paquete_objetivo",
                f.procedimental,
                documento,
                grados=[f.grado],
                asignatura=f.asignatura_malla,
                unidad=f.unidad,
                fila_id=f.id,
                estado="base_final_con_incidencias" if incidencias else "base_final_pendiente_revision",
            )
        )
    por_id = {r["id"]: r for r in registros}
    filas = {f.id: f for f in final.filas}
    for grupo in final.agrupaciones:
        orden = sorted((filas[id_] for id_ in grupo.filas), key=lambda f: (f.hoja, f.fila))
        registros.append(
            _entrada(
                "UNIDAD-FINAL:" + sha(serializar([final.huella, grupo.model_dump(mode="json")])),
                "V4",
                "paquete_unidad",
                grupo.unidad,
                comunes
                | {
                    "filas_ids": [f.id for f in orden],
                    "objetivos": [{"id": f.id, "objetivo": f.procedimental} for f in orden],
                    "alertas": [a | {"fila_id": f.id} for f in orden for a in por_id[f.id]["documento"]["alertas"]],
                    "orden": "Documental; no acredita progresión pedagógica ni prerrequisitos.",
                },
                grados=[grupo.grado],
                asignatura=grupo.asignatura_malla,
                unidad=grupo.unidad,
                estado="base_final_pendiente_revision",
            )
        )
    informe = {
        **comparacion,
        "paquetes": len(registros),
        "por_tipo": dict(Counter(r["tipo"] for r in registros)),
        "por_estado": dict(Counter(r["estado"] for r in registros)),
        "incidencias": dict(
            Counter(
                a["codigo"] for r in registros if r["tipo"] == "paquete_objetivo" for a in r["documento"]["alertas"]
            )
        ),
        "llamadas_vertex": 0,
        "revisiones_anteriores_heredadas": 0,
        "filas_sin_paquete": sorted(set(filas) - por_id.keys()),
    }
    LOGGER.warning("AMARILLO %s paquetes finales: revisión de contenido pendiente", len(registros))
    return registros, informe


def exportar(
    registros,
    originales,
    informe,
    destino: Path,
    *,
    version=VERSION,
    estado_revision="pendiente_revision_nueva_edicion",
    archivos_comunes=None,
):
    """ZIP reproducible por grado/asignatura con JSON, Markdown, insumos y comprobantes SHA."""
    destino_generado(destino / "indice.json")
    if destino.exists() or destino.is_symlink():
        raise ValueError("Las exportaciones requieren un directorio nuevo")
    for nombre, raw in (archivos_comunes or {}).items():
        if (
            not nombre.startswith("didactica/")
            or any(p in {"", ".", ".."} for p in nombre.split("/"))
            or "\\" in nombre
            or not isinstance(raw, bytes)
        ):
            raise ValueError("Los archivos comunes requieren bytes y rutas propias bajo didactica/")
    destino.mkdir(parents=True)
    grupos = sorted({(r["grados"][0], r["asignatura"]) for r in registros})
    inventario = []
    for grado, asignatura in grupos:
        seleccion = [r for r in registros if r["grados"] == [grado] and r["asignatura"] == asignatura]
        archivos = {"informe.json": serializar(informe), **(archivos_comunes or {})}
        if version == "preparacion-malla-final-3":
            from goes_science_kg.produccion.revision_docente.lectura import indice_grupo

            archivos["LEEME.md"] = indice_grupo(seleccion).encode()
        usados = set()
        for r in seleccion:
            nombre = sha(r["id"].encode())
            archivos[f"{r['tipo']}/{nombre}.json"] = serializar(r)
            archivos[f"{r['tipo']}/{nombre}.md"] = markdown(r).encode()
            fuente = r["documento"].get("fuente_original")
            if fuente:
                usados.add(fuente["archivo_local"])
        for ruta in sorted(usados):
            archivos[ruta] = originales[ruta]
        archivos["manifest.json"] = serializar(
            {
                "version": version,
                "grado": grado,
                "asignatura": asignatura,
                "paquetes": len(seleccion),
                "snapshot_id": informe["huella_final"],
                "estado_revision": estado_revision,
                "archivos": {p: {"sha256": sha(b), "bytes": len(b)} for p, b in sorted(archivos.items())},
            }
        )
        etiqueta = unicodedata.normalize("NFKD", asignatura).encode("ascii", "ignore").decode().lower()
        nombre_zip = f"grado-{grado:02d}-{re.sub('[^a-z0-9]+', '-', etiqueta)}.zip"
        with ZipFile(destino / nombre_zip, "x", compression=ZIP_DEFLATED) as z:
            for nombre, raw in sorted(archivos.items()):
                info = ZipInfo(nombre, date_time=(2026, 10, 26, 0, 0, 0))
                info.compress_type = ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                z.writestr(info, raw)
        raw = (destino / nombre_zip).read_bytes()
        inventario.append(
            {
                "archivo": nombre_zip,
                "grado": grado,
                "asignatura": asignatura,
                "paquetes": len(seleccion),
                "sha256": sha(raw),
                "bytes": len(raw),
            }
        )
    (destino / "indice.json").write_bytes(serializar({"paquetes": inventario}))
    return inventario
