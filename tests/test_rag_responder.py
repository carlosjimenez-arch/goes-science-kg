from types import SimpleNamespace

import pytest

anthropic = pytest.importorskip("anthropic")

from goes_science_kg import rag  # noqa: E402


class _Cliente:
    def __init__(self, respuesta):
        self.llamadas = []
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._create))
        self._respuesta = respuesta

    def _create(self, **kw):
        self.llamadas.append(kw)
        return self._respuesta


def _ctx():
    return rag.Contexto(consulta="¿Qué es la fotosíntesis?", grado=6, asignatura=None)


def test_responder_arma_la_llamada_y_devuelve_texto(monkeypatch):
    resp = SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(type="text", text="Respuesta [CON:x]")])
    cliente = _Cliente(resp)
    monkeypatch.setattr(anthropic, "Anthropic", lambda: cliente)
    assert rag.responder(_ctx()) == "Respuesta [CON:x]"
    kw = cliente.llamadas[0]
    assert kw["model"] == "claude-opus-5-5"
    assert kw["fallbacks"] == "default" and "server-side-fallback-2026-07-01" in kw["betas"]
    assert kw["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert "Pregunta: ¿Qué es la fotosíntesis?" in kw["messages"][0]["content"]


def test_responder_maneja_rechazo(monkeypatch):
    cliente = _Cliente(SimpleNamespace(stop_reason="refusal", content=[]))
    monkeypatch.setattr(anthropic, "Anthropic", lambda: cliente)
    assert "rechazada" in rag.responder(_ctx())
