"""El editor cambia contenido, sin falsificar ni reutilizar votos anteriores."""

import json
from copy import deepcopy
from types import SimpleNamespace

import pytest
from test_clases import ProveedorGuion, guion

from goes_science_kg.clases.editorial import guardar_parche, preparar, validar
from goes_science_kg.materiales.compilacion import serializar, sha


@pytest.fixture
def expediente(tmp_path):
    anterior = guion().model_dump(mode="json")
    resultado = tmp_path / "data/clases_v4/ejecuciones/anterior/resultado.json"
    resultado.parent.mkdir(parents=True)
    raw = serializar({"snapshot_id": "s", "filas": {"fila1": {"guion": anterior}}})
    resultado.write_bytes(raw)
    parche = {
        "version": "parche-editorial-clases-1",
        "editor": "Codex, corrección explícita de desarrollo",
        "cambios": [
            {
                "fila_id": "fila1",
                "resultado": resultado.relative_to(tmp_path).as_posix(),
                "resultado_sha256": sha(raw),
                "campos": [
                    {
                        "campo": "retroalimentacion",
                        "anterior": anterior["retroalimentacion"],
                        "nuevo": "Pide describir una propiedad que el dibujo permita observar; distingue esa "
                        "observación de una conjetura sobre una propiedad que el dibujo no muestra.",
                        "motivo": "Separar la observación representada de una inferencia que carece de evidencia.",
                    }
                ],
            }
        ],
        "limite": "Es un borrador editorial nuevo, sin aprobación previa; requiere cuatro nuevas revisiones.",
    }
    archivo = tmp_path / "data/clases_v4/ediciones_editoriales/ejemplo.json"
    p = {
        "version": "preparacion-clases-1",
        "snapshot_id": "s",
        "corpus_sha256": "a" * 64,
        "escenario": {"minutos_por_sesion_propuesta": 60},
        "fuentes": [],
        "filas": [
            {
                "fila_id": "fila1",
                "propuesta": {"objetivo_propuesto": anterior["objetivo"]},
                "fuentes_cientificas_ids": ["e1"],
            }
        ],
    }
    return tmp_path, p, archivo, parche, resultado


def test_reconstruye_cambio_y_conserva_el_resultado_anterior(expediente):
    base, p, archivo, parche, resultado = expediente
    raw = resultado.read_bytes()
    guardar_parche(base, archivo, parche)
    nuevo = preparar(base, p, archivo)
    assert validar(base, nuevo) == nuevo["borrador_inicial"]
    assert resultado.read_bytes() == raw
    assert nuevo["borrador_inicial"]["guiones"][0]["objetivo"] == p["filas"][0]["propuesta"]["objetivo_propuesto"]
    nuevo["borrador_inicial"]["guiones"][0]["titulo"] = "Contenido adulterado después de preparar el parche"
    with pytest.raises(ValueError, match="exactamente"):
        validar(base, nuevo)


@pytest.mark.parametrize("fallo", ["precondicion", "titulo", "objetivo", "resultado", "duplicado"])
def test_rechaza_cambios_inexactos_y_titulos_cosmeticos(expediente, fallo):
    base, p, archivo, parche, resultado = expediente
    campo = parche["cambios"][0]["campos"][0]
    if fallo == "precondicion":
        campo["anterior"] = "Texto que no corresponde al antecedente verdadero."
    elif fallo == "titulo":
        campo.update(campo="titulo", anterior=guion().titulo, nuevo="Título distinto con contenido idéntico")
    elif fallo == "objetivo":
        campo["campo"] = "objetivo"
    elif fallo == "resultado":
        resultado.write_bytes(resultado.read_bytes() + b" ")
    else:
        parche["cambios"][0]["campos"].append(deepcopy(campo))
    with pytest.raises(ValueError):
        guardar_parche(base, archivo, parche)
        preparar(base, p, archivo)


def test_no_sobrescribe_ediciones_ni_sale_del_directorio_autorizado(expediente):
    base, p, archivo, parche, _ = expediente
    guardar_parche(base, archivo, parche)
    with pytest.raises(FileExistsError):
        guardar_parche(base, archivo, parche)
    with pytest.raises(ValueError, match="editorial nuevo"):
        guardar_parche(base, base / "src/indebido.json", parche)
    fuera = base / "data/clases_v4/externo.json"
    fuera.write_text(json.dumps(parche))
    with pytest.raises(ValueError, match="expediente editorial"):
        preparar(base, p, archivo.parent / "../externo.json")


def test_una_ronda_explicita_valida_no_hereda_dictamenes_del_intento_fallido(expediente):
    base, p, archivo, parche, resultado = expediente
    original = guion().model_dump(mode="json")
    raw = serializar(
        {
            "snapshot_id": "s",
            "filas": {"fila1": {"guion": None}},
            "rondas": [
                {"numero": 1, "borrador": {"guiones": [original]}},
                {"numero": 2, "borrador": None, "respuesta_rechazada": "{JSON truncado"},
            ],
        }
    )
    resultado.write_bytes(raw)
    parche["cambios"][0].update(resultado_sha256=sha(raw), ronda_origen=1)
    guardar_parche(base, archivo, parche)
    nuevo = preparar(base, p, archivo)
    assert validar(base, nuevo) == nuevo["borrador_inicial"]
    assert resultado.read_bytes() == raw and "dictamenes" not in nuevo


@pytest.mark.parametrize("ronda", [1, 2])
def test_no_elige_ronda_si_hay_terminal_ni_recupera_json_truncado(expediente, ronda):
    base, p, archivo, parche, resultado = expediente
    d = json.loads(resultado.read_bytes())
    d["rondas"] = [{"numero": 2, "borrador": None, "respuesta_rechazada": "{truncado"}]
    if ronda == 2:
        d["filas"]["fila1"]["guion"] = None
    raw = serializar(d)
    resultado.write_bytes(raw)
    parche["cambios"][0].update(resultado_sha256=sha(raw), ronda_origen=ronda)
    guardar_parche(base, archivo, parche)
    with pytest.raises(ValueError, match="retrospectivamente|inequívoco"):
        preparar(base, p, archivo)


def test_edicion_salta_redaccion_y_exige_los_cuatro_lectores_de_su_contenido(expediente):
    from goes_science_kg.clases.contratos import ROLES
    from goes_science_kg.clases.motor import MotorClases
    from goes_science_kg.clases.validacion import huella_contenido
    from goes_science_kg.motor.ejecuciones import ejecutar_durable

    base, plantilla, archivo, parche, _ = expediente
    guardar_parche(base, archivo, parche)
    p = preparar(base, plantilla, archivo)
    assert huella_contenido(guion().model_dump(mode="json")) in p["huellas_vetadas"]["fila1"]
    proveedor = ProveedorGuion()
    corpus = SimpleNamespace(huella="a" * 64, raiz=base / "data/referencias_clases_2026", verificar=lambda e: None)
    r = ejecutar_durable(
        MotorClases(proveedor, corpus),
        archivo=base / "edicion.sqlite",
        solicitud=p,
        thread_id="edicion-explicita",
        ejecucion_id="prueba",
        huella_entorno="test-p9",
    )["resultado"]
    assert proveedor.redacciones == 0
    assert {rol for rol, _ in proveedor.llamadas} == set(ROLES) and len(proveedor.llamadas) == 4
    assert r["rondas"][0]["tipo"] == "edicion_editorial_importada"
    assert r["filas"]["fila1"]["guion"] == p["borrador_inicial"]["guiones"][0]
    assert r["filas"]["fila1"]["estado"] == "respaldado_automaticamente"
