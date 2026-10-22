"""Archivo autosuficiente de conocimiento: evidencia deduplicada y juicios reconstruibles."""

from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING, Literal

from pydantic import Field

from goes_science_kg.curriculo.catalogacion import CatalogoDisciplinas
from goes_science_kg.curriculo.contratos import Curriculo
from goes_science_kg.modelos import Nodo, TipoNodo
from goes_science_kg.motor.contratos import Contrato, Evidencia, huella
from goes_science_kg.producto._conocimiento_contratos import PoliticaConocimiento
from goes_science_kg.producto._juicios_contratos import (
    ROLES_CONOCIMIENTO,
    ColeccionConocimiento,
    ExpedienteConocimiento,
)
from goes_science_kg.producto.relaciones import coleccionar_resultados, consolidar_relaciones

if TYPE_CHECKING:
    from goes_science_kg.motor.conocimiento import MotorConocimiento


class RegistroExpediente(Contrato):
    """La preparación se valida con ExpedienteConocimiento al resolver sus IDs de evidencia."""

    preparacion: dict
    evidencias_ids: tuple[str, ...]


class ArchivoConocimiento(Contrato):
    version: Literal["conocimiento-publicado-1", "conocimiento-publicado-2"] = "conocimiento-publicado-1"
    huella_archivo: str = Field(pattern=r"^[a-f0-9]{64}$")
    huella_curriculo: str = Field(pattern=r"^[a-f0-9]{64}$")
    huella_referencia: str = Field(pattern=r"^[a-f0-9]{64}$")
    modelos: dict[str, str]
    configuracion_modelo: dict
    politica: PoliticaConocimiento
    fuentes: dict[str, dict]
    nodos_referencia: tuple[Nodo, ...]
    evidencias: dict[str, Evidencia]
    expedientes: dict[str, RegistroExpediente]
    coleccion: ColeccionConocimiento
    componentes: tuple[ArchivoConocimiento, ...] = Field(default=(), max_length=50, exclude_if=lambda v: not v)

    def expediente(self, candidato_id: str) -> ExpedienteConocimiento:
        registro = self.expedientes[candidato_id]
        if "evidencias" in registro.preparacion or len(set(registro.evidencias_ids)) != len(registro.evidencias_ids):
            raise ValueError("Registro de expediente ambiguo o con evidencias repetidas")
        return ExpedienteConocimiento.model_validate(
            registro.preparacion
            | {
                "evidencias": [self.evidencias[i].model_dump(mode="json") for i in registro.evidencias_ids],
            }
        )


def crear_archivo_conocimiento(motor: MotorConocimiento, estados: list[dict]) -> ArchivoConocimiento:
    """Rehidrata antes de archivar; no admite sólo una colección con banderas favorables."""
    coleccion = consolidar_relaciones(motor, estados)
    expedientes, evidencias = {}, {}
    for estado in estados:
        e = ExpedienteConocimiento.model_validate(estado["preparacion"])
        expedientes[e.candidato_id] = RegistroExpediente(
            preparacion=e.model_dump(mode="json", exclude={"evidencias"}),
            evidencias_ids=tuple(x.id for x in e.evidencias),
        )
        for prueba in e.evidencias:
            if prueba.id in evidencias and evidencias[prueba.id] != prueba:
                raise ValueError("Dos expedientes atribuyen contenido distinto a una misma evidencia")
            evidencias[prueba.id] = prueba
    documentos = {e.fuente["documento"].removeprefix("DOC:") for e in evidencias.values()}
    locales = {f.id for f in motor.preparador.curriculo.filas}
    extremos = {
        i
        for estado in estados
        if estado["preparacion"]["estado"] == "preparado"
        for i in (estado["preparacion"]["origen"], estado["preparacion"]["destino"])
    } - locales
    datos = dict(
        version="conocimiento-publicado-1",
        huella_curriculo=motor.preparador.curriculo.huella,
        huella_referencia=motor.preparador.informe.huella_referencia,
        modelos={r: motor.modelo.nombre_modelo(r) for r in ROLES_CONOCIMIENTO},
        configuracion_modelo=motor.modelo.configuracion.model_dump(mode="json")
        if getattr(motor.modelo, "configuracion", None) is not None
        else {},
        politica=motor.preparador.informe.politica.model_dump(mode="json"),
        fuentes={i: motor.preparador.fuentes.catalogo[i] for i in sorted(documentos)},
        nodos_referencia=[motor.preparador.nodos[i].model_dump(mode="json") for i in sorted(extremos)],
        evidencias={i: e.model_dump(mode="json") for i, e in sorted(evidencias.items())},
        expedientes={i: e.model_dump(mode="json") for i, e in sorted(expedientes.items())},
        coleccion=coleccion.model_dump(mode="json"),
    )
    archivo = ArchivoConocimiento(huella_archivo=huella(datos), **datos)
    validar_archivo_conocimiento(archivo, motor.preparador.curriculo)
    return archivo


