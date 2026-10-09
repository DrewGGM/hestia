# ADR-0001: Hermes Agent como dependencia, no como fork

- **Estado:** aceptada (2026-10-09)

## Contexto
Necesitamos un runtime de agente que tenga memoria, skills, gateways de mensajería, voz, cron y MCP. Construirlo desde cero tomaría meses. Las candidatas eran Hermes Agent, OpenClaw, OpenJarvis y Letta (ver [investigación](../00-investigacion.md)).

## Decisión
Usamos **Hermes Agent** (MIT) **sin forkearlo**, con versión fijada. Hestia vive en su propio repo como:
- `config.yaml`, `SOUL.md` y `distribution.yaml` en la raíz: el repo **es** una [distribución de perfil de Hermes](https://hermes-agent.nousresearch.com/docs/user-guide/profile-distributions) (`hermes profile install github.com/DrewGGM/hestia`)
- skills en `skills/` (las copia la distribución)
- plugins en `plugins/`, declarados en `distribution_owned`
- servidores MCP declarados en `mcp_servers`

## Consecuencias
- ✅ Recibimos las mejoras de upstream (release cada 2–3 días) cambiando una línea del `.env`.
- ✅ Nuestro código es pequeño y auditable.
- ⚠️ Dependemos de la API de plugins de Hermes. Si cambia, hay que adaptar `hestia_guard`.
- ⚠️ Los bugs de upstream se resuelven con PR a Hermes, y mientras tanto con un parche en un plugin. Si un fork llega a hacer falta, será temporal.

## Alternativas descartadas
- **OpenClaw:** su historial de seguridad no sirve para algo que controla una casa: más de 40k instancias expuestas, CVEs de RCE y escape del sandbox, y un marketplace con malware.
- **OpenJarvis:** prometedor pero inmaduro como producto. Lo reutilizaremos como fuente de skills e ideas.
- **Letta:** sería un segundo runtime solo para tener memoria, y Hermes ya trae memoria con proveedores enchufables.
