# Química · contraste internacional de 9.°–11.° (malla V2)

> Generado por `gskg internacional construir`. Método y límites: `specs/11_grafos_internacionales_9_11.md` y `internacional/README.md`.
> Los datos de los países los extrajo y validó Gemini (Vertex AI, proyecto GOES), con un modelo para
> extraer y otro para validar. Las clases dependen de etiquetas de IA y requieren revisión del MINED.

## Resumen

| Clase | Conceptos | Qué significa |
|---|---|---|
| Faltantes del núcleo común | 0 | El consenso (≥ 5 países) lo enseña a todos los estudiantes hasta ese grado; la V2 no lo tiene en 2.°–11.°. |
| No retomados en 9.°–11.° | 0 | La V2 solo lo ve antes de 9.°; al menos 5 países lo profundizan en su núcleo de 9.°–11.°. |
| Llegan tarde | 0 | La V2 lo introduce en 9.°–11.°, dos o más grados después de que el núcleo alcanza el consenso. |
| Nivel de especialización en un curso obligatorio | 27 | La V2 lo introduce en 9.°–11.°, pero los países solo lo enseñan en cursos electivos. |
| Adelantados | 0 | La V2 lo introduce en 9.°–11.°, 1,5 grados o más antes que la mediana del núcleo de los países. |
| Sin referente | 4 | La V2 lo enseña en 9.°–11.° y menos de 3 países lo tienen en su núcleo: no hay referente para fecharlo. |
| Alineados | 25 | La V2 lo introduce en 9.°–11.° con un momento coherente con el consenso (± 1,5 grados). |
| Retomados | 57 | La V2 lo introduce antes de 9.° y lo vuelve a trabajar en 9.°–11.° (espiral). |
| Solo antes de 9.° | 3 | La V2 lo ve antes de 9.° y el núcleo internacional no lo exige en 9.°–11.°. |
| Inciertos (a revisión) | 24 | La lectura amplia y la estricta del etiquetado dan clases distintas: no se afirma nada hasta revisarlo (revision_clases.csv). |

Países con núcleo común por grado SV (denominador del consenso): 9.°: AU, EE, ENG, JP, KR, ON, SG, TW; 10.°: AU, EE, ENG, JP, KR, ON, SG, TW; 11.°: AU, EE, ENG, JP, KR, ON, SG, TW

Sensibilidad: con 4 países en lugar de 5, 1 conceptos más pasarían de «solo antes de 9.°» a «no retomados».

Revisión experta: 1 conceptos cambiaron de clase frente a la regla automática (`data/interim/internacional/revisiones.json`): Equilibrio y rapidez en procesos industriales (solo_especializacion → alineado).

Inciertos: 24 conceptos tienen clases distintas en la lectura amplia y en la estricta; no se afirma nada de ellos hasta revisarlos (`revision_clases.csv`, con las dos clases).

## Nivel de especialización en un curso obligatorio (27)

La V2 lo introduce en 9.°–11.°, pero los países solo lo enseñan en cursos electivos.

