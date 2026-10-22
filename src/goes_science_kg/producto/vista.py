"""Explorador local del currículo: datos citables, filtros y exportación sin red."""

from __future__ import annotations

import html
import json
import re
from typing import TYPE_CHECKING
from urllib.parse import urlsplit

from goes_science_kg.curriculo.contratos import FASES, Curriculo, FilaCurricular

if TYPE_CHECKING:
    from goes_science_kg.curriculo.catalogacion import CatalogoDisciplinas

DISCIPLINAS = {
    "biologia": "Biología",
    "fisica": "Física",
    "quimica": "Química",
    "ciencias_tierra_espacio": "Tierra y espacio",
}
DECLARADAS = {nombre: codigo for codigo, nombre in DISCIPLINAS.items()}
DECLARADAS.update({codigo: codigo for codigo in DISCIPLINAS})
DECLARADAS["Ciencias de la Tierra y del Espacio"] = "ciencias_tierra_espacio"
ESTADOS = {
    "declarado_malla": "Declarada en la malla",
    "coincidencia_automatica": "Consenso automático",
    "abstencion": "Abstención",
    "fuera_alcance": "Fuera del alcance disciplinar",
    "sin_clasificar": "Sin clasificación",
}
CAMPOS = (
    (
        "Aprendizaje",
        (
            ("procedimental", "Objetivo procedimental"),
            ("subcontenido", "Subcontenidos"),
            ("indicador_avanzado", "Indicador avanzado"),
            ("indicadores_logro", "Indicadores de logro"),
            ("evidencia_aprendizaje", "Evidencia de aprendizaje"),
        ),
    ),
    (
        "Marcos declarados por el insumo",
        (
            ("competencia_pisa", "Competencia PISA declarada"),
            ("conocimiento_pisa", "Conocimiento PISA declarado"),
            ("contexto_pisa", "Contexto PISA declarado"),
            ("habilidad_timss", "Habilidad TIMSS declarada"),
            ("competencia_men", "Competencia marco MEN, según la malla"),
        ),
    ),
    (
        "Actividad y contexto",
        (
            ("eje_integrador", "Eje integrador"),
            ("actitudinal", "Actitudinal"),
            ("habilidad_siglo_xxi", "Habilidad del siglo XXI"),
            ("competencia_digital", "Competencia digital declarada"),
            ("actividad_digital", "Actividad digital e IA"),
            ("habilidad_transversal", "Habilidad transversal"),
            ("dominio_clave", "Dominio clave"),
            ("notacion", "Notación"),
            ("notas", "Notas de la fila"),
        ),
    ),
)
AUSENTE = "No declarado en el insumo."
LIMITE = (
    "Esta vista conserva declaraciones y actividades de la V4. La clasificación disciplinar "
    "no acredita corrección científica, alineación internacional, cobertura ni eficacia educativa."
)


def _url_web(valor: object) -> str:
    """Solo permite enlaces HTTPS; el texto original nunca se usa como HTML."""
    if not isinstance(valor, str) or re.search(r"[\s\x00-\x1f\x7f]", valor):
        return ""
    try:
        partes = urlsplit(valor)
        if partes.scheme == "https" and partes.hostname and not partes.username and not partes.password:
            return valor
    except ValueError:
        pass
    return ""


def _nombre_archivo(valor: object) -> str:
    return str(valor or "").replace("\\", "/").rsplit("/", 1)[-1]


def _aplica_referencia(referencia: dict, fila: FilaCurricular, encabezados: set[str]) -> bool:
    if referencia.get("hoja") != fila.hoja:
        return False
    propias = {c.coordenada for c in fila.celdas}
    propias.update(c.origen_combinado for c in fila.celdas if c.origen_combinado)
    celdas = referencia.get("celdas", [])
    if isinstance(celdas, list):
        for coordenada in celdas:
            if not isinstance(coordenada, str):
                continue
            if coordenada in propias or coordenada in encabezados:
                return True
    rango = referencia.get("rango", "")
    limites = re.fullmatch(r"([A-Z]+)([1-9][0-9]*):([A-Z]+)([1-9][0-9]*)", str(rango))
    if not limites:
        return False

    def columna(nombre: str) -> int:
        indice = 0
        for letra in nombre:
            indice = 26 * indice + ord(letra) - ord("A") + 1
        return indice

    for coordenada in propias:
        celda = re.fullmatch(r"([A-Z]+)([1-9][0-9]*)", coordenada)
        if (
            celda
            and columna(limites[1]) <= columna(celda[1]) <= columna(limites[3])
            and int(limites[2]) <= int(celda[2]) <= int(limites[4])
        ):
            return True
    return False


