---
name: pais-extraer-objetivos
description: Extrae los objetivos de aprendizaje de Ciencias de un currículo nacional (PDF) a data/interim/paises/<pais>.json, con documento, página y grado. Usar después de descargar el currículo de un país y antes de alinearlo.
---

# Objetivos de un país

Esquema (uno por objetivo; mismo formato que `reportes/cobertura_curricular/data/interim/paises/uruguay.json`):
```json
{"id": "JP-SCI-G7-01", "pais": "Japón", "documento": "JP_Course_of_Study_LowerSec_2017.pdf",
 "pagina": 41, "grado_min": 7, "grado_max": 7, "grado_o_tramo": "Grade 7 (1st year lower sec.)",
 "tipo": "Conocimiento", "eje": "Primer campo · Física", "texto": "Paráfrasis en español (≤30 palabras)"}
```

1. Lee el documento completo antes de extraer. Identifica cómo se organiza: por grado, por etapa o por banda.
2. **Grado equivalente de El Salvador** (`grado_min`/`grado_max`): usa la edad típica de ingreso del
   país y de El Salvador (1.° ≈ 7 años). Documenta la conversión en `config/referentes.yaml`
   (`equivalencia_grados`). Para bandas (KS3, Tramo 5), usa el rango y no inventes un grado puntual.
3. Extrae solo **Ciencias**. Deja fuera tecnología, matemática y geografía humana.
4. Un objetivo es la unidad mínima evaluable que el documento enumera. No partas oraciones arbitrariamente.
5. `texto`: paráfrasis en español. Las citas literales pueden tener 30 palabras como máximo.
6. `id`: `<ISO>-<eje corto>-G<grado>-<nn>`, estable.
7. Valida que cada objetivo tenga página y grado, y que no haya ids duplicados.
   Reporta el conteo por grado y por eje.
8. Para documentos largos, usa subagentes por capítulo o grado y une los resultados con un script.
