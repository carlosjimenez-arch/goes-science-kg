"""Un falso positivo se corrige con evidencia y otro texto; se conserva el respaldo anterior."""

from types import SimpleNamespace

import pytest
from test_mejoras_curriculares import ModeloPrueba
from test_mejoras_curriculares import caso as caso

from goes_science_kg.motor.contratos import Evidencia, huella
from goes_science_kg.producto.mejoras_publicadas import CasoMejora
from goes_science_kg.producto.rectificacion_mejoras import MotorRectificacion, PreparadorRectificacion
from goes_science_kg.producto.validacion_mejoras import resolver_mejora


def test_rectificacion_requiere_un_texto_distinto_y_cuatro_votos_nuevos(caso):
    p, b, modelos, ronda = caso
    resultado = resolver_mejora(p, (ronda,), ejecucion_id="x", modelos=modelos)
    anterior = CasoMejora(preparacion=p, resultado=resultado, entorno="a" * 64, plan_id="b" * 64)
    nuevo = b.model_copy(update={"sintesis": "Otra propuesta que corrige el falso positivo documentado."})
    modelo = ModeloPrueba(nuevo)
    motor = MotorRectificacion(SimpleNamespace(preparar=lambda s: p, validar=lambda p: None), modelo, anterior)
    estado = motor.compilar().invoke({"solicitud": p.solicitud.model_dump(), "ejecucion_id": "x"})
    assert estado["resultado"]["estado"] == "respaldado_automaticamente"
    assert len(modelo.llamadas) == 5 and anterior.resultado.propuesta == b


def test_enmienda_relee_ancla_y_registra_definicion_primaria(caso, monkeypatch, tmp_path):
    p = caso[0]
    solicitud = p.solicitud.model_copy(
        update={"grado": 11, "asignatura_malla": "Biología", "unidad": "5. Biotecnología microbiana"}
    )
    p = p.model_copy(update={"solicitud": solicitud})
    monkeypatch.setattr("goes_science_kg.producto.preparacion_mejoras.PreparadorMejoras.preparar", lambda self, s: p)
    monkeypatch.setattr("goes_science_kg.producto.rectificacion_mejoras.documento_de_fila", lambda f: None)
    texto = "Representa en un diagrama la siembra por estría de levadura o de yogur diluido en agar."
    celda = Evidencia.crear(
        "fila1#CELDA:K41",
        texto,
        {
            "documento": "sintetica",
            "sha256": "a" * 64,
            "celdas_verificadas": [{"coordenada_origen": "K41"}],
            "verificacion": "contenido_fuente",
        },
        "V4",
    )
    fuente = Evidencia.crear(
        "definicion",
        "Fungi are eukaryotes and have a complex cellular organization including a membrane-bound nucleus.\n"
        "Unicellular fungi are called yeasts and are distinct from prokaryotic bacteria "
        "in their cellular organization.",
        {"documento": "sintetica", "verificacion": "contenido_fuente"},
        "referencia",
    )
    monkeypatch.setattr(
        "goes_science_kg.producto.rectificacion_mejoras.RepositorioWeb.evidencia", lambda self, id_: fuente
    )
    from pathlib import Path

    (tmp_path / "config").mkdir()
    (tmp_path / "config/bioseguridad_escolar_2026.yaml").write_text(
        Path("config/bioseguridad_escolar_2026.yaml").read_text()
    )

    def fuentes_simuladas(catalogo, *, raiz_fuentes, raices_adicionales):
        return SimpleNamespace(
            hidratar=lambda d: Evidencia.crear(
                d.id,
                "Texto primario sintético sobre condiciones de bioseguridad en el aula escolar.",
                {"documento": next(iter(catalogo)), "verificacion": "contenido_fuente", "pagina": d.fuente["pagina"]},
                "referencia",
            )
        )

    monkeypatch.setattr("goes_science_kg.producto.rectificacion_mejoras.FuentesVerificadas", fuentes_simuladas)
    preparador = PreparadorRectificacion.__new__(PreparadorRectificacion)
    preparador.raiz = tmp_path
    preparador.max_caracteres = 220000
    preparador.runtime = SimpleNamespace(
        producto=SimpleNamespace(
            curriculo=SimpleNamespace(
                filas=(
                    SimpleNamespace(
                        id="fila1", procedimental="5.3. Cultivo bacteriano.", fuente_id="fuente", hoja="Biología"
                    ),
                )
            )
        ),
        fuentes=SimpleNamespace(hidratar_celdas=lambda d: (celda,)),
    )
    actual = preparador.preparar(solicitud)
    e = actual.correcciones_requeridas[0]
    assert e["antes"] == texto and "cepa bacteriana identificada" in e["despues"]
    assert e["id"] == "ENMIENDA:" + huella({k: v for k, v in e.items() if k != "id"})
    assert actual.filas_originales == p.filas_originales and "fila1" in actual.alertas
    assert actual == preparador.preparar(solicitud)
    preparador.runtime.fuentes.hidratar_celdas = lambda d: (
        celda.model_copy(update={"texto": "La celda fue cambiada."}),
    )
    with pytest.raises(ValueError, match="exacto"):
        preparador.preparar(solicitud)
