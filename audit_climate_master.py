from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
QA = ROOT / "outputs" / "qa" / "climate"
REPOSITORY_OUTPUTS = ROOT / "outputs" / "repository"
VERIFICATION_PATH = REPOSITORY_OUTPUTS / "climate_certification_verification.json"


def read_json(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(str(path))
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def report_path_to_local(path_text: str) -> Path:
    return ROOT / Path(path_text.replace("\\", "/"))


def q1_recommendation() -> str:
    path = QA / "Q1_climate_readiness.md"
    if not path.exists():
        return "MISSING"
    text = path.read_text(encoding="utf-8")
    return "GO_TO_PHENOLOGY_PHASE" if "GO_TO_PHENOLOGY_PHASE" in text else "NOT_FOUND"


def raw_archive_status() -> dict[str, Any]:
    manifest_path = QA / "climate_data_manifest.csv"
    raw_root = ROOT / "data" / "raw" / "climate"
    return {
        "mode": "RAW_RASTER_INDEPENDENT_REEXTRACTION",
        "automatic_redownload": False,
        "raw_climate_root_exists": raw_root.exists(),
        "manifest_exists": manifest_path.exists(),
        "status": "OPTIONAL_NOT_RUN",
        "reason": "This certification verifier is artifact-level by default and never redownloads the raw climate archive.",
    }


def main() -> int:
    checks: list[dict[str, Any]] = []
    blocking: list[str] = []

    def add_check(name: str, passed: bool, observed: Any = None, expected: Any = None) -> None:
        checks.append({"name": name, "pass": bool(passed), "observed": observed, "expected": expected})
        if not passed:
            blocking.append(name)

    execution_path = QA / "climate_execution_report.json"
    gate_path = QA / "climate_gate_report.json"
    independent_path = QA / "independent_extraction_audit.json"
    reproducibility_path = QA / "climate_reproducibility_report.json"

    add_check("climate_execution_report_exists", execution_path.exists(), str(execution_path.relative_to(ROOT)), True)
    add_check("climate_gate_report_exists", gate_path.exists(), str(gate_path.relative_to(ROOT)), True)
    add_check("independent_extraction_audit_exists", independent_path.exists(), str(independent_path.relative_to(ROOT)), True)
    add_check("climate_reproducibility_report_exists", reproducibility_path.exists(), str(reproducibility_path.relative_to(ROOT)), True)

    if blocking:
        report = {
            "verification_type": "CERTIFIED_ARTIFACT_VERIFICATION",
            "status": "FAIL",
            "checks": checks,
            "blocking_issues": blocking,
            "raw_raster_independent_reextraction": raw_archive_status(),
        }
        REPOSITORY_OUTPUTS.mkdir(parents=True, exist_ok=True)
        VERIFICATION_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return 1

    execution = read_json(execution_path)["supervision_report"]
    gate = read_json(gate_path)
    independent = read_json(independent_path)
    reproducibility = read_json(reproducibility_path)

    add_check("execution_status_pass", execution.get("execution_status") == "PASS", execution.get("execution_status"), "PASS")
    add_check("overall_gate_pass", gate.get("overall_gate") == "PASS", gate.get("overall_gate"), "PASS")
    add_check("q1_recommendation", q1_recommendation() == "GO_TO_PHENOLOGY_PHASE", q1_recommendation(), "GO_TO_PHENOLOGY_PHASE")
    add_check("districts_matched", execution.get("districts_matched") == "55 / 55", execution.get("districts_matched"), "55 / 55")
    add_check("main_rows_5280", execution.get("climate_rows", {}).get("main") == 5280, execution.get("climate_rows", {}).get("main"), 5280)
    add_check("overlap_rows_6215", execution.get("climate_rows", {}).get("overlap") == 6215, execution.get("climate_rows", {}).get("overlap"), 6215)
    add_check("panel_linkage_1", float(execution.get("panel_linkage_rate", -1)) == 1.0, execution.get("panel_linkage_rate"), 1.0)
    add_check("independent_36_of_36", independent.get("checks_run") == 36 and independent.get("checks_passed") == 36, independent, "36/36")
    add_check("normal_completeness_pass", execution.get("normal_completeness") == "PASS", execution.get("normal_completeness"), "PASS")
    add_check("temporal_leakage_false", gate.get("temporal_leakage") is False, gate.get("temporal_leakage"), False)
    add_check(
        "unauthorized_modelling_false",
        gate.get("unauthorized_scope_expansion") is False,
        gate.get("unauthorized_scope_expansion"),
        False,
    )
    add_check(
        "deterministic_outputs_identical",
        reproducibility.get("deterministic_outputs_identical") is True,
        reproducibility.get("deterministic_outputs_identical"),
        True,
    )

    run1_hashes = execution.get("reproducibility", {}).get("run1_hashes", {})
    hash_results: list[dict[str, Any]] = []
    for report_path, expected_hash in sorted(run1_hashes.items()):
        local_path = report_path_to_local(report_path)
        exists = local_path.exists()
        actual_hash = sha256_file(local_path) if exists else None
        passed = exists and actual_hash == expected_hash
        hash_results.append(
            {
                "path": report_path,
                "normalized_path": str(local_path.relative_to(ROOT)),
                "exists": exists,
                "expected_sha256": expected_hash,
                "actual_sha256": actual_hash,
                "pass": passed,
            }
        )
        if not passed:
            blocking.append(f"hash_mismatch:{report_path}")

    add_check(
        "committed_deterministic_output_hashes_match_run1",
        all(item["pass"] for item in hash_results) and len(hash_results) > 0,
        {"matched": sum(1 for item in hash_results if item["pass"]), "total": len(hash_results)},
        {"matched": len(hash_results), "total": len(hash_results)},
    )

    status = "PASS" if not blocking else "FAIL"
    report = {
        "verification_type": "CERTIFIED_ARTIFACT_VERIFICATION",
        "status": status,
        "certified_climate_master": "CLIMATE_MASTER_v1.1",
        "distinction": {
            "CERTIFIED_ARTIFACT_VERIFICATION": "Checks committed processed/QA artifacts and certified output hashes.",
            "RAW_RASTER_INDEPENDENT_REEXTRACTION": "Requires local raw rasters and is not run by default.",
        },
        "checks": checks,
        "deterministic_output_hashes": hash_results,
        "raw_raster_independent_reextraction": raw_archive_status(),
        "blocking_issues": blocking,
    }
    REPOSITORY_OUTPUTS.mkdir(parents=True, exist_ok=True)
    VERIFICATION_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "output": str(VERIFICATION_PATH.relative_to(ROOT))}, sort_keys=True))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
