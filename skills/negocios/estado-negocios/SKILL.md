---
name: estado-negocios
description: Supervisar los negocios y proyectos de software del usuario (repos de GitHub, releases, issues, deploys, workflows de n8n, sitios web, redes sociales). Úsala cuando el usuario pregunte "¿cómo va X?", "¿hay issues nuevos?", "¿pasó el build?", "¿el sitio está arriba?", "resume la semana de los proyectos".
version: 1.0.0
metadata:
  hermes:
    tags: [negocios, desarrollo, github, n8n]
---

# Estado de negocios y proyectos

La lista de negocios, repos, URLs y workflows vive en **`USER.md`** (sección *Negocios*), no aquí.

## Chequeos
| Qué | Cómo |
|---|---|
| Repos | GitHub MCP (solo lectura): PRs abiertos, issues nuevos, el último release y el estado de los checks de `main` |
| Builds y deploys | Estado del último workflow de GitHub Actions |
| Sitios web | Petición HTTP a cada URL: código, latencia y si el certificado vence pronto |
| Automatizaciones | n8n MCP: ejecuciones fallidas en las últimas 24 h |
| Redes | Solo si existe un flujo de publicación configurado. Hestia **no publica** sin aprobación |

## Formato
- "¿Cómo va todo?" → una línea por negocio con un semáforo 🟢🟡🔴 y solo los detalles de lo que no está en verde.
- Resumen semanal (cron, lunes 8:00): qué se movió, qué está bloqueado y qué vence.

## Permisos
- GitHub: leer, comentar y crear issues sí. **Mergear, borrar ramas, crear releases o hacer push no**, salvo con orden explícita y confirmación.
- n8n: reintentar una ejecución fallida requiere confirmación.
