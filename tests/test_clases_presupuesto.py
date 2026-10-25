"""Una restauración no puede borrar consumo posterior al primer presupuesto."""

from __future__ import annotations

import json

import pytest

from goes_science_kg.clases.presupuesto import comprobar_continuidad, fijar_punto
from goes_science_kg.materiales.compilacion import serializar, sha
from goes_science_kg.motor.registro import Registro


@pytest.fixture
def consumo(tmp_path, monkeypatch):
    monkeypatch.setenv("GSKG_RAIZ", str(tmp_path))
    registro = Registro(tmp_path / "registro.sqlite")

    def llamada():
        id_ = registro.reservar(
            ejecucion="prueba",
            clave="k",
            modelo="m",
            rol="r",
            reserva_usd=0.1,
            max_llamadas=10,
            max_usd=10,
        )
        registro.terminar(id_, estado="completa", latencia_ms=1)
        return id_

    primero = llamada()
    with registro.conexion() as db:
        db.execute("UPDATE llamadas SET creada='2020-01-01' WHERE id=?", (primero,))
        baseline = [dict(r) for r in db.execute("SELECT * FROM llamadas ORDER BY creada,id")]
    cfg = {"ejecucion": "prueba", "baseline": {"llamadas": 1, "filas_sha256": sha(serializar(baseline))}}
    segundo = llamada()
    punto = tmp_path / "data/continuidad.json"
    datos = fijar_punto(registro.archivo, punto, cfg=cfg)
    cfg["punto_continuidad"] = {"ruta": "data/continuidad.json", **datos}
    return registro, cfg, segundo, llamada, punto


@pytest.mark.parametrize("alteracion", ["borrar", "reserva", "estado"])
def test_rechaza_perder_o_alterar_consumo_nuevo_aunque_baseline_siga_intacto(consumo, alteracion):
    registro, cfg, segundo, _, _ = consumo
    assert comprobar_continuidad(registro.archivo, cfg)["llamadas"] == 2
    with registro.conexion() as db:
        if alteracion == "borrar":
            db.execute("DELETE FROM llamadas WHERE id=?", (segundo,))
        elif alteracion == "reserva":
            db.execute("UPDATE llamadas SET reserva_usd=0.01 WHERE id=?", (segundo,))
        else:
            db.execute("UPDATE llamadas SET estado='fallida' WHERE id=?", (segundo,))
    with pytest.raises(ValueError, match="retrocede o altera"):
        comprobar_continuidad(registro.archivo, cfg)


def test_nuevas_llamadas_con_misma_fecha_no_invalidan_consumo_conocido(consumo):
    registro, cfg, segundo, llamada, _ = consumo
    tercero = llamada()
    with registro.conexion() as db:
        fecha = db.execute("SELECT creada FROM llamadas WHERE id=?", (segundo,)).fetchone()[0]
        db.execute("UPDATE llamadas SET creada=? WHERE id=?", (fecha, tercero))
    assert comprobar_continuidad(registro.archivo, cfg)["llamadas"] == 3


def test_rechaza_punto_alterado_o_ausente(consumo):
    registro, cfg, _, _, punto = consumo
    contenido = json.loads(punto.read_bytes())
    contenido["llamadas"] = 1
    punto.write_bytes(serializar(contenido))
    with pytest.raises(ValueError, match="punto de continuidad.*cambió"):
        comprobar_continuidad(registro.archivo, cfg)
    punto.unlink()
    with pytest.raises(ValueError, match="Falta el punto"):
        comprobar_continuidad(registro.archivo, cfg)


def test_no_fija_llamadas_pendientes_ni_sobrescribe_punto(consumo, tmp_path):
    registro, cfg, segundo, _, punto = consumo
    with pytest.raises(FileExistsError):
        fijar_punto(registro.archivo, punto, cfg=cfg)
    with registro.conexion() as db:
        db.execute("UPDATE llamadas SET estado='reservada' WHERE id=?", (segundo,))
    # La llamada pendiente se creó después del punto: no se altera ninguna fila congelada.
    cfg.pop("punto_continuidad")
    with pytest.raises(ValueError, match="pendientes"):
        fijar_punto(registro.archivo, tmp_path / "nuevo.json", cfg=cfg)
    assert not (tmp_path / "nuevo.json").exists()
