"""Keep valid-shaped but misbound science output out of an authorized campaign cache."""

from __future__ import annotations

import copy
import sqlite3

import pytest
from test_campanas_vertex_presupuesto import _crear as _crear_presupuesto
from test_campanas_vertex_presupuesto import _reservar
from test_campanas_vertex_presupuesto import campana as campana
from test_campanas_vertex_proveedor import _cliente, _crear, _recibo
from test_campanas_vertex_proveedor import datos as datos
from test_clases import guion

from goes_science_kg.campanas_vertex.contratos import ESQUEMAS, canonico, esquema_transporte, sha256
from goes_science_kg.campanas_vertex.proveedor import SalidaNoUtilizable, preparar_solicitud


def _guion_fijado(datos):
    """Pin a synthetic science task independently of the provider's returned document."""
    datos.tipo = "guion_sucesor"
    datos.id = "guion:objetivo1"
    datos.contexto = {
        "fila_id": "fila1",
        "grado": 3,
        "objetivo_literal": guion().objetivo,
        "fuentes_citables": [{"id": "e1", "texto": "Synthetic evidence about observable properties."}],
    }
    datos.plan["componentes"] = [
        {"id": datos.id, "tipo": datos.tipo, "contexto_sha256": sha256(canonico(datos.contexto))}
    ]
    datos.plan["prompts_sha256"] = {datos.tipo: sha256(datos.sistema.encode())}
    datos.plan["esquemas_sha256"] = {
        datos.tipo: sha256(canonico(esquema_transporte(ESQUEMAS[datos.tipo]).model_json_schema()))
    }
    _recibo(datos.plan, datos.autorizacion)
    return guion().model_dump(mode="json")


@pytest.mark.parametrize("defecto", ["fila_ajena", "objetivo_cambiado", "fuente_inventada", "calculo_erroneo"])
def test_guion_valido_de_forma_pero_ajeno_o_incorrecto_no_se_cachea(datos, defecto):
    contenido = _guion_fijado(datos)
    if defecto == "fila_ajena":
        contenido["fila_id"] = "otra_fila"
    elif defecto == "objetivo_cambiado":
        contenido["objetivo"] = "Describir otro objetivo curricular que no fue solicitado."
    elif defecto == "fuente_inventada":
        contenido["explicacion_docente"][0]["fuentes_ids"] = ["fuente_no_enviada"]
    else:
        contenido["tareas"][0]["calculos"] = [{"expresion": "2+2", "resultado": 5, "unidad": "objetos"}]
    # These defects pass the shape contract, so rejection must bind output to pinned context and arithmetic.
    assert ESQUEMAS[datos.tipo].model_validate(copy.deepcopy(contenido))
    cliente, llamadas = _cliente(texto=canonico(contenido).decode())
    proveedor = _crear(datos, cliente)
    with pytest.raises(SalidaNoUtilizable):
        proveedor.generar(datos.id, contexto=datos.contexto, sistema=datos.sistema)
    solicitud = preparar_solicitud(datos.plan, datos.id, contexto=datos.contexto, sistema=datos.sistema)
    assert proveedor.presupuesto.cache(solicitud["clave"]) is None
    assert proveedor.presupuesto.salida(solicitud["clave"]) == canonico(contenido).decode()
    assert datos.registro.resumen(datos.plan["campana_id"])["detalle"][0]["estado"] == "fallida"
    assert len(llamadas) == 1


def test_guion_coherente_con_contexto_se_recupera_sin_volver_a_llamar(datos):
    contenido = _guion_fijado(datos)
    cliente, llamadas = _cliente(texto=canonico(contenido).decode())
    proveedor = _crear(datos, cliente)
    for _ in range(2):
        recibido = proveedor.generar(datos.id, contexto=datos.contexto, sistema=datos.sistema)
        assert recibido.fila_id == datos.contexto["fila_id"]
        assert recibido.objetivo == datos.contexto["objetivo_literal"]
    assert len(llamadas) == 1


def test_restaurar_solo_sqlite_no_devuelve_plazas_consumidas(campana):
    """A valid old campaign baseline must not hide rollback of the new campaign's consumed calls."""
    nueva = _crear_presupuesto(campana)
    archivo = campana[3]
    copia = sqlite3.connect(":memory:")
    try:
        with sqlite3.connect(archivo) as db:
            db.backup(copia)
        for ronda in (0, 1):
            llamada = _reservar(nueva, ronda)
            nueva.terminar(llamada, estado="fallida", latencia_ms=1)
        assert nueva.registro.resumen(nueva.ejecucion_id)["llamadas"] == 2
        with sqlite3.connect(archivo) as db:
            copia.backup(db)
        # Restoring this snapshot preserves the old campaign and the new authorization registration.
        assert nueva.registro.resumen("historica")["llamadas"] == 1
        with pytest.raises(ValueError):
            _crear_presupuesto(campana)
    finally:
        copia.close()


@pytest.mark.parametrize("reservas_previas", [0, 1])
def test_perdida_del_punto_externo_no_reinicia_campana(campana, reservas_previas):
    """Missing external evidence must fail closed even when the SQL authorization still exists."""
    nueva = _crear_presupuesto(campana)
    if reservas_previas:
        _reservar(nueva)
    nueva.continuidad.archivo.unlink()
    with pytest.raises(ValueError):
        _crear_presupuesto(campana)
    with pytest.raises(ValueError):
        _reservar(nueva, reservas_previas)
    assert nueva.registro.resumen(nueva.ejecucion_id)["llamadas"] == reservas_previas


def test_continuidad_externa_no_sigue_symlink_del_directorio(campana, tmp_path):
    """Resolve must not erase evidence of a redirected journal parent before checking it."""
    destino_externo = tmp_path / "journal_externo"
    destino_externo.mkdir()
    enlace = tmp_path / "data/operaciones/campanas_vertex"
    enlace.symlink_to(destino_externo, target_is_directory=True)
    with pytest.raises(ValueError):
        _crear_presupuesto(campana)
    assert not list(destino_externo.iterdir())
