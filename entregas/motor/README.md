# GOES Science Content · entrega inicial al motor

Primera entrega técnica del plan unificado de la [spec 16](../../specs/16_contenido_motor.md), corte 2026-10-15.
La carpeta [`0.1.0/`](0.1.0/LEEME.md) se puede validar e importar sin las fuentes Excel del productor.
El catálogo completo no implica contenido de aula completo: se habilitan **consulta y autoría asistida**.
El uso en aula permanece deshabilitado en todo el contrato inicial.

| Disponible | Cantidad |
|---|---:|
| Temas V3 con identidad y fuente exacta | 935 |
| Temas en el alcance de Ciencias | 920 |
| Nodos / relaciones del grafo principal | 3.303 / 18.177 |
| Clasificaciones del análisis V3, con procedencia separada | 1.123 |
| Paquetes existentes de Física y Química de 9.°–11.° | 230 |
| Componentes completos exportados | 1.547 |
| Componentes permitidos para autoría asistida | 1.534 |
| Componentes retenidos de autoría | 13 |
| Referencias numéricas curadas y localizadas | 0 |
| Componentes habilitados para aula | 0 |

Los 13 retenidos son seis casos pedagógicos pendientes, dos actividades dependientes de uno de ellos,
cuatro adiciones descartadas y una nota frágil de esterificación. Se conservan para consulta y trazabilidad.
La exportación abarca 23 de los 24 refuerzos revisados: son los enlazados desde estos 230 paquetes; no sustituye
el catálogo global de refuerzos. Las propuestas GOES aptas se excluyen por defecto del perfil de autoría;
`--incluir-propuestas` permite seleccionarlas sin convertirlas en adopciones del MINED.

## Comprobar y consumir

```bash
uv run gskg motor validar entregas/motor/0.1.0
uv run gskg motor importar entregas/motor/0.1.0
uv run gskg motor consultar G10-FIS-U7-7.9 --perfil autoria
uv run gskg motor consultar NM26-G10-FIS-U4-4.1 --perfil autoria
```

El almacén local de prueba queda en `data/interim/motor/consumidor/`, excluido de git. Una importación repetida
reutiliza la misma entrega. `gskg motor activar <id_entrega>` activa una versión ya importada y validada, incluida
una anterior. Para usar otra ubicación, agregar `--almacen <carpeta>` a importar, consultar o activar.

[`EJEMPLO_CONSULTA_AUTORIA.json`](EJEMPLO_CONSULTA_AUTORIA.json) muestra una respuesta real para el procedimental
actual 4.1 de Física 10.°; su id heredado es `G10-FIS-U7-7.9`. Se puede consultar por ese id o por su alias exacto
`NM26-G10-FIS-U4-4.1`. El orden vigente siempre se lee del campo `orden` y de la fuente.

## Qué se corrigió al validar

- Se incorporaron insumos seleccionados del análisis independiente y se comprobó una correspondencia exacta
  de 935 temas en los 11 libros; no se cruzaron por similitud de títulos ni sustitución de prefijos.
- La extracción completa encontró nueve temas con diferencias en campos combinados o asociados respecto
  del grafo. Las columnas oficiales completas y la extracción anterior se mantienen separadas y comparables.
- Se corrigió el orden de las unidades: se usa el orden real de libros, hojas y filas, no el alfabético.
- Se verifica la identidad después de copiar, se publica por renombrado y se activa con un puntero atómico.
  Una copia alterada o un fallo de activación no cambia la versión activa.
- Los permisos se recalculan por componente y se propagan a sus dependencias. Los reemplazos elegidos por el
  responsable permanecen separados de los alias de identidad.

La evidencia de los cinco ciclos está en [`VALIDACION_5_CICLOS.json`](VALIDACION_5_CICLOS.json). Incluye los
límites del resultado: las pruebas técnicas no verifican la corrección científica de cada actividad ni su eficacia
en el aula. Las 520 relaciones de confianza baja conservan sus avisos; no se promovieron por exportar.

## Siguiente entrega de contenido

El expediente de la unidad candidata **Física 10.°, «4. Trabajo, energía y momento»** está en
[`UNIDAD_PILOTO_FISICA_10.json`](UNIDAD_PILOTO_FISICA_10.json) y sus hallazgos en
[`UNIDAD_PILOTO_FISICA_10.md`](UNIDAD_PILOTO_FISICA_10.md). Conserva los cinco momentos de la malla,
los componentes disponibles y los pendientes; los campos de selección, tiempos observados y revisión humana
se mantienen vacíos. Es un expediente de autoría externo al contrato, no una unidad aprobada para el motor.

Para preparar otro expediente sin sobrescribir decisiones de autoría:

```bash
uv run python scripts/preparar_unidad_motor.py entregas/motor/0.1.0 \
  --grado 10 --asignatura fisica --unidad '4. Trabajo, energía y momento' --salida /tmp/unidad.json
```

La próxima tarea es seleccionar y adaptar actividades, localizar referencias científicas y diseñar evidencias e
instrumentos de evaluación. Después corresponden revisión científica y didáctica humana, ensayo de sesiones
de 55 minutos e integración con el motor real. Los pendientes globales de la spec 15 y las decisiones del MINED
siguen abiertos.
