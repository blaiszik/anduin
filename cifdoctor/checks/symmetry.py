"""Symmetry-metadata consistency check.

A CIF declares its space group redundantly across several fields:

- ``_symmetry_space_group_name_H-M`` (or ``_space_group_name_H-M_alt``) — the
  Hermann-Mauguin symbol, e.g. ``P n m a``.
- ``_symmetry_Int_Tables_number`` / ``_space_group_IT_number`` — the
  International Tables number, e.g. ``62``.
- ``_symmetry_equiv_pos_as_xyz`` / ``_space_group_symop_operation_xyz`` — the
  list of general-position symmetry operations.

When those fields disagree the file is internally inconsistent and downstream
tools silently pick one interpretation — a classic dirty-CIF failure mode. This
check compares the *declared* metadata against itself (via pymatgen's space
group tables); it does no coordinate-tolerance analysis.

Note: **under**-declaring symmetry is legal. Listing every atom in ``P 1`` for a
structure that happens to have higher symmetry is a valid (if verbose) CIF, so
we never flag "positions look more symmetric than declared" — only genuine
contradictions in the declared symmetry fields.

- symbol resolves but its IT number != declared number  -> error
- declared operation count  >  group order               -> error
- unrecognized H-M symbol                                -> warning
- 1 < declared operation count < group order             -> warning (generators only?)
- nothing declared                                       -> info (skipped)
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from cifdoctor.checks import Finding

NAME = "symmetry"

_HM_KEYS = ("_symmetry_space_group_name_H-M", "_space_group_name_H-M_alt")
_NUMBER_KEYS = ("_symmetry_Int_Tables_number", "_space_group_IT_number")
_OP_KEYS = ("_symmetry_equiv_pos_as_xyz", "_space_group_symop_operation_xyz")


def _first(block, keys) -> Optional[object]:
    for k in keys:
        v = block.get(k)
        if v is not None:
            return v
    return None


def _as_list(v) -> list:
    """Normalize a CIF field to a list (a lone loop row may come back as a str)."""
    if v is None:
        return []
    if isinstance(v, (list, tuple)):
        return list(v)
    return [v]


def _clean_symbol(sym: str) -> str:
    return str(sym).strip().strip("'\"").strip()


def run(path: Path) -> List[Finding]:
    """Check declared symmetry-metadata consistency for ``path``."""
    findings: List[Finding] = []

    try:
        from pymatgen.io.cif import CifParser, str2float
        from pymatgen.symmetry.groups import SpaceGroup
    except ImportError as exc:  # pragma: no cover - environment issue
        return [
            Finding(
                severity="error",
                message=f"pymatgen unavailable: {exc}",
                file_path=str(path),
                check_name=NAME,
            )
        ]

    try:
        blocks = CifParser(str(path)).as_dict()
    except Exception:
        # parse_health already reports the parse failure; nothing to check here.
        return findings

    for block in blocks.values():
        findings.extend(_check_block(block, path, SpaceGroup, str2float))

    return findings


def _check_block(block, path: Path, SpaceGroup, str2float) -> List[Finding]:
    findings: List[Finding] = []

    raw_symbol = _first(block, _HM_KEYS)
    symbol = _clean_symbol(raw_symbol) if raw_symbol is not None else None

    raw_number = _first(block, _NUMBER_KEYS)
    declared_number: Optional[int] = None
    if raw_number is not None:
        try:
            declared_number = int(round(str2float(str(raw_number))))
        except (TypeError, ValueError):
            declared_number = None

    ops = _as_list(_first(block, _OP_KEYS))
    n_ops = len(ops)

    # Nothing to check.
    if not symbol and declared_number is None and n_ops == 0:
        findings.append(
            Finding(
                severity="info",
                message="no space group declared; skipping symmetry check",
                file_path=str(path),
                check_name=NAME,
            )
        )
        return findings

    sg = None
    if symbol:
        try:
            sg = SpaceGroup(symbol)
        except (ValueError, KeyError):
            findings.append(
                Finding(
                    severity="warning",
                    message=f"unrecognized space group symbol '{symbol}'",
                    file_path=str(path),
                    check_name=NAME,
                )
            )

    if sg is None:
        return findings

    # Symbol resolves — cross-check the declared IT number.
    if declared_number is not None and declared_number != sg.int_number:
        findings.append(
            Finding(
                severity="error",
                message=(
                    f"space group '{symbol}' is No. {sg.int_number} but file "
                    f"declares No. {declared_number}"
                ),
                file_path=str(path),
                check_name=NAME,
            )
        )

    # Cross-check the declared operation count against the group order.
    if n_ops > sg.order:
        findings.append(
            Finding(
                severity="error",
                message=(
                    f"declares {n_ops} symmetry operations, more than "
                    f"'{symbol}' (order {sg.order}) permits"
                ),
                file_path=str(path),
                check_name=NAME,
            )
        )
    elif 1 < n_ops < sg.order:
        findings.append(
            Finding(
                severity="warning",
                message=(
                    f"declares {n_ops} symmetry operations but '{symbol}' has "
                    f"order {sg.order} (generators only?)"
                ),
                file_path=str(path),
                check_name=NAME,
            )
        )

    return findings
