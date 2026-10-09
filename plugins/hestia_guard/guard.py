"""Lógica pura de hestia_guard: sin dependencias de Hermes, para poder probarla aislada."""
from __future__ import annotations

import fnmatch
import json
import os
import re
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

LIBRE, CONFIRMAR, PROHIBIDO = "libre", "confirmar", "prohibido"

_ENTITY_RE = re.compile(r"^([a-z_][a-z0-9_]*)\.[a-z0-9_]+$")

# Valores por defecto de la delegación: se usan también si policy.yaml no se puede leer.
DELEGACION_HERRAMIENTAS = ["terminal"]
DELEGACION_COMANDOS = ["claude-hestia", "claude", "codex", "opencode"]


@dataclass
class Policy:
    libre: set[str] = field(default_factory=set)
    confirmar: set[str] = field(default_factory=set)
    prohibido: set[str] = field(default_factory=set)
    fuentes_no_confiables: list[str] = field(default_factory=list)
    herramientas_fisicas: list[str] = field(default_factory=list)
    lectura_fisica: list[str] = field(default_factory=list)
    dominio_por_herramienta: dict[str, Optional[str]] = field(default_factory=dict)
    delegacion_herramientas: list[str] = field(default_factory=lambda: list(DELEGACION_HERRAMIENTAS))
    delegacion_comandos: list[str] = field(default_factory=lambda: list(DELEGACION_COMANDOS))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Policy":
        return cls(
            libre=set(data.get("libre") or []),
            confirmar=set(data.get("confirmar") or []),
            prohibido=set(data.get("prohibido") or []),
            fuentes_no_confiables=list(data.get("fuentes_no_confiables") or []),
            herramientas_fisicas=list(data.get("herramientas_fisicas") or []),
            lectura_fisica=list(data.get("lectura_fisica") or []),
            dominio_por_herramienta=dict(data.get("dominio_por_herramienta") or {}),
            delegacion_herramientas=list((data.get("delegacion") or {}).get("herramientas") or DELEGACION_HERRAMIENTAS),
            delegacion_comandos=list((data.get("delegacion") or {}).get("comandos") or DELEGACION_COMANDOS),
        )

    @classmethod
    def load(cls, path: Path) -> "Policy":
        import yaml  # Hermes ya depende de PyYAML

        with open(path, encoding="utf-8") as fh:
            return cls.from_dict(yaml.safe_load(fh) or {})

    def nivel(self, domain: Optional[str], service: Optional[str] = None) -> str:
        """Nivel de riesgo de domain.service. La regla más específica gana y, a igual especificidad, la más estricta."""
        if not domain:
            return CONFIRMAR
        if service:
            full = f"{domain}.{service}"
            for nivel, reglas in ((PROHIBIDO, self.prohibido), (CONFIRMAR, self.confirmar), (LIBRE, self.libre)):
                if full in reglas:
                    return nivel
        for nivel, reglas in ((PROHIBIDO, self.prohibido), (CONFIRMAR, self.confirmar), (LIBRE, self.libre)):
            if domain in reglas:
                return nivel
        return CONFIRMAR


def _match(name: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatchcase(name, p) for p in patterns)


def _domain_of(entity: Any) -> Optional[str]:
    if isinstance(entity, list):
        entity = entity[0] if entity else None
    if isinstance(entity, str):
        m = _ENTITY_RE.match(entity.strip())
        if m:
            return m.group(1)
    return None


def comando_delegado(command: Any, comandos: list[str]) -> Optional[str]:
    """Si el comando de shell invoca un agente de código (claude, codex...), devuelve cuál.

    Reconoce el comando al inicio, tras ; && || | ( o un espacio, y también con ruta (/usr/local/bin/claude).
    Ante la duda prefiere reconocerlo: un falso positivo solo cuesta una confirmación de más.
    """
    if not isinstance(command, str) or not comandos:
        return None
    nombres = "|".join(re.escape(c) for c in sorted(comandos, key=len, reverse=True))
    m = re.search(rf"(?:^|[\s;&|(`$])(?:[\w./~-]*/)?({nombres})(?=$|[\s;&|)`])", command)
    return m.group(1) if m else None


def extraer_accion(tool_name: str, args: dict[str, Any], policy: Policy) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """Devuelve (domain, service, entity) de una llamada física. Si no se puede saber, cada valor queda en None."""
    args = args or {}
    entity = args.get("entity_id") or args.get("entity") or (args.get("target") or {}).get("entity_id")
    if tool_name == "ha_call_service":
        domain = args.get("domain") or _domain_of(entity)
        return domain, args.get("service"), entity if isinstance(entity, str) else None

    # MCP: mcp__homeassistant__<Tool>
    short = tool_name.split("__")[-1]
    # Los scripts expuestos a Assist aparecen como herramientas con su propio nombre.
    if short.startswith("hestia_") or short.startswith("script_"):
        return "script", short.removeprefix("script_"), None
    domain = None
    raw_domain = args.get("domain")
    if isinstance(raw_domain, list) and len(raw_domain) == 1:
        domain = raw_domain[0]
    elif isinstance(raw_domain, str):
        domain = raw_domain
    domain = domain or policy.dominio_por_herramienta.get(short) or _domain_of(entity)
    service = {"HassTurnOn": "turn_on", "HassTurnOff": "turn_off", "HassToggle": "toggle"}.get(short)
    return domain, service, args.get("name") or (entity if isinstance(entity, str) else None)


