# Skills y plugins: cómo enseñarle cosas nuevas a Hestia

Hestia aprende de tres maneras, de menos a más esfuerzo:

1. **Se lo dices:** "de ahora en adelante, cuando te pida el resumen, incluye el precio del dólar". Lo guarda en la memoria o actualiza una skill.
2. **Lo aprende sola:** después de resolver bien una tarea nueva de varios pasos, Hermes le sugiere crear una skill. Como `skills.write_approval: true`, queda **pendiente de tu aprobación**: `/skills` para verla, `/skills approve <nombre>` para aceptarla. El *Curator* de Hermes consolida y archiva las skills viejas.
3. **Tú escribes una skill o un plugin** en este repo (abajo).

## Escribir una skill

Una skill es una carpeta con un `SKILL.md`: instrucciones en lenguaje natural que el agente carga cuando la `description` coincide con lo que le piden.

```
skills/<categoria>/<nombre>/
├── SKILL.md          # obligatorio
├── references/       # opcional: documentación que la skill puede leer
└── scripts/          # opcional: scripts que la skill ejecuta
```

```markdown
---
name: mi-skill
description: Qué hace y CUÁNDO usarla, con frases de ejemplo ("cuando el usuario diga…"). Es lo que el agente lee para decidir.
version: 1.0.0
metadata:
  hermes:
    tags: [categoria]
---

# Título
Pasos, ejemplos, formato de respuesta y **límites de seguridad**.
```

Buenas prácticas:
- La `description` es lo más importante: incluye frases reales en español **y** en inglés.
- Incluye siempre una sección de **seguridad/límites** (qué nunca hacer sin confirmación).
- Nada de datos personales en la skill: el repo es público. Haz referencia a `USER.md`.
- Valida con `pytest` (el CI revisa el frontmatter) y con `hermes -p hestia skills check`.

Para publicar los cambios: commit → push → `hermes profile update hestia` (nativo) o `docker compose up -d --force-recreate hestia-init hestia` (Docker).

### Skills de otros
Hermes trae un hub de skills (`hermes skills browse`) y OpenJarvis puede importar skills de Hermes y OpenClaw. **Revisa cada skill de terceros antes de instalarla**: el marketplace de OpenClaw llegó a tener más de 1.184 skills maliciosas. Lee el `SKILL.md` y sus `scripts/`.

## Escribir un plugin

Los plugins son código Python que se engancha en Hermes: herramientas nuevas, hooks del ciclo de vida y comandos. Úsalos cuando una skill no alcance, por ejemplo para integrar una API sin MCP o para imponer una regla de seguridad.

```
plugins/mi_plugin/
├── plugin.yaml
└── __init__.py      # def register(ctx): ...
```

```python
def register(ctx):
    ctx.register_tool(name="mi_tool", toolset="mi_plugin", schema={...}, handler=fn)
    ctx.register_hook("pre_tool_call", mi_hook)   # devuelve {"action": "block"|"approve", "message": ...}
    ctx.register_command("micomando", handler)
```

Referencia: [plugins de Hermes](https://hermes-agent.nousresearch.com/docs/user-guide/features/plugins). El ejemplo completo es [`plugins/hestia_guard`](../plugins/hestia_guard/) con sus [pruebas](../tests/test_guard.py).

Para que el plugin viaje con la distribución, agrégalo a `distribution_owned` en [`distribution.yaml`](../distribution.yaml) y a `plugins.enabled` en [`config.yaml`](../config.yaml).

## Conectar un servicio con MCP

Si el servicio ya tiene un servidor MCP, no escribas código: agrégalo en `config.yaml`.
```yaml
mcp_servers:
  mi_servicio:
    url: "https://…/mcp"          # o command: + args: para stdio
    headers: { Authorization: "Bearer ${MI_TOKEN}" }
    trust: untrusted               # las escrituras piden aprobación
    tools:
      include: ["buscar_*", "leer_*"]   # lista blanca
```
Si trae contenido externo (correos, web, documentos), agrega su patrón a `fuentes_no_confiables` en la política de `hestia_guard`.
