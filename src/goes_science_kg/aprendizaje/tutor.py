"""Agente tutor (spec 13, «Tutoría»): redacta cada turno del diálogo con un modelo de lenguaje.

El tutor no decide nada sobre el estudiante. El diagnóstico, el plan de refuerzo y el dominio son deterministas
(diagnostico.py, planificador.py, estudiante.py): la sesión le dice al tutor qué hacer en cada turno (`tarea`) y con qué
contexto (`contexto.paquete`); el tutor solo decide cómo decirlo. Cada turno pasa guardas deterministas antes de
mostrarse:
- largo según el grado (config `adaptacion`) y una sola pregunta breve;
- no revela la respuesta de la actividad que sigue (la letra o el texto de la opción correcta, el valor numérico, la
  respuesta modelo de una abierta);
- cita solo fuentes del paquete (F1…Fn); sin enlaces y sin pedir datos personales.
Si un turno no pasa, se reintenta con los errores; si vuelve a fallar, se muestra el microtema tal como está en la capa
pedagógica (respaldo determinista) y queda registrado.
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field

from .llm import config as config_llm
from .pedagogia import palabras_max, registro

TAREAS = {
    "introducir": "Presenta el refuerzo: explica la idea del microtema con su ejemplo, en tus palabras, y pide al "
                  "estudiante que intente la actividad que sigue.",
    "retroalimentar": "El estudiante acaba de responder la actividad anterior. Si acertó, confirma en una oración por "
                      "qué está bien. Si no, da UNA pista que apunte a su error, sin decir la respuesta. Después "
                      "invítalo a la actividad que sigue.",
    "cerrar": "El refuerzo terminó. Resume en una oración lo que trabajó y dile que vuelve al objetivo de su clase.",
}

ESQUEMA = {
    "type": "OBJECT",
    "properties": {"mensaje": {"type": "STRING"}, "pregunta": {"type": "STRING"},
                   "fuentes": {"type": "ARRAY", "items": {"type": "STRING"}}},
    "required": ["mensaje", "pregunta", "fuentes"],
}

SISTEMA = """Eres tutor de ciencias de un estudiante de {grado}.° grado en El Salvador. Hablas en español, de tú, con
calidez y sin regañar. Registro: {registro}.
Reglas (si no las cumples, tu turno se descarta):
1. Haz SOLO la tarea del turno. No cambies de tema: si el estudiante se desvía, vuelve al objetivo.
2. «mensaje»: {palabras} palabras como máximo. «pregunta»: una sola pregunta breve ({pregunta} palabras como máximo);
   en «cerrar» puede ir vacía. El enunciado y las opciones de la actividad se muestran aparte: no los copies.
3. Nunca reveles la respuesta de la actividad que sigue: ni la letra, ni el texto de la opción correcta, ni el valor.
4. Usa solo lo que está en el contexto. Las definiciones van con el sentido exacto del contexto (foco y microtema):
   no las simplifiques de forma que digan otra cosa (por ejemplo, no confundas un concepto con el rasgo que produce).
   «fuentes»: las etiquetas (F1, F2…) de las fuentes en que te apoyas, solo en ese campo y nunca dentro del mensaje;
   no inventes otras ni pongas enlaces.
