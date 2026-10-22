"""Test reproducible discovery candidates, ambiguity, and evidence boundaries without remote services."""

from __future__ import annotations

import hashlib
import json
from io import BytesIO

import pytest
import yaml
from openpyxl import Workbook
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from goes_science_kg.curriculo import cargar_curriculo
from goes_science_kg.modelos import Arista, Fuente, Nodo, TipoArista, TipoNodo
from goes_science_kg.producto._conocimiento_lexico import IndiceAlias
from goes_science_kg.producto.conocimiento import (
    EdicionEsperada,
    InformeConocimiento,
    PoliticaConocimiento,
    generar_candidatos_conocimiento,
)
from goes_science_kg.producto.contratos import ReferenciasProducto


def _curriculo(tmp_path, *, texto="Analiza el agua y la temperatura.", grado=2, contenido="Agua"):
    carpeta = tmp_path / "v4"
    carpeta.mkdir(exist_ok=True)
    libro = Workbook()
    hoja = libro.active
    hoja.title = "Matriz"
    hoja.append(["Contenido", "Procedimental", "Indicadores de logro", "Evidencia de aprendizaje"])
    hoja.append([contenido, texto, "Explica lo observado.", "Tabla de resultados."])
    libro.save(carpeta / "malla.xlsx")
    libro.close()
    contenido_fuente = (carpeta / "malla.xlsx").read_bytes()
    (tmp_path / "procedencia.json").write_text(
        json.dumps(
            {
                "version": "V4",
                "archivos": [
                    {
                        "archivo": "malla.xlsx",
                        "sha256": hashlib.sha256(contenido_fuente).hexdigest(),
                        "bytes": len(contenido_fuente),
                    }
                ],
            }
        )
    )
    cfg = {
        "version": "V4",
        "raiz": ".",
        "directorio": "v4",
        "procedencia": "procedencia.json",
        "alias_campos": {
            "contenido": ["Contenido"],
            "procedimental": ["Procedimental"],
            "indicadores_logro": ["Indicadores de logro"],
            "evidencia_aprendizaje": ["Evidencia de aprendizaje"],
        },
        "fuentes": [
            {
                "archivo": "malla.xlsx",
                "hojas": [
                    {
                        "nombre": "Matriz",
                        "tratamiento": "curricular",
                        "motivo": "Fuente sintética",
                        "grado": grado,
                        "asignatura_malla": "Ciencias",
                        "unidad": "Unidad sintética",
                        "filas_encabezado": [1],
                    }
                ],
            }
        ],
    }
    ruta_config = tmp_path / "mallas.yaml"
    ruta_config.write_text(yaml.safe_dump(cfg, allow_unicode=True), encoding="utf-8")
    return cargar_curriculo(ruta_config)


def _concepto(identidad="conocimiento-agua", etiqueta="Agua", **props):
    return Nodo(
        id=identidad,
        tipo=TipoNodo.CONCEPTO,
        etiqueta=etiqueta,
        asignatura="fisica",
        props={"sinonimos": [], "definicion": "Definición histórica derivada", **props},
    )


def _referencia(*nodos, aristas=()):
    return ReferenciasProducto(
        nodos=nodos, aristas=aristas, procedencia={"version_curriculo": "V3", "clase": "historica"}
    )


def _generar(
    tmp_path, referencia, *, texto="Analiza el agua y la temperatura.", contenido="Agua", grado=2, politica=None
):
    curriculo = _curriculo(tmp_path, texto=texto, grado=grado, contenido=contenido)
    return generar_candidatos_conocimiento(
        curriculo, referencia, raiz_v4=tmp_path / "v4", raiz_historica=tmp_path, politica=politica
    )


def _pdf(texto):
    escritor = PdfWriter()
    pagina = escritor.add_blank_page(width=600, height=800)
    fuente = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    pagina[NameObject("/Resources")] = DictionaryObject(
        {
            NameObject("/Font"): DictionaryObject(
                {
                    NameObject("/F1"): escritor._add_object(fuente),
                }
            )
        }
    )
    contenido = DecodedStreamObject()
    contenido.set_data(f"BT /F1 12 Tf 50 750 Td ({texto}) Tj ET".encode())
    pagina[NameObject("/Contents")] = escritor._add_object(contenido)
    salida = BytesIO()
    escritor.write(salida)
    return salida.getvalue()


