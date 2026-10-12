# Capa pedagógica · puntos para la revisión del equipo de Ciencias

Todo lo que hay en `actividades.json`, `dificultades.json` y `microtemas.json` es **propuesta_pendiente**: lo redactó
el subagente `redactor-actividades` (el 2026-10-11 los tres objetivos de 9.°; el 2026-10-12 sus respuestas abiertas y
los objetivos de 3.°, 5.° y 7.°) y lo validó `gskg lotes validar` (forma, ids y vínculos), pero nadie revisó su
contenido. Las rúbricas de las respuestas abiertas las usa el evaluador automático: revisarlas como si fueran a
calificar dos docentes distintos. Para aprobar un elemento: `"estado": "verificado"` y `"revisado_por"`. Una dificultad
verificada necesita además `fuente`.

Puntos que señalaron los propios redactores:

## G09-CIE-U8-8.2 · difusión y ósmosis
1. Los datos de cambio de masa de la papa en `obj-2` (de +15 % a −14 % según la sacarosa; equilibrio cerca de 9 %)
   son verosímiles pero no salen de un experimento. Contrastarlos con uno de aula.
2. El sondeo 2 de membrana usa una bolsa de celofán con almidón y yodo: confirmar material disponible y que el lugol
   diluido es aceptable en 9.°.
3. La comprobación de membrana con remolacha supone que el docente calienta los trozos (está escrita como
   predicción, no como procedimiento).
4. Hay distractores cruzados entre conceptos (sondeo 1 de ósmosis → dificultad de membrana; práctica de membrana →
   dificultad de ósmosis): confirmar que el diagnóstico debe leerlos así.
5. La práctica y el sondeo 1 de concentración se parecen, y la explicación del microtema adelanta la idea que pide su
   comprobación.
6. La dificultad de ósmosis junta dos ideas (invertir el sentido; atribuir el cambio al soluto): podría dividirse.

7. **Abierta (2026-10-12):** el frijol regado con agua de pozo salada. La rúbrica pide 3 criterios obligatorios (más
   exigente que las otras). Además, «la sal casi no pasa la membrana» simplifica: la raíz sí absorbe algo de sodio.

## G09-CIE-U2-2.4 · procesos termodinámicos
1. Convención de signos ΔU = Q − W (W = trabajo del gas). Si los materiales del MINED usan otra, ajustar la práctica y
   la comprobación de la primera ley (que pide +150 con tolerancia 0).
2. Tres dificultades juntan dos manifestaciones (presión-volumen-temperatura, calor-temperatura, primera ley).
3. Supuestos simplificados: compresión casi adiabática en la bomba de bicicleta; extrapolación de la recta hasta
   −273 °C (un gas real se licúa antes); 273 en lugar de 273,15.
4. Seguridad: globo en botella con agua caliente del chorro (no hirviendo, con el docente); lápiz de punta roma.
5. Algunos distractores no están mapeados a una dificultad (p. ej. la comprobación de procesos).

6. **Abierta (2026-10-12):** la botella con una bolsa floja en agua caliente es isobárica solo si la bolsa queda
   floja (con un globo de hule la presión sube). Usar bolsa delgada y agua caliente sin hervir.

## G09-CIE-U3-3.6 · constante de equilibrio
1. Falta una segunda dificultad: «incluye sólidos o líquidos puros en K» (sus distractores hoy no se mapean).
2. La comprobación pide K = 40 sin unidades, aunque Kc las tiene, y el cálculo se adelanta un poco al tema 3.7.
3. Los datos de N₂O₄/NO₂ de `obj-2` están idealizados (K = 0,010 «a cierta temperatura»).
4. El sondeo con Ca(OH)₂ es un equilibrio de solubilidad: puede adelantarse a lo visto en el aula.
5. La gaseosa y la sal saturada son equilibrios físicos: decidir si se prefieren solo ejemplos químicos.
6. En la práctica de molaridad dos distractores apuntan a la misma dificultad.
7. **Abierta (2026-10-12):** los valores de K de N₂ + O₂ ⇌ 2NO (≈ 4×10⁻³¹ a 25 °C; ≈ 1×10⁻³ a unos 2000 °C) los
   calculó el redactor con datos termodinámicos estándar y no tienen fuente en el repositorio. Confirmar que en 9.° se
   maneja la notación científica con exponentes negativos. «A 25 °C no ocurre» no se penaliza a propósito: en la
   práctica es cierto porque la reacción es lentísima.

