"""Build and verify a local successor edition while preserving pinned deliveries."""

from __future__ import annotations

import hashlib
import json
import posixpath
import shutil
import stat
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit

from markdown_it import MarkdownIt

from goes_science_kg.aprendizaje.cierre_recorridos import materializar_recorrido, validar_recorrido
from goes_science_kg.archivos import destino_generado
from goes_science_kg.clases.complementaria_publicacion import leer_publicada
from goes_science_kg.clases.lectura import markdown_clase
from goes_science_kg.clases.paquete import validar as validar_base
from goes_science_kg.entrega.lectura import (
    markdown_anexo_completo,
    markdown_evaluacion,
    markdown_unidad,
    nombre,
    plan_cognitivo,
)
from goes_science_kg.materiales.compilacion import serializar, sha

VERSION = "edicion-didactica-ciencias-2"
RECIBOS = (
    "clases_ciencias",
    "complementos_ciencias",
    "datos_ciencias",
    "materiales_ciencias",
    "materiales_preparaciones",
)


def digest(archivo: Path) -> str:
    """Hash a file without loading large archived deliveries into memory."""
    with archivo.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _propio(base: Path, relativa: str) -> Path:
    partes = PurePosixPath(relativa)
    archivo = base / relativa
    if partes.is_absolute() or ".." in partes.parts or not archivo.resolve().is_relative_to(base.resolve()):
        raise ValueError("La evidencia debe permanecer dentro de su carpeta")
    if any(p.is_symlink() for p in (archivo, *archivo.parents)) or not archivo.is_file():
        raise ValueError("La evidencia requiere archivos propios")
    return archivo


class _Escritura:
    def __init__(self, destino: Path):
        self.destino = destino
        self.archivos: dict[str, dict] = {}

    def guardar(self, nombre_archivo: str, contenido: bytes | str | dict | list) -> None:
        nombre_path = PurePosixPath(nombre_archivo)
        if nombre_path.is_absolute() or ".." in nombre_path.parts or nombre_archivo in self.archivos:
            raise ValueError("Nombre repetido o fuera de la edición")
        raw = (
            contenido
            if isinstance(contenido, bytes)
            else (contenido.encode() if isinstance(contenido, str) else serializar(contenido))
        )
        destino = self.destino / nombre_archivo
        destino.parent.mkdir(parents=True, exist_ok=True)
        with destino.open("xb") as stream:
            stream.write(raw)
        self.archivos[nombre_archivo] = {"bytes": len(raw), "sha256": sha(raw)}

    def copiar(self, origen: Path, nombre_archivo: str) -> None:
        if nombre_archivo in self.archivos:
            raise ValueError("Nombre repetido en la edición")
        destino = self.destino / nombre_archivo
        destino.parent.mkdir(parents=True, exist_ok=True)
        with origen.open("rb") as entrada, destino.open("xb") as salida:
            shutil.copyfileobj(entrada, salida)
        self.archivos[nombre_archivo] = {"bytes": destino.stat().st_size, "sha256": digest(destino)}


def _correcciones(carpeta: Path | None, clases: dict[str, dict]) -> dict[str, dict]:
    if carpeta is None:
        return {}
    catalogo = json.loads(_propio(carpeta, "catalogo_correcciones.json").read_bytes())
    entradas = catalogo if isinstance(catalogo, list) else catalogo["correcciones"]
    resultado = {}
    for entrada in entradas:
        fila_id = entrada["fila_id"]
        if fila_id in resultado or fila_id not in clases:
            raise ValueError("La corrección repite o desconoce un objetivo")
        guion = clases[fila_id]["documento"]["guion"]
        if entrada["guion_sha256_anterior"] != sha(serializar(guion)):
            raise ValueError("La corrección no corresponde al guion antecedente exacto")
        for campo in ("paquete_json", "docente_md", "estudiante_md", "comprobacion_md"):
            _propio(carpeta, entrada[campo])
        paquete = json.loads(_propio(carpeta, entrada["paquete_json"]).read_bytes())
        if (
            paquete.get("origen", {}).get("fila_id") != fila_id
            or paquete["origen"].get("guion_sha256") != entrada["guion_sha256_anterior"]
        ):
            raise ValueError("El contenido de la corrección pertenece a otro antecedente")
        if paquete.get("objetivos") != [guion["objetivo"]]:
            raise ValueError("La corrección no conserva el objetivo literal")
        if corregido := paquete["origen"].get("guion_corregido"):
            from goes_science_kg.clases.contratos import GuionClase

            GuionClase.model_validate(corregido)
            if corregido["fila_id"] != fila_id or corregido["objetivo"] != guion["objetivo"]:
                raise ValueError("El guion sucesor cambia su identidad u objetivo")
            fuentes = {f["id"] for f in paquete["fuentes"]}
            if any(set(a["fuentes_ids"]) - fuentes for a in corregido["explicacion_docente"]):
                raise ValueError("La explicación sucesora tiene fuentes huérfanas")
        errores = validar_recorrido(paquete)
        if errores:
            raise ValueError(f"La corrección tiene materiales incompletos: {errores}")
        resultado[fila_id] = entrada
    return resultado


