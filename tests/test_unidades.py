"""Test unit packages and orchestration with real engine control and offline synthetic providers."""

from __future__ import annotations

import json

import openpyxl
import pytest

from goes_science_kg.curriculo.catalogacion import CatalogoDisciplinas, ClasificacionFila
from goes_science_kg.curriculo.contexto_fuentes import documento_de_fila, fuentes_del_curriculo
from goes_science_kg.curriculo.contratos import (
    FASES,
    CeldaCurricular,
    Curriculo,
    FaseCurricular,
    FilaCurricular,
    FuenteCurricular,
)
from goes_science_kg.motor.calidad import CRITERIOS
from goes_science_kg.motor.flujo import Motor
from goes_science_kg.motor.registro import Registro
from goes_science_kg.motor.vertex import ConfiguracionVertex
from goes_science_kg.producto.consulta_conocimiento import BuscadorProducto
from goes_science_kg.producto.unidades import ContextoAula, ejecutar_unidad, exportar_unidad, preparar_unidad
from goes_science_kg.recuperacion import Buscador, Resultado


@pytest.fixture
def entrega(tmp_path):
    import hashlib

    archivo = tmp_path / "fisica.xlsx"
    libro = openpyxl.Workbook()
    hoja = libro.active
    hoja.title = "Física 10.°"
    encabezados = ["Contenido", "Procedimental", "Indicadores de logro", "Evidencia", "Aproximar"]
    hoja.append(encabezados)
    datos = [
        [
            "Medición",
            "Compara dos mediciones de longitud utilizando una regla de papel.",
            "Justifica la comparación de dos mediciones.",
            "Registra las dos medidas y explica su comparación.",
            "Observa dos medidas dibujadas en una tarjeta.",
        ],
        [
            "Movimiento",
            "Representa dos movimientos sencillos mediante dibujos y observaciones.",
            "Describe una diferencia observable entre los dos movimientos.",
            "Presenta un dibujo y su explicación.",
            "Observa dos dibujos del desplazamiento de un objeto.",
        ],
    ]
    for fila in datos:
        hoja.append(fila)
    libro.save(archivo)
    fuente = FuenteCurricular(
        id="fuente-fisica",
        version="V4",
        archivo=archivo.name,
        archivo_local=archivo.name,
        sha256=hashlib.sha256(archivo.read_bytes()).hexdigest(),
        bytes=archivo.stat().st_size,
        procedencia={"version": "V4"},
    )
    campos = ("contenido", "procedimental", "indicadores_logro", "evidencia_aprendizaje", "fase_aproximar")
    filas = []
    for numero in (2, 3):
        celdas = tuple(
            CeldaCurricular(
                coordenada=c.coordinate,
                fila=numero,
                columna=c.column_letter,
                campo=campo,
                valor_original=c.value,
                valor=c.value,
                tipo_excel=c.data_type,
            )
            for c, campo in zip(hoja[numero], campos, strict=True)
        )
        filas.append(
            FilaCurricular(
                id=f"fila_{numero}",
                fuente_id=fuente.id,
                version="V4",
                hoja=hoja.title,
                fila=numero,
                grado=10,
                asignatura_malla="Física",
                unidad="Unidad de prueba",
                contenido=datos[numero - 2][0],
                procedimental=datos[numero - 2][1],
                indicadores_logro=datos[numero - 2][2],
                evidencia_aprendizaje=datos[numero - 2][3],
                fases={
                    f: FaseCurricular(
                        presente_en_hoja=f == "aproximar", texto=datos[numero - 2][4] if f == "aproximar" else ""
                    )
                    for f in FASES
                },
                celdas=celdas,
            )
        )
    libro.close()
    curriculo = Curriculo(
        version="V4", huella="a" * 64, fuentes=(fuente,), filas=tuple(filas), hojas=(), agrupaciones=()
    )
    catalogo = CatalogoDisciplinas(
        version_curriculo="V4",
        huella_curriculo=curriculo.huella,
        huella_instrucciones="b" * 64,
        huella_harness="c" * 64,
        modelos={"catalogador_a": "simulado-a", "catalogador_b": "simulado-b"},
        modo="completo",
        piloto_superado=True,
        filas=tuple(
            ClasificacionFila(
                fila_id=f.id,
                estado="declarado_malla",
                disciplinas=("fisica",),
                metodo="asignatura_malla",
                justificacion="Asignatura explícita de una fixture",
            )
            for f in filas
        ),
    )
    fuentes = fuentes_del_curriculo(curriculo, raiz_v4=tmp_path)
    return curriculo, catalogo, fuentes, tmp_path


