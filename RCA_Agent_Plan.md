# Option A Plan: Python Agent for IFS Middleware Kubernetes Log Analysis + RCA

## 1) Scope and objective
Build a **Python-based external agent** (runs outside cluster) to analyze IFS middleware pod logs and generate an RCA report for incidents such as:
- Application errors/failures
- `OOMKilled`/memory pressure
- Storage outages (PV/PVC attach/mount/backing storage)

This design keeps your hard constraint: **no new installation inside the Kubernetes cluster**.

---

## 2) Confirmed current middleware topology (your environment)
This plan is now aligned to your provided current structure:
- **1 Kubernetes node** hosting middleware workload.
- **10–20 middleware pods**.
- **Each pod has 2 containers**:
  - Sidecar container (network/traffic support)
  - Main dedicated task container (business function)

Example components called out:
- **IFS OData pod**: handles database operations.
- **IFS IAM pod**: handles authentication with Keycloak.

Why this matters for design:
- Correlation logic must be **pod-aware and container-aware** (main vs sidecar).
- Restart/failure patterns on sidecar and main container must be treated differently in RCA confidence.

---

## 3) IFS architecture alignment (based on your supplied IFS Cloud documentation)
The plan is now aligned with the IFS Cloud Platform & Architecture material you shared.

Key architecture points from your documentation and how they affect this agent:
- IFS Cloud is cloud-native and service-oriented, with middle-tier services containerized and orchestrated by Kubernetes.
- Middle-tier includes services such as OData API back-end, Identity & Access Manager (IAM), and client services.
- Business logic/API access is REST-based and sits between presentation and database tiers.
- IAM supports OpenID Connect scenarios and may integrate with providers like Azure AD.
- Deployments in IFS Cloud Service use Azure DevOps pipelines + Helm, with monitoring stack already present.

Operational implications for RCA agent:
- Prioritize middle-tier pod/container evidence because this is where OData/IAM runtime failures occur.
- Keep authentication outage rules explicit (IAM/Keycloak/OpenID Connect token and realm failures).
- Correlate API-level failures (timeouts/5xx/auth) against Kubernetes events and restart patterns.
- Keep the agent external and read-only, so it does not conflict with IFS-managed deployment and security controls.

Note on direct internet access from this environment:
- Public IFS domains were previously blocked from this runtime (`403` via proxy), but your supplied official documentation is now used as the authoritative architecture reference for this plan.

---

## 4) Recommended architecture (Option A only)

### 4.1 Runtime placement
Run agent on one of:
- Ops jump host
- CI/CD runner (Jenkins/GitLab/Azure DevOps)
- Dedicated VM

### 4.2 Data sources (read-only)
1. Kubernetes logs (pod + container level)
2. Kubernetes events
3. Pod status/restart/termination states
4. PVC/PV state for storage-related incidents

### 4.3 Processing pipeline
1. **Collector**: fetch logs/events/status in incident time-window.
2. **Normalizer**: convert to unified event schema (timestamp, source, severity, entity, raw text).
3. **Rule engine**: detect outage patterns.
4. **Correlator**: build timeline + identify probable primary failure.
5. **RCA generator**: produce markdown/JSON report.

### 4.4 Container-role-aware correlation (important)
For each pod, classify logs/events by container role:
- `sidecar` (network)
- `main` (dedicated task)

Correlation priority:
1. If main container fails first and sidecar errors follow, mark main failure as likely primary.
2. If sidecar networking fails first across multiple pods, mark network path issue as likely primary.
3. If both fail simultaneously on single node, raise node-level resource/storage suspicion.

---

## 5) Technology/tooling

## Core stack (Python)
- Python 3.11+
- `kubectl` (existing tool on runner/jump host)
- Kubernetes Python client (`kubernetes`) or subprocess wrapper over `kubectl`
- `PyYAML` for rule catalog
- `jinja2` for report templates
- `pydantic` (optional) for schema validation

