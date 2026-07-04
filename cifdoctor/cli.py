import click
from pathlib import Path
from cifdoctor.report import emit_text, emit_json, get_exit_code

@click.command()
@click.argument('paths', nargs=-1, type=click.Path(exists=True, path_type=Path))
@click.option('--format', 'fmt', type=click.Choice(['text', 'json']), default='text', help='Output format')
@click.option('--fix/--no-fix', default=False, help='Apply safe, loss-free normalizations')
def main(paths, fmt, fix):
    """cif-doctor: Batch validator and fixer for CIF files."""
    findings = []
    
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
