from goes_science_kg.disciplinas import asignatura_de_objetivo, asignatura_de_tema


def test_objetivos():
    assert asignatura_de_objetivo("T8_27-B1.2") == "biologia"
    assert asignatura_de_objetivo("T4_27-P1.1") == "quimica"
    assert asignatura_de_objetivo("T4_27-P3.1") == "fisica"
    assert asignatura_de_objetivo("TA-M1.1") == "fisica"
    assert asignatura_de_objetivo("PISA-F2") == "quimica"
    assert asignatura_de_objetivo("PISA-T7") == "ciencias_tierra_espacio"
    assert asignatura_de_objetivo("PISA-EP3") is None


def test_temas():
    assert asignatura_de_tema("fisica", None, None) == ("fisica", "malla")
    assert asignatura_de_tema("ciencias", {"obj1": "T8_27-C3.1"}, None) == ("quimica", "timss")
    assert asignatura_de_tema("ciencias", {"obj1": "FUERA"}, {"cont1": "PISA-V3"}) == ("biologia", "pisa")
    assert asignatura_de_tema("ciencias", {"obj1": "FUERA"}, None) == (None, "pendiente")
