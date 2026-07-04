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
