# Revisión del equipo de Ciencias

Cada CSV lista alineaciones hechas con IA que necesitan una decisión humana: primero los temas marcados
**FUERA** (no encajan en ningún objetivo del marco) y luego los de confianza **baja**.

Cómo llenarlo:
1. Lee el tema de la malla (`tema_malla`) y el objetivo asignado (`obj1_texto`, `obj2_texto`).
2. En `decision` escribe **aceptar**, **cambiar** (y pon el código correcto en `nuevo_obj1`/`nuevo_obj2`) o **rechazar**
   (el tema no corresponde a ningún objetivo: queda FUERA).
3. Escribe tu nombre o el del equipo en `revisado_por`.

Los códigos y textos de los objetivos están en `data/referencia/catalogo_acara_senior.json`
(Australian Curriculum Senior Secondary, parafraseado en español).