def _preparar(entrega, **opciones):
    curriculo, catalogo, fuentes, _ = entrega
    return preparar_unidad(
        curriculo,
        opciones.pop("catalogo", catalogo),
        grado=10,
        asignatura_malla="Física",
        unidad="Unidad de prueba",
        contexto=opciones.pop("contexto", ContextoAula()),
        fuentes=fuentes,
        **opciones,
    )


class ModeloSinRed:
    def __init__(self, registro, *, ejecucion_id="unidad-prueba", max_llamadas=20):
        self.registro = registro
        self.ejecucion_id = ejecucion_id
        self.otro_objetivo = False
        self.interrumpir = False
        self.configuracion = ConfiguracionVertex(
            proyecto="sin-red",
            modelos={r: f"simulado-{r}" for r in ("redactor", "cientifico", "psicopedagogo", "adversarial")},
            tarifas={},
            max_llamadas=max_llamadas,
            max_usd=1,
            max_salida_tokens=256,
            reintentos=0,
        )

    def nombre_modelo(self, rol):
        return self.configuracion.modelos[rol]

    def generar(self, *, rol, sistema, mensaje, esquema):
        llamada = self.registro.reservar(
            ejecucion=self.ejecucion_id,
            clave=rol,
            modelo=self.nombre_modelo(rol),
            rol=rol,
            reserva_usd=0.001,
            max_llamadas=self.configuracion.max_llamadas,
            max_usd=1,
        )
        if rol == "redactor" and self.interrumpir:
            self.interrumpir = False
            raise KeyboardInterrupt("Interrupción de prueba después de reservar presupuesto")
        datos = json.loads(mensaje)["datos_no_confiables"]
        if rol == "redactor":
            solicitud = json.loads(datos["solicitud"]["consulta"])
            objetivo_id = solicitud["fuente_objetivo"]["fila_id"]
            fragmento = next(
                f
                for f in datos["fragmentos"]
                if (
                    f["evidencia_id"].partition("#CELDA:")[0] != objetivo_id
                    if self.otro_objetivo
                    else f["evidencia_id"].partition("#CELDA:")[0] == objetivo_id
                )
            )
            respuesta = {
                "afirmaciones": [{"texto": fragmento["literal"], "fragmentos_ids": [fragmento["id"]]}],
                "anclaje_curricular": [fragmento["id"]],
                "actividad": {
                    "objetivo": "Explicar el registro mediante una representación de papel",
                    "pasos": ["Representa en papel el objetivo y explica lo que observas"],
                    "comprobacion": "Explica qué representa el dibujo y cuál es su limitación",
                    "minutos": 10,
                    "recursos": ["papel"],
                    "adaptacion_salvador": "Representación en papel disponible sin conexión",
                },
                "limites": ["Propuesta sintética que no demuestra eficacia educativa"],
            }
        else:
            ids = {c["evidencia_id"] for a in datos["propuesta"]["afirmaciones"] for c in a["citas"]}
            ids.update(c["evidencia_id"] for c in datos["propuesta"]["anclaje_curricular"])
            respuesta = {
                "aprobado": True,
                "errores": [],
                "criterios": dict.fromkeys(CRITERIOS[rol], True),
                "evidencia_ids": sorted(ids),
            }
        self.registro.terminar(llamada, estado="completada", latencia_ms=1, entrada_tokens=10, salida_tokens=10)
        return esquema.model_validate(respuesta)


def _motor(entrega, *, max_llamadas=20):
    curriculo, catalogo, fuentes, temporal = entrega
    registro = Registro(temporal / "registro.sqlite")
    modelo = ModeloSinRed(registro, max_llamadas=max_llamadas)
    buscador = Buscador(documento_de_fila(f) for f in curriculo.filas)
    buscador = BuscadorProducto(buscador, curriculo, catalogo, None, fuentes, snapshot_id="fixture-sin-publicar")
    return Motor(buscador, modelo, fuentes=fuentes, max_reparaciones=0), registro


def test_preparacion_conserva_todas_filas_fases_y_contexto_sin_fingir_respaldo(entrega):
    contexto = ContextoAula(
        minutos_por_sesion=25,
        recursos=("papel",),
        conectividad="sin_conexion",
        apoyos=("Representaciones visuales",),
        seguridad=("Supervisión docente",),
    )
    paquete = _preparar(entrega, contexto=contexto)
    assert paquete.estado == "preparado"
    assert paquete.filas == entrega[0].filas and len(paquete.sesiones) == len(paquete.evidencias) == 2
    for sesion in paquete.sesiones:
        assert sesion.solicitud.minutos == 25 and sesion.solicitud.recursos == ("papel",)
        assert json.loads(sesion.solicitud.consulta)["contexto_aula"]["conectividad"] == "sin_conexion"
    assert all(set(f.fases) == set(FASES) for f in paquete.filas)
    assert "normativa" in paquete.limite_organizacion


