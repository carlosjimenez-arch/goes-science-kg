"""Test historical international science graphs with simulated Vertex clients only."""

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
        assert d["nivel"] in ("nucleo", "nucleo_parcial", "especializacion"), d["id"]
        assert d["asignatura"] in extraer.CODIGO_ASIG, d["id"]
        g0, g1 = d["grado_sv"]
        assert 2 <= g0 <= g1 <= 11 and (t.contiene(g0, g1) or d.get("antecedente")), d["id"]
        if clave == "9_11":
            minimo = 6 if d.get("antecedente") else 7  # antecedente: secundaria baja (KR 중1 ≈ SV 6.°)
            assert minimo <= g0, d["id"]
            assert not d.get("antecedente") or g1 <= 8, d["id"]
        for g in (d.get("grados_pais") or {}).values():  # un grado o un rango [g0, g1]
            a, b = g if isinstance(g, list) else (g, g)
            assert g0 <= a <= b <= g1, d["id"]
    for imp in cfg.get("importar", []):
        assert imp["pais"] in cfg["paises"] and ruta(imp["archivo"]).is_file()
        assert all(t.contiene(g) for g in imp["grados_sv"]), imp


def test_ontario_no_se_lee_como_booleano():
    # «ON» sin comillas es True en YAML.
    assert "ON" in cargar("internacional")["paises"]


def test_ventanas_con_varios_rangos():
    doc = {
        "archivo": "data/fuentes/externos/paises/singapur/sec_bach/SG_SEC_G3_Chemistry_K324_2027.pdf",
        "paginas": [[9, 11], [20, 20]],
    }
    vs = list(extraer.ventanas(doc))
    assert [v.paginas for v in vs] == [[9, 10], [11], [20]]
    assert all(v.adjuntos[0][1] == "application/pdf" for v in vs)


def _ventana(paginas):
    doc = {"id": "x", "titulo": "Doc", "pais_nombre": "País", "curso": "Curso", "asignatura": "fisica"}
    return extraer.Ventana(doc, paginas, [(b"%PDF-falso", "application/pdf")], "", "p.")


def test_procesar_convierte_posicion_en_pagina_y_marca_omitidos(monkeypatch):
    def falso(prompt, *, modelo, **_):
        if modelo == vertex.MODELO_EXTRAER:
            return {
                "objetivos": [
                    {
                        "pagina": 2,
                        "eje": "E",
                        "tipo": "conocimiento",
                        "demanda": "aplicar",
                        "asignatura": "fisica",
                        "texto": "Calcular la aceleración.",
                        "cita": "acceleration",
                    },
                    {
                        "pagina": 7,
                        "eje": "E",
                        "tipo": "conocimiento",
                        "demanda": "recordar",
                        "asignatura": "fisica",
                        "texto": "Nombrar fuerzas.",
                        "cita": "forces",
                    },
                ]
            }
        return {
            "juicios": [
                {"n": 0, "veredicto": "fiel", "motivo": "ok"},
                {"n": 1, "veredicto": "no_fiel", "motivo": "no está"},
            ],
            "omitidos": [
                {
                    "pagina": 1,
                    "eje": "E",
                    "tipo": "practica",
                    "demanda": "razonar",
                    "asignatura": "fisica",
                    "texto": "Diseñar un experimento.",
                    "cita": "design",
                }
            ],
        }

    monkeypatch.setattr(vertex, "generar_json", falso)
    objs = extraer._procesar(_ventana([40, 41]))
    por_texto = {o["texto"]: o for o in objs}
    assert por_texto["Calcular la aceleración."]["pagina"] == 41
    assert por_texto["Nombrar fuerzas."]["pagina"] == 40  # posición inválida → primera página, anotada
    assert "nota_pagina" in por_texto["Nombrar fuerzas."]
    assert por_texto["Nombrar fuerzas."]["validacion"]["veredicto"] == "no_fiel"
    omitido = por_texto["Diseñar un experimento."]
    assert omitido["pagina"] == 40 and omitido["validacion"]["veredicto"] == "parcial"


