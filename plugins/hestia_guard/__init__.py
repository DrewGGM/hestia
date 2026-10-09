"""hestia_guard: plugin de seguridad de Hestia para Hermes Agent.

Hooks:
  pre_tool_call   → bloquea o pide aprobación para acciones físicas y para delegar
                    en agentes de código (Claude Code, Codex...), según policy.yaml
  post_tool_call  → marca la sesión como contaminada si una herramienta trajo contenido externo
                    y audita las acciones físicas y las delegaciones ejecutadas
  on_session_reset / on_session_end → limpia la marca de contaminación
Comando:
  /guard [estado|limpiar] → muestra o limpia la marca de la sesión actual
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

from .guard import Guard, Policy, extraer_accion, hermes_home

log = logging.getLogger("hestia_guard")
_guard: Optional[Guard] = None
_last_session: Optional[str] = None


def _on_pre_tool_call(tool_name: str = "", args: Any = None, session_id: Optional[str] = None,
                      turn_id: Optional[str] = None, **_: Any) -> Optional[dict[str, str]]:
    global _last_session
    _last_session = session_id or _last_session
    if _guard is None:
        return None
    return _guard.decidir(tool_name, args if isinstance(args, dict) else {}, session_id, turn_id)


def _on_post_tool_call(tool_name: str = "", args: Any = None, result: Any = None,
                       session_id: Optional[str] = None, status: Optional[str] = None, **_: Any) -> None:
    if _guard is None:
        return
    _guard.marcar_si_no_confiable(tool_name, session_id)
    args = args if isinstance(args, dict) else {}
    agente = _guard.delegacion(tool_name, args)
    if agente:
        _guard.auditar("ejecutado", tool_name, f"delegar → {agente}", session_id, status=status)
    elif _guard.es_fisica(tool_name):
        domain, service, entity = extraer_accion(tool_name, args, _guard.policy)
        _guard.auditar("ejecutado", tool_name, f"{domain}.{service}" + (f" → {entity}" if entity else ""),
                       session_id, status=status)


def _on_session_clear(session_id: Optional[str] = None, **_: Any) -> None:
    if _guard is not None:
        _guard.limpiar(session_id)


def _cmd_guard(raw_args: str = "") -> str:
    if _guard is None:
        return "hestia_guard no está inicializado."
    arg = (raw_args or "").strip().lower()
    if arg in {"limpiar", "clear", "reset"}:
        _guard.limpiar(_last_session)
        return "🛡️ Marca de contaminación eliminada para esta sesión."
    origen = _guard.contaminada(_last_session)
    if origen:
        return (f"🛡️ Sesión contaminada por `{origen}`: toda acción física pedirá confirmación. "
                "Usa `/guard limpiar` si ya revisaste el contenido, o `/new` para empezar limpio.")
    return "🛡️ Sesión limpia. Las acciones físicas siguen la política de policy.yaml."


def register(ctx) -> None:
    global _guard
    policy_path = Path(__file__).with_name("policy.yaml")
    try:
        policy = Policy.load(policy_path)
    except Exception as exc:  # política ilegible: modo más estricto
        log.error("hestia_guard: no pude leer %s (%s). Todo lo físico pedirá confirmación.", policy_path, exc)
        policy = Policy(herramientas_fisicas=["ha_call_service", "mcp__homeassistant__*"])
    _guard = Guard(policy, audit_path=hermes_home() / "logs" / "hestia_audit.jsonl")

    ctx.register_hook("pre_tool_call", _on_pre_tool_call)
    ctx.register_hook("post_tool_call", _on_post_tool_call)
    ctx.register_hook("on_session_reset", _on_session_clear)
    ctx.register_hook("on_session_end", _on_session_clear)
    ctx.register_command("guard", _cmd_guard, description="Estado del guardián de Hestia", args_hint="[estado|limpiar]")
