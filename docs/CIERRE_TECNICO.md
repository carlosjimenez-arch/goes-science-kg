# Estado de entrega de Ciencias · 22 de octubre de 2026

> Cierre de la entrega curricular anterior, conservado como evidencia. La rama de mantenimiento actual
> es `feat/api`; API, estilo y métricas vigentes: [índice](README.md) y [calidad](CALIDAD.md).

Ampliación posterior: la [aplicación GOES y su API](APLICACION_CIENCIAS.md) adaptan el HTML aportado a
los datos reales del snapshot. La versión ampliada pasó 1.387 pruebas y las comprobaciones HTTP y de
navegador; no altera el currículo ni consume nuevas llamadas a Vertex. El detalle siguiente conserva
la evidencia del cierre curricular anterior a esa ampliación.

**Cierre técnico completado:** 108 unidades y 1.013 filas de Ciencias cuentan con respaldo
automático; se conservan las siete filas fuera de alcance. La entrega de revisión conserva el denominador completo y sus
estados. No se presenta como currículo aprobado por la institución ni como eficacia medida.
[Resultados, artefactos y límites](CURRICULARIZACION_V4.md).

| Capacidad | Evidencia comprobada |
|---|---|
| Ingesta V4 | Once matrices, 126 hojas, 1.020 filas y 108 unidades; SHA/celdas conservados |
| Curricularización | 108 unidades respaldadas y 1.013 filas de Ciencias con propuestas; antecedentes completos |
| Cuatro especialistas | Ciencia, currículo, psicopedagogía y adversarial; veto por criterio, huella exacta |
| Controles | Cinco defectos distintos detectados por el criterio previsto; fallos no cuentan como aciertos |
| Publicación de revisión | producto-4, diez archivos, 2.327 nodos y 7.304 aristas; fuente y grafo verificados |
| Entrega utilizable | Excel/CSV original-propuesta, HTML sin conexión, fuentes y votos completos |
| Biología | Copia derivada con cuatro enmiendas; otras celdas, estilos y partes OOXML preservados |
| Progresiones nativas | Doce expectativas NGSS y nueve enlaces documentales; ninguna equivalencia de grados |
| PISA/ERCE y conocimiento | Se conservan cuatro casos de alineación y quince juicios previos, con todos sus estados |
| Respaldo final | 7.580 archivos y siete SQLite restaurados dos veces desde GCS; 61 rutas locales retiradas tras comparar todos los originales |
| Reanudación recuperada | Diez terminales P6 y uno P7; cero llamadas nuevas y ledger idéntico byte a byte |

La suite integral pasó **1.360 pruebas en 262,79 segundos**. Ruff está en verde. Incluye contratos,
rehidratación, falsificaciones con identidad recalculada, votos ausentes, presupuestos concurrentes,
mutación de publicación, protección GCS, restauración SQLite, exportación y no ejecución de fórmulas.
La API de revisión devolvió 200 para salud, filas, propuestas, progresiones y CSV. La vista se comprobó
en navegador con filtros reales y sin desbordamiento horizontal en la ventana ensayada.

Se conservan los experimentos y fallos P1–P5. P6 resolvió las diez incidencias en una ronda cada una, sin
reevaluar las 98 unidades respaldadas. P7 corrigió un falso positivo científico adicional con fuentes
primarias, conservando el caso previo y cuatro votos nuevos sobre la rectificación. El contador permanece en el mismo ledger y el límite se aplica
por llamada. La reanudación inicialmente bloqueada por Google se recuperó tras verificar nuevamente
la identidad GOES, antes de gastar. [Continuidad operativa](CONTINUIDAD_CIENCIAS_V4.md).

La selección definitiva está publicada y el corpus local fue retirado después de una segunda
restauración completa. El recibo permite recuperarlo explícitamente; no hay datos privados en el árbol
de código. Las 86 pruebas de contratos pasan desde el checkout público sin corpus.
La calibración independiente, validación en
aula y aprobación institucional siguen siendo estados separados: no se obtienen por votación de agentes.
El grafo no inventa prerrequisitos reales a partir de secuencias extranjeras.

La entrega pública usa `feat/ciencias-v4` desde la base pública. Se incorporan código, pruebas,
configuración y documentación y se retiran los datos del árbol, conservando su recuperación privada.
No se publica la historia local que contiene el corpus nuevo; no se reescribe historia ni se usa push
forzado. No se añadió CI ni se modificó IAM. [Publicación](PUBLICACION.md), [datos](DATOS_EXTERNOS.md).


La entrega posterior de biblioteca docente conserva 2.867 registros, incluidos 1.013 paquetes
V4 por objetivo, 108 por unidad y el material histórico sin migrar sus dictámenes.
Restaurar con `gskg materiales restaurar`; consultar `/api/v4/materiales` y su OpenAPI.
La preparación reutiliza textos revisados y no consume Vertex. Son materiales para montar
clases; no se presentan como guiones completos nuevos para todos los objetivos.
[Detalle, almacenamiento y pruebas](MATERIALES_DOCENTES.md).

La ampliación docente pasó 1.416 pruebas integrales (267,76 s), Ruff, 367 peticiones HTTP
correctas y restauración independiente desde GCS. Los 316 originales conservaron sus SHA.
