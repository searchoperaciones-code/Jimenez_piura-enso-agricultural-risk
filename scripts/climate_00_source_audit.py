from __future__ import annotations

from climate_common import (
    ensure_dirs,
    environment_report,
    save_source_metadata,
    verify_upstream_dataset,
    write_climate_sources_frozen,
    write_pisco_audit,
    write_station_access_audit,
)


def main() -> int:
    ensure_dirs()
    environment_report()
    upstream = verify_upstream_dataset()
    if not upstream["integrity_pass"]:
        raise SystemExit("UPSTREAM_DATASET_INTEGRITY_FAILURE")
    save_source_metadata()
    write_climate_sources_frozen()
    write_pisco_audit()
    write_station_access_audit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