def test_etiquetar_descarta_ids_inventados(monkeypatch, tmp_path):
    voc = sorted(c for c, x in conceptos.vocabulario().items() if x["asignatura"] == "fisica")
    real = voc[0]

    def falso(prompt, *, modelo, **_):
        return {
            "etiquetas": [
                {
                    "id": "T1",
                    "principales": [real, "CON:fisica/inventado"],
                    "secundarios": [],
                    "practicas": ["PRAC:no-existe"],
                    "propuestos": [],
                    "confianza": "alta",
                    "justificacion": "x",
                },
                {
                    "id": "NO-PEDIDO",
                    "principales": [real],
                    "secundarios": [],
                    "practicas": [],
                    "propuestos": [],
                    "confianza": "alta",
                    "justificacion": "x",
                },
            ]
        }

    monkeypatch.setattr(vertex, "generar_json", falso)
    monkeypatch.setattr(etiquetar, "_carpeta", lambda nombre: str(tmp_path))
    r = etiquetar.etiquetar([{"id": "T1", "texto": "t"}], "fisica", "prueba")
    assert r["etiquetados"] == 1 and r["ids_invalidos"] == 3
    salida = (tmp_path / "prueba.json").read_text(encoding="utf-8")
    assert "inventado" in salida and real in salida  # el id inventado pasa a «propuestos», no a «principales»


def test_regla_de_presencia():
    e = {"principales": ["A"], "secundarios": ["B"], "confianza": "baja"}
    assert ensenados(e) == ["A"]
    assert ensenados({**e, "confianza": "media"}) == ["A", "B"]


# (sv_primer, sv_en_tramo, g_cons, n_nucleo_en_tramo, mediana_nucleo, n_nucleo_foco, n_esp)
@pytest.mark.parametrize(
    "args, esperado",
    [
        ((None, None, 9, 6, 9.0, 6, 2), "faltante"),
        ((None, None, None, 0, None, 0, 3), "no_aplica"),
        ((5, None, 9, 6, 8.0, 7, 2), "no_retomado"),
        ((5, None, 9, 4, 8.0, 7, 2), "previo"),  # 4 de 8 es empate: no alcanza el consenso de la spec
        ((5, 10, 9, 6, 8.0, 7, 2), "retomado"),
        ((3, 9, None, 0, 10.5, 2, 1), "retomado"),  # la primaria salvadoreña no se juzga como «adelantada»
        ((11, 11, 9, 6, 9.0, 6, 2), "tardio"),
        ((10, 10, 9, 6, 9.0, 6, 2), "alineado"),
        ((9, 9, None, 0, None, 0, 5), "solo_especializacion"),
        ((9, 9, None, 2, 11.0, 2, 1), "adelantado"),
    ],
)
def test_clase_de(args, esperado):
    assert contraste.clase_de(*args) == esperado


@pytest.mark.parametrize(
    "texto, esperado",
    [
        ("4.2. Calcula la velocidad del sonido y explica su relación con la densidad", "aplicar"),
        ("Describir la estructura del átomo", "recordar"),
        ("Diseñar una investigación para medir la aceleración", "razonar"),
        ("Explicar la fotosíntesis", "aplicar"),  # TIMSS: explicar es aplicar
        ("Resuelve problemas de cinemática", "aplicar"),
        ("La célula y sus partes", "sin_verbo"),
    ],
)
def test_demanda_por_verbos(texto, esperado):
    from goes_science_kg.internacional import profundidad

    assert profundidad.demanda(texto) == esperado


def test_umbral_de_la_spec():
    assert contraste.MIN_PAISES == 5  # spec 11: «≥ 5 de 9 países»


def test_generar_json_no_altera_el_esquema(monkeypatch, tmp_path):
    import copy as _copy
    import json as _json

    class Respuesta:
        text = '{"ok": true}'

    class Modelos:
        def generate_content(self, model, contents, config):
            config.response_schema["mutado"] = True  # simula lo que hace el SDK
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
    assert etiquetar._normalizar("CON:inventado", voc, {}) == "CON:inventado"  # no se inventan códigos


def test_catalogo_de_etiquetado_congelado(monkeypatch):
    """Keep tagging prompts bound to the frozen vocabulary rather than mutable live concepts."""
    etiquetar.catalogo_congelado.cache_clear()
    monkeypatch.setattr(conceptos, "vocabulario", lambda: (_ for _ in ()).throw(AssertionError("vocabulario vivo")))
    texto = etiquetar._catalogo("quimica")
    assert "CON:quimica/configuracion-electronica" in texto
    assert "distribucion-electronica-por-niveles" not in texto  # el concepto nuevo entra por la capa de divisiones


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


