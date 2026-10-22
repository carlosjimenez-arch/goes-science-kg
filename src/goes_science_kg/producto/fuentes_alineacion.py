"""Rehydrate original reference pages using their pinned extraction profiles."""

from __future__ import annotations

import logging

from goes_science_kg.motor.fuentes import FuentesVerificadas
from goes_science_kg.producto.alineaciones import ArchivoAlineaciones

LOGGER = logging.getLogger(__name__)


class FuentesConAlineaciones(FuentesVerificadas):
    """Rehydrate row-linked alignment evidence using the original extraction profiles."""

    def __init__(self, *args, alineaciones: ArchivoAlineaciones, paginas, **kwargs):
        super().__init__(*args, **kwargs)
        self._paginas_alineacion = paginas
        self._evidencias_alineacion = {}
        for caso in alineaciones.casos:
            for e in caso.preparacion.evidencias:
                if e.version != "referencia":
                    continue
                anterior = self._evidencias_alineacion.get(e.id)
                if anterior is not None and anterior != e:
                    raise ValueError("Una página tiene dos extracciones incompatibles en las alineaciones")
                self._evidencias_alineacion[e.id] = e.model_copy(deep=True)

    def hidratar(self, documento):
        """Resolve verified local or documentary evidence under the alignment-aware source policy."""

        esperada = self._evidencias_alineacion.get(documento.id)
        if esperada is None:
            return super().hidratar(documento)
        try:
            if documento.version != "referencia" or documento.fuente != esperada.fuente:
                raise ValueError("La consulta altera el localizador o papel de la página")
            actual = self._paginas_alineacion.pagina(esperada.fuente["documento"], esperada.fuente["pagina"])
            if actual != esperada:
                raise ValueError("La extracción actual no coincide con la examinada por los lectores")
            return actual
        except (OSError, ValueError, KeyError) as error:
            LOGGER.warning("AMARILLO página de alineación no disponible: %s", type(error).__name__)
            return None
