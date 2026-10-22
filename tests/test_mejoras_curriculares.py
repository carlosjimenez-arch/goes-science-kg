"""Test exact closure, row-specific quotations, and durable resumption without real providers."""

import json
from types import SimpleNamespace
from typing import get_args

import pytest

from goes_science_kg.motor.contratos import Evidencia, huella
from goes_science_kg.motor.ejecuciones import ejecutar_durable
from goes_science_kg.motor.fragmentos import Fragmento
from goes_science_kg.motor.mejoras import MotorMejoras
from goes_science_kg.producto.mejoras_contratos import (
    CRITERIOS_MEJORA,
    ROLES_MEJORA,
    BorradorMejora,
    DictamenMejora,
    LecturaMejora,
    MejoraFila,
    PreparacionMejora,
    RondaMejora,
    SolicitudMejora,
)
from goes_science_kg.producto.preparacion_mejoras import internar_textos
from goes_science_kg.producto.validacion_mejoras import evaluar_ronda, resolver_mejora, validar_borrador


@pytest.fixture
def caso():
    fuente = {"documento": "sintetica", "tipo": "documental", "verificacion": "contenido_fuente"}
    local = Evidencia.crear(
        "fila1#CELDA:A1", "Comparar propiedades observables de materiales cotidianos.", fuente, "V4"
    )
    externa = Evidencia.crear(
        "primaria", "Matter exists as different kinds of materials with observable properties.", fuente, "referencia"
    )
    evidencias = (local, externa)
    fragmentos = tuple(Fragmento(id=f"F:{i}", evidencia_id=e.id, literal=e.texto) for i, e in enumerate(evidencias))
    datos = dict(
        solicitud=SolicitudMejora(grado=3, asignatura_malla="Ciencias", unidad="Materia"),
        huella_curriculo="c" * 64,
        huella_catalogo="d" * 64,
        filas_originales=({"id": "fila1", "procedimental": local.texto},),
        clasificaciones_originales={
            "fila1": {"fila_id": "fila1", "estado": "declarado_malla", "disciplinas": ["quimica"]}
        },
        alertas={},
        evidencias=evidencias,
        fragmentos=fragmentos,
        grupos={"fila_00": (local.id,), "referencia": (externa.id,)},
        contexto_aula={"recursos_hipoteticos": ["papel", "lapiz"]},
        limites=("Caso sintético de prueba, no evidencia de eficacia",),
    )
    p = PreparacionMejora(id="a" * 64, **datos)
    p = p.model_copy(update={"id": huella(p.model_dump(mode="json", exclude={"id"}))})
    fila = MejoraFila(
        fila_id="fila1",
        accion="mantener_objetivo",
        disciplinas_propuestas=("quimica",),
        objetivo_propuesto=local.texto,
        indicador_observable="Clasifica dos materiales por sus propiedades observables.",
        producto_evaluable="Tabla de dos materiales y sus propiedades.",
        criterio_evaluacion="Registra dos propiedades observables sin confundirlas con usos.",
        orientacion_didactica="Contrastar dos descripciones en papel y justificar la clasificación.",
        recursos_condicionales=(),
        seguridad="Trabajar con representaciones sin manipular sustancias.",
        andamiaje="Ofrecer vocabulario ilustrado y una tabla de ejemplo.",
        contexto_salvador="Ejemplo propuesto con objetos cotidianos del hogar.",
        justificacion="La comparación conserva el objetivo y permite comprobar el criterio.",
        fragmentos_ids=("F:0", "F:1"),
    )
    b = BorradorMejora(
        filas=(fila,),
        enmiendas_aceptadas=(),
        sintesis="Diseño condicional que conserva una fila original.",
        limites=p.limites,
    )
    modelos = dict.fromkeys(ROLES_MEJORA, "modelo-prueba")
    votos = tuple(
        DictamenMejora(
            rol=rol,
            modelo=modelos[rol],
            huella_preparacion=p.id,
            huella_borrador=huella(b),
            lectura=LecturaMejora(
                criterios=dict.fromkeys(CRITERIOS_MEJORA[rol], "si"),
                fragmentos_ids=("F:0", "F:1"),
                hallazgos=(),
                limites=p.limites,
            ),
        )
        for rol in ROLES_MEJORA
    )
    return p, b, modelos, RondaMejora(borrador=b, errores_estructura=(), dictamenes=votos)


