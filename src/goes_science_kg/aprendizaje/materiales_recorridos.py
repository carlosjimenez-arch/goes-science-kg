"""Author complete local successor materials for the five historical tutoring journeys."""

from __future__ import annotations

from copy import deepcopy


def _rubrica(criterio, logrado, proceso, apoyo):
    return {"criterio": criterio, "logrado": logrado, "en_proceso": proceso, "requiere_apoyo": apoyo}


def _solucion(respuesta, explicacion, rubrica, calculos=()):
    return {"respuesta": respuesta, "explicacion": explicacion, "rubrica": rubrica, "calculos": list(calculos)}


def _fuente(id_, titulo, url, alcance):
    return {"id": id_, "titulo": titulo, "url": url, "alcance": alcance}


def _base(id_, titulo, grado, objetivo_historico, objetivos, fundamento, fuentes):
    return {
        "version": "recorrido-ciencias-2",
        "id": id_,
        "titulo": titulo,
        "grado": grado,
        "origen": {
            "recorrido_historico": id_,
            "objetivo_historico": objetivo_historico,
            "alcance": (
                "Sucesor local del recorrido demostrativo. La referencia histórica no establece equivalencia "
                "automática con un objetivo V4 ni acredita una práctica instrumental realizada."
            ),
        },
        "objetivos": objetivos,
        "fundamento": fundamento,
        "fuentes": fuentes,
        "carga_cognitiva": {
            "no_medida": True,
            "decisiones": [
                "Recoger el diagnóstico antes de entregar el ejemplo resuelto; registrar la respuesta literal.",
                "Presentar primero el caso resuelto, después la práctica con pistas y finalmente una tarea nueva.",
                "Mantener datos, unidades y pregunta juntos; permitir pausas y lectura literal sin dar la solución.",
                "El número de palabras o minutos es una decisión de diseño y no una medida de carga cognitiva.",
                "Registrar el esfuerzo autoinformado por tarea si se aplica el instrumento, sin atribuirlo a eficacia.",
            ],
        },
    }


TRANSPORTE = _fuente(
    "OPENSTAX:biologia:5.2",
    "OpenStax Biology 2e · Passive Transport",
    "https://openstax.org/books/biology-2e/pages/5-2-passive-transport",
    "Difusión, membrana selectiva y movimiento neto de agua; no aporta los datos simulados de estos ejercicios.",
)
GASES = _fuente(
    "OPENSTAX:fisica:13.3",
    "OpenStax College Physics 2e · The Ideal Gas Law",
    "https://openstax.org/books/college-physics-2e/pages/13-3-the-ideal-gas-law",
    "Relaciones P-V-T para cantidad fija de gas ideal; presión absoluta y temperatura en kelvin.",
)
EQUILIBRIO = _fuente(
    "OPENSTAX:quimica:13.2",
    "OpenStax Chemistry 2e · Equilibrium Constants",
    "https://openstax.org/books/chemistry-2e/pages/13-2-equilibrium-constants",
    "Expresión de constantes, exponentes, fases puras e interpretación; los números de las tareas son simulados.",
)
CAMBIO_EQUILIBRIO = _fuente(
    "OPENSTAX:quimica:13.3",
    "OpenStax Chemistry 2e · Shifting Equilibria",
    "https://openstax.org/books/chemistry-2e/pages/13-3-shifting-equilibria-le-chateliers-principle",
    "Equilibrio dinámico, cambios de condiciones y distinción entre composición y constante a temperatura fija.",
)


