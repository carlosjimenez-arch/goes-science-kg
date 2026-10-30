"""Regression checks for complete successor views and immutable delivery provenance."""

from __future__ import annotations

import json

import pytest
from test_cierre_recorridos import recorrido as recorrido
from test_clases import guion
from test_clases_complementaria import anexo, evaluacion, item

from goes_science_kg.clases.paquete import construir
from goes_science_kg.entrega.compilacion import RECIBOS, compilar, digest, validar
from goes_science_kg.entrega.lectura import markdown_anexo_completo, markdown_evaluacion, markdown_unidad
from goes_science_kg.materiales.compilacion import _entrada, serializar, sha


def test_evaluacion_docente_conserva_tres_niveles_y_estudiante_no_recibe_claves():
    evaluada = evaluacion(
        [
            item(f"I0{i}", dominio, "respuesta_construida")
            for i, dominio in enumerate(("conocer", "aplicar", "aplicar", "razonar", "conocer", "razonar"), 1)
        ]
    ).model_dump(mode="json")
    docente = markdown_evaluacion(evaluada, "Unidad de prueba")
    estudiante = markdown_evaluacion(evaluada, "Unidad de prueba", estudiante=True)
    for pregunta in evaluada["items"]:
        assert pregunta["enunciado"] in docente and pregunta["enunciado"] in estudiante
        assert pregunta["justificacion"] in docente
        for criterio in pregunta["rubrica"]:
            for campo in ("criterio", "logrado", "en_proceso", "requiere_apoyo"):
                assert criterio[campo] in docente
    assert "- Requiere apoyo:" in docente
    assert "Clave:" not in estudiante and "Justificación:" not in estudiante and "Rúbrica" not in estudiante


def test_unidad_muestra_faltantes_y_motivos_en_la_vista_legible():
    material = {
        "titulo": "Unidad parcial",
        "grados": [4],
        "asignatura": "Ciencias",
        "documento": {
            "guiones": [],
            "completa": False,
            "licencia_adaptacion": "Atribución de la fuente.",
            "objetivos_sin_guion_liberado": [
                {
                    "fila_id": "falta",
                    "estado": "bloqueado_revision_directa",
                    "titulo": "Objetivo incompleto",
                    "motivo": "Falta una fuente pertinente para la explicación.",
                }
            ],
        },
    }
    texto = markdown_unidad(material)
    assert "Unidad incompleta" in texto and "1 objetivos sin guion" in texto
    assert "bloqueado_revision_directa" in texto and "Falta una fuente pertinente" in texto


def test_anexo_muestra_identidad_y_destino_de_la_progresion():
    datos = anexo().model_dump(mode="json")
    texto = markdown_anexo_completo(datos, "Clase de prueba")
    for grupo in ("ideas_previas", "continuidad"):
        for enlace in datos["progresion"][grupo]:
            assert enlace["fila_id"] in texto
    assert "../objetivos/" in texto and "SHA-256" in texto


@pytest.fixture
def base_sintetica(tmp_path, monkeypatch):
    raiz = tmp_path / "repo"
    (raiz / "config").mkdir(parents=True)
    g = guion("fila1").model_dump(mode="json")
    documento = {
        "guion": g,
        "snapshot_id": "snapshot",
        "preparacion_id": "p",
        "origen": {},
        "alerta_original": None,
        "enmiendas": [],
        "dictamenes": [],
        "fuentes_cientificas": [],
        "licencia_adaptacion": "Atribución.",
    }
    clase = _entrada(
        "clase1",
        "V4",
        "guion_clase",
        g["titulo"],
        documento,
        grados=[4],
        asignatura="Ciencias",
        unidad="Unidad 1",
        fila_id="fila1",
        estado="respaldado_automaticamente",
    )
    datos_unidad = {
        "guiones": [
            {
                "material_id": "clase1",
                "fila_id": "fila1",
                "titulo": g["titulo"],
                "objetivo": g["objetivo"],
                "duracion_minutos": 60,
            }
        ],
        "licencia_adaptacion": "Atribución.",
    }
    unidad = _entrada(
        "unidad1",
        "V4",
        "guion_unidad",
        "Unidad 1",
        datos_unidad,
        grados=[4],
        asignatura="Ciencias",
        unidad="Unidad 1",
        estado="respaldado_automaticamente",
    )
    archivo = raiz / "base.zip"
    manifest = construir([clase, unidad], {}, archivo, procedencia={"objetivos_sin_guion_liberado": []})
    for nombre_recibo in RECIBOS:
        recibo = {"objeto": {"sha256": digest(archivo)}, "entrega_id": manifest["id"]}
        (raiz / f"config/{nombre_recibo}.lock.json").write_bytes(serializar(recibo))
    complementos = {
        "id": "complemento",
        "clases": {},
        "unidades": {},
        "retenidos": [{"tipo": "anexo", "id": "retenido", "motivo": "Bloqueo por fuente insuficiente."}],
    }
    monkeypatch.setattr("goes_science_kg.entrega.compilacion.leer_publicada", lambda _: complementos)
    return raiz, archivo, complementos


