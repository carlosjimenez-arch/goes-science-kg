"""Alineación con Excel/PDF temporales y modelos simulados; sin nube ni gold."""

from __future__ import annotations

import hashlib
import json
from io import BytesIO
from types import SimpleNamespace

import openpyxl
import pytest
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from goes_science_kg.curriculo.contratos import (
    FASES,
    CeldaCurricular,
    Curriculo,
    FaseCurricular,
    FilaCurricular,
    FuenteCurricular,
)
from goes_science_kg.ingesta.referencias import FuentePublica, RepositorioReferencias
from goes_science_kg.ingesta.referentes_operativos import ReferenteOperativo
from goes_science_kg.motor.alineacion import ROLES_ALINEACION, MotorAlineacion, SolicitudAlineacion
from goes_science_kg.motor.ejecuciones import ejecutar_durable
from goes_science_kg.motor.fuentes import FuentesVerificadas

OBJETIVO = "Comparar plantas con condiciones de luz distintas y justificar conclusiones con evidencia."
INDICADOR = "Compara los datos y explica la relación entre luz y crecimiento."


def pdf_sintetico(texto):
    escritor = PdfWriter()
    fuente = DictionaryObject({
        NameObject("/Type"): NameObject("/Font"),
        NameObject("/Subtype"): NameObject("/Type1"),
        NameObject("/BaseFont"): NameObject("/Helvetica"),
    })
    pagina = escritor.add_blank_page(width=600, height=800)
    pagina[NameObject("/Resources")] = DictionaryObject({
        NameObject("/Font"): DictionaryObject({NameObject("/F1"): escritor._add_object(fuente)})
    })
    contenido = DecodedStreamObject()
    contenido.set_data(f"BT /F1 12 Tf 50 750 Td ({texto}) Tj ET".encode("ascii"))
    pagina[NameObject("/Contents")] = escritor._add_object(contenido)
    salida = BytesIO()
    escritor.write(salida)
    return salida.getvalue()


class LectorSimulado:
    def __init__(self, *, falla=None, negativo=False, insuficiente=False, ids_falsos=False, invierte=False):
        self.llamadas = []
        self.falla, self.negativo, self.insuficiente = falla, negativo, insuficiente
        self.ids_falsos, self.invierte = ids_falsos, invierte

    def nombre_modelo(self, rol):
        return f"simulado-{rol}"

    def generar(self, *, rol, sistema, mensaje, esquema):
        self.llamadas.append((rol, sistema, mensaje))
        if self.falla == rol:
            raise TimeoutError("Fallo de proveedor simulado")
        datos = json.loads(mensaje)["datos_no_confiables"]
        fuentes = datos["fuentes"]
        local = next(f["id"] for f in datos["fragmentos"] if fuentes[f["evidencia_id"]]["version"] == "V4")
        externo = next(f["id"] for f in datos["fragmentos"] if fuentes[f["evidencia_id"]]["version"] == "referencia")
        valor = "no" if self.negativo else ("insuficiente" if self.insuficiente else "si")
        criterios = dict.fromkeys(esquema.model_fields["criterios"].annotation.model_fields, valor)
        return esquema.model_validate({
            "criterios": criterios,
            "fragmentos_locales": ["F:ajeno" if self.ids_falsos else externo if self.invierte else local],
            "fragmentos_referente": [local if self.invierte else externo],
            "explicacion": "La declaración y el criterio se relacionan en el alcance explícito de la tarea de prueba.",
            "limites": ["El juicio simulado no acredita ejecución ni resultados de aprendizaje"],
        })


