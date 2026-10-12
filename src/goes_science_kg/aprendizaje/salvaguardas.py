"""Salvaguardas para estudiantes menores de edad (spec 13 y 14; dictamen del psicopedagogo del panel, 2026-10-12).

1. **Datos personales.** Antes de enviar una respuesta abierta a un modelo o de guardarla, `limpiar()` reemplaza
   correos, teléfonos, números de documento (DUI), direcciones web y frases como «me llamo …» por marcas neutras. No
   detecta todo (un nombre suelto, por ejemplo); por eso además el tutor nunca pide datos personales y el piloto revisa
   una muestra de respuestas.
2. **Señales de riesgo.** Si una respuesta sugiere que el estudiante está en riesgo (violencia, abuso, autolesión,
   acoso), `senales_de_riesgo()` la marca: no se envía al modelo, no se califica y va de inmediato al docente con el
   protocolo de la escuela. Es una lista de palabras: prioriza no dejar pasar un caso, aunque marque de más.
3. **Etiquetas.** El estudiante nunca ve etiquetas de diagnóstico («brecha», «hipótesis confirmada»), puntajes de
   dominio ni comparaciones con otros: `texto_para_estudiante()` las retira de lo que se le muestra.
"""

from __future__ import annotations

import re
import unicodedata

_PATRONES = [
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"), "[correo]"),
    (re.compile(r"https?://\S+|www\.\S+"), "[enlace]"),
    (re.compile(r"\b\d{8}-\d\b"), "[documento]"),                       # DUI salvadoreño: 8 dígitos y verificador
    (re.compile(r"(?<!\d)(?:\+?503[\s-]?)?[2-7]\d{3}[\s-]?\d{4}(?!\d)"), "[teléfono]"),   # teléfonos de 8 dígitos
    (re.compile(r"(?i)\b(me llamo|mi nombre es|soy)\s+[A-ZÁÉÍÓÚÑ][\wáéíóúñ]+(\s+[A-ZÁÉÍÓÚÑ][\wáéíóúñ]+)*"),
     r"\1 [nombre]"),
    (re.compile(r"(?i)\b(vivo en|mi casa (?:queda|está) en)\s+[^.,;]+"), r"\1 [lugar]"),
]

# Categorías de riesgo y raíces que las delatan (sin acentos, en minúsculas). Se revisan con el equipo del piloto.
_RIESGO = {
    "autolesion": ["matarme", "suicid", "quitarme la vida", "hacerme dano", "cortarme", "no quiero vivir",
                   "quiero morir"],
    # «me toca» sola no: en El Salvador es «es mi turno» («me toca hacer la tarea»).
    "violencia_o_abuso": ["me pegan", "me golpea", "me pega ", "me toca mis partes", "me tocan mis partes", "me manose",
                          "abuso", "abusa de mi", "me obliga a", "me amenaz", "violacion", "me viol"],
    "acoso": ["me hacen bullying", "me acosan", "me molestan todos", "acoso"],
    "maras_o_extorsion": ["la mara", "pandill", "extorsion", "pagar la renta"],
}

_ETIQUETAS = re.compile(r"(?i)\b(brecha|hip[oó]tesis (?:confirmada|abierta|descartada)|P\s*=\s*\d[.,]\d+|"
                        r"dominio de \d+ ?%|percentil \d+)\b")


def _norma(s: str) -> str:
    s = "".join(c for c in unicodedata.normalize("NFKD", (s or "").lower()) if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s)


def limpiar(texto: str) -> tuple[str, list[str]]:
    """(texto sin datos personales detectables, tipos de dato retirados)."""
    retirados = []
    for patron, marca in _PATRONES:
        texto, n = patron.subn(marca, texto)
        if n:
            retirados.append(marca if "\\1" not in marca else marca.split(" ")[-1])
    return texto, retirados


def senales_de_riesgo(texto: str) -> list[str]:
    """Categorías de riesgo que aparecen en el texto (vacío si ninguna)."""
    t = _norma(texto)
    return sorted(c for c, raices in _RIESGO.items() if any(r in t for r in raices))


def texto_para_estudiante(texto: str) -> str:
    """El texto sin etiquetas de diagnóstico, puntajes ni comparaciones."""
    return re.sub(r"\s{2,}", " ", _ETIQUETAS.sub("", texto)).strip()
