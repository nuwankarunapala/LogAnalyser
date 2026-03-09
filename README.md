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
1. Install dependencies once:

```bash
pip install -r requirements.txt
```

2. Copy exported logs into `input_logs/` (`.log`, `.txt`, `.jsonl`).

3. Run the agent:

```bash
python -m agent.main
```

4. Open generated report:

```bash
cat output/rca_report.md
```

### Windows PowerShell equivalents
```powershell
python -m agent.main
Get-Content .\output\rca_report.md
```

### Troubleshooting
- If no report appears, first check the command output for the `Report written :` absolute path and open that exact file.
- If the command fails with `ModuleNotFoundError`/`ImportError`, run `pip install -r requirements.txt` and re-run.

- If report timeline is gibberish (`ï¿½` characters), your `.log` may be compressed/binary; export plain text logs or decompress first.
