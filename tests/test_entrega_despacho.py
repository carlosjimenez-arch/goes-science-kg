"""Block unsafe releases and verify that Desktop copies retain the exact reviewed package."""

from __future__ import annotations

import json
import shutil
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest
from test_entrega_didactica import base_sintetica as base_sintetica
from test_entrega_didactica import correccion_sintetica as correccion_sintetica
from test_entrega_didactica import recorrido as recorrido

from goes_science_kg.entrega.compilacion import compilar, digest, validar
from goes_science_kg.entrega.despacho import _contar_pruebas, _huella_codigo, despachar, verificar_despacho
from goes_science_kg.materiales.compilacion import serializar, sha


@pytest.fixture
def despacho_listo(base_sintetica, correccion_sintetica, monkeypatch):
    raiz, base, _ = base_sintetica
    ciencias, datos = correccion_sintetica
    revisiones = raiz / "revisiones"
    revisiones.mkdir()
    (revisiones / "revision.json").write_bytes(
        serializar(
            {
                "estado": "favorable_en_alcance_documental",
                "archivos": [
                    {
                        "id": datos["id"],
                        "sha256": digest(ciencias / "paquete.json"),
                        "estado": "favorable_en_alcance_documental",
                        "hallazgos_abiertos": [],
                    }
                ],
            }
        )
    )
    edicion, archivo_zip = raiz / "edicion", raiz / "paquetes.zip"
    manifest = compilar(raiz, base, edicion, ciencias=ciencias, revisiones=revisiones, archivo_zip=archivo_zip)
    auditoria = raiz / "auditoria.json"
    auditoria.write_bytes(
        serializar(
            {
                "estado": "aprobado",
                "errores": [],
                "manifest_id": manifest["id"],
                "zip_sha256": digest(archivo_zip),
                "zip_bytes": archivo_zip.stat().st_size,
                "denominadores": manifest["resumen"],
                "archivos_zip_y_carpeta": len(manifest["archivos"]) + 1,
                "json_revisados": [datos["id"]],
                "comprobaciones": {
                    "json_revisados_sha_verificados": 1,
                    "entradas_zip_sha_verificadas": len(manifest["archivos"]) + 1,
                    "archivos_carpeta_sha_verificados": len(manifest["archivos"]),
                },
            }
        )
    )
    # The official fingerprint function is used, with a tiny synthetic repository.
    script = Path(__file__).resolve().parents[1] / "scripts/generar_badges.py"
    for nombre in ("pyproject.toml", "uv.lock", ".gitignore", "Makefile", ".github/workflows/quality.yml"):
        p = raiz / nombre
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("Insumo de repositorio sintético.\n")
    (raiz / "scripts").mkdir()
    shutil.copy2(script, raiz / "scripts/generar_badges.py")
    (raiz / "src").mkdir()
    (raiz / "src/ejemplo.py").write_text('"""Synthetic module."""\n')
    (raiz / "junit.xml").write_text(
        '<testsuites><testsuite tests="2" failures="0" errors="0" skipped="0"/></testsuites>'
    )
    (raiz / "coverage.xml").write_text('<coverage lines-covered="8" lines-valid="10"/>')
    medicion = raiz / "medicion.json"
    medicion.write_bytes(
        serializar(
            {
                "huella_codigo_sha256": _huella_codigo(raiz),
                "pruebas": {"tests": 2, "ejecutadas": 2, "aprobadas": 2, "failures": 0, "errors": 0, "skipped": 0},
                "cobertura": {"lineas_cubiertas": 8, "lineas_totales": 10, "porcentaje": 80.0},
            }
        )
    )
    monkeypatch.setattr("goes_science_kg.entrega.despacho._contar_pruebas", lambda _: 2)
    escritorio = raiz.parent / "Desktop"
    escritorio.mkdir()
    return {
        "raiz": raiz,
        "edicion": edicion,
        "archivo_zip": archivo_zip,
        "auditoria": auditoria,
        "medicion": medicion,
        "destino": escritorio / "Ciencias",
    }, manifest


def test_despacho_completo_conserva_originales_indice_y_evidencia(despacho_listo):
    argumentos, manifest = despacho_listo
    antes = digest(argumentos["archivo_zip"])
    extra = argumentos["raiz"] / "adecuacion.json"
    extra.write_text('{"estado":"favorable_documental"}\n')
    recibo = despachar(**argumentos, evidencias_extra=[extra])
    destino = argumentos["destino"]
    assert recibo["edicion_id"] == manifest["id"]
    assert verificar_despacho(destino) == recibo
    assert digest(argumentos["archivo_zip"]) == antes == digest(destino / "paquetes.zip")
    assert (destino / "entrega/INDICE.md").is_file() and (
        destino / "calidad/adecuacion.json"
    ).read_bytes() == extra.read_bytes()
    leeme = (destino / "LEEME.md").read_text()
    assert "Paquetes nuevos revisados" in leeme and "Comparar materiales" in leeme
    assert "carga cognitiva medida" in leeme
    assert str(argumentos["raiz"]) not in json.dumps(recibo)
    assert all("ensayo" not in p for p in recibo["archivos"])


