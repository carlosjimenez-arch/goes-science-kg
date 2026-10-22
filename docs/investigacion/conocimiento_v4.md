# Brecha de conocimiento V4 y motor local de candidatos

> Registro histórico de investigación. Describe el corte y la ejecución indicados en este documento.
> Estado vigente del código, API y métricas: [documentación actual](../README.md) y [calidad](../CALIDAD.md).

Este informe contrasta el objetivo del producto con las capacidades materializadas.
El módulo `producto/conocimiento.py` aproxima el siguiente paso de la fase 2:
propone vínculos concretos desde las celdas V4 a vocabulario y objetivos extranjeros,
con evidencia, edición, ambigüedades y bloqueos. **No acepta enlaces ni demuestra
que la V4 esté alineada, tenga una progresión válida o mejore el aprendizaje.**

## Brechas concretas frente al objetivo

| Capacidad solicitada | Disponible y comprobable | Trabajo que falta para cumplirla |
|---|---|---|
| Modelo de conocimiento de V4 | 1020 filas con identidad y celdas; 513 conceptos y 30 prácticas históricos utilizables como vocabulario | Dictaminar relaciones nuevas por su contenido y evidencia; la identidad de una fila o un nombre coincidente no acredita `TRABAJA` |
| Prerrequisitos y progresión | 822 aristas históricas declaradas por IA, con confianza y justificación | Verificar dependencia conceptual, condición necesaria/facilitadora, contexto de grado y contradicciones; formar el DAG únicamente con relaciones aceptadas |
| Contraste de países | Objetivos históricos de seis sistemas; PDF y unidades DOCX/HTML rehidratables; 12 PDF de países con ediciones y poblaciones documentadas | Revisar traducción, obligatoriedad, edad y tramo de cada objetivo; resolver los localizadores históricos japoneses; dictaminar relación antes de usarla científicamente |
| Alineación PISA/ERCE/TIMSS | 22 categorías documentales con anclas primarias; declaraciones locales de la malla | Revisar conjuntamente contenido, práctica, conocimiento, demanda y evidencia de tarea; conservar marcos y poblaciones independientes |
| Simulación de una malla mejorada | Simulador y propuestas V3 reproducibles | Caso de uso V4 con relaciones aceptadas, acciones reversibles, carga real y recursos; demostrar antes/después sin heredar propuestas V3 |
| Paquetes por unidad | Motor de actividades con fuentes, jueces, reparación y abstención | Unidad V4 completa con presaberes, secuencia, apoyos, recursos y evaluación; el consenso automático no sustituye medir aprendizaje |

Los riesgos de reutilización no son hipotéticos:

- `propuesta.candidatos()` reconoce temas mediante `startswith("TEMA:")` y busca
  `TRABAJA` principal. Los IDs V4 son opacos y no siguen ese prefijo; la V4 tampoco
  dispone todavía de esas relaciones aceptadas. Ejecutar el caso antiguo no
  constituye una simulación V4.
- Las medianas de oportunidad antiguas utilizan grados normalizados por reglas
  históricas. La política nueva exige comprobar edad, cohorte, escolaridad y
  obligatoriedad. No es válido concluir que El Salvador llega tarde restando
  esos números a un grado V4.
- Las 822 dependencias históricas son método IA. Cadenas como «SV 7 → 7» u orden
  de aparición no demuestran una dependencia cognitiva, aunque figure confianza
  alta.
- Conceptos sin fuente primaria directa y traducciones históricas son navegación
  y material para revisión. Una definición redactada por el proyecto no puede
  validarse a sí misma como evidencia científica.
- En los metadatos de países hay documentos de 2013–2023. Su disponibilidad local
  no comprueba vigencia en 2026. El cotejo actual confirmó los bytes de tres programas DfE y
  la revisión MOE enero 2026 de primaria. Australia ya dispone de hidratación por código
  DOCX/HTML; los registros japoneses históricos siguen con SHA descriptivo y requieren migración.
  Los nuevos originales MEXT no se asignan a esas traducciones por proximidad o nombre.

