# goes-science-kg · Motor de cobertura curricular de Ciencias (El Salvador)

## Contexto
- El MINED (equipo de Ciencias, lidera Katherine Cruz) entregó mallas de Ciencia y Tecnología de 2.° a 9.° y de Física, Química y Biología de 10.°–11.°. Cada fila con «Procedimental» es un TEMA (1.260). Cada tema ya trae PISA 2025, microhabilidades por fase (Aproximar, Explorar, Explicar, Indagar, Reforzar), habilidad TIMSS (Conocer/Aplicar/Razonar), MEN Colombia, DigComp 3.0, habilidades s. XXI y transversales. Sesiones de 55 min.
- El equipo GOES (Jocelyn Montoya) arma una currícula «con base en la de Uruguay». Este repo es la primera pieza del «motor» (grafo de conocimiento): mide QUÉ CUBRE Y QUÉ NO la malla frente a referentes internacionales y de otros países.

## Marco de referencia: TIMSS 2027 es el PRINCIPAL
- **TIMSS 2027** (IEA, publicado 2025; `data/referencia/externos/timss/TIMSS2027_Marcos_Evaluacion.pdf`, cap. 2 Ciencias) es la meta principal: es la próxima prueba que El Salvador podría rendir y la malla nueva se enseñará en ese horizonte.
- **TIMSS 2023** queda como referencia secundaria: es el marco que usó el MINED para la columna «Habilidad TIMSS». La cobertura v1 (2023) ya existe y NO se borra: `catalogo_timss.json`, `clasificacion_v1.json`, `outputs/Cobertura_TIMSS_Ciencias_SV.xlsx`.
- **TIMSS Advanced 2015 Física** sigue para Física 10.°–11.° (no hay versión 2027 de Advanced).
- Cambios 2027 vs 2023 (verificados en el PDF; documentar página al construir el catálogo):
  - Dominios y metas de contenido iguales: 4.° Biology 45 / Physical Science 35 / Earth Science 20; 8.° Biology 35 / Chemistry 20 / Physics 25 / Earth Science 20.
  - Cognitivo 4.° cambia a Conocer 35 / Aplicar 40 / Razonar 25 (antes 40/40/20). 8.° igual: 35/35/30.
  - Áreas 4.°: Biology (I Características y procesos vitales, II Ciclos de vida/reproducción/herencia, III Diversidad y adaptación, IV Ecosistemas, V Salud humana, VI Investigaciones biológicas); Physical Science (I Propiedades y cambios de la materia, II Energía y transferencia, III Luz y sonido, IV Electricidad y magnetismo, V Movimiento y fuerzas, VI Investigaciones); Earth Science (I Rasgos, procesos e historia de la Tierra, II Atmósfera, III Recursos, uso y conservación, IV La Tierra en el Sistema Solar, V Investigaciones).
  - Áreas 8.°: Biology (7, incluye VII Investigaciones), Chemistry (I Composición, II Propiedades, III Reacciones químicas, IV Investigaciones), Physics (6, incluye VI Investigaciones), Earth Science (5, con II Atmósfera y V Investigaciones).
  - NUEVO: áreas de «Investigations» en cada dominio (prácticas científicas). Temas que en v1 quedaron FUERA por ser indagación/método científico ahora pueden caer aquí.
  - NUEVO: subescala de **conocimiento ambiental** (~25 % de los ítems): los objetivos marcados con asterisco (*) en el PDF de Biología y Tierra. Guardar `ambiental: true/false` por objetivo.
  - Cada objetivo puede tener sub-ítems (A, B, C…): el código va a nivel de objetivo numerado (p. ej. T4_27-B1.2) y los sub-ítems se guardan como texto.

