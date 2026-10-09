# Investigación: cómo construir un JARVIS open-source en 2026

> Informe base del proyecto Hestia, de octubre de 2026. Lo produjeron una investigación profunda con verificación adversarial (5 ángulos, 22 fuentes, 105 afirmaciones extraídas, 25 verificadas por votación 3 a 3, 2 refutadas) y tres investigaciones de seguimiento sobre Hermes Agent, el stack de voz en español y la memoria, el enrutamiento y las integraciones.
>
> Cada sección marca cuánta confianza merece. **[NV]** = no verificado de forma independiente.

## Resumen ejecutivo

1. **No hay que construir un agente desde cero.** En 2026 ya existen runtimes de agente personal maduros. El más completo es **Hermes Agent** (Nous Research, MIT): unas 252k estrellas, releases cada pocos días, más de 21 gateways de mensajería, voz, memoria, skills que el propio agente escribe, cron, MCP y plugins.
2. **Hermes se usa como dependencia, no como fork.** Toda la personalización de Hestia cabe en sus puntos de extensión: skills, plugins, `mcp_servers` y `config.yaml`. Un fork sería una deuda de merges permanente con un upstream que publica cada 2–3 días.
3. **Home Assistant (HA) es la capa de domótica.** No depende de ningún fabricante, porque integra Tuya, Xiaomi, Zigbee, Matter, Thread y Alexa/Google. Se conecta al agente por MCP (`ha-mcp` o el MCP Server integrado) y aporta un pipeline de voz (Assist + Wyoming) para los satélites de cada habitación.
4. **El LLM es híbrido y pasa por LiteLLM.** Las órdenes cortas van a un modelo local en Ollama y lo complejo a Claude. Los modelos locales controlan peor la casa, según la propia documentación de HA, y eso justifica el enrutamiento.
5. **La seguridad es el factor decisivo.** OpenClaw tuvo más de 40k instancias expuestas, CVEs con exploit público y un marketplace de skills con malware. Una prueba académica mostró que un correo o un evento de calendario envenenado puede **abrir ventanas o encender una caldera** a través de un asistente. Por eso Hestia separa privilegios y pide confirmación humana antes de cualquier acción física sensible.
6. **"jev" es Jev, de TypeSafe AI**: un modelo de *decisión*, no de texto, que devuelve booleanos o puntuaciones en 70–500 ms. Sirve para enrutar y para decidir si algo necesita confirmación. Hoy es una API en acceso anticipado y no es open source, así que en Hestia entra como componente **opcional** del enrutamiento, nunca como base.

---

## 1. Frameworks base: comparativa

| Proyecto | Licencia | Tracción (oct-2026) | Qué aporta | Problemas | Veredicto |
|---|---|---|---|---|---|
| **Hermes Agent** (NousResearch/hermes-agent) | MIT | ~252k ★, ~54k forks, v0.21.6 (08-10-2026) | Gateways (Telegram, WhatsApp, Discord, Slack, Signal, Email…), voz con STT/TTS y wake word "Hey Hermes", memoria (MEMORY.md/USER.md + FTS5 + proveedores externos), **skills autogeneradas** con Curator y aprobación opcional, cron, cliente MCP, 7 backends de sandbox, plugins con 27 hooks, plugin oficial de Home Assistant | El AIRQ de Adversa lo califica de riesgo alto (5,17), con controles por defecto débiles. NVD lista 27 CVEs. Usuarios reportan skills creadas desde tareas fallidas y que sobrescribe skills editadas a mano [NV] | ✅ **Runtime base, como dependencia** |
| **OpenJarvis** (open-jarvis/OpenJarvis, Stanford) | Apache-2.0 | ~10,8k ★, v1.0.x | Local-first, mide energía, coste y latencia, optimiza skills con trazas, importa skills de Hermes y OpenClaw | Más plataforma de investigación que producto. Voz, gateways y domótica poco documentados [NV] | 🟡 Fuente de ideas y skills, no base |
| **OpenClaw** (ex Clawdbot/Moltbot) | MIT | Muy popular | Ecosistema enorme de skills | Más de 40.214 instancias expuestas (feb-2026). CVE-2026-25253 (RCE), CVE-2026-25157 y CVE-2026-24763 (escape del sandbox). Secretos en texto plano robados por infostealers. Marketplace con más de 1.184 skills maliciosas (ClawHavoc). Sandbox apagado por defecto | ❌ **Descartado** para algo que controla la casa |
| **Letta / MemGPT** | Apache-2.0 | — | Memoria jerárquica | Imagen Docker sin soporte oficial y MCP solo comunitario | ❌ Sería un segundo runtime innecesario |
| **mem0** | Apache-2.0 | — | Memoria vectorial, autoalojable | OpenMemory MCP posiblemente obsoleto [NV] | 🟡 Disponible como proveedor de memoria **dentro** de Hermes |
| **OpenHands** | MIT | — | Agente de programación | Fuera del alcance de un asistente personal | ❌ |

