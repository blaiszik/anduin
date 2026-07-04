import json
from typing import List, Dict, Any
from cifdoctor.checks import Finding

SEVERITY_CODE = {
    "error": 2,
    "warning": 1,
    "info": 0
}

def get_exit_code(findings: List[Finding]) -> int:
    if not findings:
        return 0
    return max(SEVERITY_CODE.get(f.severity, 0) for f in findings)

def emit_text(findings: List[Finding]) -> None:
    for f in findings:
        print(f"[{f.severity.upper()}] {f.file_path} ({f.check_name}): {f.message}")

def emit_json(findings: List[Finding]) -> None:
    data = [
        {
            "severity": f.severity,
            "message": f.message,
            "file_path": f.file_path,
            "check_name": f.check_name
        }
        for f in findings
    ]
    print(json.dumps(data, indent=2))
