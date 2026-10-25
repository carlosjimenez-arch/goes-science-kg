# Contribuir a GOEs Science KG

GOEs · Departamento de AI · Gobierno de El Salvador · 2026.

Instalar el entorno reproducible con `uv sync --frozen --all-extras`. Mantener Python 3.11 o superior,
imports absolutos, tipado explícito en fronteras y docstrings en inglés. El contenido curricular,
los mensajes de la aplicación y la documentación operativa se mantienen en español.
Las convenciones completas y sus excepciones están en [Calidad](docs/CALIDAD.md).

Antes de entregar cambios:

```bash
make lint
make cobertura
make pruebas-js
make auditoria
git diff --check
```

La suite completa necesita el corpus privado restaurado. La CI ejecuta un conjunto portable con
fuentes sintéticas, sin credenciales; sus resultados no equivalen a la suite integral local.
Consultar [operación](docs/OPERACION.md) y [datos externos](docs/DATOS_EXTERNOS.md) antes de restaurar.

Las fuentes, publicaciones, dictámenes y ledgers existentes son evidencia. Cambiar un docstring en un
extractor firmado puede invalidar publicaciones: `ingesta/extraccion.py` e `ingesta/estructurados.py`
conservan sus bytes históricos, igual que `clases/` y `cli/clases.py` mientras la campaña de guiones siga
abierta. Una modificación exige una migración explícita y otra publicación verificada. No cambiar hashes esperados para hacer pasar una comprobación.

Los tests deben inyectar proveedores simulados. Ninguna comprobación de calidad autoriza llamadas
pagadas, reejecución de jueces ni reinicios de presupuesto. Las correcciones de comportamiento
requieren una regresión que reproduzca el fallo; el formateo y la documentación no necesitan pruebas
que repitan literalmente la implementación.

Los cambios se revisan sobre una rama propia. En este trabajo la rama solicitada es `feat/api`.
No incorporar corpus, `.env`, credenciales, SQLite, PDF ni Excel al historial público.
