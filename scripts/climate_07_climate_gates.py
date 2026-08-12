from __future__ import annotations

from climate_common import QA_CLIMATE, write_json


def main() -> int:
    report = QA_CLIMATE / "climate_gate_report.json"
    if not report.exists():
        write_json(
            report,
            {
                "climate_master_version": "CLIMATE_MASTER_v1",
                "overall_gate": "FAIL",
                "blocking_issue": "CLIMATE_PIPELINE_NOT_COMPLETED",
            },
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
