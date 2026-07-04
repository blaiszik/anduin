"""Charge-neutrality check: net cell charge from declared oxidation states.

A well-formed ionic CIF should be charge-balanced: the occupancy-weighted sum
of the declared oxidation states across all sites in the asymmetric unit should
come out to zero (symmetry generates equivalents in the same ratio, so the net
sign is preserved regardless of multiplicity).

Oxidation states are read from the ``_atom_type_symbol`` / ``_atom_type_oxidation_number``
loop, and — failing that — parsed from the charge suffix on
``_atom_site_type_symbol`` values (e.g. ``Na+``, ``Fe3+``, ``O2-``). When no
oxidation states are declared at all, the check is *skipped* with an INFO
finding rather than silently passing (most CIFs carry no oxidation states, so
absence is not an error).

- |net| > TOL   -> warning  (declared composition is not charge-neutral)
- no states     -> info     (skipped; nothing to check)
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional

from cifdoctor.checks import Finding

NAME = "charge"
TOL = 1e-3

# Trailing ionic charge on a type symbol, e.g. "Na+", "Fe3+", "O2-", "Cl1-".
_CHARGE_RE = re.compile(r"^([A-Za-z]+)(\d*)([+-])$")


def _parse_symbol_charge(symbol: str) -> Optional[float]:
    """Parse a trailing ionic charge from a type symbol; None if absent."""
    m = _CHARGE_RE.match(symbol.strip())
    if not m:
        return None
    magnitude = float(m.group(2)) if m.group(2) else 1.0
    sign = 1.0 if m.group(3) == "+" else -1.0
    return sign * magnitude


def _oxidation_map(block: Dict) -> Dict[str, float]:
    """Build {type_symbol -> oxidation state} from the declared CIF loops.

    Prefers the explicit ``_atom_type_oxidation_number`` loop; falls back to
    the charge suffix embedded in the type-symbol strings.
    """
    from pymatgen.io.cif import str2float

    oxi: Dict[str, float] = {}

    symbols = block.get("_atom_type_symbol")
    numbers = block.get("_atom_type_oxidation_number")
    if symbols and numbers:
        for sym, num in zip(symbols, numbers):
            try:
                oxi[sym] = str2float(num)
            except (TypeError, ValueError):
                continue

    if not oxi:
        # Fall back to charges baked into the symbol strings themselves.
        for sym in block.get("_atom_site_type_symbol") or []:
            charge = _parse_symbol_charge(sym)
            if charge is not None:
                oxi[sym] = charge

    return oxi


def run(path: Path) -> List[Finding]:
    """Check declared charge neutrality for ``path``."""
    findings: List[Finding] = []

    try:
        from pymatgen.io.cif import CifParser, str2float
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
        parser = CifParser(str(path))
        blocks = parser.as_dict()
    except Exception:
        # parse_health already reports the parse failure; nothing to check here.
        return findings

    for name, block in blocks.items():
        oxi = _oxidation_map(block)

        if not oxi:
            findings.append(
                Finding(
                    severity="info",
                    message="no oxidation states declared; skipping charge check",
                    file_path=str(path),
                    check_name=NAME,
                )
            )
            continue

        site_symbols = block.get("_atom_site_type_symbol")
        occs = block.get("_atom_site_occupancy")
        if not site_symbols:
            continue

        net = 0.0
        for i, sym in enumerate(site_symbols):
            state = oxi.get(sym)
            if state is None:
                # A site whose type has no declared oxidation state: treat as
                # neutral (0) so we don't invent charge that wasn't declared.
                continue
            occ = 1.0
            if occs and i < len(occs):
                try:
                    occ = str2float(occs[i])
                except (TypeError, ValueError):
                    occ = 1.0
            net += state * occ

        if abs(net) > TOL:
            findings.append(
                Finding(
                    severity="warning",
                    message=(
                        f"declared composition is not charge-neutral: "
                        f"net cell charge {net:+.3f}"
                    ),
                    file_path=str(path),
                    check_name=NAME,
                )
            )

    return findings