@pytest.fixture
def entrada(tmp_path, monkeypatch):
    archivo = tmp_path / "malla.xlsx"
    libro = openpyxl.Workbook()
    hoja = libro.active
    hoja.title = "Unidad 1"
    hoja.append(["Procedimental", "Indicadores de logro"])
    hoja.append([OBJETIVO, INDICADOR])
    libro.save(archivo)
    libro.close()
    sha = hashlib.sha256(archivo.read_bytes()).hexdigest()
    celdas = tuple(CeldaCurricular(
        coordenada=f"{c}2", fila=2, columna=c, campo=campo,
        valor_original=texto, valor=texto, tipo_excel="s",
    ) for c, campo, texto in (("A", "procedimental", OBJETIVO), ("B", "indicadores_logro", INDICADOR)))
    fila = FilaCurricular(
        id="fila-local", fuente_id="malla", version="V4", hoja="Unidad 1", fila=2, grado=6,
        asignatura_malla="Ciencias", unidad="U1", procedimental=OBJETIVO, indicadores_logro=INDICADOR, celdas=celdas,
        fases={f: FaseCurricular(presente_en_hoja=False) for f in FASES},
    )
    fuente = FuenteCurricular(
        id="malla", version="V4", archivo=archivo.name, archivo_local=str(archivo),
        sha256=sha, bytes=archivo.stat().st_size, procedencia={},
    )
    curriculo = Curriculo(
        version="V4", huella="a" * 64, fuentes=(fuente,), filas=(fila,), hojas=(), agrupaciones=(),
    )
    fuentes = FuentesVerificadas({
        "malla": {"archivo_local": archivo.name, "sha256": sha, "version_curriculo": "V4"}
    }, raiz_fuentes=tmp_path)
    texto = "Compare plants under controlled conditions. Use evidence to justify a conclusion."
    contenido = pdf_sintetico(texto)
    monkeypatch.setattr(
        "goes_science_kg.ingesta.referencias.descargar_pdf", lambda f: (contenido, f.url_documento)
    )
    repositorio = RepositorioReferencias(tmp_path / "referencias")
    registro = repositorio.incorporar([FuentePublica(
        id="marco_sintetico", titulo="Fuente primaria sintética", institucion="Institución de prueba",
        version_documental="edicion-2026", url_catalogo="https://www.oecd.org/marco",
        url_documento="https://www.oecd.org/marco.pdf", estado_publicacion="publicado_final",
    )], descargar=True).referencias["marco_sintetico"]
    referente = ReferenteOperativo(
        id="LOCAL:comparar_plantas", marco="Marco sintético", ciclo="2026",
        version_documental=registro.version_documental, fuente=registro.id, sha256=registro.sha256,
        paginas_pdf=(1,), ancla="controlled conditions", descripcion="Comparar condiciones y justificar conclusiones.",
        eje="practica", tipo="competencia", alcance="Alcance exclusivo de una fuente sintética de prueba.",
    )

    def crear(modelo=None, *, max_caracteres=18000, ref=referente):
        return MotorAlineacion(
            curriculo, {ref.id: ref}, fuentes, repositorio, modelo or LectorSimulado(),
            max_caracteres=max_caracteres,
        )

    solicitud = SolicitudAlineacion(fila_id=fila.id, referente_id=referente.id)
    return SimpleNamespace(
        crear=crear, solicitud=solicitud, fuentes=fuentes, repositorio=repositorio,
        archivo=archivo, referente=referente, curriculo=curriculo,
    )


def ejecutar(motor, solicitud):
    return motor.compilar().invoke({
        "solicitud": solicitud.model_dump(), "ejecucion_id": "alineacion-prueba",
    })


def test_dos_fuentes_reales_tres_lecturas_ciegas_y_limite_documental(entrada):
    modelo = LectorSimulado()
    resultado = ejecutar(entrada.crear(modelo), entrada.solicitud)["resultado"]
    assert resultado["estado"] == "respaldo_documental_automatico"
    assert len(modelo.llamadas) == len(resultado["dictamenes"]) == 3
    assert len({x[1] for x in modelo.llamadas}) == 3
    assert len({x[2] for x in modelo.llamadas}) == 1
    assert all("dictamen" not in json.loads(x[2])["datos_no_confiables"] for x in modelo.llamadas)
    assert "desempeño estudiantil" in resultado["limite"]
    assert {e["version"] for e in resultado["evidencias"]} == {"V4", "referencia"}
    assert all(e["fuente"]["verificacion"] == "contenido_fuente" for e in resultado["evidencias"])


@pytest.mark.parametrize("fallo", ["falla", "insuficiente", "ids_falsos", "invierte"])
def test_fallos_o_lectura_inconclusa_no_se_convierten_en_alineacion(entrada, fallo):
    valor = ROLES_ALINEACION[0] if fallo == "falla" else True
    modelo = LectorSimulado(**{fallo: valor})
    salida = ejecutar(entrada.crear(modelo), entrada.solicitud)["resultado"]
    assert salida["estado"] == "abstencion"
    assert len(modelo.llamadas) == 3


