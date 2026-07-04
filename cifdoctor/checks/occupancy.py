"""Occupancy check: per-site occupancy sums.

Reads the raw ``_atom_site_*`` loop directly (bypassing pymatgen's
Structure construction, which silently rescales or rejects sites whose
occupancies sum above its own tolerance) so we can report the *actual*
declared sums. Sites are grouped by fractional coordinate; occupancies
within a group are summed.

- sum > 1.0 + TOL  -> error   (physically impossible; site overfilled)
- sum < 1.0 - TOL  -> info    (partial occupancy; not necessarily wrong)
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

from cifdoctor.checks import Finding

NAME = "occupancy"
TOL = 1e-4
COORD_NDIGITS = 4


def _coord_key(x: float, y: float, z: float) -> Tuple[float, float, float]:
    return (round(x, COORD_NDIGITS), round(y, COORD_NDIGITS), round(z, COORD_NDIGITS))


def run(path: Path) -> List[Finding]:
    """Check per-site occupancy sums for ``path``."""
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

    for block in blocks.values():
        labels = block.get("_atom_site_label")
        xs = block.get("_atom_site_fract_x")
        ys = block.get("_atom_site_fract_y")
        zs = block.get("_atom_site_fract_z")
        occs = block.get("_atom_site_occupancy")

        if not (labels and xs and ys and zs and occs):
            # No occupancy column declared at all: nothing to sum, assume
            # full occupancy (pymatgen/CIF convention).
            continue

        n = min(len(labels), len(xs), len(ys), len(zs), len(occs))
        sums: Dict[Tuple[float, float, float], float] = {}
        site_labels: Dict[Tuple[float, float, float], List[str]] = {}

        for i in range(n):
            try:
                x, y, z = str2float(xs[i]), str2float(ys[i]), str2float(zs[i])
                occ = str2float(occs[i])
            except (TypeError, ValueError):
                continue
            key = _coord_key(x, y, z)
            sums[key] = sums.get(key, 0.0) + occ
            site_labels.setdefault(key, []).append(labels[i])

        for key, total in sums.items():
            site_desc = "/".join(site_labels[key])
            if total > 1.0 + TOL:
                findings.append(
                    Finding(
                        severity="error",
                        message=(
                            f"site {site_desc} at {key} has occupancy sum "
                            f"{total:.4f} > 1.0"
                        ),
                        file_path=str(path),
                        check_name=NAME,
                    )
                )
            elif total < 1.0 - TOL:
                findings.append(
                    Finding(
                        severity="info",
                        message=(
                            f"site {site_desc} at {key} has partial occupancy "
                            f"sum {total:.4f}"
                        ),
                        file_path=str(path),
                        check_name=NAME,
                    )
                )

    return findings
