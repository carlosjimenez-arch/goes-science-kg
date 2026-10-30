# Ampliación de paquetes de Ciencias V4 con autoría Vertex

La ampliación tiene como horizonte 1.013 paquetes de objetivo y 108 paquetes de unidad. La revisión
de los cinco recorridos y casos concretos anterior se conserva en su propia edición del Escritorio.
Los guiones publicados, sus recibos, las fuentes y el presupuesto de la campaña histórica se mantienen.

El 29 de octubre de 2026 el usuario autorizó **un piloto separado de hasta 18 llamadas y USD 40 de
reserva**, para nueve guiones candidatos y tres controles negativos sin llamada. No autorizó una
reescritura completa de 3.255 componentes ni una nueva publicación en GCS. El recibo literal privado
está en `data/clases_v4/ampliacion_vertex_20261029/autorizacion_piloto_global.json`.

## Inventario y alcance real

`data/clases_v4/ampliacion_vertex_20261029/cobertura/` contiene las tablas JSON y CSV de los 1.013
objetivos y 108 unidades, con objetivos literales, componentes, guiones y fuentes antecedentes,
observaciones y referencias por SHA a los recibos. Conserva 862 guiones de clase y 108 de unidad;
151 objetivos sin guion liberado; 819 anexos y 97 evaluaciones aprobados como antecedentes; y 43
anexos y 11 evaluaciones retenidos. No hereda aprobaciones para versiones nuevas. Las 713 observaciones
siguen siendo observaciones por contrastar, con asignación y procedencia; no se convierten en errores
confirmados por contarlas.

El piloto cruza grados, disciplinas, mediciones, seguridad, errores de pertinencia y fuentes
insuficientes. Un guion nuevo no equivale todavía a un paquete con anexo y recorrido cerrado. Los
anexos y recorridos posteriores se redactarán a partir del guion exacto revisado; las guías y
evaluaciones de unidad deberán conservar todos sus objetivos y declarar sus faltantes.

## Autoría, revisión y control de gasto

El módulo nuevo `campanas_vertex/` vive fuera de los módulos congelados de la campaña histórica.
El comando siguiente sólo comprueba solicitudes locales y nunca crea un cliente ni llama al modelo:

```bash
uv run --frozen python -m goes_science_kg.campanas_vertex preflight PLAN.json \
  --solicitudes SOLICITUDES.json --prompts PROMPTS.json
```

La ejecución de pago requiere recibo literal del usuario, plan exacto y ledger histórico íntegro.
Fija modelo, código y dependencias, prompts, esquema, contexto, límites de bytes y salida. Cada
reserva se registra antes de invocar, con continuidad externa durable que detecta restaurar sólo
SQLite. Reanudar un proceso recupera salidas propias por SHA, sin repetir el pago. Esto no protege
contra restaurar simultáneamente todo el sistema y todas sus evidencias externas.

El reparto inicial daba dos plazas por candidato, compartidas entre redacción, corrección y fallo
técnico. Las plazas ya consumidas no reaparecen al cambiar el transporte o el nombre de una subetapa.
Los componentes de recuperación con una sola plaza disponible no permiten otra ronda.

Las dos primeras solicitudes A recibieron `400 INVALID_ARGUMENT`, sin texto de respuesta. Se
conservan sus llamadas y USD 3,346832 de reserva; no se afirma gasto facturado. El transporte sucesor
usa la compacidad del esquema histórico, conservando todos los validadores locales. La recuperación
de esos dos casos dispuso de una plaza por caso y un máximo conjunto de USD 5,653168 adicionales.
Los ocho textos recibidos en A y B requirieron correcciones. El cierre reorienta las dos plazas del
caso municipal bloqueado a corregir los dos A: esos casos tendrán tres solicitudes registradas,
incluido su HTTP400, y los otros seis tendrán dos. Diez antecedentes más ocho plazas finales mantienen
el máximo de dieciocho. Se conservan todas las filas y reservas; no es una ampliación del presupuesto.
El consumo de todas las subetapas se coteja con el recibo global y un punto de continuidad por ID/SHA;
los ejecutores anteriores no vuelven a lanzarse ni usan otra ronda además del cierre.

Una salida sólo pasa a revisión si termina correctamente, conserva identidad y objetivo, usa fuentes
citables registradas, cumple el contrato y sus cálculos declarados se recalculan. Pasar esos controles
no aprueba la ciencia, la pedagogía ni la implementación. Codex y otro agente examinan los textos
completos, fuentes, consignas, soluciones y rúbricas de la versión exacta. Los hallazgos materiales
se devuelven a Vertex si queda una plaza. Una respuesta defectuosa conserva su estado retenido al
agotarse las llamadas. La autorización editorial previa permite generar un sucesor local distinto:
debe declarar la autoría Codex, conservar la respuesta Vertex y obtener otro dictamen sobre sus bytes.
No se atribuye esa edición a Vertex ni se traslada la aprobación de una versión a otra.

