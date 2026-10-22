"""La migración preserva el corpus y no retira datos cambiados o sin recibo coincidente."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest
from typer.testing import CliRunner

from goes_science_kg.cli.datos import app
from goes_science_kg.operacion import datos_externos as datos


def preparar(tmp_path):
    raiz = tmp_path / "repo"
    (raiz / "data").mkdir(parents=True)
    (raiz / "data/fuente.pdf").write_bytes(b"%PDF-original")
    (raiz / "data/cache.npz").write_bytes(b"matriz-binaria")
    (raiz / ".env").write_text("SECRETO=no-se-respalda")
    (raiz / "src").mkdir()
    (raiz / "src/codigo.py").write_text("pass")
    (raiz / "reportes/referencia").mkdir(parents=True)
    (raiz / "reportes/referencia/fuentes").symlink_to("../../data")
    cfg = {"rutas": ["data", "reportes/referencia"]}
    archivo = tmp_path / "paquete.zip"
    plan = datos.preparar(raiz, cfg, archivo)
    recibo = {
        "version": datos.VERSION,
        "paquete": {"sha256": plan["paquete_local"]["sha256"]},
        "huella_inventario": plan["paquete_local"]["huella_inventario"],
        "montajes": plan["montajes"],
        "enlaces": plan["enlaces"],
    }
    return raiz, cfg, archivo, plan, recibo


def test_corpus_binario_enlaces_y_recuperacion_sin_credenciales(tmp_path):
    raiz, cfg, archivo, plan, recibo = preparar(tmp_path)
    restaurado = tmp_path / "restaurado"
    resultado = datos.restaurar(archivo, restaurado, recibo)
    assert resultado["archivos_restaurados"] == 2
    assert not (restaurado / ".env").exists() and not (restaurado / "src").exists()
    assert (restaurado / "reportes/referencia/fuentes/fuente.pdf").read_bytes() == b"%PDF-original"
    datos.retirar(raiz, plan, recibo, cfg)
    assert not (raiz / "data").exists()
    assert (raiz / ".env").exists() and (raiz / "src/codigo.py").exists()
    datos.incorporar(restaurado, raiz, recibo["montajes"])
    assert (raiz / "data/cache.npz").read_bytes() == b"matriz-binaria"
    assert (raiz / "reportes/referencia/fuentes/fuente.pdf").read_bytes() == b"%PDF-original"


@pytest.mark.parametrize("cambio", ["editar", "agregar", "nuevo_montaje", "wal", "recibo"])
def test_no_retira_ningun_original_si_cambio_despues_de_subir(tmp_path, cambio):
    raiz, cfg, _, plan, recibo = preparar(tmp_path)
    if cambio == "editar":
        (raiz / "data/fuente.pdf").write_bytes(b"contenido nuevo")
    elif cambio == "agregar":
        (raiz / "data/nuevo.json").write_text("{}")
    elif cambio == "nuevo_montaje":
        (raiz / "resultados").mkdir()
        cfg["rutas"].append("resultados")
    elif cambio == "wal":
        (raiz / "data/db.sqlite-wal").write_bytes(b"transaccion nueva")
    else:
        recibo["paquete"]["sha256"] = "0" * 64
    with pytest.raises(ValueError):
        datos.retirar(raiz, plan, recibo, cfg)
    assert (raiz / "data/fuente.pdf").exists()


def test_enlace_fuera_del_corpus_no_se_respalda(tmp_path):
    raiz, cfg, _, _, _ = preparar(tmp_path)
    (raiz / "data/credencial").symlink_to("../.env")
    with pytest.raises(ValueError, match="no incluidos"):
        datos.inventariar(raiz, cfg["rutas"])


def test_restauracion_hostil_o_sha_falso_no_habilitan_datos(tmp_path):
    _, _, archivo, _, recibo = preparar(tmp_path)
    recibo["enlaces"] = {"reportes/referencia/fuentes": "../../../fuera"}
    destino = tmp_path / "restaurado"
    with pytest.raises(ValueError, match="sale del destino"):
        datos.restaurar(archivo, destino, recibo)
    assert not destino.exists()
    recibo["enlaces"] = {}
    recibo["paquete"]["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="SHA"):
        datos.restaurar(archivo, destino, recibo)
    assert not destino.exists()


def test_incorporar_no_sobreescribe_ni_sigue_padres_simbolicos(tmp_path):
    raiz, _, archivo, _, recibo = preparar(tmp_path)
    restaurado = tmp_path / "restaurado"
    datos.restaurar(archivo, restaurado, recibo)
    with pytest.raises(ValueError, match="Ya existe"):
        datos.incorporar(restaurado, raiz, recibo["montajes"])
    nuevo = tmp_path / "nuevo"
    nuevo.mkdir()
    (nuevo / "reportes").symlink_to(raiz / "reportes")
    with pytest.raises(ValueError):
        datos.incorporar(restaurado, nuevo, recibo["montajes"])
    assert not (nuevo / "data").exists()


def test_sqlite_respalda_transacciones_del_wal_y_excluye_locks(tmp_path):
    raiz = tmp_path / "repo"
    (raiz / "data").mkdir(parents=True)
    con = sqlite3.connect(raiz / "data/registro.sqlite")
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("CREATE TABLE reservas (usd REAL)")
    con.execute("INSERT INTO reservas VALUES (1.25)")
    con.commit()
    (raiz / "data/.registro.lock").touch()
    archivo = tmp_path / "datos.zip"
    plan = datos.preparar(raiz, {"rutas": ["data"]}, archivo)
    assert set(plan["originales"]) == {"data/registro.sqlite"}
    from goes_science_kg.operacion.respaldo import restaurar_paquete

    restaurar_paquete(archivo, tmp_path / "restaurado", sha256=plan["paquete_local"]["sha256"])
    with sqlite3.connect(tmp_path / "restaurado/data/registro.sqlite") as restaurada:
        assert restaurada.execute("SELECT usd FROM reservas").fetchall() == [(1.25,)]
    con.close()


def test_cli_exige_destino_unico_antes_de_cualquier_red(tmp_path):
    for args in (["restaurar"], ["restaurar", "--en-repo", "--destino", str(tmp_path)]):
        r = CliRunner().invoke(app, args)
        assert r.exit_code == 2
        assert "Indique" in r.output


def test_plan_rechaza_credenciales_en_una_raiz_de_datos(tmp_path):
    raiz, cfg, _, _, _ = preparar(tmp_path)
    (raiz / "data/.env").write_text("secret")
    with pytest.raises(ValueError, match="no autorizada"):
        datos.preparar(raiz, cfg, tmp_path / "otro.zip")


def test_manifest_y_recibo_deben_corresponder(tmp_path):
    _, _, archivo, _, recibo = preparar(tmp_path)
    recibo = json.loads(json.dumps(recibo))
    recibo["huella_inventario"] = "0" * 64
    with pytest.raises(ValueError, match="inventario"):
        datos.restaurar(archivo, tmp_path / "otro", recibo)


def test_presupuestos_restaurados_conservan_reservas_y_solo_migran_el_vinculo(tmp_path):
    from goes_science_kg.motor.ejecuciones import _vincular_presupuesto
    from goes_science_kg.motor.registro import PresupuestoAgotado, Registro
    from goes_science_kg.operacion.presupuestos_restaurados import migrar_presupuestos

    original = tmp_path / "original"
    registro = Registro(original / datos.LEDGER)
    llamada = registro.reservar(
        ejecucion="campana-original",
        clave="k",
        modelo="m",
        rol="r",
        reserva_usd=1.25,
        max_llamadas=1,
        max_usd=2,
    )
    registro.guardar_salida(llamada, "respuesta que se conserva")
    identidad = datos.identidad_ledger(registro.archivo)
    with sqlite3.connect(original / "data/operaciones/checkpoints.sqlite") as db:
        _vincular_presupuesto(db, "campana-original", json.dumps(identidad, sort_keys=True))
    archivo = tmp_path / "datos.zip"
    plan = datos.preparar(original, {"rutas": ["data"]}, archivo)
    recibo = {
        "version": datos.VERSION,
        "paquete": {"sha256": plan["paquete_local"]["sha256"]},
        "huella_inventario": plan["paquete_local"]["huella_inventario"],
        "montajes": ["data"],
        "enlaces": {},
        "identidad_ledger": identidad,
    }
    destino = tmp_path / "restaurado"
    restauracion = datos.restaurar(archivo, destino, recibo)
    # Una base modificada o una identidad ajena no habilitan la reanudación.
    falsa = {**recibo, "identidad_ledger": {**identidad, "inodo": -1}}
    with pytest.raises(ValueError, match="original"):
        migrar_presupuestos(destino, falsa, restauracion["sqlite_verificados"])
    ledger_sha = datos.digest(destino / datos.LEDGER)
    migracion = migrar_presupuestos(destino, recibo, restauracion["sqlite_verificados"])
    assert migracion["vinculos_actualizados"] == 1
    assert datos.digest(destino / datos.LEDGER) == ledger_sha
    with sqlite3.connect(destino / "data/operaciones/checkpoints.sqlite") as db:
        _vincular_presupuesto(
            db, "campana-original", json.dumps(datos.identidad_ledger(destino / datos.LEDGER), sort_keys=True)
        )
    restaurado = Registro(destino / datos.LEDGER)
    assert restaurado.salida("k") == "respuesta que se conserva"
    with pytest.raises(PresupuestoAgotado):
        restaurado.reservar(
            ejecucion="campana-original",
            clave="otra",
            modelo="m",
            rol="r",
            reserva_usd=0.1,
            max_llamadas=1,
            max_usd=2,
        )
    assert json.loads(Path(migracion["auditoria"]).read_bytes())["estado"] == "completado"
    with pytest.raises(ValueError, match="SQLite cambió"):
        migrar_presupuestos(destino, recibo, restauracion["sqlite_verificados"])


def _restaurar_muchos_checkpoints(tmp_path, cantidad=20):
    from contextlib import closing

    from goes_science_kg.motor.ejecuciones import _vincular_presupuesto
    from goes_science_kg.motor.registro import Registro

    origen = tmp_path / "origen"
    registro = Registro(origen / datos.LEDGER)
    registro.reservar(ejecucion="prueba", clave="k", modelo="m", rol="r", reserva_usd=1, max_llamadas=1, max_usd=2)
    identidad = datos.identidad_ledger(registro.archivo)
    for i in range(cantidad):
        with closing(sqlite3.connect(origen / f"data/operaciones/cp_{i:02d}.sqlite")) as db:
            _vincular_presupuesto(db, "prueba", json.dumps(identidad, sort_keys=True))
            db.execute("CREATE TABLE estados (id INTEGER PRIMARY KEY, contenido TEXT)")
            db.execute("INSERT INTO estados VALUES (1,'estado del grafo que no se modifica')")
            db.commit()
    archivo = tmp_path / "muchas_bases.zip"
    plan = datos.preparar(origen, {"rutas": ["data"]}, archivo)
    recibo = {
        "version": datos.VERSION,
        "paquete": {"sha256": plan["paquete_local"]["sha256"]},
        "huella_inventario": plan["paquete_local"]["huella_inventario"],
        "montajes": ["data"],
        "enlaces": {},
        "identidad_ledger": identidad,
    }
    destino = tmp_path / "restaurado"
    restaurado = datos.restaurar(archivo, destino, recibo)
    return destino, recibo, restaurado["sqlite_verificados"]


def test_migra_veinte_bases_sin_reiniciar_presupuesto_ni_cambiar_estados(tmp_path):
    from contextlib import closing

    from goes_science_kg.motor.registro import PresupuestoAgotado, Registro
    from goes_science_kg.operacion.presupuestos_restaurados import migrar_presupuestos

    base, recibo, sqlites = _restaurar_muchos_checkpoints(tmp_path)
    assert migrar_presupuestos(base, recibo, sqlites)["vinculos_actualizados"] == 20
    assert datos.digest(base / datos.LEDGER) == sqlites[datos.LEDGER]
    for archivo in (base / "data/operaciones").glob("cp_*.sqlite"):
        with closing(sqlite3.connect(archivo)) as db:
            assert db.execute("SELECT contenido FROM estados").fetchone()[0] == "estado del grafo que no se modifica"
            assert json.loads(
                db.execute("SELECT ledger FROM checkpoint_presupuestos").fetchone()[0]
            ) == datos.identidad_ledger(base / datos.LEDGER)
    registro = Registro(base / datos.LEDGER)
    with pytest.raises(PresupuestoAgotado):
        registro.reservar(
            ejecucion="prueba", clave="otra", modelo="m", rol="r", reserva_usd=1, max_llamadas=1, max_usd=2
        )


@pytest.mark.parametrize("fallo", [OSError, KeyboardInterrupt])
def test_migracion_fallida_revierte_todos_los_bytes_sin_tocar_ledger(tmp_path, fallo):
    import os

    from goes_science_kg.operacion.presupuestos_restaurados import migrar_presupuestos

    base, recibo, sqlites = _restaurar_muchos_checkpoints(tmp_path, cantidad=3)

    def sustituir(origen, destino):
        if Path(origen).name == "actualizado.sqlite" and Path(destino).name == "cp_01.sqlite":
            raise fallo("Fallo controlado de instalación")
        return os.replace(origen, destino)

    with pytest.raises(fallo):
        migrar_presupuestos(base, recibo, sqlites, sustituir=sustituir)
    assert all(datos.digest(base / p) == sha for p, sha in sqlites.items())
    assert (
        json.loads(next((base / "data/operaciones/migraciones").glob("restauracion-*.json")).read_bytes())["estado"]
        == "revertido"
    )
    assert migrar_presupuestos(base, recibo, sqlites)["vinculos_actualizados"] == 3


@pytest.mark.parametrize("valor", [True, 0, 2**34, "8589934592"])
def test_limite_de_corpus_explicito_y_acotado(valor):
    with pytest.raises(ValueError, match="2 y 8"):
        datos.limite_bytes(valor)
