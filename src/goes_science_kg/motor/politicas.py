"""Permisos calculados por componente: consulta, autoría asistida y aula deshabilitada en v0.1."""

from __future__ import annotations

from goes_science_kg.aprendizaje.paquete import _datos_que_faltan, _hace_falta_un_dato
from goes_science_kg.motor.archivos import canonico
from goes_science_kg.motor.contrato import Calidad, Usos

INSTRUCCIONES = ("enunciado", "opciones", "retroalimentacion", "explicacion", "procedimiento", "datos_esperados",
                "analisis", "refuerzo", "materiales", "rubrica")


def calidad(elemento: dict, estado_panel: dict | None) -> Calidad:
    """El detector de datos es un aviso, nunca una certificación de ausencia de dependencias."""
    x = estado_panel or {}
    texto = canonico({k: elemento[k] for k in INSTRUCCIONES if k in elemento})
    pide = _hace_falta_un_dato(texto)
    return Calidad(estado_original=elemento.get("estado", "sin_estado"), estado_panel=x.get("estado"),
                   solidez=(x.get("bucle") or {}).get("solidez"), revisado_por=elemento.get("revisado_por") or None,
                   estado_datos="pendiente" if pide else "no_evaluado",
                   datos_por_localizar=_datos_que_faltan([{"id": elemento["id"], "texto": texto}]) if pide else [])


def usos(tipo: str, contenido: dict, c: Calidad) -> Usos:
    motivos = []
    if c.estado_original not in ("revisado_panel", "verificado"):
        motivos.append("contenido_sin_revision_favorable")
    if c.estado_panel != "resuelta":
        motivos.append("panel_sin_resolucion_favorable")
    if c.solidez in ("fragil", "sin_consenso", "en_bucle") or contenido.get("confianza") == "baja":
        motivos.append("evidencia_o_consenso_insuficiente")
    if tipo == "refuerzo":
        if contenido.get("decision") != "inyectar":
            motivos.append("propuesta_descartada")
        if c.solidez not in ("solido", "respaldado"):
            motivos.append("refuerzo_sin_bucle_suficiente")
    pendientes = ["aula_no_habilitada_en_contrato_inicial"]
    if not c.revisado_por or c.estado_original != "verificado":
        pendientes.append("sin_verificacion_humana")
    if c.estado_datos not in ("verificado", "no_requiere"):
        pendientes.append("datos_por_verificar")
    if c.solidez not in ("solido", "respaldado"):
        pendientes.append("revision_adversarial_pendiente")
    if tipo in ("actividad", "experimento"):
        pendientes.append("viabilidad_didactica_y_temporal_por_verificar")
    if tipo == "refuerzo":
        pendientes.append("propuesta_goes_sin_adopcion_institucional")
        if contenido.get("forma") == "fila_nueva":
            pendientes.append("presupuesto_de_sesion_adicional_por_validar")
    return Usos(autoria=not motivos, motivos_autoria=motivos, pendientes_aula=pendientes)


def propagar_dependencias(componentes: dict) -> None:
    """Una explicación no habilita automáticamente una práctica o dificultad requerida que sigue bloqueada."""
    for _ in range(len(componentes) + 1):
        cambio = False
        for c in componentes.values():
            if c.usos.autoria and any(not componentes[i].usos.autoria for i in c.componentes_requeridos):
                c.usos.autoria = False
                c.usos.motivos_autoria.append("componente_requerido_no_apto_para_autoria")
                cambio = True
        if not cambio:
            break
