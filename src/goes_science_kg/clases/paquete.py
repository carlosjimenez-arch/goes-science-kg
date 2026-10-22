"""ZIP docente reproducible, inventariado y restaurado antes de habilitarlo."""

from __future__ import annotations

import json
import shutil
import stat
import tempfile
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath

from goes_science_kg.archivos import destino_generado
from goes_science_kg.clases.lectura import markdown_clase, markdown_unidad
from goes_science_kg.materiales.compilacion import serializar, sha

VERSION = "entrega-guiones-ciencias-1"
MAX_ARCHIVO = 50 * 1024**2
MAX_TOTAL = 2 * 1024**3
COBERTURA_V4 = {"guion_clase": 1013, "guion_unidad": 108}


def validar_cobertura_publicable(por_tipo):
    if any(por_tipo.get(tipo, 0) != cantidad for tipo, cantidad in COBERTURA_V4.items()):
        raise ValueError("La entrega completa requiere exactamente 1013 guiones y 108 unidades V4")


def _nombre(nombre):
    p = PurePosixPath(nombre)
    if (
        not nombre
        or "\\" in nombre
        or ":" in nombre
        or p.is_absolute()
        or any(t in {"", ".", ".."} for t in nombre.split("/"))
        or p.as_posix() != nombre
    ):
        raise ValueError("Ruta ZIP incompatible")
    return nombre


