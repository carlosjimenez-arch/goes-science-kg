# Integración documental PISA/ERCE · 21 de octubre de 2026

> Registro histórico de investigación. Describe el corte y la ejecución indicados en este documento.
> Estado vigente del código, API y métricas: [documentación actual](../README.md) y [calidad](../CALIDAD.md).

El formato `producto-3` exige nueve archivos, incluido `alineaciones.json`; el lector conserva
compatibilidad con los ocho de `producto-2`. No migra silenciosamente generaciones anteriores.

La generación actual es `0e2da287eb9248c37df078835d00fb63cd9a7585c882fb1cbc1ba5ed543f41aa`:
1.191 nodos, 4.136 aristas, 1.020 filas y 108 unidades. SHA-256 del manifiesto:
`843cf7d7aa4c9acfe045c285273d08d8fb1c1a6eafd01f2f07025709e8dd92fb`.
La anterior `c8098a09…` permanece histórica. No cambian las dos relaciones de conocimiento respaldadas
ni los quince juicios de sus tres cohortes originales.

## Resultados y validación

Se conservan **los cuatro pares originales completos**: un respaldo documental automático, un
rechazo y dos abstenciones. Sus doce intentos y USD 1,563349 ya estaban contabilizados; integrarlos
no añade llamadas ni reservas. El respaldo corresponde a valoración del diseño experimental PISA,
condicionado a una fila de Física de décimo. No acredita desempeño de estudiantes, alineación global,
equivalencia de edades ni aprobación oficial.

El archivo conserva solicitud, preparación histórica, perfil de extracción, entorno original,
tres lecturas —incluidos errores— y resultado. El coleccionador relee checkpoints en modo sólo lectura
y verifica Excel y páginas PDF. Reconstruye el cierre con los mismos criterios tipados; no selecciona
de nuevo los fragmentos históricos con prompts actuales. La exportación CLI reprodujo exactamente
los bytes del archivo obtenido de los cuatro terminales originales.

El constructor exige modelos fijados por el operador y relectura física antes de publicar.
Un nodo `AlineacionDocumental` enlaza mediante `DECLARADA_EN` a la fila exacta y `CON_CRITERIO` al
criterio local documentado. Estos criterios se identifican como paráfrasis locales. No se inventan
códigos oficiales ni aristas `CUBRE`; rechazos y abstenciones siguen auditables sin convertirse en
relaciones admitidas.

## Contexto y API

La recuperación por fila añade únicamente páginas primarias de alineaciones admitidas para esa
identidad. Relee bytes y extracción antes de usarlas. Reserva esas páginas antes del relleno opcional
y conserva un fragmento obligatorio en el presupuesto de lectura completa, aunque estén en inglés
y la consulta en español. Si faltan o no caben, se abstiene; `k` tampoco puede eliminarlas silenciosamente.

- `GET /api/v4/alineaciones`: todos los estados, filtrables por `fila_id`.
- `GET /api/v4/alineaciones/{id}`: preparación, lectores, fuentes y cierre originales tras relectura.
- Modificar el noveno archivo invalida la instancia de API.
- Modificar el PDF impide auditar o utilizar el respaldo archivado.

La comprobación real auditó los cuatro casos con creación de Vertex prohibida. El contexto admitido
conservó catorce evidencias, una página PISA y once fragmentos; grado ajeno devuelve HTTP 422.
El primer listado incluyó 1.851 ms de carga local; no mide concurrencia ni latencia en producción.
Evidencia local: `docs/investigacion/cierre_integracion_v4_20261021.json`.

## Reproducción institucional

Requiere insumos y checkpoints originales del entorno institucional. Cero invocaciones de modelos:

```bash
gskg alineacion coleccionar \
  alineacion-v4-cierre-20261021-1 alineacion-v4-cierre-20261021-2 \
  alineacion-v4-cierre-20261021-3 alineacion-v4-cierre-20261021-4 \
  --salida data/producto/alineaciones/cohorte_cierre_20261021.json
gskg producto construir \
  --conocimiento data/producto/juicios/conocimiento_entrega_v2_20261021.json \
  --alineaciones data/producto/alineaciones/cohorte_cierre_20261021.json
gskg producto validar
```

Los IDs identifican la cohorte elegida por el operador; la herramienta no demuestra que represente
todas las filas. Rechaza pares repetidos y cierres incompatibles, pero los hashes locales no son firma
institucional. Los cambios del motor invalidan correctamente entornos durables anteriores: reproducir
ejecuciones experimentales requiere el código archivado de cada protocolo, sin reiniciar contadores
ni pedir nuevos votos favorables.
