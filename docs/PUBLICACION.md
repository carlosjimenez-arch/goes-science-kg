# Alcance de publicación y reproducción

Estado de mantenimiento: `feat/api`. Los resultados de pruebas y cobertura vigentes se consultan
en [Calidad](CALIDAD.md) y [medicion.json](badges/medicion.json). Las verificaciones de entregas
anteriores que siguen se conservan con su alcance original.

El remoto `carlosjimenez-arch/goes-science-kg` es público. Autorizar commits no implica autorizar
la exposición del corpus institucional completo. La rama de código se construye desde la base pública
e incorpora código, pruebas, configuración, prompts y documentación. No debe incluir como ancestro
un commit local que contenga las matrices nuevas, snapshots o evidencias completas, aunque después
se borren sus archivos.

El producto V4 descrito en esta documentación existe en el entorno institucional local. Las rutas
`insumos/v4`, `data/producto`, checkpoints y reportes JSON nuevos **no se distribuyen en la rama de
código**. Los enlaces a estos resultados son localizadores para ese entorno; no prometen que los
archivos estén en GitHub. La historia ya publicada no se reescribe; el nuevo árbol retira también los datos históricos tras verificar su recuperación privada.

Para reproducir la prueba completa se ejecuta `gskg datos restaurar --en-repo`, que recupera los once insumos originales, procedencia,
catálogo y artefactos de las cohortes desde el entorno institucional autorizado, conservando sus SHA.
Las referencias públicas se descargan por los comandos de ingesta con sus catálogos fijados. Una
descarga pública no reconstruye los dictámenes originales; sus checkpoints y presupuestos se conservan
por separado. No se copian credenciales, `.env`, datos de estudiantes ni bases SQLite a la rama pública.

```bash
uv sync --locked --all-extras
uv run pytest -q
uv run ruff check src tests
```

La batería completa usa el corpus local. Para verificar los contratos nuevos sin ese corpus pueden
ejecutarse los casos sintéticos de alineación, archivo y CLI:

```bash
uv run pytest -q tests/test_alineacion.py tests/test_archivo_alineaciones.py \
  tests/test_cli_alineacion.py tests/test_cli_referencias_colecciones.py
```

Estos casos crean Excel y PDF temporales, incluyen fallos y falsificaciones y prohíben proveedores
remotos. No equivalen a la validación integral sobre los 1.020 registros originales.

La publicación pública de los insumos requiere una decisión explícita de alcance. Un envío de código
debe verificar que su árbol no contiene el corpus privado y que ningún ancestro nuevo contiene
los insumos o resultados retenidos. El retiro autorizado de los datos se documenta en DATOS_EXTERNOS.md. No usar un push forzado ni reescribir la base pública.
