"""Compila dos expedientes reales distintos cotejando ambos contra el ledger, sin Vertex."""

from __future__ import annotations

import json
import shutil

import pytest

from goes_science_kg.clases.compilacion import compilar
from goes_science_kg.clases.fuentes import CorpusClases
from goes_science_kg.config import ruta
from goes_science_kg.materiales.almacen import Biblioteca
from goes_science_kg.materiales.compilacion import sha
from goes_science_kg.motor.registro import Registro

BASE = ruta(".")
pytestmark = pytest.mark.skipif(
    not (BASE / "data/clases_v4/seleccion_pilotos.json").is_file(), reason="Expedientes privados no restaurados"
)


def test_compila_varios_resultados_usando_el_ledger_en_todos(tmp_path):
    seleccion = json.loads((BASE / "data/clases_v4/seleccion_pilotos.json").read_bytes())
    elegidos, resultados = {}, set()
    for id_, ref in seleccion.items():
        if "/piloto_p2/" in ref["resultado"] and ref["resultado"] not in resultados:
            elegidos[id_] = ref
            resultados.add(ref["resultado"])
        if len(elegidos) == 2:
            break
    assert len(elegidos) == 2
    for ref in elegidos.values():
        for nombre in (
            ref["preparacion"],
            ref["resultado"],
            str((BASE / ref["resultado"]).parent.relative_to(BASE) / "protocolo.json"),
        ):
            destino = tmp_path / nombre
            destino.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(BASE / nombre, destino)
    archivo = "data/clases_v4/protocolos/codigo_clases_p2.zip"
    (tmp_path / archivo).parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(BASE / archivo, tmp_path / archivo)
    original = Biblioteca(BASE / "data/materiales")
    fichas = [original.detalle(i) for i in elegidos]

    class Subconjunto:
        manifest = original.manifest

        def listar(self, **_):
            return {"total": len(fichas), "materiales": fichas}

        def detalle(self, id_):
            return original.detalle(id_)

    nuevos, archivos = compilar(
        tmp_path,
        Subconjunto(),
        CorpusClases(BASE / "data/referencias_clases_2026"),
        elegidos,
        registro=Registro(BASE / "data/operaciones/registro.sqlite"),
    )
    clases = [r for r in nuevos if r["tipo"] == "guion_clase"]
    assert len(clases) == 2
    assert {c["fila_id"] for c in clases} == set(elegidos)
    auditorias = [json.loads(v) for k, v in archivos.items() if "/auditorias/" in k and "/salidas/" not in k]
    assert len(auditorias) == 2 and all(a["trazas"] for a in auditorias)
    for auditoria in auditorias:
        for traza in auditoria["trazas"]:
            assert sha(archivos[traza["archivo_salida"]]) == traza["salida_sha256"]
            assert (tmp_path / traza["archivo_salida"]).read_bytes() == archivos[traza["archivo_salida"]]
