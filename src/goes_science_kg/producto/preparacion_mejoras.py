"""Contexto completo de una unidad, fuentes externas acotadas y citas registradas por fila."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from goes_science_kg.curriculo.contexto_fuentes import documento_de_fila
from goes_science_kg.ingesta.extraccion import PaginasConPerfil, cargar_perfiles
from goes_science_kg.ingesta.progresiones import cargar_progresiones
from goes_science_kg.ingesta.referencias import RepositorioReferencias
from goes_science_kg.ingesta.web_cientifica import RepositorioWeb
from goes_science_kg.motor.contratos import Evidencia, huella
from goes_science_kg.motor.fragmentos import datos_fragmentos, preparar_fragmentos
from goes_science_kg.producto.mejoras_contratos import PreparacionMejora, SolicitudMejora
from goes_science_kg.recuperacion.ciencia_web import IndiceCienciaWeb


def compactar(e: Evidencia) -> Evidencia:
    """El texto no cambia; la procedencia enviada omite valores de celda duplicados en sus metadatos."""
    fuente = {k: v for k, v in e.fuente.items() if k != "celdas_verificadas"}
    return e.model_copy(update={"fuente": fuente})


def datos_mejora(p: PreparacionMejora) -> dict:
    referencias = [e for e in p.evidencias if e.version == "referencia"]
    filas, textos = internar_textos(p.filas_originales)
    citas = datos_fragmentos(p.fragmentos, p.evidencias)
    # SHA y huellas prueban integridad en código, no son evidencia semántica para un LLM.
    # La proyección conserva localizadores, edición y texto; el archivo conserva todos los hashes.
    citas["fuentes"] = {
        id_: {
            "version": e["version"],
            "fuente": {
                k: v
                for k, v in e["fuente"].items()
                if k not in {"sha256", "huella_implementacion", "huella_documento_textual"}
            },
        }
        for id_, e in citas["fuentes"].items()
    }
    return {
        "version": "mejoras-curriculares-1",
        "unidad": p.solicitud.model_dump(mode="json"),
        "filas_originales": filas,
        "textos_originales_registrados": textos,
        "clasificaciones_originales": {
            id_: {k: d[k] for k in ("fila_id", "estado", "disciplinas")}
            for id_, d in p.clasificaciones_originales.items()
        },
        "alertas_cientificas_originales": p.alertas,
        "enmiendas_cientificas_propuestas": p.correcciones_requeridas,
        "contexto_aula": p.contexto_aula,
        "lectura_primaria": {e.id: e.texto for e in referencias},
        "limites": p.limites,
        "grupos_de_lectura": p.grupos,
        **citas,
    }


def internar_textos(filas):
    """Deduplicación exacta: todos los caracteres se conservan una vez, sin resumen ni traducción."""
    contador = Counter()

    def contar(x):
        if isinstance(x, str) and len(x) >= 100:
            contador[x] += 1
        elif isinstance(x, dict):
            for valor in x.values():
                contar(valor)
        elif isinstance(x, (list, tuple)):
            for valor in x:
                contar(valor)

    contar(filas)
    textos = {"T:" + huella(t): t for t, cantidad in sorted(contador.items()) if cantidad > 1}
    por_texto = {v: k for k, v in textos.items()}

    def sustituir(x):
        if isinstance(x, str) and x in por_texto:
            return {"texto_registrado": por_texto[x]}
        if isinstance(x, dict):
            return {k: sustituir(v) for k, v in x.items()}
        if isinstance(x, (list, tuple)):
            return [sustituir(v) for v in x]
        return x

    return sustituir(filas), textos


class PreparadorMejoras:
    def __init__(self, runtime, *, raiz: Path, max_caracteres: int = 220000):
        self.runtime, self.raiz, self.max_caracteres = runtime, raiz, max_caracteres
        self.web = IndiceCienciaWeb(RepositorioWeb(raiz / "data/referencias_web_cientificas_2026"))
        self.progresiones = cargar_progresiones(
            raiz / "config/progresiones_documentales_2026.yaml", raiz / "data/referencias_progresiones_2026"
        )
        self.archivo_progresiones = self.progresiones.archivo()
        self.referencias = PaginasConPerfil(
            RepositorioReferencias(raiz / "data/referencias_2026"),
            cargar_perfiles(raiz / "config/extraccion_referencias_2026.yaml"),
        )
        self.paises = RepositorioReferencias(raiz / "data/referencias_paises_2026")

    def preparar(self, solicitud: SolicitudMejora) -> PreparacionMejora:
        self.progresiones.validar(self.archivo_progresiones)
        filas = sorted(
            (
                f
                for f in self.runtime.producto.curriculo.filas
                if (f.grado, f.asignatura_malla, f.unidad)
                == (solicitud.grado, solicitud.asignatura_malla, solicitud.unidad)
            ),
            key=lambda f: (f.hoja, f.fila),
        )
        if not filas or len(filas) > 30:
            raise ValueError("Unidad ausente o fuera del límite de treinta filas")
        evidencias, grupos, enmiendas = [], {}, {}
        for i, f in enumerate(filas):
            e = self.runtime.fuentes.hidratar(documento_de_fila(f))
            if e is None:
                raise ValueError("La unidad perdió una fuente curricular original")
            celdas = self.runtime.fuentes.hidratar_celdas(documento_de_fila(f))
            campos = {c.coordenada: c.campo for c in f.celdas}
            objetivos = [c for c in celdas if campos[c.fuente["celdas"][0]] == "procedimental"]
            evaluacion = [
                c
                for c in celdas
                if campos[c.fuente["celdas"][0]] in {"indicadores_logro", "indicador_avanzado", "evidencia_aprendizaje"}
            ]
            if not objetivos:
                raise ValueError("La fila no conserva su objetivo procedimental original")
            evidencias.extend(compactar(c) for c in (*objetivos, *evaluacion))
            grupos[f"fila_{i:02d}"] = tuple(c.id for c in objetivos)
            if evaluacion:
                grupos[f"evaluacion_{i:02d}"] = tuple(c.id for c in evaluacion)
            if f.grado == 10 and f.asignatura_malla == "Biología" and f.hoja == "Biología 10.°":
                for celda in celdas:
                    ancla = celda.fuente["celdas_verificadas"][0]["coordenada_origen"]
                    antes = celda.texto
                    despues = antes
                    if ancla in {"W3", "W14"} and "C = Citocina" in antes:
                        despues = antes.replace("C = Citocina", "C = Citosina")
                    elif ancla == "S3" and antes.startswith("Las biomoléculas son polímeros orgánicos"):
                        despues = (
                            "Las biomoléculas orgánicas incluyen moléculas pequeñas, como los monosacáridos, "
                            "y macromoléculas, como los polisacáridos. No todas son polímeros. "
                            + antes.partition("vivos. ")[2]
                        )
                    if despues != antes:
                        datos_enmienda = {
                            "fuente_id": f.fuente_id,
                            "sha256": celda.fuente["sha256"],
                            "hoja": f.hoja,
                            "celda_ancla": ancla,
                            "antes": antes,
                            "despues": despues,
                            "alcance": "Enmienda propuesta para una copia derivada; el original se conserva íntegro",
                        }
                        enmienda_id = "ENMIENDA:" + huella(datos_enmienda)
                        if enmienda_id not in enmiendas:
                            enmiendas[enmienda_id] = {"id": enmienda_id, **datos_enmienda}
                            evidencias.append(compactar(celda))
                            grupos["enmienda_" + ancla] = (celda.id,)
        # Poblaciones y ediciones siguen visibles; son referencias para diseño, nunca homologaciones.
        externas = [
            self.referencias.pagina("pisa_2025_marco_final", 34),
            self.referencias.pagina("erce_2019_reporte_tecnico_2025", 19),
        ]
        grupos["marco_pisa"] = (externas[0].id,)
        grupos["marco_erce"] = (externas[1].id,)
        nativas = [Evidencia.model_validate(e) for e in self.archivo_progresiones["evidencias"].values()]
        externas.extend(nativas)
        grupos["progresiones_documentales"] = tuple(e.id for e in nativas)
        pais = (
            "eng_nc_ciencias_ks1_2"
            if solicitud.grado <= 6
            else "eng_nc_ciencias_ks3"
            if solicitud.grado <= 9
            else "eng_nc_ciencias_ks4"
        )
        # Página de Working scientifically, localizada desde la edición oficial, sin trasponer su grado.
        manifiesto = self.paises.manifiesto().referencias
        if pais in manifiesto:
            e = self.paises.pagina(pais, 4)
            e = e.model_copy(update={"fuente": e.fuente | {"raiz_fuente": "referencias_paises_2026"}})
            externas.append(e)
            grupos["programa_extranjero"] = (e.id,)
        # Singapur: prácticas y explicaciones. Japón: objetivos nativos de primaria, sólo para consulta.
        paises = [("sg_primary_jan2026", 8)] if solicitud.grado <= 6 else [("sg_lower_g2g3_peicai", 6)]
        if solicitud.grado <= 6:
            paises.append(("jp_elementary_science_en", 1))
        for id_pais, pagina in paises:
            e = self.paises.pagina(id_pais, pagina)
            e = e.model_copy(update={"fuente": e.fuente | {"raiz_fuente": "referencias_paises_2026"}})
            externas.append(e)
            grupos["programa_" + id_pais] = (e.id,)
        consulta = " ".join(f"{f.unidad} {f.contenido} {f.subcontenido} {f.procedimental}" for f in filas)
        ciencia = list(self.web.buscar(consulta))
        # Las alertas conocidas exigen las definiciones específicas, no sólo resultados por ranking.
        if any(f.id in self.runtime.fuentes.bloqueos_curriculares for f in filas):
            for fuente, consulta_especifica in (
                ("nhgri_adn_es_20261022", "citosina"),
                ("openstax_bio_carbohidratos_20261022", "monosaccharides (mono-"),
                ("openstax_bio_carbohidratos_20261022", "a long chain of monosaccharides"),
                ("openstax_bio_lipidos_20261022", "triglyceride"),
            ):
                candidatos = [
                    e
                    for e in self.web.evidencias.values()
                    if e.fuente["documento"] == fuente and consulta_especifica.casefold() in e.texto.casefold()
                ]
                if not candidatos:
                    raise ValueError("Falta una definición primaria para corregir una alerta científica")
                ciencia.extend(candidatos[:1])
                grupos["correccion_" + huella([fuente, consulta_especifica])[:12]] = (candidatos[0].id,)
        ciencia = list({e.id: e for e in ciencia}.values())
        for evidencia in ciencia:
            self.web.rehidratar(evidencia)
        if ciencia:
            externas.extend(ciencia)
            grupos["definiciones_cientificas"] = tuple(e.id for e in ciencia)
        evidencias.extend(compactar(e) for e in externas)
        fragmentos = preparar_fragmentos(
            evidencias, consulta, max_caracteres=self.max_caracteres, max_fragmentos=96, grupos_obligatorios=grupos
        )
        datos = {
            "solicitud": solicitud,
            "huella_curriculo": self.runtime.producto.curriculo.huella,
            "huella_catalogo": huella(self.runtime.producto.catalogo),
            "filas_originales": tuple(f.model_dump(mode="json", exclude={"celdas"}) for f in filas),
            "clasificaciones_originales": {
                d.fila_id: d.model_dump(mode="json")
                for d in self.runtime.producto.catalogo.filas
                if d.fila_id in {f.id for f in filas}
            },
            "alertas": {
                f.id: self.runtime.fuentes.bloqueos_curriculares[f.id]
                for f in filas
                if f.id in self.runtime.fuentes.bloqueos_curriculares
            },
            "correcciones_requeridas": tuple(enmiendas.values()),
            "evidencias": tuple(evidencias),
            "fragmentos": tuple(fragmentos),
            "grupos": grupos,
            "contexto_aula": {
                "recursos_hipoteticos": ["papel", "lapiz"],
                "conectividad": "no_requerida",
                "horario_oficial": "no_constatado",
                "disponibilidad_real": "no_constatada",
            },
            "limites": (
                "Preservar todas las filas, orden, fases presentes/ausentes y carga declarada del insumo",
                "Bandas NGSS y etapas extranjeras son referencias nativas, no equivalencias SV",
                "Una propuesta condicional no afirma enseñanza, eficacia ni recursos constatados",
            ),
        }
        p = PreparacionMejora(id="0" * 64, **datos)
        p = p.model_copy(update={"id": huella(p.model_dump(mode="json", exclude={"id"}))})
        if len(json.dumps(datos_mejora(p), ensure_ascii=False)) > self.max_caracteres:
            raise ValueError("La unidad completa excede el contexto; no se eliminan filas ni se trunca")
        return p

    def validar(self, p: PreparacionMejora) -> None:
        if self.preparar(p.solicitud) != p:
            raise ValueError("El contexto de mejora cambió al releer las fuentes originales")
