---
name: decisiones-mined
description: Lleva al equipo de Ciencias del MINED las decisiones de contenido tomadas fuera de la IA (equivalencias retiradas, prerrequisitos rechazados, divisiones de conceptos, clases corregidas del contraste) y registra su veredicto. Usar al cerrar una etapa con decisiones nuevas o cuando el usuario traiga el CSV de decisiones revisado.
---

# Decisiones con el MINED

1. **Exportar:** `uv run gskg revision exportar-decisiones` → `asignaturas/decisiones/<fecha>_decisiones.csv` (una fila
   por decisión, con justificación y estado) y `<fecha>_asignaciones_division.csv` (cada elemento reasignado en una
   división, con su texto). No sobrescribe CSV que el equipo pueda estar llenando.
2. Explica al usuario, en lenguaje no técnico, cómo se llenan: `decision` (aceptar | cambiar | rechazar), `comentario` y
   `revisado_por` (obligatorio). «cambiar» solo existe en asignaciones y admite el concepto original o el nuevo.
3. **Importar** el CSV devuelto: `uv run gskg revision importar-decisiones <csv>`. Valida todo antes de escribir.
   - aceptar → queda en «confirmaciones» de la decisión;
   - cambiar → reasigna el elemento;
   - rechazar → queda en «observaciones» y la decisión pasa a «observada». No se revierte nada: una objeción pide una
     nueva decisión pedagógica; propónla al usuario con evidencia.
4. `make todo` y reporta qué cambió en los hallazgos. El contexto de inicio de sesión muestra cuántas decisiones siguen
   sin confirmar.
