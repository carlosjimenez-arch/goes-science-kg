# Documentación · GOEs AI · 2026

Estado vigente de la rama `feat/api`: un solo producto que integra la API, la aplicación, la biblioteca docente,
el código de guiones y la progresión 2.º–11.º sobre la publicación V4 `producto-4`. Los datos viven en
`gs://goes-ai-kg-artefactos/ciencias/v4/` y se traen con `gskg datos sincronizar`. Las métricas verificadas de
código están en [medicion.json](badges/medicion.json). La continuidad está en [HANDOFF](../HANDOFF.md).

| Necesidad | Documento |
|---|---|
| Instalar y traer los datos del bucket | [Datos en GCS](DATOS_EXTERNOS.md) y [verificación GCS](VERIFICACION_GCS.md) |
| Ejecutar la aplicación y consultar su API | [Aplicación de Ciencias](APLICACION_CIENCIAS.md) |
| Operar comandos y presupuestos | [Operación](OPERACION.md) |
| Entender módulos, contratos y resultados | [Arquitectura](ARQUITECTURA.md) |
| Aplicar estilo, pruebas y métricas | [Calidad](CALIDAD.md) y [referencia eor-api](REFERENCIA_EOR_API.md) |
| Revisar protección de archivos y secretos | [Auditoría de versionado](auditoria/GITIGNORE_2026.md) |
| Revisar la auditoría vigente de producto | [QA de producto 2026-10-25](auditoria/QA_PRODUCTO_20261025.md) |
| Preparar clases | [Guiones V4](CLASES_V4.md) y [materiales docentes](MATERIALES_DOCENTES.md) |
| Ampliar paquetes con autoría Vertex y revisión por versión | [Piloto, fuentes y presupuesto separado](AMPLIACION_VERTEX_CIENCIAS_V4.md) |
| Usar la edición local corregida y los cinco recorridos finales | [Entrega didáctica sucesora](ENTREGA_DIDACTICA_V2.md) y [criterios de pedagogía y medición](PEDAGOGIA_CIENCIAS_V4.md) |
| Entregar en el Escritorio y comprobar calidad antes de copiar | [Despacho verificado](DESPACHO_CIENCIAS_V4.md) y [reglas del repositorio](../AGENTS.md) |
| Ver cómo se introducen y refuerzan los conceptos | [Progresión 2.º–11.º](PROGRESION_2_11.md) |
| Entender juicios y alineaciones | [Conocimiento](juicios_conocimiento.md) y [alineación](alineacion.md) |
| Consultar contratos | [Especificaciones](../specs/README.md) |

`investigacion/` conserva sólo las auditorías de fuentes que cita la configuración:
[fuentes primarias](investigacion/auditoria_fuentes_primarias.md),
[referentes operativos](investigacion/referentes_operativos_2026.md),
[Inglaterra](investigacion/curriculo_inglaterra_2026.md), [Singapur y Japón](investigacion/curriculos_sg_jp_2026.md)
y el [memorando educativo](investigacion/educacion.md). Los informes de investigación, cierre y QA anteriores
están en el historial de Git (commit `022efed`). Las especificaciones 00–15 explican el pipeline anterior; 16–19
definen el producto V4, la aplicación, la biblioteca y los guiones.