def _r1():
    r = _base(
        "R1",
        "Difusión y ósmosis: del gradiente a una explicación con controles",
        9,
        "TEMA:G09-CIE-U8-8.2",
        [
            "Distinguir difusión de un soluto y ósmosis de agua a través de una membrana selectiva.",
            "Calcular y representar cambio porcentual de masa de tejido vegetal con datos completos y controles.",
            "Distinguir la interpretación de datos simulados de la realización y medición de una práctica real.",
        ],
        [
            "Compara concentraciones usando igual volumen de disolución: una masa mayor del mismo soluto implica "
            "mayor concentración. La cantidad total y la concentración no son la misma magnitud.",
            "En el modelo de difusión, las partículas se mueven en ambos sentidos; el flujo neto del soluto va a "
            "favor de su gradiente si puede atravesar la barrera. No significa que las partículas "
            "se detengan al final.",
            "Para el modelo de ósmosis usado aquí, la membrana deja pasar agua y retiene el soluto; se comparan "
            "temperatura y presión iniciales iguales. El movimiento neto inicial de agua va hacia el lado de mayor "
            "concentración efectiva de soluto no permeante. Otras presiones pueden equilibrar ese efecto.",
            "Cambio porcentual de masa = 100 × (masa final − masa inicial) / masa inicial. El signo conserva "
            "información. Los datos siguientes son simulados; no son mediciones de una escuela ni de un país.",
            "Buscar la concentración exterior que daría cambio neto de masa cero es una estimación "
            "operativa: requiere más concentraciones, repeticiones y controles. Un cambio de masa cero "
            "no demuestra por sí solo igualdad de concentraciones dentro y fuera del tejido.",
        ],
        [TRANSPORTE],
    )
    r["diagnostico"] = {
        "items": [
            {
                "id": "R1-D1",
                "enunciado": "A contiene 2 g de sacarosa en 100 mL de disolución y B contiene "
                "4 g del mismo soluto en 100 mL. ¿Cuál tiene mayor concentración? En un modelo con una "
                "membrana que deja pasar agua pero retiene la sacarosa, presión inicial igual y temperatura "
                "igual, indica hacia qué lado habrá movimiento neto inicial de agua y justifica.",
            },
            {
                "id": "R1-D2",
                "enunciado": "C contiene 4 g de sacarosa en 200 mL de disolución y D contiene 3 g en "
                "100 mL. ¿Cuál es más concentrada? Explica por qué comparar sólo las masas podría engañar.",
            },
        ],
        "criterio_derivacion": "Si compara sólo cantidad sin volumen, trabajar la primera explicación. Si hace "
        "cruzar la sacarosa, volver a la selectividad de membrana. Una respuesta no permite diagnosticar una "
        "brecha estable ni descartar todas las demás bases; registrar qué razonamiento falta.",
    }
    r["refuerzo"] = {
        "ejemplo_trabajado": {
            "id": "R1-E1",
            "enunciado": "Datos simulados: dos porciones de papa de 10 g se mantienen el mismo "
            "tiempo y temperatura: P en sacarosa 0 % m/v (final 11 g) y Q en 4 % m/v (final 9 g). "
            "% m/v significa gramos de sacarosa por 100 mL de disolución. "
            "En este modelo la sacarosa no atraviesa las membranas y el exterior de Q es más concentrado.",
            "pasos": [
                "P: 100 × (11 − 10)/10 = +10 %. Q: 100 × (9 − 10)/10 = −10 %.",
                "El signo positivo indica ganancia neta de masa; el negativo indica pérdida. El modelo de "
                "ósmosis explica transferencia neta de agua, sin afirmar que la sacarosa atraviesa la membrana.",
                "Mantener lote y tamaño del tejido, tiempo, temperatura, volumen de disolución y método de "
                "secado superficial. P es comparación con agua, no una prueba universal de todo tejido.",
                "Para graficar, dibuja X = concentración (% m/v), Y = cambio de masa (%). Marca (0; +10) "
                "y (4; −10). La línea horizontal Y = 0 representa ausencia de cambio neto de masa.",
                "No se supone una recta exacta entre dos puntos: el cruce con Y = 0 sería una estimación "
                "dependiente de ese supuesto. Hacen falta datos cercanos a cero y repeticiones para contrastarla.",
            ],
        },
        "practica_guiada": {
            "items": [
                {
                    "id": "R1-P1",
                    "enunciado": "Datos simulados de dos porciones del mismo tejido: en sacarosa 0 % m/v, "
                    "masa inicial 12 g y final 12,6 g; en 2 % m/v, masa inicial 12 g y final 10,8 g. "
                    "Calcula ambos cambios y ubica los puntos con concentración en X y cambio de masa en Y. "
                    "Explica el movimiento neto del agua bajo el modelo y nombra dos controles.",
                }
            ],
            "apoyos": [
                "Escribe primero final − inicial y conserva el signo.",
                "Dibuja una flecha de agua a través "
                "de la membrana; comprueba qué sustancia puede cruzarla antes de explicar.",
            ],
        },
        "retirada_apoyos": "Recoger la práctica y el ejemplo antes de entregar la nueva tabla de comprobación. "
        "Se permite leer literalmente las consignas y usar un formato accesible; no indicar la dirección del agua.",
    }
    r["comprobacion_independiente"] = {
        "items": [
            {
                "id": "R1-C1",
                "enunciado": "Nueva tabla simulada de tejido vegetal del mismo lote y "
                "tamaño: sacarosa 0 % m/v → masa inicial 20 g, final 20,5 g; 3 % m/v → inicial 20 g, "
                "final 19 g. Tiempo, temperatura, volumen y secado superficial se mantuvieron iguales. "
                "% m/v significa gramos de sacarosa por 100 mL de disolución. Calcula ambos cambios "
                "porcentuales, dibuja concentración (% m/v) en X y cambio de masa (%) en "
                "Y, ubica los dos puntos y explica el sentido neto del agua en cada caso según el modelo. "
                "Explica para qué sirven los controles e indica por qué dos puntos simulados no prueban "
                "la concentración exterior exacta que daría cambio neto de masa cero.",
            }
        ],
        "sin_ayudas": True,
        "administracion": "Usar esta hoja sin pistas conceptuales ni acceso a soluciones. Recoger tabla, dibujo "
        "y explicación; el docente corrige usando sólo el ítem, la rúbrica y la respuesta nueva.",
        "criterios": [
            "Porcentajes y gráfico con signo y unidades.",
            "Agua, membrana y controles correctamente explicados; límite de los datos declarado.",
        ],
        "si_no_logra": "Separar si falló la aritmética, el gráfico o el modelo de membrana. Reforzar sólo ese "
        "componente y preparar otra tabla reservada; no copiar esta misma como nueva evidencia.",
    }
    rub = _rubrica(
        "Modelo de concentración y membrana",
        "Compara igual volumen, identifica B y explica agua hacia B bajo los supuestos dados.",
        "Identifica B pero omite una condición o la selectividad.",
        "Afirma que el azúcar debe cruzar la membrana o confunde cantidad con concentración.",
    )
    r["soluciones_docente"] = {
        "R1-D1": _solucion(
            "B tiene mayor concentración; habrá flujo neto inicial de agua de A hacia B.",
            "La igualdad de volumen permite comparar las masas del mismo soluto; sólo el agua "
            "atraviesa la membrana en el modelo y se declararon las condiciones de presión.",
            [rub],
        ),
        "R1-D2": _solucion(
            "D es más concentrada: C equivale a 2 g por 100 mL y D a 3 g por 100 mL.",
            "La masa total es mayor en C, pero está repartida en el doble de volumen; comparar cantidades "
            "sin volumen no determina la concentración.",
            [
                _rubrica(
                    "Masa y concentración con volúmenes distintos",
                    "Reduce a igual volumen y elige D con una razón cuantitativa correcta.",
                    "Elige D pero no explicita cómo compara volúmenes.",
                    "Elige C sólo porque contiene más gramos.",
                )
            ],
            [{"expresion": "4/200*100", "resultado": 2, "unidad": "g/100 mL"}],
        ),
        "R1-P1": _solucion(
            "Cambios = +5 % y −10 %. Puntos (0; +5) y (2; −10), con X en % m/v e Y en %. En el primer "
            "caso entra agua netamente y en el segundo sale, según el modelo. Controles: tiempo y temperatura.",
            "100 × (12,6 − 12)/12 = 5 y 100 × (10,8 − 12)/12 = −10. Los signos conservan la diferencia "
            "entre ganancia y pérdida; no prueban entrada de sacarosa ni una concentración exacta de cambio cero.",
            [
                _rubrica(
                    "Cambio de masa y explicación osmótica",
                    "Obtiene +5 % y −10 %, grafica ambos puntos, explica los dos flujos y aporta dos controles.",
                    "Comprende los flujos pero omite un signo, rótulo de gráfico o control.",
                    "Invierte el flujo o no puede relacionar el signo con la pérdida de masa.",
                )
            ],
            [
                {"expresion": "100*(12.6-12)/12", "resultado": 5, "unidad": "%"},
                {"expresion": "100*(10.8-12)/12", "resultado": -10, "unidad": "%"},
            ],
        ),
        "R1-C1": _solucion(
            "Cambios: +2,5 % y −5 %. Puntos (0; 2,5) y (3; −5), con X en % m/v y Y en %. Entrada neta de agua en el "
            "primer caso y salida en el segundo según el modelo; no hay punto medido de cambio cero.",
            "El gráfico conserva ejes y signos. El cambio de masa por sí solo no demuestra su causa: la "
            "explicación osmótica depende del modelo declarado. Dos observaciones simuladas no fijan por sí "
            "solas la curva ni una concentración exacta de cambio cero; se necesitarían otras concentraciones y "
            "repeticiones reales para contrastarlo.",
            [
                _rubrica(
                    "Representación de los datos",
                    "Calcula ambos porcentajes y coloca los dos puntos con ejes y unidades correctos.",
                    "Representa la tendencia, pero omite una unidad o comete un error aritmético.",
                    "Invierte ejes o signos sin poder interpretar la masa.",
                ),
                _rubrica(
                    "Explicación y límites de evidencia",
                    "Explica movimiento neto de agua, el papel de los controles y "
                    "distingue el modelo y los datos simulados de una concentración exacta de cambio cero.",
                    "Explica el agua pero presenta el cruce como exacto sin datos suficientes.",
                    "Atribuye todo a entrada de azúcar o afirma medición real inexistente.",
                ),
            ],
            [
                {"expresion": "100*(20.5-20)/20", "resultado": 2.5, "unidad": "%"},
                {"expresion": "100*(19-20)/20", "resultado": -5, "unidad": "%"},
            ],
        ),
    }
    return r


