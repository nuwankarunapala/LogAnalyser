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

## Optional: ChatGPT-assisted root cause
You can optionally ask the agent to use ChatGPT to refine the root-cause statement and planned corrective actions.

1. Export your API key:

```bash
export OPENAI_API_KEY="<your_api_key>"
```

2. Run with ChatGPT enabled:

```bash
python -m agent.main --use-chatgpt --chatgpt-model gpt-4.1-mini
```

If ChatGPT is unavailable (missing key/network/API error), the agent automatically falls back to the built-in rule-based RCA output.