class Guard:
    """Estado del guardián: sesiones contaminadas y log de auditoría."""

    def __init__(self, policy: Policy, audit_path: Optional[Path] = None):
        self.policy = policy
        self.audit_path = audit_path
        self._tainted: dict[str, str] = {}  # session_id → herramienta que la contaminó
        self._lock = threading.Lock()

    # ── contaminación ──────────────────────────────────────────
    def marcar_si_no_confiable(self, tool_name: str, session_id: Optional[str]) -> None:
        if session_id and _match(tool_name, self.policy.fuentes_no_confiables):
            with self._lock:
                self._tainted.setdefault(session_id, tool_name)

    def contaminada(self, session_id: Optional[str]) -> Optional[str]:
        with self._lock:
            return self._tainted.get(session_id or "")

    def limpiar(self, session_id: Optional[str]) -> None:
        with self._lock:
            self._tainted.pop(session_id or "", None)

    # ── decisión ───────────────────────────────────────────────
    def es_fisica(self, tool_name: str) -> bool:
        return _match(tool_name, self.policy.herramientas_fisicas) and not _match(tool_name, self.policy.lectura_fisica)

    def delegacion(self, tool_name: str, args: dict[str, Any]) -> Optional[str]:
        """Agente de código al que se delega en esta llamada, o None."""
        if not _match(tool_name, self.policy.delegacion_herramientas):
            return None
        return comando_delegado((args or {}).get("command"), self.policy.delegacion_comandos)

    def _decidir_delegacion(self, tool_name: str, agente: str, args: dict[str, Any],
                            session_id: Optional[str], turn_id: Optional[str]) -> dict[str, str]:
        comando = str((args or {}).get("command") or "")
        resumen = comando if len(comando) <= 400 else comando[:400] + "…"
        accion = f"delegar → {agente}"
        origen = self.contaminada(session_id)
        if origen:
            self.auditar("bloqueado", tool_name, accion, session_id, PROHIBIDO, origen)
            return {
                "action": "block",
                "message": (
                    f"hestia_guard bloqueó la delegación a {agente}: en esta conversación se leyó contenido "
                    f"externo ({origen}) y un agente de código ejecuta lo que le pidan. Si el encargo viene "
                    "de ti, revisa el contenido y usa /guard limpiar, o empieza una conversación nueva con /new."
                ),
            }
        self.auditar("aprobacion", tool_name, accion, session_id, CONFIRMAR, None)
        return {
            "action": "approve",
            "message": (
                f"🧑‍💻 Hestia quiere delegar una tarea a {agente}, que puede leer y modificar código "
                f"con tu suscripción:\n\n{resumen}\n\n¿Lo autorizas?"
            ),
            # Por turno: "permitir siempre" no se vuelve un permiso permanente para delegar.
            "rule_key": f"hestia_guard:delegacion:{session_id}:{turn_id or time.time()}",
        }

    def decidir(self, tool_name: str, args: dict[str, Any], session_id: Optional[str] = None,
                turn_id: Optional[str] = None) -> Optional[dict[str, str]]:
        """Directiva para pre_tool_call: None (permitir), block o approve."""
        agente = self.delegacion(tool_name, args)
        if agente:
            return self._decidir_delegacion(tool_name, agente, args, session_id, turn_id)
        if not self.es_fisica(tool_name):
            return None
        domain, service, entity = extraer_accion(tool_name, args, self.policy)
        accion = f"{domain or '?'}.{service or '?'}" + (f" → {entity}" if entity else "")
        nivel = self.policy.nivel(domain, service)
        origen = self.contaminada(session_id)

        if nivel == PROHIBIDO:
            self.auditar("bloqueado", tool_name, accion, session_id, nivel, origen)
            return {
                "action": "block",
                "message": (
                    f"hestia_guard bloqueó {accion}: el dominio está prohibido para el agente. "
                    "Las cerraduras y la alarma solo se controlan con los scripts script.hestia_* "
                    "(piden confirmación en el celular). No reintentes por otra vía."
                ),
            }
        if origen:
            self.auditar("aprobacion", tool_name, accion, session_id, nivel, origen)
            return {
                "action": "approve",
                "message": (
                    f"⚠️ Hestia quiere ejecutar {accion}, pero en esta conversación se leyó contenido "
                    f"externo ({origen}) que podría contener instrucciones maliciosas. ¿Lo autorizas?"
                ),
                # La clave incluye el turno: "permitir siempre" no puede volverse un permiso permanente.
                "rule_key": f"hestia_guard:taint:{session_id}:{turn_id or time.time()}",
            }
        if nivel == CONFIRMAR:
            self.auditar("aprobacion", tool_name, accion, session_id, nivel, None)
            return {
                "action": "approve",
                "message": f"🏠 Hestia quiere ejecutar {accion}. Es una acción sensible. ¿Lo autorizas?",
                "rule_key": f"hestia_guard:{domain}.{service or '*'}:{entity or '*'}",
            }
        return None

    # ── auditoría ──────────────────────────────────────────────
    def auditar(self, evento: str, tool_name: str, accion: str, session_id: Optional[str],
                nivel: Optional[str] = None, origen: Optional[str] = None, **extra: Any) -> None:
        if not self.audit_path:
            return
        entry = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "evento": evento, "tool": tool_name,
                 "accion": accion, "nivel": nivel, "session": session_id, "contaminada_por": origen, **extra}
        try:
            self.audit_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.audit_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except OSError:
            pass  # la auditoría nunca debe tumbar al agente


def hermes_home() -> Path:
    try:
        from hermes_constants import get_hermes_home  # type: ignore

        return Path(get_hermes_home())
    except Exception:
        return Path(os.environ.get("HERMES_HOME") or Path.home() / ".hermes")
