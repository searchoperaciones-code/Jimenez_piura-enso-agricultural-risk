from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
QA = ROOT / "outputs" / "qa" / "climate"


def main() -> int:
    report_path = QA / "climate_execution_report.json"
    if not report_path.exists():
        raise SystemExit("CLIMATE_EXECUTION_REPORT_MISSING")
    report = json.loads(report_path.read_text(encoding="utf-8"))["supervision_report"]
    if report["execution_status"] != "PASS":
        audit = {
            "climate_checks_run": 0,
            "climate_checks_passed": 0,
            "max_abs_difference": None,
            "status": "NOT_RUN",
            "reason": "Climate extraction did not run because official IDEP boundaries were unavailable.",
        }
        (QA / "independent_extraction_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
        return 0
    raise SystemExit("PASS-path independent extraction audit is not implemented in this blocked execution artifact.")


if __name__ == "__main__":
    raise SystemExit(main())