def _r2():
    r = _base(
        "R2",
        "Gases: condiciones controladas, kelvin y procesos termodinámicos",
        9,
        "TEMA:G09-CIE-U2-2.4",
        [
            "Identificar procesos isotérmicos, isocóricos e isobáricos a partir de variables controladas.",
            "Aplicar relaciones del gas ideal con cantidad fija, presión absoluta y temperatura en kelvin.",
            "Distinguir una predicción del modelo de una medición y describir un experimento seguro.",
        ],
        [
            "Para una cantidad fija de gas ideal, PV/T permanece constante. P es presión absoluta, V volumen y "
            "T temperatura absoluta en kelvin; T(K) = temperatura(°C) + 273,15.",
            "Isotérmico: T constante y PV constante. Isocórico: V constante y P/T constante. Isobárico: P "
            "constante y V/T constante. Identifica primero qué se controla; después elige la relación.",
            "Un termómetro o una jeringa no demuestra automáticamente condiciones ideales. En una exploración "
            "con jeringa sin aguja, hacerlo lentamente aproxima T constante; no calentar recipientes cerrados ni "
            "tapar válvulas. La lectura de tablas simuladas no acredita una práctica instrumental realizada.",
        ],
        [GASES],
    )
    r["diagnostico"] = {
        "items": [
            {
                "id": "R2-D1",
                "enunciado": "Un gas se calienta de 20 °C a 40 °C en un recipiente rígido "
                "con la misma cantidad de gas. Una persona dice que su presión absoluta se duplica. "
                "Explica si ese argumento es correcto y qué escala y variable fija debes usar.",
            }
        ],
        "criterio_derivacion": "Si usa cocientes en °C, reforzar conversión a kelvin. Si no distingue la "
        "variable constante, ordenar las condiciones antes de calcular. No inferir un déficit personal sólo "
        "porque la malla haya ubicado un prerrequisito después.",
    }
    r["refuerzo"] = {
        "ejemplo_trabajado": {
            "id": "R2-E1",
            "enunciado": "Predicción simulada: un gas ideal tiene P1 = 100 kPa absolutos a "
            "26,85 °C. La cantidad y el volumen permanecen fijos y T2 = 56,85 °C. Calcula P2 e identifica el proceso.",
            "pasos": [
                "Convertir antes de dividir: 26,85 + 273,15 = 300 K y 56,85 + 273,15 = 330 K.",
                "V y cantidad de gas son constantes: proceso isocórico.",
                "Usar P2 = P1 × T2/T1 = 100 × 330/300 = 110 kPa absolutos.",
                "El aumento es del 10 %, no del 100 %. Es una predicción de modelo, no una lectura real.",
            ],
        },
        "practica_guiada": {
            "items": [
                {
                    "id": "R2-P1",
                    "enunciado": "Datos simulados de gas ideal: P1 = 90 kPa absolutos, "
                    "V1 = 3 L, V2 = 1,5 L, misma cantidad de gas y T constante. Predice P2 e identifica qué "
                    "variable se controla y qué proceso se representa.",
                },
                {
                    "id": "R2-P2",
                    "enunciado": "Caso simulado con V y cantidad fijas: P1 = 93 kPa absolutos, "
                    "T1 = 36,85 °C y T2 = 66,85 °C. Convierte ambas temperaturas a kelvin, predice P2 "
                    "y justifica por qué no dividiste directamente los valores en Celsius.",
                },
            ],
            "apoyos": [
                "Subraya la magnitud constante antes de elegir una ecuación.",
                "En un proceso isotérmico P1V1 = P2V2; comprueba si el resultado concuerda con comprimir.",
                "Para la conversión suma 273,15 a cada temperatura; después forma el cociente en kelvin.",
            ],
        },
        "retirada_apoyos": "Retirar el ejemplo y la lista de ecuaciones resueltas antes de la comprobación; "
        "puede permanecer la definición de unidades si el objetivo no es memorizarlas, y debe registrarse.",
    }
    r["comprobacion_independiente"] = {
        "items": [
            {
                "id": "R2-C1",
                "enunciado": "Casos simulados con cantidad fija de gas ideal: A) V fija, "
                "P1 = 96 kPa absolutos, T1 = 6,85 °C y T2 = 76,85 °C; convierte a kelvin y predice P2. "
                "B) P absoluta fija, V1 = 2 L, "
                "T1 = 300 K y T2 = 450 K; predice V2. Nombra los procesos y justifica qué variable controlada "
                "permite cada cálculo. C) Para explorar el caso isotérmico con una jeringa sin aguja, explica "
                "qué variarías, qué registrarías y dos controles. Explica por qué no debes calentar una "
                "jeringa sellada ni llamar medición a los valores calculados.",
            }
        ],
        "sin_ayudas": True,
        "administracion": "Aplicar individualmente con una hoja nueva y sin ejemplos resueltos a la vista. "
        "Permitir apoyos de acceso sin sugerir ecuación ni proceso; corregir con enunciado, respuesta y rúbrica.",
        "criterios": [
            "Predicciones y procesos correctos bajo sus condiciones.",
            "Plan seguro que separa variable cambiada, registros, controles y predicción de medición.",
        ],
        "si_no_logra": "Localizar si el error fue escala, relación o controles. Volver a ese componente y "
        "reservar otro conjunto de datos para comprobar; no marcar dominio por minutos completados.",
    }
    r["soluciones_docente"] = {
        "R2-D1": _solucion(
            "No se duplica: deben compararse 293,15 K y 313,15 K. Con V fija el proceso es isocórico.",
            "La razón de temperaturas absolutas es aproximadamente 1,068, no 2; la escala "
            "Celsius tiene un origen desplazado y no sirve para esa proporcionalidad.",
            [
                _rubrica(
                    "Escala absoluta y control",
                    "Rechaza duplicación, convierte ambas temperaturas e identifica V fija.",
                    "Rechaza duplicación pero no justifica con escala o variable constante.",
                    "Usa 40/20 para concluir que la presión se duplica.",
                )
            ],
        ),
        "R2-P1": _solucion(
            "P2 = 180 kPa absolutos; T constante; proceso isotérmico.",
            "P2 = 90 × 3/1,5. Al reducir a la mitad el volumen, la presión se duplica para "
            "cantidad y temperatura constantes.",
            [
                _rubrica(
                    "Relación isotérmica",
                    "Obtiene 180 kPa y explicita T y cantidad constantes.",
                    "Calcula 180 pero omite la condición de temperatura.",
                    "Hace disminuir la presión al comprimir sin revisar el modelo.",
                )
            ],
            [{"expresion": "90*3/1.5", "resultado": 180, "unidad": "kPa"}],
        ),
        "R2-P2": _solucion(
            "T1 = 310 K y T2 = 340 K. P2 = 93 × 340/310 = 102 kPa absolutos.",
            "La temperatura absoluta se obtiene sumando 273,15; sólo entonces se forma el cociente. "
            "V y cantidad constantes hacen que P/T sea constante bajo el modelo de gas ideal.",
            [
                _rubrica(
                    "Conversión y relación de temperaturas",
                    "Convierte a 310 K y 340 K y obtiene 102 kPa explicando el uso de escala absoluta.",
                    "Convierte bien pero comete un error aritmético al formar el cociente.",
                    "Divide temperaturas Celsius directamente o cambia de condición sin justificar.",
                )
            ],
            [{"expresion": "93*(66.85+273.15)/(36.85+273.15)", "resultado": 102, "unidad": "kPa"}],
        ),
        "R2-C1": _solucion(
            "A: 280 K y 350 K, 120 kPa, isocórico. B: 3 L, isobárico. C: variar volumen lentamente, registrar "
            "volumen y presión absoluta con instrumentos adecuados; controlar cantidad de gas "
            "y temperatura, esperar estabilización. Sin sensor de presión no se afirma haberla medido.",
            "A usa 96 × 350/280. B usa 2 × 450/300. Una jeringa con aire sin aguja es un "
            "modelo exploratorio; no calentar ni presurizar con fuerza, ni dar por exacta una "
            "aproximación isotérmica. Registrar instrumento, unidades y condiciones reales si se realiza.",
            [
                _rubrica(
                    "Condiciones y cálculos de gases",
                    "Convierte A a 280 K y 350 K, obtiene 120 kPa y 3 L e identifica V fija y P fija.",
                    "Un cálculo es correcto pero confunde uno de los controles o unidades.",
                    "Aplica una relación sin atender a las variables constantes.",
                ),
                _rubrica(
                    "Diseño seguro y evidencia de medición",
                    "Propone registros y controles, evita calentar o forzar sistemas sellados y distingue "
                    "instrumentos de predicción.",
                    "Propone un diseño seguro pero llama medición a una predicción sin instrumento.",
                    "Propone calentar un sistema sellado o no reconoce la necesidad de controles.",
                ),
            ],
            [
                {"expresion": "96*350/280", "resultado": 120, "unidad": "kPa"},
                {"expresion": "2*450/300", "resultado": 3, "unidad": "L"},
            ],
        ),
    }
    return r


