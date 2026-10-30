"""Test complete product-4 proposals, forged archives, and the full original-row denominator."""

from collections import defaultdict
from pathlib import Path

import pytest
import test_producto_alineaciones
import yaml
from fastapi import FastAPI
from fastapi.testclient import TestClient
from test_mejoras_curriculares import caso as caso
from test_producto_v4 import catalogo as catalogo
from test_producto_v4 import curriculo as curriculo
from test_producto_v4 import publicado as publicado
from test_producto_v4 import referencias as referencias

from goes_science_kg.api_producto import crear_router
from goes_science_kg.config import ruta
from goes_science_kg.ingesta.progresiones import BANDAS, LIMITE
from goes_science_kg.modelos import TipoArista, TipoNodo
from goes_science_kg.motor.contratos import Evidencia, huella
from goes_science_kg.motor.fragmentos import Fragmento
from goes_science_kg.producto.almacen import cargar_producto, publicar_producto
from goes_science_kg.producto.grafo_mejoras import grafo_mejoras, incorporar_mejoras, validar_grafo_mejoras
from goes_science_kg.producto.mejoras_contratos import PreparacionMejora, RondaMejora, SolicitudMejora
from goes_science_kg.producto.mejoras_publicadas import (
    ArchivoMejoras,
    CasoMejora,
    PruebaAdversarialMejora,
    validar_archivo_mejoras,
)
from goes_science_kg.producto.runtime import cargar_runtime
from goes_science_kg.producto.validacion_mejoras import resolver_mejora

publicado_alineado = test_producto_alineaciones.publicado


def identificar(modelo):
    return modelo.model_copy(update={"id": huella(modelo.model_dump(mode="json", exclude={"id"}))})


@pytest.fixture
def archivo(caso, curriculo, catalogo):
    patron, borrador, modelos, ronda = caso
    decisiones = {d.fila_id: d.model_dump(mode="json") for d in catalogo.filas}
    unidades = defaultdict(list)
    for f in curriculo.filas:
        unidades[(f.grado, f.asignatura_malla, f.unidad)].append(f)
    casos = []
    for (grado, asignatura, unidad), filas in sorted(unidades.items()):
        filas.sort(key=lambda f: (f.hoja, f.fila))
        externas = patron.evidencias[-1]
        locales = tuple(
            Evidencia.crear(
                f.id + "#CELDA:A1",
                f.procedimental,
                {"documento": f.fuente_id, "verificacion": "contenido_fuente", "tipo": "documental"},
                "V4",
            )
            for f in filas
        )
        evidencias = (*locales, externas)
        fragmentos = tuple(
            Fragmento(id=f"F:{i}", evidencia_id=e.id, literal=" ".join(e.texto.split()[:20]))
            for i, e in enumerate(evidencias)
        )
        p = identificar(
            PreparacionMejora(
                id="a" * 64,
                solicitud=SolicitudMejora(grado=grado, asignatura_malla=asignatura, unidad=unidad),
                huella_curriculo=curriculo.huella,
                huella_catalogo=huella(catalogo),
                filas_originales=tuple(f.model_dump(mode="json", exclude={"celdas"}) for f in filas),
                clasificaciones_originales={f.id: decisiones[f.id] for f in filas},
                alertas={},
                evidencias=evidencias,
                fragmentos=fragmentos,
                grupos={f"fila_{i:02d}": (e.id,) for i, e in enumerate(locales)} | {"referencia": (externas.id,)},
                contexto_aula=patron.contexto_aula,
                limites=patron.limites,
            )
        )
        propuestas = []
        for i, f in enumerate(filas):
            d = decisiones[f.id]
            fuera = d["estado"] == "fuera_alcance"
            propuestas.append(
                borrador.filas[0].model_copy(
                    update={
                        "fila_id": f.id,
                        "accion": "fuera_alcance" if fuera else "mantener_objetivo",
                        "objetivo_propuesto": f.procedimental,
                        "disciplinas_propuestas": tuple(d["disciplinas"]) or (() if fuera else ("fisica",)),
                        "fragmentos_ids": (f"F:{i}", f"F:{len(locales)}"),
                    }
                )
            )
        b = borrador.model_copy(update={"filas": tuple(propuestas)})
        rr = ronda.model_copy(
            update={
                "borrador": b,
                "dictamenes": tuple(
                    d.model_copy(
                        update={
                            "huella_preparacion": p.id,
                            "huella_borrador": huella(b),
                            "lectura": d.lectura.model_copy(update={"fragmentos_ids": tuple(f.id for f in fragmentos)}),
                        }
                    )
                    for d in ronda.dictamenes
                ),
            }
        )
        r = resolver_mejora(p, (rr,), ejecucion_id="sintetica", modelos=modelos)
        casos.append(CasoMejora(preparacion=p, resultado=r, entorno="a" * 64, plan_id="b" * 64))
    nativo = yaml.safe_load(Path("config/progresiones_documentales_2026.yaml").read_text())
    evidencias = {}
    fuentes = {}
    for e in nativo["expectativas"]:
        fuentes[e["fuente"]] = {
            "titulo": "Documento sintético para prueba",
            "sha256": e["sha256"],
            "raiz_fuente": "referencias_progresiones_2026",
            "archivo_local": e["fuente"] + ".pdf",
        }
        evidencias[e["id"]] = Evidencia.crear(
            e["id"],
            "Texto sintético, no extracción documental.",
            {
                "banda_nativa": e["banda"],
                "sha256": e["sha256"],
                "pagina": e["pagina_pdf"],
                "region": e["region"],
                "region_banda": e["region_banda"],
            },
            "referencia",
        ).model_dump(mode="json")
    cadenas = []
    for grupo in sorted({e["grupo"] for e in nativo["expectativas"]}):
        ids = [next(e["id"] for e in nativo["expectativas"] if e["grupo"] == grupo and e["banda"] == b) for b in BANDAS]
        cadenas.extend(
            {"origen": a, "destino": b, "tipo": "SIGUE_EN_REFERENCIA", "limite": LIMITE}
            for a, b in zip(ids, ids[1:], strict=False)
        )
    progresiones = {"catalogo": nativo, "evidencias": evidencias, "cadenas": cadenas}
    progresiones = {"id": huella(progresiones), **progresiones}
    pruebas = []
    base = casos[0]
    for i in range(5):
        b = base.resultado.propuesta.model_copy(update={"sintesis": f"Borrador sintético adversarial número {i}."})
        votos = []
        for j, d in enumerate(base.resultado.rondas[0].dictamenes):
            lectura = d.lectura
            if j == 0:
                lectura = lectura.model_copy(update={"criterios": lectura.criterios | {"correccion_cientifica": "no"}})
            votos.append(d.model_copy(update={"huella_borrador": huella(b), "lectura": lectura}))
        pruebas.append(
            PruebaAdversarialMejora(
                id=f"prueba{i}",
                preparacion=base.preparacion,
                ronda=RondaMejora(borrador=b, errores_estructura=(), dictamenes=tuple(votos)),
                rol_esperado="revision_ciencia",
                criterio_esperado="correccion_cientifica",
                razon_oraculo="Control sintético del contrato, sin LLM",
            )
        )
    return identificar(
        ArchivoMejoras(
            id="a" * 64,
            huella_curriculo=curriculo.huella,
            huella_catalogo=huella(catalogo),
            modelos=modelos,
            unidades=tuple(casos),
            progresiones=progresiones,
            fuentes_progresiones=fuentes,
            pruebas_adversariales=tuple(pruebas),
        )
    )


