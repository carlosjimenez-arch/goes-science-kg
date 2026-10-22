# Ciencias V4 · cierre técnico del 22 de octubre de 2026

El producto técnico está terminado. La rama de entrega es `feat/ciencias-v4`; los commits se envían con
la identidad GOES configurada. No aplicar instrucciones de Matemáticas a este repositorio.

- Selección estable `producto-4`: 108 unidades, 1.013 propuestas de Ciencias y siete filas fuera de
  alcance preservadas, sobre 1.020 originales de once matrices y 126 hojas.
- Snapshot: `e92bc700d78f0f559671acc62f559f9e5176b09c3341a47c575c640195022008`.
- P6 resolvió diez incidencias; P7 corrigió un falso positivo adicional con cuatro votos nuevos.
  Se conservan todos los antecedentes, rechazos, abstenciones y fuentes originales.
- Contador `ciencias_v4_curricularizacion_20261022`: 668 llamadas, 633 completadas, 35 fallidas,
  cero pendientes, USD 731,1485125 de reserva conservadora. No es factura. No reiniciar ni revotar.
- Hay treinta filas originales con veto científico efectivo. Corregir una propuesta no habilita el
  original erróneo. Los expedientes históricos permanecen auditables sin habilitar generación nueva.
- El respaldo privado de 7.580 archivos y siete SQLite se restauró dos veces desde GCS. Once terminales
  P6/P7 se reanudaron sin llamadas nuevas y con el ledger idéntico byte a byte.
- Se retiraron las copias del corpus de 61 rutas locales después de compararlas con el plan. El recibo
  `config/datos_ciencias.lock.json` fija las generaciones y SHA. Recuperar con
  `uv run gskg datos restaurar --en-repo`; después usar los comandos normales. No añadir datos a Git.
- La suite integral pasó 1.360 pruebas en 262,79 segundos antes del retiro; Ruff y las verificaciones
  de recuperación, grafo, API, interfaz y exportación están documentadas en el cierre.

Leer [CIERRE_TECNICO](docs/CIERRE_TECNICO.md), [CURRICULARIZACION_V4](docs/CURRICULARIZACION_V4.md),
[VERIFICACION_GCS](docs/VERIFICACION_GCS.md), [DATOS_EXTERNOS](docs/DATOS_EXTERNOS.md) y
[PUBLICACION](docs/PUBLICACION.md). El detalle histórico sigue en Git local y en el respaldo privado;
no publicar ancestros privados ni usar push forzado.

La revisión automática no constituye aprobación institucional ni eficacia de aprendizaje medida.
La calibración independiente y el piloto de aula son evaluaciones posteriores, no estados de los agentes.
