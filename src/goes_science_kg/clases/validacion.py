"""Controles deterministas; la corrección semántica requiere además los cuatro jueces."""

from __future__ import annotations

import ast
import json
import math
import operator

from pydantic import ValidationError

from goes_science_kg.clases.contratos import CRITERIOS, MAX_BYTES_BORRADOR, BorradorClases, GuionClase

OPERADORES = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
}


def huella_contenido(guion):
    from goes_science_kg.motor.contratos import huella

    def normalizar(v):
        if isinstance(v, str):
            return " ".join(v.split())
        if isinstance(v, dict):
            return {k: normalizar(x) for k, x in v.items() if k not in {"titulo", "fila_id"}}
        if isinstance(v, (tuple, list)):
            return [normalizar(x) for x in v]
        return v

    return huella(normalizar(guion))


def calcular(expresion: str) -> float:
    raiz = ast.parse(expresion, mode="eval")
    if len(list(ast.walk(raiz))) > 64:
        raise ValueError("La expresión excede el límite de complejidad")

    def evaluar(n):
        if isinstance(n, ast.Constant) and type(n.value) in (int, float):
            valor = float(n.value)
        elif isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.USub, ast.UAdd)):
            valor = evaluar(n.operand) * (-1 if isinstance(n.op, ast.USub) else 1)
        elif isinstance(n, ast.BinOp) and type(n.op) in OPERADORES:
            a, b = evaluar(n.left), evaluar(n.right)
            if isinstance(n.op, ast.Pow) and (abs(b) > 100 or abs(a) > 1e100):
                raise ValueError("Potencia fuera de límites")
            valor = OPERADORES[type(n.op)](a, b)
        elif isinstance(n, ast.Name) and n.id == "pi":
            valor = math.pi
        elif isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and not n.keywords:
            funciones = {
                nombre: getattr(math, nombre)
                for nombre in ("sqrt", "sin", "cos", "tan", "asin", "acos", "atan", "log10", "log", "exp")
            }
            if n.func.id in funciones and len(n.args) == 1:
                valor = funciones[n.func.id](evaluar(n.args[0]))
            elif n.func.id == "round" and len(n.args) == 2:
                decimales = evaluar(n.args[1])
                if decimales != int(decimales) or abs(decimales) > 12:
                    raise ValueError("Redondeo fuera de límites")
                valor = round(evaluar(n.args[0]), int(decimales))
            else:
                raise ValueError("Función no permitida o argumentos incompatibles")
        else:
            raise ValueError("Sólo se admiten aritmética y funciones explícitamente permitidas")
        if not math.isfinite(valor) or abs(valor) > 1e100:
            raise ValueError("Resultado no finito o fuera de límites")
        return valor

    return evaluar(raiz.body)


def validar_borrador(borrador: BorradorClases, preparacion: dict, *, ids_esperados=None):
    esperados = set(ids_esperados or (f["fila_id"] for f in preparacion["filas"]))
    originales = {f["fila_id"]: f for f in preparacion["filas"]}
    if {g.fila_id for g in borrador.guiones} != esperados:
        raise ValueError("El borrador no conserva exactamente las filas solicitadas")
    errores = {}
    for g in borrador.guiones:
        fallos = []
        if g.objetivo != originales[g.fila_id]["propuesta"]["objetivo_propuesto"]:
            fallos.append("El objetivo aceptado debe conservarse literalmente")
        fuentes = set(originales[g.fila_id]["fuentes_cientificas_ids"])
        if any(set(a.fuentes_ids) - fuentes for a in g.explicacion_docente):
            fallos.append("La explicación cita una fuente ajena al contexto científico de la fila")
        for t in g.tareas:
            for calculo in t.calculos:
                try:
                    obtenido = calcular(calculo.expresion)
                    # Una tolerancia absoluta no puede ocultar una magnitud física pequeña errónea.
                    # El protocolo exige 1e-6 relativo como máximo; el redondeo se expresa con round.
                    if not math.isclose(
                        obtenido,
                        calculo.resultado,
                        rel_tol=min(calculo.tolerancia_relativa, 1e-6),
                        abs_tol=min(calculo.tolerancia, abs(calculo.resultado) * 1e-6),
                    ):
                        fallos.append(
                            f"La comprobación aritmética {calculo.expresion!r} produce {obtenido!r}, "
                            f"no {calculo.resultado!r}. Expresa el redondeo con round si es necesario."
                        )
                except (ValueError, SyntaxError, TypeError, ZeroDivisionError, OverflowError) as error:
                    fallos.append("Comprobación aritmética inválida: " + type(error).__name__)
        if fallos:
            errores[g.fila_id] = sorted(set(fallos))
    return errores