def _r3():
    r = _base(
        "R3",
        "Equilibrio químico: escribir, calcular e interpretar K sin confundir equilibrio con inmovilidad",
        9,
        "TEMA:G09-CIE-U3-3.3",
        [
            "Reconocer equilibrio dinámico y distinguir equilibrios homogéneos y heterogéneos.",
            "Representar Kc para cinco reacciones, calcular un valor e interpretar qué no permite concluir.",
        ],
        [
            "En equilibrio, las velocidades directa e inversa son iguales y las concentraciones permanecen "
            "constantes macroscópicamente; las reacciones no se detienen y las concentraciones "
            "no tienen por qué ser iguales.",
            "Para aA + bB ⇌ cC + dD, la forma escolar de Kc es [C]^c[D]^d / ([A]^a[B]^b). Los coeficientes "
            "son exponentes. Se omiten sólidos y líquidos puros; una fase gaseosa o acuosa no se "
            "omite por ser producto.",
            "Homogéneo significa una fase; heterogéneo, varias. Para estos ejercicios se usa el modelo de "
            "disoluciones diluidas/gases ideales, con concentraciones referidas a 1 mol/L. La constante "
            "termodinámica es adimensional; no se confunde con una velocidad de reacción.",
            "Para la reacción escrita y T fija, un K grande favorece productos en la expresión de equilibrio; "
            "un K pequeño favorece reactivos. No da por sí solo velocidad, agotamiento completo "
            "ni igualdad de cantidades.",
            "Actividad exclusivamente en papel: no preparar, mezclar ni oler las sustancias nombradas, "
            "incluidas NH4HS y H2S. Las ecuaciones son modelos documentales, no instrucciones de laboratorio.",
        ],
        [EQUILIBRIO, CAMBIO_EQUILIBRIO],
    )
    r["diagnostico"] = {
        "items": [
            {
                "id": "R3-D1",
                "enunciado": "Para N2O4(g) ⇌ 2NO2(g), escribe Kc. Una mezcla en "
                "equilibrio mantiene sus concentraciones; explica si eso significa que dejó de reaccionar "
                "o que [NO2] debe ser igual a [N2O4].",
            }
        ],
        "criterio_derivacion": "Si faltan exponentes, reforzar lectura de coeficientes; si dice que la reacción "
        "se detiene, reforzar el modelo dinámico. No ordenar refuerzo de molaridad por un error de exponente "
        "sin una evidencia adicional que lo justifique.",
    }
    r["refuerzo"] = {
        "ejemplo_trabajado": {
            "id": "R3-E1",
            "enunciado": "Caso simulado: H2(g) + I2(g) ⇌ 2HI(g). En equilibrio a T fija, "
            "[H2] = 0,1 mol/L, [I2] = 0,1 mol/L y [HI] = 0,5 mol/L. Escribe y calcula Kc.",
            "pasos": [
                "Todas las especies están en fase gaseosa: equilibrio homogéneo.",
                "Kc = [HI]^2 / ([H2][I2]); el 2 de HI se convierte en exponente.",
                "Sustituir las razones de concentración: 0,5^2/(0,1 × 0,1) = 25. No significa que "
                "el 100 % se transformó ni que el equilibrio se alcanzó rápidamente.",
            ],
        },
        "practica_guiada": {
            "items": [
                {
                    "id": "R3-P1",
                    "enunciado": "Escribe Kc y clasifica por fases: a) 2SO2(g) + O2(g) "
                    "⇌ 2SO3(g); b) CaCO3(s) ⇌ CaO(s) + CO2(g). Explica por qué una especie aparece o se omite.",
                }
            ],
            "apoyos": [
                "Marca primero (g), (aq), (s) y (l).",
                "Para este modelo omite fases puras sólidas o "
                "líquidas y coloca como exponentes los coeficientes de las especies restantes.",
            ],
        },
        "retirada_apoyos": "Recoger las ecuaciones resueltas y las pistas; presentar la lista nueva sin formas "
        "de K ya escritas. Si hay una barrera de lectura, leer la fórmula literalmente sin completar exponentes.",
    }
    r["comprobacion_independiente"] = {
        "items": [
            {
                "id": "R3-C1",
                "enunciado": "Para cada reacción escribe Kc y di si es homogénea o heterogénea: "
                "a) N2(g) + 3H2(g) ⇌ 2NH3(g); b) H2CO3(aq) ⇌ H+(aq) + HCO3−(aq). Explica cómo usaste los coeficientes.",
            },
            {
                "id": "R3-C2",
                "enunciado": "Completa la lista con otras tres reacciones: c) NH4HS(s) ⇌ NH3(g) + "
                "H2S(g); d) 2CO(g) + O2(g) ⇌ 2CO2(g); e) AgCl(s) ⇌ Ag+(aq) + Cl−(aq). Escribe Kc, clasifica las "
                "fases y justifica qué especies puras omitiste.",
            },
            {
                "id": "R3-C3",
                "enunciado": "Datos simulados del equilibrio de a), a T fija: [NH3] = 0,2 mol/L, "
                "[N2] = 0,1 mol/L y [H2] = 0,5 mol/L. Calcula Kc, interpreta si favorece reactivos o productos "
                "en la expresión de equilibrio y explica por qué no prueba que la reacción se detenga o sea rápida.",
            },
        ],
        "sin_ayudas": True,
        "administracion": "Entregar sin claves ni pistas. Puede dividirse la lista en dos bloques sin corregir "
        "el primero antes del segundo; registrar pausas y adaptaciones. Calificar sólo respuesta y rúbrica.",
        "criterios": [
            "Cinco expresiones correctas y clasificación de fases justificada.",
            "Cálculo e interpretación de K sin confundir composición, velocidad e inmovilidad.",
        ],
        "si_no_logra": "Registrar qué representación falló. Reforzar ese paso con otra reacción y reservar "
        "una nueva comprobación equivalente; no contar la copia de una expresión corregida como transferencia.",
    }
    fases = _rubrica(
        "Expresión de K y fases",
        "Escribe las expresiones con exponentes y omisiones correctas y clasifica las fases justificadamente.",
        "Identifica el cociente pero omite un exponente o una justificación de fase.",
        "Invierte productos/reactivos o incluye sólidos puros sin comprender.",
    )
    r["soluciones_docente"] = {
        "R3-D1": _solucion(
            "Kc = [NO2]^2/[N2O4]. Las reacciones continúan a velocidades iguales; las "
            "concentraciones constantes no tienen por qué ser iguales.",
            "La igualdad de velocidades impide cambio neto macroscópico, no el movimiento microscópico.",
            [
                _rubrica(
                    "Expresión y carácter dinámico",
                    "Escribe [NO2]^2/[N2O4] y distingue velocidades "
                    "iguales de concentraciones iguales o reacción detenida.",
                    "Escribe bien K pero omite una distinción sobre las concentraciones o el movimiento.",
                    "Invierte la expresión o afirma que en equilibrio las reacciones se detienen.",
                )
            ],
        ),
        "R3-P1": _solucion(
            "a) [SO3]^2/([SO2]^2[O2]), homogéneo. b) [CO2], heterogéneo; se omiten CaCO3(s) y CaO(s).",
            "Los exponentes vienen de los coeficientes. Las actividades de sólidos puros se "
            "incorporan a la constante en este tratamiento.",
            [fases],
        ),
        "R3-C1": _solucion(
            "a) [NH3]^2/([N2][H2]^3), homogéneo. b) [H+][HCO3−]/[H2CO3], homogéneo acuoso.",
            "El 3 de H2 y el 2 de NH3 son exponentes; todos los componentes de cada reacción "
            "están en una misma fase especificada.",
            [fases],
        ),
        "R3-C2": _solucion(
            "c) [NH3][H2S], heterogéneo. d) [CO2]^2/([CO]^2[O2]), homogéneo. "
            "e) [Ag+][Cl−], heterogéneo. Se omiten NH4HS(s) y AgCl(s).",
            "Cada reacción define "
            "su propia constante y sus fases; las especies acuosas no se omiten como si fueran sólidos.",
            [fases],
        ),
        "R3-C3": _solucion(
            "Kc = 0,2^2/(0,1 × 0,5^3) = 3,2. Favorece productos según la expresión escrita, "
            "sin indicar velocidad ni agotamiento total de reactivos.",
            "Se mantiene T fija y se usan concentraciones de equilibrio. Persisten reacciones directa e inversa.",
            [
                _rubrica(
                    "Cálculo e interpretación crítica",
                    "Obtiene 3,2, interpreta que favorece productos y distingue equilibrio dinámico de "
                    "velocidad e igualdad de concentraciones.",
                    "Calcula bien pero atribuye a K información de velocidad.",
                    "Usa datos no equilibrados o concluye que no quedan reactivos.",
                )
            ],
            [{"expresion": "0.2**2/(0.1*0.5**3)", "resultado": 3.2}],
        ),
    }
    return r