def test_archivo_completo_y_proyeccion_no_inventan_prerrequisitos(archivo, curriculo, catalogo):
    validar_archivo_mejoras(archivo, curriculo, catalogo)
    assert archivo.cobertura["filas"] == 1020 and archivo.cobertura["unidades"] == 108
    nodos, aristas = grafo_mejoras(archivo)
    assert sum(n.tipo == TipoNodo.EXPECTATIVA_NATIVA for n in nodos) == 12
    assert sum(a.tipo == TipoArista.SIGUE_EN_REFERENCIA for a in aristas) == 9
    assert not any(a.tipo in {TipoArista.CUBRE, TipoArista.PRERREQUISITO_DE} for a in aristas)


@pytest.mark.parametrize("cambio", ["omision", "resultado_falso", "prueba_duplicada", "banda", "arista"])
def test_rechaza_falsificaciones_incluso_recalculando_identidad(archivo, curriculo, catalogo, cambio):
    a = archivo
    if cambio == "omision":
        a = a.model_copy(update={"unidades": a.unidades[:-1]})
    elif cambio == "resultado_falso":
        c = a.unidades[0]
        r = c.resultado.model_copy(update={"estado": "abstencion", "propuesta": None})
        a = a.model_copy(update={"unidades": (c.model_copy(update={"resultado": r}), *a.unidades[1:])})
    elif cambio == "prueba_duplicada":
        a = a.model_copy(update={"pruebas_adversariales": (a.pruebas_adversariales[0],) * 5})
    elif cambio == "banda":
        progresiones = dict(a.progresiones)
        progresiones["cadenas"] = progresiones["cadenas"][1:]
        progresiones["id"] = huella({k: v for k, v in progresiones.items() if k != "id"})
        a = a.model_copy(update={"progresiones": progresiones})
    else:
        nodos, aristas = grafo_mejoras(a)
        with pytest.raises(ValueError):
            validar_grafo_mejoras(nodos, aristas[:-1], a)
        return
    with pytest.raises(ValueError):
        validar_archivo_mejoras(identificar(a), curriculo, catalogo)


