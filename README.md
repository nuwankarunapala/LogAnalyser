# IFS Middleware Log RCA Agent (Scaffold)

This repository contains the initial file structure for **Option A** Python-based RCA agent.

## Structure
- `agent/collector`: Kubernetes logs/events/object collectors
- `agent/detect`: Rule engine + YAML rule catalog
- `agent/correlate`: Timeline and root-cause ranking logic
- `agent/report`: Markdown/Jinja report rendering
- `agent/main.py`: CLI entry point scaffold

## Quick check
```bash
python -m compileall agent
python -m agent.main
```

## Run full local analysis
1. Copy exported logs into `input_logs/` (`.log`, `.txt`, `.jsonl`).
2. Run:

```bash
python agent/main.py --log-dir input_logs --output-dir output
```

3. Open generated report:

```bash
cat output/rca_report.md
```
