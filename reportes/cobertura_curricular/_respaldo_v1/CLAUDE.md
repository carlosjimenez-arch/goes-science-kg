# Grafo Ciencias · Cobertura TIMSS de la malla de Ciencia y Tecnología (El Salvador)

## Contexto del proyecto
- El MINED (equipo de Ciencias, lidera Katherine Cruz) entregó mallas curriculares de Ciencia y Tecnología de 2.° a 9.° y de Física, Química y Biología de 10.° y 11.° (11 archivos Excel). En la carpeta de Drive «CIENCIA Y TECNOLOGÍA / Mallas sugeridas».
- Cada fila con «Procedimental» es un TEMA (1.260 en total). Cada tema ya trae: competencia PISA 2025, microhabilidades por fase (Aproximar, Explorar, Explicar, Indagar, Reforzar), habilidad TIMSS (Conocer/Aplicar/Razonar), MEN Colombia, DigComp 3.0, habilidades del siglo XXI y transversales.
- Este repo mide la COBERTURA de esas mallas frente a TIMSS: balance por dominio, amplitud de objetivos y profundidad cognitiva. Es la primera pieza del «motor» (grafo de conocimiento).

## Estructura
- `data/raw/` mallas originales (.xlsx). SOLO LECTURA: nunca escribir aquí.
- `data/referencia/catalogo_timss.json` 101 objetivos: TIMSS 2023 4.° (T4, 32), 8.° (T8, 46) y TIMSS Advanced 2015 Física (TA, 23), con dominio y meta %.
- `data/referencia/clasificacion_v1.json` clasificación vigente tema → objetivo, clave (archivo, hoja, fila) + texto del procedimental.
- `data/interim/` archivos generados (temas.json, clasificacion.json, pendientes.json).
- `scripts/` pipeline: extract_temas → merge_clasificacion → (clasificar pendientes) → build_cobertura → anotar_mallas.
- `outputs/` entregables: `Cobertura_TIMSS_Ciencias_SV.xlsx` y `mallas_anotadas/*_TIMSS.xlsx`.
- `prompts/clasificar_lote.md` instrucciones fijas para clasificar temas nuevos.

## Reglas de negocio (no cambiarlas sin preguntar)
- Marco por grado: 2.°–4.° → T4; 5.°–8.° → T8; 9.° → T8 solo como referencia; Física 10.°–11.° → TA. Química y Biología de Bachillerato: sin marco de contenido (solo análisis cognitivo).
- Cada tema tiene UN objetivo principal (obj1) y opcionalmente uno secundario (obj2). Sin contenido TIMSS → «FUERA».
- Balance: % actual = temas del dominio ÷ temas evaluables (sin FUERA ni PENDIENTE). Brecha = meta × evaluables − actuales.
- «Temas a agregar sin quitar» = ROUNDUP(meta × máx(actual/meta) − actual).
- Amplitud: objetivo cubierto si ≥1 tema de SU ciclo lo trabaja (obj1 u obj2). Profundidad: 0 / 1 débil / 2–3 básica / 4+ sólida.
- Cognitivo: si la columna «Habilidad TIMSS» nombra varios dominios, reparto en partes iguales.
- En los Excel de salida todo número de análisis debe ser FÓRMULA sobre la hoja Temas_TIMSS (nada hardcodeado). Recalcular con LibreOffice y exigir 0 errores.

## Convenciones
- Idioma: español. Fuente Arial. Entradas editables en azul.
- Python 3.11+, openpyxl, pandas. Sin XLOOKUP/FILTER/UNIQUE (LibreOffice no los evalúa): usar INDEX/MATCH, COUNTIFS, SUMIFS.
- Nunca modificar los archivos originales: siempre copias en `outputs/`.
- Toda clasificación nueva queda con confianza (alta/media/baja), justificación ≤15 palabras y versión. Las de confianza «baja» se listan para revisión humana.

## Comandos
```bash
python scripts/extract_temas.py          # 1. extraer temas de data/raw
python scripts/merge_clasificacion.py    # 2. reutilizar clasificación; deja pendientes
# 3. si hay pendientes: clasificarlos con prompts/clasificar_lote.md → data/interim/clasificacion_nuevos.json y repetir paso 2
python scripts/build_cobertura.py        # 4. libro de cobertura con fórmulas
python <ruta_skill_xlsx>/scripts/recalc.py outputs/Cobertura_TIMSS_Ciencias_SV.xlsx 120   # o: soffice --headless --convert-to xlsx
python scripts/anotar_mallas.py          # 5. copias anotadas de cada malla
pytest -q                                # 6. pruebas
```
