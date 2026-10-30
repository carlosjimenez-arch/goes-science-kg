"""Discover locally anchored V4 relationship hypotheses without approving them."""

# Historical implementation notes:
# La salida se entrega a un workflow especializado posterior. No modifica el grafo,
# el recuperador, la clasificación disciplinar ni la simulación histórica.

from __future__ import annotations

import inspect
import logging
import re
import resource
import sys
import time
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import networkx as nx

from goes_science_kg.config import ruta
from goes_science_kg.curriculo.catalogacion import DECLARADAS
from goes_science_kg.curriculo.contratos import Curriculo
from goes_science_kg.ingesta import estructurados
from goes_science_kg.modelos import Nodo, TipoArista, TipoNodo
from goes_science_kg.motor.contratos import Evidencia
from goes_science_kg.motor.fuentes import FuentesVerificadas
from goes_science_kg.producto import _conocimiento_contratos, _conocimiento_lexico
from goes_science_kg.producto._conocimiento_contratos import (
    CandidatoConocimiento,
    DAGNoValidado,
    EdicionEsperada,
    InformeConocimiento,
    PoliticaConocimiento,
)
from goes_science_kg.producto._conocimiento_lexico import IndiceAlias
from goes_science_kg.producto._validacion import json_bytes, sha, verificar_celdas
from goes_science_kg.producto.contratos import ReferenciasProducto
from goes_science_kg.recuperacion import Documento
from goes_science_kg.recuperacion.grafo import _resolver_version

LOGGER = logging.getLogger(__name__)
__all__ = [
    "CandidatoConocimiento",
    "EdicionEsperada",
    "InformeConocimiento",
    "PoliticaConocimiento",
    "generar_candidatos_conocimiento",
]
_NIVELES = {"primaria": (2, 6), "secundaria": (7, 9), "bachillerato": (10, 11)}


def _literal(valor: object) -> str:
    return " ".join(unicodedata.normalize("NFKC", str(valor or "")).split())


def _descriptor(nodo: Nodo) -> dict:
    return {
        "id": nodo.id,
        "tipo": nodo.tipo.value,
        "etiqueta": nodo.etiqueta,
        "asignatura_namespace_historico": nodo.asignatura,
        "datos_historicos": nodo.model_dump(mode="json"),
        "huella_registro_historico": sha(json_bytes(nodo.model_dump(mode="json"))),
        "estado": "referencia_historica_por_revalidar",
    }