def test_consulta_excesiva_no_trunca_fuente_y_catalogo_piloto_no_se_ejecuta(entrega):
    largo = _preparar(entrega, contexto=ContextoAula(apoyos=tuple("x" * 300 for _ in range(12))))
    assert all(s.solicitud is None and "2.000" in s.motivos[0] for s in largo.sesiones)
    assert largo.filas == entrega[0].filas
    piloto = _preparar(entrega, catalogo=entrega[1].model_copy(update={"modo": "piloto"}))
    motor, registro = _motor(entrega)
    with pytest.raises(ValueError, match="catálogo completo"):
        ejecutar_unidad(
            piloto,
            motor=motor,
            registro=registro,
            ejecucion_id="unidad-prueba",
            directorio_operaciones=entrega[3] / "operaciones",
        )
    assert registro.resumen("unidad-prueba")["llamadas"] == 0


def test_unidad_ejecuta_motor_real_y_reanuda_terminales_sin_repetir_o_resetear_presupuesto(entrega):
    paquete = _preparar(entrega)
    motor, registro = _motor(entrega)
    primero = ejecutar_unidad(
        paquete,
        motor=motor,
        registro=registro,
        ejecucion_id="unidad-prueba",
        directorio_operaciones=entrega[3] / "operaciones",
    )
    assert primero.cobertura == {
        "filas_totales": 2,
        "sesiones_propuestas": 2,
        "respaldadas": 2,
        "abstenciones": 0,
        "no_ejecutadas": 0,
    }
    assert primero.consumo_despues["llamadas"] == 8
    segundo = ejecutar_unidad(
        paquete,
        motor=motor,
        registro=registro,
        ejecucion_id="unidad-prueba",
        directorio_operaciones=entrega[3] / "operaciones",
    )
    assert segundo.consumo_incremental["llamadas"] == 0
    assert segundo.consumo_despues["llamadas"] == 8
    assert all(s.checkpoint_reutilizado and s.thread_id != "unidad-prueba" for s in segundo.sesiones)
    exportado = exportar_unidad(paquete, entrega[3] / "docente", resultado=segundo)
    assert exportado["estado"] == "preparado" and set(exportado["sha256"]) == {"paquete.json", "paquete.md"}


def test_presupuesto_unico_agotado_no_desaparece_y_cambio_entorno_rechaza_checkpoint(entrega):
    paquete = _preparar(entrega)
    motor, registro = _motor(entrega, max_llamadas=1)
    resultado = ejecutar_unidad(
        paquete,
        motor=motor,
        registro=registro,
        ejecucion_id="unidad-prueba",
        directorio_operaciones=entrega[3] / "operaciones",
    )
    assert resultado.cobertura["respaldadas"] == 0
    assert resultado.cobertura["abstenciones"] == resultado.cobertura["no_ejecutadas"] == 1
    assert registro.resumen("unidad-prueba")["llamadas"] == 1
    motor.max_caracteres += 100
    with pytest.raises(ValueError, match="Cambió el paquete, entorno o ledger"):
        ejecutar_unidad(
            paquete,
            motor=motor,
            registro=registro,
            ejecucion_id="unidad-prueba",
            directorio_operaciones=entrega[3] / "operaciones",
        )


def test_bloqueo_original_no_omite_fila_y_exportacion_no_sigue_enlaces(entrega):
    entrega[2].bloqueos_curriculares = {"fila_2": "Alerta científica confirmada de prueba"}
    paquete = _preparar(entrega)
    assert len(paquete.filas) == 2 and paquete.sesiones[0].solicitud is None
    assert any(a.estado == "bloqueo_cientifico" for a in paquete.alertas)
    base = entrega[3] / "exportacion"
    base.mkdir()
    protegido = entrega[3] / "conservar.json"
    protegido.write_text("conservar")
    (base / "paquete.json").symlink_to(protegido)
    with pytest.raises(ValueError, match="enlace"):
        exportar_unidad(paquete, base)
    assert protegido.read_text() == "conservar"