@pytest.mark.parametrize("cuenta", ["otra@ejemplo.com", None])
def test_no_se_gasta_con_otra_cuenta(monkeypatch, cuenta):
    """Reject paid calls when the ADC identity differs from the configured GOEs account."""
    from typer.testing import CliRunner

    from goes_science_kg import cli

    llamados = []
    monkeypatch.setattr(etiquetar, "pendientes", lambda grupos: 3)
    monkeypatch.setattr(etiquetar, "etiquetar", lambda *a, **k: llamados.append(a))
    monkeypatch.setattr(vertex, "cuenta_adc", lambda: cuenta)
    r = CliRunner().invoke(cli.app, ["internacional", "etiquetar", "JP", "--confirmar"])
    assert r.exit_code == 1 and "cuenta GOES" in r.output and not llamados


# -- Doble lectura de 2.°–8.° (spec 12, método v2) ----------------------------------------------------------------
def test_los_dos_tramos_usan_doble_lectura():
    """Apply the documented dual-reading method to both historical grade bands."""
    from goes_science_kg.internacional import tramo

    assert tramo.TRAMOS["2_8"].lectura_doble and tramo.TRAMOS["9_11"].lectura_doble


def test_nucleo_parcial_cuenta_en_la_presencia_laxa_y_no_en_la_solida():
    """Count optional core tracks in broad presence without asserting solid universal coverage."""

    # Historical test notes:
    # países y no en la sólida: los puntos de presencia sólida solo suman con el núcleo pleno.
    from goes_science_kg.internacional import consenso

    voc = {"CON:x": {"nombre": "x", "asignatura": "fisica"}}
    objs = [
        {"id": f"o{i}", "pais": "SG", "nivel": "nucleo_parcial", "grado_sv_min": 9, "grado_sv_max": 10}
        for i in range(3)
    ]
    etq = {o["id"]: {"principales": ["CON:x"], "secundarios": [], "confianza": "alta"} for o in objs}
    from goes_science_kg.internacional import tramo

    anterior = tramo.actual().clave
    tramo.usar("9_11")
    try:
        r = consenso._consenso(objs, etq, voc)
    finally:
        tramo.usar(anterior)
    fila = r["conceptos"][0]["paises"]["SG"]
    assert fila["primer_grado_nucleo"] is not None and fila["primer_grado_nucleo_solido"] is None
    assert "SG" in r["paises_con_nucleo_por_grado"][9]


def test_lecturas_sin_desajuste_no_quedan_inciertas(monkeypatch):
    from goes_science_kg.internacional import contraste

    p = {"amplio": 5, "amplio_en_tramo": 9, "estricto": 9, "estricto_en_tramo": 9}
    c = {
        "paises": {},
        "n_nucleo_en_tramo": 6,
        "n_nucleo_foco": 6,
        "n_nucleo": 6,
        "n_nucleo_solido": 6,
        "mediana_primer_grado_nucleo": 9.0,
        "mediana_primer_grado_nucleo_solido": 9.0,
        "nucleo_hasta_grado": {},
        "nucleo_solido_hasta_grado": {},
    }
    clase, lect = contraste.clase_doble(p, None, (9, 10, 11))
    assert clase == lect["amplia"] == lect["estricta"]
    # Dos lecturas distintas que no afirman desajuste: gana la estricta y se marca.
    monkeypatch.setattr(contraste, "clase_de", lambda *a, **k: "retomado" if a[0] == 5 else "alineado")
    monkeypatch.setattr(contraste, "_g_cons", lambda *a, **k: None)
    clase, lect = contraste.clase_doble(p, c, (9, 10, 11))
    assert clase == "alineado" and lect.get("sin_desajuste")
    # Si una lectura afirma un desajuste, sigue incierto.
    monkeypatch.setattr(contraste, "clase_de", lambda *a, **k: "retomado" if a[0] == 5 else "tardio")
    assert contraste.clase_doble(p, c, (9, 10, 11))[0] == "incierto"


def test_presencia_solida():
    from goes_science_kg.internacional.consenso import primer_grado_solido

    assert primer_grado_solido([(5, 2)]) == 5  # un principal
    assert primer_grado_solido([(7, 1), (4, 1)]) == 7  # dos secundarios: cuenta el segundo
    assert primer_grado_solido([(3, 1)]) is None  # una etiqueta secundaria suelta no basta


