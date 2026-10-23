"""La tabla publicada debe coincidir con el indicador, semana y fechas de su recibo primario."""

from copy import deepcopy

import pytest

from goes_science_kg.clases.insumos import archivos_insumos
from goes_science_kg.materiales.compilacion import serializar, sha


def expediente(tmp_path, *, modificar=None):
    url = "https://www.salud.gob.sv/wp-content/uploads/download-manager-files/Boletin_epidemiologico_SE242022.pdf"
    recibo = {
        "version": "recibo-vista-textual-web-1",
        "url": url,
        "fragmentos_literales": ["SE24", "1 Casos con sospecha de dengue 527"],
        "periodo": {"desde": "2022-06-12", "hasta": "2022-06-18"},
    }
    fuente = {
        "url": url,
        "recibo": "recibo.json",
        "original_pdf_verificado": False,
        "anclas_verificadas": recibo["fragmentos_literales"],
    }
    fila = {"semana": 24, "desde": "2022-06-12", "hasta": "2022-06-18", "sospechas_dengue": 527}
    if modificar:
        modificar(fila, fuente, recibo)
    raw = serializar(recibo)
    (tmp_path / "recibo.json").write_bytes(raw)
    fuente["recibo_sha256"] = sha(raw)
    datos = {"version": "insumo-tabular-clases-1", "fuentes": [fuente], "filas": [fila]}
    datos["id"] = sha(serializar(datos))
    raw = serializar(datos)
    (tmp_path / "datos.json").write_bytes(raw)
    return {
        "insumos_tabulares": [{"ruta": "datos.json", "bytes": len(raw), "sha256": sha(raw)}],
        "filas": [{"fila_id": "f1", "datos_contextuales": deepcopy(datos)}],
    }


def test_exporta_tabla_y_recibo_con_limite_de_verificacion(tmp_path):
    p = expediente(tmp_path)
    assert set(archivos_insumos(tmp_path, p)) == {"datos.json", "recibo.json"}


@pytest.mark.parametrize("campo,valor", [("semana", 25), ("desde", "2022-06-19"), ("sospechas_dengue", 539)])
def test_rechaza_tabla_rehasheada_que_no_corresponde_al_recibo(tmp_path, campo, valor):
    p = expediente(tmp_path, modificar=lambda fila, fuente, recibo: fila.update({campo: valor}))
    with pytest.raises(ValueError, match="no corresponde"):
        archivos_insumos(tmp_path, p)


def test_no_convierte_vista_web_en_pdf_verificado(tmp_path):
    p = expediente(tmp_path, modificar=lambda fila, fuente, recibo: fuente.update(original_pdf_verificado=True))
    with pytest.raises(ValueError, match="no acredita"):
        archivos_insumos(tmp_path, p)


def test_rechaza_contexto_tabular_distinto_a_archivo_original(tmp_path):
    p = expediente(tmp_path)
    p["filas"][0]["datos_contextuales"]["filas"][0]["sospechas_dengue"] = 999
    with pytest.raises(ValueError, match="difieren"):
        archivos_insumos(tmp_path, p)