## Suggested project structure
```text
agent/
  collector/
    kube_logs.py
    kube_events.py
    kube_objects.py
  detect/
    rules.yaml
    rule_engine.py
  correlate/
    timeline.py
    root_cause_ranker.py
    container_role_classifier.py
  report/
    rca_template.md.j2
    render.py
  main.py
```

---

## 6) Rule catalog (first iteration)
Store as YAML, each rule contains:
- `id`, `category`, `severity`
- `target_container_role` (`main`, `sidecar`, `any`)
- `match` (regex/field conditions)
- `evidence_required`
- `rca_hint`
- `recommended_actions`

### 6.1 OOMKilled rules
Signals:
- `containerStatuses[*].lastState.terminated.reason == OOMKilled`
- restart count increase in same window
- events containing `OOMKilling`, `Evicted`, `MemoryPressure`

RCA hint examples:
- memory limit too low
- workload spike
- leak suspicion

### 6.2 Storage outage rules
Signals:
- events with `FailedMount`, `FailedAttachVolume`, `MountVolume.SetUp failed`
- PVC not bound / delayed binding
- repeated I/O timeout errors in app logs

RCA hint examples:
- CSI/backend storage interruption
- volume attach latency
- node/storage network path issue

### 6.3 Middleware failure rules
Signals:
- OData main container: DB timeout, connection refused, transaction rollback patterns
- IAM main container: Keycloak/auth token/realm errors
- sidecar container: upstream/downstream connect timeout, TLS handshake, service mesh/network errors
- `CrashLoopBackOff`, probe failures

RCA hint examples:
- downstream dependency failure (DB/auth/message broker)
- authentication backend degradation
- misconfiguration/secret rotation issue

---

## 7) Kubernetes access model (no in-cluster install)
Use existing kubeconfig or dedicated read-only service account.

Minimum RBAC:
- pods: `get`, `list`, `watch`
- pods/log: `get`
- events: `get`, `list`, `watch`
- namespaces: `get`, `list`
- pvc/pv: `get`, `list` (for storage investigation)
- nodes: `get`, `list` (recommended for single-node pressure context)

Security:
- redact secrets/PII from reports
- store kube credentials in enterprise secret manager
- keep incident artifacts in controlled storage

---

## 8) Execution modes

### 8.1 On-demand incident mode
Input:
- namespace(s)
- time window
- optional pod label/app filter

Output:
- single RCA report for incident

### 8.2 Scheduled health scan mode
- Run every 5–15 minutes
- Detect silent failure patterns early
- Create incident draft report when threshold is exceeded

---

## 9) RCA report format (standard)
For each incident generate:
1. Incident summary
2. Impacted services/pods/containers
3. Timeline (event + log + restart chronology)
4. Evidence table (role-separated: sidecar vs main)
5. Most probable root cause + confidence
6. Contributing factors
7. Immediate mitigation
8. Permanent corrective actions
9. Alert/rule improvements

---

## 10) 4-week delivery plan

### Week 1: Discovery + signatures
- Confirm IFS middleware namespace/component inventory
- Create initial container-role map (main/sidecar per pod)
- Import known IFS log signatures from your internal docs (OData + IAM + sidecar)
- Validate RBAC/read-only access

### Week 2: Build MVP collector + rules
- Implement collectors and normalizer
- Add OOM/storage/middleware baseline rules
- Add OData and IAM targeted patterns
- Generate markdown RCA

### Week 3: Correlation + ranking
- Implement timeline builder
- Add root-cause ranking and confidence scoring
- Add sidecar/main precedence logic
- Validate against past incidents

### Week 4: Hardening + handover
- Add CI scheduler job
- Add runbook (how to run, triage, tune rules)
- Track KPIs (precision, false positives, time-to-RCA)

---

## 11) Best practice for IFS system engineering teams
1. Start rule-based; avoid ML-first complexity.
2. Maintain a versioned **IFS signature catalog** in Git.
3. Separate **primary cause** from cascading symptoms in RCA.
4. Make every RCA include corrective action owner + due date.
5. Re-tune rules monthly based on incident outcomes.
6. Review OData and IAM rule packs after every outage postmortem.

