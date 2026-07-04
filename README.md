# cif-doctor

A batch validator and fixer for CIF (Crystallographic Information File) files.
Everyone's CIFs are dirty; nobody has a linter. This is the linter.

## What it does

Given one or more `.cif` files (or a directory), produce a per-file report:

- **Parse health** — does the file parse at all; malformed loops/tags
  (`cifdoctor/checks/parse_health.py`)
- **Occupancy** — site occupancy sums (flag > 1.0, info on partial)
  (`cifdoctor/checks/occupancy.py`)
- **Charge neutrality** — net cell charge from declared oxidation states
  (`cifdoctor/checks/charge.py`)
- **Bond-length sanity** — nearest-neighbor distances vs. covalent-radii
  expectations; flag collisions and impossible contacts
  (`cifdoctor/checks/bonds.py`)
- **Symmetry metadata** — cross-checks the declared space group against itself:
  the H-M symbol vs. the International Tables number vs. the count of
  `_symmetry_equiv_pos_as_xyz` operations (error on a symbol/number contradiction
  or too many ops; warning on an unrecognized symbol or a generators-only op
  list). Declared metadata only — **under**-declaring symmetry (all atoms in
  `P 1`) is legal CIF and is never flagged (`cifdoctor/checks/symmetry.py`)
- `--fix` applies safe, loss-free normalizations only (whitespace, tag case,
  deterministic ordering); everything else is report-only

## Usage

```bash
pip install -e .            # registers the `cif-doctor` entry point
cif-doctor tests/fixtures/ --format text
cif-doctor tests/fixtures/clean.cif tests/fixtures/bad_occupancy.cif --format json
cif-doctor tests/fixtures/ --fix                       # apply safe normalizations, then report
```

`paths` accepts any mix of individual `.cif` files and directories (directories
are searched recursively for `*.cif`). `--format` is `text` (default, grouped
by file and severity) or `json` (machine-readable, one object with
`findings` / `fixed_files` / `summary`). The **exit code is the worst severity
found**: `0` clean, `1` warnings only, `2` at least one error — wire it
straight into CI.

Real output from the fixtures above (`--format text`, abridged to two files;
pymatgen's own parser warnings print to stderr and are omitted here):

```
File: tests/fixtures/bad_occupancy.cif
  ERRORS:
    - parse_health: failed to parse (line 9): Invalid CIF file with no structures!
    - occupancy: site Na1 at (0.0, 0.0, 0.0) has occupancy sum 1.5000 > 1.0
  INFOS:
    - occupancy: site Cl1 at (0.5, 0.5, 0.5) has partial occupancy sum 0.7000
    - charge: no oxidation states declared; skipping charge check

File: tests/fixtures/close_contact.cif
  ERRORS:
    - bonds: impossible contact Na1-Cl1: 0.250 A is 0.09x the expected 2.680 A (< 0.6x)
  INFOS:
    - charge: no oxidation states declared; skipping charge check

SUMMARY: 16 findings (4 errors, 2 warnings, 10 infos) across 8 files.
```

Note `bad_occupancy.cif` fails outright to parse into a pymatgen `Structure`
*and* still gets a precise occupancy finding — `occupancy.py` reads the raw
`_atom_site_*` loop directly rather than depending on the `Structure` object,
specifically so an out-of-range occupancy is reported instead of silently
swallowed by pymatgen's own rescale/reject behavior.

If `--fix` fails to rewrite a given file (e.g. a file that fails parse
entirely), it now prints a `WARNING: --fix failed for <path>: <reason>` line
to stderr instead of silently skipping it — that file simply won't appear in
`fixed_files`.

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
