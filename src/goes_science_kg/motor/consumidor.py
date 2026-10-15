"""Consumidor local de referencia: importa versiones inmutables y activa una por puntero atómico."""

from __future__ import annotations

import os
import re
import shutil
import tempfile
from pathlib import Path

from goes_science_kg.motor.archivos import canonico, destino_seguro, leer
from goes_science_kg.motor.validacion import cargar_entrega, validar


def activar(almacen: str | Path, id_entrega: str) -> dict:
    almacen = destino_seguro(Path(almacen))
    if not re.fullmatch(r"[a-f0-9]{64}", id_entrega):
        raise ValueError("id de entrega inválido")
    carpeta = almacen / "entregas" / id_entrega
    if (almacen / "entregas").is_symlink():
        raise ValueError("almacén con directorio de versiones simbólico")
    rep = validar(carpeta)
    if rep["id_entrega"] != id_entrega:
        raise ValueError("la carpeta no corresponde al id de entrega")
    puntero = {"id_entrega": id_entrega, "version": rep["version"]}
    actual = almacen / "activo.json"
    if actual.exists() and leer(actual) == puntero:
        return puntero
    nombre = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=almacen, delete=False,
                                         prefix=".activo-") as f:
            nombre = Path(f.name)
            f.write(canonico(puntero) + "\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(nombre, actual)
    finally:
        if nombre and nombre.exists():
            nombre.unlink()
    return puntero


def importar(entrega: str | Path, almacen: str | Path, activar_al_importar: bool = True) -> dict:
    entrega = Path(entrega)
    almacen = destino_seguro(Path(almacen))
    if almacen.is_relative_to(entrega.resolve()) or entrega.resolve().is_relative_to(almacen):
        raise ValueError("el almacén y la entrega no pueden contenerse")
    rep = validar(entrega)
    versiones = almacen / "entregas"
    if versiones.is_symlink():
        raise ValueError("directorio de versiones simbólico")
    versiones.mkdir(parents=True, exist_ok=True)
    destino = versiones / rep["id_entrega"]
    creada = not destino.exists()
    if creada:
        with tempfile.TemporaryDirectory(prefix=".importar-", dir=versiones) as temporal:
            candidato = Path(temporal) / "entrega"
            shutil.copytree(entrega, candidato)
            if validar(candidato)["id_entrega"] != rep["id_entrega"]:
                raise ValueError("la entrega cambió durante la importación")
            try:
                os.rename(candidato, destino)
            except OSError:
                if not destino.exists():
                    raise
                creada = False
                if validar(destino)["id_entrega"] != rep["id_entrega"]:
                    raise ValueError("versión existente con identidad distinta") from None
    else:
        if validar(destino)["id_entrega"] != rep["id_entrega"]:
            raise ValueError("versión existente con identidad distinta")
    if activar_al_importar:
        activar(almacen, rep["id_entrega"])
    return {**rep, "creada": creada, "activada": activar_al_importar}


def consultar(almacen: str | Path, identificador: str, perfil: str = "consulta",
              incluir_propuestas: bool = False) -> dict:
    """Resuelve alias exactos. El perfil de autoría devuelve solo componentes permitidos y declara las omisiones."""
    if perfil not in ("consulta", "autoria"):
        raise ValueError("perfil no habilitado: solo consulta y autoria; aula no disponible")
    almacen = Path(almacen)
    if (almacen / "entregas").is_symlink():
        raise ValueError("directorio de versiones simbólico")
    id_entrega = leer(almacen / "activo.json")["id_entrega"]
    if not re.fullmatch(r"[a-f0-9]{64}", id_entrega):
        raise ValueError("puntero activo inválido")
    carpeta = almacen / "entregas" / id_entrega
    rep = validar(carpeta)
    m, datos = cargar_entrega(carpeta)
    if m.id_entrega != id_entrega:
        raise ValueError("puntero activo no coincide con la entrega")
    temas = {t.id: t for t in datos["temas"]}
    aliases = {a: t.id for t in temas.values() for a in t.aliases}
    tid = aliases.get(identificador, "TEMA:" + identificador if identificador.startswith("G") else identificador)
    if tid not in temas:
        raise ValueError(f"tema o alias inexistente: {identificador}")
    t = temas[tid]
    if perfil == "autoria" and not t.en_alcance_ciencias:
        raise ValueError("tema fuera del alcance de Ciencias: disponible solo para consulta")
    p = next((p for p in datos["paquetes"] if p.tema_id == tid), None)
    comps = {c.id: c for c in datos["componentes"]}
    seleccion = {i for ids in p.componentes.values() for i in ids} if p else set()
    pendientes = set(seleccion)
    while pendientes:
        i = pendientes.pop()
        nuevos = set(comps[i].componentes_requeridos) - seleccion
        seleccion.update(nuevos)
        pendientes.update(nuevos)
    omitidos = []
    incluidos = []
    for i in sorted(seleccion):
        c = comps[i]
        motivos = list(c.usos.motivos_autoria) if perfil == "autoria" else []
        if perfil == "autoria" and c.tipo == "refuerzo" and not incluir_propuestas:
            motivos.append("propuesta_goes_no_seleccionada")
        if motivos:
            omitidos.append({"id": i, "motivos": motivos})
        else:
            incluidos.append(c.model_dump(mode="json"))
    ids_incluidos = {c["id"] for c in incluidos}
    paquete = p.model_dump(mode="json") if p else None
    if paquete:
        paquete["componentes"] = {k: [i for i in ids if i in ids_incluidos] for k, ids in p.componentes.items()}
    return {"id_entrega": rep["id_entrega"], "perfil": perfil, "tema": t.model_dump(mode="json"),
            "analisis": [a.model_dump(mode="json") for a in datos["analisis"] if a.tema_id == tid],
            "paquete": paquete, "componentes": incluidos, "omitidos": omitidos,
            "aula_habilitada": False, "aviso": "Autoría asistida requiere completar datos y revisión docente."}
