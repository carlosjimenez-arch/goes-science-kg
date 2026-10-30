"""Datos tabulares de aula: copias fijadas, procedencia y límites de verificación explícitos."""

from __future__ import annotations

import json
import re

from goes_science_kg.materiales.compilacion import serializar, sha


def archivos_insumos(base, preparacion):
    from goes_science_kg.clases.compilacion import leer_propio

    archivos, datos = {}, {}
    for ref in preparacion.get("insumos_tabulares", []):
        raw = leer_propio(base, ref["ruta"]).read_bytes()
        if len(raw) != ref["bytes"] or sha(raw) != ref["sha256"] or len(raw) > 1024**2:
            raise ValueError("El insumo tabular cambió o excede el límite")
        d = json.loads(raw)
        if d["version"] != "insumo-tabular-clases-1" or d["id"] != sha(
            serializar({k: v for k, v in d.items() if k != "id"})
        ):
            raise ValueError("Identidad o versión de insumo tabular inválida")
        if d["id"] in datos:
            raise ValueError("Insumo tabular repetido")
        archivos[ref["ruta"]], datos[d["id"]] = raw, d
        semanas_verificadas = set()
        for fuente in d["fuentes"]:
            recibo = leer_propio(base, fuente["recibo"]).read_bytes()
            if len(recibo) > 1024**2 or sha(recibo) != fuente["recibo_sha256"]:
                raise ValueError("La vista textual de la fuente del insumo cambió")
            vista = json.loads(recibo)
            if vista.get("version") != "recibo-vista-textual-web-1" or vista.get("url") != fuente["url"]:
                raise ValueError("La vista textual no corresponde a la fuente declarada")
            bloque = " ".join(" ".join(vista.get("fragmentos_literales", [])).split())
            for ancla in fuente["anclas_verificadas"]:
                if " ".join(ancla.split()) not in bloque:
                    raise ValueError("El dato no corresponde a su documento y ancla textual")
            if fuente.get("original_pdf_verificado") is not False:
                raise ValueError("Una vista textual no acredita la verificación de los bytes del PDF original")
            semana_url = re.search(r"SE([0-9]+)2022\.pdf$", fuente["url"])
            anclas = " ".join(vista.get("fragmentos_literales", []))
            valor = re.search(r"1 Casos con sospecha de dengue ([0-9]+)", anclas)
            if vista.get("version") != "recibo-vista-textual-web-1" or not semana_url or not valor:
                raise ValueError("El recibo no permite verificar el indicador tabular declarado")
            semana = int(semana_url[1])
            filas = [r for r in d["filas"] if r["semana"] == semana]
            if (
                len(filas) != 1
                or f"SE{semana}" not in vista["fragmentos_literales"]
                or filas[0]["sospechas_dengue"] != int(valor[1])
                or filas[0]["desde"] != vista["periodo"]["desde"]
                or filas[0]["hasta"] != vista["periodo"]["hasta"]
                or vista["url"] != fuente["url"]
                or semana in semanas_verificadas
            ):
                raise ValueError("La fila del insumo no corresponde a la semana, fechas y casos del recibo")
            semanas_verificadas.add(semana)
            archivos[fuente["recibo"]] = recibo
        if len(semanas_verificadas) != len(d["filas"]):
            raise ValueError("Hay filas tabulares sin una fuente verificada")
    referidos = set()
    for fila in preparacion["filas"]:
        d = fila.get("datos_contextuales")
        if d is not None:
            if datos.get(d["id"]) != d:
                raise ValueError("Los datos del contexto difieren del insumo tabular fijado")
            referidos.add(d["id"])
    if referidos != set(datos):
        raise ValueError("Los insumos tabulares no corresponden exactamente a las filas del contexto")
    return archivos
