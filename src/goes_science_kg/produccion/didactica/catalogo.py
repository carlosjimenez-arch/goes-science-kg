"""Códigos de cada libro y decisiones de diseño explícitas; sin clasificar por palabras sueltas."""

from __future__ import annotations

import re

from goes_science_kg.materiales.compilacion import serializar, sha
from goes_science_kg.produccion.didactica.contratos import DefinicionLocal, Localizador, TareaHabilidad

MACROS = {
    "E": "explicacion_modelizacion",
    "D": "indagacion_datos",
    "I": "informacion_argumentacion_decisiones",
}
MARCADOR = re.compile(r"(?<!\w)([EDI]\d+(?:\.\d+)*)\s*[·:]")


def definiciones(curriculo):
    """Lee exclusivamente las filas de códigos del auxiliar del mismo archivo original."""
    fuentes = {s.id: s for s in curriculo.fuentes}
    resultado = {}
    for hoja in curriculo.hojas:
        if hoja.nombre != "Microhabilidades PISA":
            continue
        fuente = fuentes[hoja.fuente_id]
        for registro in hoja.registros:
            valores = {c.columna: c for c in registro.celdas}
            codigo = str(valores["A"].valor or "").strip()
            if not re.fullmatch(r"[EDI][1-9]", codigo):
                continue
            clave = fuente.id, codigo
            if clave in resultado:
                raise ValueError("Código repetido en el catálogo de un libro")
            resultado[clave] = DefinicionLocal(
                codigo=codigo,
                macro_id=MACROS[codigo[0]],
                nombre=str(valores["C"].valor or ""),
                competencia_declarada=str(valores["B"].valor or ""),
                contextualizacion_original=str(valores["D"].valor or ""),
                origen=Localizador(
                    fuente_id=fuente.id,
                    archivo=fuente.archivo,
                    sha256=fuente.sha256,
                    hoja=hoja.nombre,
                    celdas=tuple(f"{col}{registro.fila}" for col in "ABCD"),
                ),
            )
    return resultado


def extraer_tareas(fila, fuente, catalogo):
    tareas, incidencias, vistos = [], [], set()
    for celda in fila.celdas:
        if not celda.campo or not celda.campo.startswith("fase_") or not celda.valor:
            continue
        ancla = celda.origen_combinado or celda.coordenada
        if ancla in vistos:
            continue
        vistos.add(ancla)
        fase = celda.campo.removeprefix("fase_")
        texto = str(celda.valor)
        marcadores = list(MARCADOR.finditer(texto))
        for i, m in enumerate(marcadores):
            fin = marcadores[i + 1].start() if i + 1 < len(marcadores) else len(texto)
            actividad = texto[m.end() : fin].strip()
            if not actividad:
                incidencias.append({"codigo": "ACTIVIDAD_VACIA", "celda": celda.coordenada, "habilidad": m[1]})
                continue
            definicion = catalogo.get((fuente.id, m[1]))
            origen = Localizador(
                fuente_id=fuente.id,
                archivo=fuente.archivo,
                sha256=fuente.sha256,
                hoja=fila.hoja,
                celdas=(celda.coordenada,),
            )
            datos = dict(fase=fase, codigo=m[1], actividad_literal=actividad, origen=origen, definicion=definicion)
            tareas.append(
                TareaHabilidad(
                    id="TAREA:" + sha(serializar([fila.id, celda.coordenada, m.start(), actividad])), **datos
                )
            )
            if definicion is None:
                incidencias.append({"codigo": "CODIGO_SIN_DEFINICION", "habilidad": m[1], "celda": celda.coordenada})
        detectados = {m[1] for m in marcadores}
        mencionados = set(re.findall(r"(?<!\w)[EDI]\d+(?:\.\d+)*(?!\w)", texto))
        for codigo in sorted(mencionados - detectados):
            incidencias.append(
                {"codigo": "CODIGO_SIN_CONSIGNA_SEPARABLE", "habilidad": codigo, "celda": celda.coordenada}
            )
    return tuple(tareas), incidencias


def perfil(grado):
    """Apoyos propuestos por tramo; se ajustan según diagnóstico, sin equivalencias con bandas PISA/NGSS."""
    if grado <= 4:
        return {
            "tramo": "2-4",
            "representacion": "Objeto o imagen, dibujo rotulado y explicación oral breve.",
            "apoyo": "Leer la consigna en voz alta, mostrar un ejemplo y dar una tabla parcialmente preparada.",
            "autonomia": "Retirar primero las pistas visuales; mantener la lectura oral si se necesita.",
            "matematicas": "Usar conteos y magnitudes concretas exigidos por esta tarea; explicitar sus unidades.",
            "carga": "Trabajar una pregunta focal por vez; oralidad y dibujo conservan la demanda científica.",
        }
    if grado <= 6:
        return {
            "tramo": "5-6",
            "representacion": "Observación, esquema y tabla relacionados por una explicación.",
            "apoyo": "Resolver un ejemplo, completar otro en pareja y justificar después una respuesta individual.",
            "autonomia": "Retirar la tabla modelo cuando el estudiante pueda organizar y explicar sus datos.",
            "matematicas": "Identificar unidades y operaciones necesarias antes de calcular; interpretar el resultado.",
            "carga": "Separar comprensión del fenómeno, registro y cálculo; reunirlos al construir la explicación.",
        }
    if grado <= 9:
        return {
            "tramo": "7-9",
            "representacion": "Vincular fenómeno, modelo y datos; justificar límites de inferencia.",
            "apoyo": (
                "Hacer explícitos variables, símbolos y unidades; contrastar un ejemplo correcto y uno defectuoso."
            ),
            "autonomia": "Pasar del diseño guiado a elegir y justificar procedimientos y representaciones.",
            "matematicas": "Comprobar razón, escala, proporcionalidad y unidades cuando la tarea las requiera.",
            "carga": "No añadir álgebra o terminología que la evidencia requerida no necesite.",
        }
    return {
        "tramo": "10-11",
        "representacion": "Conectar evidencia, modelos, supuestos, formalización y alcance.",
        "apoyo": "Diagnosticar los prerrequisitos cuantitativos y lectores antes de exigir autonomía.",
        "autonomia": "Justificar elecciones de método, evaluar alternativas y comunicar incertidumbre pertinente.",
        "matematicas": "Explicitar ejes, magnitudes, unidades, escala y dominio de validez antes del ajuste o modelo.",
        "carga": "Dividir las operaciones nuevas sin convertir la tarea científica en copia de un procedimiento.",
    }
