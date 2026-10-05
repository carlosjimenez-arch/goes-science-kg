# Brechas · Ciencias de la Tierra y del Espacio

> Generado por `gskg brechas`. No editar a mano. Método: `src/goes_science_kg/brechas.py` y specs 06 y 09.

## 1. Cobertura de los marcos por ciclo

| Marco | Ciclo | Objetivos | Cubiertos | Débiles (1 tema) | Sin cobertura |
|---|---|---|---|---|---|
| T4_27 | 2.°–4.° | 7 | 7 | 1 | 0 |
| T8_27 | 5.°–8.° | 11 | 9 | 0 | 2 |
| PISA25 | 7.°–9.° | 8 | 7 | 0 | 1 |

**T8_27 sin cobertura en 5.°–8.°:** T8_27-E4.1 Fenómenos observables por los movimientos de la Tierra y la Luna; T8_27-E5.1 Equipo usado en investigaciones de ciencias de la Tierra

**PISA25 sin cobertura en 7.°–9.°:** PISA-T8 Origen del universo y del sistema solar (evolución estelar, formación de planetas, Big Bang)

## 2. ¿Cuándo llega El Salvador? Oportunidad por concepto

Se compara el primer grado de cada concepto en El Salvador con la mediana de los países de referencia del grafo (grado equivalente por edad de ingreso; ver `config/referentes.yaml`) (conceptos que trabajan al menos dos países: 42 de 79). Oportunidad = grado SV − mediana; positivo = El Salvador llega tarde.

### Llega 2 o más grados tarde

La columna «Alto desempeño» es la mediana solo de los países entre los 10 primeros de TIMSS 2023 Ciencias (con datos en el grafo: AU, ENG, SG; ver `config/referentes.yaml`).

| Concepto | SV | Mediana países | Alto desempeño | Países | Oportunidad |
|---|---|---|---|---|---|
| Tiempo atmosférico y sus variables | 7.° | 2 | 2 | AU 2, CO 8.5, ENG 2 | +5 |
| Corrientes oceánicas superficiales y profundas | 9.° | 4.75 | — | CO 4.5, UY 5.0 | +4.25 |
| Ciclo del agua | 7.° | 3 | 3 | AU 3.0, ENG 2, SG 5.0, UY 3.0 | +4 |
| Minerales y sus propiedades | 8.° | 4 | 4 | AU 2, ENG 6.0 | +4 |
| Ciclo del carbono en los sistemas terrestres | 10.° | 6.5 | 7 | AU 8.0, CO 6.5, ENG 6.0 | +3.5 |
| Fósiles y su formación | 5.° | 2 | 2 | CO 2, ENG 2, UY 6.0 | +3 |
| Suelo: formación, componentes y tipos | 5.° | 2.5 | 2 | AU 2, CO 6.5, ENG 2, UY 3.0 | +2.5 |
| Calidad del aire y contaminación atmosférica | 7.° | 5 | 5 | CO 4.5, SG 5.0, UY 5.0 | +2 |

### Llega 2 o más grados antes

| Concepto | SV | Mediana países | Oportunidad |
|---|---|---|---|
| Conservación de recursos, residuos y sostenibilidad | 2.° | 6.5 | -4.5 |
| Fuentes de energía renovables y no renovables | 2.° | 6.25 | -4.25 |
| Sismos y fallas geológicas | 2.° | 6.25 | -4.25 |
| Ciclo de las rocas | 3.° | 6.5 | -3.5 |
| Recursos naturales renovables y no renovables | 2.° | 5.25 | -3.25 |
| Inclinación del eje terrestre y estaciones astronómicas | 2.° | 4.75 | -2.75 |
| Capas internas de la Tierra | 3.° | 5.5 | -2.5 |
| Exploración espacial | 4.° | 6.25 | -2.25 |
| Calentamiento global | 7.° | 9 | -2 |
| Cambio climático: causas y efectos | 7.° | 9 | -2 |
| El Sol como estrella | 4.° | 6 | -2 |
| La atmósfera y su composición | 3.° | 5 | -2 |
| Tiempo geológico y datación | 5.° | 7 | -2 |

### Lo trabajan los países y El Salvador nunca

- Sistemas terrestres y sus interacciones (AU 9.0, CO 4.5)

## 3. Secuencia: prerrequisitos que llegan después del concepto que los necesita

