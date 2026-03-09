# IFS Middleware Log RCA Agent

This repository contains an **Option A** Python-based RCA agent that analyzes IFS middleware logs and generates a Markdown RCA report.

## 1) Prerequisites
- Python 3.10+
- (Optional but recommended) install dependencies:

```bash
pip install -r requirements.txt
```

> If `PyYAML` is not installed, the agent still runs using built-in fallback rules.

---

## 2) Where to place logs
Put exported logs into `input_logs/` (or any folder you choose).

Supported file extensions:
- `.log`
- `.txt`
- `.jsonl`

Example files:
- `input_logs/ifsodata-main.log`
- `input_logs/ifsiam-main.log`
- `input_logs/ifsodata-sidecar.log`

Container role detection is filename-based:
- filenames containing `sidecar` -> treated as `sidecar`
- all others -> treated as `main`

---

## 3) Run the agent
Basic usage:

```bash
python agent/main.py --log-dir input_logs --output output/rca_report.md
```

Use custom rules file:

```bash
python agent/main.py \
  --log-dir /path/to/logs \
  --rules agent/detect/rules.yaml \
  --output output/rca_report.md
```

CLI options:
- `--log-dir` (required): folder containing logs
- `--rules` (optional): YAML rule file path (default: `agent/detect/rules.yaml`)
- `--output` (optional): output markdown report path (default: `output/rca_report.md`)

---

## 4) What the agent generates
The report includes:
- **Summary** of processed events and matched categories
- **Findings** with severity, rule id, evidence line, and RCA hint
- **Recommended Actions** aggregated from matched rules
- **Missing Information Required From User** when evidence is not enough

This last section tells exactly what additional context is needed (for example memory limits, PVC/PV details, IAM realm/client error context, or incident time window).

---

## 5) Quick validation
Run a quick compile and execution check:

```bash
python -m compileall agent
python agent/main.py --log-dir input_logs --output output/rca_report.md
```

Then inspect:

```bash
cat output/rca_report.md
```

---

## 6) Project structure
- `agent/collector`: local and future Kubernetes collectors
- `agent/detect`: rule engine + YAML rule catalog
- `agent/correlate`: correlation utilities (timeline/root-cause scaffolds)
- `agent/report`: RCA markdown rendering
- `input_logs/`: place user logs here
- `output/`: generated reports
