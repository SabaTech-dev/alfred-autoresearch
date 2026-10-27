---
created: 2026-10-27
owner: build (opencode)
status: vivo
---

# Roadmap — AutoResearch como harness PDCA/Kaizen universal

## Objetivo estratégico

Convertir este SDK en la base para aplicar **self-improvement + autoresearch +
PDCA + Kaizen sobre cualquier agente de IA, harness de IA y CLI de IA**, no solo
sobre un experimento de métrica única.

Lectura PDCA del ciclo actual: `description`/hipótesis = **Plan**, `run()` = **Do**,
`confidence`/comparación = **Check**, `log(keep|discard)` + backlog de ideas = **Act**.
El harness ya ES un PDCA; lo que falta es hacerlo explícito, multi-agente y reutilizable.

## Enfoques evaluados (brainstorming)

### Enfoque A — Extensión incremental del SDK actual
Extender el engine y el schema JSONL manteniendo compatibilidad total con el
formato del plugin OpenClaw.

- **Pros**: riesgo mínimo; el formato vivo (83+ runs en `~/.openclaw`) sigue
  legible; entrega valor en días; sin coordinator nuevo.
- **Cons**: el God-object `AutoResearch` crece si no se refactoriza a la vez;
  el locking multi-agente parchea el síntoma, no el diseño.
- **Cuándo conviene**: ya (fase 1).

### Enfoque B — Reescritura como framework multi-agente orquestado
Servicio/daemon central con registry de experimentos, workers, cola de runs y UI.

- **Pros**: concurrencia resuelta de raíz; observabilidad global.
- **Cons**: rompe el contrato "standalone, cero dependencias, estado en cwd";
  introduces un single point of failure que el ecosistema OpenClaw ya cubre con
  su gateway; coste de adopción alto para CLIs externas; sobredimensionado para
  el problema real (contención esporádica, no throughput).
- **Cuándo conviene**: si emergen decenas de agentes concurrentes sobre el mismo
  experimento (no es el caso hoy).

### Enfoque C — Core mínimo + adapters + registry (evolución dirigida)
Mantener el core statistístico/persistencia, extraer interfaces (Runner,
Recorder) y añadir un registry multi-experimento opcional.

- **Pros**: habilita runners no-subprocess (callable Python, MCP tool, comando
  ssh) sin tocar el ciclo; registry opcional sin romper el modo cwd; camino
  natural hacia PDCA explícito.
- **Cons**: refactor con riesgo medio; requiere disciplina de interfaces.

### Selección

**A ahora → C por fases.** Justificación: la compatibilidad con el JSONL vivo del
plugin OpenClaw es un activo (evidencia real de uso multi-agente ya existe), el
tiempo de entrega manda para los quick-wins, y B añade infraestructura que no
resuelve nada que A+C no resuelvan con menos acoplamiento. Criterios aplicados:
seguridad (no tocar datos vivos), coste, mantenimiento y compatibilidad.

## Backlog priorizado

### P0 — Quick-wins (ENTREGADOS en v1.2.0, card 8d5c3dd8)

| Ítem | Estado | Evidencia |
|------|--------|-----------|
| Fix D-1 `log(status=)` ignorado sin descripción | Hecho | tests de regresión, 47 verdes |
| Fix D-2 resume de config sin nombre | Hecho | idem |
| Fix D-3 `tail_output` property-roto | Hecho | ruff PLR0206 resuelto |
| CLI `status --json` (salida para agentes) | Hecho | smoke test |
| CLI `ideas` (ver backlog) | Hecho | idem |
| CLI `report` (regenera `autoresearch.md`, antes dead code) | Hecho | idem |
| Dedup de ideas | Hecho | idem |
| Cobertura 66% → 90% | Hecho | `pytest --cov` |
| Limpieza ruff (7 avisos → 0) | Hecho | `ruff check` |
| Docs: CHANGELOG, arquitectura, manual, roadmap, README | Hecho | este commit |

### P1 — Generalización multi-agente (próxima iteración)

