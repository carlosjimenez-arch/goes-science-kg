"""Extrae exclusivamente objetos JSON completos de una respuesta truncada; no cierra ni inventa votos."""

from __future__ import annotations

import json

from goes_science_kg.produccion.revision_docente.procesamiento import DictamenSeleccion


def extraer_prefijo(texto):
    dec = json.JSONDecoder()
    n = len(texto)

    def espacios(p):
        while p < n and texto[p].isspace():
            p += 1
        return p

    p = espacios(0)
    if p >= n or texto[p] != "{":
        raise ValueError("La respuesta no comienza como un objeto JSON")
    p += 1
    campos, rangos = {}, []
    truncada = False
    while p < n:
        p = espacios(p)
        try:
            clave, p = dec.raw_decode(texto, p)
        except json.JSONDecodeError:
            truncada = True
            break
        if clave not in {"banco_citas", "items", "observaciones"} or clave in campos:
            raise ValueError("Clave inesperada o repetida en la respuesta parcial")
        p = espacios(p)
        if p >= n or texto[p] != ":":
            raise ValueError("Separador de campo ausente")
        p = espacios(p + 1)
        if clave == "items":
            if p >= n or texto[p] != "[":
                raise ValueError("Las decisiones no son un array")
            p = espacios(p + 1)
            elementos = []
            while p < n and texto[p] != "]":
                inicio = p
                try:
                    valor, fin = dec.raw_decode(texto, p)
                except json.JSONDecodeError:
                    truncada = True
                    break
                elementos.append(valor)
                rangos.append({"inicio": inicio, "fin": fin})
                p = espacios(fin)
                if p < n and texto[p] == ",":
                    p = espacios(p + 1)
                elif p >= n or texto[p] != "]":
                    truncada = True
                    break
            campos[clave] = elementos
            if truncada or p >= n:
                truncada = True
                break
            p += 1
        else:
            try:
                campos[clave], p = dec.raw_decode(texto, p)
            except json.JSONDecodeError:
                truncada = True
                break
        p = espacios(p)
        if p >= n:
            truncada = True
            break
        if texto[p] == "}":
            break
        if texto[p] != ",":
            raise ValueError("Separador de campos incorrecto")
        p += 1
    if not truncada or not campos.get("banco_citas") or not campos.get("items"):
        raise ValueError("No hay un banco completo y decisiones completas recuperables de una respuesta truncada")
    observaciones = campos.get("observaciones")
    seleccion = DictamenSeleccion.model_validate(
        {
            "banco_citas": campos["banco_citas"],
            "items": campos["items"],
            "observaciones": observaciones
            if observaciones is not None
            else "METADATO DEL HARNESS: observaciones globales no recibidas; decisiones JSON completas extraídas.",
        }
    )
    return seleccion, {
        "version": "prefijo-json-completo-1",
        "respuesta_truncada": True,
        "decisiones_completas": len(rangos),
        "rangos_decisiones": rangos,
        "observaciones_modelo_recibidas": observaciones is not None,
        "votos_inventados": 0,
    }


def recuperar(campana, ledger, *, ronda, lote, rol):
    import sqlite3
    from contextlib import closing

    from goes_science_kg.config import cargar
    from goes_science_kg.materiales.compilacion import serializar, sha
    from goes_science_kg.motor.vertex import clave_solicitud
    from goes_science_kg.produccion.revision_docente.contratos import ROLES
    from goes_science_kg.produccion.revision_docente.ejecucion import TRANSPORTE, guardar, mensaje, proveedor_cfg
    from goes_science_kg.produccion.revision_docente.procesamiento import procesar
    from goes_science_kg.produccion.revision_docente.prompts import sistema

    if rol not in ROLES or ronda not in {1, 2} or type(lote) is not int or lote < 0:
        raise ValueError("Rol, ronda o lote ajeno al protocolo")
    p = campana / "lecturas" / f"r{ronda}_l{lote}_{rol}.json"
    if p.exists():
        raise ValueError("Ya existe una lectura; no se sobrescribe")
    s = next(s for s in json.loads((campana / f"ronda_{ronda}.json").read_bytes()) if s["lote"] == lote)
    identidad = json.loads((campana / "intentos" / f"r{ronda}_l{lote}_{rol}_1.json").read_bytes())
    cfg = proveedor_cfg()
    if identidad["solicitud_sha256"] != sha(serializar(s)) or identidad["mensaje_sha256"] != sha(mensaje(s).encode()):
        raise ValueError("La solicitud parcial perdió su identidad")
    niveles = dict(cfg.niveles_razonamiento)
    niveles[rol] = identidad.get(
        "nivel_razonamiento", cargar("mejoras_curriculares")["vertex"]["niveles_razonamiento"][rol]
    )
    actual = cfg.model_copy(update={"niveles_razonamiento": niveles})
    clave = clave_solicitud(actual, rol=rol, sistema=sistema(rol), mensaje=mensaje(s), esquema=TRANSPORTE)
    with closing(sqlite3.connect(ledger.resolve().as_uri() + "?mode=ro", uri=True)) as db:
        r = db.execute(
            "SELECT l.id,s.texto,s.sha256 FROM llamadas l JOIN salidas_llm s ON l.id=s.llamada "
            "WHERE l.clave=? ORDER BY l.creada DESC LIMIT 1",
            (clave,),
        ).fetchone()
    if r is None or sha(r[1].encode()) != r[2]:
        raise ValueError("Falta una respuesta recibida íntegra en el ledger")
    d, meta = extraer_prefijo(r[1])
    guardar(
        p,
        {
            "identidad": identidad,
            **procesar(d, s, rol),
            "recuperacion_parcial": meta | {"llamada_id": r[0], "respuesta_sha256": r[2]},
        },
    )
    return {"decisiones_recuperadas": len(d.items), "elementos_solicitados": len(s["items"]), "nuevas_invocaciones": 0}
