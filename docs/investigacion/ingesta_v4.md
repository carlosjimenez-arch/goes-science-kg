# Ingesta rigurosa de la entrega V4

Implementación: `curriculo/contratos.py`, `curriculo/_configuracion.py` y
`curriculo/ingesta.py`. Configuración independiente: `config/mallas_v4.yaml`.
La ingesta no activa la V4, no escribe los Excel ni modifica `config/mallas.yaml`,
el grafo histórico o decisiones de clasificación/alineación.

## Uso y significado del resultado

```python
from goes_science_kg.curriculo import cargar_curriculo

curriculo = cargar_curriculo()  # nombre="mallas_v4"
# También admite cargar_curriculo(config_path="/ruta/config/curriculo.yaml").
```

`Curriculo` es un contrato Pydantic con `version`, `huella`, `fuentes`, `filas`,
`hojas` y `agrupaciones`. `estado="ingerido_verificado"` significa que se verificó
la integridad de los archivos y su interpretación estructural frente a la
configuración explícita. Las alineaciones, recomendaciones y afirmaciones del
Excel siguen siendo declaraciones del insumo, pendientes de comprobación externa.

Cada fuente conserva nombre, ruta relativa, tamaño, SHA256 y metadatos de
procedencia. Se verifica tamaño y hash de los bytes **antes** de abrir el Excel;
`openpyxl` analiza un `BytesIO` construido exactamente con esos mismos bytes.
Un cambio concurrente posterior en el archivo no altera el objeto cargado. Los
consumidores que necesiten releer fuentes deben comprobar su hash de nuevo.

La configuración contiene el nombre exacto y tratamiento motivado de **cada**
hoja, incluso espacios finales. No se seleccionan hojas mediante expresiones
regulares ni se supone un número fijo de libros. Un archivo inesperado, una hoja
sin decisión explícita, un encabezado semánticamente duplicado o un hash
incompatible detienen la ingesta. Las rutas de insumos y procedencia deben
resolverse dentro de la raíz declarada; se rechazan enlaces hacia fuera.

## Resultado de la entrega recibida

| Elemento | Cantidad |
|---|---:|
| Libros originales cotejados con procedencia de Drive | 11 |
| Hojas curriculares | 62 |
| Hojas auxiliares preservadas | 64 |
| Temas con Procedimental original no vacío | 1020 |
| Agrupaciones grado / asignatura de malla / unidad | 108 |
| Registros físicos originales no vacíos, incluidos encabezados y notas | 3313 |
| Celdas conservadas en esos registros | 54975 |

| Grado | Temas |
|---|---:|
| 2 | 63 |
| 3 | 64 |
| 4 | 63 |
| 5 | 64 |
| 6 | 96 |
| 7 | 94 |
| 8 | 96 |
| 9 | 96 |
| 10 | 192: Biología 64, Física 64, Química 64 |
| 11 | 192: Biología 64, Física 64, Química 64 |

Las asignaturas se conservan como las declara la malla: `Ciencias`, `Biología`,
`Física` y `Química`. La clasificación posterior en las cuatro disciplinas del
producto será una decisión nueva y trazable. No se heredan etiquetas de la V3.

## Diferencias de formato que resuelve el lector

- Hay 13 distribuciones de columnas. Los encabezados de las filas 1 y 2 se
  interpretan por rol y columna física; se conserva su texto completo. Las
  columnas desconocidas no se eliminan ni colisionan por compartir encabezado.
- `Indicador avanzado` e `Indicadores de logro` son campos distintos. También
  permanecen separados conocimiento/contexto PISA, habilidad TIMSS, habilidad
  del siglo XXI, competencia MEN, evidencia y competencia/actividad digital.
- Física de Bachillerato incorpora `# de tema`; Química incorpora `N° Clase`.
  Los desplazamientos de columna no alteran el mapeo de los demás campos.
- La columna A sin título guarda ejes integradores. Su rol está declarado
  explícitamente por hoja. La unidad de las matrices básicas está en la
  configuración; en Bachillerato procede de la columna `Unidad` original.
- Ocho hojas carecen físicamente de `Aproximar`: las seis de sexto y las unidades
  `Recurso hídrico` y `Ambiente y energía` de séptimo. El contrato siempre incluye
  cinco fases, con `presente_en_hoja=False` y texto vacío cuando falta una.
- Química de undécimo contiene las columnas físicas Z/AA sin encabezado ni datos;
  se conservan. Las columnas desconocidas con valores también se conservan, como
  comprueban las pruebas sintéticas.
- Las celdas combinadas resuelven su ancla exacta. Un blanco ordinario nunca
  hereda el contenido de la fila anterior. `valor_original`, `valor`,
  `origen_combinado`, tipo Excel, comentario e hipervínculo quedan disponibles
  por coordenada. Los rangos combinados completos se conservan por hoja.
- Las filas sin Procedimental no se convierten en temas artificiales; permanecen
  en `HojaCurricular.registros`. Una celda combinada no duplica un procedimiento
  en filas inferiores. Los procedimientos deben ser texto; una fórmula en ese
  campo se rechaza. Las fórmulas de las hojas auxiliares se preservan literalmente.

Los códigos E/D/I/PR/EP de las fases se extraen como `codigos_locales`, con
`autoridad_codigos="insumo_local"`. Se mantiene el texto completo y no se expanden
rangos ni se inventan equivalencias. Las hojas Microhabilidades PISA, DigComp,
Habilidades transversales, Ajuste TIMSS-PISA, Herramientas IA, Notas y Mapa de
unidades permanecen accesibles como registros auxiliares. Sus códigos y
afirmaciones no se presentan como taxonomías oficiales verificadas.

## Identidad, límites y validación

La identidad de una fuente depende de versión, nombre y SHA256. La de un tema
depende además de hoja exacta, fila física y contenido completo de sus celdas y
roles. Cambiar una versión o el snapshot del archivo produce identidades nuevas;
una futura correspondencia será un artefacto separado de las decisiones humanas
o de expertos. `huella` registra configuración, procedencia, fuentes y filas
exactas; la versión del código debe registrarse adicionalmente en el experimento
o ejecución que lo consume.

El cotejo prueba integridad respecto al archivo de procedencia local, no
autenticidad mediante firma digital. La procedencia indica la captura desde Drive
y conserva el límite conocido: no fue posible comparar con la copia de Descargas
por permisos de macOS. El lector no confirma validez científica, cobertura real de
PISA/ERCE/TIMSS, adecuación pedagógica ni aprobación del MINED. Tampoco ejecuta
fórmulas, transforma las filas en actividades o activa automáticamente una versión.

Pruebas focales: **39 aprobadas**, `tests/test_curriculo_v4.py` y
`tests/test_inventario.py`; Ruff y formato verificados. Incluyen alteración de SHA,
tamaño/versión/conjunto de procedencia, cambios concurrentes después del hash,
hojas nuevas, encabezados duplicados/ambiguos, columnas desconocidas repetidas,
fórmulas y valores no textuales en Procedimental, ausencia de fases, prohibición
de arrastre de blancos, conservación de todas las celdas originales e identidad
versionada. Lectura completa medida localmente: aproximadamente **2,4 segundos**
con los once libros; es una observación de esta máquina, no un SLA.

El lector utiliza el logger del producto: inicio y cierre por archivo/proceso,
advertencias estructurales y rechazo de integridad. La configuración existente de
observabilidad muestra esos niveles como verde, amarillo y rojo en terminal.