def test_edicion_no_toca_originales_y_rechaza_alteracion(base_sintetica):
    raiz, archivo, _ = base_sintetica
    antes = digest(archivo)
    destino = raiz / "edicion"
    manifest = compilar(raiz, archivo, destino, archivo_zip=raiz / "sucesor.zip")
    assert digest(archivo) == antes and manifest["resumen"]["clases"] == 1
    assert manifest["mediciones"]["carga_cognitiva"] == "no_medida"
    assert validar(destino)["id"] == manifest["id"]
    assert "1 piezas retenidas" in (destino / "INDICE.md").read_text()
    catalogo = destino / "catalogo.json"
    catalogo.write_text(catalogo.read_text() + " ")
    with pytest.raises(ValueError, match="inventario"):
        validar(destino)


def test_no_se_hereda_aprobacion_a_retenidos_recalculando_el_inventario(base_sintetica):
    raiz, archivo, _ = base_sintetica
    destino = raiz / "edicion"
    compilar(raiz, archivo, destino)
    catalogo = json.loads((destino / "catalogo.json").read_bytes())
    catalogo["complementos"].append({"tipo": "anexo", "id": "retenido"})
    raw = serializar(catalogo)
    (destino / "catalogo.json").write_bytes(raw)
    manifest = json.loads((destino / "manifest.json").read_bytes())
    manifest["archivos"]["catalogo.json"] = {"bytes": len(raw), "sha256": sha(raw)}
    manifest["id"] = sha(serializar({k: v for k, v in manifest.items() if k != "id"}))
    (destino / "manifest.json").write_bytes(serializar(manifest))
    with pytest.raises(ValueError, match="retenido"):
        validar(destino)


def test_salida_existente_y_original_de_otro_recibo_se_rechazan(base_sintetica):
    raiz, archivo, _ = base_sintetica
    destino = raiz / "edicion"
    destino.mkdir()
    with pytest.raises(ValueError, match="carpeta nueva"):
        compilar(raiz, archivo, destino)
    recibo = raiz / "config/clases_ciencias.lock.json"
    datos = json.loads(recibo.read_bytes())
    datos["objeto"]["sha256"] = "0" * 64
    recibo.write_bytes(serializar(datos))
    with pytest.raises(ValueError, match="recibo"):
        compilar(raiz, archivo, raiz / "otra")


@pytest.mark.parametrize("fraude", ["denominador", "medicion"])
def test_no_se_inventan_denominadores_ni_mediciones_recalculando_identidad(base_sintetica, fraude):
    raiz, archivo, _ = base_sintetica
    destino = raiz / "edicion"
    compilar(raiz, archivo, destino)
    manifest = json.loads((destino / "manifest.json").read_bytes())
    if fraude == "denominador":
        manifest["resumen"]["clases"] = 1013
    else:
        manifest["mediciones"]["carga_cognitiva"] = "baja"
    manifest["id"] = sha(serializar({k: v for k, v in manifest.items() if k != "id"}))
    (destino / "manifest.json").write_bytes(serializar(manifest))
    with pytest.raises(ValueError, match="denominadores|observaciones"):
        validar(destino)


