# Investigación y evidencia experimental

Corte: 2026-10-21. Las fuentes oficiales, los resultados observados y las recomendaciones de diseño se distinguen en cada documento.

| Documento | Contenido |
|---|---|
| [Estado de entrega](../CIERRE_TECNICO.md) | Capacidades comprobadas, preparación de 108 unidades y límites del hito |
| [Integración PISA/ERCE](integracion_alineaciones_v4.md) | Producto-3, cuatro casos originales auditables y contexto obligatorio |
| [Progresiones NGSS](progresiones_ngss_20261021.md) | Tres documentos oficiales, bandas nativas y decisiones de uso |
| [Educación](educacion.md) | PISA, ERCE, TIMSS, países, pedagogía y adaptación a El Salvador |
| [Auditoría de fuentes primarias](auditoria_fuentes_primarias.md) | Corrección de columnas TIMSS, identidad documental, páginas y límites de las 22 dimensiones |
| [Anclas verificadas](dimensiones_verificadas.json) | Validación reproducible de las dimensiones frente a los PDF originales y sus SHA |
| [Arquitectura de IA](arquitectura_ia.md) | Context engineering, workflows, jueces, RAG, GCP y métricas |
| [Auditoría del repositorio](auditoria_repo.md) | Dependencias, activos conservados, deuda y limpieza |
| [Recuperación local](resultados_recuperacion.md) | El candidato más rápido pierde calidad; se mantiene el baseline |
| [Embeddings reales en Vertex](resultados_embeddings_vertex.md) | Corpus y 98 consultas autorizados, calidad, latencia, consumo y límites |
| [Jueces iniciales](resultados_jueces.md) | 16 casos saturados; no permiten elegir ganador |
| [Jueces reservados](resultados_jueces_ciegos.md) | 24 casos nuevos; diferencias en abstención y fallos incluidos |
| [Workflow de banco](resultados_workflow.json) | Errores encontrados, abstenciones y salida respaldada con selección de fragmentos |
| [Coherencia de la API](coherencia_api.md) | Publicación por artículo y rechazo de mezclas de generaciones |
| [Medición local de la API](metricas_api_local.json) | Muestras de latencia y huellas; no es prueba de carga |
| [Análisis de V4](analisis_v4.md) | Estructura, ausencias y alertas científicas localizadas |
| [Ingesta V4](ingesta_v4.md) | Mapeo de 126 hojas, contratos ricos y preservación de originales |
| [Contexto V4](contexto_v4.md) | Evidencia por celdas, combinaciones, presupuesto y mediciones |
| [Catalogación disciplinar](catalogacion_v4.md) | Lectores separados, piloto, fallos y contabilidad acumulada |
| [Catalogación V4 ejecutada](resultados_catalogacion_v4.json) | 1.020 estados preservados, 68 abstenciones y continuación autorizada dentro del límite |
| [Comparación V3–V4](comparacion_v3_v4.md) | 506 coincidencias de objetivo y diferencias de campos sin heredar etiquetas |
| [Publicación V4](producto_v4.md) | Generaciones coherentes, diagnóstico y referencias explícitas |
| [Agentic acotado](agentic_v4.md) | Política, harness y gate congelados antes de leer la reserva |
| [Baseline V4 parcial](resultados_baseline_v4_parcial.md) | 19 consultas con catálogo piloto; limitaciones y denominadores visibles |
| [Baseline V4 publicado](resultados_baseline_v4_catalogado.md) | Las mismas 19 consultas con catálogo completo, sin ajuste ni selección de un recuperador nuevo |
| [Verificación del runtime V4](verificacion_runtime_v4.json) | Publicación real, ocho filas de unidad, veto de grado y 27 bloqueos científicos, sin modelos |
| [Unidad de Física 10.º ejecutada](resultados_unidad_fisica10_v4.md) | Ocho sesiones reales: cuatro respaldadas y cuatro abstenciones; 58 intentos, reserva USD 7,4261195 y reanudación sin generación |
| [Contexto de conocimiento](contexto_conocimiento_v4.md) | Reserva de grupos y medición estructural de 1.203 contrastes, sin juicios semánticos |
| [Continuación de Ciencias](continuacion_ciencias_20261021.md) | Publicación de quince juicios, dos conceptos admitidos, fallos conservados y límites de cobertura |
| [Selección por grupo](resultados_seleccion_grupos_20261021.json) | Comparación sobre seis casos conocidos, con errores de ingeniería y presupuesto acumulado |
| [Lectura primaria completa](resultados_lectura_completa_20261021.json) | Dos pares nuevos, ocho lecturas reales, un respaldo y un rechazo |
| [Medición de lectura](medicion_lectura_primaria_20261021.json) | 1.203 preparaciones locales; 24.000 frente a 40.000 caracteres |
| [API V4 publicada](api_v4_publicada_20261021.json) | Auditoría de respaldos/rechazos, veto de grado y preparación sin modelos sobre los datos reales |
| [Escenarios operativos](resultados_escenarios_20261021.json) | Tiempo y recursos propuestos con conservación de objetivos; no aprobación pedagógica |
| [Incidente de transporte](incidente_transporte_unidad60_20261021.json) | Dieciséis fallos preservados; recuperación única con el mismo contador y límites |
| [Escenario de sesenta minutos](resultados_unidad60_20261021.md) | Siete respaldos y una abstención; 64 intentos acumulados y reanudación sin generar |
| [Entrega íntegra de Física 10.º](entrega_unidad_fisica10_20261021.md) | Ocho objetivos respaldados bajo el escenario propuesto de nueve encuentros; originales y abstenciones conservados |
| [Revisión visual V4](revision_visual_v4.md) | Escritorio comprobado; móvil y descarga real pendientes por bloqueo del controlador |

Las contrapartes JSON conservan resultados por pregunta/caso, hashes y contabilidad. Los reportes no convierten pruebas sintéticas en validación educativa ni permiten presentar datos V3 como V4. Las cachés, índices y checkpoints operativos quedan fuera de Git.