Referencias de requisitos: `specs/02_modelo_del_grafo.md`,
`specs/06_propuesta_curricular.md`, `specs/16_producto_v4.md`,
`docs/ROADMAP.md`, `docs/ARQUITECTURA.md` y el memorando educativo. Las reglas
históricas de retirada, aprobación y carga no se convierten silenciosamente en
reglas nuevas: el workflow técnico V4 deberá documentar sus propios estados.

## Interfaz ejecutable

```python
from pathlib import Path

from goes_science_kg.curriculo import cargar_curriculo
from goes_science_kg.producto.conocimiento import generar_candidatos_conocimiento
from goes_science_kg.producto.referencias import cargar_referencias_historicas

informe = generar_candidatos_conocimiento(
    cargar_curriculo(),
    cargar_referencias_historicas(Path("data/grafo")),
)
```

`InformeConocimiento` conserva huellas de currículo, referencia, pipeline y
candidatos; procedencia del manifiesto V3; política completa; candidatos;
evidencias deduplicadas; referencias y resúmenes por fila/concepto/país. Todas las
1020 filas permanecen en el denominador, incluidas las que no producen candidato.
Los IDs de nodos se tratan como opacos: se usa `TipoNodo`, no prefijos de concepto,
práctica u objetivo extranjero. Una colisión del registro documental se rechaza.

Cada `CandidatoConocimiento` contiene ID reproducible, tipo, fila local,
origen/destino, método, estado, advertencias, bloqueos de aceptación, IDs de
evidencia local/externa, alternativas y contexto. Los métodos separan una mención
léxica de una ruta histórica que requiere revalidación.

El paquete es un puerto de entrada para el workflow especializado posterior.
Ese workflow ya está implementado en `producto/juicios.py` y `motor/conocimiento.py`, con CLI
`producto juicios`; conserva su propia salida y no modifica este informe de hipótesis.
`aceptados` está tipado como tupla obligatoriamente vacía: añadir `aceptar=True`
no permite aprobar relaciones. `dag_aceptado` permanece sin nodos/aristas y con
estado `sin_progresion_verificada`; los ciclos de hipótesis se informan aparte.

## Cómo produce propuestas

1. Comprueba versiones e identidades. Rehidrata encabezados y celdas V4 con SHA,
   valores originales y anclas de combinaciones. La copia de los metadatos nunca
   sustituye el contenido del archivo.
2. Construye un índice por primer término de las etiquetas y sinónimos explícitos
   del vocabulario histórico. Busca frases completas tokenizadas en objetivo,
   indicador de logro, evidencia, contenido y subcontenido. No utiliza stemming,
   embeddings, traducción o equivalencias inferidas.
3. Conserva el caso de términos de hasta tres caracteres: `CO`, `Co`, `pH` y `PH`
   no se colapsan. En términos largos admite diferencia de capitalización; no
   elimina tildes. Los offsets se refieren a NFKC; el literal citable continúa en
   la evidencia original. No es un analizador de fórmulas químicas.
4. Propone fila→concepto/práctica y conserva campo/celda/alias detectados. Un alias
   compartido conserva todas sus alternativas. Un límite de presupuesto no
   selecciona arbitrariamente un miembro del grupo ambiguo. La negación próxima,
   el nivel histórico y el namespace disciplinar aportan advertencias/bloqueos,
   sin decidir el significado científico.
5. Desde esos conceptos propone contrastes con objetivos extranjeros por mención
   en su representación histórica o por una ruta `TRABAJA` antigua. La arista
   antigua se conserva **como procedencia de la hipótesis**, no como vínculo V4.
6. Cuando hay SHA hexadecimal y localizador compatible, rehidrata la unidad real una vez:
   página PDF, fila XML de DOCX o sección DOM de HTML anclada al código oficial completo y único.
   Se conserva el inglés nativo, sin inventar paginación ni usar etiquetas como respaldo. Se indexa
   una sola vez por snapshot; un cambio de archivo o implementación invalida la reutilización.
   Esto acredita el objeto documental; falta revisar si implica el objetivo o su traducción.
   Una edición distinta, no fijada o sin hidratador primario bloquea aceptación científica.
7. Propone dependencias a partir de antecedentes históricos del concepto
   mencionado, ligadas a la fila destino. No asigna grado a ese antecedente,
   calcula medianas ni valida una progresión por su orden.

