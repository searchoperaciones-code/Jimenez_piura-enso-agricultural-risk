from __future__ import annotations

from climate_common import audit_idep_connectivity, ensure_dirs


def main() -> int:
    ensure_dirs()
    audit = audit_idep_connectivity()
    if not audit["boundary_accessible"]:
        raise SystemExit("IDEP_OFFICIAL_BOUNDARY_ACCESS_FAILURE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
