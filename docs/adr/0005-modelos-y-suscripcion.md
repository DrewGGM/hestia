# ADR-0005: OpenRouter para el cerebro y la suscripción de Claude solo a través de Claude Code

- **Estado:** aceptada (2026-10-09)
- **Modifica:** [ADR-0003](0003-litellm-router-hibrido.md), en los modelos de cada alias

## Contexto
- Hestia necesita un modelo con buen *tool calling* disponible 24/7 (Telegram, cron, voz). Cada usuario debe poder empezar con una sola key y con un tope de gasto.
- Muchos usuarios ya pagan Claude Pro/Max y preguntan si Hestia puede usar esa suscripción en vez de una API key. Hermes lo soporta técnicamente: acepta `CLAUDE_CODE_OAUTH_TOKEN` y, **por defecto**, toma prestado el login de Claude Code de `~/.claude/.credentials.json`.
- Los [términos de Anthropic](https://code.claude.com/docs/en/legal-and-compliance) (consultados el 2026-10-09) dicen que la autenticación OAuth de los planes Free/Pro/Max es para el uso normal de Claude Code y de las apps propias de Anthropic. Los productos que interactúan con Claude deben usar API key, y Anthropic puede aplicar la restricción sin aviso. A principios de 2026 ya bloqueó tokens de suscripción usados en harnesses de terceros.
- Además, el refresh token de Claude Code es de un solo uso: si Hermes lo toma prestado, el primero que lo renueve le cierra la sesión al otro (issue de Hermes #113023).

## Decisión
1. **El cerebro de Hestia usa OpenRouter por defecto** (una sola key, con tope de gasto configurable en su panel):
   - `hestia-smart` → Claude Haiku 5.5 (día a día; unos 0,10/0,50 USD por millón de tokens)
   - `hestia-deep` → Claude Sonnet 5.5 (bajo demanda: `/model hestia-deep`)
   - `hestia-max` → Claude Opus 5.5 (bajo demanda)
   - `hestia-backup` → Gemini 3.8 Flash (otro proveedor, para tener redundancia real)
   - `hestia-fast` → Ollama local (sin cambios)
   
   La API de Anthropic directa queda como alternativa comentada en `config/litellm/config.yaml`.
2. **Hermes nunca adopta logins externos:** `auth.adopt_external_logins: false` en `config.yaml`.
3. **La suscripción solo se usa a través del CLI oficial de Claude Code, sin modificar**, y para encargos de programación que el usuario pide (skill `delegar-claude-code`):
   - La imagen `hestia-agent` = Hermes oficial + `@anthropic-ai/claude-code` con versión fijada.
   - El token de `claude setup-token` se guarda en un archivo del volumen (`/opt/data/secrets`, permisos 600), no en `.env`, así que Hermes no lo ve en su entorno.
   - El wrapper `claude-hestia` ejecuta Claude Code con un entorno limpio: sin `ANTHROPIC_API_KEY` (nunca factura a la API por accidente), sin los demás tokens y sin credenciales de push.
   - `hestia_guard` pide confirmación para **cada** delegación, mostrando el encargo, y la **bloquea** si la sesión leyó contenido externo.

## Consecuencias
- ✅ Cumple los términos de Anthropic: la suscripción la usa su propio binario, el usuario lo invoca para su propio trabajo y no hay reventa ni intermediación.
- ✅ El chat del día a día cuesta centavos con Haiku. El trabajo pesado de código va al plan que el usuario ya paga.
- ✅ Una sola key (OpenRouter) para empezar. Cambiar a Anthropic directo es editar un archivo.
- ⚠️ Claude Code corre en el mismo contenedor que Hermes: puede leer lo que el usuario `hermes` puede leer. Las mitigaciones son la confirmación humana, el bloqueo por contaminación y el entorno limpio. La separación real (otro contenedor solo con `/workspace`) llega con la separación de privilegios del [ADR-0004](0004-seguridad-acciones-fisicas.md).
- ⚠️ Los límites de Pro/Max suponen uso individual normal: la skill prohíbe delegar desde cron y reintentar en bucle.
- ⚠️ OpenRouter cobra una pequeña comisión al recargar créditos, y algunos modelos `:free` registran los prompts. Hestia no usa modelos `:free`.
