"""Preparación local y ejecución explícita de paquetes docentes por unidad."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Annotated, Literal
from uuid import uuid4

import typer

from goes_science_kg.archivos import destino_generado
from goes_science_kg.config import cargar, ruta

app = typer.Typer(help="Unidades V4: objetivos, aula, evidencia y sesiones", no_args_is_help=True)


def _destino(destino: Path) -> Path:
    """Comprueba todos los nombres antes de preparar o invocar proveedores."""
    if destino.is_symlink() or (destino.exists() and not destino.is_dir()):
        raise ValueError("El destino debe ser un directorio propio, no un archivo ni un enlace simbólico")
    for nombre in ("paquete.json", "paquete.md"):
        destino_generado(destino / nombre, raiz=ruta("."))
    return destino


@app.command("listar")
def listar(
    grado: Annotated[int | None, typer.Option(min=2, max=11)] = None,
    asignatura_malla: Annotated[str | None, typer.Option()] = None,
) -> None:
    """Muestra nombres exactos y cantidad de filas de cada unidad del insumo."""
    from goes_science_kg.curriculo import cargar_curriculo

    conteos = Counter(
        (f.grado, f.asignatura_malla, f.unidad)
        for f in cargar_curriculo().filas
        if (grado is None or grado == f.grado) and (asignatura_malla is None or asignatura_malla == f.asignatura_malla)
    )
    typer.echo(
        json.dumps(
            [{"grado": g, "asignatura_malla": a, "unidad": u, "filas": n} for (g, a, u), n in sorted(conteos.items())],
            ensure_ascii=False,
            indent=2,
        )
    )


@app.command("preparar")
def preparar(
    grado: Annotated[int, typer.Option(min=2, max=11)],
    asignatura_malla: Annotated[str, typer.Option()],
    unidad: Annotated[str, typer.Option(help="Nombre exacto mostrado por listar")],
    catalogo: Annotated[Path, typer.Option(help="Catálogo completo o piloto expresamente identificado")],
    destino: Annotated[Path, typer.Option()],
    minutos: Annotated[int, typer.Option(min=5, max=120)] = 40,
    recursos: str = typer.Option("papel,lapiz"),
    conectividad: Literal["sin_confirmar", "sin_conexion", "intermitente", "disponible"] = "sin_confirmar",
    apoyo: Annotated[list[str] | None, typer.Option(help="Apoyo conocido; opción repetible")] = None,
    seguridad: Annotated[list[str] | None, typer.Option(help="Restricción conocida; opción repetible")] = None,
) -> None:
    """Exporta todas las filas y sus evidencias; no genera respuestas ni usa GCP."""
    from goes_science_kg.curriculo import cargar_curriculo
    from goes_science_kg.curriculo.catalogacion import CatalogoDisciplinas
    from goes_science_kg.curriculo.contexto_fuentes import fuentes_del_curriculo
    from goes_science_kg.producto.garantias import bloqueos_cientificos
    from goes_science_kg.producto.unidades import ContextoAula, exportar_unidad, preparar_unidad

    try:
        _destino(destino)
        curriculo = cargar_curriculo()
        datos = json.loads(ruta(catalogo).read_text(encoding="utf-8"))
        disciplinas = CatalogoDisciplinas.model_validate(
            datos.get("catalogo", datos) if isinstance(datos, dict) else datos
        )
        fuentes = fuentes_del_curriculo(curriculo, raiz_v4=ruta("insumos/v4"))
        fuentes.bloqueos_curriculares = bloqueos_cientificos(
            curriculo, fuentes, ruta("docs/investigacion/alertas_v4.json")
        )
        contexto = ContextoAula(
            minutos_por_sesion=minutos,
            recursos=tuple(r.strip() for r in recursos.split(",") if r.strip()),
            conectividad=conectividad,
            apoyos=tuple(apoyo or ()),
            seguridad=tuple(seguridad or ()),
        )
        paquete = preparar_unidad(
            curriculo,
            disciplinas,
            grado=grado,
            asignatura_malla=asignatura_malla,
            unidad=unidad,
            contexto=contexto,
            fuentes=fuentes,
        )
        archivos = exportar_unidad(paquete, destino)
    except (OSError, ValueError) as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(
        json.dumps(
            {
                "estado": paquete.estado,
                "paquete_id": paquete.id,
                "catalogo_modo": paquete.catalogo_modo,
                "filas": len(paquete.filas),
                "sesiones_propuestas": len(paquete.sesiones),
                "solicitudes_ejecutables": sum(s.solicitud is not None for s in paquete.sesiones),
                "llamadas": 0,
                "archivos": archivos,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


@app.command("ejecutar")
def ejecutar(
    archivo: Path,
    destino: Annotated[Path, typer.Option()],
    ejecutar: bool = typer.Option(False, "--ejecutar"),
    ejecucion: Annotated[str | None, typer.Option(help="Conserva presupuesto y checkpoints")] = None,
    max_usd: Annotated[float, typer.Option(min=0.01, max=20)] = 3.0,
    max_llamadas: Annotated[int, typer.Option(min=1, max=200)] = 24,
    max_salida_tokens: Annotated[int, typer.Option(min=256, max=16384)] = 4096,
) -> None:
    """Muestra el plan; --ejecutar requiere la misma publicación completa que el paquete."""
    from goes_science_kg.motor.contratos import huella
    from goes_science_kg.producto.unidades import PaqueteUnidad

    try:
        _destino(destino)
        datos = json.loads(archivo.read_text(encoding="utf-8"))
        paquete = PaqueteUnidad.model_validate(datos.get("paquete", datos) if isinstance(datos, dict) else datos)
        if paquete.id != huella(paquete.model_dump(mode="json", exclude={"id"})):
            raise ValueError("El paquete cambió después de prepararse")
        if not ejecutar:
            typer.echo(
                json.dumps(
                    {
                        "estado": "plan",
                        "paquete_id": paquete.id,
                        "llamadas": 0,
                        "catalogo_modo": paquete.catalogo_modo,
                        "sesiones": len(paquete.sesiones),
                        "max_intentos_acumulados": max_llamadas,
                        "max_reserva_usd": max_usd,
                        "max_salida_tokens": max_salida_tokens,
                        "requiere_publicacion_completa": True,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return
        if paquete.catalogo_modo != "completo" or not paquete.piloto_superado:
            raise ValueError("La ejecución requiere un catálogo completo con piloto superado")
        id_ejecucion = ejecucion or uuid4().hex
        if not re.fullmatch(r"[a-zA-Z0-9_-]{1,100}", id_ejecucion):
            raise ValueError("El ID de presupuesto debe tener entre uno y cien caracteres seguros")
        from goes_science_kg.producto.unidades import ejecutar_unidad, exportar_unidad

        motor, registro, base = _crear_motor(paquete, id_ejecucion, max_usd, max_llamadas, max_salida_tokens)
        resultado = ejecutar_unidad(
            paquete,
            motor=motor,
            registro=registro,
            ejecucion_id=id_ejecucion,
            directorio_operaciones=base / "unidades",
        )
        archivos = exportar_unidad(paquete, destino, resultado=resultado)
    except (OSError, ValueError) as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(
        json.dumps(
            {
                "ejecucion_id": id_ejecucion,
                "cobertura": resultado.cobertura,
                "consumo": resultado.consumo_despues,
                "archivos": archivos,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def _crear_motor(paquete, id_ejecucion, max_usd, max_llamadas, max_salida_tokens):
    """Revalida la publicación y prepara un proveedor; no solicita respuestas."""
    from goes_science_kg.motor.contratos import huella
    from goes_science_kg.motor.flujo import Motor
    from goes_science_kg.motor.registro import Registro
    from goes_science_kg.motor.vertex import ConfiguracionVertex, Vertex
    from goes_science_kg.observabilidad import configurar_logging
    from goes_science_kg.producto.runtime import cargar_runtime
    from goes_science_kg.producto.unidades import preparar_unidad

    runtime = cargar_runtime()
    if (
        runtime.producto.curriculo.huella != paquete.huella_curriculo
        or huella(runtime.producto.catalogo) != paquete.huella_catalogo
    ):
        raise ValueError("El paquete no corresponde al currículo y catálogo de la publicación activa")
    verificado = preparar_unidad(
        runtime.producto.curriculo,
        runtime.producto.catalogo,
        grado=paquete.grado,
        asignatura_malla=paquete.asignatura_malla,
        unidad=paquete.unidad,
        contexto=paquete.contexto,
        fuentes=runtime.fuentes,
    )
    if verificado != paquete:
        raise ValueError(
            "El paquete no coincide con las filas, decisiones y fuentes de la publicación; prepáralo nuevamente"
        )
    cfg = cargar("motor")
    configuracion = ConfiguracionVertex.model_validate(
        cfg["vertex"] | {"max_usd": max_usd, "max_llamadas": max_llamadas, "max_salida_tokens": max_salida_tokens}
    )
    base = ruta("data/operaciones")
    configurar_logging(archivo=base / "motor.log")
    registro = Registro(base / "registro.sqlite")
    proveedor = Vertex(configuracion, registro, id_ejecucion)
    motor = Motor(
        runtime.buscador,
        proveedor,
        fuentes=runtime.fuentes,
        max_caracteres=cfg["max_caracteres_contexto"],
        max_reparaciones=cfg["max_reparaciones"],
    )
    return motor, registro, base


@app.command("recuperar-transporte")
def recuperar_transporte(
    archivo: Path,
    destino: Annotated[Path, typer.Option()],
    ejecutar: bool = typer.Option(False, "--ejecutar"),
    max_salida_tokens: Annotated[int, typer.Option(min=256, max=16384)] = 4096,
) -> None:
    """Una recuperación sin respuestas; conserva el ID, límites, ledger y archivo originales."""
    import hashlib

    from goes_science_kg.archivos import escribir_texto_generado
    from goes_science_kg.motor.contratos import huella
    from goes_science_kg.producto.unidades import PaqueteUnidad, ResultadoUnidad, exportar_unidad

    try:
        _destino(destino)
        if destino.resolve() == archivo.resolve().parent:
            raise ValueError("La recuperación debe exportarse aparte del archivo original")
        auditoria = destino / "recuperacion.json"
        destino_generado(auditoria, raiz=ruta("."))
        datos = json.loads(archivo.read_bytes())
        if not isinstance(datos, dict) or not datos.get("ejecucion"):
            raise ValueError("Se requiere el paquete con su ejecución original completa")
        paquete = PaqueteUnidad.model_validate(datos["paquete"])
        original = ResultadoUnidad.model_validate(datos["ejecucion"])
        if paquete.id != huella(paquete.model_dump(mode="json", exclude={"id"})):
            raise ValueError("El paquete cambió después de prepararse")
        if not ejecutar:
            typer.echo(
                json.dumps(
                    {
                        "estado": "plan_recuperacion_transporte",
                        "ejecucion_id": original.ejecucion_id,
                        "llamadas": 0,
                        "consumo_original": original.consumo_despues["llamadas"],
                        "limites_originales": original.limites_presupuesto,
                        "max_salida_tokens": max_salida_tokens,
                        "recuperaciones_por_objetivo": 1,
                    }
                )
            )
            return
        from goes_science_kg.operacion.recuperacion_unidad import recuperar_unidad_sin_respuesta

        motor, registro, base = _crear_motor(
            paquete,
            original.ejecucion_id,
            original.limites_presupuesto["max_usd"],
            original.limites_presupuesto["max_llamadas"],
            max_salida_tokens,
        )
        resultado = recuperar_unidad_sin_respuesta(
            paquete, original, motor=motor, registro=registro, directorio_operaciones=base / "unidades"
        )
        archivos = exportar_unidad(paquete, destino, resultado=resultado)
        recibo = {
            "original": str(archivo.resolve()),
            "original_sha256": hashlib.sha256(archivo.read_bytes()).hexdigest(),
            "ejecucion_id": original.ejecucion_id,
            "limites": original.limites_presupuesto,
            "consumo_original": original.consumo_despues,
            "consumo_incremental_recuperacion": resultado.consumo_incremental,
            "cobertura_recuperacion": resultado.cobertura,
            "archivos": archivos,
        }
        escribir_texto_generado(auditoria, json.dumps(recibo, ensure_ascii=False, indent=2) + "\n")
        typer.echo(json.dumps(recibo, ensure_ascii=False, indent=2))
    except (OSError, ValueError, KeyError) as error:
        raise typer.BadParameter(str(error)) from error