def test_archivo_de_material_alterado_bloquea_antes_de_copiar(despacho_listo):
    argumentos, _ = despacho_listo
    (argumentos["edicion"] / "INDICE.md").write_text("Índice alterado.")
    with pytest.raises(ValueError, match="inventario"):
        despachar(**argumentos)
    assert not argumentos["destino"].exists()


def test_zip_divergente_o_corrupto_no_se_despacha(despacho_listo):
    argumentos, _ = despacho_listo
    argumentos["archivo_zip"].write_bytes(b"No es un ZIP.")
    with pytest.raises(ValueError, match="integridad"):
        despachar(**argumentos)
    assert not argumentos["destino"].exists()


def test_zip_con_entrada_ajena_no_se_despacha(despacho_listo):
    argumentos, _ = despacho_listo
    with zipfile.ZipFile(argumentos["archivo_zip"], "a") as z:
        z.writestr("../fuera.txt", "No debe salir.")
    with pytest.raises(ValueError, match="inventario"):
        despachar(**argumentos)


@pytest.mark.parametrize(
    "campo,valor",
    [
        ("manifest_id", "otro"),
        ("errores", ["Defecto abierto"]),
        ("zip_sha256", "0" * 64),
        ("json_revisados", ["otra identidad"]),
    ],
)
def test_auditoria_de_otra_version_o_con_fallos_no_es_aprobacion(despacho_listo, campo, valor):
    argumentos, _ = despacho_listo
    datos = json.loads(argumentos["auditoria"].read_bytes())
    datos[campo] = valor
    argumentos["auditoria"].write_bytes(serializar(datos))
    with pytest.raises(ValueError, match="auditoría independiente"):
        despachar(**argumentos)


def test_una_edicion_sin_dictamenes_no_sale_aunque_validador_base_la_admita(despacho_listo):
    argumentos, manifest = despacho_listo
    for p in (argumentos["edicion"] / "auditoria/revisiones").glob("*.json"):
        manifest["archivos"].pop(p.relative_to(argumentos["edicion"]).as_posix())
        p.unlink()
    manifest["revision_documental"] = []
    manifest["id"] = sha(serializar({k: v for k, v in manifest.items() if k != "id"}))
    (argumentos["edicion"] / "manifest.json").write_bytes(serializar(manifest))
    assert validar(argumentos["edicion"])["revision_documental"] == []
    with pytest.raises(ValueError, match="dictámenes"):
        despachar(**argumentos)


@pytest.mark.parametrize("campo", ["failures", "errors", "skipped"])
def test_suite_con_fallos_o_omisiones_no_se_presenta_como_final(despacho_listo, campo):
    argumentos, _ = despacho_listo
    datos = json.loads(argumentos["medicion"].read_bytes())
    datos["pruebas"][campo] = 1
    argumentos["medicion"].write_bytes(serializar(datos))
    with pytest.raises(ValueError, match="suite completa"):
        despachar(**argumentos)


def test_suite_parcial_aunque_todo_lo_ejecutado_pase_se_rechaza(despacho_listo):
    argumentos, _ = despacho_listo
    datos = json.loads(argumentos["medicion"].read_bytes())
    for clave in ("tests", "ejecutadas", "aprobadas"):
        datos["pruebas"][clave] = 1
    argumentos["medicion"].write_bytes(serializar(datos))
    (argumentos["raiz"] / "junit.xml").write_text('<testsuite tests="1" failures="0" errors="0" skipped="0"/>')
    with pytest.raises(ValueError, match="colección actual"):
        despachar(**argumentos)


def test_huella_obsoleta_y_junit_contradictorio_no_acreditan_calidad(despacho_listo):
    argumentos, _ = despacho_listo
    (argumentos["raiz"] / "src/ejemplo.py").write_text('"""Nueva versión sin medir."""\n')
    with pytest.raises(ValueError, match="otra versión de código"):
        despachar(**argumentos)


def test_junit_contradictorio_bloquea(despacho_listo):
    argumentos, _ = despacho_listo
    (argumentos["raiz"] / "junit.xml").write_text('<testsuite tests="2" failures="1" errors="0" skipped="0"/>')
    with pytest.raises(ValueError, match="JUnit"):
        despachar(**argumentos)


def test_no_sobrescribe_una_carpeta_del_escritorio(despacho_listo):
    argumentos, _ = despacho_listo
    destino = argumentos["destino"]
    destino.mkdir()
    (destino / "trabajo.txt").write_text("Trabajo que se conserva.")
    with pytest.raises(ValueError, match="no se sobrescribe"):
        despachar(**argumentos)
    assert (destino / "trabajo.txt").read_text() == "Trabajo que se conserva."


