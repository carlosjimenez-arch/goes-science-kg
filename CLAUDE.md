# goes-science-kg · Grafo de conocimiento de Ciencias (El Salvador)

## Guiones completos (ampliación del 22 de octubre)

El usuario autorizó 4.000 invocaciones y USD 3.500 de reserva **acumuladas**, manteniendo las 668
anteriores en `ciencias_v4_curricularizacion_20261022`. La configuración está en
`config/presupuesto_clases_v4.json`; se comprueba el prefijo histórico íntegro antes de usar el proveedor.
No reiniciar el ledger. El piloto completo tiene 24 objetivos respaldados y la campaña exhaustiva
está en curso. `clases/` implementa los guiones, cuatro lectores, reparación acotada, campaña,
auditoría contra respuestas reales del ledger, ZIP y distribución. Se conservan P1–P4 y sus fallos.
No cambiar los ocho archivos del entorno ni parámetros de modelos durante la campaña P5; el código
está congelado en `data/clases_v4/protocolos/codigo_clases_p5.zip`. Los campos docentes admiten hasta
2.000 caracteres; tiempos, fuentes y doce criterios siguen siendo obligatorios. No repetir votos
del mismo contenido vetado. `docs/CLASES_V4.md` y `specs/19_guiones_completos_v4.md` fijan el alcance.
La biblioteca anterior sigue publicada; no afirmar que todos los guiones nuevos están publicados
hasta verificar 1.013 objetivos, artefactos, restauración desde GCS y actualizar ambos recibos.
Al iniciar P5 había 71 guiones respaldados y 942 en cola. La rama técnica recupera sólo lectores sin
dictamen válido una vez, conservando borrador y votos. Nunca se usa ante vetos semánticos. P1–P4
siguen auditables. La migración del corpus admite más de diez bases y revierte instalaciones fallidas;
el recibo nuevo declara su cota explícita, hasta 8 GiB. No restaurar el ledger anterior de 668 llamadas
para continuar una campaña que ya gastó más: se requiere el respaldo actualizado o el ledger actual.

## Biblioteca docente (2026-10-22)

`gskg materiales construir|validar|publicar|restaurar` prepara y distribuye 2.867 registros:
1.013 paquetes V4 por objetivo, 108 por unidad, siete fuera de alcance, 150 paquetes V3,
1.583 elementos pedagógicos históricos, cinco recorridos y una unidad experimental V4.
El recibo `config/materiales_ciencias.lock.json` fija dos objetos privados de Ciencias.
La API `/api/v4/materiales` es de lectura y funciona con sólo esta biblioteca restaurada.
No equivale a guiones nuevos cronometrados: reutiliza propuestas con revisión de unidad;
no trasladar estados V3/históricos ni la revisión experimental al snapshot curricular actual.
Cero llamadas nuevas y ledger inalterado. Contrato: `specs/18_materiales_docentes.md`;
operación y pruebas: `docs/MATERIALES_DOCENTES.md`. No editar los originales ni sus pendientes.

## Aplicación curricular (2026-10-22)

`gskg servir` ofrece la interfaz GOES en `/app/`, OpenAPI en `/docs` y la nueva API en
`/api/v4/interfaz`. `api_interfaz.py` comparte el lector de snapshot V4; `interfaz/consulta.py`
proyecta sus datos y `interfaz/estaticos/` contiene los assets locales. No incorporar la semilla ni el
motor simulado del HTML adjunto. El detalle y los briefs verifican las celdas originales; compilar un
brief no consume modelos ni modifica dictámenes. LXP/territorio/usuarios no tienen fuente conectada.
El corpus se restauró para servir la aplicación y sigue ignorado por Git. Pruebas y límites actuales:
`docs/APLICACION_CIENCIAS.md` y `specs/17_aplicacion_curricular.md`.

## Cierre técnico V4 (2026-10-22)

