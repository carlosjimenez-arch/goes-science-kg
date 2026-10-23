# Verificación de recuperación de Ciencias V4

## Respaldo vigente de la ampliación de clases

El recibo `config/datos_ciencias.lock.json` fija un objeto nuevo en el bucket GOES de Ciencias.
Cada escritura verificó identidad, proyecto, UBLA y PAP heredada con política efectiva `enforced`;
se usó precondición de generación cero y relectura por generación. No se cambió IAM.

| Elemento | Identidad comprobada |
|---|---|
| Archivos / bases SQLite | 12.640 / 27 |
| Bytes originales / comprimidos | 2.929.446.834 / 1.062.223.923 |
| SHA del ZIP | `7f759821cce24d08c029dd1460201f1bf27d94b5701e57402a111750ec2382f5` |
| Generación ZIP | `1792723241759606` |
| Huella del inventario | `72630b7acc157560cd3414ea8a77a5e67a049e69320a1b41fdf40d1ab2091d1d` |
| Generaciones inventario / descriptor | `1792723276602426` / `1792723284410915` |
| Consumo conservado | 3.227 llamadas; USD 2.340,8786235 de reserva |

Se descargó de GCS a una carpeta vacía, se verificó cada archivo y la integridad de las 27 bases.
La migración de vínculos de presupuesto mantuvo intacto el ledger. Se cotejaron 1.756 trazas de
lectores con sus respuestas reales y contexto congelado. Se reanudó un terminal por cada uno de
18 bloques de clases con un proveedor que rechaza cualquier generación: cero llamadas nuevas y
el mismo consumo al terminar. El ensayo usa la versión exacta del corpus de cada preparación.

`config/presupuesto_clases_v4.json` adopta un punto mínimo de continuidad sólo después de esa
verificación. El archivo privado incluido en el respaldo fija el hash de las 3.227 filas completas;
se conservan además las 668 iniciales. Un respaldo anterior ya no habilita gasto nuevo bajo esta
configuración. No se borran reservas ni se amplía el máximo de 4.000 llamadas/USD 3.500.

Reproducción, sin Vertex:

```bash
uv run gskg datos restaurar --destino /tmp/ciencias-restauradas
# Para reponer rutas en un checkout sin corpus:
uv run gskg datos restaurar --en-repo
```

El respaldo conserva borradores, vetos y abstenciones: no constituye la publicación completa de los
1.013 guiones. Las operaciones posteriores a ese punto necesitan otro respaldo antes de cerrar.
La biblioteca docente de preparaciones mantiene su recibo independiente. La suite completa pasó
1.567 pruebas en 272,64 s; Ruff pasó en `src` y `tests`. El ensayo detallado queda en
`data/clases_v4/protocolos/verificacion_restauracion_20261023.json` (fecha UTC del ensayo).

## Antecedente: respaldo del cierre curricular

La generación del cierre curricular se creó en el mismo bucket, prefijo, proyecto y cuenta GOES aprobados. Cada escritura
volvió a comprobar UBLA activo y prevención pública heredada con política efectiva enforced. Se usó
precondición de generación cero; no se sobrescribieron objetos ni se cambió IAM. Se descargó y verificó
cada generación. El recibo histórico permanece en Git y el objeto sigue recuperable por su generación.

| Elemento | Identidad comprobada |
|---|---|
| Archivos | 7.580, incluidos siete SQLite |
| Bytes originales | 1.658.473.975 |
| Bytes del paquete | 497.573.457 |
| SHA del ZIP | `b6b84b511df95ee7d85f11c0c94d03286c05594308e084282e91ec23803de065` |
| Generación del ZIP | `1792672061221417` |
| Huella del inventario | `83433867057bc8aadd676cb8e4e70d3ffcd479398cbbb44447246c72ffdec776` |
| Generación del inventario | `1792672084503133` |
| Generación del descriptor | `1792672093385592` |
| Snapshot producto-4 | `e92bc700d78f0f559671acc62f559f9e5176b09c3341a47c575c640195022008` |

