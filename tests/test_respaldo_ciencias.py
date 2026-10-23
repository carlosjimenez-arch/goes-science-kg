"""Respaldo inmutable, protección efectiva y restauración hostil; sin GCP."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import zipfile
from pathlib import Path

import pytest

from goes_science_kg.operacion.almacen_gcs import AlmacenGCS, ConfiguracionAlmacen
from goes_science_kg.operacion.respaldo import crear_paquete, nombre_seguro, restaurar_paquete


class GCloudSimulado:
    def __init__(self, *, pap="inherited", enforced=True, ubla=True, proyecto="1234", cuenta=None):
        self.pap, self.enforced, self.ubla, self.proyecto = pap, enforced, ubla, proyecto
        self.cuenta = cuenta or "carlos.jimenez@goes.gob.sv"
        self.objetos, self.llamadas, self.creaciones = {}, [], 0
        self.corromper = False

    def ejecutar(self, args):
        self.llamadas.append(args)
        if args[:3] == ["config", "get-value", "account"]:
            return self.cuenta
        if args[:2] == ["projects", "describe"]:
            return json.dumps({"projectId": "proyecto-ciencias", "projectNumber": "1234"})
        if args[:3] == ["storage", "buckets", "describe"]:
            return json.dumps(
                {
                    "name": "bucket-ciencias",
                    "projectNumber": self.proyecto,
                    "iamConfiguration": {
                        "publicAccessPrevention": self.pap,
                        "uniformBucketLevelAccess": {"enabled": self.ubla},
                    },
                }
            )
        if args[:2] == ["resource-manager", "org-policies"]:
            return json.dumps(
                {
                    "constraint": "constraints/storage.publicAccessPrevention",
                    "booleanPolicy": {"enforced": self.enforced},
                }
            )
        if args[:3] == ["storage", "objects", "describe"]:
            data = self.objetos[args[3]]
            return json.dumps(
                {"generation": "123", "size": str(len(data)), "metadata": {"sha256": hashlib.sha256(data).hexdigest()}}
            )
        if args[:2] == ["storage", "cp"]:
            if args[2].startswith("gs://"):
                assert args[2].endswith("#123")
                contenido = self.objetos[args[2].removesuffix("#123")]
                Path(args[3]).write_bytes(contenido + (b"cambio" if self.corromper else b""))
            else:
                assert "--if-generation-match=0" in args and args[3] not in self.objetos
                self.creaciones += 1
                self.objetos[args[3]] = Path(args[2]).read_bytes()
            return ""
        raise AssertionError(args)


def almacen(cli):
    return AlmacenGCS(
        ConfiguracionAlmacen(
            proyecto="proyecto-ciencias",
            bucket="bucket-ciencias",
            prefijo="ciencias/v4",
            cuenta="carlos.jimenez@goes.gob.sv",
        ),
        cli=cli,
    )


def test_crear_verifica_politica_actual_y_relee_cada_generacion(tmp_path):
    cli = GCloudSimulado()
    a = almacen(cli)
    p = tmp_path / "uno.zip"
    p.write_bytes(b"datos privados de prueba")
    for i in range(2):
        r = a.crear(p, f"objetos/{i}.zip")
        assert r["generacion"] == "123" and r["sha256"] == hashlib.sha256(p.read_bytes()).hexdigest()
    assert sum(x[:2] == ["resource-manager", "org-policies"] for x in cli.llamadas) == 2
    cli.enforced = False
    with pytest.raises(ValueError, match="efectiva"):
        a.crear(p, "otro.zip")
    assert cli.creaciones == 2


@pytest.mark.parametrize(
    "opciones",
    [
        {"pap": "inherited", "enforced": False},
        {"pap": "desconocido"},
        {"ubla": False},
        {"proyecto": "9999"},
        {"proyecto": None},
        {"cuenta": "otra@goes.gob.sv"},
    ],
)
def test_proteccion_identidad_y_proyecto_son_previos_a_escritura(tmp_path, opciones):
    cli = GCloudSimulado(**opciones)
    p = tmp_path / "prueba.zip"
    p.write_bytes(b"prueba")
    with pytest.raises(ValueError):
        almacen(cli).crear(p, "objetos/prueba.zip")
    assert cli.creaciones == 0


def test_corrupcion_de_generacion_releida_impide_emitir_respaldo(tmp_path):
    cli = GCloudSimulado()
    cli.corromper = True
    p = tmp_path / "prueba.zip"
    p.write_bytes(b"prueba")
    with pytest.raises(ValueError, match="bytes releídos"):
        almacen(cli).crear(p, "prueba.zip")


def test_objeto_que_no_puede_releerse_se_rechaza_antes_de_subir(tmp_path, monkeypatch):
    cli = GCloudSimulado()
    p = tmp_path / "grande.zip"
    p.write_bytes(b"tamanio simulado sin reservar un GiB en disco")
    monkeypatch.setattr(
        "goes_science_kg.operacion.almacen_gcs._medir", lambda _: ("a" * 64, 1024**3 + 1)
    )
    with pytest.raises(ValueError, match="límite de objeto"):
        almacen(cli).crear(p, "repositorio/objetos/grande.zip")
    assert not cli.llamadas


def test_corpus_mayor_de_un_gib_requiere_cota_explicita_y_sigue_fijando_generacion(tmp_path, monkeypatch):
    cli = GCloudSimulado()
    a = almacen(cli)
    uri = a.configuracion.ruta("repositorio/objetos/grande.zip")
    cli.objetos[uri] = b"contenido simulado; la medida logica evita un archivo gigante en el test"
    tamano = 1024**3 + 1
    monkeypatch.setattr("goes_science_kg.operacion.almacen_gcs._medir", lambda _: ("a" * 64, tamano))
    with pytest.raises(ValueError, match="límite de objeto"):
        a.verificar(uri, "123", "a" * 64, tamano)
    assert not cli.llamadas
    ampliado = AlmacenGCS(a.configuracion, cli=cli, max_bytes_objeto=8 * 1024**3)
    ampliado.verificar(uri, "123", "a" * 64, tamano, destino=tmp_path / "copia.zip")
    assert cli.llamadas == [["storage", "cp", uri + "#123", cli.llamadas[0][3]]]
    with pytest.raises(ValueError, match="límite de objeto"):
        ampliado.verificar(uri, "123", "a" * 64, 8 * 1024**3 + 1)
    assert len(cli.llamadas) == 1


@pytest.mark.parametrize("limite", [0, True, 8 * 1024**3 + 1])
def test_la_cota_de_objeto_no_admite_descargas_sin_limite(limite):
    with pytest.raises(ValueError, match="hasta 8 GiB"):
        AlmacenGCS(almacen(GCloudSimulado()).configuracion, max_bytes_objeto=limite)


@pytest.mark.parametrize("ruta", ["../otro", "/absoluto", "x/.env", "x/.git/config", "x/../y", "x\\y"])
def test_archivo_hostil_rechazado(ruta):
    with pytest.raises(ValueError):
        nombre_seguro(ruta)


def test_sqlite_wal_se_respalda_consistente_y_no_se_pierde_reserva(tmp_path):
    raiz = tmp_path / "original"
    raiz.mkdir()
    db = raiz / "registro.sqlite"
    con = sqlite3.connect(db)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("CREATE TABLE llamadas (id TEXT, reserva REAL)")
    con.execute("INSERT INTO llamadas VALUES ('sin-reiniciar', 1.25)")
    con.commit()
    (raiz / "curriculo.json").write_text('{"filas": 2}')
    archivo = tmp_path / "paquete.zip"
    plan = crear_paquete(raiz, ["registro.sqlite", "curriculo.json"], archivo)
    destino = tmp_path / "restaurado"
    r = restaurar_paquete(archivo, destino, sha256=plan["sha256"])
    assert r["archivos_restaurados"] == 2
    with sqlite3.connect(destino / "registro.sqlite") as restaurada:
        assert restaurada.execute("SELECT * FROM llamadas").fetchall() == [("sin-reiniciar", 1.25)]
    con.close()
    with pytest.raises(ValueError, match="vacío"):
        restaurar_paquete(archivo, destino, sha256=plan["sha256"])


def test_no_reemplaza_paquete_ni_acepta_sha_falso(tmp_path):
    (tmp_path / "dato.txt").write_text("dato")
    p = tmp_path / "paquete.zip"
    crear_paquete(tmp_path, ["dato.txt"], p)
    with pytest.raises(ValueError, match="nuevo"):
        crear_paquete(tmp_path, ["dato.txt"], p)
    with pytest.raises(ValueError, match="SHA"):
        restaurar_paquete(p, tmp_path / "destino", sha256="0" * 64)


def test_zip_con_miembro_no_declarado_no_escribe_nada(tmp_path):
    (tmp_path / "dato.txt").write_text("dato")
    p = tmp_path / "paquete.zip"
    crear_paquete(tmp_path, ["dato.txt"], p)
    with zipfile.ZipFile(p, "a") as z:
        z.writestr("../escapar.txt", "no")
    with pytest.raises(ValueError, match="no declarados"):
        restaurar_paquete(p, tmp_path / "destino", sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    assert not (tmp_path / "destino").exists() and not (tmp_path / "escapar.txt").exists()
