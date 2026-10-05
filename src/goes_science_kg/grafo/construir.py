"""Construye el grafo v0 con lo que ya existe: mallas, marcos, países y sus alineaciones.

El v0 NO inventa nada: solo traduce a nodos y aristas los datos del trabajo previo
(reportes/cobertura_curricular), con su evidencia. Conceptos, prerrequisitos y la propuesta
curricular se agregan en fases posteriores (specs/08_plan_de_implementacion.md).
"""

from __future__ import annotations

from goes_science_kg.config import cargar
from goes_science_kg.disciplinas import asignatura_de_objetivo, asignatura_de_tema
from goes_science_kg.ingesta import legado
from goes_science_kg.ingesta.mallas import TemaMalla, extraer
from goes_science_kg.modelos import Arista, Confianza, Fuente, Nodo, TipoArista, TipoNodo

VERSION_GRAFO = "v0"
CODIGO_PAIS = {"Uruguay": "UY", "Colombia": "CO", "Singapur": "SG", "Chile": "CL"}


class Constructor:
    def __init__(self) -> None:
        self.nodos: dict[str, Nodo] = {}
        self.aristas: dict[tuple, Arista] = {}

    # -- utilidades -------------------------------------------------------------------------
    def nodo(self, **kw) -> str:
        n = Nodo(**kw)
        self.nodos.setdefault(n.id, n)
        return n.id

    def arista(self, **kw) -> None:
        a = Arista(**kw)
        self.aristas.setdefault(a.clave, a)

    @staticmethod
    def _confianza(v: str | None) -> Confianza | None:
        return Confianza(v) if v in {c.value for c in Confianza} else None

    # -- capas ------------------------------------------------------------------------------
    def base(self) -> None:
        for asig, a in cargar("asignaturas")["asignaturas"].items():
            self.nodo(id=f"ASIG:{asig}", tipo=TipoNodo.ASIGNATURA, etiqueta=a["nombre"], asignatura=asig,
                      props={"grados": a["grados"]})
        for g in range(2, 12):
            self.nodo(id=f"GRADO:{g:02d}", tipo=TipoNodo.GRADO, etiqueta=f"{g}.° grado", grado=g)
        for d in legado.manifiesto_fuentes():
            self.nodo(id=f"DOC:{d['id']}", tipo=TipoNodo.DOCUMENTO, etiqueta=d["titulo"],
                      props={k: d.get(k) for k in ("organismo", "anio", "url", "archivo_local", "sha256", "ok")})
        for item in cargar("mallas")["archivos"]:
            nombre = item.get("canonico", item["archivo"])
            self.nodo(id=f"DOC:MALLA:{nombre}", tipo=TipoNodo.DOCUMENTO, etiqueta=f"Malla MINED · {nombre}",
                      props={"organismo": "MINED El Salvador", "archivo_local":
                             f"{cargar('mallas')['directorio']}/{item['archivo']}"})
        for clave, m in cargar("marcos")["marcos"].items():
            self.nodo(id=f"MARCO:{clave}", tipo=TipoNodo.MARCO, etiqueta=m["nombre"],
                      props={"organismo": m["organismo"], "grados_sv": m.get("grados_sv", []),
                             **({"metas_dominio": m["metas_dominio"]} if "metas_dominio" in m else {}),
                             **({"metas_cognitivas": m["metas_cognitivas"]} if "metas_cognitivas" in m else {})})

    def _objetivo(self, codigo: str, marco: str, etiqueta: str, doc: str, pagina: int | None, props: dict,
                  localizador: str | None = None) -> None:
        asig = asignatura_de_objetivo(codigo) if marco != "T23" else None
        oid = self.nodo(id=f"OBJ:{codigo}", tipo=TipoNodo.OBJETIVO_MARCO, etiqueta=etiqueta, asignatura=asig,
                        fuente=Fuente(documento=doc, pagina=pagina, localizador=localizador),
                        props={"marco": marco, **props})
        self.arista(origen=oid, destino=f"MARCO:{marco}", tipo=TipoArista.EN_MARCO, metodo="catalogo")
        self.arista(origen=oid, destino=f"DOC:{doc}", tipo=TipoArista.FUENTE, metodo="catalogo",
                    props={"pagina": pagina, "localizador": localizador})
        if asig:
            self.arista(origen=oid, destino=f"ASIG:{asig}", tipo=TipoArista.DE_ASIGNATURA, metodo="regla")

    def marcos(self) -> None:
        for o in legado.catalogo_timss2027():
            self._objetivo(o["codigo"], o["marco"], o["objetivo"], "timss27", o.get("pagina_fuente"), {
                "dominio": o["dominio"], "area_codigo": o["area_codigo"], "area": o["area"],
                "titulo_en": o.get("titulo_en"), "ambiental": o.get("ambiental", False),
                "es_investigacion": o.get("es_investigacion", False),
                "subitems": o.get("subitems", []), "pagina_pdf": o.get("pagina_pdf")})
        for o in legado.catalogo_timss_v1():
            marco, doc = ("TA15", "timssadv15") if o["marco"] == "TA" else ("T23", "timss23")
            self._objetivo(o["codigo"], marco, o["objetivo"], doc, o.get("pagina"), {
                "nivel": o["marco"], "dominio": o["dominio"], "area_codigo": o["area_codigo"], "area": o["area"]})
        tipos = set(cargar("marcos")["marcos"]["PISA25"]["tipos_objetivo"])
        for e in legado.catalogo_pisa2025()["elementos"]:
            if e["tipo"] in tipos:
                self._objetivo(e["codigo"], "PISA25", e["texto"], "pisa25final", e.get("pagina"), {
                    "tipo_conocimiento": e["tipo"], "grupo": e.get("grupo"), "titulo_en": e.get("titulo_en")})
        docs = legado.documento_por_archivo()
        for o in legado.catalogo_acara_senior():
            self._objetivo(o["codigo"], "AUSS", o["objetivo"], docs[o["documento"]], None, {
                "unidad": o["unidad"], "unidad_titulo": o.get("unidad_titulo"),
                "unidad_titulo_en": o["unidad_titulo_en"], "eje": o["eje"], "tema": o.get("tema"),
                "tema_en": o["tema_en"], "texto_en": o["texto_en"],
                "es_investigacion": o["eje"] == "indagacion"}, localizador=o["localizador"])
        for r in legado.equivalencias_timss():
            if r["codigo_2023"] and r["codigo_2027"] and f"OBJ:{r['codigo_2027']}" in self.nodos:
                self.arista(origen=f"OBJ:{r['codigo_2023']}", destino=f"OBJ:{r['codigo_2027']}",
                            tipo=TipoArista.EQUIVALE_A, metodo="catalogo",
                            props={"tipo": r["tipo"], "nota": r["nota"]})

    def temas(self, temas: list[TemaMalla]) -> None:
        ct, cp, ca = legado.clasificacion_timss(), legado.clasificacion_pisa(), legado.clasificacion_auss()
        for t in temas:
            llave = (t.archivo, t.hoja, t.fila)
            timss, pisa, auss = ct.get(llave), cp.get(llave), ca.get(llave)
            asig, metodo = asignatura_de_tema(t.asignatura, timss, pisa)
            tid = self.nodo(
                id=f"TEMA:{t.id}", tipo=TipoNodo.TEMA, etiqueta=t.procedimental, asignatura=asig, grado=t.grado,
                fuente=Fuente(documento=f"MALLA:{t.archivo}", hoja=t.hoja, fila=t.fila),
                props={"asignatura_malla": t.asignatura, "metodo_asignatura": metodo, "unidad": t.unidad,
                       "contenido": t.contenido, "subcontenido": t.subcontenido, "indicador": t.indicador,
                       "evidencia": t.evidencia, "habilidad_timss": t.habilidad_timss,
                       "competencia_pisa": t.competencia_pisa, "micro_pisa": t.micro_pisa,
                       "estado_timss": (timss or {}).get("obj1") if (timss or {}).get("obj1") in
                       ("FUERA", "PENDIENTE") else None})
            self.arista(origen=tid, destino=f"GRADO:{t.grado:02d}", tipo=TipoArista.EN_GRADO, metodo="malla")
            self.arista(origen=tid, destino=f"DOC:MALLA:{t.archivo}", tipo=TipoArista.FUENTE, metodo="malla",
                        props={"hoja": t.hoja, "fila": t.fila})
            if asig:
                self.arista(origen=tid, destino=f"ASIG:{asig}", tipo=TipoArista.DE_ASIGNATURA,
                            metodo="malla" if metodo == "malla" else "regla", props={"via": metodo})
            if timss:
                for rol, campo in (("principal", "obj1"), ("secundario", "obj2")):
                    self._cubre(tid, timss.get(campo), rol, timss, "timss")
            if auss:
                self._cubre(tid, auss.get("obj1"), "principal", auss, "auss")
                self._cubre(tid, auss.get("obj2"), "secundario", auss, "auss")
            if pisa:
                self._cubre(tid, pisa.get("cont1"), "principal", pisa, "pisa")
                self._cubre(tid, pisa.get("cont2"), "secundario", pisa, "pisa")
                for cod in [*pisa.get("proc", []), *pisa.get("epis", [])]:
                    self._cubre(tid, cod, "elemento", pisa, "pisa")

    def _cubre(self, tid: str, codigo: str | None, rol: str, c: dict, via: str) -> None:
        if not codigo or codigo in ("FUERA", "PENDIENTE") or f"OBJ:{codigo}" not in self.nodos:
            return
        extra = {k: c[k] for k in ("conocimiento", "contexto", "area", "demanda") if via == "pisa" and k in c}
        self.arista(origen=tid, destino=f"OBJ:{codigo}", tipo=TipoArista.CUBRE, rol=rol,
                    confianza=self._confianza(c.get("confianza")), justificacion=c.get("justificacion"),
                    version=c.get("version"), metodo="ia",
                    props={"revisado_por": c.get("revisado_por") or None, **extra})

    def paises(self) -> None:
        docs = legado.documento_por_archivo()
        for o in legado.alineacion_paises():
            cod = CODIGO_PAIS[o["pais"]]
            pid = self.nodo(id=f"PAIS:{cod}", tipo=TipoNodo.PAIS, etiqueta=o["pais"])
            doc = docs.get(o["documento"], o["documento"])
            asig = asignatura_de_objetivo(o["obj1"]) if o.get("obj1") not in (None, "", "FUERA") else None
            oid = self.nodo(id=f"OP:{o['id']}", tipo=TipoNodo.OBJETIVO_PAIS, etiqueta=o["texto"], asignatura=asig,
                            grado=o.get("grado_min"), fuente=Fuente(documento=doc, pagina=o.get("pagina")),
                            props={"pais": cod, "grado_min": o.get("grado_min"), "grado_max": o.get("grado_max"),
                                   "grado_o_tramo": o.get("grado_o_tramo"), "eje": o.get("eje"),
                                   "tipo": o.get("tipo"), "marco_alineacion": o.get("marco")})
            self.arista(origen=oid, destino=pid, tipo=TipoArista.DE_PAIS, metodo="catalogo")
            if f"DOC:{doc}" in self.nodos:
                self.arista(origen=oid, destino=f"DOC:{doc}", tipo=TipoArista.FUENTE, metodo="catalogo",
                            props={"pagina": o.get("pagina")})
            if asig:
                self.arista(origen=oid, destino=f"ASIG:{asig}", tipo=TipoArista.DE_ASIGNATURA, metodo="regla",
                            props={"via": "alineacion"})
            for rol, campo in (("principal", "obj1"), ("secundario", "obj2")):
                cod_obj = o.get(campo)
                if cod_obj and f"OBJ:{cod_obj}" in self.nodos:
                    self.arista(origen=oid, destino=f"OBJ:{cod_obj}", tipo=TipoArista.ALINEA_CON, rol=rol,
                                confianza=self._confianza(o.get("confianza")), justificacion=o.get("justificacion"),
                                version=o.get("version"), metodo="ia",
                                props={"revisado_por": o.get("revisado_por") or None})


def construir() -> tuple[list[Nodo], list[Arista]]:
    c = Constructor()
    c.base()
    c.marcos()
    c.temas(extraer())
    c.paises()
    nodos = sorted(c.nodos.values(), key=lambda n: (n.tipo, n.id))
    aristas = sorted(c.aristas.values(), key=lambda a: (a.tipo, a.origen, a.destino, a.rol or ""))
    return nodos, aristas
