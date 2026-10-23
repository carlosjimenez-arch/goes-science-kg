"""Guiones: tiempos, aritmética segura, votos ciegos, reparación selectiva y checkpoint durable."""

from __future__ import annotations

from copy import deepcopy
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from goes_science_kg.clases.contratos import CRITERIOS, ROLES, BorradorClases, GuionClase, LecturaClases
from goes_science_kg.clases.fuentes import extraer
from goes_science_kg.clases.motor import MotorClases
from goes_science_kg.clases.validacion import calcular, validar_borrador
from goes_science_kg.motor.contratos import Evidencia, huella
from goes_science_kg.motor.ejecuciones import ejecutar_durable


def guion(id_="fila1"):
    criterio = {
        "criterio": "Clasifica y justifica su observación con dos propiedades.",
        "logrado": "Clasifica los dos casos y explica las dos propiedades observables.",
        "en_proceso": "Clasifica un caso y explica una propiedad observable.",
        "requiere_apoyo": "Requiere una tabla de apoyo para reconocer las propiedades.",
    }
    tarea = {
        "enunciado": "Describe dos materiales representados en el papel y explica cómo los clasificarías.",
        "respuesta_esperada": "Agrupa según dos propiedades observables y explica el criterio elegido.",
        "explicacion_solucion": "Dos materiales pueden compartir una propiedad y diferir en otra.",
        "rubrica": [
            criterio,
            criterio | {"criterio": "Explica por qué su criterio permite comprobar la clasificación."},
        ],
        "calculos": [],
        "datos_simulados": False,
    }
    return GuionClase(
        fila_id=id_,
        titulo="Comparar materiales cotidianos con criterios observables",
        objetivo="Comparar materiales cotidianos y explicar sus propiedades.",
        conocimientos_a_activar=("Describir el aspecto de objetos cotidianos.",),
        explicacion_docente=[
            {"texto": "Los materiales pueden compararse por sus propiedades observables.", "fuentes_ids": ["e1"]},
            {"texto": "Una clasificación utiliza un criterio explícito y comprobable.", "fuentes_ids": ["e1"]},
        ],
        sesiones=[
            {
                "numero": 1,
                "titulo": "Observación y clasificación de representaciones",
                "bloques": [
                    {
                        "fase": f,
                        "minutos": 12,
                        "docente": "Muestra dibujos de dos materiales y pide describir sus propiedades.",
                        "estudiantes": "Describen dos propiedades en una tabla y justifican la clasificación.",
                        "evidencia_observable": "Tabla con dos propiedades observables y una explicación.",
                    }
                    for f in ("aproximar", "explorar", "explicar", "indagar", "reforzar")
                ],
            }
        ],
        tareas=[
            tarea,
            tarea | {"enunciado": "Clasifica un tercer material representado y justifica el criterio aplicado."},
        ],
        recursos=("papel", "lapiz"),
        alternativa_sin_recursos="Los materiales se representan con dibujos que la docente describe también oralmente.",
        apoyos=("Ofrecer un banco de palabras dibujadas.", "Permitir una explicación oral de las diferencias."),
        dificultad_previsible="Confundir la propiedad con la utilidad del material.",
        retroalimentacion="Pide que señale qué puede comprobar en el dibujo y revise su criterio.",
        seguridad="Se trabaja con dibujos, sin manipular sustancias ni objetos cortantes.",
        implementacion_condicionada="Escenario hipotético de una sesión de sesenta minutos con papel y lápiz.",
    )


@pytest.fixture
def preparacion():
    e = Evidencia.crear(
        "e1",
        "Materials have observable properties useful for classification.",
        {"documento": "doc", "tipo": "documental", "fuente_primaria": True},
        "referencia",
    )
    p = {
        "version": "preparacion-clases-1",
        "snapshot_id": "s",
        "corpus_sha256": "a" * 64,
        "escenario": {"minutos_por_sesion_propuesta": 60},
        "filas": [
            {
                "fila_id": id_,
                "grado": 3,
                "propuesta": {"objetivo_propuesto": guion().objetivo},
                "fuentes_cientificas_ids": ["e1"],
            }
            for id_ in ("fila1", "fila2")
        ],
        "fuentes": [e.model_dump(mode="json")],
    }
    p["id"] = huella(p)
    return p


@pytest.mark.parametrize("expresion,esperado", [("2+3*4", 14), ("(8-2)/3", 2), ("sqrt(9)", 3), ("2**3", 8)])
def test_aritmetica_acotada(expresion, esperado):
    assert calcular(expresion) == esperado


