---
name: analisis-brechas
description: Genera el análisis de brechas de una asignatura (cobertura, balance, profundidad, nivel cognitivo, oportunidad frente a países de alto desempeño y prerrequisitos tardíos) en asignaturas/<x>/brechas/. Usar en la fase 4 o cuando cambie el grafo.
---

# Brechas por asignatura

> **Estado (2026-10-05): primera versión hecha** con `gskg brechas` (`src/goes_science_kg/brechas.py`):
> cobertura por ciclo, oportunidad por concepto y errores de secuencia, en `asignaturas/<x>/brechas/`
> (md + json + csv). Falta el Excel con fórmulas del paso 3.

Reglas de cálculo: `reportes/cobertura_curricular/CLAUDE.md` («Reglas de negocio»). Siguen vigentes.

1. Implementa `src/goes_science_kg/analisis/` como funciones puras sobre el grafo cargado
   (`grafo.almacen.cargar`). No se recalcula nada desde Excel.
2. Por asignatura y ciclo (2–4, 5–8, 7–9, 10–11):
   - **Cobertura**: objetivos del pivote con ≥1 tema del ciclo (obj1 u obj2).
   - **Profundidad**: 0, 1 débil, 2–3 básica, 4+ sólida.
   - **Balance**: participación de la asignatura frente a la meta del dominio.
   - **Nivel cognitivo**: Conocer, Aplicar y Razonar desde `habilidad_timss` (reparto en partes iguales si hay varios).
   - **Oportunidad**: grado de El Salvador menos la mediana de los países, en dos versiones (todos / alto desempeño).
   - **Prerrequisitos tardíos** (si ya hay DAG): concepto enseñado antes que su prerrequisito.
3. Salidas en `asignaturas/<x>/brechas/`:
   - `brechas.json` (datos),
   - `Brechas_<Asignatura>.xlsx`: cada cifra es FÓRMULA sobre la hoja de datos; estilo 2027 y compatible con
     Numbers (ver «Convenciones» del CLAUDE.md de reportes),
   - `brechas.md`: hallazgos principales en lenguaje para el equipo de Ciencias.
4. **Prueba de regresión**: con solo Uruguay, Colombia y Singapur, la cobertura de 2.°–8.° debe coincidir
   con `reportes/cobertura_curricular/outputs/informe_timss2027.md` (31/32 y 45/48).
