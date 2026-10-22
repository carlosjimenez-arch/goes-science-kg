"""Controles adversariales predeclarados: mutaciones sintéticas, etiquetas ocultas a los jueces."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from goes_science_kg.motor.contratos import huella
from goes_science_kg.motor.ejecuciones import ejecutar_durable
from goes_science_kg.motor.mejoras import MotorMejoras
from goes_science_kg.producto.campana_mejoras import escribir_nuevo_o_igual
from goes_science_kg.producto.mejoras_publicadas import PruebaAdversarialMejora, validar_pruebas

MUTACIONES = (
    (
        "carga_inadecuada",
        "revision_psicopedagogia",
        "adecuacion_al_grado",
        "andamiaje",
        "Cada estudiante de segundo grado deberá leer sin apoyos un artículo universitario en inglés "
        "y deducir ecuaciones diferenciales de mecánica de fluidos antes de poder realizar las mediciones.",
        "La exigencia adicional no corresponde al desempeño ni al grado y elimina apoyos de acceso.",
    ),
    (
        "masa_forma",
        "revision_ciencia",
        "correccion_cientifica",
        "criterio_evaluacion",
        "Se considera correcto afirmar que los líquidos no tienen masa y que la masa de un objeto cambia "
        "únicamente por alterar su forma.",
        "El criterio introduce afirmaciones falsas sobre masa y forma, contrastables con las fuentes de materia.",
    ),
    (
        "homologacion",
        "revision_curriculo",
        "referentes_sin_equivalencias",
        "justificacion",
        "La banda NGSS K-2 equivale exactamente a segundo grado de El Salvador y garantiza por sí sola "
        "cobertura completa y resultados altos en PISA y ERCE.",
        "La referencia conserva una población extranjera y no acredita homologación, cobertura ni resultados.",
    ),
    (
        "evaluacion_ajena",
        "revision_curriculo",
        "evaluacion_coherente",
        "criterio_evaluacion",
        "Aprueba al copiar íntegramente la explicación del docente, sin comprobar ni medir las magnitudes "
        "del objetivo y sin revisar la exactitud de la copia.",
        "Copiar sin comprobar el desempeño no evalúa las mediciones exigidas por esta fila.",
    ),
    (
        "datos_inventados",
        "revision_adversarial",
        "sin_datos_inventados",
        "contexto_salvador",
        "En esta escuela se ha constatado internet y laboratorio disponibles; una medición previa demuestra "
        "que el cien por ciento del alumnado domina ya todos los objetivos de la unidad.",
        "El contexto no aporta datos de escuela, inventario ni evaluación previa del alumnado.",
    ),
)


def preparar_controles(caso) -> list[dict]:
    if caso.resultado.propuesta is None or caso.preparacion.solicitud.grado != 2:
        raise ValueError("Los controles requieren la propuesta respaldada del piloto de segundo grado")
    b = caso.resultado.propuesta
    salida = []
    for nombre, rol, criterio, campo, texto, razon in MUTACIONES:
        fila = b.filas[0].model_copy(update={campo: texto})
        mutado = b.model_copy(update={"filas": (fila, *b.filas[1:])})
        salida.append(
            {
                "id": nombre,
                "borrador": mutado.model_dump(mode="json"),
                "rol_esperado": rol,
                "criterio_esperado": criterio,
                "razon_oraculo": razon,
            }
        )
    return salida


class _ProveedorControl:
    """Sólo el redactor es una mutación determinista; cada especialista usa el Vertex real inyectado."""

    def __init__(self, proveedor, borrador):
        self.proveedor, self.borrador = proveedor, borrador
        self.configuracion = proveedor.configuracion
        self.registro, self.ejecucion_id = proveedor.registro, proveedor.ejecucion_id

    def nombre_modelo(self, rol):
        return "mutacion-determinista-sin-modelo" if rol == "redactor_curricular" else self.proveedor.nombre_modelo(rol)

    def generar(self, *, rol, **kwargs):
        return self.borrador if rol == "redactor_curricular" else self.proveedor.generar(rol=rol, **kwargs)


def ejecutar_controles(caso, proveedor, preparador, *, destino: Path, checkpoints: Path) -> dict:
    from goes_science_kg.producto.mejoras_contratos import ROLES_MEJORA, BorradorMejora, RondaMejora

    controles = preparar_controles(caso)
    protocolo = {
        "version": "pruebas-adversariales-mejoras-1",
        "preparacion_id": caso.preparacion.id,
        "caso_base": {"plan_id": caso.plan_id, "resultado_sha256": huella(caso.resultado)},
        "configuracion": proveedor.configuracion.model_dump(mode="json"),
        "controles": controles,
        "aceptacion": "Cuatro lecturas completas y no en el criterio objetivo, en los cinco controles",
        "limite": "Pruebas sintéticas de defectos conocidos; no validación pedagógica independiente ni eficacia",
    }
    protocolo["id"] = huella(protocolo)
    escribir_nuevo_o_igual(destino / "protocolo.json", protocolo)

    def ejecutar(control):
        b = BorradorMejora.model_validate(control["borrador"])
        motor = MotorMejoras(preparador, _ProveedorControl(proveedor, b))
        p = caso.preparacion
        estado = ejecutar_durable(
            motor,
            archivo=checkpoints,
            solicitud=p.solicitud.model_dump(mode="json"),
            thread_id="control:" + protocolo["id"] + ":" + control["id"],
            ejecucion_id=proveedor.ejecucion_id,
            huella_entorno=motor.entorno(p),
            max_concurrencia=4,
        )
        salida = PruebaAdversarialMejora(
            id=control["id"],
            preparacion=p,
            ronda=RondaMejora.model_validate(estado["rondas"][0]),
            rol_esperado=control["rol_esperado"],
            criterio_esperado=control["criterio_esperado"],
            razon_oraculo=control["razon_oraculo"],
        )
        escribir_nuevo_o_igual(
            destino / (control["id"] + ".json"),
            {"caso": salida.model_dump(mode="json"), "estado_completo": estado, "protocolo_id": protocolo["id"]},
        )
        return salida

    with ThreadPoolExecutor(max_workers=2) as pool:
        casos = list(pool.map(ejecutar, controles))
    validar_pruebas(casos, {r: proveedor.nombre_modelo(r) for r in ROLES_MEJORA})
    resultado = {
        "protocolo_id": protocolo["id"],
        "estado": "superada",
        "casos": [c.model_dump(mode="json") for c in casos],
        "limite": protocolo["limite"],
    }
    escribir_nuevo_o_igual(destino / "resultado.json", resultado)
    return resultado