def test_respaldo_sobre_otra_fila_se_exporta_como_abstencion_del_objetivo(entrega, monkeypatch):
    paquete = _preparar(entrega)
    motor, registro = _motor(entrega)
    motor.modelo.otro_objetivo = True
    # Un puerto defectuoso entrega dos filas: el cierre de unidad sigue rechazando el anclaje ajeno.
    monkeypatch.setattr(
        motor.buscador,
        "buscar_fila",
        lambda *args, **kwargs: [
            Resultado(documento=d, puntaje=1, canales=("puerto_contaminado",))
            for d in motor.buscador.documentos.values()
        ],
    )
    resultado = ejecutar_unidad(
        paquete,
        motor=motor,
        registro=registro,
        ejecucion_id="unidad-prueba",
        directorio_operaciones=entrega[3] / "operaciones",
    )
    assert resultado.cobertura["respaldadas"] == 0 and resultado.cobertura["abstenciones"] == 2
    assert all(s.resultado_motor.estado == "abstencion" for s in resultado.sesiones)
    assert all("fila objetivo exacta" in s.motivos[-1] for s in resultado.sesiones)
    assert {d["rol"] for d in resultado.consumo_despues["detalle"]} == {"redactor"}
    exportar_unidad(paquete, entrega[3] / "docente", resultado=resultado)
    assert "Propuesta automática con revisiones" not in (entrega[3] / "docente/paquete.md").read_text()


def test_unidad_rechaza_resultado_ajeno_si_un_ejecutor_defectuoso_pierde_ambito(entrega, monkeypatch):
    from goes_science_kg.producto import unidades

    paquete = _preparar(entrega)
    motor, registro = _motor(entrega)
    motor.modelo.otro_objetivo = True
    ejecutar_original = unidades.ejecutar_durable

    def ejecutor_defectuoso(motor, **kwargs):
        # Simula un proveedor de workflow que pierde la restricción tipada; la unidad mantiene su propio veto.
        kwargs["solicitud"] = kwargs["solicitud"] | {"fila_id": None}
        return ejecutar_original(motor, **kwargs)

    monkeypatch.setattr(unidades, "ejecutar_durable", ejecutor_defectuoso)
    resultado = ejecutar_unidad(
        paquete,
        motor=motor,
        registro=registro,
        ejecucion_id="unidad-prueba",
        directorio_operaciones=entrega[3] / "operaciones",
    )
    assert resultado.cobertura["respaldadas"] == 0
    assert all(s.resultado_motor.estado == "respaldado_automaticamente" for s in resultado.sesiones)
    assert all("fila objetivo exacta" in s.motivos[-1] for s in resultado.sesiones)


def test_interrupcion_reanuda_checkpoint_y_reserva_previa_sigue_contando(entrega):
    paquete = _preparar(entrega)
    motor, registro = _motor(entrega)
    motor.modelo.interrumpir = True
    with pytest.raises(KeyboardInterrupt):
        ejecutar_unidad(
            paquete,
            motor=motor,
            registro=registro,
            ejecucion_id="unidad-prueba",
            directorio_operaciones=entrega[3] / "operaciones",
        )
    assert registro.resumen("unidad-prueba")["llamadas"] == 1
    resultado = ejecutar_unidad(
        paquete,
        motor=motor,
        registro=registro,
        ejecucion_id="unidad-prueba",
        directorio_operaciones=entrega[3] / "operaciones",
    )
    assert resultado.cobertura["respaldadas"] == 2
    assert resultado.sesiones[0].checkpoint_reutilizado
    assert resultado.consumo_antes["llamadas"] == 1 and resultado.consumo_despues["llamadas"] == 9


def test_checkpoint_no_sigue_enlace_ni_cambia_el_id_de_presupuesto(entrega):
    paquete = _preparar(entrega)
    motor, registro = _motor(entrega)
    with pytest.raises(ValueError, match="mismo Registro e ID"):
        ejecutar_unidad(
            paquete,
            motor=motor,
            registro=registro,
            ejecucion_id="otro-presupuesto",
            directorio_operaciones=entrega[3] / "operaciones",
        )
    base = entrega[3] / "operaciones"
    base.mkdir()
    protegido = entrega[3] / "protegido.sqlite"
    protegido.write_text("conservar")
    (base / "checkpoints_unidades.sqlite").symlink_to(protegido)
    with pytest.raises(ValueError, match="enlace"):
        ejecutar_unidad(
            paquete, motor=motor, registro=registro, ejecucion_id="unidad-prueba", directorio_operaciones=base
        )
    assert protegido.read_text() == "conservar"
