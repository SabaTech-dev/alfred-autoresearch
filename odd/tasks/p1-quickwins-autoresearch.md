# Feature: P1 quickwins alfred-autoresearch (multi-agente + CLI reutilizable)

**Objective**: Ejecutar los quickwins P1 del roadmap (docs/roadmap.md) en la rama
`feat/pdca-kaizen-quickwins`: generalización multi-agente y CLI reutilizable.
**Branch**: `feat/pdca-kaizen-quickwins` (ya existente, base b799926).
**Delivery strategy**: single feature branch, work-unit commits; PR/merge decisión del dueño.
**Test runner**: `.venv/bin/python -m pytest tests/ -q --cov=autoresearch` + `.venv/bin/ruff check src tests`.
**Card**: 3b4075eb (workboard). Base: card 8d5c3dd8 (P0 entregado en v1.2.0).

## Specs

S1. **Campo `agent` en schema JSONL** (aditivo, opcional, default null). "Los runs
ya registran quién hizo qué. AC: runs del plugin viejos sin `agent` siguen cargando."
S2. **Locking de append y pending**: lock exclusivo (fcntl) en torno al
read-modify-write del pending; pending con nombre por agente
(`.autoresearch.pending.<agent>.json`). "AC: test de concurrencia con 2 procesos
que intercalan run/log sin perder runs ni heredar pending ajeno."
S3. **Registry opcional** `~/.autoresearch/registry.json` (o `AUTORESEARCH_HOME`)
con punteros a experimentos por cwd. "AC: `autoresearch experiments` lista
experimentos conocidos; el modo cwd-only sigue funcionando sin registry."
S4. **Aislamiento por defecto en `--agent <id>`**: "ar.run() y CLI aceptan
agent-id; los status lo muestran. AC: run #81 del plugin (flush de pending ajeno)
sería imposible."
S5. **`--json` global** en todos los comandos (run, log, ideas, report) "con exit
codes documentados (0 ok, 1 sin estado, 2 uso inválido). AC: agente puede operar
el ciclo completo sin parsear texto humano."
S6. **Runner pluggable** (`Protocol Runner`): "SubprocessRunner (hoy) +
CallableRunner (función Python) + CommandRunner con env/timeout enriquecidos.
AC: benchmark callable in-process sin bash."
S7. **Warn en run sin METRIC** (P-3): "un run que pasa sin métrica se marca
`no-metric` explícito en vez de 0.0 silencioso. AC: test distingue crash de
sin-métrica."
S8. **Compatibilidad JSONL con plugin OpenClaw es contrato**: cambios solo
aditivos con migration notes en CHANGELOG. Motor stdlib-puro; click/rich solo CLI.
S9. NO reintroducir CI self-hosted. Sin PR/merge (decisión del dueño).

## Tasks

- T1 [S1,S4] DONE commit 4afbd89 (RED->GREEN, +JSON plano status/export). (inline)
- T2 [S7] DONE commit 4afbd89 (RED->GREEN). (inline)
- T3 [S2] DONE commit c7e32f3 (test 2 procesos x 10 runs, 0 perdidos, pending aislado). (inline)
- T4 [S3] DONE commit 35177ee. (inline)
- T5 [S4] DONE commit 05793ce. (inline)
- T6 [S5] DONE commit 05793ce (exit 1 not_initialized/no_pending_run, exit 2 click). (inline)
- T7 [S6] DONE commit d0fc084. (inline)
- T8 [S8,S9] DONE commit 596eebd (v1.3.0, migration notes). (inline)

## Verification

```bash
cd ~/repos/alfred-autoresearch && .venv/bin/python -m pytest tests/ -q --cov=autoresearch
.venv/bin/ruff check src tests && .venv/bin/ruff format --check src tests
# Smoke: init/run(callable)/log/status --json/experiments con y sin registry
```

## Log

- L1 (2026-11-10): Card 3b4075eb: "alfred-autoresearch: ejecutar quickwins del
  roadmap en branch feat/pdca-kaizen-quickwins." Scope fijado a P1 del roadmap
  (S1-S7); P2 (ciclos PDCA/Kaizen) queda para próxima iteración. Pre-flight
  acpx-status: LIMPIO. Card movida a running vía `openclaw workboard move`
  (claim-token no disponible para agentes OpenCode — desviación ya documentada
  en card 8d5c3dd8).

- L2 (2026-11-10): Ejecución completa T1-T8. Suite 80 passed, cobertura 90%,
  ruff check+format limpios. Smoke CLI --json/agent/experiments OK
  (/tmp/opencode/ar-smoke13). 3 fallos preexistentes en la base (rich colorizaba
  status --json/export) corregidos en 4afbd89. Rama pusheada a origin; sin PR ni
  merge (decisión del dueño). Movida a review.