La selección estable es `producto-4`: 108 unidades y 1.013 propuestas de Ciencias sobre 1.020 filas,
con siete fuera de alcance preservadas. P6 y P7 terminaron; no repetir sus votos ni reiniciar el ledger
`ciencias_v4_curricularizacion_20261022` (668 invocaciones, USD 731,1485125 de reserva, cero pendientes).
Treinta filas originales tienen veto científico efectivo; el respaldo de sus propuestas corregidas no
elimina el veto del original. Los expedientes históricos siguen auditables. El código se entrega en
`feat/ciencias-v4`; el corpus privado se recupera con `gskg datos restaurar --en-repo`, mediante el recibo
`config/datos_ciencias.lock.json`. Estado, pruebas y límites: `docs/CIERRE_TECNICO.md` y
`docs/VERIFICACION_GCS.md`. Los apartados siguientes conservan el desarrollo y pipeline histórico.

## Reconstrucción V4 (2026-10-21)

El roadmap vigente para la reconstrucción está en `docs/ROADMAP.md`, la arquitectura en
`docs/ARQUITECTURA.md` y la operación en `docs/OPERACION.md`. La configuración materializada sigue en V3
hasta una migración explícita del pipeline histórico. El runtime V4 ya tiene publicación local
validada, con catálogo completo de 1.020 estados: 384 declaradas, 561 coincidencias, 68 abstenciones
y siete fuera de alcance. No confundir catálogo completo con clasificación de todas las filas.
No confundir `manifest.version` (formato) con versión curricular.
El runtime nuevo usa `motor/` y `recuperacion/`, con CLI modular en `cli/`, importaciones absolutas,
logs semafóricos y evaluación previa a seleccionar modelos o algoritmos. No se añade CI.
`curriculo/` preserva todos los campos y celdas V4; `producto/` publica generaciones aisladas y el explorador
offline. Su contrato está en `specs/16_producto_v4.md`. No publicar el catálogo piloto como completo.
`producto conocimiento` genera hipótesis sin aceptar enlaces. `producto unidades` conserva objetivos y aula;
la ejecución exige catálogo completo y correspondencia íntegra con la publicación. `alineacion` usa 29
criterios PISA/ERCE y tres lectores; su respaldo es documental y no crea `CUBRE`. Los perfiles de ERCE
son extracciones adicionales por SHA/página/región, sin sobrescribir el raw.
`ingesta/estructurados.py` hidrata DOCX/HTML por código nativo y ubicación XML/DOM; no inventar página ni
usar metadata como texto. `--coleccion paises` mantiene aparte 12 PDF con ediciones, cohortes y modalidades.
La política opcional de conocimiento fija cuatro registros ENG/SG; nunca equivale a aceptar un enlace.
`producto juicios` prepara expedientes completos y reúne cuatro lectores ciegos para conocimiento.
`producto/relaciones.py` reconstruye terminales y bloquea admisión de una colección con ciclos;
`conocimiento_publicado.py` conserva evidencia deduplicada y cierres reconstruibles. `producto-2`
exige ocho archivos, incluido `conocimiento.json` (null si no se aporta). `producto construir --conocimiento`
rehidrata fuentes y publica `RelacionCurricular` por fila, sin prerrequisitos globales. `buscar_fila`
recupera sólo vínculos admisibles de la identidad solicitada; las unidades fijan `Solicitud.fila_id` y
el Motor veta otro anclaje antes de los jueces. La publicación V4 actual conserva quince juicios reales,
dos respaldos, seis rechazos y siete abstenciones. `conocimiento-publicado-2` compone archivos originales
sin normalizar protocolos ni seleccionar rondas favorables. Revalida componentes y ciclos conjuntos.
La API `/api/v4` es local, versionada y sin generación; el grafo histórico queda separado. La autorización de clasificación se ejecutó dentro de
52 intentos nuevos/76 acumulados y USD 8 acumulados. El usuario autorizó después continuar lo pendiente
de Ciencias hasta cerrar. La unidad `unidad-fisica10-v4-20261021` ejecutó sus ocho sesiones con presupuesto
único de 64 intentos/USD 8: cuatro respaldadas, cuatro abstenciones, 58 intentos y USD 7,4261195 reservados.
La reanudación terminal consumió cero; no repetir las abstenciones para forzar acuerdo. Código de esa
ejecución archivado por SHA; ver `docs/investigacion/resultados_unidad_fisica10_v4.*`.
El escenario posterior de sesenta minutos conserva siete respaldos y una abstención: 64 intentos y
USD 10,517924 acumulados, incluidos dieciséis TransportError sin respuesta. `operacion/` permite una
recuperación explícita, única y con el mismo presupuesto, exclusivamente cuando no hubo propuestas
ni dictámenes; fija su protocolo además del entorno del motor. No se usa para repetir votos.
Una variante nueva del objetivo pendiente, en dos encuentros de sesenta minutos, obtuvo los tres
respaldos con ocho intentos/USD 1,533031 dentro de 8/USD 2. La entrega experimental conserva ocho
objetivos y nueve encuentros: `data/producto/unidades/fisica-10-entrega-experimental/`. Mantiene la
cohorte original completa y sus abstenciones. No equivale a carga oficial ni cobertura de toda la V4.
Sin fuentes de definición/dependencia se abstiene. Los grupos del contexto se reservan antes de
llenar el resto por ranking; `producto juicios medir-contexto` mide disponibilidad, no calidad semántica.
El respaldo de una relación se limita a su fila; no usarlo como verdad universal o equivalencia de grados.
El reservado de evaluación V4 ya fue abierto por el evaluador: no usarlo para ajustar prompts o ranking.
Los criterios científicos y pedagógicos se dictaminan automáticamente, con abstención cuando no alcanzan;
esto no se transforma en aprobación oficial ni en evidencia de eficacia educativa.
La selección de citas debe usar IDs de fragmentos de fuentes verificadas: el código reconstruye los literales.
Las fuentes originales y los históricos siguen siendo solo lectura.