def _pais(tmp_path, *, version="2013", sha=None, extension="pdf", pagina=1):
    contenido = _pdf("Water changes when temperature changes.")
    (tmp_path / "referencia.pdf").write_bytes(contenido)
    digest = sha or hashlib.sha256(contenido).hexdigest()
    documento = Nodo(
        id="DOC:documento-pais",
        tipo=TipoNodo.DOCUMENTO,
        etiqueta="Currículo extranjero",
        props={
            "archivo_local": f"referencia.{extension}",
            "sha256": digest,
            "version_documental": version,
            "anio": "2013",
        },
    )
    objetivo = Nodo(
        id="aprendizaje-extranjero",
        tipo=TipoNodo.OBJETIVO_PAIS,
        etiqueta="Investigar el agua.",
        grado=9,
        fuente=Fuente(documento="documento-pais", pagina=pagina),
        props={"pais": "PAIS_SINTETICO", "grado_o_tramo": "Stage 10", "grado_min": 9, "grado_max": 9},
    )
    return documento, objetivo, digest


def test_enlace_es_candidato_anclado_a_celda_y_no_etiqueta_aceptada(tmp_path):
    informe = _generar(tmp_path, _referencia(_concepto()))
    candidato = next(c for c in informe.candidatos if c.tipo == "fila_concepto")
    assert candidato.destino == "conocimiento-agua" and candidato.estado == "candidato"
    assert "fuente_primaria_no_identificada" in candidato.bloqueos_aceptacion
    assert "juicio_especializado_pendiente" in candidato.bloqueos_aceptacion
    assert candidato.evidencias_locales and not candidato.referencias_evidencia
    for id_evidencia in candidato.evidencias_locales:
        evidencia = informe.evidencias[id_evidencia]
        assert evidencia.fuente["verificacion"] == "contenido_fuente" and len(evidencia.fuente["sha256"]) == 64
        assert evidencia.fuente["celdas_verificadas"]
        assert "Agua" in evidencia.texto or "agua" in evidencia.texto
    assert informe.aceptados == () and informe.dag_aceptado.aristas == ()
    assert informe.resumen["alineaciones_confirmadas"] == 0


def test_alias_compartido_es_ambiguo_en_disciplinas_distintas(tmp_path):
    a = _concepto("fuerza-fisica", "Equilibrio")
    b = _concepto("equilibrio-quimico", "Equilibrio").model_copy(update={"asignatura": "quimica"})
    informe = _generar(tmp_path, _referencia(a, b), texto="Estudia el equilibrio.", contenido="Sistema")
    candidatos = [c for c in informe.candidatos if c.tipo == "fila_concepto"]
    assert len(candidatos) == 2 and all(c.estado == "ambiguo" for c in candidatos)
    assert all(set(c.alternativas) == {a.id, b.id} for c in candidatos)


def test_presupuesto_no_elimina_solo_una_alternativa_de_un_alias_ambiguo(tmp_path):
    referencia = _referencia(_concepto("a", "Equilibrio"), _concepto("b", "Equilibrio"))
    informe = _generar(
        tmp_path,
        referencia,
        texto="Estudia el equilibrio.",
        contenido="Sistema",
        politica=PoliticaConocimiento(max_conceptos_por_fila=1),
    )
    assert not informe.candidatos
    assert informe.resumen["omitidos_por_presupuesto"]["vocabulario"] == 2
    assert informe.resumen["filas_sin_candidato_por_presupuesto"] == 1


def test_simbolos_cortos_y_polisemia_de_co_se_conservan():
    indice = IndiceAlias([_concepto("monoxido", "CO"), _concepto("cobalto", "Co"), _concepto("acidez", "pH")])
    assert {c.nodo_id for c in indice.buscar("Observa CO y mide pH.")} == {"monoxido", "acidez"}
    assert {c.nodo_id for c in indice.buscar("Observa Co.")} == {"cobalto"}
    assert not indice.buscar("co PH")


