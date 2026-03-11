# Log Analyser - IFS Kubernetes Outage RCA Agent

This project analyzes an exported IFS Kubernetes dump and produces a professional RCA package:

- `incident_rca.md`
- `incident_rca.json`
- `timeline.txt`

It is designed to be reliable on incomplete dumps, stream log files line-by-line, and optionally use OpenAI **only after** local evidence extraction.

## What was broken before

The previous scaffold had several reliability gaps:

1. CLI did not match required interface (`--log-dir` instead of `--dump-folder`/`--outage-start`).
2. No robust dump structure discovery for `pods/logs`, `pods/descriptions`, ingress, autoscaler, deployments, jobs.
3. Timeline sorter expected timestamps that were never parsed from lines.
4. Rule catalog was too small and not IFS/Kubernetes focused.
5. No windowed outage analysis around incident time.
6. Weak root-cause scoring/correlation across components.
7. Report output format did not match required RCA structure and file names.
8. OpenAI prompt could include raw event payloads without strong condensation discipline.

- Legacy collector metadata parsing (`agent/collector/local_logs.py`) now lazily imports PyYAML and skips metadata instead of crashing when PyYAML is absent.

## Refactored design

- `log_analyser.py`: required CLI entry point.
- `agent/file_discovery.py`: recursively discovers and categorizes files from expected dump structure.
- `agent/parsers.py`: streaming parser, timestamp extraction, severity detection, pattern matching, outage window filtering.
- `agent/detect/ifs_k8s_patterns.json`: IFS/Kubernetes-focused local knowledge base.
- `agent/root_cause_engine.py`: category scoring with confidence and evidence selection.
- `agent/timeline_builder.py`: event timeline + top error summaries.
- `agent/openai_assistant.py`: optional OpenAI refinement using condensed evidence only.
- `agent/rca_writer.py`: writes `incident_rca.md`, `incident_rca.json`, `timeline.txt`.
- `tests/`: basic tests for discovery, timestamp/pattern parsing, root-cause scoring.

## CLI usage

```bash
python log_analyser.py \
  --dump-folder ./dump-folder \
  --outage-start "2026-03-01 10:15:00" \
  --window-minutes 15 \
  --output-dir ./output
```

Optional OpenAI refinement:

```bash
export OPENAI_API_KEY="<your_key>"
python log_analyser.py \
  --dump-folder ./dump-folder \
  --outage-start "2026-03-01 10:15:00" \
  --use-openai \
  --openai-model gpt-4.1-mini
```

## Arguments

- `--dump-folder` (required)
- `--outage-start` (required, format `YYYY-MM-DD HH:MM:SS`)
- `--window-minutes` (default `15`)
- `--use-openai` (flag)
- `--openai-model` (default `gpt-4.1-mini`)
- `--output-dir` (default `output`)
- `--debug` (optional verbose logs)

## OpenAI usage safety

The agent does local analysis first and only sends condensed structured evidence:

- outage time
- suspected components
- timeline slice
- top errors
- selected evidence snippets
- local hypothesis and confidence
- missing information questions

Raw full log streams are **not** sent.

## Example RCA markdown snippet

```markdown
## 5. Root Cause
Most likely root cause: Database failure based on correlated event frequency/severity across components.

## Additional information required
- Was there a deployment during the outage window?
- Was database slowness or listener outage reported?
```

## Dependency note

Core execution now works without `PyYAML` because the default pattern library is JSON.
If the configured pattern file is missing, the tool falls back to a built-in IFS/K8s pattern set so startup still succeeds.
If you explicitly use a YAML pattern file, install dependencies first:

```bash
pip install -r requirements.txt
```

## Run tests

```bash
pytest -q
```

## Notes / assumptions

- Missing folders are handled gracefully; only existing files are parsed.
- Outage duration/SLA impact are marked unknown unless inferable from data.
- For very large dumps, parser reads line-by-line to reduce memory pressure, though normalized event objects are still retained for correlation.