def _render_recorrido(paquete: dict) -> dict[str, bytes]:
    with tempfile.TemporaryDirectory(prefix="ciencias-materiales-") as temporal:
        carpeta = Path(temporal).resolve() / "materiales"
        materializar_recorrido(paquete, carpeta)
        return {p.name: p.read_bytes() for p in carpeta.iterdir() if p.is_file()}


def _comprobar_hojas(paquete: dict, carpeta: Path) -> None:
    for nombre_archivo, esperado in _render_recorrido(paquete).items():
        if _propio(carpeta, nombre_archivo).read_bytes() != esperado:
            raise ValueError(f"La hoja no conserva el contenido del recorrido: {nombre_archivo}")


def _evaluaciones(carpeta: Path | None, unidades: dict[str, dict]) -> dict[str, dict]:
    from goes_science_kg.clases.complementaria import EvaluacionUnidad, validar_evaluacion

    if carpeta is None or not (carpeta / "evaluaciones_correcciones.json").is_file():
        return {}
    entradas = json.loads(_propio(carpeta, "evaluaciones_correcciones.json").read_bytes())
    resultado = {}
    for entrada in entradas:
        unidad_id = entrada["unidad_id"]
        if unidad_id not in unidades or unidad_id in resultado:
            raise ValueError("La evaluación sucesora repite o desconoce una unidad")
        anterior = unidades[unidad_id]["evaluacion"]
        if entrada["evaluacion_sha256_anterior"] != sha(serializar(anterior)):
            raise ValueError("La evaluación no corresponde al antecedente exacto")
        nueva = json.loads(_propio(carpeta, entrada["evaluacion_json"]).read_bytes())
        errores = validar_evaluacion(
            EvaluacionUnidad.model_validate(nueva), unidad_id, {item["fila_id"] for item in anterior["items"]}
        )
        if errores:
            raise ValueError(f"La evaluación sucesora no conserva cobertura o cálculos: {errores}")
        resultado[unidad_id] = {"datos": nueva, "archivo": entrada["evaluacion_json"]}
    return resultado


def _enlaces(destino: Path) -> list[dict]:
    errores = []
    parser = MarkdownIt()
    for archivo in sorted(destino.rglob("*.md")):
        for bloque in parser.parse(archivo.read_text(encoding="utf-8")):
            for token in bloque.children or []:
                if token.type != "link_open":
                    continue
                enlace = token.attrGet("href") or ""
                url = urlsplit(enlace)
                if url.scheme or url.netloc or not url.path:
                    continue
                relativa = posixpath.normpath(
                    posixpath.join(archivo.relative_to(destino).parent.as_posix(), unquote(url.path))
                )
                if relativa.startswith("../") or not (destino / relativa).is_file():
                    errores.append({"archivo": archivo.relative_to(destino).as_posix(), "destino": enlace})
    return errores