| Concepto | Grados SV (V2) | Consenso del núcleo | Países (grado de 1.ª aparición; esp. = solo electiva) | Evidencia |
|---|---|---|---|---|
| Constante de equilibrio | 9.°–10.° | mediana 11; 1 con núcleo en 9.°–11.° | AU esp., EE esp., ENG esp., HK esp., JP esp., KR esp., ON esp., SG 11, TW esp. | SV: G09-CIE-U3-3.14 (Matriz_Ciencias_9no_Grado_U1_U12.xlsx, hoja «Unidad 3 - Equilibrio químico», fila 16)<br>AU · Senior Secondary Chemistry [esp.] (au_ss_qui, p. 4): «Seleccionar y usar representaciones apropiadas como semiecuaciones, ecuaciones balanceadas, constantes de equilibrio, pH y diagramas de celdas para resolver problemas.»<br>EE · Gymnasium, electivos de ciencias [esp.] (ee_gym_ele, p. 36): «Expresa la constante de equilibrio y el producto de solubilidad; investiga el efecto de varios factores en el equilibrio y relaciona los resultados con la constante.» |
| Ley de Hess y entalpías de formación | 10.° | mediana 9.5; 3 con núcleo en 9.°–11.° | AU esp., EE esp., ENG 8.5, HK esp., JP esp., KR esp., ON esp., SG 11, TW 9.5 | SV: G10-QUI-U11-11.2 (Matriz_Bachillerato_Quimica_10_11.xlsx, hoja «Química 10.°», fila 86)<br>AU · Senior Secondary Chemistry [esp.] (au_ss_qui, p. 1): «Comprender la entalpía y aplicarla para describir y explicar cualitativa y cuantitativamente los cambios de energía en las reacciones químicas.»<br>EE · Gymnasium, electivos de ciencias [esp.] (ee_gym_ele, p. 36): «Determina experimentalmente el cambio de entalpía; aplica la ley de Hess; explica la catálisis, distingue catálisis homogénea y heterogénea; investiga experimentalmente el efecto de los catalizadores.» |
| Reacciones orgánicas características | 11.° | mediana 9.5; 2 con núcleo en 9.°–11.° | AU esp., EE 10.5, ENG esp., HK esp., JP esp., KR esp., ON esp., SG 9.5, TW 7 | SV: G11-QUI-U3-3.8 (Matriz_Bachillerato_Quimica_10_11.xlsx, hoja «Química 11.°», fila 31)<br>AU · Senior Secondary Chemistry [esp.] (au_ss_qui4, p. 1): «Identificar la clase de compuesto orgánico mediante sus propiedades químicas y reacciones específicas (incluyendo ácido-base y oxidación) basadas en los grupos funcionales presentes.»<br>EE · Gymnasium, cursos obligatorios [núcleo] (ee_gym, p. 19): «Compara propiedades químicas de hidrocarburos saturados, insaturados y aromáticos; formula ecuaciones de halogenación, hidrogenación e hidratación catalítica.» |
| Síntesis química y rutas de reacción | 10.°–11.° | mediana 10.75; 2 con núcleo en 9.°–11.° | AU esp., EE 10.5, ENG esp., HK esp., JP esp., KR esp., ON esp., SG 11, TW esp. | SV: G10-QUI-U10-10.4 (Matriz_Bachillerato_Quimica_10_11.xlsx, hoja «Química 10.°», fila 84)<br>AU · Senior Secondary Chemistry [esp.] (au_ss_qui4, p. 1): «Realizar investigaciones de forma segura y metódica, usando métodos de síntesis orgánica y recopilando datos de análisis químicos para obtener resultados válidos y confiables.»<br>EE · Gymnasium, cursos obligatorios [núcleo] (ee_gym, p. 19): «Compara las reacciones de formación e hidrólisis de ésteres, formula las ecuaciones químicas correspondientes y prepara un éster simple.» |
| Ecuación de los gases ideales y volumen molar | 10.° | mediana 9.5; 3 con núcleo en 9.°–11.° | AU esp., EE 8, ENG esp., HK esp., JP 9.5, KR esp., ON esp., SG 9.5, TW esp. | SV: G10-QUI-U6-6.3 (Matriz_Bachillerato_Quimica_10_11.xlsx, hoja «Química 10.°», fila 57)<br>AU · Senior Secondary Chemistry [esp.] (au_ss_qui, p. 3): «Usar representaciones matemáticas para resolver problemas, incluyendo el concepto de mol para calcular masas, volúmenes de gases y concentraciones de soluciones.»<br>EE · Escuela básica, III etapa (grados 7–9) [núcleo] (ee_basic, p. 27): «Realizar cálculos basados en la relación entre cantidad de sustancia, masa y volumen de gas, usando unidades correctas y justificando pasos.» |
| Polimerización por adición y por condensación | 11.° | mediana 10; 2 con núcleo en 9.°–11.° | AU esp., EE 10.5, ENG esp., HK esp., JP esp., KR esp., ON esp., SG 9.5, TW esp. | SV: G11-QUI-U1-1.5 (Matriz_Bachillerato_Quimica_10_11.xlsx, hoja «Química 11.°», fila 7)<br>AU · Senior Secondary Chemistry [esp.] (au_ss_qui4, p. 1): «Comprender las reacciones de adición, condensación y oxidación, y predecir los productos de estas reacciones.»<br>EE · Gymnasium, cursos obligatorios [núcleo] (ee_gym, p. 19): «Representa un segmento del polímero formado a partir de un alqueno.» |
| Potenciales estándar de electrodo y de celda | 11.° | mediana 8.5; 3 con núcleo en 9.°–11.° | AU esp., EE 8, ENG 8.5, HK esp., JP 9.5, KR esp., ON esp., SG esp., TW esp. | SV: G11-QUI-U6-6.10 (Matriz_Bachillerato_Quimica_10_11.xlsx, hoja «Química 11.°», fila 64)<br>AU · Senior Secondary Chemistry [esp.] (au_ss_qui, p. 4): «Usar representaciones matemáticas para resolver problemas, incluyendo el cálculo de potenciales de celda, uso del mol en análisis volumétrico y cálculo de pH.»<br>EE · Escuela básica, III etapa (grados 7–9) [núcleo] (ee_basic, p. 27): «Distinguir entre metales activos, moderadamente activos y poco activos según su posición en la serie de actividad.» |
| Energía de Gibbs y espontaneidad | 10.°–11.° | —; 0 con núcleo en 9.°–11.° | AU esp., EE esp., ENG esp., HK esp., JP esp., KR esp., SG esp. | SV: G10-QUI-U11-11.4 (Matriz_Bachillerato_Quimica_10_11.xlsx, hoja «Química 10.°», fila 88)<br>AU · Senior Secondary Chemistry [esp.] (au_ss_qui, p. 5): «Describir cómo las celdas electrolíticas usan una diferencia de potencial externa para inducir reacciones redox no espontáneas en aplicaciones a pequeña escala e industriales.»<br>EE · Gymnasium, electivos de ciencias [esp.] (ee_gym_ele, p. 29): «Explicar la diferencia entre el equilibrio estacionario y el termodinámico, y demostrar su papel fundamental en la existencia de la vida.» |
| Estereoquímica y quiralidad | 10.°–11.° | mediana 9; 1 con núcleo en 9.°–11.° | EE esp., ENG esp., HK esp., JP esp., ON esp., SG 11, TW 7 | SV: G10-BIO-U1-1.7 (Matriz_Bachillerato_Biologia_10_11.xlsx, hoja «Biología 10.°», fila 9)<br>EE · Gymnasium, electivos de ciencias [esp.] (ee_gym_ele, p. 40): «Construcción y comparación de modelos moleculares de isómeros geométricos y ópticos, incluyendo el uso de programas informáticos.»<br>ENG · A level Biology / Chemistry / Physics [esp.] (eng_alevel, p. 11): «Identificar grupos funcionales, isómeros estructurales y estereoisómeros, incluyendo isomería geométrica (E-Z) por rotación restringida e isomería óptica por quiralidad.» |
| Hidrólisis de sales y disoluciones amortiguadoras | 9.°–11.° | mediana 11; 1 con núcleo en 9.°–11.° | EE esp., ENG esp., JP esp., KR esp., ON esp., SG 11, TW esp. | SV: G09-CIE-U3-3.15 (Matriz_Ciencias_9no_Grado_U1_U12.xlsx, hoja «Unidad 3 - Equilibrio químico», fila 17)<br>EE · Gymnasium, electivos de ciencias [esp.] (ee_gym_ele, p. 36): «Investiga la hidrólisis de sales en agua; justifica el medio de la solución de una sal que se hidroliza utilizando la ecuación de reacción.»<br>ENG · A level Biology / Chemistry / Physics [esp.] (eng_alevel, p. 10): «Comprender las constantes de disociación (Ka), calcular el pH de ácidos débiles y aplicar el concepto de soluciones amortiguadoras.» |
| Ley de velocidad, orden de reacción y ecuación de Arrhenius | 10.° | mediana 11; 1 con núcleo en 9.°–11.° | EE esp., ENG esp., HK esp., KR esp., ON esp., SG 11, TW esp. | SV: G10-QUI-U12-12.2 (Matriz_Bachillerato_Quimica_10_11.xlsx, hoja «Química 10.°», fila 93)<br>EE · Gymnasium, electivos de ciencias [esp.] (ee_gym_ele, p. 36): «Analiza la información contenida en la ecuación de velocidad de una reacción química.»<br>ENG · A level Biology / Chemistry / Physics [esp.] (eng_alevel, p. 10): «Determinar y usar ecuaciones de velocidad y órdenes de reacción para obtener información sobre el paso limitante de la reacción.» |
| Medición de la velocidad de reacción | 10.° | mediana 9; 2 con núcleo en 9.°–11.° | AU esp., ENG 8.5, HK esp., JP esp., KR esp., ON esp., SG 9.5 | SV: G10-QUI-U12-12.1 (Matriz_Bachillerato_Quimica_10_11.xlsx, hoja «Química 10.°», fila 92)<br>AU · Senior Secondary Chemistry [esp.] (au_ss_qui, p. 2): «Usar habilidades de investigación para predecir e identificar productos y medir la velocidad de las reacciones químicas.»<br>ENG · GCSE Combined Science [núcleo] (eng_gcse_comb, p. 11): «Realizar cálculos de velocidad para reacciones químicas.» |
| Valoración ácido-base | 9.°–11.° | mediana 9.5; 2 con núcleo en 9.°–11.° | AU esp., ENG esp., HK esp., JP 9.5, KR esp., ON esp., SG 9.5, TW esp. | SV: G09-CIE-U3-3.19 (Matriz_Ciencias_9no_Grado_U1_U12.xlsx, hoja «Unidad 3 - Equilibrio químico», fila 21)<br>AU · Senior Secondary Chemistry [esp.] (au_ss_qui, p. 4): «Diseñar, realizar, evaluar y comunicar investigaciones sobre propiedades de ácidos y bases, reacciones redox y celdas electroquímicas, incluyendo análisis volumétrico.»<br>ENG · A level Biology / Chemistry / Physics [esp.] (eng_alevel, p. 9): «Realizar cálculos de titulación no estructurados basados únicamente en resultados experimentales.» |
| Espectros atómicos y modelo de Bohr | 10.° | mediana 9.5; 1 con núcleo en 9.°–11.° | AU esp., ENG esp., HK esp., JP 9.5, ON esp., SG esp., TW esp. | SV: G10-QUI-U3-3.5 (Matriz_Bachillerato_Quimica_10_11.xlsx, hoja «Química 10.°», fila 27)<br>AU · Senior Secondary Chemistry [esp.] (au_ss_qui, p. 1): «Modelar átomos como un núcleo rodeado de electrones en niveles de energía, unidos por fuerzas electrostáticas; representarlos usando diagramas de capas electrónicas o nubes de carga.»<br>ENG · GCSE separate sciences (triple) [esp.] (eng_gcse_triple, p. 29): «Interpretar pruebas a la llama para identificar iones metálicos, incluyendo litio, sodio, potasio, calcio y cobre.» |
| Estructura y propiedades de los polímeros | 11.° | mediana 8.25; 2 con núcleo en 9.°–11.° | AU esp., ENG 6, HK esp., JP 9.5, SG 9.5, TW 7 | SV: G11-QUI-U1-1.4 (Matriz_Bachillerato_Quimica_10_11.xlsx, hoja «Química 11.°», fila 6)<br>AU · Senior Secondary Chemistry [esp.] (au_ss_qui4, p. 2): «Explicar propiedades de materiales orgánicos (proteínas, carbohidratos, polímeros sintéticos), como resistencia, densidad y biodegradabilidad, considerando sus estructuras primarias, secundarias o terciarias.»<br>ENG · GCSE separate sciences (triple) [esp.] (eng_gcse_triple, p. 27): «Recordar los principios básicos de la polimerización por adición en relación con el grupo funcional del monómero y las unidades repetitivas del polímero.» |
| Indicadores ácido-base | 9.°–11.° | 9.° (88% de los países con núcleo); 4 con núcleo en 9.°–11.° | AU esp., EE 8, ENG 6, HK esp., JP 5, KR 9, ON 9, SG 9.5, TW 7 | SV: G09-CIE-U3-3.10 (Matriz_Ciencias_9no_Grado_U1_U12.xlsx, hoja «Unidad 3 - Equilibrio químico», fila 12)<br>AU · Senior Secondary Chemistry [esp.] (au_ss_qui, p. 5): «Describir cómo el análisis volumétrico ácido-base identifica el punto de equivalencia midiendo el cambio de pH con indicadores o pehachímetros para revelar el punto final.»<br>EE · Escuela básica, III etapa (grados 7–9) [núcleo] (ee_basic, p. 27): «Relacionar propiedades ácidas y alcalinas con las partículas presentes, y evaluar el entorno de una solución mediante indicadores y pH.» |
| Hibridación de orbitales | 10.°–11.° | mediana 11; 1 con núcleo en 9.°–11.° | EE esp., ENG esp., HK esp., SG 11, TW esp. | SV: G10-QUI-U5-5.7 (Matriz_Bachillerato_Quimica_10_11.xlsx, hoja «Química 10.°», fila 47)<br>EE · Gymnasium, electivos de ciencias [esp.] (ee_gym_ele, p. 28): «Investigar y comparar la estructura de las sustancias utilizando modelos moleculares o programas informáticos.»<br>ENG · A level Biology / Chemistry / Physics [esp.] (eng_alevel, p. 11): «Describir la estructura y los enlaces presentes en la molécula de benceno.» |
| Hidrocarburos aromáticos | 11.° | mediana 10.5; 3 con núcleo en 9.°–11.° | EE 10.5, ENG 8.5, HK esp., JP esp., SG 11 | SV: G11-QUI-U3-3.1 (Matriz_Bachillerato_Quimica_10_11.xlsx, hoja «Química 11.°», fila 24)<br>EE · Gymnasium, cursos obligatorios [núcleo] (ee_gym, p. 19): «Compara propiedades químicas de hidrocarburos saturados, insaturados y aromáticos; formula ecuaciones de halogenación, hidrogenación e hidratación catalítica.»<br>ENG · GCSE Combined Science [núcleo] (eng_gcse_comb, p. 21): «Explicar que la gran variedad de compuestos orgánicos naturales y sintéticos se debe a la capacidad del carbono para formar familias de compuestos similares, cadenas y anillos.» |
| Mecanismos de reacción | 10.°–11.° | —; 0 con núcleo en 9.°–11.° | EE esp., ENG esp., HK esp., ON esp., SG esp. | SV: G10-QUI-U12-12.5 (Matriz_Bachillerato_Quimica_10_11.xlsx, hoja «Química 10.°», fila 96)<br>EE · Gymnasium, electivos de ciencias [esp.] (ee_gym_ele, p. 36): «Analiza la información contenida en la ecuación de velocidad de una reacción química.»<br>ENG · A level Biology / Chemistry / Physics [esp.] (eng_alevel, p. 10): «Determinar y usar ecuaciones de velocidad y órdenes de reacción para obtener información sobre el paso limitante de la reacción.» |
| Reactivo limitante y en exceso | 10.° | mediana 9.5; 3 con núcleo en 9.°–11.° | EE 10.5, ENG 8.5, HK esp., ON esp., SG 9.5, TW esp. | SV: G10-QUI-U10-10.2 (Matriz_Bachillerato_Quimica_10_11.xlsx, hoja «Química 10.°», fila 82)<br>EE · Gymnasium, cursos obligatorios [núcleo] (ee_gym, p. 19): «Resuelve problemas de cálculo basados en ecuaciones de reacción, teniendo en cuenta el porcentaje de rendimiento, las pérdidas y las impurezas.»<br>ENG · GCSE Combined Science [núcleo] (eng_gcse_comb, p. 25): «Deducir la estequiometría de una ecuación a partir de las masas y explicar el efecto de un reactivo limitante.» |
| Entropía | 10.° | —; 0 con núcleo en 9.°–11.° | EE esp., ENG esp., KR esp., SG esp. | SV: G10-BIO-U2-2.2 (Matriz_Bachillerato_Biologia_10_11.xlsx, hoja «Biología 10.°», fila 15)<br>EE · Gymnasium, electivos de ciencias [esp.] (ee_gym_ele, p. 30): «Conocer la fisicoquímica de la vida: equilibrio químico y estacionario, entropía, naturaleza física de la vida y problemas sobre el origen de la vida.»<br>ENG · A level Biology / Chemistry / Physics [esp.] (eng_alevel, p. 10): «Usar conceptos de energética, incluyendo la entropía, para predecir la viabilidad de las reacciones químicas.» |
| Nanomateriales y manufactura molecular | 11.° | mediana 8.5; 0 con núcleo en 9.°–11.° | AU esp., ENG 8.5, HK esp., TW esp. | SV: G11-QUI-U1-1.8 (Matriz_Bachillerato_Quimica_10_11.xlsx, hoja «Química 11.°», fila 10)<br>AU · Senior Secondary Chemistry [esp.] (au_ss_qui, p. 2): «Definir los nanomateriales como sustancias que contienen partículas en el rango de 1 a 100 nm y que poseen propiedades específicas relacionadas con este tamaño.»<br>ENG · GCSE separate sciences (triple) [esp.] (eng_gcse_triple, p. 23): «Comparar las dimensiones "nano" con las dimensiones típicas de átomos y moléculas.» |
| Producto de solubilidad (Kps) | 11.° | —; 0 con núcleo en 9.°–11.° | EE esp., ON esp., SG esp., TW esp. | SV: G11-QUI-U5-5.1 (Matriz_Bachillerato_Quimica_10_11.xlsx, hoja «Química 11.°», fila 50)<br>EE · Gymnasium, electivos de ciencias [esp.] (ee_gym_ele, p. 36): «Expresa la constante de equilibrio y el producto de solubilidad; investiga el efecto de varios factores en el equilibrio y relaciona los resultados con la constante.»<br>ON · Chemistry, Grade 12 (SCH4U) [esp.] (on_sch4u, p. 106): «Las aplicaciones de los sistemas químicos en equilibrio tienen implicaciones significativas para la naturaleza y la industria.» |
| Química de los ácidos nucleicos | 10.°–11.° | —; 0 con núcleo en 9.°–11.° | ENG esp., HK esp., JP esp., KR esp. | SV: G10-BIO-U1-1.10 (Matriz_Bachillerato_Biologia_10_11.xlsx, hoja «Biología 10.°», fila 12)<br>ENG · GCSE separate sciences (triple) [esp.] (eng_gcse_triple, p. 27): «Recordar que el ADN es un polímero de cuatro nucleótidos y que otros polímeros naturales importantes se basan en azúcares y aminoácidos.»<br>HK · HKDSE Chemistry (marco actualizado) [esp.] (hk_qui, p. 41): «Buscar y presentar información sobre el papel de los enlaces de hidrógeno en macromoléculas como el ADN y las proteínas.» |
| Resonancia y carga formal | 10.° | —; 0 con núcleo en 9.°–11.° | EE esp., ENG esp., JP esp., SG esp. | SV: G10-QUI-U5-5.4 (Matriz_Bachillerato_Quimica_10_11.xlsx, hoja «Química 10.°», fila 44)<br>EE · Gymnasium, electivos de ciencias [esp.] (ee_gym_ele, p. 38): «Explicar las propiedades de los compuestos aromáticos, incluyendo fenoles y aminas aromáticas, a través de la deslocalización de enlaces.»<br>ENG · A level Biology / Chemistry / Physics [esp.] (eng_alevel, p. 11): «Describir la estructura y los enlaces presentes en la molécula de benceno.» |
| Relación entre energía de Gibbs y constante de equilibrio | 10.° | —; 0 con núcleo en 9.°–11.° | ENG esp., HK esp., SG esp. | SV: G10-QUI-U12-12.13 (Matriz_Bachillerato_Quimica_10_11.xlsx, hoja «Química 10.°», fila 104)<br>ENG · A level Biology / Chemistry / Physics [esp.] (eng_alevel, p. 10): «Analizar el efecto de los cambios de temperatura sobre la constante de equilibrio Kc.»<br>HK · HKDSE Chemistry (marco actualizado) [esp.] (hk_qui, p. 69): «Derivar inductivamente la relación entre la temperatura y el valor de Kc a partir de conjuntos de datos proporcionados.» |
| Teorías del enlace de valencia y de orbitales moleculares | 10.° | mediana 11; 1 con núcleo en 9.°–11.° | EE esp., SG 11, TW esp. | SV: G10-QUI-U5-5.3 (Matriz_Bachillerato_Quimica_10_11.xlsx, hoja «Química 10.°», fila 43)<br>EE · Gymnasium, electivos de ciencias [esp.] (ee_gym_ele, p. 40): «Distingue entre enlaces sigma y pi, y relaciona la forma espacial de las moléculas con los orbitales híbridos y la dirección de los enlaces.»<br>SG · A-Level H1 Chemistry [esp.] (sg_h1_qui, p. 12): «Describir el enlace covalente en términos de superposición de orbitales (solo s y p), formando enlaces σ y π.» |

