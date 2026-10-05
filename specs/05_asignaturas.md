# 05 · Asignaturas

## Carpetas
```
asignaturas/
├── biologia/                 2.°–11.°
├── fisica/                   2.°–11.°
├── quimica/                  2.°–11.°
└── ciencias_tierra_espacio/  2.°–9.°
    ├── README.md             escrito por el equipo: alcance, marcos, decisiones
    ├── ficha.md              GENERADO (gskg fichas): temas por grado, cobertura y países
    ├── brechas/              GENERADO (fase 4): análisis por ciclo
    └── propuesta/            GENERADO + revisado (fase 5): malla propuesta
```

## Cómo se asigna un tema a una asignatura
La malla de 2.°–9.° es **integrada** («Ciencia y Tecnología»). Reglas, en orden
(`disciplinas.py`, `config/asignaturas.yaml`):

1. **Bachillerato (10.°–11.°):** la asignatura de la malla.
2. **2.°–9.°:** el dominio del objetivo TIMSS 2027 principal. En TIMSS 4.°, «Ciencias físicas»
   se reparte por área: *Propiedades y cambios de la materia* va a Química y el resto a Física.
3. **Si el tema quedó FUERA de TIMSS:** el contenido PISA principal. Sistemas físicos F1 y F2
   van a Química y el resto a Física; Sistemas vivos va a Biología; Tierra y espacio va a
   Ciencias de la Tierra.
4. **Si nada aplica:** queda «por asignar» (49 temas en v0). La skill `grafo-asignar-disciplina`
   los resuelve con justificación. Si un tema es de tecnología, se marca
   `props.fuera_de_alcance = "tecnologia"`.

Un tema conserva **una sola** asignatura. Si trabaja dos, la segunda se expresa con la arista
CUBRE secundaria o, desde la fase 3, con TRABAJA hacia conceptos de otra asignatura.

## Marcos por asignatura y grado
| Asignatura | 2.°–4.° | 5.°–8.° | 7.°–9.° | 10.°–11.° |
|---|---|---|---|---|
| Biología | TIMSS 4.° (45 %) | TIMSS 8.° (35 %) | PISA Sistemas vivos | sin pivote → definir (spec 03) |
| Física | TIMSS 4.° Cs. físicas | TIMSS 8.° (25 %) | PISA Sistemas físicos | TIMSS Advanced Física |
| Química | TIMSS 4.° Cs. físicas (P1) | TIMSS 8.° (20 %) | PISA Sistemas físicos (F1, F2) | sin pivote → definir |
| Tierra y Espacio | TIMSS 4.° (20 %) | TIMSS 8.° (20 %) | PISA Tierra y espacio | — |

Las metas de balance, cobertura, profundidad, nivel cognitivo y la regla de presupuesto siguen
**vigentes** tal como están en `reportes/cobertura_curricular/CLAUDE.md` («Reglas de negocio»).
No se cambian sin preguntar.

## Ciclos de análisis
TIMSS evalúa el acumulado: **2.°–4.°** contra TIMSS 4.° y **5.°–8.°** contra TIMSS 8.°.
PISA evalúa **7.°–9.°**. **10.°–11.°** se analiza por asignatura.