@pytest.mark.parametrize("expresion", ["__import__('os')", "(1).__class__", "2**100000", "sqrt(9,x=2)", "1/0", "1e101"])
def test_rechaza_ejecucion_y_operaciones_fuera_de_limites(expresion):
    with pytest.raises((ValueError, ZeroDivisionError)):
        calcular(expresion)


def test_tiempo_fuentes_y_objetivo_se_comprueban(preparacion):
    dato = guion().model_dump(mode="json")
    dato["sesiones"][0]["bloques"][0]["minutos"] = 1
    with pytest.raises(ValidationError, match="60"):
        GuionClase.model_validate(dato)
    dato = guion().model_dump(mode="json")
    dato["explicacion_docente"][0]["fuentes_ids"] = ["inventada"]
    b = BorradorClases(guiones=(GuionClase.model_validate(dato), guion("fila2")))
    assert "fuente ajena" in str(validar_borrador(b, preparacion))


def test_cnxml_conserva_mathml_y_rechaza_entidades():
    raw = (
        b'<document xmlns="http://cnx.rice.edu/cnxml"><title>Prueba</title><content><para id="p1">'
        + (
            b"This complete scientific paragraph has enough information "
            b"to retrieve and verify a physical expression. "
            b'<math xmlns="http://www.w3.org/1998/Math/MathML"><mi>F</mi><mo>=</mo><mi>ma</mi></math>'
        )
        + b"</para></content></document>"
    )
    titulo, bloques = extraer(raw)
    assert titulo == "Prueba" and bloques[0][0] == "p1"
    assert "MathML" in bloques[0][1] and "<ns0:mi>" in bloques[0][1]
    with pytest.raises(ValueError, match="entidades"):
        extraer(b'<!ENTITY x SYSTEM "file:///etc/passwd">')


class ProveedorGuion:
    ejecucion_id = "prueba"

    def __init__(self, veto=False):
        self.veto = veto
        self.llamadas = []
        self.redacciones = 0

    def nombre_modelo(self, rol):
        return "modelo-prueba"

    def generar(self, *, rol, sistema, mensaje, esquema):
        import json

        d = json.loads(mensaje)
        self.llamadas.append((rol, deepcopy(d)))
        if rol == "clases_redactor":
            self.redacciones += 1
            gs = [guion(f["fila_id"]) for f in d["filas"]]
            if self.redacciones > 1:
                gs = [
                    g.model_copy(
                        update={
                            "titulo": g.titulo + " corregido",
                            "retroalimentacion": "Pide comprobar con dos ejemplos el segundo criterio observado.",
                        }
                    )
                    for g in gs
                ]
            return BorradorClases(guiones=gs)
        filas = []
        for g in d["guiones"]:
            falla = self.veto and rol == "clases_ciencia" and g["fila_id"] == "fila2" and self.redacciones == 1
            filas.append(
                {
                    "fila_id": g["fila_id"],
                    "criterios": dict.fromkeys(CRITERIOS[rol], "no" if falla else "si"),
                    "hallazgos": ["Falta precisar el segundo criterio para que sea comprobable."] if falla else [],
                    "fuentes_ids": ["e1"],
                }
            )
        return LecturaClases(filas=filas)


def test_cuatro_lecturas_ciegas_y_reparacion_solo_de_la_fila_vetada(preparacion, tmp_path):
    proveedor = ProveedorGuion(veto=True)
    corpus = SimpleNamespace(huella="a" * 64, verificar=lambda e: None)
    motor = MotorClases(proveedor, corpus)
    kwargs = dict(
        archivo=tmp_path / "checkpoint.sqlite",
        solicitud=preparacion,
        thread_id="guiones",
        ejecucion_id="prueba",
        huella_entorno="b" * 64,
    )
    resultado = ejecutar_durable(motor, **kwargs)["resultado"]
    assert resultado["estado"] == "respaldado_automaticamente"
    assert len(resultado["rondas"]) == 2
    assert resultado["filas"]["fila1"]["ronda_seleccionada"] == 1
    assert resultado["filas"]["fila2"]["ronda_seleccionada"] == 2
    assert len(proveedor.llamadas) == 10
    segunda = proveedor.llamadas[5][1]
    assert [f["fila_id"] for f in segunda["filas"]] == ["fila2"]
    assert "hallazgos_a_corregir" in segunda
    for rol, mensaje in proveedor.llamadas:
        if rol in ROLES:
            assert "hallazgos_a_corregir" not in mensaje
            assert "lectores" not in mensaje
    assert ejecutar_durable(motor, **kwargs)["resultado"] == resultado
    assert len(proveedor.llamadas) == 10


