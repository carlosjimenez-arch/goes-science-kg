# 16 · Producto curricular V4

Esta especificación complementa el modelo histórico 02. La versión curricular, la versión documental,
el formato de publicación y la identidad de una ejecución son campos distintos.

## Entradas e identidad

`insumos/v4/` conserva once libros originales de la captura institucional, verificados contra
`insumos/procedencia_v4.json`. `config/mallas_v4.yaml` declara las 126 hojas: 62 curriculares y 64
auxiliares. Las 1.020 filas y sus celdas originales se preservan, sin arrastrar blancos ordinarios ni
interpretar fórmulas como texto científico. Las combinaciones conservan coordenada solicitada y ancla real.

`FilaCurricular` contiene objetivo, indicadores, evidencia, cinco fases con presencia explícita,
conocimiento/contexto, anotaciones locales y procedencia. Una fase ausente no se inventa ni se convierte
por sí sola en un juicio pedagógico. Los códigos PISA/TIMSS de la malla son declaraciones del insumo.

Un tema V4 usa `CURRICULO:V4:<sha256>` derivado de fuente, hoja, fila y contenido. La fuente incluye la
huella completa del libro. Las clasificaciones, relaciones y propuestas V3 no se trasladan a esa identidad.

## Modelo adicional

| Tipo | Identidad | Uso |
|---|---|---|
| `Unidad` | `UNIDAD:V4:<sha256>` | Agrupa las filas de grado, asignatura de malla y unidad declarada |
| `DimensionDocumental` | `LOCAL:<nombre>` | Categoría local con ancla en una edición y página PDF verificadas |
| `EN_UNIDAD` | Tema → Unidad | Pertenencia declarada, sin inferencia de secuencia pedagógica |
| `RelacionCurricular` | Relación por huella | Juicio semántico limitado a su fila y grado SV |
| `EN_CONTEXTO` | Relación → Tema | Fila a la que pertenece el juicio |
| `ORIGEN_RELACION` / `DESTINO_RELACION` | Relación → extremo | Extremos explícitos, sin proyectar un prerrequisito global |

Una dimensión documental no es un código oficial ni una alineación. Esta publicación no crea `CUBRE`
desde palabras coincidentes. Las referencias históricas solo se incorporan mediante adaptador explícito
y conservan su estado; no aportan vínculos `TRABAJA` o cobertura a temas V4 nuevos.

## Clasificación y publicación

La asignatura de Bachillerato se registra como declarada. Ciencias integradas requiere dos lecturas
separadas; las discrepancias permanecen como abstenciones. Los temas fuera de alcance y pendientes
siguen en el producto y en la vista, pero no se recuperan como evidencia disciplinar aprobada.

`producto/construccion.py` exige catálogo completo, piloto superado, huella curricular exacta y soporte
de cada coincidencia. `producto/almacen.py` escribe generaciones en `snapshots/<sha256>/` y cambia
`actual.json` atómicamente después de verificar todos los archivos. Una lectura resuelve un solo puntero
y comprueba huellas, tamaños, conteos, relaciones e identidades. El runtime indexa esos mismos objetos
verificados en memoria, sin volver a leer otro grafo desde disco.

El formato es `producto-2`, con ocho archivos obligatorios y `conocimiento.json` incluso cuando su
valor es `null`. No se acepta silenciosamente el borrador `producto-1`. El archivo de conocimiento
conserva expedientes, evidencias deduplicadas, cuatro dictámenes y colección. La construcción rehidrata
originales y coteja modelos configurados; la lectura reconstruye cierres, celdas, grupos, extremos y
correspondencia con el grafo. Una colección con ciclos no se admite. Su cobertura parcial se informa
sobre las 1.020 filas, sin convertir omisiones en ausencia curricular.

El diagnóstico distingue declarado, ausente, candidato y verificado. Contar declaraciones no mide
aprendizaje ni cobertura internacional. Las erratas científicas documentadas se revalidan por SHA y
ancla; la generación se abstiene antes de modelos si selecciona filas afectadas, incluidas combinaciones.

## Superficies

