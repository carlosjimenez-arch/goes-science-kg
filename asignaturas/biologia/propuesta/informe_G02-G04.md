# Propuesta de Biología, 2.° a 4.° (borrador)

Versión `propuesta-v1`, estado **borrador** hasta la revisión del equipo de Ciencias del MINED.
Detalle de cada acción, con su evidencia, en `propuesta_G02-G04.json`.

## En resumen
Proponemos 10 acciones: 2 temas nuevos, 2 fusiones, 1 movimiento y 5 reformulaciones (`revisar`).
El total del ciclo se mantiene en **98 temas** y no se quita ninguno.

El ciclo necesita pocos cambios. La malla de 2.° a 4.° ya cubre casi todos los objetivos de TIMSS 4.° grado, y
Biología ya pesa más de lo esperado (52 % de los temas de Ciencias del ciclo; TIMSS indica 45 %). Por eso
no se agregan temas: los dos nuevos se pagan con dos fusiones. El cambio central es cubrir el único objetivo
sin ningún tema, **T4_27-B2.2 Herencia y estrategias de reproducción**.

## Qué cambia y por qué

**1. Se cubre la herencia y la reproducción (acciones 1 a 4).**
- *3.°, unidad Los animales:* tema nuevo sobre las estrategias de reproducción de animales y plantas (huevos,
  crías vivas, semillas, esquejes, cuidado de las crías). Va después del ciclo de vida (5.2). Así, la reproducción
  sexual y asexual llega antes de la fecundación en plantas con flor (SG 5, UY 3), que la propuesta de 5.° a 8.°
  ubica en 5.°.
- *4.°, unidad Cuerpo humano:* tema nuevo sobre los rasgos que los descendientes heredan de sus progenitores.
  Hoy la herencia aparece en 10.°; Colombia la trabaja en 2.° y Singapur en 5.°. No tiene prerrequisitos.
- Se pagan con dos fusiones de temas que repiten contenido:
  - En 3.°, las dos descripciones de vertebrados (5.12 y 5.13) se unen en un tema sobre estructura y función.
  - En 4.°, las dos prácticas de medidas antropométricas (2.9 y 2.10) se unen en una sola.

**2. Las vacunas pasan después de los microorganismos (acción 5).** En 2.° se habla de vacunas antes de saber
qué es un patógeno. El tema 6.10 sube a la unidad de microorganismos de 3.°, después de infección, patógenos y
desinfectantes. Ahí se nombran, de forma sencilla, las defensas del cuerpo.

**3. Se ordenan secuencias sin gastar presupuesto (acciones 3 y 6 a 9).**
- La fusión de vertebrados (acción 3) introduce en 3.° la relación entre estructura del cuerpo y función.
  Es el prerrequisito que le falta al sistema locomotor de 4.°.
- 3.6 de 4.° hace explícita la competencia por recursos y las relaciones entre individuos de la misma especie
  (CO 3, UY 6), antes del nicho ecológico (3.8). El nicho se limita al «papel de la especie»; la exclusión competitiva
  sigue en 7.°.
- 3.3 de 4.° se precisa como organización *ecológica* (organismo → ecosistema), que no requiere la célula.
- 6.7 de 3.° trata la degradación como acción de hongos y bacterias. El papel de los descomponedores en la cadena
  se nombra en 4.° (3.7), después de la cadena alimentaria.
- 5.3 de 3.° (taxismos) se amplía a conductas que ayudan a sobrevivir (migración, hibernación). Hoy las
  adaptaciones conductuales aparecen en 11.° (CO 2, SG 6).

**4. Temas señalados por si se quiere aligerar Biología (acción 10).** Hay grupos de temas que repiten un mismo
concepto con un detalle alto para la edad:
- seis temas de 3.° sobre grupos de invertebrados (5.6 a 5.11);
- tres sobre tropismos y nastias (4.7 a 4.9);
- dos sobre requerimientos nutricionales en 4.° (2.4 y 2.7).

No se tocan ahora. Quedan como opción si el MINED decide pasar horas a otras disciplinas.

## Distribución por grado

| Grado | Antes | Después | % del ciclo (después) |
|---|---|---|---|
| 2.° | 27 | 26 | 26,5 % |
| 3.° | 32 | 33 | 33,7 % |
| 4.° | 39 | 39 | 39,8 % |
| **Total** | **98** | **98** | |

Todos los grados quedan por encima del 15 %. 4.° sigue siendo el grado más cargado.

## Prerrequisitos que se ordenan
Lo comprobó un script de validación.
- **Quedan en orden:**
  - estructuras del cuerpo animal (3.°) → sistema locomotor (4.°)
  - competencia → nicho ecológico (4.°, 3.6 antes que 3.8)
  - competencia y factores bióticos → simbiosis (4.°)
  - cadena alimentaria → descomponedores (4.°)
  - reproducción sexual y asexual (3.°) → fecundación en plantas con flor (5.°, propuesta 5.°–8.°)
- **Quedan pendientes dos secuencias.** Las dos dependen de cómo están etiquetados los conceptos (decisiones 2 y 3):
  - vacunas (3.°) → sistema inmunitario (10.°)
  - niveles de organización (4.°) → la célula (6.°; 5.° en la propuesta 5.°–8.°)
- **Fuera del alcance del ciclo:**
  - La digestión química necesita las enzimas, que llegan en 8.°.
  - El transporte en plantas necesita difusión y tejidos vegetales.
  - La propuesta de 5.° a 8.° ya adelanta a 5.° el transporte, la célula, la simbiosis y la fecundación en plantas.

## Decisiones abiertas para el MINED
1. **Peso de Biología en 2.° a 4.°:** está siete puntos por encima de TIMSS. ¿Se consolidan los temas de la acción 10
   para pasar horas a Física, Química o Ciencias de la Tierra?
2. **Vacunas y sistema inmunitario:** el grafo exige el sistema inmunitario (10.°) antes de las vacunas. En 3.°
   proponemos solo la idea de «defensas del cuerpo». Hay dos opciones:
   - aceptar este nivel introductorio y etiquetar el tema como prevención;
   - introducir las defensas del cuerpo como concepto propio en primaria.
3. **Datos que conviene verificar:**
   - El archivo de candidatos ubica la *competencia por recursos* y la *simbiosis* en 7.°, pero el tema G04-3.6 ya
     las trabaja en 4.°.
   - G04-3.3 (organización ecológica) está etiquetado como «niveles de organización de los seres vivos», lo que
     crea una dependencia de la célula que el tema no tiene.
   - «Estructuras del cuerpo animal y su función» no tiene grado en El Salvador.
4. **La célula en 4.°:** Colombia y Uruguay la enseñan en 4.°. La propuesta de 5.° a 8.° la ubica en 5.°.
   ¿Se mantiene en 5.° para no recargar 4.°?
5. **Herencia en Bachillerato:** al introducirse en 4.°, conviene ajustar la profundidad de los temas de herencia
   de 10.° para que no se repitan.