def test_diez_archivos_y_mutacion_invalida_api(publicado, archivo, tmp_path):
    p = cargar_producto(publicado[0])
    nodos = list(p.nodos)
    aristas = list(p.aristas)
    incorporar_mejoras(nodos, aristas, archivo)
    destino = tmp_path / "publicacion"
    publicar_producto(
        destino=destino,
        curriculo=p.curriculo,
        catalogo=p.catalogo,
        nodos=nodos,
        aristas=aristas,
        diagnostico=p.diagnostico,
        alertas=p.alertas,
        publicacion=p.publicacion,
        mejoras=archivo,
    )
    nuevo = cargar_producto(destino)
    assert nuevo.manifest.version == "producto-4" and len(nuevo.manifest.sha256) == 10
    assert nuevo.mejoras == archivo
    app = FastAPI()
    app.include_router(crear_router(ruta("."), destino=destino))
    cliente = TestClient(app)
    assert cliente.get("/api/v4/propuestas").status_code == 200
    archivo_snapshot = nuevo.ruta_grafo / "mejoras.json"
    original = archivo_snapshot.read_bytes()
    archivo_snapshot.write_bytes(original + b" ")
    assert cliente.get("/api/v4/propuestas").status_code == 503
    archivo_snapshot.write_bytes(original)
    assert cliente.get("/api/v4/propuestas").status_code == 503


def test_original_con_errata_sigue_bloqueado_tras_publicar_propuesta(publicado, archivo, tmp_path):
    c = archivo.unidades[-1]
    fila_id = c.preparacion.filas_originales[0]["id"]
    p = identificar(
        c.preparacion.model_copy(update={"alertas": {fila_id: "Errata primaria documentada en prueba sintética."}})
    )
    ronda = c.resultado.rondas[0]
    ronda = ronda.model_copy(
        update={"dictamenes": tuple(d.model_copy(update={"huella_preparacion": p.id}) for d in ronda.dictamenes)}
    )
    c = c.model_copy(
        update={
            "preparacion": p,
            "resultado": resolver_mejora(p, (ronda,), ejecucion_id="sintetica", modelos=archivo.modelos),
        }
    )
    archivo = identificar(archivo.model_copy(update={"unidades": (*archivo.unidades[:-1], c)}))
    base = cargar_producto(publicado[0])
    nodos, aristas = list(base.nodos), list(base.aristas)
    incorporar_mejoras(nodos, aristas, archivo)
    destino = tmp_path / "errata"
    publicar_producto(
        destino=destino,
        curriculo=base.curriculo,
        catalogo=base.catalogo,
        nodos=nodos,
        aristas=aristas,
        diagnostico=base.diagnostico,
        alertas=base.alertas,
        publicacion=base.publicacion,
        mejoras=archivo,
    )
    runtime = cargar_runtime(destino)
    assert fila_id in runtime.fuentes.bloqueos_efectivos
    assert fila_id in runtime.fuentes.bloqueos_derivados
    assert fila_id not in runtime.fuentes.bloqueos_curriculares
    assert runtime.fuentes.motivos_bloqueo(p.evidencias[:1]) == ["Errata primaria documentada en prueba sintética."]
    assert runtime.producto.mejoras.unidades[-1].resultado.propuesta is not None


def test_veto_posterior_conserva_auditoria_historica_y_bloquea_generacion(publicado_alineado, archivo, monkeypatch):
    import goes_science_kg.producto.garantias as garantias

    base = publicado_alineado.base
    p = cargar_producto(base / "data/producto/V4")
    nodos, aristas = list(p.nodos), list(p.aristas)
    incorporar_mejoras(nodos, aristas, archivo)
    destino = base / "data/producto/V4_con_veto"
    publicar_producto(
        destino=destino,
        curriculo=p.curriculo,
        catalogo=p.catalogo,
        nodos=nodos,
        aristas=aristas,
        diagnostico=p.diagnostico,
        alertas=p.alertas,
        publicacion=p.publicacion,
        alineaciones=p.alineaciones,
        mejoras=archivo,
    )
    fila_id = p.alineaciones.casos[0].solicitud.fila_id
    original = garantias.bloqueos_cientificos
    archivo_local = base / "config/alertas_derivadas_v4.yaml"

    def bloqueos_locales(c, f, a):
        if a.suffix == ".yaml":
            return {fila_id: "Veto posterior documentado de prueba"} if a == archivo_local else {}
        return original(c, f, a)

    monkeypatch.setattr(garantias, "bloqueos_cientificos", bloqueos_locales)
    app = FastAPI()
    app.include_router(crear_router(base, destino=destino))
    cliente = TestClient(app)
    casos = cliente.get("/api/v4/alineaciones")
    assert casos.status_code == 200
    caso = casos.json()["casos"][0]
    assert caso["estado"] == "respaldo_documental_automatico" and not caso["habilitada_para_generacion"]
    detalle = cliente.get("/api/v4/alineaciones/" + caso["id"])
    assert detalle.status_code == 200 and detalle.json()["alerta_cientifica_actual"]
    runtime = cargar_runtime(
        destino,
        raiz_v4=base / "insumos/v4",
        raiz_referencias=base / "data/referencias_2026",
        archivo_alertas=base / "docs/investigacion/alertas_v4.json",
        archivo_alertas_derivadas=archivo_local,
    )
    with pytest.raises(ValueError, match="alerta científica"):
        runtime.buscador.buscar_fila(fila_id, version="V4", grado=10, asignatura="fisica")
