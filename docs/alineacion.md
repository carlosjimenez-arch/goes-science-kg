# Alineación documental reproducible

El grupo `gskg alineacion` compara **una fila V4 y un referente operativo** con evidencia original.
Preparar un par y verificar referentes son operaciones locales. La evaluación remota requiere añadir
`--ejecutar`; sin esa opción no se crea un proveedor ni un registro de gasto.

Los únicos resultados del motor son `respaldo_documental_automatico`, `no_respaldado` o `abstencion`.
Describen lo que respalda la documentación examinada. No acreditan enseñanza, desempeño estudiantil,
aprendizaje, equivalencia entre edades/grados ni cobertura internacional de la malla. Estos comandos
no crean relaciones `CUBRE` ni cambian el grafo. El grupo es independiente del antiguo comando `alinear`.

## Referentes y extracción

```bash
.venv/bin/gskg alineacion listar-referentes --marco ERCE
.venv/bin/gskg alineacion validar-referentes
```

Ambos comandos guardan JSON por defecto en `data/producto/alineaciones/` y aceptan `--salida ruta.json`.
El primero lista las paráfrasis y sus poblaciones, fuentes, páginas y límites. El segundo verifica SHA,
versión, páginas y anclas, e incluye los perfiles usados y `huella_extraccion`. La huella incorpora la
configuración de regiones, biblioteca, opciones y código del extractor: un cambio obliga a revisar
la identidad de la extracción y de cualquier ejecución que dependa de ella.

Las páginas ERCE 11 y 19 usan `PaginasConPerfil`, con regiones verificadas visualmente y orden explícito.
Las demás páginas conservan la lectura documental habitual. La extracción Pypdf original y su
manifiesto no se reemplazan. Una huella o un ancla válidas sólo prueban procedencia y localización;
no son un dictamen de alineación. Alcance y auditoría de los 29 referentes:
[referentes operativos 2026](investigacion/referentes_operativos_2026.md).

## Preparar un par real sin modelo

Ejemplo verificado con sexto de primaria, unidad de fluidos, fila física 3 y contenido «Fluidos estáticos»:

```bash
.venv/bin/gskg alineacion preparar \
  'CURRICULO:V4:4321beb24582b990714504cd8394e5be9780f6e0e90fd7282afbf383fa1853bc' \
  'LOCAL:erce2019_dom_energia_materia' \
  --salida data/producto/alineaciones/par_preparado.json
```

La salida conserva objetivo, evidencia, fragmentos seleccionados y sus identidades, referente, población,
grado declarado, SHA del currículo, huella del referente y de extracción. Se vuelve a leer el contenido de
las celdas y páginas originales: el texto de búsqueda no se convierte en evidencia por sí solo. También
se aplican las alertas científicas localizadas del repositorio. Una falta de integridad, un pasaje ilegible
o un presupuesto de contexto insuficiente pueden producir abstención antes de cualquier modelo.

La demostración preparada **no ha sido evaluada por modelos** y no se presenta como relación respaldada.
En la ejecución local de esta entrega, del 21 de octubre de 2026, quedó en estado `preparado`, con 15
evidencias, 17 fragmentos, cero llamadas y ningún motivo de abstención. El archivo incluye evidencias
completas para auditoría; su tamaño no representa el payload enviado a un modelo, cuyo límite se comprueba
por separado en el motor.

## Plan y evaluación explícita

`evaluar` prepara el mismo par y muestra el proyecto, región, tres roles/modelos, límite de llamadas y
reserva máxima configurados. Su comportamiento predeterminado sigue siendo local:

```bash
.venv/bin/gskg alineacion evaluar \
  'CURRICULO:V4:4321beb24582b990714504cd8394e5be9780f6e0e90fd7282afbf383fa1853bc' \
  'LOCAL:erce2019_dom_energia_materia' \
  --salida data/producto/alineaciones/plan.json
```

Para habilitar la ejecución remota del par se añade `--ejecutar`. Un ID estable permite reanudar sus
checkpoints y conservar su presupuesto:

```bash
.venv/bin/gskg alineacion evaluar \
  'CURRICULO:V4:4321beb24582b990714504cd8394e5be9780f6e0e90fd7282afbf383fa1853bc' \
  'LOCAL:erce2019_dom_energia_materia' \
  --ejecutar --ejecucion ejemplo-fluidos-erce-01 \
  --max-llamadas 3 --max-usd 1.5 \
  --salida data/producto/alineaciones/resultado.json
```

