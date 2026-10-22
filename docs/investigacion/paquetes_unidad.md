# Paquetes docentes por unidad

> Registro histórico de investigación. Describe el corte y la ejecución indicados en este documento.
> Estado vigente del código, API y métricas: [documentación actual](../README.md) y [calidad](../CALIDAD.md).

Fecha: 21 de octubre de 2026. Preparación local y orquestación implementadas. La unidad V4 de Física
10.º ya se ejecutó: cuatro sesiones respaldadas y cuatro abstenciones, 58 intentos y reserva USD 7,4261195.
El escenario posterior de sesenta minutos obtuvo siete respaldos y una abstención. La
[entrega experimental íntegra](entrega_unidad_fisica10_20261021.md) conserva esa cohorte completa y
una variante del objetivo pendiente en dos encuentros: ocho objetivos respaldados en nueve encuentros
de sesenta minutos. No cambia los resultados de cuarenta o sesenta minutos ni la carga oficial.
La preparación no usa GCP ni consulta el gold; la generación autorizada sí usó Vertex.
[Resultados, límites y reanudación](resultados_unidad_fisica10_v4.md).

## Contrato y significado de los estados

`producto.unidades` expone `ContextoAula`, `PaqueteUnidad`, `ResultadoUnidad`, `preparar_unidad`,
`ejecutar_unidad` y `exportar_unidad`.

```python
from goes_science_kg.producto.unidades import ContextoAula, preparar_unidad, exportar_unidad

paquete = preparar_unidad(
    curriculo,
    catalogo,
    grado=10,
    asignatura_malla="Física",
    unidad="1. La física como ciencia",
    contexto=ContextoAula(
        minutos_por_sesion=40,
        recursos=("papel", "lapiz"),
        conectividad="sin_confirmar",
        apoyos=(),
        seguridad=(),
    ),
    fuentes=fuentes_verificadas,
)
exportar_unidad(paquete, directorio)
```

La selección requiere coincidencia exacta de grado, asignatura literal de malla y nombre de unidad.
Se conservan todas las filas seleccionadas, sus celdas, fases, indicadores, evidencia de aprendizaje,
campos ricos y decisiones de clasificación. No se heredan prerrequisitos ni actividades de otras
versiones. Cada fila origina una sesión **propuesta** para organizar solicitudes; este conteo no
establece carga horaria normativa, duración suficiente ni una secuencia pedagógica validada.

El estado del paquete es siempre `preparado`. Un paquete puede conservar una procedencia de catálogo
`piloto` para inspección y preparación; el orquestador rechaza ejecutarlo. La preparación no publica,
activa, corrige ni aprueba el catálogo. La procedencia incluye huellas del currículo y catálogo,
modelos/pipeline del catálogo y la identidad, edición y procedencia de los archivos originales.

El contexto de aula contiene tiempo solicitado, recursos declarados para esa preparación, conectividad,
apoyos y condiciones de seguridad. Los valores de ejemplo no equivalen a una constatación de recursos
de una escuela. `Solicitud.minutos` y `Solicitud.recursos` se construyen desde ese contexto, además
de incluirlo como JSON de datos en la consulta. Se conserva el objetivo original; una solicitud de más
de 2.000 caracteres queda no ejecutable con una razón explícita. No se trunca el original ni el aula.

La solicitud también fija `fila_id` como campo tipado; el texto de consulta no decide su identidad.
El runtime `BuscadorProducto.buscar_fila` comprueba fila, versión, grado y disciplina y sólo añade
evidencia primaria de vínculos admisibles de esa fila. Si el puerto no ofrece esa operación, el
Motor se abstiene; no la sustituye con una búsqueda general. Un anclaje en otra fila se veta antes
de llamar a los jueces. La comprobación al cerrar la unidad sigue siendo una defensa independiente.

## Fuentes y pendientes visibles

La preparación hidrata cada fila desde `FuentesVerificadas`, coteja coordenadas, tipos, valores,
combinaciones, campos y SHA de edición. Una fuente no verificable no se sustituye con texto de metadata.
Una fila sin evidencia permanece en el paquete y su sesión queda no ejecutable. Se conservan los
blancos y las fases ausentes, diferenciando ausencia de columna y celda sin texto.

