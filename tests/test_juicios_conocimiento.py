"""Integración de fuentes nativas, juicios simulados y reanudación; nunca consume modelos reales."""

from __future__ import annotations

import copy
import json
from types import SimpleNamespace

import pytest
from test_conocimiento_v4 import _concepto, _curriculo, _pais, _referencia

from goes_science_kg.curriculo.contexto_fuentes import fuentes_del_curriculo
from goes_science_kg.modelos import Arista, TipoArista, TipoNodo
from goes_science_kg.motor.conocimiento import MotorConocimiento
from goes_science_kg.motor.contratos import huella
from goes_science_kg.motor.ejecuciones import ejecutar_durable
from goes_science_kg.producto._juicios_contratos import (
    ESQUEMAS_CONOCIMIENTO,
    ROLES_CONOCIMIENTO,
    SolicitudConocimiento,
    SoporteSemantico,
)
from goes_science_kg.producto.conocimiento import EdicionEsperada, PoliticaConocimiento, generar_candidatos_conocimiento
from goes_science_kg.producto.juicios import PreparadorConocimiento, datos_juicio


class LectoresSimulados:
    def __init__(self, cambios=None, fragmentos_invalidos=False):
        self.llamadas = []
        self.cambios = cambios or {}
        self.fragmentos_invalidos = fragmentos_invalidos

    def nombre_modelo(self, rol):
        return "simulado-" + rol

    def generar(self, *, rol, sistema, mensaje, esquema):
        self.llamadas.append(rol)
        assert "No ves otros lectores" in sistema
        datos = json.loads(mensaje)["datos_no_confiables"]
        assert "dictamenes" not in datos and "confianza" not in datos
        fragmentos = datos["fragmentos"]
        por_grupo = {
            nombre: next(f["id"] for f in fragmentos if f["evidencia_id"] in grupo)
            for nombre, grupo in datos["evidencia_por_grupo"].items()
        }
        if self.fragmentos_invalidos:
            por_grupo = {g: "F:inventado" for g in por_grupo}
        criterios = {k: "si" for k in esquema.model_fields["criterios"].annotation.model_fields}
        criterios.update(self.cambios.get(rol, {}))
        return esquema.model_validate(
            dict(
                criterios=criterios,
                fragmentos_por_grupo=por_grupo,
                explicacion="Dictamen sintético para probar el contrato; no demuestra calidad semántica real.",
                limites=["Fuentes y modelo sintéticos; sin validez educativa"],
            )
        )


def entrada(tmp_path, *, tipo="contraste_pais", soportes=False):
    curriculo = _curriculo(tmp_path)
    documento, objetivo, digest = _pais(tmp_path)
    concepto = _concepto()
    nodos, aristas = [concepto, documento, objetivo], []
    if tipo == "fila_practica":
        concepto = concepto.model_copy(update={"tipo": TipoNodo.PRACTICA})
        nodos[0] = concepto
    if tipo == "prerrequisito":
        origen = _concepto("concepto-temperatura", "Temperatura")
        nodos.append(origen)
        aristas.append(Arista(origen=origen.id, destino=concepto.id, tipo=TipoArista.PRERREQUISITO_DE))
    referencia = _referencia(*nodos, aristas=aristas)
    politica = PoliticaConocimiento(
        ediciones_por_documento={
            "documento-pais": EdicionEsperada(sha256=digest, version_documental="2013"),
        }
    )
    informe = generar_candidatos_conocimiento(
        curriculo,
        referencia,
        raiz_v4=tmp_path / "v4",
        raiz_historica=tmp_path,
        politica=politica,
    )
    candidato = next(c for c in informe.candidatos if c.tipo == tipo)
    fuentes = fuentes_del_curriculo(
        curriculo,
        raiz_v4=tmp_path / "v4",
        raiz_historica=tmp_path,
        catalogo_historico={"documento-pais": documento.props},
    )
    grupos = ("origen", "destino", "dependencia") if tipo == "prerrequisito" else ("destino",)
    complementos = (
        tuple(
            SoporteSemantico(
                candidato_id=candidato.id,
                grupo=g,
                documento="documento-pais",
                pagina=1,
                sha256=digest,
                version_documental="2013",
            )
            for g in grupos
        )
        if soportes
        else ()
    )
    preparador = PreparadorConocimiento(curriculo, informe, referencia, fuentes, soportes=complementos)
    solicitud = SolicitudConocimiento(candidato_id=candidato.id)
    return SimpleNamespace(**locals())