## Qué es
Grafo de conocimiento de **Biología, Física, Química y Ciencias de la Tierra y del Espacio**
(2.°–11.°) que une la malla del MINED con los marcos internacionales (TIMSS 2027, TIMSS Advanced,
PISA 2025) y los currículos de otros países. Su propósito es **proponer una curricularización
mejor, con evidencia**, por asignatura. Visión completa: `specs/00_vision_y_alcance.md`.

Contexto: el MINED (equipo de Ciencias) entregó las mallas y el equipo GOES diseña la nueva
currícula. El trabajo previo de cobertura está en `reportes/cobertura_curricular/`.

## Antes de implementar
1. Lee `specs/README.md` y las specs que tocan la tarea. El plan con las fases está en `specs/08_plan_de_implementacion.md`.
2. Revisa si hay una skill en `.claude/skills/` para la tarea y síguela.
3. Trabaja por fase. Al cerrar una, muestra el resultado, marca ✅ en la spec 08 y haz commit.

## Estructura
- `grados/G<gg>/`: grafo de cada grado (ficha + visor HTML). Es el entregable que pidió el MINED (spec 09).
- `asignaturas/<asignatura>/`: una carpeta por disciplina. El `README.md` lo escribe el equipo;
  `ficha.md`, `brechas/` y `propuesta/` se generan.
- `config/`: reglas en YAML (mallas, asignaturas, marcos, referentes). Se cambian aquí, no en el código.
- `src/goes_science_kg/`: el paquete (ver la tabla de módulos en la spec 01).
- `data/fuentes/`: mallas del MINED y PDF externos. **SOLO LECTURA.** La malla vigente es la V3 (2026-10-13, spec 15),
  con ids estables: un tema que ya estaba en la V2 conserva su id.
- `data/interim/`: intermedios, como lotes de IA y objetivos de países.
- `data/grafo/`: el grafo (`nodos.jsonl`, `aristas.jsonl`, `manifest.json`). Se versiona.
- `reportes/cobertura_curricular/`: trabajo previo, autocontenido. **No se modifica.** Sus `input/`,
  `data/raw` y `data/referencia/externos` son enlaces simbólicos a `data/fuentes/`.
