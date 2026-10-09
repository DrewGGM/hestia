# Instalación

Hay dos formas de instalar Hestia y se pueden combinar:

| Modo | Para qué | Comando clave |
|---|---|---|
| **A. Servidor (Docker)** | El cerebro 24/7: Telegram, cron, Home Assistant, API para satélites | `docker compose up -d` |
| **B. Nativo (perfil de Hermes)** | Voz en el PC con micrófono, chat en la terminal | `hermes profile install github.com/DrewGGM/hestia` |

## Requisitos

| | Mínimo | Recomendado |
|---|---|---|
| Servidor | 2 vCPU, 4 GB RAM, Docker 24+ | 4+ núcleos, 16 GB RAM, GPU NVIDIA de 8 GB o más para el modelo local |
| Cuentas | API key de Anthropic | + bot de Telegram, OpenRouter (respaldo), Google Cloud (OAuth) |
| Casa | — | Home Assistant + al menos un satélite Voice PE |

## A. Servidor con Docker

```bash
git clone https://github.com/DrewGGM/hestia.git
cd hestia
cp .env.example .env
# Edita .env: ANTHROPIC_API_KEY, LITELLM_MASTER_KEY, HESTIA_API_KEY, TELEGRAM_*
```

Elige los profiles según tu caso:

```bash
# Solo cerebro (nube), por ejemplo en un VPS
docker compose up -d

# Casa sin GPU: cerebro + modelo local + voz
docker compose --profile local --profile voice up -d

# Casa con GPU NVIDIA
docker compose -f docker-compose.yml -f compose.gpu.yaml --profile local --profile voice up -d

# Todo, incluido Home Assistant y Google Workspace (Linux)
docker compose --profile local --profile voice --profile home --profile workspace up -d
```

Qué pasa al arrancar:
1. `hestia-init` instala la distribución (este repo) como perfil `hestia` dentro del volumen de Hermes e instala el plugin `homeassistant`.
2. `litellm` levanta el router de modelos en `:4000`.
3. `hestia` arranca el gateway: Telegram, cron, eventos de HA, la API en `:8642` y el dashboard en `:9119`.

Verifica:
```bash
./scripts/doctor.sh                      # chequeo completo
docker compose logs -f hestia            # logs del agente
docker compose exec hestia hermes -p hestia doctor
```

Escríbele a tu bot de Telegram: *"Hola Hestia, ¿quién eres?"*.

**Actualizar Hestia** (después de `git pull`): `docker compose up -d --force-recreate hestia-init hestia`. En Docker, el `config.yaml` del repo es la fuente de verdad.

**Actualizar Hermes:** cambia `HERMES_VERSION` en `.env` (revisa antes el changelog) y `docker compose up -d`.

### Windows (Docker Desktop)
- Usa WSL2 como backend. Para la GPU: Docker Desktop + driver NVIDIA reciente; `compose.gpu.yaml` funciona igual.
- El profile `home` (Home Assistant con `network_mode: host`) **no** funciona bien en Docker Desktop. Usa HA OS en otra máquina.
- Los datos de Hermes van en un volumen con nombre (`hermes-data`) y no en una carpeta de Windows: un bind mount en Windows corrompe la base SQLite de Hermes.

## B. Nativo (PC con micrófono)

1. Instala Hermes Agent: https://hermes-agent.nousresearch.com/docs/getting-started/installation
   ```powershell
   # Windows (PowerShell)
   iex (irm https://hermes-agent.nousresearch.com/install.ps1)
   ```
   ```bash
   # Linux / macOS / WSL2
   curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
   ```
2. Instala Hestia como perfil:
   ```bash
   hermes profile install github.com/DrewGGM/hestia --alias
   ```
3. Llena `~/.hermes/profiles/hestia/.env` (el instalador deja un `.env.EXAMPLE`). Lo mínimo es `LITELLM_BASE_URL` y `LITELLM_MASTER_KEY`, apuntando al LiteLLM de tu servidor o a uno local (`docker compose up -d litellm`).
4. Plugin de Home Assistant: `hestia plugins install homeassistant --enable`
5. Usa la voz:
   ```bash
   hestia chat
   /voice on     # Ctrl+B para hablar
   /wake on      # "Hey Hermes"
   ```
6. Actualizar: `hermes profile update hestia` (tu `config.yaml` local se conserva; `--force-config` lo reemplaza).

## C. VPS + casa (remoto)

1. **Tailscale** en el VPS (en el host, no en un contenedor) y en la máquina de Home Assistant. Los contenedores salen por la red del host.
2. En `.env` del VPS: `HASS_URL=http://<nombre-magicdns-de-ha>:8123`.
3. ACL de Tailscale mínima:
   ```json
   { "grants": [ { "src": ["tag:hestia"], "dst": ["tag:ha"], "ip": ["tcp:8123"] } ] }
   ```
4. Dashboard: `--profile remote` con `CLOUDFLARE_TUNNEL_TOKEN`. En Cloudflare Zero Trust, crea la ruta pública hacia `http://hestia:9119` **protegida con Access** (tu correo).
5. Si quieres el modelo local de tu PC con GPU: `OLLAMA_API_BASE=http://<ip-tailscale-del-pc>:11434`.
6. Google OAuth en un VPS: haz el primer login con un túnel SSH (`ssh -L 8000:localhost:8000 vps`) y abre la URL de autorización en tu navegador.

## Siguientes pasos
- [Configuración](03-configuracion.md): personalizar a Hestia y tu `USER.md`
- [Domótica](05-domotica.md)
- [Voz](04-voz.md)
- [Seguridad](06-seguridad.md): **léela antes de exponer nada**
