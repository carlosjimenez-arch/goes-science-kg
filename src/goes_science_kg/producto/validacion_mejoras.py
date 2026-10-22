"""Cierre reproducible de propuestas: conserva filas y rondas, sin confianza en banderas persistidas."""

from __future__ import annotations

from goes_science_kg.motor.contratos import huella
from goes_science_kg.producto.mejoras_contratos import (
    CRITERIOS_MEJORA,
    ROLES_MEJORA,
    BorradorMejora,
    PreparacionMejora,
    ResultadoMejora,
    RondaMejora,
)


def validar_borrador(b: BorradorMejora, p: PreparacionMejora) -> tuple[str, ...]:
    filas = {f["id"]: f for f in p.filas_originales}
    if [f.fila_id for f in b.filas] != list(filas):
        return ("La propuesta debe conservar exactamente todas las filas y su orden, sin duplicar ni eliminar",)
    fragmentos = {f.id: f for f in p.fragmentos}
    evidencias = {e.id: e for e in p.evidencias}
    errores = []
    if list(b.enmiendas_aceptadas) != [e["id"] for e in p.correcciones_requeridas]:
        errores.append("Las enmiendas científicas deben aceptarse explícitamente y conservarse sin cambios")
    for n, f in enumerate(b.filas):
        original = filas[f.fila_id]
        decision = p.clasificaciones_originales[f.fila_id]
        if (f.accion == "fuera_alcance") != (decision["estado"] == "fuera_alcance"):
            errores.append(f"Fila {n}: no se retiran ni incorporan temas fuera del alcance original de Ciencias")
        if decision["estado"] in {"declarado_malla", "coincidencia_automatica"} and not set(
            decision["disciplinas"]
        ).issubset(f.disciplinas_propuestas):
            errores.append(f"Fila {n}: la propuesta no conserva las disciplinas respaldadas del original")
        if f.accion == "mantener_objetivo" and " ".join(f.objetivo_propuesto.split()) != " ".join(
            original["procedimental"].split()
        ):
            errores.append(f"Fila {n}: mantener_objetivo no puede cambiar su texto")
        if len(set(f.fragmentos_ids)) != len(f.fragmentos_ids) or set(f.fragmentos_ids) - fragmentos.keys():
            errores.append(f"Fila {n}: citas duplicadas o inventadas")
            continue
        pruebas = [evidencias[fragmentos[i].evidencia_id] for i in f.fragmentos_ids]
        if not any(fragmentos[i].evidencia_id in p.grupos[f"fila_{n:02d}"] for i in f.fragmentos_ids):
            errores.append(f"Fila {n}: falta una cita del objetivo exacto, no de otra celda o fila")
        if not any(e.version == "referencia" for e in pruebas):
            errores.append(f"Fila {n}: falta la referencia primaria que informa el diseño propuesto")
        if any(e.version == "V4" and e.id.partition("#CELDA:")[0] != f.fila_id for e in pruebas):
            errores.append(f"Fila {n}: se usó evidencia de otra fila")
    return tuple(errores)


def evaluar_ronda(r: RondaMejora, p: PreparacionMejora, modelos: dict[str, str]) -> tuple[str, tuple[str, ...]]:
    if r.borrador is None:
        return "abstencion", ("No existe un borrador válido: " + (r.error_generacion or "sin respuesta"),)
    errores = validar_borrador(r.borrador, p)
    if errores != r.errores_estructura:
        raise ValueError("Los errores de estructura archivados no corresponden a la propuesta")
    if errores:
        return "abstencion", errores
    if len(r.dictamenes) != len(ROLES_MEJORA) or {d.rol for d in r.dictamenes} != set(ROLES_MEJORA):
        return "abstencion", ("Se requieren cuatro revisiones independientes completas",)
    conocidos = {f.id: f for f in p.fragmentos}
    incertidumbre, negativos, motivos = False, False, []
    for d in r.dictamenes:
        if d.modelo != modelos[d.rol] or d.huella_preparacion != p.id or d.huella_borrador != huella(r.borrador):
            raise ValueError("Dictamen de otro modelo, contexto o borrador")
        if d.error or d.lectura is None:
            incertidumbre = True
            motivos.append(f"{d.rol}: lectura no disponible ({d.error})")
            continue
        lectura = d.lectura
        if set(lectura.criterios) != set(CRITERIOS_MEJORA[d.rol]) or set(lectura.fragmentos_ids) - conocidos.keys():
            raise ValueError("La lectura cambia criterios o introduce citas desconocidas")
        seleccion = {conocidos[i].evidencia_id for i in lectura.fragmentos_ids}
        if any(not seleccion.intersection(ids) for ids in p.grupos.values()):
            raise ValueError("La revisión omitió un grupo obligatorio de fuentes")
        for criterio, valor in lectura.criterios.items():
            incertidumbre |= valor == "insuficiente"
            negativos |= valor == "no"
            if valor != "si":
                motivos.append(f"{d.rol}/{criterio}: {valor}")
        if lectura.hallazgos:
            motivos.extend(f"{d.rol}: {x}" for x in lectura.hallazgos)
            # Un hallazgo no resuelto no coexiste con una aprobación total.
            incertidumbre = True
    estado = "no_respaldado" if negativos else "abstencion" if incertidumbre else "respaldado_automaticamente"
    return estado, tuple(motivos)


def resolver_mejora(
    p: PreparacionMejora, rondas: tuple[RondaMejora, ...], *, ejecucion_id: str, modelos: dict[str, str]
) -> ResultadoMejora:
    if not 1 <= len(rondas) <= 2:
        raise ValueError("Se admite una propuesta y una única reparación")
    for i, ronda in enumerate(rondas):
        estado, motivos = evaluar_ronda(ronda, p, modelos)
        if i < len(rondas) - 1 and estado == "respaldado_automaticamente":
            raise ValueError("No se vuelve a votar una propuesta respaldada")
    if len(rondas) == 2 and rondas[0].borrador is not None and rondas[0].borrador == rondas[1].borrador:
        raise ValueError("Una reparación no puede repetir el mismo borrador")
    return ResultadoMejora(
        solicitud=p.solicitud,
        ejecucion_id=ejecucion_id,
        preparacion_id=p.id,
        estado=estado,
        propuesta=rondas[-1].borrador if estado == "respaldado_automaticamente" else None,
        rondas=rondas,
        motivos=motivos,
    )
