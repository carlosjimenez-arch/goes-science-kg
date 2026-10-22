# Continuidad · GOEs AI · feat/api

Corte: 22 de octubre de 2026. El estado vigente se concentra en [README](README.md),
[documentación](docs/README.md) y [auditoría de esta rama](docs/auditoria/REVISION_API_2026.md).

La aplicación usa el snapshot V4 `e92bc700d78f0f559671acc62f559f9e5176b09c3341a47c575c640195022008`:
1.020 originales, 1.013 propuestas de Ciencias, siete filas fuera de alcance y 108 unidades.
Conserva treinta alertas científicas de los originales. Las propuestas corregidas no levantan sus vetos.

La rama `feat/api` contiene el refactor de consultas y publicación, índices, contratos de respuesta,
docstrings en inglés, formato, controles de calidad y documentación. El diseño conserva el CSS del
HTML aportado. La API de referencia `eor-api` está pendiente de acceso por macOS.

Los extractores `ingesta/extraccion.py` y `ingesta/estructurados.py` conservan sus bytes anteriores:
son parte de la identidad de evidencia publicada. No formatearlos ni cambiar sus docstrings sin una
migración explícita. El refactor cambia las huellas de los workflows; no reanudar presupuestos antiguos
con el código nuevo ni repetir votos para resolver incompatibilidades.

El ledger `ciencias_v4_curricularizacion_20261022` conserva 668 invocaciones y
USD 731,1485125 de reserva conservadora, sin pendientes. No es factura. La consulta no gasta modelos.
El corpus está restaurado localmente, ignorado por Git y recuperable mediante
`config/datos_ciencias.lock.json`. No repetir restauración sobre rutas existentes.

Las métricas de esta entrega se generan en [medicion.json](docs/badges/medicion.json).
La CI portable se ejecuta al publicar `feat/api`; su estado remoto se consulta desde el badge del
README. El usuario autorizó el commit y envío de esta rama tras el cierre de QA. No se repitieron
campañas. La aprobación institucional y el piloto educativo son procesos separados.

Al preparar este envío, `origin/feat/ciencias-v4` avanzó a
`663d071d31bc7e4689f6b04f60ee16f3b24589f3` con materiales docentes y guiones de clase. Esas
funcionalidades están en otra rama y no pertenecen a la huella de código validada aquí. La entrega
integral exige integrar ambas líneas y repetir la validación sobre el árbol resultante; esta rama
constituye una entrega técnica verificada para revisión y piloto controlado.

El [QA posterior independiente](docs/auditoria/QA_SEGUNDA_REVISION.md) revisó el conjunto del repo y
motivó correcciones en el respaldo de assets, las respuestas tardías de briefs, las exportaciones
Excel, el aislamiento de alertas por base y la reserva de embeddings entre procesos. No se migraron
ledgers ni se reanudaron experimentos para probarlas.