## Cierre del piloto autorizado

Se ejecutaron **18 solicitudes**, con **USD 29,661560 de reserva conservadora registrada**; no es
una factura verificada. Dos solicitudes devolvieron HTTP400 sin texto y dieciséis produjeron
respuestas: ocho borradores y ocho correcciones. No quedan llamadas disponibles del piloto.

La selección final contiene **ocho guiones sucesores de seis unidades**, con 21 tareas, 54 criterios
de rúbrica de tres niveles y 88 comprobaciones aritméticas declaradas recalculadas. Dos conservan
íntegra la última respuesta Vertex y seis incorporan ediciones Codex identificadas, revisadas por
un agente distinto de su editor. Los dictámenes se anclan a los SHA de esas versiones exactas.

Se corrigieron, entre otros, confusiones entre dispersión, error e incertidumbre; una pista de
calibración en la comprobación; inferencias de seguridad de materiales; atribución indebida de
temperatura a calor de reacción; denominadores sanitarios y períodos históricos; y correspondencia
entre consignas, soluciones y criterios. El cotejo literal final añadió el esbozo de dos curvas
amplitud-frecuencia a la comprobación de resonancia, con solución y rúbrica gráfica. La predicción
de suelo se reparte antes que la hoja con datos simulados, sin alterar el JSON aprobado.
Las respuestas anteriores, sus dictámenes históricos y sus hallazgos se conservan identificados.
Los guiones nuevos tendrán guía docente, tareas del estudiante y comprobación reservada. No son
todavía ocho paquetes completos con anexo nuevo y recorrido nuevo de cuatro hojas.

El caso municipal `da854ca155` sigue retenido: quince recursos oficiales recuperados no completan
un expediente municipal coherente para los tres riesgos y su priorización familiar. Los controles
`5a7ca1ea5d`, `6cd3ad4ea5` y `6c4d9b13ca` siguen bloqueados sin llamada. El guion de resonancia
aprobado no levanta el estado retenido de su anexo histórico.

La química permite análisis documental y planificación. La práctica requiere FDS vigente del
producto real, EPP y protocolo institucional revisado, especialmente para CO2/agua de cal sin
soplado bucal. La FDS histórica Fisher se pudo consultar indexada, pero sus enlaces directos
devolvieron HTTP404; la entrega conserva esta limitación y no fabrica un PDF ni un SHA remoto.

La comprobación de conservación final cotejó 23.231 antecedentes y los cinco recibos originales.
Las filas históricas del ledger permanecen intactas; las 18 solicitudes del piloto tienen sus
propios identificadores y se exportan como evidencia, sin crear un ledger de arranque.
El diagnóstico detallado privado es
`data/clases_v4/ampliacion_vertex_20261029/DIAGNOSTICO_REVISION_PILOTO_002.md`;
el diagnóstico y catálogo anteriores permanecen como antecedentes superados.

## Fuentes, carga cognitiva y entrega

El protocolo privado de revisión exige correspondencia por cada cláusula del indicador y criterio:
enseñanza → tarea → solución → rúbrica. Distingue una referencia didáctica como OpenStax de una
fuente primaria específica para datos locales, salud y normas. Se comprueban fechas, denominadores,
unidades y límites. La integridad de una fuente oficial no valida cada afirmación que contiene.

La curación incluye las definiciones oficiales de [UNDRR](https://www.undrr.org/terminology/disaster-risk)
y la distinción de [NIST entre error e incertidumbre](https://www.nist.gov/pml/nist-technical-note-1297/nist-tn-1297-2-classification-components-uncertainty).
Los registros distinguen originales descargados por SHA de consultas textuales web con acceso HTTP
local bloqueado; no se inventan hashes de documentos remotos. Las inferencias algebraicas y las
síntesis se identifican como tales. Los documentos sanitarios conservan su período y sus intervalos,
sin presentarlos como datos actuales de 2026.

Palabras, minutos, pasos, cantidad de archivos, pruebas de código y simulaciones no miden carga
cognitiva, aprendizaje ni eficacia. Los materiales nuevos mantienen esas variables como no medidas
sin observaciones reales. El piloto verifica diseño y contenido documental, sin declarar resultados
de estudiantes o aprobación institucional.

Los diagnósticos operativos, respuestas crudas, revisiones y versiones aprobadas o retenidas se
conservan por separado en `data/clases_v4/ampliacion_vertex_20261029/`. Al cerrar el piloto, la copia
del Escritorio tendrá inventario y SHA, índice utilizable, evidencia de calidad y límites explícitos;
conservará la entrega anterior y no presentará borradores como paquetes finales completos.
