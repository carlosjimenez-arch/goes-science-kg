"""ZIP individuales y colecciones reproducibles, con inventario y biblioteca independiente."""

from __future__ import annotations

import csv
import io
import logging
import re
import unicodedata
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from goes_science_kg.archivos import destino_generado
from goes_science_kg.materiales.almacen import Biblioteca, construir
from goes_science_kg.materiales.compilacion import serializar, sha
from goes_science_kg.operacion.respaldo import nombre_seguro
from goes_science_kg.produccion.indicadores.compilacion import LIMITE, VERSION, compilar
from goes_science_kg.produccion.indicadores.lectura import indice_markdown, markdown_indicador

LOGGER = logging.getLogger(__name__)


def zip_verificable(archivos, metadatos):
    """La fecha fija y las rutas explícitas permiten reproducir los mismos bytes."""
    if "manifest.json" in archivos:
        raise ValueError("El manifiesto se construye con el contenido exacto")
    inventario = {n: {"sha256": sha(raw), "bytes": len(raw)} for n, raw in sorted(archivos.items())}
    contenido = dict(archivos, **{"manifest.json": serializar(metadatos | {"archivos": inventario})})
    salida = io.BytesIO()
    with ZipFile(salida, "w", compression=ZIP_DEFLATED) as z:
        for nombre, raw in sorted(contenido.items()):
            nombre_seguro(nombre)
            info = ZipInfo(nombre, date_time=(2026, 10, 26, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            z.writestr(info, raw)
    return salida.getvalue()


def catalogo_csv(indice):
    columnas = [
        "id",
        "grado",
        "asignatura",
        "unidad",
        "codigo",
        "indicador",
        "origen",
        "estado_contextos",
        "estado_reagrupamiento",
        "colision_codigo",
        "filas_ids",
        "zip_sha256",
        "zip_bytes",
    ]
    f = io.StringIO(newline="")
    w = csv.DictWriter(f, fieldnames=columnas)
    w.writeheader()
    for i in indice:
        fila = {c: i.get(c, "") for c in columnas}
        fila.update(
            filas_ids=" | ".join(i["filas_ids"]),
            zip_sha256=i["zip_individual"]["sha256"],
            zip_bytes=i["zip_individual"]["bytes"],
        )
        # El CSV es una vista de consulta; los literales exactos permanecen en el JSON.
        fila = {k: "'" + v if isinstance(v, str) and v.startswith(("=", "+", "-", "@")) else v for k, v in fila.items()}
        w.writerow(fila)
    return f.getvalue().encode("utf-8-sig")


def guardar(origen: Path, destino: Path, exportaciones: Path):
    for p in (destino, exportaciones):
        destino_generado(p / "manifest.json")
        if p.exists() or p.is_symlink():
            raise ValueError("Se requieren destinos nuevos")
    rutas = [p.resolve() for p in (origen, destino, exportaciones)]
    if any(a == b or a in b.parents or b in a.parents for n, a in enumerate(rutas) for b in rutas[n + 1 :]):
        raise ValueError("La biblioteca de origen y los destinos deben ser independientes")
    biblioteca = Biblioteca(origen)
    originales, archivos_base = biblioteca.exportar()
    if biblioteca.manifest["procedencia"].get("version_diseno") != "preparacion-malla-final-3":
        raise ValueError("Se requiere la biblioteca de preparaciones V3")
    registros, indice, informe = compilar(
        originales,
        biblioteca_id=biblioteca.manifest["id"],
        snapshot_id=biblioteca.manifest["procedencia"]["snapshot_id"],
    )
    registros = sorted(registros, key=lambda r: r["id"])
    registros_por_id = {r["id"]: r for r in registros}
    indice_por_id = {i["id"]: i for i in indice}
    activos, textos, documentos = {}, {}, {}
    for r in registros:
        nombre = sha(r["id"].encode())
        textos[r["id"]] = markdown_indicador(r).encode()
        documentos[r["id"]] = serializar(r)
        zip_ = zip_verificable(
            {"LEEME.md": textos[r["id"]], "indicador.json": documentos[r["id"]]},
            {"version": VERSION, "indicador_id": r["id"], "snapshot_id": informe["huella_final"]},
        )
        ruta = f"indicadores/{nombre}.zip"
        activos[ruta] = zip_
        indice_por_id[r["id"]]["zip_individual"] = {"ruta": ruta, "sha256": sha(zip_), "bytes": len(zip_)}
    exportaciones.mkdir(parents=True)
    grupos = sorted({(i["grado"], i["asignatura"]) for i in indice})
    inventario = []
    for grado, asignatura in grupos:
        items = [i for i in indice if i["grado"] == grado and i["asignatura"] == asignatura]
        files = {
            "LEEME.md": indice_markdown(items).encode(),
            "indice.json": serializar({"indicadores": items, "limite": LIMITE}),
            "informe.json": serializar(informe),
        }
        for i in items:
            nombre = sha(i["id"].encode())
            files[f"paquete_indicador/{nombre}.md"] = textos[i["id"]]
            files[f"paquete_indicador/{nombre}.json"] = documentos[i["id"]]
            files[i["zip_individual"]["ruta"]] = activos[i["zip_individual"]["ruta"]]
            registro = registros_por_id[i["id"]]
            for fuente in registro["documento"]["fuentes_originales"]:
                ruta = fuente["archivo_local"]
                raw = archivos_base[ruta]
                if sha(raw) != fuente["sha256"]:
                    raise ValueError("El Excel no coincide con la procedencia de la preparación")
                files[ruta] = raw
                activos[ruta] = raw
        etiqueta = unicodedata.normalize("NFKD", asignatura).encode("ascii", "ignore").decode().lower()
        nombre = f"grado-{grado:02d}-{re.sub('[^a-z0-9]+', '-', etiqueta)}.zip"
        raw = zip_verificable(
            files,
            {
                "version": VERSION,
                "grado": grado,
                "asignatura": asignatura,
                "paquetes": len(items),
                "snapshot_id": informe["huella_final"],
                "estado_revision": "sin_revision_especifica",
            },
        )
        (exportaciones / nombre).write_bytes(raw)
        activos["paquetes/" + nombre] = raw
        inventario.append(
            {
                "archivo": nombre,
                "grado": grado,
                "asignatura": asignatura,
                "paquetes": len(items),
                "sha256": sha(raw),
                "bytes": len(raw),
            }
        )
        LOGGER.info("VERDE indicadores: %s / %s; %d ZIP individuales", grado, asignatura, len(items))
    raw = serializar({"paquetes": inventario})
    (exportaciones / "indice.json").write_bytes(raw)
    activos["paquetes/indice.json"] = raw
    activos["indicadores/indice.json"] = serializar({"indicadores": indice, "limite": LIMITE})
    activos["indicadores/catalogo.csv"] = catalogo_csv(indice)
    activos["indicadores/auditoria.json"] = serializar(informe)
    activos["preparaciones/manifest.json"] = biblioteca.archivo_manifest.read_bytes()
    manifest = construir(
        registros,
        activos,
        destino,
        procedencia={
            "snapshot_id": informe["huella_final"],
            "edicion": "produccion-final-20261026",
            "version_diseno": VERSION,
            "biblioteca_preparaciones_id": biblioteca.manifest["id"],
            "estado_revision": "sin_revision_especifica",
            "metodo": "agrupacion_literal_por_ambito_sin_generacion",
            "limite": LIMITE,
        },
    )
    biblioteca.comprobar()
    return manifest, informe