5. No pidas datos personales (nombre completo, dirección, teléfono, correo) ni hables de la evaluación del estudiante.
Responde solo con el JSON pedido."""


@dataclass
class Turno:
    tarea: str
    mensaje: str
    pregunta: str
    fuentes: list[str]
    origen: str                      # «modelo» o «respaldo» (texto del microtema)
    errores: list[str] = field(default_factory=list)   # guardas que fallaron en los intentos descartados

    def texto(self) -> str:
        return " ".join(x for x in (self.mensaje, self.pregunta) if x)


def _norma(s: str) -> str:
    s = "".join(c for c in unicodedata.normalize("NFKD", (s or "").lower()) if not unicodedata.combining(c))
    return " ".join(re.findall(r"[a-z0-9]+(?:[.,][0-9]+)?", s))


def _palabras(s: str) -> int:
    return len((s or "").split())


def fuentes(paq: dict, microtema: dict | None) -> dict[str, str]:
    """Etiqueta → fuente que el tutor puede citar: objetivo, concepto foco, microtema y citas del paquete."""
    lista = [f"objetivo de la malla {paq['objetivo']['id']}: {paq['objetivo']['indicador']}",
             f"concepto {paq['foco']['nombre']}: {paq['foco']['definicion']}"]
    if microtema:
        lista.append(f"microtema {microtema['id']} «{microtema['titulo']}» ({microtema['estado']})")
    lista += paq.get("fuentes", [])
    return {f"F{i}": x for i, x in enumerate(lista, start=1)}


def _trigramas(s: str) -> set[tuple[str, ...]]:
    w = _norma(s).split()
    return {tuple(w[i:i + 3]) for i in range(len(w) - 2)}


def revela(texto: str, actividad: dict | None) -> str | None:
    """Por qué el texto revela la respuesta de la actividad (None si no la revela)."""
    if not actividad:
        return None
    t = _norma(texto)
    if actividad["formato"] == "opcion_multiple":
        letra = actividad["correcta"].lower()
        if re.search(rf"\b(opcion|respuesta|inciso|literal|letra)\s+(correcta\s+)?(es\s+)?(la\s+)?{letra}\b", t):
            return f"nombra la opción correcta ({actividad['correcta']})"
        correcta = _norma(actividad["opciones"][actividad["correcta"]])
        if len(correcta.split()) >= 3 and correcta in t:
            return "copia el texto de la opción correcta"
    if actividad["formato"] == "numerica" and actividad.get("valor") is not None:
        v = float(actividad["valor"])
        variantes = {f"{v:g}", f"{v:g}".replace(".", ",")}
        if any(re.search(rf"(?<![0-9.,]){re.escape(x)}(?![0-9])", t) for x in variantes):
            return f"da el valor de la respuesta ({v:g})"
    if actividad["formato"] == "abierta":
        modelo = _trigramas(actividad["rubrica"]["respuesta_modelo"])
        if modelo and len(modelo & _trigramas(texto)) / len(modelo) >= 0.5:
            return "reproduce la respuesta modelo de la rúbrica"
    return None


_DATOS_PERSONALES = re.compile(r"\b(tu|su)\s+(nombre completo|apellido|direccion|telefono|celular|correo|contrasena)"
                               r"|\bdonde vives\b|\bcuantos anos tienes\b")


def errores_turno(t: dict, tarea: str, grado: int, permitidas: dict[str, str], actividad: dict | None) -> list[str]:
    """Las guardas del docstring del módulo. Lista vacía: el turno se puede mostrar."""
    e = []
    mensaje, pregunta = (t.get("mensaje") or "").strip(), (t.get("pregunta") or "").strip()
    if not mensaje:
        e.append("mensaje vacío")
    if _palabras(mensaje) > palabras_max(grado):
        e.append(f"mensaje de {_palabras(mensaje)} palabras; máximo {palabras_max(grado)} en {grado}.°")
    if tarea != "cerrar" and not pregunta:
        e.append("falta la pregunta")
    if _palabras(pregunta) > config_llm()["palabras_pregunta"] or pregunta.count("?") > 1:
        e.append("la pregunta debe ser una sola y breve")
    if motivo := revela(f"{mensaje} {pregunta}", actividad):
        e.append(f"revela la respuesta: {motivo}")
    if extra := sorted(set(t.get("fuentes") or []) - permitidas.keys()):
        e.append(f"fuentes que no están en el contexto: {extra}")
    if re.search(r"\bF\d+\b", f"{mensaje} {pregunta}"):
        e.append("etiquetas de fuentes dentro del texto (van solo en «fuentes»)")
    texto = f"{mensaje} {pregunta}"
    if re.search(r"https?://|www\.", texto):
        e.append("trae un enlace")
    if _DATOS_PERSONALES.search(_norma(texto)):
        e.append("pide datos personales")
    return e


def _sin_respuesta(a: dict | None) -> dict | None:
    """La actividad tal como la ve el estudiante: sin la clave, la rúbrica ni la retroalimentación."""
    if not a:
        return None
    return {"enunciado": a["enunciado"], "formato": a["formato"], "habilidad": a["habilidad"],
            **({"opciones": a["opciones"]} if a["formato"] == "opcion_multiple" else {}),
            **({"unidad": a.get("unidad")} if a["formato"] == "numerica" else {})}


def prompt(tarea: str, paq: dict, microtema: dict | None, actividad: dict | None, ultimo: dict | None,
           permitidas: dict[str, str]) -> str:
    """El contexto del turno: objetivo, foco, microtema, fuentes, la actividad que sigue (sin la clave) y la última
    respuesta. Del estudiante, solo su grado y su evidencia; nunca su identificador."""
    contexto = {
        "tarea": TAREAS[tarea],
        "objetivo": {k: paq["objetivo"][k] for k in ("procedimental", "indicador", "evidencia_de_logro")},
        "foco": {k: paq["foco"][k] for k in ("nombre", "definicion")},
        "microtema": ({k: microtema[k] for k in ("titulo", "explicacion", "ejemplo", "criterio")}
                      if microtema else None),
        "fuentes": permitidas,
        "actividad_que_sigue": _sin_respuesta(actividad),
        "ultima_respuesta": ultimo,
        "hipotesis_confirmadas": [h["concepto"] for h in paq["estudiante"]["hipotesis"] if h["estado"] == "confirmada"],
    }
    return "CONTEXTO DEL TURNO (JSON):\n" + json.dumps(contexto, ensure_ascii=False, indent=1)


class Tutor:
    """Redacta turnos con `modelo` (ver llm.py) y aplica las guardas."""

    def __init__(self, modelo, intentos: int | None = None):
        self.modelo = modelo
        self.intentos = intentos or config_llm()["intentos_tutor"]
        self.turnos: list[Turno] = []

    def turno(self, tarea: str, paq: dict, microtema: dict | None, actividad: dict | None = None,
              ultimo: dict | None = None) -> Turno:
        grado = paq["estudiante"]["grado"]
        permitidas = fuentes(paq, microtema)
        sistema = SISTEMA.format(grado=grado, registro=registro(grado), palabras=palabras_max(grado),
                                 pregunta=config_llm()["palabras_pregunta"])
        base = prompt(tarea, paq, microtema, actividad, ultimo, permitidas)
        errores: list[str] = []
        for _ in range(self.intentos):
            texto = base + (f"\n\nTu turno anterior se descartó por: {'; '.join(errores)}. Corrígelo."
                            if errores else "")
            try:
                r = self.modelo.generar(sistema, texto, ESQUEMA, rol="tutor")
            except Exception as ex:  # noqa: BLE001 — un fallo del modelo no detiene la sesión: se usa el respaldo
                errores = [f"el modelo falló: {type(ex).__name__}"]
                break
            nuevos = errores_turno(r, tarea, grado, permitidas, actividad)
            if not nuevos:
                t = Turno(tarea, r["mensaje"].strip(), (r.get("pregunta") or "").strip(), sorted(r["fuentes"]),
                          "modelo", errores)
                self.turnos.append(t)
                return t
            errores = nuevos
        t = self.respaldo(tarea, microtema, permitidas, errores)
        self.turnos.append(t)
        return t

    @staticmethod
    def respaldo(tarea: str, microtema: dict | None, permitidas: dict[str, str], errores: list[str]) -> Turno:
        """El texto revisable de la capa pedagógica, sin modelo: lo que el prototipo mostraba antes del tutor."""
        etiqueta_mt = next((k for k, v in permitidas.items() if v.startswith("microtema ")), None)
        if tarea == "introducir" and microtema:
            return Turno(tarea, f"{microtema['explicacion']} {microtema['ejemplo']}".strip(),
                         "Intenta la actividad que sigue.", [etiqueta_mt] if etiqueta_mt else [], "respaldo", errores)
        if tarea == "retroalimentar":
            return Turno(tarea, "Revisa la explicación y vuelve a intentarlo.", "Intenta la actividad que sigue.",
                         [], "respaldo", errores)
        return Turno(tarea, "Volvemos al objetivo de tu clase.", "", [], "respaldo", errores)
