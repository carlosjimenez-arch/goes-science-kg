# 03 · Fuentes y referentes

## Dónde están
| Carpeta | Contenido |
|---|---|
| `data/fuentes/mined/` | Copia de la carpeta de Drive del proyecto: `Mallas sugeridas/` (14 Excel), `Mapa de aprendizaje CyT.xlsx`, `Fuentes/` (PISA 2025, NGSS, MEN Colombia, Marco STEM y otros) |
| `data/fuentes/externos/` | PDF descargados de marcos y países + `manifest.csv` (id, organismo, url, uso) + `estado.csv` (descargado sí/no, bytes, sha256) |

Todo es **solo lectura**. Para agregar una fuente: fila en `manifest.csv`, descarga (skill
`fuentes-descargar`) y fila en `estado.csv` con su sha256.

## Marcos pivote (ya catalogados, con página)
| Marco | Grados SV | Objetivos | Catálogo |
|---|---|---|---|
| TIMSS 2027 · 4.° | 2–4 | 32 | `reportes/cobertura_curricular/data/referencia/catalogo_timss2027.json` |
| TIMSS 2027 · 8.° | 5–8 | 48 | ídem |
| TIMSS Advanced 2015 · Física | 10–11 | 23 | `catalogo_timss.json` (TA, sin página: completar) |
| PISA 2025 · Ciencias | 7–9 | 21 de contenido + 8 procedimentales + 20 epistémicos | `catalogo_pisa2025.json` |
| TIMSS 2023 (secundario) | 2–8 | 78 | `catalogo_timss.json` + equivalencias con 2027 |

**Faltan pivotes para Química y Biología de Bachillerato.** Candidatos que hay que evaluar
en la fase 1 (decide el equipo GOES):
- **PISA 2025** como techo de alfabetización científica a los 15 años.
- **Currículos de alto desempeño de 10.° y 11.°**: Singapur (O-Level Chemistry/Biology),
  Inglaterra (GCSE Combined Science), Australia (Senior Secondary Chemistry/Biology).
- **IB Diploma (Chemistry, Biology)** solo como referencia, porque tiene licencia restringida.

## Países
Estado y motivo de cada uno en `config/referentes.yaml`.

| País | Estado | Qué falta |
|---|---|---|
| Uruguay | alineado (135 objetivos) | Física-Química 7.°, Tierra y Espacio 7.°–9.° |
| Colombia | alineado (272) | — |
| Singapur | alineado (99, solo primaria) | Lower Secondary Science (el MOE retiró el enlace) |
| Chile | pendiente | Bases Curriculares (el sitio bloquea la descarga automática: bajar a mano) |
| Japón, Corea, Estonia, Inglaterra, Australia, Finlandia, Canadá-Ontario | pendientes | Todo |

### Criterios para elegir países de alto desempeño
1. Ubicarse en el grupo superior de **TIMSS 2023 Ciencias** (4.° u 8.°) o de **PISA 2022 Ciencias**.
   **Hay que verificarlo** contra los informes internacionales oficiales (IEA y OCDE) y citar
   documento y página en `config/referentes.yaml`. No usar cifras de memoria.
2. Tener el currículo oficial **público y descargable**, idealmente en español o inglés y con
   licencia que permita el uso.
3. Que esté **organizado por grado o por etapa corta**, para poder ubicar el primer grado en que
   aparece cada objetivo.
4. Cubrir varias tradiciones: Asia (Singapur, Japón, Corea), Europa (Estonia, Inglaterra, Finlandia),
   anglosajón (Australia, Ontario) y región (Uruguay, Chile, Colombia).

### Estándares y evaluaciones complementarias
- **NGSS** (EE. UU.): prácticas de ciencia e ingeniería y progresiones K–12. Ya está en
  `data/fuentes/mined/Fuentes/`. Sirve para la capa de prácticas y prerrequisitos.
- **ERCE 2019** (UNESCO-LLECE, 6.°): referente regional. `ERCE2019_Analisis_curricular.pdf` es en
  realidad un HTML de error (2 KB): hay que volver a descargarlo.
- **Progresiones de Aprendizaje de Uruguay (2022)**: evidencia directa de secuencia y prerrequisitos.

## Licencias y publicación
El repositorio es público y el equipo GOES decidió versionar también las fuentes. Los PDF siguen
siendo de sus autores (IEA, OCDE, ANEP, MEN, MOE y otros). Ver `NOTICE`. En los catálogos se
**parafrasea en español**: no se copian párrafos.
