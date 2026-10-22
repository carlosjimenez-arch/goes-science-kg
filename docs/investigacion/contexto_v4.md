# Contexto V4 verificable por celda

Fecha: 21 de octubre de 2026. Alcance: lectura local de los XLSX entregados; sin llamadas a GCP,
sin modificar los originales y sin activar por sí mismo una nueva versión del grafo. La verificación
de bytes acredita fidelidad al insumo recibido, no aprobación oficial de su contenido curricular.

## Contrato de integración

```python
from pathlib import Path

from goes_science_kg.curriculo.contexto_fuentes import (
    contexto_celdas,
    documento_de_fila,
    fuentes_del_curriculo,
)
from goes_science_kg.curriculo.ingesta import cargar_curriculo

curriculo = cargar_curriculo()
fuentes = fuentes_del_curriculo(curriculo, raiz_v4=Path("insumos/v4"))
documentos = [documento_de_fila(fila) for fila in curriculo.filas]
# El recuperador produce Resultado(documento=..., puntaje=..., canales=...).
evidencias = contexto_celdas(
    resultados,
    version=curriculo.version,
    fuentes=fuentes,
    max_caracteres=18000,
    max_filas=3,
)
```

`Documento.texto` sirve para recuperar candidatos. Nunca se utiliza como respaldo si falta un
archivo, cambia su SHA o falla la extracción. El catálogo se construye desde las identidades de
`Curriculo.fuentes`; la raíz autorizada se inyecta explícitamente en código de aplicación.
El contrato del catálogo conserva `archivo_local`, `sha256`, `bytes`, `raiz_fuente="v4"` y
`version_curriculo`. La ruta de un `Documento` no amplía permisos. Las fuentes históricas pueden
agregarse con `catalogo_historico` y `raiz_historica`, sin colisiones de identidad.

`FuentesVerificadas.hidratar_celdas(documento)` devuelve una `Evidencia` por celda no vacía, con
identidad `<id_fila>#CELDA:<coordenada>`. Acepta una lista explícita `fuente.celdas` o un
`fuente.rango` rectangular de hasta 64 celdas. La hoja y las coordenadas deben existir. Las filas
completas históricas siguen funcionando cuando tienen como máximo 64 columnas. Selecciones
ambiguas, rangos abiertos, coordenadas de otra hoja y dimensiones excesivas se rechazan.

## Procedencia y fidelidad

Cada evidencia contiene texto obtenido del snapshot y su huella SHA-256 de texto. La fuente incluye
el SHA-256 del archivo y las coordenadas verificadas:

```json
{
  "documento": "<id del catálogo>",
  "hoja": "Unidad 1",
  "fila": 3,
  "celdas": ["B3"],
  "sha256": "<SHA-256 fijado en el catálogo>",
  "verificacion": "contenido_fuente",
  "raiz_fuente": "v4",
  "tipo": "documental",
  "celdas_verificadas": [{
    "coordenada_solicitada": "B3",
    "coordenada_origen": "B2",
    "valor_original": null,
    "valor_real": "Fotosíntesis",
    "tipo_excel": "s",
    "rango_combinado": "B2:B3",
    "valor_es_formula": false
  }]
}
```

Este ejemplo sólo atribuye el valor a B3 porque B3 pertenece realmente a la combinación B2:B3.
Un blanco ordinario no hereda la celda anterior. Se conservan la coordenada solicitada, el ancla
real y el vacío original; combinaciones superpuestas se consideran ambiguas. Una fórmula conserva
su expresión y `valor_es_formula=true`: no se ejecuta ni se presenta un resultado calculado.
Comentarios, hipervínculos, nombres de campos y texto arbitrario del payload no se convierten en
evidencia. Los localizadores publicados se reconstruyen a partir de las celdas extraídas; no se
conserva una fila falsa ni una página ajena al formato.

El registro de versión impide solicitar una fuente V4 como si fuera V3. Si el catálogo histórico
no declara versión, su correspondencia sigue dependiendo del adaptador histórico; no se infiere una
nueva versión a partir de un marcador o del formato del grafo.

## Lectura segura y reutilización

La instancia mantiene un snapshot por archivo y SHA esperado. Abre por descriptores, con
`O_NOFOLLOW` para los componentes internos, y verifica antes de parsear:

- La ubicación pertenece a la raíz específica asignada por el catálogo.
- El archivo tiene como máximo 64 MiB, conserva identidad/tamaño/fechas durante la lectura y coincide
  con el SHA y, cuando está declarado, con el tamaño esperado.
- El ZIP XLSX declara como máximo 128 MiB descomprimidos.

La lectura de bytes y el parseo del libro se reutilizan entre filas y celdas mediante un bloqueo
local a la instancia. Cada reutilización compara dispositivo, inodo, tamaño, mtime y ctime; un cambio
invalida el acceso y requiere una instancia nueva con un catálogo revisado. PDF conserva una caché
independiente de lector y texto por página. `estadisticas()` expone lecturas, bytes y parseos.

