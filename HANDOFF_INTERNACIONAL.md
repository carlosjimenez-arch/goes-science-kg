# Traspaso: grafos internacionales de 9.°–11.° y contraste con la malla V2

> Sesiones del 2026-10-07 y 2026-10-08. Rama `feat/grafos-internacionales-9-11`. Hallazgos y validación: `internacional/README.md`.
> Diseño completo: `specs/11_grafos_internacionales_9_11.md`. Léelo antes que este archivo.

## El pedido (palabras del usuario, resumidas)
Construir, para cada ciencia (Biología, Física, Química y Tierra y Espacio), grafos de conocimiento de países con
educación científica de excelencia para **9.°–11.°**, y contrastarlos con las mallas sugeridas del MINED,
**Versión 2** (`Mallas sugeridas/Versión 2/`). Hacerlo con rol de especialista en educación científica, ser
crítico y detallado. **Todo con la cuenta GOES**:
- git: `carlos.jimenez@goes.gob.sv`, ya configurado en esta carpeta; remoto por el alias SSH `github-goes`.
- GCP: proyecto `g-edu-lxp-xai-dev-prj-976d`, con las credenciales por defecto de gcloud (ADC) y el `.env` del repo.
  **No leas ni imprimas `.env`**: el código lo carga solo.

## Decisiones del usuario (no reabrir)
- **Países (9):** SG, JP, KR, ENG, AU, HK, TW, EE, ON. HK y TW ya están agregados a `config/referentes.yaml`.
- **Contraste contra la malla V2.** La V1 sigue alimentando el grafo principal.
- **Dos niveles por país:** núcleo (lo cursa la mayoría) y especialización (electiva). El contraste principal es
  contra el núcleo; la especialización funciona como techo.
- **Ontario:** se acepta la fuente de Grade 9.
- **Hong Kong:** se usan los marcos actualizados (borradores de consulta del CDC de junio de 2026), no las guías
  de 2015/2018.
- **Inglaterra:** hay que usar lo más actualizado. Se verificó que no hay contenido nuevo publicado: el currículo
  renovado sale en 2027 para enseñarse desde 2028, y los GCSE nuevos desde 2029. Se usa el contenido del DfE de
  2014/2015.

## Estado
| Paso | Estado |
|---|---|
| Descarga de fuentes oficiales (~100 docs) | ✅ `data/fuentes/externos/paises/*/sec_bach/` (Japón: `japon/bachillerato/`), cada una con su `_registro.json` (URL, sha256, vigencia, % de alumnos). Ya están en `manifest.csv` y `estado.csv` |
| Catálogo de extracción | ✅ `config/internacional.yaml`: 60 documentos, uno por curso, con páginas del PDF, nivel y grado SV |
| Malla V2 | ✅ copiada a `data/fuentes/mined/Mallas sugeridas v2/`; `config/mallas_v2.yaml`; `extraer("mallas_v2")` |
| Etiquetado de la malla V2 | ✅ 2.°–11.° completo: `data/interim/internacional/etiquetado/malla_v2_*.json` (746 temas de 9.°–11.° y 561 de 2.°–8.°) |
| Extracción y validación de los países | ✅ 9 países, 8.602 objetivos; la 2.ª corrida hace 0 llamadas (caché estable verificada) |
| Etiquetado de los países | ✅ 9 países; la V2 de 9.°–11.° con dos vocabularios (`malla_v2_<asig>` y `_completo`) |
| Grafo y consenso | ✅ `data/grafo/internacional/` (9.205 nodos, 36.114 aristas, 509 conceptos) |
| Informes y Excel | ✅ `internacional/<asig>.md`, Excel (Datos, Contraste, Resumen), `revision_humana.csv`, README con 20 hallazgos verificados |
| Pruebas | ✅ `tests/test_internacional.py` (24), sin llamar a Vertex |

## Cómo retomar
```bash
uv sync --extra dev --extra pdf --extra analisis --extra rag --extra api --extra vertex
uv run gskg internacional extraer          # 9 países; lo que ya está en caché no se vuelve a pagar
uv run gskg internacional extraer          # 2.ª vez: debe reportar «llamadas» ≈ 0 en cada país (caché estable)
uv run gskg internacional etiquetar        # países + malla V2 (gemini-2.5-pro); unas 300 llamadas
uv run gskg internacional construir        # data/grafo/internacional/ + internacional/<asignatura>.md + Excel
uv run pytest -q && uv run ruff check src tests
```
- Tiempos: Gemini 3.1 Pro con PDF tarda unos 50 s por llamada. La extracción completa sin caché son ~1.000
  llamadas, más o menos 2 horas con 6–8 hilos.
- **No corras el mismo país en dos procesos a la vez**: el segundo sobrescribe el `<pais>.json` del primero y los
  ids cambian.