## Sin referente (4)

La V2 lo enseña en 9.°–11.° y menos de 3 países lo tienen en su núcleo: no hay referente para fecharlo.

| Concepto | Grados SV (V2) | Consenso del núcleo | Países (grado de 1.ª aparición; esp. = solo electiva) | Evidencia |
|---|---|---|---|---|
| Ecuaciones y reacciones nucleares | 10.°–11.° | mediana 8.5; 0 con núcleo en 9.°–11.° | ENG 8.5, ON esp. | SV: G10-QUI-U13-13.9 (Matriz_Bachillerato_Quimica_10_11.xlsx, hoja «Química 10.°», fila 114)<br>ON · Chemistry, Grade 12 (SCH4U) [esp.] (on_sch4u, p. 112): «Evaluar los beneficios sociales de tecnologías basadas en principios de estructuras atómicas y moleculares, como la resonancia magnética, cristalografía de rayos X o energía nuclear.» |
| Ecuación de Nernst | 11.° | —; 0 con núcleo en 9.°–11.° | SG esp. | SV: G11-QUI-U6-6.10 (Matriz_Bachillerato_Quimica_10_11.xlsx, hoja «Química 11.°», fila 64)<br>SG · A-Level H2 Chemistry [esp.] (sg_h2_qui, p. 33): «Comprender las limitaciones del uso de potenciales estándar de celda para predecir la espontaneidad de una reacción.» |
| Energía reticular y ciclo de Born-Haber | 10.° | mediana 11; 1 con núcleo en 9.°–11.° | SG 11 | SV: G10-QUI-U5-5.11 (Matriz_Bachillerato_Quimica_10_11.xlsx, hoja «Química 10.°», fila 51)<br>SG · A-Level H1 Chemistry [esp.] (sg_h1_qui, p. 17): «Explicar cualitativamente el efecto de la carga y el radio iónico sobre la magnitud numérica de la energía reticular.» |
| Leyes de los gases | 10.°–11.° | mediana 8.25; 1 con núcleo en 9.°–11.° | AU esp., HK esp., JP esp., KR 7, ON esp., SG esp., TW 9.5 | SV: G10-QUI-U6-6.2 (Matriz_Bachillerato_Quimica_10_11.xlsx, hoja «Química 10.°», fila 56)<br>AU · Senior Secondary Chemistry [esp.] (au_ss_qui, p. 2): «Comprender cómo la teoría cinética explica el comportamiento de los gases y cómo la teoría de colisiones explica y predice el efecto de condiciones variables en la velocidad de reacción.»<br>HK · HKDSE Chemistry (marco actualizado) [esp.] (hk_qui, p. 32): «Reconocer que igual número de moles de gases ocupan volúmenes iguales a la misma temperatura y presión (Ley de Avogadro).» |