def _alertas(curriculo: Curriculo, documento: dict | None) -> tuple[list[dict], dict[str, list[int]]]:
    registros = (documento or {}).get("alertas", [])
    if not isinstance(registros, list):
        raise ValueError("El registro de alertas debe contener una lista de alertas")
    fuentes = {f.id: f for f in curriculo.fuentes}
    encabezados = {
        (h.fuente_id, h.nombre): {f"{c.columna}{fila}" for c in h.columnas for fila in h.filas_encabezado}
        for h in curriculo.hojas
    }
    asociadas: dict[str, list[int]] = {fila.id: [] for fila in curriculo.filas}
    salida = []
    for original in registros:
        if not isinstance(original, dict) or not isinstance(original.get("fuente"), dict):
            raise ValueError("Cada alerta debe conservar su referencia de fuente")
        referencia = original["fuente"]
        contraste = original.get("contraste_documental", [])
        referencias = [referencia] + (
            [r for r in contraste if isinstance(r, dict)] if isinstance(contraste, list) else []
        )
        indice = len(salida)
        coincidencia = False
        for fila in curriculo.filas:
            fuente = fuentes[fila.fuente_id]
            identidad = (
                referencia.get("sha256") == fuente.sha256
                and _nombre_archivo(referencia.get("archivo")) == fuente.archivo
            )
            if not identidad:
                continue
            coincidencia = True
            filas_encabezado = encabezados.get((fila.fuente_id, fila.hoja), set())
            if any(_aplica_referencia(r, fila, filas_encabezado) for r in referencias):
                asociadas[fila.id].append(indice)
        salida.append(
            {
                "id": str(original.get("id", f"Alerta {indice + 1}")),
                "clase": str(original.get("clase", "Sin clase declarada")),
                "severidad": str(original.get("severidad", "No declarada")),
                "estado": str(original.get("estado_verificacion", "pendiente")),
                "explicacion": str(original.get("explicacion", "")),
                "ancla": str(original.get("ancla_original", "")),
                "limite": str(original.get("limite", "")),
                "fuente": referencia,
                "contraste": referencias[1:],
                "url": _url_web(original.get("url_primaria_contraste")),
                "coincide_captura": coincidencia,
            }
        )
    return salida, asociadas


def _datos(curriculo: Curriculo, catalogo: CatalogoDisciplinas | None, alertas: dict | None) -> dict:
    fuentes = {fuente.id: fuente for fuente in curriculo.fuentes}
    if len(fuentes) != len(curriculo.fuentes) or len({f.id for f in curriculo.filas}) != len(curriculo.filas):
        raise ValueError("La vista requiere identidades de fuentes y filas únicas")
    if any(f.fuente_id not in fuentes for f in curriculo.filas):
        raise ValueError("Una fila referencia una fuente ausente")
    if any(f.version != curriculo.version for f in (*curriculo.fuentes, *curriculo.filas)):
        raise ValueError("La captura mezcla versiones curriculares")
    decisiones = {}
    if catalogo is not None:
        if catalogo.version_curriculo != curriculo.version or catalogo.huella_curriculo != curriculo.huella:
            raise ValueError("El catálogo disciplinar pertenece a otra versión o captura")
        decisiones = {d.fila_id: d for d in catalogo.filas}
        if len(decisiones) != len(catalogo.filas) or set(decisiones) - {f.id for f in curriculo.filas}:
            raise ValueError("El catálogo repite filas o referencia filas ajenas al currículo")
    registro_alertas, por_fila = _alertas(curriculo, alertas)
    filas = []
    claves = [clave for _, campos in CAMPOS for clave, _ in campos]

    def orden(fila: FilaCurricular) -> tuple:
        unidad = re.sub(r"\d+", lambda n: f"{int(n[0]):09}", fila.unidad.casefold())
        return fila.grado, fila.asignatura_malla, unidad, fila.hoja, fila.fila

    for fila in sorted(curriculo.filas, key=orden):
        fuente = fuentes[fila.fuente_id]
        ficha = fuente.procedencia.get("archivo", {})
        url = ficha.get("url", "") if isinstance(ficha, dict) else ""
        url = url or fuente.procedencia.get("url", "")
        decision = decisiones.get(fila.id)
        declarada = DECLARADAS.get(fila.asignatura_malla)
        if decision is not None:
            clasificacion = {
                "estado": decision.estado,
                "disciplinas": list(decision.disciplinas),
                "metodo": {
                    "asignatura_explicita_del_libro": "Asignatura declarada en el libro curricular",
                    "dos_lecturas_independientes": "Dos lecturas separadas de modelos",
                }.get(decision.metodo, decision.metodo.replace("_", " ")),
                "justificacion": decision.justificacion,
                "errores": list(decision.errores),
            }
        else:
            clasificacion = {
                "estado": "declarado_malla" if declarada else "sin_clasificar",
                "disciplinas": [declarada] if declarada else [],
                "metodo": "Asignatura explícita del insumo" if declarada else "Sin decisión disciplinar",
                "justificacion": "No se infiere una disciplina desde el tema ni desde códigos PISA/TIMSS.",
                "errores": [],
            }
        filas.append(
            {
                "id": fila.id,
                "grado": fila.grado,
                "asignatura_malla": fila.asignatura_malla,
                "unidad": fila.unidad,
                "contenido": fila.contenido,
                "origen": fila.origen_contenido,
                "numero_tema": fila.numero_tema,
                "numero_clase": fila.numero_clase,
                **{clave: getattr(fila, clave) for clave in claves},
                "clasificacion": clasificacion,
                "fuente": {
                    "id": fuente.id,
                    "version": fuente.version,
                    "archivo": fuente.archivo,
                    "sha256": fuente.sha256,
                    "hoja": fila.hoja,
                    "fila": fila.fila,
                    "drive_url": _url_web(url),
                    "url_declarada": str(url),
                },
                "celdas": [
                    {
                        "coordenada": c.coordenada,
                        "campo": c.campo or "Sin rol lógico",
                        "origen": c.origen_combinado or "",
                    }
                    for c in fila.celdas
                ],
                "fases": [
                    {
                        "nombre": fase,
                        "presente": fila.fases[fase].presente_en_hoja,
                        "texto": fila.fases[fase].texto,
                        "codigos": list(fila.fases[fase].codigos_locales),
                        "celdas": list(fila.fases[fase].coordenadas),
                    }
                    for fase in FASES
                ],
                "alertas": por_fila[fila.id],
            }
        )
    return {
        "version": curriculo.version,
        "huella": curriculo.huella,
        "fuentes": len(fuentes),
        "hojas": len(curriculo.hojas),
        "avisos": list(curriculo.avisos),
        "catalogo": catalogo is not None,
        "alertas_cargadas": alertas is not None,
        "limite_catalogo": str(getattr(catalogo, "limites", "")) if catalogo is not None else "",
        "limite": LIMITE,
        "disciplinas": DISCIPLINAS,
        "estados": ESTADOS,
        "campos": CAMPOS,
        "filas": filas,
        "alertas": registro_alertas,
    }


