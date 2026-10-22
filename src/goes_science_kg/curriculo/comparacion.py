"""Correspondencia documental conservadora V3→V4, sin trasladar identidad ni decisiones."""

from __future__ import annotations

import logging
import re
import tempfile
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Literal

from pydantic import Field

from goes_science_kg.config import ruta
from goes_science_kg.curriculo.contratos import ContratoCurricular, Curriculo, FilaCurricular
from goes_science_kg.modelos import Nodo, TipoNodo
from goes_science_kg.motor.fuentes import FuentesVerificadas
from goes_science_kg.producto.contratos import ReferenciasProducto
from goes_science_kg.recuperacion import Documento
from goes_science_kg.recuperacion.grafo import _resolver_version

LOGGER = logging.getLogger(__name__)
# Diferencia documentada entre la representación de config V3 y el literal de la malla V4.
# No usa Nodo.asignatura (disciplina inferida o revisada) ni elimina tildes de otros textos.
REPRESENTACIONES_MALLA = {
    "ciencias": "Ciencias",
    "biologia": "Biología",
    "fisica": "Física",
    "quimica": "Química",
}
PARES_CAMPOS = {
    "contenido": "contenido",
    "subcontenido": "subcontenido",
    "evidencia": "evidencia_aprendizaje",
    "habilidad_timss": "habilidad_timss",
    "competencia_pisa": "competencia_pisa",
}
CABECERAS = {
    "Contenido": "contenido",
    "Subcontenidos": "subcontenido",
    "Evidencia de aprendizaje": "evidencia",
    "Habilidad TIMSS": "habilidad_timss",
    "Competencia PISA 2025": "competencia_pisa",
    "Indicadores de logro": "indicadores_logro",
    "Indicador avanzado": "indicador_avanzado",
}
INCORPORADOS = (
    "eje_integrador",
    "numero_tema",
    "numero_clase",
    "actitudinal",
    "conocimiento_pisa",
    "contexto_pisa",
    "habilidad_siglo_xxi",
    "competencia_digital",
    "actividad_digital",
    "habilidad_transversal",
    "competencia_men",
    "dominio_clave",
    "notacion",
    "notas",
    "origen_contenido",
    "celdas",
    "fases",
)


def normalizar_literal(texto: str) -> str:
    """Solo NFKC y espacios: conserva mayúsculas, tildes, puntuación, números y negaciones."""
    return " ".join(unicodedata.normalize("NFKC", texto).split())


def _asignatura(texto: str) -> str:
    literal = normalizar_literal(texto)
    return REPRESENTACIONES_MALLA.get(literal, literal)


class RegistroComparado(ContratoCurricular):
    """Registro sin disciplina inferida ni etiquetas que puedan heredarse."""

    id: str
    grado: int
    asignatura_malla: str
    asignatura_comparable: str
    objetivo: str
    unidad: str
    fuente: dict[str, Any]


class CampoComparado(ContratoCurricular):
    campo_v3: str
    campo_v4: str | None
    estado: Literal[
        "igual_normalizado",
        "valor_distinto",
        "vacios_ambos",
        "antes_vacio_ahora_presente",
        "antes_presente_ahora_vacio",
        "no_comparable",
    ]
    valor_v3: str | None
    valor_v4: str | None
    motivo: str
    fuente_v3: dict[str, Any] = Field(default_factory=dict)


class CoincidenciaObjetivo(ContratoCurricular):
    estado: Literal["coincidencia_objetivo_1_a_1", "ambigua"]
    grado: int
    asignatura_malla: str
    objetivo_normalizado: str
    anteriores: tuple[RegistroComparado, ...]
    actuales: tuple[RegistroComparado, ...]
    campos: tuple[CampoComparado, ...] = ()
    sin_contraparte_v3: tuple[str, ...] = ()


class SinCorrespondencia(ContratoCurricular):
    registro: RegistroComparado
    estado: Literal["sin_coincidencia_exacta"] = "sin_coincidencia_exacta"
    mismo_objetivo_otro_contexto: tuple[RegistroComparado, ...] = ()
    limite: str = "No demuestra eliminación, incorporación conceptual, fusión o cambio de grado"


