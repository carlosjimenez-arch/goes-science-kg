"""Indexed projections of published evidence for the GOEs curriculum interface."""

from __future__ import annotations

import re
import unicodedata
from collections import Counter, defaultdict
from urllib.parse import urlparse

from goes_science_kg.curriculo.contratos import FilaCurricular
from goes_science_kg.producto.mejoras_contratos import ROLES_MEJORA
from goes_science_kg.producto.runtime import RuntimeProducto


def normalizar(texto: str) -> str:
    """Normalize accents and case for deterministic substring matching."""
    return "".join(c for c in unicodedata.normalize("NFKD", str(texto).casefold()) if not unicodedata.combining(c))


def orden_natural(texto: str) -> tuple:
    """Sort mixed text and numeric unit labels in their natural order."""
    return tuple((0, int(p)) if p.isdigit() else (1, p.casefold()) for p in re.split(r"(\d+)", texto))


def url_publica(valor: object) -> str | None:
    """Accept only valid HTTP or HTTPS documentary links without embedded credentials."""
    if not isinstance(valor, str):
        return None
    try:
        u = urlparse(valor)
        return valor if u.scheme in {"https", "http"} and u.hostname and not u.username and not u.password else None
    except ValueError:
        return None


class ConsultaInterfaz:
    """Index one verified snapshot without generating claims or changing reviews."""

    def __init__(self, runtime: RuntimeProducto) -> None:
        self.runtime = runtime
        self.producto = p = runtime.producto
        if p.mejoras is None:
            raise ValueError("La aplicación requiere una publicación con propuestas curriculares")
        self.identidad = {"version_curriculo": "V4", "snapshot_id": p.manifest.snapshot_id}
        self.filas = {f.id: f for f in p.curriculo.filas}
        self.casos = {c.preparacion.id: c for c in p.mejoras.unidades}
        self.decisiones = {d.fila_id: d for d in p.catalogo.filas}
        self.por_fila, self.propuestas = {}, {}
        for caso in p.mejoras.unidades:
            for f in caso.preparacion.filas_originales:
                self.por_fila[f["id"]] = caso
            if caso.resultado.propuesta:
                self.propuestas.update({f.fila_id: f for f in caso.resultado.propuesta.filas})
        self.nodos = {n.id: n for n in p.nodos}
        self.vecinos = defaultdict(set)
        self.aristas_por_nodo = defaultdict(list)
        for a in p.aristas:
            self.vecinos[a.origen].add(a.destino)
            self.vecinos[a.destino].add(a.origen)
            self.aristas_por_nodo[a.origen].append(a)
            if a.destino != a.origen:
                self.aristas_por_nodo[a.destino].append(a)
        self.documentos = self._documentos()

        self._texto_por_fila = {
            f.id: normalizar(
                " ".join(
                    (
                        f.procedimental,
                        f.unidad,
                        f.contenido,
                        f.asignatura_malla,
                        self.propuestas[f.id].objetivo_propuesto if f.id in self.propuestas else "",
                    )
                )
            )
            for f in p.curriculo.filas
        }
        self._ids_por_grado = defaultdict(set)
        self._ids_por_disciplina = defaultdict(set)
        for f in p.curriculo.filas:
            self._ids_por_grado[f.grado].add(f.id)
            for disciplina in self.decisiones[f.id].disciplinas:
                self._ids_por_disciplina[disciplina].add(f.id)
        self._orden_filas = tuple(
            sorted(
                self.filas,
                key=lambda i: (
                    self.filas[i].grado,
                    self.filas[i].asignatura_malla,
                    self.filas[i].hoja,
                    self.filas[i].fila,
                ),
            )
        )

    def seleccionar(self, grado: int | None = None, disciplina: str | None = None, q: str = "") -> list[FilaCurricular]:
        """Intersect grade and subject indexes before searching normalized row text."""
        consulta = normalizar(q).strip()
        ids = self.filas.keys()
        if grado is not None:
            ids = ids & self._ids_por_grado.get(grado, set())
        if disciplina is not None:
            ids = ids & self._ids_por_disciplina.get(disciplina, set())
        return [
            self.filas[i]
            for i in self._orden_filas
            if i in ids and (not consulta or consulta in self._texto_por_fila[i])
        ]

    def ficha(self, f: FilaCurricular) -> dict:
        """Return row metadata, proposal availability, review state, and original alerts."""
        c, propuesta = self.por_fila[f.id], self.propuestas.get(f.id)
        return {
            "id": f.id,
            "grado": f.grado,
            "asignatura": f.asignatura_malla,
            "unidad": f.unidad,
            "objetivo_original": f.procedimental,
            "objetivo_propuesto": propuesta.objetivo_propuesto if propuesta else None,
            "accion": propuesta.accion if propuesta else None,
            "disciplinas": self.decisiones[f.id].disciplinas,
            "estado_clasificacion": self.decisiones[f.id].estado,
            "estado_revision": c.resultado.estado,
            "preparacion_id": c.preparacion.id,
            "fuera_alcance": propuesta is not None and propuesta.accion == "fuera_alcance",
            "alerta_original": self.runtime.fuentes.bloqueos_efectivos.get(f.id),
            "hoja": f.hoja,
            "fila": f.fila,
        }

    def resumen(self) -> dict:
        """Compute snapshot counts and explicitly report disconnected integrations."""
        p = self.producto
        grupos = defaultdict(list)
        for f in p.curriculo.filas:
            grupos[f.grado].append(f)
        grados = []
        for grado, filas in sorted(grupos.items()):
            ids = {f.id for f in filas}
            unidades = {self.por_fila[i].preparacion.id for i in ids}
            grados.append(
                {
                    "grado": grado,
                    "filas": len(filas),
                    "unidades": len(unidades),
                    "propuestas_ciencias": sum(
                        i in self.propuestas and self.propuestas[i].accion != "fuera_alcance" for i in ids
                    ),
                    "alertas_originales": len(ids.intersection(self.runtime.fuentes.bloqueos_efectivos)),
                }
            )
        return self.identidad | {
            "archivo_id": p.mejoras.id,
            "cobertura": p.mejoras.cobertura,
            "nodos": len(p.nodos),
            "aristas": len(p.aristas),
            "fuentes": len(self.documentos),
            "tipos_nodo": dict(Counter(n.tipo for n in p.nodos)),
            "tipos_arista": dict(Counter(a.tipo for a in p.aristas)),
            "clasificaciones": dict(Counter(d.estado for d in p.catalogo.filas)),
            "acciones": dict(Counter(f.accion for f in self.propuestas.values())),
            "alertas_originales": len(self.runtime.fuentes.bloqueos_efectivos),
            "grados": grados,
            "disciplinas": sorted({d for f in p.catalogo.filas for d in f.disciplinas}),
            "unidades": sorted(
                (
                    {
                        "id": c.preparacion.id,
                        **c.preparacion.solicitud.model_dump(mode="json"),
                        "filas": len(c.preparacion.filas_originales),
                        "estado": c.resultado.estado,
                        "rondas": len(c.resultado.rondas),
                    }
                    for c in p.mejoras.unidades
                ),
                key=lambda u: (u["grado"], u["asignatura_malla"], orden_natural(u["unidad"])),
            ),
            "limite": p.mejoras.limite,
            "integraciones": {
                "lxp": {"estado": "sin_datos", "clases": None, "escuelas": None, "evaluaciones": None},
                "territorio": {"estado": "sin_datos", "departamentos": None},
                "aprobacion_institucional": {"estado": "no_acreditada"},
                "usuarios": {"estado": "sin_proveedor_de_identidad"},
            },
        }

    def _documentos(self) -> dict:
        """Collect source identities and count distinct unit-level evidence uses."""
        documentos = {}
        for id_, registro in self.runtime.fuentes.catalogo.items():
            nodo = self.nodos.get("DOC:" + id_)
            procedencia = registro.get("procedencia", {})
            url = registro.get("url_documento") or registro.get("url")
            if not url:
                url = procedencia.get("archivo", {}).get("url")
            documentos[id_] = {
                "id": id_,
                "titulo": nodo.etiqueta if nodo else registro.get("titulo", id_),
                "sha256": registro.get("sha256"),
                "url": url_publica(url),
                "tipo": "curriculo" if registro.get("version_curriculo") == "V4" else "referencia",
                "version_documental": registro.get("version_documental", "V4"),
                "licencia": registro.get("licencia"),
                "usos": 0,
            }
        for c in self.producto.mejoras.unidades:
            vistos = set()
            for e in c.preparacion.evidencias:
                fuente = e.fuente
                id_ = fuente.get("documento")
                if not id_:
                    continue
                if id_ not in documentos:
                    documentos[id_] = {
                        "id": id_,
                        "titulo": fuente.get("titulo", id_.replace("_", " ")),
                        "sha256": fuente.get("sha256"),
                        "url": url_publica(fuente.get("url")),
                        "tipo": "referencia",
                        "version_documental": fuente.get("version_documental"),
                        "licencia": fuente.get("licencia"),
                        "usos": 0,
                    }
                if id_ not in vistos:
                    documentos[id_]["usos"] += 1
                    vistos.add(id_)
        return documentos

    def grafo(self, *, grado=None, disciplina=None, q="", limite=220) -> dict:
        """Select a bounded real subgraph, preserving edge types and both endpoints."""
        if grado is None and disciplina is None and not q.strip():
            permitidos = set(self.nodos)
        else:
            semillas = {f.id for f in self.seleccionar(grado, disciplina, q)}
            permitidos = semillas | set().union(*(self.vecinos[i] for i in semillas)) if semillas else set()
        # Expandir vecindarios de filas conserva sus unidades, propuestas y fuentes en la muestra.
        # El recorte anterior por tipo podía gastar todo el cupo en unidades sin sus relaciones.
        prioridad = {"Tema": 0, "Unidad": 1, "MejoraCurricular": 2, "RevisionUnidad": 3}

        def clave(id_):
            return prioridad.get(self.nodos[id_].tipo, 4), -len(self.vecinos[id_]), id_

        elegidos, vistos = [], set()
        for raiz in sorted(permitidos, key=clave):
            for id_ in [raiz, *sorted(self.vecinos[raiz].intersection(permitidos), key=clave)]:
                if id_ not in vistos and len(elegidos) < limite:
                    elegidos.append(id_)
                    vistos.add(id_)
            if len(elegidos) == limite:
                break
        ids = set(elegidos)
        aristas = [a for a in self.producto.aristas if a.origen in ids and a.destino in ids]
        return self.identidad | {
            "total_nodos_filtrados": len(permitidos),
            "limite": limite,
            "recortado": len(permitidos) > len(elegidos),
            "nodos": [
                {
                    "id": i,
                    "tipo": self.nodos[i].tipo,
                    "etiqueta": self.nodos[i].etiqueta,
                    "grado": self.nodos[i].grado,
                    "asignatura": self.nodos[i].asignatura,
                    "conexiones": len(self.vecinos[i]),
                }
                for i in elegidos
            ],
            "aristas": [{"origen": a.origen, "destino": a.destino, "tipo": a.tipo} for a in aristas],
            "limite_semantico": "La disposición es visual. Cada arista conserva su tipo; no todas son prerrequisitos.",
        }

    def detalle(self, fila_id: str) -> dict:
        """Expose a row and the evidence cited by its selected proposal."""
        f = self.filas[fila_id]
        c = self.por_fila[fila_id]
        propuesta = self.propuestas.get(fila_id)
        ids_fragmentos = set(propuesta.fragmentos_ids) if propuesta else set()
        ids_evidencias = {x.evidencia_id for x in c.preparacion.fragmentos if x.id in ids_fragmentos}
        return self.identidad | {
            **self.ficha(f),
            "original": f.model_dump(mode="json", exclude={"celdas"}),
            "propuesta": propuesta.model_dump(mode="json") if propuesta else None,
            "contexto_aula": c.preparacion.contexto_aula,
            "revisiones": self.revisiones(c),
            "motivos": c.resultado.motivos,
            "enmiendas": c.preparacion.correcciones_requeridas,
            "fragmentos": [x.model_dump(mode="json") for x in c.preparacion.fragmentos if x.id in ids_fragmentos],
            "evidencias": [e.model_dump(mode="json") for e in c.preparacion.evidencias if e.id in ids_evidencias],
            "limite": self.producto.mejoras.limite,
        }

    @staticmethod
    def revisiones(caso) -> dict:
        """Return the last recorded review round without re-evaluating votes."""
        ultima = caso.resultado.rondas[-1]
        return {
            "rondas": len(caso.resultado.rondas),
            "roles_esperados": ROLES_MEJORA,
            "dictamenes": [d.model_dump(mode="json") for d in ultima.dictamenes],
            "errores_estructura": ultima.errores_estructura,
        }

    def revision(self, grado=None, disciplina=None, q="", estado=None) -> dict:
        """Filter published unit reviews using the same row selection indexes."""
        ids = {self.por_fila[f.id].preparacion.id for f in self.seleccionar(grado, disciplina, q)}
        casos = [c for id_, c in self.casos.items() if id_ in ids and (estado is None or c.resultado.estado == estado)]
        return self.identidad | {
            "total": len(casos),
            "columnas": dict(Counter(c.resultado.estado for c in casos)),
            "unidades": [
                {
                    "id": c.preparacion.id,
                    **c.preparacion.solicitud.model_dump(mode="json"),
                    "estado": c.resultado.estado,
                    "motivos": c.resultado.motivos,
                    "filas": len(c.preparacion.filas_originales),
                    **self.revisiones(c),
                }
                for c in casos
            ],
            "limite": self.producto.mejoras.limite,
        }

    def brief(self, fila_id: str, formato: str) -> dict:
        """Compile existing evidence and proposals into a traceable Markdown brief."""
        detalle = self.detalle(fila_id)
        propuesta = self.propuestas.get(fila_id)
        if propuesta is None or propuesta.accion == "fuera_alcance":
            raise ValueError("La fila no dispone de una propuesta de Ciencias respaldada")
        f = self.filas[fila_id]
        campos = [
            ("Objetivo", propuesta.objetivo_propuesto),
            ("Indicador observable", propuesta.indicador_observable),
            ("Producto evaluable", propuesta.producto_evaluable),
            ("Criterio de evaluación", propuesta.criterio_evaluacion),
            ("Orientación didáctica", propuesta.orientacion_didactica),
            ("Andamiaje", propuesta.andamiaje),
            ("Contexto salvadoreño propuesto", propuesta.contexto_salvador),
            ("Seguridad", propuesta.seguridad),
            ("Recursos condicionales", "; ".join(propuesta.recursos_condicionales)),
        ]
        titulo = f"{f.asignatura_malla} · {f.grado}.º · {f.procedimental}"
        partes = [
            "# " + titulo,
            "",
            "Formato de organización: " + formato,
            "",
            "Brief documental compilado desde una propuesta respaldada; no es una clase generada nueva.",
            "",
        ]
        for nombre, texto in campos:
            partes.extend(["## " + nombre, texto, ""])
        if formato == "cinco_fases":
            partes.extend(["## Cinco fases del insumo original", ""])
            for nombre, fase in f.fases.items():
                partes.extend(
                    [
                        "### " + nombre.capitalize(),
                        fase.texto if fase.presente_en_hoja else "Ausente en el insumo; no se inventa una actividad.",
                        "",
                    ]
                )
        partes.extend(
            [
                "## Trazabilidad",
                f"Fila: {fila_id}",
                f"Snapshot: {self.producto.manifest.snapshot_id}",
                f"Archivo curricular: {self.producto.mejoras.id}",
                "",
            ]
        )
        for evidencia in detalle["evidencias"]:
            partes.append(
                f"- {evidencia['id']} · {evidencia['fuente'].get('documento')} · "
                f"SHA {evidencia['fuente'].get('sha256', 'en el expediente')}"
            )
        partes.extend(["", self.producto.mejoras.limite])
        return self.identidad | {
            "fila_id": fila_id,
            "formato": formato,
            "titulo": titulo,
            "markdown": "\n".join(partes),
            "llamadas_modelos": 0,
        }
