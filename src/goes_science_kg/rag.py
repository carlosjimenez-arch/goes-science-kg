"""GraphRAG sobre el grafo de Ciencias (local, por grado).

Recuperación (determinista, sin red):
1. Índice léxico BM25 en español sobre los nodos con texto (temas, conceptos, prácticas, objetivos de marco
   y de países). Normaliza tildes y quita palabras vacías.
2. Semillas: los k nodos con mejor puntaje, filtrados por grado y asignatura si se pide.
3. Expansión por el grafo: vecinos a 1–2 saltos por aristas con significado curricular
   (TRABAJA, CUBRE, ALINEA_CON, PRERREQUISITO_DE). El puntaje decae por salto y depende del tipo de arista;
   los temas fuera del grado pedido se penalizan.
4. Contexto: los nodos mejor puntuados, como bloques de evidencia citables (id, tipo, grado, fuente con
   documento y página, u hoja y fila) más las relaciones entre ellos.

Generación (opcional, `responder()`): manda el contexto a Claude (SDK oficial de Anthropic) con la instrucción
de responder solo con esa evidencia y citar los ids. Requiere `uv sync --extra rag` y credenciales de Anthropic.
"""

from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from goes_science_kg.modelos import Arista, Nodo, TipoArista, TipoNodo

TIPOS_INDEXADOS = {TipoNodo.TEMA, TipoNodo.CONCEPTO, TipoNodo.PRACTICA, TipoNodo.OBJETIVO_MARCO,
                   TipoNodo.OBJETIVO_PAIS}
PESO_ARISTA = {TipoArista.TRABAJA: 1.0, TipoArista.PRERREQUISITO_DE: 0.9, TipoArista.CUBRE: 0.8,
               TipoArista.ALINEA_CON: 0.6}
VACIAS = set("""a al algo ante con contra de del desde donde durante e el ella ellas ellos en entre era es esa
ese eso esta este esto estos estas ha han hasta la las le les lo los mas me mi muy no nos o otra otro para
pero por que se sea ser si sin sobre su sus tambien te tiene tienen tu un una uno unos unas y ya cual cuales
como cuando grado grados tema temas estudiante estudiantes alumno alumnos docente docentes deben debe saber
sabe necesita necesitan dominar dominan comprender entender trabajar trabaja relacion ideas idea antes despues
consolidadas consolidado previo previos aborda abordan ensena ensenan ensenar cual cuales que quien donde
para hacer pais paises otros""".split())
INTENCION_PRERREQ = re.compile(r"\b(antes de|previo|previos|prerrequisit|deben saber|deben dominar|necesitan? saber|"
                               r"base para|para comprender|para entender|consolidad)", re.I)
# Raíces sin tildes (se comparan con la consulta sin tildes): nombre del país y gentilicio.
PAIS_NOMBRADO = {"uruguay": "UY", "colombia": "CO", "singapur": "SG", "inglaterra": "ENG", "ingles": "ENG",
                 "britanic": "ENG", "australia": "AU", "japon": "JP", "japones": "JP"}
INTENCION_PAISES = re.compile(r"\b(pais|paises|internacional|otros sistemas|compar|" + "|".join(PAIS_NOMBRADO) + ")")
INTENCION_MARCO = re.compile(
    r"\b(timss|pisa|acara|australian|marco|marcos|evaluaci[oó]n internacional|objetivos? internacional)", re.I)
MARCO_NOMBRADO = {"timss": ("T4_27", "T8_27", "TA15"), "pisa": ("PISA25",), "acara": ("AUSS",),
                  "australian": ("AUSS",)}
PESO_MARCO = 1.0  # ablación 1,0–1,8 sin mejora en preguntas de marco (data/evaluacion/resultados.md)
PESO_TIPO = {TipoNodo.CONCEPTO: 1.15}  # ablación en data/evaluacion/resultados.md


def _sin_tildes(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto.lower()) if unicodedata.category(c) != "Mn")


def normalizar(texto: str) -> list[str]:
    t = unicodedata.normalize("NFKD", (texto or "").lower()).encode("ascii", "ignore").decode()
    return [w for w in re.findall(r"[a-z0-9]+", t) if len(w) > 2 and w not in VACIAS]


def _texto(n: Nodo) -> str:
    p = n.props
    partes = [n.etiqueta, p.get("definicion"), p.get("unidad"), p.get("contenido"), p.get("subcontenido"),
              p.get("indicador"), p.get("area"), p.get("tema"), p.get("texto_en"), p.get("titulo_en"),
              " ".join(p.get("sinonimos") or [])]
    return " ".join(x for x in partes if isinstance(x, str) and x)


