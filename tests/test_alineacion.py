from goes_science_kg.alineacion import _validar_pisa, _validar_timss, pendientes

CATALOGO_PISA = [{"codigo": "PISA-F1", "tipo": "contenido"}, {"codigo": "PISA-V1", "tipo": "contenido"},
                 {"codigo": "PISA-PR1", "tipo": "procedimental"}, {"codigo": "PISA-EP1", "tipo": "epistemico"}]
BIEN = {"confianza": "alta", "justificacion": "Trabaja la estructura de la materia con el modelo de partículas."}


def test_validar_timss():
    codigos = {"T8_27-P1.1", "T8_27-B1.1"}
    assert _validar_timss({**BIEN, "obj1": "T8_27-P1.1", "obj2": ""}, codigos) == []
    assert _validar_timss({**BIEN, "obj1": "FUERA", "obj2": ""}, codigos) == []
    assert _validar_timss({**BIEN, "obj1": "T8_27-X9.9", "obj2": ""}, codigos)          # código inventado
    assert _validar_timss({**BIEN, "obj1": "T8_27-P1.1", "obj2": "T8_27-P1.1"}, codigos)  # obj2 = obj1
    assert _validar_timss({**BIEN, "obj1": "T8_27-P1.1", "justificacion": "palabra " * 16}, codigos)


def test_validar_pisa():
    ok = {**BIEN, "cont1": "PISA-F1", "cont2": "", "conocimiento": "Contenido", "proc": ["PISA-PR1"], "epis": [],
          "contexto": "Global", "area": "Recursos naturales", "demanda": "Media"}
    assert _validar_pisa(ok, CATALOGO_PISA) == []
    assert _validar_pisa({**ok, "cont1": "PISA-PR1"}, CATALOGO_PISA)        # procedimental no es contenido
    assert _validar_pisa({**ok, "epis": ["PISA-PR1"]}, CATALOGO_PISA)       # tipo equivocado
    assert _validar_pisa({**ok, "contexto": "Regional"}, CATALOGO_PISA)     # fuera de la lista cerrada


def test_todo_tema_de_2_a_9_tiene_clasificacion():
    """TIMSS 2027 para 2.°–9.° y PISA 2025 para 7.°–9.°: la previa o la de los temas nuevos de la V2."""
    assert pendientes() == {"timss": [], "pisa": []}
