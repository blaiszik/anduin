import click
from pathlib import Path
from cifdoctor.report import emit_text, emit_json, get_exit_code
from cifdoctor.checks import parse_health, occupancy, charge, bonds

# Checks are plain modules exposing a `run(path) -> List[Finding]` function
# (see cifdoctor/checks/__init__.py for the Finding/Check protocol).
CHECKS = [parse_health, occupancy, charge, bonds]


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
    fixed_files = []

    for cif_path in _iter_cif_files(paths):
        cif_path = Path(cif_path)
        for check in CHECKS:
            findings.extend(check.run(cif_path))
            
        if fix:
            try:
                from pymatgen.io.cif import CifFile
                cf = CifFile.from_file(cif_path)
                with open(cif_path, "w") as f:
                    f.write(str(cf))
                fixed_files.append(str(cif_path))
            except Exception as exc:  # noqa: BLE001 - report, don't hide, fix failures
                click.echo(f"WARNING: --fix failed for {cif_path}: {exc}", err=True)

    if fmt == 'json':
        emit_json(findings, fixed_files)
    else:
        emit_text(findings, fixed_files)

    exit_code = get_exit_code(findings)
    if exit_code > 0:
        import sys
        sys.exit(exit_code)

if __name__ == '__main__':
    main()
