"""Test bounded agentic retrieval with synthetic fixtures and isolated reference annotations."""

from __future__ import annotations

import hashlib
import json
from types import SimpleNamespace

import openpyxl
import pytest
from pydantic import ValidationError

from goes_science_kg.curriculo.contexto_fuentes import contexto_celdas
from goes_science_kg.motor.contratos import Evidencia
from goes_science_kg.motor.fuentes import FuentesVerificadas
from goes_science_kg.motor.registro import Registro
from goes_science_kg.motor.vertex import ConfiguracionVertex, Vertex
from goes_science_kg.recuperacion import Buscador, Documento, Resultado, huella_corpus
from goes_science_kg.recuperacion.agentic import BuscadorAgentic, ConfiguracionAgentic, PlanBusqueda
from goes_science_kg.recuperacion.evaluacion_agentic import (
    ConfiguracionComparacion,
    ConsultaEvaluacion,
    ObjetivoRelevante,
    cargar_consultas,
    comparar_agentic,
    resolver_objetivos,
)

OBJETIVO = "Compara el crecimiento de una planta con agua y luz mediante una observación."


def _documento(identificador="fila_2", *, texto=OBJETIVO, version="V4", grado=4, fila=2):
    return Documento(
        id=identificador,
        texto=texto,
        version=version,
        grado=grado,
        asignatura="Ciencias",
        fuente={"documento": "FUENTE_PRIVADA_FIXTURE", "hoja": "Unidad 1", "fila": fila, "celdas": [f"B{fila}"]},
        metadata={"campos_por_celda": {f"B{fila}": "procedimental"}},
    )


class BaselineSimulado:
    def __init__(self, documentos, rankings):
        self.documentos = {d.id: d for d in documentos}
        self.huella = huella_corpus(documentos)
        self.rankings = rankings
        self.llamadas = []

    def buscar(self, consulta, **filtros):
        self.llamadas.append((consulta, filtros))
        return self.rankings.get(consulta, [])


class ModeloSimulado:
    def __init__(self, respuesta=None, *, coste=0.001):
        self.respuesta = respuesta or {"consulta_busqueda": "crecimiento planta", "motivo": "Vocabulario concreto"}
        self.llamadas = []
        self.coste = coste

    def nombre_modelo(self, rol):
        assert rol == "planificador_recuperacion"
        return "modelo-simulado-sin-red"

    def generar(self, *, rol, sistema, mensaje, esquema):
        self.llamadas.append({"rol": rol, "sistema": sistema, "mensaje": mensaje})
        if isinstance(self.respuesta, Exception):
            raise self.respuesta
        return esquema.model_validate(self.respuesta)

    def consumo(self):
        return {"llamadas": len(self.llamadas), "reserva_usd": len(self.llamadas) * self.coste}


def _resultado(documento):
    return Resultado(documento=documento, puntaje=0.2, canales=("baseline_fixture",))


def test_consulta_suficiente_no_usa_planificador_ni_altera_ranking():
    documento = _documento()
    original = [_resultado(documento)]
    baseline = BaselineSimulado([documento], {"crecimiento planta": original})
    modelo = ModeloSimulado()
    buscador = BuscadorAgentic(baseline, modelo)
    busqueda = buscador.buscar_con_traza("crecimiento planta", version="V4", grado=4, k=1)
    assert busqueda.resultados == original
    assert busqueda.traza["diagnostico"]["motivo"] == "suficiente"
    assert busqueda.traza["planificaciones"] == 0 and busqueda.traza["busquedas"] == 1
    assert not modelo.llamadas


def test_una_reformulacion_una_busqueda_extra_conservan_filtros_y_excluyen_gold():
    documento = _documento()
    baseline = BaselineSimulado([documento], {"crecimiento planta": [_resultado(documento)]})
    modelo = ModeloSimulado()
    busqueda = BuscadorAgentic(baseline, modelo).buscar_con_traza(
        "semillas escondidas",
        version="V4",
        grado=4,
        asignatura="Ciencias",
        k=1,
        saltos_grafo=2,
    )
    assert [r.documento.id for r in busqueda.resultados] == [documento.id]
    assert len(baseline.llamadas) == 2 and len(modelo.llamadas) == 1
    assert (
        baseline.llamadas[0][1]
        == baseline.llamadas[1][1]
        == {
            "version": "V4",
            "grado": 4,
            "asignatura": "Ciencias",
            "k": 1,
            "saltos_grafo": 2,
        }
    )
    datos = json.loads(modelo.llamadas[0]["mensaje"])
    assert set(datos) == {"consulta", "filtros", "diagnostico"}
    assert documento.id not in modelo.llamadas[0]["mensaje"]
    assert documento.fuente["documento"] not in modelo.llamadas[0]["mensaje"]
    assert OBJETIVO not in modelo.llamadas[0]["mensaje"]
    assert all("plan" not in r.documento.fuente for r in busqueda.resultados)


