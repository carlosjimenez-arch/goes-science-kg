# Estado de entrega de Ciencias · 21 de octubre de 2026

La reconstrucción implementa un producto V4 consultable y un motor automático durable con fuentes
verificadas, especialistas, psicopedagogía, revisión adversarial, presupuesto y abstención. El hito
técnico no se presenta como aprobación oficial ni como validación del aprendizaje del currículo completo.

## Evidencia comprobada

| Capacidad | Comprobación |
|---|---|
| Ingesta V4 | Once matrices, 126 hojas, 1.020 filas originales, SHA y celdas verificadas |
| Publicación y API | `producto-3`, 1.191 nodos, 4.136 aristas, nueve archivos; aislamiento del histórico |
| Conocimiento | Quince juicios originales, dos relaciones admitidas; rechazos y abstenciones conservados |
| PISA/ERCE | Cuatro casos auditables, un respaldo documental limitado a su fila; sin votos nuevos |
| Contexto | Lectura primaria completa, citas por ID, reserva de fuentes obligatorias y veto ante cambios |
| Organización por unidades | 108 unidades y 1.020 filas rehidratadas; 853 solicitudes preparadas y 167 detenidas |
| Caso de generación | Una unidad experimental íntegra de Física de décimo, ocho objetivos bajo tiempos propuestos |
| Investigación adicional | NGSS E/F/G, tres PDF y 58 páginas, ediciones y huellas fijadas |

La preparación exhaustiva tardó 3.460 ms localmente y no invocó modelos. Sus 167 sesiones sin solicitud
se explican por 140 clasificaciones pendientes/fuera de alcance o multidisciplinares y 27 filas con
alertas científicas bloqueantes; no se desechan del paquete. Las 138 filas sin columna «Aproximar»
mantienen esa ausencia. La preparación no evalúa la calidad de actividades aún no generadas ni adopta
sesenta minutos como carga oficial. Evidencia institucional:
`docs/investigacion/preparacion_exhaustiva_unidades_20261021.json`.

El [contrato de alineaciones](investigacion/integracion_alineaciones_v4.md) describe publicación,
rehidratación y auditoría. Las [decisiones NGSS](investigacion/progresiones_ngss_20261021.md) impiden
confundir bandas documentales con equivalencias de grados o prerrequisitos individuales.

## Límites del hito

Verificación final: **1.260 pruebas aprobadas en 223,76 s**, Ruff y `git diff --check` en verde.
El checkout separado de sólo código pasó otras **157 pruebas sintéticas en 4,49 s**, sin el corpus V4.
La batería encontró y permitió corregir un problema del hook heredado: `uv` intentaba abrir su caché
fuera del sandbox. Ahora reutiliza la CLI instalada y conserva el fallback con lock fijado; la salida
inválida vuelve a bloquearse. No se desactivaron guardas ni se aceptó el fallo como prueba aprobada.
Se añadieron casos de falsificación de archivos/citas/modelos, mutación de PDF y snapshot,
aislamiento de fila, falta de presupuesto y protección común de destinos. Informe institucional:
`docs/investigacion/verificacion_entrega_20261021.json`.

No se declara terminado el contenido curricular completo. Falta ampliar las relaciones respaldadas y
las unidades generadas a otras áreas; fundamentar progresiones locales; calibrar los jueces con casos
independientes; y resolver los estados pendientes sin modificar los originales. La infraestructura
puede preparar todas las unidades, pero esa disponibilidad no demuestra eficacia pedagógica.

Las ejecuciones conservan contadores, fallos y terminales originales. Esta integración y las pruebas
adicionales consumieron cero nuevas invocaciones de Vertex. Los USD documentados son reservas
conservadoras de experimentos anteriores, no una factura ni un presupuesto reiniciado.

## Entrega pública

Se separa código de corpus institucional. La rama pública parte de la base existente y distribuye
código, pruebas, configuración y documentación, conservando los nuevos insumos y evidencias localmente.
No incorpora como ancestro el commit que contiene el corpus retenido. [Alcance y reproducción](PUBLICACION.md).
No se instaló CI ni se modificaron proyectos, cuentas o buckets de Matemáticas.