class ComparacionCurricular(ContratoCurricular):
    version: Literal["comparacion-1"] = "comparacion-1"
    version_anterior: Literal["V3"] = "V3"
    version_actual: Literal["V4"] = "V4"
    huella_curriculo_v4: str
    procedencia_grafo_v3: dict[str, Any]
    criterios: dict[str, Any]
    resumen: dict[str, Any]
    coincidencias: tuple[CoincidenciaObjetivo, ...]
    sin_correspondencia_v3: tuple[SinCorrespondencia, ...]
    sin_correspondencia_v4: tuple[SinCorrespondencia, ...]
    repeticiones: dict[str, list[dict[str, Any]]]
    campos_incorporados_al_contrato_v4: tuple[str, ...] = INCORPORADOS
    limites: tuple[str, ...]


class _DatosHistoricos:
    """Localiza campos mediante cabecera y fila originales cotejadas con SHA."""

    def __init__(self, nodos: tuple[Nodo, ...], raiz_historica: Path):
        catalogo = {n.id.removeprefix("DOC:"): n.props for n in nodos if n.tipo == TipoNodo.DOCUMENTO}
        self.fuentes = FuentesVerificadas(catalogo, raiz_fuentes=raiz_historica)
        self._cabeceras: dict[tuple[str, str], dict[str, list[str]]] = {}
        self._filas: dict[str, dict | None] = {}

    def _columnas(self, nodo: Nodo) -> dict[str, list[str]]:
        fuente = nodo.fuente
        if fuente is None or not fuente.hoja:
            return {}
        clave = fuente.documento, fuente.hoja
        if clave not in self._cabeceras:
            por_campo: dict[str, set[str]] = defaultdict(set)
            for fila in (1, 2):
                evidencia = self.fuentes.hidratar(
                    Documento(
                        id=f"CABECERA:{nodo.id}:{fila}",
                        texto="Cabecera original",
                        version="V3",
                        fuente={"documento": fuente.documento, "hoja": fuente.hoja, "fila": fila},
                    )
                )
                if evidencia is None:
                    continue
                for celda in evidencia.fuente["celdas_verificadas"]:
                    valor = celda["valor_original"]
                    if isinstance(valor, str) and (campo := CABECERAS.get(normalizar_literal(valor))):
                        columna = re.match(r"[A-Z]+", celda["coordenada_solicitada"]).group()
                        por_campo[campo].add(columna)
            self._cabeceras[clave] = {c: sorted(cols) for c, cols in por_campo.items()}
        return self._cabeceras[clave]

    def _original(self, nodo: Nodo) -> dict | None:
        if nodo.id not in self._filas:
            fuente = nodo.fuente
            if fuente is None or not fuente.hoja or not fuente.fila:
                self._filas[nodo.id] = None
            else:
                evidencia = self.fuentes.hidratar(
                    Documento(
                        id=nodo.id,
                        texto="Fila original, sin usar metadatos como evidencia",
                        version="V3",
                        fuente=fuente.model_dump(exclude_none=True),
                    )
                )
                self._filas[nodo.id] = evidencia.model_dump(mode="json") if evidencia else None
        return self._filas[nodo.id]

    def dato(self, nodo: Nodo, campo: str) -> tuple[str, dict] | None:
        columnas = self._columnas(nodo).get(campo, [])
        original = self._original(nodo)
        if len(columnas) != 1 or original is None:
            return None
        coordenada = f"{columnas[0]}{nodo.fuente.fila}"
        celda = next(
            (c for c in original["fuente"]["celdas_verificadas"] if c["coordenada_solicitada"] == coordenada), None
        )
        if celda is None or celda["valor_es_formula"]:
            return None
        valor = celda["valor_real"]
        if valor is not None and not isinstance(valor, str):
            return None
        localizador = {k: v for k, v in original["fuente"].items() if k != "celdas_verificadas"} | {
            "celdas": [coordenada],
            "celdas_verificadas": [celda],
            "cabecera": campo,
        }
        return valor or "", localizador

    def indicador(self, nodo: Nodo) -> tuple[str, dict] | None:
        almacenado = nodo.props.get("indicador")
        if not isinstance(almacenado, str) or not normalizar_literal(almacenado):
            return None
        coincidencias = []
        for campo in ("indicadores_logro", "indicador_avanzado"):
            if dato := self.dato(nodo, campo):
                if normalizar_literal(dato[0]) == normalizar_literal(almacenado):
                    coincidencias.append((campo, dato[1]))
        return coincidencias[0] if len(coincidencias) == 1 else None


