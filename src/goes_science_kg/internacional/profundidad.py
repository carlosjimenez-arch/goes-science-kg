"""Profundidad (demanda cognitiva) y prácticas científicas: malla V2 de 9.°–11.° frente al núcleo de los países
(spec 11, puntos 5 y 6).

Demanda: la V2 no la declara y la de los países la puso Gemini, así que comparar esas dos fuentes mezclaría
métodos. Se usa el MISMO clasificador determinista en los dos lados: los verbos del enunciado (indicador de la V2,
paráfrasis en español del país) en la escala de TIMSS. Un enunciado con varios verbos toma la demanda más alta,
como un ítem de TIMSS. «Explicar» es aplicar en TIMSS, no razonar. Sin verbo reconocible: «sin_verbo».

Prácticas: las etiquetas `PRAC:` del etiquetado (mismo modelo y catálogo en los dos lados), en tres familias.
"""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict

from goes_science_kg import conceptos
from goes_science_kg.config import ruta
from goes_science_kg.internacional import etiquetar
from goes_science_kg.internacional.consenso import _cargar_etiquetas, ensenados, objetivos, paises

NIVELES = ("recordar", "aplicar", "razonar")
_LEMAS = {
    "recordar": "identificar reconocer nombrar enumerar listar definir describir mencionar conocer indicar señalar "
                "enunciar recordar citar ubicar localizar",
    "aplicar": "calcular aplicar usar utilizar resolver determinar medir clasificar comparar relacionar representar "
               "interpretar graficar realizar convertir balancear construir elaborar distinguir diferenciar estimar "
               "demostrar ilustrar asociar organizar ordenar registrar preparar seleccionar observar experimentar "
               "simular explicar",
    "razonar": "analizar evaluar argumentar justificar diseñar investigar predecir deducir inferir formular proponer "
               "modelar modelizar valorar discutir plantear sintetizar criticar indagar integrar generalizar debatir "
               "fundamentar concluir",
}
_IRREGULARES = {"resuelve": "resolver", "resuelven": "resolver", "mide": "medir", "miden": "medir",
                "construye": "construir", "construyen": "construir", "predice": "predecir", "predicen": "predecir",
                "infiere": "inferir", "infieren": "inferir", "propone": "proponer", "proponen": "proponer",
                "concluye": "concluir", "concluyen": "concluir", "distingue": "distinguir", "distinguen": "distinguir"}


def _formas() -> dict[str, str]:
    """Forma verbal → nivel. Infinitivo y presente de 3.ª persona (singular y plural), que es como se redactan los
    indicadores de la V2 y las paráfrasis de los países."""
    formas: dict[str, str] = {}
    for nivel, lemas in _LEMAS.items():
        for lema in lemas.split():
            raiz, fin = lema[:-2], lema[-2:]
            vocal = "a" if fin == "ar" else "e"
            for f in (lema, raiz + vocal, raiz + vocal + "n"):
                formas[f] = nivel
    for forma, lema in _IRREGULARES.items():
        formas[forma] = next(n for n, ls in _LEMAS.items() if lema in ls.split())
    return formas


_FORMAS = _formas()


def demanda(texto: str) -> str:
    """Nivel más alto entre los verbos del enunciado; «sin_verbo» si no reconoce ninguno."""
    niveles = {_FORMAS[p] for p in re.findall(r"[a-záéíóúñü]+", texto.lower()) if p in _FORMAS}
    return next((n for n in reversed(NIVELES) if n in niveles), "sin_verbo")


FAMILIAS = {
    "indagacion": ["formular-preguntas-investigables", "formular-hipotesis-y-predicciones",
                   "planificar-investigaciones", "controlar-variables", "medir-con-instrumentos",
                   "repetir-mediciones-y-estimar-error",
                   "observar-y-registrar", "analizar-datos-con-estadistica", "interpretar-datos-y-concluir",
                   "representar-datos", "evaluar-disenos-de-investigacion"],
    "modelacion": ["desarrollar-y-usar-modelos", "evaluar-modelos-y-limitaciones", "transformar-representaciones",
                   "usar-matematicas-en-ciencias", "usar-pensamiento-computacional-y-simulaciones"],
    "argumentacion": ["argumentar-con-evidencia", "construir-explicaciones-con-evidencia",
                      "evaluar-afirmaciones-y-argumentos", "evaluar-fuentes-de-informacion",
                      "distinguir-correlacion-y-causalidad", "distinguir-observacion-e-inferencia"],
}
FAMILIA_DE = {f"PRAC:{p}": fam for fam, ps in FAMILIAS.items() for p in ps}


