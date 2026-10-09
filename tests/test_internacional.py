"""Grafos internacionales de 9.°–11.° (spec 11). Ninguna prueba llama a Vertex: se simula el cliente."""

from __future__ import annotations

import pytest

from goes_science_kg import conceptos
from goes_science_kg.config import cargar, ruta
from goes_science_kg.internacional import contraste, etiquetar, extraer, vertex
from goes_science_kg.internacional.consenso import ensenados


@pytest.mark.parametrize("clave", ["9_11", "2_8"])
def test_config_internacional_valida(clave):
    from goes_science_kg.internacional import tramo

    t = tramo.TRAMOS[clave]
    cfg = cargar(t.config)
    ids = [d["id"] for d in cfg["documentos"]]
    assert len(ids) == len(set(ids))
    for d in cfg["documentos"]:
        assert d["pais"] in cfg["paises"], d["id"]
        assert ruta(d["archivo"]).is_file(), d["archivo"]
        assert d["nivel"] in ("nucleo", "especializacion"), d["id"]
        assert d["asignatura"] in extraer.CODIGO_ASIG, d["id"]
        g0, g1 = d["grado_sv"]
        assert 2 <= g0 <= g1 <= 11 and (t.contiene(g0, g1) or d.get("antecedente")), d["id"]
        if clave == "9_11":
            minimo = 6 if d.get("antecedente") else 7   # antecedente: secundaria baja (KR 중1 ≈ SV 6.°)
            assert minimo <= g0, d["id"]
            assert not d.get("antecedente") or g1 <= 8, d["id"]
        for g in (d.get("grados_pais") or {}).values():   # un grado o un rango [g0, g1]
            a, b = g if isinstance(g, list) else (g, g)
            assert g0 <= a <= b <= g1, d["id"]
    for imp in cfg.get("importar", []):
        assert imp["pais"] in cfg["paises"] and ruta(imp["archivo"]).is_file()
        assert all(t.contiene(g) for g in imp["grados_sv"]), imp


def test_ontario_no_se_lee_como_booleano():
    # «ON» sin comillas es True en YAML.
    assert "ON" in cargar("internacional")["paises"]


def test_ventanas_con_varios_rangos():
    doc = {"archivo": "data/fuentes/externos/paises/singapur/sec_bach/SG_SEC_G3_Chemistry_K324_2027.pdf",
           "paginas": [[9, 11], [20, 20]]}
    vs = list(extraer.ventanas(doc))
    assert [v.paginas for v in vs] == [[9, 10], [11], [20]]
    assert all(v.adjuntos[0][1] == "application/pdf" for v in vs)


def _ventana(paginas):
    doc = {"id": "x", "titulo": "Doc", "pais_nombre": "País", "curso": "Curso", "asignatura": "fisica"}
    return extraer.Ventana(doc, paginas, [(b"%PDF-falso", "application/pdf")], "", "p.")


def test_procesar_convierte_posicion_en_pagina_y_marca_omitidos(monkeypatch):
    def falso(prompt, *, modelo, **_):
        if modelo == vertex.MODELO_EXTRAER:
            return {"objetivos": [
                {"pagina": 2, "eje": "E", "tipo": "conocimiento", "demanda": "aplicar", "asignatura": "fisica",
                 "texto": "Calcular la aceleración.", "cita": "acceleration"},
                {"pagina": 7, "eje": "E", "tipo": "conocimiento", "demanda": "recordar", "asignatura": "fisica",
                 "texto": "Nombrar fuerzas.", "cita": "forces"}]}
        return {"juicios": [{"n": 0, "veredicto": "fiel", "motivo": "ok"},
                            {"n": 1, "veredicto": "no_fiel", "motivo": "no está"}],
                "omitidos": [{"pagina": 1, "eje": "E", "tipo": "practica", "demanda": "razonar",
                              "asignatura": "fisica", "texto": "Diseñar un experimento.", "cita": "design"}]}

    monkeypatch.setattr(vertex, "generar_json", falso)
    objs = extraer._procesar(_ventana([40, 41]))
    por_texto = {o["texto"]: o for o in objs}
    assert por_texto["Calcular la aceleración."]["pagina"] == 41
    assert por_texto["Nombrar fuerzas."]["pagina"] == 40          # posición inválida → primera página, anotada
    assert "nota_pagina" in por_texto["Nombrar fuerzas."]
    assert por_texto["Nombrar fuerzas."]["validacion"]["veredicto"] == "no_fiel"
    omitido = por_texto["Diseñar un experimento."]
    assert omitido["pagina"] == 40 and omitido["validacion"]["veredicto"] == "parcial"


def test_etiquetar_descarta_ids_inventados(monkeypatch, tmp_path):
    voc = sorted(c for c, x in conceptos.vocabulario().items() if x["asignatura"] == "fisica")
    real = voc[0]

    def falso(prompt, *, modelo, **_):
        return {"etiquetas": [{"id": "T1", "principales": [real, "CON:fisica/inventado"], "secundarios": [],
                               "practicas": ["PRAC:no-existe"], "propuestos": [], "confianza": "alta",
                               "justificacion": "x"},
                              {"id": "NO-PEDIDO", "principales": [real], "secundarios": [], "practicas": [],
                               "propuestos": [], "confianza": "alta", "justificacion": "x"}]}

    monkeypatch.setattr(vertex, "generar_json", falso)
    monkeypatch.setattr(etiquetar, "_carpeta", lambda nombre: str(tmp_path))
    r = etiquetar.etiquetar([{"id": "T1", "texto": "t"}], "fisica", "prueba")
    assert r["etiquetados"] == 1 and r["ids_invalidos"] == 3
    salida = (tmp_path / "prueba.json").read_text(encoding="utf-8")
    assert "inventado" in salida and real in salida   # el id inventado pasa a «propuestos», no a «principales»


