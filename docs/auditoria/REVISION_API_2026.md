# Auditoría de homogeneización y API · GOEs · 2026

Fecha: 22 de octubre de 2026. Rama: `feat/api`. Commit de partida:
`d971920bde3d6adedb5a6160fce963e01e277685`. Los cambios se mantienen revisables en el árbol de trabajo;
no se publicaron commits ni se hicieron llamadas a modelos.

## Alcance y evidencia

Se inventariaron código, imports, CLI, contratos, assets y documentación del repositorio. El inventario
se reproduce con `make auditoria` y se conserva en [inventario.json](inventario.json). La comparación
AST se encuentra en [compatibilidad_ast.json](compatibilidad_ast.json): 174 módulos existentes conservan
su estructura ejecutable al excluir docstrings; dieciséis incorporan cambios funcionales de API,
índices, SQLite, respaldo, exportación o presupuesto. No se interpreta el AST como prueba absoluta de equivalencia: los docstrings
pueden cambiar descripciones de esquemas y huellas de ejecución.

El paquete actual tiene 193 módulos Python. Ruff comprueba formato, imports y documentación pública;
los docstrings mantenidos de producción, pruebas y hooks se escriben en inglés. Los comentarios
extensos que explicaban decisiones anteriores se conservaron como notas de implementación.
No se introdujo una clase por cada transformación: los servicios encapsulan estado y dependencias;
las reglas puras permanecen como funciones.

La carpeta de referencia `eor-api` fue inaccesible por permisos de macOS, también fuera del sandbox.
No se afirma haberla leído ni haber reproducido exactamente su organización. Se aplicó una separación
explícita de rutas, servicios, contratos y lector de publicación sobre el proyecto accesible.

## Datos reales y correcciones

La revisión física e independiente comprobó el snapshot
`e92bc700d78f0f559671acc62f559f9e5176b09c3341a47c575c640195022008`:
1.020 filas originales, 1.013 propuestas de Ciencias, siete fuera de alcance, 108 unidades, 2.327 nodos,
7.304 relaciones y 35 documentos con sus bytes/SHA cotejados. Las treinta alertas del original se
conservan. La campaña permanece en 668 invocaciones y USD 731,1485125 de reserva; no es factura.

| Hallazgo | Corrección y evidencia |
|---|---|
| IDs de conceptos con `/` recibían 404 | Convertidor de ruta que conserva la identidad completa; regresión y nodo real comprobados |
| Errores históricos exponían rutas locales | Respuesta pública genérica 503/sin_datos; detalle limitado al logging |
| Un puntero JSON de tipo incorrecto producía 500 | Validación explícita de objeto e identidad string; cinco variantes inválidas cubiertas |
| Una campaña ausente parecía gasto cero | Estado sin_datos, reserva y facturación null; sin creación de ledger |
| URLs documentales malformadas rompían la vista | Rechazo de autoridades inválidas sin excepción interna |
| CSV carecía de identidad en la descarga | Cabecera X-Snapshot-ID, como en Excel |
| Una respuesta antigua sobrescribía datos de otra vista | Confirmación conjunta de HTML/datos después del guard de navegación; dos regresiones Node |
| Conexiones SQLite permanecían abiertas | Cierre explícito después de commit/rollback en ocho módulos; 121 regresiones y QA incremental |
| El respaldo omitía recursos de la interfaz y de calidad | Selección de JS/CSS/fuente, imágenes, scripts y workflow; restauración sintética byte a byte |
| Una compilación tardía restituía un brief obsoleto | Invalidación por formato, selección y visita; seis regresiones Node en el conjunto actual |
| Excel idéntico cambiaba de bytes y no protegía metadata | Guardado determinista y texto seguro en todas las hojas, con regresiones de reloj y fórmulas |
| Una base alternativa heredaba alertas de otro checkout | Configuración de alertas derivadas inyectada desde la base; alerta incompatible produce 503 |
| Dos adaptadores superaban un presupuesto JSONL compartido | Lectura/reserva bajo flock y fsync antes del proveedor; pruebas entre instancias y procesos sin red |

`LecturaProducto` centraliza carga e invalidación. Readiness comparte el lector de los routers V4;
`/health/live` no presupone corpus. `ServicioInterfaz` coordina proyección y originales y
`RegistroActividad` materializa lecturas SQLite en modo sólo lectura. Los contratos Pydantic hacen
explícitas las respuestas de filas, documentos, grafo y briefs.

