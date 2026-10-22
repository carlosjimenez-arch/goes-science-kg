"""Ensamblaje de consulta desde una publicación curricular verificada."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from goes_science_kg.config import ruta
from goes_science_kg.curriculo.contexto_fuentes import catalogo_fuentes_v4
from goes_science_kg.modelos import TipoNodo
from goes_science_kg.motor.contratos import huella
from goes_science_kg.motor.fuentes import FuentesVerificadas
from goes_science_kg.producto.almacen import cargar_producto
from goes_science_kg.producto.consulta_conocimiento import BuscadorProducto
from goes_science_kg.producto.contratos import ProductoMaterializado
from goes_science_kg.recuperacion import BuscadorBaseline, cargar_buscador_baseline


@dataclass(frozen=True)
class RuntimeProducto:
    producto: ProductoMaterializado
    buscador: BuscadorProducto
    fuentes: FuentesVerificadas


def cargar_runtime(
    destino: Path | None = None,
    *,
    raiz_v4: Path | None = None,
    raiz_referencias: Path | None = None,
    raiz_historica: Path | None = None,
    raiz_paises: Path | None = None,
    raiz_cientificas: Path | None = None,
    archivo_alertas: Path | None = None,
    raiz_progresiones: Path | None = None,
) -> RuntimeProducto:
    """Fija una generación; las raíces permitidas no proceden de las consultas."""
    producto = cargar_producto(destino or ruta("data/producto/V4"))
    catalogo = catalogo_fuentes_v4(producto.curriculo)
    for nodo in producto.nodos:
        if nodo.tipo != TipoNodo.DOCUMENTO:
            continue
        id_fuente = nodo.id.removeprefix("DOC:")
        if id_fuente in catalogo:
            if nodo.props.get("sha256") != catalogo[id_fuente]["sha256"]:
                raise ValueError("La fuente del grafo difiere de la ingesta curricular")
            continue
        if nodo.props.get("raiz_fuente", "principal") not in {
            "principal",
            "referencias_2026",
            "referencias_paises_2026",
            "referencias_cientificas_2026",
            "referencias_progresiones_2026",
        }:
            raise ValueError("Raíz de referencia no autorizada para el producto")
        catalogo[id_fuente] = nodo.props
    clase_fuentes = FuentesVerificadas
    opciones = {}
    if producto.alineaciones is not None:
        from goes_science_kg.ingesta.extraccion import PaginasConPerfil
        from goes_science_kg.ingesta.referencias import RepositorioReferencias
        from goes_science_kg.producto.fuentes_alineacion import FuentesConAlineaciones

        paginas = RepositorioReferencias(raiz_referencias or ruta("data/referencias_2026"))
        if producto.alineaciones.perfiles is not None:
            paginas = PaginasConPerfil(paginas, producto.alineaciones.perfiles)
        opciones = {"alineaciones": producto.alineaciones, "paginas": paginas}
        clase_fuentes = FuentesConAlineaciones
    fuentes = clase_fuentes(
        catalogo,
        raiz_fuentes=raiz_historica or ruta("data/fuentes"),
        raices_adicionales={
            "v4": raiz_v4 or ruta("insumos/v4"),
            "referencias_2026": raiz_referencias or ruta("data/referencias_2026"),
            "referencias_paises_2026": raiz_paises or ruta("data/referencias_paises_2026"),
            "referencias_cientificas_2026": raiz_cientificas or ruta("data/referencias_cientificas_2026"),
            "referencias_progresiones_2026": raiz_progresiones or ruta("data/referencias_progresiones_2026"),
        },
        **opciones,
    )
    baseline = BuscadorBaseline(
        [n.model_copy(deep=True) for n in producto.nodos],
        [a.model_copy(deep=True) for a in producto.aristas],
        version="V4",
    )
    from goes_science_kg.producto.garantias import bloqueos_cientificos

    fuentes.bloqueos_curriculares = bloqueos_cientificos(
        producto.curriculo, fuentes, archivo_alertas or ruta("docs/investigacion/alertas_v4.json")
    )
    if producto.alineaciones is not None:
        from goes_science_kg.producto.alineaciones import validar_archivo_alineaciones

        # Revalida el expediente histórico en sus fuentes y alertas de origen. Los vetos
        # posteriores se aplican a toda nueva consulta/generación sin reescribir sus votos.
        validar_archivo_alineaciones(producto.alineaciones, producto.curriculo, fuentes=fuentes, paginas=paginas)
    if producto.mejoras is not None:
        fuentes.bloqueos_derivados.update(
            bloqueos_cientificos(producto.curriculo, fuentes, ruta("config/alertas_derivadas_v4.yaml"))
        )
        # Las enmiendas corrigen copias propuestas: los originales con errores siguen bloqueados
        # para la generación genérica, que no debe enseñar la errata como evidencia correcta.
        for caso in producto.mejoras.unidades:
            fuentes.bloqueos_derivados.update(
                {
                    id_: motivo
                    for id_, motivo in caso.preparacion.alertas.items()
                    if id_ not in fuentes.bloqueos_curriculares
                }
            )
    buscador = BuscadorProducto(
        baseline,
        producto.curriculo,
        producto.catalogo,
        producto.conocimiento,
        fuentes,
        snapshot_id=producto.manifest.snapshot_id,
        alineaciones=producto.alineaciones,
    )
    buscador.huella = huella({"indice": buscador.huella, "bloqueos": fuentes.bloqueos_efectivos})
    return RuntimeProducto(producto=producto, buscador=buscador, fuentes=fuentes)


def cargar_recursos(version: str):
    """La V4 se carga de su publicación; la V3 conserva una entrada explícita."""
    if version == "V4":
        runtime = cargar_runtime()
        return runtime.buscador, runtime.fuentes
    if version == "V3":
        from goes_science_kg.grafo.almacen import cargar

        nodos, _ = cargar()
        return cargar_buscador_baseline(version="V3"), FuentesVerificadas.del_grafo(nodos)
    raise ValueError(f"No existe una publicación admitida para {version}")
