# Prompt 00 · Montar el proyecto completo (para pegar en Claude Code)

> Abre Claude Code en la raíz de `goes-science-kg` y pega todo lo que está debajo de la línea.

---

Actúa como ingeniero de software de IA y de Python en este repositorio. El objetivo es construir el
**grafo de conocimiento de Ciencias de El Salvador** (Biología, Física, Química, Ciencias de la Tierra
y del Espacio), anclado en los marcos internacionales (TIMSS 2027, TIMSS Advanced, PISA 2025) y en
los currículos de otros países, priorizando los de mejor desempeño en Ciencias. Con ese grafo hay
que **proponer, por asignatura, una curricularización mejor para El Salvador**, con evidencia.

**Antes de escribir código:**
1. Lee `CLAUDE.md` y todas las specs de `specs/`, en orden (00 → 08).
2. Revisa las skills de `.claude/skills/` (cada etapa con IA tiene la suya).
3. Ejecuta `uv sync --extra dev --extra pdf --extra analisis`, `uv run gskg grafo construir`,
   `uv run gskg grafo validar` y `uv run pytest -q`. Confirma que el punto de partida (grafo v0) está sano.
4. Lee `reportes/cobertura_curricular/outputs/informe_timss2027.md` e `informe_paises_timss2027.md`:
   ahí están los hallazgos actuales.

**Luego ejecuta `specs/08_plan_de_implementacion.md` fase por fase (1 → 6):**
- Usa la skill que corresponda en cada tarea. Para clasificar o alinear, usa subagentes **en paralelo**,
  un lote por país, grado o asignatura, y une los resultados con un script que valide los códigos.
- Antes de cada lote completo, haz una muestra de control de 20 ítems y muéstramela.
- Al terminar cada fase: `gskg grafo construir` → `gskg grafo validar` (0 errores) → `gskg fichas` →
  `pytest -q` en verde → marca ✅ en la spec 08 → commit `tipo(ámbito): resumen` → muéstrame un
  resumen de lo que cambió (conteos del grafo y hallazgos por asignatura) **y espera mi visto bueno**
  antes de seguir.

**Pregúntame antes de:**
- elegir el pivote de Química y Biología de 10.°–11.° (fase 1.3);
- agregar países que no estén en `config/referentes.yaml`;
- cambiar una regla de negocio de `CLAUDE.md` o de `reportes/cobertura_curricular/CLAUDE.md`;
- proponer quitar temas de la malla.

**No hagas:**
- modificar `data/fuentes/`, `reportes/` ni los PDF;
- usar cifras de desempeño de países sin citar el informe oficial y la página;
- inventar códigos de objetivos o copiar párrafos de los documentos.

**Entregable final por asignatura** (`asignaturas/<asignatura>/`): `ficha.md`, `brechas/`
(Excel con fórmulas + `brechas.md`), `propuesta/` (`propuesta.json`, `Propuesta_<Asignatura>.xlsx`,
`informe.md`) y `revision/` (CSV para el equipo de Ciencias del MINED).
Empieza la propuesta por **Biología de 5.°–8.°**, que es la brecha más clara del informe de países.