- `specs/`, `.claude/skills/`, `prompts/`.

## Reglas (no cambiarlas sin preguntar)
- Nunca modificar `data/fuentes/`, `reportes/` ni los PDF.
- **Pivote:** todo currículo se alinea contra los marcos, nunca país contra país.
- **Evidencia:** cada nodo trae su fuente (documento y página, o archivo, hoja y fila). Cada inferencia de IA
  trae confianza, justificación (≤15 palabras) y versión. Las de confianza baja van a revisión humana.
- **No inventar códigos.** Al unir lotes de IA se validan contra el catálogo.
- **Parafrasear** en español. No copiar párrafos de los PDF.
- Las reglas de cobertura, balance, profundidad, nivel cognitivo y presupuesto de
  `reportes/cobertura_curricular/CLAUDE.md` siguen vigentes.
- Las decisiones humanas (`revisado_por`) ganan sobre la IA y no se reclasifican sin preguntar.
- Pregunta antes de: agregar países fuera de `config/referentes.yaml`, cambiar el pivote de
  Química y Biología de Bachillerato (hoy ACARA Senior Secondary, spec 03), o proponer quitar temas.
- Alcance: solo ciencias. Los temas de tecnología se marcan fuera de alcance y se enlazan con `goes-techonoly-kg`.

## Convenciones
- Español en código, datos y documentos. Python 3.11+, `uv`, `ruff` (120), `pytest`.
- Rutas relativas a la raíz con `config.ruta()`. Salidas deterministas (ordenadas).
- Subagentes por lote para clasificar o alinear. La unión se hace con un script que valida.
- Excel: todo número de análisis es una fórmula. Compatible con Numbers (sin «·» en pestañas, sin CHAR(10),
  sin XLOOKUP/FILTER). Estilo 2027: encabezado verde bosque 1E4D3A y sin azul.
- Commits: `tipo(ámbito): resumen` en español. `pytest -q` en verde antes de cada commit.
- El remoto usa el alias SSH `github-goes` (`git@github-goes:carlosjimenez-arch/goes-science-kg.git`).

## Harness (Claude Code)
`.claude/settings.json` conecta hooks que aplican estas reglas solos (detalle en `.claude/hooks/README.md`):
- Al iniciar la sesión se inyecta el estado: rama, cuenta de git, decisiones sin confirmar con el MINED y etapas.
- Se bloquea leer `.env`, editar `data/fuentes/`, `reportes/`, PDF o salidas generadas (`data/grafo/`), y hacer commit
  con otra cuenta o con `ruff`/`pytest` en rojo.
- Todo gasto en Vertex (`--confirmar`, `congelar-catalogo`) pide la aprobación del usuario.
- Subagentes de lotes (`.claude/agents/`): `alineador-marcos`, `etiquetador-conceptos`, `ordenador-prerrequisitos`,
  `redactor-bloques`, `conciliador-propuestas` y `redactor-actividades` (capa pedagógica, spec 13). Úsalos en lugar de subagentes genéricos: traen su prompt y sus reglas,
  escriben solo su `salida_*.json` y, al terminar, el hook `validar_lotes.py` (SubagentStop) los devuelve a corregir si
  la salida no pasa `gskg lotes validar`. La unión la corre la sesión principal.
- Subagente `verificador-hallazgos` (solo lectura) y skills `internacional-contraste`, `calidad-grafos` y
  `decisiones-mined`.
- **Panel de expertos IA** (spec 14): `experto-biologia`, `experto-fisica`, `experto-quimica`, `experto-tierra-espacio` y
  `psicopedagogo` dictaminan las decisiones que esperaban al MINED (`gskg panel preparar|consolidar|aplicar|informe`).
  Sus dictámenes no son confirmaciones del MINED: quedan como «dictamen del panel», con evidencia, y son reversibles.
- **Bucle de fortalecimiento** (spec 14, sección 7). El subagente `refutador` impugna cada dictamen con citas literales,
  y el código verifica esas citas en la fuente. Una sonda ciega mide la estabilidad, y lo impugnado vuelve a la réplica
  del panel. Cada dictamen queda «sólido», «respaldado», «frágil» o «sin consenso»; lo frágil no se lleva al MINED como
  recomendación sin una fuente primaria.

