"""Render original and proposed curricula with their evidence and review history."""

import html
from importlib.resources import files
from string import Template
from urllib.parse import urlsplit

from goes_science_kg.curriculo.contratos import FASES

CAMPOS_VISTA = (
    "objetivo_propuesto",
    "indicador_observable",
    "producto_evaluable",
    "criterio_evaluacion",
    "orientacion_didactica",
    "recursos_condicionales",
    "seguridad",
    "andamiaje",
    "contexto_salvador",
    "justificacion",
)
ESTADOS = {
    "respaldado_automaticamente": "Respaldada automáticamente",
    "no_respaldado": "Requiere corrección",
    "abstencion": "Evidencia insuficiente",
}


def h(valor):
    """Escape source values before interpolating them into the offline HTML view."""

    return html.escape(str(valor), quote=True)


def _cantidad(numero, singular, plural=None):
    return f"{numero} {singular if numero == 1 else plural or singular + 's'}"


def _fuente_legible(evidencia):
    fuente = evidencia.fuente
    nombre = fuente.get("titulo") or fuente.get("documento", "Fuente primaria").replace("_", " ")
    partes = [str(nombre)]
    for clave, etiqueta in (("pagina", "página PDF"), ("hoja", "hoja"), ("banda_nativa", "banda nativa")):
        if fuente.get(clave):
            partes.append(f"{etiqueta}: {fuente[clave]}")
    if fuente.get("celdas"):
        partes.append("celdas: " + ", ".join(fuente["celdas"]))
    if fuente.get("version_documental"):
        partes.append(str(fuente["version_documental"]))
    texto = h(" · ".join(partes))
    url = fuente.get("url") or fuente.get("url_documento")
    if isinstance(url, str):
        try:
            p = urlsplit(url)
            if p.scheme == "https" and p.hostname and not p.username and not p.password:
                return f'<a href="{h(url)}" rel="noopener noreferrer">{texto}</a>'
        except ValueError:
            pass
    return texto


def _fila(f, original, p):
    campos = []
    for c in CAMPOS_VISTA:
        valor = "; ".join(getattr(f, c)) if c == "recursos_condicionales" else getattr(f, c)
        campos.append(f"<dt>{h(c.replace('_', ' '))}</dt><dd>{h(valor)}</dd>")
    citas = {x.id: x for x in p.fragmentos}
    fuentes = {e.id: e for e in p.evidencias}
    pruebas = []
    for id_ in f.fragmentos_ids:
        cita = citas[id_]
        pruebas.append(f"<li>{h(cita.literal)} <small>— {_fuente_legible(fuentes[cita.evidencia_id])}</small></li>")
    evaluacion_original = "".join(
        f"<dt>{h(nombre)}</dt><dd>{h(original.get(campo) or 'No declarado en el insumo')}</dd>"
        for campo, nombre in (
            ("indicadores_logro", "Indicadores originales"),
            ("evidencia_aprendizaje", "Evidencia original"),
        )
    )
    fases_originales = []
    for fase in FASES:
        etapa = original["fases"][fase]
        texto = etapa["texto"] if etapa["presente_en_hoja"] else "Ausente en el insumo"
        fases_originales.append(f"<dt>{h(fase.title())}</dt><dd>{h(texto)}</dd>")
    fases = "".join(fases_originales)
    return (
        f"<details><summary>{h(original['procedimental'])}</summary>"
        f"<p>Acción: {h(f.accion)} · {h(', '.join(f.disciplinas_propuestas))}</p>"
        "<details><summary>Evaluación y fases originales</summary><dl>"
        + evaluacion_original
        + fases
        + "</dl></details>"
        "<dl>" + "".join(campos) + "</dl><h4>Fragmentos seleccionados</h4><ul>" + "".join(pruebas) + "</ul>"
        f"<small>Fuente original: {h(original['hoja'])} · fila {h(original['fila'])}</small></details>"
    )


def _unidad(caso):
    p, r = caso.preparacion, caso.resultado
    originales = {f["id"]: f for f in p.filas_originales}
    contenido = (
        "".join(_fila(f, originales[f.fila_id], p) for f in r.propuesta.filas)
        if r.propuesta
        else ("<ul>" + "".join(f"<li>{h(m)}</li>" for m in r.motivos) + "</ul>")
    )
    revisiones = []
    for n, ronda in enumerate(r.rondas):
        for d in ronda.dictamenes:
            resultado = "Fallo: " + d.error if d.error else str(d.lectura.criterios) if d.lectura else "Sin lectura"
            revisiones.append(f"<li>Ronda {n + 1} · {h(d.rol)}: {h(resultado)}</li>")
    enmiendas = []
    for e in p.correcciones_requeridas:
        estado = "Aceptada por los cuatro especialistas" if r.propuesta else "Pendiente de respaldo completo"
        enmiendas.append(
            f"<details><summary>Enmienda: {h(e['hoja'])} {h(e['celda_ancla'])}</summary>"
            f"<p>{estado}</p><p><b>Original:</b> {h(e['antes'])}</p>"
            f"<p><b>Propuesta:</b> {h(e['despues'])}</p></details>"
        )
    return (
        f'<section data-grado="{p.solicitud.grado}" data-estado="{h(r.estado)}">'
        f"<h2>{h(p.solicitud.asignatura_malla)} · {p.solicitud.grado}.º · {h(p.solicitud.unidad)}</h2>"
        f'<p class="estado">{ESTADOS[r.estado]} · {_cantidad(len(p.filas_originales), "fila")}</p>'
        + contenido
        + "".join(enmiendas)
        + "<details><summary>Revisiones y trazabilidad</summary><ul>"
        + "".join(revisiones)
        + f"</ul><code>{h(p.id)}</code></details></section>"
    )


def vista_mejoras(curriculo, archivo) -> str:
    """Render the complete original-versus-proposal view with evidence and review history."""

    progresiones = []
    for e in archivo.progresiones["catalogo"]["expectativas"]:
        progresiones.append(
            f"<li><b>{h(e['titulo'])} · {h(e['banda'])}</b>: "
            + h(archivo.progresiones["evidencias"][e["id"]]["texto"])
            + f"<small> — {h(e['fuente'])} · PDF {e['pagina_pdf']}</small></li>"
        )
    c = archivo.cobertura
    alcance = (
        f'<p>{h(archivo.limite)}</p><p class="cobertura">{_cantidad(c["unidades"], "unidad", "unidades")} · '
        f"{_cantidad(c['filas'], 'fila original', 'filas originales')} · "
        f"{_cantidad(c['filas_respaldadas'], 'fila')} con propuesta respaldada</p>"
    )
    plantilla = files("goes_science_kg.producto").joinpath("plantillas/mejoras.html").read_text(encoding="utf-8")
    return Template(plantilla).substitute(
        alcance=alcance,
        grados="".join(f"<option>{g}</option>" for g in sorted({f.grado for f in curriculo.filas})),
        tarjetas="".join(_unidad(c) for c in archivo.unidades),
        progresiones="".join(progresiones),
        archivo_id=h(archivo.id),
    )
