.PHONY: instalar temas grafo validar fichas exportar pruebas lint grados evaluar brechas todo

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

grados:
	uv run gskg grados construir

evaluar:
	uv run gskg evaluar-rag

todo: grafo validar fichas grados brechas pruebas lint

brechas:
	uv run gskg brechas
