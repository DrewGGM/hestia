#!/usr/bin/env bash
# Hestia · diagnóstico rápido del stack Docker.
# Uso: ./scripts/doctor.sh
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1

ok()   { printf '  \033[32m✔\033[0m %s\n' "$1"; }
warn() { printf '  \033[33m!\033[0m %s\n' "$1"; }
fail() { printf '  \033[31m✘\033[0m %s\n' "$1"; FAILED=1; }
FAILED=0

echo "Hestia doctor"
echo "─ Archivos"
[ -f .env ] && ok ".env existe" || fail ".env no existe (cp .env.example .env)"
if [ -f .env ]; then
  # shellcheck disable=SC1091
  set -a; . ./.env; set +a
  if [ -n "${OPENROUTER_API_KEY:-}" ]; then ok "OPENROUTER_API_KEY definida"
  elif [ -n "${ANTHROPIC_API_KEY:-}" ]; then ok "ANTHROPIC_API_KEY definida (recuerda cambiar los alias en config/litellm/config.yaml)"
  else fail "Falta OPENROUTER_API_KEY (o ANTHROPIC_API_KEY)"; fi
  case "${LITELLM_MASTER_KEY:-}" in ""|*cambia-esto*) fail "LITELLM_MASTER_KEY sin cambiar";; *) ok "LITELLM_MASTER_KEY definida";; esac
  case "${HESTIA_API_KEY:-}" in ""|*cambia-esto*) fail "HESTIA_API_KEY sin cambiar";; *) ok "HESTIA_API_KEY definida";; esac
  [ -n "${TELEGRAM_BOT_TOKEN:-}" ] && { [ -n "${TELEGRAM_ALLOWED_USERS:-}" ] && ok "Telegram con allowlist" || fail "TELEGRAM_BOT_TOKEN sin TELEGRAM_ALLOWED_USERS: cualquiera podría hablarle"; } || warn "Telegram no configurado"
  [ -n "${HASS_TOKEN:-}" ] && ok "Home Assistant configurado" || warn "Home Assistant no configurado (fase 2)"
  if [ "$(stat -c %a .env 2>/dev/null || echo 600)" != "600" ]; then warn ".env debería tener permisos 600 (chmod 600 .env)"; fi
fi

echo "─ Contenedores"
if ! docker compose ps >/dev/null 2>&1; then fail "docker compose no responde"; else
  for s in litellm hestia; do
    state=$(docker compose ps --format '{{.Service}} {{.State}}' 2>/dev/null | awk -v s="$s" '$1==s{print $2}')
    [ "$state" = "running" ] && ok "$s corriendo" || fail "$s no está corriendo (${state:-ausente})"
  done
  exposed=$(docker compose ps --format '{{.Ports}}' 2>/dev/null | tr ',' '\n' | grep -E '0\.0\.0\.0:|:::' || true)
  [ -z "$exposed" ] && ok "Ningún puerto publicado en 0.0.0.0" || fail "Puertos expuestos a toda la red: $exposed"
fi

echo "─ Servicios"
if curl -fsS -m 5 -H "Authorization: Bearer ${LITELLM_MASTER_KEY:-}" http://127.0.0.1:4000/v1/models >/dev/null 2>&1; then
  ok "LiteLLM responde en :4000"
else fail "LiteLLM no responde en :4000"; fi
code=$(curl -s -o /dev/null -m 5 -w '%{http_code}' -H "Authorization: Bearer ${HESTIA_API_KEY:-}" http://127.0.0.1:8642/v1/models || true)
[ "$code" = "200" ] && ok "API de Hestia responde en :8642" || warn "API de Hestia en :8642 devolvió ${code:-nada}"
if docker compose exec -T hestia hermes -p hestia plugins list 2>/dev/null | grep -q hestia_guard; then
  ok "plugin hestia_guard cargado"
else warn "no pude confirmar el plugin hestia_guard (docker compose exec hestia hermes -p hestia plugins list)"; fi
if docker compose exec -T -u hermes hestia test -s /opt/data/secrets/claude_code_oauth_token 2>/dev/null; then
  ok "Claude Code con tu suscripción configurado (prueba: docker compose exec -u hermes hestia claude-hestia --check)"
else warn "Claude Code sin token (opcional): ./scripts/claude-code-login.sh"; fi

echo
[ "$FAILED" = 0 ] && echo "Todo bien ✔" || { echo "Hay problemas que resolver ✘"; exit 1; }
