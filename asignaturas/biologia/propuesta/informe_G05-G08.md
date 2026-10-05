# Propuesta de Biología, 5.° a 8.° (borrador)

Versión `propuesta-v4`, estado **borrador** hasta la revisión del equipo de Ciencias del MINED.
Detalle de cada acción, con su evidencia, en `propuesta_G05-G08.json`.

## En resumen
Proponemos 19 acciones: 6 movimientos, 5 fusiones, 6 temas nuevos, 1 división y 1 reformulación (`revisar`).

El ciclo tiene **106 temas** de Biología, y ese total se mantiene. No se quita ningún tema.

El cambio central sigue siendo que **5.° vuelve a tener Biología**: hoy tiene 1 tema y pasaría a 17. Son contenidos
que Inglaterra, Singapur, Australia y Japón (alto desempeño), Colombia y Uruguay enseñan entre 2.° y 6.°.
Los grados de los países son equivalentes de El Salvador (Japón: grado japonés − 1).

## Qué cambia y por qué

**1. 5.° recibe una base de Biología (acciones 1, 2, 4 a 6, 16, 18 y 19).**
- *La célula y la organización de los seres vivos*: teoría celular, niveles de organización, biomoléculas (con el
  carbono como elemento base), **enzimas**, partes básicas de la célula y difusión, todo de forma experimental.
- *Funciones vitales de plantas y animales*: propagación asexual, fecundación en plantas con flor, germinación,
  **herencia de rasgos** (ENG 4, SG 5) y **digestión química** (ENG 4, SG 4, JP 5, UY 4).
- *Interacciones en los ecosistemas*: competencia, depredación (ENG 2, JP 5), simbiosis, redes tróficas y
  **adaptaciones conductuales** (JP 3, AU 4, SG 6).
- **Evidencias de la evolución** (fósiles y comparación de estructuras), en la unidad 6, antes de las extinciones.

**2. 6.° adelanta funciones de las plantas y la energía en los ecosistemas (acciones 3, 7, 11 y 13).**
- **Transporte en plantas:** sube de 8.° a 6.° (ENG 2, UY 3, JP 5, SG 5). No puede ir en 5.° porque los tejidos
  vegetales dependen de la diferenciación celular de 6.°.
- **Intercambio de gases en las hojas:** sube a 6.°, después de fotosíntesis y respiración.
- **Flujo de energía y pirámides** (de 7.° a 6.°) y un tema nuevo de **ciclos del carbono y del oxígeno**, juntos tras
  la fotosíntesis.

**3. Temas nuevos para contenidos que hoy llegan tarde (acciones 9, 11, 15, 16, 18 y 19):** célula animal y vegetal
(6.°), ciclos del carbono y del oxígeno (6.°), homeostasis y hormonas (8.°), evidencias de la evolución, herencia de
rasgos y adaptaciones conductuales (5.°).

**4. Se pagan con fusiones de temas que repiten contenido (acciones 7, 8, 10, 14 y 17).** Dos son triples y liberan
dos temas cada una: matriz extracelular (5.19, 5.20 y 5.22 de 6.°) y replicación del ADN (2.4, 2.5 y 2.6 de 7.°). Las
otras unen funciones de la hoja (8.°), extracción de ADN (7.°) y excreción (8.°). La de la hoja paga la división del
tema 6.8.

**5. El papel de los seres vivos en el ciclo del agua (acción 12)** se integra en el tema 5.8 de 7.° (JP 5, SG 5),
sin gastar presupuesto: no puede ir antes porque el ciclo del agua se enseña en 7.°.

## Qué cambió con Japón
- **La digestión química y las enzimas bajan a 5.° (antes, a 6.°).** Japón la enseña en 5.° (saliva y almidón), con
  Inglaterra y Singapur en 4.°. El tema de enzimas se mueve con ella, porque es su bloqueo.
- **Respiración, circulación y estructura del sistema digestivo ya no suben de 8.° a 5.°.** Con el grafo regenerado,
  El Salvador los introduce en 3.° y 4.°, a la par de la mediana de alto desempeño (JP 5, SG 4–5). Los temas de 8.°
  son una profundización y se quedan.
- **Entran la herencia de rasgos y las adaptaciones conductuales en 5.°**, que en v3 quedaron sin cupo. Japón suma un
  tercer país de alto desempeño para las adaptaciones (JP 3, AU 4, SG 6).