def test_menos_de_3_paises_no_fechan():
    # V2 en 4.°, un solo país en 7.°: con la regla simple sería «adelantado»; con doble lectura no hay referente
    assert contraste.clase_de(4, 4, None, 1, 7.0, 1, 0, (2, 3, 4, 5, 6, 7, 8)) == "adelantado"
    assert contraste.clase_de(4, 4, None, 1, 7.0, 1, 0, (2, 3, 4, 5, 6, 7, 8), n_mediana=1) == "sin_referente"


def _consenso(g_laxo, g_solido, med=6.0, med_solida=6.0, n=6, n_solido=6):
    grados = (2, 3, 4, 5, 6, 7, 8)

    def fila(g0, paises):
        return {str(g): (paises if g0 is not None and g >= g0 else []) for g in grados}

    seis = ["AU", "EE", "ENG", "JP", "KR", "TW"]
    return {
        "paises": {},
        "n_nucleo_en_tramo": n,
        "n_nucleo_foco": n_solido,
        "n_nucleo": n,
        "n_nucleo_solido": n_solido,
        "mediana_primer_grado_nucleo": med,
        "mediana_primer_grado_nucleo_solido": med_solida,
        "nucleo_hasta_grado": fila(g_laxo, seis),
        "nucleo_solido_hasta_grado": fila(g_solido, seis),
        "proporcion_nucleo_hasta_grado": {k: len(v) / 9 for k, v in fila(g_laxo, seis).items()},
        "proporcion_nucleo_solido_hasta_grado": {k: len(v) / 9 for k, v in fila(g_solido, seis).items()},
    }


def _pres(amplio, estricto):
    en = lambda g: g if g is not None and g <= 8 else None  # noqa: E731
    return {"amplio": amplio, "estricto": estricto, "amplio_en_tramo": en(amplio), "estricto_en_tramo": en(estricto)}


def test_clase_doble_solo_afirma_lo_que_resiste_las_dos_lecturas():
    grados = (2, 3, 4, 5, 6, 7, 8)
    # Tardío firme: la V2 no lo tiene antes ni con una etiqueta suelta y los países lo dan sólido en 3.°
    assert contraste.clase_doble(_pres(6, 6), _consenso(3, 3), grados)[0] == "tardio"
    # Una etiqueta suelta de la V2 en 3.° (factores bióticos, campo magnético): ya no se afirma «tardío»
    clase, lect = contraste.clase_doble(_pres(3, 6), _consenso(3, 3, med=3.5, med_solida=3.5), grados)
    assert clase == "incierto" and lect == {"amplia": "alineado", "estricta": "tardio"}
    # Los países solo lo tienen como etiqueta secundaria suelta (ley de Coulomb): tampoco
    assert contraste.clase_doble(_pres(9, 9), _consenso(7, None), grados)[0] == "incierto"
    # Sin ningún país: «sin referente» solo si la V2 lo enseña de forma sólida en el tramo (leyes de Kepler)
    assert contraste.clase_doble(_pres(4, 4), None, grados)[0] == "sin_referente"
    assert contraste.clase_doble(_pres(4, 11), None, grados) == (
        "incierto",
        {"amplia": "sin_referente", "estricta": "posterior"},
    )


def test_busqueda_de_texto():
    c = {"nombre": "Sustancias puras: elementos y compuestos", "sinonimos": ["elementos y compuestos"]}
    fr = contraste.frases(c)
    assert ("sustan", "pura") in fr and ("elemen", "compue") in fr
    assert contraste.aparece(fr, "Clasifica las sustancias puras y las mezclas")
    assert contraste.aparece(fr, "Diferencia elementos de compuestos químicos")
    assert not contraste.aparece(fr, "Reconoce los elementos de la tabla periódica")
    assert not contraste.aparece(fr, "Los elementos del paisaje cambian; los suelos están compuestos de rocas")  # lejos
    # una palabra suelta no es una frase: «pila» no basta para «celdas galvánicas»
    assert contraste.frases({"nombre": "Celdas galvánicas", "sinonimos": ["pila"]}) == [("celda", "galvan")]