Objetivo: que N agentes compartan experimento sin pisarse (hoy: P-1).

1. **`agent` field en el schema JSONL** (opcional, default null). Los runs ya
   registran quién hizo qué. AC: runs del plugin viejos sin `agent` siguen cargando.
2. **Locking de append y pending**: lock exclusivo (fcntl) en torno al
   read-modify-write del pending; pending con nombre por agente
   (`.autoresearch.pending.<agent>.json`). AC: test de concurrencia con 2 procesos
   que intercalan run/log sin perder runs ni heredar pending ajeno.
3. **Registry opcional** `~/.autoresearch/registry.json` (o `AUTORESEARCH_HOME`)
   con punteros a experimentos por cwd. AC: `autoresearch experiments` lista
   experimentos conocidos; el modo cwd-only sigue funcionando sin registry.
4. **Aislamiento por defecto en `--agent <id>`**: `ar.run()` y CLI aceptan agent-id;
   los status lo muestran. AC: run #81 del plugin (flush de pending ajeno) sería
   imposible.

### P1 — CLI reutilizable para cualquier harness

1. **`--json` global** en todos los comandos (run, log, ideas, report) con exit
   codes documentados (0 ok, 1 sin estado, 2 uso inválido). AC: agente puede
   operar el ciclo completo sin parsear texto humano.
2. **Runner pluggable** (`Protocol Runner`): SubprocessRunner (hoy) +
   CallableRunner (función Python) + CommandRunner con env/timeout enriquecidos.
   AC: benchmark callable in-process sin bash.
3. **Warn en run sin METRIC** (P-3): un run que pasa sin métrica se marca
   `no-metric` explícito en vez de 0.0 silencioso. AC: test distingue crash de
   sin-métrica.

### P2 — Ciclos PDCA/Kaizen integrados

1. **Ciclo explícito**: comando `autoresearch cycle --plan "..."` que agrupa
   runs bajo un ciclo P/D/C/A etiquetado (el `segment` actual es el embrión).
   AC: report agrupa por ciclo con veredicto Check (confidence) y Act (keep/discard).
2. **Kaizen: consumo del backlog**: `autoresearch ideas --next` saca (pop) la
   idea más antigua y la convierte en hipótesis sugerida para el siguiente
   experimento (cierra el loop descartar→aprender→reintentar).
   AC: flujo discard→ideas--next→run→keep pasa end-to-end en test.
3. **Learnings log separado**: distinguir "idea a probar" de "lección aprendida"
   (hoy el backlog del plugin mezcla ambas). Schema: `autoresearch.learnings.md`.
4. **Kaizen scorecard**: métrica de mejora continua = Δ best por segmento +
   tasa de ideas convertidas en keeps. AC: `status --json` expone `kaizen` block.
5. **Integración self-improvement Alfred**: adaptador que exporta un ciclo
   cerrado al formato de `iteration-complete` (SESSION-STATE/daily). AC: un ciclo
   completo genera el bloque de daily-note automáticamente.

### Restricciones vigentes

- **NO reintroducir CI que dependa del runner self-hosted** (offline; commit
  23b96e6 eliminó pr-agent por eso). Cualquier CI futuro debe correr en
  GitHub-hosted runners.
- Compatibilidad JSONL con el plugin OpenClaw es un contrato: cambios de schema
  solo aditivos y con migration notes en CHANGELOG.
- Mantener el motor stdlib-puro; click/rich solo en la capa CLI.

## Riesgos

| Riesgo | Mitigación |
|--------|-----------|
| Refactor de interfaces (C) rompa consumidores | Extraer interfaces en P1 con adapters shim y deprecations |
| Schema drift con el plugin OpenClaw | Campos aditivos opcionales + tests con fixtures del JSONL real |
| Locking introduce deadlocks | Timeouts en locks + tests de concurrencia con y sin contención |
| Scope creep hacia "framework" | Cada ítem P1/P2 con AC cerradas; lo que no tiene AC no entra |
