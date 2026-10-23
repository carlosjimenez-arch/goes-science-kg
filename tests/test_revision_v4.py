"""Audit final contracts with independent fixtures and no private evaluation annotations."""

from __future__ import annotations

import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import openpyxl
import pytest
import typer
from pydantic import BaseModel, ValidationError
from typer.testing import CliRunner

from goes_science_kg.cli import producto as cli_producto
from goes_science_kg.curriculo.catalogacion import ClasificacionFila, DecisionDisciplina
from goes_science_kg.curriculo.contratos import (
    FASES,
    CeldaCurricular,
    Curriculo,
    FaseCurricular,
    FilaCurricular,
    FuenteCurricular,
)
from goes_science_kg.motor.fuentes import FuentesVerificadas
from goes_science_kg.motor.registro import PresupuestoAgotado, Registro
from goes_science_kg.motor.vertex import ConfiguracionVertex, Vertex
from goes_science_kg.producto.garantias import bloqueos_cientificos


@pytest.mark.parametrize(
    "relativo",
    [
        "insumos/procedencia_v4.json",
        "data/grafo/manifest.json",
        "reportes/salida.json",
        ".env",
        ".claude/settings.json",
        "config/modelo.json",
        "src/ejemplo.json",
        "data/operaciones/registro.sqlite",
    ],
)
def test_catalogar_rechaza_originales_e_historico_antes_de_ingerir_o_gastar(tmp_path, monkeypatch, relativo):
    monkeypatch.setattr(cli_producto, "ruta", lambda p: tmp_path / p)
    llamadas = []

    def no_ingerir():
        llamadas.append("ingesta")
        raise RuntimeError("La ruta debió rechazarse antes de ingerir o iniciar modelos")

    monkeypatch.setattr("goes_science_kg.curriculo.ingesta.cargar_curriculo", no_ingerir)
    resultado = CliRunner().invoke(cli_producto.app, ["catalogar", "--ejecutar", "--salida", str(tmp_path / relativo)])
    assert resultado.exit_code == 2
    assert llamadas == []
    assert not (tmp_path / relativo).exists()


def test_salida_json_personalizada_es_valida_y_enlace_no_sobrescribe_su_destino(tmp_path, monkeypatch):
    monkeypatch.setattr(cli_producto, "ruta", lambda p: tmp_path / "repo" / p)
    salida = tmp_path / "salida-personalizada.json"
    assert cli_producto._destino_escritura(salida, extension=".json") == salida.resolve()
    protegido = tmp_path / "configuracion-ajena.json"
    protegido.write_text("conservar")
    salida.symlink_to(protegido)
    with pytest.raises(typer.BadParameter, match="enlace simbólico"):
        cli_producto._destino_escritura(salida, extension=".json")
    assert protegido.read_text() == "conservar"


@pytest.fixture
def fuente_combinada(tmp_path):
    texto = "Afirmación científica de prueba que debe bloquearse por su alerta confirmada."
    archivo = tmp_path / "malla.xlsx"
    libro = openpyxl.Workbook()
    hoja = libro.active
    hoja.title = "Unidad 1"
    hoja.append(["Contenido", "Procedimental"])
    hoja.append(["Uno", texto])
    hoja.append(["Dos", None])
    hoja.append(["Tres", None])
    hoja.merge_cells("B2:B4")
    libro.save(archivo)
    libro.close()
    fuente = FuenteCurricular(
        id="fuente",
        version="V4",
        archivo=archivo.name,
        archivo_local="insumos/v4/malla.xlsx",
        sha256=hashlib.sha256(archivo.read_bytes()).hexdigest(),
        bytes=archivo.stat().st_size,
        procedencia={"version": "V4"},
    )
    filas = tuple(
        FilaCurricular(
            id=f"fila_{i}",
            fuente_id=fuente.id,
            version="V4",
            hoja="Unidad 1",
            fila=i,
            grado=4,
            asignatura_malla="Ciencias",
            unidad="U1",
            procedimental=texto,
            fases={f: FaseCurricular(presente_en_hoja=False) for f in FASES},
            celdas=(
                CeldaCurricular(
                    coordenada=f"B{i}",
                    fila=i,
                    columna="B",
                    campo="procedimental",
                    valor_original=texto if i == 2 else None,
                    valor=texto,
                    origen_combinado="B2",
                    tipo_excel="s",
                ),
            ),
        )
        for i in range(2, 5)
    )
    curriculo = Curriculo(version="V4", huella="a" * 64, fuentes=(fuente,), filas=filas, hojas=(), agrupaciones=())
    fuentes = FuentesVerificadas(
        {fuente.id: {"archivo_local": archivo.name, "sha256": fuente.sha256, "version_curriculo": "V4"}},
        raiz_fuentes=tmp_path,
    )
    alerta = {
        "id": "ALERTA-PRUEBA",
        "clase": "error_cientifico",
        "estado_verificacion": "confirmada",
        "ancla_original": texto,
        "explicacion": "Error confirmado en una fixture, no dictamen del producto",
        "fuente": {"archivo": fuente.archivo_local, "sha256": fuente.sha256, "hoja": "Unidad 1", "celdas": ["B3"]},
    }
    archivo_alertas = tmp_path / "alertas.json"
    archivo_alertas.write_text(json.dumps({"alertas": [alerta]}))
    return curriculo, fuentes, archivo_alertas, alerta


