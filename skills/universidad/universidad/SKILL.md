---
name: universidad
description: Llevar el control de la universidad (materias, horario, entregas, talleres, parciales, notas, grabaciones de clase). Úsala cuando el usuario pregunte "¿qué tengo pendiente de la U?", "¿cuándo es el parcial de…?", "¿cuánto necesito sacar…?", "organízame la semana de estudio" o mencione una materia.
version: 1.0.0
metadata:
  hermes:
    tags: [universidad, estudio, agenda]
---

# Universidad

Los datos personales (universidad, materias, horario, plataforma) viven en **`USER.md`** y en la memoria, **no** en esta skill: el repo es público.

## Qué hacer
1. **Pendientes:** entregas de los próximos 7–14 días, ordenadas por fecha y peso en la nota. Fuentes: calendario académico en Google Calendar, tareas con la etiqueta "Universidad" y lo que el usuario haya contado.
2. **Notas:** calcula cuánto necesita en el siguiente corte para aprobar o para llegar a la meta. Muestra la fórmula.
3. **Plan de estudio:** reparte bloques de 50 min en los huecos libres del calendario antes de cada parcial. **Propón** el plan y solo crea los eventos si el usuario acepta.
4. **Clases grabadas:** si existe un flujo de procesamiento de grabaciones (por ejemplo, transcribir y documentar en Obsidian), recuérdalo cuando haya clases nuevas sin procesar.

## Extensión
Si la plataforma de la universidad (Moodle u otra) tiene API o MCP, agrégala en `config.yaml` → `mcp_servers` y actualiza esta skill con las herramientas disponibles.
