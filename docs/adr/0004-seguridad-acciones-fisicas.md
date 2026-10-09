# ADR-0004: Confirmación humana y separación de privilegios en acciones físicas

- **Estado:** aceptada (2026-10-09)

## Contexto
Investigación sobre *promptware* (arXiv 2508.12175): un correo o un evento de calendario envenenado logró que un asistente abriera ventanas y encendiera una caldera. Hestia lee Gmail y Calendar, y controla la casa.

## Decisión
**Defensa en capas:**
1. **HA:** el agente usa un usuario no admin. `lock` y `alarm_control_panel` **no se exponen**; se accede a ellos con scripts de HA que exigen confirmación.
2. **Plugin `hestia_guard`:**
   - Clasifica los dominios en `libre` (luces, media), `confirmar` (clima, cubiertas, scripts sensibles) y `prohibido`.
   - Marca el turno como *contaminado* cuando el contexto incluye contenido externo (correo, web, calendario).
   - En un turno contaminado, **cualquier** acción física pide confirmación.
   - Registra todas las llamadas en un log de auditoría.
3. **MCP con `trust: untrusted`** para Gmail, GitHub y n8n: toda herramienta de escritura (enviar correo, crear issue) exige aprobación. Opcionalmente `--read-only`.
4. **Fase 3:** dos instancias de Hermes. Una *lectora* (correo, web, calendario), sin herramientas físicas, y una *actuadora* (casa), sin acceso a contenido externo. Se comunican solo con resúmenes estructurados.
5. **Skills de terceros:** no se instalan sin revisión manual. `skills.write_approval: true` controla las skills que el propio agente escribe.

## Consecuencias
- ✅ Una inyección de prompt no basta para hacer daño físico.
- ⚠️ Hay algo de fricción: algunas órdenes piden un "sí" por Telegram.
