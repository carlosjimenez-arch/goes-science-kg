"""Elegir un capítulo no aprueba una clase ni permite citar documentos inexistentes."""

import json
from types import SimpleNamespace

import pytest

from goes_science_kg.clases.enrutamiento import Rutas, catalogo_relevante, preparar_contexto
from goes_science_kg.materiales.compilacion import serializar
from goes_science_kg.motor.contratos import Evidencia
from goes_science_kg.recuperacion.lexico import IndiceLexico
from goes_science_kg.recuperacion.modelos import Documento


@pytest.fixture
def entorno():
    evidencias = {}
    for n in (1, 2):
        e = Evidencia.crear(
            f"CNXML:capitulo#p{n}",
            "Elastic stress is force divided by area. A material deforms when a force acts on it. " * n,
            {
                "url": "https://example.org/elasticity",
                "documento": "capitulo",
                "titulo": "Elasticity: Stress and Strain",
                "fuente_primaria": True,
                "libro": "college-physics-2e",
            },
            "referencia",
        )
        evidencias[e.id] = e
    indice = IndiceLexico(
        Documento(id=e.id, texto=e.texto, fuente=e.fuente, version=e.version) for e in evidencias.values()
    )
    c = SimpleNamespace(huella="corpus", evidencias=evidencias, indice=indice, verificar=lambda e: None)
    filas = [{"fila_id": "f1", "consulta_recuperacion": "bridge maximum load", "propuesta": {"objetivo": "Puente"}}]
    return c, filas


class Proveedor:
    def __init__(self, *, ajeno=False, fallo=False):
        self.ajeno, self.fallo, self.llamadas = ajeno, fallo, 0

    def generar(self, **kwargs):
        self.llamadas += 1
        if self.fallo:
            raise RuntimeError("Fallo de transporte controlado")
        m = json.loads(kwargs["mensaje"])
        return Rutas.model_validate(
            {
                "filas": [
                    {
                        "fila_id": "f1",
                        "documentos_ids": ["inexistente" if self.ajeno else m["catalogo"][0]["id"]],
                        "conceptos": ["elasticity stress strain"],
                        "limite": "No acredita la carga real del modelo escolar.",
                    }
                ]
            }
        )


def test_enrutamiento_recupera_pasajes_y_reanuda_sin_modelo(entorno, tmp_path):
    c, filas = entorno
    p = Proveedor()
    r = preparar_contexto(c, filas, p, tmp_path)
    assert len(r["fuentes_por_fila"]["f1"]) == 2 and not r["pendientes"]
    assert preparar_contexto(c, filas, p, tmp_path) == r and p.llamadas == 1
    assert "no aprueba un guion" in r["limite"]


def test_documento_inventado_permanece_rechazado(entorno, tmp_path):
    c, filas = entorno
    r = preparar_contexto(c, filas, Proveedor(ajeno=True), tmp_path)
    assert not r["fuentes_por_fila"] and "f1" in r["pendientes"]


def test_fallo_de_transporte_no_se_convierte_en_reintentos(entorno, tmp_path):
    c, filas = entorno
    p = Proveedor(fallo=True)
    r = preparar_contexto(c, filas, p, tmp_path)
    assert r["errores"] == ["RuntimeError"] and "f1" in r["pendientes"]
    assert preparar_contexto(c, filas, p, tmp_path) == r and p.llamadas == 1


@pytest.mark.parametrize("archivo", ["solicitud.json", "respuesta.json"])
def test_no_se_reanuda_si_el_expediente_documental_cambio(entorno, tmp_path, archivo):
    c, filas = entorno
    p = Proveedor()
    preparar_contexto(c, filas, p, tmp_path)
    f = tmp_path / archivo
    f.write_bytes(f.read_bytes() + b"alterado")
    with pytest.raises(ValueError, match="cambió"):
        preparar_contexto(c, filas, p, tmp_path)
    assert p.llamadas == 1


def test_catalogo_grande_con_indice_real_conserva_consulta_especifica():
    catalogo, docs = {}, []
    for n in range(600):
        id_ = f"e{n}"
        texto = "mangrove salinity" if n == 599 else "matter energy motion"
        catalogo[f"d{n}"] = {
            "titulo": texto + " Contexto documental explicativo." * 12,
            "libro": "referencia",
            "evidencias": [SimpleNamespace(id=id_)],
        }
        docs.append(Documento(id=id_, texto=texto, fuente={"documento": id_}, version="v1"))
    corpus = SimpleNamespace(indice=IndiceLexico(docs))
    filas = [{"consulta_recuperacion": "matter energy", "consultas_enrutamiento": ["mangrove salinity"]}]
    reducido = catalogo_relevante(corpus, catalogo, filas)
    assert len(serializar(reducido)) <= 145000
    assert "d599" in {d["id"] for d in reducido}
    assert len(reducido) < len(catalogo)