## G03-CIE-U1-1.3 · fuerzas de contacto (3.°, 2026-10-12)
1. El concepto principal incluye las fuerzas a distancia, así que la práctica y el microtema usan un imán. En la malla,
   el imán llega en 1.4, después de este objetivo: decidir si se deja.
2. Los datos de `obj-2` (estiramiento de la liga por superficie) son inventados; en clase la tabla puede no coincidir.
3. En la pelota y la carreta, la retroalimentación dice que «la cancha la roza y la frena». En algo que rueda el
   frenado viene sobre todo de la resistencia a la rodadura y del aire.
4. El sondeo 1 de empuje y tirón pide la idea de roce, que es del concepto principal: un fallo puede deberse a la
   fricción y no a la base.
5. Vocabulario: ¿«fricción» o solo «roce» en 3.°? La rúbrica acepta los dos. Confirmar «tirro», «gaveta», «pupitre».
6. Varios distractores apuntan a la misma dificultad, y un error de la rúbrica («se cansa y ya no tiene fuerza») podría
   mapearse a la idea de que la fuerza se gasta.
7. Seguridad: en `obj-1` la liga se jala despacio; cuidar que no se suelte de golpe.
8. Las dos dificultades son ideas infantiles conocidas, pero no traen referencia.

## G05-CIE-U6-6.14 · suelo (5.°, 2026-10-12)
1. El objetivo pide «procesos químicos del suelo» y el concepto principal es «formación, componentes y tipos». El
   redactor tomó como procesos químicos el humus, la oxidación del hierro y la caliza con vinagre: confirmar que es lo
   que pide el MINED en 5.°.
2. `obj-2` pone 0 burbujas con agua en las cuatro muestras; el suelo seco suelta algo de aire al mojarse.
3. Lombrices agrupadas con los descomponedores (en rigor, detritívoros).
4. Meteorización por cambios de temperatura entre el día y la noche (sondeo 2): válida, pero su peso real se discute.
5. Afirmaciones locales por verificar: el color rojizo de muchos suelos salvadoreños por óxidos de hierro, la pómez de
   Ilopango como roca ígnea, coladas del volcán de San Salvador, la caliza formada con conchas (regla general).
6. La malla introduce la meteorización en este mismo tema: fallar sus sondeos es esperable, no una base que falte.
7. «Productores, consumidores y descomponedores» es prerrequisito con confianza media.
8. Un error de la rúbrica abierta («la lluvia se lleva la tierra») no tiene dificultad asociada.

## G07-CIE-U2-2.7 · genes y alelos (7.°, 2026-10-12)
1. `obj-2`, la práctica y la comprobación usan «dominante» (definido en el enunciado): puede corresponder a un tema
   posterior de Mendel.
2. Rasgos de un gen elegidos a propósito: flor y altura de la arveja, grano de maíz amarillo o blanco, tomate rojo o
   amarillo («en estas plantas»). Se evitaron el color de ojos y el lóbulo de la oreja. Confirmar las simplificaciones.
3. «Dos copias de cada gen» no se cumple en los genes de X e Y de los varones ni en organismos haploides.
4. Opciones marcadas incorrectas con algo de verdad (`obj-2` D; práctica de genes D). Si se quiere seguir «dominante =
   más común» como dificultad aparte, hace falta otra ranura.
5. Cifras aproximadas: unos 2 m de ADN por célula y un núcleo de unas 6 milésimas de milímetro. Los datos de Mendel
   (705 y 224) son los de su experimento.
