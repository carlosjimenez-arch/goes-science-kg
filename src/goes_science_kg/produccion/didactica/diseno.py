"""Diseño conectado a consignas reales: apoyos, evidencia, criterios y transferencia."""

from __future__ import annotations

import re
from collections import defaultdict

from goes_science_kg.produccion.didactica.casos import caso_para
from goes_science_kg.produccion.didactica.catalogo import extraer_tareas, perfil
from goes_science_kg.produccion.didactica.contratos import CriterioHabilidad, DisenoDidactico

CORRECCIONES = {
    "LOCAL:alerta_v4_base_c": (
        "En los ácidos nucleicos, C corresponde a citosina. Citocina no es el nombre de esa base.",
        "nhgri_citosina",
    ),
    "LOCAL:alerta_v4_biomoleculas_polimeros": (
        "Las biomoléculas incluyen moléculas pequeñas y macromoléculas. La glucosa es un monosacárido; "
        "el almidón es un polisacárido. No todas las biomoléculas son polímeros.",
        "openstax_carbohidratos",
    ),
    "V4_FISICA10_PENDIENTE_RESORTE": (
        "Para F = kx en el régimen elástico lineal, una gráfica x frente a F tiene pendiente 1/k, "
        "en m/N. Una gráfica F frente a x tiene pendiente k, en N/m. Identificar ejes antes de interpretar.",
        "openstax_resorte",
    ),
    "V4_QUIMICA10_DISOLUCION_EVIDENCIAS": (
        "Una disolución puede intercambiar energía; una variación de temperatura por sí sola no "
        "demuestra una reacción concreta ni identifica sustancias nuevas. Se requieren controles y "
        "evidencia pertinente. No ejecutar estaciones sólo por estar rotuladas como seguras en la malla.",
        "openstax_disolucion",
    ),
}
PRACTICA = re.compile(
    r"^\s*(?:\d+(?:\.\d+)*\.?\s*)?(?:experimentaci[oó]n|manipulaci[oó]n|medici[oó]n|calibraci[oó]n|"
    r"construcci[oó]n y calibraci[oó]n|construcci[oó]n de (?:un |una )?instrumento)",
    re.I,
)


