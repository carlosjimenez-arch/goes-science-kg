# Progresiones NGSS: evidencia y decisión de diseño

Consulta: 21 de octubre de 2026. Se descargaron del [índice oficial de apéndices NGSS](https://www.nextgenscience.org/resources/ngss-appendices)
los apéndices E, F y G. El almacén separado `data/referencias_progresiones_2026` conserva manifiesto,
SHA-256, páginas físicas y versiones. La fecha de consulta no cambia las ediciones de 2013.
`config/progresiones_2026.yaml` fija las tres huellas.

| Apéndice | Contenido documental | Páginas |
|---|---|---:|
| E | Progresión de ideas disciplinares | 8 |
| F | Prácticas de ciencia e ingeniería | 33 |
| G | Conceptos transversales | 17 |

El [apéndice E, página física 1](https://www.nextgenscience.org/sites/default/files/resource/files/AppendixE-ProgressionswithinNGSS-061617.pdf)
describe una referencia por bandas, integrada con las otras dimensiones. La tabla de ecosistemas
en su página física 5 se renderizó e inspeccionó: conserva columnas K–2, 3–5, 6–8 y 9–12 y ausencias
explícitas. La extracción lineal no basta para atribuir una frase a una columna. No se construirán
relaciones educativas sólo a partir del orden de palabras del PDF.

Los apéndices [F](https://www.nextgenscience.org/sites/default/files/resource/files/Appendix%20F%20%20Science%20and%20Engineering%20Practices%20in%20the%20NGSS%20-%20FINAL%20060513.pdf)
y [G](https://www.nextgenscience.org/sites/default/files/resource/files/Appendix%20G%20-%20Crosscutting%20Concepts%20FINAL%20edited%204.10.13.pdf)
permiten contrastar prácticas y conceptos transversales junto al contenido. Tenerlos no demuestra
que una actividad local reúna las tres dimensiones ni valida un prerrequisito individual.

## Aplicación a Ciencias

La progresión documental organiza expectativas entre bandas. Un prerrequisito expresa una necesidad
concreta para una tarea y requiere otro juicio. No se transforma 6–8 en equivalencia automática con
grados salvadoreños. Poblaciones nativas y límites acompañarán cualquier contraste futuro.

La ampliación debe conservar un expediente con contenido, práctica y concepto transversal; página
física y columna comprobadas; objetivo y evaluación V4; viabilidad de tiempo, recursos, lectura y
seguridad; y el cierre de especialistas implementado. Los valores ausentes del insumo local permanecen
ausentes. La contextualización puede usar agua, ecosistemas, sismos o energía cuando el objetivo lo
permita, sin inventar disponibilidad de equipos ni datos locales.

La colección permite consulta reproducible, sin admisión automática ni generación pagada adicional.
**No hay una progresión NGSS–V4 respaldada en esta entrega.** Los documentos originales permanecen
locales mientras se decide el alcance de publicación pública.

```bash
gskg investigacion referencias ingerir ngss_apendice_e ngss_apendice_f ngss_apendice_g \
  --coleccion progresiones --descargar
gskg investigacion referencias buscar 'planning investigations' --coleccion progresiones
gskg investigacion referencias pagina ngss_apendice_e 5 --coleccion progresiones
```

Se mantienen las protecciones HTTPS, dominio permitido, límite de tamaño y SHA. Exportar resultados
no puede sobrescribir este almacén. Su aislamiento se prueba con fuentes sintéticas de contenido
distinto bajo un mismo ID. Se revisaron visualmente las páginas físicas E-5 (ecosistemas), F-7
(planificación de investigaciones) y G-11 (estabilidad y cambio). No se afirma haber inspeccionado
visualmente todas las tablas de los tres PDF.
