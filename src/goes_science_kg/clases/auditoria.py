"""Reconstruye las claves de las revisiones y las coteja con respuestas reales del ledger."""

from __future__ import annotations

import ast
import io
import json
import re
import zipfile

from goes_science_kg.clases.compilacion import leer_propio
from goes_science_kg.clases.contexto import contexto
from goes_science_kg.clases.contratos import CRITERIOS, ROLES, LecturaClases, esquema_lectura, esquema_transporte
from goes_science_kg.clases.preparacion import contexto as contexto_historico
from goes_science_kg.clases.presupuesto import comprobar_continuidad
from goes_science_kg.clases.proveedor import EJECUCION, MODELOS
from goes_science_kg.materiales.compilacion import sha
from goes_science_kg.motor.contratos import huella


def cierre_presupuesto(registro):
    balance = comprobar_continuidad(registro.archivo)
    with registro.conexion() as db:
        filas = [
            dict(r) for r in db.execute("SELECT * FROM llamadas WHERE ejecucion=? ORDER BY creada,id", (EJECUCION,))
        ]
    if any(r["estado"] == "reservada" for r in filas):
        raise ValueError("Hay invocaciones pendientes; la entrega no puede fijar todavía el consumo de cierre")
    return {"ejecucion": EJECUCION, **balance, "huella_filas": huella(filas)}


def _clave(modelo, sistema, mensaje, esquema, max_salida, razonamiento):
    # Mismo contrato del adaptador Vertex; no incluye credenciales ni ejecuta código archivado.
    contenido = [
        "g-edu-lxp-xai-dev-prj-976d",
        "global",
        modelo,
        sistema,
        mensaje,
        esquema,
        max_salida,
        {"thinking_level": razonamiento},
    ]
    return sha(json.dumps(contenido, ensure_ascii=False, sort_keys=True).encode())


def protocolo_congelado(base, archivo_resultado, preparacion, resultado):
    ref = json.loads(
        leer_propio(base, (archivo_resultado.parent / "protocolo.json").relative_to(base).as_posix()).read_bytes()
    )
    m = re.fullmatch(
        r"clases-p([2-9]|10)(?:-(?:masivo|seguimiento|r10-correcciones|editorial)-[0-9]{3})?", ref["protocolo"]
    )
    if not m or preparacion["id"] not in ref["preparaciones"] or ref["ejecucion"] != EJECUCION:
        raise ValueError("El protocolo no pertenece a la ejecución y preparación de Ciencias")
    numero = int(m[1])
    archivo = leer_propio(base, f"data/clases_v4/protocolos/codigo_clases_p{numero}.zip")
    codigo = archivo.read_bytes()
    prefijo = "src/goes_science_kg/clases/"
    with zipfile.ZipFile(io.BytesIO(codigo)) as z:
        arbol = ast.parse(z.read(prefijo + "prompts.py"))
        constantes = {
            n.targets[0].id: ast.literal_eval(n.value)
            for n in arbol.body
            if isinstance(n, ast.Assign)
            and len(n.targets) == 1
            and isinstance(n.targets[0], ast.Name)
            and n.targets[0].id in {"JUEZ", "ESPECIALIDADES", "EDITOR"}
        }
        archivos = ("contratos.py", "fuentes.py", "motor.py", "prompts.py", "preparacion.py", "validacion.py")
        if numero >= 5:
            archivos += ("proveedor.py", "operacion.py")
        if numero >= 8:
            archivos += ("edicion.py",)
            constantes["_ESQUEMA_EDICION"] = json.loads(z.read("esquemas/edicion.json"))
        if numero >= 9:
            archivos += ("editorial.py",)
        if numero >= 10:
            archivos += ("contexto.py",)
        constantes["_CONTEXTO_VERSION"] = 2 if numero >= 10 else 1
        hashes = {n: sha(z.read(prefijo + n)) for n in archivos}
    configuracion = {
        rol: {
            "modelo": MODELOS[rol],
            "max_salida": (24576 if numero < 4 else 32768)
            if rol == "clases_redactor"
            else (
                8192
                if numero == 2 and rol == "clases_psicopedagogia"
                else 32768
                if numero >= 7 and rol != "clases_psicopedagogia"
                else 16384
            ),
            "razonamiento": "MEDIUM" if rol in {"clases_redactor", "clases_psicopedagogia"} else "HIGH",
        }
        for rol in (*ROLES, "clases_redactor")
    }
    datos_entorno = {
        "protocolo": ref["protocolo"],
        "corpus_sha256": preparacion["corpus_sha256"],
        "codigo": hashes,
        "configuracion": configuracion,
    }
    if numero >= 5:
        datos_entorno["configuracion_tecnica"] = {rol: configuracion[rol] | {"max_salida": 32768} for rol in ROLES}
    esperado = huella(datos_entorno)
    if ref["huella_entorno"] != esperado or resultado["huella_entorno"] != esperado:
        raise ValueError("El entorno no reconstruye el código y configuración congelados")
    return constantes, configuracion, archivo, sha(codigo)