def disenar(fila, fuente, catalogo, reglas, catalogo_sha, huella_curriculo, alertas, *, antecedente=None, casos=None):
    tareas, incidencias = extraer_tareas(fila, fuente, catalogo)
    por_codigo = defaultdict(list)
    for tarea in tareas:
        if tarea.definicion is not None and tarea.codigo in reglas["habilidades"]:
            por_codigo[tarea.codigo].append(tarea)
        elif tarea.definicion is not None:
            incidencias.append({"codigo": "HABILIDAD_SIN_DISENO", "habilidad": tarea.codigo})
    criterios = []
    for codigo, items in sorted(por_codigo.items()):
        regla = reglas["habilidades"][codigo]
        criterios.append(
            CriterioHabilidad(
                codigo=codigo,
                tarea_ids=tuple(t.id for t in items),
                evidencia_propuesta=regla["evidencia"],
                criterios_observables=tuple(regla["criterios"]),
                retroalimentacion=regla["retroalimentacion"],
                error_a_indagar=regla["error"],
                apoyo=regla["apoyo"],
                retirada_del_apoyo=regla["retirada"],
                transferencia=regla["transferencia"],
            )
        )
    controles = []
    for alerta in alertas:
        id_ = alerta["codigo"].removeprefix("ANTECEDENTE_CIENTIFICO_PERSISTENTE:")
        if id_ in CORRECCIONES:
            correccion, referencia = CORRECCIONES[id_]
            controles.append(
                {
                    "alerta_original": alerta,
                    "nota_docente_propuesta": correccion,
                    "referencia_id": referencia,
                    "tratamiento": "Original intacto; corrección derivada explícita, sin voto nuevo de especialistas.",
                }
            )
    if not tareas:
        incidencias.append(
            {"codigo": "SIN_TAREAS_TRAZABLES", "descripcion": "No se fabrican fases ni consignas faltantes."}
        )
    if not fila.indicadores_logro or not fila.evidencia_aprendizaje:
        incidencias.append(
            {
                "codigo": "EVALUACION_ORIGINAL_INCOMPLETA",
                "descripcion": "Falta indicador o evidencia original; el diseño no lo oculta ni lo acredita.",
            }
        )
    apoyo = perfil(fila.grado)
    focos = list(dict.fromkeys(t.codigo for t in tareas if t.fase == "indagar" and t.definicion))
    fases = {k: v.texto for k, v in fila.fases.items() if v.presente_en_hoja}
    practica = bool(PRACTICA.search(fila.procedimental))
    return DisenoDidactico(
        fila_id=fila.id,
        catalogo_sha256=catalogo_sha,
        objetivo_original=fila.procedimental,
        indicador_original=fila.indicadores_logro,
        producto_original=fila.evidencia_aprendizaje,
        perfil_apoyo=apoyo,
        tareas=tareas,
        criterios=tuple(criterios),
        macrohabilidades=tuple(sorted({t.definicion.macro_id for t in tareas if t.definicion})),
        transposicion={
            "intencion": "Conectar conocimiento del fenómeno, representaciones y evidencia del desempeño.",
            "contenido_y_subcontenido_originales": [fila.contenido, fila.subcontenido],
            "nucleo_conceptual_declarado": fila.dominio_clave,
            "nucleo_estado": "declarado_por_la_malla; aplicar notas científicas antes de usarlo como explicación",
            "puente_representacional": apoyo["representacion"],
            "activacion": {
                "consigna_original": fases.get("explorar", ""),
                "uso": "Recoger una respuesta individual inicial y su razón; no anunciar todavía la conclusión.",
            },
            "articulacion": [
                "Hacer visible qué se intenta explicar o decidir y qué evidencia se necesitaría.",
                "Modelar una relación entre representación y fenómeno sin ocultar sus límites.",
                "Pedir una producción individual y usar los criterios para decidir el apoyo siguiente.",
            ],
            "vocabulario": "Elegir términos indispensables de este contenido; contrastar uso cotidiano y científico "
            "con ejemplo y contraejemplo. No exigir definiciones de memoria como única evidencia.",
            "focos_de_la_indagacion_declarados": focos,
            "focos_limite": "Proceden de la fase Indagar; no son una jerarquía validada de habilidades "
            "ni omiten las otras tareas.",
            "rubrica": reglas["rubrica_comun"],
            "apoyo_contextual_antecedente": antecedente,
        },
        aplicacion={
            "tarea_de_transferencia_original": fases.get("reforzar", ""),
            "variacion_cercana": "Cambiar un objeto, una representación o un dato del caso conservando "
            "el concepto y el criterio; pedir justificar qué se conserva.",
            "contraste": "Presentar una explicación o inferencia alternativa; localizar el dato o condición "
            "que permitiría distinguirlas, con el apoyo adecuado al grado.",
            "extension_condicional": "Proponer otra situación del mismo contenido y explicar por qué el modelo "
            "sirve o deja de servir; elegir una sola extensión si la carga resulta excesiva.",
            "criterio": "La transferencia exige conservar el razonamiento en la variación, "
            "no sólo cambiar nombres de lugares.",
        },
        recuperacion={
            "sin_copiar": "En una revisión posterior, resolver de nuevo una tarea del objetivo "
            "sin mirar la respuesta y explicar la razón.",
            "comparacion": "Contrastar con evidencia o clave disponible y corregir una relación concreta; "
            "no sólo marcar correcto o incorrecto.",
            "espaciado": "Planificar una revisión diferida según horario y respuesta observada; "
            "no se impone un intervalo universal.",
            "estado": "actividad_propuesta_sin_resultados_observados",
        },
        contexto_y_factibilidad={
            "escenario": fila.contexto_pisa
            or "Usar las situaciones explícitas de las consignas; no se inventa una localidad ni datos observados.",
            "contexto_hipotetico": True,
            "preparacion_sin_internet": "Imprimir o dibujar las consignas y fuentes pertinentes; "
            "un dispositivo no sustituye el razonamiento evaluado.",
            "recurso_y_tiempo_reales": "no_constatados",
            "demanda_instrumental_detectada": practica,
            "deteccion_limite": "Marca literal de la acción inicial, no análisis exhaustivo de recursos o seguridad.",
            "si_faltan_instrumentos": "Puede prepararse o analizarse información en papel. La manipulación, medición, "
            "calibración o experimentación real permanece pendiente cuando el objetivo la exige.",
            "desempeno_practico_observado": None,
            "seguridad": "Verificar materiales, reactivos, concentraciones, supervisión y residuos "
            "antes de toda práctica. "
            "No cultivar muestras humanas o ambientales desconocidas, ingerir sustancias, usar tensión de red "
            "ni exponerse a riesgos naturales. La ausencia de alerta no certifica seguridad.",
        },
        controles_cientificos=tuple(controles),
        caso_resuelto=caso_para(fila, huella_curriculo, banco=casos),
        incidencias=tuple(incidencias),
    )
