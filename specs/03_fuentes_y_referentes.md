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
| ACARA Senior Secondary · Biología y Química (AUSS) | 10–11 | 125 + 138 | `data/referencia/catalogo_acara_senior.json` |
| PISA 2025 · Ciencias | 7–9 | 21 de contenido + 8 procedimentales + 20 epistémicos | `catalogo_pisa2025.json` |
| TIMSS 2023 (secundario) | 2–8 | 78 | `catalogo_timss.json` + equivalencias con 2027 |

### Pivote de Bachillerato para Química y Biología (decidido el 2026-10-05)
No existe un TIMSS Advanced de Química ni de Biología. Se eligió como pivote el **Australian
Curriculum: Senior Secondary (Biology, Chemistry) v8.4** de ACARA por cuatro razones:
1. **Edad:** cubre Years 11–12 (16–18 años). Coincide con 10.°–11.° de El Salvador
   (unidades 1–2 ≈ 10.° y 3–4 ≈ 11.°).
2. **Licencia abierta:** CC BY 4.0. Se puede versionar, parafrasear y citar.
3. **Estructura comparable a TIMSS Advanced:** cada descripción de contenido tiene un código
   oficial estable (ACSBL…, ACSCH…). Se usa como localizador, porque el documento es HTML y no tiene páginas.
4. **Alto desempeño y base internacional:** Australia está en el grupo superior de PISA Ciencias
   (verificar en la fase 1.1). ACARA declara que lo construyó revisando los currículos de Reino Unido,
   Singapur, Ontario y Nueva Zelanda, el IB y el Framework for K-12 Science Education de EE. UU.
   (hoja informativa oficial de Senior Secondary Science).

Descartados como pivote:
- **Singapur O-Level (SEAB 6092/6093):** Sec 3–4, 15–16 años. El sitio de SEAB devolvía 404 el 2026-10-05.
  Queda como referencia de país en la fase 1.
- **IB Diploma:** licencia restringida.
- **PISA 2025:** mide a los 15 años y sigue siendo el piso de alfabetización científica.

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
- **ERCE 2019** (UNESCO-LLECE, 6.°): referente regional (niveles de aprendizaje y aportes para la enseñanza).
- **Progresiones de Aprendizaje de Uruguay (2022)**: evidencia directa de secuencia y prerrequisitos.

## Licencias y publicación
El repositorio es público y el equipo GOES decidió versionar también las fuentes. Los PDF siguen
siendo de sus autores (IEA, OCDE, ANEP, MEN, MOE y otros). Ver `NOTICE`. En los catálogos se
**parafrasea en español**: no se copian párrafos.