def _md(valor: object) -> str:
    texto = html.escape(str(AUSENTE if valor is None or valor == "" else valor), quote=True)
    return re.sub(r"([\\`*_{}\[\]()<>#+\-.!|])", r"\\\1", texto)


def _markdown_fila(fila: dict, datos: dict) -> str:
    fuente = fila["fuente"]
    clasificacion = fila["clasificacion"]
    lineas = [
        f"## {_md(fila['grado'])}.° · {_md(fila['contenido'])}",
        f"**Unidad:** {_md(fila['unidad'])}",
        f"**Asignatura de la malla:** {_md(fila['asignatura_malla'])}",
        f"**Origen declarado:** {_md(fila['origen'])}",
        f"**Tema / clase del insumo:** {_md(fila['numero_tema'])} / {_md(fila['numero_clase'])}",
        f"**Clasificación:** {_md(ESTADOS.get(clasificacion['estado'], clasificacion['estado']))}",
        f"**Disciplinas:** {_md(', '.join(DISCIPLINAS[d] for d in clasificacion['disciplinas']))}",
        f"**Método:** {_md(clasificacion['metodo'])}",
        f"**Justificación:** {_md(clasificacion['justificacion'])}",
    ]
    for grupo, campos in CAMPOS:
        lineas.append(f"### {grupo}")
        for clave, etiqueta in campos:
            lineas.append(f"**{etiqueta}:** {_md(fila[clave])}")
    lineas.append("### Secuencia didáctica del insumo")
    for fase in fila["fases"]:
        estado = "Columna presente" if fase["presente"] else "Ausente en esta hoja"
        lineas.extend(
            [
                f"**{fase['nombre'].capitalize()} — {estado}:** {_md(fase['texto'])}",
                f"Códigos locales: {_md(', '.join(fase['codigos']))}",
                f"Celdas: {_md(', '.join(fase['celdas']))}",
            ]
        )
    lineas.extend(
        [
            "### Fuente y trazabilidad",
            f"**ID de fila:** {_md(fila['id'])}",
            f"**Archivo:** {_md(fuente['archivo'])}",
            f"**Versión:** {_md(fuente['version'])}",
            f"**Hoja:** {_md(fuente['hoja'])}",
            f"**Fila física:** {fuente['fila']}",
            f"**SHA-256:** {fuente['sha256']}",
            f"**URL declarada del original:** {_md(fuente['url_declarada'])}",
        ]
    )
    for celda in fila["celdas"]:
        origen = f"; ancla combinada {celda['origen']}" if celda["origen"] else ""
        lineas.append(f"- {_md(celda['coordenada'])}: {_md(celda['campo'] + origen)}")
    lineas.append("### Alertas localizadas")
    if not datos["alertas_cargadas"]:
        lineas.append("No se cargó un registro de alertas.")
    elif not fila["alertas"]:
        lineas.append("No se localizaron alertas del registro cargado; esto no certifica la fila.")
    for indice in fila["alertas"]:
        alerta = datos["alertas"][indice]
        lineas.extend(
            [
                f"**{_md(alerta['id'])} · {_md(alerta['estado'])} · {_md(alerta['severidad'])}**",
                _md(alerta["explicacion"]),
                f"Alcance: {_md(alerta['limite'])}",
                f"Contraste: {_md(alerta['url'])}",
            ]
        )
    return "\n\n".join(lineas)


def markdown(
    curriculo: Curriculo,
    catalogo: CatalogoDisciplinas | None = None,
    alertas: dict | None = None,
    *,
    fila_id: str | None = None,
) -> str:
    """Exporta la captura o una ficha, escapando el contenido original como texto."""
    datos = _datos(curriculo, catalogo, alertas)
    filas = datos["filas"] if fila_id is None else [f for f in datos["filas"] if f["id"] == fila_id]
    if fila_id is not None and not filas:
        raise ValueError("La fila solicitada no pertenece al currículo")
    cabecera = f"# Revisión curricular {_md(datos['version'])}\n\n{LIMITE}\n\nCaptura: {datos['huella']}"
    return cabecera + "\n\n" + "\n\n---\n\n".join(_markdown_fila(f, datos) for f in filas) + "\n"