def test_regla_de_presencia():
    e = {"principales": ["A"], "secundarios": ["B"], "confianza": "baja"}
    assert ensenados(e) == ["A"]
    assert ensenados({**e, "confianza": "media"}) == ["A", "B"]


# (sv_primer, sv_en_tramo, g_cons, n_nucleo_en_tramo, mediana_nucleo, n_nucleo_foco, n_esp)
@pytest.mark.parametrize("args, esperado", [
    ((None, None, 9, 6, 9.0, 6, 2), "faltante"),
    ((None, None, None, 0, None, 0, 3), "no_aplica"),
    ((5, None, 9, 6, 8.0, 7, 2), "no_retomado"),
    ((5, None, 9, 4, 8.0, 7, 2), "previo"),          # 4 de 8 es empate: no alcanza el consenso de la spec
    ((5, 10, 9, 6, 8.0, 7, 2), "retomado"),
    ((3, 9, None, 0, 10.5, 2, 1), "retomado"),       # la primaria salvadoreña no se juzga como «adelantada»
    ((11, 11, 9, 6, 9.0, 6, 2), "tardio"),
    ((10, 10, 9, 6, 9.0, 6, 2), "alineado"),
    ((9, 9, None, 0, None, 0, 5), "solo_especializacion"),
    ((9, 9, None, 2, 11.0, 2, 1), "adelantado"),
])
def test_clase_de(args, esperado):
    assert contraste.clase_de(*args) == esperado


@pytest.mark.parametrize("texto, esperado", [
    ("4.2. Calcula la velocidad del sonido y explica su relación con la densidad", "aplicar"),
    ("Describir la estructura del átomo", "recordar"),
    ("Diseñar una investigación para medir la aceleración", "razonar"),
    ("Explicar la fotosíntesis", "aplicar"),            # TIMSS: explicar es aplicar
    ("Resuelve problemas de cinemática", "aplicar"),
    ("La célula y sus partes", "sin_verbo"),
])
def test_demanda_por_verbos(texto, esperado):
    from goes_science_kg.internacional import profundidad

    assert profundidad.demanda(texto) == esperado


def test_umbral_de_la_spec():
    assert contraste.MIN_PAISES == 5   # spec 11: «≥ 5 de 9 países»


def test_generar_json_no_altera_el_esquema(monkeypatch, tmp_path):
    import copy as _copy
    import json as _json

    class Respuesta:
        text = '{"ok": true}'

    class Modelos:
        def generate_content(self, model, contents, config):
            config.response_schema["mutado"] = True   # simula lo que hace el SDK
            return Respuesta()

    class Cliente:
        models = Modelos()

    esquema = {"type": "OBJECT", "properties": {"ok": {"type": "BOOLEAN"}}}
    original = _copy.deepcopy(esquema)
    monkeypatch.setattr(vertex, "_cliente", lambda: Cliente())
    monkeypatch.setattr(vertex, "DIR_CACHE", str(tmp_path))
    assert vertex.generar_json("p", modelo="m", esquema=esquema) == {"ok": True}
    assert esquema == original
    clave = vertex._clave("m", "", "p", original, [])
    assert _json.loads((tmp_path / clave[:2] / f"{clave}.json").read_text())["respuesta"] == {"ok": True}


def test_normalizar_ids_solo_si_existen():
    voc = {"CON:fisica/primera-ley-newton": {}, "CON:quimica/tabla-periodica": {}}
    assert etiquetar._normalizar("CON:fisica:primera-ley-newton", voc, {}) == "CON:fisica/primera-ley-newton"
    assert etiquetar._normalizar("CON:tabla-periodica", voc, {}) == "CON:quimica/tabla-periodica"
    assert etiquetar._normalizar("CON:inventado", voc, {}) == "CON:inventado"   # no se inventan códigos


def test_catalogo_de_etiquetado_congelado(monkeypatch):
    """Los prompts no dependen del vocabulario vivo: cambiarlo (triaje, divisiones) no invalida la caché de Vertex."""
    etiquetar.catalogo_congelado.cache_clear()
    monkeypatch.setattr(conceptos, "vocabulario", lambda: (_ for _ in ()).throw(AssertionError("vocabulario vivo")))
    texto = etiquetar._catalogo("quimica")
    assert "CON:quimica/configuracion-electronica" in texto
    assert "distribucion-electronica-por-niveles" not in texto   # el concepto nuevo entra por la capa de divisiones


@pytest.mark.parametrize("comando", ["etiquetar", "extraer"])
def test_sin_confirmar_no_se_gasta(monkeypatch, comando):
    from typer.testing import CliRunner

    from goes_science_kg import cli
    from goes_science_kg.internacional import extraer as mod_extraer

    llamados = []
    monkeypatch.setattr(etiquetar, "pendientes", lambda grupos: 7)
    monkeypatch.setattr(mod_extraer, "llamadas_pendientes", lambda pais: 7)
    monkeypatch.setattr(etiquetar, "etiquetar", lambda *a, **k: llamados.append(a))
    monkeypatch.setattr(mod_extraer, "extraer_pais", lambda *a, **k: llamados.append(a))
    r = CliRunner().invoke(cli.app, ["internacional", comando, "JP"])
    assert r.exit_code == 1 and "--confirmar" in r.output and not llamados
