# Revisión visual del explorador V4

> Registro histórico de investigación. Describe el corte y la ejecución indicados en este documento.
> Estado vigente del código, API y métricas: [documentación actual](../README.md) y [calidad](../CALIDAD.md).

Fecha: 21 de octubre de 2026. **Resultado: escritorio y móvil revisados, descarga Markdown sin confirmar.**

## Continuación: vista móvil y corrección

Se revisó el integrado `data/producto/explorador_v4.html` mediante Chrome y CUA sobre un servidor temporal
en `127.0.0.1:8765`, con viewport **390 × 844**. Los filtros grado 10, Física y
`1. La física como ciencia` mostraron ocho registros. La ficha conservó objetivo, indicadores, evidencia,
cinco fases y fuente en el DOM. No hubo errores ni advertencias capturados en esa sesión.

La medición inicial encontró desbordamiento: `scrollWidth=458`, ancho cliente 375 e `innerWidth=390`.
Se localizó en el SHA sin cortes del pie de página. Se añadió `overflow-wrap:anywhere` al pie,
se regeneró el HTML y se repitieron los mismos filtros tras recargar. Resultado: ancho de documento y
ancho cliente **375**, sin desbordamiento. El ancho cliente excluye la barra de desplazamiento.

HTML final: **6.926.672 bytes**, SHA-256
`87dd74fff2a9d648c22349b035e746b9fa4eaa2c29a5bda3e5b570ad8117006a`.
Captura móvil: `data/producto/revision_visual/movil_cua_2026-10-21.jpg`, **40.210 bytes**, SHA-256
`d4f88f1836bb6d676a32b91a7641eadde4e7dcd5310aceef175041208aff8578`.

El clic de `Exportar selección · MD` volvió a agotar la espera del evento de descarga a los 15 segundos;
la ruta conocida `~/Downloads/GOES-curriculo-8-filas.md` no estaba presente. La descarga real sigue sin
confirmar; tampoco se atribuye la incidencia al contenido de exportación sin evidencia suficiente.
No se repitió la llamada nativa de Chrome que se había bloqueado. Se restauró el viewport y se detuvo
el servidor al cerrar la revisión.

![Explorador V4 en móvil, con ocho objetivos de Física](../../data/producto/revision_visual/movil_cua_2026-10-21.jpg)

Las secciones siguientes conservan la primera revisión de escritorio y sus límites históricos.

## Artefacto y entorno

Se generó el HTML con la API final `vista(...)`, el currículo de 1.020 filas, las cinco alertas documentales y el catálogo **piloto** de `/tmp/goes-v4-piloto-low.json`, campo `catalogo`. El piloto contiene 384 asignaciones declaradas, 23 coincidencias automáticas y 613 abstenciones. No se ejecutó catalogación ni se consultó la reserva educativa.

El archivo revisado, `/private/tmp/goes_v4_revision_visual/index.html`, tiene **6.917.839 bytes**.
La captura revisada conserva esta identidad:

`SHA-256 064f07fd9509f7a076210e08a04aee7423fdf4985a0463b2ec91004ee7799ae3`.

El integrado `data/producto/explorador_v4.html` se regeneró después para mostrar nombres legibles
del método de clasificación en lugar de identificadores internos. Esta revisión visual corresponde
a la captura anterior; el cambio de etiqueta se verificó con las pruebas de vista y exportación.

CUA abrió Chrome sobre un servidor temporal limitado a `127.0.0.1:8769`. Se inspeccionaron el DOM y capturas reales. La captura persistida usa un viewport de **1440 × 900**; el área visible excluye la barra de desplazamiento. No hubo publicación ni transferencia a un servicio externo.

## Comprobaciones realizadas

| Comprobación | Evidencia observada | Estado |
| --- | --- | --- |
| Carga inicial | Encabezado V4, 11 fuentes y 126 hojas; contador de 1.020 filas y 613 pendientes; filas con abstención visibles | Verificado |
| Escritorio | Filtros en una fila, botones legibles, lista y ficha en dos columnas; paleta verde y foco visible | Verificado a 1440 × 900 |
| Filtros combinados | Grado 10, Biología, unidad `1. Biomoléculas`, búsqueda `Introducción`: dos resultados, carbohidratos y proteínas | Verificado |
| Selección por teclado | Enter sobre la fila de proteínas cambió el título de la ficha; el foco quedó en `ficha` | Verificado |
| Ficha y trazabilidad | Objetivo, indicadores, evidencia, fases, campos ausentes, archivo, hoja, fila física, celdas, SHA y enlace de Drive presentes en el DOM | Verificado |
| Ausencia de fase | Al seleccionar sexto se mostraron 96 filas; Aproximar figuró ausente, con Explorar en I3 y Reforzar en L3; alerta documental visible | Verificado |
| Alertas localizadas | La ficha de carbohidratos mostró tres alertas: notación de la base C, generalización de biomoléculas y metadata de unidades/temas; conservaron fuente y alcance | Verificado |
| Desbordamiento de escritorio | Lectura del DOM: `scrollWidth > innerWidth` devolvió falso | Verificado en ese estado |
| Consola | Las consultas de advertencias/errores devolvieron listas vacías durante las acciones observadas, incluida la comprobación posterior al clic de exportación | Sin errores capturados; alcance limitado a esta sesión |
| Descarga Markdown | Se pulsó `Exportar ficha · MD`; el evento de descarga esperado no se confirmó en 15 segundos | No confirmado |
| Ancho móvil | No se llegó a aplicar ni inspeccionar un viewport móvil | Pendiente |

## Límite e incidencia de herramientas

Tras el clic de exportación, CUA agotó la espera del evento de descarga. La página seguía operativa, el botón habilitado y la consola sin errores capturados. No se encontró el nombre esperado en las tres rutas de descarga concretas comprobadas. Esto **no demuestra un defecto de la exportación**: no se confirmó si intervino una política de Chrome, un diálogo o la observación de eventos de la extensión.

Para diagnosticarlo se invocó `cua.getApp("com.google.Chrome")`. Esa llamada no devolvió estado de la aplicación,
quedó bloqueada aproximadamente **827 segundos** y fue interrumpida por el coordinador de la tarea.
No se realizaron más acciones de navegación después de la interrupción. El bloqueo impidió completar móvil
y descarga. La revisión no sustituyó esa falta de evidencia por resultados de pruebas de código.

No se modificaron `vista.py`, sus tests ni otros componentes durante esta tanda. No se detectó un defecto material demostrado en la vista de escritorio inspeccionada. Quedan pendientes una captura móvil y una descarga con archivo verificable; tampoco se afirma una auditoría completa de accesibilidad.

Al cerrar se detuvo el servidor temporal y se restauró el viewport normal de Chrome. Estas acciones de limpieza no añadieron comprobaciones visuales.

## Captura conservada

Archivo: `data/producto/revision_visual/escritorio_cua_2026-10-21.jpg`.

`SHA-256 4dee67c40da120a772689e799a2f33e94ca166abce67350904caea067e48516d`.

La captura muestra los filtros combinados, dos resultados, clasificación declarada, foco en búsqueda y el indicador de tres alertas. La lectura detallada de alertas y fases se comprobó además en el DOM; no se presenta una captura móvil inexistente.

![Explorador V4 en escritorio con filtros y alertas](../../data/producto/revision_visual/escritorio_cua_2026-10-21.jpg)
