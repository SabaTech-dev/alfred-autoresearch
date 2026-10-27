# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/),
versionado [SemVer](https://semver.org/lang/es/).

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
