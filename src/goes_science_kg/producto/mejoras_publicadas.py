"""Archive complete curriculum denominators, votes, and adversarial verification results."""

from __future__ import annotations

from collections import Counter
from typing import Literal

from pydantic import Field

from goes_science_kg.curriculo.contratos import Curriculo
from goes_science_kg.motor.contratos import Contrato, Evidencia, huella
from goes_science_kg.producto.mejoras_contratos import (
    CRITERIOS_MEJORA,
    ROLES_MEJORA,
    PreparacionMejora,
    ResultadoMejora,
    RondaMejora,
)
from goes_science_kg.producto.validacion_mejoras import evaluar_ronda, resolver_mejora


class CasoMejora(Contrato):
    """Bind one published unit preparation to its execution outcome and environment."""

    preparacion: PreparacionMejora
    resultado: ResultadoMejora
    entorno: str = Field(pattern=r"^[a-f0-9]{64}$")
    plan_id: str = Field(pattern=r"^[a-f0-9]{64}$")


class PruebaAdversarialMejora(Contrato):
    """Declare an adversarial mutation and its hidden expected reviewer criterion."""

    id: str
    preparacion: PreparacionMejora
    ronda: RondaMejora
    rol_esperado: Literal["revision_ciencia", "revision_curriculo", "revision_psicopedagogia", "revision_adversarial"]
    criterio_esperado: str
    razon_oraculo: str


class ArchivoMejoras(Contrato):
    """Archive complete curriculum proposals, native progressions, sources, and adversarial controls."""

    version: Literal["mejoras-publicadas-1"] = "mejoras-publicadas-1"
    id: str = Field(pattern=r"^[a-f0-9]{64}$")
    huella_curriculo: str
    huella_catalogo: str
    modelos: dict[str, str]
    unidades: tuple[CasoMejora, ...]
    progresiones: dict
    fuentes_progresiones: dict[str, dict]
    pruebas_adversariales: tuple[PruebaAdversarialMejora, ...]
    protocolos_anteriores: tuple[dict, ...] = ()
    limite: str = "Diseño curricular propuesto, revisado automáticamente; no acredita eficacia ni aprobación oficial"

    @property
    def cobertura(self) -> dict:
        """Report the complete original-row denominator and all proposal states."""

        return {
            "unidades": len(self.unidades),
            "filas": sum(len(c.preparacion.filas_originales) for c in self.unidades),
            "estados": dict(Counter(c.resultado.estado for c in self.unidades)),
            "filas_respaldadas": sum(
                f.accion != "fuera_alcance"
                for c in self.unidades
                if c.resultado.propuesta
                for f in c.resultado.propuesta.filas
            ),
            "filas_fuera_alcance_original": sum(
                d["estado"] == "fuera_alcance"
                for c in self.unidades
                for d in c.preparacion.clasificaciones_originales.values()
            ),
        }


def verificar_preparacion(p: PreparacionMejora) -> None:
    """Verify preparation fingerprints, complete source evidence, and quotation literals."""

    if p.id != huella(p.model_dump(mode="json", exclude={"id"})):
        raise ValueError("Preparación curricular modificada")
    evidencias = {e.id: e for e in p.evidencias}
    if any(
        e.version not in {"V4", "referencia"}
        or not e.fuente.get("documento")
        or e.fuente.get("verificacion") != "contenido_fuente"
        or e.fuente.get("tipo") == "derivada"
        or e.fuente.get("fuente_primaria") is False
        for e in p.evidencias
    ):
        raise ValueError("La evidencia debe proceder de una fuente primaria verificada de esta versión")
    if len(evidencias) != len(p.evidencias) or any(e.huella != huella_texto(e.texto) for e in p.evidencias):
        raise ValueError("Evidencias duplicadas o texto modificado")
    if len({f.id for f in p.fragmentos}) != len(p.fragmentos):
        raise ValueError("Fragmentos duplicados")
    if any(
        f.evidencia_id not in evidencias
        or " ".join(f.literal.split()) not in " ".join(evidencias[f.evidencia_id].texto.split())
        for f in p.fragmentos
    ):
        raise ValueError("Un literal no pertenece a su fuente")
    if not p.grupos or any(not ids or set(ids) - evidencias.keys() for ids in p.grupos.values()):
        raise ValueError("Grupos de evidencia incompatibles")


def huella_texto(texto):
    """Fingerprint normalized text under the documented archive comparison policy."""

    import hashlib

    return hashlib.sha256(texto.encode()).hexdigest()


def validar_pruebas(pruebas, modelos) -> None:
    """Validate complete adversarial controls and their expected rejection criteria."""

    if len(pruebas) != 5 or len({p.id for p in pruebas}) != 5:
        raise ValueError("Se requieren cinco controles adversariales distintos")
    if len({huella(p.ronda.borrador) for p in pruebas}) != 5:
        raise ValueError("No se duplican borradores para aparentar cinco controles")
    for caso in pruebas:
        verificar_preparacion(caso.preparacion)
        estado, _ = evaluar_ronda(caso.ronda, caso.preparacion, modelos)
        if estado != "no_respaldado" or caso.criterio_esperado not in CRITERIOS_MEJORA[caso.rol_esperado]:
            raise ValueError("El control adversarial no produjo el veto esperado")
        if any(d.error or d.lectura is None for d in caso.ronda.dictamenes):
            raise ValueError("Un fallo de proveedor no cuenta como detección de un defecto")
        lector = next(d for d in caso.ronda.dictamenes if d.rol == caso.rol_esperado)
        if lector.lectura.criterios[caso.criterio_esperado] != "no":
            raise ValueError("El especialista no identificó el defecto que se evalúa")


