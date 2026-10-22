"""Dos lecturas distintas, alcance explícito y fallos que no se vuelven consenso."""

import json

import pytest
from pydantic import ValidationError

from goes_science_kg.curriculo.catalogacion import DecisionDisciplina, clasificar_disciplinas, plan_catalogacion
from goes_science_kg.curriculo.contratos import FASES, Curriculo, FaseCurricular, FilaCurricular


def curriculo_de_prueba():
    filas = tuple(
        FilaCurricular(
            id=f"FILA:{i}",
            fuente_id="fuente_prueba",
            version="V4",
            hoja="Unidad de prueba",
            fila=i,
            grado=10 if asignatura == "Biología" else 6,
            asignatura_malla=asignatura,
            unidad="U1",
            procedimental="Investigar los procesos celulares con modelos sencillos",
            fases={f: FaseCurricular(presente_en_hoja=False) for f in FASES},
            celdas=(),
        )
        for i, asignatura in enumerate(("Ciencias", "Ciencias", "Biología"), 1)
    )
    return Curriculo(version="V4", huella="a" * 64, fuentes=(), filas=filas, hojas=(), agrupaciones=())


class ClasificadorSimulado:
    def __init__(self, *, discrepancia=False, faltan=False, falla=False):
        self.discrepancia = discrepancia
        self.faltan = faltan
        self.falla = falla
        self.llamadas = []

    def nombre_modelo(self, rol):
        return f"simulado-{rol}"

    def generar(self, *, rol, sistema, mensaje, esquema):
        self.llamadas.append((rol, sistema, mensaje))
        if self.falla and rol == "catalogador_b":
            raise TimeoutError()
        filas = json.loads(mensaje)["datos_no_confiables"]
        decisiones = [
            {
                "fila_id": fila["id"],
                "estado": "en_alcance",
                "disciplinas": ["quimica" if self.discrepancia and rol == "catalogador_b" else "biologia"],
                "justificacion": "El objetivo describe procesos celulares investigados con modelos",
            }
            for fila in filas
        ]
        return esquema.model_validate({"decisiones": decisiones[:-1] if self.faltan else decisiones})


def test_plan_no_envia_fases_digital_ni_datos_ajenos():
    plan = plan_catalogacion(curriculo_de_prueba())
    assert plan["declaradas_en_malla"] == 1
    assert plan["filas_a_clasificar"] == 2
    assert plan["llamadas_previstas"] == 2
    assert plan["llamadas_ejecutadas"] == 0


def test_asignatura_literal_del_libro_se_preserva_y_lecturas_estan_separadas():
    modelo = ClasificadorSimulado()
    resultado = clasificar_disciplinas(curriculo_de_prueba(), modelo)
    assert len(modelo.llamadas) == 2
    assert modelo.llamadas[0][1] != modelo.llamadas[1][1]
    assert all("lecturas" not in json.loads(llamada[2]) for llamada in modelo.llamadas)
    por_id = {f.fila_id: f for f in resultado.filas}
    assert por_id["FILA:3"].estado == "declarado_malla"
    assert por_id["FILA:3"].disciplinas == ("biologia",)
    assert por_id["FILA:1"].estado == "coincidencia_automatica"
    assert resultado.modelos["catalogador_a"] != resultado.modelos["catalogador_b"]
    assert {f["id"] for f in json.loads(modelo.llamadas[0][2])["datos_no_confiables"]} == {"1", "2"}
    assert {d.fila_id for d in por_id["FILA:1"].lecturas.values()} == {"FILA:1"}


@pytest.mark.parametrize("fallo", ["discrepancia", "faltan", "falla"])
def test_discrepancia_ids_omitidos_y_fallo_de_proveedor_no_aprueban(fallo):
    resultado = clasificar_disciplinas(curriculo_de_prueba(), ClasificadorSimulado(**{fallo: True}))
    assert all(f.estado == "abstencion" for f in resultado.filas if f.fila_id != "FILA:3")
    assert next(f for f in resultado.filas if f.fila_id == "FILA:3").estado == "declarado_malla"


def test_no_mezclar_fuera_de_alcance_con_disciplinas():
    with pytest.raises(ValidationError):
        DecisionDisciplina(
            fila_id="fila",
            estado="fuera_alcance",
            disciplinas=("fisica",),
            justificacion="Una decisión fuera de alcance no acredita una disciplina",
        )


def test_piloto_fallido_no_despacha_los_lotes_restantes():
    base = curriculo_de_prueba()
    fila = base.filas[0]
    curriculo = base.model_copy(
        update={"filas": tuple(fila.model_copy(update={"id": f"FILA:{i:03}", "fila": i}) for i in range(1, 50))}
    )
    modelo = ClasificadorSimulado(falla=True)
    resultado = clasificar_disciplinas(curriculo, modelo)
    assert len(modelo.llamadas) == 2
    assert not resultado.piloto_superado
    assert len(resultado.filas) == 49 and all(f.estado == "abstencion" for f in resultado.filas)


def test_un_catalogo_no_puede_omitir_estado_del_piloto_o_alcance():
    resultado = clasificar_disciplinas(curriculo_de_prueba(), ClasificadorSimulado()).model_dump()
    for campo in ("modo", "piloto_superado"):
        incompleto = {k: v for k, v in resultado.items() if k != campo}
        with pytest.raises(ValidationError):
            type(clasificar_disciplinas(curriculo_de_prueba(), ClasificadorSimulado())).model_validate(incompleto)