def test_tres_lecturas_negativas_no_afirmacion_de_cobertura(entrada):
    salida = ejecutar(entrada.crear(LectorSimulado(negativo=True)), entrada.solicitud)["resultado"]
    assert salida["estado"] == "no_respaldado"


@pytest.mark.parametrize("origen", ["xlsx", "pdf", "version", "ancla", "bloqueo", "presupuesto"])
def test_falta_integridad_o_contexto_abstiene_antes_de_modelos(entrada, origen):
    modelo = LectorSimulado()
    motor = entrada.crear(modelo)
    if origen == "xlsx":
        entrada.archivo.write_bytes(b"Fuente cambiada")
    elif origen == "pdf":
        r = entrada.repositorio.manifiesto().referencias[entrada.referente.fuente]
        (entrada.repositorio.raiz / r.archivo_pdf).write_bytes(b"PDF cambiado")
    elif origen in {"version", "ancla"}:
        cambios = {"version_documental": "edicion-distinta"} if origen == "version" else {"ancla": "Ancla inexistente"}
        motor = entrada.crear(modelo, ref=entrada.referente.model_copy(update=cambios))
    elif origen == "bloqueo":
        entrada.fuentes.bloqueos_curriculares["fila-local"] = "Errata conocida"
    else:
        motor = entrada.crear(modelo, max_caracteres=1000)
    salida = ejecutar(motor, entrada.solicitud)["resultado"]
    assert salida["estado"] == "abstencion" and modelo.llamadas == []


@pytest.mark.parametrize("alteracion", ["criterios", "estado", "cita", "huella", "rol"])
def test_gate_detecta_dictamenes_ajenos_o_incoherentes_tras_checkpoint(entrada, alteracion):
    motor = entrada.crear()
    estado = ejecutar(motor, entrada.solicitud)
    dictamen = estado[ROLES_ALINEACION[0]]["dictamen"]
    if alteracion == "criterios":
        dictamen["criterios"] = {"otro": "si"}
    elif alteracion == "estado":
        dictamen["criterios"]["evidencia_explicita"] = "no"
    elif alteracion == "cita":
        dictamen["citas_referente"][0]["literal"] = "Una cita ajena a los fragmentos registrados"
    elif alteracion == "huella":
        dictamen["huella_tarea"] = "b" * 64
    else:
        dictamen["rol"] = ROLES_ALINEACION[1]
    assert motor._cerrar(estado)["resultado"]["estado"] == "abstencion"


def test_contexto_completo_respeta_presupuesto_y_omite_texto_no_citado(entrada):
    motor = entrada.crear(max_caracteres=7000)
    p = motor.preparar(entrada.solicitud)
    assert p.estado == "preparado", p.motivos
    assert len(json.dumps(motor._datos(p), ensure_ascii=False)) <= 7000
    assert {e.id for e in p.evidencias} == {f.evidencia_id for f in p.fragmentos}


def test_id_desconocido_es_error_de_entrada_sin_modelos(entrada):
    modelo = LectorSimulado()
    with pytest.raises(ValueError, match="catálogo"):
        entrada.crear(modelo).preparar(entrada.solicitud.model_copy(update={"fila_id": "ajena"}))
    assert not modelo.llamadas


def test_reanudar_y_no_reasignar_solicitud_entorno_o_presupuesto(entrada, tmp_path):
    modelo = LectorSimulado()
    motor = entrada.crear(modelo)
    kwargs = dict(
        archivo=tmp_path / "checkpoints.sqlite", solicitud=entrada.solicitud.model_dump(),
        thread_id="sesion-1", ejecucion_id="unidad-presupuesto", huella_entorno=motor.huella_entorno,
    )
    uno = ejecutar_durable(motor, **kwargs)
    dos = ejecutar_durable(motor, **kwargs)
    assert uno["resultado"] == dos["resultado"] and len(modelo.llamadas) == 3
    for campo, nuevo in (
        ("solicitud", {"fila_id": "otra", "referente_id": entrada.referente.id}),
        ("huella_entorno", "entorno-distinto"),
        ("ejecucion_id", "otro-presupuesto"),
    ):
        with pytest.raises(ValueError):
            ejecutar_durable(motor, **(kwargs | {campo: nuevo}))
    assert len(modelo.llamadas) == 3