def construir(registros: list[dict], originales: dict[str, bytes], archivo: Path, *, procedencia: dict):
    destino_generado(archivo)
    if archivo.exists() or archivo.is_symlink():
        raise ValueError("La entrega requiere un archivo nuevo")
    if not registros or len({r["id"] for r in registros}) != len(registros):
        raise ValueError("La entrega requiere identidades únicas y contenido")
    if any(
        r["tipo"] not in {"guion_clase", "guion_unidad"} or r["estado"] != "respaldado_automaticamente"
        for r in registros
    ):
        raise ValueError("La entrega sólo incluye guiones con respaldo reconstruido")
    archivos = {"fuentes/" + _nombre(r): b for r, b in originales.items()}
    catalogo = []
    for r in sorted(registros, key=lambda v: v["id"]):
        carpeta = "clases" if r["tipo"] == "guion_clase" else "unidades"
        prefijo = carpeta + "/" + sha(r["id"].encode())
        archivos[prefijo + ".json"] = serializar(r)
        if r["tipo"] == "guion_clase":
            archivos[prefijo + ".docente.md"] = markdown_clase(r).encode()
            archivos[prefijo + ".estudiante.md"] = markdown_clase(r, estudiante=True).encode()
        else:
            archivos[prefijo + ".md"] = markdown_unidad(r).encode()
        catalogo.append(
            {
                **{k: r[k] for k in ("id", "titulo", "tipo", "grados", "asignatura", "unidad", "fila_id", "estado")},
                "archivo": prefijo + ".json",
            }
        )
    archivos["catalogo.json"] = serializar(catalogo)
    archivos["LEEME.md"] = (
        "# Guiones de Ciencias V4\n\n"
        "Consulta `catalogo.json` para ubicar cada clase y unidad por grado, asignatura y fila.\n"
        "En `clases/`, cada JSON conserva el guion y cuatro dictámenes; `.docente.md` incluye\n"
        "el solucionario y `.estudiante.md` contiene únicamente las tareas. `unidades/` agrupa\n"
        "los objetivos en orden documental. `fuentes/` conserva evidencia y expedientes.\n\n"
        "Los controles de auditoría incluyen ejemplos defectuosos introducidos a propósito;\n"
        "no pertenecen a las hojas de trabajo ni a los guiones liberados.\n\n"
        "Las sesiones y recursos son propuestas condicionadas. El respaldo automático no es\n"
        "aprobación institucional, validación en aula ni prueba de eficacia educativa.\n"
        "Se mantienen las alertas del original y las correcciones derivadas.\n\n"
        "Las adaptaciones basadas en OpenStax / Rice University se distribuyen bajo\n"
        "CC BY-NC-SA 4.0; atribuciones, cambios y licencias se incluyen con cada guion\n"
        "y en los archivos fuente. No se extiende esa licencia al código ni a las mallas MINED.\n"
    ).encode()
    if any(len(b) > MAX_ARCHIVO for b in archivos.values()) or sum(map(len, archivos.values())) > MAX_TOTAL:
        raise ValueError("La entrega excede los límites de restauración")
    manifest = {
        "version": VERSION,
        "materiales": len(registros),
        "por_tipo": dict(Counter(r["tipo"] for r in registros)),
        "procedencia": procedencia,
        "archivos": {n: {"sha256": sha(b), "bytes": len(b)} for n, b in sorted(archivos.items())},
    }
    manifest["id"] = sha(serializar(manifest))
    archivos["manifest.json"] = serializar(manifest)
    archivo.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archivo, "x", compression=zipfile.ZIP_DEFLATED) as z:
        for nombre, contenido in sorted(archivos.items()):
            info = zipfile.ZipInfo(_nombre(nombre), date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            z.writestr(info, contenido)
    if validar(archivo)["id"] != manifest["id"]:
        raise ValueError("La entrega construida no conserva su identidad")
    return manifest


def validar(archivo: Path):
    if archivo.is_symlink() or not archivo.is_file():
        raise ValueError("Se requiere un ZIP regular")
    with zipfile.ZipFile(archivo) as z:
        infos = z.infolist()
        nombres = [_nombre(i.filename) for i in infos]
        if len(nombres) != len(set(nombres)) or len(nombres) > 30000:
            raise ValueError("ZIP con rutas repetidas o demasiados archivos")
        if (
            any(
                i.file_size > MAX_ARCHIVO or i.is_dir() or i.flag_bits & 1 or stat.S_ISLNK(i.external_attr >> 16)
                for i in infos
            )
            or sum(i.file_size for i in infos) > MAX_TOTAL
        ):
            raise ValueError("ZIP fuera de límites, con enlaces o cifrado")
        m = json.loads(z.read("manifest.json"))
        if m["version"] != VERSION or m["id"] != sha(serializar({k: v for k, v in m.items() if k != "id"})):
            raise ValueError("Manifest de guiones incompatible")
        if set(nombres) != {"manifest.json", *m["archivos"]}:
            raise ValueError("El ZIP no conserva su inventario exacto")
        for n, ref in m["archivos"].items():
            raw = z.read(n)
            if (len(raw), sha(raw)) != (ref["bytes"], ref["sha256"]):
                raise ValueError("El contenido ZIP no corresponde al manifest")
        catalogo = json.loads(z.read("catalogo.json"))
        if (
            len(catalogo) != m["materiales"]
            or len({r["id"] for r in catalogo}) != len(catalogo)
            or dict(Counter(r["tipo"] for r in catalogo)) != m["por_tipo"]
        ):
            raise ValueError("Denominador del catálogo incompatible")
        filas = [r["fila_id"] for r in catalogo if r["tipo"] == "guion_clase"]
        if len(filas) != len(set(filas)):
            raise ValueError("El catálogo repite un objetivo curricular entre sus guiones")
        for r in catalogo:
            material = json.loads(z.read(r["archivo"]))
            if any(material[k] != r[k] for k in r if k != "archivo"):
                raise ValueError("La ficha de catálogo no corresponde al material")
    return m


def extraer(archivo: Path, destino: Path):
    destino_generado(destino / "manifest.json")
    if destino.exists() or destino.is_symlink():
        raise ValueError("La extracción requiere un directorio nuevo")
    manifest = validar(archivo)
    destino.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".clases-", dir=destino.parent) as temporal:
        base = Path(temporal) / "verificado"
        base.mkdir()
        with zipfile.ZipFile(archivo) as z:
            for nombre in [*manifest["archivos"], "manifest.json"]:
                p = base / nombre
                p.parent.mkdir(parents=True, exist_ok=True)
                with z.open(nombre) as entrada, p.open("xb") as salida:
                    shutil.copyfileobj(entrada, salida, length=1024 * 1024)
                if nombre != "manifest.json" and sha(p.read_bytes()) != manifest["archivos"][nombre]["sha256"]:
                    raise ValueError("El ZIP cambió durante la extracción")
        if (base / "manifest.json").read_bytes() != serializar(manifest):
            raise ValueError("El manifest cambió durante la extracción")
        base.rename(destino)
    return manifest