**Por qué no fork.** `hermes update` resetea `main` a `origin/main` y las ramas propias quedan en "SKIPPED". Upstream publica v0.21.4 → v0.21.5 → v0.21.6 en dos semanas. Todo lo que Hestia necesita ya existe como extensión:
- `skills.external_dirs`: skills cargadas desde este repo.
- Plugins (`plugin.yaml` + `register(ctx)`): herramientas, hooks y comandos propios.
- `mcp_servers`: HA, Google Workspace, GitHub, n8n.
- `config.yaml` + `.env`.

Los bugs de upstream se reportan con un PR a Hermes y, mientras se resuelven, se parchean con un plugin.

Fuentes: [repo Hermes](https://github.com/NousResearch/hermes-agent), [docs Hermes](https://hermes-agent.nousresearch.com/docs/), [AIRQ Adversa](https://airq.adversa.ai/agent/hermes-agent), [OpenJarvis](https://github.com/open-jarvis/OpenJarvis), [Infosecurity: 40k OpenClaw expuestos](https://infosecurity-magazine.com/news/researchers-40000-exposed-openclaw/), [The Register](https://www.theregister.com/2026/01/27/clawdbot_moltbot_security_concerns/), [The Stack: backdoor en skills](https://www.thestack.technology/a-backdoor-was-the-most-downloaded-skill-for-viral-clawdbot-moltbot-and-why-that-matters/), [OpenClaw sandboxing](https://docs.openclaw.ai/gateway/sandboxing), [Letta docker](https://docs.letta.com/v1-sdk/docker/index.md).

## 2. Domótica: Home Assistant como hub (confianza alta)

- **No depende de ningún fabricante.** Dispositivos sueltos (Tuya/SmartLife con LocalTuya o Tuya Local, Xiaomi, Alexa/Google), Zigbee (ZHA o Zigbee2MQTT), Matter y Thread quedan todos como *entidades* de HA. El agente solo habla con HA.
- **Hay dos direcciones de MCP:**
  - **De la casa al agente.** El *MCP Server* integrado de HA (`/api/mcp`, streamable HTTP) expone la API Assist y **solo las entidades expuestas a Assist**. Permite un usuario no admin si se desactiva "Require administrator". La alternativa es **ha-mcp** (homeassistant-ai, MIT, 87 herramientas), mucho más potente porque edita automatizaciones, y por eso mismo más riesgosa: crea su propio token de admin y, si se expone a un agente de conversación, *"hands that power to everyone who can talk to that agent, including anyone within earshot of a voice satellite"*. Tiene modo solo lectura (`/readonly`), políticas de aprobación y backups antes de editar.
  - **Del agente a la casa.** La integración *MCP* (cliente, desde 2025.2) convierte a HA en cliente MCP. Las herramientas de Hestia quedan disponibles para los agentes de conversación de HA, es decir, desde los satélites de voz.
- **Plugin `homeassistant` de Hermes:** `ha_list_entities`, `ha_get_state`, `ha_list_services` y `ha_call_service` por REST. Escucha `state_changed` por WebSocket y **bloquea** `shell_command` y `python_script`.
- **Límites del LLM local en HA:** solo controlan la casa los modelos con *Tools*. *"Smaller models are more likely to make mistakes"*. Se recomienda **exponer menos de 25 entidades** y subir el contexto (8k en la integración frente a 2k por defecto en Ollama).
- **Extended OpenAI Conversation** (jekalmin, ~1,4k ★) sirve para endpoints OpenAI-compatibles, pero su límite de entidades **no** es una barrera de seguridad (afirmación refutada 0-3).

Fuentes: [ha-mcp in-process](https://raw.githubusercontent.com/homeassistant-ai/ha-mcp/master/docs/in-process-server.md), [ha-mcp](https://github.com/homeassistant-ai/ha-mcp), [HA MCP Server](https://www.home-assistant.io/integrations/mcp_server/), [HA MCP client](https://home-assistant.io/integrations/mcp), [HA Ollama](https://home-assistant.io/integrations/ollama), [Hermes HA plugin](https://hermes-agent.nousresearch.com/docs/user-guide/messaging/homeassistant).

## 3. Voz bilingüe ES/EN

### Satélites por habitación
- **Home Assistant Voice PE** (69 USD, ESP32-S3 + XMOS XU316 para cancelación de eco). Wake words en el propio dispositivo: **"Okay Nabu", "Hey Jarvis", "Hey Mycroft"**. Corren localmente con **microWakeWord**, que es más rápido y escala mejor que hacerlo en el servidor (alta).
- Se puede entrenar una wake word propia ("Hey Hestia") con `OHF-Voice/micro-wake-word` y cargarla en el YAML de ESPHome. El proyecto es *early release* y hay reportes de errores de esquema con ESPHome 2026.7.
- **Raspberry Pi:** `wyoming-satellite` está **archivado (27-01-2026)**. Su reemplazo es `linux-voice-assistant` (protocolo ESPHome, Linux, experimental). openWakeWord queda del lado del servidor.
- **Bilingüe en satélites:** el pipeline de HA usa un solo idioma. Desde HA 2025.10 se resuelve con **dos wake words por satélite, cada una con su pipeline**: por ejemplo "Hey Jarvis" en español y "Okay Nabu" en inglés.

### STT (voz a texto)
| Opción | Español | Notas |
|---|---|---|
| **Parakeet TDT 0.6B v3** (sherpa, dentro de `wyoming-faster-whisper`) | WER 3,4–4,4 % | **Detecta el idioma solo**, muy rápido en CPU, CC-BY-4.0. ✅ Recomendado para una GPU de 8 GB, porque deja la VRAM al LLM |
| faster-whisper `large-v3-turbo` | Excelente | Unas 2,7 veces más rápido que large-v3. Con GPU, menos de 1 s por comando [estimado]. La imagen GPU hay que construirla a mano |
| distil-whisper | ❌ | Es solo inglés y no admite sesgo por entidades |
| Moonshine | ❌ | Sin modelo en español verificado. El multilingüe "legacy" no es comercial |

`wyoming-faster-whisper` v3.9 trae `--stt-library auto|faster-whisper|sherpa|…` y `--hass-token` para sesgar el reconocimiento hacia los nombres de tus dispositivos.

### TTS (texto a voz)
| Opción | Notas |
|---|---|
| **Piper** `es_MX-claude-high`, `es_AR-daniela-high` (latino) y voces en inglés | ✅ Local, rápido y gratis. Español e inglés quedan como **dos voces distintas** |
| **ElevenLabs** `eleven_flash_v2_5` | ✅ Premium: unos 200 ms de mediana y **la misma voz en ES y EN** |
| Chatterbox Multilingual (MIT) | 23 idiomas y clonación de voz; la V3 tiene ajuste para español latino. Añade marca de agua |
| Kokoro-82M | Solo 3 voces en español y soporte "thin" |
| XTTS-v2 / F5-TTS | ❌ Licencias no comerciales |

Desde HA 2025.10 el **TTS se transmite en streaming**: la respuesta empieza a sonar en unos 0,5 s.

### Voz en el PC
- **Fase 1:** el *voice mode* de Hermes, con wake word, push-to-talk y barge-in. Es lo que menos código propio exige.
- **Fase 4 (opcional):** un cliente propio con **Pipecat** (BSD-2) y **Smart Turn v3.2** (detección de turno en 23 idiomas, incluido español, unos 12 ms en CPU). Es preferible a LiveKit Agents porque corre sin servidor WebRTC y su detector de turno es abierto.

Fuentes: [voice chapter 6](https://www.home-assistant.io/blog/2024/02/21/voice-chapter-6/), [voice chapter 11](https://www.home-assistant.io/blog/2025/10/22/voice-chapter-11), [wyoming-faster-whisper](https://github.com/OHF-Voice/wyoming-faster-whisper), [wyoming-piper](https://github.com/OHF-Voice/wyoming-piper), [Parakeet v3](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3), [voces Piper](https://huggingface.co/rhasspy/piper-voices/raw/main/voices.json), [micro-wake-word](https://github.com/OHF-Voice/micro-wake-word), [Smart Turn](https://github.com/pipecat-ai/smart-turn), [ElevenLabs models](https://elevenlabs.io/docs/overview/models), [Hermes voice mode](https://hermes-agent.nousresearch.com/docs/user-guide/features/voice-mode).

## 4. LLM híbrido y enrutamiento

- **LiteLLM proxy** (`ghcr.io/berriai/litellm`, **≥1.83.0**: las versiones 1.82.7 y 1.82.8 de PyPI tenían malware que robaba credenciales, y desde 1.83 las imágenes van firmadas con cosign). Da un único endpoint OpenAI-compatible (`:4000`) delante de Ollama, Anthropic y OpenRouter, con `fallbacks`, `context_window_fallbacks` y un *complexity router* (SIMPLE/MEDIUM/COMPLEX/REASONING).
- Hermes también tiene **fallback providers** y **modelos auxiliares** por tarea (compresión, visión…).
- **Modelos locales para 8 GB de VRAM** (RTX 5060 Laptop): `qwen3.5:4b` (unos 3,3 GB) o `gemma4:e4b` para órdenes rápidas. `qwen3.5:9b` entra muy justo junto con otros procesos en GPU. Con 24 GB, `qwen3.6:27b` o `mistral-small3.2:24b`.
- Hermes pide **≥64k de contexto** cuando el modelo principal es Ollama. Por eso en Hestia el modelo **principal es Claude** y el local queda para tareas auxiliares y órdenes simples.
- **Jev (TypeSafe AI)** puede reemplazar al clasificador heurístico ("¿esta petición es simple?", "¿esta acción necesita confirmación?"). Lanzado el 15-09-2026, es una API en acceso anticipado, cerrada. Hay un MCP en Composio y el plugin `jev-use` para Claude Code.

Fuentes: [LiteLLM security update](https://docs.litellm.ai/blog/security-update-march-2026), [LiteLLM reliability](https://docs.litellm.ai/docs/proxy/reliability), [LiteLLM auto router](https://docs.litellm.ai/docs/auto_router/), [Ollama qwen3.5](https://ollama.com/library/qwen3.5), [Hermes providers](https://hermes-agent.nousresearch.com/docs/integrations/providers), [Jev](https://letsdatascience.com/news/typesafe-ai-launches-jev-decision-model-889a38c0), [qué es Jev](https://nexos.ai/blog/what-is-jev/).

## 5. Integraciones (MCP)

| Área | Servidor | Notas |
|---|---|---|
| Google Calendar, Gmail, Drive y Tasks | [taylorwilsdon/google_workspace_mcp](https://github.com/taylorwilsdon/google_workspace_mcp) | MIT, más de 120 herramientas, OAuth 2.1, niveles core/extended/complete y **`--read-only`** |
| GitHub | [github/github-mcp-server](https://github.com/github/github-mcp-server) | Oficial, `ghcr.io/github/github-mcp-server`, `--toolsets` y `--read-only` |
| n8n | MCP nativo de instancia (n8n ≥2.18) o `ghcr.io/czlonkowski/n8n-mcp` | Cada workflow se habilita por separado |
| Home Assistant | MCP Server integrado o `ha-mcp` | Ver la sección 2 |
| Memoria | Nativa de Hermes + **Holographic** (SQLite local) u **Honcho** | Graphiti solo si hace falta un grafo de relaciones |

## 6. Seguridad (confianza alta en la clase de riesgo)

- **Promptware** (Nassi et al., Black Hat USA 2025, [arXiv 2508.12175](https://arxiv.org/pdf/2508.12175)): 14 escenarios en 5 clases (envenenamiento del contexto y de la memoria, mal uso de herramientas, invocación automática de agentes y de apps). El 73 % se calificó de riesgo alto o crítico. Un correo o una invitación de calendario logró que Gemini **controlara la domótica**. Google lo mitigó, pero **la clase de ataque sigue abierta** para cualquier agente con memoria y herramientas.
- **La cadena de suministro de skills es real**: la popularidad no es señal de confianza (una skill con backdoor llegó al primer puesto con 4.000 descargas infladas).
- **Lecciones aplicadas en Hestia:** ver [06-seguridad.md](06-seguridad.md).

## 7. Preguntas abiertas (a resolver en la implementación)

1. Latencia real de Parakeet frente a whisper-turbo en el hardware del usuario.
2. Si conviene una sola instancia de Hermes con guardas o dos (lectora y actuadora) desde el día 1. Decisión actual: una instancia con guardas en la fase 1 y la separación en la fase 3 (ver ADR-0004).
3. Si el acceso a la API de Jev permite usarlo de verdad o hay que quedarse con el router heurístico de LiteLLM.
4. Calidad del entrenamiento de "Hey Hestia" con microWakeWord.

## Afirmaciones refutadas durante la verificación
- ❌ "Exponer entidades en Extended OpenAI Conversation es una barrera de permisos" (0-3).
- ❌ "12.812 instancias de OpenClaw con RCE y el 63 % vulnerables" (0-3).