def test_objetivo_o_fuentes_modificadas_no_reutilizan_checkpoint(preparacion, tmp_path):
    motor = MotorClases(ProveedorGuion(), SimpleNamespace(huella="a" * 64, verificar=lambda e: None))
    kwargs = dict(
        archivo=tmp_path / "checkpoint.sqlite",
        solicitud=preparacion,
        thread_id="mismo",
        ejecucion_id="prueba",
        huella_entorno="b" * 64,
    )
    ejecutar_durable(motor, **kwargs)
    with pytest.raises(ValueError, match="Cambió"):
        ejecutar_durable(motor, **(kwargs | {"huella_entorno": "c" * 64}))
    distinto = deepcopy(preparacion)
    distinto["escenario"]["minutos_por_sesion_propuesta"] = 40
    with pytest.raises(ValueError, match="otra solicitud"):
        ejecutar_durable(motor, **(kwargs | {"solicitud": distinto}))


def test_esquema_compacto_conserva_validadores_de_contenido():
    import json

    from goes_science_kg.clases.contratos import esquema_transporte

    transporte = esquema_transporte(BorradorClases)
    esquema = json.dumps(transporte.model_json_schema())
    assert '"maxLength"' not in esquema and '"minItems"' not in esquema
    assert '"additionalProperties": false' in esquema and '"required"' in esquema
    dato = {"guiones": [guion().model_dump(mode="json")]}
    assert transporte.model_validate(dato).guiones[0] == guion()
    dato["guiones"][0]["tareas"][0]["respuesta_esperada"] = "x" * 2001
    with pytest.raises(ValidationError, match="2000"):
        transporte.model_validate_json(json.dumps(dato))


def material_clase():
    return {
        "id": "clase-prueba",
        "tipo": "guion_clase",
        "version_curriculo": "V4",
        "titulo": guion().titulo,
        "grados": [3],
        "asignatura": "Ciencias",
        "unidad": "Materia",
        "fila_id": "fila1",
        "estado": "respaldado_automaticamente",
        "documento": {
            "guion": guion().model_dump(mode="json"),
            "fuentes_cientificas": [],
            "licencia_adaptacion": "Licencia y atribución de la adaptación de prueba.",
            "snapshot_id": "s",
            "preparacion_id": "p",
            "origen": {},
            "alerta_original": {},
            "enmiendas": [],
            "dictamenes": [],
        },
    }


def test_hoja_estudiante_no_revela_solucionario():
    from goes_science_kg.clases.lectura import markdown_clase

    r = material_clase()
    hoja = markdown_clase(r, estudiante=True)
    docente = markdown_clase(r)
    assert r["documento"]["guion"]["tareas"][0]["enunciado"] in hoja
    assert r["documento"]["guion"]["tareas"][0]["respuesta_esperada"] not in hoja
    assert "Solucionario" in docente and "Solucionario" not in hoja
    assert "aprobación institucional" in docente


def test_zip_reproducible_restaurable_y_sin_rutas_peligrosas(tmp_path):
    import zipfile

    from goes_science_kg.clases.paquete import construir, extraer, validar

    uno, dos = tmp_path / "uno.zip", tmp_path / "dos.zip"
    m = construir([material_clase()], {"prueba.txt": b"fuente"}, uno, procedencia={"snapshot_id": "s"})
    construir([material_clase()], {"prueba.txt": b"fuente"}, dos, procedencia={"snapshot_id": "s"})
    assert uno.read_bytes() == dos.read_bytes()
    destino = tmp_path / "restaurado"
    assert extraer(uno, destino) == m
    assert (destino / "fuentes/prueba.txt").read_bytes() == b"fuente"
    with pytest.raises(ValueError, match="nuevo"):
        extraer(uno, destino)
    roto = tmp_path / "roto.zip"
    with zipfile.ZipFile(uno) as origen, zipfile.ZipFile(roto, "w") as salida:
        for n in origen.namelist():
            salida.writestr(n, b"alterado" if n == "fuentes/prueba.txt" else origen.read(n))
    with pytest.raises(ValueError, match="manifest"):
        validar(roto)
    peligroso = tmp_path / "peligroso.zip"
    with zipfile.ZipFile(peligroso, "w") as z:
        z.writestr("../escape.txt", b"no")
    with pytest.raises(ValueError, match="Ruta"):
        validar(peligroso)


