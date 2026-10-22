"""Test automatic publication, reviewer failures, and durable spending limits."""

import json
from concurrent.futures import ThreadPoolExecutor

import pytest
from typer.testing import CliRunner

from goes_science_kg.motor.calidad import CRITERIOS, normalizar, validar_dictamenes, validar_propuesta
from goes_science_kg.motor.contratos import (
    Actividad,
    Afirmacion,
    Cita,
    Dictamen,
    Evidencia,
    Propuesta,
    Revision,
    Solicitud,
    huella,
)
from goes_science_kg.motor.flujo import Motor
from goes_science_kg.motor.registro import PresupuestoAgotado, Registro
from goes_science_kg.recuperacion import Buscador, Documento

TEXTO = "Una membrana celular regula el intercambio de sustancias entre la célula y su entorno."


@pytest.fixture
def solicitud():
    return Solicitud(
        consulta="¿Cómo preparar una clase sobre membrana celular?",
        version_curriculo="V4",
        grado=9,
        asignatura="biologia",
    )


@pytest.fixture
def documentos():
    return [
        Documento(
            id="tema-1",
            texto=TEXTO,
            fuente={"documento": "malla", "hoja": "Unidad 1", "fila": 3},
            version="V4",
            grado=9,
            asignatura="biologia",
        )
    ]


def propuesta():
    return Propuesta(
        afirmaciones=[Afirmacion(texto=TEXTO, citas=[Cita(evidencia_id="tema-1", literal=TEXTO)])],
        anclaje_curricular=[Cita(evidencia_id="tema-1", literal=TEXTO)],
        actividad=Actividad(
            objetivo="Explicar el intercambio de sustancias con un modelo",
            pasos=["Dibuja un modelo y explica sus límites"],
            comprobacion="Explica qué cambia si la membrana pierde su función",
            minutos=20,
            recursos=["papel"],
            adaptacion_salvador="Modelo en papel, utilizable sin conexión en El Salvador",
        ),
        limites=["La eficacia de esta actividad propuesta no está medida"],
    )


class ModeloPrueba:
    def __init__(self, *, rechaza=False, falla=None):
        self.llamadas = []
        self.rechaza = rechaza
        self.falla = falla

    def nombre_modelo(self, rol):
        return "modelo-de-prueba"

    def generar(self, *, rol, sistema, mensaje, esquema):
        self.llamadas.append(rol)
        if rol == self.falla:
            raise RuntimeError("proveedor no disponible")
        if rol == "redactor":
            salida = propuesta()
            fragmentos = json.loads(mensaje)["datos_no_confiables"]["fragmentos"]

            def fragmento_id(cita):
                return next(
                    (
                        f["id"]
                        for f in fragmentos
                        if f["evidencia_id"] == cita.evidencia_id
                        and normalizar(cita.literal) in normalizar(f["literal"])
                    ),
                    "fragmento-inexistente",
                )

            return esquema.model_validate(
                {
                    "afirmaciones": [
                        {"texto": a.texto, "fragmentos_ids": [fragmento_id(c) for c in a.citas]}
                        for a in salida.afirmaciones
                    ],
                    "anclaje_curricular": [fragmento_id(c) for c in salida.anclaje_curricular],
                    "actividad": salida.actividad.model_dump(),
                    "limites": salida.limites,
                }
            )
        return Revision(
            aprobado=not self.rechaza,
            errores=["Error científico"] if self.rechaza else [],
            criterios=dict.fromkeys(CRITERIOS[rol], not self.rechaza),
            evidencia_ids=["tema-1"],
        )


class FuentesPrueba:
    """Provide an explicit test-only evidence adapter while production verifies physical sources."""

    def __init__(self, documentos):
        self.documentos = {d.id: d for d in documentos}

    def motivos_bloqueo(self, evidencias):
        return []

    def hidratar(self, documento):
        original = self.documentos[documento.id]
        return Evidencia.crear(
            original.id,
            original.texto,
            original.fuente | {"verificacion": "contenido_fuente"},
            original.version,
        )


def ejecutar(solicitud, documentos, modelo, reparaciones=1):
    motor = Motor(Buscador(documentos), modelo, max_reparaciones=reparaciones, fuentes=FuentesPrueba(documentos))
    return motor.compilar().invoke({"solicitud": solicitud.model_dump(), "ejecucion_id": "prueba"})["resultado"]


