# Hestia · imagen del agente: Hermes Agent + Claude Code CLI.
# Hermes sigue siendo la imagen oficial, sin cambios. Esta capa solo añade:
#   - el CLI oficial de Claude Code (para delegar programación con tu suscripción)
#   - el wrapper claude-hestia, que lo ejecuta aislado del resto de secretos
ARG HERMES_VERSION=v0.21.6
FROM nousresearch/hermes-agent:${HERMES_VERSION}

# Versión fijada: Dependabot no la vigila, actualízala a propósito (npm view @anthropic-ai/claude-code version)
ARG CLAUDE_CODE_VERSION=2.1.296

USER root
# --prefix /usr/local: el prefijo global de npm en la imagen de Hermes no está en el PATH.
# --allow-scripts: npm ≥12 bloquea los postinstall; solo se permite el de Claude Code (baja su binario nativo).
RUN npm install -g --prefix /usr/local --allow-scripts=@anthropic-ai/claude-code \
      "@anthropic-ai/claude-code@${CLAUDE_CODE_VERSION}" \
 && npm cache clean --force \
 && claude --version

COPY --chmod=755 scripts/claude-hestia /usr/local/bin/claude-hestia

ENV HESTIA_CLAUDE_TOKEN_FILE=/opt/data/secrets/claude_code_oauth_token \
    HESTIA_CLAUDE_HOME=/opt/data/claude-code
