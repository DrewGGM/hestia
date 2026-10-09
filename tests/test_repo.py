"""Validación estructural del repo: YAML/JSON parsean, skills bien formadas, distribución coherente."""
import json
import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
SKILLS = sorted(ROOT.glob("skills/**/SKILL.md"))
YAMLS = [p for p in ROOT.rglob("*.y*ml") if ".git" not in p.parts and "data" not in p.parts]


class _Loader(yaml.SafeLoader):
    """Acepta los tags propios de ESPHome/HA (!secret, !include…)."""


_Loader.add_multi_constructor("!", lambda loader, suffix, node: None)


@pytest.mark.parametrize("path", YAMLS, ids=lambda p: str(p.relative_to(ROOT)))
def test_yaml_valido(path):
    yaml.load(path.read_text(encoding="utf-8"), Loader=_Loader)


def test_cron_jobs():
    data = json.loads((ROOT / "cron" / "jobs.json").read_text(encoding="utf-8"))
    ids = [j["id"] for j in data["jobs"]]
    assert len(ids) == len(set(ids))
    skill_names = {_frontmatter(p)["name"] for p in SKILLS}
    for job in data["jobs"]:
        assert job.get("prompt") and job.get("schedule")
        for s in job.get("skills", []):
            assert s in skill_names, f"cron {job['id']} usa la skill inexistente {s}"


def _frontmatter(path: Path) -> dict:
    m = re.match(r"^---\n(.*?)\n---\n", path.read_text(encoding="utf-8"), re.S)
    assert m, f"{path} sin frontmatter"
    return yaml.safe_load(m.group(1))


@pytest.mark.parametrize("path", SKILLS, ids=lambda p: p.parent.name)
def test_skill_frontmatter(path):
    fm = _frontmatter(path)
    assert fm["name"] == path.parent.name, "name debe coincidir con la carpeta"
    assert re.fullmatch(r"[a-z0-9-]+", fm["name"])
    assert len(fm.get("description", "")) >= 60, "description demasiado corta para que el agente la elija"
    assert fm.get("version")


def test_nombres_de_skill_unicos():
    names = [_frontmatter(p)["name"] for p in SKILLS]
    assert len(names) == len(set(names))


def test_distribucion_coherente():
    dist = yaml.safe_load((ROOT / "distribution.yaml").read_text(encoding="utf-8"))
    assert dist["name"] == "hestia"
    for rel in dist["distribution_owned"]:
        assert (ROOT / rel).exists(), f"distribution_owned apunta a {rel}, que no existe"
    cfg = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
    assert "hestia_guard" in cfg["plugins"]["enabled"]
    assert cfg["skills"]["write_approval"] is True
    assert cfg["approvals"]["mode"] == "manual"


def test_compose_solo_localhost():
    compose = yaml.safe_load((ROOT / "docker-compose.yml").read_text(encoding="utf-8"))
    for name, svc in compose["services"].items():
        for port in svc.get("ports", []):
            assert str(port).startswith("127.0.0.1:"), f"{name} publica {port} fuera de localhost"


def test_env_example_sin_secretos():
    text = (ROOT / ".env.example").read_text(encoding="utf-8")
    assert not re.search(r"sk-ant-[A-Za-z0-9]", text)
    assert not re.search(r"\d{8,10}:[A-Za-z0-9_-]{30,}", text)  # token de Telegram


def test_versiones_fijadas_coinciden():
    """HERMES_VERSION y CLAUDE_CODE_VERSION iguales en Dockerfile, compose y .env.example."""
    env = dict(re.findall(r"^([A-Z_]+)=(.*)$", (ROOT / ".env.example").read_text(encoding="utf-8"), re.M))
    dockerfile = (ROOT / "docker" / "Dockerfile").read_text(encoding="utf-8")
    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    for var in ("HERMES_VERSION", "CLAUDE_CODE_VERSION"):
        assert f"ARG {var}={env[var]}" in dockerfile, var
        assert f"${{{var}:-{env[var]}}}" in compose, var


def test_suscripcion_aislada():
    """La suscripción de Claude nunca se usa como modelo de Hermes (ADR-0005)."""
    cfg = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
    assert cfg["auth"]["adopt_external_logins"] is False
    env_example = (ROOT / ".env.example").read_text(encoding="utf-8")
    assert not re.search(r"^\s*#?\s*(CLAUDE_CODE_OAUTH_TOKEN|ANTHROPIC_TOKEN)=", env_example, re.M)