def _registro_v3(nodo: Nodo) -> RegistroComparado:
    asignatura = nodo.props.get("asignatura_malla")
    if nodo.grado is None or not isinstance(asignatura, str) or not normalizar_literal(asignatura):
        raise ValueError("Tema V3 sin grado o asignatura_malla literal; no se usa la disciplina inferida")
    if not normalizar_literal(nodo.etiqueta):
        raise ValueError("Tema V3 sin objetivo")
    return RegistroComparado(
        id=nodo.id,
        grado=nodo.grado,
        asignatura_malla=asignatura,
        asignatura_comparable=_asignatura(asignatura),
        objetivo=nodo.etiqueta,
        unidad=str(nodo.props.get("unidad", "")),
        fuente=nodo.fuente.model_dump(exclude_none=True) if nodo.fuente else {},
    )


def _registro_v4(fila: FilaCurricular) -> RegistroComparado:
    return RegistroComparado(
        id=fila.id,
        grado=fila.grado,
        asignatura_malla=fila.asignatura_malla,
        asignatura_comparable=_asignatura(fila.asignatura_malla),
        objetivo=fila.procedimental,
        unidad=fila.unidad,
        fuente={
            "documento": fila.fuente_id,
            "hoja": fila.hoja,
            "fila": fila.fila,
            "celdas": [c.coordenada for c in fila.celdas],
        },
    )


def _comparar_campo(
    nodo: Nodo, fila: FilaCurricular, anterior: str, actual: str | None, datos: _DatosHistoricos
) -> CampoComparado:
    v3 = nodo.props.get(anterior)
    v4 = getattr(fila, actual) if actual else None
    dato = datos.dato(nodo, actual if anterior == "indicador" else anterior) if actual else None
    if not isinstance(v3, str) or dato is None or normalizar_literal(v3) != normalizar_literal(dato[0]):
        return CampoComparado(
            campo_v3=anterior,
            campo_v4=actual,
            estado="no_comparable",
            valor_v3=v3,
            valor_v4=v4,
            motivo="Columna original no identificada inequívocamente o valor del grafo incompatible con la fuente",
        )
    a, b = normalizar_literal(v3), normalizar_literal(v4)
    estado = (
        "vacios_ambos"
        if not a and not b
        else "igual_normalizado"
        if a == b
        else "antes_vacio_ahora_presente"
        if not a
        else "antes_presente_ahora_vacio"
        if not b
        else "valor_distinto"
    )
    return CampoComparado(
        campo_v3=anterior,
        campo_v4=actual,
        estado=estado,
        valor_v3=v3,
        valor_v4=v4,
        fuente_v3=dato[1],
        motivo="Compara declaraciones literales del mismo campo; no verifica eficacia ni equivalencia internacional",
    )


