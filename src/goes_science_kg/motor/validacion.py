"""Validador portátil: usa solo la entrega, nunca los Excel ni el estado local del productor."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import networkx as nx

from goes_science_kg.grafo.validar import validar as validar_grafo
from goes_science_kg.motor.archivos import decodificar, firma, id_manifiesto, leer, sha
from goes_science_kg.motor.contrato import ARCHIVOS, MODELOS, Componente, Manifiesto, esquemas
from goes_science_kg.motor.politicas import calidad, propagar_dependencias, usos


def _exigir(condicion, mensaje):
    if not condicion:
        raise ValueError(mensaje)


def _unicos(filas: list, campo="id") -> dict:
    ids = [getattr(r, campo) for r in filas]
    _exigir(len(ids) == len(set(ids)), f"{campo} repetido")
    return dict(zip(ids, filas, strict=True))


def _clasificaciones(datos: dict) -> None:
    catalogos = datos["catalogos"]
    codigos = {"TIMSS": {r["codigo"]: r["marco"] for r in catalogos["TIMSS"]},
               "ACARA": {r["codigo"]: r["marco"] for r in catalogos["ACARA"]},
               "PISA": {r["codigo"]: r["tipo"] for r in catalogos["PISA"]["elementos"]}}
    especiales = ("", "FUERA", "PENDIENTE", "N/A", None)
    temas = {t.id: t for t in datos["temas"]}
    pares = set()
    for a in datos["analisis"]:
        _exigir(a.tema_id in temas, f"análisis con tema inexistente: {a.id}")
        t = temas[a.tema_id]
        r = a.resultado
        _exigir(r.get("id") in t.aliases and r.get("marco") == a.marco, f"identidad del análisis distinta: {a.id}")
        _exigir(a.id == f"AN:{a.tipo}:{r['id']}", f"id de análisis inestable: {a.id}")
        _exigir(r.get("confianza") in ("alta", "media", "baja") and r.get("version"),
                f"análisis sin confianza o versión: {a.id}")
        _exigir((t.id, a.tipo) not in pares, f"análisis repetido por tema y tipo: {a.id}")
        pares.add((t.id, a.tipo))
        if a.tipo == "TIMSS":
            marco = "T4_27" if t.grado <= 4 else "T8_27" if t.grado <= 8 else "TA15"
            _exigir(a.marco == marco and (t.grado <= 8 or (t.grado in (10, 11) and t.asignatura_malla == "fisica")),
                    f"TIMSS no aplicable: {a.id}")
        elif a.tipo == "ACARA":
            _exigir(a.marco == "AUSS" and t.grado in (10, 11)
                    and t.asignatura_malla in ("biologia", "quimica"), f"ACARA no aplicable: {a.id}")
        else:
            _exigir(a.marco == "PISA25" and 7 <= t.grado <= 9, f"PISA no aplicable: {a.id}")
        campos = ("obj1", "obj2") if a.tipo != "PISA" else ("cont1", "cont2")
        for campo in campos:
            c = r.get(campo)
            _exigir(c in especiales or c in codigos[a.tipo], f"código de marco desconocido: {a.id}/{c}")
            if c not in especiales and a.tipo != "PISA":
                _exigir(codigos[a.tipo][c] == a.marco, f"código de otra edición de marco: {a.id}/{c}")
        if a.tipo == "PISA":
            for campo in campos:
                c = r.get(campo)
                _exigir(c in especiales or codigos["PISA"].get(c) == "contenido",
                        f"elemento PISA no es contenido: {a.id}/{c}")
            for campo, tipo in (("proc", "procedimental"), ("epis", "epistemico"),
                                ("subcompetencias_validadas", "subcompetencia")):
                for c in r.get(campo, []):
                    _exigir(codigos["PISA"].get(c) == tipo, f"elemento PISA desconocido: {a.id}/{c}")


def _semantica_componente(c: Componente, nodos: dict, componentes: dict) -> None:
    e = c.contenido
    _exigir(c.id == ("RFZ:" if c.tipo == "refuerzo" else "") + e.get("id", ""), "id de componente distinto")
    _exigir(c.tipo == "refuerzo" or e.get("tipo") == c.tipo, f"tipo de componente distinto: {c.id}")
    _exigir(c.calidad.estado_original == e.get("estado", "sin_estado")
            and c.calidad.revisado_por == (e.get("revisado_por") or None), f"revisión de origen distinta: {c.id}")
    _exigir(len(set(c.nodos_referidos)) == len(c.nodos_referidos), f"nodos repetidos en {c.id}")
    _exigir(all(i in nodos for i in c.nodos_referidos), f"componente con nodo inexistente: {c.id}")
    _exigir(all(nodos[i].tipo == "Tema" for i in e.get("objetivos", [])),
            f"objetivo de componente no es tema: {c.id}")
    _exigir(all(nodos[i].tipo in ("Tema", "Concepto") for i in e.get("evalua", [])),
            f"objetivo evaluado de tipo inválido: {c.id}")
    if e.get("concepto"):
        _exigir(nodos[e["concepto"]].tipo == "Concepto", f"concepto de tipo inválido: {c.id}")
    _exigir(len(set(c.componentes_requeridos)) == len(c.componentes_requeridos), f"dependencias repetidas: {c.id}")
    _exigir(all(i in componentes for i in c.componentes_requeridos), f"componente requerido inexistente: {c.id}")
    ns = {*e.get("objetivos", []), *e.get("evalua", [])}
    if e.get("concepto"):
        ns.add(e["concepto"])
    if c.tipo == "refuerzo" and e.get("tema_ancla"):
        ns.add("TEMA:" + e["tema_ancla"].removeprefix("TEMA:"))
    _exigir(set(c.nodos_referidos) == ns, f"nodos_referidos no corresponden al contenido: {c.id}")
    rs = {e[k] for k in ("practica", "comprobacion") if e.get(k)}
    rs.update((e.get("distractores") or {}).values())
    rs.update(r["dificultad"] for r in (e.get("rubrica") or {}).get("errores", []) if r.get("dificultad"))
    _exigir(rs == set(c.componentes_requeridos), f"dependencias no corresponden al contenido: {c.id}")
    if c.tipo == "actividad":
        _exigir(e.get("enunciado") and e.get("objetivos") and e.get("evalua"), f"actividad incompleta: {c.id}")
        _exigir(isinstance(e.get("duracion_min"), int) and e["duracion_min"] > 0, f"duración inválida: {c.id}")
        if e.get("formato") == "opcion_multiple":
            ops = e.get("opciones") or {}
            _exigir(len(ops) >= 3 and e.get("correcta") in ops, f"clave de actividad inválida: {c.id}")
        elif e.get("formato") == "numerica":
            _exigir(isinstance(e.get("valor"), int | float) and isinstance(e.get("tolerancia"), int | float)
                    and e["tolerancia"] >= 0, f"respuesta numérica inválida: {c.id}")
        elif e.get("formato") == "abierta":
            r = e.get("rubrica") or {}
            crit = r.get("criterios") or []
            _exigir(r.get("respuesta_modelo") and len(crit) >= 2 and any(x.get("obligatorio") for x in crit),
                    f"rúbrica incompleta: {c.id}")
        else:
            raise ValueError(f"formato de actividad desconocido: {c.id}")
    elif c.tipo == "experimento":
        _exigir(e.get("procedimiento") and e.get("materiales") and e.get("seguridad") and e.get("objetivos"),
                f"experimento incompleto: {c.id}")
        _exigir(isinstance(e.get("duracion_min"), int) and e["duracion_min"] > 0, f"duración inválida: {c.id}")


def cargar_entrega(directorio: str | Path) -> tuple[Manifiesto, dict]:
    """Valida primero bytes y contrato; después devuelve objetos tipados, sin depender del repo productor."""
    d = Path(directorio)
    _exigir(d.is_dir() and not d.is_symlink(), "entrega inexistente o enlace simbólico")
    _exigir({p.name for p in d.iterdir()} == ARCHIVOS | {"manifiesto.json"}, "archivos de entrega incompletos o ajenos")
    _exigir(all(p.is_file() and not p.is_symlink() for p in d.iterdir()),
            "archivos simbólicos o directorios inesperados")
    m = Manifiesto.model_validate(leer(d / "manifiesto.json"))
    _exigir(set(m.archivos) == ARCHIVOS, "manifiesto con rutas o archivos no permitidos")
    _exigir(m.id_entrega == id_manifiesto(m.model_dump(mode="json")), "identidad del manifiesto no coincide")
    _exigir(set(m.perfiles) == {"consulta", "autoria"} and len(m.perfiles) == 2, "perfiles de uso inválidos")
    datos = {}
    for n, f in m.archivos.items():
        p = d / n
        _exigir(p.stat().st_size == f.bytes and sha(p) == f.sha256, f"SHA o tamaño distintos: {n}")
        if n.endswith(".jsonl"):
            tipo = n.removesuffix(".jsonl")
            filas = [MODELOS[tipo].model_validate(decodificar(linea))
                     for linea in p.read_text(encoding="utf-8").splitlines()]
            _exigir(len(filas) == f.registros, f"conteo distinto: {n}")
            _unicos(filas, "id_analisis" if tipo == "puente" else "id")
            datos[tipo] = filas
        elif n.endswith(".json"):
            datos[n.removesuffix(".json")] = leer(p)
    _exigir(datos["esquemas"] == esquemas(), "esquemas distintos del contrato ejecutable")
    return m, datos


def validar(directorio: str | Path) -> dict:
    m, datos = cargar_entrega(directorio)
    nodos = _unicos(datos["nodos"])
    temas = _unicos(datos["temas"])
    puentes = _unicos(datos["puente"], "tema_id")
    _exigir(set(temas) == {n.id for n in nodos.values() if n.tipo == "Tema"} == set(puentes),
            "temas, puente y nodos no corresponden uno a uno")
    aliases = set()
    _exigir({t.orden for t in temas.values()} == set(range(1, len(temas) + 1)), "orden de temas no es único y completo")
    for t in temas.values():
        p = puentes[t.id]
        n = nodos[t.id]
        _exigir(t.id.startswith("TEMA:") and t.aliases == [p.id_analisis] and not aliases.intersection(t.aliases),
                f"identidad ambigua: {t.id}")
        aliases.update(t.aliases)
        _exigir(t.fuente == p.fuente and p.sha256_columnas == firma(t.columnas), f"columnas o fuente distintas: {t.id}")
        _exigir(n.etiqueta == t.columnas.get("Procedimental") and n.grado == t.grado and n.fuente
                and n.fuente.documento == "MALLA:" + t.fuente.archivo
                and n.fuente.hoja == t.fuente.hoja and n.fuente.fila == t.fuente.fila,
                f"el nodo no representa la fila oficial: {t.id}")
        _exigir(t.en_alcance_ciencias == (n.asignatura is not None) and t.asignatura == n.asignatura,
                f"alcance de ciencias incoherente: {t.id}")
        documento = nodos.get("DOC:" + n.fuente.documento)
        _exigir(documento is not None and documento.tipo == "Documento"
                and documento.props.get("sha256") == t.fuente.sha256
                and m.insumos.get(documento.props.get("archivo_local")) == t.fuente.sha256,
                f"fuente de tema sin respaldo en documento e insumos: {t.id}")
    for r in datos["relaciones"]:
        _exigir(r.id == "REL:" + firma(r.clave), "identidad de relación distinta")
    gr = validar_grafo(list(nodos.values()), datos["relaciones"])
    _exigir(not gr.errores, "grafo inválido: " + "; ".join(gr.errores[:5]))
    try:
        _clasificaciones(datos)
    except (KeyError, TypeError, AttributeError) as e:
        raise ValueError("catálogos o resultados de análisis mal formados") from e
    comps = _unicos(datos["componentes"])
    esperados = {}
    for c in comps.values():
        _semantica_componente(c, nodos, comps)
        q = calidad(c.contenido, {"estado": c.calidad.estado_panel, "bucle": {"solidez": c.calidad.solidez}})
        _exigir(q == c.calidad, f"calidad incoherente: {c.id}")
        copia = c.model_copy(deep=True)
        copia.usos = usos(c.tipo, c.contenido, c.calidad)
        esperados[c.id] = copia
    dep = nx.DiGraph([(c.id, i) for c in comps.values() for i in c.componentes_requeridos])
    _exigir(nx.is_directed_acyclic_graph(dep), "dependencias de componentes con ciclos")
    propagar_dependencias(esperados)
    _exigir(all(c.usos == esperados[i].usos for i, c in comps.items()), "permisos no corresponden a la revisión")
    por_tema = set()
    for p in datos["paquetes"]:
        _exigir(p.tema_id in temas and p.tema_id not in por_tema, "paquete duplicado o con tema inexistente")
        por_tema.add(p.tema_id)
        _exigir(p.id == "PAQ:" + p.tema_id.removeprefix("TEMA:"), "identidad de paquete distinta")
        _exigir(all(i in comps for ids in p.componentes.values() for i in ids), "paquete con componente inexistente")
        tipos = {"actividades": "actividad", "experimentos": "experimento", "ideas_previas": "dificultad",
                 "microtemas": "microtema", "refuerzos": "refuerzo"}
        _exigir(set(p.componentes) == set(tipos), "grupos de componentes del paquete inválidos")
        for grupo, ids in p.componentes.items():
            _exigir(len(set(ids)) == len(ids) and all(comps[i].tipo == tipos[grupo] for i in ids),
                    "tipo o identidad de componente inválido en paquete")
        if p.reemplazo_elegido:
            _exigir(p.reemplazo_elegido.get("tema_usado") == p.tema_id.removeprefix("TEMA:")
                    and "TEMA:" + p.reemplazo_elegido.get("pedido", "") not in temas,
                    "reemplazo elegido incoherente con la malla")
        _exigir(all(i in nodos and nodos[i].tipo == "Concepto" for i in p.conceptos),
                "concepto de paquete inexistente o de tipo inválido")
        for b in p.bases:
            _exigir(b.get("concepto") in nodos and nodos[b["concepto"]].tipo == "Concepto"
                    and (not b.get("primer_tema") or (b["primer_tema"] in nodos
                                                     and nodos[b["primer_tema"]].tipo == "Tema")),
                    "base de paquete con referencia inexistente")
    for r in datos["referencias"]:
        _exigir(r.documento in nodos and nodos[r.documento].tipo == "Documento"
                and all(c in nodos and nodos[c].tipo == "Concepto" for c in r.conceptos),
                "referencia sin documento o concepto")
        _exigir(nodos[r.documento].props.get("sha256") == r.sha256, "SHA de referencia sin respaldo en documento")
    metricas = {k: len(datos[k]) for k in MODELOS}
    metricas.update(temas_en_alcance=sum(t.en_alcance_ciencias for t in temas.values()),
                    componentes_autoria=sum(c.usos.autoria for c in comps.values()), componentes_aula=0,
                    temas_con_diferencias_extraccion=sum(bool(t.diferencias_extraccion) for t in temas.values()),
                    relaciones_confianza_baja=sum(r.confianza == "baja" for r in datos["relaciones"]))
    _exigir(metricas == m.metricas, "métricas del manifiesto distintas de los datos")
    return {"resultado": "valido", "id_entrega": m.id_entrega, "version": m.version_contenido,
            "metricas": metricas, "avisos_grafo": gr.avisos,
            "componentes_por_tipo": dict(Counter(c.tipo for c in comps.values()))}