La implementación está dirigida a macOS/Linux, incluidos los contenedores de GCP. No promete soporte
Windows para la apertura por descriptores. El límite de tamaño descomprimido y la captura de errores
no constituyen aislamiento de CPU/memoria del parser; una ingesta de archivos externos adversariales
necesita además un proceso con recursos y tiempo limitados. Las raíces y el catálogo son configuración
confiable de la aplicación, no instrucciones recibidas del modelo.

## Selección y presupuesto

`contexto_celdas` acepta sólo resultados recuperados de la versión solicitada o de tipo `referencia`.
Hidrata hasta `max_filas` filas locales, sin buscar ni incorporar filas vecinas. Los resultados deben
venir ya filtrados y ordenados por el recuperador; esta selección no demuestra su relevancia semántica.
Las hojas auxiliares no se promocionan automáticamente a evidencia curricular.

La prioridad es procedimental; indicadores y evidencia de aprendizaje; las cinco fases; conocimiento,
contexto y competencia PISA; contenido, subcontenido y unidad; otros campos. Dentro de cada nivel se
conserva el orden del recuperador y de las celdas. Los nombres de campo del contrato ayudan a ordenar,
pero sus valores se vuelven a leer de los bytes. Se eliminan repeticiones del mismo ancla combinada.

El límite incluye el JSON completo de evidencias, huellas y procedencia, no sólo el texto. No se corta
una celda para fingir fidelidad: una celda que no cabe se omite. Se conserva al menos una evidencia local
verificable; si ninguna cabe, se devuelve una lista vacía. Esto también puede suceder con objetivos muy
largos o presupuestos pequeños y debe conducir a abstención en el motor. El método no garantiza incluir
las cinco fases cuando faltan en el original o no caben.

La etapa posterior puede construir fragmentos citables y hacer que el redactor seleccione IDs. La
hidratación por celda evita inventar procedencia; la resolución de IDs evita inventar literales. Ninguna
de las dos demuestra que la evidencia implique la afirmación ni que la propuesta pedagógica sea adecuada:
siguen siendo necesarias las revisiones semánticas y los gates de publicación.

## Verificación y medición local

Las pruebas específicas cubren suplantación de texto, SHA y raíz; rutas con enlaces externos; versión
incorrecta; lectura concurrente única; cambio posterior del archivo; celdas combinadas; blancos;
fórmulas; rangos y coordenadas inválidos; localizadores publicados; prioridades y presupuesto.

```bash
.venv/bin/ruff check src/goes_science_kg/motor/fuentes.py src/goes_science_kg/curriculo/contexto_fuentes.py tests/test_contexto_fuentes_v4.py
.venv/bin/pytest tests/test_contexto_fuentes_v4.py tests/test_motor_integracion.py tests/test_referencias.py tests/test_referencias_adversarial.py -q
```

Resultado al cerrar el cambio: Ruff correcto y 81 pruebas aprobadas. Se observó únicamente una
advertencia de deprecación de `google.genai` sobre tipos de Python 3.14.

La medición siguiente es una prueba de lectura local, no un benchmark de calidad de recuperación ni
una estimación de latencia de producción. Se seleccionaron determinísticamente las primeras tres filas
del contrato (Biología 10.°, filas físicas 3, 4 y 5), se solicitó un presupuesto de 18.000 caracteres y
se repitió 21 veces sobre la misma instancia: una primera lectura y 20 reutilizaciones.

| Dato | Resultado observado |
|---|---:|
| Fuentes / filas / hojas del currículo | 11 / 1.020 / 126 |
| Tiempo de ingesta completa, independiente del hidratador | 2.412,908 ms |
| Archivo de la muestra | `Matriz_Bachillerato_Biologia_10_11_V4.xlsx` |
| Columnas por fila de la muestra | 23 |
| Evidencias en el contexto final | 17 |
| Caracteres de texto / JSON completo | 1.831 / 17.652 |
| Lecturas / parseos XLSX / bytes verificados | 1 / 1 / 201.068 |
| Primera hidratación | 170,946 ms |
| p50 / máximo de 20 reutilizaciones | 9,654 / 10,078 ms |

Huella del currículo: `9f491de56b3ccb1f76dd9b0a216b2fe32564600dd9de30f5be7003a4b1f241c5`.
SHA del archivo: `4ad2fdefdf0bdad400bdaf8c38cb243393d87f74a68fd3b28746d18ecefa41c6`.
SHA del JSON de contexto, `ensure_ascii=False`, orden original:
`044122fbfc9f6a5a33dcc70bb2e14825868fa7e049ee4e37e751aeb7689960b8`.

La procedencia detallada consume gran parte del contexto: esta observación justifica mantener separado
el registro de auditoría de una futura proyección compacta para el modelo, conservando sus huellas y
localizadores y midiendo ambos presupuestos. La implementación actual cuenta toda la estructura para
evitar presentar una mejora de eficiencia que sólo excluya metadatos del cálculo.