class BM25:
    def __init__(self, docs: dict[str, list[str]], k1: float = 1.4, b: float = 0.75):
        self.docs, self.k1, self.b = docs, k1, b
        self.largo_medio = sum(map(len, docs.values())) / max(1, len(docs))
        df = Counter(t for toks in docs.values() for t in set(toks))
        n = len(docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}
        self.tf = {d: Counter(toks) for d, toks in docs.items()}

    def puntaje(self, consulta: list[str], doc: str) -> float:
        tf, largo = self.tf[doc], len(self.docs[doc])
        s = 0.0
        for t in consulta:
            if t in tf:
                f = tf[t]
                s += self.idf[t] * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * largo / self.largo_medio))
        return s


@dataclass
class Contexto:
    consulta: str
    grado: int | None
    asignatura: str | None
    nodos: list[tuple[Nodo, float]] = field(default_factory=list)
    relaciones: list[Arista] = field(default_factory=list)

    def como_texto(self) -> str:
        md = [f"Consulta: {self.consulta}",
              f"Filtro: grado={self.grado or 'todos'} asignatura={self.asignatura or 'todas'}",
             "", "## Evidencia"]
        for n, _s in self.nodos:
            f = n.fuente
            cita = ("" if not f else f"{f.documento}" + (f" p.{f.pagina}" if f.pagina else "")
                    + (f" {f.localizador}" if f.localizador else "")
                    + (f" hoja «{f.hoja}» fila {f.fila}" if f.hoja else ""))
            extra = n.props.get("definicion") or n.props.get("unidad") or ""
            extra = extra if isinstance(extra, str) else ""
            md.append(f"[{n.id}] ({n.tipo.value}{', ' + str(n.grado) + '.°' if n.grado else ''}"
                     f"{', ' + n.asignatura if n.asignatura else ''}) {n.etiqueta}"
                      + (f" — {extra}" if extra and extra != n.etiqueta else "")
                      + (f" · fuente: {cita}" if cita else ""))
        md += ["", "## Relaciones"]
        md += [f"{a.origen} -{a.tipo.value}{'/' + a.rol if a.rol else ''}-> {a.destino}" for a in self.relaciones]
        return "\n".join(md)


class GraphRAG:
    def __init__(self, nodos: list[Nodo], aristas: list[Arista]):
        self.por_id = {n.id: n for n in nodos}
        self.vecinos: dict[str, list[tuple[str, Arista]]] = defaultdict(list)
        for a in aristas:
            if a.tipo in PESO_ARISTA:
                self.vecinos[a.origen].append((a.destino, a))
                self.vecinos[a.destino].append((a.origen, a))
        self.bm25 = BM25({n.id: normalizar(_texto(n)) for n in nodos if n.tipo in TIPOS_INDEXADOS})

    def _admite(self, n: Nodo, grado: int | None, asignatura: str | None) -> bool:
        if n.props.get("marco") == "T23":  # TIMSS 2023 es referencia secundaria: no entra al contexto
            return False
        if asignatura and n.asignatura and n.asignatura != asignatura:
            return False
        if grado and n.tipo == TipoNodo.TEMA and n.grado != grado:
            return False
        return True

    def _ancestros(self, puntos: dict[str, float], asignatura: str | None, saltos: int = 2) -> None:
        """Consulta de prerrequisitos: sube por el DAG desde los conceptos mejor puntuados."""
        conceptos = sorted((d for d in puntos if d.startswith("CON:")), key=lambda d: -puntos[d])[:3]
        frontera = {c: puntos[c] for c in conceptos}
        for salto in range(1, saltos + 1):
            nueva = {}
            for d, s in frontera.items():
                for v, a in self.vecinos[d]:
                    if a.tipo == TipoArista.PRERREQUISITO_DE and a.destino == d and v in self.por_id \
                            and self._admite(self.por_id[v], None, asignatura):
                        nueva[v] = max(nueva.get(v, 0.0), s * (0.95 ** salto))
            for v, s in nueva.items():
                puntos[v] = max(puntos.get(v, 0.0), s)
            frontera = nueva

    @staticmethod
    def _foco(n: Nodo, grado: int | None) -> float:
        """Con un grado elegido, prioriza los temas de ese grado y atenúa lo que es de otros grados."""
        if not grado or n.grado is None:
            return 1.0
        return 1.5 if (n.tipo == TipoNodo.TEMA and n.grado == grado) else 0.5 if n.grado != grado else 1.0

    def recuperar(self, consulta: str, grado: int | None = None, asignatura: str | None = None,
                  k_semillas: int = 8, saltos: int = 2, k_final: int = 25) -> Contexto:
        q = normalizar(consulta)
        plano = _sin_tildes(consulta)
        paises = INTENCION_PAISES.search(plano)
        nombrados = {c for p, c in PAIS_NOMBRADO.items() if re.search(rf"\b{p}", plano)}
        marco = INTENCION_MARCO.search(consulta)
        marcos = {m for clave, ms in MARCO_NOMBRADO.items() if clave in consulta.lower() for m in ms}

        def peso(n: Nodo) -> float:
            w = self._foco(n, grado) * PESO_TIPO.get(n.tipo, 1.0)
            if paises and n.tipo == TipoNodo.OBJETIVO_PAIS:
                w *= 2.0 if (not nombrados or n.props.get("pais") in nombrados) else 0.5
            if marco and n.tipo == TipoNodo.OBJETIVO_MARCO:
                w *= PESO_MARCO if (not marcos or n.props.get("marco") in marcos) else 0.6
            return w

        candidatos = [(d, self.bm25.puntaje(q, d) * peso(self.por_id[d])) for d in self.bm25.docs]
        semillas = sorted(((d, s) for d, s in candidatos if s > 0 and self._admite(self.por_id[d], grado, asignatura)),
                          key=lambda x: (-x[1], x[0]))[:k_semillas]
        puntos: dict[str, float] = {d: s for d, s in semillas}
        frontera = dict(puntos)
        for salto in range(1, saltos + 1):
            nueva: dict[str, float] = {}
            for d, s in frontera.items():
                for v, a in self.vecinos[d]:
                    n = self.por_id.get(v)
                    if not n or not self._admite(n, None, asignatura):
                        continue
                    factor = PESO_ARISTA[a.tipo] * (0.5 ** salto)
                    if grado and n.tipo == TipoNodo.TEMA and n.grado != grado:
                        factor *= 0.3
                    nueva[v] = max(nueva.get(v, 0.0), s * factor)
            for v, s in nueva.items():
                if s > puntos.get(v, 0.0):
                    puntos[v] = s
            frontera = nueva
        if INTENCION_PRERREQ.search(consulta):
            self._ancestros(puntos, asignatura)
        elegidos = sorted(puntos.items(), key=lambda x: (-x[1], x[0]))[:k_final]
        ids = {d for d, _ in elegidos}
        unicas = {(a.origen, a.destino, a.tipo, a.rol): a for d in ids for _, a in self.vecinos[d]
                  if a.origen in ids and a.destino in ids}
        relaciones = sorted(unicas.values(), key=lambda a: (a.tipo, a.origen, a.destino))
        return Contexto(consulta, grado, asignatura, [(self.por_id[d], s) for d, s in elegidos], relaciones)


