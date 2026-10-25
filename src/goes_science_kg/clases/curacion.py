"""Reduce redundancia documental sin truncar pasajes ni declarar suficiencia científica."""

from __future__ import annotations

import html
import re
from collections import Counter

from goes_science_kg.clases.recuperacion import es_expositivo
from goes_science_kg.materiales.compilacion import serializar, sha


def _texto(evidencia):
    return " ".join(html.unescape(re.sub(r"<[^>]*>", " ", evidencia.texto)).split())


def curar(corpus, documentos, ids_documentos, consultas, *, max_bytes=24000):
    """Conserva un pasaje por documento y añade diversidad si cabe. Una laguna queda explícita."""
    if not 2000 <= max_bytes <= 60000 or len(set(ids_documentos)) != len(ids_documentos):
        raise ValueError("Cota o documentos repetidos en la curación")
    if set(ids_documentos) - documentos.keys():
        raise ValueError("Documento ajeno al catálogo")
    consultas = list(dict.fromkeys(q.strip() for q in consultas if q.strip()))
    if not consultas:
        raise ValueError("La curación requiere consultas específicas")
    ranking, duplicados, propietarios = Counter(), {}, {}
    por_documento = {}
    for doc in ids_documentos:
        candidatos = []
        for e in documentos[doc]["evidencias"]:
            texto = _texto(e)
            # Se conserva el párrafo entero. Los grupos históricos extensos siguen en el corpus.
            if not 60 <= len(texto) <= 4500 or not es_expositivo(texto):
                continue
            if re.match(r"^(?:draw|sketch|list|find|give|make a drawing|show that|write)\b", texto, re.I):
                continue
            identidad = sha(texto.encode())
            previo = duplicados.get((doc, identidad))
            if previo:
                continue
            duplicados[doc, identidad] = e.id
            propietarios[e.id] = doc
            candidatos.append(e.id)
        por_documento[doc] = candidatos
    permitidos = set(propietarios)
    for consulta in consultas:
        for posicion, (id_, _) in enumerate(corpus.indice.buscar(consulta, permitidos=permitidos, limite=200), 1):
            ranking[id_] += 1 / (20 + posicion)
    ordenes = {
        doc: sorted(ids, key=lambda i: (-ranking[i], len(serializar(corpus.evidencias[i].model_dump())), i))
        for doc, ids in por_documento.items()
    }
    elegidas, pendientes = [], {}

    def anexar(id_):
        e = corpus.evidencias[id_]
        datos = e.model_dump(mode="json")
        if len(serializar([*elegidas, datos])) > max_bytes:
            return False
        corpus.verificar(e)
        elegidas.append(datos)
        return True

    # Primera pasada: cada capítulo seleccionado conserva representación dentro de la cota.
    for doc in ids_documentos:
        if not any(anexar(id_) for id_ in ordenes[doc] if ranking[id_] > 0):
            pendientes[doc] = "No hay un pasaje expositivo pertinente íntegro dentro de la cota"
    # Segunda pasada: otro pasaje por capítulo si aporta texto no contenido en el elegido.
    for doc in ids_documentos:
        textos = [_texto(corpus.evidencias[e["id"]]) for e in elegidas]
        for id_ in ordenes[doc]:
            texto = _texto(corpus.evidencias[id_])
            if ranking[id_] > 0 and not any(texto in t or t in texto for t in textos) and anexar(id_):
                break
    return {
        "fuentes": elegidas,
        "pendientes": pendientes,
        "bytes": len(serializar(elegidas)),
        "limite": "Curación léxica de pasajes completos; no acredita respaldo factual ni aprobación de la clase.",
    }
