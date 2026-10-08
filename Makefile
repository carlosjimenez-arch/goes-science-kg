.PHONY: instalar temas grafo validar fichas exportar pruebas lint grados evaluar brechas todo progresion propuestas \
	internacional internacional-ia

instalar:
	uv sync --extra dev --extra pdf --extra analisis --extra rag --extra api --extra vertex

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

# Secuencia del proceso (cada paso usa lo que deja el anterior):
#   1. temas            mallas del MINED → data/interim/temas.json
#   2. grafo, validar   temas + vocabulario + prerrequisitos + países → data/grafo/
#   3. fichas, grados, brechas, progresion   lecturas del grafo por asignatura y por grado
#   4. internacional    contraste de 9.°–11.° con la malla V2 (usa vocabulario y prerrequisitos; caché de Vertex)
#   5. pruebas, lint    incluye la prueba de que data/grafo/ está al día y de que las salidas son deterministas
# La capa de conceptos (gskg conceptos …) y las propuestas (make propuestas) son pasos con revisión: no van en `todo`.
todo: temas grafo validar fichas grados brechas progresion internacional pruebas lint

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

# Contraste internacional: solo reconstruye desde lo extraído y etiquetado (no llama a Vertex).
internacional:
	uv run gskg internacional construir

# Extracción y etiquetado con Vertex AI (credenciales de gcloud). Lo que ya está en caché no se vuelve a pagar.
internacional-ia:
	uv run gskg internacional extraer
	uv run gskg internacional etiquetar
	uv run gskg internacional construir