class _ReferenciasVerificables:
    """Verify native documentary units once without claiming semantic translation validation."""

    def __init__(self, referencia: ReferenciasProducto, politica: PoliticaConocimiento, raiz: Path):
        self.documentos = {}
        catalogo = {}
        for nodo in referencia.nodos:
            if nodo.tipo == TipoNodo.DOCUMENTO:
                identificador = nodo.id.removeprefix("DOC:")
                if identificador in catalogo:
                    raise ValueError("Identidad documental ambigua después de resolver su registro de fuente")
                catalogo[identificador] = nodo.props
                self.documentos[identificador] = nodo
        self.fuentes = FuentesVerificadas(catalogo, raiz_fuentes=raiz)
        self.politica = politica
        self.cache: dict[str, tuple[dict, tuple[str, ...], Evidencia | None]] = {}

    def consultar(self, nodo: Nodo) -> tuple[dict, tuple[str, ...], Evidencia | None]:
        """Look up a native documentary unit through its verified source index."""

        if nodo.id in self.cache:
            return self.cache[nodo.id]
        fuente = nodo.fuente
        documento = self.documentos.get(fuente.documento.removeprefix("DOC:")) if fuente else None
        descripcion = _descriptor(nodo)
        bloqueos = []
        evidencia = None
        if fuente is None or documento is None:
            bloqueos.append("fuente_primaria_no_identificada")
        else:
            metadatos = documento.props
            version = _literal(metadatos.get("version_documental", metadatos.get("anio")))
            descripcion["edicion_documental"] = {
                "documento": fuente.documento,
                "sha256": metadatos.get("sha256"),
                "version_documental_declarada": version,
                "titulo": documento.etiqueta,
                "vigencia_normativa": "no_verificada",
                "url": metadatos.get("url"),
            }
            esperada = self.politica.ediciones_por_documento.get(fuente.documento)
            if esperada is None:
                bloqueos.append("edicion_no_fijada_por_politica")
            elif esperada.sha256 != metadatos.get("sha256") or _literal(esperada.version_documental) != version:
                bloqueos.append("edicion_documental_no_coincide_con_politica")
            hash_valido = isinstance(metadatos.get("sha256"), str) and bool(
                re.fullmatch(r"[a-f0-9]{64}", metadatos["sha256"])
            )
            extension = Path(str(metadatos.get("archivo_local", ""))).suffix.lower()
            pdf = extension == ".pdf" and bool(fuente.pagina)
            codigo = extension in {".docx", ".html", ".htm"} and bool(fuente.localizador)
            if not hash_valido:
                bloqueos.append("sha_documental_no_es_hexadecimal_verificable")
            if not (pdf or codigo):
                bloqueos.append("localizador_o_formato_sin_hidratador_primario")
            if hash_valido and (pdf or codigo):
                hidratada = self.fuentes.hidratar(
                    Documento(
                        id=nodo.id,
                        texto="Los metadatos no sustituyen la unidad documental original",
                        version="referencia",
                        fuente=fuente.model_dump(exclude_none=True),
                    )
                )
                if hidratada is None:
                    bloqueos.append("fuente_original_no_verificable")
                else:
                    identidad = sha(json_bytes(hidratada.fuente))
                    evidencia = Evidencia.crear(
                        f"{'PAGINA_VERIFICADA' if pdf else 'CODIGO_VERIFICADO'}:{identidad}",
                        hidratada.texto,
                        hidratada.fuente,
                        "referencia",
                    )
        self.cache[nodo.id] = descripcion, tuple(sorted(set(bloqueos))), evidencia
        return self.cache[nodo.id]


def _evidencia_celda(fila_id: str, evidencia: dict, celda: dict) -> Evidencia:
    fuente = {k: v for k, v in evidencia["fuente"].items() if k not in {"celdas", "celdas_verificadas"}}
    coordenada = celda["coordenada_solicitada"]
    fuente.update(celdas=[coordenada], celdas_verificadas=[celda])
    return Evidencia.crear(f"{fila_id}#CELDA:{coordenada}", str(celda["valor_real"]), fuente, "V4")


def _seleccionar_grupos(opciones: list[dict], limite: int) -> tuple[list[dict], list[str]]:
    """Preserve ambiguity rather than silently discarding competing group members."""
    seleccionados, omitidos, procesados = [], [], set()
    disponibles = {o["destino"] for o in opciones}
    for opcion in opciones:
        if opcion["destino"] in procesados:
            continue
        grupo = {opcion["destino"]}
        while True:
            ampliado = grupo | {i for o in opciones if o["destino"] in grupo for i in o["alternativas"]}
            ampliado &= disponibles
            if ampliado == grupo:
                break
            grupo = ampliado
        miembros = [o for o in opciones if o["destino"] in grupo]
        procesados.update(grupo)
        if len(seleccionados) + len(miembros) <= limite:
            seleccionados.extend(miembros)
        else:
            omitidos.extend(grupo)
    return seleccionados, sorted(set(omitidos))


def _rotar_paises(opciones: list[dict], limite: int) -> tuple[list[dict], list[str]]:
    """Diversify review candidates by country without inferring superiority or equivalence."""
    por_pais = defaultdict(list)
    for opcion in opciones:
        por_pais[opcion["pais"]].append(opcion)
    salida = []
    while len(salida) < limite and any(por_pais.values()):
        for pais in sorted(por_pais):
            if por_pais[pais] and len(salida) < limite:
                salida.append(por_pais[pais].pop(0))
    return salida, sorted(o["destino"] for valores in por_pais.values() for o in valores)


