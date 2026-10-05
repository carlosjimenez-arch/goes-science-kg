import os
import subprocess
import sys

CODIGO = """
import hashlib, json
from goes_science_kg.grafo.almacen import cargar
from goes_science_kg.comunidades import comunidades_grado
from goes_science_kg.grados import subgrafo
from goes_science_kg.prerrequisitos import evidencia_orden
n, a = cargar(); ev = evidencia_orden(n, a)
_, _, d = subgrafo(6, n, a, ev)
c = comunidades_grado(6, n, a)
print(hashlib.sha256(json.dumps([d, c], ensure_ascii=False).encode()).hexdigest())
"""


def _hash(semilla: str) -> str:
    env = {**os.environ, "PYTHONHASHSEED": semilla}
    return subprocess.run([sys.executable, "-c", CODIGO], env=env, capture_output=True, text=True, check=True).stdout


def test_diagnostico_y_bloques_no_dependen_del_hash():
    assert _hash("1") == _hash("2") == _hash("12345")
