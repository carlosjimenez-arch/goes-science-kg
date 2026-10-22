# Materialización y consulta del producto V4

El paquete `producto/` construye publicaciones aisladas del grafo histórico. No
modifica las fuentes, `config/mallas.yaml`, las decisiones anteriores o la API
histórica; tampoco activa una versión por el solo hecho de escribirla.

## Contrato operativo

```python
import json
from pathlib import Path

from goes_science_kg.curriculo import cargar_curriculo
from goes_science_kg.curriculo.catalogacion import CatalogoDisciplinas
from goes_science_kg.producto import cargar_producto, construir_producto

curriculo = cargar_curriculo()
# El comando de catalogación conserva catalogo, ejecucion_id y consumo.
# Aquí se valida el objeto "catalogo" del artefacto, no el envoltorio.
artefacto = json.loads(Path("data/producto/V4/catalogo_disciplinas.json").read_text(encoding="utf-8"))
catalogo = CatalogoDisciplinas.model_validate(artefacto["catalogo"])
resultado = construir_producto(
    curriculo,
    catalogo,
    destino=Path("data/producto/V4"),
)
producto = cargar_producto(Path("data/producto/V4"))
# producto.ruta_grafo es la ruta estable de esta generación concreta.
```

La entrada exige versión V4, exactamente 1020 IDs únicos y correspondencia completa
entre catálogo, huella curricular, filas, hojas y agrupaciones. El catálogo debe
declarar `modo="completo"` y `piloto_superado=True`; un piloto no puede materializar
el producto. Se rechazan coincidencias sin las dos lecturas exigidas, disciplinas
asignadas a abstenciones, herencia de asignaturas declaradas donde la malla solo
declara Ciencias y metadatos curriculares incompatibles con sus celdas.

El constructor rehidrata encabezados y celdas de las 1020 filas desde los archivos
autorizados, comprobando SHA256, tipo, valor original, valor de ancla combinada y
coordenadas. La raíz V4 se autoriza mediante `raiz_v4`, cuyo valor predeterminado
es `insumos/v4`; las rutas del metadato no otorgan permisos. La comprobación real
leyó 11 archivos y procesó 11 libros una sola vez, 1,96 MB comprimidos. Verificar
esas celdas tomó aproximadamente 3,3 segundos en la máquina de desarrollo.

## Grafo y significado de sus estados

Cada fila conserva su ID `CURRICULO:V4:<hash>` como ID del nodo Tema. Sus propiedades
incluyen todos los campos ricos, fases, celdas, `campos_por_celda`, clasificación
completa y `disciplinas`. La fuente conserva documento, hoja, fila y las coordenadas
explícitas. Hay nodos nuevos Unidad y aristas `EN_UNIDAD`, además de grado, fuentes
y asignaturas.

`Nodo.asignatura` se establece únicamente cuando hay una disciplina. Una fila
multidisciplinar conserva la lista y una arista `DE_ASIGNATURA` por disciplina.
Fuera de alcance y abstención conservan el Tema y su fuente, con lista vacía y
estado explícito. No desaparecen de la entrega ni reciben una disciplina ficticia.
El runtime excluye esas filas del contexto recuperado por el buscador.

El diagnóstico distingue declaraciones y ausencias del insumo de candidatos y
alineaciones verificadas. Los candidatos no se publican como vínculos. El archivo opcional de
conocimiento añade sólo relaciones semánticas admisibles, con su cobertura separada; no hay
relaciones reales juzgadas ni publicación activa todavía. No crea `CUBRE`. Una competencia PISA escrita en una celda o una
coincidencia temática con TIMSS no demuestra desempeño ni cobertura. Las ausencias
describen esta entrega; no prueban que algo no se enseñe.

Las alertas de publicación son observaciones pendientes. Incorporan SHA y valores
de celdas rehidratadas, sin convertir la descripción de una observación en dictamen
científico. Las ocho hojas sin Aproximar afectan **138 filas**: 96 de sexto y 42
de séptimo. Esas alertas muestran los encabezados físicos verificados donde se
constató la ausencia. Las observaciones adicionales se pasan como
`AlertaSolicitada`, con los argumentos nombrados `fila_id`, `campo`, `codigo` y
`descripcion`.

## Referencias explícitas

No se inyecta el grafo V3 automáticamente. Los adaptadores opcionales están en
`producto/referencias.py`:

- `referencias_documentales(catalogo_dimensiones, repositorio)` coteja las anclas
  de las dimensiones con los PDF locales y crea nodos `DimensionDocumental`.
  Conserva edición, institución, estado de publicación, páginas y SHA. Las 22
  dimensiones disponibles son categorías del proyecto; no objetivos oficiales ni
  relaciones de cobertura curricular.
- `cargar_referencias_historicas(directorio)` captura bytes del grafo V3 cotejados
  con su manifiesto, preservando su versión como procedencia histórica.
- `combinar_referencias(*conjuntos)` rechaza identidades superpuestas para exigir
  resolución explícita.

Al incorporar una referencia histórica se descartan Temas y Propuestas anteriores,
sus relaciones y los documentos huérfanos. Los conceptos, prácticas,
prerrequisitos y redes de países conservados quedan marcados como históricos y
no acreditan vínculos con las filas V4. No se hereda `TRABAJA` hacia temas nuevos.
El PISA histórico no se etiqueta como edición final vigente. La referencia final
actual procede exclusivamente del adaptador documental con su edición comprobada.