def test_partes_validas_y_ampliar():
    from goes_science_kg.internacional.consenso import ampliar

    voc = conceptos.vocabulario()
    partes = conceptos.partes()
    assert partes
    for r in partes:
        assert r["parte"] in voc and r["todo"] in voc and r["parte"] != r["todo"], r
        assert r["revisado_por"] and r["justificacion"], r
    assert {(r["todo"], r["parte"]) for r in partes}.isdisjoint({(r["parte"], r["todo"]) for r in partes})  # sin ciclos
    assert "CON:fisica/conservacion-energia" in ampliar(["CON:fisica/conservacion-energia-mecanica"])
    assert "CON:fisica/conservacion-energia-mecanica" not in ampliar(["CON:fisica/conservacion-energia"])


@pytest.mark.parametrize(
    "grado_pais, esperado",
    [
        ("First school stage", (2, 3)),  # sin distinguir mayúsculas (antes caía en el rango del documento)
        ("second school stage", (4, 6)),
        ("P5 Foundation", (5, 5)),  # la clave con un agregado
        ("P4-P6", (4, 6)),  # varias claves: el rango que las cubre
        ("Units 1 and 2", (2, 2)),  # plural con lista de números (AU Senior Secondary)
        ("", (2, 6)),  # sin grado del país: el rango del documento
    ],
)
def test_grados_sv_del_catalogo(grado_pais, esperado):
    d = {
        "grado_sv": [2, 6],
        "grados_pais": {
            "first school stage": [2, 3],
            "second school stage": [4, 6],
            "P4": 4,
            "P5": 5,
            "P6": 6,
            "Unit 1": 2,
            "Unit 2": 2,
        },
    }
    assert extraer.grados_sv(d, grado_pais) == esperado


def test_metadatos_de_2_8_ya_corregidos():
    """Require corrected grade metadata to remain idempotent in the earlier-grade corpus."""
    import json

    from goes_science_kg.internacional import tramo

    t = tramo.TRAMOS["2_8"]
    docs = {d["id"]: d for d in cargar(t.config)["documentos"]}
    for pais in ("EE", "SG", "HK"):
        for o in json.loads((ruta(t.objetivos) / f"{pais}.json").read_text(encoding="utf-8")):
            if o["documento"] in docs:
                assert (o["grado_sv_min"], o["grado_sv_max"]) == extraer.grados_sv(
                    docs[o["documento"]], o.get("grado_pais", "")
                ), o["id"]
    assert "hk_s1_3" in cargar(t.config)["extension_en_cursiva"]


def test_ajustes_de_busqueda_quitan_falsos_positivos_y_agregan_frases():
    """Reject documented lexical false positives and retain explicitly reviewed search phrases."""

    # Historical test notes:
    # crítico; al concepto virus le faltaba una frase. Los ajustes solo afectan la búsqueda del contraste.
    from goes_science_kg import conceptos

    voc = conceptos.vocabulario()
    assert ("reacci", "cadena") not in contraste.frases(voc["CON:fisica/fision-fusion-nuclear"])
    assert ("angulo", "critic") not in contraste.frases(voc["CON:fisica/reflexion-interna-total"])
    assert ("viru", "infecc") in contraste.frases(voc["CON:biologia/virus"])
    assert ("reacci", "cadena") in contraste.frases({"nombre": "x", "sinonimos": ["reacción en cadena"]})


def test_el_antecedente_de_9_11_suma_el_nucleo_de_2_8_sin_duplicar():
    """Include earlier core evidence without duplicating country objectives across grade bands."""

    # Historical test notes:
    # 9.°–11.°: solo el núcleo (sin la Extension Part de HK) y sin los documentos que el tramo ya tiene (kr_jung).
    from goes_science_kg.internacional import consenso, tramo

    tramo.usar("9_11")
    try:
        filas = consenso._antecedente_2_8()
        objetivos = {f["objetivo"] for f in filas}
        assert {f["pais"] for f in filas} <= set(consenso.ANTECEDENTE_2_8)
        assert all(f["grado"] <= 8.5 for f in filas)
        assert not any("-kr_jung-" in o or "-tw_jh-" in o or "-on_snc1w-" in o for o in objetivos)
        assert {
            "pais": "HK",
            "concepto": "CON:fisica/reflexion-interna-total",
            "grado": 7.0,
            "objetivo": "HK-FIS-hk_s1_3-p074-04",
            "puntos": 2,
        } in filas
        tramo.usar("2_8")
        extension = {o["id"] for o in consenso.objetivos() if o["documento"] == "hk_s1_3" and o["nivel"] != "nucleo"}
        assert extension and not extension & objetivos
        assert consenso._antecedente_2_8() == []
    finally:
        tramo.usar("9_11")