def test_no_stemming_ni_coincidencia_dentro_de_otra_palabra():
    indice = IndiceAlias([_concepto("sal", "sal"), _concepto("gen", "gen")])
    assert not indice.buscar("salinidad y genes")
    assert {c.nodo_id for c in indice.buscar("gen y sal")} == {"sal", "gen"}


def test_polimorfismo_concepto_practica_y_sinonimos_invalidos_no_colisionan(tmp_path):
    practica = Nodo(
        id="actividad-sin-prefijo",
        tipo=TipoNodo.PRACTICA,
        etiqueta="Analiza datos",
        props={"sinonimos": ["Analiza el agua"]},
    )
    concepto = _concepto(sinonimos="No debe indexarse carácter por carácter")
    informe = _generar(tmp_path, _referencia(practica, concepto))
    assert {c.tipo for c in informe.candidatos} == {"fila_concepto", "fila_practica"}
    assert informe.resumen["avisos_vocabulario"]


def test_nivel_historico_incompatible_no_asigna_grado_ni_valida_enlace(tmp_path):
    informe = _generar(tmp_path, _referencia(_concepto(nivel="bachillerato")), grado=2)
    assert any("nivel_historico_no_corresponde_al_grado_local" in c.bloqueos_aceptacion for c in informe.candidatos)
    assert not informe.aceptados and informe.dag_aceptado.estado == "sin_progresion_verificada"


def test_mencion_negada_es_advertida_sin_inferir_ensenanza(tmp_path):
    informe = _generar(
        tmp_path, _referencia(_concepto()), texto="No se estudia agua en esta actividad.", contenido="Sistema"
    )
    assert any("negación" in a for c in informe.candidatos for a in c.advertencias)
    assert not informe.aceptados


def test_contraste_pais_preserva_edicion_y_pagina_sin_equivaler_grados(tmp_path):
    documento, objetivo, digest = _pais(tmp_path)
    politica = PoliticaConocimiento(
        ediciones_por_documento={
            "documento-pais": EdicionEsperada(sha256=digest, version_documental="2013"),
        }
    )
    informe = _generar(tmp_path, _referencia(_concepto(), documento, objetivo), politica=politica)
    candidato = next(c for c in informe.candidatos if c.tipo == "contraste_pais")
    assert candidato.estado == "candidato" and candidato.referencias_evidencia
    assert candidato.contexto["equivalencia_grado_sv"] is None
    assert candidato.contexto["grado_o_tramo_extranjero"] == "Stage 10"
    assert candidato.contexto["grado_sv"] == 2
    for identidad in candidato.referencias_evidencia:
        evidencia = informe.evidencias[identidad]
        assert evidencia.fuente["sha256"] == digest and evidencia.fuente["pagina"] == 1
        assert "Water changes" in evidencia.texto


def test_mismatch_de_version_curricular_extranjera_bloquea_aceptacion(tmp_path):
    documento, objetivo, digest = _pais(tmp_path)
    politica = PoliticaConocimiento(
        ediciones_por_documento={
            "documento-pais": EdicionEsperada(sha256=digest, version_documental="2023"),
        }
    )
    informe = _generar(tmp_path, _referencia(_concepto(), documento, objetivo), politica=politica)
    candidato = next(c for c in informe.candidatos if c.tipo == "contraste_pais")
    assert candidato.estado == "bloqueado"
    assert "edicion_documental_no_coincide_con_politica" in candidato.bloqueos_aceptacion
    assert candidato.contexto["edicion"]["version_documental_declarada"] == "2013"


@pytest.mark.parametrize(
    "extension,hash_invalido,pagina", [("docx", False, None), ("html", False, None), ("pdf", True, 1)]
)
def test_formatos_sin_hidratador_y_sha_no_hex_no_se_convierten_en_evidencia(tmp_path, extension, hash_invalido, pagina):
    documento, objetivo, _ = _pais(
        tmp_path, extension=extension, sha="ver manifest antiguo" if hash_invalido else None, pagina=pagina
    )
    informe = _generar(tmp_path, _referencia(_concepto(), documento, objetivo))
    candidato = next(c for c in informe.candidatos if c.tipo == "contraste_pais")
    assert candidato.estado == "bloqueado" and not candidato.referencias_evidencia
    assert informe.metricas["fuentes_referencia"]["archivos_leidos"] == 0


