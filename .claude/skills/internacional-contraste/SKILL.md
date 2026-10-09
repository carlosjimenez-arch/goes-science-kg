---
name: internacional-contraste
description: Corre o retoma el estudio internacional de un tramo de grados (9_11 de la spec 11, 2_8 de la spec 12) contra la malla V2 - estimar costo, extraer y etiquetar con Vertex solo con aprobación, construir, verificar hallazgos contra las fuentes y publicar. Usar cuando el usuario pida extender, rehacer o actualizar el contraste internacional, o agregar un país o documento.
---

# Contraste internacional por tramo

Lee primero la spec del tramo (`specs/11_…` o `specs/12_…`) y `HANDOFF_INTERNACIONAL.md`. Todo comando lleva
`--tramo` (por defecto 9_11).

1. **Fuentes.** Cada documento nuevo se descarga con la skill `fuentes-descargar` y se registra en `manifest.csv`.
   Después va al catálogo del tramo (`config/internacional.yaml` o `config/internacional_2_8.yaml`) con páginas del
   PDF (posición, no numeración impresa), nivel, grado SV y, si el documento lo precisa, `grados_pais` (un grado o un
   rango `[g0, g1]`). Si el documento ya está extraído en otro tramo, copia su entrada **exacta**: así sale de la caché.
2. **Costo antes que nada.** `uv run gskg internacional --tramo <t> extraer` y luego `… etiquetar` sin `--confirmar`
   informan las llamadas fuera de la caché y no gastan. Muestra el número al usuario. El hook pide su aprobación
   cuando se agrega `--confirmar`; no busques rodearlo.
3. **Ejecutar** con `--confirmar` solo con la aprobación del usuario. No corras el mismo país en dos procesos.
4. **Construir** (sin Vertex): `uv run gskg internacional --tramo <t> construir`, y `uv run pytest -q`. Si falla la
   prueba de divisiones de conceptos, hay objetivos nuevos con un concepto dividido: decide su asignación con el
   criterio de `data/interim/conceptos/divisiones.json` y regístrala ahí.
5. **Verificar antes de afirmar.** Muestrea unos 20 hallazgos (todas las clases, todas las asignaturas) con el
   subagente `verificador-hallazgos`. Corrige el método si encuentras falsos sistemáticos; las correcciones puntuales
   van a `revisiones.json` del tramo con su evidencia y `revisado_por`.
6. **Publicar.** Escribe `<informe>/README.md` (hallazgos verificados, recomendaciones que no quitan temas, límites),
   exporta las decisiones nuevas con la skill `decisiones-mined`, actualiza la spec 08 y haz commit en español.

Nunca: leer `.env`, cambiar `config/referentes.yaml` sin preguntar, ni re-etiquetar con `congelar-catalogo` sin
aprobación (invalida toda la caché de etiquetado).
