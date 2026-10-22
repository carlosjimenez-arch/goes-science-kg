"""API de lectura con grafo fijado y derivados publicados por artículo.

`gskg servir` no regenera ni adopta artefactos históricos. Cada generador publica
su procedencia después de recalcular. Los cambios posteriores se rechazan hasta
reiniciar el servicio; propuestas no publicadas no bloquean conceptos o GraphRAG.
"""

from __future__ import annotations

import re
from pathlib import Path
from threading import Lock

from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import JSONResponse

from goes_science_kg.config import raiz
from goes_science_kg.modelos import TipoArista, TipoNodo
from goes_science_kg.publicacion_api import DIRECTORIO_PUBLICACIONES, LecturaPublicada, PublicacionNoDisponible
from goes_science_kg.rag import BM25, normalizar


def crear_app(base: Path | None = None) -> FastAPI:
    """Crea una instancia aislada; para adoptar un grafo nuevo se reinicia el proceso."""
    directorio = (base or raiz()).resolve()
    aplicacion = FastAPI(
        title="goes-science-kg", description="Grafo de Ciencias · El Salvador (solo lectura)", version="1.1"
    )

    instancia: LecturaPublicada | None = None
    inicializacion = Lock()

    def lectura() -> LecturaPublicada:
        nonlocal instancia
        with inicializacion:
            if instancia is None:
                instancia = LecturaPublicada(directorio)
            return instancia

    @aplicacion.exception_handler(PublicacionNoDisponible)
    async def publicacion_no_disponible(_peticion: Request, error: PublicacionNoDisponible):
        return JSONResponse(
            status_code=503, content={"detail": {"codigo": "publicacion_no_disponible", "motivo": str(error)}}
        )

    def grado_publicado(g: int) -> tuple[dict, list]:
        rutas = [f"data/grafo/grados/G{g:02d}/{nombre}.json" for nombre in ("diagnostico", "comunidades")]
        datos = lectura().articulo(f"grado-G{g:02d}", rutas)
        diagnostico, bloques = datos[rutas[0]], datos[rutas[1]]
        if not isinstance(diagnostico, dict) or diagnostico.get("grado") != g or not isinstance(bloques, list):
            raise PublicacionNoDisponible(f"grado-G{g:02d}: estructura incompatible")
        return diagnostico, bloques

    def resumen_grado(d: dict) -> dict:
        try:
            return {
                k: d[k]
                for k in (
                    "grado",
                    "temas",
                    "temas_por_asignatura",
                    "conceptos",
                    "conceptos_nuevos",
                    "conceptos_retomados",
                    "referentes_paises",
                )
            } | {
                "prerrequisitos_tarde": sum(a["estado"] in ("ausente", "posterior") for a in d["anclajes"]),
                "faltantes_por_edad": len(d["faltantes_por_edad"]),
            }
        except (KeyError, TypeError) as error:
            raise PublicacionNoDisponible("Diagnóstico publicado con estructura incompatible") from error

    def incompletos(salida: list, errores: list[str], respuesta: Response) -> list:
        lectura().verificar_grafo()
        if errores:
            respuesta.headers["X-Articulos-No-Disponibles"] = ",".join(errores)
            if not salida:
                raise PublicacionNoDisponible(f"No hay artículos verificables en este conjunto: {', '.join(errores)}")
        return salida

    def propuesta_publicada(asignatura: str, ciclo: str) -> dict:
        articulo = f"propuesta-{asignatura}-{ciclo}"
        relativo = f"asignaturas/{asignatura}/propuesta/simulacion_{ciclo}.json"
        s = lectura().articulo(articulo, [relativo])[relativo]
        try:
            return {"asignatura": asignatura, "ciclo": ciclo, "antes": s["antes"], "despues": s["despues"]}
        except (KeyError, TypeError) as error:
            raise PublicacionNoDisponible(f"{articulo}: estructura incompatible") from error

    @aplicacion.get("/api/salud")
    def salud() -> dict:
        """Salud del grafo; cada artículo derivado se verifica cuando se solicita."""
        return {
            "estado": "ok",
            "alcance": "grafo",
            "manifest": lectura().manifest(),
            "derivados": "requieren_publicacion_por_articulo",
        }

    @aplicacion.get("/api/grados")
    def grados(respuesta: Response) -> list[dict]:
        """Grados publicados; la cabecera informa artículos ausentes o invalidados."""
        lectura().verificar_grafo()
        salida, errores = [], []
        for g in range(2, 12):
            try:
                salida.append(resumen_grado(grado_publicado(g)[0]))
            except PublicacionNoDisponible:
                errores.append(f"grado-G{g:02d}")
        return incompletos(salida, errores, respuesta)

    @aplicacion.get("/api/grados/{grado}")
    def grado(grado: int) -> dict:
        if not 2 <= grado <= 11:
            raise HTTPException(404, "Grado fuera de 2–11")
        diagnostico, bloques = grado_publicado(grado)
        resumen_grado(diagnostico)
        return {"diagnostico": diagnostico, "bloques": bloques}

    @aplicacion.get("/api/conceptos/{asignatura}/{slug}")
    def concepto(asignatura: str, slug: str) -> dict:
        """Concepto y relaciones del mismo grafo verificado e inmutable en memoria."""
        por_id, aristas, _ = lectura().grafo()
        cid = f"CON:{asignatura}/{slug}"
        if cid not in por_id:
            raise HTTPException(404, f"No existe {cid}")
        n = por_id[cid]

        def etiqueta(i: str) -> dict:
            x = por_id[i]
            return {"id": i, "etiqueta": x.etiqueta, "grado": x.grado, "asignatura": x.asignatura}

        return {
            "id": cid,
            "nombre": n.etiqueta,
            "definicion": n.props.get("definicion"),
            "prerrequisitos": [
                etiqueta(a.origen) for a in aristas if a.tipo == TipoArista.PRERREQUISITO_DE and a.destino == cid
            ],
            "habilita": [
                etiqueta(a.destino) for a in aristas if a.tipo == TipoArista.PRERREQUISITO_DE and a.origen == cid
            ],
            "equivalentes": sorted(
                (
                    etiqueta(a.destino if a.origen == cid else a.origen)
                    for a in aristas
                    if a.tipo == TipoArista.EQUIVALE_A and cid in (a.origen, a.destino)
                ),
                key=lambda x: x["id"],
            ),
            "objetivos_marco": sorted(
                (
                    etiqueta(a.origen)
                    for a in aristas
                    if a.tipo == TipoArista.TRABAJA
                    and a.destino == cid
                    and por_id[a.origen].tipo == TipoNodo.OBJETIVO_MARCO
                ),
                key=lambda x: x["id"],
            ),
            "temas_sv": sorted(
                (
                    etiqueta(a.origen)
                    for a in aristas
                    if a.tipo == TipoArista.TRABAJA and a.destino == cid and por_id[a.origen].tipo == TipoNodo.TEMA
                ),
                key=lambda t: (t["grado"] or 0, t["id"]),
            ),
            "objetivos_paises": [
                etiqueta(a.origen)
                for a in aristas
                if a.tipo == TipoArista.TRABAJA and a.destino == cid and por_id[a.origen].tipo == TipoNodo.OBJETIVO_PAIS
            ],
        }

    @aplicacion.get("/api/propuestas")
    def propuestas(respuesta: Response) -> list[dict]:
        """Simulaciones recalculadas y publicadas; las históricas no se adoptan automáticamente."""
        lectura().verificar_grafo()
        candidatos = {
            (p.parent.parent.name, p.stem.removeprefix("simulacion_"))
            for p in (directorio / "asignaturas").glob("*/propuesta/simulacion_G*.json")
            if re.fullmatch(r"simulacion_G\d{2}-G\d{2}", p.stem) and re.fullmatch(r"[a-z_]{1,70}", p.parent.parent.name)
        }
        for p in (directorio / DIRECTORIO_PUBLICACIONES).glob("propuesta-*.json"):
            if m := re.fullmatch(r"propuesta-([a-z_]+)-(G\d{2}-G\d{2})", p.stem):
                candidatos.add((m[1], m[2]))
        for nombre in lectura().articulos_cargados():
            if m := re.fullmatch(r"propuesta-([a-z_]+)-(G\d{2}-G\d{2})", nombre):
                candidatos.add((m[1], m[2]))
        salida, errores = [], []
        for asignatura, ciclo in sorted(candidatos):
            articulo = f"propuesta-{asignatura}-{ciclo}"
            try:
                salida.append(propuesta_publicada(asignatura, ciclo))
            except PublicacionNoDisponible:
                errores.append(articulo)
        return incompletos(salida, errores, respuesta)

    @aplicacion.get("/api/propuestas/{asignatura}/{ciclo}")
    def propuesta(asignatura: str, ciclo: str) -> dict:
        """Estado y datos de una simulación independiente del resto del conjunto."""
        if not re.fullmatch(r"[a-z_]{1,70}", asignatura) or not re.fullmatch(r"G\d{2}-G\d{2}", ciclo):
            raise HTTPException(404, "Identificador de propuesta inválido")
        return propuesta_publicada(asignatura, ciclo)

    @aplicacion.get("/api/rag")
    def rag(
        q: str = Query(..., min_length=3),
        grado: int | None = Query(None, ge=2, le=11),
        asignatura: str | None = None,
        k: int = Query(20, ge=1, le=60),
    ) -> dict:
        por_id, _, recuperador = lectura().grafo()
        asignaturas = {n.asignatura for n in por_id.values() if n.asignatura}
        if asignatura and asignatura not in asignaturas:
            raise HTTPException(422, "Asignatura desconocida")
        ctx = recuperador.recuperar(q, grado=grado, asignatura=asignatura, k_final=k)
        return {
            "consulta": q,
            "grado": grado,
            "asignatura": asignatura,
            "nodos": [
                {
                    "id": n.id,
                    "tipo": n.tipo.value,
                    "etiqueta": n.etiqueta,
                    "grado": n.grado,
                    "asignatura": n.asignatura,
                    "puntaje": round(s, 4),
                    "fuente": n.fuente.model_dump(exclude_none=True) if n.fuente else None,
                }
                for n, s in ctx.nodos
            ],
            "relaciones": [
                {"origen": a.origen, "tipo": a.tipo.value, "rol": a.rol, "destino": a.destino} for a in ctx.relaciones
            ],
        }

    @aplicacion.get("/api/rag/global")
    def rag_global(q: str = Query(..., min_length=3), grado: int = Query(..., ge=2, le=11)) -> list[dict]:
        """Busca exclusivamente en las comunidades capturadas del artículo validado."""
        bloques = grado_publicado(grado)[1]
        try:
            coms = {c["id"]: c for c in bloques}
            indice = BM25(
                {
                    i: normalizar(
                        " ".join(
                            x
                            for x in (
                                c["nombre"],
                                c["resumen"],
                                c.get("titulo"),
                                c.get("resumen_ia"),
                                *(c["unidades"] or []),
                            )
                            if x
                        )
                    )
                    for i, c in coms.items()
                }
            )
            consulta = normalizar(q)
            orden = sorted(coms, key=lambda i: (-indice.puntaje(consulta, i), -len(coms[i]["conceptos"]), i))
            return [coms[i] | {"puntaje": round(indice.puntaje(consulta, i), 3)} for i in orden[:5]]
        except (KeyError, TypeError) as error:
            raise PublicacionNoDisponible("Comunidades publicadas con estructura incompatible") from error

    from goes_science_kg.api_producto import crear_router

    aplicacion.include_router(crear_router(directorio))
    return aplicacion


app = crear_app()
