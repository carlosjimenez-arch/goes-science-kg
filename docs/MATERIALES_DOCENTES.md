# Biblioteca docente de Ciencias

La entrega final recibida el 26 de octubre tiene una biblioteca independiente en
`/api/v4/produccion/materiales`: 1.020 paquetes base por objetivo y 108 por unidad, con revisión de
contenido pendiente. Sus 14 ZIP se descargan con `gskg produccion descargar`.
[Edición final, incidencias y comandos](MALLAS_PRODUCCION_V4.md).
Las propuestas revisadas descritas abajo pertenecen a la captura del 22 de octubre.

La entrega del 22 de octubre de 2026 completa el empaquetado y la consulta de materiales para
preparar clases a partir del grafo real. No requiere llamadas a modelos al construir ni consultar.
El código está en `materiales/`, `api_materiales.py` y `cli/materiales.py`.

## Qué contiene

| Material | Registros | Procedencia y alcance |
|---|---:|---|
| Paquetes V4 por objetivo | 1.013 | Propuestas de Ciencias con revisión automática de su unidad |
| Paquetes V4 por unidad | 108 | Agrupación exhaustiva de las filas, sin inferir secuencia pedagógica |
| Filas fuera de alcance | 7 | Conservadas sin presentarlas como preparación de Ciencias |
| Paquetes históricos | 150 | V3: 44 de Ciencias 9.º, 30 de Física 10.º, 42 de Química 10.º, 21 de Física 11.º y 13 de Química 11.º |
| Actividades | 827 | Banco histórico: 583 revisadas por panel y 244 pendientes |
| Experimentos | 230 | Banco histórico: 150 revisados por panel y 80 pendientes |
| Microtemas | 33 | Banco histórico: 32 revisados por panel y uno pendiente |
| Dificultades | 493 | Banco histórico: 348 revisadas por panel y 145 pendientes |
| Recorridos de tutoría | 5 | Demostraciones históricas |
| Unidad experimental V4 | 1 | Física 10.º: ocho objetivos y nueve encuentros propuestos, snapshot propio |
| **Total** | **2.867** | Las categorías no representan 2.867 clases nuevas |

Se incluyen además los **316 archivos originales** seleccionados, byte a byte: JSON y Markdown de
los 150 paquetes, índices, pendientes, bancos, recorridos, revisión histórica y unidad experimental.
Cada ruta y SHA se pueden consultar en el manifest y descargar por SHA desde la API.

## Cómo se construyó y qué se completó

El generador histórico `aprendizaje/paquete.py` reunía la fila V3, conceptos y bases del grafo,
objetivos internacionales, ideas previas, actividades, experimentos y datos de referencia citables.
Registraba la completitud y separaba lo revisado por panel. Los archivos originales se conservan;
no se vuelve a ejecutar ese generador contra V4 ni se trasladan sus vínculos por similitud textual.

Para V4, `materiales/compilacion.py` lee el snapshot producto-4 seleccionado y verifica sus fuentes
físicas. Coteja las celdas originales con los libros y compila **todas** las filas, sin seleccionar sólo
casos favorables. Cada preparación de Ciencias contiene íntegros:

- objetivo original y propuesto, indicador observable y orientación didáctica;
- producto evaluable, criterios de evaluación, andamiaje y contexto salvadoreño propuesto;
- recursos condicionados y seguridad, sin afirmar disponibilidad en las escuelas;
- celdas originales, fuente, hoja, fila, SHA, fragmentos citados y evidencias;
- cuatro dictámenes de la unidad, número de rondas, alertas del original y enmiendas.

Los votos conservan su **alcance de revisión curricular de unidad**. No se renombran como revisión de
una clase nueva. La unidad experimental mantiene su snapshot de origen y sus tres jueces originales;
no adopta los cuatro dictámenes de la publicación curricular actual. Las duraciones nuevas permanecen
nulas. Esto completa materiales para preparar clases; los guiones completos cronometrados para todos
los objetivos requieren otro proceso finito de generación y evaluación.

Los 470 elementos pendientes del banco histórico siguen pendientes; los revisados conservan su
registro. Las dos observaciones de Química 10.º de `REVISION_HUMANA.md` siguen accesibles. No se
inventan datos de referencia, homologaciones entre grados ni correspondencias entre versiones.
El respaldo automático tampoco acredita eficacia en aula ni aprobación institucional.

## Bucket y recuperación

La biblioteca se publica en el bucket institucional aprobado de Ciencias, bajo
`gs://goes-ai-kg-artefactos/ciencias/v4/materiales/<biblioteca_id>/`.
La generación publicada tiene identidad
`5b64ee509613b25ef91a941bcdbb2cc6a271daef98a0ecbddbc279a3eba2f510`.
La base ocupa 84.766.720 bytes y el manifest 46.634 bytes. El recibo conserva sus SHA y generaciones
exactas; no se debe resolver un objeto sin fijar la generación del recibo.

Son dos objetos: `biblioteca.sqlite` y `manifest.json`; ambos tienen generación y SHA fijados en
`config/materiales_ciencias.lock.json`. SQLite reúne los registros y los originales en un solo objeto
indexado, evitando cientos de descargas a GCS por consulta. El manifest conserva conteos, estados,
procedencia, identidad del snapshot curricular y hash del ledger.

