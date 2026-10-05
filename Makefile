.PHONY: instalar temas grafo validar fichas exportar pruebas lint todo

instalar:
	uv sync --extra dev --extra pdf --extra analisis

temas:
	uv run gskg temas

grafo:
	uv run gskg grafo construir

validar:
	uv run gskg grafo validar

fichas:
	uv run gskg fichas

exportar:
	uv run gskg grafo exportar

pruebas:
	uv run pytest -q

lint:
	uv run ruff check src tests

todo: grafo validar fichas pruebas lint
