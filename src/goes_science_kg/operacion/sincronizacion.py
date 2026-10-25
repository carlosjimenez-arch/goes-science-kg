"""Keep the local corpus, teacher library, and class delivery aligned with their pinned GCS receipts."""

from __future__ import annotations

import json
import tempfile
import zipfile
from pathlib import Path

from goes_science_kg.motor.contratos import huella
from goes_science_kg.operacion import datos_externos as datos

RECIBO_CORPUS = "config/datos_ciencias.lock.json"
RECIBO_MATERIALES = "config/materiales_ciencias.lock.json"
RECIBO_CLASES = "config/clases_ciencias.lock.json"
RECIBO_PREPARACIONES = "config/materiales_preparaciones.lock.json"
DIR_MATERIALES = "data/materiales"
DIR_CLASES = "data/descargas/clases-v4"
DIR_PREPARACIONES = "data/materiales_preparaciones"


def _guardar(destino: Path, contenido: dict, *, reemplazar: bool = False) -> None:
    destino.parent.mkdir(parents=True, exist_ok=True)
    texto = json.dumps(contenido, ensure_ascii=False, indent=2) + "\n"
    if not reemplazar:
        with destino.open("x", encoding="utf-8") as stream:
            stream.write(texto)
        return
    temporal = destino.with_name(f".{destino.name}.tmp")
    temporal.write_text(texto, encoding="utf-8")
    temporal.replace(destino)


def subir_paquete(almacen, preparado: dict) -> dict:
    """Upload a prepared corpus package, its inventory, and its descriptor as new verified objects."""
    if preparado.get("version") != datos.VERSION:
        raise ValueError("Plan incompatible")
    local = preparado["paquete_local"]
    archivo = Path(local["archivo"])
    if datos.digest(archivo) != local["sha256"]:
        raise ValueError("El paquete cambió después de prepararse")
    objeto = almacen.crear(archivo, f"repositorio/objetos/{local['sha256']}.zip")
    with tempfile.TemporaryDirectory(prefix="goes-datos-manifest-") as temporal:
        inventario = Path(temporal) / "inventario.json"
        with zipfile.ZipFile(archivo) as zip_:
            inventario.write_bytes(zip_.read("MANIFEST_RESPALDO.json"))
        manifest = json.loads(inventario.read_bytes())
        comprobante = {
            "version": datos.VERSION,
            "paquete": objeto,
            "inventario": almacen.crear(inventario, f"repositorio/inventarios/{local['sha256']}.json"),
            "huella_inventario": local["huella_inventario"],
            "archivos": local["archivos"],
            "bytes_originales": manifest["bytes_sin_comprimir"],
            "montajes": preparado["montajes"],
            "enlaces": preparado["enlaces"],
            "identidad_ledger": preparado["identidad_ledger"],
            "max_bytes_sin_comprimir": datos.limite_bytes(preparado.get("max_bytes_sin_comprimir")),
        }
        descriptor = Path(temporal) / "recibo.json"
        _guardar(descriptor, comprobante)
        comprobante["descriptor"] = almacen.crear(descriptor, f"repositorio/recibos/{local['sha256']}.json")
    return comprobante


def descargar_corpus(almacen, comprobante: dict, destino: Path) -> dict:
    """Download the pinned corpus generation and restore it into a new directory, verifying every file."""
    with tempfile.TemporaryDirectory(prefix="goes-datos-gcs-") as temporal:
        archivo = Path(temporal) / "datos.zip"
        almacen.descargar(comprobante["paquete"], archivo)
        return datos.restaurar(archivo, destino, comprobante)


def restaurar_en_repo(almacen, comprobante: dict, raiz: Path) -> dict:
    """Restore the corpus into the checkout paths and rebind budget checkpoints to the restored ledger."""
    from goes_science_kg.operacion.presupuestos_restaurados import migrar_presupuestos

    with tempfile.TemporaryDirectory(prefix="goes-datos-restaurados-") as temporal:
        restaurado = Path(temporal) / "corpus"
        resultado = descargar_corpus(almacen, comprobante, restaurado)
        datos.incorporar(restaurado, raiz, comprobante["montajes"])
        resultado["presupuestos"] = migrar_presupuestos(raiz, comprobante, resultado["sqlite_verificados"])
    return resultado


