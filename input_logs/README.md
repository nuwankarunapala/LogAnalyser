# Place logs here

Put your exported middleware logs in this folder before running the agent.

Supported extensions:
- `.log`
- `.txt`
- `.jsonl`

Example:
- `ifsodata-main.log`
- `ifsiam-main.log`
- `ifsodata-sidecar.log`


Optional metadata file:
- `log_metadata.yaml` to map file names to friendly display names in the report.

Example `log_metadata.yaml`:
```yaml
files:
  kubectl-describe.txt:
    display_name: kubectl describe
    container_role: main
  pod-logs.txt:
    display_name: pod logs
    container_role: main
```
