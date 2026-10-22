# Aplicación curricular de Ciencias

La interfaz adapta el HTML aportado por el usuario al producto V4 real. Reutiliza su identidad visual,
menú lateral, paneles, tarjetas y recorrido; reemplaza los datos y procesos de demostración por consultas
al grafo y sus expedientes. [Contrato de la aplicación](../specs/17_aplicacion_curricular.md).

## Iniciar

```bash
uv sync --extra dev --extra pdf --extra rag --extra api --extra motor
uv run gskg datos restaurar --en-repo  # sólo si el corpus no está repuesto
uv run gskg servir --puerto 8010
```

Abrir `http://127.0.0.1:8010/app/`. OpenAPI: `http://127.0.0.1:8010/docs`.
La restauración rechaza raíces que ya existen; no repetirla sobre el corpus repuesto.
La aplicación no necesita claves nuevas ni llama a Vertex para consultar, exportar o compilar briefs.

## Recorrido

- **Inicio:** fuentes, grafo, revisión, currículo y contenido, con los conteos del snapshot.
- **Monitoreo nacional:** balance curricular por grado y tipo de nodo. LXP y territorio se muestran
  sin integración porque no hay resultados escolares conectados.
- **Corpus:** documentos registrados o citados por los expedientes, con SHA, usos y enlaces disponibles.
- **Grafo 3D:** relaciones reales, filtros de grado/disciplina/texto, giro, zoom, detalle y tabla accesible.
- **Revisión:** dictámenes de ciencia, currículo, psicopedagogía y adversarial, con rondas y criterios.
- **Curricularización:** comparación por fila, indicadores, evaluación, didáctica, fases y alertas del
  original. Exportación CSV o Excel íntegra, sin fórmulas ejecutables aportadas por contenido.
- **Templates y Brief:** elegir hasta veinte objetivos y compilar briefs Markdown. Se organizan los
  textos ya respaldados; no se presentan como nuevas clases generadas o validadas.
- **Administración:** snapshot, archivos y sus SHA; lectura del gasto reservado cuando existe ledger.
  No crea cuentas ni presupone una sesión institucional autenticada.

No hay calendario oficial de 160 días ni métricas de escuelas en el grafo V4: no se heredan del HTML
adjunto. La aprobación institucional continúa separada de los dictámenes automáticos.

## Reproducibilidad

Los assets están dentro del paquete Python. No hay un servidor de frontend, compilación npm ni CDN.
Inter se distribuye con su licencia OFL, conservada en `interfaz/estaticos/OFL-Inter.txt`.
El endpoint `/api/v4/interfaz/resumen` identifica el snapshot; los detalles y exportaciones corresponden
a esa misma generación. Si un archivo publicado cambia, reiniciar sólo después de verificar la nueva
publicación; la instancia no adopta silenciosamente otra generación.

## Verificación de entrega · 22 de octubre de 2026

La versión final pasó **1.387 pruebas en 266,07 segundos**, incluidas 27 pruebas nuevas para la
aplicación y sus límites. Ruff comprobó `src`, `tests` y `.claude/hooks`. Los 18 controles de calidad y
determinismo del grafo volvieron a pasar. Los módulos JavaScript superaron la comprobación de sintaxis.

Por HTTP contra el servidor real se cotejaron las **1.020 filas** con el JSON curricular del snapshot:
identidades, objetivos originales y grados coinciden. Se preservan **1.013 propuestas de Ciencias**,
**siete filas fuera de alcance** y **treinta alertas científicas del original**. Las 35 fuentes tienen
35 SHA distintos, ninguno ausente. El subgrafo inicial contiene 260 nodos y 633 relaciones reales,
con extremos presentes, incluidos temas, unidades y propuestas. No se inventaron prerrequisitos.

Se comprobó la rectificación K41 de Biología 11, con su alerta y enmienda, y la compilación de un brief
de cinco fases. El Excel descargado por HTTP tiene 1.021 filas con encabezado, ninguna fórmula
procedente de contenido y la misma identidad del snapshot. OpenAPI incluye el contrato de briefs.

Se recorrieron las ocho pantallas en navegador. Se comprobaron el filtro por grado, el detalle
original/propuesta con alerta y la selección/compilación de un brief. La interfaz conserva un modo
oscuro local, menú adaptable, foco del modal y alternativa tabular al canvas. La revisión visual se
realizó en escritorio; no se presenta como una auditoría completa de accesibilidad o de dispositivos.

Antes y después de las consultas, exportación y compilación de briefs, el ledger conservó **668
invocaciones** y exactamente el mismo SHA-256:
`3ad9b798421a8b463f8d3dd924498330b42ddbd483ca4f774c5386bb74f722ae`.
No hubo nuevas llamadas a Vertex ni modificaciones del snapshot o sus originales.

El wheel final contiene **206 archivos**, incluidos todos los assets y la licencia de Inter, sin PDF,
Excel, SQLite ni credenciales. SHA-256:
`4e642c89e1ee9cf154f8eb4faac573316d0ca5e0d5c33e27d67768e655151eba`.
Los datos restaurados para ejecutar la aplicación permanecen ignorados por Git y son recuperables
desde la generación institucional fijada; el nuevo commit distribuye únicamente código y documentación.