def test_alerta_en_combinada_secundaria_bloquea_todas_las_filas_que_leen_el_ancla(fuente_combinada):
    curriculo, fuentes, archivo, _ = fuente_combinada
    bloqueos = bloqueos_cientificos(curriculo, fuentes, archivo)
    assert set(bloqueos) == {"fila_2", "fila_3", "fila_4"}


def test_una_alerta_confirmada_sin_ancla_no_acredita_que_se_localizo_un_error(fuente_combinada):
    curriculo, fuentes, archivo, alerta = fuente_combinada
    alerta["ancla_original"] = "   "
    archivo.write_text(json.dumps({"alertas": [alerta]}))
    with pytest.raises(ValueError, match="ancla"):
        bloqueos_cientificos(curriculo, fuentes, archivo)


@pytest.mark.parametrize(
    "lecturas,errores",
    [
        ({}, ()),
        ({"catalogador_a": "fisica"}, ()),
        ({"catalogador_a": "fisica", "catalogador_b": "quimica"}, ()),
        ({"catalogador_a": "fisica", "catalogador_b": "fisica"}, ("fallo",)),
    ],
)
def test_contrato_impide_mostrar_consenso_sin_dos_lecturas_que_lo_respaldan(lecturas, errores):
    decisiones = {
        rol: DecisionDisciplina(
            fila_id="fila",
            estado="en_alcance",
            disciplinas=(disciplina,),
            justificacion="Objeto científico de una prueba sintética",
        )
        for rol, disciplina in lecturas.items()
    }
    with pytest.raises(ValidationError):
        ClasificacionFila(
            fila_id="fila",
            estado="coincidencia_automatica",
            disciplinas=("fisica",),
            metodo="dos_lecturas_independientes",
            justificacion="La etiqueta no demuestra consenso",
            lecturas=decisiones,
            errores=errores,
        )


class Respuesta(BaseModel):
    resultado: str


def _vertex_simulado(tmp_path, respuesta, *, max_llamadas=1):
    pytest.importorskip("google.genai")
    registro = Registro(tmp_path / "ledger.sqlite")
    cfg = ConfiguracionVertex(
        proyecto="proyecto-prueba",
        modelos={"prueba": "modelo-prueba"},
        tarifas={"modelo-prueba": {"entrada": 1, "salida": 1}},
        max_llamadas=max_llamadas,
        max_usd=1,
        max_salida_tokens=256,
        reintentos=0,
    )
    modelo = Vertex(cfg, registro, "revision-sin-red")
    modelo.__dict__["cliente"] = SimpleNamespace(models=SimpleNamespace(generate_content=respuesta))
    return modelo, registro


def test_uso_de_tokens_ausente_permanece_desconocido_y_conserva_reserva(tmp_path):
    modelo, registro = _vertex_simulado(
        tmp_path,
        lambda **_: SimpleNamespace(
            text='{"resultado":"válido"}',
            usage_metadata=None,
        ),
    )
    modelo.generar(rol="prueba", sistema="Sistema de prueba", mensaje="Mensaje de prueba", esquema=Respuesta)
    resumen = registro.resumen("revision-sin-red")
    assert resumen["reserva_usd"] > 0 and resumen["llamadas"] == 1
    assert resumen["detalle"][0]["entrada_tokens"] is None
    assert resumen["detalle"][0]["salida_tokens"] is None


def test_reservas_concurrentes_nunca_inician_mas_llamadas_que_el_limite(tmp_path):
    modelo, registro = _vertex_simulado(
        tmp_path,
        lambda **_: SimpleNamespace(
            text='{"resultado":"válido"}',
            usage_metadata=SimpleNamespace(prompt_token_count=10, candidates_token_count=5, thoughts_token_count=0),
        ),
        max_llamadas=3,
    )

    def ejecutar(i):
        try:
            return modelo.generar(rol="prueba", sistema="Sistema", mensaje=f"Consulta distinta {i}", esquema=Respuesta)
        except PresupuestoAgotado:
            return None

    with ThreadPoolExecutor(max_workers=8) as ejecutor:
        resultados = list(ejecutor.map(ejecutar, range(8)))
    assert sum(r is not None for r in resultados) == registro.resumen("revision-sin-red")["llamadas"] == 3