| Concepto | Grado | Necesita | Grado del prerrequisito | Confianza |
|---|---|---|---|---|
| Ciclo del carbono en los sistemas terrestres | 10.° | Sistemas terrestres y sus interacciones | nunca | alta |
| Energía geotérmica | 2.° | Convección del manto y energía interna de la Tierra | nunca | alta |
| Formación del sistema solar | 5.° | Gravedad y órbitas | nunca | alta |
| Mareas | 4.° | Gravedad y órbitas | nunca | alta |
| Tectónica de placas | 5.° | Convección del manto y energía interna de la Tierra | nunca | alta |
| Ciclo de vida de las estrellas | 5.° | Fisión y fusión nuclear | 11.° | alta |
| Recursos minerales y minería | 3.° | Minerales y sus propiedades | 8.° | alta |
| Aguas subterráneas y acuíferos | 3.° | Ciclo del agua | 7.° | alta |
| Cuencas hidrográficas y aguas superficiales | 3.° | Ciclo del agua | 7.° | alta |
| Ciclones tropicales y tormentas | 4.° | Tiempo atmosférico y sus variables | 7.° | alta |
| Clima: diferencia con el tiempo, tipos y factores | 4.° | Tiempo atmosférico y sus variables | 7.° | alta |
| Ondas sísmicas, magnitud e intensidad | 5.° | Ondas mecánicas transversales y longitudinales | 8.° | alta |
| Ciclo de las rocas | 3.° | Erosión, transporte y sedimentación | 5.° | alta |
| Acidificación del océano | 9.° | Ciclo del carbono en los sistemas terrestres | 10.° | alta |
| Campo magnético terrestre | 5.° | Imanes y polos magnéticos | 6.° | alta |
| Uso del suelo y su degradación | 4.° | Erosión, transporte y sedimentación | 5.° | alta |
| Uso del suelo y su degradación | 4.° | Suelo: formación, componentes y tipos | 5.° | alta |
| Calidad y tratamiento del agua | 3.° | Abastecimiento y conservación del agua dulce | nunca | media |
| Ciclo de vida de las estrellas | 5.° | Gravedad y órbitas | nunca | media |
| Exploración espacial | 4.° | Gravedad y órbitas | nunca | media |
| Origen del universo: el Big Bang | 5.° | Efecto Doppler | 11.° | media |
| Tiempo geológico y datación | 5.° | Desintegración radiactiva | 11.° | media |
| Ciclones tropicales y tormentas | 4.° | Calentamiento desigual de la Tierra y circulación atmosférica | 9.° | media |
| Clima: diferencia con el tiempo, tipos y factores | 4.° | Calentamiento desigual de la Tierra y circulación atmosférica | 9.° | media |
| Patrones estacionales: época seca y lluviosa | 2.° | Tiempo atmosférico y sus variables | 7.° | media |
| Tipos de rocas: ígneas, sedimentarias y metamórficas | 3.° | Minerales y sus propiedades | 8.° | media |
| Cambio climático: causas y efectos | 7.° | Ciclo del carbono en los sistemas terrestres | 10.° | media |
| Capas de la atmósfera y variación con la altitud | 3.° | Presión hidrostática y atmosférica | 6.° | media |
| Sismos y fallas geológicas | 2.° | Límites de placas: convergentes, divergentes y transformantes | 5.° | media |
| Aguas subterráneas y acuíferos | 3.° | Suelo: formación, componentes y tipos | 5.° | media |
| Amenazas naturales geológicas e hidrometeorológicas | 2.° | Ciclones tropicales y tormentas | 4.° | media |
| Ciclo de las rocas | 3.° | Origen del magma y vulcanismo | 5.° | media |
| Ciclones tropicales y tormentas | 4.° | Presión hidrostática y atmosférica | 6.° | media |
| Volcanes: estructura, tipos y productos | 3.° | Origen del magma y vulcanismo | 5.° | media |


## Cómo usar esto

- **Sección 1** dice qué objetivos internacionales no tienen ningún tema o tienen uno solo en su ciclo.
- **Sección 2** dice cuándo enseña El Salvador cada idea frente a otros países (por concepto, no por objetivo).
- **Sección 3** son errores de secuencia candidatos a «mover» en la propuesta (spec 06). Las de confianza alta van primero; antes de mover un tema conviene revisar el caso con el equipo de Ciencias.
