"""CLI `gskg`: composición de grupos, con un único punto de entrada público.

Cada grupo adapta argumentos de terminal a los casos de uso del dominio; los imports
de dependencias opcionales se mantienen dentro del comando que las necesita.
"""

from goes_science_kg.cli import (
    alineacion,
    alinear,
    artefactos,
    bucle,
    catalogo,
    conceptos,
    datos,
    grados,
    grafo,
    internacional,
    investigacion,
    juicios,
    lotes,
    mejoras,
    motor,
    panel,
    producto,
    propuesta,
    refuerzo,
    revision,
    tutor,
    unidades,
)
from goes_science_kg.cli.principales import app
from goes_science_kg.observabilidad import instrumentar_cli

__all__ = ["app"]

app.add_typer(grafo.app, name="grafo")
app.add_typer(artefactos.app, name="artefactos")
app.add_typer(datos.app, name="datos")
app.add_typer(refuerzo.app, name="refuerzo")
app.add_typer(catalogo.app, name="catalogo")
app.add_typer(alinear.app, name="alinear")
app.add_typer(alineacion.app, name="alineacion")
app.add_typer(conceptos.app, name="conceptos")
app.add_typer(grados.app, name="grados")
app.add_typer(propuesta.app, name="propuesta")
app.add_typer(tutor.app, name="tutor")
app.add_typer(lotes.app, name="lotes")
app.add_typer(revision.app, name="revision")
app.add_typer(panel.app, name="panel")
app.add_typer(bucle.app, name="bucle")
app.add_typer(internacional.app, name="internacional")
app.add_typer(motor.app, name="motor")
app.add_typer(investigacion.app, name="investigacion")
app.add_typer(producto.app, name="producto")
producto.app.add_typer(unidades.app, name="unidades")
producto.app.add_typer(mejoras.app, name="mejoras")
producto.app.add_typer(juicios.app, name="juicios")

instrumentar_cli(app)
