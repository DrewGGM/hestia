# Wake word "Hey Hestia" (fase 4)

Mientras tanto, usa las wake words de fábrica: **"Hey Jarvis"** (español) y **"Okay Nabu"** (inglés) en los satélites, y **"Hey Hermes"** en el voice mode del PC.

## Entrenar "Hey Hestia"

| Destino | Herramienta | Resultado |
|---|---|---|
| Satélites ESP32-S3 / Voice PE | [OHF-Voice/micro-wake-word](https://github.com/OHF-Voice/micro-wake-word) → `basic_training_notebook.ipynb` | `hey_hestia.json` + `.tflite` |
| Servidor (openWakeWord / PC) | [openWakeWord](https://github.com/dscripka/openWakeWord) → notebook de entrenamiento automático | `hey_hestia.tflite` / `.onnx` |

Ambos notebooks generan las muestras sintéticas con Piper, así que no hace falta grabar cientos de audios.

1. Abre el notebook en Google Colab (necesita GPU).
2. Frase objetivo: `hey hestia`. Agrega variantes de pronunciación: `hey estia`, `oye hestia`.
3. Descarga el modelo, ponlo en esta carpeta y haz commit.
4. ESPHome: descomenta el bloque `micro_wake_word` de [`../esphome/hestia-satelite-voice-pe.yaml`](../esphome/hestia-satelite-voice-pe.yaml).
5. openWakeWord: el compose monta esta carpeta como `--custom-model-dir`. Selecciona `hey_hestia` en el pipeline de Assist.

> microWakeWord está en *early release*. Hay reportes de errores de esquema con ESPHome 2026.7, así que fija la versión de ESPHome si algo falla.
