# Panel de expertos IA

Mientras no haya un equipo del MINED que revise, un panel de expertos IA resuelve con criterio técnico las decisiones
que esperaban esa revisión. El panel tiene cinco miembros: un experto en la didáctica de cada ciencia (Biología,
Física, Química y Ciencias de la Tierra y del Espacio) y un psicopedagogo. El método y sus límites están en
[`specs/14_panel_expertos.md`](../specs/14_panel_expertos.md).

- **[`DICTAMEN.md`](DICTAMEN.md)** (generado): lo que el panel resolvió, lo que dejó sin consenso y su asesoría para el
  piloto.
- **Estado y lotes** de cada ronda: en `data/interim/panel/`.
- **Los dictámenes no son confirmaciones del MINED.** Quedan en las capas como «dictamen del panel», con su evidencia,
  y se pueden confirmar o revertir.
- **Usar contenido con estudiantes** exige además el aval de una persona responsable (`aprendizaje/PILOTO.md`).
