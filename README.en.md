# hudson-mcp

[日本語](./README.md) | **English**

A post-hoc decision MCP server that helps Claude Code agents switch their judgment axis to "values to protect" after anomaly detection.

When a test failure, build failure, secret access, scope deviation, or potential API break occurs, it computes a Recovery Decision: `stop` / `rollback` / `pause_and_ask`, etc.

## Philosophy

In 2009, US Airways Flight 1549 lost both engines to a bird strike.
Captain Sullenberger instantly assessed whether a return to any airport was possible, concluded it wasn't, and in that same moment decided to ditch in the Hudson River.
All 155 passengers and crew survived.

This is the **Miracle on the Hudson**.

Hudson MCP models that decision process:

1. **Anomaly detected** — both engines out = test failure, secret access, etc.
2. **Immediate assessment** — compute whether normal work can continue from the situation (`hudson_assess_incident`)
3. **Return to values** — judge not by runbook, but by the priority order of "values to protect" (`hudson_recommend_recovery`)
4. **Decision** — `stop` / `rollback` / `pause_and_ask` — choose the safest landing spot

Sullenberger's first thought was to protect the passengers.
Hudson's first reference is `dev-value-hierarchy.yaml` — the hierarchy of values to protect.

> The miracle is better left unhappened. But when it does happen, it must work without fail.

## What is Hudson?

A post-hoc recovery engine that activates **after** a Claude Code agent has gone wrong.
It is called only when the hook harness (`beforeToolUse` / `afterToolUse`, etc.) fails to prevent a problem.

### Harness (hook) vs. Hudson MCP

| | Harness (hook) | Hudson MCP |
|---|---|---|
| Timing | Before/after tool calls | After anomaly detected |
| Purpose | Prevent problems | Evaluate and recover from problems that already happened |
| Ideal state | Always running | **Never fires** |

### The blunt truth: Hudson firing is a bad sign

When Hudson activates, it means a problem slipped past the harness.
The more Hudson alerts fire, the more gaps exist in the harness.

**Ideal workflow**:

1. The hook harness blocks suspicious operations upfront
2. Hudson does nothing → zero activations

When Hudson does fire, add a hook rule for that incident type to prevent recurrence.
Hudson exists not to detect problems, but as a feedback loop to strengthen the harness.

## Installation

```bash
claude mcp add hudson -- uvx hudson-mcp
```

## Customization (using project-specific YAML)

Create a `hudson/` directory in your project and place only the files you want to override.
Files not placed there will use the package's built-in defaults.

```bash
claude mcp add hudson -- uvx hudson-mcp --config ./hudson/
```

Customizable files (all optional):

| File | Description |
|---|---|
| `dev-value-hierarchy.yaml` | Priority order of values to protect (13 items) |
| `dev-rule-map.yaml` | Mapping of incident types to rules |
| `dev-purpose-map.yaml` | Mapping of purposes to values |
| `recovery-decision-policy.yaml` | Conditions for stop / rollback decisions |
| `severity-policy.yaml` | Default severity per incident type |
| `secret-policy.yaml` | Monitored files and secret value patterns |
| `package-risk-policy.yaml` | Rules for detecting dangerous packages |
| `scope-policy.yaml` | Thresholds for large-scale changes |
| `feedback-policy.yaml` | Rules for generating recurrence-prevention candidates |

## CLAUDE.md Template

Copy this into your project's `CLAUDE.md`:

```markdown
## Hudson MCP (Recovery Tool)

When a test failure, build failure, secret access, scope deviation, or potential API break occurs,
immediately run the following pipeline:

1. `hudson_analyze_*` (call the relevant detection tool)
2. `hudson_assess_incident`
3. `hudson_recommend_recovery`

If the Decision is `stop` or `rollback`, suspend normal work and report to the user.
```

## Tool List (17 tools)

| Tool | Description |
|---|---|
| `hudson_get_status` | Evaluates a set of incidents and returns triggered status |
| `hudson_scan_diff` | Summarizes git diff (cwd or diff_numstat) |
| `hudson_scan_test_result` | Detects test_regression from test output |
| `hudson_scan_build_result` | Detects build/typecheck failures from build output |
| `hudson_analyze_scope_expansion` | Post-hoc analysis of intended vs. actual changed files; reports scope deviation |
| `hudson_analyze_secret_access` | Post-hoc analysis of read file paths; reports secret_access |
| `hudson_analyze_secret_exposure` | Post-hoc analysis of output text; reports secret value exposure |
| `hudson_analyze_secret_propagation` | Post-hoc analysis of propagation of read secrets into subsequent text |
| `hudson_analyze_dangerous_package` | Post-hoc analysis of install logs / lockfile diffs; reports dangerous dependencies |
| `hudson_analyze_repeated_failure` | Post-hoc analysis of accumulated error signatures; reports repeated identical errors |
| `hudson_analyze_api_break` | Post-hoc analysis of changed symbol sets; reports public API breakage |
| `hudson_assess_incident` | Integrates incident set and returns SituationAssessment |
| `hudson_recover_purpose` | Computes Purpose Recovery Questions as structured answers |
| `hudson_recommend_recovery` | Computes Recovery Decision from situation × values |
| `hudson_generate_feedback` | Generates recurrence-prevention candidates from incident types |
| `hudson_build_report` | Generates Hudson Report (Markdown) |
| `hudson_write_log` | Appends to JSONL log |

## License

MIT
