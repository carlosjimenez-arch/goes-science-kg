# Propuesta de Biología, 10.° y 11.° (borrador)

Versión `propuesta-v1`, estado **borrador** hasta la revisión del equipo de Ciencias del MINED.
Detalle de cada acción, con su evidencia, en `propuesta_G10-G11.json`.

## En resumen
Proponemos 20 acciones: 8 fusiones, 8 temas nuevos, 2 movimientos (3 temas) y 2 reformulaciones (`revisar`).
El total del ciclo se mantiene en **162 temas** y no se quita ninguno. El pivote es **ACARA Senior Secondary Biology**
(unidades 1–2 ≈ 10.°, 3–4 ≈ 11.°). El cambio central es que **10.° recupera la célula como sistema de intercambio**:
membrana, transporte, tipos de célula y tejidos de intercambio. Hoy, esos contenidos solo se ven en 6.°.

## Qué cambia y por qué

**1. Una unidad nueva en 10.°: la célula, sus membranas y el intercambio (acciones 1 a 8).** Se ubica entre
*Biomoléculas* y *Biología celular*, con numeración provisional 9:
- 9.1 Procariotas y eucariotas, animales y vegetales, y sus organelos (se trae G11-3.3; ACSBL048–049).
- 9.2 Membrana celular como límite regulador (nuevo; ACSBL045).
- 9.3 Difusión, ósmosis, relación superficie-volumen y gradientes (nuevo; ACSBL046–047).
- 9.4 Tejidos y organización jerárquica con tinciones (se trae G11-3.2; ACSBL054–055).
- 9.5 Alvéolos, vellosidades, nefronas y estomas como superficies de intercambio (nuevo; ACSBL056, 057 y 059).

Además, el tema 2.6 se reformula para trabajar el transporte activo y la endocitosis. Los temas 3.2 y 3.3 de 11.°
eran biología celular dentro de la unidad agroindustrial. Al llevarlos a 10.°, quedan donde ACARA los ubica.

**2. Salud e inmunidad: lo que falta del marco (acciones 10 y 12).**
- **Inmunidad innata** (inflamación, fagocitos, defensinas, complemento) en 10.°, después de 3.10 (ACSBL119 y 121).
- **Transmisión y propagación de enfermedades** a escala regional y global en 11.°, al cerrar la unidad de microbios
  y virus (ACSBL124; refuerza 116 y 118).

**3. Ecología: diversidad de ecosistemas y especies clave en 11.° (acciones 17 y 19).**
- Al inicio de *Ecología y ambiente*: descripción y clasificación de ecosistemas salvadoreños por sus especies,
  sus interacciones y sus factores abióticos (ACSBL019 y 021).
- En *Dinámica de poblaciones*, después del modelo depredador-presa: especies clave y nicho (ACSBL024 y 023).

**4. Técnicas del ADN, en orden (acciones 14 y 15).** El tema del genoma humano (G10-4.7) supone la PCR y la
electroforesis, que la malla nunca enseña. Un tema nuevo las introduce justo antes. La transgénesis y la edición
genética (G11-4.15) suben a 10.° para completar el bloque (Colombia, 8.°; Uruguay, 6.°).

**5. Cómo se paga: ocho fusiones de temas repetidos o muy específicos.**
- **10.°:** carbohidratos (1.1 + 1.2), lípidos (1.4 + 1.5) y energía biológicamente útil (2.4 + 2.5). Los dos
  primeros pares están FUERA de ACARA (biomoléculas en detalle).
- **11.°, detalle agroindustrial:** propagación vegetativa (3.4 + 3.5), cultivo *in vitro* (3.13 + 3.14) y
  germoplasma y semillas (3.16 + 3.17).
- **11.°, otras:** cultivos y conteo de colonias (2.5 + 2.6) y ciclos biogeoquímicos (1.2 + 1.3), que la unidad 8
  de 10.° ya trabaja a fondo.

Además, sin costo, el tema 6.6 de 11.° (flotación, hoy física sin objetivo del marco) suma la osmorregulación de
los animales acuáticos (ACSBL115, débil).

## Distribución por grado

| Grado | Antes | Después | % del ciclo (después) |
|---|---|---|---|
| 10.° | 70 | 75 | 46,3 % |
| 11.° | 92 | 87 | 53,7 % |
| **Total** | **162** | **162** | |

Los dos grados quedan muy por encima del 15 %. La unidad agroindustrial de 11.° pasa de 18 a 13 temas.

## Cobertura del marco
Los **12 objetivos de contenido de ACARA que hoy no tienen ningún tema pasan a tener al menos uno**: 019, 024, 045,
046, 047, 048, 054, 057, 059, 119, 121 y 124. Además, seis objetivos débiles suman un tema: 021, 023, 056, 115, 116
y 118. Otros dos, 049 y 055, conservan un solo tema, pero ahora reformulado y ubicado en el grado del marco.

## Prerrequisitos que se ordenan
Un script confirma que se conserva el total. También confirma que todos los ids existen y que ningún tema movido o
nuevo queda antes de un prerrequisito de confianza alta. Se corrige la única secuencia invertida del archivo de
candidatos: la **PCR y la electroforesis** ahora van antes de la secuenciación del ADN.

Al ordenar los temas dentro de cada grado, hay que respetar esta secuencia:
- **10.°:**
  - biomoléculas (lípidos) → membrana → difusión y ósmosis → tejidos → superficies de intercambio;
  - ATP (2.1–2.4) y difusión → transporte activo (2.6);
  - sistema inmunitario (3.10) → inmunidad innata → enfermedades (3.12);
  - PCR → genoma humano (4.7) → transgénesis.
- **11.°:**
  - virus (2.13–2.14) → propagación de enfermedades;
  - depredador-presa (7.6) → especies clave.

## Decisiones abiertas para el MINED
1. **Evidencia de países para los temas nuevos.** El archivo de candidatos solo trae países para los tres conceptos
   de `mover_antes`. Los ocho temas nuevos se apoyan en objetivos ACARA sin cobertura. Antes de aprobarlos, falta
   citar al menos un país de referencia con su página, como pide la spec 06.
2. **Repetición con 5.°–8.°.** La propuesta para 5.°–8.° adelanta la membrana, la difusión y la célula animal y
   vegetal. En 10.°, estos temas deben profundizar (modelo de membrana, superficie-volumen, procariotas), no repetir.
3. **Ecología en 11.° frente a ACARA.** ACARA trata ecosistemas y poblaciones en la unidad 1 (≈ 10.°). Alinear
   del todo exigiría intercambiar unidades completas entre grados. No lo proponemos por ser un cambio mayor.
4. **Datos dudosos en `mover_antes`:**
   - «Adaptaciones conductuales» figura sin temas actuales, pero G11-8.5 ya la trabaja, y ACARA la ubica en la
     unidad 4 (≈ 11.°). No se mueve; hay que revisar el etiquetado.
   - La ingeniería genética se movió porque su bloqueo, la síntesis de proteínas, ya se trabaja antes. Aun así,
     la transcripción y la traducción (G11-4.8 y 4.9) siguen en 11.°. ¿Conviene subirlas también?
5. **Temas FUERA del marco.** Hay que decidir los temas FUERA que siguen en la malla con el CSV de
   `revision/2026-10-05_alineacion_acara_bachillerato.csv`. Entre ellos están los de agroindustria y el de agro-químicos (3.18).
   No proponemos quitarlos.
