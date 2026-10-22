"""Prepare knowledge-review dossiers from verified records and original bytes."""

from __future__ import annotations

import json
import logging
from collections.abc import Sequence

from goes_science_kg.curriculo.contexto_fuentes import documento_de_fila
from goes_science_kg.curriculo.contratos import Curriculo
from goes_science_kg.modelos import TipoNodo
from goes_science_kg.motor.contratos import Evidencia, huella
from goes_science_kg.motor.fragmentos import datos_fragmentos, preparar_fragmentos
from goes_science_kg.motor.fuentes import FuentesVerificadas
from goes_science_kg.producto._conocimiento_contratos import InformeConocimiento
from goes_science_kg.producto._juicios_contratos import (
    ExpedienteConocimiento,
    SolicitudConocimiento,
    SoporteSemantico,
)
from goes_science_kg.producto._validacion import json_bytes, sha
from goes_science_kg.producto.contratos import ReferenciasProducto
from goes_science_kg.recuperacion import Documento

LOGGER = logging.getLogger(__name__)
_TIPOS = {
    "fila_concepto": (TipoNodo.CONCEPTO, "trabaja_concepto"),
    "fila_practica": (TipoNodo.PRACTICA, "practica_declarada"),
    "contraste_pais": (TipoNodo.OBJETIVO_PAIS, "contraste_documental"),
    "prerrequisito": (TipoNodo.CONCEPTO, "prerrequisito_necesario"),
}


def datos_juicio(expediente: ExpedienteConocimiento) -> dict:
    """Send evidence to reviewers without prior confidence, votes, or historical AI paths."""
    return {
        "version": expediente.version,
        "datos_no_confiables": {
            "fila_id": expediente.fila_id,
            "grado_sv": expediente.grado,
            "asignatura_malla": expediente.asignatura_malla,
            "relacion_propuesta": {
                "tipo": expediente.tipo_relacion,
                "origen": expediente.origen,
                "destino": expediente.destino,
                "ambito": "fila_curricular",
            },
            "descriptores_para_identificar_no_evidencia": expediente.descriptores,
            "evidencia_por_grupo": expediente.grupos,
            "lectura_primaria": {
                e.id: e.texto
                for e in expediente.evidencias
                if e.version == "referencia"
                or e.id
                in {i for nombre in ("objetivo_local", "evaluacion_local") for i in expediente.grupos.get(nombre, ())}
            },
            **datos_fragmentos(expediente.fragmentos, expediente.evidencias),
        },
    }