Los 7.580 archivos se restauraron desde GCS en otra carpeta y se verificaron sus SHA. Se migraron
15 vínculos de presupuesto a la identidad física de esa copia, sin modificar el ledger. El runtime
recuperó 108 unidades, 1.020 filas originales y 1.013 propuestas de Ciencias; las siete fuera de alcance
siguen presentes. Los diez terminales reales de P6 y el de P7 se recuperaron con una guarda que
rechaza cualquier intento de llamar a un modelo: **cero llamadas nuevas**. El contador se mantuvo en
668 y la reserva en USD 731,1485125. SHA del ledger, idéntico antes y después:
`3ad9b798421a8b463f8d3dd924498330b42ddbd483ca4f774c5386bb74f722ae`.

El ensayo detectó que una alerta derivada de P7 activaba referencias específicas de otra errata al
reconstruir contexto. La corrección separa `bloqueos_curriculares` de `bloqueos_derivados` y aplica su
unión en `bloqueos_efectivos` para generación, consulta, API y preparación de sesiones. El contexto de
cada protocolo mantiene sus alertas de origen, fuentes, identidad y votos. Los dos errores originales
de Hooke y evidencias de cambio químico, corregidos en las propuestas P6, también se revalidan por
SHA/celda/ancla desde config/alertas_derivadas_v4.yaml. Hay 30 filas originales bloqueadas: las 27
iniciales y tres derivadas; las propuestas corregidas conservan su respaldo. No se cambiaron checkpoints,
huellas guardadas, rúbricas, bytes de fuentes primarias ni presupuestos. Tras corregir, los once terminales volvieron a validar
exactamente el contexto físico y su resultado. Los archivos de datos y el paquete no requirieron cambios.

La API conserva los cuatro expedientes históricos PISA/ERCE y señala que uno tiene un veto científico
posterior: sigue siendo auditable, pero no habilita generación nueva. Una prueba de regresión verifica
esta separación entre el dictamen histórico y los permisos actuales. Las rutas de salud, filas,
propuestas, progresiones y `/api/v4/exportaciones/mejoras.csv` respondieron 200 desde la copia restaurada.

El respaldo anterior sigue recuperable por su generación:
`gs://goes-ai-kg-artefactos/ciencias/v4/repositorio/objetos/76c1a0e38b38884c5f55aac91b616be7f47d3810e1752fe4082fbe1c82f36523.zip#1792642807234664`.
Su SHA es el del nombre del objeto. No se borró ni se reescribió la historia de GCS o de Git.

La retirada local terminó tras una **segunda restauración real** de los 7.580 archivos y los siete SQLite.
La comparación exacta con el plan comprobó originales, vínculos y WAL antes de retirar 7.580 archivos de
61 rutas. El código y el recibo permanecen en Git; los datos vuelven a las mismas rutas con
`gskg datos restaurar --en-repo`. [Procedimiento operativo](DATOS_EXTERNOS.md).

La batería integral pasó **1.360 pruebas en 262,79 segundos**, antes de retirar el corpus. Ruff comprobó
`src`, `tests` y `.claude/hooks`. Desde el checkout público sin corpus pasaron además **86 pruebas**
de contratos, recuperación, presupuesto, propuestas, exportación y seguridad de archivos. Las 18 pruebas
de calidad/determinismo del grafo también pasaron. El wheel final contiene 194 archivos, incluida la
plantilla y la rectificación, sin PDF, Excel, SQLite ni credenciales. SHA-256 del wheel:
`77c8ab1ee40cd2a1aa514e9b303cc5ba4efe83dfb08af17954a3842d0d84e4f5`.

Después del retiro local volvieron a pasar las 31 pruebas de almacenamiento/migración. El contrato
histórico `tests/contracts/cli_v1.txt` permanece en la rama pública: sus **89 pruebas** comprueban la
disponibilidad de comandos y su ayuda sin necesitar corpus ni red. Se compararon los árboles completos
preparados del checkout local y de la rama pública y resultaron idénticos, sin incorporar ancestros privados.