- **Los ciclos del carbono y del oxígeno pasan de 7.° a 6.°** (JP 5, ENG 6). El papel de los seres vivos en el ciclo
  del agua (JP 5, SG 5) se queda en 7.° por su bloqueo.
- **El tema nuevo de 5.° se centra en las evidencias de la evolución.** Los fósiles ya aparecen en 5.° (JP 5); lo que
  falta antes de la filogenia de 7.° son las evidencias.
- **Se retira la reformulación de 2.8 (variación en la descendencia):** el grafo ya la ubica en 7.°, antes de la
  selección natural.

## Distribución por grado

| Grado | Antes | v3 | v4 | % del ciclo (v4) |
|---|---|---|---|---|
| 5.° | 1 | 17 | 17 | 16,0 % |
| 6.° | 34 | 34 | 32 | 30,2 % |
| 7.° | 44 | 39 | 37 | 34,9 % |
| 8.° | 27 | 16 | 20 | 18,9 % |
| **Total** | **106** | **106** | **106** | |

Todos los grados quedan sobre el 15 %. 8.° deja de estar en el límite.

## Prerrequisitos que se ordenan
El script de validación confirma que ningún concepto movido queda antes que sus bloqueos y que se corrigen las tres
secuencias invertidas de confianza alta del archivo de candidatos: carbono → biomoléculas; aminoácidos → proteínas →
enzimas; evidencias de la evolución → filogenia. También se corrigen dos de confianza media: célula animal y vegetal
→ organelos, y herencia de rasgos → ADN.

Orden que hay que respetar dentro de cada grado:
- **5.°:** biomoléculas → enzimas → digestión química; estructuras celulares → difusión; propagación asexual →
  fecundación → herencia de rasgos; redes tróficas → adaptaciones conductuales; fósiles → extinciones.
- **6.°:** partes básicas de la célula → célula animal y vegetal; diferenciación → tejidos → transporte; fotosíntesis y
  respiración → intercambio de gases en hojas, flujo de energía y ciclos del carbono y del oxígeno.
- **7.°:** ciclo del agua → papel de los seres vivos en él (5.8).
- **8.°:** excreción → homeostasis.

## Verificación con el grafo
Simulación en memoria (`propuesta.simular`) sobre los candidatos regenerados con Japón:

| Métrica | Antes | v3 | v4 |
|---|---|---|---|
| Secuencias invertidas en el ciclo | 7 | 1 | **2** |
| Secuencias invertidas de confianza alta | 3 | 0 | **1** |
| Conceptos que llegan 2 o más grados tarde | 14 | 6 | **5** |
| Desfase medio (grados) | 2,06 | 1,64 | **1,59** |

## Decisiones abiertas para el MINED
1. **Carga de 5.°:** 16 temas más, en tres unidades nuevas (numeración provisional 7, 8 y 9) y un tema en la unidad 6.
   En 6.° se crea la unidad provisional 7, sobre estructura y transporte en las plantas.
2. **Enzimas en 5.°:** presentar las enzimas como proteínas formadas por aminoácidos exige un modelo sencillo (cuentas).
   Quedan dos dependencias de Química sin resolver en 5.°: energía de activación (catalizadores) y fuerzas
   intermoleculares. El tema de enzimas (G06-5.2, acción 2) **deja de llevar la etiqueta *Catalizadores***
   (`quitar_conceptos`): muestra que la catalasa acelera un proceso, pero no trabaja la energía de activación, que es
   lo que define el concepto químico. Así Química 5.° a 8.° deja de enseñar catalizadores en 6.° antes de la energía de
   activación (10.°). El costo es la única secuencia de confianza alta que queda en Biología (enzimas en 5.°,
   catalizadores en 10.°): proponemos tratarla como aceptable, porque en 5.° la enzima se presenta solo como «algo que
   acelera sin gastarse»; o bien revisar esa arista del grafo. Si se prefiere, enzimas y digestión química pueden quedar en 6.° como en v3, pero 5.° bajaría a 15 temas (14,2 %) y haría falta otro tema allí.
3. **Coordinación con Ciencias de la Tierra:** el tema de evidencias de la evolución debe ir junto al de fósiles de 5.°,
   sin repetirlo.
4. **Enfermedades (B6.1):** solo tienen un tema débil en el ciclo y no hay países en el archivo que respalden un tema
   nuevo.
5. **Temas de 10.° y 11.°:** la célula vegetal, las evidencias de la evolución, la herencia, los ciclos
   biogeoquímicos y las hormonas llegarán antes. Conviene ajustar su profundidad en Bachillerato.