def validar_lectura(lectura, rol, guiones, preparacion):
    esperados = {g.fila_id for g in guiones}
    if {f.fila_id for f in lectura.filas} != esperados or len(lectura.filas) != len(esperados):
        raise ValueError("La lectura debe evaluar cada fila exactamente una vez")
    fuentes = {f["fila_id"]: set(f["fuentes_cientificas_ids"]) for f in preparacion["filas"]}
    for f in lectura.filas:
        if set(f.criterios) != set(CRITERIOS[rol]):
            raise ValueError("La lectura no conserva todos los criterios exactos del rol")
        if set(f.fuentes_ids) - fuentes[f.fila_id]:
            raise ValueError("La lectura cita una fuente ajena al contexto científico de la fila")
        if any(v != "si" for v in f.criterios.values()) and not f.hallazgos:
            raise ValueError("Cada veto o insuficiencia requiere un hallazgo concreto")


def recuperar_validos(texto, preparacion, ids):
    """Rescata filas válidas de un JSON completo, conservando el fallo de cada una de las demás.

    Nunca reconstruye JSON truncado ni corrige la respuesta del modelo. Todas las identidades deben
    estar presentes exactamente una vez y cada guion que siga a revisión pasa el contrato íntegro.
    """
    if not texto or len(texto.encode()) > MAX_BYTES_BORRADOR:
        raise ValueError("No hay una respuesta completa dentro del límite de contexto")
    datos = json.loads(texto)
    if not isinstance(datos, dict) or set(datos) != {"guiones"} or not isinstance(datos["guiones"], list):
        raise ValueError("El contenedor no conserva el contrato")
    filas = datos["guiones"]
    if not all(isinstance(g, dict) for g in filas):
        raise ValueError("Los guiones deben ser objetos")
    if len(filas) != len(ids) or {g.get("fila_id") for g in filas} != set(ids):
        raise ValueError("El JSON no conserva exactamente las identidades solicitadas")
    validos, errores = [], {}
    for dato in filas:
        try:
            validos.append(GuionClase.model_validate(dato))
        except ValidationError as error:
            errores[dato["fila_id"]] = [
                ".".join(str(x) for x in e["loc"]) + ": " + e["msg"] for e in error.errors(include_input=False)[:8]
            ]
    borrador = BorradorClases(guiones=validos) if validos else None
    if borrador:
        errores.update(validar_borrador(borrador, preparacion, ids_esperados={g.fila_id for g in validos}))
    return borrador, errores


