# Cobertura de marcos sobre la malla V4 · método, resultado y decisiones (2026-11-05)

> **Datos privados fuera de Git.** El repositorio es público. Las filas de la malla V4, los lotes, los veredictos y la
> malla propuesta están solo en el bucket institucional:
> `gs://goes-ai-kg-artefactos/ciencias/v4/analisis/cobertura_marcos/2026-11-05/`, con un `MANIFIESTO_SHA256.txt` por
> carpeta. Este documento solo trae el método, las cifras agregadas y las decisiones pendientes. Todo es dictamen de
> IA (alineadores, revisor ciego y panel de expertos IA) y **no es una confirmación del MINED**.

## Pregunta
¿Cuánto cubre la malla V4 del MINED (11 matrices, 1.020 filas) los marcos que el proyecto usa en cada ciclo, y qué
cambios mínimos la llevarían a una cobertura mayor sin sobrecargar el año escolar?

| Ciclo | Marco |
|---|---|
| 2.°–4.° | TIMSS 2027 · 4.° grado |
| 5.°–8.° | TIMSS 2027 · 8.° grado |
| 7.°–9.° | PISA 2025 (contenido, conocimiento procedimental y epistémico) |
| Física 10.°–11.° | TIMSS Advanced 2015 |
| Biología y Química 10.°–11.° | ACARA Senior Secondary v8.4 |

TIMSS 2023 queda fuera del denominador, porque se representa por equivalencias con 2027. Total: 415 objetivos.

## Método (cuatro iteraciones)
1. **Alineación por objetivo.** Cada objetivo de marco se compara con todas las filas V4 de su ciclo, usando el
   procedimental, el indicador de logro y la evidencia de aprendizaje de cada fila.
   - En TIMSS se juzga subítem por subítem.
   - «Cubierto» exige que la fila trabaje la idea central con demanda comparable; nombrarla no basta.
   - La unión valida que ningún id esté inventado.
   - Un verificador independiente coincidió en el 83 % de una muestra.
2. **Prioridad por código, sin IA**, a partir del contraste internacional de 9.° a 11.°:
   - A: TIMSS, PISA y el núcleo de ACARA que enseñan 3 o más países.
   - B: el resto.
   - C: especialización, que nunca se convierte en clase.
3. **Reglas duras de la propuesta:**
   - una fila es una clase de 55 minutos con un objetivo principal;
   - el procedimental tiene 45 palabras como máximo;
   - el indicador de logro evalúa lo que dice el procedimental;
   - **una reformulación no puede perder nada del original**;
   - techo de **+3 clases netas por grado y asignatura**, pagadas con fusiones de filas duplicadas;
   - no se quita ningún tema.
4. **Verificación:** re-juicio ciego de todos los cierres sobre la malla resultante, que juzga cobertura,
   viabilidad, pérdida de contenido y exactitud científica y de seguridad. Después, panel de expertos IA (cuatro
   disciplinas y psicopedagogo) con adoptar, adaptar o descartar.

**Errores propios corregidos en el camino.** Quedan documentados en el bucket.
- La primera extracción leyó el «Indicador avanzado» (uno por unidad) en lugar de los campos por fila, lo que
  subestimaba la línea base.
- La propuesta de la ronda 2 cubría sustituyendo contenido: 32 filas perdían algo. La regla «no se pierde nada»
  lo corrigió; en la ronda 3 no hubo ninguna pérdida.

## Resultado

| Marco | V4 hoy | Cobertura limpia propuesta¹ |
|---|---|---|
| TIMSS 4.° | 62 % | 88 % |
| TIMSS 8.° | 38 % | 75 % |
| PISA contenido | 95 % | 100 % |
| PISA procedimental y epistémico | 75 % | 82 % |
| TIMSS Advanced Física | 87 % | 100 % |
| ACARA Biología | 45 % | 73 % |
| ACARA Química | 63 % | 84 % |
| **Global (415)** | **58 %** | **81 %** |

¹ Limpia: el revisor ciego confirma la cobertura, la clase cabe en 55 minutos y no hay error científico ni de
seguridad. Se midió antes de aplicar las adaptaciones del panel. La cobertura verificada sin esos filtros es del 93 %.

- **Carga:** como máximo +3 clases netas por asignatura y año. La malla pasa de 1.020 a 1.038 filas: cambian 176 y
  se fusionan 15.
- **Pérdidas de contenido:** de 32 a 9, y el panel atendió las 9.
- **Errores científicos:** de 5 a 2, en la misma fila, que el panel corrigió.
- **Panel sobre la última ronda:** 93 adoptar, 46 adaptar, 16 conciliados y 0 descartar.

## Decisiones pendientes para el MINED
1. Dividir en dos la clase de solubilidad de Química 10.°.
2. Salud en 9.°: si inmunidad y vacunas bajan a 6.°, hay que adoptar también las dos clases nuevas de 9.°.
3. Verificar con el MARN la alerta sísmica que menciona una fila de 9.°.
4. Crear clases propias de naturaleza de la ciencia en 7.°–11.°: 51 de 168 cierres siguen sobrecargados, sobre todo
   en el eje epistémico.
5. Ampliar el techo de carga en 5.°–8.° si TIMSS 8.° es prioridad. Faltan separación de mezclas, herencia frente a
   adquisición, el Sol como estrella, electroimanes y recursos no renovables.
6. Corregir inconsistencias de la propia V4: indicadores copiados, filas repetidas y 8 grupos de duplicados.

## Límites
- Todos los juicios son de modelos de la misma familia. El panel encontró errores que el revisor ciego no vio.
- La línea base varía unos ±15 % por objetivo entre mediciones.
- Antes de dar el 81 % por bueno, un especialista humano debe revisar una muestra.
- La malla final, con el panel aplicado, no ha pasado por un nuevo re-juicio ciego.

## Dónde está cada cosa (bucket)

| Carpeta | Contenido |
|---|---|
| raíz | Ronda 1 y su informe |
| `ronda2/` | Priorización y techo de carga |
| `panel/` | Panel sobre la ronda 2 |
| `correccion_extractor/` | Nota del defecto de columnas |
| `ronda3/` | Nueva línea base y propuesta con las columnas reales |
| `correccion_y_panel/` | Corrección acotada, panel final, `malla_final_v3.json`, `malla_final_v3_cambios.csv` y `INFORME_CORRECCION.md` |

En cada carpeta, los scripts que generan y validan sus resultados están junto a ellos.
