# Reforzamiento de los dictámenes por ciencia

Este folder guarda los **snapshots del bucle de fortalecimiento** del panel de expertos IA. El método está en
[`specs/14_panel_expertos.md`](../../specs/14_panel_expertos.md), sección 7. Este README lo escribe el equipo; los
demás archivos los genera `uv run gskg bucle snapshot --etapa "<etapa>"` en cada etapa del bucle, y cada corte queda
en el historial de git.

| Archivo | Qué trae |
|---|---|
| [`RESUMEN.md`](RESUMEN.md) | totales por ciencia: impugnados, cambiados y solidez |
| [`biologia.md`](biologia.md), [`fisica.md`](fisica.md), [`quimica.md`](quimica.md), [`tierra-espacio.md`](tierra-espacio.md) | por ciencia: solidez por tipo, lo que el bucle cambió y por qué, lo mantenido frente a contraevidencia, lo frágil y los patrones de error |

**Cómo leer la solidez:**
- **sólido:** sobrevivió al revisor adversarial y tiene una cita literal verificada por el código en una fuente
  primaria (en contenido: el revisor no encontró errores);
- **respaldado:** sobrevivió, pero con una fuente parafraseada, o la réplica lo mantuvo frente a contraevidencia
  anclada o a una discrepancia de la sonda ciega;
- **frágil:** sin fuente primaria verificable o cambiado en la última vuelta;
- **sin consenso:** decide una persona.

> Son dictámenes del panel de expertos IA, **no confirmaciones del MINED**. Usar contenido con estudiantes exige
> además la firma de un docente (`aprendizaje/PILOTO.md`).
