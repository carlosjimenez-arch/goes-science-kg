---
name: grafo-conceptos
description: Construye la capa de Conceptos y Prácticas del grafo (nodos Concepto/Practica y aristas TRABAJA) a partir de temas SV, objetivos de marcos y objetivos de países, con vocabulario canónico por asignatura. Usar en la fase 3.
---

# Conceptos y prácticas

Un **concepto** es una idea científica enseñable y evaluable (p. ej. «fotosíntesis», «modelo de
partículas», «circuito en serie»). No es un tema ni una actividad.

1. **Vocabulario semilla** por asignatura, en `data/interim/conceptos/<asignatura>_semilla.json`.
   Sale de los objetivos de TIMSS 2027, PISA y TIMSS Advanced (son el pivote y tienen la granularidad
   adecuada), con 40 a 120 conceptos por asignatura. Campos: `id` (`CON:<asig>/<slug>`), `nombre`,
   `definicion` (≤25 palabras), `sinonimos`, `objetivos_marco`.
2. **Etiquetado con subagentes**, un lote por asignatura y grado: a cada tema y objetivo de país se le
   asignan de 1 a 4 conceptos del vocabulario, con confianza y justificación. Si falta un concepto,
   el subagente lo **propone** en `nuevos` sin crearlo.
3. **Consolidar**: revisa los propuestos y deduplica por sinónimos. Un concepto entra solo si lo trabajan
   ≥2 fuentes, o 1 fuente y 1 marco (regla 4 de la spec 02).
4. **Prácticas**: TIMSS Investigations, PISA PR1–PR8 y EP1–EP20, y las 8 prácticas de NGSS
   (`data/fuentes/mined/Fuentes/Standars…NGSS…pdf`, con página). Id `PRAC:<slug>`.
5. Implementa `grafo/conceptos.py`: lee los archivos consolidados y agrega los nodos y las aristas TRABAJA
   (`metodo = ia`). Agrega pruebas: cada tema con al menos 1 concepto y sin conceptos huérfanos.
6. Reconstruye, valida y muestra al usuario los 10 conceptos con más fuentes por asignatura.
