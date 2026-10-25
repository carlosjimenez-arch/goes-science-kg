"""Reconstruye la entrega desde los dictámenes exactos, sin heredar etiquetas de aprobación."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from goes_science_kg.clases.contratos import GuionClase
from goes_science_kg.clases.preparacion import leer_preparacion, validar_importacion
from goes_science_kg.clases.proveedor import MODELOS
from goes_science_kg.clases.validacion import certificar_resultado
from goes_science_kg.materiales.compilacion import _entrada, serializar, sha
from goes_science_kg.motor.contratos import Evidencia

LICENCIA = (
    "Adaptación didáctica en español basada en OpenStax / Rice University, CC BY-NC-SA 4.0 "
    "(https://creativecommons.org/licenses/by-nc-sa/4.0/). Se han creado actividades y explicaciones "
    "para el contexto salvadoreño mediante IA y revisión automática. Se conservan las atribuciones "
    "y licencias de cada fuente; no se atribuye su aprobación a OpenStax. Esta licencia se refiere "
    "a las adaptaciones de Ciencias, no al código ni a los documentos curriculares originales del MINED. "
    "Los datos cronológicos complementarios de ICS conservan su atribución y licencia CC BY 4.0; "
    "el texto complementario USDA conserva su atribución y declaración de dominio público."
)


def leer_propio(base: Path, nombre: str) -> Path:
    p = base / nombre
    if p.is_symlink() or any(t.is_symlink() for t in p.parents) or not p.resolve().is_relative_to(base.resolve()):
        raise ValueError("El expediente requiere archivos propios dentro de su repositorio")
    if not p.is_file():
        raise ValueError("Falta un archivo regular del expediente")
    return p


def cargar_revisiones_directas(base: Path, rutas) -> dict:
    """Load direct-review files, keyed by objective, with the exact script hash each verdict applies to."""
    revisiones = {}
    for ruta in rutas:
        raw = leer_propio(base, ruta).read_bytes()
        documento = json.loads(raw)
        for r in documento["revisiones"]:
            if r["veredicto"] not in {"liberable", "bloquear"} or r["fila_id"] in revisiones:
                raise ValueError("Revisión directa con veredicto desconocido o duplicada")
            revisiones[r["fila_id"]] = r | {"expediente": ruta, "expediente_sha256": sha(raw)}
    return revisiones


def _pendiente_verificado(base: Path, id_: str, declarado: dict, revisiones: dict) -> dict:
    # Un objetivo sin guion conserva su último resultado real; no basta con declararlo.
    expediente = declarado.get("expediente") or {}
    raw = leer_propio(base, expediente.get("resultado", "")).read_bytes()
    final = json.loads(raw)["filas"].get(id_)
    if declarado.get("estado") == "bloqueado_revision_directa":
        revision = revisiones.get(id_) or {}
        if (
            not final
            or final["estado"] != "respaldado_automaticamente"
            or revision.get("veredicto") != "bloquear"
            or revision.get("guion_sha256") != sha(serializar(final["guion"]))
        ):
            raise ValueError("Un bloqueo por revisión directa debe corresponder al guion exacto revisado")
    elif not final or final["estado"] == "respaldado_automaticamente" or final["estado"] != declarado.get("estado"):
        raise ValueError("Un objetivo sin guion debe apuntar a su último resultado negativo real")
    if not isinstance(declarado.get("motivo"), str) or len(declarado["motivo"].strip()) < 20:
        raise ValueError("Cada objetivo sin guion declara un motivo concreto")
    return {
        "fila_id": id_,
        "estado": declarado["estado"],
        "motivo": declarado["motivo"],
        "expediente": {"preparacion": expediente["preparacion"], "resultado": expediente["resultado"]},
        "resultado_sha256": sha(raw),
    }


def compilar(
    base: Path,
    biblioteca,
    corpus,
    seleccion: dict,
    *,
    registro,
    pendientes: dict | None = None,
    revisiones_directas: dict | None = None,
):
    """La selección explícita no permite publicar pendientes ni omitir objetivos del catálogo.

    `pendientes` declara objetivos sin guion liberado: no se publican como clases, cada uno conserva su último
    resultado negativo y su unidad lo indica. Selección y pendientes cubren exactamente el catálogo.
    """
    from goes_science_kg.clases.auditoria import verificar_trazas

    objetivos = []
    for offset in range(0, biblioteca.listar(tipo="paquete_objetivo", limite=1)["total"], 200):
        objetivos.extend(biblioteca.listar(tipo="paquete_objetivo", limite=200, offset=offset)["materiales"])
    esperados = {r["id"] for r in objetivos}
    pendientes = pendientes or {}
    revisiones_directas = revisiones_directas or {}
    if set(seleccion) & set(pendientes) or set(seleccion) | set(pendientes) != esperados:
        raise ValueError("La selección no cubre exactamente todos los objetivos de Ciencias de la biblioteca")
    from goes_science_kg.clases.revision_contenido import validar_seleccion

    validar_seleccion(base, seleccion, obligatoria=len(esperados) == 1013, excluidos=frozenset(pendientes))
    originales, resultados, preparaciones, auditorias = {}, {}, {}, {}
    registros, unidades, contenidos = [], defaultdict(list), set()
    sin_guion = defaultdict(list)
    for ficha in objetivos:
        id_ = ficha["id"]
        if id_ in pendientes:
            clave = (ficha["grados"][0], ficha["asignatura"], ficha["unidad"])
            verificado = _pendiente_verificado(base, id_, pendientes[id_], revisiones_directas)
            sin_guion[clave].append(verificado | {"titulo": ficha["titulo"]})
            continue
        ref = seleccion[id_]
        ruta_p, ruta_r = ref["preparacion"], ref["resultado"]
        if ruta_p not in preparaciones:
            pp = leer_propio(base, ruta_p)
            preparaciones[ruta_p] = leer_preparacion(pp)
            originales[ruta_p] = pp.read_bytes()
            from goes_science_kg.clases.insumos import archivos_insumos

            originales.update(archivos_insumos(base, preparaciones[ruta_p]))
        p = preparaciones[ruta_p]
        validar_importacion(p, base)
        from goes_science_kg.clases.editorial import archivos as archivos_editoriales

        originales.update(archivos_editoriales(base, p))
        huellas = getattr(corpus, "huellas_compatibles", {corpus.huella})
        if p["biblioteca_id"] != biblioteca.manifest["id"] or p["corpus_sha256"] not in huellas:
            raise ValueError("La preparación no pertenece a la biblioteca y corpus solicitados")
        if ruta_r not in resultados:
            rr = leer_propio(base, ruta_r)
            r = json.loads(rr.read_bytes())
            certificar_resultado(r, p, MODELOS)
            auditoria = verificar_trazas(base, rr, p, r, registro)
            for traza in auditoria["trazas"]:
                raw_lector = registro.salida(traza["clave"]).encode()
                if sha(raw_lector) != traza["salida_sha256"]:
                    raise ValueError("La respuesta del lector cambió después de comprobarla")
                ruta_lector = traza["archivo_salida"]
                archivo_lector = base / ruta_lector
                if archivo_lector.exists():
                    if leer_propio(base, ruta_lector).read_bytes() != raw_lector:
                        raise ValueError("La copia de la respuesta del lector cambió")
                else:
                    archivo_lector.parent.mkdir(parents=True, exist_ok=True)
                    with archivo_lector.open("xb") as f:
                        f.write(raw_lector)
                originales[ruta_lector] = raw_lector
            raw_auditoria = serializar(auditoria)
            ruta_auditoria = "data/clases_v4/auditorias/" + sha(raw_auditoria) + ".json"
            archivo_auditoria = base / ruta_auditoria
            if archivo_auditoria.exists():
                if leer_propio(base, ruta_auditoria).read_bytes() != raw_auditoria:
                    raise ValueError("La auditoría existente corresponde a otro expediente")
            else:
                archivo_auditoria.parent.mkdir(parents=True, exist_ok=True)
                with archivo_auditoria.open("xb") as f:
                    f.write(raw_auditoria)
            originales[ruta_auditoria] = raw_auditoria
            auditorias[ruta_r] = ruta_auditoria
            resultados[ruta_r] = r
            originales[ruta_r] = rr.read_bytes()
        r = resultados[ruta_r]
        if r["preparacion_id"] != p["id"]:
            raise ValueError("El resultado y la preparación seleccionados no corresponden")
        final = r["filas"][id_]
        if final["estado"] != "respaldado_automaticamente":
            raise ValueError("No se libera una clase vetada o abstención como lista para impartir")
        g = GuionClase.model_validate(final["guion"])
        revision = revisiones_directas.get(id_)
        if revision and revision["guion_sha256"] != sha(serializar(final["guion"])):
            revision = None  # La revisión corresponde a otra versión del guion.
        if revision and revision["veredicto"] == "bloquear":
            raise ValueError("No se libera un guion bloqueado por revisión directa")
        revision_directa = (
            {
                "estado": "aprobada",
                "expediente": revision["expediente"],
                "expediente_sha256": revision["expediente_sha256"],
            }
            if revision
            else {"estado": "no_realizada"}
        )
        anterior = biblioteca.detalle(id_)["documento"]
        fila = next(f for f in p["filas"] if f["fila_id"] == id_)
        if g.objetivo != anterior["propuesta"]["objetivo_propuesto"] or p["snapshot_id"] != anterior["snapshot_id"]:
            raise ValueError("La clase no conserva el objetivo y snapshot de su fila original")
        # El título y objetivo no bastan para justificar cuerpos copiados entre objetivos.
        cuerpo = sha(
            serializar({k: v for k, v in final["guion"].items() if k not in {"fila_id", "titulo", "objetivo"}})
        )
        if cuerpo in contenidos:
            raise ValueError("Dos objetivos presentan un cuerpo didáctico íntegramente duplicado")
        contenidos.add(cuerpo)
        fuentes = [e for e in p["fuentes"] if e["id"] in fila["fuentes_cientificas_ids"]]
        for e in fuentes:
            corpus.verificar(Evidencia.model_validate(e))
        documento = {
            "version_contenido": "guion-clase-v4-1",
            "snapshot_id": p["snapshot_id"],
            "preparacion_id": p["id"],
            "corpus_cientifico_sha256": p["corpus_sha256"],
            "huella_entorno": r["huella_entorno"],
            "guion": final["guion"],
            "dictamenes": final["dictamenes"],
            "ronda_seleccionada": final["ronda_seleccionada"],
            "origen": fila["origen"],
            "alerta_original": anterior["alerta_original"],
            "enmiendas": anterior["enmiendas"],
            "ajuste_didactico_auditoria": fila.get("enmienda_didactica_auditoria"),
            "datos_contextuales": fila.get("datos_contextuales"),
            "fuentes_cientificas": fuentes,
            "licencia_adaptacion": LICENCIA
            + "".join(" " + a for a in sorted({e["fuente"]["aviso"] for e in fuentes if e["fuente"].get("aviso")})),
            "expediente": ref,
            "auditoria_revisiones": auditorias[ruta_r],
            "revision_alcance": "guion_exacto_cuatro_roles_ciegos",
            "revision_directa": revision_directa,
            "guion_cronometrado": True,
            "duracion_minutos": 60 * len(g.sesiones),
            "validado_en_aula": False,
            "aprobacion_institucional": False,
        }
        material_id = "CLASE-V4:" + sha(serializar([id_, p["id"], final["guion"]]))
        material = _entrada(
            material_id,
            "V4",
            "guion_clase",
            g.titulo,
            documento,
            grados=ficha["grados"],
            asignatura=ficha["asignatura"],
            unidad=ficha["unidad"],
            fila_id=id_,
            estado="respaldado_automaticamente",
        )
        registros.append(material)
        unidades[(ficha["grados"][0], ficha["asignatura"], ficha["unidad"])].append(material)
    for clave in set(sin_guion) - set(unidades):
        unidades[clave] = []
    for (grado, asignatura, unidad), clases in sorted(unidades.items()):
        faltan = sorted(sin_guion.get((grado, asignatura, unidad), []), key=lambda x: x["fila_id"])
        clases.sort(key=lambda c: (c["documento"]["origen"]["hoja"], c["documento"]["origen"]["fila"], c["fila_id"]))
        documento = {
            "version_contenido": "guion-unidad-v4-1",
            "snapshot_id": biblioteca.manifest["procedencia"]["snapshot_id"],
            "guiones": [
                {
                    "material_id": c["id"],
                    "fila_id": c["fila_id"],
                    "titulo": c["titulo"],
                    "objetivo": c["documento"]["guion"]["objetivo"],
                    "duracion_minutos": c["documento"]["duracion_minutos"],
                }
                for c in clases
            ],
            "orden": "documental; no secuencia pedagógica inferida ni carga horaria oficial",
            "licencia_adaptacion": LICENCIA,
        }
        if faltan:
            documento["completa"] = False
            documento["objetivos_sin_guion_liberado"] = faltan
        registros.append(
            _entrada(
                "CLASE-UNIDAD-V4:" + sha(serializar(documento)),
                "V4",
                "guion_unidad",
                unidad,
                documento,
                grados=[grado],
                asignatura=asignatura,
                unidad=unidad,
                estado="respaldado_automaticamente",
            )
        )
    # Se redistribuyen las fuentes con atribuciones y licencias, sin alterar sus bytes.
    originales["data/referencias_clases_2026/manifest.json"] = corpus.manifest_bytes
    for libro in corpus.manifest["libros"]:
        for ref in [libro["licencia"], libro["coleccion"], *libro["modulos"]]:
            originales["data/referencias_clases_2026/" + ref["ruta"]] = corpus._leer(ref)
    if hasattr(corpus, "originales_adicionales"):
        originales.update(corpus.originales_adicionales())
    # Preserva también rechazos, abstenciones y controles; nunca se presentan como clases liberadas.
    rutas = sorted((base / "data/clases_v4/ejecuciones").rglob("resultado_*.json"))
    rutas += sorted((base / "data/clases_v4/ejecuciones").rglob("protocolo.json"))
    rutas += sorted((base / "data/clases_v4/ejecuciones").rglob("preflight.json"))
    rutas += sorted((base / "data/clases_v4/protocolos").glob("*.json"))
    rutas += sorted((base / "data/clases_v4/protocolos").glob("*.zip"))
    rutas += sorted((base / "data/clases_v4/controles_pre_escalado").glob("*.json"))
    rutas += sorted((base / "data/clases_v4/auditoria_contenido").glob("*.json"))
    for carpeta in sorted((base / "data/clases_v4").glob("preparaciones*")):
        rutas += sorted(carpeta.glob("*.json"))
    for carpeta in sorted((base / "data/clases_v4").glob("contextos_*")):
        rutas += sorted(carpeta.rglob("*.json"))
    for carpeta in (base / "data/clases_v4/ejecuciones").glob("control_*"):
        rutas += sorted(carpeta.glob("*.json"))
    for archivo in rutas:
        nombre = archivo.relative_to(base).as_posix()
        originales[nombre] = leer_propio(base, nombre).read_bytes()
    return registros, originales
