"""Compila una entrega inmutable sin recalcular ni sustituir decisiones curriculares."""

from __future__ import annotations

import os
import subprocess
import tempfile
from collections import Counter
from pathlib import Path

from goes_science_kg import panel
from goes_science_kg.aprendizaje.pedagogia import Pedagogia
from goes_science_kg.config import cargar, relativa, ruta
from goes_science_kg.grafo.almacen import cargar as cargar_grafo
from goes_science_kg.ingesta.mallas import vigente_de
from goes_science_kg.motor.archivos import canonico, destino_seguro, escribir, firma, id_manifiesto, leer, sha
from goes_science_kg.motor.contrato import (
    Analisis,
    Componente,
    FichaArchivo,
    Identidad,
    Manifiesto,
    Paquete,
    Relacion,
    Tema,
    Ubicacion,
    clase_manifiesto,
    esquemas,
)
from goes_science_kg.motor.identidades import columnas_vigentes, comprobar_identidades
from goes_science_kg.motor.politicas import calidad, propagar_dependencias, usos


def _referidos(tipo: str, e: dict) -> tuple[list[str], list[str]]:
    nodos = [*e.get("objetivos", []), *e.get("evalua", [])]
    if e.get("concepto"):
        nodos.append(e["concepto"])
    if tipo == "refuerzo" and e.get("tema_ancla"):
        nodos.append("TEMA:" + e["tema_ancla"].removeprefix("TEMA:"))
    requeridos = [e[k] for k in ("practica", "comprobacion") if e.get(k)]
    requeridos += list((e.get("distractores") or {}).values())
    requeridos += [r["dificultad"] for r in (e.get("rubrica") or {}).get("errores", []) if r.get("dificultad")]
    return sorted(set(nodos)), sorted(set(requeridos))


def componentes_de(paquetes: list[dict], estado: dict) -> dict[str, Componente]:
    ped = Pedagogia.cargar()
    por_tipo = {"actividad": ped.actividades, "experimento": ped.experimentos, "dificultad": ped.dificultades,
                "microtema": ped.microtemas}
    origen = {i: (t, e) for t, es in por_tipo.items() for i, e in es.items()}
    for e in leer(ruta("data/interim/refuerzo_v3/refuerzos.json")):
        origen["RFZ:" + e["id"]] = ("refuerzo", e)
    ids = set()
    for p in paquetes:
        for campo in ("actividades", "experimentos", "ideas_previas", "microtemas"):
            ids.update(e["id"] for e in p[campo])
        ids.update("RFZ:" + e["id"] for e in p["refuerzo_de_la_malla"])
    resultado = {}
    while ids:
        i = min(ids)
        ids.remove(i)
        if i in resultado:
            continue
        if i not in origen:
            raise ValueError(f"componente del paquete sin registro activo: {i}")
        tipo, original = origen[i]
        e = dict(original)
        for campo in ("objetivos", "evalua"):
            if campo in e:
                traducidos = [(vigente_de(n) or n) if n.startswith("TEMA:") else n for n in e[campo]]
                if traducidos != e[campo]:
                    e[campo + "_antes_de_exportar"] = e[campo]
                    e[campo] = traducidos
        x = estado.get(i if tipo == "refuerzo" else "PED:" + i)
        q = calidad(e, x)
        ns, rs = _referidos(tipo, e)
        resultado[i] = Componente(id=i, tipo=tipo, contenido=e, nodos_referidos=ns, componentes_requeridos=rs,
                                  calidad=q, usos=usos(tipo, e, q))
        ids.update(set(rs) - resultado.keys())
    propagar_dependencias(resultado)
    return resultado


