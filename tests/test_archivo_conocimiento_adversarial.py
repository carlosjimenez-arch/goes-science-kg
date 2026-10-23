"""Reject rehashed archives that substitute the curriculum or edition reviewed originally."""

from __future__ import annotations

import hashlib
import json

import pytest
from test_producto_v4 import catalogo as catalogo
from test_producto_v4 import curriculo as curriculo
from test_publicacion_conocimiento import preparado as preparado

from goes_science_kg.motor.contratos import huella
from goes_science_kg.motor.validacion_conocimiento import resolver_resultado
from goes_science_kg.producto._juicios_contratos import ExpedienteConocimiento, SolicitudConocimiento
from goes_science_kg.producto.conocimiento_publicado import ArchivoConocimiento, validar_archivo_conocimiento
from goes_science_kg.producto.relaciones import coleccionar_resultados


def _archivo(datos):
    datos["huella_archivo"] = huella({k: v for k, v in datos.items() if k != "huella_archivo"})
    return ArchivoConocimiento.model_validate(datos)


def _reconstruir(datos):
    """Retain favorable synthetic votes while reconstructing all derived outcomes."""

    # Historical test notes:
    # Así las pruebas de preparación no dependen de detectar una huella vieja: el rechazo
    # debe proceder del contraste determinista con la fila y las fuentes canónicas.
    resultados, filas = [], {}
    anteriores = {r["solicitud"]["candidato_id"]: r for r in datos["coleccion"]["resultados"]}
    usados = {i for registro in datos["expedientes"].values() for i in registro["evidencias_ids"]}
    datos["evidencias"] = {i: e for i, e in datos["evidencias"].items() if i in usados}
    for id_, registro in datos["expedientes"].items():
        preparacion = registro["preparacion"]
        evidencias = [datos["evidencias"][i] for i in registro["evidencias_ids"]]
        por_id = {e["id"]: e for e in evidencias}
        for fragmento in preparacion["fragmentos"]:
            e = por_id[fragmento["evidencia_id"]]
            material = json.dumps(
                [e["id"], e["version"], e["huella"], e["fuente"], fragmento["literal"]],
                ensure_ascii=False,
                sort_keys=True,
            )
            fragmento["id"] = "F:" + hashlib.sha256(material.encode()).hexdigest()[:24]
        expediente = ExpedienteConocimiento.model_validate(preparacion | {"evidencias": evidencias})
        anterior = anteriores[id_]
        salidas = {}
        for dictamen in anterior["dictamenes"]:
            dictamen["huella_tarea"] = huella(expediente)
            citas = [c for c in dictamen["citas"] if c["evidencia_id"] in por_id]
            for ids in expediente.grupos.values():
                if not {c["evidencia_id"] for c in citas}.intersection(ids):
                    f = next(f for f in expediente.fragmentos if f.evidencia_id in ids)
                    citas.append({"evidencia_id": f.evidencia_id, "literal": f.literal})
            dictamen["citas"] = citas
            salidas[dictamen["rol"]] = {"dictamen": dictamen, "error": None}
        resultado = resolver_resultado(
            expediente=expediente,
            solicitud=SolicitudConocimiento.model_validate(anterior["solicitud"]),
            ejecucion_id=anterior["ejecucion_id"],
            huella_motor=datos["coleccion"]["huella_motor"],
            modelos=datos["modelos"],
            salidas=salidas,
        )
        assert resultado.estado == "respaldado", "El cierre sintético debe ser internamente coherente"
        resultados.append(resultado)
        filas[id_] = expediente.fila_id
    datos["coleccion"] = coleccionar_resultados(
        resultados,
        huella_curriculo=datos["huella_curriculo"],
        huella_motor=datos["coleccion"]["huella_motor"],
        filas_por_candidato=filas,
    ).model_dump(mode="json")
    return _archivo(datos)


def _rechaza(preparado, archivo):
    with pytest.raises(ValueError):
        validar_archivo_conocimiento(
            archivo,
            preparado.curriculo,
            catalogo=preparado.catalogo,
            modelos_esperados=preparado.archivo.modelos,
        )


@pytest.mark.parametrize("campo", ["etiqueta", "pais", "tramo", "pagina", "disciplina", "definicion"])
def test_extremo_reetiquetado_no_reutiliza_juicios_del_registro_anterior(preparado, campo):
    datos = preparado.archivo.model_dump(mode="json")
    nodo = datos["nodos_referencia"][0]
    if campo == "etiqueta":
        nodo["etiqueta"] = "Demostrar la fisión nuclear"
    elif campo == "pais":
        nodo["props"]["pais"] = "OTRO_PAIS"
    elif campo == "tramo":
        nodo["props"]["grado_o_tramo"] = "Universidad"
    elif campo == "pagina":
        nodo["fuente"]["pagina"] = 99
    elif campo == "disciplina":
        nodo["asignatura"] = "quimica"
    else:
        nodo["props"]["definicion"] = "Una definición distinta de la examinada"
    _rechaza(preparado, _archivo(datos))


