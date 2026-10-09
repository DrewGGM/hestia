---
name: finanzas-personales
description: Registrar gastos e ingresos, recordar pagos y vencimientos (servicios, arriendo, impuestos), resumir el mes y alertar sobre desviaciones del presupuesto. Úsala cuando el usuario diga "gasté…", "pagué…", "¿cuánto llevo gastado?", "¿qué pagos vienen?", "recuérdame la declaración", o envíe una foto de una factura.
version: 1.0.0
metadata:
  hermes:
    tags: [finanzas, gastos, presupuesto]
---

# Finanzas personales

## Registro
- "Gasté 45 mil en mercado" → `{fecha, monto: 45000, moneda, categoría: Mercado, medio, nota}`.
- Guarda en la hoja o base que el usuario defina en `USER.md` (Google Sheets vía MCP de Workspace, o un CSV en la carpeta de datos de Hestia).
- **Foto de una factura:** extrae emisor, fecha, total e impuestos, confirma los datos con el usuario y después registra.

## Vencimientos
Mantén en el calendario los pagos recurrentes (servicios, arriendo, tarjetas) y las fechas de impuestos que el usuario indique. Avisa **3 días antes y el mismo día**.

## Resumen mensual (cron, día 1)
Gasto por categoría frente al presupuesto, las 3 categorías que más crecieron y los pagos pendientes del mes.

## Límites
- **Solo lectura y registro.** Hestia **nunca** hace pagos, transferencias ni presenta declaraciones por su cuenta. Si existe una skill para presentar declaraciones, requiere que el usuario autorice cada paso irreversible.
- No guardes números completos de tarjetas ni contraseñas, ni en memoria ni en notas.
