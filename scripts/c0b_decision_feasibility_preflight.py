"""Preflight gates for C0B.0 decision-feasibility reconnaissance.

This script is read-only. It validates the evidence package and prints the
scientific gates needed before any later C0B.1 design work.
"""

from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_BRANCH = "phase/c0b-decision-feasibility-v1"
EXPECTED_HEAD = "144cb679186b8fdfe5b821aad635a7f805b7de28"
EXPECTED_TAG = "v0.4.0-climate-exposure-freeze"

REGISTRY_PATH = ROOT / "outputs/decision_feasibility/C0B_EVIDENCE_REGISTRY.csv"
CANDIDATES_PATH = ROOT / "outputs/decision_feasibility/C0B_CONSTRAINT_CANDIDATES.csv"
REPORT_PATH = ROOT / "outputs/decision_feasibility/C0B_DECISION_FEASIBILITY_REPORT.md"
SCRIPT_PATH = ROOT / "scripts/c0b_decision_feasibility_preflight.py"
TEST_PATH = ROOT / "tests/test_c0b_decision_feasibility_preflight.py"

AUTHORIZED_SCOPE = {
    "outputs/decision_feasibility/C0B_EVIDENCE_REGISTRY.csv",
    "outputs/decision_feasibility/C0B_CONSTRAINT_CANDIDATES.csv",
    "outputs/decision_feasibility/C0B_DECISION_FEASIBILITY_REPORT.md",
    "scripts/c0b_decision_feasibility_preflight.py",
    "tests/test_c0b_decision_feasibility_preflight.py",
}

REGISTRY_SCHEMA = [
    "EVIDENCE_ID",
    "DOMAIN",
    "CLAIM",
    "SOURCE_TIER",
    "SOURCE_AUTHORITY",
    "SOURCE_TITLE",
    "SOURCE_DATE",
    "SOURCE_URL",
    "LOCAL_SOURCE_PATH",
    "SPATIAL_UNIT",
    "TEMPORAL_UNIT",
    "TARGET_CROP",
    "EVIDENCE_STATUS",
    "EVIDENCE_FINDING",
    "LIMITATION",
    "NOTES",
]

CANDIDATE_SCHEMA = [
    "CONSTRAINT_ID",
    "CONSTRAINT_DOMAIN",
    "CANDIDATE_CONSTRAINT",
    "TARGET_CROP",
    "SOURCE_EVIDENCE_IDS",
    "UNIT",
    "SOURCE_SPATIAL_UNIT",
    "MODEL_SPATIAL_UNIT",
    "SPATIAL_FIT",
    "TEMPORAL_FIT",
    "EVIDENCE_STATUS",
    "DECISION_ROLE",
    "REQUIRED_CROSSWALK",
    "KEY_ASSUMPTION",
    "CRITICAL_GAP",
    "NEXT_EVIDENCE_NEEDED",
    "NOTES",
]

ALLOWED_DOMAINS = {
    "DECISION_MAKER",
    "LAND",
    "BASELINE_CROP_STOCK",
    "PCR",
    "WATER_AVAILABILITY",
    "HYDRAULIC_SYSTEM",
    "WATER_SPATIAL_CROSSWALK",
    "CROP_WATER_REQUIREMENT",
    "IRRIGATION_STATUS",
    "PERENNIAL_INERTIA",
    "ADJUSTMENT_CAPACITY",
    "ECONOMIC_COST",
    "SPATIAL_SCALE",
}

ALLOWED_SOURCE_TIERS = {"TIER_1", "TIER_2", "TIER_3", "TIER_4"}
ALLOWED_EVIDENCE_STATUSES = {
    "CERTIFIED_EXACT_OFFICIAL",
    "SUPPORTED_PRIMARY_OFFICIAL",
    "SUPPORTED_TECHNICAL",
    "PROXY_ONLY",
    "UNRESOLVED",
    "CONTRADICTED",
}
ALLOWED_SPATIAL_FIT = {
    "EXACT_DISTRICT",
    "DISTRICT_DERIVABLE_WITH_OFFICIAL_CROSSWALK",
    "CROSSWALK_REQUIRED",
    "AGGREGATE_ONLY",
    "NONSPATIAL",
    "UNKNOWN",
}
ALLOWED_DECISION_ROLES = {
    "HARD_CONSTRAINT_CANDIDATE",
    "SOFT_CONSTRAINT_CANDIDATE",
    "SENSITIVITY_ONLY",
    "CONTEXT_ONLY",
    "EXCLUDE_FROM_MODEL",
    "UNRESOLVED",
}