def compilar() -> tuple[dict[str, object], dict[str, str], dict[str, int], list[str]]:
    cfg = cargar("motor")
    base = ruta(cfg["analisis"])
    nombres = ("identidades.json", "fuentes_mallas.json", "fuentes_marcos.json", "procedencia.json",
               "clasificaciones_consolidadas.json", "catalogo_timss.json", "catalogo_pisa.json", "catalogo_acara.json")
    insumos = {relativa(base / n): sha(base / n) for n in nombres}
    datos = {n: leer(base / n) for n in nombres}
    columnas = columnas_vigentes()
    puente = comprobar_identidades(datos["identidades.json"], datos["fuentes_mallas.json"], columnas)
    nodos, aristas = cargar_grafo()
    por_id = {n.id: n for n in nodos}
    if {"TEMA:" + t.id for t in puente.values()} != {n.id for n in nodos if n.tipo == "Tema"}:
        raise ValueError("el grafo no corresponde a los temas de la malla vigente")
    gm = leer(ruta("data/grafo/manifest.json"))
    for n, h in gm["sha256"].items():
        if sha(ruta("data/grafo") / n) != h:
            raise ValueError("SHA del grafo distinto de su manifiesto")
    cfg_malla = cargar("mallas")
    fuentes = {f["archivo"]: f["sha256"] for f in datos["fuentes_mallas.json"]}
    identidades, temas = [], []
    diferencias = Counter()
    # Respeta el orden real de libros, hojas y filas; ordenar títulos situaría Unidad 10 antes de Unidad 2.
    posiciones = {lugar: orden for orden, lugar in enumerate(columnas)}
    ordenados = sorted(puente.items(), key=lambda a: posiciones[(a[1].ruta, a[1].hoja, a[1].fila)])
    for orden, (alias, t) in enumerate(ordenados, 1):
        col, fin = columnas[(t.ruta, t.hoja, t.fila)]
        ubicacion = Ubicacion(archivo=t.ruta, hoja=t.hoja, fila=t.fila, fila_fin=fin, sha256=fuentes[t.ruta])
        tid = "TEMA:" + t.id
        ds = [k for k, v in {"unidad": col.get("Unidad", ""), "contenido": col.get("Contenido", ""),
                              "subcontenido": col.get("Subcontenidos", ""),
                              "indicador": col.get("Indicadores de logro") or col.get("Indicador avanzado", ""),
                              "evidencia": col.get("Evidencia de aprendizaje", ""),
                              "habilidad_timss": col.get("Habilidad TIMSS", "")}.items() if v != getattr(t, k)]
        diferencias.update(ds)
        temas.append(Tema(id=tid, aliases=[alias], grado=t.grado, asignatura=por_id[tid].asignatura,
                          asignatura_malla=t.asignatura, en_alcance_ciencias=por_id[tid].asignatura is not None,
                          orden=orden, fuente=ubicacion, columnas=col, extraccion_grafo=t.dict(),
                          diferencias_extraccion=ds))
        identidades.append(Identidad(id_analisis=alias, tema_id=tid, fuente=ubicacion, sha256_columnas=firma(col)))
    analisis = [Analisis(id=f"AN:{tipo}:{r['id']}", tema_id="TEMA:" + puente[r["id"]].id,
                        tipo=tipo, marco=r["marco"], resultado=r)
                for tipo, rs in datos["clasificaciones_consolidadas.json"].items() for r in rs]
    archivos_p = sorted(ruta(cfg["paquetes"]).glob("G*.json"))
    paquetes_origen = [leer(p) for p in archivos_p]
    estado = panel.cargar_estado()
    componentes = componentes_de(paquetes_origen, estado)
    paquetes = []
    for p in paquetes_origen:
        t = p["tema"]
        tid = "TEMA:" + t["id"]
        lugar = (t["archivo"], t["hoja"], t["fila"])
        if tid not in por_id or columnas[lugar][0]["Procedimental"] != t["procedimental"]:
            raise ValueError(f"paquete ajeno a la malla vigente: {tid}")
        grupos = {k: [e["id"] for e in p[k]] for k in ("actividades", "experimentos", "ideas_previas", "microtemas")}
        grupos["refuerzos"] = ["RFZ:" + e["id"] for e in p["refuerzo_de_la_malla"]]
        paquetes.append(Paquete(id="PAQ:" + t["id"], tema_id=tid, componentes=grupos,
                                conceptos=[c["id"] for c in p["conceptos"]], bases=p["bases"], fuentes=p["fuentes"],
                                datos_referencia=p["datos_de_referencia"], completitud_origen=p["completitud"],
                                reemplazo_elegido=p.get("reemplazo")))
    referencias = []
    rp = ruta("data/interim/datos_referencia.json")
    if rp.exists():
        # El contrato nuevo exige datos con unidades, condiciones y fuente verificable; no se inventan conversiones.
        from goes_science_kg.motor.contrato import Referencia

        referencias = [Referencia.model_validate(r) for r in leer(rp)]
        insumos[relativa(rp)] = sha(rp)
    for p in [ruta("config/motor.yaml"), ruta("config/mallas.yaml"), ruta(cfg_malla["correspondencia"]),
              ruta("data/grafo/manifest.json"), ruta("data/grafo/nodos.jsonl"), ruta("data/grafo/aristas.jsonl"),
              ruta("data/interim/panel/estado.json"), ruta("data/interim/refuerzo_v3/refuerzos.json"),
              *[ruta("data/pedagogia") / n for n in ("actividades.json", "experimentos.json", "dificultades.json",
                                                     "microtemas.json")],
              ruta("config/aprendizaje.yaml"), ruta("config/panel.yaml"), ruta("pyproject.toml"), ruta("uv.lock"),
              *archivos_p, *sorted(ruta("src/goes_science_kg").rglob("*.py")),
              *[ruta(cfg_malla["directorio"]) / n for n in fuentes]]:
        insumos[relativa(p)] = sha(p)
    rels = [Relacion(**a.model_dump(), id="REL:" + firma(a.clave)) for a in aristas]
    colecciones = {"temas": temas, "puente": identidades, "nodos": nodos, "relaciones": rels,
                   "analisis": analisis, "componentes": list(componentes.values()), "paquetes": paquetes,
                   "referencias": referencias}
    colecciones = {k: sorted(v, key=lambda r: getattr(r, "id", None) or r.id_analisis) for k, v in colecciones.items()}
    metricas = {k: len(v) for k, v in colecciones.items()}
    metricas.update(temas_en_alcance=sum(t.en_alcance_ciencias for t in temas),
                    componentes_autoria=sum(c.usos.autoria for c in componentes.values()), componentes_aula=0,
                    temas_con_diferencias_extraccion=sum(bool(t.diferencias_extraccion) for t in temas),
                    relaciones_confianza_baja=sum(a.confianza == "baja" for a in aristas))
    avisos = ["La entrega habilita consulta y autoría asistida; el uso en aula no está habilitado.",
              "Las clasificaciones del análisis y las del grafo conservan procedencia y catálogos separados.",
              "Los datos no marcados por el detector siguen no evaluados, no certificados como innecesarios.",
              "Las propuestas GOES se consultan como propuestas; no son adopciones del MINED."]
    if diferencias:
        avisos.append("Diferencias entre extracción completa y grafo: " + canonico(dict(diferencias)))
    colecciones["catalogos"] = {"TIMSS": datos["catalogo_timss.json"], "PISA": datos["catalogo_pisa.json"],
                                "ACARA": datos["catalogo_acara.json"], "fuentes_marcos": datos["fuentes_marcos.json"]}
    return colecciones, insumos, metricas, avisos


