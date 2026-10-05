# Prompt para pegar en Claude Code (en la carpeta de este kit)

> Antes: copia las 11 mallas .xlsx de Drive («CIENCIA Y TECNOLOGÍA / Mallas sugeridas») a `data/raw/`. Para 3.° grado, descarga la versión Google Sheets como .xlsx con el nombre `Matriz_Ciencias_3er_Grado_U1_U6.xlsx`.

---

Lee CLAUDE.md completo antes de empezar. Vamos a medir qué cubren y qué no cubren las mallas de Ciencias de El Salvador frente a TIMSS y dejarlo escrito en copias de esas mismas mallas.

1. **Entender antes de tocar.** Inventaria `data/raw/`: por archivo, lista hojas, número de temas (filas con «Procedimental») y columnas. Compara con lo esperado en CLAUDE.md (1.260 temas; 2.°: 70, 3.°: 66, 4.°: 72, 5.°: 72, 6.°: 68, 7.°: 91, 8.°: 93, 9.°: 90, Física 10.°: 121, 11.°: 146, Química 10.°: 112, 11.°: 97, Biología 10.°: 70, 11.°: 92). Si algo cambió (archivos nuevos, filas distintas), dímelo antes de seguir.
2. **Extraer y reutilizar.** Corre `scripts/extract_temas.py` y `scripts/merge_clasificacion.py`. Dime cuántos temas se reutilizaron y cuántos quedaron pendientes.
3. **Clasificar solo lo pendiente.** Si hay pendientes, divídelos por grado y lanza un subagente por lote con `prompts/clasificar_lote.md` y el catálogo que corresponda. Junta los resultados en `data/interim/clasificacion_nuevos.json` y vuelve a correr el paso 2 hasta que no queden pendientes.
4. **Construir el libro de cobertura.** Corre `scripts/build_cobertura.py`, recalcula con LibreOffice y verifica 0 errores de fórmula. Comprueba con pandas que el balance del ciclo 5.°–8.° coincide con un conteo directo en Python.
5. **Anotar las mallas.** Corre `scripts/anotar_mallas.py`. Abre una copia anotada y confirma que las 7 columnas «TIMSS · …» quedaron alineadas con su tema (misma fila) y que existe la hoja «Cobertura TIMSS».
6. **Pruebas.** Corre `pytest -q`. Si algo falla, corrige el código, no los datos de referencia.
7. **Informe final (corto).** Por ciclo: dominio con mayor faltante y cuántos temas, objetivos TIMSS no cubiertos, y la lista de temas con confianza «baja» para que los revise el equipo de Ciencias.

Reglas: no modificar nunca `data/raw/` ni `data/referencia/catalogo_timss.json`; no inventar códigos; todo número en Excel debe ser fórmula; pregunta antes de cambiar una regla de negocio de CLAUDE.md.
