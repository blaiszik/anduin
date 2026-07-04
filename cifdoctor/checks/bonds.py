"""Bond-length sanity check: nearest-neighbour contacts vs covalent radii.

For every close contact in the structure we compare the interatomic distance
against the sum of the two elements' covalent radii. Physically implausible
contacts almost always mean overlapping sites, a bad fractional coordinate, or
a units/cell-parameter error in the CIF.

- distance < ERROR_FACTOR x (r_i + r_j)  -> error   (impossible contact)
- distance < WARN_FACTOR  x (r_i + r_j)  -> warning  (suspiciously short)

Covalent radii come from pymatgen's ``CovalentRadius`` table. Contacts beyond
``SEARCH_CUTOFF`` angstroms are not evaluated (a sanity check only cares about
things that are *too close*, never too far).
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple

from cifdoctor.checks import Finding

NAME = "bonds"

ERROR_FACTOR = 0.6
WARN_FACTOR = 0.75
# Generous upper bound on any real bond; contacts farther than this are ignored.
SEARCH_CUTOFF = 4.0
# Distances at/below this are true coincident sites; radii comparison is moot.
COINCIDENT_TOL = 1e-3


def _covalent_radius(symbol: str) -> Optional[float]:
    from pymatgen.analysis.molecule_structure_comparator import CovalentRadius

    return CovalentRadius.radius.get(symbol)


def _site_radius(site) -> Optional[float]:
    """Covalent radius for a site's dominant element (largest occupancy)."""
    try:
        species = site.species.get_el_amt_dict()  # {symbol: amount}
    except Exception:  # noqa: BLE001 - be defensive about odd site species
        return None
    if not species:
        return None
    dominant = max(species, key=species.get)
    return _covalent_radius(dominant)


def _site_desc(structure, i: int) -> str:
    label = getattr(structure[i], "label", None)
    return label or f"{structure[i].species_string}#{i}"


def run(path: Path) -> List[Finding]:
    """Check bond-length plausibility for ``path``."""
    findings: List[Finding] = []

    try:
        from pymatgen.io.cif import CifParser
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
        structures = parser.parse_structures(primitive=False, on_error="warn")
    except Exception:
        # parse_health already reports the parse failure; nothing to check here.
        return findings

    for structure in structures:
        findings.extend(_check_structure(structure, path))

    return findings


def _check_structure(structure, path: Path) -> List[Finding]:
    findings: List[Finding] = []

    try:
        all_neighbors = structure.get_all_neighbors(SEARCH_CUTOFF)
    except Exception:  # noqa: BLE001 - malformed lattices can raise here
        return findings

    # Keep only the shortest contact per unordered site pair to avoid
    # reporting the same too-close pair once per periodic image.
    shortest: Dict[Tuple[int, int], float] = {}
    for i, neighbors in enumerate(all_neighbors):
        for nb in neighbors:
            j = nb.index
            if j == i:
                continue
            dist = float(nb.nn_distance)
            key = (i, j) if i < j else (j, i)
            if key not in shortest or dist < shortest[key]:
                shortest[key] = dist

    radii: Dict[int, Optional[float]] = {}
    for (i, j), dist in sorted(shortest.items()):
        if dist <= COINCIDENT_TOL:
            continue
        ri = radii.setdefault(i, _site_radius(structure[i]))
        rj = radii.setdefault(j, _site_radius(structure[j]))
        if ri is None or rj is None:
            continue
        expected = ri + rj
        if expected <= 0:
            continue
        ratio = dist / expected

        pair = f"{_site_desc(structure, i)}-{_site_desc(structure, j)}"
        if ratio < ERROR_FACTOR:
            findings.append(
                Finding(
                    severity="error",
                    message=(
                        f"impossible contact {pair}: {dist:.3f} A is "
                        f"{ratio:.2f}x the expected {expected:.3f} A "
                        f"(< {ERROR_FACTOR:g}x)"
                    ),
                    file_path=str(path),
                    check_name=NAME,
                )
            )
        elif ratio < WARN_FACTOR:
            findings.append(
                Finding(
                    severity="warning",
                    message=(
                        f"suspiciously short contact {pair}: {dist:.3f} A is "
                        f"{ratio:.2f}x the expected {expected:.3f} A "
                        f"(< {WARN_FACTOR:g}x)"
                    ),
                    file_path=str(path),
                    check_name=NAME,
                )
            )

    return findings