def exportar(destino: str | Path | None = None, version: str | None = None,
             commit_base: str | None = None, incluir_secuencias: bool = False) -> Path:
    """Crea una entrega candidata, la valida y solo entonces la publica. Nunca reemplaza otra versión."""
    cfg = cargar("motor")
    if cfg["contrato"] != Manifiesto.model_fields["version_contrato"].default:
        raise ValueError("versión del contrato de configuración no implementada")
    version = version or cfg["contenido"]
    salida = destino_seguro(ruta(destino or Path(cfg["salida"]) / version))
    colecciones, insumos, metricas, avisos = compilar()
    contrato = '1.1.0' if incluir_secuencias else '1.0.0'
    if incluir_secuencias:
        from goes_science_kg.secuencias_ia import compilar as compilar_secuencias
        from goes_science_kg.secuencias_ia import configuracion as reglas_secuencias

        ss, origen = compilar_secuencias(colecciones['temas'])
        colecciones['secuencias'] = ss
        reglas = reglas_secuencias()
        colecciones['catalogos']['secuencias_ia'] = reglas
        ejecucion = ruta(reglas['directorio']) / 'EJECUCION.json'
        colecciones['catalogos']['secuencias_ia_ejecucion'] = leer(ejecucion)
        insumos[relativa(ejecucion)] = sha(ejecucion)
        insumos.update(origen)
        # commit_base identifica el punto de partida; las huellas también identifican el código local exportador.
        for n in ('secuencias_ia.py', 'motor/construccion.py', 'motor/contrato.py',
                  'motor/validacion.py', 'motor/consumidor.py'):
            p = ruta('src/goes_science_kg') / n
            insumos[relativa(p)] = sha(p)
        metricas['secuencias'] = len(ss)
        metricas['secuencias_autoria_ia'] = sum(s.autoria_asistida for s in ss)
        avisos.append('Secuencias revisadas por agentes IA; no son validación humana ni tiempo observado.')
    salida.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".motor-", dir=salida.parent) as temporal:
        d = Path(temporal)
        fichas = {}
        for nombre, rs in colecciones.items():
            if nombre == "catalogos":
                escribir(d / "catalogos.json", rs)
                continue
            p = d / f"{nombre}.jsonl"
            p.write_text("".join(canonico(r.model_dump(mode="json")) + "\n" for r in rs), encoding="utf-8")
            fichas[p.name] = FichaArchivo(sha256=sha(p), bytes=p.stat().st_size, registros=len(rs))
        escribir(d / "esquemas.json", esquemas(contrato))
        (d / "LEEME.md").write_text(
            "# GOES Science Content " + version + "\n\n"
            "Entrega V3 para consulta y autoría asistida. El uso en aula no está habilitado.\n\n"
            "Los permisos se verifican por componente. Las propuestas GOES conservan su estado; "
            "el perfil de autoría las excluye salvo selección explícita. Las celdas combinadas de la fuente "
            "se conservan completas. El orden de enseñanza es un atributo, no se deduce del id.\n\n"
            "Validar: `gskg motor validar <carpeta>`. Importar: `gskg motor importar <carpeta>`.\n\n"
            "Las huellas detectan alteraciones; no son una firma digital de identidad institucional. "
            "Contrato: `specs/16_contenido_motor.md`.\n" + (
                "\nEsta versión agrega secuencias propuestas para todos los temas de Ciencias. "
                "Incluye revisión científica, psicopedagogía, refutación, cierre y nueva refutación de sus cambios. "
                "Las secuencias retenidas se consultan, pero se omiten del perfil de autoría. "
                "La distribución de 55 minutos es orientativa; no hay tiempo observado ni firma humana. "
                "Los roles de las ejecuciones IA se documentan en catalogos.json, sin presumir diversidad de modelos. "
                "Contrato ampliado: `specs/17_panel_secuencias_ia.md`.\n"
                if incluir_secuencias else ""), encoding="utf-8")
        for n in ("catalogos.json", "esquemas.json", "LEEME.md"):
            p = d / n
            fichas[n] = FichaArchivo(sha256=sha(p), bytes=p.stat().st_size)
        commit = commit_base or subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ruta("."), text=True).strip()
        m = clase_manifiesto(contrato)(version_contenido=version, fecha_corte=cfg["fecha_corte"],
                       perfiles=cfg["perfiles"],
                       commit_base=commit, insumos=insumos, archivos=fichas, metricas=metricas,
                       advertencias=avisos, id_entrega="0" * 64).model_dump(mode="json")
        m["id_entrega"] = id_manifiesto(m)
        escribir(d / "manifiesto.json", m)
        from goes_science_kg.motor.validacion import validar

        validar(d)
        if salida.exists():
            if (salida / "manifiesto.json").read_bytes() != (d / "manifiesto.json").read_bytes():
                raise ValueError("el destino ya contiene otra entrega; usar una nueva versión o destino")
            validar(salida)
        else:
            os.rename(d, salida)
    return salida