def _asignatura_tema(t: dict, e: dict, voc: dict) -> str | None:
    """Asignatura de un tema de la V2. En 9.° («ciencias») decide el concepto principal."""
    if t["asignatura"] != "ciencias":
        return t["asignatura"]
    for c in e["principales"] + e["secundarios"]:
        if c in voc:
            a = voc[c]["asignatura"]
            return "tierra_espacio" if a == "ciencias_tierra_espacio" else a
    return None


def _unidades() -> dict[str, dict[str, list[dict]]]:
    """asignatura → {'SV': [enunciados], '<país>': [enunciados del núcleo de 9.°–11.°]} con texto y prácticas."""
    from goes_science_kg.ingesta.mallas import extraer

    voc = conceptos.vocabulario()
    etq_sv: dict[str, dict] = {}
    # Solo el etiquetado con el vocabulario de la asignatura, como el de los países (las prácticas no cambian).
    for f in sorted(ruta(etiquetar.DIR).glob("malla_v2_*.json")):
        if f.stem.endswith("_completo"):
            continue
        etq_sv.update(json.loads(f.read_text(encoding="utf-8")))
    salida: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    for t in extraer("mallas_v2"):
        if t.grado < 9 or t.id not in etq_sv:
            continue
        t = t.dict()
        asig = _asignatura_tema(t, etq_sv[t["id"]], voc)
        if asig:
            salida[asig]["SV"].append({"id": t["id"], "texto": t["indicador"] or t["procedimental"],
                                       "practicas": etq_sv[t["id"]]["practicas"]})
    etq = _cargar_etiquetas("pais_")
    for o in objetivos():
        if o["nivel"] != "nucleo" or o["grado_sv_max"] < 9 or o["id"] not in etq or not o["asignatura"]:
            continue
        if not ensenados(etq[o["id"]]) and not etq[o["id"]]["practicas"]:
            continue
        salida[o["asignatura"]][o["pais"]].append({"id": o["id"], "texto": o["texto"], "demanda_ia": o["demanda"],
                                                   "practicas": etq[o["id"]]["practicas"]})
    return salida


def analizar() -> dict:
    """Por asignatura: distribución de demanda y presencia de familias y prácticas, V2 frente a cada país."""
    unidades = _unidades()
    resultado = {}
    acuerdo, total = 0, 0
    for asig, grupos in sorted(unidades.items()):
        filas = {}
        for quien, items in sorted(grupos.items()):
            dem = Counter(demanda(i["texto"]) for i in items)
            fam = Counter(f for i in items
                          for f in {FAMILIA_DE.get(p, "naturaleza_y_contexto") for p in i["practicas"]})
            filas[quien] = {"n": len(items), "demanda": dict(sorted(dem.items())),
                            "familias": dict(sorted(fam.items())),
                            "practicas": sorted({p for i in items for p in i["practicas"]}),
                            "con_practica": sum(bool(i["practicas"]) for i in items)}
            for i in items:
                if i.get("demanda_ia") and (d := demanda(i["texto"])) != "sin_verbo":
                    total += 1
                    acuerdo += d == i["demanda_ia"]
        paises_n = [p for p in paises() if p in filas]
        # Prácticas que exige el núcleo de ≥ 5 países en la asignatura y que la V2 no etiqueta en 9.°–11.°.
        cuenta = Counter(p for q in paises_n for p in filas[q]["practicas"])
        sv_prac = set(filas.get("SV", {}).get("practicas", []))
        resultado[asig] = {"filas": filas, "paises": paises_n,
                           "practicas_ausentes": sorted(p for p, n in cuenta.items() if n >= 5 and p not in sv_prac),
                           "cuenta_practicas": dict(sorted(cuenta.items()))}
    return {"asignaturas": resultado,
            "acuerdo_con_ia": {"coinciden": acuerdo, "total": total, "proporcion": round(acuerdo / max(1, total), 3)}}
