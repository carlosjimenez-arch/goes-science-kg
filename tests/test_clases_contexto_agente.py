"""El selector debe aportar fuentes de la fila y detenerse sin evidencia nueva."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from goes_science_kg.clases.contexto_agente import DecisionFuentes, candidatos, evaluar_respuesta, seleccionar
from goes_science_kg.motor.contratos import Evidencia
from goes_science_kg.recuperacion.lexico import IndiceLexico
from goes_science_kg.recuperacion.modelos import Documento


@pytest.fixture
def entorno():
    es = {
        id_: Evidencia.crear(
            id_,
            "Living organisms interact with nonliving environmental factors in a functioning ecosystem. " + id_,
            {"documento": id_, "titulo": "Ecosystems", "libro": "biology-2e", "tipo": "documental"},
            "referencia",
        )
        for id_ in ("e1", "e2", "e3", "e4")
    }

    def buscar(q, **_):
        return [(i, 1.0) for i in (("e3", "e4") if "new evidence" in q else ("e1", "e2"))]

    def verificar(e):
        assert es[e.id].model_dump() == e.model_dump()

    corpus = SimpleNamespace(huella="a" * 64, evidencias=es, indice=SimpleNamespace(buscar=buscar), verificar=verificar)
    filas = [
        {
            "fila_id": "f1",
            "consulta_recuperacion": "ecosystem components",
            "propuesta": {
                "disciplinas_propuestas": ["biologia"],
                "objetivo_propuesto": "Compare ecosystem components.",
            },
        }
    ]
    return corpus, filas


class Selector:
    def __init__(self, *, laguna=False, nueva_evidencia=False, ajena=False):
        self.llamadas = 0
        self.laguna, self.nueva_evidencia, self.ajena = laguna, nueva_evidencia, ajena

    def generar(self, **kwargs):
        self.llamadas += 1
        m = json.loads(kwargs["mensaje"])
        insuficiente = self.laguna and self.llamadas == 1
        ids = [e["id"] for e in m["filas"][0]["candidatos"]][:2]
        if self.ajena:
            ids[-1] = "fuente-inventada"
        return DecisionFuentes.model_validate(
            {
                "filas": [
                    {
                        "fila_id": "f1",
                        "cobertura": "insuficiente" if insuficiente else "suficiente",
                        "fuentes_ids": ids,
                        "lagunas": ["Falta una relación científica específica."] if insuficiente else [],
                        "consultas": ["new evidence"] if insuficiente and self.nueva_evidencia else [],
                    }
                ]
            }
        )


def test_seleccion_terminal_se_reanuda_sin_llamadas(entorno, tmp_path):
    c, filas = entorno
    p = Selector()
    r = seleccionar(c, filas, p, tmp_path)
    assert r["fuentes_por_fila"]["f1"] and not r["pendientes"] and p.llamadas == 1
    assert seleccionar(c, filas, p, tmp_path) == r and p.llamadas == 1


def test_insuficiencia_sin_fuentes_nuevas_no_recibe_otro_voto(entorno, tmp_path):
    c, filas = entorno
    p = Selector(laguna=True)
    r = seleccionar(c, filas, p, tmp_path)
    assert "f1" in r["pendientes"] and not r["fuentes_por_fila"] and p.llamadas == 1


def test_nueva_busqueda_permite_una_segunda_decision_acotada(entorno, tmp_path):
    c, filas = entorno
    p = Selector(laguna=True, nueva_evidencia=True)
    r = seleccionar(c, filas, p, tmp_path)
    assert not r["pendientes"] and p.llamadas == 2


def test_fuente_ajena_no_se_convierte_en_evidencia(entorno, tmp_path):
    c, filas = entorno
    proveedor = Selector(ajena=True)
    r = seleccionar(c, filas, proveedor, tmp_path)
    assert not r["fuentes_por_fila"] and "f1" in r["pendientes"] and proveedor.llamadas == 1
    assert (tmp_path / "ronda_1_respuesta.json").is_file()


def test_fuente_invalida_no_descarta_la_otra_fila_correcta():
    solicitudes = [{"fila_id": f, "candidatos": [{"id": "e1"}, {"id": "e2"}]} for f in ("f1", "f2")]
    respuesta = {
        "filas": [
            {"fila_id": f, "cobertura": "suficiente", "fuentes_ids": ids, "lagunas": [], "consultas": []}
            for f, ids in (("f1", ["e1", "inventada"]), ("f2", ["e1", "e2"]))
        ]
    }
    elegidas, pendientes = evaluar_respuesta(solicitudes, respuesta)
    assert set(elegidas) == {"f2"} and set(pendientes) == {"f1"}


def test_una_decision_no_habilita_segunda_llamada_aunque_existan_consultas_nuevas(entorno, tmp_path):
    c, filas = entorno
    proveedor = Selector(laguna=True, nueva_evidencia=True)
    assert seleccionar(c, filas, proveedor, tmp_path, max_decisiones=1)["pendientes"]
    assert proveedor.llamadas == 1


def test_dos_fallos_tecnicos_no_habilitan_reintentos_ilimitados(entorno, tmp_path):
    c, filas = entorno

    class Fallo:
        llamadas = 0

        def generar(self, **_):
            self.llamadas += 1
            raise RuntimeError("Fallo de transporte controlado")

    p = Fallo()
    r = seleccionar(c, filas, p, tmp_path)
    assert "f1" in r["pendientes"] and p.llamadas == 2
    assert seleccionar(c, filas, p, tmp_path) == r and p.llamadas == 2


def test_una_laguna_especifica_recupera_fisica_para_un_objetivo_biologico():
    evidencias = {}
    for n in range(20):
        id_ = f"bio{n}"
        evidencias[id_] = Evidencia.crear(
            id_,
            "The reproductive system contains organs and tissues whose cells participate in reproduction. " * 2,
            {"documento": id_, "titulo": "Reproductive system", "libro": "biology-2e"},
            "referencia",
        )
    evidencias["ultrasonido"] = Evidencia.crear(
        "ultrasonido",
        "Ultrasound imaging uses reflected sound waves to produce noninvasive images of internal tissues and organs.",
        {"documento": "fisica", "titulo": "Ultrasound imaging", "libro": "college-physics-2e"},
        "referencia",
    )
    indice = IndiceLexico(
        Documento(id=e.id, texto=e.texto, fuente=e.fuente, version=e.version) for e in evidencias.values()
    )
    corpus = SimpleNamespace(
        evidencias=evidencias,
        indice=indice,
        verificar=lambda e: None,
    )
    fila = {
        "consulta_recuperacion": "reproductive system organs tissues cells reproduction",
        "consultas_documentales_adicionales": ["ultrasound imaging noninvasive"],
        "propuesta": {"disciplinas_propuestas": ["biologia"]},
    }
    ids = {e["id"] for e in candidatos(corpus, fila)}
    assert "ultrasonido" in ids and len(ids - {"ultrasonido"}) >= 2
