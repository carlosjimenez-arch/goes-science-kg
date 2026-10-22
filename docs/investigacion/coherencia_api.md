# Coherencia de lecturas de la API

> Registro histórico de investigación. Describe el corte y la ejecución indicados en este documento.
> Estado vigente del código, API y métricas: [documentación actual](../README.md) y [calidad](../CALIDAD.md).

La API fija el grafo al atender la primera petición y verifica sus bytes contra `manifest.json`. La inicialización se serializa con un `Lock`, por lo que peticiones concurrentes no pueden crear instancias de generaciones distintas al arrancar. Valida identificadores, extremos de las relaciones y conteos del manifiesto. El manifiesto, los modelos y el índice GraphRAG proceden de los mismos bytes capturados. No combina un índice antiguo con un manifiesto nuevo.

Los diagnósticos, comunidades y simulaciones históricos no contienen la identidad del grafo que los produjo. Su coexistencia en el repositorio no acredita esa relación. La API no los adopta automáticamente ni escribe atestaciones durante una lectura.

## Publicación utilizable

Los generadores existentes ahora publican un sidecar después de recalcular sus resultados:

```bash
# Diagnóstico y comunidades: publica cada grado de forma independiente.
uv run gskg grados construir

# Recalcula y publica una simulación; no promueve el JSON anterior.
uv run gskg propuesta simular biologia 5 8

# La API sigue siendo de lectura y arranca en localhost.
uv run gskg servir
```

No es necesario reconstruir el grafo para publicar derivados del grafo persistido. Estos comandos sí regeneran entregables; deben ejecutarse cuando se decida publicar esa regeneración. Durante esta intervención no se ejecutaron sobre los datos originales del repositorio.

`grados.construir_grados` y `propuesta.escribir_simulacion` verifican primero que los modelos recibidos coinciden exactamente con las huellas del grafo persistido. Después generan los archivos, comprueban que el grafo y los derivados no cambiaron durante la generación/publicación y escriben el sidecar mediante reemplazo atómico. Si el grafo cambia durante el proceso, no se publica la atestación. El antiguo `propuesta.simular` conserva su función de cálculo en memoria y no publica por sí solo.

Los sidecars viven en `data/grafo/publicaciones_api/`:

- `grado-G07.json` vincula diagnóstico y comunidades de 7.º al par de huellas del grafo.
- `propuesta-biologia-G05-G08.json` vincula una simulación regenerada al mismo par de huellas.

Cada documento incluye versión de formato, identificador de artículo, generador, SHA-256 de nodos/aristas y SHA-256 de los archivos derivados. Se rechazan archivos que no coinciden con su sidecar, artículos ligados a otro grafo y conjuntos incompletos. No se ofrece un comando que atestigüe resultados históricos sin recalcularlos.

La ruta resuelta de publicación debe quedar dentro del repositorio antes de crear el archivo temporal. Un enlace simbólico del directorio de publicaciones o del sidecar hacia fuera se rechaza sin escribir en el destino externo.

## Comportamiento HTTP

| Ruta | Disponibilidad y contrato |
|---|---|
| `/api/salud` | `200` si el grafo es verificable. `alcance: grafo` aclara que no certifica derivados pendientes. |
| `/api/conceptos/{asignatura}/{slug}` | Usa exclusivamente el grafo fijado. Un concepto ausente conserva `404`. |
| `/api/rag` | Usa el índice del mismo grafo; no lee diagnósticos ni propuestas. |
| `/api/grados/{grado}` | `200` solo con diagnóstico y comunidades publicados para ese grafo; `503` si falta la procedencia o cambió el artículo. |
| `/api/rag/global` | Usa las comunidades capturadas del grado verificado; no llama al lector global de archivos mutables. |
| `/api/grados` | Devuelve los grados disponibles. `X-Articulos-No-Disponibles` enumera los omitidos. Si ninguno está disponible, devuelve `503`. |
| `/api/propuestas` | Devuelve simulaciones publicadas y señala omisiones con la misma cabecera. Si solo hay resultados no verificables, devuelve `503`; si no existe ninguna propuesta, devuelve una lista vacía. |
| `/api/propuestas/{asignatura}/{ciclo}` | Consulta una simulación individual; por ejemplo `biologia/G05-G08`. Un artículo no verificable devuelve `503` con el motivo. |

