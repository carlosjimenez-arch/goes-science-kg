"""Las erratas conocidas no se convierten en respaldo mediante una cita exacta."""

import json

import pytest

from goes_science_kg.config import ruta
from goes_science_kg.curriculo import cargar_curriculo
from goes_science_kg.curriculo.contexto_fuentes import fuentes_del_curriculo
from goes_science_kg.motor.contratos import Evidencia, Solicitud
from goes_science_kg.motor.flujo import Motor
from goes_science_kg.producto.garantias import bloqueos_cientificos
from goes_science_kg.recuperacion import Buscador, Documento


@pytest.fixture(scope="module")
def curriculo():
    return cargar_curriculo()


def test_localiza_alertas_contra_bytes_y_celdas_actuales(curriculo):
    fuentes = fuentes_del_curriculo(curriculo, raiz_v4=ruta("insumos/v4"))
    bloqueos = bloqueos_cientificos(curriculo, fuentes, ruta("docs/investigacion/alertas_v4.json"))
    filas = {f.id: f for f in curriculo.filas}
    # W3:W13 y W14:W29 son celdas combinadas: la errata afecta las 27 filas,
    # no solo las dos anclas visibles. S3:S13 comparte parte de ese alcance.
    assert {filas[i].fila for i in bloqueos} == set(range(3, 30))
    assert {filas[i].hoja for i in bloqueos} == {"Biología 10.°"}
    fuentes.bloqueos_curriculares = bloqueos
    id_fila = next(iter(bloqueos))
    assert fuentes.motivos_bloqueo([Evidencia.crear(f"{id_fila}#CELDA:E3", "Objetivo", {}, "V4")])


@pytest.mark.parametrize("campo", ["sha256", "ancla_original"])
def test_rechaza_alerta_cuya_edicion_o_ancla_no_coincide(curriculo, tmp_path, campo):
    datos = json.loads(ruta("docs/investigacion/alertas_v4.json").read_text())
    if campo == "sha256":
        datos["alertas"][0]["fuente"][campo] = "0" * 64
    else:
        datos["alertas"][0][campo] = "Ancla ajena al original"
    archivo = tmp_path / "alertas.json"
    archivo.write_text(json.dumps(datos))
    fuentes = fuentes_del_curriculo(curriculo, raiz_v4=ruta("insumos/v4"))
    with pytest.raises(ValueError):
        bloqueos_cientificos(curriculo, fuentes, archivo)


def test_error_cientifico_localizado_abstiene_antes_de_modelos(tmp_path):
    from goes_science_kg.motor.fuentes import FuentesVerificadas

    class FuentesSimuladas(FuentesVerificadas):
        def hidratar(self, documento):
            return Evidencia.crear(documento.id, documento.texto, documento.fuente, documento.version)

    class ProveedorQueNoDebeLlamarse:
        def generar(self, **kwargs):
            raise AssertionError("Una alerta bloqueante debe evitar cualquier generación")

    doc = Documento(
        id="fila-bloqueada", texto="Objetivo curricular localizado con errata conocida",
        fuente={"documento": "local", "hoja": "Biología", "fila": 3}, version="V4", grado=10,
        asignatura="biologia",
    )
    fuentes = FuentesSimuladas(
        {}, raiz_fuentes=tmp_path, bloqueos_curriculares={doc.id: "Errata científica documentada"}
    )
    salida = Motor(Buscador([doc]), ProveedorQueNoDebeLlamarse(), fuentes=fuentes).compilar().invoke(
        {"solicitud": Solicitud(consulta="Objetivo curricular", version_curriculo="V4", grado=10,
                                asignatura="biologia").model_dump(), "ejecucion_id": "bloqueo-local"}
    )["resultado"]
    assert salida["estado"] == "abstencion" and salida["propuesta"] is None
    assert salida["motivos"] == ["Errata científica documentada"]