## Candidatos a error de secuencia en la V2 (4)

El prerrequisito llega después que el concepto que lo necesita (grafo de prerrequisitos del repo). Son candidatos: en la revisión manual de 2026-10-08, 2 de 4 resultaron falsos porque el etiquetado no vio el prerrequisito en primaria. Los confirmados están en `internacional/README.md`. Lectura prudente: el concepto con presencia sólida en la V2 y el prerrequisito sin ninguna etiqueta hasta después; la alerta marca los temas cuyo texto ya nombra el prerrequisito.

| Concepto (grado) | Prerrequisito que llega después (grado) | Confianza | Tema SV |
|---|---|---|---|
| Aminoácidos y estructura de las proteínas (10.°) | Polimerización por adición y por condensación (11.°) | media | G10-BIO-U1-1.7 |
| Isomería estructural (10.°) | Hidrocarburos: alcanos, alquenos y alquinos (11.°) | alta | G10-QUI-U2-2.6 |
| Química de los lípidos (10.°) | Esterificación e hidrólisis (11.°) | alta | G10-BIO-U1-1.4 |
| Síntesis química y rutas de reacción (10.°) | Reacciones orgánicas características (11.°) | alta | G10-QUI-U10-10.4 |

## Profundidad: demanda cognitiva en 9.°–11.°