@pytest.mark.parametrize(
    "expresion,resultado,ok",
    [
        ("0.1+0.2", 0.3, True),
        ("6.626e-34*2", 1.3252e-33, True),
        ("6.626e-34*2", 0, False),
        ("4*pi*pi", 39.4, False),
        ("round(4*pi*pi,2)", 39.48, True),
    ],
)
def test_tolerancia_no_oculta_errores_de_magnitud(preparacion, expresion, resultado, ok):
    d = guion().model_dump(mode="json")
    d["tareas"][0]["calculos"] = [
        {
            "expresion": expresion,
            "resultado": resultado,
            "tolerancia": 0.01,
            "tolerancia_relativa": 0.01,
            "unidad": "unidad de prueba",
        }
    ]
    b = BorradorClases(guiones=(GuionClase.model_validate(d), guion("fila2")))
    assert (not validar_borrador(b, preparacion)) == ok


def test_fallo_de_una_fila_no_elimina_la_otra_y_no_reconstruye_json_truncado(preparacion):
    import json

    from goes_science_kg.clases.validacion import recuperar_validos

    mal = guion("fila2").model_dump(mode="json")
    mal["tareas"][0]["respuesta_esperada"] = "x" * 2001
    texto = json.dumps({"guiones": [guion().model_dump(mode="json"), mal]})
    b, errores = recuperar_validos(texto, preparacion, ["fila1", "fila2"])
    assert [g.fila_id for g in b.guiones] == ["fila1"]
    assert set(errores) == {"fila2"} and "2000" in str(errores)
    with pytest.raises(ValueError):
        recuperar_validos(texto[:-10], preparacion, ["fila1", "fila2"])
    with pytest.raises(ValueError, match="identidades"):
        recuperar_validos(texto, preparacion, ["fila1"])


@pytest.mark.parametrize("alteracion", ["guion", "voto", "terminal"])
def test_no_se_puede_promover_un_respaldo_manipulado(preparacion, tmp_path, alteracion):
    from goes_science_kg.clases.validacion import certificar_resultado

    motor = MotorClases(ProveedorGuion(), SimpleNamespace(huella="a" * 64, verificar=lambda e: None))
    r = ejecutar_durable(
        motor,
        archivo=tmp_path / "cp.sqlite",
        solicitud=preparacion,
        thread_id="x",
        ejecucion_id="prueba",
        huella_entorno="b" * 64,
    )["resultado"]
    certificar_resultado(r, preparacion)
    if alteracion == "guion":
        r["filas"]["fila1"]["guion"]["titulo"] += " CAMBIADO"
    elif alteracion == "voto":
        r["rondas"][0]["lectores"][ROLES[0]]["lectura"]["filas"][0]["criterios"]["ciencia_correcta"] = "no"
    else:
        r["filas"]["fila1"]["dictamenes"].pop()
    with pytest.raises(ValueError):
        certificar_resultado(r, preparacion)


def test_reparacion_identica_no_recibe_otra_ronda_de_votos(preparacion, tmp_path):
    class SinCambios(ProveedorGuion):
        def generar(self, **kwargs):
            r = super().generar(**kwargs)
            if kwargs["rol"] == "clases_redactor" and self.redacciones > 1:
                return BorradorClases(guiones=[guion(g.fila_id) for g in r.guiones])
            return r

    proveedor = SinCambios(veto=True)
    motor = MotorClases(proveedor, SimpleNamespace(huella="a" * 64, verificar=lambda e: None))
    r = ejecutar_durable(
        motor,
        archivo=tmp_path / "cp.sqlite",
        solicitud=preparacion,
        thread_id="x",
        ejecucion_id="prueba",
        huella_entorno="b" * 64,
    )["resultado"]
    assert r["filas"]["fila1"]["estado"] == "respaldado_automaticamente"
    assert r["filas"]["fila2"]["estado"] == "abstencion"
    assert len(proveedor.llamadas) == 6  # Dos redactores, cuatro revisiones; no cuatro revotos adicionales.


