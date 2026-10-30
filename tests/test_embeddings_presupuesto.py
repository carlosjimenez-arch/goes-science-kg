"""Enforce one durable embedding budget across instances without external requests."""

from __future__ import annotations

import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from types import SimpleNamespace

import pytest

from goes_science_kg.recuperacion.vertex_embeddings import PresupuestoEmbeddingsAgotado, VertexEmbeddings


@pytest.mark.parametrize("limites", [{"max_requests": 1}, {"max_requests": 2, "max_usd": 0.0004}])
def test_instancias_concurrentes_comparten_limites_y_resumen_durable(tmp_path, limites):
    llamadas = []

    def generar(**campos):
        llamadas.append(campos)
        return SimpleNamespace(
            embeddings=[SimpleNamespace(values=[1.0] * 768, statistics=SimpleNamespace(token_count=4, truncated=False))]
        )

    opciones = {
        "proyecto": "proyecto-prueba",
        "directorio_cache": tmp_path / "cache",
        "ledger": tmp_path / "ledger.jsonl",
        "cliente": SimpleNamespace(models=SimpleNamespace(embed_content=generar)),
        **limites,
    }
    proveedores = [VertexEmbeddings(**opciones), VertexEmbeddings(**opciones)]
    barrera = Barrier(2)

    def solicitar(i):
        barrera.wait(timeout=10)
        try:
            proveedores[i].vectorizar_texto(f"texto sintético {i}", tarea="RETRIEVAL_DOCUMENT")
        except PresupuestoEmbeddingsAgotado:
            return "bloqueada"
        return "completada"

    with ThreadPoolExecutor(max_workers=2) as ejecutor:
        resultados = list(ejecutor.map(solicitar, range(2)))
    assert sorted(resultados) == ["bloqueada", "completada"]
    assert len(llamadas) == 1
    eventos = [json.loads(linea) for linea in opciones["ledger"].read_text().splitlines()]
    assert sum(e["evento"] == "reserva" for e in eventos) == 1
    for proveedor in proveedores:
        resumen = proveedor.resumen()
        assert resumen["requests_reservadas"] == resumen["completadas"] == 1
        assert resumen["tokens_reservados"] == 2048 and resumen["tokens_reportados"] == 4
        assert resumen["usd_reservado"] <= resumen["limite_usd"]


def test_procesos_distintos_reservan_en_el_mismo_limite_sin_invocar_proveedor(tmp_path):
    codigo = """
import sys
from pathlib import Path
from goes_science_kg.recuperacion.vertex_embeddings import VertexEmbeddings, PresupuestoEmbeddingsAgotado
raiz = Path(sys.argv[1])
proveedor = VertexEmbeddings(proyecto='prueba', directorio_cache=raiz / 'cache', ledger=raiz / 'ledger', max_requests=1)
print('listo', flush=True)
sys.stdin.readline()
try:
    proveedor._reservar(sys.argv[2], 2048)
except PresupuestoEmbeddingsAgotado:
    print('bloqueada')
else:
    print('reservada')
"""
    procesos = [
        subprocess.Popen(
            [sys.executable, "-c", codigo, str(tmp_path), str(i)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for i in range(2)
    ]
    try:
        for proceso in procesos:
            assert proceso.stdout.readline().strip() == "listo"
        for proceso in procesos:
            proceso.stdin.write("reservar\n")
            proceso.stdin.flush()
        resultados = []
        for proceso in procesos:
            salida, error = proceso.communicate(timeout=30)
            assert proceso.returncode == 0, error
            resultados.append(salida.strip())
        assert sorted(resultados) == ["bloqueada", "reservada"]
        eventos = [json.loads(linea) for linea in (tmp_path / "ledger").read_text().splitlines()]
        assert len(eventos) == 1 and eventos[0]["evento"] == "reserva"
    finally:
        for proceso in procesos:
            if proceso.poll() is None:
                proceso.kill()
            proceso.communicate()
