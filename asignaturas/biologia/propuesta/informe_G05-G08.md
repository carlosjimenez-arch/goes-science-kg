# Propuesta de Biología, 5.° a 8.° (borrador)

Versión `propuesta-v3`, estado **borrador** hasta la revisión del equipo de Ciencias del MINED.
Detalle de cada acción, con su evidencia, en `propuesta_G05-G08.json`.

## En resumen
Proponemos 20 acciones: 7 movimientos, 5 fusiones, 4 temas nuevos, 1 división y 3 reformulaciones (`revisar`).

Después de la revisión de disciplinas, el ciclo tiene **106 temas** de Biología, y ese total se mantiene. No se quita
ningún tema.

El cambio central es que **5.° vuelve a tener Biología**: hoy tiene 1 tema y pasaría a 17. Son contenidos que
Inglaterra, Singapur, Australia, Colombia y Uruguay enseñan entre 2.° y 6.°.

## Qué cambia y por qué

**1. 5.° recibe una base de Biología (acciones 1, 2, 4 a 7 y 18).** La acción 2 añade el carbono al tema de biomoléculas.
- *La célula y la organización de los seres vivos*:
  - teoría celular y niveles de organización (CO 4, SG 5, UY 4);
  - biomoléculas de los alimentos y partes básicas de la célula;
  - difusión y ósmosis, trabajadas de forma experimental.
- *Funciones vitales de plantas y animales*:
  - propagación asexual, fecundación en plantas con flor y germinación (ENG 2, UY 3, SG 5);
  - respiración, circulación y estructura del sistema digestivo (ENG 4–6, SG 4–5, UY 4–5).
- *Interacciones en los ecosistemas*: competencia, depredación, simbiosis y redes tróficas (CO 3, ENG 2–6, UY 6).
- **Fósiles como evidencia de los cambios de los seres vivos** (ENG 4, CO 2). Es un tema nuevo en la unidad 6, antes del
  tema sobre extinciones.

**2. 6.° adelanta funciones y energía que hoy esperan hasta 8.° (acciones 3, 8, 13 a 15).**
- **Transporte en plantas:** sube de 8.° a 6.°, después de mitosis y diferenciación celular. No puede ir en 5.° porque
  los tejidos dependen de ellas.
- **Intercambio de gases en las hojas:** sube a 6.°, después de fotosíntesis y respiración.
- **Flujo de energía y pirámides ecológicas:** pasa de 7.° a 6.° (AU 6, SG 6, UY 6).
- **Digestión química:** pasa de 8.° a 6.°, justo después del tema de enzimas (ENG 4, SG 4, UY 4). Ese tema se
  reformula para presentar las enzimas como proteínas formadas por aminoácidos.

**3. Temas nuevos para contenidos que hoy llegan tarde (acciones 10, 12, 17 y 18):**
- Célula animal y célula vegetal, en 6.° (ENG 6; AU y UY 7).
- Papel de los seres vivos en los ciclos del agua, el oxígeno y el carbono, en 7.° (B5.3; CO 6,5, ENG 6, SG 5).
- Homeostasis y hormonas, en 8.° (AU 8, CO 8, UY 8).
- Fósiles, en 5.°.

Se pagan con cinco fusiones de temas que repiten contenido. La quinta paga la división del tema 6.8.
- Funciones de la hoja (8.°).
- Matriz extracelular (6.°).
- Replicación del ADN (7.°).
- Extracción de ADN (7.°).
- Excreción (8.°).

## Distribución por grado

| Grado | Antes | Después | % del ciclo (después) |
|---|---|---|---|
| 5.° | 1 | 17 | 16,0 % |
| 6.° | 34 | 34 | 32,1 % |
| 7.° | 44 | 39 | 36,8 % |
| 8.° | 27 | 16 | 15,1 % |
| **Total** | **106** | **106** | |

Todos los grados quedan sobre el 15 %. 8.° queda justo en el límite.

## Prerrequisitos que se ordenan
El script de validación confirma que ningún concepto queda antes que sus bloqueos. También confirma que se ordenan las
cinco secuencias invertidas del archivo de candidatos:
- carbono → biomoléculas;
- fósiles → historia de la vida;
- aminoácidos → proteínas → enzimas;
- evidencias de la evolución → filogenia;
- variación genética → selección natural.