Cada escritura vuelve a comprobar cuenta GOES, proyecto, UBLA y prevención de acceso público. Si PAP
es heredada, exige la política efectiva del proyecto en enforced. Se escribe con precondición de objeto
nuevo y se relee la generación exacta para comparar todos sus bytes. No se cambia IAM ni se publica
el contenido en Git. Un recibo de progreso permite reanudar las subidas completadas sin sobrescribirlas.

Para un consumidor nuevo basta recuperar esta biblioteca; no necesita el ZIP completo del corpus:

```bash
uv sync --extra api
uv run gskg materiales restaurar
uv run gskg materiales validar
uv run gskg servir --puerto 8010
```

Requiere acceso de lectura al bucket con la identidad institucional configurada. Si gcloud necesita un
Python compatible, definir `CLOUDSDK_PYTHON` con su intérprete antes de restaurar. La API no inicia
sesiones ni hace llamadas a GCS por petición: consulta la copia local verificada en modo de sólo lectura.
La restauración descarga ambos objetos a una carpeta temporal y sólo los habilita tras validar todo.

Para reconstruir desde las fuentes recuperadas:

```bash
uv sync --extra api --extra motor
uv run gskg datos restaurar --en-repo
uv run gskg materiales construir --destino data/materiales-nueva
uv run gskg materiales validar --directorio data/materiales-nueva
uv run gskg materiales publicar --directorio data/materiales-nueva --recibo var/materiales-nueva.json
```

La construcción y restauración requieren destinos nuevos; no modifican una biblioteca en servicio.
Para adoptar otra generación se despliega la nueva carpeta y se reinicia el proceso. Una modificación
posterior de SQLite o manifest invalida la instancia y responde 503.

## Contrato de consulta

OpenAPI expone el grupo **Materiales docentes**. La versión predeterminada es V4; seleccionar V3 o
histórico explícitamente permite acceder al material anterior.

```http
GET /api/v4/materiales/salud
GET /api/v4/materiales/manifest
GET /api/v4/materiales?version=V4&tipo=paquete_unidad&grado=10
GET /api/v4/materiales?version=V4&tipo=paquete_objetivo&grado=10&q=energía
GET /api/v4/materiales?version=V3&tipo=paquete_historico&grado=9
GET /api/v4/materiales?version=historico&tipo=experimento&grado=9
GET /api/v4/materiales/detalle/{id}
GET /api/v4/materiales/descarga/{id}?formato=md
GET /api/v4/materiales/archivos/{sha256}
```

Otros filtros: `asignatura` exacta de la malla, `fila_id`, `offset` y `limite` (1–200).
La búsqueda ignora mayúsculas y tildes; utiliza título, unidad, asignatura e identidades. Los IDs que
incluyen `/` se aceptan completos en detalle y descarga. JSON es el formato de descarga predeterminado.
La consulta devuelve el denominador antes de paginar y la identidad de la biblioteca. No existen
operaciones de generación o escritura en esta API. Mantenerla dentro del servicio institucional con
su control de acceso; el proceso local existente escucha en loopback.

Ejemplo Python de consumidor:

```python
import requests

base = "http://127.0.0.1:8010/api/v4/materiales"
r = requests.get(base, params={"version": "V4", "tipo": "paquete_objetivo", "grado": 10}, timeout=15)
r.raise_for_status()
id_ = r.json()["materiales"][0]["id"]
detalle = requests.get(f"{base}/detalle/{id_}", timeout=15)
detalle.raise_for_status()
propuesta = detalle.json()["material"]["documento"]["propuesta"]
print(propuesta["orientacion_didactica"])
```

## Verificación

`tests/test_materiales.py` verifica versiones, estados, paginación, consultas adversarias,
originales, determinismo, alteraciones, fuentes ausentes, descargas y publicación recuperable.
`tests/test_materiales_reales.py` coteja las 1.020 filas, 108 unidades, textos propuestos, votos,
celdas, 150 paquetes V3, los cuatro bancos completos, los 316 archivos y el ledger inalterado.
Los tests de GCS existentes verifican PAP efectivo actual, UBLA, identidad, proyecto,
precondición de creación y lectura por generación con SHA. La comprobación real de GCS usa
el recibo fijado y una restauración completa independiente antes de entregar.

La compilación se completó en 8,245 s en el equipo de trabajo. No representa un benchmark de
producción. Vertex conserva **668 invocaciones acumuladas**, cero nuevas por esta entrega y el
mismo ledger; no se abre un presupuesto nuevo.


La auditoría real por HTTP enumeró los 2.867 registros en sus tres versiones y recuperó los 316
originales comparando tamaño y SHA. Fueron 367 peticiones correctas y cuatro controles de entrada
rechazados con 422. Un consumidor independiente, sin `insumos/` ni `data/producto/`, recuperó la
biblioteca de GCS y reprodujo detalle y Markdown. También se ensayó una instalación mínima API
sin SDK Vertex, LangGraph ni Anthropic. En 30 consultas locales calientes: p50 3,747 ms y p95 5,806 ms;
no es una medición de producción. La suite integral pasó **1.416 pruebas en 267,76 s**. Ruff y el control de identidad GOES
están en verde. La primera ejecución detectó el correo global personal de la copia temporal;
se fijó la identidad GOES y se repitió la suite completa, sin omitir esa prueba.
