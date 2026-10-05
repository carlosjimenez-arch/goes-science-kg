# Revisión del equipo de Ciencias

Estos archivos CSV listan lo que propuso la inteligencia artificial y necesita una decisión humana. Se abren
con Excel o Numbers.

| Archivo | Qué revisar |
|---|---|
| `<fecha>_conceptos_temas.csv` | Temas de la malla cuyo **concepto principal** se asignó con confianza baja. |
| `<fecha>_prerrequisitos.csv` | Relaciones «hay que saber A antes que B». Primero vienen las que **sostienen un hallazgo** (columna `sostiene_hallazgo_de_secuencia` = sí): si la relación está mal, el hallazgo también lo está. |
| `<fecha>_alineacion_acara_bachillerato.csv` | (Biología y Química) Temas de 10.°–11.° alineados con ACARA con confianza baja o marcados FUERA. |

## Cómo llenarlos
1. Lee cada fila: el tema o la relación, y la justificación de la IA.
2. En `decision` escribe **aceptar**, **cambiar** o **rechazar**:
   - en `conceptos_temas`, **cambiar** significa poner en `nuevos_conceptos` los códigos correctos separados por `;`
     (están en `data/interim/conceptos/vocabulario.json`; también se pueden buscar con el visor de cada grado);
   - en `prerrequisitos`, **rechazar** quita la relación del grafo.
3. Escribe tu nombre o el del equipo en `revisado_por`. Puedes agregar un `comentario`.
4. Devuelve el archivo. El equipo GOES lo carga con `gskg revision importar <archivo>`, reconstruye el grafo y
   vuelve a generar las fichas y las propuestas.
