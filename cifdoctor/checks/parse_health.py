"""Parse-health check: does the CIF parse at all?

Runs the file through pymatgen's CifParser and reports an error finding for
any file that fails to parse (malformed loops, missing required tags,
truncated data) or that parses with zero structures. Parser-level warnings
(e.g. missing symmetry keys) are reported as INFO so a clean-but-terse file
doesn't fail the whole run.
"""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import List

from cifdoctor.checks import Finding

NAME = "parse_health"


def _line_hint(path: Path, needle: str | None = None) -> str | None:
    """Best-effort line number for an error mentioning a tag/label."""
    if not needle:
        return None
    try:
        text = path.read_text(errors="replace")
    except OSError:
        return None
    for i, line in enumerate(text.splitlines(), start=1):
        if needle in line:
            return f"line {i}"
    return None


def run(path: Path) -> List[Finding]:
    """Check that ``path`` parses as a CIF file.

    Returns a list with a single ERROR Finding if parsing fails outright,
    or INFO findings for any parser warnings surfaced along the way.
    """
    findings: List[Finding] = []

    try:
        from pymatgen.io.cif import CifParser
    except ImportError as exc:  # pragma: no cover - environment issue
        return [
            Finding(
                severity="error",
                message=f"pymatgen unavailable: {exc}",
                file_path=str(path),
                check_name=NAME,
            )
        ]

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            parser = CifParser(str(path))
            structures = parser.parse_structures(primitive=False, on_error="warn")
        except Exception as exc:  # noqa: BLE001 - pymatgen raises many types here
            hint = _line_hint(path, "loop_")
            location = f" ({hint})" if hint else ""
            findings.append(
                Finding(
                    severity="error",
                    message=f"failed to parse{location}: {exc}",
                    file_path=str(path),
                    check_name=NAME,
                )
            )
            return findings

        if not structures:
            findings.append(
                Finding(
                    severity="error",
                    message="parsed with zero structures",
                    file_path=str(path),
                    check_name=NAME,
                )
            )

        for warning in caught:
            findings.append(
                Finding(
                    severity="info",
                    message=str(warning.message),
                    file_path=str(path),
                    check_name=NAME,
                )
            )

    return findings