@pytest.mark.parametrize(
    "respuesta",
    [
        RuntimeError("Fallo simulado"),
        {"consulta_busqueda": " ", "motivo": "Respuesta vacía"},
        {"consulta_busqueda": "x" * 601, "motivo": "Demasiado largo"},
        {"consulta_busqueda": "crecimiento planta", "motivo": "Objetivo claro", "ids": ["id_inventado"]},
    ],
)
def test_error_o_esquema_invalido_conserva_baseline_sin_reintentar(respuesta):
    documento = _documento()
    originales = [_resultado(documento)]
    baseline = BaselineSimulado([documento], {"semillas escondidas": originales})
    modelo = ModeloSimulado(respuesta)
    busqueda = BuscadorAgentic(baseline, modelo).buscar_con_traza("semillas escondidas", version="V4", k=1)
    assert busqueda.resultados == originales
    assert busqueda.traza["errores"]
    assert len(baseline.llamadas) == len(modelo.llamadas) == 1


def test_reformulacion_identica_no_repite_busqueda_y_no_cambia_default_de_version():
    documento = _documento()
    baseline = BaselineSimulado([documento], {})
    modelo = ModeloSimulado({"consulta_busqueda": "SEMILLAS ESCONDIDAS", "motivo": "No hay sinónimo disponible"})
    busqueda = BuscadorAgentic(baseline, modelo).buscar_con_traza("semillas escondidas", grado=4)
    assert not busqueda.resultados
    assert len(baseline.llamadas) == 1 and baseline.llamadas[0][1]["version"] is None
    assert busqueda.traza["busquedas"] == 1


def test_fusion_no_admite_ids_ajenos_contenido_suplantado_ni_version_grado_incorrectos():
    local = _documento()
    referencia = _documento("ref", version="referencia", texto="Referencia sobre crecimiento de plantas")
    otra_version = _documento("otra_version", version="V3")
    otro_grado = _documento("otro_grado", grado=9)
    inventado = _documento("no_existe")
    falsificado = local.model_copy(update={"texto": "Contenido ajeno al registro"})
    baseline = BaselineSimulado(
        [local, referencia, otra_version, otro_grado],
        {
            "semillas escondidas": [_resultado(referencia)],
            "crecimiento planta": [
                _resultado(inventado),
                _resultado(falsificado),
                _resultado(otra_version),
                _resultado(otro_grado),
                _resultado(referencia),
                _resultado(local),
            ],
        },
    )
    resultados = BuscadorAgentic(baseline, ModeloSimulado()).buscar(
        "semillas escondidas",
        version="V4",
        grado=4,
        k=2,
    )
    assert [r.documento.id for r in resultados] == [local.id, referencia.id]
    assert all(r.documento.texto != falsificado.texto for r in resultados)


def test_presupuesto_del_plan_impide_generar_y_huella_cambia_con_corpus_indice_y_config():
    documento = _documento()
    baseline = BaselineSimulado([documento], {})
    modelo = ModeloSimulado()
    limitado = BuscadorAgentic(baseline, modelo, configuracion=ConfiguracionAgentic(max_caracteres_plan=1000))
    resultado = limitado.buscar_con_traza("semillas escondidas " * 80, version="V4")
    assert resultado.traza["errores"] == ["presupuesto_plan_insuficiente"] and not modelo.llamadas
    normal = BuscadorAgentic(baseline, modelo)
    cambiado = BaselineSimulado([documento.model_copy(update={"texto": "Otro contenido"})], {})
    assert normal.huella != limitado.huella != BuscadorAgentic(cambiado, modelo).huella
    baseline.huella = "indice-distinto"
    assert normal.huella != BuscadorAgentic(baseline, modelo).huella