def validar_archivo_mejoras(archivo: ArchivoMejoras, curriculo: Curriculo, catalogo, *, modelos=None) -> None:
    """Reconstruct and validate every published unit against its original curriculum."""

    if archivo.id != huella(archivo.model_dump(mode="json", exclude={"id"})):
        raise ValueError("El archivo curricular no conserva su identidad")
    if archivo.huella_curriculo != curriculo.huella or archivo.huella_catalogo != huella(catalogo):
        raise ValueError("Propuestas de otro currículo o catálogo")
    if set(archivo.modelos) != set(ROLES_MEJORA) or (modelos is not None and modelos != archivo.modelos):
        raise ValueError("Política de modelos distinta de los cuatro especialistas configurados")
    esperadas = {(f.grado, f.asignatura_malla, f.unidad) for f in curriculo.filas}
    recibidas = [
        (c.preparacion.solicitud.grado, c.preparacion.solicitud.asignatura_malla, c.preparacion.solicitud.unidad)
        for c in archivo.unidades
    ]
    if len(recibidas) != len(set(recibidas)) or set(recibidas) != esperadas:
        raise ValueError("La publicación debe contener todas las unidades, sin selección de resultados")
    decisiones = {d.fila_id: d.model_dump(mode="json") for d in catalogo.filas}
    for caso in archivo.unidades:
        p = caso.preparacion
        verificar_preparacion(p)
        if (p.huella_curriculo, p.huella_catalogo) != (archivo.huella_curriculo, archivo.huella_catalogo):
            raise ValueError("La preparación corresponde a otro currículo o catálogo")
        clave = (p.solicitud.grado, p.solicitud.asignatura_malla, p.solicitud.unidad)
        filas = sorted(
            (f for f in curriculo.filas if (f.grado, f.asignatura_malla, f.unidad) == clave),
            key=lambda f: (f.hoja, f.fila),
        )
        if list(p.filas_originales) != [f.model_dump(mode="json", exclude={"celdas"}) for f in filas]:
            raise ValueError("La preparación omite, reordena o modifica filas originales")
        if p.clasificaciones_originales != {f.id: decisiones[f.id] for f in filas}:
            raise ValueError("Las clasificaciones originales cambiaron")
        esperado = resolver_mejora(
            p, caso.resultado.rondas, ejecucion_id=caso.resultado.ejecucion_id, modelos=archivo.modelos
        )
        if esperado != caso.resultado:
            raise ValueError("El resultado publicado no corresponde a sus cuatro votos completos")
    validar_pruebas(archivo.pruebas_adversariales, archivo.modelos)
    preparaciones = {c.preparacion.id: c.preparacion for c in archivo.unidades}
    if any(preparaciones.get(c.preparacion.id) != c.preparacion for c in archivo.pruebas_adversariales):
        raise ValueError("Los controles deben conservar el contexto primario del piloto publicado")
    progresiones = archivo.progresiones
    if progresiones["id"] != huella({k: v for k, v in progresiones.items() if k != "id"}):
        raise ValueError("Las progresiones documentales cambiaron")
    from goes_science_kg.ingesta.progresiones import BANDAS, LIMITE, CatalogoProgresiones

    catalogo_nativo = CatalogoProgresiones.model_validate(progresiones["catalogo"])
    nativas = {e.id: e for e in catalogo_nativo.expectativas}
    if set(archivo.fuentes_progresiones) != {e.fuente for e in nativas.values()}:
        raise ValueError("El inventario documental nativo difiere de sus expectativas")
    if set(progresiones["evidencias"]) != set(nativas):
        raise ValueError("Una expectativa nativa perdió evidencia")
    for id_, bruto in progresiones["evidencias"].items():
        e = Evidencia.model_validate(bruto)
        n = nativas[id_]
        fuente = archivo.fuentes_progresiones[n.fuente]
        if fuente.get("sha256") != n.sha256 or fuente.get("raiz_fuente") != "referencias_progresiones_2026":
            raise ValueError("La fuente nativa perdió su raíz o SHA")
        if (
            e.id != id_
            or e.huella != huella_texto(e.texto)
            or (e.fuente.get("banda_nativa"), e.fuente.get("sha256"), e.fuente.get("pagina"))
            != (n.banda, n.sha256, n.pagina_pdf)
            or e.fuente.get("region") != n.region.model_dump(mode="json")
            or e.fuente.get("region_banda") != n.region_banda.model_dump(mode="json")
        ):
            raise ValueError("La expectativa no conserva banda, página y edición")
    cadenas = []
    for grupo in sorted({e.grupo for e in nativas.values()}):
        ids = [next(e.id for e in nativas.values() if e.grupo == grupo and e.banda == b) for b in BANDAS]
        cadenas.extend(
            {"origen": a, "destino": b, "tipo": "SIGUE_EN_REFERENCIA", "limite": LIMITE}
            for a, b in zip(ids, ids[1:], strict=False)
        )
    if progresiones["cadenas"] != cadenas:
        raise ValueError("La cadena no sigue las bandas documentales nativas")
