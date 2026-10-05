# data/

| Carpeta | Contenido | ¿Se edita? |
|---|---|---|
| `fuentes/mined/` | Copia de la carpeta de Drive: `Mallas sugeridas/`, `Mapa de aprendizaje CyT.xlsx`, `Fuentes/` | No |
| `fuentes/externos/` | PDF de marcos, países y evaluaciones + `manifest.csv` y `estado.csv` (sha256) | Solo para agregar (skill `fuentes-descargar`) |
| `interim/` | Intermedios: temas, lotes de IA, objetivos de países y revisiones | Lo generan el pipeline y las skills |
| `grafo/` | `nodos.jsonl`, `aristas.jsonl` y `manifest.json` | Lo genera `gskg grafo construir` |