class PreparadorConocimiento:
    """Prepare review evidence without treating candidate transport flags as authorization."""

    def __init__(
        self,
        curriculo: Curriculo,
        informe: InformeConocimiento,
        referencias: ReferenciasProducto,
        fuentes: FuentesVerificadas,
        *,
        soportes: Sequence[SoporteSemantico] = (),
        max_caracteres: int = 24000,
    ):
        if not 2000 <= max_caracteres <= 40000:
            raise ValueError("El contexto requiere entre 2000 y 40000 caracteres")
        # Los contratos frozen contienen diccionarios: copiar evita mutaciones externas posteriores.
        self.curriculo = Curriculo.model_validate(curriculo.model_dump(mode="python"))
        self.informe = InformeConocimiento.model_validate(informe.model_dump(mode="python"))
        self.referencias = ReferenciasProducto.model_validate(referencias.model_dump(mode="python"))
        self.soportes = tuple(SoporteSemantico.model_validate(s.model_dump(mode="json")) for s in soportes)
        self.fuentes, self.max_caracteres = fuentes, max_caracteres
        self.filas = {f.id: f for f in self.curriculo.filas}
        self.nodos = {n.id: n for n in self.referencias.nodos}
        self.candidatos = {c.id: c for c in self.informe.candidatos}
        if (
            self.curriculo.version != "V4"
            or self.referencias.procedencia.get("version_curriculo") != "V3"
            or self.informe.huella_curriculo != self.curriculo.huella
            or len(self.filas) != len(self.curriculo.filas)
            or len(self.nodos) != len(self.referencias.nodos)
            or len(self.candidatos) != len(self.informe.candidatos)
        ):
            raise ValueError("Currículo, referencia y candidatos requieren identidades únicas y versiones compatibles")
        material = {
            "nodos": [n.model_dump(mode="json") for n in sorted(self.referencias.nodos, key=lambda n: n.id)],
            "aristas": [
                a.model_dump(mode="json")
                for a in sorted(
                    self.referencias.aristas, key=lambda a: (a.origen, a.destino, a.tipo.value, a.rol or "")
                )
            ],
            "procedencia": self.referencias.procedencia,
        }
        if (
            sha(json_bytes(material)) != self.informe.huella_referencia
            or sha(json_bytes([c.model_dump(mode="json") for c in self.informe.candidatos]))
            != self.informe.huella_candidatos
        ):
            raise ValueError("El informe no corresponde a su catálogo de candidatos y referencia")
        base = [
            self.curriculo.huella,
            self.informe.huella_referencia,
            self.informe.huella_pipeline,
            self.informe.politica.model_dump(mode="json"),
        ]
        for c in self.informe.candidatos:
            if c.id != "CANDIDATO_V4:" + sha(json_bytes([base, c.model_dump(mode="json", exclude={"id"})])):
                raise ValueError("Identidad de candidato incompatible con su contenido")
        if any(s.candidato_id not in self.candidatos for s in self.soportes):
            raise ValueError("Un soporte identifica un candidato ausente")

    @property
    def huella_entorno(self) -> str:
        """Fingerprint the knowledge preparer and its explicit evidence environment."""

        return huella(
            {
                "curriculo": self.curriculo.huella,
                "candidatos": self.informe.huella_candidatos,
                "referencia": self.informe.huella_referencia,
                "politica": self.informe.politica.model_dump(mode="json"),
                "soportes": [s.model_dump(mode="json") for s in self.soportes],
                "fuentes": self.fuentes.catalogo,
                "bloqueos": self.fuentes.bloqueos_curriculares,
                "max_caracteres": self.max_caracteres,
            }
        )

    def _externa(self, documento: str, fuente: dict, *, sha256: str, version: str) -> Evidencia:
        registro = self.fuentes.catalogo[documento.removeprefix("DOC:")]
        if (
            registro.get("sha256") != sha256
            or str(registro.get("version_documental", registro.get("anio", ""))) != version
        ):
            raise ValueError("El soporte no corresponde a la edición documental fijada")
        evidencia = self.fuentes.hidratar(
            Documento(
                id="SOPORTE:" + huella([documento, fuente, sha256, version]),
                texto="Localizador primario; el texto se obtiene de los bytes verificados",
                version="referencia",
                fuente={"documento": documento, **fuente},
            )
        )
        if evidencia is None or evidencia.fuente.get("sha256") != sha256:
            raise ValueError("No se pudo rehidratar la fuente primaria fijada")
        if any(marca in evidencia.texto for marca in ("(cid:", "\ufffd")):
            raise ValueError("La extracción contiene glifos no resueltos")
        return evidencia

    def preparar(self, solicitud: SolicitudConocimiento) -> ExpedienteConocimiento:
        """Prepare one candidate from verified original cells and primary documentary context."""

        candidato = self.candidatos[solicitud.candidato_id]
        fila = self.filas[candidato.fila_id]
        tipo_nodo, tipo_relacion = _TIPOS[candidato.tipo]
        destino = self.nodos[candidato.destino]
        if (
            destino.tipo != tipo_nodo
            or (candidato.tipo != "prerrequisito" and candidato.origen != fila.id)
            or (
                candidato.tipo == "prerrequisito"
                and (
                    candidato.origen not in self.nodos
                    or self.nodos[candidato.origen].tipo != TipoNodo.CONCEPTO
                    or candidato.origen == candidato.destino
                )
            )
        ):
            raise ValueError("Extremos o dirección incompatibles con el tipo de relación")
        descriptores = {
            "destino": {"id": destino.id, "etiqueta_historica": destino.etiqueta, "huella_registro": huella(destino)}
        }
        if candidato.tipo == "prerrequisito":
            descriptores["origen"] = {
                "id": candidato.origen,
                "etiqueta_historica": self.nodos[candidato.origen].etiqueta,
                "huella_registro": huella(self.nodos[candidato.origen]),
            }
        datos = dict(
            candidato_id=candidato.id,
            huella_curriculo=self.curriculo.huella,
            huella_referencia=self.informe.huella_referencia,
            huella_candidato=huella(candidato),
            fila_id=fila.id,
            grado=fila.grado,
            asignatura_malla=fila.asignatura_malla,
            tipo_relacion=tipo_relacion,
            origen=candidato.origen,
            destino=candidato.destino,
            descriptores=descriptores,
        )
        try:
            originales = self.fuentes.hidratar_celdas(documento_de_fila(fila))
            if not originales or self.fuentes.motivos_bloqueo(originales):
                raise ValueError("La fila carece de evidencia o tiene una alerta científica bloqueante")
            origen_fuente = next(f for f in self.curriculo.fuentes if f.id == fila.fuente_id)
            por_celda = {e.fuente["celdas"][0]: e for e in originales}
            esperadas = {c.coordenada for c in fila.celdas if c.valor is not None and str(c.valor).strip()}
            if set(por_celda) != esperadas or len(por_celda) != len(originales):
                raise ValueError("La evidencia omite o duplica celdas no vacías de la fila")
            for celda in fila.celdas:
                if celda.coordenada in por_celda:
                    prueba = por_celda[celda.coordenada]
                    fisica = prueba.fuente["celdas_verificadas"][0]
                    if (
                        prueba.fuente["sha256"] != origen_fuente.sha256
                        or str(celda.valor) != prueba.texto
                        or prueba.id != f"{fila.id}#CELDA:{celda.coordenada}"
                        or prueba.version != "V4"
                        or prueba.fuente.get("documento") != fila.fuente_id
                        or prueba.fuente.get("hoja") != fila.hoja
                        or fisica["coordenada_origen"] != (celda.origen_combinado or celda.coordenada)
                        or fisica["valor_real"] != celda.valor
                        or fisica["valor_original"] != celda.valor_original
                        or fisica["tipo_excel"] != celda.tipo_excel
                        or fisica["valor_es_formula"] != (celda.tipo_excel == "f")
                    ):
                        raise ValueError("Una celda del expediente no corresponde a la fila original")
            locales = [e for e in originales if not e.fuente["celdas_verificadas"][0]["valor_es_formula"]]
            if any(i not in {e.id for e in locales} for i in candidato.evidencias_locales):
                raise ValueError("El candidato usa una celda ajena a su fila")
            evidencias = {e.id: e for e in locales}
            grupos = {"fila": tuple(evidencias)}
            for nombre, campos in {
                "objetivo_local": {"procedimental"},
                "evaluacion_local": {
                    "indicadores_logro",
                    "indicador_avanzado",
                    "evidencia_aprendizaje",
                },
            }.items():
                ids = tuple(
                    por_celda[c.coordenada].id
                    for c in fila.celdas
                    if c.campo in campos and c.coordenada in por_celda and c.tipo_excel != "f"
                )
                if ids:
                    grupos[nombre] = ids
            if "objetivo_local" not in grupos:
                raise ValueError("No hay un objetivo local verificable")
            if candidato.tipo == "contraste_pais":
                if destino.fuente is None:
                    raise ValueError("Objetivo extranjero sin localizador primario")
                doc = destino.fuente.documento
                edicion = self.informe.politica.ediciones_por_documento.get(doc)
                if edicion is None:
                    raise ValueError("La edición extranjera no está fijada por la política")
                prueba = self._externa(
                    doc,
                    destino.fuente.model_dump(exclude={"documento"}, exclude_none=True),
                    sha256=edicion.sha256,
                    version=edicion.version_documental,
                )
                evidencias[prueba.id] = prueba
                grupos["destino"] = (prueba.id,)
                grupos["objetivo_extranjero"] = (prueba.id,)
                descriptores["destino"].update(
                    pais=destino.props.get("pais"),
                    tramo_nativo=destino.props.get("grado_o_tramo"),
                    equivalencia_grado_sv=None,
                )
            for soporte in self.soportes:
                if soporte.candidato_id != candidato.id:
                    continue
                fuente = {
                    k: v
                    for k, v in {"pagina": soporte.pagina, "localizador": soporte.localizador}.items()
                    if v is not None
                }
                if len(fuente) != 1:
                    raise ValueError("El soporte requiere página o código nativo, sin ambigüedad")
                prueba = self._externa(
                    soporte.documento, fuente, sha256=soporte.sha256, version=soporte.version_documental
                )
                evidencias[prueba.id] = prueba
                grupos[soporte.grupo] = tuple(dict.fromkeys((*grupos.get(soporte.grupo, ()), prueba.id)))
            obligatorios = {"fila", "destino"}
            if candidato.tipo == "prerrequisito":
                obligatorios |= {"origen", "dependencia"}
            if faltan := obligatorios - grupos.keys():
                raise ValueError("Falta evidencia primaria semántica: " + ", ".join(sorted(faltan)))
            # No ocultar la identidad de una práctica/definición detrás de una descripción histórica.
            datos["grupos"] = grupos
            datos["evidencias"] = tuple(evidencias.values())
            vacio = ExpedienteConocimiento(estado="preparado", **datos)
            sobrecarga = len(json.dumps(datos_juicio(vacio), ensure_ascii=False)) - len(
                json.dumps(datos_fragmentos([], []), ensure_ascii=False)
            )
            fragmentos = preparar_fragmentos(
                list(evidencias.values()),
                fila.procedimental + " " + destino.etiqueta,
                self.max_caracteres - sobrecarga,
                max_fragmentos=64,
                grupos_obligatorios=grupos
                | {"lectura_primaria:" + e.id: (e.id,) for e in evidencias.values() if e.version == "referencia"},
            )
            seleccionados = {f.evidencia_id for f in fragmentos}
            if any(not seleccionados.intersection(ids) for ids in grupos.values()):
                raise ValueError("El presupuesto no conserva un fragmento de cada grupo obligatorio")
            datos["fragmentos"] = tuple(fragmentos)
            expediente = ExpedienteConocimiento(estado="preparado", **datos)
            if len(json.dumps(datos_juicio(expediente), ensure_ascii=False)) > self.max_caracteres:
                raise ValueError("El payload completo excede el presupuesto")
            return expediente
        except (ValueError, KeyError, StopIteration) as error:
            LOGGER.warning("AMARILLO juicio sin contexto suficiente: %s", error)
            return ExpedienteConocimiento(
                estado="abstencion",
                motivos=(str(error),),
                **{k: v for k, v in datos.items() if k not in {"grupos", "evidencias", "fragmentos"}},
            )
