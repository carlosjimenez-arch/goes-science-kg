"""Enriquecimiento inmutable de la biblioteca final; cada propuesta conserva sus anclas."""

from __future__ import annotations

import logging
from collections import Counter
from copy import deepcopy

from goes_science_kg.materiales.compilacion import serializar, sha
from goes_science_kg.produccion.didactica.catalogo import definiciones
from goes_science_kg.produccion.didactica.diseno import disenar

VERSION = "preparacion-malla-final-2"
LOGGER = logging.getLogger(__name__)
LIMITE = (
    "Diseño didáctico propuesto sobre las mallas finales: actividades documentadas, apoyos, criterios "
    "y transferencia. La integridad se verifica en código. Mantiene pendiente la revisión científica, "
    "curricular, psicopedagógica y adversarial de esta edición. No acredita desempeño observado ni "
    "eficacia, no hereda votos y no certifica seguridad de prácticas. Los códigos E/D/I son locales."
)


def enriquecer(registros, curriculo, reglas, *, sha_reglas, biblioteca_base, historicos=None, casos=None):
    fuentes = {s.id: s for s in curriculo.fuentes}
    filas = {f.id: f for f in curriculo.filas}
    catalogo = definiciones(curriculo)
    propuestas, indice = [], []
    for material in registros:
        if material["documento"].get("version_contenido") != "preparacion-malla-final-1":
            raise ValueError("Se requiere una base final sin enriquecer; no se aplican mejoras dos veces")
        r = deepcopy(material)
        d = r["documento"]
        d.update(
            version_contenido=VERSION,
            limite_biblioteca=LIMITE,
            biblioteca_base=biblioteca_base,
            estado_revision="propuesta_didactica_pendiente_revision",
        )
        r["estado"] = "diseno_didactico_pendiente_revision"
        if r["tipo"] == "paquete_objetivo":
            f = filas[r["fila_id"]]
            if d["original"] != f.model_dump(mode="json"):
                raise ValueError("La fila del paquete difiere del currículo íntegro")
            antecedente = None
            if historicos and (id_ := d["antecedente"].get("fila_id")):
                h = historicos.get(id_)
                if h is not None and h.get("objetivo_original") == f.procedimental and h.get("propuesta"):
                    p = h["propuesta"]
                    antecedente = {
                        "fila_id": id_,
                        "biblioteca_id": d["antecedente"]["biblioteca_id"],
                        "andamiaje": p["andamiaje"],
                        "contexto_salvador": p["contexto_salvador"],
                        "estado": "antecedente_textual_sin_revalidar_ni_adoptar",
                        "votos_trasladados": False,
                        "limite": "El objetivo coincide literalmente; el contexto completo cambió. "
                        "El apoyo se ofrece para contraste, no como validación de la edición final.",
                    }
            diseno = disenar(
                f,
                fuentes[f.fuente_id],
                catalogo,
                reglas,
                sha_reglas,
                curriculo.huella,
                d["alertas"],
                antecedente=antecedente,
                casos=casos,
            )
            d["didactica"] = diseno.model_dump(mode="json")
            indice.append(
                {
                    "fila_id": f.id,
                    "grado": f.grado,
                    "asignatura": f.asignatura_malla,
                    "unidad": f.unidad,
                    "objetivo": f.procedimental,
                    "codigos": sorted({t.codigo for t in diseno.tareas if t.definicion}),
                    "macrohabilidades": list(diseno.macrohabilidades),
                    "tareas": len(diseno.tareas),
                    "incidencias": len(diseno.incidencias),
                    "controles_cientificos": len(diseno.controles_cientificos),
                    "caso_resuelto_id": diseno.caso_resuelto["id"] if diseno.caso_resuelto else None,
                    "estado_revision": diseno.estado_revision,
                }
            )
        propuestas.append(r)
    por_fila = {r["fila_id"]: r for r in propuestas if r["tipo"] == "paquete_objetivo"}
    if set(por_fila) != set(filas):
        raise ValueError("El enriquecimiento requiere todas las filas, sin omisiones ni selección de resultados")
    for r in propuestas:
        if r["tipo"] != "paquete_unidad":
            continue
        d = r["documento"]
        ruta = [por_fila[f]["documento"]["didactica"] for f in d["filas_ids"]]
        habilidades = {}
        for f in ruta:
            for criterio in f["criterios"]:
                habilidades.setdefault(criterio["codigo"], []).append(
                    {
                        "fila_id": f["fila_id"],
                        "tarea_ids": criterio["tarea_ids"],
                        "evidencia_propuesta": criterio["evidencia_propuesta"],
                    }
                )
        d["didactica_unidad"] = {
            "ruta_por_habilidad": habilidades,
            "articulacion": "Elegir un fenómeno o problema de las tareas para conectar conceptos, "
            "representaciones, indagación y comunicación; conservar cada objetivo de la malla.",
            "progresion_propuesta": [
                "Diagnosticar las ideas y destrezas necesarias para cada nuevo contenido.",
                "Mostrar un ejemplo razonado y contrastarlo con un error o contraejemplo.",
                "Practicar con apoyo, retirarlo según la respuesta y observar una producción individual.",
                "Retomar el aprendizaje después y contrastar una variación del caso.",
            ],
            "regla": "Las apariciones del código son oportunidades declaradas, no progreso ni dominio observado. "
            "Un contenido nuevo puede requerir apoyo aunque ya se haya trabajado la misma habilidad.",
            "desempenos_observados": None,
            "filas_sin_tareas": [f["fila_id"] for f in ruta if not f["tareas"]],
            "casos_resueltos": [f["caso_resuelto"]["id"] for f in ruta if f["caso_resuelto"]],
            "estado_revision": "propuesta_didactica_pendiente_revision",
        }
    auditoria = auditar(propuestas, biblioteca_base)
    LOGGER.warning(
        "AMARILLO %s diseños y %s casos: integridad comprobable; revisión de contenido pendiente",
        len(filas),
        auditoria["despues"]["casos_resueltos"],
    )
    auditoria["huella_final"] = curriculo.huella
    documento_indice = {
        "version": "indice-didactico-1",
        "huella_curriculo": curriculo.huella,
        "catalogo_sha256": sha_reglas,
        "macrohabilidades": reglas["macrohabilidades"],
        "filas": sorted(indice, key=lambda f: f["fila_id"]),
        "limite": (
            "Índice documental de tareas y propuestas, sin atribuir habilidades aprendidas ni alineación validada."
        ),
    }
    return propuestas, auditoria, documento_indice, grafo(propuestas, catalogo)


