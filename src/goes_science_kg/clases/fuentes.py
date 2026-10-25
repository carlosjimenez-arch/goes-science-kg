"""Párrafos CNXML oficiales fijados por SHA; recuperación léxica bilingüe y localizador XML."""

from __future__ import annotations

import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

from goes_science_kg.motor.contratos import Evidencia, huella
from goes_science_kg.recuperacion.lexico import IndiceLexico, normalizar
from goes_science_kg.recuperacion.modelos import Documento

# Expansiones de consulta explícitas; no crean alineaciones ni traducen el texto de las fuentes.
TERMINOS = {
    "medic": "measurement precision uncertainty",
    "magnitud": "physical quantity units",
    "unidad": "units measurement",
    "sistema internacional": "SI units",
    "cientific": "scientific method inquiry",
    "masa": "mass kilogram",
    "peso": "weight gravitational force",
    "longitud": "length meter",
    "temperatura": "temperature kelvin",
    "tiempo": "time second",
    "movim": "motion velocity",
    "veloci": "velocity speed",
    "acelera": "acceleration",
    "fuerza": "force Newton",
    "fricci": "friction",
    "torque": "torque equilibrium",
    "palanc": "lever torque",
    "equilibr": "equilibrium",
    "energia": "energy conservation",
    "trabajo": "work energy",
    "potencia": "power work",
    "gravedad": "gravity gravitation",
    "proyect": "projectile motion",
    "presion": "pressure",
    "fluido": "fluid buoyancy",
    "densidad": "density",
    "flota": "buoyancy Archimedes",
    "onda": "waves",
    "sonido": "sound frequency",
    "luz": "light optics",
    "optica": "optics reflection refraction",
    "espejo": "mirror reflection",
    "lente": "lens refraction",
    "electric": "electric current charge circuit",
    "circuit": "circuit voltage resistance",
    "magnet": "magnetic field",
    "calor": "heat thermal",
    "termo": "thermodynamics entropy",
    "nuclear": "nuclear radiation",
    "atomo": "atom nucleus",
    "materia": "matter substance properties",
    "molecul": "molecule molecular",
    "element": "element periodic",
    "enlace": "bond chemical",
    "mezcla": "mixture separation",
    "disoluc": "solution solubility",
    "concentra": "concentration molarity",
    "mol ": "mole stoichiometry",
    "quimic": "chemical reaction",
    "reaccion": "reaction chemical",
    "acido": "acid base pH",
    "base": "base acid",
    "oxid": "oxidation reduction",
    "reduc": "reduction oxidation",
    "gas": "gas pressure volume",
    "estequi": "stoichiometry",
    "carbon": "carbon organic",
    "hidrocar": "hydrocarbon",
    "polimer": "polymer monomer",
    "lipid": "lipid fats",
    "gras": "fat lipid",
    "carbohidr": "carbohydrate glucose",
    "protein": "protein amino acid",
    "enzima": "enzyme",
    "seres vivos": "living organisms",
    "celul": "cell membrane",
    "tejido": "tissue",
    "organo": "organ systems",
    "fotosint": "photosynthesis",
    "respir": "respiration gas exchange",
    "digesti": "digestion nutrition",
    "nutric": "nutrition",
    "circula": "circulation blood",
    "sangre": "blood heart",
    "excret": "excretion kidney",
    "nervi": "nervous neurons",
    "endocr": "endocrine hormone",
    "inmun": "immune infection",
    "microorg": "microorganism bacteria",
    "bacter": "bacteria prokaryote",
    "virus": "virus infection",
    "hongo": "fungi yeast",
    "adn": "DNA nucleic acid",
    "arn": "RNA",
    "genet": "genetic inheritance",
    "herencia": "inheritance Mendel",
    "reprodu": "reproduction meiosis",
    "mitosis": "mitosis cell cycle",
    "evoluc": "evolution selection",
    "biodiver": "biodiversity",
    "clasifica": "classification taxonomy",
    "plant": "plant",
    "animal": "animal",
    "ecosist": "ecosystem",
    "cadena": "food web trophic",
    "poblac": "population ecology",
    "habitat": "habitat ecology",
    "agua": "water cycle",
    "suelo": "soil nutrient cycle",
    "contamina": "pollution",
    "clima": "climate atmosphere",
    "tiempo atmosferico": "weather atmosphere",
    "atmosfer": "atmosphere",
    "tierra": "Earth planet",
    "roca": "rocks mineral",
    "mineral": "minerals",
    "tecton": "plate tectonics",
    "sismo": "earthquake seismic",
    "volcan": "volcano geology",
    "erosion": "erosion weathering",
    "planeta": "planet solar system",
    "sistema solar": "solar system",
    "estrella": "stars",
    "sol ": "Sun solar",
    "luna": "Moon lunar phases",
    "estacion": "seasons tilt",
    "universo": "universe galaxies",
    "constel": "constellation sky",
    "dia": "Earth rotation day",
}