def _verificar_fragmentos(expediente: ExpedienteConocimiento) -> None:
    evidencias = {e.id: e for e in expediente.evidencias}
    if len(evidencias) != len(expediente.evidencias) or len({f.id for f in expediente.fragmentos}) != len(
        expediente.fragmentos
    ):
        raise ValueError("Evidencias o fragmentos duplicados en el expediente")
    for f in expediente.fragmentos:
        e = evidencias[f.evidencia_id]
        datos = json.dumps([e.id, e.version, e.huella, e.fuente, f.literal], ensure_ascii=False, sort_keys=True)
        if f.id != "F:" + hashlib.sha256(datos.encode()).hexdigest()[:24] or f.literal not in " ".join(e.texto.split()):
            raise ValueError("Un fragmento no pertenece al texto e identidad de su evidencia")
    for nombre, ids in expediente.grupos.items():
        if not ids or set(ids) - evidencias.keys():
            raise ValueError("Grupo de evidencia vacío o con localizadores desconocidos")
        version = "V4" if nombre in {"fila", "objetivo_local", "evaluacion_local"} else "referencia"
        if any(evidencias[i].version != version for i in ids):
            raise ValueError("Un grupo cambia el papel de evidencia local y externa")


def _verificar_fila(expediente: ExpedienteConocimiento, fila) -> None:
    if expediente.estado != "preparado":
        return
    esperadas = {
        f"{fila.id}#CELDA:{c.coordenada}"
        for c in fila.celdas
        if c.tipo_excel != "f" and c.valor is not None and str(c.valor).strip()
    }
    locales = {e.id for e in expediente.evidencias if e.version == "V4"}
    if locales != esperadas or set(expediente.grupos.get("fila", ())) != esperadas:
        raise ValueError("El expediente debe conservar todas las celdas locales no vacías y sin fórmulas")
    for nombre, campos in {
        "objetivo_local": {"procedimental"},
        "evaluacion_local": {
            "indicadores_logro",
            "indicador_avanzado",
            "evidencia_aprendizaje",
        },
    }.items():
        ids = {
            f"{fila.id}#CELDA:{c.coordenada}"
            for c in fila.celdas
            if c.campo in campos and f"{fila.id}#CELDA:{c.coordenada}" in esperadas
        }
        if (ids and set(expediente.grupos.get(nombre, ())) != ids) or (not ids and nombre in expediente.grupos):
            raise ValueError("Los grupos de objetivo y evaluación deben corresponder a las celdas originales")
    por_coordenada = {c.coordenada: c for c in fila.celdas}
    for e in expediente.evidencias:
        if e.version != "V4":
            continue
        coordenada = e.id.removeprefix(fila.id + "#CELDA:")
        celda = por_coordenada[coordenada].model_dump(mode="json")
        fisicas = e.model_dump(mode="json")["fuente"].get("celdas_verificadas", [])
        if len(fisicas) != 1 or e.fuente.get("celdas") != [coordenada]:
            raise ValueError("La evidencia debe identificar una celda física exacta")
        fisica = fisicas[0]
        if (
            fisica.get("coordenada_solicitada") != coordenada
            or fisica.get("coordenada_origen") != (celda["origen_combinado"] or coordenada)
            or fisica.get("tipo_excel") != celda["tipo_excel"]
            or fisica.get("valor_es_formula") is not False
            or any(
                (type(fisica.get(a)), fisica.get(a)) != (type(celda[b]), celda[b])
                for a, b in (("valor_real", "valor"), ("valor_original", "valor_original"))
            )
        ):
            raise ValueError("Coordenada, ancla, tipo o valor de evidencia distinto del currículo original")