def auditar(registros, biblioteca_base):
    filas = [r["documento"]["didactica"] for r in registros if r["tipo"] == "paquete_objetivo"]
    return {
        "version": "auditoria-didactica-1",
        "biblioteca_base": biblioteca_base,
        "critica": [
            "Las bases transcribían las fases y etiquetas sin un puente explícito a observables y retroalimentación.",
            "La coincidencia de un código de habilidad no prueba que la tarea realmente la exija.",
            "Los productos declarados no incluyen por sí solos criterios de logro ni evidencia de autonomía.",
            "La alternativa en papel no acredita el desempeño práctico de un objetivo instrumental.",
            "Las alertas científicas precisan contraste y correcciones explícitas, sin modificar originales.",
            "Contexto local y desempeño lector o cuantitativo necesitan apoyos diferenciados; no se presumen recursos.",
        ],
        "antes": {
            "paquetes_objetivo": len(filas),
            "disenos_didacticos_estructurados": 0,
            "criterios_de_microhabilidad": 0,
            "casos_resueltos": 0,
        },
        "despues": {
            "paquetes_objetivo": len(filas),
            "unidades": sum(r["tipo"] == "paquete_unidad" for r in registros),
            "disenos_didacticos_estructurados": len(filas),
            "tareas_con_ancla": sum(len(f["tareas"]) for f in filas),
            "criterios_de_microhabilidad": sum(len(f["criterios"]) for f in filas),
            "casos_resueltos": sum(f["caso_resuelto"] is not None for f in filas),
            "objetivos_sin_tareas": [f["fila_id"] for f in filas if not f["tareas"]],
            "incidencias": dict(Counter(a["codigo"] for f in filas for a in f["incidencias"])),
            "controles_cientificos_explicitos": sum(len(f["controles_cientificos"]) for f in filas),
            "por_codigo": dict(Counter(c["codigo"] for f in filas for c in f["criterios"])),
            "por_perfil_apoyo": dict(Counter(f["perfil_apoyo"]["tramo"] for f in filas)),
        },
        "invariantes": {
            "originales_sin_modificar": True,
            "votos_heredados": 0,
            "llamadas_vertex_nuevas": 0,
            "logros_observados": 0,
            "eficacia_medida": False,
            "alineaciones_acreditadas": 0,
            "revision_de_la_nueva_edicion": "pendiente",
        },
        "interpretacion": (
            "Son métricas de estructura y cobertura documental; no un aumento "
            "medido de calidad pedagógica o aprendizaje."
        ),
    }


