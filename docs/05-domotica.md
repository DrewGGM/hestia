# Domótica con Home Assistant

Hestia **nunca** habla directamente con un bombillo o un enchufe: todo pasa por Home Assistant (HA). Por eso funciona con cualquier marca.

## ¿Dónde corre Home Assistant?

| Opción | Para quién | Cómo |
|---|---|---|
| **HA OS en Raspberry Pi 5 / mini-PC** | ✅ Recomendado | Imagen oficial, add-ons, actualizaciones con un clic. Con un dongle Zigbee/Thread conectado ahí |
| HA en el compose de Hestia | Servidor Linux que ya tienes | `docker compose --profile home up -d` (Linux; no funciona bien en Docker Desktop) |
| HA que ya tienes | Ya tienes HA | Solo apunta `HASS_URL` y `HASS_TOKEN` en `.env` |

## Paso a paso

### 1. Integra tus dispositivos
Ajustes → Dispositivos y servicios → Añadir integración. Ver la tabla de marcas en [`config/homeassistant/README.md`](../config/homeassistant/README.md). Ponle **áreas** a todo (Sala, Cuarto, Cocina…) y **alias** a los dispositivos ("la lámpara", "el aire"). Hestia y Whisper usan esos nombres.

### 2. Crea el usuario del agente
Ajustes → Personas → Añadir persona `Hestia` → *Permitir iniciar sesión*, **sin** administrador. Inicia sesión como `hestia` → Perfil → Seguridad → **Token de larga duración** → `HASS_TOKEN`.

### 3. Exposición mínima
Ajustes → Asistentes de voz → **Exponer**:
- ✅ Luces, media, ventiladores, escenas, sensores útiles y los scripts `hestia_*`.
- ❌ `lock.*`, `alarm_control_panel.*` y cualquier cosa que no quieras que un desconocido controle con la voz.
- Con un modelo local en HA, menos de 25 entidades. Con Hestia (Claude) puedes exponer más.

### 4. Conecta Hestia
- **MCP Server de HA** (respeta la exposición): Añadir integración → *Model Context Protocol Server* → desactiva *Require an administrator account*. En `config.yaml` de Hestia: `mcp_servers.homeassistant.enabled: true`.
- **Plugin `homeassistant` de Hermes** (eventos en tiempo real y control por REST): ya viene en `plugins.enabled`. Avisa por Telegram cuando cambian puertas, alarma o cerraduras (`platforms.homeassistant.extra.watch_domains`).

> ⚠️ El plugin `homeassistant` llama servicios por REST y **no** respeta la exposición de Assist. Por eso existe `hestia_guard`: bloquea `lock`, `alarm_control_panel` y `homeassistant.*`, y pide confirmación para clima, persianas y scripts, venga la llamada por la vía que venga.

### 5. Scripts con confirmación
Copia [`config/homeassistant/hestia_scripts.yaml`](../config/homeassistant/hestia_scripts.yaml) → `/config/scripts/hestia.yaml`. Ajusta `notify.mobile_app_*` y los `entity_id`. Expón solo esos scripts.

Así, "Hestia, abre la puerta" llama a `script.hestia_abrir_cerradura` → te llega una notificación al celular → solo se abre si tocas **Sí**.

### 6. ha-mcp (opcional, avanzado)
[ha-mcp](https://github.com/homeassistant-ai/ha-mcp) da 87 herramientas, entre ellas crear y editar automatizaciones. Es potente y crea **su propio token de admin**. Si lo usas:
- Instálalo por HACS y usa el endpoint **`/readonly`** al principio.
- Agrégalo en `mcp_servers` con `trust: untrusted`.
- **Nunca** lo expongas como LLM API a los satélites de voz (lo advierte su propia documentación).

## ¿Qué comprar si empiezas de cero?

| Necesidad | Recomendación |
|---|---|
| Hub | Raspberry Pi 5 (4–8 GB) + SSD, o un mini-PC N100 |
| Radio Zigbee + Thread | Home Assistant Connect ZBT-2 o SLZB-06 (PoE) |
| Luces | Bombillos o interruptores Zigbee/Matter (IKEA, Aqara, Sonoff). Evita depender de la nube |
| Enchufes con medición | Zigbee/Matter (Sonoff S60ZB, Aqara) o Tuya con *Tuya Local* |
| Sensores | Puertas y ventanas, movimiento y temperatura Zigbee (Aqara, Sonoff SNZB) |
| Voz | 1 Home Assistant Voice PE por habitación principal |

Prioriza **Zigbee y Matter (local)** sobre Wi-Fi con nube: responden más rápido, siguen funcionando sin internet y no dependen de que el fabricante mantenga sus servidores.