def ejecutar(e, modelo=None):
    modelo = modelo or LectoresSimulados()
    motor = MotorConocimiento(e.preparador, modelo)
    estado = motor.compilar().invoke({"solicitud": e.solicitud.model_dump(mode="json"), "ejecucion_id": "prueba"})
    return motor, modelo, estado


def test_lectura_primaria_conserva_textos_completos_y_citas_breves(tmp_path):
    e = entrada(tmp_path)
    expediente = e.preparador.preparar(e.solicitud)
    datos = datos_juicio(expediente)["datos_no_confiables"]
    obligatorias = {i for g in ("objetivo_local", "evaluacion_local") for i in expediente.grupos.get(g, ())} | {
        prueba.id for prueba in expediente.evidencias if prueba.version == "referencia"
    }
    assert set(datos["lectura_primaria"]) == obligatorias
    originales = {prueba.id: prueba.texto for prueba in expediente.evidencias}
    assert all(texto == originales[id_] for id_, texto in datos["lectura_primaria"].items())
    assert all(len(f.literal.split()) <= 20 for f in expediente.fragmentos)
    assert len(json.dumps(datos_juicio(expediente), ensure_ascii=False)) <= e.preparador.max_caracteres


def test_contexto_no_recorta_fuentes_primarias_para_aparentar_que_caben(tmp_path):
    e = entrada(tmp_path)
    e.preparador.max_caracteres = 2000
    _, modelo, estado = ejecutar(e)
    assert estado["resultado"]["estado"] == "abstencion"
    assert modelo.llamadas == []


@pytest.mark.parametrize("tipo", ["fila_concepto", "fila_practica", "prerrequisito", "contraste_pais"])
def test_fuentes_y_cuatro_lectores_ciegos(tmp_path, tipo):
    e = entrada(tmp_path, tipo=tipo, soportes=True)
    motor, modelo, estado = ejecutar(e)
    assert sorted(modelo.llamadas) == sorted(ROLES_CONOCIMIENTO)
    assert estado["resultado"]["estado"] == "respaldado"
    assert estado["resultado"]["relacion"]["ambito"] == "fila_curricular"
    motor.validar_estado(estado)
    assert len(modelo.llamadas) == 4
    for d in estado["resultado"]["dictamenes"]:
        assert all(len(c["literal"].split()) <= 20 for c in d["citas"])


@pytest.mark.parametrize("tipo", ["fila_concepto", "fila_practica", "prerrequisito"])
def test_definicion_o_dependencia_sin_fuente_abstiene_cero_llamadas(tmp_path, tipo):
    e = entrada(tmp_path, tipo=tipo)
    _, modelo, estado = ejecutar(e)
    assert modelo.llamadas == []
    assert estado["resultado"]["estado"] == "abstencion"
    assert estado["resultado"]["relacion"] is None
    assert "evidencia primaria" in estado["resultado"]["motivos"][0]


@pytest.mark.parametrize("rol", ROLES_CONOCIMIENTO)
@pytest.mark.parametrize("valor,decision", [("no", "no_respaldado"), ("insuficiente", "abstencion")])
def test_un_criterio_impide_relacion_sin_mayoria(tmp_path, rol, valor, decision):
    e = entrada(tmp_path)
    _, modelo, estado = ejecutar(e, LectoresSimulados({rol: {"fuentes_implican_relacion": valor}}))
    assert len(modelo.llamadas) == 4
    assert estado["resultado"]["estado"] == decision
    assert estado["resultado"]["relacion"] is None


def test_citas_inventadas_no_pasan(tmp_path):
    _, _, estado = ejecutar(entrada(tmp_path), LectoresSimulados(fragmentos_invalidos=True))
    assert estado["resultado"]["estado"] == "abstencion"


@pytest.mark.parametrize("campo", ["modelo", "rol", "huella_tarea", "criterios", "citas"])
def test_dictamen_persistido_manipulado_no_pasa(tmp_path, campo):
    motor, _, estado = ejecutar(entrada(tmp_path))
    d = estado[ROLES_CONOCIMIENTO[0]]["dictamen"]
    d[campo] = {"fuentes_implican_relacion": "si"} if campo == "criterios" else ([] if campo == "citas" else "otro")
    with pytest.raises(ValueError, match="terminal"):
        motor.validar_estado(estado)


