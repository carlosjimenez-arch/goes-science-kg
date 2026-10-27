"""Preparación de cierre trazable y sin Vertex; nunca cambia límites ni publicaciones."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import yaml

from goes_science_kg.archivos import destino_generado
from goes_science_kg.clases.presupuesto import comprobar_continuidad, configuracion
from goes_science_kg.materiales.almacen import Biblioteca
from goes_science_kg.materiales.compilacion import serializar, sha
from goes_science_kg.operacion.respaldo import nombre_seguro
from goes_science_kg.produccion.revision_docente.calibracion import agregar
from goes_science_kg.produccion.revision_docente.contexto import codificar_identidades, item
from goes_science_kg.produccion.revision_docente.contratos import ROLES, leer_ruta
from goes_science_kg.produccion.revision_docente.edicion import escribir_campo, validar_edicion
from goes_science_kg.produccion.revision_docente.ejecucion import guardar, mensaje, preflight, proveedor_cfg
from goes_science_kg.produccion.revision_docente.procesamiento import numerar_fuentes


def propuesta_presupuesto(plan, limites):
    """Calcula una propuesta, no autorización ni modificación del contador."""
    minimo_total = plan["consumo_inicial"]["llamadas"] + plan["primera_pasada_llamadas"]
    total = plan["consumo_inicial"]["llamadas"] + plan["max_nuevas_llamadas"]
    reserva_total = plan["consumo_inicial"]["reserva_usd"] + plan["max_reserva_nueva_usd"]
    return {
        "autorizado": False,
        "minimo_max_llamadas_primera_pasada": minimo_total,
        "max_llamadas_acumuladas_propuesto": max(limites["max_llamadas_acumuladas"], total),
        "aumento_llamadas_recomendado": max(0, total - limites["max_llamadas_acumuladas"]),
        "max_reserva_usd_acumulada_vigente": limites["max_reserva_usd_acumulada"],
        "reserva_acumulada_max_prevista": reserva_total,
        "requiere_aumentar_reserva_usd": reserva_total > limites["max_reserva_usd_acumulada"],
        "safe_si_se_autorizan_solo_las_llamadas": reserva_total <= limites["max_reserva_usd_acumulada"],
        "limite": "Cota según las tarifas configuradas, no factura ni garantía de aprobación pedagógica.",
    }


def recuperar_fuentes(contextos, seleccionados):
    """Intersección común más recuperación explícita de las filas seleccionadas."""
    coleccion, recuperadas, conjuntos = {}, {}, []
    for s in contextos:
        alias = {}
        for f in s["fuentes"]:
            real = f.get("identidad_original", f["id"])
            alias[f["id"]] = real
            texto = "".join(f["fragmentos"])
            if sha(texto.encode()) != f["texto_visible_sha256"]:
                raise ValueError("La fuente capturada perdió su texto literal")
            limpia = {"id": real, "texto": texto, "fuente": f["fuente"]}
            if real in coleccion and coleccion[real] != limpia:
                raise ValueError("La misma fuente tiene contenidos diferentes")
            coleccion[real] = limpia
        conjuntos.append(set(alias.values()))
        for i in s["items"]:
            real = i.get("identidad_original", i["id"])
            if real in seleccionados:
                recuperadas[real] = [alias[id_] for id_ in i.get("fuentes_recuperadas_ids", [])]
    if not conjuntos:
        raise ValueError("Faltan contextos documentales de la revisión anterior")
    comunes = set.intersection(*conjuntos)
    ids = comunes | {id_ for valores in recuperadas.values() for id_ in valores}
    return [coleccion[id_] for id_ in sorted(ids)], recuperadas, len(comunes)


def referencias_metrologia(carpeta):
    from pypdf import PdfReader

    manifest = json.loads((carpeta / "manifest.json").read_bytes())
    fuentes, comprobaciones = [], []
    paginas = {"NIST_HB1052": [10, 13], "BIPM_SI9": [134, 135]}
    if {f["id"] for f in manifest["fuentes"]} != set(paginas):
        raise ValueError("Se requieren las dos referencias de metrología previstas")
    for f in manifest["fuentes"]:
        nombre_seguro(f["archivo"])
        archivo = carpeta / f["archivo"]
        if archivo.is_symlink() or not archivo.is_file() or archivo.suffix != ".pdf":
            raise ValueError("Las referencias deben ser PDF propios")
        raw = archivo.read_bytes()
        if (len(raw), sha(raw)) != (f["bytes"], f["sha256"]):
            raise ValueError("La referencia primaria perdió sus bytes")
        lector = PdfReader(archivo)
        for pagina in paginas[f["id"]]:
            texto = lector.pages[pagina - 1].extract_text() or ""
            fuentes.append(
                {
                    "id": f"CIERRE:METROLOGIA:{f['id']}:PDF:{pagina}",
                    "texto": texto,
                    "fuente": {
                        "url": f["url"],
                        "sha256": f["sha256"],
                        "pagina_pdf": pagina,
                        "archivo_capturado": f["archivo"],
                        "texto_pagina_sha256": sha(texto.encode()),
                    },
                }
            )
        comprobaciones.append(f | {"paginas_pdf": paginas[f["id"]]})
    return fuentes, comprobaciones


def preparar(base: Path, destino: Path, referencias: Path):
    destino_generado(destino / "preflight.json")
    if destino.exists() or destino.is_symlink():
        raise ValueError("La captura de cierre requiere un directorio nuevo")
    ledger = base / "data/operaciones/registro.sqlite"
    antes = sha(ledger.read_bytes())
    consumo, limites = comprobar_continuidad(ledger), configuracion()
    cfg = yaml.safe_load((base / "config/cierre_indicadores_ciencias.yaml").read_bytes())
    biblioteca = Biblioteca(base / "data/materiales_produccion_v4")
    indicadores = Biblioteca(base / "data/materiales_indicadores_v4")
    if (biblioteca.manifest["id"], indicadores.manifest["id"]) != (
        cfg["biblioteca_preparaciones"],
        cfg["biblioteca_indicadores"],
    ):
        raise ValueError("Las bibliotecas cambiaron; revisar el alcance antes de presupuestar")
    registros, archivos = biblioteca.exportar()
    indicadores.validar()
    ref = indicadores.manifest["originales"]["indicadores/indice.json"]
    catalogo = json.loads(indicadores.archivo(ref["sha256"])[0])["indicadores"]
    pendientes = [i for i in catalogo if i["estado_contextos"] == "contextos_con_pendientes"]
    objetivos = {
        r["id"] for r in registros if r["tipo"] == "paquete_objetivo" and r["estado"] != "revision_automatica_completa"
    }
    if not objetivos or objetivos != {f for i in pendientes for f in i["filas_ids"]}:
        raise ValueError("Los indicadores y las preparaciones pendientes no coinciden")
    unidades = [
        r
        for r in registros
        if r["tipo"] == "paquete_unidad"
        and (r["estado"] != "revision_automatica_completa" or objetivos.intersection(r["documento"]["filas_ids"]))
    ]
    ids = objetivos | {r["id"] for r in unidades} | {f for r in unidades for f in r["documento"]["filas_ids"]}
    nuevos = deepcopy([r for r in registros if r["id"] in ids])
    por_id = {r["id"]: r for r in nuevos}
    cambios = []
    for enmienda in cfg["enmiendas"]:
        r = por_id[enmienda["item_id"]]
        e = r["documento"]["edicion_docente"]
        if sha(serializar(e)) != enmienda["edicion_base_sha256"]:
            raise ValueError("La aclaración editorial no corresponde a la edición publicada")
        for ruta, texto in enmienda["cambios"].items():
            previo = leer_ruta(e, ruta)
            escribir_campo(e, ruta, texto)
            cambios.append(
                {"item_id": r["id"], "ruta": ruta, "anterior": previo, "nuevo": texto, "motivo": enmienda["motivo"]}
            )
    for r in nuevos:
        d = r["documento"]
        validar_edicion(d["edicion_docente"])
        d["revision_docente_previa_cierre"] = deepcopy(d["revision_docente"])
        r.pop("sha256", None)
        r["estado"] = d["estado_revision"] = "revision_automatica_con_pendientes"
        d["revision_docente"] = {
            "estado": r["estado"],
            "edicion_sha256": sha(serializar(d["edicion_docente"])),
            "lecturas": [],
            "faltan_roles": list(ROLES),
            "etapa": "cierre_pendiente_nuevas_lecturas",
        }
    anteriores = {r["id"]: r for r in registros}
    if any(r["documento"].get("original") != anteriores[r["id"]]["documento"].get("original") for r in nuevos):
        raise ValueError("Se alteró un original")
    previas = json.loads(archivos["didactica/revision/ronda_2.json"])
    documentos, enlaces, comunes = recuperar_fuentes(previas, ids)
    adicionales, referencias_verificadas = referencias_metrologia(referencias)
    s = {
        "lote": 0,
        "items": [
            item(r) | {"fuentes_recuperadas_ids": enlaces.get(r["id"], [])}
            for r in sorted(nuevos, key=lambda r: r["id"])
        ],
        "fuentes": documentos + adicionales,
    }
    s = numerar_fuentes(codificar_identidades(s))
    s["restricciones_originales"] = [
        {
            "item_id": i["id"],
            "notacion": i["original"]["notacion"],
            "indicador_logro_literal": i["original"]["indicadores_logro"],
        }
        for i in s["items"]
        if i["original"] is not None
    ]
    agregar(s, registros)
    if len(s["items"]) > 230:
        raise ValueError("El contexto requiere otro plan de lotes y presupuesto")
    plan = preflight([s], ledger, proveedor_cfg())
    if plan["consumo_inicial"] != consumo or sha(ledger.read_bytes()) != antes:
        raise ValueError("El ledger cambió durante la preparación")
    plan.update(
        {
            "tipo_campana": cfg["version"],
            "biblioteca_preparaciones": biblioteca.manifest["id"],
            "biblioteca_indicadores": indicadores.manifest["id"],
            "indicadores_pendientes": [i["id"] for i in pendientes],
            "objetivos_pendientes": sorted(objetivos),
            "unidades_dependientes": sorted(r["id"] for r in unidades),
            "objetivos_en_contexto": sum(r["tipo"] == "paquete_objetivo" for r in nuevos),
            "elementos_reales": len(nuevos),
            "controles_negativos": 3,
            "fuentes_comunes": comunes,
            "fuentes_totales": len(s["fuentes"]),
            "mensaje_bytes": len(mensaje(s).encode()),
            "llamadas_nuevas_preparacion": 0,
            "originales_modificados": 0,
            "config_enmiendas_sha256": sha(serializar(cfg)),
            "limite_lecturas": "Cuatro perfiles sobre preparaciones y unidades. El reagrupamiento por indicador "
            "no se convierte en evaluación específica de cada actividad.",
        }
    )
    plan["propuesta_presupuesto"] = propuesta_presupuesto(plan, limites)
    guardar(destino / "candidato_1.json", nuevos)
    guardar(destino / "ronda_1.json", [s])
    guardar(destino / "enmiendas_preparadas.json", cambios)
    guardar(destino / "referencias_verificadas.json", referencias_verificadas)
    guardar(destino / "indicadores_pendientes.json", pendientes)
    guardar(destino / "preflight.json", plan)
    biblioteca.comprobar()
    indicadores.comprobar()
    return plan
