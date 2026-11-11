# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/),
versionado [SemVer](https://semver.org/lang/es/).

## [1.3.0] — 2026-11-10

### Añadido (quickwins P1 del roadmap — card 3b4075eb)

- **Campo `agent` en el schema JSONL** (aditivo, opcional, default `null`): los
  runs registran qué agente los produjo. *Migration note*: los ficheros JSONL
  del plugin OpenClaw sin el campo siguen cargando sin cambios.
- **Locking inter-proceso**: lock exclusivo fcntl (`.autoresearch.lock`) en
  torno a los appends del JSONL y la persistencia del pending; múltiples
  agentes ya no pierden runs por appends intercalados.
- **Pending por agente** (`.autoresearch.pending.<agent>.json`): un agente
  nunca hereda ni descarta el pending de otro (bug del run #81 del plugin).
  Los runs sin agente mantienen el nombre legado `.autoresearch.pending.json`.
- **Registry opcional**: `~/.autoresearch/registry.json` (o `$AUTORESEARCH_HOME`)
  registra experimentos conocidos; nuevo comando `autoresearch experiments`.
  El registro es best-effort: el modo cwd-only funciona sin registry.
- **CLI `--agent <id>`** en `run` y `log`; `status --json` lo expone.
- **CLI `--json` global** en `run`, `log`, `ideas` y `report`: salida JSON sin
  color, con exit codes documentados (0 ok, 1 sin estado
  `not_initialized`/`no_pending_run`, 2 uso inválido).
- **Runners pluggables** (`autoresearch.runners`): protocolo `Runner`
  (cualquier objeto con `execute()`), `SubprocessRunner` (default histórico),
  `CallableRunner` (benchmark Python in-process) y `CommandRunner` (comando
  fijo con env/timeout enriquecidos).
- `status --json` y `export` emiten JSON plano sin colorear (antes rich podía
  colorear y romper el parseo por agentes).

### Corregido

- Un run que pasa sin reportar la métrica primaria se registra como
  `status=no-metric` en vez de un 0.0 silencioso (P-3); `best_metric` lo ignora.
  *Migration note*: el valor `no-metric` es nuevo en el campo `status`; los
  consumidores del JSONL deben tratarlo como run sin métrica.

## [1.2.0] — 2026-10-27

### Añadido

- CLI `autoresearch ideas`: visualiza el backlog de ideas descartadas.
- CLI `autoresearch report`: regenera el informe de sesión `autoresearch.md`
  desde los runs registrados (la constante existía pero era código muerto).
- CLI `autoresearch status --json`: estado completo en JSON para consumo por
  agentes (también en experimentos sin inicializar).
- `AutoResearch.generate_report()`: render Markdown del experimento (formato
  del plugin OpenClaw).
- Deduplicación de ideas: el mismo texto no se añade dos veces al backlog.
- Suite de tests de CLI (`tests/test_cli.py`, CliRunner) — cobertura del 66% al 90%.
- Documentación: `docs/arquitectura.md` (review con defectos catalogados),
  `docs/roadmap.md` (propuesta priorizada multi-agente / CLI / PDCA-Kaizen),
  `docs/manual_usuario.md`, este CHANGELOG.

### Corregido

- `log(status=...)` sin descripción ignoraba el estado: un run descartado se
  registraba como `keep` y contaminaba `best_metric` (D-1).
- Los experimentos sin nombre no restauraban metricName/direction del JSONL al
  reanudar: los argumentos del constructor ganaban silenciosamente y podían
  invertir el significado de "mejor" (D-2).
- `ExecutionResult.tail_output` era una property con parámetro inutilizable;
  convertido a método (D-3).
- Limpieza de lint: 7 avisos ruff a 0 (SIM102, PLW1510 con `check=False`
  explícito, PLR0124 NaN vía `math.isnan`).

### Cambiado

- Bump de versión 1.1.0 → 1.2.0.
- URLs del pyproject apuntadas al remote real (SabaTech-dev/alfred-autoresearch).

## [1.1.0] — 2026-06-27

### Añadido

- SDK standalone v1.1.0: engine de experimentos, confianza MAD, parser de
  métricas, CLI click+rich, persistencia JSONL compatible con el plugin
  OpenClaw AutoResearch, pending run persistente entre comandos, LICENSE MIT.

## [1.0.0] — 2026-06-27

### Añadido

- Versión inicial: bucle init/run/log, ideas backlog, checkpoint.
