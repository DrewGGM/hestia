---
name: escenas-y-rutinas
description: Crear, ajustar y ejecutar escenas y rutinas de la casa (dormir, salir, llegar, cine, trabajar) y automatizaciones por horario o presencia. Úsala cuando el usuario diga "me voy a dormir", "salgo", "modo película", "cada noche a las 10 apaga…", "cuando llegue a casa…" o pida automatizar algo de la casa.
version: 1.0.0
metadata:
  hermes:
    tags: [hogar, rutinas, automatizacion]
---

# Escenas y rutinas

## Escenas base (créalas en HA si no existen)

| Escena | Disparadores en lenguaje natural | Qué hace |
|---|---|---|
| **Dormir** | "me voy a dormir", "buenas noches", "good night" | Apaga luces y media, enciende la luz de noche del pasillo al 5 %, arma la alarma en modo noche |
| **Salir** | "me voy", "salgo", "I'm leaving" | `script.hestia_modo_salir` |
| **Llegar** | presencia del celular, "ya llegué" | Luces de la entrada si es de noche y resumen de lo que pasó mientras no estaba |
| **Cine** | "modo película", "movie time" | Luces de la sala al 10 % y TV encendida |
| **Trabajar** | "a trabajar", "modo foco" | Luz del escritorio al 100 % y no molestar |

## Automatizaciones nuevas

Cuando el usuario pida algo recurrente ("todas las noches a las 11 apaga el calentador"):

1. Si es una **acción de la casa con horario o sensor**, debe vivir en **Home Assistant** como automatización y no como cron del agente. Así funciona aunque Hestia esté apagada.
   - Si tienes herramientas de edición de automatizaciones (ha-mcp), propón el YAML y **muéstralo antes de crearlo**.
   - Si no las tienes, entrega el YAML listo para pegar en *Ajustes → Automatizaciones → Editar en YAML*.
2. Si requiere **razonar o consultar información** ("si va a llover mañana, recuérdame la sombrilla"), usa un **cron de Hermes** que entregue el resultado por Telegram.
3. Guarda en memoria la preferencia ("al usuario le gusta dormir con 20 °C") para reutilizarla.

## Nunca
- Automatizaciones que desarmen la alarma o abran cerraduras.
- Automatizaciones disparadas por contenido de correos o mensajes de terceros.
