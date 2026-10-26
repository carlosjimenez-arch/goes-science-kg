# Aplicación curricular de Ciencias

La interfaz adapta el HTML aportado por el usuario al producto V4 real. Reutiliza su identidad visual,
menú lateral, paneles, tarjetas y recorrido; reemplaza los datos y procesos de demostración por consultas
al grafo y sus expedientes. [Contrato de la aplicación](../specs/17_aplicacion_curricular.md).

## Iniciar

```bash
uv sync --frozen --all-extras
uv run --frozen gskg servir --puerto 8010 --sincronizar   # equivale a `make producto`
```

`--sincronizar` descarga desde GCS lo que falte según los recibos (corpus, biblioteca docente y entrega de
guiones) y nunca sobrescribe datos existentes; también puede ejecutarse aparte con `gskg datos sincronizar`.
Abrir `http://127.0.0.1:8010/app/`. OpenAPI: `http://127.0.0.1:8010/docs`. El servicio sólo escucha en
loopback; `--permitir-red` lo expone fuera de la máquina, pero la API no autentica y en ese caso debe ir
detrás de un proxy con control de acceso. La aplicación no necesita claves nuevas ni llama a Vertex para
consultar, exportar o compilar briefs. [Datos en GCS](DATOS_EXTERNOS.md).

## Recorrido

- **Inicio:** fuentes, grafo, revisión, currículo y contenido, con los conteos del snapshot.
- **Monitoreo nacional:** balance curricular por grado y tipo de nodo. LXP y territorio se muestran
  sin integración porque no hay resultados escolares conectados.
- **Corpus:** documentos registrados o citados por los expedientes, con SHA, usos y enlaces disponibles.
- **Grafo 3D:** relaciones reales, filtros de grado/disciplina/texto, giro, zoom, detalle y tabla accesible.
- **Progresión 2.º–11.º:** cómo se introduce y refuerza cada concepto, patrones de refuerzo, prerrequisitos
  tardíos clasificados, entrada a bachillerato y trayectorias con sus filas. Vista original o con propuestas.
  [Método y límites](PROGRESION_2_11.md).
- **Revisión:** dictámenes de ciencia, currículo, psicopedagogía y adversarial, con rondas y criterios.
- **Curricularización:** comparación por fila, indicadores, evaluación, didáctica, fases y alertas del
  original. Exportación CSV o Excel íntegra, sin fórmulas ejecutables aportadas por contenido.
- **Templates y Brief:** elegir hasta veinte objetivos y compilar briefs Markdown. Se organizan los
  textos ya respaldados; no se presentan como nuevas clases generadas o validadas.
- **Materiales docentes:** preparaciones por objetivo y unidad, paquetes históricos y bancos de actividades,
  experimentos, dificultades y microtemas, con descarga Markdown/JSON y enlace a la fila curricular.
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
La compilación de briefs se invalida al cambiar formato, objetivos o visita; una respuesta tardía no
restablece resultados anteriores. Las exportaciones Excel del mismo producto conservan los mismos
bytes, con fechas internas fijas y texto seguro en todas las hojas, incluida la metadata de control.

## Revisión de API y calidad · feat/api

La marca de la aplicación es GOEs · Departamento de AI · 2026. El CSS principal es idéntico al bloque
`style` del HTML aportado; se conservaron los estilos y se adaptaron los datos a Ciencias. La referencia
`eor-api` ya se revisó; la [comparación de ingeniería](REFERENCIA_EOR_API.md) explica la adaptación.

Las rutas `/health/live` y `/health/ready` separan proceso y disponibilidad de datos. Una raíz sin
corpus mantiene accesibles `/app/` y `/docs`, pero las consultas responden 503 con `estado: sin_datos`
y «No hay datos disponibles». Los errores históricos tampoco exponen rutas del servidor.
Las identidades que contienen `/`, como `CON:fisica/sistema-internacional-unidades`, se resuelven
completas. OpenAPI describe las respuestas de filas, documentos, grafo y briefs con contratos tipados.

La capa HTTP delega en `ServicioInterfaz`, `RegistroActividad` y el lector de publicaciones. Los índices
reutilizan texto normalizado y relaciones por nodo. Una campaña ausente conserva `reserva_usd: null`;
una ausencia de telemetría no se muestra como gasto cero. Las descargas CSV y Excel conservan
`X-Snapshot-ID` y el navegador rechaza otra generación.

Las respuestas gestionadas incluyen `X-Request-ID` y el tiempo hasta iniciar la respuesta en
`Server-Timing`. Los eventos del middleware GOEs usan plantillas de ruta, estado y duración sin
incorporar valores de consulta, cuerpos o datos de usuario. Se emiten al logging local existente.

Las pruebas y la cobertura vigentes se publican en [medicion.json](badges/medicion.json) y en los badges del
README. La CI ejecuta contratos portables en Python 3.11 y 3.14; su estado remoto se consulta en el badge
del README.

La biblioteca docente vigente tiene 3.837 registros (guiones publicados, preparaciones por objetivo y por
unidad, y material histórico sin migrar sus dictámenes); se consulta en `/api/v4/materiales` y su OpenAPI.
Consultarla no consume Vertex. [Detalle, almacenamiento y pruebas](MATERIALES_DOCENTES.md).