def comparar_curriculos(
    grafo_v3: ReferenciasProducto,
    curriculo_v4: Curriculo,
    *,
    raiz_historica: Path | None = None,
) -> ComparacionCurricular:
    """Relaciona objetivos exactos por contexto; nunca activa correspondencias o copia etiquetas.

    La entrada histórica debe proceder de ``cargar_referencias_historicas`` o de una
    validación equivalente de bytes, manifiesto y versión. La tabla de representación
    solo traduce los cuatro nombres de malla de config V3 a sus literales V4.
    """
    if grafo_v3.procedencia.get("version_curriculo") != "V3" or curriculo_v4.version != "V4":
        raise ValueError("La comparación requiere una referencia histórica V3 y un currículo V4")
    LOGGER.info("Comparación documental V3→V4: comprobando claves y campos comparables")
    if _resolver_version(grafo_v3.nodos, "V3") != "V3":
        raise ValueError("El grafo histórico mezcla versiones")
    anteriores = [n for n in grafo_v3.nodos if n.tipo == TipoNodo.TEMA]
    if not anteriores or not curriculo_v4.filas or len({n.id for n in grafo_v3.nodos}) != len(grafo_v3.nodos):
        raise ValueError("La comparación requiere temas e identidades históricas únicas")
    if len({f.id for f in curriculo_v4.filas}) != len(curriculo_v4.filas) or any(
        f.version != "V4" for f in curriculo_v4.filas
    ):
        raise ValueError("El currículo actual duplica identidades o mezcla versiones")
    registros = {
        "V3": {n.id: _registro_v3(n) for n in anteriores},
        "V4": {f.id: _registro_v4(f) for f in curriculo_v4.filas},
    }
    por_clave = {"V3": defaultdict(list), "V4": defaultdict(list)}
    por_objetivo = {"V3": defaultdict(list), "V4": defaultdict(list)}
    for version, elementos in registros.items():
        for elemento in elementos.values():
            objetivo = normalizar_literal(elemento.objetivo)
            clave = elemento.grado, elemento.asignatura_comparable, objetivo
            por_clave[version][clave].append(elemento)
            por_objetivo[version][objetivo].append(elemento)
    nodos = {n.id: n for n in anteriores}
    filas = {f.id: f for f in curriculo_v4.filas}
    datos = _DatosHistoricos(grafo_v3.nodos, raiz_historica or ruta("data/fuentes"))
    coincidencias = []
    compartidas = set(por_clave["V3"]) & set(por_clave["V4"])
    for grado, asignatura, objetivo in sorted(compartidas):
        previas = tuple(sorted(por_clave["V3"][grado, asignatura, objetivo], key=lambda r: r.id))
        nuevas = tuple(sorted(por_clave["V4"][grado, asignatura, objetivo], key=lambda r: r.id))
        unica = len(previas) == len(nuevas) == 1
        campos = []
        sin_contraparte = list(INCORPORADOS)
        if unica:
            nodo, fila = nodos[previas[0].id], filas[nuevas[0].id]
            campos = [_comparar_campo(nodo, fila, a, b, datos) for a, b in PARES_CAMPOS.items()]
            indicador = datos.indicador(nodo)
            campo_actual = indicador[0] if indicador else None
            campos.append(_comparar_campo(nodo, fila, "indicador", campo_actual, datos))
            sin_contraparte.extend(c for c in ("indicadores_logro", "indicador_avanzado") if c != campo_actual)
        coincidencias.append(
            CoincidenciaObjetivo(
                estado="coincidencia_objetivo_1_a_1" if unica else "ambigua",
                grado=grado,
                asignatura_malla=asignatura,
                objetivo_normalizado=objetivo,
                anteriores=previas,
                actuales=nuevas,
                campos=tuple(campos),
                sin_contraparte_v3=tuple(sin_contraparte),
            )
        )
    sin_correspondencia = {}
    repeticiones = {}
    for version, otra in (("V3", "V4"), ("V4", "V3")):
        pendientes = []
        repetidas = []
        for clave, elementos in sorted(por_clave[version].items()):
            if len(elementos) > 1:
                repetidas.append(
                    {
                        "grado": clave[0],
                        "asignatura_malla": clave[1],
                        "objetivo_normalizado": clave[2],
                        "ids": sorted(e.id for e in elementos),
                    }
                )
            if clave in compartidas:
                continue
            for elemento in sorted(elementos, key=lambda r: r.id):
                otras = tuple(sorted(por_objetivo[otra].get(clave[2], []), key=lambda r: r.id))
                pendientes.append(SinCorrespondencia(registro=elemento, mismo_objetivo_otro_contexto=otras))
        sin_correspondencia[version] = tuple(pendientes)
        repeticiones[version] = repetidas
    exactas = sum(c.estado == "coincidencia_objetivo_1_a_1" for c in coincidencias)
    estados_campos = {
        campo: dict(
            sorted(Counter(c.estado for grupo in coincidencias for c in grupo.campos if c.campo_v3 == campo).items())
        )
        for campo in (*PARES_CAMPOS, "indicador")
    }
    no_comparables = sum(c.estado == "no_comparable" for grupo in coincidencias for c in grupo.campos)
    if no_comparables:
        LOGGER.warning("Comparación V3→V4: %d valores sin contraparte original inequívoca", no_comparables)
    LOGGER.info("Comparación V3→V4: %d parejas únicas, %d grupos ambiguos", exactas, len(coincidencias) - exactas)
    return ComparacionCurricular(
        huella_curriculo_v4=curriculo_v4.huella,
        procedencia_grafo_v3=grafo_v3.procedencia,
        criterios={
            "clave": ["grado", "asignatura_malla_declarada", "objetivo_procedimental"],
            "normalizacion_objetivo": "NFKC y secuencias de espacios; conserva mayúsculas, puntuación y numeración",
            "representaciones_malla_legacy": REPRESENTACIONES_MALLA,
            "normalizacion_asignatura": "NFKC/espacios y tabla explícita de representación, sin disciplina inferida",
            "similitud_fuzzy": False,
            "hereda_identidad_etiquetas_aristas": False,
            "unidad": "Contexto mostrado; sus formatos distintos no se interpretan como cambio semántico",
            "indicador": "Solo se compara con la columna original identificada por SHA, cabecera y valor único",
        },
        resumen={
            "registros_v3": len(anteriores),
            "registros_v4": len(curriculo_v4.filas),
            "coincidencias_1_a_1": exactas,
            "grupos_ambiguos": len(coincidencias) - exactas,
            "sin_coincidencia_exacta_v3": len(sin_correspondencia["V3"]),
            "sin_coincidencia_exacta_v4": len(sin_correspondencia["V4"]),
            "mismo_objetivo_otro_contexto_v3": sum(
                bool(r.mismo_objetivo_otro_contexto) for r in sin_correspondencia["V3"]
            ),
            "mismo_objetivo_otro_contexto_v4": sum(
                bool(r.mismo_objetivo_otro_contexto) for r in sin_correspondencia["V4"]
            ),
            "campos_comparados": estados_campos,
            "lectura_fuentes_v3": datos.fuentes.estadisticas(),
        },
        coincidencias=tuple(coincidencias),
        sin_correspondencia_v3=sin_correspondencia["V3"],
        sin_correspondencia_v4=sin_correspondencia["V4"],
        repeticiones=repeticiones,
        limites=(
            "Una coincidencia de objetivo no demuestra identidad de toda la secuencia, profundidad o carga horaria",
            "Sin coincidencia exacta no equivale a tema eliminado, concepto nuevo, fusión o traslado confirmado",
            "Los campos sin contraparte se incorporan al contrato; pueden haber existido antes en los Excel",
            "V3 colapsó los dos indicadores y perdió campos; no se atribuyen cambios a esa pérdida de representación",
            "No se trasladan IDs, decisiones humanas, etiquetas, clasificaciones, alineaciones o aristas",
            "La comparación usa el grafo histórico validado; no afirma que este capture toda la V3 original",
        ),
    )