def _cotejar_dictamenes(destino: Path, catalogo: dict) -> list[str]:
    candidatos = [c["archivo"] + ".json" for c in catalogo["clases"] if c["estado"] == "sucesor_local_con_correccion"]
    candidatos += [
        e["archivo"].replace(".docente.md", ".json")
        for e in catalogo["complementos"]
        if e.get("estado") == "sucesor_local_con_correccion"
    ]
    candidatos += [r["archivo"] for r in [*catalogo["recorridos"], *catalogo.get("modulos_adicionales", [])]]
    identidades = {}
    for relativa in candidatos:
        archivo = _propio(destino, relativa)
        datos = json.loads(archivo.read_bytes())
        identidad = datos.get("id", datos.get("unidad_id"))
        if identidad in identidades:
            raise ValueError("Una representación duplicada no cuenta como otro paquete revisado")
        identidades[identidad] = digest(archivo)
    dictamenes = sorted((destino / "auditoria/revisiones").glob("*.json"))
    revisadas = set()
    for archivo in dictamenes:
        dictamen = json.loads(_propio(destino, archivo.relative_to(destino).as_posix()).read_bytes())
        if dictamen.get("estado") != "favorable_en_alcance_documental":
            raise ValueError("El dictamen no cierra la revisión documental")
        for revision in [*dictamen.get("archivos", []), *dictamen.get("recorridos", [])]:
            identidad = revision["id"]
            esperado = revision.get("sha256", revision.get("documento_canonico_sha256"))
            if (
                identidades.get(identidad) != esperado
                or revision.get("hallazgos_abiertos")
                or revision.get("estado") != "favorable_en_alcance_documental"
            ):
                raise ValueError("El material entregado no conserva la versión revisada sin hallazgos abiertos")
            revisadas.add(identidad)
    if dictamenes and revisadas != set(identidades):
        raise ValueError("Las revisiones no cubren exactamente los paquetes nuevos de la edición")
    return sorted(revisadas)


def validar(destino: Path) -> dict:
    """Verify the exact inventory, retained exclusions, and every generated internal Markdown link."""
    manifest = json.loads(_propio(destino, "manifest.json").read_bytes())
    if manifest["version"] != VERSION or manifest["id"] != sha(
        serializar({k: v for k, v in manifest.items() if k != "id"})
    ):
        raise ValueError("La identidad de la edición cambió")
    reales = {p.relative_to(destino).as_posix() for p in destino.rglob("*") if p.is_file()}
    if reales != set(manifest["archivos"]) | {"manifest.json"}:
        raise ValueError("La edición no conserva su inventario exacto")
    for relativa, meta in manifest["archivos"].items():
        archivo = _propio(destino, relativa)
        if archivo.stat().st_size != meta["bytes"] or digest(archivo) != meta["sha256"]:
            raise ValueError(f"El archivo no corresponde al inventario: {relativa}")
    catalogo = json.loads((destino / "catalogo.json").read_bytes())
    retenidos = json.loads((destino / "pendientes/retenidos.json").read_bytes())
    pendientes = json.loads((destino / "pendientes/objetivos_sin_guion.json").read_bytes())
    clases = [c["id"] for c in catalogo["clases"]]
    if len(clases) != len(set(clases)) or set(clases) & {p["fila_id"] for p in pendientes}:
        raise ValueError("El catálogo repite clases o presenta un objetivo pendiente como disponible")
    conteos = {
        "clases": len(clases),
        "unidades": len(catalogo["unidades"]),
        "retenidos": len(retenidos),
        "objetivos_sin_guion": len(pendientes),
        "recorridos": len(catalogo["recorridos"]),
        "modulos_adicionales": len(catalogo.get("modulos_adicionales", [])),
        "correcciones_cientificas": sum(c["estado"] == "sucesor_local_con_correccion" for c in catalogo["clases"]),
    }
    if any(manifest["resumen"].get(k) != v for k, v in conteos.items()):
        raise ValueError("Los denominadores declarados no corresponden al contenido")
    if manifest["mediciones"] != {"carga_cognitiva": "no_medida", "eficacia_en_aula": "no_medida"}:
        raise ValueError("La edición de materiales no aporta observaciones para afirmar carga o eficacia medidas")
    for clase in catalogo["clases"]:
        for sufijo in (".docente.md", ".estudiante.md", ".json"):
            _propio(destino, clase["archivo"] + sufijo)
        if clase["estado"] == "sucesor_local_con_correccion":
            paquete = json.loads(_propio(destino, clase["archivo"] + ".json").read_bytes())
            esperados = _render_recorrido(paquete)
            for original, sufijo in (
                ("docente.md", ".docente.md"),
                ("estudiante.md", ".estudiante.md"),
                ("diagnostico_estudiante.md", ".diagnostico.md"),
                ("comprobacion_estudiante.md", ".comprobacion.md"),
            ):
                if _propio(destino, clase["archivo"] + sufijo).read_bytes() != esperados[original]:
                    raise ValueError("La clase corregida no conserva sus cuatro hojas canónicas")
    for entrada in [*catalogo["recorridos"], *catalogo.get("modulos_adicionales", [])]:
        archivo_recorrido = _propio(destino, entrada["archivo"])
        paquete = json.loads(archivo_recorrido.read_bytes())
        errores = validar_recorrido(paquete)
        if errores:
            raise ValueError(f"Recorrido incompleto: {errores}")
        _comprobar_hojas(paquete, archivo_recorrido.parent)
    aprobados = {(a["tipo"], a["id"]) for a in catalogo["complementos"]}
    if aprobados & {(r["tipo"], r["id"]) for r in retenidos}:
        raise ValueError("Un contenido retenido aparece como complemento aprobado")
    if manifest.get("revision_documental", []) != _cotejar_dictamenes(destino, catalogo):
        raise ValueError("El resumen de revisión no corresponde a los dictámenes")
    enlaces = _enlaces(destino)
    if enlaces:
        raise ValueError(f"Hay enlaces internos incompletos: {enlaces[:5]}")
    return manifest


