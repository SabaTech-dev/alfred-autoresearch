# AutoResearch SDK

[![PyPI version](https://img.shields.io/pypi/v/autoresearch.svg)](https://pypi.org/project/autoresearch/)
[![Python](https://img.shields.io/pypi/pyversions/autoresearch.svg)](https://pypi.org/project/autoresearch/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

**Standalone Python SDK for autonomous experiment loops.**

Try ideas, keep what works, discard what doesn't, never stop.

Inspired by [karpathy/autoresearch](https://github.com/karpathy/autoresearch) and the OpenClaw AutoResearch plugin.

## Features

- 🔄 **Experiment Loop Engine** — init → run → log → improve → repeat (a PDCA loop: plan/description, do/run, check/confidence, act/keep-discard)
- 📊 **Statistical Confidence** — MAD-based noise floor to distinguish real improvements from noise
- 📝 **Ideas Backlog** — Failed experiments automatically generate ideas for future exploration (deduplicated)
- 📈 **State Persistence** — JSONL results log, survives restarts
- 📄 **Session Reports** — `autoresearch report` regenerates a Markdown summary of everything tried
- 🤖 **Agent-friendly** — `status --json` for machine-readable state
- 🛠️ **CLI** — Full command-line interface with rich output
- 🐍 **Pure Python** — Zero external dependencies required (only `rich` + `click`)
- 📦 **OpenClaw Compatible** — Same JSONL format as the OpenClaw AutoResearch plugin

## Installation

```bash
pip install autoresearch
```

## Quick Start

### CLI

```bash
# Initialize experiment
autoresearch init --name "optimize-latency" --metric latency_ms --direction lower --unit ms

# Run baseline
autoresearch run -c "./benchmark.sh"

# Log result
autoresearch log -d "Baseline measurement"

# Make changes, run again
autoresearch run -c "./benchmark.sh"
autoresearch log -d "Added caching layer"

# Discard bad idea
autoresearch run -c "./benchmark.sh"
autoresearch log -s discard -d "Thread pool didn't help" -i "Try async I/O instead"

# Check status (human or machine-readable)
autoresearch status
autoresearch status --json

# Review the ideas backlog (deduplicated)
autoresearch ideas

# Regenerate the session report (autoresearch.md)
autoresearch report
```

### Python API

```python
from autoresearch import AutoResearch

# Initialize
ar = AutoResearch(
    name="optimize-latency",
    metric="latency_ms",
    direction="lower",  # lower is better
    unit="ms",
)

ar.init()

# Run baseline
result = ar.run("./benchmark.sh")
print(f"Passed: {result.passed}, Duration: {result.duration_seconds:.1f}s")
ar.log("Baseline measurement")

# Run experiment
result = ar.run("./benchmark.sh")
if result.passed:
    ar.log("Added Redis caching")
else:
    ar.log("Crashed", status="crash")

# Discard with idea
result = ar.run("./benchmark.sh")
ar.discard_with_idea("Thread pool overhead", "Try event loop instead")

# Check confidence
print(f"Confidence: {ar.confidence}")
print(f"Best: {ar.best_metric} vs Baseline: {ar.baseline_metric}")

# Export results
import json
print(json.dumps(ar.get_status(), indent=2))
```

## How It Works

### The Loop

```
SCAN → HYPOTHESIS → EXPERIMENT → MEASURE → INTEGRATE → repeat
```

1. **SCAN** — Identify optimization opportunities
2. **HYPOTHESIS** — Form a testable hypothesis
3. **EXPERIMENT** — Make the change and run the benchmark
4. **MEASURE** — Parse metrics, compare to baseline
5. **INTEGRATE** — Keep if better, discard if worse, log idea for future

### Confidence Scoring

AutoResearch uses **Median Absolute Deviation (MAD)** as the noise floor:

| Confidence | Meaning |
|-----------|---------|
| ≥ 2.0x | Improvement is likely real ✅ |
| 1.0-2.0x | Above noise but marginal ⚠️ |
| < 1.0x | Within noise, re-run to confirm ❓ |

This prevents false positives from natural variance.

### Output Format

Your benchmark script should output `METRIC name=value` lines:

```bash
#!/bin/bash
set -euo pipefail

# Run your benchmark
result=$(./my_benchmark)

# Output metrics
echo "METRIC latency_ms=$result"
echo "METRIC throughput_qps=$(echo '10000 / ' $result | bc)"
```

### Persistence

All results are stored in `autoresearch.results.jsonl`:

```jsonl
{"type": "config", "name": "optimize-latency", "metricName": "latency_ms", "metricUnit": "ms", "bestDirection": "lower"}
{"run": 1, "commit": "abc1234", "metric": 142.5, "metrics": {"latency_ms": 142.5}, "status": "keep", "baseline": true, "description": "Baseline", "timestamp": 1713888000, "segment": 0, "confidence": null}
```

### Ideas Backlog

Discarded experiments append to `autoresearch.ideas.md`:

```markdown
- Try async I/O instead of thread pool
- Consider connection pooling for database
- Pre-compute lookup table for hot path
```

## Architecture

```
autoresearch/
├── src/autoresearch/
│   ├── __init__.py        # Public API
│   ├── core/
│   │   ├── engine.py      # Experiment loop engine
│   │   ├── confidence.py  # Statistical confidence (MAD)
│   │   └── metrics.py     # METRIC name=value parser
│   ├── cli.py             # Rich CLI interface
│   ├── utils/
│   └── metrics/
├── tests/
│   ├── test_autoresearch.py  # Engine, confidence, metrics, ideas, report
│   └── test_cli.py           # CLI end-to-end
├── docs/
│   ├── arquitectura.md    # Architecture review + ADRs (Spanish)
│   ├── roadmap.md         # Prioritized roadmap: multi-agent / CLI / PDCA-Kaizen
│   └── manual_usuario.md  # User guide (Spanish)
├── CHANGELOG.md
├── pyproject.toml
└── README.md
```

See `docs/arquitectura.md` for the full architecture review and `docs/roadmap.md`
for the prioritized improvement proposal (multi-agent generalization, reusable
CLI, integrated PDCA/Kaizen cycles).

## Comparison with OpenClaw AutoResearch Plugin

| Feature | OpenClaw Plugin | Python SDK |
|---------|----------------|------------|
| Experiment loop | ✅ (via tools) | ✅ (API + CLI) |
| Confidence scoring | ✅ (MAD) | ✅ (MAD, same algorithm) |
| Ideas backlog | ✅ | ✅ |
| State persistence | ✅ (JSONL) | ✅ (JSONL, compatible) |
| Git integration | ✅ (auto checkout) | ⚠️ (commit tracking only) |
| Session management | ✅ (OpenClaw sessions) | ❌ (standalone) |
| Rich output | ✅ | ✅ (click + rich) |
| OpenClaw required | ✅ | ❌ |
| Python importable | ❌ | ✅ |

## License

MIT — Use it however you want.

## Author

Jose Manuel Sabarís García ([@llllJokerllll](https://github.com/llllJokerllll))

## Acknowledgments

- [karpathy/autoresearch](https://github.com/karpathy/autoresearch) — Original concept
- [OpenClaw AutoResearch Plugin](https://github.com/openclaw/openclaw) — Confidence algorithm and JSONL format