---

## 12) First commands to operationalize
Example read-only diagnostics your agent should automate:
- `kubectl get pods -n <ns> -o wide`
- `kubectl get pods -n <ns> -o json`
- `kubectl get events -n <ns> --sort-by=.lastTimestamp`
- `kubectl logs -n <ns> <pod> -c <main_container> --since=2h`
- `kubectl logs -n <ns> <pod> -c <sidecar_container> --since=2h`
- `kubectl describe pod -n <ns> <pod>`
- `kubectl get pvc,pv -n <ns>`
- `kubectl describe node <node-name>`

These commands become data collectors inside the Python workflow.


---

## 13) Immediate next steps (start this week)

### Step 1 — Day 1: Access and inventory
- Confirm kube context and namespace list for IFS middleware.
- Export current pod/container inventory (identify `main` vs `sidecar` per pod).
- Validate read-only RBAC access for logs, events, pvc/pv, and nodes.

Deliverable:
- `inventory.csv` (namespace, pod, container, role, node)
- `access-check.md` with pass/fail per required API resource

### Step 2 — Day 2–3: Build baseline rule pack
- Create `rules.yaml` with first 15–25 rules:
  - OOMKilled / memory pressure
  - storage attach/mount failures
  - OData DB operation failures
  - IAM/Keycloak authentication failures
  - sidecar network failures
- Assign severity and suggested corrective action per rule.

Deliverable:
- `rules.yaml` v0.1
- `rule-mapping.md` (rule -> RCA hint -> action owner)

### Step 3 — Day 4: Build collector MVP
- Implement collector commands for:
  - pod status JSON
  - events stream for time window
  - per-container logs (`main` and `sidecar` separately)
  - pvc/pv and node describe snapshots
- Save raw evidence in timestamped incident folders.

Deliverable:
- MVP script producing `incident_<ts>/raw/*` artifacts

### Step 4 — Day 5: First RCA output
- Add a simple correlator and markdown report generator.
- Run against one known historical incident.
- Review RCA quality with operations team (30–45 min review).

Deliverable:
- `incident_<ts>/rca_report.md`
- review notes with false positives/missed signals

### Step 5 — Week 2 kickoff
- Tune top noisy rules.
- Add confidence scoring (high/medium/low) and primary-cause ranking.
- Schedule automated runs every 10 minutes + on-demand mode.

Success criteria for “next step complete”:
- Agent can produce one RCA report from real incident data with clear timeline, probable root cause, and corrective actions.


---

## 14) IFS-specific signal matrix (from supplied architecture context)

### 14.1 OData service incident signals
Collect and correlate:
- Main-container logs: DB timeout, connection refused, transaction rollback, ORA/SQL errors
- Kubernetes events: restarts, probe failures, OOMKilled
- Sidecar logs: upstream timeout/TLS/connect reset that may mask as app errors

RCA interpretation:
- Main-container DB errors first -> likely data-tier or connection pool issue
- Sidecar network errors first across pods -> likely network/service-mesh path issue

### 14.2 IAM/Keycloak incident signals
Collect and correlate:
- IAM main-container logs: token validation failure, realm/client config error, auth provider timeout
- Events: CrashLoopBackOff, readiness probe failures
- Cross-service impact: authentication failures appearing in OData/client services shortly after IAM errors

RCA interpretation:
- IAM errors first + downstream auth failures -> IAM/auth provider is probable primary cause

### 14.3 Storage and node context (single-node emphasis)
Given single-node topology, include:
- Node pressure and eviction signals
- PVC/PV attach and mount errors
- Synchronized failures across many pods in same minute window

RCA interpretation:
- Multi-pod simultaneous failures on one node -> elevate node/storage/infrastructure suspicion

### 14.4 Security and compliance-aware reporting
Based on IFS security posture (RBAC, encryption, compliance):
- Mask tokens, credentials, and personal data in exported evidence
- Keep report access controlled (need-to-know)
- Track who generated each RCA and when (auditability)
