"""CLI de alineación con Excel/PDF sintéticos, ledger y checkpoints locales; cero GCP."""

from __future__ import annotations

import copy
import json

import pytest
import typer
from test_alineacion import LectorSimulado
from test_alineacion import entrada as entrada
from typer.testing import CliRunner

from goes_science_kg.cli import alineacion
from goes_science_kg.ingesta.extraccion import CatalogoPerfilesPDF, PaginasConPerfil
from goes_science_kg.ingesta.referentes_operativos import CatalogoReferentesOperativos
from goes_science_kg.motor.registro import Registro


@pytest.fixture
def interfaz(entrada, tmp_path, monkeypatch):
    monkeypatch.setenv("GSKG_RAIZ", str(tmp_path))
    cfg = dict(
        version_curriculo="V4",
        referentes="config/referentes.yaml",
        perfiles="config/perfiles.yaml",
        repositorio="data/referencias",
        raiz_v4="insumos/v4",
        alertas="docs/alertas.json",
        registro="data/operaciones/registro.sqlite",
        checkpoints="data/operaciones/alineacion.sqlite",
        log="data/operaciones/alineacion.log",
        max_caracteres_contexto=18000,
        max_concurrencia=3,
        max_llamadas=3,
        max_usd=0.5,
        reintentos=0,
        roles_vertex={
            "alineador_cientifico": "cientifico",
            "alineador_psicopedagogo": "psicopedagogo",
            "alineador_adversarial": "adversarial",
        },
    )
    motor_cfg = {
        "vertex": dict(
            proyecto="proyecto-falso",
            region="global",
            modelos={"cientifico": "simulado-a", "psicopedagogo": "simulado-b", "adversarial": "simulado-a"},
            tarifas={"simulado-a": {"entrada": 1, "salida": 2}, "simulado-b": {"entrada": 1, "salida": 2}},
            max_llamadas=24,
            max_usd=3,
        )
    }
    monkeypatch.setattr(
        alineacion, "cargar", lambda nombre: copy.deepcopy(cfg if nombre == "alineacion" else motor_cfg)
    )
    ref = entrada.referente
    catalogo = CatalogoReferentesOperativos.model_validate(
        {
            "schema_version": "1.0",
            "meta": {
                "clasificacion": "parafrasis_del_proyecto",
                "no_equivalencia": "No es código oficial ni acredita alineación de una tarea o aprendizaje.",
                "fecha_consulta": "2026-10-21",
                "alcance": "Un referente sintético para comprobar la interfaz local.",
                "exhaustividad": "por_unidad_no_global",
                "paginas": "PDF desde 1, incluyendo la portada.",
                "procedencia": "data/referencias_2026/manifest.json",
                "documentacion": "docs/prueba.md",
                "limites": ["Sin inferencia de resultados de aprendizaje"],
                "cobertura": [
                    {
                        "fuente": ref.fuente,
                        "unidad": "Competencia sintética",
                        "paginas_pdf": [1],
                        "tipo": "competencia",
                        "esperados": 1,
                        "incluidos": 1,
                        "estado": "completa_en_unidad_declarada",
                        "limites": "La cobertura se limita a esta unidad sintética.",
                    }
                ],
            },
            "referentes": [ref.model_dump(mode="json")],
        }
    )
    perfiles = CatalogoPerfilesPDF.model_validate(
        {
            "schema_version": "1.0",
            "perfiles": [
                {
                    "id": "LOCAL:pagina_sintetica",
                    "fuente": ref.fuente,
                    "sha256": ref.sha256,
                    "pagina_pdf": 1,
                    "extractor": "pdfplumber",
                    "version": "1",
                    "regiones": [{"id": "LOCAL:cuerpo_sintetico", "bbox": [0, 0, 600, 800]}],
                }
            ],
        }
    )
    paginas = PaginasConPerfil(entrada.repositorio, perfiles)
    monkeypatch.setattr(alineacion, "_contexto", lambda _: (entrada.curriculo, catalogo, entrada.fuentes, paginas))
    monkeypatch.setattr(alineacion, "_referentes", lambda _: (catalogo, paginas))
    invocaciones = []
    creaciones = []
    salida = tmp_path / "resultado.json"

    class VertexSimulado(LectorSimulado):
        def __init__(self, configuracion, registro, ejecucion_id):
            super().__init__()
            assert json.loads(salida.read_text())["fase"] == "preparacion_local"
            assert json.loads(salida.read_text())["ejecucion_id"] == ejecucion_id
            self.configuracion, self.registro, self.ejecucion_id = configuracion, registro, ejecucion_id
            creaciones.append(self)

        def nombre_modelo(self, rol):
            return self.configuracion.modelos[rol]

        def generar(self, **kwargs):
            invocaciones.append(kwargs["rol"])
            llamada = self.registro.reservar(
                ejecucion=self.ejecucion_id,
                clave="prueba-" + kwargs["rol"],
                modelo=self.nombre_modelo(kwargs["rol"]),
                rol=kwargs["rol"],
                reserva_usd=0.001,
                max_llamadas=self.configuracion.max_llamadas,
                max_usd=self.configuracion.max_usd,
            )
            respuesta = super().generar(**kwargs)
            self.registro.terminar(llamada, estado="completada", latencia_ms=1, entrada_tokens=1, salida_tokens=1)
            return respuesta

    monkeypatch.setattr("goes_science_kg.motor.vertex.Vertex", VertexSimulado)
    app = typer.Typer()
    app.add_typer(alineacion.app, name="alineacion")
    return dict(
        runner=CliRunner(),
        app=app,
        solicitud=entrada.solicitud,
        cfg=cfg,
        paginas=paginas,
        invocaciones=invocaciones,
        creaciones=creaciones,
        salida=salida,
        base=tmp_path,
    )


