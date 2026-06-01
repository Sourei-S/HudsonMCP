# src/hudson_mcp/tools/__init__.py
from hudson_mcp.tools import definitions as d

def _obj(props: dict, required: list[str] | None = None) -> dict:
    return {"type": "object", "properties": props, "required": required or []}

_CONTEXT = {
    "type": "object",
    "properties": {
        "diff_text":          {"type": "string"},
        "before_symbols":     {"type": "array", "items": {"type": "string"}},
        "after_symbols":      {"type": "array", "items": {"type": "string"}},
        "changed_signatures": {"type": "array", "items": {"type": "object"}},
        "blame_info":         {"type": "object"},
        "revertable":         {"type": "boolean"},
        "recent_change":      {"type": "boolean"},
    },
}

TOOLS: dict[str, dict] = {
    "hudson.get_status": {
        "fn": d.get_status, "description": "incident 群から状況評価し triggered を返す",
        "schema": _obj({"incidents": {"type": "array", "items": {"type": "object"}}}),
    },
    "hudson.scan_diff": {
        "fn": d.scan_diff, "description": "git 差分（cwd or diff_numstat）を要約する",
        "schema": _obj({"cwd": {"type": "string"}, "diff_numstat": {"type": "string"}}),
    },
    "hudson.scan_test_result": {
        "fn": d.scan_test_result, "description": "テスト出力から test_regression を検知",
        "schema": _obj({"output": {"type": "string"}, "recent_change": {"type": "boolean"},
                        "revertable": {"type": "boolean"}}, ["output"]),
    },
    "hudson.scan_build_result": {
        "fn": d.scan_build_result, "description": "ビルド出力から build/typecheck failure を検知",
        "schema": _obj({"output": {"type": "string"}, "recent_change": {"type": "boolean"},
                        "revertable": {"type": "boolean"}}, ["output"]),
    },
    "hudson.analyze_scope_expansion": {
        "fn": d.analyze_scope_expansion, "description": "意図/実変更ファイル集合を事後分析し範囲逸脱を報告",
        "schema": _obj({"intended": {"type": "array", "items": {"type": "string"}},
                        "changed": {"type": "array", "items": {"type": "string"}},
                        "changed_lines": {"type": "integer"},
                        "context": _CONTEXT}),
    },
    "hudson.analyze_secret_access": {
        "fn": d.analyze_secret_access, "description": "読取済みファイルパスを事後分析し secret_access を報告",
        "schema": _obj({"read_paths": {"type": "array", "items": {"type": "string"}}}),
    },
    "hudson.analyze_secret_exposure": {
        "fn": d.analyze_secret_exposure, "description": "出力済みテキストを事後分析し秘密値露出を報告",
        "schema": _obj({"text": {"type": "string"}, "context": _CONTEXT}, ["text"]),
    },
    "hudson.analyze_secret_propagation": {
        "fn": d.analyze_secret_propagation, "description": "既読秘密の後続出力テキストへの伝播を事後分析し報告",
        "schema": _obj({"followup_text": {"type": "string"},
                        "secret_was_accessed": {"type": "boolean"},
                        "context": _CONTEXT}, ["followup_text"]),
    },
    "hudson.analyze_dangerous_package": {
        "fn": d.analyze_dangerous_package, "description": "インストール後ログ・lockfile差分を事後分析し危険依存を報告",
        "schema": _obj({"added_packages": {"type": "array", "items": {"type": "string"}},
                        "install_log": {"type": "string"}, "lockfile_diff": {"type": "string"}}),
    },
    "hudson.analyze_repeated_failure": {
        "fn": d.analyze_repeated_failure, "description": "蓄積されたエラー署名を事後分析し同一エラー反復を報告",
        "schema": _obj({"error_signatures": {"type": "array", "items": {"type": "string"}}}),
    },
    "hudson.assess_incident": {
        "fn": d.assess_incident, "description": "incident 群を統合し SituationAssessment を返す",
        "schema": _obj({"incidents": {"type": "array", "items": {"type": "object"}}}),
    },
    "hudson.recover_purpose": {
        "fn": d.recover_purpose, "description": "Purpose Recovery Questions を構造化回答で算出",
        "schema": _obj({"assessment": {"type": "object"},
                        "matched_rules": {"type": "array", "items": {"type": "string"}},
                        "matched_purposes": {"type": "array", "items": {"type": "string"}}}, ["assessment"]),
    },
    "hudson.recommend_recovery": {
        "fn": d.recommend_recovery, "description": "状況×価値から Recovery Decision を算出",
        "schema": _obj({"assessment": {"type": "object"},
                        "purpose_recovery": {"type": "object"}}, ["assessment"]),
    },
    "hudson.generate_feedback": {
        "fn": d.generate_feedback, "description": "incident_type から再発防止候補を生成",
        "schema": _obj({"incident_type": {"type": "string"}}, ["incident_type"]),
    },
    "hudson.write_log": {
        "fn": d.write_log, "description": "jsonl ログへ追記",
        "schema": _obj({"name": {"type": "string"}, "record": {"type": "object"}}, ["name", "record"]),
    },
    "hudson.analyze_api_break": {
        "fn": d.analyze_api_break,
        "description": "変更後のシンボル集合を事後分析し公開API破壊・署名非互換を報告",
        "schema": _obj({
            "before_symbols":     {"type": "array", "items": {"type": "string"}},
            "after_symbols":      {"type": "array", "items": {"type": "string"}},
            "changed_signatures": {"type": "array", "items": {"type": "object"}},
            "context": _CONTEXT,
        }),
    },
    "hudson.build_report": {
        "fn": d.build_report, "description": "Hudson Report(markdown)を生成（『通常作業を停止』指示を含む最終出力）",
        "schema": _obj({"assessment": {"type": "object"}, "purpose_recovery": {"type": "object"},
                        "decision": {"type": "object"}, "feedback": {"type": "object"}},
                       ["assessment", "purpose_recovery", "decision"]),
    },
}
