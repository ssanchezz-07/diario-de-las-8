---
tipo: proyecto
estado: en uso
actualizado: 2026-10-22
tags: [proyecto, noticias, github-actions]
---
# Diario de las 8

> Periódico personal de cada mañana (Mundo, España, Málaga, Economía y mercados, Fiscal y laboral, Tecnología e IA, Cofrade) que se genera solo, sin Claude, con GitHub Actions.

## Estado actual
- 🟢 Publicado: https://ssanchezz-07.github.io/diario-de-las-8/ (repo `ssanchezz-07/diario-de-las-8`, Pages desde `main` /docs). Acceso «Diario de las 8» del Escritorio apunta ahí.
- Sustituye al artefacto «Diario de las 8» (https://claude.ai/artifact/DLHMxfj9Kdh6HMh9n9uWKF), que tenía los datos escritos a mano y se quedó en el 4 de octubre.

## Dónde está cada cosa
| Ruta | Qué es |
|---|---|
| `generar.py` | Lee RSS (El País, BBC Mundo, Expansión, Xataka, Google News por tema) y Yahoo Finance; quita duplicados; escribe `docs/index.html`. Solo biblioteca estándar |
| `plantilla.html` | Diseño (el del artefacto antiguo); `__DATOS__` se sustituye por el JSON del día |
| `docs/` | Lo que publica GitHub Pages (`index.html`, manifiesto e icono para instalarlo en el móvil) |
| `.github/workflows/diario.yml` | Tarea diaria a las 05:15 UTC (07:15 en verano, 06:15 en invierno) + botón manual |

## Cómo se ejecuta
```
python generar.py      # genera docs/index.html en local
```
En GitHub: pestaña Actions → «Diario de las 8» → Run workflow.

## Decisiones y reglas
- GitHub Actions + Pages y no una tarea de Claude: Pablo pidió que se actualice «sin ti». Gratis y visible desde el móvil.
- La tarea hace un commit diario: así GitHub no la desactiva por inactividad (lo hace a los 60 días sin cambios).
- Sin resúmenes con IA: titular + entradilla del medio. Si se quisiera resumir, haría falta una clave de API (de pago).
- Si una fuente cae, la sección sale con las demás; si la edición no es de hoy, la página lo avisa.
- Plazos de la AEAT (1-20 de abril, julio y octubre; 1-30 de enero) como aviso en Fiscal.

## Pendientes
- [ ] Comprobar que la tarea de mañana (05:15 UTC) se ejecuta en la pestaña Actions.
- [ ] Pablo: abrir la dirección en el móvil → «Añadir a pantalla de inicio».

## Relacionado
- [[00 Índice]] · [[Artefactos publicados]]

## Historial
- 2026-10-04: última edición manual en artefacto.
- 2026-10-22: generador automático con GitHub Actions.
- 2026-10-22: publicado en GitHub Pages con el visto bueno de Pablo.