La última se resuelve con la acción 20: el tema G07-2.8, que ya está en 7.° antes de 2.15, hace explícita la variación
en la descendencia.

Al ordenar las unidades de cada grado hay que respetar este orden:
- **5.°:**
  - biomoléculas y partes de la célula → difusión → respiración;
  - fósiles → extinciones (6.5).

  La historia de la vida también usa el tiempo geológico, que Ciencias de la Tierra enseña en el mismo 5.°.
- **6.°:**
  - ADN → mitosis → diferenciación → tejidos → transporte;
  - enzimas → digestión química;
  - fotosíntesis y respiración → intercambio de gases en hojas y flujo de energía.
- **7.°:** ciclo del agua → ciclos biogeoquímicos.
- **8.°:** excreción → homeostasis.

## Qué cambió con los países de alto desempeño
- **Inglaterra adelanta las plantas:** enseña transporte en plantas, fecundación en plantas con flor y depredación en
  2.° (equivalente). Esto refuerza las acciones de 5.° y 6.°.
- **La digestión química sube a 6.°:** Inglaterra, Singapur y Uruguay la enseñan en 4.°. Como la revisión de
  disciplinas dejó las enzimas en 6.° (G06-5.2), ya no hay que esperar a 8.°.
- **El flujo de energía pasa de 7.° a 6.°:** lo respaldan Australia y Singapur, además de Uruguay.
- **Nuevo tema de fósiles en 5.°:** Inglaterra los enseña en 4.°. Además, el tema de fósiles de 5.° (G05-6.3) pasó a
  Ciencias de la Tierra, y sin este tema la historia de la vida quedaría sin su prerrequisito.
- **Los ciclos del carbono y del oxígeno se suman al tema nuevo de ciclos de 7.°:** lo respaldan Inglaterra y Colombia.
- **La célula animal y vegetal se mantiene en 6.°:** el respaldo internacional es más fuerte (ENG 6, AU 7, UY 7).
- **Respaldados, pero sin cupo:** la herencia de rasgos y las adaptaciones conductuales (ENG, SG y AU, 4.°–5.°) no
  tienen tema en el ciclo. No caben en el límite de 20 acciones sin otra fusión, así que quedan como decisión abierta.

## Verificación con el grafo
Sobre la versión 1, la simulación del equipo coordinador dio dos resultados:
- Los conceptos que llegan 2 o más grados tarde bajaron de 15 a 4.
- El atraso medio bajó de 2,34 a 1,66 grados.

La versión 2 corrigió los cuatro prerrequisitos de confianza alta que esa simulación detectó:
- Membrana celular ← estructuras celulares y biomoléculas.
- Mitosis ← ADN.
- Tejidos vegetales ← diferenciación celular.

Resultado de la v3 con `gskg propuesta simular biologia 5 8`, sobre los candidatos regenerados:

| Métrica | Antes | Después |
|---|---|---|
| Secuencias invertidas en el ciclo | 10 | 2 |
| Secuencias invertidas de confianza alta | 5 | **0** |
| Conceptos que llegan 2 o más grados tarde | 18 | 9 |
| Desfase medio (grados) | 2,34 | 1,75 |

La simulación no aplica el grado de destino de una fusión. Por eso no refleja que la fusión de las funciones de la hoja
sube a 6.° (acción 8), y la mejora real es algo mayor.

## Decisiones abiertas para el MINED
1. **Carga de 5.°:** son 16 temas más, en tres unidades nuevas (numeración provisional 7, 8 y 9), más un tema de fósiles
   en la unidad 6. En 6.° se crea la unidad provisional 7, sobre estructura y transporte en las plantas.
2. **Herencia de rasgos y adaptaciones conductuales:** ENG, SG y AU las enseñan en 4.° y 5.°. Si se quieren en 5.°,
   cada una necesita un tema nuevo y otra fusión.
3. **Coordinación con Ciencias de la Tierra:** el tema de fósiles de Biología en 5.° debe ir junto al de datación de
   fósiles (G05-6.3), sin repetirlo.
4. **Enfermedades (B6.1):** solo tienen un tema débil en el ciclo y no hay países en el archivo que respalden un tema
   nuevo.
5. **Temas de 10.° y 11.°:** la célula vegetal, los fósiles, las evidencias de la evolución y las hormonas llegarán
   antes. Conviene ajustar su profundidad en Bachillerato.