@pytest.fixture
def entrega(tmp_path):
    archivo = tmp_path / "malla.xlsx"
    libro = openpyxl.Workbook()
    hoja = libro.active
    hoja.title = "Unidad 1"
    hoja.append(["Contenido", "Procedimental"])
    hoja.append(["Plantas", OBJETIVO])
    libro.save(archivo)
    libro.close()
    fuentes = FuentesVerificadas(
        {
            "FUENTE_PRIVADA_FIXTURE": {
                "archivo_local": archivo.name,
                "sha256": hashlib.sha256(archivo.read_bytes()).hexdigest(),
                "version_curriculo": "V4",
            }
        },
        raiz_fuentes=tmp_path,
    )
    documentos = [_documento()]
    baseline = Buscador(documentos)
    modelo = ModeloSimulado()
    candidato = BuscadorAgentic(baseline, modelo)
    consultas = [ConsultaEvaluacion(id="caso-sintetico", consulta="semillas escondidas", version="V4", grado=4)]
    gold = {
        consultas[0].id: [
            ObjetivoRelevante(documento="FUENTE_PRIVADA_FIXTURE", hoja="Unidad 1", fila=2, celdas=("B2",))
        ]
    }

    def contextualizar(resultados, *, version, max_caracteres):
        return contexto_celdas(resultados, version=version, fuentes=fuentes, max_caracteres=max_caracteres)

    return SimpleNamespace(
        baseline=baseline,
        modelo=modelo,
        candidato=candidato,
        consultas=consultas,
        gold=gold,
        contextualizar=contextualizar,
    )


def _comparar(entrega, **opciones):
    cfg = ConfiguracionComparacion(
        k=1, repeticiones=2, min_casos_totales=1, min_casos_por_grado=1, conjunto_independiente=True
    )
    return comparar_agentic(
        entrega.consultas,
        entrega.gold,
        baseline=entrega.baseline,
        candidato=entrega.candidato,
        contextualizar=entrega.contextualizar,
        configuracion=opciones.pop("configuracion", cfg),
        medir_consumo=opciones.pop("medir_consumo", entrega.modelo.consumo),
        **opciones,
    )


def test_harness_compara_mismo_k_contexto_y_gold_por_celda_sin_enviarlo_al_modelo(entrega):
    reporte = _comparar(entrega)
    assert reporte["resumen"]["baseline"]["filas"]["recall@1"] == 0
    assert reporte["resumen"]["agentic"]["filas"]["recall@1"] == 1
    assert reporte["resumen"]["agentic"]["celdas"]["recall_contexto"] == 1
    assert reporte["gate"]["seleccionar_candidato"]
    assert reporte["gate"]["default"] == "baseline"
    for llamada in entrega.modelo.llamadas:
        assert "FUENTE_PRIVADA_FIXTURE" not in llamada["mensaje"] and "B2" not in llamada["mensaje"]
    assert all(f["caracteres_contexto"] <= 18000 for filas in reporte["ejecuciones"].values() for f in filas)


def test_gold_ausente_permanece_en_recall_y_se_reporta_separado(entrega):
    entrega.gold[entrega.consultas[0].id].append(
        ObjetivoRelevante(
            documento="FUENTE_AUSENTE",
            hoja="Unidad ausente",
            fila=8,
            celdas=("E8",),
        )
    )
    reporte = _comparar(entrega)
    assert reporte["resumen"]["agentic"]["filas"]["recall@1"] == 0.5
    assert reporte["resumen"]["agentic"]["celdas"]["recall_contexto"] == 0.5
    resuelto = reporte["gold_resuelto_offline"][entrega.consultas[0].id]
    assert len(resuelto["ausentes_en_indice"]) == 1
    assert resuelto["ausentes_en_indice"][0]["motivo"] == "fila_ausente"


def test_resolver_objetivos_no_inventa_selector_y_rechaza_duplicar_fila(entrega):
    objetivo = ObjetivoRelevante(documento="FUENTE_PRIVADA_FIXTURE", hoja="Unidad 1", fila=2, celdas=("Z2",))
    resuelto = resolver_objetivos([objetivo], entrega.baseline.documentos, version="V4")
    assert resuelto["celdas"] == ["fila_2#CELDA:Z2"]
    assert resuelto["ausentes_en_indice"][0]["motivo"] == "selector_ausente"
    duplicado = _documento("id_distinto_misma_fila")
    with pytest.raises(ValueError, match="ambiguamente"):
        resolver_objetivos([objetivo], {**entrega.baseline.documentos, duplicado.id: duplicado}, version="V4")


def test_gate_no_selecciona_sin_independencia_muestra_consumo_o_con_coste_excesivo(entrega):
    sin_medicion = _comparar(entrega, medir_consumo=None, configuracion=ConfiguracionComparacion(k=1))
    assert not sin_medicion["gate"]["seleccionar_candidato"]
    assert set(sin_medicion["gate"]["motivos"]) >= {
        "conjunto_no_declarado_independiente",
        "muestra_total_insuficiente",
        "muestra_por_grado_insuficiente",
        "consumo_no_medido",
    }
    entrega.modelo.coste = 0.05
    caro = _comparar(entrega)
    assert "presupuesto_coste_excedido" in caro["gate"]["motivos"]


