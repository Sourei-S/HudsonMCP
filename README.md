# hudson-mcp

<details open>
<summary>🇯🇵 日本語</summary>

Claude Code のエージェントが異常検知後に「守るべき価値」へ判断軸を切り替えるための事後判断 MCP サーバ。

テスト失敗・ビルド失敗・秘密情報アクセス・スコープ逸脱・API 破壊の可能性が生じたとき、
`stop` / `rollback` / `pause_and_ask` などの Recovery Decision を算出する。

## 理念

2009年、USエアウェイズ1549便はバードストライクで両エンジンを失った。
機長のサレンバーガーは「空港に戻れるか」を即座に評価し、戻れないと判断した瞬間にハドソン川への着水を決断。
乗客・乗員155名全員が生還した。

これが**ハドソン川の奇跡**。

Hudson MCP はこの判断プロセスを模倣する:

1. **異常検知** — 両エンジン停止 ＝ テスト失敗・秘密情報アクセスなど
2. **即時評価** — 「通常作業を続けられるか」を状況から算出（`hudson_assess_incident`）
3. **価値への回帰** — 手順書ではなく「守るべき価値の優先順位」に従って判断（`hudson_recommend_recovery`）
4. **決断** — `stop` / `rollback` / `pause_and_ask` — 安全な着水地点を選ぶ

サレンバーガーが最初に考えたのは「乗客を守ること」だった。
Hudson が最初に参照するのも `dev-value-hierarchy.yaml` — 守るべき価値の階層。

> 奇跡は起きないほうがいい。しかし起きたとき、確実に機能しなければならない。

## Hudson とは

Claude Code エージェントが異常を起こした**後**に動く事後リカバリーエンジン。
hook ハーネス（`beforeToolUse` / `afterToolUse` など）が防ぎきれなかった不具合が発生したときのみ呼ばれる。

### ハーネス（hook）との違い

| | ハーネス（hook） | Hudson MCP |
|---|---|---|
| タイミング | ツール呼び出しの前後 | 異常検知後 |
| 目的 | 不具合の予防 | 発生済み不具合の評価・回収 |
| 理想状態 | 常に稼働 | **一度も発動しない** |

### 極論：発動しないほうがいい

Hudson が動くということは、ハーネスをすり抜けた不具合が起きたということ。
Hudson のアラートが増えるほど、ハーネスの穴が多いことを示す。

**理想のワークフロー**:

1. hook ハーネスが事前に不審な操作をブロック
2. Hudson は何もしない → ゼロ発動

Hudson が発動したら、そのインシデント種別に対応する hook ルールを追加して再発防止。
Hudson は検知するためではなく、ハーネスを育てるためのフィードバックループ。

## インストール

### PyPI から（公開後）

```bash
claude mcp add hudson -- uvx hudson-mcp
```

### ローカルリポジトリから（git clone 後）

Windows / macOS / Linux 共通:

```bash
cd /path/to/HudsonMCP
uv tool install --editable .
claude mcp add hudson -s user -- hudson-mcp
```

## カスタマイズ（プロジェクト固有の YAML を使う場合）

プロジェクトに `hudson/` ディレクトリを作成し、上書きしたいファイルだけ置く。
置かなかったファイルはパッケージ同梱のデフォルトを使用。

```bash
# PyPI から
claude mcp add hudson -- uvx hudson-mcp --config ./hudson/

# ローカルインストール済みの場合
claude mcp add hudson -s user -- hudson-mcp --config ./hudson/
```

カスタマイズ可能なファイル（いずれも省略可）:

| ファイル名 | 内容 |
|---|---|
| `dev-value-hierarchy.yaml` | 守るべき価値の優先順位（13項目） |
| `dev-rule-map.yaml` | インシデント種別とルールの対応 |
| `dev-purpose-map.yaml` | 目的と価値の対応 |
| `recovery-decision-policy.yaml` | stop / rollback 等の判定条件 |
| `severity-policy.yaml` | インシデント種別ごとのデフォルト severity |
| `secret-policy.yaml` | 監視対象ファイル・秘密値パターン |
| `package-risk-policy.yaml` | 危険パッケージ判定ルール |
| `scope-policy.yaml` | 大規模変更の閾値 |
| `feedback-policy.yaml` | 再発防止候補の生成ルール |

## CLAUDE.md への追記テンプレート

プロジェクトの `CLAUDE.md` にコピーして使う:

```markdown
## Hudson MCP（リカバリーツール）

テスト失敗・ビルド失敗・秘密情報アクセス・スコープ逸脱・API 破壊の可能性がある変更が
起きたら即座に以下のパイプラインを実行する:

1. `hudson_analyze_*`（該当する検知ツールを呼ぶ）
2. `hudson_assess_incident`
3. `hudson_recommend_recovery`

`stop` / `rollback` の Decision が出たら通常作業を中断し、ユーザーに報告する。
```

## ツール一覧（17 ツール）

| ツール名 | 説明 |
|---|---|
| `hudson_get_status` | インシデント群から状況評価し triggered を返す |
| `hudson_scan_diff` | git 差分（cwd or diff_numstat）を要約 |
| `hudson_scan_test_result` | テスト出力から test_regression を検知 |
| `hudson_scan_build_result` | ビルド出力から build/typecheck failure を検知 |
| `hudson_analyze_scope_expansion` | 意図/実変更ファイル集合を事後分析し範囲逸脱を報告 |
| `hudson_analyze_secret_access` | 読取済みファイルパスを事後分析し secret_access を報告 |
| `hudson_analyze_secret_exposure` | 出力済みテキストを事後分析し秘密値露出を報告 |
| `hudson_analyze_secret_propagation` | 既読秘密の後続テキストへの伝播を事後分析 |
| `hudson_analyze_dangerous_package` | インストールログ・lockfile 差分を事後分析し危険依存を報告 |
| `hudson_analyze_repeated_failure` | 蓄積エラー署名を事後分析し同一エラー反復を報告 |
| `hudson_analyze_api_break` | 変更後シンボル集合を事後分析し公開 API 破壊を報告 |
| `hudson_assess_incident` | インシデント群を統合し SituationAssessment を返す |
| `hudson_recover_purpose` | Purpose Recovery Questions を構造化回答で算出 |
| `hudson_recommend_recovery` | 状況×価値から Recovery Decision を算出 |
| `hudson_generate_feedback` | インシデント種別から再発防止候補を生成 |
| `hudson_build_report` | Hudson Report（Markdown）を生成 |
| `hudson_write_log` | JSONL ログへ追記 |

## ライセンス

MIT

</details>

<details>
<summary>🇺🇸 English</summary>

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

### From PyPI (after publishing)

```bash
claude mcp add hudson -- uvx hudson-mcp
```

### From local repository (after git clone)

Windows / macOS / Linux:

```bash
cd /path/to/HudsonMCP
uv tool install --editable .
claude mcp add hudson -s user -- hudson-mcp
```

## Customization (using project-specific YAML)

Create a `hudson/` directory in your project and place only the files you want to override.
Files not placed there will use the package's built-in defaults.

```bash
# From PyPI
claude mcp add hudson -- uvx hudson-mcp --config ./hudson/

# From local install
claude mcp add hudson -s user -- hudson-mcp --config ./hudson/
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

</details>
