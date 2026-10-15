# Paquetes de clase: lo que espera una decisión humana

Seis elementos quedaron **sin consenso** en el panel de expertos IA: dos de Química de 10.°, tres actividades de
Física de 10.° y una dificultad sobre aromaticidad de 11.°. **No se marcan como revisados** en sus paquetes
(aparecen en `sin_revision_del_panel`). El generador de clases no debería usarlos hasta que
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

## 3. `TEMA:G10-FIS-U16-16.10`: las tres actividades evalúan espejos esféricos

**Problema** (lo señaló el experto de Física, con la cita de la fila 34 de la V3 anclada): la fila vigente pide
espejos planos (posición y tamaño de la imagen), la altura mínima de un espejo de pared y la profundidad aparente. Las
actividades `obj-1`, `obj-2` y `obj-abierta` son correctas en física, pero evalúan espejos esféricos (espejo de
maquillaje, ecuación del espejo, espejo convexo de seguridad), que no aparecen en ninguna fila vigente de 10.° ni de
11.°. El experimento ya se rehízo para la fila (espejo plano, altura mínima y profundidad aparente) y quedó revisado;
el espejo cóncavo pasó a extensión.

**Causa:** el concepto principal que el grafo asignó al tema es `CON:fisica/espejos-esfericos`.

**Opciones:**
- reasignar el concepto del tema (espejos planos o formación de imágenes por reflexión y refracción) y redactar tres
  actividades nuevas para la fila; o
- aceptar los espejos esféricos como extensión de «imagen formada por reflexión» y dejar las actividades como están.

## 4. `DIF:quimica/hidrocarburos-aromaticos/3`: regla de Hückel como ampliación

El experto consideró correcta la distinción entre sistemas aromáticos, antiaromáticos y no aromáticos, pero advirtió
que la regla de Hückel excede el indicador de reconocimiento de aromáticos. El psicopedagogo dejó confianza baja
por ese alcance curricular. La dificultad sigue sin revisión completa; hace falta decidir si se conserva como
ampliación o se reemplaza por una idea previa que mida el indicador. No se registra una confirmación humana ni se
aplica una decisión a partir de esta nota.
