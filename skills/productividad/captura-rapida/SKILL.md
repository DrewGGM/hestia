---
name: captura-rapida
description: Capturar al vuelo ideas, tareas, recordatorios y notas dichas por voz o texto y archivarlas en el lugar correcto (Google Tasks, calendario, memoria o nota). Úsala cuando el usuario diga "recuérdame…", "anota…", "tengo una idea…", "agrega a mis tareas…", "remind me to…".
version: 1.0.0
metadata:
  hermes:
    tags: [productividad, tareas, notas]
---

# Captura rápida

Clasifica la frase y guárdala **sin preguntar** salvo que falte algo imprescindible:

| Tipo | Señales | Destino |
|---|---|---|
| Recordatorio con hora | "recuérdame mañana a las 3…" | Cron de Hermes (one-shot) que avisa por Telegram y por el satélite si está en casa |
| Tarea | "tengo que…", "agrega a pendientes" | Google Tasks (lista según el contexto: Personal / Universidad / el negocio mencionado) |
| Evento | fecha + hora + con quién o dónde | Google Calendar. **Confirma** antes de invitar a otras personas |
| Idea / nota | "se me ocurrió…", "anota que…" | Nota en la memoria o en el proyecto correspondiente |
| Preferencia personal | "no me gusta…", "prefiero…" | Memoria del usuario (`USER.md`) |

- Interpreta las fechas relativas en la zona horaria del usuario ("el viernes" = el próximo viernes).
- Responde con una sola línea: "Anotado: pagar el arriendo, viernes 9:00."
