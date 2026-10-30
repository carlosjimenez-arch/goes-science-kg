"""Retrieve evidence for explicit rows without crossing dependency contexts."""

from __future__ import annotations

from pathlib import Path

from goes_science_kg.config import ruta
from goes_science_kg.curriculo.catalogacion import CatalogoDisciplinas
from goes_science_kg.curriculo.contexto_fuentes import catalogo_fuentes_v4, documento_de_fila
from goes_science_kg.curriculo.contratos import Curriculo
from goes_science_kg.motor.contratos import huella
from goes_science_kg.motor.fuentes import FuentesVerificadas
from goes_science_kg.producto.alineaciones import ArchivoAlineaciones
from goes_science_kg.producto.conocimiento_publicado import ArchivoConocimiento
from goes_science_kg.recuperacion import BuscadorBaseline, Documento, Resultado


def fuentes_del_archivo(
    archivo: ArchivoConocimiento,
    curriculo: Curriculo,
    *,
    raiz_v4: Path,
    raiz_historica: Path | None = None,
    raiz_referencias: Path | None = None,
    raiz_paises: Path | None = None,
    raiz_cientificas: Path | None = None,
) -> FuentesVerificadas:
    """Resolve source roots from host configuration rather than permissions claimed by an archive."""
    catalogo = catalogo_fuentes_v4(curriculo)
    for doc, registro in archivo.fuentes.items():
        if registro.get("raiz_fuente", "principal") not in {
            "principal",
            "v4",
            "referencias_2026",
            "referencias_paises_2026",
            "referencias_cientificas_2026",
        }:
            raise ValueError("Raíz documental de conocimiento no autorizada")
        if doc in catalogo:
            if registro != catalogo[doc]:
                raise ValueError("El conocimiento intenta sustituir una fuente curricular")
        else:
            if registro.get("version_curriculo") is not None:
                raise ValueError("Una referencia no puede declarar otra versión curricular local")
            catalogo[doc] = registro
    return FuentesVerificadas(
        catalogo,
        raiz_fuentes=raiz_historica or ruta("data/fuentes"),
        raices_adicionales={
            "v4": raiz_v4,
            "referencias_2026": raiz_referencias or ruta("data/referencias_2026"),
            "referencias_paises_2026": raiz_paises or ruta("data/referencias_paises_2026"),
            "referencias_cientificas_2026": raiz_cientificas or ruta("data/referencias_cientificas_2026"),
        },
    )


def rehidratar_evidencias(archivo: ArchivoConocimiento, fuentes: FuentesVerificadas, ids) -> None:
    """Rehydrate the selected archive evidence from permitted original sources."""

    for id_ in sorted(set(ids)):
        prueba = archivo.evidencias[id_]
        actual = fuentes.hidratar(
            Documento(
                id=prueba.id,
                texto="La fuente se lee de su snapshot verificado",
                fuente=prueba.fuente,
                version=prueba.version,
            )
        )
        if actual is None or actual.model_dump(mode="json") != prueba.model_dump(mode="json"):
            raise ValueError("Una evidencia del juicio cambió o no corresponde a los bytes originales")
    if motivos := fuentes.motivos_bloqueo([archivo.evidencias[i] for i in ids]):
        raise ValueError("Alerta científica bloqueante: " + " | ".join(motivos))


def rehidratar_archivo(
    archivo: ArchivoConocimiento,
    curriculo: Curriculo,
    *,
    raiz_v4: Path,
    raiz_historica: Path | None = None,
    archivo_alertas: Path | None = None,
) -> None:
    """Rehydrate every archived evidence item before admitting it for query use."""

    from goes_science_kg.producto.garantias import bloqueos_cientificos

    fuentes = fuentes_del_archivo(archivo, curriculo, raiz_v4=raiz_v4, raiz_historica=raiz_historica)
    fuentes.bloqueos_curriculares = bloqueos_cientificos(
        curriculo,
        fuentes,
        archivo_alertas or ruta("docs/investigacion/alertas_v4.json"),
    )
    rehidratar_evidencias(archivo, fuentes, tuple(archivo.evidencias))


