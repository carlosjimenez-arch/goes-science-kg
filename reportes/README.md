# Reportes

| Carpeta | Qué es |
|---|---|
| [`cobertura_curricular/`](cobertura_curricular) | Cobertura de las mallas de Ciencias frente a TIMSS 2027/2023, TIMSS Advanced 2015 y PISA 2025, y comparación con Uruguay, Colombia y Singapur (oct-2026). Antes era el repo `goes-science-kg-II`. |

`cobertura_curricular/` es autocontenido: sus scripts usan rutas relativas y se ejecutan desde esa
carpeta. Sus fuentes (`input/`, `data/raw`, `data/referencia/externos`) son **enlaces simbólicos** a
`data/fuentes/` de la raíz, para que haya una sola copia de cada documento.

Entregables principales:
- `outputs/informe_timss2027.md` y `outputs/informe_paises_timss2027.md`: informes para el MINED.
- `outputs/Cobertura_TIMSS2027_Ciencias_SV.xlsx`: libro con fórmulas.
- `outputs/Explorador_Cobertura_Ciencias_SV.html`: explorador interactivo.

Nota: su `scripts/extract_temas.py` elige la versión de las mallas duplicadas por fecha de
modificación, y git no conserva esas fechas. Tras un clone, usa el extractor del paquete
(`gskg temas`), que fija las versiones en `config/mallas.yaml`.