def busqueda_global(consulta: str, grado: int, k: int = 5) -> list[dict]:
    """Búsqueda «global»: devuelve los bloques temáticos (comunidades) del grado más pertinentes a la consulta."""
    import json

    from goes_science_kg.config import ruta

    p = ruta(f"data/grafo/grados/G{grado:02d}/comunidades.json")
    if not p.exists():
        return []
    coms = {c["id"]: c for c in json.loads(p.read_text(encoding="utf-8"))}
    idx = BM25({i: normalizar(" ".join(x for x in (c["nombre"], c["resumen"], c.get("titulo"), c.get("resumen_ia"),
                                                      *(c["unidades"] or [])) if x))
                for i, c in coms.items()})
    q = normalizar(consulta)
    orden = sorted(coms, key=lambda i: (-idx.puntaje(q, i), -len(coms[i]["conceptos"]), i))
    return [coms[i] | {"puntaje": round(idx.puntaje(q, i), 3)} for i in orden[:k]]


SISTEMA = """Eres un asistente de diseño curricular de Ciencias para el MINED de El Salvador.
Respondes en español, SOLO con la evidencia del contexto (nodos del grafo de conocimiento y sus relaciones).
Cita los ids entre corchetes, por ejemplo [TEMA:G07-CIE-U2-2.3] o [CON:biologia/fotosintesis].
Si la evidencia no alcanza para responder, dilo y explica qué faltaría. No inventes grados, códigos ni páginas."""

MODELO = "claude-opus-5-5"


def responder(ctx: Contexto, modelo: str = MODELO) -> str:
    """Genera una respuesta citada con Claude. Requiere el extra `rag` (paquete `anthropic`)."""
    import anthropic

    client = anthropic.Anthropic()
    respuesta = client.beta.messages.create(
        model=modelo,
        max_tokens=16000,
        output_config={"effort": "medium"},
        # Si un clasificador de seguridad rechaza la solicitud, la API la reintenta con el modelo de respaldo.
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        system=[{"type": "text", "text": SISTEMA, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": f"{ctx.como_texto()}\n\nPregunta: {ctx.consulta}"}],
    )
    if respuesta.stop_reason == "refusal":
        return "La solicitud fue rechazada por los filtros de seguridad del modelo."
    return "".join(b.text for b in respuesta.content if b.type == "text")