Los cuerpos `200` de los endpoints anteriores conservan su estructura. Los clientes de listas deben comprobar `X-Articulos-No-Disponibles`; una lista parcial no significa que los demás grados o propuestas hayan desaparecido del currículo.

Los errores de publicación usan `503` y `detail.codigo: publicacion_no_disponible`. La invalidez de una propuesta no bloquea otros artículos ni salud, conceptos o recuperación local. La API actual puede servir el grafo histórico verificado aunque todavía no existan sidecars para sus derivados.

## Cambios mientras el servicio está activo

Los bytes cargados se conservan en memoria. Antes de reutilizarlos se comparan con sus archivos de origen:

- Si cambia el grafo o su manifiesto, las lecturas dependientes del grafo quedan rechazadas hasta reiniciar el servicio. No hay recarga implícita.
- Si cambia un artículo ya cargado o su sidecar, ese artículo queda rechazado hasta reiniciar; otros artículos siguen disponibles.
- Un artículo que aún no se había cargado puede publicarse durante la ejecución si corresponde al mismo grafo fijado. Su primera lectura captura y verifica el conjunto completo.
- Restaurar los bytes después de que se detectó una mutación no elimina el rechazo dentro del proceso. Reiniciar crea una instancia nueva que vuelve a verificar las publicaciones.

La comparación se basa en contenido, no en fecha de modificación. Una escritura que conserva los mismos bytes no cambia la identidad del artefacto. Ningún endpoint devuelve diagnósticos o propuestas leídos de nuevo junto a modelos cacheados de otra generación.

## Límites y validación

El sidecar prueba la relación declarada por un generador que acaba de ejecutar con esos modelos y protege la integridad de sus archivos. No demuestra la corrección científica de una propuesta ni captura por sí solo todas las reglas auxiliares del análisis; no debe interpretarse como una validación educativa completa. Un operador con permiso para alterar código, grafo y sidecars puede alterar la publicación: no son firmas criptográficas de una autoridad externa.

Se leen y comparan los archivos del grafo en cada petición, y los del artículo solicitado antes de reutilizarlo. Esto añade E/S proporcional a su tamaño; evita depender únicamente de timestamps. Los datos del repositorio caben en memoria. Una publicación masiva necesitará directorios inmutables y un cambio atómico de versión para evitar ese coste, manteniendo los mismos contratos de identidad.

La [medición local](metricas_api_local.json) usó `TestClient`, 30 repeticiones secuenciales calientes y una sola consulta de fotosíntesis/respiración en sexto, sin red TCP ni GCP. Medianas: recuperación directa 1,619 ms; salud 1,343 ms; RAG por API con verificación 4,050 ms (p95 4,402 ms). La primera petición de salud, incluida la carga, tomó 119,936 ms. Es una referencia de costo local, no una prueba de carga ni de latencia de producción. El JSON conserva muestras y huellas del código/grafo.

No hay un bloqueo de escritura sobre procesos externos. Una respuesta usa los bytes coherentes ya capturados aunque un escritor empiece a modificarlos después de la última comprobación; la siguiente lectura detectará el cambio. No hay mezcla de bytes nuevos dentro de esa respuesta.

`tests/test_api_publicacion.py` regenera grados en un repositorio temporal y comprueba contratos `200`, mutaciones posteriores de manifiesto/nodos/aristas/JSON, rechazo inicial de derivados ajenos, invalidez por artículo, publicación posterior a regeneración y prevención de publicación si cambia el grafo durante el cálculo. Las fuentes y entregas originales no se modifican en esas pruebas.

Verificación de esta intervención: **132 pruebas focales aprobadas** (API, publicaciones, grados, propuestas, simulador y catálogo CLI), con Ruff correcto en los módulos y tests afectados. Incluye concurrencia de inicialización y rechazo de enlaces de publicación a rutas externas.