## Estructura
- `input/` copia de la carpeta de Drive (mallas, mapa de aprendizaje, fuentes del MINED). SOLO LECTURA.
- `data/raw/` mallas que procesa el pipeline. SOLO LECTURA. Hay duplicados «(1)» con el mismo contenido: `extract_temas.py` usa el más reciente y avisa.
- `data/referencia/catalogo_timss.json` catálogo 2023 (T4=32, T8=46) + TA 2015 (23). Se conserva.
- `data/referencia/catalogo_timss2027.json` (lo construye `scripts/build_catalogo_timss2027.py`) catálogo 2027: codigo (T4_27-…, T8_27-…), marco, dominio, meta_dominio, area_codigo, area, objetivo (paráfrasis en español), subitems, ambiental, es_investigacion, pagina_fuente.
- `data/referencia/equivalencias_timss_2023_2027.csv` (lo construye `scripts/build_equivalencias_timss.py`) codigo_2023 → codigo_2027, tipo (igual / dividido / fusionado / sin_equivalente), nota.
- `data/referencia/clasificacion_v1.json` clasificación 2023 (889 temas). `clasificacion_v2_timss2027.json` misma estructura + version «v2-2027». La muestra de control de la traducción directa falló (3 de 20 mal), así que los 622 temas de 2.°–9.° se reclasificaron (version «v2-2027-reclasificado»); Física 10.°–11.° queda idéntica a v1.
- `data/referencia/externos/` fuentes externas (`manifest.csv`, `estado.csv`). Disponibles: TIMSS 2023/2027/Advanced, PISA 2025, DigComp 3.0, Uruguay, Colombia (Estándares y DBA), Singapur primaria, ERCE 2019. Faltan: Chile (Bases 1.°–6.° y 7.°–2.° medio) y Singapur secundaria baja (MOE retiró el enlace); correr `scripts/descargar_fuentes.py`.
- `data/interim/paises/` objetivos de Uruguay, Colombia y Singapur (con documento y página) y su alineación con TIMSS 2027 (`alineacion.json`, prompt `prompts/alinear_paises.md`). Con ese archivo, `build_cobertura.py --marco 2027` agrega las hojas «Comparacion_paises» y «Paises_objetivos»; informe en `outputs/informe_paises_timss2027.md`.
- `data/referencia/catalogo_pisa2025.json` (`scripts/build_catalogo_pisa2025.py`), `clasificacion_pisa2025.json` (`scripts/clasificar_pisa.py` + `prompts/clasificar_lote_pisa.md`), `presupuesto_candidatos.json` (`scripts/presupuesto.py` + `prompts/presupuesto_lote.md`).
- `outputs/Explorador_Cobertura_Ciencias_SV.html` (`scripts/build_explorador.py`): explorador con filtros por grado, evaluación, dominio y estado; lee los valores del libro recalculado.
- `data/interim/` generados. `outputs/` entregables. `scripts/` pipeline. `prompts/` tareas. `tests/` pruebas. `_respaldo_v*/` versiones anteriores (no tocar).

## Reglas de negocio (no cambiarlas sin preguntar)
- Marco por grado (2027, decisión del equipo GOES del 2026-10-02): 2.°–4.° → T4_27; 5.°–6.° → T8_27; 7.°–8.° → T8_27 Y PISA 2025 (escenarios 100 % TIMSS / 50-50 / 100 % PISA / peso personalizado en `Apego_escenarios!E4`); 9.° → SOLO PISA 2025 (sale de las hojas TIMSS); Física 10.°–11.° → TA 2015. Química/Biología de Bachillerato: sin marco de contenido (solo cognitivo).
- PISA 2025 (7.°–9.°, ciclo acumulado 7.°–9.°): catálogo `catalogo_pisa2025.json` desde el marco final OECD 2026 (cap. 2, con página). Clasificación por IA (`clasificacion_pisa2025.json`): contenido (Box 2.6) obj1/obj2, tipo de conocimiento predominante, elementos procedimentales y epistémicos explícitos, contexto, área de aplicación y demanda cognitiva. La competencia y las subcompetencias NO se clasifican: salen de la malla («Competencia PISA 2025» y microhabilidades E1–E6/D1–D4/I1–I5 por fase).
- Metas PISA: sistemas 37/37/26 (Tabla 2.3); competencias 36–44 / 24–36 / 24–36 (Tabla 2.4); conocimiento 38–48 / 27–33 / 24–30; contextos 1:2:1. Se compara contra el rango y contra el punto medio normalizado.
- Índice de apego = promedio de COINCIDENCIA de balance, COINCIDENCIA cognitiva y (en ciclos) amplitud; coincidencia = 1 − ½ Σ|actual − meta|.
- Presupuesto: por CICLO, con el mismo total de temas (fusiones liberan lo que usan las inserciones). Si un área sale de la tolerancia se aplican todas las brechas del ciclo. Inserción por «cobertura» (objetivo sin temas en un área que sobra) siempre entra y se paga con una fusión extra. «Reubicar» no cuenta en el presupuesto.
- Cada tema: UN objetivo principal (obj1) y opcional uno secundario (obj2). Sin contenido del marco → «FUERA». Nuevos o modificados → «PENDIENTE».
- Un tema va a un área de «Investigations» SOLO si su foco es la práctica científica (planificar, medir, registrar, analizar datos, concluir) y no un contenido disciplinar; si trabaja un contenido mediante indagación, se clasifica por el contenido y la investigación puede ir como obj2.
- Balance: % actual = temas del dominio ÷ evaluables (sin FUERA ni PENDIENTE). Brecha = meta × evaluables − actuales. Agregar sin quitar = ROUNDUP(meta × máx(actual/meta) − actual).
- Amplitud: objetivo cubierto si ≥1 tema de SU ciclo lo trabaja (obj1 u obj2). Profundidad: 0 / 1 débil / 2–3 básica / 4+ sólida.
- Ambiental: % de temas evaluables cuyo obj1 u obj2 es un objetivo ambiental, comparado con la referencia de ~25 %.
- Cognitivo: si «Habilidad TIMSS» nombra varios dominios, reparto en partes iguales. Metas 2027: 4.° 35/40/25; 8.° 35/35/30; TA 30/40/30.
- Excel de salida: todo número de análisis es FÓRMULA sobre la hoja de temas; recalcular con `scripts/recalc.py` y exigir 0 errores.
- Recalcular SIN LibreOffice (no está instalado en la Mac del equipo y no debe instalarse): abrir el libro con **Numbers** y exportarlo a Excel como `outputs/<libro>_numbers.xlsx` (Archivo → Exportar a → Excel, o el `osascript` de Comandos). Luego leer los valores con openpyxl `data_only=True` y exigir 0 errores (`pytest -q` lo revisa para el libro 2027). El `_numbers.xlsx` es solo para verificar: Numbers le agrega la hoja «Resumen de exportación»; el entregable sigue siendo el `.xlsx` generado por el script.
- `build_cobertura.py` y `anotar_mallas.py` se PARAMETRIZAN por marco (`--marco 2023|2027`); no duplicar scripts. La salida 2027 va a `outputs/Cobertura_TIMSS2027_Ciencias_SV.xlsx` y `outputs/mallas_anotadas_2027/`.
- Los catálogos se construyen SOLO desde los PDF oficiales de `data/referencia/externos/` (citar página). Paráfrasis en español, sin copiar párrafos.
- Nunca modificar `input/`, `data/raw/`, los PDF de referencia ni los entregables v1.

