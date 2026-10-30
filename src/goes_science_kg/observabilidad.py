"""Configure terminal logging with explicit success, warning, and failure levels."""

import logging
import os
import time
from functools import wraps
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme


def configurar_logging(*, nivel: str = "INFO", archivo: Path | None = None) -> None:
    """Configure only the product logger without changing third-party SDK logging."""
    logger = logging.getLogger("goes_science_kg")
    logger.setLevel(nivel)
    logger.propagate = False
    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)
    tema = Theme(
        {
            "logging.level.info": "green",
            "logging.level.warning": "yellow",
            "logging.level.error": "bold red",
            "logging.level.critical": "bold red",
        }
    )
    consola = RichHandler(
        console=Console(stderr=True, theme=tema), show_path=False, markup=False, rich_tracebacks=False
    )
    consola.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(consola)
    if archivo:
        archivo.parent.mkdir(parents=True, exist_ok=True)
        salida = logging.FileHandler(archivo, encoding="utf-8")
        salida.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
        logger.addHandler(salida)
    if os.environ.get("NO_COLOR"):
        consola.console.no_color = True


def instrumentar_cli(app) -> None:
    """Instrument CLI callbacks while preserving their signatures and exit behavior."""
    logger = logging.getLogger("goes_science_kg.cli")

    def envolver(funcion, nombre):
        @wraps(funcion)
        def ejecutar(*args, **kwargs):
            if not logging.getLogger("goes_science_kg").handlers:
                configurar_logging()
            inicio = time.perf_counter()
            logger.info("%s: inicio", nombre)
            try:
                resultado = funcion(*args, **kwargs)
            except Exception as error:
                codigo = getattr(error, "exit_code", None)
                nivel = logging.WARNING if codigo is not None else logging.ERROR
                logger.log(nivel, "%s: terminó con %s", nombre, type(error).__name__)
                raise
            logger.info("%s: completado en %.3f s", nombre, time.perf_counter() - inicio)
            return resultado

        return ejecutar

    def recorrer(grupo, prefijo):
        for comando in grupo.registered_commands:
            if comando.callback is not None:
                nombre = f"{prefijo} {comando.name or comando.callback.__name__}"
                comando.callback = envolver(comando.callback, nombre)
        for hijo in grupo.registered_groups:
            recorrer(hijo.typer_instance, f"{prefijo} {hijo.name}")

    recorrer(app, "gskg")
