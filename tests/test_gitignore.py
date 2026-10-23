"""Keep private evidence and local state out of Git without hiding public source files."""

import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def repositorio_temporal(tmp_path):
    subprocess.run(["git", "init", "--quiet", str(tmp_path)], check=True, capture_output=True)
    reglas = Path(__file__).parents[1] / ".gitignore"
    (tmp_path / ".gitignore").write_bytes(reglas.read_bytes())
    return tmp_path


@pytest.mark.parametrize(
    "ruta",
    [
        ".env",
        ".env.production",
        "config/.env.local",
        "desarrollo.env",
        ".envrc.local",
        ".direnv/config.json",
        ".aws/credentials",
        ".gcloud/configurations/config_default",
        "application_default_credentials.json",
        "config/service-account-goes.json",
        "config/credentials-local.json",
        "respaldo.sqlite",
        "respaldo.sqlite-wal",
        "respaldo.sqlite-shm",
        "respaldo.db",
        "respaldo.db-journal",
        "originales.xlsx",
        "referencia.pdf",
        "respaldo-ciencias.zip",
        "vectores.npy",
        ".claude/settings.local.json",
        "data/operaciones/registro.sqlite",
        "insumos/v4/malla.json",
        "entregas/privado.json",
        "docs/investigacion/alertas_v4.json",
        "reportes/cobertura_curricular/outputs/entrega.json",
        ".venv/bin/python",
        "src/goes_science_kg/__pycache__/api.cpython-314.pyc",
        "coverage.xml",
        "junit.xml",
    ],
)
def test_datos_y_estado_privado_se_ignoran(repositorio_temporal, ruta):
    resultado = subprocess.run(
        ["git", "-c", "core.excludesFile=/dev/null", "check-ignore", "--no-index", "--", ruta],
        cwd=repositorio_temporal,
        capture_output=True,
        text=True,
    )
    assert resultado.returncode == 0, f"Falta proteger {ruta}: {resultado.stderr}"


@pytest.mark.parametrize(
    "ruta",
    [
        ".env.example",
        "config/.env.example",
        "uv.lock",
        "pyproject.toml",
        "config/datos_ciencias.lock.json",
        "config/almacen_ciencias.yaml",
        "config/materiales_ciencias.lock.json",
        "src/goes_science_kg/api.py",
        "src/goes_science_kg/interfaz/estaticos/producto.js",
        "src/goes_science_kg/interfaz/estaticos/inter-latin.woff2",
        "tests/test_api_interfaz.py",
        "tests/fixtures/contrato.json",
        "docs/badges/coverage.svg",
        "docs/badges/medicion.json",
        "docs/auditoria/inventario.json",
        "docs/auditoria/app-goes-2026.png",
        ".github/workflows/quality.yml",
        ".claude/hooks/guardia_bash.py",
        "reportes/cobertura_curricular/README.md",
    ],
)
def test_codigo_contratos_y_recibos_publicos_permanecen_visibles(repositorio_temporal, ruta):
    resultado = subprocess.run(
        ["git", "-c", "core.excludesFile=/dev/null", "check-ignore", "--no-index", "--", ruta],
        cwd=repositorio_temporal,
        capture_output=True,
        text=True,
    )
    assert resultado.returncode == 1, f"Se oculta un archivo público: {ruta}: {resultado.stdout}"
