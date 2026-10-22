"""Materialización V4, aislamiento del histórico y publicación coherente frente a alteraciones."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from goes_science_kg.config import cargar, ruta
from goes_science_kg.curriculo import cargar_curriculo
from goes_science_kg.curriculo.catalogacion import (
    DECLARADAS,
    ROLES,
    CatalogoDisciplinas,
    ClasificacionFila,
    DecisionDisciplina,
)
from goes_science_kg.ingesta.dimensiones import CatalogoDimensiones
from goes_science_kg.ingesta.referencias import RepositorioReferencias
from goes_science_kg.modelos import Arista, Fuente, Nodo, TipoArista, TipoNodo
from goes_science_kg.motor.contexto import construir_contexto
from goes_science_kg.motor.contratos import Solicitud
from goes_science_kg.motor.flujo import Motor
from goes_science_kg.producto import AlertaSolicitada, ReferenciasProducto, almacen, cargar_producto, construir_producto
from goes_science_kg.producto import runtime as modulo_runtime
from goes_science_kg.producto._validacion import validar_entrada
from goes_science_kg.producto.construccion import _estructura, _incorporar_referencias
from goes_science_kg.producto.referencias import referencias_documentales
from goes_science_kg.producto.runtime import cargar_runtime
from goes_science_kg.recuperacion import Resultado


@pytest.fixture(scope="module")
def curriculo():
    return cargar_curriculo()


@pytest.fixture(scope="module")
def catalogo(curriculo):
    filas = []
    indice = 0
    for fila in curriculo.filas:
        if fila.asignatura_malla in DECLARADAS:
            filas.append(
                ClasificacionFila(
                    fila_id=fila.id,
                    estado="declarado_malla",
                    disciplinas=(DECLARADAS[fila.asignatura_malla],),
                    metodo="asignatura_explicita_del_libro",
                    justificacion="Asignatura declarada en la malla",
                )
            )
            continue
        if indice in (1, 2):
            filas.append(
                ClasificacionFila(
                    fila_id=fila.id,
                    estado="abstencion" if indice == 1 else "fuera_alcance",
                    metodo="dos_lecturas_independientes",
                    justificacion="Clasificación pendiente o fuera del alcance",
                )
            )
        else:
            disciplinas = ("fisica", "quimica") if indice == 0 else ("fisica",)
            lecturas = {
                rol: DecisionDisciplina(
                    fila_id=fila.id,
                    estado="en_alcance",
                    disciplinas=disciplinas,
                    justificacion="Objetivo científico específico de la fila",
                )
                for rol in ROLES
            }
            filas.append(
                ClasificacionFila(
                    fila_id=fila.id,
                    estado="coincidencia_automatica",
                    disciplinas=disciplinas,
                    metodo="dos_lecturas_independientes",
                    justificacion="Dos lecturas coinciden en el objetivo",
                    lecturas=lecturas,
                )
            )
        indice += 1
    return CatalogoDisciplinas(
        version_curriculo="V4",
        huella_curriculo=curriculo.huella,
        huella_instrucciones="a" * 64,
        huella_harness="b" * 64,
        modelos={r: f"modelo-prueba-{r}" for r in ROLES},
        modo="completo",
        piloto_superado=True,
        filas=tuple(filas),
    )


@pytest.fixture(scope="module")
def referencias():
    nodos = (
        Nodo(
            id="DOC:pisa_legacy",
            tipo=TipoNodo.DOCUMENTO,
            etiqueta="PISA histórico",
            props={"estado_publicacion": "publicado_final"},
        ),
        Nodo(id="DOC:malla_v3", tipo=TipoNodo.DOCUMENTO, etiqueta="Malla anterior"),
        Nodo(id="DOC:huerfano", tipo=TipoNodo.DOCUMENTO, etiqueta="Documento sin usos"),
        Nodo(
            id="TEMA:V3:1",
            tipo=TipoNodo.TEMA,
            etiqueta="Tema anterior",
            fuente=Fuente(documento="malla_v3", hoja="Anterior", fila=3),
        ),
        Nodo(id="PROP:V3:1", tipo=TipoNodo.PROPUESTA, etiqueta="Propuesta anterior"),
        Nodo(
            id="OBJ:PISA:historico",
            tipo=TipoNodo.OBJETIVO_MARCO,
            etiqueta="Objetivo histórico PISA",
            fuente=Fuente(documento="pisa_legacy", pagina=2),
        ),
        Nodo(
            id="OBJ:SIN:documento",
            tipo=TipoNodo.OBJETIVO_MARCO,
            etiqueta="Fuente ausente",
            fuente=Fuente(documento="no_existe", pagina=2),
        ),
        Nodo(id="CON:a", tipo=TipoNodo.CONCEPTO, etiqueta="Concepto A"),
        Nodo(id="CON:b", tipo=TipoNodo.CONCEPTO, etiqueta="Concepto B"),
    )
    aristas = (
        Arista(origen="TEMA:V3:1", destino="OBJ:PISA:historico", tipo=TipoArista.CUBRE, metodo="regla"),
        Arista(origen="TEMA:V3:1", destino="CON:a", tipo=TipoArista.TRABAJA, metodo="regla"),
        Arista(origen="OBJ:PISA:historico", destino="CON:a", tipo=TipoArista.TRABAJA, metodo="regla"),
        Arista(origen="CON:a", destino="CON:b", tipo=TipoArista.PRERREQUISITO_DE, metodo="regla"),
        Arista(origen="OBJ:PISA:historico", destino="DOC:pisa_legacy", tipo=TipoArista.FUENTE),
        Arista(origen="TEMA:V3:1", destino="DOC:malla_v3", tipo=TipoArista.FUENTE),
    )
    return ReferenciasProducto(nodos=nodos, aristas=aristas, procedencia={"version_curriculo": "V3"})


@pytest.fixture(scope="module")
def publicado(tmp_path_factory, curriculo, catalogo, referencias):
    destino = tmp_path_factory.mktemp("producto-publicado") / "grafo"
    observada = next(f for f in curriculo.filas if f.asignatura_malla == "Ciencias")
    resultado = construir_producto(
        curriculo,
        catalogo,
        destino=destino,
        referencias=referencias,
        alertas=(
            AlertaSolicitada(
                fila_id=observada.id,
                campo="procedimental",
                codigo="revision_test",
                descripcion="Observación de prueba sin dictamen científico",
            ),
        ),
    )
    return destino, resultado


def test_producto_real_conserva_rico_y_no_asigna_abstenciones(publicado, curriculo, catalogo):
    destino, resultado = publicado
    producto = cargar_producto(destino)
    assert producto.manifest.version_curriculo == "V4" and producto.manifest.version == "producto-2"
    assert "conocimiento.json" in producto.manifest.sha256 and producto.conocimiento is None
    assert producto.ruta_grafo == Path(resultado["ruta_grafo"])
    assert producto.curriculo == curriculo and producto.catalogo == catalogo
    temas = {n.id: n for n in producto.nodos if n.tipo == TipoNodo.TEMA}
    assert len(temas) == 1020 and sum(n.tipo == TipoNodo.UNIDAD for n in producto.nodos) == 108
    for fila in curriculo.filas:
        assert temas[fila.id].props["celdas"] == fila.model_dump(mode="json")["celdas"]
        assert temas[fila.id].fuente.celdas == [c.coordenada for c in fila.celdas]
    pendientes = [f for f in catalogo.filas if f.estado in {"abstencion", "fuera_alcance"}]
    assert len(pendientes) == 2
    for pendiente in pendientes:
        tema = temas[pendiente.fila_id]
        assert tema.asignatura is None and tema.props["disciplinas"] == []
        assert not any(a.origen == tema.id and a.tipo == TipoArista.DE_ASIGNATURA for a in producto.aristas)
    multiple = next(f for f in catalogo.filas if len(f.disciplinas) == 2)
    assert temas[multiple.fila_id].asignatura is None
    assert temas[multiple.fila_id].props["disciplinas"] == ["fisica", "quimica"]
    assert sum(a.origen == multiple.fila_id and a.tipo == TipoArista.DE_ASIGNATURA for a in producto.aristas) == 2


def test_diagnostico_no_convierte_declaraciones_en_cobertura_y_alertas_tienen_celdas(publicado):
    producto = cargar_producto(publicado[0])
    diagnostico = producto.diagnostico
    assert diagnostico["alineacion_internacional"]["verificado"] == 0
    assert diagnostico["alineacion_internacional"]["candidato"] == 0
    assert diagnostico["campos"]["competencia_pisa"]["declarado"] > 0
    assert diagnostico["fases"]["aproximar"]["columna_ausente"] == 138
    assert producto.alertas["resumen"]["fase_sin_columna"] == 8
    assert producto.alertas["resumen"]["clasificacion_pendiente"] == 1
    for alerta in producto.alertas["alertas"]:
        fuente = alerta["fuente"]
        assert len(fuente["sha256"]) == 64 and fuente["verificacion"] == "contenido_fuente"
        assert fuente["celdas_verificadas"] and fuente["celdas"]
        assert alerta["estado"] == "observacion_pendiente"
    assert producto.publicacion["fuentes_verificadas"]["archivos_leidos"] == 11


def test_referencias_no_heredan_temas_ni_fuentes_huerfanas_o_pisa_final(publicado):
    producto = cargar_producto(publicado[0])
    ids = {n.id for n in producto.nodos}
    assert {"TEMA:V3:1", "PROP:V3:1", "DOC:malla_v3", "DOC:huerfano", "OBJ:SIN:documento"}.isdisjoint(ids)
    assert {"CON:a", "CON:b", "OBJ:PISA:historico", "DOC:pisa_legacy"} <= ids
    pisa = next(n for n in producto.nodos if n.id == "DOC:pisa_legacy")
    assert pisa.props["estado_publicacion"] == "historico_sin_verificar_edicion_no_final_vigente"
    assert pisa.props["uso_en_producto"] == "referencia_historica"
    assert not any(a.tipo == TipoArista.CUBRE for a in producto.aristas)
    assert not any(a.origen.startswith("CURRICULO:") and a.tipo == TipoArista.TRABAJA for a in producto.aristas)
    assert any(a.tipo == TipoArista.PRERREQUISITO_DE and a.origen == "CON:a" for a in producto.aristas)


@pytest.mark.parametrize("cambio", ["version", "huella", "piloto", "piloto_no_superado", "faltante", "duplicado"])
def test_catalogo_incompleto_de_otra_generacion_o_piloto_rechazado(curriculo, catalogo, cambio):
    actualizacion = {
        "version": {"version_curriculo": "V3"},
        "huella": {"huella_curriculo": "0" * 64},
        "piloto": {"modo": "piloto"},
        "piloto_no_superado": {"piloto_superado": False},
        "faltante": {"filas": catalogo.filas[:-1]},
        "duplicado": {"filas": catalogo.filas[:-1] + catalogo.filas[:1]},
    }[cambio]
    with pytest.raises(ValueError):
        validar_entrada(curriculo, catalogo.model_copy(update=actualizacion))


def test_rechaza_heredar_clasificacion_declarada_a_ciencias(curriculo, catalogo):
    basica = next(f for f in catalogo.filas if f.estado == "coincidencia_automatica")
    falsa = basica.model_copy(update={"estado": "declarado_malla"})
    filas = tuple(falsa if f.fila_id == falsa.fila_id else f for f in catalogo.filas)
    with pytest.raises(ValueError, match="declarada"):
        validar_entrada(curriculo, catalogo.model_copy(update={"filas": filas}))


def test_rechaza_coincidencia_sin_jueces_y_abstencion_con_disciplina(curriculo, catalogo):
    basica = next(f for f in catalogo.filas if f.estado == "coincidencia_automatica")
    for falsa in (basica.model_copy(update={"lecturas": {}}), basica.model_copy(update={"estado": "abstencion"})):
        filas = tuple(falsa if f.fila_id == falsa.fila_id else f for f in catalogo.filas)
        with pytest.raises(ValueError):
            validar_entrada(curriculo, catalogo.model_copy(update={"filas": filas}))


def test_rechaza_datos_rico_alterados_sin_cambiar_celdas(curriculo, catalogo):
    falsa = curriculo.filas[0].model_copy(update={"procedimental": "Inventado fuera de la celda"})
    falso = curriculo.model_copy(update={"filas": (falsa, *curriculo.filas[1:])})
    with pytest.raises(ValueError, match="no corresponde a su celda"):
        validar_entrada(falso, catalogo)


def test_rechaza_curriculo_incompleto_o_ids_duplicados(curriculo, catalogo):
    for filas in (curriculo.filas[:-1], curriculo.filas[:-1] + curriculo.filas[:1]):
        with pytest.raises(ValueError, match="1020"):
            validar_entrada(curriculo.model_copy(update={"filas": filas}), catalogo)


@pytest.mark.parametrize(
    "archivo",
    [
        "nodos.jsonl",
        "aristas.jsonl",
        "curriculo.json",
        "catalogo.json",
        "diagnostico_v4.json",
        "alertas_v4.json",
        "publicacion.json",
        "conocimiento.json",
        "manifest.json",
    ],
)
def test_snapshot_rechaza_mutacion_de_cualquier_artefacto(publicado, tmp_path: Path, archivo: str):
    copia = tmp_path / "copia"
    shutil.copytree(publicado[0], copia)
    pointer = json.loads((copia / "actual.json").read_text())
    ruta_archivo = copia / "snapshots" / pointer["snapshot_id"] / archivo
    ruta_archivo.write_bytes(ruta_archivo.read_bytes() + b"alterado")
    with pytest.raises(ValueError, match="SHA|manifiesto"):
        cargar_producto(copia)


@pytest.mark.parametrize("cambio", ["escape", "version", "hash"])
def test_puntero_manipulado_se_rechaza_antes_de_exponer_datos(publicado, tmp_path: Path, cambio: str):
    copia = tmp_path / "copia"
    copia.mkdir()
    pointer = json.loads((publicado[0] / "actual.json").read_text())
    if cambio == "escape":
        pointer["snapshot_id"] = "../../reservado"
    elif cambio == "version":
        pointer["version_curriculo"] = "V3"
    else:
        pointer["manifest_sha256"] = "0" * 64
        (copia / "snapshots").symlink_to(publicado[0] / "snapshots", target_is_directory=True)
    (copia / "actual.json").write_text(json.dumps(pointer))
    with pytest.raises(ValueError):
        cargar_producto(copia)


def test_snapshot_symlink_externo_no_se_lee(publicado, tmp_path: Path):
    copia = tmp_path / "copia"
    shutil.copytree(publicado[0], copia)
    pointer = json.loads((copia / "actual.json").read_text())
    snapshot = copia / "snapshots" / pointer["snapshot_id"]
    (snapshot / "nodos.jsonl").unlink()
    (snapshot / "nodos.jsonl").symlink_to(Path(publicado[1]["ruta_grafo"]) / "nodos.jsonl")
    with pytest.raises(ValueError, match="enlaces"):
        cargar_producto(copia)


def test_escritor_rechaza_snapshots_redirigido_fuera_del_almacen(tmp_path: Path):
    base = tmp_path / "almacen"
    externo = tmp_path / "externo"
    base.mkdir()
    externo.mkdir()
    (base / "snapshots").symlink_to(externo, target_is_directory=True)
    with pytest.raises(ValueError, match="enlaces"):
        almacen._segura(base.resolve(), "snapshots/0")
    assert list(externo.iterdir()) == []


def test_fallo_de_escritura_conserva_puntero_anterior(
    publicado,
    curriculo,
    catalogo,
    monkeypatch,
):
    destino, _ = publicado
    anterior = (destino / "actual.json").read_bytes()

    # Falla al escribir el staging: el puntero vigente y la generación previa siguen legibles.
    def fallar(*args, **kwargs):
        raise OSError("Disco no disponible")

    monkeypatch.setattr(almacen, "_escribir_archivo", fallar)
    nodos, aristas = _estructura(curriculo, catalogo)
    with pytest.raises(OSError, match="Disco"):
        almacen.publicar_producto(
            destino=destino,
            curriculo=curriculo,
            catalogo=catalogo,
            nodos=nodos,
            aristas=aristas,
            diagnostico={},
            alertas={},
            publicacion={},
        )
    assert (destino / "actual.json").read_bytes() == anterior
    assert cargar_producto(destino).manifest.version_curriculo == "V4"
    assert not list(destino.glob(".publicando-*"))


def test_rechaza_destinos_historicos_sin_escribir():
    with pytest.raises(ValueError, match="histórico"):
        almacen._destino(ruta("data/grafo"), crear=True)


def test_referencia_nunca_sustituye_identidad_de_tema_v4(curriculo, catalogo):
    nodos, aristas = _estructura(curriculo, catalogo)
    primera = nodos[0]
    colision = ReferenciasProducto(nodos=(Nodo(id=primera.id, tipo=TipoNodo.CONCEPTO, etiqueta="Colisión"),))
    with pytest.raises(ValueError, match="sustituir"):
        _incorporar_referencias(nodos, aristas, colision)


def test_publicacion_identica_reutiliza_generacion(publicado):
    destino, esperado = publicado
    producto = cargar_producto(destino)
    resultado = almacen.publicar_producto(
        destino=destino,
        curriculo=producto.curriculo,
        catalogo=producto.catalogo,
        nodos=list(producto.nodos),
        aristas=list(producto.aristas),
        diagnostico=producto.diagnostico,
        alertas=producto.alertas,
        publicacion=producto.publicacion,
    )
    assert resultado["snapshot_id"] == esperado["snapshot_id"]
    assert len(list((destino / "snapshots").iterdir())) == 1


@pytest.fixture(scope="module")
def runtime(publicado):
    return cargar_runtime(publicado[0])


def test_runtime_recupera_fila_multidisciplinar_para_ambas_disciplinas(runtime, curriculo, catalogo):
    decision = next(d for d in catalogo.filas if len(d.disciplinas) == 2)
    fila = next(f for f in curriculo.filas if f.id == decision.fila_id)
    for asignatura in ("fisica", "quimica"):
        resultados = runtime.buscador.buscar(
            fila.procedimental, version="V4", grado=fila.grado, asignatura=asignatura, k=100
        )
        recuperada = next(r.documento for r in resultados if r.documento.id == fila.id)
        assert recuperada.asignatura is None
        assert set(recuperada.metadata["disciplinas"]) == {"fisica", "quimica"}
        assert recuperada.metadata["campos_por_celda"]
    ajena = runtime.buscador.buscar(fila.procedimental, version="V4", grado=fila.grado, asignatura="biologia", k=100)
    assert fila.id not in {r.documento.id for r in ajena}


def test_runtime_no_recupera_abstenciones_o_fuera_de_alcance(runtime, curriculo, catalogo):
    por_id = {f.id: f for f in curriculo.filas}
    for decision in catalogo.filas:
        if decision.estado not in {"abstencion", "fuera_alcance"}:
            continue
        fila = por_id[decision.fila_id]
        resultados = runtime.buscador.buscar(fila.procedimental, version="V4", grado=fila.grado, k=100)
        assert fila.id not in {r.documento.id for r in resultados}


def test_runtime_contexto_rehidrata_celdas_reales_y_ignora_texto_modificado(runtime, curriculo):
    fila = next(f for f in curriculo.filas if f.asignatura_malla == "Ciencias")
    documento = runtime.buscador.documentos[fila.id].model_copy(update={"texto": "Texto inyectado sin respaldo"})
    resultados = [Resultado(documento=documento, puntaje=1, canales=("prueba",))]
    contexto = construir_contexto(resultados, version="V4", fuentes=runtime.fuentes, max_caracteres=50000)
    assert contexto and all(e.version == "V4" for e in contexto)
    assert any(e.texto == fila.procedimental for e in contexto)
    assert not any("Texto inyectado" in e.texto for e in contexto)
    assert all(e.fuente["verificacion"] == "contenido_fuente" and e.fuente["celdas_verificadas"] for e in contexto)
    assert construir_contexto(resultados, version="V4", fuentes=None) == []


@pytest.fixture(scope="module")
def runtime_documental(tmp_path_factory, curriculo, catalogo):
    catalogo_dimensiones = CatalogoDimensiones.model_validate(cargar("dimensiones_evaluativas_2026"))
    repositorio = RepositorioReferencias(ruta("data/referencias_2026"))
    referencias = referencias_documentales(catalogo_dimensiones, repositorio)
    destino = tmp_path_factory.mktemp("producto-documental")
    construir_producto(curriculo, catalogo, destino=destino, referencias=referencias)
    return cargar_runtime(destino)


def test_runtime_incluye22_dimensiones_con_pdf_real_sin_crear_cobertura(runtime_documental):
    dimensiones = [n for n in runtime_documental.producto.nodos if n.tipo == TipoNodo.DIMENSION_DOCUMENTAL]
    assert len(dimensiones) == 22
    assert runtime_documental.producto.diagnostico["categorias_documentales"]["anclas_verificadas"] == 22
    assert not any(a.tipo == TipoArista.CUBRE for a in runtime_documental.producto.aristas)
    for dimension in dimensiones:
        documento = runtime_documental.buscador.documentos[dimension.id]
        evidencia = runtime_documental.fuentes.hidratar(documento)
        assert evidencia is not None and evidencia.version == "referencia"
        assert evidencia.fuente["sha256"] == dimension.props["comprobacion"]["sha256"]
        assert evidencia.fuente["raiz_fuente"] == "referencias_2026"
        assert dimension.props["ancla"].casefold() in " ".join(evidencia.texto.split()).casefold()


def test_runtime_contexto_combina_fila_v4_y_ancla_documental_verificada(runtime_documental, curriculo):
    fila = curriculo.filas[0]
    dimension = next(n for n in runtime_documental.producto.nodos if n.tipo == TipoNodo.DIMENSION_DOCUMENTAL)
    resultados = [
        Resultado(documento=runtime_documental.buscador.documentos[identidad], puntaje=1, canales=("prueba",))
        for identidad in (fila.id, dimension.id)
    ]
    contexto = construir_contexto(resultados, version="V4", fuentes=runtime_documental.fuentes, max_caracteres=50000)
    assert {e.version for e in contexto} == {"V4", "referencia"}
    assert any(e.version == "V4" and e.fuente.get("celdas_verificadas") for e in contexto)
    assert any(e.version == "referencia" and e.fuente.get("pagina") for e in contexto)


def test_runtime_indexa_snapshot_en_memoria_sin_releer_archivos_mutados(publicado, tmp_path, monkeypatch):
    copia = tmp_path / "producto"
    shutil.copytree(publicado[0], copia)
    cargar_original = modulo_runtime.cargar_producto

    def mutar_despues_de_cargar(destino):
        producto = cargar_original(destino)
        (producto.ruta_grafo / "nodos.jsonl").write_bytes("Cambio concurrente tras capturar la generación".encode())
        return producto

    monkeypatch.setattr(modulo_runtime, "cargar_producto", mutar_despues_de_cargar)
    actual = modulo_runtime.cargar_runtime(copia)
    assert len([d for d in actual.buscador.documentos.values() if d.version == "V4"]) == 1020
    assert actual.producto.manifest.snapshot_id == publicado[1]["snapshot_id"]
    with pytest.raises(ValueError, match="SHA"):
        cargar_producto(copia)


def test_runtime_bloqueo_cientifico_abstiene_antes_de_llamar_modelos(runtime_documental, curriculo):
    bloqueadas = runtime_documental.fuentes.bloqueos_curriculares
    assert len(bloqueadas) == 27
    fila = next(f for f in curriculo.filas if f.id in bloqueadas)

    class ModeloNoDebeEjecutarse:
        llamadas = 0

        def generar(self, **kwargs):
            self.llamadas += 1
            pytest.fail("Una fila bloqueada no debe llegar a modelos remotos")

    modelo = ModeloNoDebeEjecutarse()
    solicitud = Solicitud(consulta=fila.procedimental, grado=fila.grado, asignatura="biologia", version_curriculo="V4")
    motor = Motor(runtime_documental.buscador, modelo, fuentes=runtime_documental.fuentes)
    resultado = motor.compilar().invoke({"solicitud": solicitud.model_dump(), "ejecucion_id": "bloqueo-local"})
    assert resultado["resultado"]["estado"] == "abstencion"
    assert resultado["resultado"]["motivos"] and modelo.llamadas == 0