@pytest.mark.parametrize("alteracion", ["ausente", "sha", "version"])
def test_edicion_fijada_se_contrasta_con_fuente_extranjera(preparado, alteracion):
    datos = preparado.archivo.model_dump(mode="json")
    ediciones = datos["politica"]["ediciones_por_documento"]
    documento = next(iter(ediciones))
    if alteracion == "ausente":
        ediciones.pop(documento)
    elif alteracion == "sha":
        ediciones[documento]["sha256"] = "0" * 64
    else:
        ediciones[documento]["version_documental"] = "2099"
    _rechaza(preparado, _archivo(datos))


@pytest.mark.parametrize("grupo", ["evaluacion_local", "objetivo_extranjero"])
def test_grupo_obligatorio_omitido_no_se_oculta_reconstruyendo_el_cierre(preparado, grupo):
    datos = preparado.archivo.model_dump(mode="json")
    registro = next(iter(datos["expedientes"].values()))
    assert registro["preparacion"]["grupos"].pop(grupo)
    _rechaza(preparado, _reconstruir(datos))


@pytest.mark.parametrize("grupo", ["objetivo_local", "evaluacion_local"])
def test_grupos_locales_no_intercambian_roles_de_las_celdas(preparado, grupo):
    datos = preparado.archivo.model_dump(mode="json")
    grupos = next(iter(datos["expedientes"].values()))["preparacion"]["grupos"]
    otro = "evaluacion_local" if grupo == "objetivo_local" else "objetivo_local"
    assert set(grupos[grupo]) != set(grupos[otro])
    grupos[grupo] = list(grupos[otro])
    _rechaza(preparado, _reconstruir(datos))


def test_celda_local_no_citada_sigue_siendo_obligatoria_en_el_expediente(preparado):
    datos = preparado.archivo.model_dump(mode="json")
    id_, registro = next(iter(datos["expedientes"].items()))
    resultado = next(r for r in datos["coleccion"]["resultados"] if r["solicitud"]["candidato_id"] == id_)
    citadas = {c["evidencia_id"] for d in resultado["dictamenes"] for c in d["citas"]}
    omitida = next(
        i for i in registro["evidencias_ids"] if datos["evidencias"][i]["version"] == "V4" and i not in citadas
    )
    registro["evidencias_ids"].remove(omitida)
    preparacion = registro["preparacion"]
    preparacion["fragmentos"] = [f for f in preparacion["fragmentos"] if f["evidencia_id"] != omitida]
    preparacion["grupos"] = {g: [i for i in ids if i != omitida] for g, ids in preparacion["grupos"].items()}
    assert all(preparacion["grupos"].values())
    _rechaza(preparado, _reconstruir(datos))


@pytest.mark.parametrize(
    "campo",
    ["tipo_excel", "valor_real", "valor_original", "coordenada_origen", "coordenada_solicitada", "valor_es_formula"],
)
def test_celda_fisica_modificada_con_hashes_coherentes_no_es_respaldo(preparado, campo):
    datos = preparado.archivo.model_dump(mode="json")
    prueba = next(e for e in datos["evidencias"].values() if e["version"] == "V4")
    celda = prueba["fuente"]["celdas_verificadas"][0]
    if campo == "tipo_excel":
        celda[campo] = "f" if celda[campo] != "f" else "s"
    elif campo == "valor_es_formula":
        celda[campo] = not celda[campo]
    elif campo.startswith("coordenada_"):
        celda[campo] = "ZZ999"
    else:
        celda[campo] = "Un valor ajeno al insumo"
    _rechaza(preparado, _reconstruir(datos))


def test_identidad_de_evidencia_no_puede_atribuir_otra_celda_de_la_misma_fila(preparado):
    datos = preparado.archivo.model_dump(mode="json")
    anterior = next(i for i, e in datos["evidencias"].items() if e["version"] == "V4")
    nueva = anterior.partition("#CELDA:")[0] + "#CELDA:ZZ999"
    datos["evidencias"][nueva] = datos["evidencias"].pop(anterior)
    datos["evidencias"][nueva]["id"] = nueva
    for registro in datos["expedientes"].values():
        registro["evidencias_ids"] = [nueva if i == anterior else i for i in registro["evidencias_ids"]]
        for fragmento in registro["preparacion"]["fragmentos"]:
            if fragmento["evidencia_id"] == anterior:
                fragmento["evidencia_id"] = nueva
        registro["preparacion"]["grupos"] = {
            g: [nueva if i == anterior else i for i in ids] for g, ids in registro["preparacion"]["grupos"].items()
        }
    for resultado in datos["coleccion"]["resultados"]:
        for dictamen in resultado["dictamenes"]:
            for cita in dictamen["citas"]:
                if cita["evidencia_id"] == anterior:
                    cita["evidencia_id"] = nueva
    _rechaza(preparado, _reconstruir(datos))
