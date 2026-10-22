"""Componer cohortes con protocolos distintos preserva fuentes, vetos y huellas originales."""

from __future__ import annotations

import pytest
from test_juicios_conocimiento import LectoresSimulados
from test_producto_v4 import catalogo as catalogo
from test_producto_v4 import curriculo as curriculo
from test_publicacion_conocimiento import preparado as preparado
from test_relaciones_v4 import red

from goes_science_kg.motor.conocimiento import MotorConocimiento
from goes_science_kg.motor.contratos import huella
from goes_science_kg.producto import cargar_producto, construir_producto
from goes_science_kg.producto._juicios_contratos import SolicitudConocimiento
from goes_science_kg.producto.composicion import componer_archivos
from goes_science_kg.producto.conocimiento_publicado import (
    ArchivoConocimiento,
    crear_archivo_conocimiento,
    validar_archivo_conocimiento,
)
from goes_science_kg.producto.juicios import PreparadorConocimiento


@pytest.fixture(scope="module")
def componentes(preparado):
    a = crear_archivo_conocimiento(preparado.motor, [preparado.estados[0]])
    p = preparado.motor.preparador
    nuevo = PreparadorConocimiento(
        p.curriculo,
        p.informe,
        p.referencias,
        p.fuentes,
        soportes=p.soportes,
        max_caracteres=30000,
    )
    motor = MotorConocimiento(nuevo, LectoresSimulados({"juez_ciencia": {"fuentes_implican_relacion": "no"}}))
    s = SolicitudConocimiento(candidato_id=preparado.candidatos[1].id)
    estado = motor.compilar().invoke({"solicitud": s.model_dump(), "ejecucion_id": "sintetica-otra-cohorte"})
    b = crear_archivo_conocimiento(motor, [estado])
    return a, b


def test_union_conserva_rechazo_y_protocolos_distintos(preparado, componentes):
    a = componer_archivos(componentes, preparado.curriculo, catalogo=preparado.catalogo)
    assert a.version == "conocimiento-publicado-2"
    assert {c.huella_archivo for c in a.componentes} == {c.huella_archivo for c in componentes}
    assert len(a.coleccion.resultados) == 2 and len(a.coleccion.relaciones_admisibles) == 1
    assert {r.estado for r in a.coleccion.resultados} == {"respaldado", "no_respaldado"}
    assert len({r.huella_motor for r in a.coleccion.resultados}) == 2
    assert a == componer_archivos(tuple(reversed(componentes)), preparado.curriculo, catalogo=preparado.catalogo)


def test_duplicar_ronda_no_permite_seleccionar_respaldo(preparado, componentes):
    with pytest.raises(ValueError, match="repetido"):
        componer_archivos([componentes[0], componentes[0]], preparado.curriculo)


@pytest.mark.parametrize("cambio", ["omitir_rechazo", "motor", "componente"])
def test_recalcular_hash_no_oculta_alteraciones_de_la_union(preparado, componentes, cambio):
    a = componer_archivos(componentes, preparado.curriculo)
    d = a.model_dump(mode="json")
    if cambio == "omitir_rechazo":
        d["coleccion"]["resultados"] = [r for r in d["coleccion"]["resultados"] if r["estado"] == "respaldado"]
    elif cambio == "motor":
        d["coleccion"]["resultados"][0]["huella_motor"] = "a" * 64
    else:
        d["componentes"][0]["coleccion"]["resultados"][0]["estado"] = "abstencion"
    d["huella_archivo"] = huella({k: v for k, v in d.items() if k != "huella_archivo"})
    with pytest.raises(ValueError):
        validar_archivo_conocimiento(ArchivoConocimiento.model_validate(d), preparado.curriculo)


def test_publicacion_de_union_se_relee_con_mismos_juicios(preparado, componentes, tmp_path):
    a = componer_archivos(componentes, preparado.curriculo, catalogo=preparado.catalogo)
    construir_producto(
        preparado.curriculo,
        preparado.catalogo,
        destino=tmp_path / "producto",
        conocimiento=a,
        modelos_conocimiento=a.modelos,
        raiz_historica=preparado.base,
    )
    p = cargar_producto(tmp_path / "producto")
    assert p.conocimiento == a
    assert p.diagnostico["conocimiento"]["filas_con_juicio"] == 2


def test_ciclo_entre_componentes_bloquea_todos_sin_descartar_juicios(tmp_path):
    motor, estados = red(tmp_path, ciclo=True)
    partes = [crear_archivo_conocimiento(motor, [e]) for e in estados]
    assert all(p.coleccion.proyeccion_dependencias.estado == "aciclica" for p in partes)
    conjunto = componer_archivos(partes, motor.preparador.curriculo)
    assert conjunto.coleccion.proyeccion_dependencias.estado == "bloqueada_por_ciclos"
    assert len(conjunto.coleccion.relaciones_respaldadas) == 3
    assert conjunto.coleccion.relaciones_admisibles == ()