class BuscadorProducto:
    """Preserve general retrieval while keeping exact row selection outside the historical graph."""

    def __init__(
        self,
        baseline: BuscadorBaseline,
        curriculo: Curriculo,
        catalogo: CatalogoDisciplinas,
        conocimiento: ArchivoConocimiento | None,
        fuentes: FuentesVerificadas,
        *,
        snapshot_id: str,
        alineaciones: ArchivoAlineaciones | None = None,
    ):
        self._baseline = baseline
        self._filas = {f.id: f.model_copy(deep=True) for f in curriculo.filas}
        self._clasificaciones = {f.fila_id: f.model_copy(deep=True) for f in catalogo.filas}
        self._conocimiento = conocimiento.model_copy(deep=True) if conocimiento else None
        self._fuentes = fuentes
        self._alineaciones_por_fila = {}
        if alineaciones is not None:
            for caso in alineaciones.model_copy(deep=True).admitidos:
                self._alineaciones_por_fila.setdefault(caso.solicitud.fila_id, []).append(caso)
        self.documentos = baseline.documentos
        self.version = "V4"
        self.huella = huella(
            {
                "baseline": baseline.huella,
                "snapshot_id": snapshot_id,
                "conocimiento": conocimiento.huella_archivo if conocimiento else None,
            }
        )
        self._candidatos_por_fila = {}
        if conocimiento:
            admitidas = {r.id for r in conocimiento.coleccion.relaciones_admisibles}
            for resultado in conocimiento.coleccion.resultados:
                if resultado.relacion is not None and resultado.relacion.id in admitidas:
                    self._candidatos_por_fila.setdefault(resultado.relacion.fila_id, []).append(
                        resultado.solicitud.candidato_id
                    )

    def buscar(self, consulta: str, **kwargs) -> list[Resultado]:
        """Retrieve general evidence while preserving the product's version and baseline semantics."""

        return self._baseline.buscar(consulta, **kwargs)

    def buscar_fila(self, fila_id: str, *, version: str, grado: int, asignatura: str, k: int = 16) -> list[Resultado]:
        """Validate exact row identity and filters before retrieving any source evidence."""
        if fila_id not in self._filas or version != "V4" or not 1 <= k <= 100:
            raise ValueError("La fila, versión o límite no corresponde a esta publicación V4")
        fila, decision = self._filas[fila_id], self._clasificaciones[fila_id]
        if (
            grado != fila.grado
            or asignatura not in decision.disciplinas
            or decision.estado
            not in {
                "declarado_malla",
                "coincidencia_automatica",
            }
        ):
            raise ValueError("La fila no corresponde al grado, disciplina o clasificación solicitados")
        if fila_id in self._fuentes.bloqueos_efectivos:
            raise ValueError("La fila tiene una alerta científica bloqueante")
        local = documento_de_fila(fila)
        candidatos = self._candidatos_por_fila.get(fila_id, [])
        externos = {}
        if candidatos:
            ids = {i for c in candidatos for i in self._conocimiento.expedientes[c].evidencias_ids}
            rehidratar_evidencias(self._conocimiento, self._fuentes, ids)
            for id_ in sorted(ids):
                prueba = self._conocimiento.evidencias[id_]
                if prueba.version != "referencia":
                    continue
                externos[id_] = Documento(
                    id=prueba.id,
                    texto=prueba.texto,
                    fuente=prueba.fuente,
                    version="referencia",
                    metadata={"fila_contexto": fila_id, "naturaleza": "fuente_primaria_del_juicio_condicionado"},
                )
        for caso in self._alineaciones_por_fila.get(fila_id, ()):
            for e in caso.preparacion.evidencias:
                documento = Documento(id=e.id, texto=e.texto, fuente=e.fuente, version=e.version)
                if self._fuentes.hidratar(documento) != e:
                    raise ValueError("Una fuente de la alineación cambió; no se usa el respaldo anterior")
                if e.version == "referencia":
                    externos[e.id] = documento.model_copy(
                        update={
                            "metadata": {
                                "fila_contexto": fila_id,
                                "naturaleza": "fuente_primaria_de_alineacion",
                                "referente_id": caso.solicitud.referente_id,
                                "obligatoria": True,
                            }
                        }
                    )
        # La fila completa encabeza siempre la recuperación; las fuentes externas son evidencia, no equivalencia SV.
        if sum(d.metadata.get("obligatoria") is True for d in externos.values()) + 1 > k:
            raise ValueError("El límite no permite conservar la fila y sus fuentes obligatorias")
        ordenados = sorted(externos.values(), key=lambda d: d.metadata.get("obligatoria") is not True)
        return [
            Resultado(documento=d, puntaje=1 if i == 0 else 0.5, canales=("fila_explicita",))
            for i, d in enumerate([local, *ordenados][:k])
        ]
