# Prompt 00 · Cobertura TIMSS v1 (pegar en Claude Code, en la raíz de goes-science-kg)

Lee CLAUDE.md completo. Vamos a medir qué cubren y qué no cubren las mallas de Ciencias frente a TIMSS y dejarlo escrito en copias de esas mismas mallas.

1. **Entorno y fuentes.** `pip install -r requirements.txt`. Corre `python scripts/descargar_fuentes.py --check` y luego sin `--check` para bajar lo que falte. Si alguna fuente queda en FALTA, dime cuál y su URL para bajarla a mano; no sigas con una fuente que el paso necesite.
2. **Entender antes de tocar.** Inventaria `data/raw/`: por archivo, hojas, número de temas y columnas. Esperado: 1.260 temas (2.°: 70, 3.°: 66, 4.°: 72, 5.°: 72, 6.°: 68, 7.°: 91, 8.°: 93, 9.°: 90, Física 10.°: 121, 11.°: 146, Química 10.°: 112, 11.°: 97, Biología 10.°: 70, 11.°: 92). Hay copias «(1)»: confirma que el extractor las deduplica. Si cambió algo, avísame antes de seguir.
3. **Verificar el catálogo contra los PDF oficiales.** Extrae el texto de `externos/timss/TIMSS2023_Marco_Ciencias.pdf` y `TIMSSAdvanced2015_Marco_Fisica.pdf` y comprueba, objetivo por objetivo, que `data/referencia/catalogo_timss.json` tiene las mismas áreas, el mismo número de objetivos (T4=32, T8=46, TA=23) y las mismas metas por dominio. Agrega a cada objetivo la página del PDF (`pagina_fuente`). Reporta diferencias; no cambies códigos existentes.
4. **Extraer y reutilizar.** `scripts/extract_temas.py` y `scripts/merge_clasificacion.py`. Dime cuántos temas se reutilizaron y cuántos quedaron pendientes.
5. **Clasificar solo lo pendiente** con subagentes (un lote por grado) usando `prompts/clasificar_lote.md`. Junta en `data/interim/clasificacion_nuevos.json` y repite el paso 4 hasta 0 pendientes.
6. **Construir y recalcular.** `scripts/build_cobertura.py` + `scripts/recalc.py` (0 errores). Comprueba con pandas que el balance del ciclo 5.°–8.° coincide con un conteo directo en Python.
7. **Anotar las mallas.** `scripts/anotar_mallas.py`. Abre una copia y confirma que las 7 columnas «TIMSS · …» están en la fila de su tema y que existe la hoja «Cobertura TIMSS».
8. **Pruebas.** `pytest -q`. Si algo falla, corrige el código, no los datos de referencia.
9. **Informe corto.** Por ciclo: dominio con mayor faltante y cuántos temas, objetivos no cubiertos y la lista de temas con confianza «baja» para el equipo de Ciencias.

Reglas: no modificar `input/`, `data/raw/` ni los PDF de `externos/`; no inventar códigos; todo número en Excel es fórmula; pregunta antes de cambiar una regla de CLAUDE.md.