def test_ruta_trabaja_historica_solo_propone_contraste_por_revalidar(tmp_path):
    documento, objetivo, _ = _pais(tmp_path)
    objetivo = objetivo.model_copy(update={"etiqueta": "Una frase extranjera sin el alias local"})
    arista = Arista(
        origen=objetivo.id,
        destino="conocimiento-agua",
        tipo=TipoArista.TRABAJA,
        metodo="regla",
        version="clasificacion-legacy",
    )
    informe = _generar(tmp_path, _referencia(_concepto(), documento, objetivo, aristas=(arista,)))
    candidato = next(c for c in informe.candidatos if c.tipo == "contraste_pais")
    assert candidato.metodo == "ruta_historica_por_revalidar"
    assert candidato.contexto["rutas"][0]["arista_historica"]["version"] == "clasificacion-legacy"
    assert not informe.aceptados


def test_ciclo_de_hipotesis_no_entra_en_dag_aceptado(tmp_path):
    a, b = _concepto("a", "Agua"), _concepto("b", "Temperatura")
    aristas = tuple(
        Arista(origen=o, destino=d, tipo=TipoArista.PRERREQUISITO_DE, metodo="regla")
        for o, d in ((a.id, b.id), (b.id, a.id))
    )
    informe = _generar(tmp_path, _referencia(a, b, aristas=aristas))
    assert informe.resumen["por_tipo"]["prerrequisito"] == 2
    assert informe.dag_aceptado.ciclos_candidatos == (("a", "b"),)
    assert not informe.dag_aceptado.aristas and not informe.resumen["dag_verificado"]


def test_salida_no_puede_declarar_aceptado_true_sin_workflow_especializado(tmp_path):
    informe = _generar(tmp_path, _referencia(_concepto()))
    datos = informe.model_dump(mode="json")
    datos["aceptados"] = [{"aceptar": True}]
    with pytest.raises(ValueError):
        InformeConocimiento.model_validate(datos)


def test_orden_de_entrada_no_cambia_candidatos_y_fuentes_se_cachean(tmp_path):
    a, b = _concepto("agua", "Agua"), _concepto("temperatura", "Temperatura")
    curriculo = _curriculo(tmp_path)
    r1 = generar_candidatos_conocimiento(curriculo, _referencia(a, b), raiz_v4=tmp_path / "v4")
    r2 = generar_candidatos_conocimiento(curriculo, _referencia(b, a), raiz_v4=tmp_path / "v4")
    assert r1.huella_candidatos == r2.huella_candidatos and r1.candidatos == r2.candidatos
    assert r1.metricas["fuentes_v4"]["archivos_leidos"] == r1.metricas["fuentes_v4"]["libros_parseados"] == 1
    assert r1.metricas["segundos_total"] >= 0 and r1.metricas["memoria_pico_proceso_bytes"] > 0


def test_fuente_local_alterada_no_se_sustituye_por_texto_metadata(tmp_path):
    curriculo = _curriculo(tmp_path)
    (tmp_path / "v4/malla.xlsx").write_bytes(b"alterado")
    with pytest.raises(ValueError, match="verificables|respaldo"):
        generar_candidatos_conocimiento(curriculo, _referencia(_concepto()), raiz_v4=tmp_path / "v4")


def test_validacion_entrada_y_politica_no_admite_version_ajena_o_campos_instruccionales(tmp_path):
    curriculo = _curriculo(tmp_path)
    with pytest.raises(ValueError, match="V3"):
        generar_candidatos_conocimiento(curriculo, ReferenciasProducto(), raiz_v4=tmp_path / "v4")
    with pytest.raises(ValueError, match="Campos locales"):
        PoliticaConocimiento(campos_locales=("notacion",))


def test_registro_documental_ambiguo_no_sobrescribe_la_fuente(tmp_path):
    a = Nodo(id="DOC:una-fuente", tipo=TipoNodo.DOCUMENTO, etiqueta="Primera fuente")
    b = Nodo(id="una-fuente", tipo=TipoNodo.DOCUMENTO, etiqueta="Otra fuente con registro coincidente")
    with pytest.raises(ValueError, match="documental ambigua"):
        _generar(tmp_path, _referencia(_concepto(), a, b))