## Convenciones
- Español. Arial. Python 3.11+, openpyxl, pandas, pdfplumber/pdftotext.
- Estilo Excel: los entregables v1 (TIMSS 2023) conservan su estilo original (entradas editables en azul). Los libros 2027 y los nuevos van SIN azul: encabezados verde bosque (1E4D3A), totales verde claro, valores editables en celda ámbar con texto café, filas alternadas grises (lo aplica `build_cobertura.py --marco 2027`).
- En Excel: nada de XLOOKUP/FILTER/UNIQUE/SEQUENCE (LibreOffice no los evalúa) → INDEX/MATCH, COUNTIFS, SUMIFS.
- Compatibilidad con Numbers (probado): NO usar «·» en nombres de pestaña (las referencias dan 0); NO usar CHAR(10) (la celda queda vacía; usar un salto de línea literal dentro del texto); NO formatos con signo explícito como '+0.0;-0.0' (Numbers muestra «--»); números dentro de textos siempre con FIXED(x,0) (si no, Numbers hereda el formato: «5000% %», «12,0»). Numbers ignora los formatos condicionales: el estado debe leerse también en texto.
- Pestañas del libro 2027: nombres visibles en `scripts/hojas.py` (prefijo «TIMSS -», «PISA -» o «Datos -»; sin prefijo = mezcla los dos marcos). El script construye con nombres internos y renombra al final. Cada pestaña abre con un recuadro verde de hallazgos cuyo encabezado es el marco que mide (cifras en fórmula, veredicto BIEN/OJO; sin rótulos tipo «en 30 segundos», pedido del usuario); la nota técnica va al final como «Cómo se calcula».
- Toda clasificación con confianza (alta/media/baja), justificación ≤15 palabras y versión; las «baja» se listan para revisión humana.
- Clasificar con subagentes, un lote por grado, usando `prompts/clasificar_lote.md` y el catálogo que corresponda.

## Comandos
```bash
pip install -r requirements.txt                 # openpyxl, pandas, pytest, pdfplumber
python scripts/descargar_fuentes.py --check     # 0. fuentes externas
python scripts/extract_temas.py                 # 1. temas de data/raw (deduplica «(1)»)
python scripts/merge_clasificacion.py           # 2. reutiliza clasificación; deja pendientes
python scripts/build_catalogo_pisa2025.py       # 2-bis. catálogo PISA (valida contra el PDF)
python scripts/clasificar_pisa.py preparar|unir # 2-ter. PISA 7.°–9.° (subagentes en medio)
python scripts/presupuesto.py preparar|unir     # 2-quater. candidatos del presupuesto (subagentes en medio)
python scripts/build_cobertura.py --marco 2027  # 3. libro (--marco 2023 = libro v1, idéntico)
python scripts/recalc.py outputs/<libro>.xlsx   # 4. solo si hay LibreOffice (NO instalarlo en la Mac del equipo); si no, usar 4-bis
# 4-bis. sin LibreOffice: recalcular con Numbers y exportar con valores (luego pytest revisa 0 errores)
osascript -e 'tell application "Numbers"' -e 'activate' \
  -e 'set d to open (POSIX file "'"$PWD"'/outputs/Cobertura_TIMSS2027_Ciencias_SV.xlsx")' -e 'delay 60' \
  -e 'export d to (POSIX file "'"$PWD"'/outputs/Cobertura_TIMSS2027_Ciencias_SV_numbers.xlsx") as Microsoft Excel' \
  -e 'close d saving no' -e 'end tell'
python scripts/anotar_mallas.py                 # 5. copias anotadas
python scripts/alinear_paises.py preparar|unir  # Prompt 02: lotes de países → data/interim/paises/alineacion.json (luego rehacer el libro 2027)
python scripts/build_explorador.py              # 5-bis. explorador HTML (después de recalcular con Numbers)
pytest -q                                       # 6. pruebas
```
