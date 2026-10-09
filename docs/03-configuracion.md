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

| Alias | Por defecto (vía OpenRouter) | USD por millón de tokens, entrada/salida | Uso |
|---|---|---|---|
| `hestia-smart` | Claude Haiku 5.5 | 0,10 / 0,50 | Modelo principal: chat, casa, briefings |
| `hestia-deep` | Claude Sonnet 5.5 | 2 / 10 | Tareas difíciles: `/model hestia-deep` |
| `hestia-max` | Claude Opus 5.5 | 4 / 20 | Lo máximo, solo cuando lo pidas: `/model hestia-max` |
| `hestia-fast` | Ollama `qwen3.5:4b` (local) | gratis | Títulos, búsqueda de sesiones, compresión |
| `hestia-backup` | Gemini 3.8 Flash | 0,75 / 3,75 | Respaldo si Claude falla (otro proveedor) |

Precios de octubre de 2026. Los vigentes están en [openrouter.ai/models](https://openrouter.ai/models).

### OpenRouter (por defecto)
[OpenRouter](https://openrouter.ai) da acceso a cientos de modelos (Claude, Gemini, GPT, DeepSeek…) con **una sola key** y pago por uso, sin mensualidad.
1. Crea una cuenta en openrouter.ai y recarga créditos (con 5–10 USD alcanza para empezar).
2. Crea una key en [openrouter.ai/keys](https://openrouter.ai/keys) y ponle un **límite de crédito**. Es tu tope de gasto real.
3. Ponla en `.env` como `OPENROUTER_API_KEY`.

### API de Anthropic directa (alternativa)
En `config/litellm/config.yaml`, en cada alias de Claude, comenta las líneas de OpenRouter, descomenta las de *Anthropic directo* y llena `ANTHROPIC_API_KEY`. Pagas un poco menos que por OpenRouter, pero solo tienes Claude.

### ¿Y mi suscripción de Claude Pro/Max?
**No se usa como cerebro de Hestia.** Los términos de Anthropic reservan el login de la suscripción para Claude Code y sus apps, y usarlo en un agente de terceros puede hacer que te suspendan la cuenta. Hestia incluso le impide a Hermes tomar prestado tu login de Claude Code (`auth.adopt_external_logins: false`). Detalles en el [ADR-0005](adr/0005-modelos-y-suscripcion.md).

Lo que sí puedes hacer es **delegarle programación a Claude Code** con tu suscripción. Ver la sección siguiente.

Para que Hestia use un modelo **solo local**, cambia `hestia-smart` a `ollama_chat/qwen3.6:27b` (necesitas 24 GB de VRAM). Hermes recomienda 64k de contexto o más para el modelo principal.

**Enrutamiento por complejidad (opcional):** LiteLLM trae un *auto router* que clasifica cada petición (SIMPLE/MEDIUM/COMPLEX) y la envía al modelo adecuado. Ver la [documentación del auto router](https://docs.litellm.ai/docs/auto_router/). Jev (TypeSafe AI) puede reemplazar al clasificador cuando haya acceso a su API (roadmap, fase 3).

## Claude Code con tu suscripción (programación)
Con esto, cuando le pidas a Hestia *"usa Claude Code para arreglar el test roto de mi-web"*, ella le pasa el encargo al **CLI oficial de Claude Code**, que trabaja en el repo con tu plan Pro/Max. Te pide aprobación antes de cada encargo (skill [`delegar-claude-code`](../skills/desarrollo/delegar-claude-code/SKILL.md)).

**Docker**
1. En `.env`, apunta `HESTIA_WORKSPACE` a la carpeta de tus proyectos (en Windows, con barras normales: `C:/Users/tu-usuario/proyectos`) y reinicia con `docker compose up -d`. Se monta en `/workspace`.
2. En tu PC, en una terminal aparte, corre `claude setup-token`. Inicias sesión en el navegador y te muestra un token `sk-ant-oat01-…` válido por un año.
3. Corre `./scripts/claude-code-login.sh` y pega el token (no se muestra). El script lo guarda en el volumen con permisos 600 y prueba que funciona.

**Nativo (Linux, macOS o WSL)**: instala Claude Code (`npm install -g @anthropic-ai/claude-code`), inicia sesión con `claude` y copia `scripts/claude-hestia` a tu `PATH`. Sin archivo de token, el wrapper usa el login que ya tienes. En Windows nativo usa Docker o WSL para esta función.

**Reglas**
- **Nunca pegues el token en un chat**, tampoco con Hestia.
- Cada encargo pide tu aprobación y muestra el texto exacto que recibirá Claude Code. Si la conversación leyó correos o webs, la delegación se bloquea: revisa y usa `/guard limpiar`, o abre `/new`.
- Claude Code no recibe credenciales de push: los commits quedan locales y el push lo haces tú.
- Si Claude Code se queda sin cupo del plan, Hestia te avisa y no reintenta.
- Para revocar el acceso: borra el token (`docker compose exec -u hermes hestia rm /opt/data/secrets/claude_code_oauth_token`) y revócalo en claude.ai.

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