Ese último ejemplo se documenta para uso reproducible: **no se ejecutó contra GCP durante esta entrega**.
Con el flag, Vertex recibe los fragmentos curriculares y del referente seleccionados. No hay entrada
de datos de estudiantes en estos comandos.

Antes de crear el proveedor se validan los destinos del resultado, ledger, checkpoints y log mediante
`archivos.destino_generado`. Se guarda una preparación revisable mediante `escribir_texto_generado` antes
de cualquier llamada. Las salidas en fuentes, insumos, código, configuración, grafo o evaluación protegida,
y los archivos de salida que son enlaces simbólicos, se rechazan. Al completar se reemplaza atómicamente
la preparación por el resultado y su consumo. Si una excepción capturada o una interrupción de teclado
detiene el workflow, el archivo recoge ese estado y el consumo disponible en el ledger. Una terminación
forzada del proceso puede dejar sólo la preparación y el ledger durable, que conserva las reservas.
El ID de ejecución ya está guardado en esa preparación para poder localizar y reanudar sus checkpoints.

Los tres roles son científico, psicopedagogo y adversarial, con lecturas ciegas del mismo par. El cierre
requiere las condiciones del motor para sus tres lecturas; una discrepancia o insuficiencia no se resuelve
por mayoría. El ledger es el único registro compartido `data/operaciones/registro.sqlite`; los checkpoints
de alineación tienen un SQLite independiente. La huella de entorno incluye corpus, modelos, configuración,
extracción, código y contratos. Reutilizar el ID con otro par, entorno o presupuesto no reasigna el checkpoint.
La validación también contrasta la identidad real del modelo por rol y reconstruye el resultado terminal
desde la preparación, las tres lecturas y sus citas. Un terminal sin preparación o una bandera positiva
alterada se rechazan antes de reutilizar el checkpoint. Esta comprobación no consume nuevos modelos.

## Configuración y salidas

`config/alineacion.yaml` fija la versión V4, rutas de fuentes, alertas y referentes, límite de contexto,
concurrencia y presupuesto. Hereda proyecto, región, modelos y tarifas de `config/motor.yaml`, y mapea
explícitamente los tres roles de alineación. No duplica credenciales. Los valores predeterminados son tres
llamadas, reserva máxima de USD 1,50 y cero reintentos del proveedor. La reserva no es un cargo facturado.
Las opciones `--max-llamadas` y `--max-usd` se validan antes de crear un modelo y forman parte del entorno
de una ejecución durable.

La operación correcta termina con código 0, incluso si el dictamen documental es `no_respaldado`.
La abstención termina con código 2 y un JSON que explica sus motivos; Typer también utiliza código 2
para argumentos inválidos. En ese último caso no se genera una decisión documental.

Artefactos locales comprobados:

| Archivo | Contenido y límite |
| --- | --- |
| `data/producto/alineaciones/par_preparado.json` | Par real de fluidos y dominio ERCE; preparación, cero modelos, sin dictamen |
| `data/producto/alineaciones/auditoria_referentes.json` | 29 referentes con procedencia y anclas verificadas mediante el puerto con perfiles; cero modelos |

Ambos artefactos registraron `huella_extraccion`
`9af72ec5e6a321a455fab8acc3f034a10d12a9d2caca7664ddfe2609cc44b516` en la generación comprobada.
Si cambia el código auditado del extractor, la biblioteca o el perfil, se regeneran mediante los comandos
anteriores; no se traslada esa identidad a una versión nueva por conveniencia.

## Verificación de la interfaz

```bash
.venv/bin/pytest -q tests/test_cli_alineacion.py
.venv/bin/ruff check src/goes_science_kg/cli/alineacion.py tests/test_cli_alineacion.py
```

Las 19 pruebas usan Excel y PDF sintéticos, perfiles, ledger y checkpoints locales y un proveedor simulado.
Comprueban preparación sin remoto, salidas protegidas, identidad, límites, tres roles, reanudación sin
llamadas adicionales, interrupción con consumo persistido y auditoría perfilada. No son una evaluación
de eficacia de aprendizaje ni un benchmark real del proveedor.

`tests/test_alineacion_estado.py` añade 17 casos adversariales: modelos ajenos, terminales adulterados,
preparación ausente y una modificación real del checkpoint SQLite que intenta promover un rechazo a
respaldo. El terminal válido sigue siendo reutilizable sin nuevas llamadas.