La API sin corpus conserva `/app/`, OpenAPI y liveness, mientras que las consultas V4 y las históricas
responden 503 y «No hay datos disponibles». Los resultados escolares, territorio, usuarios y
aprobación institucional siguen sin fuente conectada y no se simulan.

## Compatibilidad y limpieza

`ingesta/extraccion.py` e `ingesta/estructurados.py` se conservan byte a byte respecto al commit de
partida. Su implementación identifica evidencia archivada. La revisión detectó que traducir sólo
el docstring invalidaba el runtime; se restituyeron esos cambios, sin sustituir hashes esperados,
perfiles, fuentes, dictámenes ni snapshots. Esos dos módulos mantienen sus docstrings históricos.
Una migración de extracción debe ser explícita y versionada.

Se retiró `refuerzo_excel.py`: ningún import, comando CLI o prueba lo consumía; su entregable V3
estaba desconectado y la entrega V4 usa exportadores activos con procedencia. La especificación 15
explica la retirada. `cli/__main__.py` se conserva como entrada pública aunque no tenga imports
entrantes. No se borraron documentos de evidencia ni fuentes por antigüedad o ausencia de imports.

README, continuidad y convenciones describen el estado actual. Los documentos de investigación,
los cierres anteriores y las specs V1–V3 están rotulados con su alcance histórico. La distinción
preserva decisiones auditables y evita presentar sus cifras como métricas actuales.

## Eficiencia

[Microbenchmark de selección](benchmark_consultas.json): cinco consultas y veinte repeticiones por
consulta, mismo snapshot e identidades seleccionadas idénticas. La mediana bajó de 0,9917 a
0,0497 ms; el percentil 95 de 18,2761 a 0,3795 ms. Se midió selección en memoria, excluyendo HTTP,
serialización, carga inicial e I/O de verificación. No representa una garantía de latencia de la API.

Los índices reutilizan texto normalizado, conjuntos de grado/disciplina y aristas por nodo. Las
fuentes y el lector siguen verificándose: la mejora no elimina controles de procedencia.

## Verificación y límites

La línea base pasó 1.387 pruebas. La entrega final, después del segundo QA, pasó **1.408 pruebas Python**, sin fallos ni
omisiones, en 413,19 segundos y sin advertencias. La cobertura de líneas medida es **79,37 %**
(15681 de 19757 líneas ejecutables). Las métricas integrales finales se conservan en
[medicion.json](../badges/medicion.json), con fecha, denominadores y huella del código. Las seis
regresiones JavaScript pasan en Node.js 24; la sintaxis de los cuatro módulos también es válida.
El conjunto portable actual pasó 149 contratos sobre una copia sin corpus y sin credenciales;
registró una advertencia de deprecación del SDK Google, sin fallos.
La CI de Python 3.11/3.14 está configurada; su ejecución remota queda pendiente de publicar la rama.

Se recorrieron las ocho secciones en navegador con el corpus real, se comprobó paginación y el modal
original/propuesta. [Captura del inicio](app-goes-2026.png). El CSS principal es idéntico al bloque style
del HTML aportado, SHA `a572956734a42bbd77ec1c787b7d0f748c8029f858fb8a35a6e996305ec719f1`.
La revisión visual fue de escritorio; no constituye una auditoría completa de accesibilidad o móvil.

El wheel se construye con 208 archivos, incluidos servicios y assets; no contiene corpus, PDF,
Excel, SQLite, credenciales ni el exportador retirado. Las consultas y mediciones conservaron el ledger
SHA `3ad9b798421a8b463f8d3dd924498330b42ddbd483ca4f774c5386bb74f722ae`.
El [QA independiente inicial](QA_INDEPENDIENTE.md) cerró sus hallazgos y revisó el ciclo de vida SQLite.
La [segunda revisión independiente](QA_SEGUNDA_REVISION.md), pedida expresamente por el usuario,
reprodujo y revalidó cinco fallos adicionales. Conserva su alcance y sus límites de inspección.

Las pruebas evalúan integridad y comportamiento de software. No acreditan aprobación institucional,
calibración educativa ni eficacia en aula. La cobertura de líneas tampoco significa que se hayan
probado todas las combinaciones posibles.
