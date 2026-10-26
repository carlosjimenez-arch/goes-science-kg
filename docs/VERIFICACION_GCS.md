# Verificación de recuperación de Ciencias V4

## Respaldo vigente · 25 de octubre de 2026

Generación publicada con `gskg datos publicar` (empaqueta, sube, restaura en una carpeta de trabajo y compara
antes de adoptar el recibo). Agrega la revisión directa de los 968 guiones, las correcciones R23, el libro para
especialistas, los checkpoints revinculados a la identidad del ledger sin ruta y los registros operativos con
rutas de la estación sustituidas por rutas del repositorio (`data/operaciones/redaccion_rutas_locales_20261025.json`).

| Elemento | Identidad comprobada |
|---|---|
| Archivos / bases SQLite | 29.086 / 44 |
| Bytes originales / comprimidos | 4.530.002.344 / 1.604.162.276 |
| SHA del ZIP | `20c6e813fc23ff123387c08a4525fbaff8b63071b144510297956cfe129bda81` |
| Generaciones ZIP / inventario / descriptor | `1792987241757698` / `1792987298254823` / `1792987307641831` |
| Huella del inventario | `e9e75a3fcb13a53860d179343f0ac903da79aefc7d88cf1df09e1dbd44d48ddb` |
| Identidad del ledger en el recibo | nombre, dispositivo e inodo; sin ruta |
| Consumo conservado | 4.294 llamadas de la campaña de guiones; USD 3.219,54 de reserva; sin reinicio |

Recibos complementarios: biblioteca `8af1b65d…` (3.837 registros), entrega de guiones `e4b32786…` (862 guiones
y 108 unidades, todos con revisión directa aprobada) y biblioteca de preparaciones `5b64ee…`. Las copias
locales de la biblioteca y la entrega se retiraron y se descargaron del bucket con `gskg datos sincronizar`.
Las copias de bibliotecas y SQLite reemplazadas que estaban fuera del repositorio se subieron como
`respaldos/65f4ebeb….zip`; su manifiesto se verificó tras descargarlo.

**Consumidor nuevo (commit `6fd6be2`).** En un `git worktree` limpio sin datos, `gskg datos sincronizar` bajó todo
del bucket en 67 s; `gskg datos verificar` dio 29.044 archivos idénticos por SHA y 42 SQLite operativos, sin
diferencias. La suite completa pasó **1.705 pruebas sin omisiones**.

Las generaciones anteriores siguen en el bucket por su generación; no se sobrescriben ni se eliminan. Su
registro detallado (identidades, ensayos y suites de cada corte) está en el historial de Git (commit `022efed`).

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
