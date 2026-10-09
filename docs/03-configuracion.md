# Configuración

## Mapa de archivos

| Archivo | Qué controla | Se versiona |
|---|---|---|
| [`SOUL.md`](../SOUL.md) | Personalidad, idioma y reglas inquebrantables de Hestia | ✅ |
| [`config.yaml`](../config.yaml) | Modelos, voz, MCP, plugins, aprobaciones (config de Hermes) | ✅ |
| [`config/litellm/config.yaml`](../config/litellm/config.yaml) | Qué modelo real hay detrás de cada alias | ✅ |
| [`plugins/hestia_guard/policy.yaml`](../plugins/hestia_guard/policy.yaml) | Qué acciones físicas son libres, piden confirmación o están prohibidas | ✅ |
| [`cron/jobs.json`](../cron/jobs.json) | Tareas programadas (llegan **pausadas**) | ✅ |
| [`skills/`](../skills/) | Habilidades de Hestia | ✅ |
| `.env` | Secretos y URLs | ❌ nunca |
| `USER.md` / `MEMORY.md` (en el perfil) | Lo que Hestia sabe de ti | ❌ datos personales |

## Tu perfil personal (`USER.md`)

Los datos personales **no** van en el repo, que es público. Viven en la memoria del perfil (`~/.hermes/profiles/hestia/memories/USER.md`, o dentro del volumen `hermes-data` en Docker). La forma más fácil de llenarlos es decírselos a Hestia:

> "Hestia, recuerda: vivo en Medellín, estudio Ingeniería de Software en la universidad X, mis materias son…, mis negocios son A (repo github.com/…, sitio …) y B (…), mi presupuesto mensual de mercado es…"

Plantilla sugerida:
```markdown
## Básico
- Nombre: …  · Ciudad: …  · Zona horaria: America/Bogota
- Idiomas: español (principal), inglés
## Universidad
- Universidad/plataforma: …  · Semestre: …  · Materias y horario: …
## Negocios
- Negocio A: repos …, sitio …, workflows n8n …
## Finanzas
- Hoja de gastos: …  · Pagos recurrentes: arriendo (día 5), internet (día 15)…
## Preferencias
- Respuestas por voz: cortas  · Temperatura para dormir: 20 °C
```

## Cambiar modelos
Todo se hace en `config/litellm/config.yaml`. Hermes solo conoce los alias:

| Alias | Por defecto | Uso |
|---|---|---|
| `hestia-smart` | Claude Sonnet 5.5 | Modelo principal |
| `hestia-deep` | Claude Opus 5.5 | Razonamiento profundo |
| `hestia-fast` | Ollama `qwen3.5:4b` | Títulos, búsqueda de sesiones, compresión |
| `hestia-backup` | OpenRouter | Respaldo |

Para que Hestia use un modelo **solo local**, cambia `hestia-smart` a `ollama_chat/qwen3.6:27b` (necesitas 24 GB de VRAM). Hermes recomienda 64k de contexto o más para el modelo principal.

**Enrutamiento por complejidad (opcional):** LiteLLM trae un *auto router* que clasifica cada petición (SIMPLE/MEDIUM/COMPLEX) y la envía al modelo adecuado. Ver la [documentación del auto router](https://docs.litellm.ai/docs/auto_router/). Jev (TypeSafe AI) puede reemplazar al clasificador cuando haya acceso a su API (roadmap, fase 3).

## Activar integraciones por fase
En `config.yaml` → `mcp_servers`, cambia `enabled: false` a `true` cuando tengas las credenciales:

| Servidor | Fase | Requiere |
|---|---|---|
| `homeassistant` | 2 | `HASS_URL`, `HASS_TOKEN`, la integración MCP Server en HA |
| `google_workspace` | 3 | profile `workspace`, `GOOGLE_OAUTH_*` |
| `github` | 3 | `GITHUB_PAT` (fine-grained, solo lectura) |
| `n8n` | 3 | MCP de instancia activado en n8n, `N8N_MCP_URL`, `N8N_MCP_TOKEN` |

`trust: untrusted` hace que **toda herramienta de escritura** de ese servidor (enviar correo, crear issue, ejecutar un workflow) pida tu aprobación.

## Cron
Las tareas de `cron/jobs.json` llegan **pausadas**. Actívalas:
```bash
hermes -p hestia cron list
hermes -p hestia cron resume hestia-briefing
# o desde Telegram: /cron
```
Crea las tuyas en lenguaje natural: *"Hestia, todos los viernes a las 6 pm recuérdame revisar las finanzas"*.

## Política del guardián
Edita [`plugins/hestia_guard/policy.yaml`](../plugins/hestia_guard/policy.yaml). Por ejemplo, para que el enchufe del calentador siempre pida confirmación:
```yaml
confirmar:
  - switch.turn_on        # o crea una entrada por entity en una versión futura
```
Ver el estado en el chat: `/guard`. Después de leer un correo sospechoso: `/new` para empezar limpio, o `/guard limpiar` si ya lo revisaste.