def verificar_trazas(base, archivo_resultado, preparacion, resultado, registro):
    constantes, configuracion, archivo_codigo, codigo_sha = protocolo_congelado(
        base, archivo_resultado, preparacion, resultado
    )
    trazas = []
    for ronda in resultado["rondas"]:
        edicion = ronda.get("edicion_formato")
        if edicion and edicion.get("respuesta"):
            from goes_science_kg.clases.edicion import EdicionesClases

            clave = _clave(
                "gemini-3.8-flash",
                constantes["EDITOR"],
                json.dumps(edicion["solicitud"], ensure_ascii=False, sort_keys=True),
                constantes["_ESQUEMA_EDICION"],
                16384,
                "MEDIUM",
            )
            raw = registro.salida(clave)
            if (
                raw is None
                or edicion["modelo"] != "gemini-3.8-flash"
                or huella(EdicionesClases.model_validate_json(raw)) != huella(edicion["respuesta"])
            ):
                raise ValueError("El parche editorial no corresponde a una respuesta real del proveedor")
            with registro.conexion() as db:
                llamadas = [
                    dict(f)
                    for f in db.execute(
                        "SELECT id,modelo,rol,estado FROM llamadas WHERE ejecucion=? AND clave=? ORDER BY creada,id",
                        (EJECUCION, clave),
                    )
                ]
            if not llamadas or any(f["modelo"] != "gemini-3.8-flash" or f["rol"] != "clases_editor" for f in llamadas):
                raise ValueError("El parche no tiene una invocación editorial en el ledger acumulado")
            trazas.append(
                {
                    "ronda": ronda["numero"],
                    "rol": "clases_editor",
                    "clave": clave,
                    "salida_sha256": sha(raw.encode()),
                    "archivo_salida": "data/clases_v4/auditorias/salidas/" + clave + ".json",
                    "llamadas": llamadas,
                }
            )
        if not ronda["borrador"]:
            continue
        guiones = [g for g in ronda["borrador"]["guiones"] if g["fila_id"] not in ronda["errores_estructura"]]
        if not guiones:
            continue
        ids = {g["fila_id"] for g in guiones}
        for rol in ROLES:
            lector = ronda["lectores"].get(rol)
            if not lector or lector["error"] or not lector["lectura"]:
                continue
            cfg = configuracion[rol]
            crear_contexto = contexto if constantes["_CONTEXTO_VERSION"] == 2 else contexto_historico
            mensaje = json.dumps(
                crear_contexto(preparacion, ids=ids) | {"guiones": guiones, "criterios_obligatorios": CRITERIOS[rol]},
                ensure_ascii=False,
                sort_keys=True,
            )
            clave = _clave(
                cfg["modelo"],
                constantes["JUEZ"] + "\n" + constantes["ESPECIALIDADES"][rol],
                mensaje,
                esquema_transporte(esquema_lectura(rol)).model_json_schema(),
                32768 if lector.get("recuperacion_tecnica") else cfg["max_salida"],
                cfg["razonamiento"],
            )
            raw = registro.salida(clave)
            if raw is None:
                raise ValueError("No hay respuesta real del proveedor para la revisión exacta publicada")
            lectura = LecturaClases.model_validate_json(raw)
            if huella(lectura) != huella(lector["lectura"]):
                raise ValueError("El dictamen no coincide con la respuesta real del proveedor")
            with registro.conexion() as db:
                llamadas = [
                    dict(f)
                    for f in db.execute(
                        "SELECT id,modelo,rol,estado FROM llamadas WHERE ejecucion=? AND clave=? ORDER BY creada,id",
                        (EJECUCION, clave),
                    )
                ]
            if not llamadas or any(f["modelo"] != cfg["modelo"] or f["rol"] != rol for f in llamadas):
                raise ValueError("La respuesta no tiene una invocación registrada en el ledger acumulado")
            trazas.append(
                {
                    "ronda": ronda["numero"],
                    "rol": rol,
                    "clave": clave,
                    "salida_sha256": sha(raw.encode()),
                    "archivo_salida": "data/clases_v4/auditorias/salidas/" + clave + ".json",
                    "llamadas": llamadas,
                }
            )
    return {
        "version": "auditoria-clases-2",
        "preparacion_id": preparacion["id"],
        "resultado_sha256": sha(archivo_resultado.read_bytes()),
        "codigo_archivado": archivo_codigo.relative_to(base).as_posix(),
        "codigo_sha256": codigo_sha,
        "trazas": trazas,
    }