def guardar_comparacion(
    comparacion: ComparacionCurricular,
    *,
    salida_json: Path,
    salida_markdown: Path,
) -> None:
    """Escribe el informe explícito sin tocar fuentes, grafos o correspondencias activas."""
    if salida_json.resolve() == salida_markdown.resolve():
        raise ValueError("JSON y Markdown requieren destinos distintos")
    # Valida ambos antes de crear carpetas o tocar cualquiera de los archivos.
    salida_json = _destino_informe(salida_json, extension=".json")
    salida_markdown = _destino_informe(salida_markdown, extension=".md")
    r = comparacion.resumen
    lineas = [
        "# Comparación documental V3 → V4",
        "",
        f"Se compararon {r['registros_v3']} registros del grafo V3 y {r['registros_v4']} filas V4.",
        "",
        f"Hay **{r['coincidencias_1_a_1']} coincidencias únicas de objetivo** y "
        f"**{r['grupos_ambiguos']} grupos ambiguos**. Permanecen sin coincidencia exacta "
        f"{r['sin_coincidencia_exacta_v3']} registros V3 y {r['sin_coincidencia_exacta_v4']} filas V4.",
        "",
        "Estas cifras no cuentan conceptos eliminados, nuevos o fusionados. No se trasladan IDs ni decisiones.",
        "",
        "## Criterio",
        "",
        "La clave exige grado, asignatura declarada en la malla y objetivo. El objetivo solo normaliza NFKC y "
        "espacios: conserva puntuación, mayúsculas, numeración y negaciones. No se utiliza similitud aproximada.",
        "",
        "La V3 almacena los nombres de malla como slugs de configuración. Se traduce únicamente la "
        "representación explícita ciencias→Ciencias, biologia→Biología, fisica→Física y quimica→Química. "
        "No se usa la disciplina inferida o revisada del nodo.",
        "",
        f"Hay {r['mismo_objetivo_otro_contexto_v3']} registros V3 y "
        f"{r['mismo_objetivo_otro_contexto_v4']} filas V4 con el mismo literal en otro contexto. "
        "Quedan como referencias de revisión, sin confirmar traslado de grado o asignatura.",
        "",
        "## Campos comparables",
        "",
        "Cada valor comparado de V3 se localiza de nuevo por cabecera y fila en un archivo con SHA verificado. "
        "Un blanco arrastrado por el lector antiguo o una columna no identificable se declara no comparable. "
        "Las diferencias son textuales; no prueban mejora o pérdida pedagógica.",
        "",
        "| Campo del grafo V3 | Campo V4 | Estados en parejas únicas |",
        "|---|---|---|",
    ]
    for campo, estados in r["campos_comparados"].items():
        actual = PARES_CAMPOS.get(campo, "Indicadores de logro o Indicador avanzado, solo si se identifica")
        detalle = "; ".join(f"{e}: {n}" for e, n in sorted(estados.items()))
        lineas.append(f"| {campo} | {actual} | {detalle} |")
    lineas.extend(
        [
            "",
            "El indicador V3 combinaba Indicadores de logro con Indicador avanzado mediante fallback. "
            "Se compara únicamente con la columna cuyo valor original coincide de forma inequívoca. Si ambas "
            "columnas contienen el mismo texto, la procedencia semántica permanece ambigua.",
            "",
            "## Información incorporada al contrato",
            "",
            ", ".join(f"`{c}`" for c in comparacion.campos_incorporados_al_contrato_v4) + ".",
            "",
            "Son campos sin contraparte almacenada comparable en el grafo V3. Pueden estar presentes en el Excel "
            "antiguo: incorporados al contrato no significa contenidos curriculares nuevos. Los dos indicadores "
            "se desagregan; las fases V4 conservan texto/códigos locales, mientras `micro_pisa` V3 preservaba "
            "listas parciales de códigos y no permite comparar el texto completo. La unidad se muestra como "
            "contexto, sin equiparar automáticamente sus formatos de nombre.",
            "",
            "## Trazabilidad y límites",
            "",
            f"Huella curricular V4: `{comparacion.huella_curriculo_v4}`.",
            "",
            "El JSON adjunto conserva todas las parejas, grupos ambiguos, valores comparados, localizadores y "
            "registros sin correspondencia. La procedencia del grafo incluye sus SHA. No se consultaron "
            "conjuntos de evaluación reservados ni servicios remotos.",
            "",
            *[f"- {limite}." for limite in comparacion.limites],
            "",
            "## Reproducción",
            "",
            "```python",
            "from pathlib import Path",
            "from goes_science_kg.curriculo import cargar_curriculo",
            "from goes_science_kg.curriculo.comparacion import comparar_curriculos, guardar_comparacion",
            "from goes_science_kg.producto.referencias import cargar_referencias_historicas",
            "",
            'comparacion = comparar_curriculos(cargar_referencias_historicas(Path("data/grafo")), cargar_curriculo())',
            "guardar_comparacion(",
            "    comparacion,",
            '    salida_json=Path("docs/investigacion/comparacion_v3_v4.json"),',
            '    salida_markdown=Path("docs/investigacion/comparacion_v3_v4.md"),',
            ")",
            "```",
            "",
        ]
    )
    _escribir_informe(salida_json, comparacion.model_dump_json(indent=2) + "\n")
    _escribir_informe(salida_markdown, "\n".join(lineas))


