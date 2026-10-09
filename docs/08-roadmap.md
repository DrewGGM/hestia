# Roadmap por fases

Cada fase deja algo **usable**. Hestia sirve desde la fase 1. Las siguientes suman canales, más seguridad y autonomía.

## Fase 0: Fundaciones ✅
- [x] Investigación profunda y verificada ([00-investigacion.md](00-investigacion.md))
- [x] Arquitectura y ADRs
- [x] Repo público, estructura, README y guías

## Fase 1: Cerebro + chat (semana 1)
**Meta:** hablar con Hestia por Telegram (texto y notas de voz) y desde la terminal del PC.
- [ ] `docker compose --profile core up -d`: Hermes + LiteLLM
- [ ] Claude como modelo principal y Ollama `qwen3.5:4b` como modelo auxiliar
- [ ] Personalidad de Hestia (`SOUL.md`) bilingüe
- [ ] Gateway de Telegram con allowlist
- [ ] Skills: `briefing-diario`, `captura-rapida`
- [ ] Plugin `hestia_guard` activo
- [ ] Voice mode de Hermes en el PC ("Hey Hermes" mientras se entrena "Hey Hestia")

## Fase 2: Casa (semanas 2–3)
**Meta:** controlar la casa por chat y por voz desde un satélite.
- [ ] Home Assistant (profile `home`, o uno existente)
- [ ] Usuario `hestia` no admin, exposición mínima y scripts con confirmación
- [ ] MCP Server de HA conectado a Hermes y plugin `homeassistant`
- [ ] Wyoming: Parakeet/whisper + Piper `es_MX-claude-high` + openWakeWord (profile `voice`)
- [ ] Primer satélite: HA Voice PE con "Hey Jarvis" (ES) y "Okay Nabu" (EN)
- [ ] Satélites conectados al cerebro de Hestia (conversation agent → Hermes)
- [ ] Skills: `control-casa`, `escenas-y-rutinas`

## Fase 3: Vida digital (semanas 3–5)
**Meta:** agenda, correo, tareas, negocios, universidad y finanzas.
- [ ] Google Workspace MCP (Calendar, Tasks, Gmail; escrituras con aprobación vía `trust: untrusted`)
- [ ] GitHub MCP (solo lectura + issues) y n8n MCP
- [ ] Skills: `gestion-correo`, `universidad`, `finanzas-personales`, `estado-negocios`
- [ ] Cron: briefing diario 7:00, resumen semanal y auditoría de memoria
- [ ] Separación de privilegios: instancia lectora y actuadora (ADR-0004)
- [ ] Jev como clasificador de riesgo y complejidad (si hay acceso a la API)

## Fase 4: Voz premium y autonomía (semanas 5–8)
- [ ] Wake word propia **"Hey Hestia"** entrenada con microWakeWord y openWakeWord
- [ ] Voz única ES/EN (ElevenLabs flash o Chatterbox Multilingual clonada)
- [ ] Cliente de voz del PC con Pipecat + Smart Turn (barge-in natural)
- [ ] Dashboard: memoria, skills pendientes de aprobar, auditoría y coste por modelo
- [ ] Ciclo de automejora: el Curator de Hermes, revisión semanal de skills y métricas

## Fase 5: Despliegue remoto
- [ ] Profile `remote`: VPS + Tailscale sidecar + ACLs
- [ ] Cloudflare Tunnel + Access para el dashboard
- [ ] Secretos con SOPS + age
- [ ] Backups de `~/.hermes` (memoria y skills) y de HA

## Ideas futuras
- Visión: cámaras de HA con un modelo multimodal ("¿quién está en la puerta?")
- Presencia por habitación (ESPresense) para que responda en el satélite más cercano
- Integración con la plataforma EAM y la DIAN reutilizando las skills existentes del usuario