Mismo clasificador por verbos (escala TIMSS) para la V2 y para el núcleo de cada país; los enunciados sin verbo reconocible no entran en el porcentaje. Coincidencia del clasificador con la etiqueta de Gemini: 65% (la diferencia principal: TIMSS pone «explicar» en aplicar).

| Currículo | Enunciados | Recordar | Aplicar | Razonar | Sin verbo |
|---|---|---|---|---|---|
| **El Salvador (V2)** | 229 | 17% | 64% | 19% | 14 |
| EE | 109 | 8% | 53% | 39% | 11 |
| ENG | 119 | 26% | 63% | 11% | 5 |
| KR | 19 | 20% | 47% | 33% | 4 |
| ON | 17 | 33% | 40% | 27% | 2 |
| TW | 44 | 55% | 40% | 5% | 2 |

## Prácticas científicas en 9.°–11.°

La V2 trae una columna procedimental en cada fila y los países separan prácticas de contenidos, así que la proporción de enunciados con práctica no es comparable. Se compara la cobertura del catálogo.

| Currículo | Indagación | Modelación | Argumentación | Naturaleza y contexto | Prácticas distintas |
|---|---|---|---|---|---|
| **El Salvador (V2)** | 66 | 117 | 86 | 18 | 23 |
| EE | 23 | 31 | 37 | 19 | 20 |
| ENG | 21 | 47 | 30 | 6 | 17 |
| KR | 7 | 2 | 3 | 4 | 11 |
| ON | 5 | 4 | 3 | 2 | 11 |
| TW | 2 | 5 | 7 | 4 | 8 |

Prácticas que exige el núcleo de ≥ 5 países y la V2 no nombra en 9.°–11.°: ninguna.

## Conceptos que el vocabulario no tiene (propuestos para triaje)

El vocabulario nació de la malla salvadoreña, así que un contenido que El Salvador no enseña puede no existir en él. Estos nombres los propuso el etiquetado en ≥ 3 países.

| Propuesto | Países | Con núcleo |
|---|---|---|
| Historia de la química | AU, EE, HK, JP, ON, TW | EE, TW |
| Serie de reactividad de los metales | EE, ENG, HK, SG | EE, ENG |
| Química, tecnología y sociedad | EE, JP, KR, TW | EE |
| seguridad en el laboratorio | EE, ENG, HK, KR | EE |
| Conservación de la energía | ENG, SG, TW | TW |
| Desarrollo sostenible | EE, HK, TW | TW |
| Química farmacéutica | HK, ON, TW | TW |
| Serie homóloga | ENG, HK, SG | ENG |
| Calorimetría | AU, HK, ON, SG | — |
| Naturaleza de la ciencia | AU, HK, KR, TW | — |
| Naturaleza de los modelos científicos | AU, HK, KR | — |
| Química y sociedad | HK, JP, ON | — |