La política predeterminada admite hasta ocho conceptos/prácticas, seis objetivos
extranjeros y ocho hipótesis de prerrequisito por fila. Para objetivos extranjeros
rota por país en una cola reproducible; no es una clasificación de superioridad.
Se registran los IDs omitidos por cada presupuesto. Estos límites ordenan el
trabajo de revisión y no cambian el ranking del recuperador del producto.

Ejemplo para fijar una edición documental revisada por el integrador:

```python
from goes_science_kg.producto.conocimiento import EdicionEsperada, PoliticaConocimiento

politica = PoliticaConocimiento(ediciones_por_documento={
    "id_documental": EdicionEsperada(
        sha256=sha256_comprobado,
        version_documental=version_documental_comprobada,
    ),
})
```

Fijar edición no la convierte en norma vigente ni aprueba un enlace. Las
advertencias de fuentes científicamente erróneas del runtime siguen siendo un
gate independiente: un workflow que consuma estos paquetes debe aplicar también
los bloqueos curriculares existentes antes de llamadas remotas.

## Resultado local sobre V4

La reproducción medida usa `gskg producto conocimiento --politica config/politica_conocimiento_v4.yaml`.
La política fija cuatro registros históricos cotejados con bytes oficiales actuales: tres DfE y primaria
MOE revisada en enero de 2026. Los años de metadata permanecen 2013/2014/2023; seriales y correcciones
están en `config/curriculos_paises_2026.yaml`. No se renombran las ediciones.

El [resumen medido](resultados_conocimiento_v4.json) identifica por SHA el
artefacto completo `data/producto/V4/candidatos_conocimiento.json`. Este archivo
contiene propuestas de revisión y no constituye una generación de grafo activada.

| Resultado | Cantidad |
|---|---:|
| Filas examinadas | 1020 |
| Filas con alguna propuesta | 766 |
| Filas sin alias detectado | 254 |
| Propuestas fila→concepto | 1342 |
| Contrastes con objetivos extranjeros | 3584 |
| Hipótesis localizadas de prerrequisito | 1975 |
| Total de hipótesis | 6901 |
| Hipótesis de mención marcadas ambiguas | 77 |
| Celdas V4 utilizadas como evidencia | 2212 |
| Páginas externas deduplicadas | 120 |
| Unidades nativas DOCX deduplicadas | 46 |
| Enlaces aceptados / alineaciones confirmadas | 0 / 0 |

No se detectaron prácticas mediante los alias completos existentes. Es una
limitación real de recuperación: no demuestra ausencia de prácticas en la malla.
Resolverla exige nuevas expresiones explícitas y revisión semántica de acciones y
evidencias, sin inflar cobertura a partir de verbos aislados.

Los 3584 contrastes siguen pendientes de juicio especializado. La política seleccionada fija las
ediciones de 1203 candidatos (936 Inglaterra, 267 Singapur); otros 2381 no tienen edición fijada.
Los 445 candidatos australianos ya tienen evidencia nativa por código. Persisten 602 japoneses
sin localizador/formato compatible ni SHA hexadecimal en su registro histórico. Los nuevos PDF MEXT
no reparan ese vínculo automáticamente. Los bloqueos se solapan. Los 1342 candidatos de concepto carecen de
fuente primaria directa del concepto; conservan evidencia local de la mención.
En 696 aparece nivel histórico distinto del grado local, sin que ello resuelva su
pertinencia. Ninguno se aprueba mediante esos metadatos.

El presupuesto dejó 7084 posibles objetivos extranjeros y once dependencias fuera
de la cola seleccionada; sus identificadores permanecen informados por fila.
Los conteos seleccionados por país son AU 445, CO 835, ENG 936, JP 602, SG 267 y
UY 499. **No representan cobertura, calidad del sistema o acuerdos curriculares.**