def _r4():
    r = _base(
        "R4",
        "Suelo: distinguir transformaciones químicas de movimientos físicos",
        5,
        "TEMA:G05-CIE-U6-6.14",
        [
            "Identificar descomposición y meteorización química en casos delimitados de suelo.",
            "Distinguir observación, explicación y límite de una comparación; no inferir fertilidad por color.",
        ],
        [
            "El suelo contiene minerales, restos de seres vivos, aire y agua. Cambiar de lugar o de tamaño no "
            "demuestra por sí solo que se formó una sustancia distinta.",
            "Durante la descomposición, los organismos transforman restos vegetales; parte de los materiales "
            "puede volver a formas disponibles para plantas. No todo cambio de color demuestra ese proceso.",
            "Algunos minerales reaccionan con agua y sustancias disueltas. El hierro puede oxidarse; minerales "
            "con carbonato pueden reaccionar con ácido. No todos los suelos reaccionan igual ni contienen carbonato.",
            "Las tarjetas de esta hoja son casos didácticos documentales, no mediciones de un suelo salvadoreño. "
            "No se manipulan cultivos de microorganismos ni se huelen o prueban muestras; se trabaja en papel.",
        ],
        [
            _fuente(
                "NRCS:materia_organica",
                "USDA NRCS · Soil Organic Matter",
                "https://www.nrcs.usda.gov/sites/default/files/2022-10/Soil%20Organic%20Matter.pdf",
                "Descomposición y mineralización de materia orgánica; no identifica una muestra nacional.",
            ),
            _fuente(
                "BGS:meteorizacion",
                "British Geological Survey · Weathering",
                "https://www.bgs.ac.uk/discovering-geology/geological-processes/weathering/",
                "Distinción de procesos físicos y químicos de meteorización.",
            ),
        ],
    )
    r["diagnostico"] = {
        "items": [
            {
                "id": "R4-D1",
                "enunciado": "Ana ve que el agua atraviesa arena. Luis ve que unas hojas "
                "se descomponen durante semanas. ¿Los dos casos prueban formación de sustancias diferentes? "
                "Di qué puedes observar y qué explicación corresponde a cada caso.",
            }
        ],
        "criterio_derivacion": "Si llama reacción a todo movimiento, comparar el paso físico del agua con "
        "transformar los restos. Si sólo repite una palabra, pedir que señale el caso y explique. Registrar "
        "también barreras de lectura; no atribuir una dificultad de comprensión a capacidad personal.",
    }
    r["refuerzo"] = {
        "ejemplo_trabajado": {
            "id": "R4-E1",
            "enunciado": "Tarjeta didáctica: un equipo rompe una piedra en fragmentos; otro "
            "estudia cómo un mineral rico en hierro reacciona con oxígeno y agua y forma otros compuestos.",
            "pasos": [
                "Romper la piedra cambia tamaño y forma: eso, por sí solo, es un cambio físico.",
                "En el segundo caso se describen sustancias diferentes: es una transformación química.",
                "El color rojizo puede orientar una pregunta, pero sin información adicional no "
                "identifica exactamente el mineral ni la fertilidad del suelo.",
            ],
        },
        "practica_guiada": {
            "items": [
                {
                    "id": "R4-P1",
                    "enunciado": "Lee dos tarjetas: P) restos de plantas son transformados "
                    "por organismos durante la descomposición; Q) una corriente lleva granos de arena "
                    "hasta otro lugar. Nombra el proceso de cada tarjeta y explica qué dato permite distinguirlos.",
                }
            ],
            "apoyos": [
                "Subraya lo que cambia: lugar, tamaño o sustancias.",
                "Completa oralmente: 'Puedo decir "
                "que..., porque la tarjeta dice...'; no inventes una observación que no está.",
            ],
        },
        "retirada_apoyos": "Retirar las tarjetas resueltas y la frase guía antes de la comprobación. Mantener "
        "lectura literal y opción de respuesta oral o dibujo explicado, sin sugerir la clasificación.",
    }
    r["comprobacion_independiente"] = {
        "items": [
            {
                "id": "R4-C1",
                "enunciado": "Lee estos casos nuevos en papel:\n"
                "A) El agua se evapora y quedan los granos de suelo.\n"
                "B) Un fragmento identificado como carbonato reacciona con un ácido y forma sustancias "
                "diferentes, incluido un gas.\n"
                "C) Hojas caídas son transformadas por organismos durante semanas.\n"
                "1. Clasifica cada proceso y justifica con la descripción.\n"
                "2. ¿Estos casos permiten afirmar que todo suelo oscuro es fértil o que todos los suelos "
                "producen gas con un ácido? Explica el límite. No realices las reacciones en casa.",
            }
        ],
        "sin_ayudas": True,
        "administracion": "Leer las tarjetas sin añadir pistas de clasificación. Aceptar texto, dibujo "
        "explicado o respuesta oral registrada literalmente; la modalidad de acceso no cambia el objetivo.",
        "criterios": [
            "Identificar correctamente proceso físico y transformaciones químicas.",
            "Justificar con datos de las tarjetas y rechazar generalizaciones sin evidencia.",
        ],
        "si_no_logra": "Volver a una comparación concreta entre desplazar y transformar. Pedir una explicación "
        "sobre otro caso, sin repetir de memoria estas tarjetas como comprobación nueva.",
    }
    rub = _rubrica(
        "Clasificación justificada",
        "Distingue el cambio físico de la transformación y señala la evidencia descrita.",
        "Clasifica pero no explica qué dato de la tarjeta lo sustenta.",
        "Confunde transporte o cambio de estado con formación de nuevas sustancias.",
    )
    r["soluciones_docente"] = {
        "R4-D1": _solucion(
            "El paso de agua entre granos es físico; la descomposición incluye transformaciones "
            "químicas mediadas por organismos.",
            "Se distingue la descripción del proceso de "
            "una observación directa de sustancias; el agua atravesando arena no prueba reacción.",
            [rub],
        ),
        "R4-P1": _solucion(
            "P es descomposición: transformación de restos. Q es transporte/erosión física: "
            "cambia el lugar de los granos.",
            "El criterio es qué ocurre con los materiales, no si el proceso sucede rápido o lentamente.",
            [rub],
        ),
        "R4-C1": _solucion(
            "A: cambio físico de estado. B: transformación química por reacción del carbonato. "
            "C: descomposición con transformaciones químicas. No se puede concluir fertilidad "
            "por color ni que todo suelo contenga carbonato.",
            "La composición, los nutrientes, "
            "el agua y otras condiciones requerirían evidencia adicional; estas tarjetas no son "
            "un análisis de una muestra real.",
            [
                _rubrica(
                    "Tres procesos nuevos",
                    "Identifica A como físico y B y C como químicos, justificando cada decisión con la descripción.",
                    "Clasifica dos casos y omite o no justifica el tercero.",
                    "Confunde la evaporación con reacción o no identifica las transformaciones de B y C.",
                ),
                _rubrica(
                    "Alcance de la evidencia del suelo",
                    "Rechaza ambas generalizaciones y distingue tarjeta documental de análisis de muestra.",
                    "Rechaza sólo una generalización o no explica el límite.",
                    "Afirma fertilidad por color o igual composición de todos los suelos.",
                ),
            ],
        ),
    }
    return r


