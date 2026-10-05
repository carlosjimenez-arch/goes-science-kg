# Asignaturas

Una carpeta por disciplina. En todas se usa la misma estructura:

| Archivo | Quién lo escribe | Contenido |
|---|---|---|
| `README.md` | Equipo | Alcance, marcos, hallazgos y decisiones abiertas |
| `ficha.md` | `gskg fichas` | Temas por grado, cobertura de marcos y países (no editar) |
| `brechas/` | `gskg brechas` | Cobertura por ciclo, oportunidad por concepto frente a países y errores de secuencia |
| `propuesta/` | `gskg propuesta candidatos` + especialista + `gskg propuesta excel` | Borrador de malla por ciclo: candidatos, propuesta (JSON + Excel) e informe |
| `revision/` | Skill `revision-humana` | CSV para el equipo de Ciencias del MINED |

Cómo se asigna cada tema de la malla integrada de 2.°–9.° a una asignatura: `specs/05_asignaturas.md`.

Los grafos **por grado** (lo que pidió el MINED) están en [`../grados/`](../grados/README.md).