## Publicación atómica y lectura

```text
<destino>/
  actual.json                  # puntero reemplazado atómicamente
  snapshots/<sha>/
    manifest.json
    nodos.jsonl
    aristas.jsonl
    curriculo.json             # incluye hojas y registros auxiliares
    catalogo.json
    conocimiento.json          # archivo verificable o null
    diagnostico_v4.json
    alertas_v4.json
    publicacion.json
```

El manifiesto separa `version="producto-2"` del formato y
`version_curriculo="V4"`. Registra SHA256 y tamaño de cada uno de los ocho
artefactos, conteos de nodos/aristas y huellas curricular y del catálogo. El puntero
incluye el SHA del propio manifiesto. El ID de snapshot depende del contenido.
El borrador anterior `producto-1` no se migra silenciosamente ni se confunde con la versión V3
del currículo histórico. `conocimiento.json` es obligatorio, incluso sin juicios (`null`).

`producto construir --conocimiento <archivo>` incorpora expedientes consolidados con cuatro lectores.
Rehidrata originales y revalida currículo, catálogo, modelos, cierres y ciclos; el lector repite los
controles estructurales y verifica la correspondencia con el grafo. `RelacionCurricular` mantiene
fila y extremos mediante tres aristas distintas, sin crear relaciones globales de conceptos.
Los expedientes rechazados permanecen en el archivo, sin exponer sus referencias como conocimiento
admitido. [Contrato de conocimiento](../juicios_conocimiento.md).

La escritura usa una carpeta temporal, verifica toda la generación, sincroniza
archivos y publica bajo un bloqueo local antes de reemplazar `actual.json`. Una
interrupción conserva la generación anterior; puede quedar una generación completa
sin seleccionar, que una repetición idéntica reutiliza. No se borran snapshots.
Se rechazan destinos históricos/protegidos y enlaces simbólicos bajo el almacén.

`cargar_producto` captura el puntero una sola vez y comprueba todos los bytes antes
de exponer el resultado tipado `ProductoMaterializado`. También valida correspondencia
entre catálogo y temas ricos, extremos de aristas, estados de clasificación, unidades,
fuentes y ausencia de objetos anteriores. Un cambio posterior del puntero no mezcla
generaciones durante esa carga. Los snapshots son inmutables por contrato; el sistema
de archivos permite cambios, pero una carga posterior los rechaza por hash.

`producto/runtime.py` ensambla el buscador desde los nodos y aristas ya capturados,
sin una segunda lectura del grafo. Las citas se rehidratan de Excel/PDF; modificar
`Documento.texto` no convierte ese metadato en evidencia. Los bloqueos científicos
localizados de `docs/investigacion/alertas_v4.json` se cotejan de nuevo con SHA y
celdas, forman parte de la huella de recuperación y detienen generación antes de
llamar modelos cuando afectan al contexto. Son un artefacto de confianza separado
de las observaciones estructurales del snapshot.

El runtime añade `BuscadorProducto`: `buscar_fila` exige identidad, grado y disciplina admitida y
reúne la fila local con fuentes primarias de sus relaciones admisibles. Cada fuente se rehidrata;
no hay caminos entre filas ni equivalencias de grados extranjeros. La búsqueda general sigue usando
el baseline. Las unidades fijan `Solicitud.fila_id`; el Motor rechaza otro anclaje antes de los jueces.

## Comprobaciones y límites

La [auditoría local vigente](resultados_juicios_locales_2026.json) registra **1.161 pruebas globales
aprobadas** y los controles de conocimiento añadidos después de la primera materialización.
Ruff verificado sobre código, pruebas y hooks. Se probaron mutaciones de cada
artefacto y del puntero, intentos de salir del almacén, escritura interrumpida,
republicación idéntica, clasificación multidisciplinar, rechazo de pendientes,
contexto con texto inyectado y lectura sin volver a abrir un grafo alterado tras
capturarlo. Las 22 dimensiones se probaron contra sus PDF reales, sin red. El
recorrido de bloqueo científico comprobó abstención sobre las 27 filas afectadas
sin ninguna llamada al modelo.

Los hashes comprueban integridad respecto a los manifiestos locales; no aportan
autenticidad mediante firma digital. El lector no vuelve a verificar todo el mundo
exterior al abrir un snapshot: la hidratación verifica las fuentes al citarlas.
Las dos lecturas automáticas no prueban independencia epistemológica, validez
científica o eficacia educativa. Ningún estado del producto equivale a aprobación
del MINED. El constructor y runtime son locales, no crean CI ni modifican la configuración histórica.
La clasificación previa sí usó Vertex con autorización específica, según su registro independiente.

La publicación real seleccionada por `actual.json` es
`2a8d9382c167879c2a42c54b4e015da0e1d7cc5ceb1d908d2c6d8873e7a8cfb5`.
Conserva 1.020 temas, 108 unidades y 22 dimensiones; `conocimiento.json` es null. Pasaron la lectura
íntegra y 133 pruebas focales posteriores. [Verificación real](verificacion_runtime_v4.json),
[catalogación y consumo](resultados_catalogacion_v4.json). El catálogo completo conserva 68 abstenciones;
el runtime no las transforma en evidencia disciplinar utilizable.