def test_motor_recupera_fila_valida_y_repara_solo_la_invalida(preparacion, tmp_path):
    import json

    from goes_science_kg.clases.validacion import certificar_resultado
    from goes_science_kg.motor.vertex import _validar_salida

    class Parcial(ProveedorGuion):
        def generar(self, **kwargs):
            r = super().generar(**kwargs)
            if kwargs["rol"] == "clases_redactor" and self.redacciones == 1:
                d = r.model_dump(mode="json")
                d["guiones"][1]["tareas"][0]["respuesta_esperada"] = "x" * 2001
                return _validar_salida(kwargs["esquema"], json.dumps(d))
            return r

    proveedor = Parcial()
    motor = MotorClases(proveedor, SimpleNamespace(huella="a" * 64, verificar=lambda e: None))
    r = ejecutar_durable(
        motor,
        archivo=tmp_path / "cp.sqlite",
        solicitud=preparacion,
        thread_id="x",
        ejecucion_id="prueba",
        huella_entorno="b" * 64,
    )["resultado"]
    certificar_resultado(r, preparacion)
    assert r["estado"] == "respaldado_automaticamente"
    assert r["filas"]["fila1"]["ronda_seleccionada"] == 1
    assert r["rondas"][0]["respuesta_rechazada"]
    lectores = [m for rol, m in proveedor.llamadas if rol in ROLES]
    assert all([g["fila_id"] for g in m["guiones"]] in (["fila1"], ["fila2"]) for m in lectores)


def test_editor_consume_segunda_ronda_y_requiere_cuatro_lecturas_del_guion_editado(preparacion, tmp_path):
    import json

    from goes_science_kg.clases.edicion import EdicionesClases
    from goes_science_kg.clases.validacion import certificar_resultado
    from goes_science_kg.motor.vertex import _validar_salida

    class ConEditor(ProveedorGuion):
        ediciones = 0

        def generar(self, **kwargs):
            r = super().generar(**kwargs)
            if kwargs["rol"] == "clases_redactor" and self.redacciones == 1:
                d = r.model_dump(mode="json")
                d["guiones"][1]["tareas"][0]["enunciado"] = "Texto repetido innecesariamente. " * 70
                return _validar_salida(kwargs["esquema"], json.dumps(d))
            return r

        def editar_formato(self, solicitud):
            self.ediciones += 1
            assert [f["fila_id"] for f in solicitud["filas"]] == ["fila2"]
            return EdicionesClases.model_validate(
                {
                    "cambios": [
                        {
                            "fila_id": "fila2",
                            "tarea": 0,
                            "campo": "enunciado",
                            "texto": guion("fila2").tareas[0].enunciado,
                        }
                    ]
                }
            )

    proveedor = ConEditor()
    r = ejecutar_durable(
        MotorClases(proveedor, SimpleNamespace(huella="a" * 64, verificar=lambda e: None)),
        archivo=tmp_path / "cp.sqlite",
        solicitud=preparacion,
        thread_id="edicion",
        ejecucion_id="prueba",
        huella_entorno="b" * 64,
    )["resultado"]
    certificar_resultado(r, preparacion)
    assert r["estado"] == "respaldado_automaticamente"
    assert proveedor.redacciones == 1 and proveedor.ediciones == 1
    assert len(proveedor.llamadas) == 9  # Un redactor y ocho lectores; el editor del doble no invoca proveedor.
    assert r["rondas"][1]["tipo"] == "edicion_formato"
    assert "Texto repetido" in r["rondas"][0]["respuesta_rechazada"]
    assert "Comprobación interna" not in json.dumps(r["filas"])
    adulterado = deepcopy(r)
    adulterado["rondas"][1]["borrador"]["guiones"][0]["seguridad"] += " CAMBIADA"
    with pytest.raises(ValueError, match="campos ajenos"):
        certificar_resultado(adulterado, preparacion)


