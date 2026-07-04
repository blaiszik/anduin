import json
import os
import tempfile
from pathlib import Path

from click.testing import CliRunner
from cifdoctor.cli import main

FIXTURES = Path(__file__).parent / "fixtures"

def test_empty_dir():
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as temp_dir:
        result = runner.invoke(main, [temp_dir, '--format', 'text'])
        assert result.exit_code == 0
        assert "SUMMARY: 0 findings" in result.output


def test_fixtures_dir_exits_nonzero_and_flags_broken_files():
    runner = CliRunner()
    result = runner.invoke(main, [str(FIXTURES), '--format', 'json'])
    assert result.exit_code != 0
    assert "broken_loop.cif" in result.output
    assert "bad_occupancy.cif" in result.output


def test_fix_reports_failure_instead_of_silently_skipping(tmp_path):
    # broken_loop.cif fails to parse at all, so the --fix rewrite must also
    # fail; that failure should surface as a WARNING on stderr, not vanish.
    broken = tmp_path / "broken_loop.cif"
    broken.write_text((FIXTURES / "broken_loop.cif").read_text())

    runner = CliRunner()
    result = runner.invoke(main, [str(broken), '--fix', '--format', 'json'])

    assert "WARNING: --fix failed for" in result.stderr
    data = json.loads(result.stdout)
    assert data["fixed_files"] == []
