# Cambios TIMSS Ciencias 2023 → 2027 (4.° y 8.°)

Fuentes: `externos/timss/TIMSS2023_Marco_Ciencias.pdf` (cap. 2) y `externos/timss/TIMSS2027_Marcos_Evaluacion.pdf` (cap. 2).
Las páginas son las **impresas** en cada marco («p. 23 / p. 26» = 2023 / 2027).
El detalle objetivo por objetivo está en `equivalencias_timss_2023_2027.csv`, generado por `scripts/build_equivalencias_timss.py`.

## 1. Lo que no cambia
- Dominios de contenido y metas (2023 p. 21–22 y 29 / 2027 p. 23): 4.° 45/35/20 y 8.° 35/20/25/20. En 4.°, «Life Science» pasa a llamarse «Biology».
- Metas cognitivas de 8.°: 35/35/30.
- Número de objetivos en 4.°: 32 en las dos versiones, pero no son los mismos 32 (ver §3).

## 2. Cambios generales (2027 p. 21 y 23–25)
| Cambio | Página 2027 |
|---|---|
| Metas cognitivas de 4.°: de 40/40/20 a **35/40/25** (menos Conocer, más Razonar) | p. 24 |
| **Subescala de conocimiento ambiental** (~25 % de los ítems), con objetivos de Biología y Tierra marcados con asterisco (24 de 80 objetivos) | p. 21, 23, 45–46 |
| **Áreas de Investigaciones** en cada dominio: 7 objetivos nuevos | p. 26–45 |
| Las prácticas científicas se incorporan dentro de los dominios cognitivos (Relacionar, Usar modelos, Interpretar, Explicar…) | p. 24–25, 47–48 |
| Temas de 4.° y 8.° alineados para mostrar la progresión entre grados (mismas áreas en Ciencias físicas/Física y Tierra) | p. 21 |

## 3. Áreas nuevas, fusionadas, divididas y renombradas

### 4.° grado
| Dominio | Área 2023 | Área 2027 | Cambio | Pág. 2023 / 2027 |
|---|---|---|---|---|
| Biología | Características y procesos vitales | B1 · mismo nombre | Recibe «respuestas a cambios externos» y «las plantas fabrican su alimento» | 23–24 / 26–27 |
| Biología | Organismos, ambiente y sus interacciones | B3 · Diversidad y adaptación | **Se reduce y renombra**: el impacto humano pasa a Ecosistemas y las respuestas, al área I | 23–24 / 27 |
| Biología | Ecosistemas | B4 · Ecosistemas | **Recibe** el impacto humano (B4.3); competencia y cadenas se reúnen en B4.2 | 24 / 28 |
| Biología | — | **B6 · Investigaciones biológicas** | **Nueva** | — / 28 |
| Ciencias físicas | Clasificación y propiedades de la materia y sus cambios | P1 · Propiedades y cambios de la materia | Pierde los imanes; 5 objetivos pasan a 3 | 25–26 / 29–30 |
| Ciencias físicas | Formas de energía y transferencia | P2 · Energía y transferencia de energía | **Se divide en tres**: P2 (energía), P3 (luz y sonido) y P4 (electricidad) | 26 / 30 |
| Ciencias físicas | — | **P3 · Luz y sonido** | **Nueva como área**; el contenido ya existía dentro de Energía (T4-F2.2) | 26 / 30 |
| Ciencias físicas | — | **P4 · Electricidad y magnetismo** | **Nueva como área**: une electricidad (de Energía) e imanes (de Materia) | 26 / 30 |
| Ciencias físicas | Fuerzas y movimiento | P5 · Movimiento y fuerzas | Renombrada; agrega la resistencia del aire | 27 / 31 |
| Ciencias físicas | — | **P6 · Investigaciones en ciencias físicas** | **Nueva** | — / 31 |
| Tierra | Características físicas, recursos e historia | E1 · Rasgos, procesos e historia | **Se divide**: los recursos salen a un área propia (E3) | 27–28 / 32 |
| Tierra | Tiempo atmosférico y clima | **E2 · La atmósfera terrestre** | **Renombrada**; 3 objetivos se reúnen en 1. Se elimina aplicar cambios de estado al tiempo atmosférico | 28 / 32 |
| Tierra | — | **E3 · Recursos, uso y conservación** | **Nueva como área**; recibe también las fuentes de energía (antes en Ciencias físicas) | 27 / 32 |
| Tierra | La Tierra en el sistema solar | E4 · mismo nombre | En 4.° ya no se explican las estaciones por la inclinación del eje | 28 / 32 |
| Tierra | — | **E5 · Investigaciones en ciencias de la Tierra** | **Nueva** | — / 33 |