@pytest.mark.parametrize(
    "campo,valor", [("estado", "no_respaldado"), ("relacion", None), ("ejecucion_id", "otra"), ("huella_motor", "otra")]
)
def test_terminal_se_reconstruye(tmp_path, campo, valor):
    motor, _, estado = ejecutar(entrada(tmp_path))
    estado["resultado"][campo] = valor
    with pytest.raises(ValueError, match="terminal"):
        motor.validar_estado(estado)


def test_terminal_sin_preparacion_no_se_reutiliza(tmp_path):
    motor, _, estado = ejecutar(entrada(tmp_path))
    estado.pop("preparacion")
    with pytest.raises(ValueError, match="preparación"):
        motor.validar_estado(estado)


@pytest.mark.parametrize("coordenada", ["A2", "B2", "C2", "D2"])
def test_celda_no_vacia_omitida_abstiene_antes_del_fanout(tmp_path, monkeypatch, coordenada):
    e = entrada(tmp_path)
    original = e.fuentes.hidratar_celdas
    monkeypatch.setattr(
        e.fuentes,
        "hidratar_celdas",
        lambda doc: [prueba for prueba in original(doc) if prueba.fuente["celdas"][0] != coordenada],
    )
    _, modelo, estado = ejecutar(e)
    assert estado["resultado"]["estado"] == "abstencion" and modelo.llamadas == []
    assert "omite" in estado["resultado"]["motivos"][0]


def test_fuente_sustituida_invalida_terminal_y_parcial(tmp_path):
    e = entrada(tmp_path)
    motor, _, estado = ejecutar(e)
    (tmp_path / "referencia.pdf").write_bytes(b"fuente reemplazada")
    with pytest.raises(ValueError, match="rehidratar"):
        motor.validar_estado(estado)


def test_alerta_nueva_invalida_antes_de_reanudar(tmp_path):
    e = entrada(tmp_path)
    motor, _, estado = ejecutar(e)
    e.fuentes.bloqueos_curriculares[e.candidato.fila_id] = "Error científico comprobado"
    with pytest.raises(ValueError, match="otro codigo|otro código"):
        motor.validar_estado(estado)


def test_candidato_rehasheado_sin_actualizar_identidad_no_autoriza(tmp_path):
    e = entrada(tmp_path)
    informe = e.informe.model_copy(update={"candidatos": (e.candidato.model_copy(update={"destino": "otro"}),)})
    with pytest.raises(ValueError):
        PreparadorConocimiento(e.curriculo, informe, e.referencia, e.fuentes)


def test_copias_externas_no_cambian_expediente(tmp_path):
    e = entrada(tmp_path)
    antes = e.preparador.preparar(e.solicitud)
    e.informe.referencias.clear()
    e.referencia.nodos[0].props["definicion"] = "Una orden infiltrada"
    assert huella(antes) == huella(e.preparador.preparar(e.solicitud))


def test_payload_sin_grados_normalizados_ni_confianza(tmp_path):
    e = entrada(tmp_path)
    datos = datos_juicio(e.preparador.preparar(e.solicitud))
    texto = json.dumps(datos)
    assert "grado_min" not in texto and "confianza" not in texto
    assert (
        datos["datos_no_confiables"]["descriptores_para_identificar_no_evidencia"]["destino"]["equivalencia_grado_sv"]
        is None
    )


def test_checkpoint_terminal_no_duplica_llamadas(tmp_path):
    e = entrada(tmp_path)
    modelo = LectoresSimulados()
    motor = MotorConocimiento(e.preparador, modelo)
    opciones = dict(
        archivo=tmp_path / "checkpoint.sqlite",
        solicitud=e.solicitud.model_dump(mode="json"),
        thread_id="prueba",
        ejecucion_id="presupuesto",
        huella_entorno=motor.huella_entorno,
        max_concurrencia=4,
    )
    a = ejecutar_durable(motor, **opciones)
    b = ejecutar_durable(motor, **opciones)
    assert a == b and len(modelo.llamadas) == 4
    corrupto = copy.deepcopy(a)
    corrupto["huella_motor"] = "otro"
    with pytest.raises(ValueError, match="otro código"):
        motor.validar_estado(corrupto)


def test_esquemas_rechazan_criterios_extra_y_bools():
    esquema = ESQUEMAS_CONOCIMIENTO["juez_ciencia"]
    with pytest.raises(ValueError):
        esquema.model_validate(
            {
                "criterios": {k: True for k in esquema.model_fields["criterios"].annotation.model_fields},
                "fragmentos_ids": ["uno", "dos"],
                "explicacion": "Un texto suficientemente largo.",
                "limites": ["Síncrono"],
            }
        )