def _verificar_extremos(archivo: ArchivoConocimiento, expediente: ExpedienteConocimiento, nodos) -> None:
    papeles = ("destino", "origen") if expediente.tipo_relacion == "prerrequisito_necesario" else ("destino",)
    for papel in papeles:
        id_ = getattr(expediente, papel)
        nodo = nodos[id_]
        if expediente.descriptores[papel].get("huella_registro") != huella(nodo) or (
            expediente.descriptores[papel].get("id") != id_
            or expediente.descriptores[papel].get("etiqueta_historica") != nodo.etiqueta
        ):
            raise ValueError("El extremo no corresponde al registro exacto que examinaron los jueces")
    if expediente.tipo_relacion == "contraste_documental":
        nodo = nodos[expediente.destino]
        if nodo.fuente is None:
            raise ValueError("El objetivo extranjero requiere localizador nativo")
        edicion = archivo.politica.ediciones_por_documento.get(nodo.fuente.documento)
        registro = archivo.fuentes[nodo.fuente.documento.removeprefix("DOC:")]
        if (
            edicion is None
            or edicion.sha256 != registro.get("sha256")
            or edicion.version_documental != str(registro.get("version_documental", registro.get("anio", "")))
        ):
            raise ValueError("La política no corresponde a la edición extranjera utilizada")
        ids = expediente.grupos.get("objetivo_extranjero", ())
        if not ids:
            raise ValueError("Falta el grupo del objetivo extranjero nativo")
        for id_ in ids:
            e = archivo.evidencias[id_]
            if (
                e.version != "referencia"
                or e.fuente.get("documento") != nodo.fuente.documento
                or any(
                    valor is not None and e.fuente.get(campo) != valor
                    for campo, valor in nodo.fuente.model_dump(exclude={"documento"}).items()
                )
            ):
                raise ValueError("El objetivo extranjero se sustituyó por otro localizador")
        descriptor = expediente.descriptores["destino"]
        if (
            descriptor.get("pais") != nodo.props.get("pais")
            or descriptor.get("tramo_nativo") != nodo.props.get("grado_o_tramo")
            or descriptor.get("equivalencia_grado_sv") is not None
        ):
            raise ValueError("El contraste alteró país, tramo nativo o equivalencia de grado")


