#!/usr/bin/env bash
# Hestia · guarda el token de tu suscripción de Claude dentro del contenedor (no en .env ni en git).
#
# 1. En tu PC, en una terminal aparte:   claude setup-token
#    (abre el navegador, inicias sesión con tu cuenta Pro/Max y te muestra un token sk-ant-oat01-…)
# 2. Aquí:                               ./scripts/claude-code-login.sh
#    y pega el token cuando lo pida (no se muestra en pantalla).
#
# Nunca pegues el token en un chat, ni siquiera con Hestia o Claude.
set -euo pipefail
cd "$(dirname "$0")/.." || exit 1

TOKEN_PATH=/opt/data/secrets/claude_code_oauth_token

if [ -t 0 ]; then
  printf 'Pega el token de "claude setup-token" (no se mostrará): '
  IFS= read -rs token
  echo
else
  IFS= read -r token
fi
token="$(printf '%s' "$token" | tr -d '[:space:]')"

case "$token" in
  sk-ant-oat*) ;;
  sk-ant-api*) echo "✘ Eso es una API key, no un token de suscripción. Usa 'claude setup-token'." >&2; exit 1 ;;
  *) echo "✘ No parece un token de 'claude setup-token' (empieza por sk-ant-oat)." >&2; exit 1 ;;
esac

if ! docker compose ps --status running --services 2>/dev/null | grep -qx hestia; then
  echo "✘ El contenedor hestia no está corriendo (docker compose up -d)." >&2
  exit 1
fi

printf '%s' "$token" | docker compose exec -T -u hermes hestia sh -c \
  "umask 077 && mkdir -p \"\$(dirname $TOKEN_PATH)\" && cat > $TOKEN_PATH"
echo "✔ Token guardado en el volumen de Hestia ($TOKEN_PATH, permisos 600)."

echo "… probando Claude Code con tu suscripción"
if docker compose exec -T -u hermes hestia claude-hestia --check; then
  echo "✔ Claude Code responde. Pídele a Hestia: \"usa Claude Code para …\""
else
  echo "✘ Claude Code no respondió. Revisa el token o vuelve a generarlo con 'claude setup-token'." >&2
  exit 1
fi
