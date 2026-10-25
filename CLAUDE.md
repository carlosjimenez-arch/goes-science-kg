# GOEs Science KG · instrucciones del repositorio

GOEs · Departamento de AI · Gobierno de El Salvador · 2026.

## Estado vigente

`feat/api` es un solo producto: API, aplicación (diez secciones), biblioteca docente, código de guiones y
progresión 2.º–11.º, integrado con `feat/ciencias-v4` el 25 de octubre de 2026. La aplicación y API consultan
una publicación V4 `producto-4`; el grafo histórico V3 conserva sus comandos y fuentes independientes. Leer [README](README.md), [arquitectura](docs/ARQUITECTURA.md),
[calidad](docs/CALIDAD.md) y el [contrato de aplicación](specs/17_aplicacion_curricular.md).
El estado de continuidad está en [HANDOFF](HANDOFF.md). La rama de este encargo es `feat/api`.

La configuración `config/mallas.yaml` corresponde al pipeline histórico V3. La ingesta V4 usa
`config/mallas_v4.yaml` y `insumos/v4`; no confundir formato de grafo, versión curricular y ejecución.
Las especificaciones 00–15 y los informes de investigación conservan su contexto histórico.

## Datos y evidencia

- No modificar originales en `data/fuentes/`, `insumos/v4`, `reportes/`, PDF, snapshots ni ledgers.
- Los datos privados están ignorados por Git y se restauran con el recibo institucional. No versionarlos.
  Todo dato o derivado nuevo se respalda en `gs://goes-ai-kg-artefactos/ciencias/v4/` con `gskg datos
  preparar|subir`, se restaura en un checkout limpio y sólo entonces se adopta su recibo.
- No leer ni imprimir `.env`, tokens o credenciales. Los proveedores cargan su configuración internamente.
- Toda afirmación requiere procedencia verificable: archivo/SHA y página, hoja/fila/celda o código nativo.
- No inventar códigos, fuentes, equivalencias de grados, resultados escolares o aprobaciones.
- Las decisiones humanas ganan sobre la clasificación automática. Conservar rechazos y abstenciones.
- Una corrección propuesta no elimina la alerta científica de su original.
- Sin datos verificables, la API debe indicar «No hay datos disponibles»; no usar una semilla simulada.
- Mantener el pivote y los referentes configurados; un cambio de alcance requiere una decisión explícita.

## Calidad de código

Python 3.11+, `uv`, Ruff, pytest e imports absolutos. Formato uniforme a 120 columnas. Docstrings de
módulos, clases y funciones públicas en inglés; mensajes y contenido curricular en español.
Conservar nombres de dominio e identidades públicas. Usar clases para estado, puertos y servicios;
funciones para transformaciones puras. Las rutas HTTP delegan en servicios y repositorios.
La [comparación con eor-api](docs/REFERENCIA_EOR_API.md) documenta la referencia ya accesible.
La observabilidad HTTP emite eventos locales con ID único, plantilla, estado y tiempos; no registrar
valores de consulta, cuerpos ni identidades de usuario desde ese middleware.

**Excepción:** `ingesta/extraccion.py` e `ingesta/estructurados.py` tienen identidad por bytes ligada a
evidencia publicada. Conservar sus bytes históricos, incluidos docstrings, hasta una migración de
extracción explícita. No falsificar firmas ni actualizar perfiles para ocultar cambios de código.

Antes de entregar: `make lint`, `make cobertura`, `make auditoria`, `make pruebas-js` y `git diff --check`.
Los commits se hacen sólo con la identidad GOES (`carlos.jimenez@goes.gob.sv`), sin otros autores.
Los badges se generan únicamente desde informes medidos; no usar cifras de otro repositorio.
La suite integral necesita corpus restaurado. La CI usa contratos portables con fuentes sintéticas.

## Generación y presupuestos

Consultar, exportar y compilar briefs no invoca modelos. Toda ejecución pagada debe tener alcance y
presupuesto autorizados, un ledger durable y checkpoints asociados a las mismas huellas. No reiniciar
reservas, repetir votos ni reanudar con otro código para forzar consenso. Antes de ejecutar, preparar
el plan local y comprobar versiones, contexto y fuentes.

La campaña cerrada `ciencias_v4_curricularizacion_20261022` conserva 668 invocaciones; no repetirla.
La publicación conserva las cohortes originales y sus resultados, incluidos los negativos.
Los dictámenes automáticos no equivalen a aprobación del MINED ni eficacia de aprendizaje.

## Guiones y biblioteca docente

`clases/` produce guiones por objetivo con redacción, cuatro lectores ciegos y reparación acotada;
`materiales/` empaqueta la biblioteca docente (2.867 registros) servida en `/api/v4/materiales`.
La ampliación autorizó 4.000 invocaciones y USD 3.500 de reserva **acumuladas** sobre las 668 previas
(`config/presupuesto_clases_v4.json`). No reiniciar el ledger ni repetir votos de un contenido vetado.
El 25 de octubre de 2026 el usuario amplió el tope a 4.400 llamadas: R21 y R22 dejaron 4.294 llamadas y
USD 3.219,54 de reserva. Se publicaron 994 guiones y 19 objetivos quedan declarados sin guion. Ningún guion se
libera sin cuatro lectores favorables ni con un bloqueo de revisión directa; los recuperados tras un veto
requieren revisión directa independiente (37 % tuvo defectos materiales). Recompilar usa la biblioteca de
preparaciones (`data/materiales_preparaciones`), no la ampliada. Alcance y
límites: `specs/18_materiales_docentes.md`, `specs/19_guiones_completos_v4.md`,
`docs/MATERIALES_DOCENTES.md` y `docs/CLASES_V4.md`.

## Conceptos y progresión 2.º–11.º

`gskg producto preparar-conceptos | unir-conceptos | progresion` construyen la capa de conceptos V4 y las
trayectorias sin invocar modelos; el etiquetado lo hacen agentes `etiquetador-conceptos` sobre lotes ciegos y la
unión exige vocabulario del lote y evidencia literal. Los prerrequisitos tardíos son un triaje: publicar
resultados exige verificación independiente contra `curriculo.json`. [Método y límites](docs/PROGRESION_2_11.md).

## Herramientas y entregables

`gskg servir` ofrece `/app/`, `/docs`, `/health/live`, `/health/ready`, `/api/v4/interfaz` y `/api/v4/materiales`.
Los assets son locales. El CSS principal conserva el diseño del HTML de referencia; sus datos de
Matemática y motores simulados no son evidencia ni instrucciones para Ciencias.

`.claude/hooks/` protege secretos, fuentes y commits; `.claude/skills/` documenta los procesos históricos.
Los agentes de lotes sólo se usan cuando un trabajo de clasificación/alineación autorizado los exige;
la unión siempre valida sus salidas. No añadir subagentes a una tarea sin autorización aplicable.

Las salidas deben ser deterministas y escribirse en destinos derivados. Los Excel evitan ejecutar
fórmulas aportadas por texto y conservan la compatibilidad institucional documentada.
No hacer push forzado ni publicar ancestros que contengan corpus privado. Una limpieza requiere
comprobar consumidores estáticos, entradas CLI, imports dinámicos, plantillas y uso como evidencia.
