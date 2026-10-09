# ADR-0002: Home Assistant como capa única de domótica

- **Estado:** aceptada (2026-10-09)

## Contexto
La casa debe funcionar con cualquier hardware: dispositivos sueltos (Tuya/SmartLife, Xiaomi, Alexa/Google) o una red Zigbee/Matter/Thread. Además queremos satélites de voz por habitación.

## Decisión
**Home Assistant** es el único punto de contacto con el mundo físico. Hestia nunca habla directamente con un dispositivo, solo con HA:
- El agente accede a HA con el **MCP Server integrado** (`/api/mcp`, usuario no admin, solo las entidades expuestas a Assist) y/o con el plugin `homeassistant` de Hermes.
- `ha-mcp` (87 herramientas, puede editar automatizaciones) es **opcional** y arranca en modo `/readonly`.
- Los satélites usan el pipeline Assist + Wyoming de HA.

## Consecuencias
- ✅ Cualquiera de las más de 3.000 integraciones de HA sirve sin código nuevo.
- ✅ La exposición de entidades en HA es la primera barrera de permisos.
- ⚠️ HA es un componente crítico. Si se cae, se pierde el control de la casa, aunque el resto (agenda, chat) sigue funcionando.
