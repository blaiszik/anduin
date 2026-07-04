# cif-doctor

A batch validator and fixer for CIF (Crystallographic Information File) files.
Everyone's CIFs are dirty; nobody has a linter. This is the linter.

## What it does

Given one or more `.cif` files (or a directory), produce a per-file report:

- **Parse health** — does the file parse at all; malformed loops/tags
- **Symmetry** — declared space group vs. positions consistency
- **Occupancy** — site occupancy sums (flag > 1.0, warn on partial)
- **Charge neutrality** — net cell charge from declared oxidation states
- **Bond-length sanity** — nearest-neighbor distances vs. covalent-radii
  expectations; flag collisions and impossible contacts
- `--fix` applies safe, loss-free normalizations only (whitespace, tag case,
  deterministic ordering); everything else is report-only

## Shape

- Python 3.11+, `pymatgen` for parsing, `click` for the CLI
- `cifdoctor/` package: `checks/` (one module per check, a common
  `Check` protocol), `report.py` (text + JSON emitters), `cli.py`
- `tests/fixtures/` — small deliberately-broken CIFs, one per failure class
- `cif-doctor path/ --format json|text`, exit code = worst severity found

## Working agreement

Work is coordinated through the Moment project — claim a task before
building, leave a bench note when you stop, keep the handoff honest.
`main` is protected; all work lands on the `cif-doctor` branch. Pull
before you start. Run `pytest` before you push.