def test_editor_solo_admite_longitud_y_campos_exactos():
    import json

    from goes_science_kg.clases.edicion import aplicar_ediciones, preparar_edicion

    original = guion().model_dump(mode="json")
    original["tareas"][0]["enunciado"] = "Texto largo de la consigna. " * 80
    raw = json.dumps({"guiones": [original]})
    solicitud = preparar_edicion(raw, ["fila1"], ["fila1"])
    assert solicitud and original["tareas"][0]["enunciado"] in json.dumps(solicitud)
    cambio = {"fila_id": "fila1", "tarea": 0, "campo": "enunciado", "texto": guion().tareas[0].enunciado}
    nuevo = aplicar_ediciones(solicitud, {"cambios": [cambio]}).guiones[0].model_dump(mode="json")
    assert nuevo["seguridad"] == original["seguridad"] and nuevo["objetivo"] == original["objetivo"]
    with pytest.raises(ValueError, match="exactamente los campos"):
        aplicar_ediciones(solicitud, {"cambios": [cambio, cambio]})
    with pytest.raises(ValueError):
        aplicar_ediciones(solicitud, {"cambios": [cambio | {"campo": "seguridad"}]})
    original["sesiones"][0]["bloques"][0]["minutos"] = 1
    assert preparar_edicion(json.dumps({"guiones": [original]}), ["fila1"], ["fila1"]) is None
    assert preparar_edicion(raw[:-2], ["fila1"], ["fila1"]) is None


def test_error_400_detiene_sin_gastar_reparacion(preparacion, tmp_path):
    class ErrorConfiguracion(RuntimeError):
        code = 400

    class MalConfigurado(ProveedorGuion):
        def generar(self, **kwargs):
            self.llamadas.append(kwargs["rol"])
            raise ErrorConfiguracion("Solicitud inválida")

    proveedor = MalConfigurado()
    motor = MotorClases(proveedor, SimpleNamespace(huella="a" * 64, verificar=lambda e: None))
    with pytest.raises(ErrorConfiguracion):
        ejecutar_durable(
            motor,
            archivo=tmp_path / "cp.sqlite",
            solicitud=preparacion,
            thread_id="x",
            ejecucion_id="prueba",
            huella_entorno="b" * 64,
        )
    assert proveedor.llamadas == ["clases_redactor"]


def test_presupuesto_conserva_prefijo_y_rechaza_reset_o_modificacion(tmp_path):
    from goes_science_kg.clases.presupuesto import comprobar_continuidad
    from goes_science_kg.materiales.compilacion import serializar, sha
    from goes_science_kg.motor.registro import Registro

    registro = Registro(tmp_path / "ledger.sqlite")

    def llamada():
        return registro.reservar(
            ejecucion="prueba",
            clave="a",
            modelo="m",
            rol="r",
            reserva_usd=0.1,
            max_llamadas=10,
            max_usd=10,
        )

    id_ = llamada()
    with registro.conexion() as db:
        db.execute("UPDATE llamadas SET creada='2020-01-01 00:00:00'")
        filas = [dict(r) for r in db.execute("SELECT * FROM llamadas ORDER BY creada,id")]
    cfg = {"ejecucion": "prueba", "baseline": {"llamadas": 1, "filas_sha256": sha(serializar(filas))}}
    assert comprobar_continuidad(registro.archivo, cfg)["llamadas"] == 1
    llamada()
    assert comprobar_continuidad(registro.archivo, cfg)["llamadas"] == 2
    with registro.conexion() as db:
        db.execute("UPDATE llamadas SET reserva_usd=0.01 WHERE id=?", (id_,))
    with pytest.raises(ValueError, match="consumo anterior"):
        comprobar_continuidad(registro.archivo, cfg)
    vacio = Registro(tmp_path / "vacio.sqlite")
    with pytest.raises(ValueError, match="consumo anterior"):
        comprobar_continuidad(vacio.archivo, cfg)


def test_api_entrega_guion_hoja_estudiante_y_fuente_cnxml(tmp_path):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from goes_science_kg.api_materiales import crear_router_materiales
    from goes_science_kg.materiales.almacen import construir
    from goes_science_kg.materiales.compilacion import sha

    raw = b'<document xmlns="http://cnx.rice.edu/cnxml"><title>Fuente</title></document>'
    r = material_clase()
    r["titulo"] = "Una aventura en el patio"
    r["unidad"] = "Entorno"
    construir([r], {"fuente.cnxml": raw}, tmp_path / "data/materiales", procedencia={"snapshot_id": "s"})
    app = FastAPI()
    app.include_router(crear_router_materiales(tmp_path))
    with TestClient(app) as c:
        assert c.get("/api/v4/materiales?tipo=guion_clase").json()["total"] == 1
        assert c.get("/api/v4/materiales?tipo=guion_clase&q=comparar%20materiales").json()["total"] == 1
        direccion = "/api/v4/materiales/descarga/" + r["id"]
        alumno = c.get(direccion + "?formato=md&audiencia=estudiante")
        assert alumno.status_code == 200 and "Solucionario" not in alumno.text
        assert r["documento"]["guion"]["tareas"][0]["respuesta_esperada"] not in alumno.text
        assert "Solucionario" in c.get(direccion + "?formato=md").text
        assert c.get(direccion + "?audiencia=estudiante").status_code == 422
        fuente = c.get("/api/v4/materiales/archivos/" + sha(raw))
        assert fuente.content == raw and fuente.headers["content-type"].startswith("application/xml")