def test_no_se_publica_v3_como_v4_ni_se_llama_al_modelo(solicitud, documentos):
    modelo = ModeloPrueba()
    anteriores = [documentos[0].model_copy(update={"version": "V3"})]
    salida = ejecutar(solicitud, anteriores, modelo)
    assert salida["estado"] == "abstencion" and salida["propuesta"] is None
    assert modelo.llamadas == []


def test_cada_propuesta_requiere_tres_jueces_y_citas_primarias(solicitud, documentos):
    modelo = ModeloPrueba()
    salida = ejecutar(solicitud, documentos, modelo)
    assert salida["estado"] == "respaldado_automaticamente"
    assert set(modelo.llamadas) == {"redactor", "cientifico", "psicopedagogo", "adversarial"}
    evidencia = Evidencia.crear("tema-1", TEXTO, {"documento": "derivada", "tipo": "derivada"}, "V4")
    assert validar_propuesta(propuesta(), solicitud, [evidencia])


def test_metadata_autodeclarada_no_sustituye_un_repositorio_de_fuentes(solicitud, documentos):
    documento = documentos[0].model_copy(
        update={"fuente": documentos[0].fuente | {"verificacion": "contenido_fuente", "sha256": "a" * 64}}
    )
    modelo = ModeloPrueba()
    salida = (
        Motor(Buscador([documento]), modelo)
        .compilar()
        .invoke({"solicitud": solicitud.model_dump(), "ejecucion_id": "sin-repositorio"})["resultado"]
    )
    assert salida["estado"] == "abstencion" and salida["propuesta"] is None
    assert modelo.llamadas == []
    assert any("repositorio" in motivo for motivo in salida["motivos"])


@pytest.mark.parametrize("falla", ["cientifico", "psicopedagogo", "adversarial", "redactor"])
def test_fallo_de_cualquier_rol_produce_abstencion(solicitud, documentos, falla):
    salida = ejecutar(solicitud, documentos, ModeloPrueba(falla=falla), reparaciones=0)
    assert salida["estado"] == "abstencion" and salida["propuesta"] is None


def test_desacuerdo_no_se_resuelve_por_mayoria_ni_bucle_infinito(solicitud, documentos):
    modelo = ModeloPrueba(rechaza=True)
    salida = ejecutar(solicitud, documentos, modelo)
    assert salida["estado"] == "abstencion"
    assert modelo.llamadas.count("redactor") == 2
    assert len(modelo.llamadas) == 8


def test_cita_inventada_y_dictamen_de_borrador_anterior_se_rechazan(solicitud):
    evidencia = Evidencia.crear(
        "tema-1", "Un texto diferente que no respalda la afirmación", {"documento": "malla"}, "V4"
    )
    assert validar_propuesta(propuesta(), solicitud, [evidencia])
    dictamenes = [
        Dictamen(
            rol=rol,
            modelo="prueba",
            huella_propuesta=huella({"otro": "borrador"}),
            revision=Revision(
                aprobado=True, errores=[], criterios=dict.fromkeys(criterios, True), evidencia_ids=["tema-1"]
            ),
        )
        for rol, criterios in CRITERIOS.items()
    ]
    assert len(validar_dictamenes(propuesta(), dictamenes, [evidencia])) == 3


def test_presupuesto_persiste_y_es_atomico_entre_hilos(tmp_path):
    archivo = tmp_path / "registro.sqlite"
    registro = Registro(archivo)

    def reservar(_):
        try:
            return registro.reservar(
                ejecucion="x", clave="tarea", modelo="m", rol="juez", reserva_usd=0.1, max_llamadas=3, max_usd=0.25
            )
        except PresupuestoAgotado:
            return None

    with ThreadPoolExecutor(max_workers=8) as pool:
        resultados = list(pool.map(reservar, range(8)))
    assert sum(r is not None for r in resultados) == 2
    assert Registro(archivo).resumen("x")["llamadas"] == 2


def test_cli_v4_ausente_se_abstiene_sin_sdk_cloud(monkeypatch, tmp_path):
    from goes_science_kg.cli.motor import app

    monkeypatch.setattr("goes_science_kg.producto.runtime.ruta", lambda valor: tmp_path / valor)
    monkeypatch.setattr(
        "goes_science_kg.motor.vertex.Vertex.__init__",
        lambda *args, **kwargs: pytest.fail("No debe crear Vertex sin publicación"),
    )
    salida = CliRunner().invoke(
        app, ["responder", "Una clase sobre membranas", "--grado", "9", "--asignatura", "biologia", "--ejecutar"]
    )
    assert salida.exit_code == 2
    assert '"llamadas": 0' in salida.stdout