Las observaciones adicionales usan `AlertaSolicitada(fila_id, campo, codigo, descripcion)` y se exportan
como pendientes. Los bloqueos científicos efectivos proceden de `fuentes.bloqueos_curriculares`; deben
configurarse con el runtime o el verificador de alertas antes de preparar/ejecutar. Esos bloqueos se
exportan y evitan solicitudes para las filas afectadas. Una disciplina pendiente, fuera de alcance o
ambigua tampoco se transforma automáticamente en una asignatura para el Motor.

El JSON conserva el registro completo, las evidencias originales y, cuando existe, el resultado crudo
del Motor. Markdown presenta las fuentes y las fases originales por sesión. Las propuestas automáticas
sólo se muestran como tales cuando la sesión completa tiene respaldo; los rechazos y abstenciones
permanecen visibles y no cuentan como cobertura.

La CLI `gskg producto unidades` añade `listar`, `preparar`, `ejecutar` y `recuperar-transporte`.
`ejecutar` muestra un plan local
sin `--ejecutar`. Antes de crear Vertex coteja el paquete reconstruido desde currículo, catálogo y fuentes
de la publicación; rechaza alteraciones de sesiones/contexto aunque alguien recalcule el hash del JSON.
Comprueba destinos y enlaces, ID de ejecución y cambios de bloqueos científicos antes de consumir.
El paquete vincula currículo, catálogo y unidad completa; no contiene `snapshot_id` ni identifica por sí
solo todo el conjunto externo de referencias. El entorno durable sí fija corpus/fuentes en cada ejecución.

## Ejecución durable con un presupuesto de unidad

```python
from goes_science_kg.producto.unidades import ejecutar_unidad, exportar_unidad

resultado = ejecutar_unidad(
    paquete,
    motor=motor,
    registro=registro,
    ejecucion_id=id_presupuesto_unidad,
    directorio_operaciones=directorio_operaciones,
)
exportar_unidad(paquete, directorio, resultado=resultado)
```

Esta invocación sí ejecuta el modelo inyectado en el Motor. Antes de conectarlo a Vertex deben existir
la autorización de payload/destino y el presupuesto correspondiente. El componente no crea un proveedor,
no cambia sus límites, no genera un nuevo ID de presupuesto y no establece autorizaciones por sí mismo.
El proveedor declara su `registro` y `ejecucion_id`; deben coincidir con los suministrados al orquestador.
Un modelo simulado puede cumplir ese contrato sin importar ni ejecutar Vertex.

Se reutiliza `motor.ejecuciones.ejecutar_durable`, con el mismo workflow, jueces y controles existentes.
Cada sesión tiene un `thread_id` distinto, mientras todas conservan **un único ID de ledger**. Un vínculo
SQLite registra paquete, entorno y archivo de ledger. La huella incorpora solicitud/paquete, corpus,
recuperador, modelos, configuración, fuentes/bloqueos y código de motor, recuperación, currículo y
producto, incluidos los prompts. Un cambio de paquete o entorno rechaza el uso de esa ejecución.

El directorio de operaciones mantiene `checkpoints_unidades.sqlite` y un bloqueo exclusivo por ejecución.
No acepta archivos de checkpoint enlazados fuera de su ubicación ni destinos bajo originales, código o
configuración. La implementación utiliza mecanismos POSIX para macOS/Linux/GCP. Los terminales se leen
sin repetir generación; un estado interrumpido se reanuda. Reservas previas, incluidas las que quedaron
sin respuesta, siguen formando parte del ledger. No se repone presupuesto al pasar de una sesión a otra.
Los estados parciales y terminales se rehidratan contra los originales, comprueban modelos y
fragmentos y reconstruyen el cierre; la bandera persistida de respaldo no sustituye esas comprobaciones.

Una sesión sólo cuenta como `respaldado_automaticamente` cuando el Motor respalda y su anclaje cita
evidencia de la **fila física e identidad objetivo exactas**. Un respaldo sobre otra fila se conserva
para auditoría, pero la sesión se informa como abstención. Esto comprueba correspondencia del objetivo;
no añade otra prueba de implicación semántica ni de eficacia educativa.

