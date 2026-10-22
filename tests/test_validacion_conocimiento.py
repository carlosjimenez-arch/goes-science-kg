"""Test pure reusable knowledge closure without providers, network, or original-source files."""

from __future__ import annotations

import copy

import pytest

from goes_science_kg.motor.contratos import Cita, Evidencia, huella
from goes_science_kg.motor.fragmentos import Fragmento
from goes_science_kg.motor.validacion_conocimiento import resolver_resultado, validar_dictamen
from goes_science_kg.producto._juicios_contratos import (
    ESQUEMAS_CONOCIMIENTO,
    ROLES_CONOCIMIENTO,
    DictamenConocimiento,
    ExpedienteConocimiento,
    SolicitudConocimiento,
)


@pytest.fixture
def argumentos():
    evidencias = tuple(
        Evidencia.crear(
            f"evidencia-{grupo}",
            f"Texto primario sintético del grupo {grupo} para probar citas exactas.",
            {"documento": f"documento-{grupo}", "verificacion": "contenido_fuente"},
            "V4" if grupo == "local" else "referencia",
        )
        for grupo in ("local", "origen", "destino", "dependencia")
    )
    fragmentos = tuple(Fragmento(id=f"F:{e.id}", evidencia_id=e.id, literal=e.texto) for e in evidencias)
    expediente = ExpedienteConocimiento(
        estado="preparado",
        candidato_id="CANDIDATO_V4:" + "a" * 64,
        huella_curriculo="b" * 64,
        huella_referencia="c" * 64,
        huella_candidato="d" * 64,
        fila_id="fila-2",
        grado=7,
        asignatura_malla="Ciencias",
        tipo_relacion="prerrequisito_necesario",
        origen="concepto-origen",
        destino="concepto-destino",
        descriptores={},
        grupos={grupo: (f"evidencia-{grupo}",) for grupo in ("local", "origen", "destino", "dependencia")},
        evidencias=evidencias,
        fragmentos=fragmentos,
    )
    modelos = {rol: "modelo-verificable-" + rol for rol in ROLES_CONOCIMIENTO}
    salidas = {
        rol: {
            "dictamen": DictamenConocimiento(
                rol=rol,
                modelo=modelos[rol],
                huella_tarea=huella(expediente),
                criterios=dict.fromkeys(
                    ESQUEMAS_CONOCIMIENTO[rol].model_fields["criterios"].annotation.model_fields, "si"
                ),
                citas=tuple(Cita(evidencia_id=f.evidencia_id, literal=f.literal) for f in fragmentos),
                explicacion="Validación sintética de un contrato, sin acreditar corrección semántica real.",
                limites=("El llamador verifica el expediente antes de reconstruir el cierre",),
            ).model_dump(mode="json"),
            "error": None,
        }
        for rol in ROLES_CONOCIMIENTO
    }
    return dict(
        expediente=expediente,
        solicitud=SolicitudConocimiento(candidato_id=expediente.candidato_id),
        ejecucion_id="ledger-unico",
        huella_motor="e" * 64,
        modelos=modelos,
        salidas=salidas,
    )


def test_reconstruccion_pura_conserva_identidades_orden_rubricas_y_grupos(argumentos):
    antes = copy.deepcopy(argumentos)
    resultado = resolver_resultado(**argumentos)
    assert resultado.estado == "respaldado"
    assert resultado.ejecucion_id == "ledger-unico" and resultado.huella_motor == "e" * 64
    assert resultado.solicitud == argumentos["solicitud"]
    assert resultado.huella_tarea == huella(argumentos["expediente"])
    assert tuple(d.rol for d in resultado.dictamenes) == ROLES_CONOCIMIENTO
    assert resultado.relacion.fila_id == "fila-2" and resultado.relacion.grado_sv == 7
    datos_relacion = resultado.relacion.model_dump(mode="json", exclude={"id", "ambito"})
    assert resultado.relacion.id == "RELACION_V4:" + huella(datos_relacion)
    assert argumentos == antes
    invertidas = dict(reversed(list(argumentos["salidas"].items())))
    assert resolver_resultado(**(argumentos | {"salidas": invertidas})) == resultado


@pytest.mark.parametrize("rol", ROLES_CONOCIMIENTO)
@pytest.mark.parametrize("valor,decision", [("no", "no_respaldado"), ("insuficiente", "abstencion")])
def test_cada_rubrica_conserva_veto_e_insuficiencia_sin_mayoria(argumentos, rol, valor, decision):
    argumentos["salidas"][rol]["dictamen"]["criterios"]["fuentes_implican_relacion"] = valor
    resultado = resolver_resultado(**argumentos)
    assert resultado.estado == decision and resultado.relacion is None
    assert len(resultado.dictamenes) == 4
    assert len(resultado.motivos) == 1
    assert ("veto explícito" if valor == "no" else "resolver todos") in resultado.motivos[0]


@pytest.mark.parametrize("alteracion", ["rol", "modelo", "huella", "criterios", "cita_ajena", "duplicada", "grupo"])
def test_validador_independiente_rechaza_dictamen_incompatible(argumentos, alteracion):
    rol = ROLES_CONOCIMIENTO[0]
    datos = argumentos["salidas"][rol]["dictamen"]
    if alteracion == "rol":
        datos["rol"] = ROLES_CONOCIMIENTO[1]
    elif alteracion == "modelo":
        datos["modelo"] = "otro-modelo"
    elif alteracion == "huella":
        datos["huella_tarea"] = "f" * 64
    elif alteracion == "criterios":
        datos["criterios"]["criterio_ajeno"] = "si"
    elif alteracion == "cita_ajena":
        datos["citas"][0]["literal"] = "Una cita que no pertenece a los fragmentos primarios registrados."
    elif alteracion == "duplicada":
        datos["citas"][1] = copy.deepcopy(datos["citas"][0])
    else:
        datos["citas"].pop()
    with pytest.raises(ValueError):
        validar_dictamen(datos, rol, argumentos["expediente"], argumentos["modelos"])
    resultado = resolver_resultado(**argumentos)
    assert resultado.estado == "abstencion" and resultado.relacion is None
    assert len(resultado.dictamenes) == 3
    assert resultado.motivos == (f"{rol}: dictamen no verificable (ValueError)",)


def test_expediente_sin_preparacion_conserva_motivos_sin_admitir_lecturas(argumentos):
    argumentos["expediente"] = argumentos["expediente"].model_copy(
        update={
            "estado": "abstencion",
            "motivos": ("Falta una fuente primaria del grupo dependencia",),
        }
    )
    resultado = resolver_resultado(**argumentos)
    assert resultado.estado == "abstencion" and resultado.relacion is None and resultado.dictamenes == ()
    assert resultado.motivos == argumentos["expediente"].motivos


def test_roles_ausentes_y_proveedor_ausente_no_fabrican_respaldo(argumentos):
    argumentos["salidas"].pop(ROLES_CONOCIMIENTO[0])
    assert resolver_resultado(**argumentos).estado == "abstencion"
    argumentos["modelos"] = None
    resultado = resolver_resultado(**argumentos)
    assert resultado.estado == "abstencion" and resultado.dictamenes == () and len(resultado.motivos) == 4