def _destino_informe(salida: Path, *, extension: str) -> Path:
    if salida.is_symlink():
        raise ValueError("El informe no admite enlaces simbólicos de archivo")
    destino = salida.resolve()
    if destino.suffix.lower() != extension:
        raise ValueError(f"El informe requiere extensión {extension}")
    if any(parte == ".env" or parte.startswith(".env.") for parte in destino.parts) or destino.name in {
        "CLAUDE.md",
        "AGENTS.md",
        "SKILL.md",
    }:
        raise ValueError("El informe no puede sustituir entorno o instrucciones del harness")
    protegidos = (
        "insumos",
        "data/fuentes",
        "data/grafo",
        "reportes",
        "data/referencias_2026",
        "data/referencia",
        "src",
        "config",
        ".claude",
        ".codex",
        ".agents",
        ".git",
        "prompts",
        "tests",
    )
    if any(destino.is_relative_to(ruta(p).resolve()) for p in protegidos):
        raise ValueError("El resultado debe guardarse fuera de originales, código, referencias y configuración")
    if destino.exists() and not destino.is_file():
        raise ValueError("La salida debe identificar un archivo, no un directorio")
    return destino


def _escribir_informe(destino: Path, texto: str) -> None:
    """Reemplaza cada archivo completo; el par JSON/Markdown no es una transacción."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporal = tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", prefix=f".{destino.name}.", dir=destino.parent, delete=False
    )
    archivo_temporal = Path(temporal.name)
    try:
        with temporal:
            temporal.write(texto)
        archivo_temporal.replace(destino)
    finally:
        archivo_temporal.unlink(missing_ok=True)
