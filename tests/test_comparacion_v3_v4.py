"""Compare versions conservatively without inheriting identities, grades, or decisions."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from openpyxl import Workbook

from goes_science_kg.config import ruta
from goes_science_kg.curriculo.comparacion import comparar_curriculos, guardar_comparacion, normalizar_literal
from goes_science_kg.curriculo.contratos import FASES, CeldaCurricular, Curriculo, FaseCurricular, FilaCurricular
from goes_science_kg.modelos import Fuente, Nodo, TipoNodo
from goes_science_kg.producto.referencias import cargar_referencias_historicas


def _sha(contenido: bytes) -> str:
    return hashlib.sha256(contenido).hexdigest()


def _historico(tmp_path: Path, filas: list[dict]):
    """Build synthetic graph and workbook sources whose hashes are checked on loading."""
    libro = Workbook()
    hoja = libro.active
    hoja.title = "Unidad 1"
    hoja.append(
        [
            "Contenido",
            "Subcontenidos",
            "Procedimental",
            "Indicador avanzado",
            "Indicadores de logro",
            "Evidencia de aprendizaje",
            "Habilidad TIMSS",
            "Competencia PISA 2025",
        ]
    )
    hoja.append([None] * 8)
    nodos = []
    for indice, datos in enumerate(filas, 3):
        contenido = datos.get("contenido_original", datos.get("contenido", "Materia"))
        avanzado, logro = datos.get("avanzado", "Indicador avanzado"), datos.get("logro", "Indicador de logro")
        objetivo = datos.get("objetivo", "1.1. Mide el agua.")
        hoja.append(
            [
                contenido,
                datos.get("subcontenido", "Medidas"),
                objetivo,
                avanzado,
                logro,
                "Tabla",
                "Aplicar",
                "Explicar fenómenos",
            ]
        )
        nodos.append(
            Nodo(
                id=datos.get("id", f"TEMA:V3:{indice}"),
                tipo=TipoNodo.TEMA,
                etiqueta=objetivo,
                grado=datos.get("grado", 2),
                asignatura=datos.get("inferida", "fisica"),
                fuente=Fuente(documento="malla3", hoja="Unidad 1", fila=indice),
                props={
                    "version_curriculo": "V3",
                    "asignatura_malla": datos.get("malla", "ciencias"),
                    "contenido": datos.get("contenido", "Materia"),
                    "subcontenido": datos.get("subcontenido", "Medidas"),
                    "indicador": datos.get("indicador", logro),
                    "unidad": "1. Materia.",
                    "evidencia": "Tabla",
                    "habilidad_timss": "Aplicar",
                    "competencia_pisa": "Explicar fenómenos",
                    "revisado_por": "Decisión humana que no se debe trasladar",
                },
            )
        )
    archivo = tmp_path / "malla.xlsx"
    libro.save(archivo)
    libro.close()
    nodos.append(
        Nodo(
            id="DOC:malla3",
            tipo=TipoNodo.DOCUMENTO,
            etiqueta="Fuente V3",
            props={"archivo_local": "malla.xlsx", "sha256": _sha(archivo.read_bytes())},
        )
    )
    datos_nodos = "".join(n.model_dump_json() + "\n" for n in nodos).encode()
    (tmp_path / "nodos.jsonl").write_bytes(datos_nodos)
    (tmp_path / "aristas.jsonl").write_bytes(b"")
    (tmp_path / "manifest.json").write_text(
        json.dumps(
            {
                "version": "v1",
                "version_curriculo": "V3",
                "sha256": {"nodos.jsonl": _sha(datos_nodos), "aristas.jsonl": _sha(b"")},
            }
        )
    )
    return cargar_referencias_historicas(tmp_path)


def _fila(
    identidad="CURRICULO:V4:uno",
    *,
    objetivo="1.1. Mide el agua.",
    grado=2,
    malla="Ciencias",
    contenido="Materia",
    avanzado="Indicador avanzado nuevo",
    logro="Indicador de logro",
    fila=3,
):
    return FilaCurricular(
        id=identidad,
        fuente_id="fuente4",
        version="V4",
        hoja="Unidad 1",
        fila=fila,
        grado=grado,
        asignatura_malla=malla,
        unidad="Unidad 1 - Materia",
        contenido=contenido,
        subcontenido="Medidas",
        procedimental=objetivo,
        indicador_avanzado=avanzado,
        indicadores_logro=logro,
        evidencia_aprendizaje="Tabla",
        habilidad_timss="Aplicar",
        competencia_pisa="Explicar fenómenos",
        fases={f: FaseCurricular(presente_en_hoja=False) for f in FASES},
        celdas=(
            CeldaCurricular(
                coordenada=f"C{fila}",
                fila=fila,
                columna="C",
                campo="procedimental",
                valor_original=objetivo,
                valor=objetivo,
                tipo_excel="s",
            ),
        ),
    )


def _curriculo(*filas):
    """Provide the minimum comparison contract without claiming actual ingestion or activation."""
    return Curriculo(version="V4", huella="a" * 64, fuentes=(), hojas=(), agrupaciones=(), filas=filas)


def test_normalizacion_conserva_semantica_de_simbolos_y_numeracion():
    assert normalizar_literal("１．１． Mide\n  agua") == "1.1. Mide agua"
    assert normalizar_literal("CO") != normalizar_literal("Co")
    assert normalizar_literal("1.1. Mide.") != normalizar_literal("Mide")
    assert normalizar_literal("No mezclar") != normalizar_literal("Mezclar")


def test_coincidencia_literal_normalizada_no_transfiere_etiquetas(tmp_path):
    historico = _historico(tmp_path, [{"objetivo": "１．１． Mide\n   el agua."}])
    resultado = comparar_curriculos(historico, _curriculo(_fila()), raiz_historica=tmp_path)
    assert resultado.resumen["coincidencias_1_a_1"] == 1
    pareja = resultado.coincidencias[0]
    assert pareja.estado == "coincidencia_objetivo_1_a_1"
    assert pareja.anteriores[0].asignatura_malla == "ciencias" and pareja.actuales[0].asignatura_malla == "Ciencias"
    assert "revisado_por" not in pareja.model_dump_json() and "inferida" not in pareja.model_dump_json()
    assert resultado.criterios["hereda_identidad_etiquetas_aristas"] is False


@pytest.mark.parametrize("lados", [(1, 2), (2, 1), (2, 2)])
def test_repeticiones_nunca_se_resuelven_arbitrariamente(tmp_path, lados):
    historico = _historico(tmp_path, [{} for _ in range(lados[0])])
    actual = _curriculo(*(_fila(f"CURRICULO:V4:{i}", fila=3 + i) for i in range(lados[1])))
    resultado = comparar_curriculos(historico, actual, raiz_historica=tmp_path)
    assert resultado.resumen["coincidencias_1_a_1"] == 0 and resultado.resumen["grupos_ambiguos"] == 1
    grupo = resultado.coincidencias[0]
    assert grupo.estado == "ambigua" and not grupo.campos
    assert len(grupo.anteriores) == lados[0] and len(grupo.actuales) == lados[1]
    assert not resultado.sin_correspondencia_v3 and not resultado.sin_correspondencia_v4
    assert bool(resultado.repeticiones["V3"]) == (lados[0] > 1)
    assert bool(resultado.repeticiones["V4"]) == (lados[1] > 1)


def test_mismo_objetivo_en_otro_grado_solo_referencia_de_revision(tmp_path):
    resultado = comparar_curriculos(
        _historico(tmp_path, [{"grado": 2}]), _curriculo(_fila(grado=3)), raiz_historica=tmp_path
    )
    assert not resultado.coincidencias
    assert resultado.resumen["mismo_objetivo_otro_contexto_v3"] == 1
    assert resultado.resumen["mismo_objetivo_otro_contexto_v4"] == 1
    assert resultado.sin_correspondencia_v3[0].estado == "sin_coincidencia_exacta"
    assert resultado.sin_correspondencia_v4[0].mismo_objetivo_otro_contexto[0].grado == 2


def test_disciplina_inferida_no_sustituye_asignatura_de_malla(tmp_path):
    resultado = comparar_curriculos(
        _historico(tmp_path, [{"malla": "ciencias", "inferida": "biologia"}]),
        _curriculo(_fila(malla="Biología")),
        raiz_historica=tmp_path,
    )
    assert not resultado.coincidencias
    assert resultado.sin_correspondencia_v3[0].registro.asignatura_comparable == "Ciencias"


def test_representacion_slug_bachillerato_es_explicita_y_no_inferida(tmp_path):
    resultado = comparar_curriculos(
        _historico(tmp_path, [{"malla": "quimica", "inferida": "fisica"}]),
        _curriculo(_fila(malla="Química")),
        raiz_historica=tmp_path,
    )
    assert resultado.resumen["coincidencias_1_a_1"] == 1
    assert resultado.coincidencias[0].asignatura_malla == "Química"


def test_misma_fila_fisica_con_otro_objetivo_no_confirma_identidad(tmp_path):
    resultado = comparar_curriculos(
        _historico(tmp_path, [{}]), _curriculo(_fila(objetivo="1.1. Evapora el agua.")), raiz_historica=tmp_path
    )
    assert not resultado.coincidencias
    assert resultado.sin_correspondencia_v3[0].registro.fuente["fila"] == 3
    assert resultado.sin_correspondencia_v4[0].registro.fuente["fila"] == 3
    assert not resultado.sin_correspondencia_v4[0].mismo_objetivo_otro_contexto


def test_objetivo_igual_y_contenido_distinto_no_es_secuencia_identica(tmp_path):
    resultado = comparar_curriculos(
        _historico(tmp_path, [{}]), _curriculo(_fila(contenido="Otro contenido")), raiz_historica=tmp_path
    )
    pareja = resultado.coincidencias[0]
    contenido = next(c for c in pareja.campos if c.campo_v3 == "contenido")
    assert contenido.estado == "valor_distinto" and pareja.estado == "coincidencia_objetivo_1_a_1"
    assert contenido.fuente_v3["sha256"] and contenido.fuente_v3["celdas"] == ["A3"]


def test_indicador_legacy_se_compara_solo_con_su_columna_precisa(tmp_path):
    resultado = comparar_curriculos(_historico(tmp_path, [{}]), _curriculo(_fila()), raiz_historica=tmp_path)
    indicador = next(c for c in resultado.coincidencias[0].campos if c.campo_v3 == "indicador")
    assert indicador.campo_v4 == "indicadores_logro" and indicador.estado == "igual_normalizado"
    assert indicador.fuente_v3["celdas"] == ["E3"]
    assert "indicador_avanzado" in resultado.coincidencias[0].sin_contraparte_v3
    assert "competencia_digital" in resultado.campos_incorporados_al_contrato_v4


def test_indicador_legacy_ambiguo_no_se_compara_con_dos_campos(tmp_path):
    historico = _historico(tmp_path, [{"avanzado": "El mismo texto", "logro": "El mismo texto"}])
    resultado = comparar_curriculos(historico, _curriculo(_fila()), raiz_historica=tmp_path)
    indicador = next(c for c in resultado.coincidencias[0].campos if c.campo_v3 == "indicador")
    assert indicador.estado == "no_comparable" and indicador.campo_v4 is None


def test_blanco_arrastrado_por_legacy_no_se_cuenta_como_cambio(tmp_path):
    historico = _historico(tmp_path, [{"contenido": "Materia anterior", "contenido_original": None}])
    resultado = comparar_curriculos(historico, _curriculo(_fila(contenido="")), raiz_historica=tmp_path)
    campo = next(c for c in resultado.coincidencias[0].campos if c.campo_v3 == "contenido")
    assert campo.estado == "no_comparable"


def test_fuente_alterada_no_respalda_comparaciones_de_campos(tmp_path):
    historico = _historico(tmp_path, [{}])
    (tmp_path / "malla.xlsx").write_bytes(b"No coincide con la fuente del manifiesto")
    resultado = comparar_curriculos(historico, _curriculo(_fila()), raiz_historica=tmp_path)
    assert all(c.estado == "no_comparable" for c in resultado.coincidencias[0].campos)


def test_duplicados_y_mezcla_de_versiones_rechazados(tmp_path):
    historico = _historico(tmp_path, [{}])
    with pytest.raises(ValueError, match="duplica"):
        comparar_curriculos(historico, _curriculo(_fila(), _fila()), raiz_historica=tmp_path)
    with pytest.raises(ValueError, match="requiere"):
        comparar_curriculos(
            historico, _curriculo(_fila()).model_copy(update={"version": "V3"}), raiz_historica=tmp_path
        )
    with pytest.raises(ValueError, match="únicas"):
        comparar_curriculos(
            historico.model_copy(update={"nodos": historico.nodos + historico.nodos[:1]}),
            _curriculo(_fila()),
            raiz_historica=tmp_path,
        )


def test_reporte_determinista_no_toca_originales_y_es_escribible(tmp_path):
    historico = _historico(tmp_path, [{}])
    fuente_antes = (tmp_path / "malla.xlsx").read_bytes()
    resultado = comparar_curriculos(historico, _curriculo(_fila()), raiz_historica=tmp_path)
    repetido = comparar_curriculos(historico, _curriculo(_fila()), raiz_historica=tmp_path)
    assert resultado == repetido and fuente_antes == (tmp_path / "malla.xlsx").read_bytes()
    guardar_comparacion(resultado, salida_json=tmp_path / "salida.json", salida_markdown=tmp_path / "salida.md")
    assert json.loads((tmp_path / "salida.json").read_text())["resumen"]["coincidencias_1_a_1"] == 1
    assert "No se trasladan IDs" in (tmp_path / "salida.md").read_text()


def test_reporte_real_separa_correspondencia_de_cambio_conceptual():
    resultado = json.loads(Path("docs/investigacion/comparacion_v3_v4.json").read_text())
    assert resultado["resumen"]["registros_v3"] == 935 and resultado["resumen"]["registros_v4"] == 1020
    assert resultado["resumen"]["coincidencias_1_a_1"] == 506 and resultado["resumen"]["grupos_ambiguos"] == 0
    assert resultado["resumen"]["sin_coincidencia_exacta_v3"] == 429
    assert resultado["resumen"]["sin_coincidencia_exacta_v4"] == 514
    indicadores = [c for pareja in resultado["coincidencias"] for c in pareja["campos"] if c["campo_v3"] == "indicador"]
    assert len(indicadores) == 506 and all(c["campo_v4"] == "indicadores_logro" for c in indicadores)
    assert resultado["criterios"]["similitud_fuzzy"] is False


@pytest.mark.parametrize(
    "relativa",
    [
        "config/informe.md",
        "src/informe.md",
        ".claude/informe.md",
        ".codex/informe.md",
        ".agents/informe.md",
        "data/referencias_2026/informe.md",
        "data/referencia/informe.md",
        "prompts/informe.md",
        ".env.md",
    ],
)
def test_writer_valida_destinos_antes_de_escribir_cualquiera(tmp_path, relativa):
    resultado = comparar_curriculos(_historico(tmp_path, [{}]), _curriculo(_fila()), raiz_historica=tmp_path)
    salida = tmp_path / "resultado.json"
    salida.write_text("Antes de la validación", encoding="utf-8")
    with pytest.raises(ValueError):
        guardar_comparacion(resultado, salida_json=salida, salida_markdown=ruta(relativa))
    assert salida.read_text(encoding="utf-8") == "Antes de la validación"


def test_writer_rechaza_destino_repetido_extension_incorrecta_y_directorio(tmp_path):
    resultado = comparar_curriculos(_historico(tmp_path, [{}]), _curriculo(_fila()), raiz_historica=tmp_path)
    repetida = tmp_path / "resultado.json"
    with pytest.raises(ValueError, match="distintos"):
        guardar_comparacion(resultado, salida_json=repetida, salida_markdown=repetida)
    for extension in ("resultado.txt", "resultado.md"):
        with pytest.raises(ValueError, match="extensión"):
            guardar_comparacion(resultado, salida_json=tmp_path / extension, salida_markdown=tmp_path / "bueno.md")
    carpeta = tmp_path / "carpeta.md"
    carpeta.mkdir()
    with pytest.raises(ValueError, match="directorio"):
        guardar_comparacion(resultado, salida_json=repetida, salida_markdown=carpeta)
    assert not repetida.exists()


def test_writer_no_sigue_enlace_de_archivo_ni_sustituye_destino_valido_primero(tmp_path):
    resultado = comparar_curriculos(_historico(tmp_path, [{}]), _curriculo(_fila()), raiz_historica=tmp_path)
    original = tmp_path / "original.md"
    original.write_text("Conservar", encoding="utf-8")
    enlace = tmp_path / "enlace.md"
    enlace.symlink_to(original)
    salida = tmp_path / "informe.json"
    with pytest.raises(ValueError, match="enlaces"):
        guardar_comparacion(resultado, salida_json=salida, salida_markdown=enlace)
    assert original.read_text(encoding="utf-8") == "Conservar" and enlace.is_symlink()
    assert not salida.exists()


def test_writer_fallo_replace_preserva_archivo_y_limpia_temporal(tmp_path, monkeypatch):
    resultado = comparar_curriculos(_historico(tmp_path, [{}]), _curriculo(_fila()), raiz_historica=tmp_path)
    salida = tmp_path / "informe.json"
    salida.write_text("Archivo anterior", encoding="utf-8")

    def fallar(*args, **kwargs):
        raise OSError("Fallo de reemplazo")

    monkeypatch.setattr(Path, "replace", fallar)
    with pytest.raises(OSError, match="reemplazo"):
        guardar_comparacion(resultado, salida_json=salida, salida_markdown=tmp_path / "informe.md")
    assert salida.read_text(encoding="utf-8") == "Archivo anterior"
    assert not list(tmp_path.glob(".informe.json.*"))