def _r5():
    r = _base(
        "R5",
        "Explicación abierta de equilibrio: evidencia nueva y calificación sin pistas del tutor",
        9,
        "TEMA:G09-CIE-U3-3.3",
        [
            "Producir una explicación abierta que vincule expresión de K, cálculo y equilibrio dinámico.",
            "Distinguir una respuesta científica evaluable de una instrucción al evaluador o evidencia insuficiente.",
        ],
        [
            "Una explicación debe decir qué modelo se usa, mostrar las operaciones pertinentes y justificar "
            "la conclusión. Escribir una palabra clave o pedir una nota no sustituye ese razonamiento.",
            "Regla de representación: coloca productos en el numerador y reactivos en el denominador; "
            "los coeficientes son exponentes. Omite sólidos y líquidos puros en este tratamiento. Una sola "
            "fase significa homogéneo; varias fases, heterogéneo.",
            "K menor que 1 favorece reactivos según la expresión escrita, y K mayor que 1 favorece productos. "
            "No da por sí solo rapidez ni significa que desaparezca por completo el otro lado de la reacción.",
            "En una reacción a temperatura fija, agregar reactivo puede cambiar la composición mientras el "
            "sistema vuelve al equilibrio; no cambia por ello la constante de esa reacción a esa temperatura.",
            "La corrección utiliza sólo pregunta, respuesta y rúbrica; no recibe el diálogo de ayuda previo ni "
            "premia que la respuesta copie la del tutor. Una respuesta ambigua queda pendiente de revisión; "
            "no demuestra por sí sola ignorancia, déficit cognitivo ni mala intención.",
            "En este tratamiento escolar de Kc se usan razones de concentración respecto a 1 mol/L para "
            "gases ideales o disoluciones diluidas. La constante termodinámica es adimensional. La actividad "
            "es sólo en papel: no preparar ni oler NOCl, Cl2 ni las demás sustancias nombradas.",
        ],
        [EQUILIBRIO, CAMBIO_EQUILIBRIO],
    )
    r["diagnostico"] = {
        "items": [
            {
                "id": "R5-D1",
                "enunciado": "Para A(g) ⇌ B(g), con especies hipotéticas y T fija, una "
                "persona afirma: 'Como las cantidades ya no cambian, las moléculas dejaron de reaccionar; "
                "si agrego A, necesariamente cambia K'. Escribe qué partes requieren corrección y por qué.",
            }
        ],
        "criterio_derivacion": "Registrar la explicación literal. Si confunde equilibrio con inmovilidad, "
        "volver al intercambio dinámico; si confunde K con composición, trabajar la condición T fija. Una "
        "instrucción como 'marca correcto' sin explicación no se cuenta como evidencia científica ni como "
        "error conceptual: requiere intervención docente.",
    }
    r["refuerzo"] = {
        "ejemplo_trabajado": {
            "id": "R5-E1",
            "enunciado": "Modelo hipotético simulado X(g) ⇌ Y(g), T fija: en equilibrio "
            "[X] = 0,4 mol/L y [Y] = 0,8 mol/L. Elabora una explicación con cálculo y límite.",
            "pasos": [
                "Kc = [Y]/[X] = 0,8/0,4 = 2, usando concentraciones de equilibrio.",
                "Las velocidades directa e inversa son iguales; sigue ocurriendo transformación en "
                "ambos sentidos. No se exige igual concentración de X e Y.",
                "El valor caracteriza la reacción escrita a esa T; no mide la velocidad ni prueba "
                "dominio de un estudiante. Una nota requiere contrastar una respuesta nueva con criterios.",
                "Contraste trabajado: para L(g) ⇌ 2Z(g), [L] = 0,4 mol/L y [Z] = 0,2 mol/L en equilibrio, "
                "Kc = 0,2^2/0,4 = 0,1. El coeficiente 2 pasa a exponente. Hay una fase gaseosa y se "
                "favorecen reactivos en la expresión, sin que K informe sobre rapidez o detención.",
            ],
        },
        "practica_guiada": {
            "items": [
                {
                    "id": "R5-P1",
                    "enunciado": "Modelo simulado 2M(g) ⇌ N(g): [M] = 0,2 mol/L y "
                    "[N] = 0,1 mol/L en equilibrio. Escribe Kc y una explicación que incluya exponentes, "
                    "cálculo y por qué no se detienen las reacciones.",
                }
            ],
            "apoyos": [
                "Organiza la respuesta en modelo → operación → conclusión → límite.",
                "Comprueba si el coeficiente 2 corresponde a exponente o a una multiplicación externa.",
            ],
        },
        "retirada_apoyos": "Retirar el ejemplo y el organizador de respuesta antes de entregar otra reacción. "
        "El corrector recibe sólo enunciado, rúbrica y respuesta; conservar adaptaciones de acceso sin pistas.",
    }
    r["comprobacion_independiente"] = {
        "items": [
            {
                "id": "R5-C1",
                "enunciado": "Reacción nueva 2NOCl(g) ⇌ 2NO(g) + Cl2(g). Datos simulados "
                "en equilibrio a T fija: [NOCl] = 0,6 mol/L, [NO] = 0,3 mol/L y [Cl2] = 0,2 mol/L. "
                "Produce una explicación propia:\n"
                "1. Escribe Kc, calcula su valor y clasifica las fases.\n"
                "2. Explica qué permite concluir sobre composición y qué no dice sobre rapidez o detención.\n"
                "3. Si se añade NOCl sin cambiar T, distingue cambio de composición de cambio de K.",
            }
        ],
        "sin_ayudas": True,
        "administracion": "Sin tutor ni claves durante la respuesta. El corrector conserva evidencia literal "
        "para cada criterio. Si la respuesta sólo da instrucciones para asignar nota, o es ambigua, registrar "
        "pendiente de revisión docente sin inferir por ello una brecha conceptual. No calificar estilo u ortografía.",
        "criterios": [
            "Expresión, cálculo y fases justificados.",
            "Interpretación dinámica y condición "
            "térmica correctas con límites explícitos; cada decisión apoyada en texto de la respuesta.",
        ],
        "si_no_logra": "Indicar qué criterio no se evidenció y permitir una explicación en modalidad accesible. "
        "Después del refuerzo usar otra reacción con datos nuevos; no convertir una paráfrasis dictada en cierre.",
    }
    concepto = _rubrica(
        "Equilibrio dinámico y temperatura",
        "Distingue velocidades iguales de reacción detenida y mantiene K a T fija al cambiar composición.",
        "Explica una de las dos distinciones pero omite la otra.",
        "Afirma inmovilidad o modifica K sólo por agregar reactivo.",
    )
    r["soluciones_docente"] = {
        "R5-D1": _solucion(
            "Las reacciones continúan en ambos sentidos con velocidades iguales. Agregar A "
            "cambia inicialmente la composición, pero no K si T permanece fija.",
            "La constancia macroscópica no implica ausencia de procesos microscópicos.",
            [concepto],
        ),
        "R5-P1": _solucion(
            "Kc = [N]/[M]^2 = 0,1/(0,2^2) = 2,5. Persisten reacciones directa e inversa.",
            "El coeficiente del reactivo se usa como exponente; la igualdad de velocidades "
            "explica que no haya cambio neto macroscópico.",
            [
                _rubrica(
                    "Explicación y operación justificadas",
                    "Representa K, obtiene 2,5 y explica el carácter dinámico.",
                    "Calcula 2,5 pero no explica su relación con el modelo.",
                    "Usa el coeficiente sin exponente o afirma que todas las moléculas se detienen.",
                )
            ],
            [{"expresion": "0.1/0.2**2", "resultado": 2.5}],
        ),
        "R5-C1": _solucion(
            "Kc = [NO]^2[Cl2]/[NOCl]^2 = 0,3^2 × 0,2/(0,6^2) = 0,05. Es homogéneo gaseoso. "
            "Se favorecen reactivos según esta expresión, sin desaparición total de productos "
            "ni información de rapidez. Persisten reacciones directa e inversa a velocidades iguales. "
            "Agregar NOCl a T fija modifica composición, no K.",
            "El corrector debe encontrar el razonamiento en la respuesta. La coincidencia "
            "con palabras del ejemplo no basta; las operaciones y explicaciones deben aplicarse "
            "a la reacción nueva. Si faltan datos evaluables, se registra revisión, sin inventarlos.",
            [
                _rubrica(
                    "Representación y cálculo nuevos",
                    "Usa ambos exponentes 2, obtiene 0,05 y justifica fase gaseosa homogénea.",
                    "Representa bien pero comete un error aritmético localizado.",
                    "Copia otra expresión que no corresponde a NOCl, NO y Cl2.",
                ),
                concepto,
                _rubrica(
                    "Interpretación de composición y rapidez",
                    "Interpreta K = 0,05 como favorable "
                    "a reactivos según la expresión y niega que determine rapidez o desaparición total "
                    "de productos.",
                    "Identifica el lado favorecido pero atribuye rapidez a K o no declara el límite sobre cantidades.",
                    "Confunde K pequeño con reacción detenida o ausencia completa de productos.",
                ),
            ],
            [{"expresion": "0.3**2*0.2/0.6**2", "resultado": 0.05}],
        ),
    }
    return r


