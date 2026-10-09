# Home Assistant para Hestia

1. **Usuario del agente:** crea la persona/usuario `hestia` **sin** permisos de administrador y genera un *Long-Lived Access Token* con ese usuario → `HASS_TOKEN` en `.env`.
2. **MCP Server:** Ajustes → Dispositivos y servicios → Añadir → *Model Context Protocol Server*. Desactiva *Require an administrator account*.
3. **Exposición mínima:** Ajustes → Asistentes de voz → Exponer. Expón luces, media, sensores y los scripts `hestia_*`. **No** expongas `lock.*` ni `alarm_control_panel.*`.
4. **Scripts con confirmación:** copia [`hestia_scripts.yaml`](hestia_scripts.yaml) a `/config/scripts/` (ver las instrucciones dentro).
5. **Voz:** añade las integraciones *Wyoming Protocol* que apuntan a `whisper:10300`, `piper:10200` y `openwakeword:10400` (con el profile `voice`).
6. **Satélites → cerebro de Hestia:** ver [docs/04-voz.md](../../docs/04-voz.md).

## ¿Dispositivos sueltos? Integraciones recomendadas

| Dispositivo | Integración |
|---|---|
| Tuya / SmartLife | *Tuya* oficial (nube) o **Tuya Local** / LocalTuya por HACS (sin nube) |
| Xiaomi / Mi Home | *Xiaomi Home* oficial |
| Zigbee | **ZHA** o **Zigbee2MQTT** con un dongle (Sonoff ZBDongle-E, SLZB-06) |
| Matter / Thread | *Matter* + *Thread* (border router: HA Connect ZBT-1/ZBT-2 o un HomePod/Nest) |
| Alexa / Google Home | *Alexa Media Player* (HACS) o *Google Assistant SDK* |
| TV, Chromecast, Spotify | *Cast*, *Spotify*, *Android TV Remote*, *LG webOS*, *Samsung* |
