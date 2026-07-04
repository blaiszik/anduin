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
    return max(SEVERITY_CODE.get(f.severity.lower(), 0) for f in findings)

def emit_text(findings: List[Finding], fixed_files: List[str] = None) -> None:
    fixed_files = fixed_files or []
    
    by_file = {}
    for f in findings:
        by_file.setdefault(str(f.file_path), []).append(f)
        
    for path, fnds in by_file.items():
        print(f"File: {path}")
        for sev in ["error", "warning", "info"]:
            sev_fnds = [f for f in fnds if f.severity.lower() == sev]
            if sev_fnds:
                print(f"  {sev.upper()}S:")
                for f in sev_fnds:
                    print(f"    - {f.check_name}: {f.message}")
        print()
        
    if fixed_files:
        print("FIXES APPLIED:")
        for p in fixed_files:
            print(f"  - {p} (loss-free normalizations applied)")
        print()
        
    errs = sum(1 for f in findings if f.severity.lower() == "error")
    warns = sum(1 for f in findings if f.severity.lower() == "warning")
    infos = sum(1 for f in findings if f.severity.lower() == "info")
    print(f"SUMMARY: {len(findings)} findings ({errs} errors, {warns} warnings, {infos} infos) across {len(by_file)} files.")

def emit_json(findings: List[Finding], fixed_files: List[str] = None) -> None:
    fixed_files = fixed_files or []
    data = {
        "findings": [
            {
                "file_path": str(f.file_path),
                "check_name": f.check_name,
                "severity": f.severity.lower(),
                "message": f.message
            }
            for f in findings
        ],
        "fixed_files": fixed_files,
        "summary": {
            "errors": sum(1 for f in findings if f.severity.lower() == "error"),
            "warnings": sum(1 for f in findings if f.severity.lower() == "warning"),
            "infos": sum(1 for f in findings if f.severity.lower() == "info"),
            "total_files_with_findings": len(set(str(f.file_path) for f in findings))
        }
    }
    print(json.dumps(data, indent=2))