FORBIDDEN_REPO_PATH_PARTS = [
    "data/processed/decision",
    "config/optimization",
    "optimization",
    "optimizer",
    "scenario",
    "regression",
    "econometric",
    "gvp",
    "returns",
    "profit",
]

C0A_PATHS = {
    "outputs/outcome/C0A_EVIDENCE_REGISTRY.csv",
    "outputs/outcome/C0A_OUTCOME_EVIDENCE_REPORT.md",
    "scripts/c0a_outcome_evidence_preflight.py",
    "tests/test_c0a_outcome_evidence_preflight.py",
}


def _run_git(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return result.stdout.strip()


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def repository_identity() -> dict[str, str | bool]:
    branch = _run_git(["branch", "--show-current"])
    head = _run_git(["rev-parse", "HEAD"])
    tag_target = _run_git(["rev-parse", f"refs/tags/{EXPECTED_TAG}^{{commit}}"])
    return {
        "branch": branch,
        "head": head,
        "tag_target": tag_target,
        "branch_ok": branch == EXPECTED_BRANCH,
        "head_ok": head == EXPECTED_HEAD,
        "tag_ok": tag_target == EXPECTED_HEAD,
    }


def persistent_scope() -> dict[str, object]:
    status_lines = [
        line.strip()
        for line in _run_git(["status", "--short", "--untracked-files=all"]).splitlines()
        if line.strip()
    ]
    observed = {line[3:].replace("\\", "/") for line in status_lines if line.startswith("?? ")}
    tracked_changes = [line for line in status_lines if not line.startswith("?? ")]
    return {
        "status": "PASS" if observed == AUTHORIZED_SCOPE and not tracked_changes else "FAIL",
        "observed": sorted(observed),
        "tracked_changes": tracked_changes,
    }


def upstream_immutability() -> dict[str, object]:
    tracked_diff = [
        line.replace("\\", "/")
        for line in _run_git(["diff", "--name-only"]).splitlines()
        if line.strip()
    ]
    return {
        "status": "PASS" if not tracked_diff else "FAIL",
        "tracked_diff": tracked_diff,
    }


def validate_registry(rows: list[dict[str, str]]) -> dict[str, object]:
    ids = [row["EVIDENCE_ID"] for row in rows]
    domain_ok = all(row["DOMAIN"] in ALLOWED_DOMAINS for row in rows)
    tiers_ok = all(row["SOURCE_TIER"] in ALLOWED_SOURCE_TIERS for row in rows)
    status_ok = all(row["EVIDENCE_STATUS"] in ALLOWED_EVIDENCE_STATUSES for row in rows)
    id_ok = ids == [f"C0B-E{i:03d}" for i in range(1, len(rows) + 1)]
    schema_ok = list(rows[0].keys()) == REGISTRY_SCHEMA if rows else False
    required_domains_ok = ALLOWED_DOMAINS <= {row["DOMAIN"] for row in rows}
    return {
        "status": "PASS"
        if all([schema_ok, id_ok, domain_ok, tiers_ok, status_ok, required_domains_ok])
        else "FAIL",
        "rows": len(rows),
        "schema_ok": schema_ok,
        "id_ok": id_ok,
        "required_domains_ok": required_domains_ok,
    }


def validate_candidates(rows: list[dict[str, str]], registry_rows: list[dict[str, str]]) -> dict[str, object]:
    ids = [row["CONSTRAINT_ID"] for row in rows]
    registry_ids = {row["EVIDENCE_ID"] for row in registry_rows}
    schema_ok = list(rows[0].keys()) == CANDIDATE_SCHEMA if rows else False
    id_ok = ids == [f"C0B-C{i:03d}" for i in range(1, len(rows) + 1)]
    roles_ok = all(row["DECISION_ROLE"] in ALLOWED_DECISION_ROLES for row in rows)
    spatial_ok = all(row["SPATIAL_FIT"] in ALLOWED_SPATIAL_FIT for row in rows)
    statuses_ok = all(row["EVIDENCE_STATUS"] in ALLOWED_EVIDENCE_STATUSES for row in rows)
    references_ok = True
    for row in rows:
        refs = [ref for ref in row["SOURCE_EVIDENCE_IDS"].split(";") if ref]
        references_ok = references_ok and bool(refs) and all(ref in registry_ids for ref in refs)
    return {
        "status": "PASS" if all([schema_ok, id_ok, roles_ok, spatial_ok, statuses_ok, references_ok]) else "FAIL",
        "rows": len(rows),
        "schema_ok": schema_ok,
        "id_ok": id_ok,
        "references_ok": references_ok,
    }


def no_c0a_contamination() -> dict[str, object]:
    existing = sorted(path for path in C0A_PATHS if (ROOT / path).exists())
    return {"status": "PASS" if not existing else "FAIL", "existing": existing}


def no_optimization_artifacts() -> dict[str, object]:
    allowed = AUTHORIZED_SCOPE
    offenders: list[str] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = _relative(path).lower()
        if _relative(path) in allowed:
            continue
        if any(part in rel for part in FORBIDDEN_REPO_PATH_PARTS):
            offenders.append(_relative(path))
    return {"status": "PASS" if not offenders else "FAIL", "offenders": sorted(offenders)}


def report_firewalls(report: str) -> dict[str, object]:
    required_phrases = [
        "MIDAGRI physical agricultural area equals freely reallocable land: FALSE",
        "Chira-Piura PADH agrarian Hm3 can be divided among districts by area share: NOT_AUTHORIZED",
        "Poechos represents water availability for all Piura districts: FALSE",
        "District-level strategic recommendations are equivalent to parcel-level planting layouts: FALSE",
        "No optimizer is built.",
        "No C0A artifact is imported.",
        "C0B_0_STATUS=PASS_TO_C0B1_WITH_CRITICAL_GAPS",
    ]
    missing = [phrase for phrase in required_phrases if phrase not in report]
    return {"status": "PASS" if not missing else "FAIL", "missing": missing}


def critical_gap_summary(candidates: list[dict[str, str]]) -> list[str]:
    gaps = []
    for row in candidates:
        if row["DECISION_ROLE"] in {"UNRESOLVED", "EXCLUDE_FROM_MODEL"}:
            gaps.append(f"{row['CONSTRAINT_ID']}:{row['CRITICAL_GAP']}")
    return gaps


def main() -> int:
    identity = repository_identity()
    scope = persistent_scope()
    upstream = upstream_immutability()
    registry = _read_csv(REGISTRY_PATH)
    candidates = _read_csv(CANDIDATES_PATH)
    report = REPORT_PATH.read_text(encoding="utf-8")

    registry_gate = validate_registry(registry)
    candidate_gate = validate_candidates(candidates, registry)
    c0a_gate = no_c0a_contamination()
    optimization_gate = no_optimization_artifacts()
    report_gate = report_firewalls(report)

    gates = {
        "REPOSITORY_IDENTITY_GATE": "PASS"
        if identity["branch_ok"] and identity["head_ok"] and identity["tag_ok"]
        else "FAIL",
        "PERSISTENT_SCOPE_GATE": scope["status"],
        "UPSTREAM_IMMUTABILITY_GATE": upstream["status"],
        "REGISTRY_SCHEMA_GATE": registry_gate["status"],
        "CONSTRAINT_SCHEMA_GATE": candidate_gate["status"],
        "NO_C0A_CONTAMINATION_GATE": c0a_gate["status"],
        "NO_OPTIMIZATION_GATE": optimization_gate["status"],
        "REPORT_FIREWALL_GATE": report_gate["status"],
    }

    print(f"C0B_BRANCH={identity['branch']}")
    print(f"C0B_HEAD={identity['head']}")
    print(f"C0B_TAG_TARGET={identity['tag_target']}")
    print(f"EVIDENCE_REGISTRY_ROWS={registry_gate['rows']}")
    print(f"CONSTRAINT_CANDIDATES_ROWS={candidate_gate['rows']}")
    print("CRITICAL_EVIDENCE_GAPS=" + " | ".join(critical_gap_summary(candidates)))
    for key, value in gates.items():
        print(f"{key}={value}")
    print("C0B_0_STATUS=PASS_TO_C0B1_WITH_CRITICAL_GAPS" if all(value == "PASS" for value in gates.values()) else "C0B_0_STATUS=FAIL")
    return 0 if all(value == "PASS" for value in gates.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