def validar_archivo_conocimiento(
    archivo: ArchivoConocimiento,
    curriculo: Curriculo,
    *,
    catalogo: CatalogoDisciplinas | None = None,
    modelos_esperados: dict[str, str] | None = None,
) -> None:
    """Integridad y cierre sin modelos. Los bytes físicos se rehidratan en publicación y consulta."""
    from goes_science_kg.motor.validacion_conocimiento import resolver_resultado

    if archivo.huella_archivo != huella(archivo.model_dump(mode="json", exclude={"huella_archivo"})):
        raise ValueError("El archivo de conocimiento no conserva su identidad")
    if archivo.huella_curriculo != curriculo.huella or archivo.coleccion.huella_curriculo != curriculo.huella:
        raise ValueError("Conocimiento de otro currículo")
    if set(archivo.modelos) != set(ROLES_CONOCIMIENTO) or any(not m for m in archivo.modelos.values()):
        raise ValueError("El archivo requiere identidad de los cuatro modelos")
    if modelos_esperados is not None and archivo.modelos != modelos_esperados:
        raise ValueError("Modelos de conocimiento distintos de la política de publicación")
    motores = None
    if archivo.version == "conocimiento-publicado-2":
        from goes_science_kg.producto.composicion import componer_archivos

        if len(archivo.componentes) < 2 or any(c.version != "conocimiento-publicado-1" for c in archivo.componentes):
            raise ValueError("La composición necesita al menos dos archivos originales sin anidación")
        esperado = componer_archivos(
            archivo.componentes,
            curriculo,
            catalogo=catalogo,
            modelos_esperados=modelos_esperados,
            validar_resultado=False,
        )
        if esperado != archivo:
            raise ValueError("La composición no corresponde a la unión íntegra de sus archivos originales")
        motores = {r.solicitud.candidato_id: r.huella_motor for r in archivo.coleccion.resultados}
    elif archivo.componentes:
        raise ValueError("Un archivo de primera versión no admite componentes")
    resultados = {r.solicitud.candidato_id: r for r in archivo.coleccion.resultados}
    if len(resultados) != len(archivo.coleccion.resultados) or resultados.keys() != archivo.expedientes.keys():
        raise ValueError("El archivo debe conservar todos los resultados y sus expedientes únicos")
    filas = {f.id: f for f in curriculo.filas}
    fuentes_locales = {f.id: f for f in curriculo.fuentes}
    usados, documentos, reconstruidos, por_candidato = set(), set(), [], {}
    for id_, resultado in resultados.items():
        e = archivo.expediente(id_)
        fila = filas[e.fila_id]
        if (
            e.candidato_id != id_
            or e.huella_curriculo != curriculo.huella
            or e.huella_referencia != archivo.huella_referencia
            or e.grado != fila.grado
            or e.asignatura_malla != fila.asignatura_malla
        ):
            raise ValueError("El expediente no corresponde a su candidato, fila o currículo")
        por_candidato[id_] = fila.id
        _verificar_fragmentos(e)
        _verificar_fila(e, fila)
        if e.estado == "preparado":
            obligatorios = {"fila", "objetivo_local", "destino"}
            if e.tipo_relacion == "prerrequisito_necesario":
                obligatorios |= {"origen", "dependencia"}
            if obligatorios - e.grupos.keys():
                raise ValueError("Faltan grupos primarios obligatorios en la preparación")
        for prueba in e.evidencias:
            usados.add(prueba.id)
            doc = prueba.fuente["documento"].removeprefix("DOC:")
            documentos.add(doc)
            registro = archivo.fuentes[doc]
            if prueba.huella != hashlib.sha256(prueba.texto.encode()).hexdigest() or (
                prueba.fuente.get("sha256") != registro.get("sha256")
            ):
                raise ValueError("La evidencia no conserva texto y edición documentales")
            if prueba.version == "V4" and (
                doc != fila.fuente_id
                or registro.get("sha256") != fuentes_locales[doc].sha256
                or prueba.fuente.get("hoja") != fila.hoja
                or not prueba.id.startswith(fila.id + "#CELDA:")
                or set(prueba.fuente.get("celdas", [])) - {c.coordenada for c in fila.celdas}
            ):
                raise ValueError("La evidencia local pertenece a otra fila o fuente")
        reconstruido = resolver_resultado(
            expediente=e,
            solicitud=resultado.solicitud,
            ejecucion_id=resultado.ejecucion_id,
            huella_motor=resultado.huella_motor if motores is not None else archivo.coleccion.huella_motor,
            modelos=archivo.modelos,
            salidas={d.rol: {"dictamen": d.model_dump(mode="json"), "error": None} for d in resultado.dictamenes},
        )
        if reconstruido != resultado:
            raise ValueError("El resultado no corresponde a sus juicios y preparación")
        reconstruidos.append(reconstruido)
    if usados != archivo.evidencias.keys() or documentos != archivo.fuentes.keys():
        raise ValueError("Evidencia o documentos huérfanos en el archivo de conocimiento")
    coleccion = coleccionar_resultados(
        reconstruidos,
        huella_curriculo=curriculo.huella,
        huella_motor=archivo.coleccion.huella_motor,
        filas_por_candidato=por_candidato,
        motores_por_candidato=motores,
    )
    if coleccion != archivo.coleccion:
        raise ValueError("La admisión o proyección de dependencias no corresponde a los juicios")
    nodos = {n.id: n for n in archivo.nodos_referencia}
    preparados = [
        archivo.expediente(i)
        for i in archivo.expedientes
        if archivo.expedientes[i].preparacion["estado"] == "preparado"
    ]
    extremos = {i for e in preparados for i in (e.origen, e.destino)} - filas.keys()
    if len(nodos) != len(archivo.nodos_referencia) or nodos.keys() != extremos:
        raise ValueError("Los extremos de conocimiento deben estar completos y sin nodos ajenos")
    tipos = {
        "trabaja_concepto": TipoNodo.CONCEPTO,
        "practica_declarada": TipoNodo.PRACTICA,
        "contraste_documental": TipoNodo.OBJETIVO_PAIS,
        "prerrequisito_necesario": TipoNodo.CONCEPTO,
    }
    decisiones = {f.fila_id: f for f in catalogo.filas} if catalogo is not None else {}
    for e in preparados:
        _verificar_extremos(archivo, e, nodos)
    for r in coleccion.relaciones_admisibles:
        if (
            nodos[r.destino].tipo != tipos[r.tipo]
            or (r.tipo == "prerrequisito_necesario" and nodos[r.origen].tipo != TipoNodo.CONCEPTO)
            or (r.tipo != "prerrequisito_necesario" and r.origen != r.fila_id)
        ):
            raise ValueError("Tipo de extremo incompatible con la relación")
        if catalogo is not None and decisiones[r.fila_id].estado not in {"declarado_malla", "coincidencia_automatica"}:
            raise ValueError("Una relación respaldada no habilita una fila sin clasificación disciplinar")