- Si Vertex devuelve 403: el usuario tiene que volver a autenticar gcloud con la cuenta GOES
  (`gcloud auth application-default login` y `set-quota-project g-edu-lxp-xai-dev-prj-976d`).

## Código nuevo (`src/goes_science_kg/internacional/`)
- `vertex.py`: cliente de Gemini con caché en disco (`data/interim/internacional/cache/`, no se versiona), reintentos
  y tope de llamadas (`VERTEX_MAX_CALLS`). Modelos: extraer con `gemini-3.1-pro-preview`, validar con
  `gemini-2.5-pro`, etiquetar con `gemini-2.5-pro` (región `global`).
- `extraer.py`: recorre cada documento en ventanas de 2 páginas que Gemini lee como PDF (sirve en japonés, coreano,
  chino y estonio). El validador, otro modelo:
  - juzga cada objetivo como fiel, parcial o no fiel; los «no fiel» se descartan;
  - lista los objetivos omitidos, que entran marcados como parciales.
  Las páginas se piden como **posición dentro del adjunto**, porque los modelos confundían el número de página
  impreso con el del PDF.
- `etiquetar.py`: conceptos y prácticas con el vocabulario del repo; los ids inventados pasan a `propuestos`.
- `consenso.py`: grafo por país (país → curso → objetivo → concepto, más los prerrequisitos del repo) y consenso por
  concepto:
  - países que lo enseñan en el núcleo hasta el grado g, y la mediana de su primer grado;
  - como antecedente, los objetivos de grados ≤ 8 de ENG, AU y JP del grafo principal.
- `contraste.py`: clasifica cada concepto de la V2 en faltante, tarde, solo especialización, adelantado, alineado o
  sin referente, y detecta errores de secuencia. La regla está en `clase_de()`.
- `informe.py`: un Markdown por asignatura con evidencia citada (documento y página del país; archivo, hoja y fila
  de la malla) y un Excel con fórmulas (estilo 1E4D3A).

## Errores ya corregidos (no repetir)
1. **Cobertura:** con ventanas de 4 páginas el extractor tomaba solo las notas de alcance y omitía ítems centrales
   (Física Básica de Japón: 21 → 40). Se pasó a 2 páginas, se exige cada ítem hoja de la jerarquía y hay un paso
   de completitud.
2. **Caché que no convergía:** algunas ventanas nunca quedaban guardadas y se volvían a pagar en cada corrida. Se
   arregló pasando al SDK una copia del esquema (`copy.deepcopy`). La causa exacta no quedó aislada: una prueba
   aislada no reproduce la mutación. **Verifica con la 2.ª corrida de `extraer` que las llamadas bajen a ≈ 0.**
3. **YAML:** la clave `ON` se leía como `True`; ahora va entre comillas y hay una prueba.

## Hallazgos para el informe (verificar con los datos al construir)
- **El núcleo obligatorio después de los 16 años es minoría:** solo JP, TW y EE lo tienen. En ENG, AU, HK y ON, y en
  KR desde 고2, Física, Química y Biología son electivas. HK no tiene ciencia común en S4–S6 desde 2021/22. El
  Bachillerato SV, que obliga a cursar las tres ciencias, es más amplio que la mayoría, así que para 10.°–11.° el
  contraste justo es contra JP, TW y EE (y SG H1 en 11.°).
- **La V2 de 9.° incluye disoluciones amortiguadoras, Le Châtelier, titulación y Ka.** En SG, ENG y AU eso es
  A-level/H2 o Senior Secondary 3–4, es decir, 17–18 años. Debe salir en la clase «solo_especializacion» o
  «adelantado»; cuantifícalo.
- **Tierra y Espacio no existe en el Bachillerato SV.** JP y TW la tienen en el núcleo (地学基礎, 必修地球科學), y KR,
  AU, ON y ENG (geología) como electiva.
- **Límites que hay que declarar:**
  - HK no indica el año dentro de S4–S6: todo cae en el rango 9–11, con punto medio 10.
  - El nivel de detalle varía mucho: HK y SG tienen unos 1.850 objetivos cada uno y JP unos 290. El consenso usa
    presencia por país, no conteos.
  - Las clases dependen de etiquetas de IA y van a revisión del MINED.
  - KR 고3 todavía cursa el currículo de 2015.
  - Solo ENG, AU y JP tienen antecedente de grados ≤ 8.

## Pendientes
1. ✅ Visor HTML (`internacional/visor.html`) y antecedente de KR, TW y ON (`antecedente: true` en el catálogo).
2. Confirmar con el MINED las 5 correcciones de `data/interim/internacional/revisiones.json`.
3. **Recalcular los Excel en Numbers a mano.** La automatización con AppleScript se quedó esperando un diálogo.
   Las funciones son compatibles.
4. Preguntar al usuario qué hacer con la carpeta `Mallas sugeridas/` de la raíz (no se versiona).
5. Triaje de los conceptos propuestos (tabla en cada informe), sobre todo «serie de reactividad de los metales».