El reporte distingue filas totales, sesiones propuestas, respaldadas, abstenciones y no ejecutadas.
Incluye tiempo observado, reanudación de checkpoint y consumo antes/después e incremental, junto a
los límites compartidos `max_llamadas` y `max_usd` del proveedor. La reserva
USD es una cota del ledger; no es una factura. Agotar el límite antes de una sesión nueva la deja
explícitamente no ejecutada. Fallos durante el workflow quedan como abstención del Motor, sin ocultarlos.

## Artefacto real preparado

Directorio: `data/producto/unidades/fisica-10-preparada`.

- Grado: 10; asignatura explícita: Física; unidad: `1. La física como ciencia`.
- Ocho filas y ocho evidencias originales; ocho sesiones propuestas, ninguna ejecutada.
- Catálogo de referencia en modo `piloto`, sin publicación ni activación.
- Contexto de ejemplo: 40 minutos solicitados, papel/lápiz y conectividad sin confirmar.
- Archivos: `paquete.json` y `paquete.md`; estado `preparado`, cero llamadas de preparación.

El origen del catálogo es `data/evaluacion/v4/catalogo_piloto_referencia.json`; sólo se usa su registro
de clasificación y procedencia. No se abren consultas ni labels de evaluación. El JSON exportado
contiene una clave `paquete` que puede cargarse mediante `PaqueteUnidad.model_validate(datos["paquete"])`;
la clave `ejecucion` es `null` en este ejemplo.

## Verificación

La continuación autorizada de clasificación permitió preparar un segundo paquete con catálogo completo:
`data/producto/unidades/fisica-10-v4-catalogada/`, identidad
`2fe0788040800303767a05179332577dbe77689821d81bb103d505ecb30d0bc8`.
Conserva ocho filas y ocho solicitudes ejecutables. La recuperación real verificó las celdas de cada
fila y el rechazo de grado incompatible. `paquete.json` tiene SHA
`9ae516be2a9bcf178863ac868dd3f9ce76010c3d5eb997e3527d10f816d5a320` antes de ejecutar;
la exportación con el resultado tiene SHA
`0d30dfcf1e6df1ba4a2d68675dd7547500b63ba59da177476b6cfd1de26b76b1`.
El paquete piloto anterior permanece como evidencia de esa fase.

El usuario autorizó continuar lo pendiente de Ciencias hasta cerrar y se ejecutó el plan de 64 intentos
y USD 8 nuevos para toda la unidad, sin repartir ni reiniciar el presupuesto por sesión. El recibo
`autorizacion_generacion_20261021.json` conserva la respuesta y las huellas del plan y paquete previos.
Las ocho sesiones terminaron: cuatro respaldadas y cuatro abstenciones. Consumieron 58 intentos
y USD 7,4261195 de reserva; reanudar recuperó los ocho terminales con cero generación y cero gasto adicional.
El archivo con nombre `plan_generacion_pendiente.json` se conserva como evidencia del plan anterior.
El contexto sigue siendo un ejemplo: 40 minutos solicitados, papel/lápiz y conectividad sin confirmar,
sin describir recursos constatados en una escuela.

Las pruebas usan archivos sintéticos y el Motor real con un modelo simulado que reserva llamadas en
Registro. Comprueban conservación de filas y fases, campos de tiempo/recursos, consultas excesivas,
rechazo de pilotos, respaldo sobre una fila equivocada, reanudación terminal, interrupción después de
reservar, presupuesto compartido agotado, cambios de entorno y destinos enlazados. Dos sesiones
respaldadas consumen ocho llamadas simuladas; reanudarlas consume cero llamadas adicionales. Una
interrupción conserva su primera reserva y no la elimina al reanudar.

```bash
.venv/bin/ruff check src/goes_science_kg/producto/unidades.py tests/test_unidades.py
.venv/bin/pytest tests/test_unidades.py tests/test_motor_integracion.py tests/test_producto_v4.py -q
```

Estas pruebas simuladas son de software y contabilidad. La ejecución real y la reanudación se registran
por separado; cuatro abstenciones impiden declarar la unidad completamente respaldada. No se acredita
eficacia educativa, aprobación institucional ni cumplimiento de horas oficiales.

La [auditoría local vigente](resultados_juicios_locales_2026.json) registra la suite global y los controles
posteriores de identidad de fila, fuentes persistidas y publicación de conocimiento. Los proveedores
de estas pruebas son simulados y no acceden a la red. La advertencia de tipos de `google.genai` bajo
Python 3.14 no constituye una llamada a un modelo.
