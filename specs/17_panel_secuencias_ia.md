# 17 · Ampliación de autoría con panel multiagente IA

## Decisión del responsable y objetivo

El 2026-10-15 el responsable indicó que no hay revisión humana disponible y autorizó un sistema de agentes
expertos de disciplina más psicopedagogía para continuar esta fase y el resto de grados. Se amplía la autoría a
**todos los 920 temas de Ciencias de la V3, de 2.° a 11.°**, sobre los 935 temas del catálogo. Los 15 fuera del alcance
de Ciencias siguen identificados como tales. Esta decisión reemplaza la prioridad de limitar la autoría a una
unidad hasta disponer del piloto, descrita en la spec 16; permite avanzar en paralelo sin inventar actos humanos.

La revisión de IA queda explícita. No se llena `revisado_por` con nombres de agentes, no se inventan tiempos
observados y no se declara aprobación del MINED. Los objetivos y archivos oficiales siguen inmutables.

## Capas y autoridad

- `config/secuencias_ia.yaml`: versión, roles, particiones por grado y distribución orientativa de tiempo.
- `data/interim/secuencias_ia/lotes/`: entradas reproducibles, no versionadas por ser proyecciones de la entrega
  y los dictámenes. Cada agente recibe la candidata completa de su etapa.
- `data/interim/secuencias_ia/dictamenes/`: salidas independientes versionadas por rol/partición/etapa.
- `secuencias_ia.py`: contrato, preparación, comprobación de citas/cambios, consolidación y permisos.
- `entregas/motor/0.2.0/`: nueva entrega con contrato 1.1.0, conservando íntegra la entrega 0.1.0 y contrato 1.0.0.

Los 920 registros son secuencias propuestas basadas en los cinco momentos de la malla, con modificaciones
explícitas del panel, criterios observables, consigna de salida, apoyos, alternativa sin conexión y sesiones
sugeridas. No equivalen a920 materiales experimentales terminados ni a920 sesiones de duración demostrada.
Los 230 paquetes previos y sus componentes conservan sus revisiones propias: esta nueva capa no los promueve
por asociación. Un tema puede tener secuencia nueva aunque carezca de paquete antiguo.

## Proceso de revisión

1. Comprobar identidad, alcance y fuentes de cada tema.
2. Revisión científica independiente por Biología, Física, Química o Tierra/Espacio.
3. Revisión psicopedagógica de la candidata científica por tramo; elaborar tres criterios de evaluación,
   apoyos, alternativa sin internet y una hipótesis de sesiones.
4. Refutación por agentes que no redactaron esos dictámenes.
5. Cierre del especialista sobre la candidata completa y las objeciones; refutar de nuevo sus cambios cuando los haya.

La primera proyección científica incluyó el indicador de logro y los momentos; no incluía `Indicador avanzado`.
La auditoría del sistema detectó esta limitación y el cierre la complementa con las columnas completas y evidencia
del indicador avanzado cuando existe. Se conserva la huella de cada entrada realmente leída. El indicador avanzado
se interpreta en el contexto de la unidad, sin exigir todos sus alcances en cada tema.

Roles y reglas: [`prompts/revisar_secuencias_ia.md`](../prompts/revisar_secuencias_ia.md).
Los agentes son ejecuciones separadas con especialización de tarea; no se presume diversidad de modelos ni
independencia estadística. El acuerdo entre agentes no demuestra verdad. Las citas se comprueban contra campos
exactos para evitar evidencia inventada; una cita curricular no sustituye una fuente científica externa.

## Retenciones y tiempo

Una decisión `retener`, confianza baja o corrección final sin nueva refutación excluye la secuencia del perfil de
autoría. Se conserva para consulta con sus motivos. Un dictamen posterior favorable no borra objeciones anteriores
por mayoría. Los conflictos con objetivos oficiales, protocolos ausentes o fuentes insuficientes se documentan;
no se fuerzan aprobaciones para alcanzar cobertura.

La distribución 5+8+12+20+7 minutos y 3 de transiciones es un presupuesto orientativo por sesión de 55 minutos.
`sesiones_sugeridas` y su motivo provienen de psicopedagogía. No se reduce automáticamente una actividad extensa
para hacerla caber. `tiempo_observado_min=null`, `presupuesto_demostrado=false` y `aula_habilitada=false` se exigen
en el contrato. El ensayo docente y la validación institucional se mantienen como información no disponible,
sin impedir seguir preparando y revisando propuestas de autoría.

## Integración y compatibilidad

El contrato 1.1.0 agrega `secuencias.jsonl` y las reglas de la capa en `catalogos.json`. Este catálogo también
incluye el registro de ejecuciones IA y sus límites, con huella del archivo de procedencia en el manifiesto;
los nombres de agentes identifican ejecuciones, no personas ni credenciales profesionales. El lector reconoce ambos
contratos y conserva exactamente los esquemas del 1.0.0. El validador reconstruye cada candidata y sus permisos
a partir de la malla y los dictámenes incluidos en la entrega, sin archivos del productor. La consulta expone la
secuencia por id estable o alias, y en autoría declara omisiones por retención.

La nueva entrega se valida antes de importar, se compara por bytes al reproducir y se puede activar o revertir
como la anterior. Ninguna llamada a Vertex o a otro servicio pagado forma parte de este proceso.