## Comandos
```bash
uv sync --extra dev --extra pdf --extra rag --extra api
uv run gskg malla-correspondencia # malla vigente (V3) frente a la V2 → data/interim/mallas/v2_a_v3.json (spec 15)
uv run gskg temas                 # mallas → data/interim/temas.json
uv run gskg grafo construir       # grafo → data/grafo/ (falla si hay errores)
uv run gskg grafo validar         # invariantes + avisos + métricas
uv run gskg fichas                # asignaturas/<x>/ficha.md
uv run gskg grafo exportar        # data/grafo/export/grafo.graphml
uv run gskg grados construir      # grafos por grado: data/grafo/grados/ + grados/G<gg>/{ficha.md,grafo.html}
uv run gskg rag "<consulta>" --grado 7 [--asignatura biologia] [--responder] [--global]
uv run gskg evaluar-rag           # recall@k y MRR sobre data/evaluacion/rag_preguntas.json (ajuste)
uv run gskg evaluar-rag --conjunto data/evaluacion/rag_preguntas_prueba.json   # prueba independiente: no ajustar con él
uv run gskg servir                # API de lectura en http://127.0.0.1:8010/docs (grados, conceptos, propuestas, rag)
# Capa de conceptos (cada paso «preparar» genera lotes para subagentes; «unir» valida):
uv run gskg conceptos preparar-vocabulario | consolidar | preparar-etiquetado | unir-etiquetado
uv run gskg conceptos preparar-paises | unir-paises | preparar-prerrequisitos | unir-prerrequisitos
uv run gskg grados resumenes      # títulos y resúmenes de bloques temáticos (subagentes)
uv run gskg brechas               # asignaturas/<x>/brechas/
uv run gskg progresion            # asignaturas/<x>/progresion.html
uv run gskg lotes validar [--agente <subagente>]   # salidas de subagentes con las reglas de la unión
uv run gskg tutor bases|apoya|alinear|contexto|preparar-actividades|unir-actividades|validar|recorridos   # spec 13
uv run gskg tutor turno <tema> --grado g | evaluar <actividad> "<respuesta>"   # tutor y evaluador; --confirmar = Vertex
uv run gskg revision exportar|importar <csv>   # circuito de revisión con el MINED
uv run gskg revision exportar-decisiones | importar-decisiones <csv>   # confirmar con el MINED las decisiones de contenido
uv run gskg panel preparar --ronda n | consolidar --ronda n | aplicar | informe | resumen   # panel de expertos IA (spec 14)
uv run gskg bucle anclar | impugnar --vuelta k | sonda --vuelta k | cerrar-impugnacion --vuelta k   # bucle (spec 14 §7)
uv run gskg bucle replicar --vuelta k --paso p | cerrar-replica --vuelta k --paso p | solidez | cita "<fuente>" "<cita>"
# expedientes nuevos: la misma secuencia con --serie <s> en impugnar, cerrar-impugnacion, replicar y cerrar-replica
uv run gskg propuesta candidatos|simular|excel <asig> <g0> <g1>   # propuesta por ciclo (spec 06)
uv run gskg internacional extraer|etiquetar|construir   # spec 11 (Vertex AI con ADC; caché en data/interim/internacional/cache)
uv run gskg internacional --tramo 2_8 corregir-metadatos   # grados y Extension Part de los países, sin Vertex (spec 12)
uv run pytest -q
make todo                         # temas → grafo → validar → fichas, grados, brechas, progresión → internacional → pruebas + lint
make internacional-ia             # extraer + etiquetar + construir; sin --confirmar no gasta en Vertex
uv run gskg internacional congelar-catalogo <versión>   # solo para re-etiquetar a propósito (se paga completo)
make propuestas                   # simula las 11 propuestas, rehace sus Excel y asignaturas/PROPUESTAS.md
```