def test_mejora_global_no_oculta_regresion_en_un_grado():
    mejora = _documento("fila_grado4", fila=2)
    correcto = _documento("z_correcto", grado=5, fila=3)
    incorrecto = _documento("a_incorrecto", grado=5, fila=4)

    class BaselineFiltrado(BaselineSimulado):
        def buscar(self, consulta, **filtros):
            return [r for r in super().buscar(consulta, **filtros) if r.documento.grado == filtros["grado"]][
                : filtros["k"]
            ]

    baseline = BaselineFiltrado(
        [mejora, correcto, incorrecto],
        {
            "pregunta abstracta": [_resultado(correcto)],
            "crecimiento planta": [_resultado(mejora), _resultado(incorrecto)],
        },
    )
    modelo = ModeloSimulado()
    candidato = BuscadorAgentic(baseline, modelo)
    consultas = [
        ConsultaEvaluacion(
            id=f"caso_{i}",
            consulta="semillas escondidas" if i < 2 else "pregunta abstracta",
            version="V4",
            grado=4 if i < 2 else 5,
        )
        for i in range(3)
    ]
    gold = {
        c.id: [
            ObjetivoRelevante(
                documento="FUENTE_PRIVADA_FIXTURE",
                hoja="Unidad 1",
                fila=2 if c.grado == 4 else 3,
                celdas=("B2" if c.grado == 4 else "B3",),
            )
        ]
        for c in consultas
    }

    def contexto_simulado(resultados, **_):
        return [
            Evidencia.crear(
                f"{r.documento.id}#CELDA:{r.documento.fuente['celdas'][0]}",
                r.documento.texto,
                r.documento.fuente,
                r.documento.version,
            )
            for r in resultados
        ]

    reporte = comparar_agentic(
        consultas,
        gold,
        baseline=baseline,
        candidato=candidato,
        contextualizar=contexto_simulado,
        medir_consumo=modelo.consumo,
        configuracion=ConfiguracionComparacion(
            k=1, repeticiones=1, min_casos_totales=1, min_casos_por_grado=1, conjunto_independiente=True
        ),
    )
    assert reporte["resumen"]["agentic"]["filas"]["mrr"] > reporte["resumen"]["baseline"]["filas"]["mrr"]
    assert "regresion_grado:5:filas:mrr" in reporte["gate"]["motivos"]
    assert not reporte["gate"]["seleccionar_candidato"]


def test_loader_extrae_lista_blanca_de_consultas_y_valida_gold(tmp_path):
    archivo = tmp_path / "casos.json"
    archivo.write_text(
        json.dumps(
            {
                "casos": [
                    {
                        "id": "c1",
                        "consulta": "Una pregunta de ciencias",
                        "version": "V4",
                        "grado": 4,
                        "reservado_evaluador": {"secreto": "NO ENVIAR"},
                        "objetivos_relevantes": ["TAMPOCO ENVIAR"],
                    }
                ]
            }
        )
    )
    consultas = cargar_consultas(archivo)
    assert set(consultas[0].model_dump()) == {"id", "consulta", "version", "grado", "asignatura"}
    assert "NO ENVIAR" not in consultas[0].model_dump_json()
    with pytest.raises(ValidationError):
        ObjetivoRelevante(documento="archivo", hoja="Hoja", fila=2, celdas=("A3",))


def test_vertex_existente_cachea_plan_y_no_rebasa_reserva_durable(tmp_path):
    pytest.importorskip("google.genai")
    registro = Registro(tmp_path / "ledger.sqlite")
    cfg = ConfiguracionVertex(
        proyecto="proyecto-simulado",
        modelos={"planificador_recuperacion": "simulado"},
        tarifas={"simulado": {"entrada": 1, "salida": 1}},
        max_llamadas=1,
        max_usd=1,
        max_salida_tokens=256,
        reintentos=0,
    )
    modelo = Vertex(cfg, registro, "agentic-sin-red")
    llamadas = []

    def generar(**kwargs):
        llamadas.append(kwargs)
        return SimpleNamespace(
            text=PlanBusqueda(consulta_busqueda="crecimiento planta", motivo="Sinónimo concreto").model_dump_json(),
            usage_metadata=SimpleNamespace(prompt_token_count=50, candidates_token_count=20, thoughts_token_count=0),
        )

    modelo.__dict__["cliente"] = SimpleNamespace(models=SimpleNamespace(generate_content=generar))
    documento = _documento()
    baseline = BaselineSimulado([documento], {"crecimiento planta": [_resultado(documento)]})
    buscador = BuscadorAgentic(baseline, modelo)
    assert buscador.buscar("semillas escondidas", version="V4")
    assert buscador.buscar("semillas escondidas", version="V4")
    assert len(llamadas) == registro.resumen("agentic-sin-red")["llamadas"] == 1
    assert 0 < registro.resumen("agentic-sin-red")["reserva_usd"] <= 1
