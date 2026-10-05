---
name: alinear-objetivos
description: Alinea objetivos (de un país o temas de la malla SV) contra un catálogo pivote (TIMSS 2027, TIMSS Advanced, PISA 2025) con subagentes por lote, asignando obj1/obj2/FUERA, confianza y justificación. Usar en la fase 2 o al reclasificar temas.
---

# Alinear contra el pivote

Prompts de referencia (ya probados): `reportes/cobertura_curricular/prompts/alinear_paises.md`,
`clasificar_lote.md` y `clasificar_lote_pisa.md`.

1. **Preparar lotes** (script, no a mano): `data/interim/alineaciones/lotes/lote_<PAIS>_<MARCO>_<n>.json`,
   con 40 a 60 ítems por lote. Cada lote incluye el catálogo completo del marco que corresponde al grado.
   - Grados 1–4 → T4_27; 5–8 → T8_27; 7–9 también PISA25; Física 10–11 → TA15.
2. **Muestra de control**: 20 ítems al azar. Clasifícalos y muéstralos al usuario. Si hay 3 errores o más,
   ajusta las instrucciones antes de seguir.
3. **Subagentes en paralelo**, uno por lote, con estas reglas:
   - `obj1` = el objetivo que mejor describe el contenido; `obj2` = opcional, solo si es claro.
   - `FUERA` si no hay contenido del marco.
   - Investigaciones: va a un área de *Investigations* solo si el foco es la práctica (planificar, medir,
     analizar). Si la práctica sirve a un contenido, se clasifica por el contenido y la investigación va como obj2.
   - `confianza`: alta, media o baja. `justificacion`: 15 palabras como máximo, en español.
   - Solo códigos que existan en el catálogo.
4. **Unir** con un script: valida códigos, cobertura del 100 % de ids, agrega `version`
   (`paises-v2-2027`), escribe `data/interim/alineaciones/<pais>.json` y lista las de confianza baja.
5. Reconstruye el grafo (`gskg grafo construir`) y valida.
