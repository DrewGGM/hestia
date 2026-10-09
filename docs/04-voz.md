# Voz: satélites, PC y notas de voz

Hestia escucha por tres caminos. Los tres terminan en el mismo cerebro.

| Camino | Wake word | STT → TTS | Dónde se configura |
|---|---|---|---|
| **Satélites por habitación** (HA Voice PE, ESP32-S3) | En el dispositivo: "Hey Jarvis" (ES), "Okay Nabu" (EN). Fase 4: "Hey Hestia" | Wyoming (profile `voice`) | Home Assistant → Asistentes de voz |
| **PC** | "Hey Hermes" (fase 4: "Hey Hestia") o push-to-talk `Ctrl+B` | faster-whisper local en Hermes → Edge/Piper/ElevenLabs | `config.yaml` → `stt`, `tts`, `wake_word` |
| **Telegram / WhatsApp** | — (nota de voz) | faster-whisper en Hermes → respuesta en texto o audio | `config.yaml` → `stt`, `tts` |

## 1. Satélites (Home Assistant)

### Servicios Wyoming
```bash
docker compose --profile voice up -d
```
En HA: **Ajustes → Dispositivos y servicios → Añadir → Wyoming Protocol**, tres veces:

| Servicio | Host | Puerto |
|---|---|---|
| STT (whisper/Parakeet) | IP del host de Docker | 10300 |
| TTS (Piper) | IP del host de Docker | 10200 |
| Wake word (openWakeWord) | IP del host de Docker | 10400 |

> Los puertos se publican en `127.0.0.1`. Si HA corre en otra máquina, cambia `127.0.0.1:` por la IP LAN del host en `docker-compose.yml`, o usa los add-ons equivalentes de HA OS (*Whisper*, *Piper*, *openWakeWord*).

**Elección de STT según tu hardware:**

| Hardware | Configuración (`.env`) |
|---|---|
| CPU modesta / Raspberry Pi | `WHISPER_LIBRARY=sherpa` → Parakeet TDT v3: rápido en CPU y con español nativo |
| CPU decente | `WHISPER_LIBRARY=auto`, `WHISPER_MODEL=small-int8` |
| GPU NVIDIA | Construye la imagen GPU (`Dockerfile.gpu` de [wyoming-faster-whisper](https://github.com/OHF-Voice/wyoming-faster-whisper)) con `large-v3-turbo`. Con 8 GB de VRAM, mejor deja la GPU al LLM y usa Parakeet |

Opcional: `--hass-token` en whisper sesga el reconocimiento hacia los nombres de tus dispositivos ("prende la *Govee* del estudio").

### Pipelines bilingües
HA usa **un idioma por pipeline**. Crea dos (Ajustes → Asistentes de voz):

| Pipeline | Idioma | STT | TTS | Agente de conversación | Wake word |
|---|---|---|---|---|---|
| **Hestia ES** | Español | Wyoming whisper (es) | Piper `es_MX-claude-high` | **Hestia** (ver abajo) | "Hey Jarvis" |
| **Hestia EN** | English | Wyoming whisper (en) | Piper `en_US-lessac-high` | **Hestia** | "Okay Nabu" |

Desde HA 2025.10 cada satélite puede tener **dos wake words, cada una con su pipeline**. Así dices "Hey Jarvis" para hablar en español y "Okay Nabu" para inglés.

### Conectar los satélites al cerebro de Hestia
Hestia expone una **API compatible con OpenAI** en `:8642` (el API server de Hermes). Para que los satélites hablen con Hestia y no con un LLM suelto:

1. Instala por HACS **Extended OpenAI Conversation** (o cualquier integración de conversación que acepte *Base URL* OpenAI-compatible).
2. Configúrala con:
   - **Base URL:** `http://<host-docker>:8642/v1`
   - **API key:** el valor de `HESTIA_API_KEY`
   - **Modelo:** `hestia`
   - **Funciones:** desactívalas o déjalas vacías. Hestia controla la casa con sus propias herramientas (MCP de HA + plugin), con el guardián activo.
3. En cada pipeline, elige ese agente y activa **"Preferir gestionar comandos localmente"**. Las órdenes simples ("apaga la luz de la sala") las resuelve HA al instante y sin LLM. Lo demás ("¿qué tengo mañana y apaga todo cuando me vaya?") llega a Hestia.

> 🔎 **Por verificar en tu instalación:** que la integración elegida no inyecte sus propias funciones de HA. Si lo hace, Hestia vería dos juegos de herramientas. Prueba primero con "¿qué hora es?" y "¿qué tengo hoy?".

**Aprobaciones desde la voz:** si `hestia_guard` pide confirmación durante una petición de voz, la ejecución queda en espera. Apruébala desde Telegram o el dashboard. Si nadie responde, se deniega por timeout. Es intencional: nadie puede abrir nada gritando cerca de un micrófono.

### Hardware de satélites
| Opción | Precio aprox. | Notas |
|---|---|---|
| **Home Assistant Voice PE** | 59 USD | ✅ Recomendado. Cancelación de eco (XMOS), wake word en el dispositivo, buen micrófono |
| ESP32-S3-BOX-3 | 50 USD | Con pantalla. Firmware ESPHome oficial |
| ESP32-S3 + INMP441 + MAX98357 (DIY) | 10–15 USD | Barato, requiere soldar y ajustar |
| Raspberry Pi + ReSpeaker | 60–100 USD | `linux-voice-assistant` (experimental). `wyoming-satellite` está archivado |

Firmware: [`voice/esphome/hestia-satelite-voice-pe.yaml`](../voice/esphome/hestia-satelite-voice-pe.yaml).

## 2. PC (voice mode de Hermes)

La voz en el PC necesita un micrófono, así que Hermes debe correr **nativo** en el PC, no en Docker:

```bash
# Windows (PowerShell) o Linux/macOS: instala Hermes
#   https://hermes-agent.nousresearch.com/docs/getting-started/installation
hermes profile install github.com/DrewGGM/hestia --alias
hestia chat
# dentro del chat:
/voice on        # push-to-talk con Ctrl+B
/wake on         # escucha continua con "Hey Hermes"
```

El Hestia del PC puede usar el mismo LiteLLM del servidor (`LITELLM_BASE_URL=http://<servidor>:4000/v1` en `~/.hermes/profiles/hestia/.env`, por Tailscale). Hay que tener presente que **la memoria es por instalación**: el PC y el servidor son dos instancias con memoria propia. En la fase 4 el cliente de voz Pipecat se conectará directo a la API del servidor y habrá una sola memoria.

## 3. Notas de voz (Telegram/WhatsApp)
Funcionan desde la fase 1: mándale un audio al bot y Hermes lo transcribe con faster-whisper, que detecta solo si hablas español o inglés.
- Para que **responda con audio**, activa `voice.auto_tts: true` o pídeselo ("respóndeme en audio").
- Para las burbujas de voz de Telegram con Piper o Edge hace falta **ffmpeg**. La imagen Docker ya lo trae.

## 4. Voz única ES/EN (fase 4)
Con Piper, el español y el inglés son dos voces distintas. Para una sola identidad vocal:
- **ElevenLabs** `eleven_flash_v2_5`: unos 200 ms, la misma voz en 32 idiomas. `tts.provider: elevenlabs`.
- **Chatterbox Multilingual** (MIT, local): clona una voz de referencia en 23 idiomas. Añade marca de agua.
- **Edge** `en-US-AvaMultilingualNeural`: gratis y multilingüe, aunque con acento neutro.
