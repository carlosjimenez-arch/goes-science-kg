"""Selección literal de evidencia e aislamiento de fallos por paquete, sin fabricar votos."""

from __future__ import annotations

from collections import Counter

from pydantic import Field

from goes_science_kg.motor.contratos import Contrato
from goes_science_kg.produccion.revision_docente.contexto import vista_revision
from goes_science_kg.produccion.revision_docente.contratos import (
    DictamenLote,
    Hallazgo,
    LecturaItem,
    Respaldo,
    leer_ruta,
    validar_dictamen,
)


class SeleccionCita(Contrato):
    id: str
    fuente_id: str
    fragmento: int = Field(ge=0, le=10000)


class ObservacionSeleccion(Contrato):
    ruta: str
    problema: str = Field(min_length=20)
    reemplazo: str
    respaldo_ids: list[str] = Field(max_length=3)


class DecisionSeleccion(Contrato):
    id: str
    veredicto: str
    comprobacion: str = Field(min_length=30, max_length=1200)
    respaldo_ids: list[str] = Field(max_length=3)
    hallazgos: list[ObservacionSeleccion] = Field(max_length=8)


class DictamenSeleccion(Contrato):
    banco_citas: list[SeleccionCita] = Field(max_length=690)
    items: list[DecisionSeleccion] = Field(min_length=1, max_length=230)
    observaciones: str = Field(max_length=2000)


def fragmentar(texto, maximo=350):
    """Partición contigua, sin perder caracteres; el contexto se conserva en orden."""
    salida, inicio = [], 0
    while inicio < len(texto):
        fin = min(len(texto), inicio + maximo)
        if fin < len(texto):
            corte = texto.rfind(" ", inicio + maximo // 2, fin)
            if corte > inicio:
                fin = corte + 1
        salida.append(texto[inicio:fin])
        inicio = fin
    if "".join(salida) != texto:
        raise ValueError("Se perdió texto al numerar la fuente")
    return salida


def numerar_fuentes(solicitud):
    from copy import deepcopy

    from goes_science_kg.materiales.compilacion import sha

    s = deepcopy(solicitud)
    for f in s["fuentes"]:
        texto = f.pop("texto")
        f["fragmentos"] = fragmentar(texto)
        f["texto_visible_sha256"] = sha(texto.encode())
    return s


def procesar(salida, solicitud, rol):
    """Un error de evidencia invalida la lectura de esa fila, no crea una abstención del modelo."""
    items = {i["id"]: i for i in solicitud["items"]}
    fuentes = {f["id"]: f for f in solicitud["fuentes"]}
    visibles = (
        {i["id"]: i["edicion"] for i in vista_revision(solicitud)["items"]}
        if solicitud.get("iteracion_lectura") == 2
        else None
    )
    banco, citas_erroneas = {}, {}
    conteo_citas = Counter(c.id for c in salida.banco_citas)
    for c in salida.banco_citas:
        try:
            if conteo_citas[c.id] != 1 or c.fuente_id not in fuentes:
                raise ValueError("Cita repetida o fuente ausente")
            texto = fuentes[c.fuente_id]["fragmentos"][c.fragmento]
            if texto.strip().lower().startswith(("watch the following video", "https://", "http://")):
                raise ValueError("Una invitación o un enlace no respalda el contenido")
            banco[c.id] = Respaldo(fuente_id=c.fuente_id, cita=texto)
        except (ValueError, IndexError) as error:
            citas_erroneas[c.id] = str(error)
    conteos = Counter(i.id for i in salida.items)
    validas, errores = [], {}
    for id_, item in items.items():
        if conteos[id_] != 1:
            errores[id_] = "Falta la decisión o está repetida"
            continue
        r = next(i for i in salida.items if i.id == id_)
        try:
            if visibles is not None:
                for h in r.hallazgos:
                    if {"tarea_ids", "filas_ids", "tarea_de_transferencia_original"}.intersection(h.ruta.split("/")):
                        raise ValueError("El hallazgo intenta modificar un vínculo o antecedente literal")
                    leer_ruta(visibles[id_], h.ruta)
            ids = [*r.respaldo_ids, *(c for h in r.hallazgos for c in h.respaldo_ids)]
            if any(c not in banco or c in citas_erroneas for c in ids):
                raise ValueError("La decisión selecciona una cita no verificable")
            if (
                r.veredicto == "aprobar"
                and rol == "revision_psicopedagogia"
                and not any(
                    fuentes[banco[c].fuente_id]["identidad_original"].startswith(("ies_", "mined_", "pisa_", "MINED:"))
                    for c in r.respaldo_ids
                )
            ):
                raise ValueError(
                    "La lectura psicopedagógica requiere un principio didáctico, no sólo un dato científico"
                )
            hallazgos = [
                Hallazgo(
                    ruta=h.ruta,
                    ancla=leer_ruta(item["edicion"], h.ruta),
                    problema=h.problema,
                    reemplazo=h.reemplazo,
                    respaldo=[banco[c] for c in h.respaldo_ids],
                )
                for h in r.hallazgos
            ]
            lectura = LecturaItem(
                id=id_,
                veredicto=r.veredicto,
                comprobacion=r.comprobacion,
                respaldos=[banco[c] for c in r.respaldo_ids],
                hallazgos=hallazgos,
            )
            parcial = DictamenLote(items=[lectura], observaciones=salida.observaciones)
            validar_dictamen(parcial, solicitud | {"items": [item]})
            validas.append(lectura.model_dump(mode="json"))
        except (ValueError, KeyError, IndexError) as error:
            errores[id_] = str(error)[:500]
    extras = sorted(set(conteos) - set(items))
    return {
        "dictamen": {"items": validas, "observaciones": salida.observaciones},
        "salida_selecciones": salida.model_dump(mode="json"),
        "validacion_local": {
            "elementos_esperados": len(items),
            "elementos_validos": len(validas),
            "errores_por_item": errores,
            "ids_ajenos": extras,
            "metodo_citas": "fragmentos_seleccionados_por_el_modelo_extraidos_literalmente_por_codigo",
            "anclas": "Campos seleccionados por el modelo y recuperados del contenido exacto.",
        },
    }