def grafo(registros, catalogo):
    nodos, aristas = {}, []
    for definicion in catalogo.values():
        id_ = "MICRO:" + definicion.origen.fuente_id + ":" + definicion.codigo
        macro = "MACRO:" + definicion.macro_id
        nodos[id_] = {"id": id_, "tipo": "definicion_local", **definicion.model_dump(mode="json")}
        nodos[macro] = {"id": macro, "tipo": "macrohabilidad_de_diseno", "nombre": definicion.macro_id}
        aristas.append({"origen": id_, "destino": macro, "tipo": "ORGANIZADO_EN"})
    for r in registros:
        if r["tipo"] != "paquete_objetivo":
            continue
        f = r["documento"]["didactica"]
        nodos[r["id"]] = {"id": r["id"], "tipo": "objetivo_original", "grado": r["grados"][0]}
        for tarea in f["tareas"]:
            id_ = tarea["id"]
            nodos[id_] = {
                "id": id_,
                "tipo": "tarea_declarada",
                "actividad": tarea["actividad_literal"],
                "origen_documental": tarea["origen"],
                "fase": tarea["fase"],
            }
            aristas.append({"origen": r["id"], "destino": id_, "tipo": "PROPONE_PRACTICAR_CON"})
            if tarea["definicion"]:
                destino = "MICRO:" + tarea["definicion"]["origen"]["fuente_id"] + ":" + tarea["codigo"]
                aristas.append({"origen": id_, "destino": destino, "tipo": "DECLARA_CODIGO_LOCAL"})
        for criterio in f["criterios"]:
            id_ = "CRITERIO:" + sha(serializar([f["fila_id"], criterio["codigo"]]))
            nodos[id_] = {
                "id": id_,
                "tipo": "criterio_propuesto",
                "codigo": criterio["codigo"],
                "criterios": criterio["criterios_observables"],
                "desempeno_observado": None,
            }
            for tarea in criterio["tarea_ids"]:
                aristas.append({"origen": tarea, "destino": id_, "tipo": "PROPONE_EVALUAR_CON"})
    if any(a["origen"] not in nodos or a["destino"] not in nodos for a in aristas):
        raise ValueError("El grafo didáctico tiene relaciones sin extremo")
    return {
        "version": "grafo-didactico-1",
        "nodos": sorted(nodos.values(), key=lambda n: n["id"]),
        "aristas": sorted(aristas, key=lambda a: (a["origen"], a["destino"], a["tipo"])),
        "limite": "Grafo documental de propuestas; no contiene prerrequisitos acreditados ni dominio observado.",
    }