def test_lectura_presenta_fuente_primaria_con_rangos_de_bytes():
    from goes_science_kg.clases.lectura import markdown_clase

    material = material_clase()
    material["documento"]["fuentes_cientificas"] = [
        {
            "id": "ICS:revision#Triassic",
            "fuente": {
                "institucion": "ICS",
                "titulo": "International Chronostratigraphic Chart",
                "version_publicacion": "2026-06",
                "url": "https://stratigraphy.org/chart/",
                "localizador": {"formato": "extractos_bytes_utf8", "selecciones": [[10, 100], [200, 300]]},
                "sha256": "a" * 64,
                "licencia": "CC BY 4.0",
                "licencia_url": "https://creativecommons.org/licenses/by/4.0/",
            },
        }
    ]
    texto = markdown_clase(material)
    assert "ICS, 2026-06" in texto and "10:100, 200:300" in texto
    assert "https://stratigraphy.org/chart/" in texto


@pytest.mark.parametrize("defecto", ["clase_ausente", "clase_repetida", "objetivo_distinto", "duracion_distinta"])
def test_descarga_rechaza_unidades_que_no_corresponden_a_las_clases(tmp_path, defecto):
    from goes_science_kg.clases.paquete import construir

    clase = material_clase()
    ref = {
        "material_id": clase["id"],
        "fila_id": clase["fila_id"],
        "titulo": clase["titulo"],
        "objetivo": clase["documento"]["guion"]["objetivo"],
        "duracion_minutos": 60,
    }
    unidad = clase | {
        "id": "unidad-prueba",
        "tipo": "guion_unidad",
        "titulo": "Materia",
        "fila_id": None,
        "documento": {"guiones": [ref], "licencia_adaptacion": "Atribución de prueba."},
    }
    if defecto == "clase_ausente":
        ref["material_id"] = "inexistente"
    elif defecto == "clase_repetida":
        unidad["documento"]["guiones"].append(ref.copy())
    elif defecto == "objetivo_distinto":
        ref["objetivo"] = "Otro objetivo que no es el de la clase enlazada."
    else:
        ref["duracion_minutos"] = 120
    with pytest.raises(ValueError, match="unidad|unidades"):
        construir([clase, unidad], {}, tmp_path / "invalido.zip", procedencia={})


def test_reanudar_terminal_no_reserva_un_lote_completo_de_nuevo(preparacion, tmp_path, monkeypatch):
    import json

    from goes_science_kg.clases import operacion
    from goes_science_kg.materiales.compilacion import serializar

    proveedor = ProveedorGuion()
    corpus = SimpleNamespace(huella="a" * 64, verificar=lambda e: None)
    motor = MotorClases(proveedor, corpus)
    r = ejecutar_durable(
        motor,
        archivo=tmp_path / "cp.sqlite",
        solicitud=preparacion,
        thread_id="x",
        ejecucion_id="prueba",
        huella_entorno="b" * 64,
    )["resultado"]
    d = tmp_path / "ejecucion"
    d.mkdir()
    (d / ("resultado_" + preparacion["id"] + ".json")).write_bytes(serializar(r))
    (d / "protocolo.json").write_text(
        json.dumps(
            {
                "protocolo": "prueba",
                "huella_entorno": "b" * 64,
                "ejecucion": operacion.EJECUCION,
                "preparaciones": [preparacion["id"]],
            }
        )
    )
    monkeypatch.setattr(operacion, "entorno", lambda *args: "b" * 64)

    def estimar_solo_pendientes(lotes, prov):
        assert not lotes
        return {"safe_to_start": True}

    monkeypatch.setattr(operacion, "estimar", estimar_solo_pendientes)
    antes = len(proveedor.llamadas)
    assert operacion.ejecutar([preparacion], proveedor, corpus, d, protocolo="prueba") == [r]
    assert len(proveedor.llamadas) == antes