def vista(
    curriculo: Curriculo,
    catalogo: CatalogoDisciplinas | None = None,
    alertas: dict | None = None,
) -> str:
    """Devuelve HTML autónomo sin peticiones de red ni interpolación HTML de datos."""
    datos = json.dumps(_datos(curriculo, catalogo, alertas), ensure_ascii=False, separators=(",", ":"))
    for caracter, escape in (
        ("&", "\\u0026"),
        ("<", "\\u003c"),
        (">", "\\u003e"),
        ("\u2028", "\\u2028"),
        ("\u2029", "\\u2029"),
    ):
        datos = datos.replace(caracter, escape)
    return _HTML.replace("__DATOS_CURRICULARES__", datos, 1)


_HTML = r"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy"
 content="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline';
 connect-src 'none'; base-uri 'none'; form-action 'none'">
<title>GOES · Explorador curricular V4</title>
<style>
:root{color-scheme:light;--bosque:#173f32;--hoja:#2c634b;--fondo:#f3f4ee;--borde:#d2d9cf;
 --tinta:#23342b;--suave:#536359;--ambar:#805313;--papel:#fff;--rojo:#8b302b}
*{box-sizing:border-box}body{margin:0;background:var(--fondo);color:var(--tinta);
 font:15px/1.55 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
button,input,select{font:inherit}button,select{cursor:pointer}button{min-height:42px}
a{color:var(--hoja);text-underline-offset:3px}a:hover{text-decoration-thickness:2px}
:focus-visible{outline:3px solid #a35c18;outline-offset:3px}
.saltar{position:absolute;left:16px;top:-70px;background:white;padding:10px;z-index:5}
.saltar:focus{top:8px}header{background:var(--bosque);color:#f4f5e9;padding:30px max(24px,4vw)}
.marca{font-size:12px;font-weight:750;letter-spacing:.16em;text-transform:uppercase}
.cabecera{display:flex;align-items:end;justify-content:space-between;gap:24px;flex-wrap:wrap}
h1{font-size:clamp(27px,3vw,40px);line-height:1.12;margin:12px 0 10px;font-weight:650}
header p{margin:0;max-width:750px;color:#dce7dc}.captura{font-size:12px;color:#d0dfd0}
.contenedor{max-width:1600px;margin:auto;padding:24px max(20px,3vw) 48px}
.contexto{display:flex;gap:16px;justify-content:space-between;align-items:start;margin-bottom:20px}
.limite{font-size:13px;color:var(--suave);max-width:900px;margin:0}.acciones{display:flex;gap:8px;flex-wrap:wrap}
button{border:1px solid var(--borde);background:white;color:var(--bosque);border-radius:8px;
 padding:9px 14px;font-weight:650}button:hover{background:#e9eee4}button:disabled{opacity:.5;cursor:default}
.principal{background:var(--bosque);color:white;border-color:var(--bosque)}.principal:hover{background:#285b46}
.filtros{display:grid;grid-template-columns:120px minmax(170px,1fr) minmax(200px,1.1fr)
 minmax(200px,1.3fr) auto;gap:14px;padding:20px;background:white;border:1px solid var(--borde);border-radius:12px}
label{display:block;font-size:12px;font-weight:750;margin-bottom:6px;color:var(--suave)}
select,input{width:100%;min-height:44px;border:1px solid #a8b6a8;border-radius:7px;padding:9px;background:white;
 color:var(--tinta)}.restablecer{align-self:end}.estado{font-size:13px;color:var(--suave);margin:14px 0}
.explorador{display:grid;grid-template-columns:minmax(260px,330px) minmax(0,1fr);gap:22px;align-items:start}
.lista-panel,.ficha{background:white;border:1px solid var(--borde);border-radius:12px;overflow:hidden}
.lista-cabecera{padding:16px 18px;border-bottom:1px solid var(--borde)}
.lista-cabecera h2{font-size:15px;margin:0}.lista{max-height:72vh;overflow:auto;padding:8px}
.fila-boton{display:block;text-align:left;width:100%;border:0;border-bottom:1px solid #e8ece5;
 border-radius:5px;padding:14px 12px;font-weight:400;margin:2px 0}
.fila-boton[aria-pressed="true"]{background:#e6eee1;box-shadow:inset 4px 0 var(--hoja)}
.fila-titulo{font-weight:650;display:block;line-height:1.4}.fila-contexto{display:block;font-size:12px;
 color:var(--suave);margin-top:5px}.cargar{margin:12px;width:calc(100% - 24px)}
.ficha{padding:24px 28px}.ficha h2{font-size:27px;line-height:1.2;margin:12px 0}
.ficha h3{font-size:17px;margin:28px 0 12px}.ficha h4{font-size:14px;margin:0 0 7px}
.etiquetas{display:flex;flex-wrap:wrap;gap:7px}.etiqueta{display:inline-block;border-radius:5px;
 background:#edf1e7;color:var(--bosque);padding:4px 8px;font-size:12px;font-weight:650}
.advertencia{background:#fff3d9;color:#6f480d}.peligro{background:#fbeae5;color:var(--rojo)}
.metadato{font-size:13px;color:var(--suave);overflow-wrap:anywhere}.texto{white-space:pre-wrap;
 overflow-wrap:anywhere;margin:5px 0 16px}.vacio{color:#67756b;font-style:italic}
.campo{border-bottom:1px solid #edf0e9;padding:8px 0}.campo dt{font-size:12px;font-weight:750;color:var(--suave)}
.campo dd{margin:5px 0 8px;white-space:pre-wrap;overflow-wrap:anywhere}dl{margin:0}
.fases{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px}
.fase{border:1px solid var(--borde);border-radius:8px;padding:15px;background:#fafbf7}
.fase-ausente{border-style:dashed;background:#f6f5ef}.fase .texto{font-size:14px}
details{border-top:1px solid var(--borde);padding:15px 0}summary{cursor:pointer;font-weight:650}
.alerta{padding:16px;border-left:4px solid #a06a26;background:#fff8e9;border-radius:5px;margin:12px 0}
.alerta p{margin:8px 0}.fuente{background:#f4f6f0;border-radius:9px;padding:18px;margin-top:18px}
.fuente h3{margin-top:0}.tabla-contenedor{overflow:auto}table{border-collapse:collapse;width:100%;font-size:12px}
caption{text-align:left;padding:10px 0;color:var(--suave)}th,td{text-align:left;padding:8px;border-bottom:1px solid
 var(--borde);overflow-wrap:anywhere}th{font-weight:700}.documentales{margin-top:24px}
.sin-resultados{padding:20px;color:var(--suave)}footer{margin-top:28px;font-size:12px;color:var(--suave);
 overflow-wrap:anywhere}
@media(max-width:1000px){.filtros{grid-template-columns:1fr 1fr}.contexto{display:block}.acciones{margin-top:14px}
 .explorador{grid-template-columns:270px minmax(0,1fr)}.ficha{padding:20px}}
@media(max-width:720px){header{padding:24px 20px}.contenedor{padding:18px 14px 35px}
 .explorador{grid-template-columns:1fr}.lista{max-height:310px}.ficha{padding:20px 17px}
 .ficha h2{font-size:23px}.fases{grid-template-columns:1fr}.filtros{padding:16px;gap:12px}
 .filtros .busqueda{grid-column:1/-1}.restablecer{grid-column:1/-1}.acciones button{flex:1}}
@media print{header{background:white;color:black}.captura,header p{color:black}.filtros,.lista-panel,
 .acciones,.documentales,.saltar{display:none}.explorador{display:block}.ficha{border:0}.contenedor{padding:0}}
</style>
</head>
<body>
<a class="saltar" href="#filtros">Ir a los filtros del currículo</a>
<header><div class="cabecera"><div><div class="marca">GOES / Ciencias</div>
<h1>Explorador curricular</h1><p>Revisa aprendizajes, secuencias y evidencias de la V4 con su fuente original.</p>
</div><div id="captura" class="captura"></div></div></header>
<main class="contenedor">
<div class="contexto"><p id="limite" class="limite"></p><div class="acciones">
<button id="exportar-filtro" class="principal" type="button">Exportar selección · MD</button>
<button id="exportar-ficha" type="button">Exportar ficha · MD</button></div></div>
<form id="filtros" class="filtros" aria-label="Filtrar currículo">
<div><label for="grado">Grado</label><select id="grado"></select></div>
<div><label for="disciplina">Disciplina o malla</label><select id="disciplina"></select></div>
<div><label for="unidad">Unidad</label><select id="unidad"></select></div>
<div class="busqueda"><label for="buscar">Buscar en las filas</label>
<input id="buscar" type="search" placeholder="Contenido, objetivo, evidencia o fuente" autocomplete="off"></div>
<button id="restablecer" class="restablecer" type="button">Restablecer</button>
</form>
<p id="estado" class="estado" role="status" aria-live="polite"></p>
<div class="explorador"><section class="lista-panel" aria-labelledby="titulo-lista">
<div class="lista-cabecera"><h2 id="titulo-lista">Filas del insumo</h2></div>
<div id="lista" class="lista"></div><button id="cargar" class="cargar" type="button">Mostrar más filas</button>
</section><article id="ficha" class="ficha" tabindex="-1" aria-label="Ficha de la fila seleccionada"></article></div>
<details class="documentales"><summary id="titulo-alertas">Registro documental de alertas</summary>
<p class="metadato">Se conservan también las alertas sin una fila localizada en esta captura.</p>
<div id="alertas-documentales"></div></details>
<details><summary>Avisos de la captura</summary><div id="avisos"></div></details>
<footer id="pie"></footer>
<noscript>Esta página funciona sin conexión.
Activa JavaScript para filtrar y exportar sus datos incorporados.</noscript>
</main>
<script id="datos-curriculares" type="application/json">__DATOS_CURRICULARES__</script>
<script>
"use strict";
(() => {
 const datos = JSON.parse(document.getElementById("datos-curriculares").textContent);
 const $ = id => document.getElementById(id);
 const ausente = "No declarado en el insumo.";
 const texto = valor => String(valor === undefined || valor === null || valor === "" ? ausente : valor);
 const crear = (tag, contenido, clase) => {
  const nodo = document.createElement(tag);
  if (contenido !== undefined) nodo.textContent = texto(contenido);
  if (clase) nodo.className = clase;
  return nodo;
 };
 const normalizar = valor => String(valor).normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
 const enlace = (url, etiqueta) => {
  try {
   const destino = new URL(url);
   if (destino.protocol !== "https:" || destino.username || destino.password) return crear("span", ausente);
   const a = crear("a", etiqueta);
   a.href = destino.href; a.target = "_blank"; a.rel = "noopener noreferrer";
   return a;
  } catch { return crear("span", ausente); }
 };
 const opcion = (select, valor, etiqueta) => {
  const option = crear("option", etiqueta); option.value = valor; select.append(option);
 };
 const nombres = fila => fila.clasificacion.disciplinas.map(d => datos.disciplinas[d] || d).join(", ");
 const campo = (contenedor, etiqueta, valor) => {
  const bloque = crear("div", undefined, "campo");
  bloque.append(crear("dt", etiqueta));
  const dd = crear("dd", valor); if (!valor) dd.className = "vacio";
  bloque.append(dd); contenedor.append(bloque);
 };
 const md = valor => texto(valor).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
  .replace(/"/g, "&quot;").replace(/'/g, "&#x27;").replace(/([\\`*_{}\[\]()<>#+\-.!|])/g, "\\$1");
 const markdownFila = fila => {
  const f = fila.fuente, c = fila.clasificacion;
  const lineas = ["## " + md(fila.grado) + ".° · " + md(fila.contenido),
   "**Unidad:** " + md(fila.unidad), "**Asignatura de la malla:** " + md(fila.asignatura_malla),
   "**Origen declarado:** " + md(fila.origen), "**Clasificación:** " + md(datos.estados[c.estado] || c.estado),
   "**Disciplinas:** " + md(nombres(fila)), "**Método:** " + md(c.metodo),
   "**Justificación:** " + md(c.justificacion)];
  lineas.splice(4, 0, "**Tema / clase del insumo:** " + md(fila.numero_tema) + " / " + md(fila.numero_clase));
  datos.campos.forEach(([grupo, campos]) => {
   lineas.push("### " + grupo);
   campos.forEach(([clave, etiqueta]) => lineas.push("**" + etiqueta + ":** " + md(fila[clave])));
  });
  lineas.push("### Secuencia didáctica del insumo");
  fila.fases.forEach(fase => {
   const estado = fase.presente ? "Columna presente" : "Ausente en esta hoja";
   const nombre = fase.nombre[0].toUpperCase() + fase.nombre.slice(1);
   lineas.push("**" + nombre + " — " + estado + ":** " + md(fase.texto),
    "Códigos locales: " + md(fase.codigos.join(", ")), "Celdas: " + md(fase.celdas.join(", ")));
  });
  lineas.push("### Fuente y trazabilidad", "**ID de fila:** " + md(fila.id),
   "**Archivo:** " + md(f.archivo), "**Versión:** " + md(f.version), "**Hoja:** " + md(f.hoja),
   "**Fila física:** " + f.fila, "**SHA-256:** " + f.sha256,
   "**URL declarada del original:** " + md(f.url_declarada));
  fila.celdas.forEach(celda => lineas.push("- " + md(celda.coordenada) + ": " +
   md(celda.campo + (celda.origen ? "; ancla combinada " + celda.origen : ""))));
  lineas.push("### Alertas localizadas");
  if (!datos.alertas_cargadas) lineas.push("No se cargó un registro de alertas.");
  else if (!fila.alertas.length) lineas.push(
   "No se localizaron alertas del registro cargado; esto no certifica la fila.");
  fila.alertas.forEach(indice => {
   const a = datos.alertas[indice];
   lineas.push("**" + md(a.id) + " · " + md(a.estado) + " · " + md(a.severidad) + "**", md(a.explicacion),
    "Alcance: " + md(a.limite), "Contraste: " + md(a.url));
  });
  return lineas.join("\n\n");
 };
 const alerta = a => {
  const caja = crear("section", undefined, "alerta");
  caja.append(crear("h4", a.id), crear("p", a.estado + " · " + a.severidad + " · " + a.clase, "metadato"),
   crear("p", a.explicacion, "texto"));
  const f = a.fuente;
  caja.append(crear("p", (f.archivo || ausente) + " / " + (f.hoja || ausente) + " / " +
   (Array.isArray(f.celdas) ? f.celdas.join(", ") : ausente), "metadato"));
  if (a.ancla) caja.append(crear("p", "Texto localizado: " + a.ancla, "texto"));
  if (a.limite) caja.append(crear("p", "Alcance: " + a.limite, "metadato"));
  if (!a.coincide_captura) caja.append(crear("p", "SHA o archivo sin coincidencia en esta captura.", "metadato"));
  if (a.url) caja.append(enlace(a.url, "Consultar el contraste primario"));
  return caja;
 };
 let seleccion = null, visibles = [], limiteLista = 60;
 const indiceBusqueda = new Map(datos.filas.map(f => [f.id, normalizar(JSON.stringify(f))]));
 const seleccionar = (fila, enfocar) => {
  seleccion = fila;
  $("exportar-ficha").disabled = !fila;
  const ficha = $("ficha"); ficha.replaceChildren();
  if (!fila) { ficha.append(crear("h2", "No hay filas para estos filtros"),
   crear("p", "Cambia el grado, la disciplina, la unidad o el texto de búsqueda.")); return; }
  const etiquetas = crear("div", undefined, "etiquetas");
  etiquetas.append(crear("span", fila.grado + ".° grado", "etiqueta"),
   crear("span", datos.estados[fila.clasificacion.estado] || fila.clasificacion.estado, "etiqueta"));
  if (fila.alertas.length) etiquetas.append(crear("span", fila.alertas.length + " alerta(s)", "etiqueta advertencia"));
  ficha.append(etiquetas, crear("h2", fila.contenido || "Contenido sin declarar"),
   crear("p", fila.unidad, "metadato"));
  const perfil = crear("dl");
  campo(perfil, "Asignatura declarada en la malla", fila.asignatura_malla);
  campo(perfil, "Disciplinas de la clasificación", nombres(fila));
  campo(perfil, "Origen del contenido, según la V4", fila.origen);
  campo(perfil, "Tema / clase del insumo", texto(fila.numero_tema) + " / " + texto(fila.numero_clase));
  campo(perfil, "Método de clasificación", fila.clasificacion.metodo);
  campo(perfil, "Justificación de la clasificación", fila.clasificacion.justificacion);
  ficha.append(perfil);
  fila.clasificacion.errores.forEach(e => ficha.append(crear("p", e, "metadato")));
  if (fila.alertas.length) {
   ficha.append(crear("h3", "Alertas localizadas"));
   fila.alertas.forEach(i => ficha.append(alerta(datos.alertas[i])));
  }
  datos.campos.forEach(([grupo, campos], indice) => {
   const destino = indice === 2 ? crear("details") : crear("section");
   destino.append(crear(indice === 2 ? "summary" : "h3", grupo));
   const dl = crear("dl"); campos.forEach(([clave, etiqueta]) => campo(dl, etiqueta, fila[clave]));
   destino.append(dl); ficha.append(destino);
   if (indice === 0) {
    ficha.append(crear("h3", "Secuencia didáctica del insumo"));
    const fases = crear("div", undefined, "fases");
    fila.fases.forEach((fase, i) => {
     const caja = crear("section", undefined, "fase" + (fase.presente ? "" : " fase-ausente"));
     caja.append(crear("h4", (i + 1) + ". " + fase.nombre[0].toUpperCase() + fase.nombre.slice(1)),
      crear("span", fase.presente ? "Columna presente" : "Ausente en esta hoja",
       "etiqueta" + (fase.presente ? "" : " advertencia")), crear("p", fase.texto, "texto"),
      crear("p", "Códigos locales: " + texto(fase.codigos.join(", ")), "metadato"),
      crear("p", "Celdas: " + texto(fase.celdas.join(", ")), "metadato"));
     fases.append(caja);
    });
    ficha.append(fases, crear("p", "Los códigos de estas fases pertenecen al insumo local.", "metadato"));
   }
  });
  const fuente = crear("section", undefined, "fuente"), dl = crear("dl"), f = fila.fuente;
  fuente.append(crear("h3", "Fuente y trazabilidad"));
  [["Archivo original", f.archivo], ["Versión", f.version], ["Hoja exacta", f.hoja],
   ["Fila física", f.fila], ["SHA-256 del original", f.sha256], ["ID de fila", fila.id]]
   .forEach(([etiqueta, valor]) => campo(dl, etiqueta, valor));
  fuente.append(dl);
  if (f.drive_url) fuente.append(enlace(f.drive_url, "Abrir original en Drive"));
  else fuente.append(crear("p", "Sin enlace HTTPS del original disponible.", "metadato"));
  const detalles = crear("details"); detalles.append(crear("summary", "Celdas y anclas combinadas"));
  const contenedor = crear("div", undefined, "tabla-contenedor"), tabla = crear("table");
  tabla.append(crear("caption", "Localizadores de la fila; un ancla combinada puede estar en otra fila física."));
  const thead = crear("thead"), tr = crear("tr");
  ["Celda", "Campo del insumo", "Ancla combinada"].forEach(t => {
   const th = crear("th", t); th.scope = "col"; tr.append(th);
  });
  thead.append(tr); tabla.append(thead); const tbody = crear("tbody");
  fila.celdas.forEach(c => {
   const row = crear("tr"); [c.coordenada, c.campo, c.origen || "Celda propia"]
    .forEach(v => row.append(crear("td", v))); tbody.append(row);
  });
  tabla.append(tbody); contenedor.append(tabla); detalles.append(contenedor); fuente.append(detalles);
  ficha.append(fuente);
  if (!fila.alertas.length) ficha.append(crear("p", datos.alertas_cargadas ?
   "Sin alertas localizadas en el registro cargado. Esto no certifica la fila." :
   "Registro de alertas no cargado.", "metadato"));
  if (enfocar) ficha.focus({preventScroll:true});
 };
 const disciplinaCoincide = fila => {
  const d = $("disciplina").value;
  if (!d) return true;
  if (d === "integrada") return normalizar(fila.asignatura_malla) === "ciencias";
  if (d === "pendientes") return ["sin_clasificar", "abstencion"].includes(fila.clasificacion.estado);
  if (d === "fuera") return fila.clasificacion.estado === "fuera_alcance";
  return fila.clasificacion.disciplinas.includes(d);
 };
 const base = fila => (!$("grado").value || String(fila.grado) === $("grado").value) && disciplinaCoincide(fila);
 const pintarLista = () => {
  $("lista").replaceChildren();
  const fragmento = document.createDocumentFragment();
  visibles.slice(0, limiteLista).forEach(fila => {
   const boton = crear("button", undefined, "fila-boton"); boton.type = "button";
   boton.setAttribute("aria-pressed", String(seleccion && seleccion.id === fila.id));
   boton.append(crear("span", fila.contenido || "Contenido sin declarar", "fila-titulo"),
    crear("span", fila.grado + ".° · " + fila.unidad, "fila-contexto"),
    crear("span", datos.estados[fila.clasificacion.estado] || fila.clasificacion.estado, "fila-contexto"));
   if (fila.alertas.length) boton.append(crear("span", fila.alertas.length + " alerta(s)", "etiqueta advertencia"));
   boton.addEventListener("click", () => { seleccionar(fila, true); pintarLista(); });
   fragmento.append(boton);
  });
  if (!visibles.length) fragmento.append(crear("p", "Sin resultados.", "sin-resultados"));
  $("lista").append(fragmento);
  $("cargar").hidden = limiteLista >= visibles.length;
  $("cargar").textContent = "Mostrar 60 filas más (" + Math.max(0, visibles.length - limiteLista) + " restantes)";
 };
 const filtrar = actualizarUnidades => {
  if (actualizarUnidades) {
   const anterior = $("unidad").value;
   $("unidad").replaceChildren(); opcion($("unidad"), "", "Todas las unidades");
   [...new Set(datos.filas.filter(base).map(f => f.unidad))].sort((a,b) => a.localeCompare(b,"es",{numeric:true}))
    .forEach(u => opcion($("unidad"), u, u || "Unidad sin declarar"));
   if ([...$("unidad").options].some(o => o.value === anterior)) $("unidad").value = anterior;
  }
  const busqueda = normalizar($("buscar").value.trim());
  visibles = datos.filas.filter(f => base(f) && (!$("unidad").value || f.unidad === $("unidad").value)
   && (!busqueda || indiceBusqueda.get(f.id).includes(busqueda)));
  limiteLista = 60;
  seleccionar(visibles.find(f => seleccion && f.id === seleccion.id) || visibles[0] || null, false);
  pintarLista();
  const pendientes = visibles.filter(f => ["sin_clasificar", "abstencion"].includes(f.clasificacion.estado)).length;
  $("estado").textContent = visibles.length + " de " + datos.filas.length + " filas · " + pendientes +
   " sin clasificación resuelta en esta selección. Se muestran también filas pendientes y fuera de alcance.";
  $("exportar-filtro").disabled = !visibles.length;
 };
 const descargar = filas => {
  const contenido = "# Revisión curricular " + md(datos.version) + "\n\n" + datos.limite +
   "\n\nCaptura: " + datos.huella + "\n\n" + filas.map(markdownFila).join("\n\n---\n\n") + "\n";
  const url = URL.createObjectURL(new Blob([contenido], {type:"text/markdown;charset=utf-8"}));
  const a = crear("a"); a.href = url; a.download = "GOES-curriculo-" + filas.length + "-filas.md";
  document.body.append(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000);
 };
 opcion($("grado"), "", "Todos");
 [...new Set([...Array.from({length:10}, (_,i) => i+2), ...datos.filas.map(f => f.grado)])]
  .sort((a,b) => a-b).forEach(g => opcion($("grado"), String(g), g + ".° grado"));
 opcion($("disciplina"), "", "Todas las filas");
 Object.entries(datos.disciplinas).forEach(([codigo,nombre]) => opcion($("disciplina"), codigo, nombre));
 opcion($("disciplina"), "integrada", "Malla integrada de Ciencias");
 opcion($("disciplina"), "pendientes", "Sin clasificar o abstención");
 opcion($("disciplina"), "fuera", "Fuera del alcance disciplinar");
 $("filtros").addEventListener("submit", evento => evento.preventDefault());
 ["grado", "disciplina"].forEach(id => $(id).addEventListener("change", () => filtrar(true)));
 $("unidad").addEventListener("change", () => filtrar(false));
 $("buscar").addEventListener("input", () => filtrar(false));
 $("restablecer").addEventListener("click", () => {
  ["grado","disciplina","unidad","buscar"].forEach(id => { $(id).value = ""; }); filtrar(true);
 });
 $("cargar").addEventListener("click", () => { limiteLista += 60; pintarLista(); });
 $("exportar-filtro").addEventListener("click", () => descargar(visibles));
 $("exportar-ficha").addEventListener("click", () => { if (seleccion) descargar([seleccion]); });
 $("captura").textContent = "VERSIÓN " + datos.version + " · " + datos.fuentes + " fuentes · " + datos.hojas + " hojas";
 $("limite").textContent = datos.limite;
 $("pie").textContent = "Captura " + datos.huella + " · Consulta local sin conexión ni envío de datos.";
 $("titulo-alertas").textContent = "Registro documental de alertas (" + datos.alertas.length + ")";
 if (!datos.alertas_cargadas) $("alertas-documentales").append(crear("p", "Registro de alertas no cargado."));
 else if (!datos.alertas.length) $("alertas-documentales").append(crear("p", "El registro cargado está vacío."));
 datos.alertas.forEach(a => $("alertas-documentales").append(alerta(a)));
 const avisos = [...datos.avisos];
 if (!datos.catalogo) avisos.unshift(
  "Catálogo disciplinar no cargado. Se conserva la asignatura explícita de la malla.");
 if (datos.limite_catalogo) avisos.unshift(datos.limite_catalogo);
 if (!avisos.length) avisos.push("No hay avisos adicionales de ingesta en esta captura.");
 avisos.forEach(a => $("avisos").append(crear("p", a, "metadato")));
 filtrar(true);
})();
</script>
</body></html>"""
