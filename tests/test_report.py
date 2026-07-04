import json
import pytest
from cifdoctor.checks import Finding
from cifdoctor.report import get_exit_code, emit_text, emit_json

def test_get_exit_code():
    assert get_exit_code([]) == 0
    assert get_exit_code([Finding(severity="info", message="m", file_path="f", check_name="c")]) == 0
    assert get_exit_code([Finding(severity="warning", message="m", file_path="f", check_name="c")]) == 1
    assert get_exit_code([
        Finding(severity="info", message="m", file_path="f", check_name="c"),
        Finding(severity="error", message="m", file_path="f", check_name="c")
    ]) == 2

def test_emit_text(capsys):
    findings = [
        Finding(severity="error", message="err msg", file_path="f1.cif", check_name="c1"),
        Finding(severity="warning", message="warn msg", file_path="f1.cif", check_name="c2"),
    ]
    emit_text(findings, fixed_files=["f1.cif"])
    captured = capsys.readouterr().out
    assert "File: f1.cif" in captured
    assert "ERRORS:" in captured
    assert "c1: err msg" in captured
    assert "WARNINGS:" in captured
    assert "c2: warn msg" in captured
    assert "FIXES APPLIED:" in captured
    assert "f1.cif (loss-free normalizations applied)" in captured
    assert "SUMMARY: 2 findings (1 errors, 1 warnings, 0 infos) across 1 files." in captured

def test_emit_json(capsys):
    findings = [
        Finding(severity="error", message="err msg", file_path="f1.cif", check_name="c1")
    ]
    emit_json(findings, fixed_files=["f1.cif"])
    captured = capsys.readouterr().out
    data = json.loads(captured)
    assert len(data["findings"]) == 1
    assert data["findings"][0]["severity"] == "error"
    assert data["findings"][0]["file_path"] == "f1.cif"
    assert data["fixed_files"] == ["f1.cif"]
    assert data["summary"]["errors"] == 1
    assert data["summary"]["total_files_with_findings"] == 1