def test_no_se_solapa_con_la_edicion_y_rechaza_enlaces(despacho_listo):
    argumentos, _ = despacho_listo
    argumentos["destino"] = argumentos["edicion"] / "copia"
    with pytest.raises(ValueError, match="solaparse"):
        despachar(**argumentos)
    argumentos["destino"] = argumentos["raiz"].parent / "enlace"
    argumentos["destino"].symlink_to(argumentos["edicion"], target_is_directory=True)
    with pytest.raises(ValueError, match="carpeta nueva"):
        despachar(**argumentos)


def test_destino_que_aparece_durante_copia_se_conserva(despacho_listo, monkeypatch):
    argumentos, _ = despacho_listo
    original = shutil.copytree

    def copiar_y_crear_destino(*args, **kwargs):
        salida = original(*args, **kwargs)
        destino = argumentos["destino"]
        if not destino.exists():
            destino.mkdir()
            (destino / "ajeno.txt").write_text("No sobrescribir.")
        return salida

    monkeypatch.setattr("goes_science_kg.entrega.despacho.shutil.copytree", copiar_y_crear_destino)
    with pytest.raises(FileExistsError):
        despachar(**argumentos)
    assert (argumentos["destino"] / "ajeno.txt").read_text() == "No sobrescribir."


@pytest.mark.parametrize("cambio", ["evidencia", "codigo"])
def test_cambio_durante_la_copia_invalida_el_despacho(despacho_listo, monkeypatch, cambio):
    argumentos, _ = despacho_listo
    original = shutil.copy2
    cambiado = False

    def copiar_y_alterar(origen, destino, *args, **kwargs):
        nonlocal cambiado
        resultado = original(origen, destino, *args, **kwargs)
        if not cambiado:
            cambiado = True
            if cambio == "evidencia":
                datos = json.loads(argumentos["auditoria"].read_bytes())
                datos["nota"] = "Cambio posterior a la validación."
                argumentos["auditoria"].write_bytes(serializar(datos))
            else:
                (argumentos["raiz"] / "src/ejemplo.py").write_text('"""Código cambiado durante copia."""\n')
        return resultado

    monkeypatch.setattr("goes_science_kg.entrega.despacho.shutil.copy2", copiar_y_alterar)
    with pytest.raises(ValueError, match="evidencias|cambiaron"):
        despachar(**argumentos)
    assert not argumentos["destino"].exists()


def test_recibo_no_permite_escapar_por_ruta_zip(despacho_listo):
    argumentos, _ = despacho_listo
    despachar(**argumentos)
    p = argumentos["destino"] / "recibo_despacho.json"
    recibo = json.loads(p.read_bytes())
    recibo["zip"]["archivo"] = "../paquetes.zip"
    recibo["id"] = sha(serializar({k: v for k, v in recibo.items() if k != "id"}))
    p.write_bytes(serializar(recibo))
    with pytest.raises(ValueError, match="nombre ZIP"):
        verificar_despacho(argumentos["destino"])


def test_copia_posteriormente_alterada_no_supera_el_recibo(despacho_listo):
    argumentos, _ = despacho_listo
    despachar(**argumentos)
    (argumentos["destino"] / "LEEME.md").write_text("Otro contenido.")
    with pytest.raises(ValueError, match="incompleta o fue alterada"):
        verificar_despacho(argumentos["destino"])


def test_coleccion_no_ejecuta_pruebas_y_rechaza_fallo(monkeypatch, tmp_path):
    llamadas = []

    def ejecutar(comando, **kwargs):
        llamadas.append(comando)
        return SimpleNamespace(returncode=0, stdout="2 tests collected in 0.1s\n")

    monkeypatch.setattr("goes_science_kg.entrega.despacho.subprocess.run", ejecutar)
    assert _contar_pruebas(tmp_path) == 2
    assert "--collect-only" in llamadas[0]
    monkeypatch.setattr(
        "goes_science_kg.entrega.despacho.subprocess.run", lambda *a, **k: SimpleNamespace(returncode=1, stdout="error")
    )
    with pytest.raises(ValueError, match="colección completa"):
        _contar_pruebas(tmp_path)


def test_un_filtro_del_entorno_no_convierte_una_suite_parcial_en_completa(monkeypatch, tmp_path):
    monkeypatch.setenv("PYTEST_ADDOPTS", "-k solo_una_prueba")
    llamadas = []

    def ejecutar(comando, **kwargs):
        llamadas.append((comando, kwargs))
        return SimpleNamespace(returncode=0, stdout="5 tests collected in 0.1s\n")

    monkeypatch.setattr("goes_science_kg.entrega.despacho.subprocess.run", ejecutar)
    assert _contar_pruebas(tmp_path) == 5
    comando, opciones = llamadas[0]
    assert "PYTEST_ADDOPTS" not in opciones["env"]
    assert "tests" in comando and "addopts=" in comando
