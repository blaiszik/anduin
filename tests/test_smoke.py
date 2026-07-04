import os
import tempfile
from click.testing import CliRunner
from cifdoctor.cli import main

def test_empty_dir():
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as temp_dir:
        result = runner.invoke(main, [temp_dir, '--format', 'text'])
        assert result.exit_code == 0
        assert result.output == ""