### 8.° grado
| Dominio | Área 2023 | Área 2027 | Cambio | Pág. 2023 / 2027 |
|---|---|---|---|---|
| Biología | Características y procesos vitales | B1 · mismo nombre | **Recibe** fotosíntesis y respiración celular (ahora ambientales) | 30–31 / 34 |
| Biología | Células y sus funciones | B2 · mismo nombre | Pierde fotosíntesis y respiración | 30–31 / 34 |
| Biología | Ciclos de vida, reproducción y herencia | B3 · mismo nombre | **Se elimina** «ciclos de vida y patrones de desarrollo» | 31 / 35 |
| Biología | Ecosistemas | B5 · Ecosistemas | De 5 a 6 objetivos: **nuevo** B5.1 (ecosistemas naturales, rurales y urbanos); redes tróficas pasan a «Relaciones» | 31–32 / 35–36 |
| Biología | — | **B7 · Investigaciones biológicas** | **Nueva** | — / 37 |
| Química | Cambio químico | C3 · Reacciones químicas | Renombrada; el enlace químico pasa a C1 | 34–35 / 39 |
| Química | Propiedades de la materia | C2 · mismo nombre | Dos objetivos de propiedades se fusionan en C2.1 | 34 / 38 |
| Química | — | **C4 · Investigaciones químicas** | **Nueva** | — / 39 |
| Física | (5 áreas) | P1–P5 · mismos nombres | Sin cambios de área; la temperatura constante en el cambio de fase pasa de P2 a P1 | 36–38 / 40–42 |
| Física | — | **P6 · Investigaciones en física** | **Nueva** | — / 42 |
| Tierra | Estructura y rasgos físicos + Procesos, ciclos e historia | **E1 · Rasgos, procesos e historia** | **Fusión** de la parte geológica de dos áreas 2023 | 38–39 / 43 |
| Tierra | (atmósfera en Estructura; ciclo del agua y clima en Procesos) | **E2 · La atmósfera terrestre** | **Nueva como área**: reúne composición, ciclo del agua, tiempo/clima y un objetivo **propio de cambio climático** (E2.4) | 38–39 / 44 |
| Tierra | Recursos, uso y conservación | E3 · mismo nombre | Reorganizada: fuentes de energía (E3.1) y gestión de recursos (E3.2); el agua dulce pasa a E1.1 | 39 / 44 |
| Tierra | La Tierra en el sistema solar y el universo | E4 · La Tierra en el sistema solar | Se quitan las estrellas y constelaciones; agrega efectos de la rotación | 40 / 45 |
| Tierra | — | **E5 · Investigaciones en ciencias de la Tierra** | **Nueva** | — / 45 |

## 4. Objetivos 2027 SIN equivalente en 2023: aquí puede haber vacíos nuevos en la malla
| Código 2027 | Objetivo | Por qué importa | Pág. 2027 |
|---|---|---|---|
| T4_27-B6.1 | Rasgos y equipo de una investigación biológica | Prueba justa, observación vs inferencia, lupa | 28 |
| T4_27-P6.1 | Rasgos y uso de equipo en ciencias físicas | Preguntas comprobables, repetir mediciones, balanza, cronómetro | 31 |
| T4_27-E5.1 | Equipo en investigaciones de la Tierra | Termómetro, brújula, pluviómetro | 33 |
| T8_27-B5.1 | Ecosistemas naturales, urbanos y rurales | Contenido disciplinar nuevo (ambiental) | 35 |
| T8_27-B7.1 | Rasgos y equipo de una investigación biológica | Variables control/tratamiento, microscopio | 37 |
| T8_27-C4.1 | Rasgos y equipo de una investigación química | Una variable a la vez, seguridad en el laboratorio | 39 |
| T8_27-P6.1 | Rasgos y equipo de una investigación en física | Repetir mediciones, amperímetro, dinamómetro | 42 |
| T8_27-E5.1 | Equipo en investigaciones de la Tierra | Telescopio, brújula | 45 |

**Áreas nuevas cuyo contenido SÍ existía en 2023.** No son vacíos nuevos en sí mismas, pero conviene revisarlas:
- **Luz y sonido, 4.°** (T4_27-P3.1, P3.2): antes era un solo objetivo dentro de Energía (T4-F2.2) y ahora son dos. Si la malla trabaja solo luz o solo sonido, el otro queda descubierto.
- **Atmósfera, 8.°** (T8_27-E2.1–E2.4): reúne contenido que antes estaba repartido. Lo nuevo de verdad es E2.4 **cambio climático con sus causas** (2023 solo pedía evidencias) y en E2.2 la formación de nubes por enfriamiento del aire.
- **Atmósfera, 4.°** (T4_27-E2.1): es el área 2023 «Tiempo atmosférico y clima» con otro nombre.

Otros contenidos nuevos dentro de objetivos con equivalente: identificar diagramas de circuitos (T4_27-P4.1), salud mental (T4_27-B5.2), circuitos en serie vs en paralelo (T8_27-P4.1), cómo actúan las vacunas (T8_27-B6.1) y efectos de la rotación en 8.° (T8_27-E4.1).

## 5. Contenido 2023 que desaparece del marco 2027
| Código 2023 | Contenido | Nota | Pág. 2023 |
|---|---|---|---|
| T4-T2.1 | Aplicar cambios de estado del agua a fenómenos del tiempo | Lo más cercano en 2027 es T4_27-P1.1 | 28 |
| T8-B3.1 | Ciclos de vida y patrones de desarrollo (8.°) | Solo queda en 4.° (T4_27-B2.1) | 31 |
| (parte de T4-V3.2) | Respuesta de las plantas a las condiciones del ambiente | Se elimina en 4.° | 24 |
| (parte de T4-T3.2) | Estaciones por la inclinación del eje (4.°) | Pasa a 8.° (T8_27-E4.1) | 28 |
| (parte de T8-F5.2) | Gravedad en distintos planetas | Se elimina | 37 |
| (parte de T8-T4.1/T4.2) | Constelaciones y otras estrellas | Se elimina | 40 |
| (parte de T8-T1.2) | Relación de los gases atmosféricos con procesos vitales | Se elimina | 38 |

## 6. Resumen de equivalencias (por objetivo 2023)
| Tipo | 4.° | 8.° | Significado para el paso 3 |
|---|---|---|---|
| igual | 19 | 31 | Traducción directa: se conservan confianza y justificación |
| fusionado | 7 | 9 | Varios 2023 → un solo 2027 (el destino es único) |
| dividido | 5 | 5 | Un 2023 → varios 2027: hay que elegir destino |
| sin_equivalente | 1 | 1 | Hay que reclasificar |
| nuevo_2027 (objetivos 2027) | 3 | 5 | Ningún tema v1 llega aquí por traducción |
