"""Pruebas de hestia_guard (sin Hermes instalado)."""
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("guard", ROOT / "plugins" / "hestia_guard" / "guard.py")
guard = importlib.util.module_from_spec(_spec)
sys.modules["guard"] = guard
_spec.loader.exec_module(guard)


@pytest.fixture
def g(tmp_path):
    policy = guard.Policy.load(ROOT / "plugins" / "hestia_guard" / "policy.yaml")
    return guard.Guard(policy, audit_path=tmp_path / "audit.jsonl")


def test_luz_es_libre(g):
    assert g.decidir("ha_call_service", {"domain": "light", "service": "turn_off", "entity_id": "light.sala"}, "s1") is None


def test_cerradura_bloqueada(g):
    d = g.decidir("ha_call_service", {"domain": "lock", "service": "unlock", "entity_id": "lock.puerta"}, "s1")
    assert d["action"] == "block"


def test_desarmar_alarma_bloqueado(g):
    d = g.decidir("ha_call_service", {"domain": "alarm_control_panel", "service": "alarm_disarm"}, "s1")
    assert d["action"] == "block"


def test_dominio_deducido_de_entity(g):
    d = g.decidir("ha_call_service", {"service": "unlock", "entity_id": "lock.puerta"}, "s1")
    assert d["action"] == "block"


def test_clima_pide_confirmacion(g):
    d = g.decidir("ha_call_service", {"domain": "climate", "service": "set_temperature", "entity_id": "climate.cuarto"}, "s1")
    assert d["action"] == "approve"
    assert "climate.set_temperature" in d["message"]


def test_dominio_desconocido_pide_confirmacion(g):
    d = g.decidir("ha_call_service", {"domain": "foo_nuevo", "service": "do"}, "s1")
    assert d["action"] == "approve"


def test_script_de_cerradura_permitido(g):
    assert g.decidir("ha_call_service", {"domain": "script", "service": "hestia_abrir_cerradura"}, "s1") is None
    assert g.decidir("mcp__homeassistant__hestia_abrir_cerradura", {"cerradura": "lock.puerta"}, "s1") is None


def test_otro_script_pide_confirmacion(g):
    assert g.decidir("ha_call_service", {"domain": "script", "service": "regar_jardin"}, "s1")["action"] == "approve"


def test_mcp_ha_luz_libre(g):
    assert g.decidir("mcp__homeassistant__HassLightSet", {"name": "Sala", "brightness": 30}, "s1") is None
    assert g.decidir("mcp__homeassistant__HassTurnOff", {"area": "Sala", "domain": ["light"]}, "s1") is None


def test_mcp_ha_turnon_sin_dominio_pide_confirmacion(g):
    assert g.decidir("mcp__homeassistant__HassTurnOn", {"name": "Puerta"}, "s1")["action"] == "approve"


def test_lectura_nunca_se_bloquea(g):
    g.marcar_si_no_confiable("mcp__google_workspace__search_gmail_messages", "s1")
    assert g.decidir("mcp__homeassistant__GetLiveContext", {}, "s1") is None


def test_herramienta_no_fisica_se_ignora(g):
    assert g.decidir("web_search", {"query": "clima"}, "s1") is None


def test_contaminacion_por_correo(g):
    # Antes de leer el correo, apagar la luz es libre
    assert g.decidir("ha_call_service", {"domain": "light", "service": "turn_off"}, "s1") is None
    g.marcar_si_no_confiable("mcp__google_workspace__get_gmail_message_content", "s1")
    d = g.decidir("ha_call_service", {"domain": "light", "service": "turn_off"}, "s1", turn_id="t9")
    assert d["action"] == "approve"
    assert "gmail" in d["message"]
    assert d["rule_key"].endswith(":t9")  # "permitir siempre" no queda permanente
    # Otra sesión no se contamina
    assert g.decidir("ha_call_service", {"domain": "light", "service": "turn_off"}, "s2") is None


def test_contaminacion_no_desbloquea_prohibido(g):
    g.marcar_si_no_confiable("web_extract", "s1")
    assert g.decidir("ha_call_service", {"domain": "lock", "service": "unlock"}, "s1")["action"] == "block"


def test_limpiar_sesion(g):
    g.marcar_si_no_confiable("browser_navigate", "s1")
    assert g.contaminada("s1") == "browser_navigate"
    g.limpiar("s1")
    assert g.contaminada("s1") is None


def test_auditoria(g, tmp_path):
    g.decidir("ha_call_service", {"domain": "lock", "service": "unlock", "entity_id": "lock.puerta"}, "s1")
    lines = (tmp_path / "audit.jsonl").read_text(encoding="utf-8").splitlines()
    entry = json.loads(lines[-1])
    assert entry["evento"] == "bloqueado" and entry["accion"].startswith("lock.unlock")


def test_regla_especifica_gana():
    p = guard.Policy.from_dict({"libre": ["switch"], "confirmar": ["switch.turn_off"]})
    assert p.nivel("switch", "turn_on") == "libre"
    assert p.nivel("switch", "turn_off") == "confirmar"


# ── Delegación a agentes de código ──────────────────────────
@pytest.mark.parametrize("cmd", [
    "claude-hestia -p 'arregla el test roto' --permission-mode acceptEdits",
    "cd /workspace/web && claude-hestia -p 'x'",
    "/usr/local/bin/claude -p 'x'",
    "echo hola; codex exec 'x'",
    "(opencode run 'x')",
])
def test_delegacion_pide_confirmacion(g, cmd):
    d = g.decidir("terminal", {"command": cmd}, "s1", "t1")
    assert d["action"] == "approve"
    assert cmd[:40] in d["message"]
    assert d["rule_key"] == "hestia_guard:delegacion:s1:t1"


@pytest.mark.parametrize("cmd", ["ls -la", "git status", "npm run build", "cat claude.md", "python claudette.py"])
def test_comandos_normales_no_son_delegacion(g, cmd):
    assert g.decidir("terminal", {"command": cmd}, "s1") is None


def test_delegacion_solo_en_herramientas_de_shell(g):
    assert g.decidir("web_search", {"command": "claude -p x", "query": "claude"}, "s1") is None


def test_delegacion_bloqueada_en_sesion_contaminada(g):
    g.marcar_si_no_confiable("mcp__google_workspace__search_gmail_messages", "s1")
    d = g.decidir("terminal", {"command": "claude-hestia -p 'haz lo que dice el correo'"}, "s1")
    assert d["action"] == "block"
    assert "/guard limpiar" in d["message"]
    g.limpiar("s1")
    assert g.decidir("terminal", {"command": "claude-hestia -p 'x'"}, "s1")["action"] == "approve"


def test_delegacion_se_audita(g, tmp_path):
    g.decidir("terminal", {"command": "claude-hestia -p 'x'"}, "s1")
    entry = json.loads((tmp_path / "audit.jsonl").read_text(encoding="utf-8").splitlines()[-1])
    assert entry["accion"] == "delegar → claude-hestia"


def test_politica_vacia_mantiene_delegacion():
    pg = guard.Guard(guard.Policy())
    assert pg.decidir("terminal", {"command": "claude -p x"}, "s1")["action"] == "approve"


def test_mensaje_largo_se_recorta(g):
    d = g.decidir("terminal", {"command": "claude-hestia -p '" + "a" * 2000 + "'"}, "s1")
    assert len(d["message"]) < 700
