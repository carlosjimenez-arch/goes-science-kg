# 07 · Calidad y gobernanza

## Invariantes (los revisa `gskg grafo validar`; si falla uno, es un ERROR)
1. Ids únicos. Toda arista apunta a nodos existentes.
2. Todo `Tema` trae archivo, hoja y fila. Todo `ObjetivoPais` trae documento y página.
   Todo `ObjetivoMarco` de TIMSS 2027 o PISA trae página.
3. Toda arista con `metodo = ia` trae confianza, justificación y versión.
4. *(fase 3)* `PRERREQUISITO_DE` sin ciclos dentro de cada asignatura.
5. *(fase 5)* Toda `PropuestaTema` trae al menos una evidencia, y el presupuesto por ciclo cuadra.

## Avisos (no bloquean; van a revisión humana)
- Temas sin asignatura.
- Justificaciones de más de 15 palabras.
- Aristas de confianza «baja».

## Reglas para la IA
- **No inventar códigos**: el script de unión rechaza códigos que no estén en el catálogo.
- **Parafrasear** en español. No copiar párrafos de los PDF (citas literales de 30 palabras como máximo).
- **Confianza**: «alta» si el texto es inequívoco; «media» si hay que interpretar; «baja» si es dudoso
  o el encaje es parcial.
- **Versión** en cada lote (`<tarea>-v<n>-<marco>`). No se sobrescriben versiones anteriores:
  se agrega la nueva y se registra la diferencia.
- Antes de un lote completo se corre una **muestra de control** (20 ítems), que se revisa a mano.
  Si hay 3 errores o más, se ajusta el prompt (el trabajo previo lo hizo así con TIMSS 2027).

## Pruebas
- `pytest -q` en verde antes de cada commit.
- Pruebas de contrato: conteos de v0, determinismo (dos construcciones con el mismo SHA-256),
  reglas de disciplina y trazabilidad.
- Cada etapa nueva agrega sus pruebas: catálogo (metas y páginas), alineación (códigos válidos
  y 100 % cubierto) y DAG (sin ciclos).

## Revisión humana
- Los CSV de revisión van a `asignaturas/<x>/revision/` con columnas para la decisión.
- La decisión se reimporta como `revisado_por = <persona o equipo>` y gana sobre la IA.
- Las clasificaciones que ya revisó el equipo de Ciencias no se reclasifican sin preguntar.

## Git
- Commits pequeños por etapa, en español, con el formato `tipo(ámbito): resumen`.
- Siempre se versionan `data/grafo/` y `asignaturas/*/ficha.md`, para ver los cambios del grafo en el diff.