class Sincronizador:
    """Compare, download, and publish every pinned data component of the product through GCS."""

    def __init__(self, raiz: Path, almacen) -> None:
        self.raiz = raiz.resolve()
        self.almacen = almacen

    def _recibo(self, rel: str) -> dict | None:
        archivo = self.raiz / rel
        return json.loads(archivo.read_bytes()) if archivo.is_file() else None

    def estado(self) -> dict:
        """Report, without downloading packages, which components are present, missing, or partial."""
        corpus = self._recibo(RECIBO_CORPUS)
        montajes = corpus["montajes"] if corpus else []
        presentes = [m for m in montajes if (self.raiz / m).exists()]
        materiales = self._recibo(RECIBO_MATERIALES)
        manifest = self.raiz / DIR_MATERIALES / "manifest.json"
        local = json.loads(manifest.read_bytes()).get("id") if manifest.is_file() else None
        clases = self._recibo(RECIBO_CLASES)
        preparaciones = self._recibo(RECIBO_PREPARACIONES)
        manifest_prep = self.raiz / DIR_PREPARACIONES / "manifest.json"
        local_prep = json.loads(manifest_prep.read_bytes()).get("id") if manifest_prep.is_file() else None
        return {
            "corpus": {
                "recibo": corpus["paquete"]["sha256"] if corpus else None,
                "estado": "sin_recibo"
                if not corpus
                else "completo"
                if len(presentes) == len(montajes)
                else "ausente"
                if not presentes
                else "parcial",
                "montajes_presentes": len(presentes),
                "montajes": len(montajes),
            },
            "materiales": {
                "recibo": materiales["biblioteca_id"] if materiales else None,
                "local": local,
                "estado": "sin_recibo"
                if not materiales
                else "vigente"
                if local == materiales["biblioteca_id"]
                else "ausente"
                if local is None
                else "distinto",
            },
            "preparaciones": {
                "recibo": preparaciones["biblioteca_id"] if preparaciones else None,
                "local": local_prep,
                "estado": "sin_recibo"
                if not preparaciones
                else "vigente"
                if local_prep == preparaciones["biblioteca_id"]
                else "ausente"
                if local_prep is None
                else "distinto",
            },
            "clases": {
                "recibo": clases["entrega_id"] if clases else None,
                "estado": "sin_publicar"
                if not clases
                else "presente"
                if (self.raiz / DIR_CLASES).exists()
                else "ausente",
            },
        }

    def verificar_corpus(self) -> dict:
        """Hash every local corpus file against the remote inventory; consistent SQLite copies are only counted."""
        comprobante = self._recibo(RECIBO_CORPUS)
        if not comprobante:
            raise ValueError("No hay recibo del corpus")
        with tempfile.TemporaryDirectory(prefix="goes-datos-inventario-") as temporal:
            archivo = Path(temporal) / "inventario.json"
            self.almacen.descargar(comprobante["inventario"], archivo)
            inventario = json.loads(archivo.read_bytes())
        if huella(inventario["archivos"]) != comprobante["huella_inventario"]:
            raise ValueError("El inventario remoto no corresponde al recibo")
        identicos, distintos, faltan, sqlite = 0, [], [], 0
        for rel, meta in sorted(inventario["archivos"].items()):
            local = self.raiz / rel
            if not local.is_file():
                faltan.append(rel)
            elif meta.get("copia_sqlite_consistente"):
                sqlite += 1
            elif datos.digest(local) == meta["sha256"]:
                identicos += 1
            else:
                distintos.append(rel)
        return {
            "archivos": len(inventario["archivos"]),
            "identicos": identicos,
            "sqlite_operativos": sqlite,
            "distintos": distintos[:50],
            "total_distintos": len(distintos),
            "faltan": faltan[:50],
            "total_faltan": len(faltan),
        }

    def sincronizar(self) -> dict:
        """Download every missing component; refuse partial or divergent states instead of overwriting."""
        estado = self.estado()
        acciones = {}
        if estado["corpus"]["estado"] == "parcial":
            raise ValueError("El corpus local está incompleto; restaure en una carpeta nueva y compare antes de mover")
        if estado["corpus"]["estado"] == "ausente":
            acciones["corpus"] = restaurar_en_repo(self.almacen, self._recibo(RECIBO_CORPUS), self.raiz)
            estado = self.estado()
        if estado["materiales"]["estado"] == "distinto":
            raise ValueError("La biblioteca local no coincide con su recibo; no se sobrescribe")
        if estado["materiales"]["estado"] == "ausente":
            from goes_science_kg.materiales.publicacion import restaurar as restaurar_materiales

            manifest = restaurar_materiales(self._recibo(RECIBO_MATERIALES), self.raiz / DIR_MATERIALES, self.almacen)
            acciones["materiales"] = {"biblioteca_id": manifest["id"], "materiales": manifest["materiales"]}
        if estado["preparaciones"]["estado"] == "distinto":
            raise ValueError("La biblioteca de preparaciones local no coincide con su recibo; no se sobrescribe")
        if estado["preparaciones"]["estado"] == "ausente":
            from goes_science_kg.materiales.publicacion import restaurar as restaurar_materiales

            manifest = restaurar_materiales(
                self._recibo(RECIBO_PREPARACIONES), self.raiz / DIR_PREPARACIONES, self.almacen
            )
            acciones["preparaciones"] = {"biblioteca_id": manifest["id"], "materiales": manifest["materiales"]}
        if estado["clases"]["estado"] == "ausente":
            from goes_science_kg.clases.publicacion import descargar as descargar_clases

            m = descargar_clases(self._recibo(RECIBO_CLASES), self.raiz / DIR_CLASES, self.almacen)
            acciones["clases"] = {"entrega_id": m["id"], "por_tipo": m["por_tipo"]}
        return {"acciones": acciones, "estado": self.estado()}

    def publicar_corpus(self, configuracion: dict, trabajo: Path) -> dict:
        """Package, upload, restore into a scratch directory, compare, and only then adopt the new receipt."""
        if trabajo.exists() and any(trabajo.iterdir()):
            raise ValueError("La carpeta de trabajo debe ser nueva o estar vacía")
        trabajo.mkdir(parents=True, exist_ok=True)
        preparado = datos.preparar(self.raiz, configuracion, trabajo / "corpus.zip")
        comprobante = subir_paquete(self.almacen, preparado)
        verificacion = descargar_corpus(self.almacen, comprobante, trabajo / "verificacion")
        if verificacion["huella_inventario"] != comprobante["huella_inventario"] or verificacion[
            "archivos_restaurados"
        ] != len(preparado["originales"]):
            raise ValueError("La restauración desde GCS no reproduce el paquete subido; no se adopta el recibo")
        anterior = self._recibo(RECIBO_CORPUS)
        if anterior:
            _guardar(trabajo / "recibo_anterior.json", anterior)
        _guardar(self.raiz / RECIBO_CORPUS, comprobante, reemplazar=True)
        return {
            "paquete": comprobante["paquete"]["sha256"],
            "generacion": comprobante["paquete"]["generacion"],
            "archivos": comprobante["archivos"],
            "recibo_anterior": anterior["paquete"]["sha256"] if anterior else None,
            "restauracion_verificada": True,
        }