@pytest.mark.parametrize("faltantes", [("clases_adversarial",), ROLES])
def test_recuperacion_tecnica_conserva_borrador_y_no_repite_votos_validos(preparacion, tmp_path, faltantes):
    from goes_science_kg.clases.validacion import certificar_resultado

    class FalloTecnico(ProveedorGuion):
        tecnicas = None

        def generar(self, *, recuperacion_tecnica=False, **kwargs):
            if self.tecnicas is None:
                self.tecnicas = []
            if kwargs["rol"] in faltantes and not recuperacion_tecnica:
                self.llamadas.append((kwargs["rol"], {"fallo_tecnico": True}))
                raise RuntimeError("JSON truncado sin dictamen válido")
            if recuperacion_tecnica:
                self.tecnicas.append(kwargs["rol"])
            return super().generar(**kwargs)

    proveedor = FalloTecnico()
    motor = MotorClases(proveedor, SimpleNamespace(huella="a" * 64, verificar=lambda e: None))
    r = ejecutar_durable(
        motor,
        archivo=tmp_path / "cp.sqlite",
        solicitud=preparacion,
        thread_id="x",
        ejecucion_id="prueba",
        huella_entorno="b" * 64,
    )["resultado"]
    certificar_resultado(r, preparacion)
    assert r["estado"] == "respaldado_automaticamente"
    assert proveedor.redacciones == 1 and set(proveedor.tecnicas) == set(faltantes)
    assert len(proveedor.llamadas) == 5 + len(faltantes)
    assert r["rondas"][1]["tipo"] == "recuperacion_tecnica"
    assert r["rondas"][0]["borrador"] == r["rondas"][1]["borrador"]
    for rol in set(ROLES) - set(faltantes):
        assert r["rondas"][0]["lectores"][rol] == r["rondas"][1]["lectores"][rol]


def test_no_se_recupera_tecnicamente_un_veto_semantico(preparacion, tmp_path):
    class VetoYFallo(ProveedorGuion):
        def generar(self, *, recuperacion_tecnica=False, **kwargs):
            assert not recuperacion_tecnica
            if kwargs["rol"] == "clases_adversarial" and self.redacciones == 1:
                self.llamadas.append((kwargs["rol"], {"fallo_tecnico": True}))
                raise RuntimeError("Fallo técnico controlado")
            return super().generar(**kwargs)

    proveedor = VetoYFallo(veto=True)
    motor = MotorClases(proveedor, SimpleNamespace(huella="a" * 64, verificar=lambda e: None))
    r = ejecutar_durable(
        motor,
        archivo=tmp_path / "cp.sqlite",
        solicitud=preparacion,
        thread_id="x",
        ejecucion_id="prueba",
        huella_entorno="b" * 64,
    )["resultado"]
    assert proveedor.redacciones == 2
    assert r["rondas"][1]["tipo"] == "redaccion"


def test_campana_no_inicia_un_bloque_si_la_cota_completa_no_cabe(tmp_path, monkeypatch):
    from goes_science_kg.clases import campana

    control = tmp_path / "control.json"
    control.write_text('{"lotes":16,"vertex":24,"continuar":true}')
    monkeypatch.setattr(campana, "planificar", lambda *a, **kw: {"safe_to_start": False})
    monkeypatch.setattr(campana, "ejecutar", lambda *a, **kw: pytest.fail("No debía iniciar ninguna llamada"))
    with pytest.raises(ValueError, match="toda la campaña"):
        campana.ejecutar_campana([], None, None, tmp_path / "destino", control)
    assert not (tmp_path / "destino").exists()


@pytest.mark.parametrize("lotes,vertex", [(0, 16), (17, 24), (16, 25), (True, 16)])
def test_control_de_concurrencia_acotado(tmp_path, lotes, vertex):
    import json

    from goes_science_kg.clases.campana import leer_control

    archivo = tmp_path / "control.json"
    archivo.write_text(json.dumps({"lotes": lotes, "vertex": vertex, "continuar": True}))
    with pytest.raises(ValueError):
        leer_control(archivo)


def test_una_muestra_valida_no_se_publica_como_entrega_completa(tmp_path):
    from goes_science_kg.clases.paquete import construir
    from goes_science_kg.clases.publicacion import publicar

    archivo = tmp_path / "muestra.zip"
    construir([material_clase()], {}, archivo, procedencia={"snapshot_id": "s"})
    with pytest.raises(ValueError, match="1013"):
        publicar(archivo, None, tmp_path / "recibo.json")
    assert not (tmp_path / "recibo.json").exists()
