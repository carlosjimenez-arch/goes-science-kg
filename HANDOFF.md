# Continuidad · GOEs AI · feat/api

Corte: 22 de octubre de 2026. El estado vigente se concentra en [README](README.md),
[documentación](docs/README.md) y [auditoría de esta rama](docs/auditoria/REVISION_API_2026.md).

La aplicación usa el snapshot V4 `e92bc700d78f0f559671acc62f559f9e5176b09c3341a47c575c640195022008`:
1.020 originales, 1.013 propuestas de Ciencias, siete filas fuera de alcance y 108 unidades.
Conserva treinta alertas científicas de los originales. Las propuestas corregidas no levantan sus vetos.

La rama `feat/api` contiene el refactor de consultas y publicación, índices, contratos de respuesta,
docstrings en inglés, formato, controles de calidad y documentación. El diseño conserva el CSS del
HTML aportado. La API de referencia `eor-api` ya se revisó tras recuperar el acceso local;
la [adaptación](docs/REFERENCIA_EOR_API.md) documenta patrones y decisiones propias de GOEs.

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

El [QA posterior independiente](docs/auditoria/QA_SEGUNDA_REVISION.md) revisó el conjunto del repo y
motivó correcciones en el respaldo de assets, las respuestas tardías de briefs, las exportaciones
Excel, el aislamiento de alertas por base y la reserva de embeddings entre procesos. No se migraron
ledgers ni se reanudaron experimentos para probarlas.

La revisión posterior al PR añade observabilidad HTTP local, 49 contratos de `.gitignore` y una
huella de métricas que incluye las políticas de calidad. Se mantiene el alcance Ciencias confirmado
por el usuario.

La revisión automática no constituye aprobación institucional ni eficacia de aprendizaje medida.
La calibración independiente y el piloto de aula son evaluaciones posteriores, no estados de los agentes.


La entrega posterior de biblioteca docente conserva 2.867 registros, incluidos 1.013 paquetes
V4 por objetivo, 108 por unidad y el material histórico sin migrar sus dictámenes.
Restaurar con `gskg materiales restaurar`; consultar `/api/v4/materiales` y su OpenAPI.
La preparación reutiliza textos revisados y no consume Vertex. Son materiales para montar
clases; no se presentan como guiones completos nuevos para todos los objetivos.
[Detalle, almacenamiento y pruebas](docs/MATERIALES_DOCENTES.md).
