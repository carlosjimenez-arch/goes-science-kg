# Paquetes de clase: lo que espera una decisión humana

Dos elementos de 10.° Química (4.8) quedaron **sin consenso** en el panel de expertos IA y **no se marcan como
revisados** en su paquete (aparecen en `sin_revision_del_panel`). El generador de clases no debería usarlos hasta que
una persona del equipo de Ciencias acepte o rechace la corrección propuesta. Son propuestas del panel, no
confirmaciones del MINED.

## 1. `ACT:G10-QUI-U4-4.8/obj-2` (halógenos que se desplazan)

**Problema** (lo señaló el psicopedagogo y lo confirmó el experto de Química):
- La clave D liga la electronegatividad a «atraer un electrón extra». Eso es afinidad electrónica, no
  electronegatividad, y es la misma confusión que el panel corrigió en la comprobación de propiedades periódicas.
- Solo D trae el orden correcto (Cl > Br > I). Basta con leer bien los datos para acertar, sin entender el porqué.

**Propuesta del experto:**
- `opciones.A`: «Cl > Br > I, porque el cloro tiene la energía de ionización más baja del grupo y cede sus electrones
  con más facilidad»
- `opciones.D` (clave): «Cl > Br > I: al bajar en el grupo, el electrón que ganan queda más lejos del núcleo y más
  apantallado, y lo atraen menos»
- `distractores`: A y B → `DIF:quimica/propiedades-periodicas/1`; C → `DIF:quimica/propiedades-periodicas/2`
- `retroalimentacion`: «Un halógeno más reactivo saca al menos reactivo de su sal: el cloro desplazó al bromo y al
  yodo, y el bromo solo al yodo; el agua de bromo con cloruro solo conservó su color. Los halógenos reaccionan ganando
  un electrón. Al bajar en el grupo, ese electrón queda más lejos del núcleo y más apantallado, así que lo atraen con
  menos fuerza y reaccionan menos. Por la misma causa baja la electronegatividad, que mide cuánto atrae un átomo los
  electrones de un enlace.»

**Costo:** se pierde el distractor que leía mal los datos (Br > Cl > I).

## 2. `MT:quimica/distribucion-electronica-por-niveles/G10` (microtema)

**Problema:** «los electrones de valencia indican el grupo» choca con la numeración 1–18 que usan las actividades (el
cloro es del grupo 17 y tiene 7). El agregado del psicopedagogo («del 13 al 18, su última cifra») es correcto pero
críptico, no menciona los grupos 1 y 2 ni la excepción del helio.

**Propuesta del experto para `explicacion`** (100 palabras): «En el modelo de capas caben 2 electrones en la primera
y 8 en la segunda. Hasta el calcio, la tercera llega a 8 y los siguientes pasan a la cuarta (4s); del escandio al
zinc, la tercera completa 18 (3d). La capa externa es la de valencia. El número de capas da el período; los
electrones de valencia, el grupo: su número en los grupos 1 y 2, y su última cifra del 13 al 18 (salvo el helio). Al
bajar en un grupo se suma una capa sin cambiar el número de electrones externos: por eso reaccionan parecido.»

## Cómo aplicar la decisión
Quien decida registra la versión aceptada en `data/interim/revisiones/` con `revisado_por` y se rehace el paquete con
`uv run gskg tutor paquete "G10-QUI-U13-13.8=G10-QUI-U4-4.8"`.