def _comprimir(destino: Path, archivo: Path) -> None:
    with zipfile.ZipFile(archivo, "x", compression=zipfile.ZIP_DEFLATED) as zip_:
        for origen in sorted(p for p in destino.rglob("*") if p.is_file()):
            info = zipfile.ZipInfo(origen.relative_to(destino).as_posix(), date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            with origen.open("rb") as entrada, zip_.open(info, "w", force_zip64=True) as salida:
                shutil.copyfileobj(entrada, salida)


def compilar(
    raiz: Path,
    archivo_base: Path,
    destino: Path,
    *,
    ciencias: Path | None = None,
    recorridos: Path | None = None,
    revisiones: Path | None = None,
    archivo_zip: Path | None = None,
) -> dict:
    """Create a complete local edition, preserving the published ZIP and its original receipts."""
    destino = destino.resolve()
    destino_generado(destino / "manifest.json", raiz=raiz)
    if destino.exists() or any(p.is_symlink() for p in (destino, *destino.parents)):
        raise ValueError("La edición requiere una carpeta nueva y propia")
    if archivo_zip:
        archivo_zip = destino_generado(archivo_zip, extension=".zip", raiz=raiz)
        if archivo_zip.exists() or archivo_zip.is_relative_to(destino):
            raise ValueError("El ZIP requiere un archivo nuevo fuera de la carpeta de edición")
    recibos = {n: json.loads((raiz / f"config/{n}.lock.json").read_bytes()) for n in RECIBOS}
    recibo = recibos["clases_ciencias"]
    base = validar_base(archivo_base)
    if digest(archivo_base) != recibo["objeto"]["sha256"] or base["id"] != recibo["entrega_id"]:
        raise ValueError("El ZIP no corresponde al recibo de entrega vigente")
    complementos = leer_publicada(raiz)
    with zipfile.ZipFile(archivo_base) as original:
        catalogo_original = json.loads(original.read("catalogo.json"))
        materiales = [json.loads(original.read(r["archivo"])) for r in catalogo_original]
    clases = {m["fila_id"]: m for m in materiales if m["tipo"] == "guion_clase"}
    unidades = [m for m in materiales if m["tipo"] == "guion_unidad"]
    correcciones = _correcciones(ciencias, clases)
    evaluaciones_corregidas = _evaluaciones(ciencias, complementos["unidades"])
    destino.mkdir(parents=True)
    escritura = _Escritura(destino)
    escritura.copiar(archivo_base, "antecedentes/guiones_publicados.zip")
    if recibos["complementos_ciencias"].get("ruta"):
        escritura.copiar(
            _propio(raiz, recibos["complementos_ciencias"]["ruta"]), "antecedentes/complementos_publicados.json"
        )
    for n in RECIBOS:
        escritura.copiar(raiz / f"config/{n}.lock.json", f"antecedentes/recibos/{n}.lock.json")
    catalogo = {
        "version": VERSION,
        "clases": [],
        "unidades": [],
        "complementos": [],
        "recorridos": [],
        "modulos_adicionales": [],
    }
    for fila_id, material in sorted(clases.items()):
        prefijo = f"clases/{nombre(fila_id)}"
        if fila_id in correcciones:
            entrada = correcciones[fila_id]
            assert ciencias is not None
            paquete = json.loads(_propio(ciencias, entrada["paquete_json"]).read_bytes())
            hojas = _render_recorrido(paquete)
            for original, sufijo in (
                ("docente.md", ".docente.md"),
                ("estudiante.md", ".estudiante.md"),
                ("diagnostico_estudiante.md", ".diagnostico.md"),
                ("comprobacion_estudiante.md", ".comprobacion.md"),
            ):
                escritura.guardar(prefijo + sufijo, hojas[original])
            escritura.copiar(_propio(ciencias, entrada["paquete_json"]), prefijo + ".json")
            estado = "sucesor_local_con_correccion"
        else:
            docente = markdown_clase(material) + "\n" + plan_cognitivo(material)
            escritura.guardar(prefijo + ".docente.md", docente)
            escritura.guardar(prefijo + ".estudiante.md", markdown_clase(material, estudiante=True))
            escritura.guardar(prefijo + ".json", material)
            estado = "antecedente_representado_con_apoyos_de_diseno"
        catalogo["clases"].append({"id": fila_id, "titulo": material["titulo"], "estado": estado, "archivo": prefijo})
    indice = [
        "# Entrega didáctica de Ciencias · edición local sucesora",
        "",
        "Materiales con separación docente/estudiante y trazabilidad a la entrega publicada. "
        "La completitud documental y las pruebas de software no acreditan eficacia en aula.",
        "",
    ]
    for material in sorted(unidades, key=lambda m: (m["grados"][0], m["asignatura"], m["titulo"])):
        archivo = f"unidades/{nombre(material['id'])}.md"
        texto_unidad = markdown_unidad(material)
        for referencia in material["documento"]["guiones"]:
            if referencia["fila_id"] in correcciones:
                prefijo = nombre(referencia["fila_id"])
                texto_unidad += f"\n### Recorrido sucesor de {referencia['titulo']}\n\n"
                texto_unidad += f"[Diagnóstico](../clases/{prefijo}.diagnostico.md) · "
                texto_unidad += f"[Refuerzo](../clases/{prefijo}.estudiante.md) · "
                texto_unidad += f"[Comprobación reservada](../clases/{prefijo}.comprobacion.md).\n"
        escritura.guardar(archivo, texto_unidad)
        faltan = len(material["documento"].get("objetivos_sin_guion_liberado", []))
        indice.append(
            f"- [{material['grados'][0]}.º · {material['asignatura']} · {material['titulo']}]({archivo}) · "
            f"{len(material['documento']['guiones'])} guiones; **{faltan} objetivos sin guion**."
        )
        catalogo["unidades"].append({"id": material["id"], "archivo": archivo, "faltantes": faltan})
    pendientes = base["procedencia"].get("objetivos_sin_guion_liberado", [])
    objetivos = {p["fila_id"]: p for p in pendientes}
    destinos = set(clases) | set(objetivos)
    for anexo in complementos["clases"].values():
        for grupo in ("ideas_previas", "continuidad"):
            destinos.update(e["fila_id"] for e in anexo["anexo"]["progresion"][grupo])
    for fila_id in sorted(destinos):
        if fila_id in clases:
            texto = f"# {clases[fila_id]['titulo']}\n\n[Guía docente](../clases/{nombre(fila_id)}.docente.md).\n"
        else:
            pendiente = objetivos.get(fila_id, {})
            texto = (
                f"# Objetivo sin guion en esta edición\n\nIdentidad: `{fila_id}`.\n\n"
                + pendiente.get(
                    "motivo",
                    "La progresión registra este destino; no hay un guion local liberado. "
                    "Solicite acompañamiento docente.",
                )
                + "\n"
            )
        escritura.guardar(f"objetivos/{nombre(fila_id)}.md", texto)
    for fila_id, registro in sorted(complementos["clases"].items()):
        archivo = f"anexos/{nombre(fila_id)}.md"
        texto = markdown_anexo_completo(registro["anexo"], registro["titulo"])
        if fila_id in correcciones:
            texto = texto.replace("(../objetivos/", "(../../objetivos/")
            texto = "# Anexo antecedente: no aplicar automáticamente al guion corregido\n\n" + texto
            archivo = f"antecedentes/anexos/{nombre(fila_id)}.md"
        escritura.guardar(archivo, texto)
        catalogo["complementos"].append(
            {"tipo": "anexo", "id": fila_id, "archivo": archivo, "aplicable_sucesor": fila_id not in correcciones}
        )
    for unidad_id, registro in sorted(complementos["unidades"].items()):
        evaluacion = (
            evaluaciones_corregidas[unidad_id]["datos"]
            if unidad_id in evaluaciones_corregidas
            else registro["evaluacion"]
        )
        for estudiante in (False, True):
            sufijo = "estudiante" if estudiante else "docente"
            escritura.guardar(
                f"evaluaciones/{nombre(unidad_id)}.{sufijo}.md",
                markdown_evaluacion(evaluacion, registro["unidad"], estudiante=estudiante),
            )
        if unidad_id in evaluaciones_corregidas:
            assert ciencias is not None
            escritura.copiar(
                _propio(ciencias, evaluaciones_corregidas[unidad_id]["archivo"]),
                f"evaluaciones/{nombre(unidad_id)}.json",
            )
        else:
            escritura.guardar(f"evaluaciones/{nombre(unidad_id)}.json", evaluacion)
        catalogo["complementos"].append(
            {
                "tipo": "evaluacion",
                "id": unidad_id,
                "archivo": f"evaluaciones/{nombre(unidad_id)}.docente.md",
                "estado": "sucesor_local_con_correccion"
                if unidad_id in evaluaciones_corregidas
                else "antecedente_representado_con_rubrica_completa",
            }
        )
    escritura.guardar("pendientes/retenidos.json", complementos["retenidos"])
    escritura.guardar("pendientes/objetivos_sin_guion.json", pendientes)
    derivados = {}
    if ciencias:
        for entrada in correcciones.values():
            hojas = _render_recorrido(json.loads(_propio(ciencias, entrada["paquete_json"]).read_bytes()))
            for campo, original in (
                ("docente_md", "docente.md"),
                ("estudiante_md", "estudiante.md"),
                ("comprobacion_md", "comprobacion_estudiante.md"),
                ("diagnostico_md", "diagnostico_estudiante.md"),
            ):
                if campo in entrada:
                    destino_derivado = "correcciones/" + entrada[campo]
                    if destino_derivado in derivados:
                        raise ValueError("Dos correcciones comparten una hoja de salida")
                    derivados[destino_derivado] = hojas[original]
    for carpeta, prefijo in ((ciencias, "correcciones"), (recorridos, "recorridos")):
        if carpeta:
            for origen in sorted(p for p in carpeta.rglob("*") if p.is_file()):
                relativa = origen.relative_to(carpeta).as_posix()
                destino_relativo = f"{prefijo}/{relativa}"
                if prefijo == "correcciones" and relativa.startswith("canonicos/"):
                    vigentes = [str(PurePosixPath(c["paquete_json"]).parent) + "/" for c in correcciones.values()]
                    if not any(relativa.startswith(p) for p in vigentes):
                        continue
                if destino_relativo in derivados:
                    escritura.guardar(destino_relativo, derivados.pop(destino_relativo))
                    continue
                if "__pycache__" in origen.parts or origen.suffix in {".py", ".pyc"}:
                    continue
                if prefijo == "correcciones" and origen.parent == carpeta and origen.suffix == ".md":
                    continue
                escritura.copiar(_propio(carpeta, relativa), destino_relativo)
                if prefijo == "recorridos" and origen.name == "recorrido.json":
                    catalogo["recorridos"].append({"archivo": f"{prefijo}/{relativa}"})
    for destino_relativo, contenido in derivados.items():
        escritura.guardar(destino_relativo, contenido)
    if revisiones:
        for archivo in sorted(revisiones.glob("*.json")):
            escritura.copiar(_propio(revisiones, archivo.name), f"auditoria/revisiones/{archivo.name}")
    if ciencias:
        usados = {c["paquete_json"] for c in correcciones.values()}
        for origen in sorted(ciencias.glob("CIEN-*.json")):
            if origen.name in usados:
                continue
            paquete = json.loads(_propio(ciencias, origen.name).read_bytes())
            if paquete.get("origen", {}).get("fila_id") in correcciones:
                continue
            hojas = _render_recorrido(paquete)
            prefijo = f"modulos/{nombre(paquete['id'])}"
            for nombre_archivo, contenido in hojas.items():
                escritura.guardar(f"{prefijo}/{nombre_archivo}", contenido)
            catalogo["modulos_adicionales"].append(
                {"archivo": f"{prefijo}/recorrido.json", "titulo": paquete["titulo"]}
            )
    pedagogia = raiz / "docs/PEDAGOGIA_CIENCIAS_V4.md"
    if pedagogia.is_file():
        escritura.copiar(pedagogia, "PEDAGOGIA_CIENCIAS.md")
        indice += ["", "[Protocolo pedagógico y medición del esfuerzo](PEDAGOGIA_CIENCIAS.md)."]
    indice += ["", "## Recorridos finales", ""]
    if recorridos:
        for entrada in catalogo["recorridos"]:
            carpeta = PurePosixPath(entrada["archivo"]).parent.as_posix()
            indice.append(f"- [{carpeta.removeprefix('recorridos/')}]({carpeta}/docente.md).")
    if catalogo["modulos_adicionales"]:
        indice += ["", "## Módulos nuevos de aplicación", ""]
        for entrada in catalogo["modulos_adicionales"]:
            carpeta = PurePosixPath(entrada["archivo"]).parent.as_posix()
            indice.append(f"- [{entrada['titulo']}]({carpeta}/docente.md).")
    indice += [
        "",
        "## Cobertura pendiente",
        "",
        f"Los {len(pendientes)} objetivos sin guion y las "
        f"{len(complementos['retenidos'])} piezas retenidas conservan identidad y motivos. "
        "Esta edición no los presenta como nuevos contenidos aprobados.",
        "",
        "[Catálogo íntegro](catalogo.json) · [Retenidos](pendientes/retenidos.json) · "
        "[Objetivos sin guion](pendientes/objetivos_sin_guion.json).",
        "",
    ]
    escritura.guardar("INDICE.md", "\n".join(indice))
    escritura.guardar("catalogo.json", catalogo)
    resumen = {
        "clases": len(clases),
        "unidades": len(unidades),
        "correcciones_cientificas": len(correcciones),
        "evaluaciones_corregidas": len(evaluaciones_corregidas),
        "anexos_antecedentes_aprobados": len(complementos["clases"]),
        "evaluaciones_antecedentes_aprobadas": len(complementos["unidades"]),
        "retenidos": len(complementos["retenidos"]),
        "objetivos_sin_guion": len(pendientes),
        "recorridos": len(catalogo["recorridos"]),
        "modulos_adicionales": len(catalogo["modulos_adicionales"]),
    }
    manifest = {
        "version": VERSION,
        "procedencia": {"guiones": base["id"], "complementos": complementos["id"]},
        "resumen": resumen,
        "mediciones": {"carga_cognitiva": "no_medida", "eficacia_en_aula": "no_medida"},
        "archivos": escritura.archivos,
        "revision_documental": _cotejar_dictamenes(destino, catalogo),
    }
    manifest["id"] = sha(serializar(manifest))
    (destino / "manifest.json").write_bytes(serializar(manifest))
    validar(destino)
    if archivo_zip:
        archivo_zip.parent.mkdir(parents=True, exist_ok=True)
        _comprimir(destino, archivo_zip)
    return manifest