def _invocar(interfaz, comando, *opciones):
    s = interfaz["solicitud"]
    return interfaz["runner"].invoke(
        interfaz["app"],
        [
            "alineacion",
            comando,
            s.fila_id,
            s.referente_id,
            "--salida",
            str(interfaz["salida"]),
            *opciones,
        ],
    )


@pytest.mark.parametrize("comando", ["preparar", "evaluar"])
def test_prepara_contexto_real_y_no_crea_modelo_o_ledger_sin_flag(interfaz, comando):
    resultado = _invocar(interfaz, comando)
    assert resultado.exit_code == 0, resultado.output
    datos = json.loads(interfaz["salida"].read_text())
    assert datos["llamadas"] == 0 and datos["preparacion"]["estado"] == "preparado"
    assert datos["huella_extraccion"] == interfaz["paginas"].huella_extraccion
    assert any(e["fuente"].get("perfil_id") for e in datos["preparacion"]["evidencias"])
    assert not interfaz["creaciones"] and not interfaz["invocaciones"]
    assert not (interfaz["base"] / interfaz["cfg"]["registro"]).exists()


def test_ejecutar_exige_flag_tres_roles_ledger_unico_y_reanuda_sin_llamadas_extra(interfaz):
    for _ in range(2):
        resultado = _invocar(interfaz, "evaluar", "--ejecutar", "--ejecucion", "mismo-par")
        assert resultado.exit_code == 0, resultado.output
    datos = json.loads(interfaz["salida"].read_text())
    assert datos["resultado"]["estado"] == "respaldo_documental_automatico"
    assert set(interfaz["invocaciones"]) == set(alineacion.ROLES_ALINEACION)
    assert len(interfaz["invocaciones"]) == datos["consumo"]["llamadas"] == 3
    assert all(c.registro.archivo == interfaz["base"] / interfaz["cfg"]["registro"] for c in interfaz["creaciones"])
    assert all(set(c.configuracion.modelos) == set(alineacion.ROLES_ALINEACION) for c in interfaz["creaciones"])
    assert len(datos["resultado"]["dictamenes"]) == 3
    assert "desempeño estudiantil" in datos["resultado"]["limite"]
    assert "CUBRE" not in interfaz["salida"].read_text()


def test_coleccion_relee_terminal_en_modo_solo_lectura_sin_modelos(interfaz):
    resultado = _invocar(interfaz, "evaluar", "--ejecutar", "--ejecucion", "par-original")
    assert resultado.exit_code == 0, resultado.output
    archivo = interfaz["base"] / interfaz["cfg"]["checkpoints"]
    original = archivo.read_bytes()
    invocaciones, creaciones = len(interfaz["invocaciones"]), len(interfaz["creaciones"])
    salida = interfaz["base"] / "cohorte.json"
    r = interfaz["runner"].invoke(
        interfaz["app"],
        [
            "alineacion",
            "coleccionar",
            "par-original",
            "--salida",
            str(salida),
        ],
    )
    assert r.exit_code == 0, r.output
    datos = json.loads(salida.read_text())
    assert len(datos["casos"]) == 1 and len(datos["casos"][0]["lecturas"]) == 3
    assert datos["casos"][0]["ejecucion_id"] == "par-original"
    assert archivo.read_bytes() == original
    assert len(interfaz["invocaciones"]) == invocaciones and len(interfaz["creaciones"]) == creaciones