def test_cierre_positivo_solo_con_cuatro_roles_y_salida_exacta(caso):
    p, b, modelos, ronda = caso
    assert validar_borrador(b, p) == ()
    r = resolver_mejora(p, (ronda,), ejecucion_id="compartida", modelos=modelos)
    assert r.estado == "respaldado_automaticamente" and r.propuesta == b
    assert r.rondas == (ronda,) and r.preparacion_id == p.id


@pytest.mark.parametrize("rol", ROLES_MEJORA)
@pytest.mark.parametrize("valor,estado", [("no", "no_respaldado"), ("insuficiente", "abstencion")])
def test_ninguna_mayoria_compensa_un_veto(caso, rol, valor, estado):
    p, _, modelos, ronda = caso
    votos = []
    for d in ronda.dictamenes:
        if d.rol == rol:
            lectura = d.lectura.model_copy(update={"criterios": dict.fromkeys(CRITERIOS_MEJORA[rol], valor)})
            d = d.model_copy(update={"lectura": lectura})
        votos.append(d)
    alterada = ronda.model_copy(update={"dictamenes": tuple(votos)})
    assert evaluar_ronda(alterada, p, modelos)[0] == estado
    assert resolver_mejora(p, (alterada,), ejecucion_id="x", modelos=modelos).propuesta is None


@pytest.mark.parametrize("campo", ["huella_preparacion", "huella_borrador", "modelo"])
def test_voto_de_otro_contexto_o_borrador_es_rechazado(caso, campo):
    p, _, modelos, ronda = caso
    votos = list(ronda.dictamenes)
    votos[0] = votos[0].model_copy(update={campo: "ajeno"})
    with pytest.raises(ValueError, match="otro modelo"):
        evaluar_ronda(ronda.model_copy(update={"dictamenes": tuple(votos)}), p, modelos)


@pytest.mark.parametrize(
    "alteracion", ["omision", "duplicacion", "otra_fila", "otra_disciplina", "cita_inventada", "cambio_oculto"]
)
def test_preservacion_de_alcance_y_citas(caso, alteracion):
    p, b, _, _ = caso
    f = b.filas[0]
    cambios = {
        "otra_fila": {"fila_id": "ajena"},
        "otra_disciplina": {"disciplinas_propuestas": ("fisica",)},
        "cita_inventada": {"fragmentos_ids": ("F:0", "F:no-existe")},
        "cambio_oculto": {"objetivo_propuesto": "Enseñar otro tema que no pertenece al original."},
    }
    filas = (
        ()
        if alteracion == "omision"
        else (f, f)
        if alteracion == "duplicacion"
        else (f.model_copy(update=cambios[alteracion]),)
    )
    assert validar_borrador(b.model_copy(update={"filas": filas}), p)


def test_lectura_debe_cubrir_cada_grupo_y_criterio(caso):
    p, _, modelos, ronda = caso
    for cambios in ({"fragmentos_ids": ("F:0",)}, {"criterios": {"inventado": "si"}}):
        d = ronda.dictamenes[0]
        votos = (d.model_copy(update={"lectura": d.lectura.model_copy(update=cambios)}), *ronda.dictamenes[1:])
        with pytest.raises(ValueError):
            evaluar_ronda(ronda.model_copy(update={"dictamenes": votos}), p, modelos)


def test_no_repetir_votos_positivos_ni_borradores_identicos(caso):
    p, _, modelos, ronda = caso
    with pytest.raises(ValueError, match="vuelve a votar"):
        resolver_mejora(p, (ronda, ronda), ejecucion_id="x", modelos=modelos)


