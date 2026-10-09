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
