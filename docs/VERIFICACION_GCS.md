# Verificación de recuperación de Ciencias V4

## Respaldo vigente · 27 de octubre de 2026

Generación publicada a partir del ZIP preparado y autorizado, con las funciones de subida y restauración de
`gskg datos publicar`: crea objetos nuevos, descarga por generación, restaura en una carpeta de trabajo y
compara el inventario completo antes de adoptar el recibo. Incluye la capa complementaria cerrada:
108 revisiones iniciales, 105 revisiones finales, originales archivados,
correcciones trazables, informe de observaciones y publicación aprobada. Los 862 guiones de la entrega
`e4b32786…` y los 108 expedientes originales mantienen su identidad.

| Elemento | Identidad comprobada |
|---|---|
| Archivos | 30.956 |
| Bytes originales / comprimidos | 4.699.352.020 / 1.710.639.459 |
| SHA del ZIP | `2ceaf1f0541f09ae4749cc76c89578072dabb34e55d169d79c81b63d71cbdf56` |
| Generaciones ZIP / inventario / descriptor | `1793153028994446` / `1793153096141393` / `1793153105197377` |
| Huella del inventario | `64e02c763887f1cce7ac216f87fbdeee8bae94633a8351234e95e35a20350a85` |
| Complementos aprobados | 819 anexos + 97 evaluaciones; 43 anexos + 11 evaluaciones retenidos |
| SHA del JSON de complementos | `7710e8383cc6ecad2057911855a3c3f443c0790a6bf66606d6bafc536d475b7d` |
| Identidad del ledger en el recibo | nombre, dispositivo e inodo; sin ruta |
| Consumo conservado | 4.294 llamadas de la campaña de guiones; USD 3.219,54 de reserva; sin llamadas nuevas a Vertex |

Cinco recibos versionados fijan corpus, biblioteca docente (`8af1b65d…`, 3.837 registros), guiones
(`e4b32786…`, 862 + 108), preparaciones (`5b64ee…`) y complementos (`f69e7739…`). Los datos y las
evidencias completas permanecen fuera de Git. Los recibos y este documento conservan las identidades de
recuperación. La restauración no amplía presupuestos ni modifica IAM.

**Consumidor aislado sin datos.** Se creó una carpeta nueva con la configuración y los recibos vigentes,
usando el código de esta revisión. `Sincronizador.sincronizar()` restauró todo desde GCS en
76,87 s; la verificación posterior dio **30.914 archivos idénticos por SHA y
42 SQLite operativos, cero diferencias y cero faltantes**. Los cinco componentes quedaron disponibles.
Se comprobaron respuestas 200 de `/health/live`, `/health/ready`, resumen, lista, fuentes y detalles de
clase/unidad de `/api/v4/complementos`; los conteos e identidad coincidieron con el recibo. Los
916 detalles aprobados respondieron 200 y los 54 retenidos, 404.
La consulta declara cero llamadas a modelos por petición. Esta comprobación usó un consumidor
sin datos con el código actual; no se presenta como una segunda ejecución completa de pruebas en un checkout Git.

**Controles de código.** Suite local completa: **1.740 pruebas aprobadas, cero fallos y cero omitidas**;
cobertura de líneas 79,63 % (19.427/24.396).
Ruff, auditoría de módulos, seis pruebas JavaScript y revisión independiente de publicación/restauración
aprobados. La revisión detectó y corrigió la comparación de roles: `codex-corrector-c` y `codex-revisor-c`,
así como el alias histórico `codex-root`, identifican al mismo actor y no cuentan como revisión independiente.
Fecha, denominadores y huella del código están en [la medición](badges/medicion.json).

**Respaldo anterior.** La generación `797eb37b…` del 25 de octubre conserva 29.415 archivos, las correcciones
R23 y el libro de especialistas. Su ensayo en checkout limpio del 26 de octubre pasó 1.718 pruebas y verificó
29.373 archivos y 42 SQLite. Sigue disponible por generación; no se sobrescribió ni eliminó. Las copias de
bibliotecas y SQLite reemplazadas permanecen en `respaldos/65f4ebeb….zip`, con manifiesto verificado.

**Retiro local.** `gskg datos retirar <plan> --recibo config/datos_ciencias.lock.json` vuelve a restaurar el recibo
completo, comprueba que los datos locales no cambiaron desde el plan y sólo entonces retira los montajes.
No se ejecutó un retiro como parte de este cierre.

## Procedimiento

Cada publicación comprueba, antes de escribir, la identidad del proyecto, el acceso uniforme (UBLA) y la
prevención efectiva de acceso público; crea objetos nuevos con precondición de generación cero y los relee por
generación y SHA. No cambia IAM.

Para repetir la verificación en un checkout nuevo, sin datos:

```bash
git worktree add <carpeta> feat/api
cd <carpeta>
uv sync --frozen --all-extras
uv run --frozen gskg datos sincronizar
uv run --frozen gskg datos verificar
uv run --frozen gskg producto validar
uv run --frozen pytest -q
```

`gskg datos verificar` termina con código 1 si un archivo difiere o falta. Las bases SQLite operativas en WAL se
respaldan como copia consistente y se cuentan aparte. Restaurar no invoca modelos ni habilita gasto: el
punto mínimo de consumo está fijado en la configuración y un respaldo anterior no rebaja el contador.
[Procedimiento operativo de datos](DATOS_EXTERNOS.md).
