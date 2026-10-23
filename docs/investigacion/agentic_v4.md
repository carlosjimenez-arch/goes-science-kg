# Recuperación adaptativa acotada para V4

> Registro histórico de investigación. Describe el corte y la ejecución indicados en este documento.
> Estado vigente del código, API y métricas: [documentación actual](../README.md) y [calidad](../CALIDAD.md).

Fecha: 21 de octubre de 2026. Estado: candidato implementado, pruebas locales sintéticas; sin ejecución
de modelos remotos ni lectura del conjunto reservado durante su desarrollo. El default continúa siendo
el baseline. Esta implementación no declara una mejora de calidad en V4.

## Beneficio plausible y límites

El índice léxico sólo recupera términos presentes en el corpus. Una consulta coloquial que pide
observar cómo crece una planta puede utilizar vocabulario diferente al procedimental de la malla. Una
reformulación puede encontrar esa fila conservando filtros. Es una hipótesis verificable, no un resultado.
Una consulta ambigua también puede cambiar de tema al reformularse; añadir una llamada introduce coste,
latencia y otra superficie de fallo. Reformular no resuelve un objetivo ausente, una clasificación
pendiente, un archivo inaccesible ni un SHA incorrecto. En esos casos debe mantenerse la abstención.

[Self-RAG](https://arxiv.org/abs/2310.11511) estudia recuperación adaptativa mediante entrenamiento y tokens
de reflexión. [CRAG](https://arxiv.org/abs/2401.15884) combina evaluación de recuperación y corrección,
incluyendo búsqueda web. Ambos motivan experimentar con decisiones de recuperación; este wrapper no
reproduce esos sistemas ni permite navegación. Sus resultados publicados no demuestran una mejora en
el currículo salvadoreño. Fuentes primarias revisadas en la fecha indicada.

## Política congelada antes de medir

`BuscadorAgentic` ejecuta el recuperador original y examina sólo sus resultados. Considera un objetivo
local cuando pertenece a la versión vigente, tiene hoja y localizador físico y no está marcado como
derivado. Es un diagnóstico de recuperación; los bytes se verifican después mediante el hidratador.

La cobertura léxica es la mayor fracción de términos únicos de la consulta presentes en alguno de los
objetivos locales recuperados. Usa `recuperacion.lexico.normalizar`, sin stemming añadido ni ajuste al
gold. El umbral por defecto es 0,5. Sólo solicita planificación cuando faltan objetivos locales o esa
cobertura es inferior al umbral. Una consulta sin términos recuperables no activa planificación. Esta
señal no es una probabilidad ni evalúa implicación semántica; puede tener falsos positivos y negativos.

El planner recibe únicamente consulta, filtros originales y diagnóstico numérico/categórico. No recibe
el corpus, los textos curriculares, IDs de filas, gold, nombres de archivos relevantes ni resultados de
evaluación. Su esquema es `PlanBusqueda(consulta_busqueda, motivo)`, sin campos adicionales. La consulta
reformulada admite de 3 a 600 caracteres y necesita términos recuperables; el motivo admite de 8 a 240.
Se presupuesta el mensaje junto al sistema y esquema, por defecto hasta 6.000 caracteres.

Se admite una generación lógica y una recuperación adicional. Una reformulación léxicamente idéntica
no repite la búsqueda. El wrapper nunca ejecuta una herramienta sugerida, sigue un enlace ni interpreta
IDs generados por el planner. El motivo se conserva sólo en la traza; no se ancla como evidencia.

Las dos búsquedas conservan exactamente versión, grado, asignatura, K y saltos originales. La fusión
utiliza RRF con constante 60 y prioriza objetivos locales vigentes frente a referencias. Sólo admite
IDs y contenido idénticos al corpus registrado, elimina duplicados y conserva como máximo K resultados.
Si falla el planner, su validación o la segunda búsqueda, devuelve los resultados iniciales. No aumenta
el presupuesto de contexto: el mismo hidratador y límite se aplican después a ambas variantes.

## API e integración con Vertex

```python
from goes_science_kg.recuperacion.agentic import BuscadorAgentic

candidato = BuscadorAgentic(baseline, modelo_estructurado)
resultados = candidato.buscar(
    consulta,
    version="V4",
    grado=4,
    asignatura="Ciencias",
    k=10,
    saltos_grafo=1,
)
busqueda = candidato.buscar_con_traza(consulta, version="V4", grado=4)
```

`baseline` debe cumplir `motor.puertos.Recuperador` y exponer `.documentos` y `.huella`.
El wrapper mantiene el mismo puerto, añade `.buscar_con_traza` sin estado mutable por solicitud y
expone `.documentos`, `.identidad` y `.huella`. La huella incluye corpus completo, índice original,
configuración, modelo real, prompt, esquema e implementación, incluida la normalización.

El rol es `planificador_recuperacion`; se utiliza el `ModeloEstructurado` existente. Con `Vertex`, el
proyecto, región, esquema, mensajes y configuración del proveedor intervienen en su caché y las llamadas
reservan presupuesto durable en `Registro`. No se crea un cliente o una caché paralela. La integración
debe configurar una instancia con salida de 512 tokens, razonamiento `LOW` cuando corresponda al modelo
y timeout acotado. Los reintentos físicos siguen la configuración del proveedor: una generación lógica
no significa necesariamente una única petición HTTP. Para comparar un intento físico, configurar cero
reintentos. El wrapper no puede cancelar por sí mismo una implementación síncrona que ignore su timeout.

No se ha elegido un modelo ganador. El modelo del rol y su configuración deben quedar congelados antes
del experimento, con autorización del payload y presupuesto correspondiente antes de usar nube.

## Harness con gold offline

`recuperacion.evaluacion_agentic` separa dos contratos:

- `ConsultaEvaluacion(id, consulta, version, grado, asignatura)`, la lista blanca pública.
- `ObjetivoRelevante(documento, hoja, fila, celdas)`, un mapping offline por ID de consulta. `documento`
  identifica `FuenteCurricular.id`; las celdas son coordenadas exactas de esa fila, no textos esperados.

`cargar_consultas(path)` extrae sólo la lista blanca de un archivo de casos. No consulta ni envía los
campos privados del evaluador. El integrador construye el mapping de objetivos fuera del planner.
`resolver_objetivos` vincula localizadores a IDs de fila y a `<id_fila>#CELDA:<coordenada>`; las filas o
selectores ausentes se reportan por separado y permanecen en el denominador. Una fila física ambigua
con dos identidades en el índice invalida la evaluación.

```python
from goes_science_kg.curriculo.contexto_fuentes import contexto_celdas
from goes_science_kg.recuperacion.evaluacion_agentic import comparar_agentic

def contextualizar(resultados, *, version, max_caracteres):
    return contexto_celdas(
        resultados, version=version, fuentes=fuentes, max_caracteres=max_caracteres
    )

# Ejecutar este bloque con un proveedor real sí consume su presupuesto y red.
reporte = comparar_agentic(
    consultas_publicas,
    gold_offline,
    baseline=baseline,
    candidato=candidato,
    contextualizar=contextualizar,
    medir_consumo=lambda: registro.resumen(ejecucion_id),
)
```

Las dos variantes deben tener exactamente el mismo corpus y reciben el mismo K y presupuesto. Las
variantes alternan orden entre repeticiones. Los errores mantienen la consulta en el agregado con
recuperación vacía. Se comprueban la correspondencia de la evidencia con una fila recuperada, sus
coordenadas, versión y huella textual; el callback confiable sigue siendo responsable de verificar
los bytes y el SHA del archivo. Un marcador de metadata no sustituye esa verificación.

Se reportan MRR y `recall@K` de filas, además de MRR y `recall_contexto` de celdas realmente hidratadas.
K limita filas, no celdas: el contexto puede incluir varias celdas por fila y su límite completo de
caracteres sigue vigente. Se reportan métricas globales y por grado, ranking por caso/repetición,
presupuesto de contexto, latencia p50/p95/máxima, trazas y consumo observado. El informe incluye hashes
de consultas, gold, corpus, configuración, candidato y harness.

El callback de consumo debe usar un `ejecucion_id` dedicado sin llamadas concurrentes ajenas; se leen
deltas de llamadas y reserva por solicitud. La reserva es una cota conservadora, no coste facturado.
No se infieren tokens, precio o cache hits si faltan esos datos. Sin medición de consumo, el gate no
selecciona el candidato. Las repeticiones pueden aprovechar caché: se conserva el p95 de cada una y
se utiliza el peor para evitar que una media caliente oculte la primera ejecución.

## Gate predeclarado

Valores por defecto de `ConfiguracionComparacion`:

| Condición | Valor |
|---|---|
| K / presupuesto / saltos / repeticiones | 10 / 18.000 caracteres / 1 / 3 |
| No regresión | MRR y recall globales y en cada grado, para filas y celdas |
| Beneficio exigido | Al menos una mejora estricta global |
| Tamaño mínimo | 20 consultas y 3 por grado presente |
| Cobertura | Todos los grados declarados en `grados_esperados`, si se especifican |
| Independencia | Debe declararse explícitamente; por defecto es falsa |
| Estabilidad y ejecución | Rankings estables entre repeticiones y cero errores |
| Peor p95 total / incremental | Hasta 6.000 / 5.000 ms |
| Reserva media por consulta | Hasta USD 0,02 en la peor repetición |

Modificar un umbral después de ver resultados requiere otro experimento y otro conjunto independiente.
Un conjunto de 19 consultas no satisface el mínimo de 20, aunque mejore sus métricas. Un conjunto usado
para desarrollar prompts ya no se considera independiente. La selección técnica nunca cambia el
default automáticamente: el reporte conserva `default="baseline"` y una decisión explícita de gate.
No demuestra eficacia educativa, seguridad pedagógica ni cobertura de todos los grados y contenidos.

## Validación realizada

Las pruebas usan consultas y fuentes sintéticas creadas en el test, sin abrir el gold del producto.
Cubren omisión del planner cuando hay cobertura, límites de llamadas, conservación de filtros/K,
errores y JSON inválido, IDs y contenido suplantados, preferencia local, caché/reserva del Vertex
existente con cliente simulado, gold ausente, privacidad de labels, contexto presupuestado y veto de
una regresión por grado aunque mejore el promedio global. No constituyen un resultado experimental de
recuperación V4 ni una comparación de modelos remotos.

```bash
.venv/bin/ruff check src/goes_science_kg/recuperacion/agentic.py src/goes_science_kg/recuperacion/evaluacion_agentic.py tests/test_agentic.py
.venv/bin/pytest tests/test_agentic.py tests/test_recuperacion.py tests/test_contexto_fuentes_v4.py -q
```

Resultado al cerrar el cambio: Ruff correcto y 60 pruebas aprobadas, incluidas 16 nuevas del candidato
y harness. No se generó un informe de calidad real ni se activó automáticamente el candidato.