La medida final de tiempo y memoria se conserva en el JSON adjunto. El alcance de
memoria es el máximo RSS de todo el proceso, incluidos inputs y trabajo anterior,
no un incremento atribuible solo al algoritmo. Es una observación local; no p95
ni SLA. La caché leyó una vez cada uno de once XLSX, dieciocho PDF y dos DOCX. Se liberan la
copia serializada del grafo y las filas ya consumidas durante el procesamiento.
No se usó nube ni conjuntos reservados para desarrollar o medir este módulo. La observación actual fue
8,704 s y 409.042.944 bytes de RSS máximo del proceso, sin contar esa memoria como incremento atribuible
al algoritmo. El JSON conserva conteos/huellas iniciales: 1047 sin hidratador frente a 602 ahora.
No es un ensayo de precisión, comparación p95 ni prueba de eficacia.

El índice estructurado omite ocultación declarada, campos Word y cambios eliminados; no ejecuta
JavaScript ni CSS externo y no certifica visibilidad computada por un navegador. Una unidad ambigua o
demasiado grande se rechaza sin truncarla. El límite queda en limites_visibilidad de cada evidencia.

## Camino concreto hacia un refuerzo curricular utilizable

1. **Juicio de enlace.** Implementado el flujo de cuatro lectores (científico,
   curricular, psicopedagogo y refutador), con huellas, fila completa, soportes
   semánticos y cierre tipado. Un veto impide respaldo, insuficiencia o fallo de
   contrato produce abstención. Falta ejecutar y medir juicios reales; no hay
   enlaces V4 aceptados. La salida independiente no sobrescribe hipótesis.
   [Contrato, operación y límites](../juicios_conocimiento.md).
2. **Prácticas y alineación.** Añadir candidatos de prácticas desde expresiones
   documentadas y revisar tareas completas contra las dimensiones independientes
   de PISA, ERCE y TIMSS. Compartir un tema o un código local no basta. Las
   alineaciones aceptadas deberán separar contenido, práctica, conocimiento,
   demanda y evidencia observable.
3. **Dependencias y DAG.** Revisar necesidad/facilitación y tipo de dependencia,
   resolver bloqueos/ciclos y comprobar el grafo aceptado también entre
   disciplinas. Un DAG matemático sin relaciones semánticamente justificadas no
   es una progresión educativa válida. La consolidación ya comprueba ciclos entre
   los lotes que recibe y conserva todos los vínculos conflictivos. El archivo y su integración
   en `producto-2` y recuperación por fila están implementados y probados con juicios simulados;
   falta una colección íntegra juzgada y calibrada con modelos reales.
4. **Contraste transferible.** Completar fuentes/ediciones, distinguir traducción
   y texto original y comprobar edad/cohorte/obligatoriedad. Solo después podrá
   evaluarse una decisión de secuencia; este módulo no calcula «adelanto» o
   «retraso» frente a los países.
5. **Escenario V4.** Usar exclusivamente relaciones aceptadas para un escenario
   reversible por unidad, con acciones explícitas, minutos, recursos, apoyos y
   comprobación de aprendizaje. Las filas no equivalen automáticamente a clases
   de 55 minutos. Comparar carga y secuencia antes/después sin copiar propuestas
   V3 ni declararlas aprobadas.

Los dictámenes pueden automatizarse con los puertos y presupuesto durable
existentes; esta propuesta no incorpora una capa humana rutinaria como puerta
técnica. La aprobación institucional y la evidencia de aprendizaje observado
permanecen distintas del respaldo automático. Un cambio de corpus, política o
código altera la huella y exige revisar qué dictámenes pueden reutilizarse.

## Pruebas y límites

Las pruebas focales cubren fuentes alteradas, alias compartidos, símbolos cortos,
negación, ausencia de stemming, conceptos/prácticas con estructuras diferentes,
nivel y grado incompatibles, versiones extranjeras distintas, DOCX/HTML/SHA no
verificable, ciclos de hipótesis, invariancia ante reordenamiento y prohibición de
inyectar una aceptación. No son una evaluación ciega de precisión o exhaustividad
de candidatos; no se leyó el gold.

Los códigos/documentos/niveles históricos pueden estar equivocados. Un literal
correcto puede usarse en un sentido diferente, y la búsqueda exacta omite
sinónimos ausentes. Los países disponibles no agotan los sistemas seleccionados
por la investigación nueva. Cero ciclos en las hipótesis seleccionadas no acredita
una secuencia correcta. Estas incertidumbres impiden dar por cerradas las fases
de conocimiento, alineación, simulación o eficacia del producto.
