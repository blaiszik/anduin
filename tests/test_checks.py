from pathlib import Path

from cifdoctor.checks import parse_health, occupancy, charge, bonds, symmetry

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


def test_charge_neutral_file_has_no_warnings():
    findings = charge.run(FIXTURES / "charge_neutral.cif")
    severities = _severities(findings)
    assert "warning" not in severities
    assert "error" not in severities


def test_charge_flags_imbalanced_composition():
    findings = charge.run(FIXTURES / "charge_imbalanced.cif")
    assert "warning" in _severities(findings)
    assert any("net cell charge" in f.message for f in findings)


def test_charge_skips_with_info_when_states_absent():
    findings = charge.run(FIXTURES / "clean.cif")
    severities = _severities(findings)
    assert severities == ["info"]
    assert "skipping" in findings[0].message


def test_bonds_clean_file_has_no_findings():
    findings = bonds.run(FIXTURES / "clean.cif")
    assert findings == []


def test_bonds_flags_impossible_contact_as_error():
    findings = bonds.run(FIXTURES / "close_contact.cif")
    assert "error" in _severities(findings)
    assert any("impossible contact" in f.message for f in findings if f.severity == "error")


def test_bonds_flags_short_contact_as_warning():
    findings = bonds.run(FIXTURES / "short_contact.cif")
    severities = _severities(findings)
    assert "error" not in severities
    assert "warning" in severities


def test_symmetry_consistent_file_has_no_findings():
    # clean.cif declares P 1 with a single 'x, y, z' op and no IT number:
    # nothing contradicts, so the check is silent.
    findings = symmetry.run(FIXTURES / "clean.cif")
    assert _severities(findings, "symmetry") == []


def test_symmetry_flags_symbol_number_mismatch_as_error():
    findings = symmetry.run(FIXTURES / "sym_mismatch_number.cif")
    sym = [f for f in findings if f.check_name == "symmetry"]
    assert "error" in [f.severity for f in sym]
    assert any("No." in f.message for f in sym if f.severity == "error")


def test_symmetry_flags_unrecognized_symbol_as_warning():
    findings = symmetry.run(FIXTURES / "sym_bad_symbol.cif")
    sym = [f for f in findings if f.check_name == "symmetry"]
    assert [f.severity for f in sym] == ["warning"]
    assert "unrecognized space group symbol" in sym[0].message


def test_symmetry_flags_too_many_operations_as_error():
    findings = symmetry.run(FIXTURES / "sym_too_many_ops.cif")
    sym = [f for f in findings if f.check_name == "symmetry"]
    assert "error" in [f.severity for f in sym]
    assert any("more than" in f.message for f in sym if f.severity == "error")


def test_symmetry_flags_generators_only_as_warning():
    findings = symmetry.run(FIXTURES / "sym_generators_only.cif")
    sym = [f for f in findings if f.check_name == "symmetry"]
    assert "error" not in [f.severity for f in sym]
    assert any(
        f.severity == "warning" and "generators only" in f.message for f in sym
    )
