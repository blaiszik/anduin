import click
from pathlib import Path
from cifdoctor.report import emit_text, emit_json, get_exit_code
from cifdoctor.checks import parse_health, occupancy

# Checks are plain modules exposing a `run(path) -> List[Finding]` function
# (see cifdoctor/checks/__init__.py for the Finding/Check protocol).
CHECKS = [parse_health, occupancy]


def _iter_cif_files(paths):
    for p in paths:
        if p.is_dir():
            yield from sorted(p.rglob("*.cif"))
        elif p.suffix == ".cif":
            yield p


@click.command()
@click.argument('paths', nargs=-1, type=click.Path(exists=True, path_type=Path))
@click.option('--format', 'fmt', type=click.Choice(['text', 'json']), default='text', help='Output format')
@click.option('--fix/--no-fix', default=False, help='Apply safe, loss-free normalizations')
def main(paths, fmt, fix):
    """cif-doctor: Batch validator and fixer for CIF files."""
    findings = []

    for cif_path in _iter_cif_files(paths):
        for check in CHECKS:
            findings.extend(check.run(cif_path))

    if fmt == 'json':
        emit_json(findings)
    else:
        emit_text(findings)

    exit_code = get_exit_code(findings)
    if exit_code > 0:
        import sys
        sys.exit(exit_code)

if __name__ == '__main__':
    main()
