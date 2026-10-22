"""Consolidar toda la campaña y publicar la mejora sobre la misma base curricular verificada."""

import json
from pathlib import Path

from goes_science_kg.config import cargar
from goes_science_kg.motor.contratos import huella
from goes_science_kg.producto.almacen import publicar_producto
from goes_science_kg.producto.campana_mejoras import escribir_nuevo_o_igual
from goes_science_kg.producto.grafo_mejoras import grafo_mejoras, incorporar_mejoras
from goes_science_kg.producto.mejoras_contratos import ROLES_MEJORA
from goes_science_kg.producto.mejoras_publicadas import ArchivoMejoras, CasoMejora, validar_archivo_mejoras
from goes_science_kg.producto.preparacion_mejoras import PreparadorMejoras


def consolidar_campana(
    directorio: Path,
    *,
    raiz: Path,
    runtime,
    pruebas: Path,
    historiales: tuple[Path, ...] = (),
    seguimiento: Path | None = None,
) -> ArchivoMejoras:
    plan = json.loads((directorio / "plan.json").read_bytes())
    if plan["id"] != huella({k: v for k, v in plan.items() if k != "id"}):
        raise ValueError("El plan no conserva su identidad")
    casos = []
    for u in plan["unidades"]:
        caso = CasoMejora.model_validate_json((directorio / "resultados" / f"{u['id']}.json").read_bytes())
        if caso.preparacion.id != u["id"] or caso.entorno != u["entorno"] or caso.plan_id != plan["id"]:
            raise ValueError("El caso consolidado no corresponde al protocolo completo")
        casos.append(caso)
    if seguimiento:
        from goes_science_kg.producto.seguimiento_mejoras import incorporar_seguimiento

        casos = incorporar_seguimiento(casos, seguimiento, plan)
        historiales = (*historiales, directorio, seguimiento)
    preparador = PreparadorMejoras(runtime, raiz=raiz)
    fuentes = {
        id_: r.model_dump(mode="json")
        | {"archivo_local": r.archivo_pdf, "raiz_fuente": "referencias_progresiones_2026"}
        for id_, r in preparador.progresiones.repositorio.manifiesto().referencias.items()
    }
    antecedentes = []
    for carpeta in historiales:
        rutas = [
            carpeta / "plan.json",
            *sorted((carpeta / "resultados").glob("*.json")),
            *sorted(carpeta.glob("diagnostico*.json")),
        ]
        antecedentes.append(
            {
                "directorio": carpeta.name,
                "archivos": {
                    p.relative_to(carpeta).as_posix(): json.loads(p.read_bytes()) for p in rutas if p.is_file()
                },
            }
        )
    datos = dict(
        huella_curriculo=runtime.producto.curriculo.huella,
        huella_catalogo=huella(runtime.producto.catalogo),
        modelos={r: plan["configuracion"]["modelos"][r] for r in ROLES_MEJORA},
        unidades=tuple(casos),
        progresiones=preparador.archivo_progresiones,
        fuentes_progresiones=fuentes,
        pruebas_adversariales=json.loads(pruebas.read_bytes())["casos"],
        protocolos_anteriores=tuple(antecedentes),
    )
    archivo = ArchivoMejoras(id="0" * 64, **datos)
    archivo = archivo.model_copy(update={"id": huella(archivo.model_dump(mode="json", exclude={"id"}))})
    validar_archivo_mejoras(archivo, runtime.producto.curriculo, runtime.producto.catalogo)
    return archivo


def publicar_mejoras(archivo: ArchivoMejoras, *, runtime, raiz: Path, destino: Path) -> dict:
    modelos = cargar("mejoras_curriculares")["vertex"]["modelos"]
    validar_archivo_mejoras(
        archivo, runtime.producto.curriculo, runtime.producto.catalogo, modelos={r: modelos[r] for r in ROLES_MEJORA}
    )
    preparador = PreparadorMejoras(runtime, raiz=raiz)
    preparador.progresiones.validar(archivo.progresiones)
    for caso in archivo.unidades:
        if "complemento_cientifico" in caso.preparacion.grupos:
            from goes_science_kg.producto.seguimiento_mejoras import PreparadorSeguimiento

            PreparadorSeguimiento(runtime, raiz=raiz).validar(caso.preparacion)
        else:
            preparador.validar(caso.preparacion)
    producto = runtime.producto
    nodos = [n.model_copy(deep=True) for n in producto.nodos]
    aristas = [a.model_copy(deep=True) for a in producto.aristas]
    if producto.mejoras:
        viejos, enlaces = grafo_mejoras(producto.mejoras)
        retirar = {n.id for n in viejos if n.tipo.value != "Documento"}
        claves = {a.clave for a in enlaces}
        nodos = [n for n in nodos if n.id not in retirar]
        aristas = [a for a in aristas if a.clave not in claves]
    incorporar_mejoras(nodos, aristas, archivo)
    return publicar_producto(
        destino=destino,
        curriculo=producto.curriculo,
        catalogo=producto.catalogo,
        nodos=nodos,
        aristas=aristas,
        diagnostico=producto.diagnostico | {"mejoras_curriculares": archivo.cobertura},
        alertas=producto.alertas,
        publicacion=producto.publicacion
        | {
            "mejoras_curriculares": {"archivo_id": archivo.id, "cobertura": archivo.cobertura, "limite": archivo.limite}
        },
        conocimiento=producto.conocimiento,
        alineaciones=producto.alineaciones,
        mejoras=archivo,
    )


def guardar_archivo(archivo: ArchivoMejoras, destino: Path):
    escribir_nuevo_o_igual(destino, archivo.model_dump(mode="json"))
