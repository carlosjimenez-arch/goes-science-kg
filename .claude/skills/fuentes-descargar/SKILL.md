---
name: fuentes-descargar
description: Descarga y registra fuentes externas (marcos internacionales, currículos de países, informes TIMSS/PISA) en data/fuentes/externos con su sha256. Usar al agregar un país o documento nuevo, o cuando estado.csv marque una fuente como faltante.
---

# Descargar y registrar fuentes

1. Ubica la URL **oficial** (ministerio, IEA, OCDE). No uses espejos ni copias de terceros.
   Si no hay URL estable, detente y pide el archivo al usuario.
2. Agrega una fila a `data/fuentes/externos/manifest.csv`:
   `id,categoria,organismo,titulo,anio,url,archivo_local,uso_en_el_motor`.
   - `id`: `<pais>_<documento>` en minúsculas (p. ej. `jp_cos_lowsec`).
   - `archivo_local`: `paises/<pais>/<PAIS>_<Documento>_<año>.pdf` o `timss/…`, `pisa/…`.
3. Descarga con `curl -L --fail -o <archivo>` y verifica que sea un PDF (`file`). Si es HTML,
   es un error: no lo registres como bajado.
4. Registra en `estado.csv`: `id,archivo_local,ok,bytes,sha256` (`shasum -a 256`).
5. Si el sitio bloquea la descarga (Chile, MOE Singapur), deja `ok=False` y dile al usuario
   la URL exacta para que la baje a mano a esa ruta.
6. Actualiza `config/referentes.yaml` (`documentos`, `estado: descargado`).
7. Nunca modifiques ni borres un PDF ya registrado. Una edición nueva lleva un id nuevo.
