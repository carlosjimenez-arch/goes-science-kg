---
name: revision-humana
description: Exporta a CSV lo que debe revisar el equipo de Ciencias del MINED (confianza baja, casos límite, propuestas) y reimporta sus decisiones al grafo con revisado_por. Usar al cerrar cada fase o cuando el usuario traiga un CSV revisado.
---

# Revisión humana

1. **Exportar** a `asignaturas/<x>/revision/<fecha>_<tema>.csv`, con estas columnas:
   `id, tipo_arista, origen, origen_texto, destino, destino_texto, confianza, justificacion,
   decision (aceptar|cambiar|rechazar), nuevo_destino, comentario, revisado_por`.
   Ordena por asignatura, grado y confianza. Pon los casos límite primero.
2. Escribe un README corto en esa carpeta explicando cómo llenar el CSV, en lenguaje no técnico.
3. **Reimportar**: valida el CSV (los códigos existen y la decisión es válida) y guarda las decisiones en
   `data/interim/revisiones/<fecha>.json`. `construir.py` aplica las revisiones **después** de la IA:
   la decisión humana gana y la arista lleva `revisado_por`.
4. Nunca reclasifiques con IA algo que ya tenga `revisado_por` sin preguntar.
5. Reconstruye el grafo, vuelve a generar las fichas y reporta cuántas decisiones cambiaron métricas.