def test_internacion_es_reversible_caracter_por_caracter():
    texto = "Átomos y moléculas con unidades, símbolos y condiciones. " * 8
    original = [{"a": texto, "b": [texto, "corto"]}, {"c": texto}]
    compactas, registro = internar_textos(original)

    def restaurar(x):
        if isinstance(x, dict):
            if set(x) == {"texto_registrado"}:
                return registro[x["texto_registrado"]]
            return {k: restaurar(v) for k, v in x.items()}
        return [restaurar(v) for v in x] if isinstance(x, list) else x

    assert restaurar(compactas) == original and len(registro) == 1


class ModeloPrueba:
    def __init__(self, borrador, *, fallo=False, veto=False):
        self.borrador, self.llamadas, self.fallo, self.veto = borrador, [], fallo, veto

    def nombre_modelo(self, rol):
        return "modelo-prueba"

    def generar(self, *, rol, sistema, mensaje, esquema):
        self.llamadas.append(rol)
        assert "otros votos" not in json.loads(mensaje)
        if self.fallo:
            raise TimeoutError("proveedor simulado")
        if rol == "redactor_curricular":
            return self.borrador
        seleccion = esquema.model_fields["fragmentos_por_grupo"].annotation
        return esquema.model_validate(
            {
                "criterios": dict.fromkeys(CRITERIOS_MEJORA[rol], "no" if self.veto else "si"),
                "fragmentos_por_grupo": {k: get_args(c.annotation)[0] for k, c in seleccion.model_fields.items()},
                "hallazgos": [],
                "limites": ["Simulación sin proveedor real"],
            }
        )


def motor_prueba(caso, **kwargs):
    p, b, _, _ = caso

    def validar(actual):
        if actual != p:
            raise ValueError("Cambió la fuente original")

    preparador = SimpleNamespace(preparar=lambda s: p, validar=validar)
    return MotorMejoras(preparador, ModeloPrueba(b, **kwargs))


def test_workflow_y_checkpoint_terminado_se_reutilizan_sin_llamadas(caso, tmp_path):
    p = caso[0]
    motor = motor_prueba(caso)
    args = dict(
        archivo=tmp_path / "check.sqlite",
        solicitud=p.solicitud.model_dump(),
        thread_id="unidad",
        ejecucion_id="unico",
        huella_entorno=motor.entorno(p),
        max_concurrencia=4,
    )
    primero = ejecutar_durable(motor, **args)
    assert primero["resultado"]["estado"] == "respaldado_automaticamente"
    assert len(motor.modelo.llamadas) == 5
    assert ejecutar_durable(motor, **args) == primero
    assert len(motor.modelo.llamadas) == 5


def test_fallo_no_dispara_reintentos_ocultos(caso):
    p = caso[0]
    motor = motor_prueba(caso, fallo=True)
    r = motor.compilar().invoke({"solicitud": p.solicitud.model_dump(), "ejecucion_id": "x"})
    assert r["resultado"]["estado"] == "abstencion" and len(motor.modelo.llamadas) == 1


def test_reparacion_identica_no_repite_cuatro_votos(caso):
    p = caso[0]
    motor = motor_prueba(caso, veto=True)
    r = motor.compilar().invoke({"solicitud": p.solicitud.model_dump(), "ejecucion_id": "x"})
    assert r["resultado"]["estado"] == "abstencion" and len(motor.modelo.llamadas) == 6
    assert len(r["resultado"]["rondas"]) == 2


def test_esquema_contextual_impide_citas_que_no_existen(caso):
    from goes_science_kg.motor.esquemas import contrato_transporte
    from goes_science_kg.motor.esquemas_mejoras import esquema_redaccion

    p, b, _, _ = caso
    esquema = contrato_transporte(esquema_redaccion(p))
    assert esquema.model_validate(b.model_dump()).filas[0].fragmentos_ids == ("F:0", "F:1")
    datos = b.model_dump(mode="json")
    datos["filas"][0]["fragmentos_ids"][1] = "F:inventado"
    with pytest.raises(ValueError):
        esquema.model_validate(datos)