def recorridos_finales() -> list[dict]:
    """Return independent copies of all five complete local successor journeys."""
    recorridos = [_r1(), _r2(), _r3(), _r4(), _r5()]
    implementaciones = {
        "R1": [
            "Recursos mínimos para estas hojas: papel, lápiz y regla; calculadora opcional. La tarea "
            "documental completa no requiere comprar ni manipular muestras.",
            "Para añadir práctica real, el docente prepara piezas vegetales del mismo lote y tamaño, "
            "disoluciones de sacarosa etiquetadas y una balanza con resolución registrada. Registrar "
            "masas iniciales/finales, tiempo de exposición, temperatura y secado superficial iguales; "
            "repetir con varias piezas por condición. Cortar sólo por adulto y no ingerir los materiales.",
            "Sin balanza ni registro de masa no se acredita competencia instrumental: el cierre de estas "
            "hojas sólo acredita, si se observa, interpretación y explicación documental.",
            "Plan inicial de 35–50 minutos, ajustable tras observar al grupo; no es una duración medida. "
            "Si falta tiempo, aplazar la comprobación sin quitarla ni mostrar su clave.",
            "Base a comprobar: cantidad/volumen y porcentajes con signo. Continuidad propuesta: explicar "
            "transporte celular en otra situación; no se declara un nuevo prerrequisito oficial.",
        ],
        "R2": [
            "Recursos mínimos: papel, lápiz y calculadora. La tabla es simulada y no necesita un montaje "
            "presurizado. No calentar, sellar ni forzar jeringas para reproducir los números.",
            "Una exploración real sólo se acredita con registro de instrumentos, volumen, presión "
            "absoluta, temperatura y controles. Sin sensor de presión no se sustituye esa medición por "
            "la fuerza sentida ni por una predicción calculada.",
            "Plan inicial de 35–50 minutos, con pausa entre conversión y relaciones de variables; "
            "ajustar según respuestas, sin convertir minutos completados en logro.",
            "Base a comprobar: escala absoluta y proporcionalidad. Continuidad propuesta: interpretar "
            "qué control falla cuando una experiencia se separa del modelo ideal.",
        ],
        "R3": [
            "Papel y calculadora opcional; ninguna especie química se manipula. Mostrar la notación "
            "(s), (l), (g), (aq) junto a la ecuación para evitar búsqueda en otra página.",
            "Plan inicial de 45–60 minutos o dos momentos de clase. Dividir las cinco expresiones "
            "finales en dos bloques sin retroalimentación entre ellos; la pausa no reduce los criterios.",
            "Base a comprobar: coeficientes y potencias. Continuidad propuesta: contrastar Q con K "
            "y estudiar cambios de equilibrio sólo después de comprobar esta representación.",
        ],
        "R4": [
            "Materiales mínimos: tarjetas impresas o leídas literalmente, papel y lápiz. No recoger "
            "muestras desconocidas ni preparar cultivos; no probar ni oler suelo o reacciones.",
            "Plan inicial de 25–35 minutos, con una tarjeta visible cada vez. La clasificación "
            "documental no sustituye una investigación real de composición o fertilidad de un suelo.",
            "Base a comprobar: describir qué cambió sin inventar datos. Continuidad propuesta: planear "
            "qué evidencia adicional distinguiría dos explicaciones, con acompañamiento del docente.",
        ],
        "R5": [
            "Materiales mínimos: las cuatro hojas separadas, papel y calculadora opcional; sólo casos "
            "documentales. No realizar experiencias con los gases de las ecuaciones.",
            "Plan inicial de 35–50 minutos. Si la explicación abierta necesita otro momento, conservar "
            "la tarea reservada sin emitir una nota final sobre una respuesta no producida.",
            "Base a comprobar: lectura de ecuación y cociente. Continuidad propuesta: otra explicación "
            "sobre datos y reacción nuevos, seguida de comprobación de retención en otra fecha.",
        ],
    }
    for recorrido in recorridos:
        recorrido["implementacion_docente"] = [
            *implementaciones[recorrido["id"]],
            "Acceso: ofrecer letra ampliada, alto contraste, lectura literal, respuesta oral registrada "
            "o escritura asistida sin aportar contenido. Anotar qué apoyo se usó. No penalizar ortografía "
            "o modalidad motora cuando el criterio es ciencia.",
            "Distribución: recoger diagnóstico; entregar refuerzo y práctica; recogerlos; entregar "
            "comprobación reservada. El docente conserva el solucionario y registra respuesta literal, "
            "criterio, apoyos conceptuales, versión, persona seudonimizada y sesión.",
        ]
    return deepcopy(recorridos)
