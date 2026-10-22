"""Recuperar una revisión ausente no cambia votos; un veto exige otro borrador."""

from types import SimpleNamespace

from test_mejoras_curriculares import ModeloPrueba
from test_mejoras_curriculares import caso as caso

from goes_science_kg.producto.mejoras_contratos import ROLES_MEJORA
from goes_science_kg.producto.mejoras_publicadas import CasoMejora
from goes_science_kg.producto.seguimiento_mejoras import MotorSeguimiento, solo_revision_fallida
from goes_science_kg.producto.validacion_mejoras import resolver_mejora


def antecedente(caso, *, veto=False):
    p, b, modelos, ronda = caso
    d = ronda.dictamenes[0].model_copy(update={"lectura": None, "error": "ClientError"})
    votos = (d, *ronda.dictamenes[1:])
    if veto:
        d2 = votos[1]
        criterios = d2.lectura.criterios | {next(iter(d2.lectura.criterios)): "no"}
        votos = (
            d,
            d2.model_copy(update={"lectura": d2.lectura.model_copy(update={"criterios": criterios})}),
            *votos[2:],
        )
    r = resolver_mejora(p, (ronda.model_copy(update={"dictamenes": votos}),), ejecucion_id="x", modelos=modelos)
    return CasoMejora(preparacion=p, resultado=r, entorno="a" * 64, plan_id="b" * 64)


def test_recupera_solo_la_revision_ausente_sin_nuevo_redactor(caso):
    p, b, _, _ = caso
    anterior = antecedente(caso)
    assert solo_revision_fallida(anterior)
    modelo = ModeloPrueba(b)
    motor = MotorSeguimiento(SimpleNamespace(preparar=lambda s: p, validar=lambda p: None), modelo, anterior)
    estado = motor.compilar().invoke({"solicitud": p.solicitud.model_dump(), "ejecucion_id": "x"})
    assert estado["resultado"]["estado"] == "respaldado_automaticamente"
    assert modelo.llamadas == [ROLES_MEJORA[0]]
    assert estado["resultado"]["rondas"][0]["dictamenes"][1:] == [
        d.model_dump(mode="json") for d in anterior.resultado.rondas[-1].dictamenes[1:]
    ]


def test_fallo_y_veto_no_se_convierten_en_reintento_del_mismo_texto(caso):
    p, b, _, _ = caso
    anterior = antecedente(caso, veto=True)
    assert not solo_revision_fallida(anterior)
    modelo = ModeloPrueba(b)
    motor = MotorSeguimiento(SimpleNamespace(preparar=lambda s: p, validar=lambda p: None), modelo, anterior)
    estado = motor.compilar().invoke({"solicitud": p.solicitud.model_dump(), "ejecucion_id": "x"})
    assert estado["resultado"]["estado"] == "abstencion"
    assert modelo.llamadas == ["redactor_curricular"]
    assert estado["resultado"]["propuesta"] is None
