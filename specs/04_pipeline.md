# 04 · Pipeline

Cada etapa tiene entrada, salida, comando y criterio de aceptación. Las etapas con IA usan
subagentes por lote (`.claude/skills/`) y un paso determinista para unir los resultados.

| # | Etapa | Entrada | Salida | Cómo | Acepta si |
|---|---|---|---|---|---|
| 0 | Fuentes | `manifest.csv` | PDF + `estado.csv` | skill `fuentes-descargar` | sha256 registrado; las faltantes quedan listadas |
| 1 | Temas | `config/mallas.yaml` | `data/interim/temas.json` | `gskg temas` | 1.260 temas, ids únicos |
| 2 | Catálogos pivote | PDF de marcos | `data/referencia/catalogo_*.json` | skill `marco-catalogo` | metas validadas contra el PDF; página en cada objetivo |
| 3 | Objetivos de países | PDF de países | `data/interim/paises/<pais>.json` | skill `pais-extraer-objetivos` | documento + página + grado en cada objetivo |
| 4 | Alineación | objetivos + catálogo | `data/interim/alineaciones/*.json` | skill `alinear-objetivos` | 100 % alineado; confianza «baja» listada |
| 5 | Grafo | todo lo anterior | `data/grafo/*` | `gskg grafo construir` | `gskg grafo validar` sin errores |
| 6 | Disciplina | temas sin asignatura | aristas DE_ASIGNATURA | skill `grafo-asignar-disciplina` | 0 temas sin asignatura |
| 7 | Conceptos | temas + objetivos | nodos Concepto + TRABAJA | skill `grafo-conceptos` | cada tema con ≥1 concepto; sin duplicados |
| 8 | Prerrequisitos | conceptos + órdenes por país | PRERREQUISITO_DE | skill `grafo-prerrequisitos` | DAG por asignatura; evidencia en cada arista |
| 9 | Brechas | grafo | `asignaturas/<x>/brechas/` | skill `analisis-brechas` | cifras reproducibles; Excel con fórmulas |
| 10 | Propuesta | brechas + prerrequisitos | `asignaturas/<x>/propuesta/` | skill `propuesta-curricular` | presupuesto respetado; cada cambio con evidencia |
| 11 | Revisión humana | confianza baja + propuesta | CSV para el MINED → `revisado_por` | skill `revision-humana` | decisiones reimportadas |

## Datos previos que se reutilizan (no rehacer)
- Clasificación TIMSS 2027 de los 622 temas de 2.°–9.° y TIMSS Advanced de Física 10.°–11.°.
- Clasificación PISA 2025 de 7.°–9.°.
- Objetivos de Uruguay, Colombia y Singapur ya alineados.

Todo está en `reportes/cobertura_curricular/data/`, y `ingesta/legado.py` lo lee.

## Formato de un lote de IA (genérico)
```json
{"lote": "alinear_JP_T8_27_1", "version": "paises-v2-2027", "catalogo": "T8_27",
 "instrucciones": ".claude/skills/alinear-objetivos/SKILL.md",
 "items": [{"id": "JP-...", "texto": "...", "grado_min": 7, "documento": "...", "pagina": 41}]}
```
Salida del subagente: `[{"id", "obj1", "obj2", "confianza", "justificacion"}]`. El script de unión
valida los códigos contra el catálogo (no se aceptan códigos inventados), agrega `version` y
rechaza lotes incompletos.
