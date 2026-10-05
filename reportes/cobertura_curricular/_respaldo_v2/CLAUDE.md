# goes-science-kg · Motor de cobertura curricular de Ciencias (El Salvador)

## Contexto
- El MINED (equipo de Ciencias, lidera Katherine Cruz) entregó mallas de Ciencia y Tecnología de 2.° a 9.° y de Física, Química y Biología de 10.°–11.°. Cada fila con «Procedimental» es un TEMA (1.260). Cada tema ya trae PISA 2025, microhabilidades por fase (Aproximar, Explorar, Explicar, Indagar, Reforzar), habilidad TIMSS (Conocer/Aplicar/Razonar), MEN Colombia, DigComp 3.0, habilidades s. XXI y transversales. Sesiones de 55 min.
- El equipo GOES (Jocelyn Montoya) arma una currícula «con base en la de Uruguay». Este repo es la primera pieza del «motor» (grafo de conocimiento): mide QUÉ CUBRE Y QUÉ NO la malla frente a referentes internacionales y de otros países.
- v1 (2026-10-01): cobertura frente a TIMSS 2023 (4.°/8.°) y TIMSS Advanced 2015 Física. 889 temas clasificados (`data/referencia/clasificacion_v1.json`).

## Estructura
- `input/` copia de la carpeta de Drive (mallas, mapa de aprendizaje, fuentes del MINED). SOLO LECTURA.
- `data/raw/` mallas que procesa el pipeline. SOLO LECTURA. Hay duplicados «(1)» con el mismo contenido: `extract_temas.py` usa el más reciente y avisa.
- `data/referencia/catalogo_timss.json` 101 objetivos TIMSS (T4=32, T8=46, TA=23) con dominio y meta %.
- `data/referencia/clasificacion_v1.json` tema → objetivo, clave (archivo, hoja, fila) + texto del procedimental.
- `data/referencia/externos/` marcos y currículos externos (ver `manifest.csv` y `estado.csv`): TIMSS 2023/2027/Advanced, PISA 2025, DigComp 3.0 (Excel + JSON-LD), Uruguay (MCN, progresiones, programas EBI por tramo), Chile, Colombia (EBC, DBA), Singapur, ERCE.
- `data/interim/` generados. `outputs/` entregables. `scripts/` pipeline. `prompts/` instrucciones de tareas. `tests/` pruebas.

## Reglas de negocio (no cambiarlas sin preguntar)
- Marco por grado: 2.°–4.° → T4; 5.°–8.° → T8; 9.° → T8 solo referencia; Física 10.°–11.° → TA. Química/Biología de Bachillerato: sin marco de contenido (solo cognitivo).
- Cada tema: UN objetivo principal (obj1) y opcional uno secundario (obj2). Sin contenido del marco → «FUERA». Nuevos o modificados → «PENDIENTE» hasta clasificarlos.
- Balance: % actual = temas del dominio ÷ evaluables (sin FUERA ni PENDIENTE). Brecha = meta × evaluables − actuales. Agregar sin quitar = ROUNDUP(meta × máx(actual/meta) − actual).
- Amplitud: objetivo cubierto si ≥1 tema de SU ciclo lo trabaja (obj1 u obj2). Profundidad: 0 / 1 débil / 2–3 básica / 4+ sólida.
- Cognitivo: si «Habilidad TIMSS» nombra varios dominios, reparto en partes iguales.
- Excel de salida: todo número de análisis es FÓRMULA sobre Temas_TIMSS; recalcular con `scripts/recalc.py` y exigir 0 errores.
- Los catálogos se construyen SOLO desde los PDF oficiales de `data/referencia/externos/` (citar página). Objetivos parafraseados en español, sin copiar párrafos.
- Nunca modificar `input/`, `data/raw/` ni los PDF de referencia. Las copias anotadas van a `outputs/`.

## Convenciones
- Español. Arial. Entradas editables en azul. Python 3.11+, openpyxl, pandas, pdfplumber/pdftotext.
- En Excel: nada de XLOOKUP/FILTER/UNIQUE/SEQUENCE (LibreOffice no los evalúa) → INDEX/MATCH, COUNTIFS, SUMIFS.
- Toda clasificación con confianza (alta/media/baja), justificación ≤15 palabras y versión; las «baja» se listan para revisión humana.

## Comandos
```bash
pip install -r requirements.txt                 # openpyxl, pandas, pytest, pdfplumber
brew install --cask libreoffice                 # solo si scripts/recalc.py no lo encuentra
python scripts/descargar_fuentes.py --check     # 0. ¿están todas las fuentes externas?
python scripts/descargar_fuentes.py             #    baja lo que falte (o indica URL para bajarlo a mano)
python scripts/extract_temas.py                 # 1. temas de data/raw (deduplica «(1)»)
python scripts/merge_clasificacion.py           # 2. reutiliza clasificación; deja pendientes
#   3. pendientes → prompts/clasificar_lote.md → data/interim/clasificacion_nuevos.json → repetir 2
python scripts/build_cobertura.py               # 4. libro con fórmulas
python scripts/recalc.py outputs/Cobertura_TIMSS_Ciencias_SV.xlsx
python scripts/anotar_mallas.py                 # 5. copias anotadas
pytest -q                                       # 6. pruebas
```