def certificar_resultado(resultado, preparacion, modelos=None):
    """Reconstituye cada respaldo desde el borrador y sus cuatro lecturas, sin confiar en la etiqueta."""
    from goes_science_kg.clases.contratos import ROLES, GuionClase, LecturaClases
    from goes_science_kg.motor.contratos import huella

    ids = {f["fila_id"] for f in preparacion["filas"]}
    if resultado["preparacion_id"] != preparacion["id"] or set(resultado["filas"]) != ids:
        raise ValueError("El resultado no conserva la preparación ni sus filas exactas")
    if resultado["snapshot_id"] != preparacion["snapshot_id"] or not 1 <= len(resultado["rondas"]) <= 2:
        raise ValueError("Snapshot o número de rondas incompatible")
    for i, ronda in enumerate(resultado["rondas"]):
        if ronda.get("tipo") == "edicion_formato":
            from goes_science_kg.clases.edicion import aplicar_ediciones, preparar_edicion

            if i != 1:
                raise ValueError("La edición de formato sólo puede consumir la segunda y última ronda")
            anterior = resultado["rondas"][0]
            solicitud = preparar_edicion(anterior["respuesta_rechazada"], ronda["filas"], anterior["filas"])
            edicion = ronda.get("edicion_formato") or {}
            if solicitud is None or edicion.get("solicitud") != solicitud:
                raise ValueError("La edición no corresponde a un fallo de longitud puro en el guion anterior")
            if ronda["borrador"]:
                reconstruido = aplicar_ediciones(solicitud, edicion["respuesta"]).model_dump(mode="json")
                if reconstruido != ronda["borrador"]:
                    raise ValueError("El guion editado cambia campos ajenos al parche autorizado")
        if ronda.get("tipo") != "recuperacion_tecnica":
            continue
        if i != 1:
            raise ValueError("La recuperación técnica sólo puede ser la segunda y última ronda")
        anterior = resultado["rondas"][0]
        if (
            ronda["borrador"] != anterior["borrador"]
            or ronda["filas"] != anterior["filas"]
            or ronda["errores_estructura"]
            or anterior["errores_estructura"]
        ):
            raise ValueError("La recuperación técnica debe conservar el guion y contexto sin fallos estructurales")
        recuperados = 0
        for rol in ROLES:
            previo = anterior["lectores"][rol]
            nuevo = ronda["lectores"][rol]
            if previo["error"] or not previo["lectura"]:
                if not nuevo.get("recuperacion_tecnica"):
                    raise ValueError("Falta la traza del lector recuperado")
                recuperados += 1
            elif previo != nuevo or any(v != "si" for f in previo["lectura"]["filas"] for v in f["criterios"].values()):
                raise ValueError("La recuperación técnica no puede cambiar votos válidos ni repetir vetos")
        if not recuperados:
            raise ValueError("La recuperación no tiene ningún lector técnicamente fallido")
    for id_, final in resultado["filas"].items():
        if final["fila_id"] != id_:
            raise ValueError("Una fila terminal cambió de identidad")
        numero = final["ronda_seleccionada"]
        if not 1 <= numero <= len(resultado["rondas"]):
            raise ValueError("La ronda seleccionada no existe")
        ronda = resultado["rondas"][numero - 1]
        if ronda["numero"] != numero or id_ not in ronda["filas"]:
            raise ValueError("La ronda no evaluó esa fila")
        if final["estado"] != "respaldado_automaticamente":
            if not final["motivos"]:
                raise ValueError("Una abstención o veto necesita motivos")
            continue
        guion = GuionClase.model_validate(final["guion"])
        if final["motivos"] or not ronda["borrador"]:
            raise ValueError("Un respaldo no puede contener motivos de veto ni carecer de borrador")
        borrador = BorradorClases.model_validate(ronda["borrador"])
        presentes = {g.fila_id: g for g in borrador.guiones}
        if presentes.get(id_) != guion:
            raise ValueError("El guion respaldado difiere del borrador leído")
        presentes_ids = set(presentes)
        invalidos = set(ronda["errores_estructura"]) - presentes_ids
        if presentes_ids | invalidos != set(ronda["filas"]):
            raise ValueError("El borrador parcial y los errores no conservan las filas de la ronda")
        errores = validar_borrador(borrador, preparacion, ids_esperados=presentes_ids)
        if id_ in errores or id_ in ronda["errores_estructura"]:
            raise ValueError("El guion respaldado no supera los controles deterministas")
        dictamenes = []
        guiones_leidos = [g for g in borrador.guiones if g.fila_id not in ronda["errores_estructura"]]
        for rol in ROLES:
            lector = ronda["lectores"].get(rol)
            if not lector or lector["error"] or not lector["lectura"]:
                raise ValueError("Falta una lectura válida para el respaldo")
            if modelos and lector["modelo"] != modelos[rol]:
                raise ValueError("El modelo del dictamen no corresponde al protocolo")
            lectura = LecturaClases.model_validate(lector["lectura"])
            validar_lectura(lectura, rol, guiones_leidos, preparacion)
            fila = next(f for f in lectura.filas if f.fila_id == id_)
            if any(v != "si" for v in fila.criterios.values()):
                raise ValueError("El respaldo contiene un veto o evidencia insuficiente")
            dictamenes.append(
                {
                    "rol": rol,
                    "modelo": lector["modelo"],
                    "huella_guion": huella(guion),
                    "huella_preparacion": preparacion["id"],
                    "lectura": fila.model_dump(mode="json"),
                    "error": None,
                }
            )
        if final["dictamenes"] != dictamenes:
            raise ValueError("Los dictámenes terminales no reconstruyen las cuatro lecturas exactas")
    todo = all(f["estado"] == "respaldado_automaticamente" for f in resultado["filas"].values())
    if (resultado["estado"] == "respaldado_automaticamente") != todo:
        raise ValueError("La cobertura global no coincide con las filas")
