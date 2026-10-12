"""Control de fidelidad científica del tutor (spec 13 y 14).

La prueba de humo con Vertex mostró que un turno puede pasar todas las guardas de forma y aun así decir algo
científicamente impreciso (en 7.°: «el gen es el color»). Este control usa la misma idea que el evaluador: un modelo
separado propone y el código decide con citas literales.
- El verificador lista cada afirmación científica del turno, copiada del turno, y para cada una copia del contexto
  revisado el fragmento que la respalda, o dice que no hay respaldo o que el contexto la contradice.
- El código exige que cada afirmación esté de verdad en el turno y cada respaldo de verdad en el contexto. Una
  afirmación sin respaldo o contradicha descarta el turno. Un turno con contenido (más de PALABRAS_SIN_AFIRMACION
  palabras) sin ninguna afirmación también se descarta: el verificador no puede no ver nada.
El contexto revisado es lo que la capa pedagógica y el vocabulario dicen del concepto: la definición, el microtema
(explicación, ejemplo y criterio) y el indicador del objetivo. Cuesta una llamada más por turno.
"""

from __future__ import annotations

import json
import re
import unicodedata

PALABRAS_SIN_AFIRMACION = 25

ESQUEMA = {
    "type": "OBJECT",
    "properties": {
        "afirmaciones": {"type": "ARRAY", "items": {"type": "OBJECT", "properties": {
            "turno": {"type": "STRING"}, "contexto": {"type": "STRING"},
            "estado": {"type": "STRING", "enum": ["respaldada", "sin_respaldo", "contradice"]}},
            "required": ["turno", "contexto", "estado"]}},
    },
    "required": ["afirmaciones"],
}

SISTEMA = """Eres verificador de fidelidad científica de un tutor de ciencias para estudiantes. No reescribes ni
opinas: comparas.
1. Lista CADA afirmación científica del TURNO (qué es algo, cómo funciona, causas, definiciones, datos). Copia en
   «turno» el fragmento literal del turno (25 palabras como máximo). Saludos, ánimos e instrucciones no son
   afirmaciones.
2. Para cada una, busca en el CONTEXTO el fragmento que la respalda y cópialo literal en «contexto». Estado:
   «respaldada» si el contexto dice lo mismo, aunque con otras palabras; «sin_respaldo» si el contexto no lo dice;
   «contradice» si el contexto dice otra cosa o la afirmación cambia el sentido de una definición (por ejemplo,
   confundir un concepto con el rasgo que produce). En esos dos casos, «contexto» puede ir vacío.
Responde solo con el JSON pedido."""


def _norma(s: str) -> str:
    s = "".join(c for c in unicodedata.normalize("NFKD", (s or "").lower()) if not unicodedata.combining(c))
    return " ".join(re.findall(r"[a-z0-9]+", s))


def contexto(paq: dict, microtema: dict | None) -> str:
    """El contexto revisado contra el que se verifica un turno."""
    partes = [f"Concepto: {paq['foco']['nombre']}. Definición: {paq['foco']['definicion']}",
              f"Objetivo: {paq['objetivo']['indicador']}"]
    if microtema:
        partes += [f"Explicación: {microtema['explicacion']}", f"Ejemplo: {microtema['ejemplo']}",
                   f"Criterio: {microtema['criterio']}"]
    return "\n".join(partes)


def errores(salida: dict, turno: str, ctx: str) -> list[str]:
    """Decide con citas literales (docstring del módulo). Lista vacía: el turno es fiel al contexto."""
    e = []
    afirmaciones = salida.get("afirmaciones") or []
    t, c = _norma(turno), _norma(ctx)
    if not afirmaciones and len(turno.split()) > PALABRAS_SIN_AFIRMACION:
        e.append("el verificador no encontró afirmaciones en un turno con contenido")
    for a in afirmaciones:
        frag = (a.get("turno") or "").strip()
        if not _norma(frag) or _norma(frag) not in t:
            e.append(f"afirmación que no está en el turno: «{frag[:60]}»")
            continue
        if a.get("estado") == "contradice":
            e.append(f"contradice el contexto: «{frag[:80]}»")
        elif a.get("estado") != "respaldada":
            e.append(f"sin respaldo en el contexto: «{frag[:80]}»")
        elif not _norma(a.get("contexto")) or _norma(a.get("contexto")) not in c:
            e.append(f"el respaldo citado no está en el contexto: «{frag[:60]}»")
    return e


class Verificador:
    """Verificador de fidelidad con `modelo` (llm.py), separado del tutor y del evaluador."""

    def __init__(self, modelo):
        self.modelo = modelo

    def revisar(self, turno: str, paq: dict, microtema: dict | None) -> list[str]:
        ctx = contexto(paq, microtema)
        prompt = f"CONTEXTO REVISADO:\n{ctx}\n\nTURNO DEL TUTOR:\n{turno}"
        try:
            salida = self.modelo.generar(SISTEMA, prompt, ESQUEMA, rol="fidelidad")
        except Exception as ex:  # noqa: BLE001 — sin verificación, el turno no se muestra
            return [f"el verificador falló: {type(ex).__name__}"]
        return errores(salida if isinstance(salida, dict) else json.loads(salida), turno, ctx)
