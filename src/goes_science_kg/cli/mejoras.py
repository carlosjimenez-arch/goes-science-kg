"""Prepare and execute finite V4 curriculum improvement campaigns."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from goes_science_kg.config import cargar, ruta
from goes_science_kg.motor.contratos import huella
from goes_science_kg.motor.registro import Registro
from goes_science_kg.motor.vertex import ConfiguracionVertex, Vertex
from goes_science_kg.producto.campana_mejoras import crear_plan, ejecutar_campana, escribir_nuevo_o_igual

app = typer.Typer(help="Propuestas curriculares V4 completas, cuatro revisiones y exportación", no_args_is_help=True)


@app.command("preparar")
def preparar(destino: Annotated[Path, typer.Option()]) -> None:
    """Rehydrate all units and sources while preserving the complete curriculum denominator."""
    from goes_science_kg.motor.mejoras import MotorMejoras
    from goes_science_kg.producto.mejoras_contratos import SolicitudMejora
    from goes_science_kg.producto.preparacion_mejoras import PreparadorMejoras, datos_mejora
    from goes_science_kg.producto.runtime import cargar_runtime

    try:
        cfg = cargar("mejoras_curriculares")
        vertex = ConfiguracionVertex.model_validate(cfg["vertex"])
        runtime = cargar_runtime()
        preparador = PreparadorMejoras(runtime, raiz=ruta("."))
        proveedor = Vertex(vertex, Registro(ruta("data/operaciones/registro.sqlite")), cfg["ejecucion_id"])
        motor = MotorMejoras(preparador, proveedor)
        unidades = []
        for g, a, u in sorted({(f.grado, f.asignatura_malla, f.unidad) for f in runtime.producto.curriculo.filas}):
            solicitud = SolicitudMejora(grado=g, asignatura_malla=a, unidad=u)
            p = preparador.preparar(solicitud)
            archivo = huella(solicitud) + ".json"
            escribir_nuevo_o_igual(destino / archivo, p.model_dump(mode="json"))
            unidades.append(
                {
                    "archivo": archivo,
                    "id": p.id,
                    "solicitud": solicitud.model_dump(mode="json"),
                    "filas": len(p.filas_originales),
                    "caracteres": len(json.dumps(datos_mejora(p), ensure_ascii=False)),
                }
            )
        resumen = {
            "unidades": unidades,
            "llamadas": 0,
            "filas": sum(u["filas"] for u in unidades),
            "huella_curriculo": runtime.producto.curriculo.huella,
            "huella_catalogo": huella(runtime.producto.catalogo),
        }
        escribir_nuevo_o_igual(destino / "preparaciones.json", resumen)
        plan = crear_plan(destino, vertex, cfg["ejecucion_id"], motor)
        escribir_nuevo_o_igual(destino / "plan.json", plan)
    except (OSError, ValueError) as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(
        json.dumps(
            {"plan_id": plan["id"], "unidades": len(unidades), "filas": resumen["filas"], **plan["preflight"]},
            ensure_ascii=False,
            indent=2,
        )
    )


@app.command("ejecutar")
def ejecutar(
    directorio: Path,
    ejecutar: bool = typer.Option(False, "--ejecutar"),
    unidad_id: Annotated[list[str] | None, typer.Option(help="ID de preparación; opción repetible")] = None,
    trabajadores: Annotated[int, typer.Option(min=1, max=8)] = 1,
) -> None:
    """Show the plan or execute with one cumulative campaign counter and unit checkpoints."""
    from goes_science_kg.internacional.vertex import verificar_cuenta
    from goes_science_kg.observabilidad import configurar_logging
    from goes_science_kg.producto.runtime import cargar_runtime

    try:
        plan = json.loads((directorio / "plan.json").read_bytes())
        if plan["id"] != huella({k: v for k, v in plan.items() if k != "id"}):
            raise ValueError("El plan no conserva su identidad")
        ids = set(unidad_id or ())
        if ids - {u["id"] for u in plan["unidades"]}:
            raise ValueError("Se solicitaron unidades ajenas a la campaña")
        if not ejecutar:
            typer.echo(
                json.dumps(
                    {
                        "estado": "plan",
                        "id": plan["id"],
                        "llamadas_nuevas": 0,
                        "seleccion": list(ids),
                        "preflight": plan["preflight"],
                        "configuracion": plan["configuracion"],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return
        verificar_cuenta()
        configurar_logging(archivo=ruta("data/operaciones/mejoras.log"))
        resultado = ejecutar_campana(
            plan,
            directorio=directorio,
            raiz=ruta("."),
            runtime=cargar_runtime(),
            seleccion=tuple(ids),
            trabajadores=trabajadores,
        )
    except (OSError, ValueError) as error:
        raise typer.BadParameter(str(error)) from error
    from collections import Counter

    typer.echo(
        json.dumps(
            {
                "plan_id": plan["id"],
                "estados": dict(Counter(r["estado"] for r in resultado["resultados"])),
                "consumo": resultado["consumo"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


@app.command("consolidar")
def consolidar(
    directorio: Path,
    pruebas: Annotated[Path, typer.Option()],
    salida: Annotated[Path, typer.Option()],
    historial: Annotated[list[Path] | None, typer.Option()] = None,
    seguimiento: Annotated[Path | None, typer.Option()] = None,
    rectificacion: Annotated[Path | None, typer.Option()] = None,
) -> None:
    """Require complete unit coverage while retaining failed runs and adversarial controls."""
    from goes_science_kg.producto.publicacion_mejoras import consolidar_campana, guardar_archivo
    from goes_science_kg.producto.runtime import cargar_runtime

    try:
        archivo = consolidar_campana(
            directorio,
            raiz=ruta("."),
            runtime=cargar_runtime(),
            pruebas=pruebas,
            historiales=tuple(historial or ()),
            seguimiento=seguimiento,
            rectificacion=rectificacion,
        )
        guardar_archivo(archivo, salida)
    except (ValueError, OSError) as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(
        json.dumps({"id": archivo.id, "cobertura": archivo.cobertura, "llamadas": 0}, ensure_ascii=False, indent=2)
    )


@app.command("seguimiento")
def seguimiento(
    directorio: Path,
    destino: Annotated[Path, typer.Option()],
    ejecutar: bool = typer.Option(False, "--ejecutar"),
) -> None:
    """Prepare finite incident follow-up and invoke models only under explicit execution."""
    from collections import Counter

    from goes_science_kg.internacional.vertex import verificar_cuenta
    from goes_science_kg.observabilidad import configurar_logging
    from goes_science_kg.producto.runtime import cargar_runtime
    from goes_science_kg.producto.seguimiento_mejoras import crear_seguimiento, ejecutar_seguimiento

    try:
        runtime = cargar_runtime()
        if ejecutar:
            plan = json.loads((destino / "plan.json").read_bytes())
            verificar_cuenta()
            configurar_logging(archivo=ruta("data/operaciones/seguimiento_mejoras.log"))
            casos = ejecutar_seguimiento(plan, raiz=ruta("."), runtime=runtime, destino=destino)
            salida = {"plan_id": plan["id"], "estados": dict(Counter(c.resultado.estado for c in casos))}
        else:
            plan = crear_seguimiento(directorio, raiz=ruta("."), runtime=runtime, destino=destino)
            salida = {
                "plan_id": plan["id"],
                "unidades": len(plan["tareas"]),
                "llamadas": 0,
                "modos": dict(Counter(t["modo"] for t in plan["tareas"])),
                "reserva_maxima_usd": sum(t["preflight"]["max_reserva_usd"] for t in plan["tareas"]),
            }
    except (ValueError, OSError) as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(json.dumps(salida, ensure_ascii=False, indent=2))


@app.command("publicar")
def publicar(archivo: Path, destino: Annotated[Path, typer.Option()] = Path("data/producto/V4")) -> None:
    """Verify sources and atomically select the complete product-4 generation."""
    from goes_science_kg.producto.mejoras_publicadas import ArchivoMejoras
    from goes_science_kg.producto.publicacion_mejoras import publicar_mejoras
    from goes_science_kg.producto.runtime import cargar_runtime

    try:
        datos = ArchivoMejoras.model_validate_json(archivo.read_bytes())
        resultado = publicar_mejoras(datos, runtime=cargar_runtime(), raiz=ruta("."), destino=destino)
    except (ValueError, OSError) as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(json.dumps(resultado, ensure_ascii=False, indent=2))


@app.command("rectificar")
def rectificar(
    caso: Path,
    destino: Annotated[Path, typer.Option()],
    ejecutar: bool = typer.Option(False, "--ejecutar"),
) -> None:
    """Record a corrected scientific false positive while preserving its original dossier."""
    from goes_science_kg.internacional.vertex import verificar_cuenta
    from goes_science_kg.observabilidad import configurar_logging
    from goes_science_kg.producto.mejoras_publicadas import CasoMejora
    from goes_science_kg.producto.rectificacion_mejoras import ejecutar_rectificacion, preparar_rectificacion
    from goes_science_kg.producto.runtime import cargar_runtime

    try:
        runtime = cargar_runtime()
        if ejecutar:
            plan = json.loads((destino / "plan.json").read_bytes())
            verificar_cuenta()
            configurar_logging(archivo=ruta("data/operaciones/rectificacion_mejoras.log"))
            resultado = ejecutar_rectificacion(plan, raiz=ruta("."), runtime=runtime, destino=destino)
            salida = {"plan_id": plan["id"], "estado": resultado.resultado.estado}
        else:
            cfg = cargar("mejoras_curriculares")
            plan = preparar_rectificacion(
                CasoMejora.model_validate_json(caso.read_bytes()),
                configuracion=cfg["vertex"],
                ejecucion_id=cfg["ejecucion_id"],
                raiz=ruta("."),
                runtime=runtime,
                destino=destino,
            )
            salida = {"plan_id": plan["id"], "llamadas": 0, "preflight": plan["preflight"]}
    except (ValueError, OSError) as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(json.dumps(salida, ensure_ascii=False, indent=2))


@app.command("exportar")
def exportar(destino: Annotated[Path, typer.Option()]) -> None:
    """Export Excel, CSV, and offline views without invoking models."""
    from goes_science_kg.producto.exportacion_mejoras import exportar_entrega
    from goes_science_kg.producto.runtime import cargar_runtime

    try:
        runtime = cargar_runtime()
        if runtime.producto.mejoras is None:
            raise ValueError("La publicación actual no contiene propuestas curriculares")
        salida = exportar_entrega(
            runtime.producto.curriculo, runtime.producto.mejoras, destino, raiz_v4=ruta("insumos/v4")
        )
    except (ValueError, OSError) as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(json.dumps(salida, ensure_ascii=False, indent=2))


@app.command("ensayar")
def ensayar(
    directorio: Path,
    preparacion_id: Annotated[str, typer.Option()],
    destino: Annotated[Path, typer.Option()],
    caso_base: Annotated[
        Path | None, typer.Option(help="Piloto respaldado del mismo contexto, preservado como base")
    ] = None,
    ejecutar: bool = typer.Option(False, "--ejecutar"),
) -> None:
    """Test five declared defects without exposing expected labels to the provider."""
    from goes_science_kg.internacional.vertex import verificar_cuenta
    from goes_science_kg.observabilidad import configurar_logging
    from goes_science_kg.producto.mejoras_publicadas import CasoMejora
    from goes_science_kg.producto.preparacion_mejoras import PreparadorMejoras
    from goes_science_kg.producto.pruebas_mejoras import ejecutar_controles, preparar_controles
    from goes_science_kg.producto.runtime import cargar_runtime

    try:
        plan = json.loads((directorio / "plan.json").read_bytes())
        if plan["id"] != huella({k: v for k, v in plan.items() if k != "id"}):
            raise ValueError("El plan no conserva su identidad")
        u = next((u for u in plan["unidades"] if u["id"] == preparacion_id), None)
        if u is None:
            raise ValueError("La preparación no pertenece a la campaña")
        origen = caso_base or directorio / "resultados" / f"{preparacion_id}.json"
        caso = CasoMejora.model_validate_json(origen.read_bytes())
        if caso.preparacion.id != preparacion_id:
            raise ValueError("La base de los controles pertenece a otro contexto")
        from goes_science_kg.producto.mejoras_contratos import ROLES_MEJORA
        from goes_science_kg.producto.validacion_mejoras import resolver_mejora

        if (
            resolver_mejora(
                caso.preparacion,
                caso.resultado.rondas,
                ejecucion_id=caso.resultado.ejecucion_id,
                modelos={r: plan["configuracion"]["modelos"][r] for r in ROLES_MEJORA},
            )
            != caso.resultado
        ):
            raise ValueError("La base no conserva sus cuatro votos originales")
        controles = preparar_controles(caso)
        if not ejecutar:
            typer.echo(
                json.dumps(
                    {
                        "estado": "plan",
                        "llamadas_nuevas": 0,
                        "controles": [c["id"] for c in controles],
                        "max_llamadas": 20,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return
        verificar_cuenta()
        configurar_logging(archivo=ruta("data/operaciones/mejoras.log"))
        proveedor = Vertex(
            ConfiguracionVertex.model_validate(plan["configuracion"]),
            Registro(ruta("data/operaciones/registro.sqlite")),
            plan["ejecucion_id"],
        )
        resultado = ejecutar_controles(
            caso,
            proveedor,
            PreparadorMejoras(cargar_runtime(), raiz=ruta(".")),
            destino=destino,
            checkpoints=ruta("data/operaciones/mejoras_controles.sqlite"),
        )
    except (ValueError, OSError) as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(
        json.dumps(
            {
                "protocolo_id": resultado["protocolo_id"],
                "estado": resultado["estado"],
                "casos": len(resultado["casos"]),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
