# Calidad y mantenimiento · GOEs AI · 2026

El estilo del proyecto usa Python 3.11+, Ruff y pytest. La referencia visual es el HTML curricular
aportado; la referencia de estructura `eor-api` ya se revisó tras recuperar el acceso local.
La [comparación y adaptación](REFERENCIA_EOR_API.md) explica las decisiones aplicadas a GOEs.
El inventario se reproduce con `make auditoria`.

## Organización del código

Las rutas HTTP validan parámetros y traducen resultados. `ServicioInterfaz` coordina consultas y
verificación de originales; `RegistroActividad` lee SQLite sin mutaciones; `LecturaProducto` fija la
generación publicada y la invalida ante cambios. `ConsultaInterfaz` conserva índices de filas, texto
normalizado, grados, disciplinas y adyacencia. Los contratos Pydantic describen las respuestas del
listado, documentos, grafo y briefs en OpenAPI.

Se usan clases cuando existe estado, caché, una dependencia inyectada o un contrato de dominio. Las
transformaciones puras permanecen como funciones. La modularidad no exige convertir cada función
en una clase ni renombrar identidades públicas de datos.

Ruff aplica imports consistentes, comprobaciones de errores, modernización de Python y formato con
120 columnas, el límite acordado por este repositorio. Los docstrings del código mantenido se
escriben en inglés y Ruff exige documentación en módulos, clases, métodos y funciones públicas. Las notas extensas históricas se conservan como comentarios de implementación.
Los nombres de dominio existentes y los mensajes al usuario siguen en español.

## Excepción de procedencia

`ingesta/extraccion.py` e `ingesta/estructurados.py` conservan exactamente los bytes de la publicación
anterior. Sus hashes identifican el código que produjo evidencia archivada; incluso un cambio de
formato o docstring rompe la verificación del producto actual. Ruff excluye estos dos archivos del
formateo automático. La excepción incluye sus docstrings históricos en español.

`clases/` sigue la misma regla en sus módulos con huella: el entorno de cada protocolo P1–P11 fija los SHA de
`contratos`, `fuentes`, `motor`, `prompts`, `preparacion`, `validacion`, `proveedor`, `operacion`, `edicion`,
`editorial` y `contexto`, y `contexto_agente.py`, `enrutamiento.py` y `complementos.py` comparan su propio
archivo. Esos bytes no se tocan. Los módulos sin huella (`compilacion`, `paquete`, `auditoria`, `publicacion`,
`revision_contenido`) se corrigieron el 25 de octubre para la entrega parcial declarada y para verificar el
parche editorial P11 con el esquema que su propio código envía. Ruff no formatea `clases/` ni exige allí
docstrings, para no reescribir por accidente un módulo con huella.

No se sustituyeron hashes, perfiles, snapshots ni dictámenes para ocultar esa incompatibilidad.
Cambiar esos extractores requiere una migración de extracción versionada, rehidratación de evidencia
y publicación explícita. Tampoco se reanudan checkpoints antiguos con una nueva huella de código.

## Métricas y pruebas

`make cobertura` ejecuta la suite integral, escribe JUnit y cobertura XML y regenera tres badges SVG
locales. [La medición](badges/medicion.json) registra fecha, commit base, huella del código, denominador
de pruebas ejecutadas, aprobadas, omitidas, errores y líneas cubiertas. La aprobación se calcula como
`aprobadas / (recopiladas - omitidas)`; cobertura significa líneas ejecutadas, no eficacia educativa.
Las regresiones JavaScript se ejecutan con `make pruebas-js` (Node.js 24) y cubren respuestas
HTTP fuera de orden: HTML y datos se confirman juntos tras verificar la navegación activa.
La configuración también recoge ramas; el badge de cobertura informa explícitamente líneas.

Las regresiones comprueban también la compilación de briefs frente a cambios de
formato, selección y navegación, la restauración íntegra de assets y herramientas de calidad, y la
igualdad de bytes de las exportaciones Excel. Todas las hojas tratan los textos como texto, incluida
la metadata de control. Una base alternativa resuelve sus alertas derivadas desde su propio `config/`.

El adaptador de embeddings comparte su presupuesto JSONL entre instancias y procesos: adquiere un
bloqueo exclusivo, relee el consumo y persiste la reserva con `flush` y `fsync` antes de invocar el
proveedor. Los resultados y resúmenes usan el mismo ledger; una reserva fallida no se libera.
Las regresiones usan clientes simulados y procesos locales, sin peticiones externas. El bloqueo es
local al sistema de archivos en macOS/Linux, como los demás checkpoints del proyecto.

Los badges son una medición fechada del árbol identificado, no una promesa sobre modificaciones
posteriores. No se muestra Codecov de otro repositorio. El workflow de GitHub conserva JUnit y
cobertura como artefactos y comprueba contratos portables en Python 3.11 y 3.14. El estado remoto se consulta en el badge de GitHub Actions del README; las insignias locales
no lo sustituyen. Los informes de auditoría conservan el estado remoto existente en su fecha de corte.

La medición integral local se verifica con Python 3.14.3 y las dependencias de `uv.lock`. La CI
configura Python 3.11 y 3.14 para contratos portables; no se presenta como verificación del corpus
archivado en ambos entornos. Los extractores conservan también versiones de biblioteca y runtime
en su procedencia.

La suite completa necesita el corpus privado. La suite portable usa datos sintéticos identificados
como tales y prohíbe proveedores Vertex reales desde `tests/conftest.py`. Las dos verificaciones
tienen alcances diferentes y se documentan por separado.

## Limpieza

Se retiró `refuerzo_excel.py`: no tenía importaciones, comandos CLI ni pruebas consumidores y
pertenecía al entregable V3 desconectado. Las exportaciones V4 activas usan
`producto/exportacion_mejoras.py` y `producto/enmiendas_excel.py`. No se borraron mallas, propuestas,
revisiones, fuentes ni corpus. `cli/__main__.py` se conserva como entrada pública aunque un análisis
estático no encuentre imports entrantes.

El 26 de octubre de 2026 se retiraron los informes de investigación, cierre y continuidad ya superados;
siguen en el historial de Git (commit `022efed`). Se conservan las especificaciones y las auditorías de
fuentes que la configuración cita. [Índice documental](README.md).

## Auditorías

El 22 de octubre de 2026 hubo tres barridos QA de la API (revisión inicial, QA independiente y segunda
revisión); sus informes y evidencias están en el historial de Git (commit `022efed`). La auditoría vigente es
[QA de producto 2026-10-25](auditoria/QA_PRODUCTO_20261025.md).

## Versionado y observabilidad

La [auditoría de versionado](auditoria/GITIGNORE_2026.md) valida 49 escenarios de protección y
visibilidad de archivos. Las variantes de secretos, bases y respaldos quedan excluidas sin ocultar
contratos, recibos ni recursos públicos. La huella medida incluye ahora esas reglas, el Makefile y
el workflow de CI. Los [eventos HTTP locales](REFERENCIA_EOR_API.md) correlacionan rutas, estado y
tiempos sin registrar valores de consulta o cuerpos desde el middleware GOEs.