def generar_candidatos_conocimiento(
    curriculo: Curriculo,
    referencia_v3: ReferenciasProducto,
    *,
    raiz_v4: Path | None = None,
    raiz_historica: Path | None = None,
    politica: PoliticaConocimiento | None = None,
) -> InformeConocimiento:
    """Propose links from verified cells without creating accepted curriculum edges or prerequisites."""

    # Implementation notes:
    # La referencia debe proceder del cargador histórico validado. Los IDs son opacos:
    # el tipo del nodo identifica conceptos, prácticas y objetivos de países.
    inicio = time.perf_counter()
    politica = politica or PoliticaConocimiento()
    if curriculo.version != "V4" or referencia_v3.procedencia.get("version_curriculo") != "V3":
        raise ValueError("Se requiere currículo V4 y referencia histórica V3 explícita")
    _resolver_version(referencia_v3.nodos, "V3")
    nodos = {n.id: n for n in referencia_v3.nodos}
    if len(nodos) != len(referencia_v3.nodos) or len({f.id for f in curriculo.filas}) != len(curriculo.filas):
        raise ValueError("Identidades duplicadas en fuentes de candidatos")
    if any(f.version != "V4" for f in curriculo.filas) or any(f.version != "V4" for f in curriculo.fuentes):
        raise ValueError("Las fuentes o filas mezclan versiones curriculares")
    LOGGER.info("Conocimiento V4: rehidratando fuentes y construyendo hipótesis locales")
    material = {
        "nodos": [n.model_dump(mode="json") for n in sorted(referencia_v3.nodos, key=lambda n: n.id)],
        "aristas": [
            a.model_dump(mode="json")
            for a in sorted(referencia_v3.aristas, key=lambda a: (a.origen, a.destino, a.tipo.value, a.rol or ""))
        ],
        "procedencia": referencia_v3.procedencia,
    }
    huella_referencia = sha(json_bytes(material))
    del material  # No retener otra copia completa del grafo durante el parseo de las fuentes.
    archivos = [
        Path(__file__),
        Path(_conocimiento_contratos.__file__),
        Path(_conocimiento_lexico.__file__),
        Path(estructurados.__file__),
        Path(inspect.getfile(verificar_celdas)),
        Path(inspect.getfile(FuentesVerificadas)),
    ]
    huella_pipeline = sha(json_bytes({p.name: sha(p.read_bytes()) for p in archivos}))
    base_identidad = [curriculo.huella, huella_referencia, huella_pipeline, politica.model_dump(mode="json")]
    vocabulario = [n for n in nodos.values() if n.tipo in {TipoNodo.CONCEPTO, TipoNodo.PRACTICA}]
    indice = IndiceAlias(vocabulario)
    locales, estadisticas_locales = verificar_celdas(curriculo, raiz_v4 or ruta("insumos/v4"))
    verificables = _ReferenciasVerificables(referencia_v3, politica, raiz_historica or ruta("data/fuentes"))
    evidencias: dict[str, Evidencia] = {}
    referencias = {}
    candidatos = []
    por_fila = {}
    omisiones = Counter()
    por_concepto = defaultdict(lambda: {"filas": [], "contrastes_pais": [], "prerrequisitos": []})
    por_pais = defaultdict(lambda: {"filas": set(), "objetivos": set(), "candidatos": [], "bloqueos": Counter()})

    def crear(
        tipo: str,
        fila,
        destino: str,
        *,
        origen: str | None = None,
        metodo="alias_literal",
        estado="candidato",
        anclas: tuple[str, ...],
        pruebas: tuple[str, ...] = (),
        advertencias=(),
        bloqueos=(),
        alternativas=(),
        contexto: dict,
    ):
        campos = {
            "tipo": tipo,
            "fila_id": fila.id,
            "origen": origen or fila.id,
            "destino": destino,
            "metodo": metodo,
            "estado": estado,
            "evidencias_locales": tuple(sorted(set(anclas))),
            "referencias_evidencia": tuple(sorted(set(pruebas))),
            "advertencias": tuple(sorted(set(advertencias))),
            "bloqueos_aceptacion": tuple(sorted({*bloqueos, "juicio_especializado_pendiente"})),
            "alternativas": tuple(sorted(set(alternativas))),
            "contexto": contexto,
        }
        identidad = sha(json_bytes([base_identidad, campos]))
        candidato = CandidatoConocimiento(id=f"CANDIDATO_V4:{identidad}", **campos)
        candidatos.append(candidato)
        return candidato

    # La red V3 solo propone rutas de búsqueda; nunca se convierte en relaciones V4.
    rutas_pais = defaultdict(dict)
    for objetivo in sorted((n for n in nodos.values() if n.tipo == TipoNodo.OBJETIVO_PAIS), key=lambda n: n.id):
        for coincidencia in indice.buscar(objetivo.etiqueta):
            rutas_pais[coincidencia.nodo_id][objetivo.id] = ("alias_literal", None)
    prerequisitos = defaultdict(list)
    invalidas = []
    for arista in sorted(referencia_v3.aristas, key=lambda a: (a.origen, a.destino, a.tipo.value, a.rol or "")):
        origen, destino = nodos.get(arista.origen), nodos.get(arista.destino)
        if arista.tipo == TipoArista.TRABAJA and origen and destino and origen.tipo == TipoNodo.OBJETIVO_PAIS:
            if destino.tipo in {TipoNodo.CONCEPTO, TipoNodo.PRACTICA}:
                rutas_pais[destino.id].setdefault(origen.id, ("ruta_historica_por_revalidar", arista))
        if arista.tipo == TipoArista.PRERREQUISITO_DE:
            if origen and destino and origen.tipo == destino.tipo == TipoNodo.CONCEPTO:
                prerequisitos[destino.id].append(arista)
            else:
                invalidas.append(arista.model_dump(mode="json"))
    for fila in sorted(curriculo.filas, key=lambda f: f.id):
        evidencia_fila = locales.pop(fila.id)
        por_celda = {c["coordenada_solicitada"]: c for c in evidencia_fila["fuente"]["celdas_verificadas"]}
        encontrados = defaultdict(list)
        for prioridad, campo in enumerate(politica.campos_locales):
            for celda in fila.celdas:
                if celda.campo != campo:
                    continue
                original = por_celda[celda.coordenada]
                texto = original["valor_real"]
                if original["valor_es_formula"] or not isinstance(texto, str):
                    continue
                for coincidencia in indice.buscar(texto):
                    evidencia = _evidencia_celda(fila.id, evidencia_fila, original)
                    evidencias[evidencia.id] = evidencia
                    encontrados[coincidencia.nodo_id].append(
                        {
                            "evidencia_id": evidencia.id,
                            "campo": campo,
                            "prioridad": prioridad,
                            "alias": coincidencia.alias,
                            "literal_nfkc": coincidencia.literal,
                            "offset_nfkc": [coincidencia.inicio, coincidencia.fin],
                            "alternativas": coincidencia.alternativas,
                            "negacion_cercana": bool(
                                re.search(
                                    r"\b(no|sin|ausencia)\b",
                                    unicodedata.normalize("NFKC", texto)[: coincidencia.inicio][-45:].casefold(),
                                )
                            ),
                        }
                    )
        opciones = [
            {
                "destino": identidad,
                "alternativas": sorted({i for m in matches for i in m["alternativas"]}),
                "matches": matches,
            }
            for identidad, matches in encontrados.items()
        ]
        opciones.sort(
            key=lambda o: (
                min(m["prioridad"] for m in o["matches"]),
                -max(len(m["literal_nfkc"]) for m in o["matches"]),
                o["destino"],
            )
        )
        elegidos, omitidos = _seleccionar_grupos(opciones, politica.max_conceptos_por_fila)
        registro = {
            "grado": fila.grado,
            "asignatura_malla": fila.asignatura_malla,
            "unidad": fila.unidad,
            "candidatos": [],
            "sin_alias_detectado": not opciones,
            "omitidos_por_presupuesto": {"vocabulario": omitidos},
        }
        omisiones["vocabulario"] += len(omitidos)
        puente = {}
        for opcion in elegidos:
            nodo = nodos[opcion["destino"]]
            referencia, bloqueos, prueba = verificables.consultar(nodo)
            referencias[nodo.id] = referencia
            if prueba:
                evidencias[prueba.id] = prueba
            avisos = ["Mención léxica no acredita enseñanza, dominio o relación conceptual"]
            nivel = _NIVELES.get(nodo.props.get("nivel"))
            if nivel and not nivel[0] <= fila.grado <= nivel[1]:
                bloqueos = (*bloqueos, "nivel_historico_no_corresponde_al_grado_local")
            declarada = DECLARADAS.get(fila.asignatura_malla)
            if declarada and nodo.asignatura and declarada != nodo.asignatura:
                avisos.append("Namespace disciplinar distinto: requiere juicio interdisciplinar")
            if any(m["negacion_cercana"] for m in opcion["matches"]):
                avisos.append("Hay negación próxima al término; no se infiere que el contenido se enseñe")
            anclas = tuple(sorted({m["evidencia_id"] for m in opcion["matches"]}))
            candidato = crear(
                "fila_concepto" if nodo.tipo == TipoNodo.CONCEPTO else "fila_practica",
                fila,
                nodo.id,
                estado="ambiguo" if len(opcion["alternativas"]) > 1 else "candidato",
                anclas=anclas,
                pruebas=(prueba.id,) if prueba else (),
                bloqueos=bloqueos,
                advertencias=avisos,
                alternativas=opcion["alternativas"],
                contexto={
                    "grado_sv": fila.grado,
                    "asignatura_malla": fila.asignatura_malla,
                    "ocurrencias": opcion["matches"],
                    "nivel_historico": nodo.props.get("nivel"),
                    "version_referencia": "V3",
                    "huella_registro": referencia["huella_registro_historico"],
                },
            )
            registro["candidatos"].append(candidato.id)
            por_concepto[nodo.id]["filas"].append(fila.id)
            puente[nodo.id] = candidato
        paises_opciones = {}
        for concepto, candidato in puente.items():
            for objetivo_id, (metodo, arista) in rutas_pais[concepto].items():
                objetivo = nodos[objetivo_id]
                opcion = paises_opciones.setdefault(
                    objetivo_id,
                    {
                        "destino": objetivo_id,
                        "pais": str(objetivo.props.get("pais", "desconocido")),
                        "rutas": [],
                        "conceptos": set(),
                        "anclas": set(),
                    },
                )
                opcion["conceptos"].add(concepto)
                opcion["anclas"].update(candidato.evidencias_locales)
                opcion["rutas"].append(
                    {
                        "concepto": concepto,
                        "metodo": metodo,
                        "arista_historica": arista.model_dump(mode="json") if arista else None,
                    }
                )
        orden_paises = sorted(
            paises_opciones.values(),
            key=lambda o: (not any(r["metodo"] == "alias_literal" for r in o["rutas"]), o["pais"], o["destino"]),
        )
        paises_elegidos, paises_omitidos = _rotar_paises(orden_paises, politica.max_objetivos_pais_por_fila)
        registro["omitidos_por_presupuesto"]["objetivos_pais"] = paises_omitidos
        omisiones["objetivos_pais"] += len(paises_omitidos)
        for opcion in paises_elegidos:
            objetivo = nodos[opcion["destino"]]
            referencia, bloqueos, prueba = verificables.consultar(objetivo)
            referencias[objetivo.id] = referencia
            if prueba:
                evidencias[prueba.id] = prueba
            metodo = (
                "alias_literal"
                if any(r["metodo"] == "alias_literal" for r in opcion["rutas"])
                else ("ruta_historica_por_revalidar")
            )
            alternativas = sorted({i for concepto in opcion["conceptos"] for i in puente[concepto].alternativas})
            advertencias = [
                "El grado extranjero o normalizado en V3 no equivale a grado salvadoreño",
                "El objetivo del grafo es traducción/representación histórica por revalidar",
            ]
            if any(puente[concepto].estado == "ambiguo" for concepto in opcion["conceptos"]):
                advertencias.append("El puente conceptual local contiene alias ambiguos")
            candidato = crear(
                "contraste_pais",
                fila,
                objetivo.id,
                metodo=metodo,
                estado="bloqueado" if bloqueos else "candidato",
                anclas=tuple(opcion["anclas"]),
                pruebas=(prueba.id,) if prueba else (),
                bloqueos=bloqueos,
                advertencias=advertencias,
                alternativas=alternativas,
                contexto={
                    "pais": opcion["pais"],
                    "grado_sv": fila.grado,
                    "grado_o_tramo_extranjero": objetivo.props.get("grado_o_tramo"),
                    "grados_normalizados_legacy_no_equivalentes": {
                        "grado": objetivo.grado,
                        "min": objetivo.props.get("grado_min"),
                        "max": objetivo.props.get("grado_max"),
                    },
                    "equivalencia_grado_sv": None,
                    "edicion": referencia.get("edicion_documental"),
                    "rutas": sorted(opcion["rutas"], key=lambda r: (r["concepto"], r["metodo"])),
                },
            )
            registro["candidatos"].append(candidato.id)
            for concepto in sorted(opcion["conceptos"]):
                por_concepto[concepto]["contrastes_pais"].append(candidato.id)
            pais = por_pais[opcion["pais"]]
            pais["filas"].add(fila.id)
            pais["objetivos"].add(objetivo.id)
            pais["candidatos"].append(candidato.id)
            pais["bloqueos"].update(candidato.bloqueos_aceptacion)
        opciones_prereq = sorted(
            [a for concepto in puente for a in prerequisitos[concepto]],
            key=lambda a: (a.origen, a.destino, a.version or ""),
        )
        omitidos_prereq = [f"{a.origen} → {a.destino}" for a in opciones_prereq[politica.max_prerrequisitos_por_fila :]]
        registro["omitidos_por_presupuesto"]["prerrequisitos"] = omitidos_prereq
        omisiones["prerrequisitos"] += len(omitidos_prereq)
        for arista in opciones_prereq[: politica.max_prerrequisitos_por_fila]:
            nodo = nodos[arista.origen]
            referencias.setdefault(nodo.id, _descriptor(nodo))
            candidato = crear(
                "prerrequisito",
                fila,
                arista.destino,
                origen=arista.origen,
                metodo="ruta_historica_por_revalidar",
                anclas=puente[arista.destino].evidencias_locales,
                bloqueos=("dependencia_conceptual_y_adecuacion_de_grado_no_verificadas",),
                advertencias=("Orden observado y confianza IA histórica no demuestran necesidad cognitiva",),
                contexto={
                    "grado_sv_destino": fila.grado,
                    "grado_prerrequisito_propuesto": None,
                    "arista_historica": arista.model_dump(mode="json"),
                    "estado": "hipotesis_de_dependencia",
                },
            )
            registro["candidatos"].append(candidato.id)
            por_concepto[arista.destino]["prerrequisitos"].append(candidato.id)
        por_fila[fila.id] = registro
    candidatos.sort(key=lambda c: (c.fila_id, c.tipo, c.origen, c.destino, c.id))
    if len({c.id for c in candidatos}) != len(candidatos):
        raise ValueError("Rutas históricas duplicadas producen candidatos ambiguos; revise la referencia")
    usados = {i for c in candidatos for i in (*c.evidencias_locales, *c.referencias_evidencia)}
    evidencias = {i: e for i, e in sorted(evidencias.items()) if i in usados}
    grafo_hipotesis = nx.DiGraph((c.origen, c.destino) for c in candidatos if c.tipo == "prerrequisito")
    ciclos = tuple(
        sorted(
            tuple(sorted(componente))
            for componente in nx.strongly_connected_components(grafo_hipotesis)
            if len(componente) > 1 or any(grafo_hipotesis.has_edge(i, i) for i in componente)
        )
    )
    memoria = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform == "darwin" else 1024)
    resumen = {
        "filas": len(curriculo.filas),
        "filas_con_candidato": sum(bool(r["candidatos"]) for r in por_fila.values()),
        "filas_sin_alias": sum(r["sin_alias_detectado"] for r in por_fila.values()),
        "filas_sin_candidato_por_presupuesto": sum(
            not r["sin_alias_detectado"] and not r["candidatos"] for r in por_fila.values()
        ),
        "por_tipo": dict(sorted(Counter(c.tipo for c in candidatos).items())),
        "por_estado": dict(sorted(Counter(c.estado for c in candidatos).items())),
        "bloqueos_aceptacion": dict(sorted(Counter(b for c in candidatos for b in c.bloqueos_aceptacion).items())),
        "omitidos_por_presupuesto": dict(sorted(omisiones.items())),
        "avisos_vocabulario": indice.avisos,
        "prerrequisitos_historicos_invalidos": invalidas,
        "aceptados": 0,
        "alineaciones_confirmadas": 0,
        "dag_verificado": False,
        "ciclos_en_hipotesis": len(ciclos),
    }
    LOGGER.info("Conocimiento V4: %d propuestas, %d filas; 0 vínculos aceptados", len(candidatos), len(por_fila))
    return InformeConocimiento(
        huella_curriculo=curriculo.huella,
        huella_referencia=huella_referencia,
        procedencia_referencia=referencia_v3.procedencia,
        huella_pipeline=huella_pipeline,
        huella_candidatos=sha(json_bytes([c.model_dump(mode="json") for c in candidatos])),
        politica=politica,
        candidatos=tuple(candidatos),
        evidencias=evidencias,
        referencias=dict(sorted(referencias.items())),
        por_fila=dict(sorted(por_fila.items())),
        por_concepto={k: v for k, v in sorted(por_concepto.items())},
        por_pais={
            k: {
                "filas": sorted(v["filas"]),
                "objetivos": sorted(v["objetivos"]),
                "candidatos": sorted(v["candidatos"]),
                "bloqueos": dict(sorted(v["bloqueos"].items())),
            }
            for k, v in sorted(por_pais.items())
        },
        dag_aceptado=DAGNoValidado(ciclos_candidatos=ciclos),
        resumen=resumen,
        metricas={
            "segundos_total": round(time.perf_counter() - inicio, 6),
            "memoria_pico_proceso_bytes": memoria,
            "alcance_memoria": "Máximo RSS de este proceso; incluye inputs y trabajo anterior, no memoria incremental",
            "fuentes_v4": estadisticas_locales,
            "fuentes_referencia": verificables.fuentes.estadisticas(),
            "unidades_estructuradas_referencia": verificables.fuentes.estadisticas_estructuradas(),
        },
        limites=(
            "Solo se detectan frases/alias completos tokenizados; sin stemming, traducción o inferencia de sinonimia",
            "Tokens de hasta tres caracteres conservan mayúsculas; NFKC no constituye un analizador de fórmulas",
            "Una mención, incluso negada, no demuestra enseñanza, dominio, cobertura o pertinencia de grado",
            "Definiciones, traducciones, niveles y rutas históricas no son evidencia primaria por sí mismos",
            "SHA y localizador verificado prueban identidad documental; falta revisar la implicación semántica",
            "No se calculan medianas de oportunidad ni equivalencias entre grados de sistemas educativos",
            "No se aceptan enlaces ni se crea TRABAJA/CUBRE/DAG/propuesta/simulación a partir de estas hipótesis",
        ),
    )
