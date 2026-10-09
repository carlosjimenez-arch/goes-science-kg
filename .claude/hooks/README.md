# Harness del proyecto (Claude Code)

Las reglas de `CLAUDE.md` que dependían de recordarlas ahora las aplica Claude Code solo, en cualquier sesión.
Configuración en `.claude/settings.json`; identidad esperada en `.claude/harness.json`. Los scripts usan solo la
biblioteca estándar de Python y se prueban en `tests/test_harness.py`.

| Hook | Cuándo | Qué hace |
|---|---|---|
| `contexto_sesion.py` | al iniciar, retomar, limpiar o compactar | rama, cambios sin commit, cuenta de git frente a la de GOES, decisiones sin confirmar con el MINED y estado de las etapas internacionales |
| `guardia_bash.py` | antes de cada comando de terminal | **bloquea** leer o copiar `.env`, escribir en `data/fuentes/` o `reportes/`, commit con otra cuenta o con `ruff`/`pytest` en rojo, push forzado a main o a otro remoto; **pide aprobación** para todo gasto en Vertex (`--confirmar`, `congelar-catalogo`, `make internacional-ia CONFIRMAR=…`) |
| `guardia_archivos.py` | antes de editar o escribir un archivo | **bloquea** `.env`, PDF, `data/fuentes/`, `reportes/` y salidas generadas (`data/grafo/`, caché de Vertex) |

Además, `permissions.deny` impide leer `.env` y editar las fuentes aunque un hook fallara. Un hook que excede su
tiempo no bloquea; por eso las guardas son rápidas y deciden de forma explícita.

Subagente: `.claude/agents/verificador-hallazgos.md` (solo lectura) verifica hallazgos contra las fuentes.
Skills nuevas: `internacional-contraste`, `calidad-grafos`, `decisiones-mined`.

Para cambiar la cuenta o el remoto esperados se edita `.claude/harness.json`; para desactivar una guarda, su entrada
en `.claude/settings.json` (con el acuerdo del responsable del proyecto).
