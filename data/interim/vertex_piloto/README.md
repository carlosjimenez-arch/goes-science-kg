# Piloto de agentes en Vertex (2026-10-14)

Unidad: 11.° Química, unidad 2 (12 temas). Modelo: `gemini-4-argon`.

- **Redacción con Gemini** (`gskg lotes vertex --agente redactor-actividades`): 12 lotes válidos al primer intento,
  12 llamadas. Errores que encontró después el experto de Claude: cuentas de material que no cierran, efectos menores
  que el error de medida descritos como observables, simuladores con funciones que no tienen, una fórmula mal y un
  montaje peligroso (etino con aire en rango explosivo cerca de una llama, en 2.11). Claves de opción múltiple
  cargadas a la A (16 de 24).
- **Experto del panel con Gemini** (salidas guardadas aquí, no consolidadas): 59 de 60 aprobados, todos con confianza
  alta. Sobre los mismos 12 experimentos, el experto de Claude corrigió 10.
- **Decisión:** Gemini redacta; el panel sigue con los subagentes de Claude.
