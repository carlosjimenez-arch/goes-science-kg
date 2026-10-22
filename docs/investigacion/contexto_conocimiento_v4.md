# Empaquetado de evidencia para juicios V4

Medición local del 21 de octubre de 2026. Se prepararon los mismos 1.203 candidatos de contraste
documental con edición ENG/SG fijada, sin filtrar positivos esperados. No se usó un gold, un proveedor
ni un resultado semántico para seleccionar el contexto. Las huellas del currículo, candidatos y código,
los motivos e identidades de abstención están en los JSON de [antes](presupuesto_contexto_v4_antes.json)
y [después](presupuesto_contexto_v4.json).

El selector anterior garantizaba una fuente local y añadía otras por coincidencia léxica. Muchas
celdas en español podían desplazar la evaluación local o el objetivo extranjero en otra lengua.
El preparador detectaba la omisión y se abstenía correctamente, pero desperdiciaba contexto disponible.

El selector ahora recibe grupos explícitos. Reserva primero fragmentos que cubran esos grupos y la
versión local, permite que un fragmento cubra varios y después completa el contexto con el ranking
anterior. Usa máscaras de bits y selección voraz determinista; no promete empaquetado óptimo.
El límite incluye el JSON completo, metadatos y procedencia. Si no cabe, mantiene la abstención.
Los usuarios del selector que no declaran grupos conservan el comportamiento anterior.

| Límite en caracteres | Preparados antes | Preparados después | Filas distintas antes → después | p95 local después |
|---|---:|---:|---:|---:|
| 18.000 | 404 | 1.166 | 292 → 617 | 9,999 ms |
| 24.000 | 509 | 1.166 | 347 → 617 | 10,161 ms |
| 40.000 | 1.165 | 1.166 | 617 → 617 | 13,881 ms |

Los 37 candidatos restantes se abstienen por evidencia/alerta científica bloqueante, conservando el
veto. No son 37 filas diferentes. Las tres mediciones comparten caché: se verificaron 15 archivos
(11 XLSX y 4 PDF) una sola vez. Las latencias son preparación local secuencial con esa caché, sin
generación, red ni costo de modelos. No se interpretan como una comparación causal de velocidad.

Se mantiene **24.000** como límite predeterminado. Que 18.000 permita representar todos los grupos
no demuestra que preserve el contexto semántico suficiente. Tampoco 40.000 demostró mejor calidad.
Tener una ventana de cada grupo acredita disponibilidad estructural; no implica que esa ventana
demuestre la relación, que cuatro lectores sean independientes ni que mejore la enseñanza.

Reproducción local, sin SDK de Vertex ni ledger:

```bash
uv run gskg producto juicios medir-contexto --salida /tmp/contexto-v4.json
```

La autorización de clasificación V4 ya ejecutada no cubre por sí sola un experimento de cuatro jueces.
La calibración de ese flujo necesita un corpus, destino y gasto correspondientes, y debe medir
aceptaciones incorrectas, rechazos, abstenciones, costo y latencia con casos independientes.
