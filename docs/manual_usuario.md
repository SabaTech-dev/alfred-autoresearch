---
created: 2026-10-27
owner: build (opencode)
status: vivo
version: 1.2.0
---

# Manual de usuario — AutoResearch SDK

## Requisitos

- Python 3.10 o superior
- Un benchmark que emita líneas `METRIC nombre=valor` (por stdout o stderr)

## Instalación

```bash
# Desde el repositorio (recomendado en este entorno)
uv venv && uv pip install -e .

# Desde PyPI
pip install autoresearch
```

## Conceptos básicos

Un **experimento** tiene una métrica principal y una dirección de mejora
(`lower`/`higher`). Cada ejecución del benchmark es un **run**. Tras ejecutarlo,
se **registra** (`log`) con un veredicto: `keep` (mantener), `discard` (descartar,
con idea para el futuro) o `crash` (falló). El motor calcula la **confianza**
estadística (multiplicador del suelo de ruido MAD) y trackea baseline y mejor
métrica. Todo persiste en ficheros del directorio de trabajo.

## Ciclo de trabajo con la CLI

```bash
# 1. Inicializar (una vez por experimento)
autoresearch init --name optimizar-latencia --metric latency_ms \
    --direction lower --unit ms

# 2. Ejecutar el benchmark (queda pendiente de registro)
autoresearch run -c "./benchmark.sh"

# 3. Registrar el resultado
autoresearch log -d "baseline"

# 4. Cambiar algo, repetir y registrar
autoresearch run -c "./benchmark.sh"
autoresearch log -d "añadida capa de caché"

# 5. Descartar una idea mala y aprender de ella
autoresearch run -c "./benchmark.sh"
autoresearch log -d "thread pool" -s discard -i "probar I/O asíncrona"

# 6. Consultar estado
autoresearch status           # humano
autoresearch status --json    # máquina (agentes)

# 7. Ver el backlog de ideas (con deduplicación automática)
autoresearch ideas

# 8. Regenerar el informe de sesión en Markdown
autoresearch report           # escribe autoresearch.md

# 9. Exportar todo el histórico
autoresearch export

# 10. Reiniciar el experimento
autoresearch reset --force
```

## Salida del benchmark

El comando debe imprimir al menos una línea con la métrica principal:

```bash
#!/bin/bash
set -euo pipefail
result=$(./mi_benchmark)
echo "METRIC latency_ms=$result"
echo "METRIC throughput_qps=$(echo "10000 / $result" | bc)"
```

Formato aceptado: `METRIC nombre=valor` con enteros, decimales, notación
científica, negativos y µ unicode. Cualquier otra línea se ignora.

## API Python

```python
from autoresearch import AutoResearch

ar = AutoResearch(name="optimizar-latencia", metric="latency_ms",
                  direction="lower", unit="ms")
ar.init()

result = ar.run("./benchmark.sh")     # ejecuta y captura métricas
print(result.passed, result.duration_seconds)
ar.log("baseline")                    # registra (default: keep si pasó)

result = ar.run("./benchmark.sh")
if result.passed:
    ar.log("con caché")
else:
    ar.log("falló", status="crash")

ar.discard_with_idea("thread pool", "probar I/O asíncrona")  # descarta + idea

print(ar.confidence, ar.best_metric, ar.baseline_metric)
print(ar.generate_report())           # Markdown del experimento
```

Notas importantes:

- `log()` admite `status` con o sin `description`; el estado explícito siempre
  tiene prioridad (desde v1.2.0).
- El estado se reconstruye desde `autoresearch.results.jsonl` al instanciar;
  la config del fichero prevalece sobre los argumentos del constructor.
- Un run ejecutado y no registrado queda en `.autoresearch.pending.json` y
  sobrevive entre comandos; el siguiente `run` exige resolverlo con `log`.

## Interpretación de la confianza

| Confianza | Lectura |
|-----------|---------|
| ≥ 2.0x | Mejora probablemente real |
| 1.0–2.0x | Por encima del ruido pero marginal |
| < 1.0x | Dentro del ruido, repetir para confirmar |
| n/a | Menos de 3 runs con métrica o ruido cero |

## Ficheros generados

| Fichero | Contenido |
|---------|-----------|
| `autoresearch.results.jsonl` | Fuente de verdad: config + runs |
| `autoresearch.ideas.md` | Backlog de ideas (sin duplicados) |
| `autoresearch.checkpoint.json` | Resumen del estado (informativo) |
| `autoresearch.md` | Informe de sesión (comando `report`) |
| `.autoresearch.pending.json` | Run pendiente de registrar |

## Resolución de problemas

- **"Not initialized"** → falta `autoresearch init` (o el JSONL está en otro cwd;
  usa `--cwd`).
- **"Pending run exists"** → registra el run pendiente con `log` antes de otro `run`.
- **Un run que pasa queda con métrica 0** → el benchmark no emitió
  `METRIC nombre=valor`; revisa el nombre exacto (debe coincidir con `--metric`).
