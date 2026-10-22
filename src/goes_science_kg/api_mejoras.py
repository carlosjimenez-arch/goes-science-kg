"""Consulta de propuestas y progresiones de una publicación fijada; sin generación remota."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Response


def crear_router_mejoras(leer) -> APIRouter:
    router = APIRouter()

    def archivo():
        runtime = leer()
        if runtime.producto.mejoras is None:
            raise HTTPException(409, "La publicación seleccionada todavía no contiene propuestas curriculares")
        return runtime, runtime.producto.mejoras

    @router.get("/propuestas")
    def propuestas(
        grado: Annotated[int | None, Query(ge=2, le=11)] = None,
        estado: Annotated[str | None, Query(max_length=40)] = None,
    ):
        runtime, mejoras = archivo()
        casos = [
            c
            for c in mejoras.unidades
            if (grado is None or c.preparacion.solicitud.grado == grado)
            and (estado is None or c.resultado.estado == estado)
        ]
        return {
            "snapshot_id": runtime.producto.manifest.snapshot_id,
            "archivo_id": mejoras.id,
            "cobertura": mejoras.cobertura,
            "limite": mejoras.limite,
            "unidades": [
                {
                    "id": c.preparacion.id,
                    **c.preparacion.solicitud.model_dump(mode="json"),
                    "filas": len(c.preparacion.filas_originales),
                    "estado": c.resultado.estado,
                    "motivos": c.resultado.motivos,
                }
                for c in casos
            ],
        }

    @router.get("/propuestas/{preparacion_id}")
    def propuesta(preparacion_id: str):
        runtime, mejoras = archivo()
        caso = next((c for c in mejoras.unidades if c.preparacion.id == preparacion_id), None)
        if caso is None:
            raise HTTPException(404, "La unidad no pertenece a las propuestas de esta publicación")
        return {
            "snapshot_id": runtime.producto.manifest.snapshot_id,
            "archivo_id": mejoras.id,
            "limite": mejoras.limite,
            **caso.model_dump(mode="json"),
        }

    @router.get("/progresiones")
    def progresiones():
        runtime, mejoras = archivo()
        return {"snapshot_id": runtime.producto.manifest.snapshot_id, **mejoras.progresiones}

    @router.get("/exportaciones/mejoras.csv")
    def csv_mejoras():
        runtime, mejoras = archivo()
        from goes_science_kg.producto.exportacion_mejoras import csv_curricular

        return Response(
            content=csv_curricular(runtime.producto.curriculo, mejoras),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="ciencias-v4-propuestas.csv"'},
        )

    return router
