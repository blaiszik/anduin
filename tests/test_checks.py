from pathlib import Path

from cifdoctor.checks import parse_health, occupancy

FIXTURES = Path(__file__).parent / "fixtures"


def _severities(findings, check_name=None):
    if check_name:
        findings = [f for f in findings if f.check_name == check_name]
    return [f.severity for f in findings]


def test_parse_health_clean_file_has_no_errors():
    findings = parse_health.run(FIXTURES / "clean.cif")
    assert "error" not in _severities(findings)


def test_parse_health_flags_broken_loop():
    findings = parse_health.run(FIXTURES / "broken_loop.cif")
    assert "error" in _severities(findings)


def test_occupancy_clean_file_has_no_findings():
    findings = occupancy.run(FIXTURES / "clean.cif")
    assert findings == []


def test_occupancy_flags_overfilled_site():
    findings = occupancy.run(FIXTURES / "bad_occupancy.cif")
    assert "error" in _severities(findings)
    assert any("1.5" in f.message or ">" in f.message for f in findings if f.severity == "error")


def test_occupancy_flags_partial_site_as_info():
    findings = occupancy.run(FIXTURES / "partial_occupancy.cif")
    severities = _severities(findings)
    assert "error" not in severities
    assert "info" in severities
