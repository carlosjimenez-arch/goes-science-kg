"""RAG auxiliar sobre párrafos primarios: índice invertido y expansión terminológica explícita."""

from __future__ import annotations

import json

from goes_science_kg.ingesta.web_cientifica import RepositorioWeb
from goes_science_kg.motor.contratos import Evidencia, huella
from goes_science_kg.recuperacion.lexico import IndiceLexico, normalizar
from goes_science_kg.recuperacion.modelos import Documento

TERMINOS = {
    "adn": "dna nucleotide base cytosine",
    "arn": "rna nucleotide",
    "genet": "genetic dna inheritance",
    "heren": "inheritance dna genetic",
    "biomole": "biological molecules monomers polymers",
    "polimer": "polymer monomer",
    "carbohidrat": "carbohydrate glucose polysaccharide",
    "glucid": "carbohydrate glucose",
    "lipid": "lipid fatty acid membrane",
    "membrana": "membrane lipid",
    "gras": "fat fatty acid",
    "materia": "matter substance molecule atom",
    "atom": "atom molecule element",
    "mezcla": "mixture compound solution",
    "sustanc": "substance matter compound",
    "compuest": "compound element",
    "soluci": "solution mixture",
    "masa": "mass kilogram",
    "medicion": "measurement units precision",
    "magnitud": "physical quantity unit",
    "longitud": "length meter",
    "tiempo": "time second",
    "unidad": "unit",
    "temperatura": "temperature kelvin",
    "sism": "seismic waves earth interior",
    "terremot": "seismic waves earth",
    "corteza": "crust earth",
    "nucleo": "core nucleus",
    "tierra": "earth planet",
    "campo": "field magnetic",
    "geolog": "earth mantle crust",
}


def fragmentar_web(e: Evidencia) -> tuple[Evidencia, ...]:
    return tuple(
        Evidencia.crear(
            "WEBPAR:" + huella([e.id, i, linea]),
            linea,
            e.fuente
            | {
                "parrafo_dom": i,
                "huella_documento_textual": e.huella,
                "alcance": "Párrafo completo del selector DOM; no es página PDF ni texto de metadatos",
            },
            "referencia",
        )
        for i, linea in enumerate(e.texto.splitlines())
        if 80 <= len(linea) <= 3000
    )


class IndiceCienciaWeb:
    def __init__(self, repositorio: RepositorioWeb):
        self.repositorio = repositorio
        manifest = json.loads((repositorio.raiz / "manifest.json").read_bytes())
        self.manifest = manifest
        self.evidencias = {
            p.id: p for id_ in sorted(manifest["fuentes"]) for p in fragmentar_web(repositorio.evidencia(id_))
        }
        self.indice = IndiceLexico(
            Documento(id=e.id, texto=e.texto, fuente=e.fuente, version=e.version) for e in self.evidencias.values()
        )

    def buscar(self, consulta: str, *, k: int = 6, max_caracteres: int = 6000) -> tuple[Evidencia, ...]:
        terminos = set(normalizar(consulta))
        expansion = " ".join(v for prefijo, v in TERMINOS.items() if any(t.startswith(prefijo) for t in terminos))
        candidatos = self.indice.buscar(consulta + " " + expansion, permitidos=set(self.evidencias), limite=30)
        seleccion, usados = [], 0
        for id_, _ in candidatos:
            e = self.evidencias[id_]
            if usados + len(e.texto) <= max_caracteres:
                seleccion.append(e)
                usados += len(e.texto)
            if len(seleccion) == k:
                break
        return tuple(seleccion)

    def rehidratar(self, e: Evidencia) -> Evidencia:
        documento = self.repositorio.evidencia(e.fuente["documento"])
        candidatos = {p.id: p for p in fragmentar_web(documento)}
        if candidatos.get(e.id) != e:
            raise ValueError("El párrafo científico cambió o perdió su localizador primario")
        return candidatos[e.id]
