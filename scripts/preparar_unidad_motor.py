"""Prepara un expediente de autoría desde una entrega; no redacta ni aprueba clases.

Ejemplo: .venv/bin/python scripts/preparar_unidad_motor.py entregas/motor/0.1.0
  --grado 10 --asignatura fisica --unidad '4. Trabajo, energía y momento' --salida /tmp/unidad.json
"""

from __future__ import annotations

import argparse
from pathlib import Path

from goes_science_kg.motor.archivos import destino_seguro, escribir
from goes_science_kg.motor.politicas import INSTRUCCIONES
from goes_science_kg.motor.validacion import cargar_entrega, validar

MOMENTOS = ("1. Aproximar", "2. Explorar", "3. Explicar", "4. Indagar", "5. Reforzar")


def preparar(entrega: Path, grado: int, asignatura: str, unidad: str) -> dict:
    validar(entrega)
    manifiesto, datos = cargar_entrega(entrega)
    temas = sorted((t for t in datos["temas"] if t.grado == grado and t.asignatura_malla == asignatura
                    and t.columnas.get("Unidad") == unidad), key=lambda t: t.orden)
    if not temas:
        raise ValueError("la unidad no existe con esos atributos actuales")
    paquetes = {p.tema_id: p for p in datos["paquetes"]}
    componentes = {c.id: c for c in datos["componentes"]}
    filas = []
    for t in temas:
        p = paquetes.get(t.id)
        ids = {i for grupo in p.componentes.values() for i in grupo} if p else set()
        seleccion = [componentes[i] for i in sorted(ids)]
        avisos_datos = [{"componente": c.id, "estado": c.calidad.estado_datos,
                         "datos_detectados": c.calidad.datos_por_localizar,
                         "campos_para_revisar": {k: c.contenido[k] for k in INSTRUCCIONES
                                                 if "tabla de referencia" in str(c.contenido.get(k, "")).lower()}}
                        for c in seleccion if c.calidad.estado_datos == "pendiente"]
        experimentos = [{"id": c.id, "minutos_declarados": c.contenido["duracion_min"],
                         "excede_una_sesion": c.contenido["duracion_min"] > 55,
                         "minutos_observados": None} for c in seleccion if c.tipo == "experimento"]
        filas.append({"tema_id": t.id, "aliases": t.aliases, "fuente": t.fuente.model_dump(),
                      "procedimental": t.columnas["Procedimental"],
                      "indicadores_malla": t.columnas.get("Indicadores de logro", ""),
                      "evidencia_malla": t.columnas.get("Evidencia de aprendizaje", ""),
                      "momentos": [{"nombre": m, "propuesta_malla": t.columnas.get(m, ""),
                                    "actividad_seleccionada": None, "minutos_planificados": None,
                                    "evidencia_observable": None, "instrumento_evaluacion": None} for m in MOMENTOS],
                      "competencias_declaradas_malla": {k: v for k, v in t.columnas.items()
                                                        if "Competencia" in k or "Habilidad" in k},
                      "evidencia_de_ejercitacion_verificada": False,
                      "componentes_disponibles_autoria": [c.id for c in seleccion if c.usos.autoria
                                                           and c.tipo != "refuerzo"],
                      "componentes_retenidos": [{"id": c.id, "motivos": c.usos.motivos_autoria}
                                                for c in seleccion if not c.usos.autoria],
                      "dependencias_datos_por_verificar": avisos_datos,
                      "ausencia_de_aviso_no_certifica_datos": True,
                      "experimentos_disponibles": experimentos,
                      "paquete_id": p.id if p else None,
                      "referencias_citables_seleccionadas": [], "sesiones_planificadas": None,
                      "revision_cientifica_humana": None, "revision_didactica_humana": None,
                      "ensayo_docente": None, "aula_habilitada": False})
    return {"tipo": "expediente_de_autoria_fuera_del_contrato_motor", "estado": "preparacion",
            "id_entrega_origen": manifiesto.id_entrega, "grado": grado, "asignatura_malla": asignatura,
            "unidad": unidad, "duracion_objetivo_sesion_min": 55,
            "aviso": "Material para seleccionar y adaptar; no es una secuencia de clases aprobada.",
            "temas": filas}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("entrega", type=Path)
    parser.add_argument("--grado", type=int, required=True)
    parser.add_argument("--asignatura", required=True)
    parser.add_argument("--unidad", required=True)
    parser.add_argument("--salida", type=Path, required=True)
    args = parser.parse_args()
    args.salida = destino_seguro(args.salida)
    if args.salida.exists():
        parser.error("el expediente ya existe; no se sobrescriben decisiones de autoría")
    resultado = preparar(args.entrega, args.grado, args.asignatura, args.unidad)
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    escribir(args.salida, resultado)
    print(f"{len(resultado['temas'])} temas → {args.salida}")