@pytest.fixture
def correccion_sintetica(base_sintetica, recorrido):
    import zipfile

    raiz, archivo, _ = base_sintetica
    with zipfile.ZipFile(archivo) as z:
        entrada = next(r for r in json.loads(z.read("catalogo.json")) if r["tipo"] == "guion_clase")
        material = json.loads(z.read(entrada["archivo"]))
    recorrido["origen"] = {"fila_id": "fila1", "guion_sha256": sha(serializar(material["documento"]["guion"]))}
    recorrido["objetivos"] = [material["documento"]["guion"]["objetivo"]]
    ciencias = raiz / "ciencias"
    ciencias.mkdir()
    (ciencias / "paquete.json").write_bytes(serializar(recorrido))
    for nombre in ("docente.md", "estudiante.md", "comprobacion.md"):
        (ciencias / nombre).write_text("Hoja obsoleta que no debe convertirse en entrega efectiva.")
    catalogo = [
        {
            "fila_id": "fila1",
            "guion_sha256_anterior": recorrido["origen"]["guion_sha256"],
            "paquete_json": "paquete.json",
            "docente_md": "docente.md",
            "estudiante_md": "estudiante.md",
            "comprobacion_md": "comprobacion.md",
        }
    ]
    (ciencias / "catalogo_correcciones.json").write_bytes(serializar(catalogo))
    return ciencias, recorrido


def test_correccion_regenera_cuatro_hojas_y_rechaza_un_clon_aunque_recalculen_sha(base_sintetica, correccion_sintetica):
    raiz, archivo, _ = base_sintetica
    ciencias, _ = correccion_sintetica
    destino = raiz / "edicion"
    compilar(raiz, archivo, destino, ciencias=ciencias)
    catalogo = json.loads((destino / "catalogo.json").read_bytes())
    prefijo = catalogo["clases"][0]["archivo"]
    assert "Hoja obsoleta" not in (destino / (prefijo + ".docente.md")).read_text()
    assert "Diagnóstico" in (destino / (prefijo + ".diagnostico.md")).read_text()
    final = destino / (prefijo + ".comprobacion.md")
    final.write_bytes((destino / (prefijo + ".estudiante.md")).read_bytes())
    manifest = json.loads((destino / "manifest.json").read_bytes())
    manifest["archivos"][prefijo + ".comprobacion.md"] = {"bytes": final.stat().st_size, "sha256": digest(final)}
    manifest["id"] = sha(serializar({k: v for k, v in manifest.items() if k != "id"}))
    (destino / "manifest.json").write_bytes(serializar(manifest))
    with pytest.raises(ValueError, match="cuatro hojas"):
        validar(destino)


def test_correccion_de_otro_objetivo_no_se_admite_por_cambiar_el_catalogo(base_sintetica, correccion_sintetica):
    raiz, archivo, _ = base_sintetica
    ciencias, datos = correccion_sintetica
    datos["origen"]["fila_id"] = "otro_objetivo"
    (ciencias / "paquete.json").write_bytes(serializar(datos))
    with pytest.raises(ValueError, match="otro antecedente"):
        compilar(raiz, archivo, raiz / "edicion", ciencias=ciencias)


def test_alias_json_de_una_correccion_no_cuenta_como_otro_modulo(base_sintetica, correccion_sintetica):
    raiz, archivo, _ = base_sintetica
    ciencias, datos = correccion_sintetica
    (ciencias / "CIEN-ALIAS.json").write_bytes(serializar(datos))
    manifest = compilar(raiz, archivo, raiz / "edicion", ciencias=ciencias)
    assert manifest["resumen"]["correcciones_cientificas"] == 1
    assert manifest["resumen"]["modulos_adicionales"] == 0


def test_dictamen_no_aprueba_otra_version_aunque_las_hojas_se_regeneren(base_sintetica, correccion_sintetica):
    raiz, archivo, _ = base_sintetica
    ciencias, datos = correccion_sintetica
    revisiones = raiz / "revisiones"
    revisiones.mkdir()
    dictamen = {
        "estado": "favorable_en_alcance_documental",
        "archivos": [
            {
                "id": datos["id"],
                "estado": "favorable_en_alcance_documental",
                "hallazgos_abiertos": [],
                "sha256": digest(ciencias / "paquete.json"),
            }
        ],
    }
    (revisiones / "revision.json").write_bytes(serializar(dictamen))
    manifest = compilar(raiz, archivo, raiz / "primera", ciencias=ciencias, revisiones=revisiones)
    assert manifest["revision_documental"] == [datos["id"]]
    datos["fundamento"].append("Una afirmación nueva que el dictamen anterior no revisó.")
    (ciencias / "paquete.json").write_bytes(serializar(datos))
    with pytest.raises(ValueError, match="versión revisada"):
        compilar(raiz, archivo, raiz / "segunda", ciencias=ciencias, revisiones=revisiones)
