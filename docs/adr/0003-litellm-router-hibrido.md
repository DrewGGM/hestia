# ADR-0003: Enrutamiento híbrido local/nube con LiteLLM

- **Estado:** aceptada (2026-10-09)

## Contexto
Queremos privacidad y latencia baja en las órdenes simples, y potencia en las tareas complejas. La documentación de HA advierte que los modelos pequeños fallan más al controlar la casa, y Hermes pide ≥64k de contexto cuando el modelo principal es Ollama.

## Decisión
- **LiteLLM proxy** (versión fijada **≥1.83.0**) expone un único endpoint OpenAI-compatible con estos alias:
  - `hestia-smart` → Claude (modelo principal de Hermes)
  - `hestia-fast` → Ollama local (tareas auxiliares: compresión, resúmenes cortos, clasificación)
  - `hestia-backup` → OpenRouter (fallback)
- Los fallbacks están definidos en LiteLLM y en Hermes (`fallback providers`).
- **Jev** (TypeSafe AI) queda como clasificador opcional de complejidad y riesgo cuando haya acceso a su API (fase 3).

## Consecuencias
- ✅ Cambiar de modelo no requiere tocar Hermes.
- ✅ Se pueden registrar el coste y el uso por modelo.
- ⚠️ LiteLLM es un servicio más que hay que mantener. Ojo con la cadena de suministro: hubo malware en PyPI en 1.82.7 y 1.82.8, así que usamos solo la imagen oficial con versión fijada.
