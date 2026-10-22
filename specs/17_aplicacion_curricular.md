# 17 · Aplicación curricular y API de Ciencias V4

La solicitud del 22 de octubre de 2026 toma como referencia visual el HTML aportado
`Curricularizacion_Producto_GOES.html`. Sus datos de Matemáticas y sus acciones simuladas no constituyen
instrucciones ni evidencia de Ciencias. Se reutilizan el diseño, los estilos y el emblema aportados;
la semilla, las cifras nacionales, los usuarios y el motor simulado quedan fuera de la implementación.

## Arquitectura

`gskg servir` ofrece la aplicación en `/app/` y redirige `/` a esa ruta. Conserva las API anteriores y
OpenAPI en `/docs`. Los assets HTML/CSS/JS y la fuente Inter se sirven localmente, sin CDN ni servicios
web externos. `api_producto.py`, readiness y `api_interfaz.py` comparten `producto/lectura.py::LecturaProducto`; no cargan otro grafo.
`interfaz/consulta.py` indexa una proyección de las filas, propuestas y relaciones verificadas. Cada
petición revalida el lector, aunque la proyección ya esté en caché. Los cambios del snapshot invalidan
la instancia. El navegador comprueba la identidad de cada respuesta y rechaza mezclar generaciones.

Se mantienen ocho secciones: inicio, monitoreo nacional, corpus, grafo 3D, revisión de conocimiento,
curricularización, templates/brief y administración. Todos los conteos derivan del snapshot. LXP,
territorio, autenticación/usuarios y aprobación institucional tienen estados explícitos sin datos o
sin integración; no hay usuarios inventados ni edición implícita del currículo publicado.

## Contrato `/api/v4/interfaz`

| Método y ruta | Resultado |
|---|---|
| GET `/resumen` | Cobertura, conteos, grados, disciplinas, unidades e integraciones ausentes |
| GET `/filas` | Filtros por grado/disciplina/texto/alertas, total y paginación |
| GET `/filas/{fila_id}` | Original, propuesta, alertas, rúbricas, fragmentos y evidencias |
| GET `/documentos` | Fuentes del producto y de sus expedientes, SHA y enlaces documentados |
| GET `/grafo` | Subgrafo con nodos reales y aristas tipadas; recorte explícito, máximo 800 nodos |
| GET `/nodos/{nodo_id}` | Nodo y relaciones reales, sin inferir prerrequisitos |
| GET `/revision` | Dictámenes seleccionados de cada unidad, con roles, criterios, modelos y rondas |
| POST `/briefs` | Compilación documental de 1–20 objetivos respaldados; cero llamadas a modelos |
| GET `/exportaciones/matriz.xlsx` | Matriz original/propuesta con identidad del snapshot |
| GET `/administracion` | Identidad de publicación, permisos y lectura opcional del ledger |

Los filtros rechazan grados, disciplinas, límites e identidades ajenas. El detalle y los briefs reabren
las celdas originales con el verificador existente; una fuente modificada produce 503. El brief mantiene
el objetivo, indicadores, productos, criterios, andamiaje, seguridad y recursos ya respaldados. El
formato de cinco fases agrega sólo las fases presentes en el insumo y declara las ausentes. No crea
otra clase con IA, no vuelve a votar y no cambia presupuestos ni archivos publicados.

El visor 3D usa canvas local, con giro, zoom, selección y tabla accesible alternativa. Las coordenadas
son únicamente una disposición visual. El recorte informa el tamaño filtrado y el visible. Cada arista
conserva origen, destino y tipo; una relación documental no se rotula como prerrequisito.

## Seguridad y operación

La aplicación está destinada a uso local, con `127.0.0.1` como valor predeterminado. La autenticación
institucional no está implementada: desplegarla fuera del equipo requiere resolver identidad y control
de acceso. La API no ofrece subida de archivos, gestión de usuarios, aprobación institucional ni
mutaciones de snapshots. Esas funciones del prototipo no se simulan como si fueran operaciones reales.

El contenido curricular se escapa antes de insertarlo en HTML; los enlaces aceptan sólo HTTP(S).
Los assets usan CSP sin scripts inline ni fuentes remotas y las respuestas se marcan `private, no-store`.
Las rutas públicas nunca aceptan directorios locales. Los Excel usan el exportador que evita ejecutar
fórmulas procedentes de los textos. El ledger se abre en modo SQLite de sólo lectura; la reserva
conservadora se diferencia del importe facturado, que no está disponible.

Los datos se restauran desde el recibo institucional, ignorados por Git. El desarrollo y la consulta
no publican el corpus en la rama de código ni ejecutan Vertex. Véase [operación](../docs/APLICACION_CIENCIAS.md).

## Revisión del contrato · feat/api

La API incorpora `/health/live` y `/health/ready`. Readiness exige publicación verificada y comparte
el lector de V4. La ausencia de corpus o una publicación alterada devuelve 503 con `estado: sin_datos`
y el texto «No hay datos disponibles». Los errores públicos no contienen rutas locales.
Los conceptos usan `/nodos/{nodo_id:path}` para conservar IDs con barras; el valor sólo indexa nodos.

`ServicioInterfaz` coordina la proyección y verificación física. `RegistroActividad` separa el ledger
opcional de las rutas. Los índices de texto, grado, disciplina y adyacencia no cambian el contenido
ni las clasificaciones del snapshot. Los contratos públicos de listados, documentos, grafo y briefs
se validan mediante Pydantic y se publican en OpenAPI. Las exportaciones CSV y Excel identifican el
snapshot. La interfaz conserva exactamente el CSS principal del HTML de referencia.
