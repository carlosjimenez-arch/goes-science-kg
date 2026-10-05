.PHONY: instalar temas grafo validar fichas exportar pruebas lint grados evaluar brechas todo progresion propuestas

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

todo: grafo validar fichas grados brechas progresion pruebas lint

brechas:
	uv run gskg brechas

progresion:
	uv run gskg progresion

# Ciclos con propuesta (asignatura:desde:hasta). Simula cada una sobre el grafo actual, rehace su Excel y el resumen.
CICLOS = biologia:2:4 biologia:5:8 biologia:10:11 fisica:2:4 fisica:5:8 fisica:10:11 quimica:2:4 quimica:5:8 \
	quimica:10:11 ciencias_tierra_espacio:2:4 ciencias_tierra_espacio:5:8

propuestas:
	@for c in $(CICLOS); do \
		a=$${c%%:*}; r=$${c#*:}; d=$${r%%:*}; h=$${r#*:}; \
		uv run gskg propuesta simular $$a $$d $$h > /dev/null && uv run gskg propuesta excel $$a $$d $$h > /dev/null \
			|| exit 1; \
	done
	uv run gskg propuesta resumen
