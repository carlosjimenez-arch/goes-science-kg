---
name: grafo-prerrequisitos
description: Infiere aristas PRERREQUISITO_DE entre conceptos de una asignatura con evidencia (orden en países de alto desempeño, Progresiones de Uruguay, NGSS, dependencia lógica) y garantiza un DAG. Usar en la fase 3, después de grafo-conceptos.
---

# Prerrequisitos (DAG por asignatura)

> **Estado (2026-10-05): hecho.** 797 aristas y 11 equivalencias entre asignaturas
> (`data/interim/conceptos/equivalencias.json`). Comandos: `gskg conceptos preparar-prerrequisitos |
> unir-prerrequisitos`. Prompt: `prompts/prerrequisitos.md`. El primer grado SV cuenta los temas donde el concepto
> es principal, o secundario con confianza alta o media.

Evidencias, de más fuerte a más débil:
1. **Declarada**: el documento lo dice («a partir de lo aprendido sobre…»; Progresiones de Uruguay;
   progresiones de NGSS). Se cita documento y página.
2. **Orden observado**: en ≥3 países de referencia, el concepto A aparece en un grado estrictamente
   menor que B **y** A está en la definición o el objetivo de B. Se calcula con el grafo (primer grado
   por país); el texto solo no basta.
3. **Lógica disciplinar**: B no se puede definir sin A (p. ej. «enlace químico» requiere «átomo»).
   Lo propone un subagente con justificación y queda con confianza «media» como máximo.

Pasos:
1. Candidatos: para cada par de conceptos de la misma asignatura con co-ocurrencia en objetivos, calcula
   la evidencia de tipo 2 con un script.
2. Subagentes por asignatura: confirman o rechazan los candidatos y agregan los de tipo 1 y 3.
   Salida: `{origen, destino, tipo_evidencia, evidencias:[…], confianza, justificacion}`.
3. Elimina la redundancia transitiva (si A→B→C, quita A→C salvo que tenga evidencia declarada).
4. **Valida que sea un DAG** (`networkx.is_directed_acyclic_graph`). Si hay un ciclo, quita la arista de
   menor confianza y repórtala. Agrega este invariante a `grafo/validar.py`.
5. Muestra al usuario la cadena más larga por asignatura y 10 aristas al azar para revisión.
