# Datos de Ciencias en GCS

El repositorio contiene código, configuración, pruebas, contratos y documentación. El corpus, los PDF, las
matrices, los snapshots, los grafos, los resultados de investigación, los checkpoints, los ledgers y las
entregas viven en `gs://goes-ai-kg-artefactos/ciencias/v4/`, con objetos nombrados por SHA que nunca se
sobrescriben. La cuenta y el proyecto institucionales están en `config/almacen_ciencias.yaml`; se usa la
sesión de `gcloud`, sin copiar claves al repositorio. El `.env` es local y no forma parte del respaldo.

## Recibos

Cada componente se fija con un recibo versionado que declara URI, generación y SHA-256 de sus objetos:

| Recibo | Contenido |
|---|---|
| `config/datos_ciencias.lock.json` | Corpus completo: fuentes, publicación `producto-4`, campañas, ledgers, checkpoints y progresión |
| `config/materiales_ciencias.lock.json` | Biblioteca docente vigente (3.837 registros) que sirve la aplicación |
| `config/clases_ciencias.lock.json` | Entrega descargable de guiones (Markdown docente y de estudiante, fuentes y auditorías) |
| `config/complementos_ciencias.lock.json` | Recibo preparado localmente; se versionará tras publicar y verificar el JSON de anexos y evaluaciones dentro del corpus fijado |
| `config/materiales_preparaciones.lock.json` | Biblioteca de preparaciones (2.867 registros); sólo para recompilar guiones |

El paquete del corpus conserva las rutas originales y un manifiesto con tamaño y SHA-256 de cada archivo; en
GCS hay además un inventario JSON y un descriptor independientes. Las bases SQLite se respaldan con su API de
copia consistente, incluidas las transacciones confirmadas en WAL; locks, WAL, SHM y cachés no se restauran
como archivos sueltos. Identidades del corte vigente: [verificación GCS](VERIFICACION_GCS.md).

## Comandos

| Comando | Efecto |
|---|---|
| `gskg datos estado` | Compara corpus, bibliotecas, guiones y complementos con sus recibos, sin descargar |
| `gskg datos sincronizar` | Descarga lo que falte de cada componente fijado; rechaza estados parciales o divergentes en vez de sobrescribir |
| `gskg datos verificar` | Coteja por SHA el corpus local con el inventario remoto (código 1 si algo difiere o falta) |
| `gskg datos inventario` | Lee el inventario remoto (ruta, tamaño y SHA) sin descargar el corpus |
| `gskg datos publicar --trabajo <carpeta>` | Empaqueta, sube, restaura en la carpeta, compara y sólo entonces adopta el recibo nuevo |
| `gskg datos retirar <plan> --recibo <recibo>` | Restaura de nuevo desde GCS y retira sólo originales sin cambios desde el plan |
| `gskg servir --sincronizar` | Sincroniza antes de servir; `make producto` hace lo mismo tras instalar |

`gskg datos restaurar --en-repo | --destino <carpeta>` restaura una generación exacta; `preparar` y `subir` son
los pasos sueltos que `publicar` encadena. Ninguno de estos comandos invoca modelos.

Los complementos se compilan con `gskg clases complementaria`, que fija el SHA del JSON publicado en su recibo.
Si un consumidor ya tiene el corpus anterior y le falta ese JSON, `datos sincronizar` recupera únicamente el
archivo aprobado desde una restauración aislada del corpus vigente y comprueba su SHA. Conserva los demás
datos locales; rechaza un JSON existente divergente y las rutas que salgan de `complementaria/publicacion/`.
El recibo de complementos debe acompañar al recibo de corpus que contiene ese archivo.

## Consumidor nuevo

Requisitos: Python 3.11+, `uv` y `gcloud` autenticado con la cuenta GOES y acceso de lectura al bucket. Si
`gcloud storage` falla con Python 3.14, el código elige un Python 3.13/3.12/3.11 instalado o respeta
`CLOUDSDK_PYTHON`.

```bash
uv sync --frozen --all-extras
uv run --frozen gskg datos sincronizar
uv run --frozen gskg servir
```

La descarga verifica el SHA del paquete y de cada archivo antes de incorporar las raíces y rechaza una raíz que
ya exista para no perder trabajo local. Los datos recuperados quedan ignorados por Git; no usar `git add -f`
sobre esas rutas. Al reponerlos en el repositorio también se verifican los bytes de los SQLite y se migra
únicamente la identidad física del ledger en `checkpoint_presupuestos` (una copia descargada tiene otro inodo),
con registro en `data/operaciones/migraciones/restauracion-*.json`. El ledger, las reservas, las respuestas y
los identificadores de presupuesto se conservan; restaurar no autoriza repetir llamadas ni reiniciar contadores.

## Datos nuevos

Todo dato o derivado nuevo se publica con `gskg datos publicar --trabajo <carpeta fuera del repositorio>` y se
adopta su recibo. `config/datos_externos.yaml` declara las raíces y patrones; el plan fija la selección concreta,
incluidos los archivos no versionados, y deja fuera código y credenciales. Antes de publicar hay que terminar
las escrituras de los procesos que usan esas raíces. Cada escritura comprueba proyecto, acceso uniforme y
prevención efectiva de acceso público, y crea objetos nuevos sin sobrescribir generaciones.

Adoptar un recibo es un cambio de código: se revisa y se confirma con la identidad GOES. El recibo anterior y
sus objetos siguen disponibles por generación. El inventario permite recuperar la procedencia exacta, pero no
equivale a aprobación curricular.

## Alcance de publicación

El remoto `carlosjimenez-arch/goes-science-kg` es público. Autorizar commits no autoriza exponer el corpus
institucional. La rama de código no debe tener como ancestro un commit que contenga matrices, snapshots o
evidencias completas, aunque después se borren. No se usa push forzado ni se reescribe la historia publicada;
retirar datos del checkout no borra objetos de commits anteriores. No se copian credenciales, `.env`, datos de
estudiantes ni bases SQLite a la rama pública. Publicar los insumos requiere una decisión explícita de alcance.

La suite integral necesita el corpus sincronizado. Sin él, la CI y los contratos portables usan fuentes
sintéticas que incluyen fallos y falsificaciones y prohíben proveedores remotos; no equivalen a la validación
integral sobre los 1.020 registros originales.
