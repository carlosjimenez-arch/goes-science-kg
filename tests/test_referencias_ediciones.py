"""Require researched source editions to match before publishing an ingestion batch."""

from __future__ import annotations

import hashlib
import ssl
from urllib.request import HTTPSHandler

import pytest

from goes_science_kg.ingesta.referencias import FuentePublica, RepositorioReferencias


@pytest.fixture
def fuente():
    return FuentePublica(
        id="curriculo",
        titulo="Currículo de prueba",
        institucion="Emisor de prueba",
        version_documental="edicion-fijada",
        estado_publicacion="publicado",
        url_catalogo="https://www.mext.go.jp/catalogo",
        url_documento="https://www.mext.go.jp/curriculo.pdf",
    )


def test_descarga_verifica_tls_y_anade_certifi_sin_transmitir_payload(monkeypatch, fuente):
    import certifi

    import goes_science_kg.ingesta.referencias as modulo

    cargas = []
    original = ssl.SSLContext.load_verify_locations

    def registrar(contexto, *args, **kwargs):
        cargas.append(kwargs.get("cafile", args[0] if args else None))
        return original(contexto, *args, **kwargs)

    monkeypatch.setattr(ssl.SSLContext, "load_verify_locations", registrar)

    class Respuesta:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def geturl(self):
            return fuente.url_documento

        def read(self, limite):
            assert limite == modulo.MAX_BYTES + 1
            return b"%PDF-contenido-publico"

    class Apertura:
        def open(self, solicitud, timeout):
            assert solicitud.data is None
            assert set(k.lower() for k in solicitud.headers) == {"user-agent"}
            assert timeout == 45
            return Respuesta()

    def construir(*handlers):
        https = next(h for h in handlers if isinstance(h, HTTPSHandler))
        assert https._context.verify_mode == ssl.CERT_REQUIRED
        assert https._context.check_hostname
        assert any(isinstance(h, modulo._RedireccionOficial) for h in handlers)
        return Apertura()

    monkeypatch.setattr(modulo, "build_opener", construir)
    assert modulo.descargar_pdf(fuente) == (b"%PDF-contenido-publico", fuente.url_documento)
    assert certifi.where() in cargas


@pytest.mark.parametrize("esperadas", [{"ajena": "a" * 64}, {"curriculo": "a" * 63}, {"curriculo": True}])
def test_huellas_invalidas_no_crean_almacen_ni_hacen_red(tmp_path, monkeypatch, fuente, esperadas):
    def prohibida(*args, **kwargs):
        pytest.fail("No debe descargar una selección inválida")

    monkeypatch.setattr("goes_science_kg.ingesta.referencias.descargar_pdf", prohibida)
    repo = RepositorioReferencias(tmp_path / "referencias")
    with pytest.raises(ValueError, match="huellas esperadas"):
        repo.incorporar([fuente], descargar=True, sha256_esperados=esperadas)
    assert not repo.raiz.exists()


def test_pdf_distinto_rechaza_antes_del_parser_y_de_publicar(tmp_path, monkeypatch, fuente):
    import goes_science_kg.ingesta.referencias as modulo

    monkeypatch.setattr(modulo, "descargar_pdf", lambda f: (b"%PDF-cambio", f.url_documento))

    def parser_prohibido(*args, **kwargs):
        pytest.fail("El PDF de otra edición no debe llegar al parser")

    monkeypatch.setattr(RepositorioReferencias, "_extraer", parser_prohibido)
    repo = RepositorioReferencias(tmp_path / "referencias")
    with pytest.raises(ValueError, match="SHA-256 esperado"):
        repo.incorporar([fuente], descargar=True, sha256_esperados={fuente.id: "a" * 64})
    assert not repo.archivo_manifest.exists()
    assert not (repo.raiz / "objetos").exists()


def _pdf(clave=None, permisos=None):
    from io import BytesIO

    from pypdf import PdfWriter
    from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

    escritor = PdfWriter()
    pagina = escritor.add_blank_page(width=600, height=800)
    tipo = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    pagina[NameObject("/Resources")] = DictionaryObject(
        {NameObject("/Font"): DictionaryObject({NameObject("/F1"): escritor._add_object(tipo)})}
    )
    texto = DecodedStreamObject()
    texto.set_data(b"BT /F1 12 Tf 50 750 Td (Scientific inquiry.) Tj ET")
    pagina[NameObject("/Contents")] = escritor._add_object(texto)
    if clave is not None:
        escritor.encrypt(
            user_password=clave,
            owner_password="propietario-sintetico",
            permissions_flag=permisos,
            algorithm="RC4-128",
        )
    salida = BytesIO()
    escritor.write(salida)
    return salida.getvalue()


def test_lote_con_segunda_edicion_incorrecta_no_publica_manifiesto(tmp_path, monkeypatch, fuente):
    pdf = _pdf()
    sha = hashlib.sha256(pdf).hexdigest()
    segunda = fuente.model_copy(update={"id": "segunda"})
    monkeypatch.setattr("goes_science_kg.ingesta.referencias.descargar_pdf", lambda f: (pdf, f.url_documento))
    repo = RepositorioReferencias(tmp_path / "referencias")
    with pytest.raises(ValueError, match="SHA-256 esperado"):
        repo.incorporar(
            [fuente, segunda],
            descargar=True,
            sha256_esperados={fuente.id: sha, segunda.id: "0" * 64},
        )
    assert not repo.archivo_manifest.exists()
    # El objeto content-addressed del primer documento puede existir; no es una edición publicada.
    manifest = repo.incorporar([fuente], descargar=True, sha256_esperados={fuente.id: sha})
    assert manifest.referencias[fuente.id].sha256 == sha

    def sin_red(*args, **kwargs):
        pytest.fail("La comprobación local no hace red")

    monkeypatch.setattr("goes_science_kg.ingesta.referencias.descargar_pdf", sin_red)
    assert repo.incorporar([fuente], sha256_esperados={fuente.id: sha}) == manifest
    with pytest.raises(ValueError, match="edición esperada"):
        repo.incorporar([fuente], sha256_esperados={fuente.id: "0" * 64})


@pytest.mark.parametrize("clave,extraer,admitido", [("", True, True), ("", False, False), ("privada", True, False)])
def test_cifrado_abierto_con_permiso_de_extraccion_no_requiere_reescribir_pdf(fuente, clave, extraer, admitido):
    from pypdf.constants import UserAccessPermissions

    permisos = UserAccessPermissions.PRINT | (UserAccessPermissions.EXTRACT if extraer else 0)
    contenido = _pdf(clave, permisos)
    original = hashlib.sha256(contenido).hexdigest()
    if not admitido:
        with pytest.raises(ValueError):
            RepositorioReferencias._extraer(fuente, contenido, fuente.url_documento)
    else:
        registro, paginas = RepositorioReferencias._extraer(fuente, contenido, fuente.url_documento)
        assert registro.sha256 == original and registro.paginas == 1
        assert b"Scientific inquiry" in paginas
    assert hashlib.sha256(contenido).hexdigest() == original