def _contenido(elemento):
    if elemento.tag.rsplit("}", 1)[-1] == "math":
        return " " + ET.tostring(elemento, encoding="unicode") + " "
    return (elemento.text or "") + "".join(_contenido(h) + (h.tail or "") for h in elemento)


def extraer(contenido: bytes):
    if len(contenido) > 6 * 1024**2 or b"<!ENTITY" in contenido:
        raise ValueError("CNXML fuera de límites o con entidades no permitidas")
    raiz = ET.fromstring(contenido)
    titulo = next((e.text or "" for e in raiz if e.tag.endswith("}title")), "")
    bloques = []
    for i, e in enumerate(raiz.iter()):
        if e.tag.rsplit("}", 1)[-1] != "para":
            continue
        texto = " ".join(_contenido(e).split())
        if 100 <= len(texto) <= 6000:
            bloques.append((e.attrib.get("id", f"indice-{i}"), texto))
    return titulo, bloques


class CorpusClases:
    def __init__(self, raiz: Path):
        self.raiz = raiz
        self.manifest_bytes = (raiz / "manifest.json").read_bytes()
        self.huella = hashlib.sha256(self.manifest_bytes).hexdigest()
        self.manifest = json.loads(self.manifest_bytes)
        self.evidencias, self.por_documento, self.archivos = {}, {}, {}
        for libro in self.manifest["libros"]:
            licencia = self._leer(libro["licencia"]).decode()
            if "Attribution-NonCommercial-ShareAlike 4.0 International" not in licencia:
                raise ValueError("La edición científica requiere verificar su licencia antes de incorporarla")
            for ref in libro["modulos"]:
                titulo, bloques = extraer(self._leer(ref))
                documento = "CNXML:" + huella([libro["repositorio"], libro["commit"], ref["ruta"]])
                self.archivos[documento] = ref
                registros = []
                for localizador, texto in bloques:
                    fuente = {
                        "documento": documento,
                        "tipo": "documental",
                        "fuente_primaria": True,
                        "sha256": ref["sha256"],
                        "url": ref["url"],
                        "titulo": titulo,
                        "institucion": "OpenStax / Rice University",
                        "libro": libro["libro"],
                        "commit": libro["commit"],
                        "licencia": "CC BY-NC-SA 4.0",
                        "licencia_sha256": libro["licencia"]["sha256"],
                        "licencia_url": libro["licencia"]["url"],
                        "localizador": {"formato": "cnxml", "bloque": localizador},
                        "verificacion": "contenido_fuente",
                    }
                    e = Evidencia.crear(documento + "#" + localizador, texto, fuente, "referencia")
                    self.evidencias[e.id] = e
                    registros.append(e.id)
                self.por_documento[documento] = registros
        self.indice = IndiceLexico(
            Documento(id=e.id, texto=e.fuente["titulo"] + " " + e.texto, fuente=e.fuente, version=e.version)
            for e in self.evidencias.values()
        )

    def _leer(self, ref):
        p = self.raiz / ref["ruta"]
        if not p.resolve().is_relative_to(self.raiz.resolve()) or p.is_symlink():
            raise ValueError("La fuente CNXML sale de su repositorio")
        raw = p.read_bytes()
        if len(raw) != ref["bytes"] or hashlib.sha256(raw).hexdigest() != ref["sha256"]:
            raise ValueError("La fuente CNXML cambió")
        return raw

    def buscar(self, consulta, *, k=4, max_caracteres=7000):
        normalizada = " ".join(normalizar(consulta))
        palabras = normalizada.split()
        expansion = " ".join(
            v
            for t, v in TERMINOS.items()
            if (
                t.strip() in normalizada
                if " " in t.strip()
                else any(p == t.strip() if len(t.strip()) <= 3 else p.startswith(t.strip()) for p in palabras)
            )
        )
        candidatos = self.indice.buscar(consulta + " " + expansion, permitidos=set(self.evidencias), limite=40)
        salida, usados, documentos = [], 0, {}
        for id_, _ in candidatos:
            e = self.evidencias[id_]
            doc = e.fuente["documento"]
            if usados + len(e.texto) > max_caracteres or documentos.get(doc, 0) >= 2:
                continue
            salida.append(e)
            usados += len(e.texto)
            documentos[doc] = documentos.get(doc, 0) + 1
            if len(salida) == k:
                break
        return tuple(salida)

    def verificar(self, evidencia):
        documento = evidencia.fuente["documento"]
        _, bloques = extraer(self._leer(self.archivos[documento]))
        textos = dict(bloques)
        if textos.get(evidencia.fuente["localizador"]["bloque"]) != evidencia.texto:
            raise ValueError("La evidencia perdió su localizador XML")
        if self.evidencias.get(evidencia.id) != evidencia:
            raise ValueError("La evidencia no coincide con el corpus fijado")