- `gskg producto insumo`: ingesta y resumen sin nube.
- `gskg producto comparar`: correspondencia textual conservadora con V3 y campos revalidados.
- `gskg producto catalogar`: plan por defecto; `--ejecutar` consume presupuesto durable autorizado.
- `gskg producto explorar`: HTML autónomo con filtros, fichas, alertas y exportación Markdown.
- `gskg producto construir`: publicación local desde currículo, catálogo y referencias documentales.
- `gskg producto validar`: verificación de la generación seleccionada, sin mutaciones.
- `gskg producto conocimiento`: hipótesis con evidencia original, sin enlaces aceptados ni DAG verificado.
- `gskg producto juicios evaluar/consolidar`: prepara evidencia semántica, cuatro lecturas ciegas y
  relaciones condicionadas a una fila; la consolidación revalida y bloquea admisión ante ciclos entre
  los lotes indicados. `producto construir --conocimiento` integra el archivo; no activa la V4 por sí solo.
- `gskg producto juicios medir-contexto`: cobertura estructural de los grupos, sin modelos ni gold.
- `gskg producto unidades listar/preparar/ejecutar`: selección exhaustiva, contexto de aula, paquete y
  orquestación por objetivo; sin modelos por defecto y ejecución incompatible con un catálogo piloto.
- `gskg alineacion`: criterios PISA/ERCE, evidencia local y documental, tres lecturas ciegas y unanimidad;
  ningún resultado crea cobertura o equivalencia de grados automáticamente.
- `gskg motor buscar/responder --version V4`: consume exclusivamente la publicación V4; `--fila-id`
  exige la fila, grado y disciplina exactos y permite recuperar su conocimiento admisible.

Los perfiles de extracción documental son configuración de confianza ligada a edición, página y SHA.
Se conservan el raw y los límites de regiones auditadas. Una cita se copia desde fragmentos registrados;
un dictamen no puede introducir texto de fuente ni intercambiar los lados local/internacional.

Un paquete propone una sesión por fila sin inferir carga normativa. Toda ejecución comparte presupuesto
y rechaza checkpoints de otro paquete, entorno o ledger. Una sesión respaldada debe citar su fila exacta;
las abstenciones y las sesiones no ejecutadas siguen presentes en el informe de cobertura técnica.
Las unidades incluyen siempre `Solicitud.fila_id`. Un anclaje de otra fila produce abstención antes
de los jueces y vuelve a comprobarse al cerrar la unidad. Reanudar el Motor rehidrata las evidencias
persistidas y reconstruye terminales; el checkpoint no sustituye fuentes ni dictámenes.

La vista admite un catálogo parcial y muestra sus estados; ello no permite publicar el piloto como
producto completo. El motor exige evidencia original y todos los dictámenes. Su respaldo automático
no equivale a eficacia demostrada, calibración psicométrica ni aprobación del MINED.

Aceptación y tareas abiertas: [continuidad](../HANDOFF.md); el roadmap y las investigaciones previas están en el
historial de Git (commit `022efed`).


## Formatos producto-3 y producto-4

Producto-3 añade `alineaciones.json` a los ocho archivos, con los expedientes originales y sin crear
cobertura CUBRE. Producto-4 exige diez archivos e incluye `mejoras.json`; `alineaciones.json` puede ser
null si no existe colección admitida. Los formatos anteriores siguen siendo legibles. Hashes, bytes,
nodos, aristas y puntero se verifican como una sola generación; la API invalida una instancia modificada.

El archivo de mejoras conserva todas las unidades, filas originales completas, clasificaciones,
evidencias, fragmentos, grupos, cuatro rúbricas, borradores, rondas y protocolos anteriores. Se requiere
el denominador íntegro; no se publica sólo lo favorable. Cada respaldo se reconstruye desde sus cuatro
lecturas exactas. Cinco controles adversariales únicos requieren votos completos y un veto del criterio
esperado; errores del proveedor no sirven como detección.

Las enmiendas son propuestas derivadas explícitas, verificadas contra el texto y SHA original. La copia
Excel modifica sólo las celdas aceptadas; no sobrescribe el libro ni borra las alertas de los originales.
El grafo distingue revisiones de unidad, mejoras por fila y expectativas documentales nativas. Las bandas
extranjeras y el orden de sus documentos no se convierten en equivalencias SV ni prerrequisitos reales.
Los recursos adicionales son condiciones de implementación, no disponibilidad constatada en escuelas.
