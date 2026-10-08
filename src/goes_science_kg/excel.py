"""Guardado determinista de libros de Excel.

`openpyxl` escribe la hora actual en `docProps/core.xml` (creado y modificado) y en cada entrada del zip, así que el
mismo libro sale con bytes distintos en cada corrida y ensucia los diffs. Aquí se fijan las dos cosas: con los mismos
datos, el archivo es idéntico.
"""

from __future__ import annotations

import io
import re
import zipfile
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from openpyxl.workbook.workbook import Workbook

FECHA_FIJA = datetime(2026, 1, 1)
_FECHA_ZIP = (2026, 1, 1, 0, 0, 0)
_FECHA_XML = rb"2026-01-01T00:00:00Z"
_CORE = re.compile(rb"(<dcterms:(?:created|modified)[^>]*>)[^<]*")


def guardar(wb: Workbook, destino: Path) -> Path:
    """Guarda `wb` en `destino` con fechas fijas. Devuelve la ruta."""
    wb.properties.creator = "goes-science-kg"
    wb.properties.created = wb.properties.modified = FECHA_FIJA
    buf = io.BytesIO()
    wb.save(buf)
    with zipfile.ZipFile(buf) as zin, zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as zout:
        for info in zin.infolist():
            datos = zin.read(info.filename)
            if info.filename == "docProps/core.xml":
                datos = _CORE.sub(rb"\g<1>" + _FECHA_XML, datos)
            entrada = zipfile.ZipInfo(info.filename, date_time=_FECHA_ZIP)
            entrada.compress_type = zipfile.ZIP_DEFLATED
            zout.writestr(entrada, datos)
    return destino