@pytest.mark.parametrize("ids", [["../ajeno"], ["duplicado", "duplicado"], ["inexistente"]])
def test_coleccion_no_inventa_ejecuciones_ni_modifica_checkpoints(interfaz, ids):
    r = interfaz["runner"].invoke(
        interfaz["app"],
        [
            "alineacion",
            "coleccionar",
            *ids,
            "--salida",
            str(interfaz["salida"]),
        ],
    )
    assert r.exit_code == 2 and not interfaz["salida"].exists()
    assert not interfaz["invocaciones"] and not interfaz["creaciones"]


@pytest.mark.parametrize("protegido", ["insumos", "data/evaluacion", "data/referencias_2026", "src", "config"])
def test_destino_protegido_rechaza_antes_de_modelo_y_contexto(interfaz, monkeypatch, protegido):
    monkeypatch.setattr(alineacion, "_contexto", lambda _: pytest.fail("No preparar con salida inválida"))
    interfaz["salida"] = interfaz["base"] / protegido / "resultado.json"
    resultado = _invocar(interfaz, "evaluar", "--ejecutar")
    assert resultado.exit_code != 0 and not interfaz["creaciones"]
    assert not interfaz["salida"].exists()


def test_symlink_de_salida_no_puede_reemplazar_fuente(interfaz):
    original = interfaz["base"] / "original.json"
    original.write_text("conservar")
    interfaz["salida"].symlink_to(original)
    resultado = _invocar(interfaz, "evaluar", "--ejecutar")
    assert resultado.exit_code != 0 and original.read_text() == "conservar"
    assert not interfaz["creaciones"]


@pytest.mark.parametrize(
    "opciones",
    [
        ["--ejecucion", "../otro"],
        ["--max-llamadas", "2"],
        ["--max-usd", "0"],
        ["--max-usd", "20.1"],
    ],
)
def test_identidad_y_presupuesto_invalidos_no_llaman_modelos(interfaz, opciones):
    resultado = _invocar(interfaz, "evaluar", "--ejecutar", *opciones)
    assert resultado.exit_code != 0 and not interfaz["creaciones"]


def test_archivos_operativos_tambien_se_validan_antes_del_proveedor(interfaz):
    interfaz["cfg"]["registro"] = "data/evaluacion/registro.sqlite"
    resultado = _invocar(interfaz, "evaluar", "--ejecutar")
    assert resultado.exit_code != 0 and not interfaz["creaciones"]


def test_abstencion_local_no_habilita_modelos_aunque_haya_flag(interfaz, entrada):
    entrada.archivo.write_bytes(b"Fuente mutada")
    resultado = _invocar(interfaz, "evaluar", "--ejecutar")
    assert resultado.exit_code == 2, resultado.output
    datos = json.loads(interfaz["salida"].read_text())
    assert datos["preparacion"]["estado"] == "abstencion" and datos["llamadas"] == 0
    assert not interfaz["creaciones"]


@pytest.mark.parametrize("comando", ["listar-referentes", "validar-referentes"])
def test_referentes_perfilados_son_locales_y_reportan_huella(interfaz, comando):
    resultado = interfaz["runner"].invoke(
        interfaz["app"],
        [
            "alineacion",
            comando,
            "--salida",
            str(interfaz["salida"]),
        ],
    )
    assert resultado.exit_code == 0, resultado.output
    datos = json.loads(interfaz["salida"].read_text())
    assert datos["llamadas"] == 0 and datos["huella_extraccion"] == interfaz["paginas"].huella_extraccion
    if comando == "validar-referentes":
        assert datos["referentes"][0]["evidencias"][0]["contiene_ancla"]
        assert ":PERFIL:" in datos["referentes"][0]["evidencias"][0]["id"]
    assert not interfaz["creaciones"]


@pytest.mark.parametrize("error_interrupcion", [ValueError, KeyboardInterrupt])
def test_interrupcion_persiste_consumo_en_vez_de_cero(interfaz, monkeypatch, error_interrupcion):
    def interrumpir(motor, **kwargs):
        proveedor = motor.modelo
        proveedor.registro.reservar(
            ejecucion=kwargs["ejecucion_id"],
            clave="inconclusa",
            modelo="simulado-a",
            rol="alineador_cientifico",
            reserva_usd=0.001,
            max_llamadas=3,
            max_usd=0.5,
        )
        raise error_interrupcion("Interrupción sintética")

    monkeypatch.setattr("goes_science_kg.motor.ejecuciones.ejecutar_durable", interrumpir)
    resultado = _invocar(interfaz, "evaluar", "--ejecutar", "--ejecucion", "interrumpida")
    assert resultado.exit_code != 0
    datos = json.loads(interfaz["salida"].read_text())
    assert datos["fase"] == "evaluacion_interrumpida" and datos["consumo"]["llamadas"] == 1
    assert Registro(interfaz["base"] / interfaz["cfg"]["registro"]).resumen("interrumpida")["llamadas"] == 1
