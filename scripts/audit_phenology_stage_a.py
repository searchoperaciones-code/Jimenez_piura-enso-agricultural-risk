from __future__ import annotations

import argparse
import ast
import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASE_SHA = "e4710b1429ed54c557e6c0a88212a24a6fdd7d47"
QA = ROOT / "outputs" / "phenology" / "qa"
READINESS = ROOT / "outputs" / "phenology" / "PHENOLOGY_STAGE_A_READINESS.md"

PROCESSING_FILES = [ROOT / "scripts" / "phenology_stage_a.py"]
TRANSIENT_CROPS = {"14010020000", "14010070000"}
FORBIDDEN_COLUMNS = {"YIELD_RAW", "YIELD_UNIT", "PRECIO", "PRECIO_CHACRA"}
FORBIDDEN_IMPORTS = {"statsmodels", "sklearn", "linearmodels", "pymc", "cvxpy", "pyomo"}
FORBIDDEN_IDENTIFIERS = {"regression", "pvalue", "pvalues", "rsquared", "aic", "bic", "predict", "fit"}
FORBIDDEN_OUTPUT_NAMES = {
    "crop_exposure_architecture.csv",
    "phenology_windows_frozen.csv",
    "phenology_exposures_panel.parquet",
    "phenology_exposures_long.parquet",
}
TRANSIENT_PRODUCTION_METADATA_COLUMNS = [
    "PRODUCTION_ANNUAL_DENOMINATOR",
    "PRODUCTION_MISSING_MONTH_COUNT",
    "PRODUCTION_POSITIVE_MONTH_COUNT",
    "PRODUCTION_SHARE",
]
TRANSIENT_PRODUCTION_ALLOWED_STATUS = "NOT_COMPUTED_TRANSIENT"
PROTECTED_PATHS = [
    "data/processed/panel_master.csv",
    "data/processed/panel_balanceado.csv",
    "data/processed/climate",
    "outputs/qa",
    "outputs/figures/climate_qa",
    "outputs/repository",
]


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def run_git(args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=check)


def git_lines(args: list[str]) -> list[str]:
    result = run_git(args)
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def protected_diff() -> list[str]:
    return git_lines(["diff", "--name-only", BASE_SHA, "--", *PROTECTED_PATHS])


def protected_status() -> list[str]:
    return git_lines(["status", "--short", "--", *PROTECTED_PATHS])


def base_is_ancestor() -> bool:
    return run_git(["merge-base", "--is-ancestor", BASE_SHA, "HEAD"], check=False).returncode == 0


def call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = call_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return ""


def string_args(node: ast.Call) -> list[str]:
    values = []
    for arg in list(node.args) + [kw.value for kw in node.keywords]:
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            values.append(arg.value)
    return values


class StageAFirewallVisitor(ast.NodeVisitor):
    def __init__(self, path: Path):
        self.path = path
        self.findings: list[dict[str, Any]] = []

    def add(self, node: ast.AST, kind: str, detail: str) -> None:
        self.findings.append(
            {
                "file": str(self.path.relative_to(ROOT)),
                "line": getattr(node, "lineno", None),
                "finding": kind,
                "detail": detail,
            }
        )

    def visit_Constant(self, node: ast.Constant) -> None:
        if isinstance(node.value, str) and node.value in FORBIDDEN_COLUMNS:
            self.add(node, "FORBIDDEN_COLUMN_LITERAL", node.value)
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            root = alias.name.split(".")[0]
            if root in FORBIDDEN_IMPORTS or alias.name == "scipy.stats":
                self.add(node, "FORBIDDEN_IMPORT", alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        root = module.split(".")[0]
        if root in FORBIDDEN_IMPORTS or module == "scipy.stats":
            self.add(node, "FORBIDDEN_IMPORT", module)
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        if node.id.lower() in FORBIDDEN_IDENTIFIERS:
            self.add(node, "FORBIDDEN_IDENTIFIER", node.id)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        lowered = node.attr.lower()
        if lowered == "corr":
            self.add(node, "FORBIDDEN_CORRELATION_CALL", node.attr)
        if lowered in FORBIDDEN_IDENTIFIERS:
            self.add(node, "FORBIDDEN_IDENTIFIER", node.attr)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        name = call_name(node.func).lower()
        args = string_args(node)
        if name.endswith("read_parquet"):
            self.add(node, "FORBIDDEN_PARQUET_READ", name)
        if name.endswith("read_table") and any("climate_monthly_primary.parquet" in value for value in args):
            self.add(node, "FORBIDDEN_CLIMATE_TABLE_READ", name)
        if name.endswith("read_csv") and any("panel_master.csv" in value or "panel_balanceado.csv" in value for value in args):
            self.add(node, "FORBIDDEN_PANEL_TABLE_READ", name)
        if name.split(".")[-1] in FORBIDDEN_IDENTIFIERS:
            self.add(node, "FORBIDDEN_MODEL_METHOD_CALL", name)
        self.generic_visit(node)


def processing_files() -> list[Path]:
    files = set(PROCESSING_FILES)
    files.update(ROOT.glob("scripts/phenology_stage_a_*.py"))
    files.discard(ROOT / "scripts" / "audit_phenology_stage_a.py")
    return sorted(files)


def nonnull_count(frame, columns: list[str]) -> int:
    present = [column for column in columns if column in frame.columns]
    if not present:
        return 0
    return int(frame[present].notna().sum().sum())


def evaluate_transient_production_firewall(processed_root: Path, qa_root: Path) -> dict[str, Any]:
    import pandas as pd

    findings: list[dict[str, Any]] = []
    monthly_path = processed_root / "temporal_structure_monthly.csv"
    summary_path = processed_root / "temporal_structure_summary.csv"
    crossing_path = qa_root / "year_crossing_audit.csv"

    monthly_counts = {
        "transient_produccion_nonnull_cells": None,
        "transient_production_metadata_nonnull_cells": None,
        "transient_bad_status_cells": None,
    }
    summary_rows = None
    crossing_values = None
    permanent_preserved = None

    if monthly_path.exists():
        monthly = pd.read_csv(monthly_path, dtype={"COD_CULTIVO": "string"})
        transient_monthly = monthly[monthly["COD_CULTIVO"].astype(str).isin(TRANSIENT_CROPS)]
        monthly_counts["transient_produccion_nonnull_cells"] = int(transient_monthly["PRODUCCION"].notna().sum()) if "PRODUCCION" in transient_monthly.columns else 0
        monthly_counts["transient_production_metadata_nonnull_cells"] = nonnull_count(
            transient_monthly, TRANSIENT_PRODUCTION_METADATA_COLUMNS
        )
        if "PRODUCTION_DENOMINATOR_STATUS" in transient_monthly.columns:
            bad_status = transient_monthly["PRODUCTION_DENOMINATOR_STATUS"].fillna("") != TRANSIENT_PRODUCTION_ALLOWED_STATUS
            monthly_counts["transient_bad_status_cells"] = int(bad_status.sum())
        else:
            monthly_counts["transient_bad_status_cells"] = len(transient_monthly)
        permanent = monthly[~monthly["COD_CULTIVO"].astype(str).isin(TRANSIENT_CROPS)]
        permanent_preserved = bool("PRODUCTION_SHARE" in permanent.columns and permanent["PRODUCTION_SHARE"].notna().sum() > 0)
    else:
        findings.append({"file": display_path(monthly_path), "line": None, "finding": "MISSING_TEMPORAL_MONTHLY", "detail": "temporal_structure_monthly.csv"})

    if monthly_counts["transient_produccion_nonnull_cells"]:
        findings.append(
            {
                "file": display_path(monthly_path),
                "line": None,
                "finding": "TRANSIENT_PRODUCCION_VALUE_EXPOSED",
                "detail": monthly_counts["transient_produccion_nonnull_cells"],
            }
        )
    if monthly_counts["transient_production_metadata_nonnull_cells"]:
        findings.append(
            {
                "file": display_path(monthly_path),
                "line": None,
                "finding": "TRANSIENT_PRODUCTION_METADATA_EXPOSED",
                "detail": monthly_counts["transient_production_metadata_nonnull_cells"],
            }
        )
    if monthly_counts["transient_bad_status_cells"]:
        findings.append(
            {
                "file": display_path(monthly_path),
                "line": None,
                "finding": "TRANSIENT_PRODUCTION_STATUS_INVALID",
                "detail": monthly_counts["transient_bad_status_cells"],
            }
        )

    if summary_path.exists():
        summary = pd.read_csv(summary_path, dtype={"COD_CULTIVO": "string"})
        summary_rows = int(((summary["COD_CULTIVO"].astype(str).isin(TRANSIENT_CROPS)) & (summary["VARIABLE"].astype(str) == "PRODUCCION")).sum())
    else:
        findings.append({"file": display_path(summary_path), "line": None, "finding": "MISSING_TEMPORAL_SUMMARY", "detail": "temporal_structure_summary.csv"})
    if summary_rows:
        findings.append(
            {
                "file": display_path(summary_path),
                "line": None,
                "finding": "TRANSIENT_PRODUCTION_SUMMARY_ROW",
                "detail": summary_rows,
            }
        )

    if crossing_path.exists():
        crossing = pd.read_csv(crossing_path, dtype={"COD_CULTIVO": "string"})
        transient_crossing = crossing[crossing["COD_CULTIVO"].astype(str).isin(TRANSIENT_CROPS)]
        production_columns = [column for column in transient_crossing.columns if "PRODUCTION" in column.upper()]
        crossing_values = nonnull_count(transient_crossing, production_columns)
    else:
        findings.append({"file": display_path(crossing_path), "line": None, "finding": "MISSING_YEAR_CROSSING", "detail": "year_crossing_audit.csv"})
    if crossing_values:
        findings.append(
            {
                "file": display_path(crossing_path),
                "line": None,
                "finding": "TRANSIENT_YEAR_CROSSING_PRODUCTION_VALUE",
                "detail": crossing_values,
            }
        )

    if permanent_preserved is False:
        findings.append(
            {
                "file": display_path(monthly_path),
                "line": None,
                "finding": "PERMANENT_PRODUCTION_SEASONALITY_NOT_PRESERVED",
                "detail": "No non-null permanent production shares found.",
            }
        )

    return {
        **monthly_counts,
        "transient_production_summary_rows": summary_rows,
        "transient_year_crossing_production_values": crossing_values,
        "permanent_production_seasonality_preserved": permanent_preserved,
        "findings": findings,
        "status": "PASS" if not findings else "FAIL",
    }


def scan_processing_code() -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    scanned = []
    for path in processing_files():
        if not path.exists():
            continue
        scanned.append(str(path.relative_to(ROOT)))
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        visitor = StageAFirewallVisitor(path)
        visitor.visit(tree)
        findings.extend(visitor.findings)
    forbidden_outputs = []
    for root in [ROOT / "data" / "processed" / "phenology", ROOT / "outputs" / "phenology"]:
        if root.exists():
            for path in root.rglob("*"):
                if path.is_file() and path.name in FORBIDDEN_OUTPUT_NAMES:
                    forbidden_outputs.append(str(path.relative_to(ROOT)))
    for path in forbidden_outputs:
        findings.append({"file": path, "line": None, "finding": "FORBIDDEN_STAGE_B_OUTPUT", "detail": path})
    production_firewall = evaluate_transient_production_firewall(
        ROOT / "data" / "processed" / "phenology", ROOT / "outputs" / "phenology" / "qa"
    )
    findings.extend(production_firewall["findings"])
    climate_parsed_for_analysis = any(item["finding"] in {"FORBIDDEN_PARQUET_READ", "FORBIDDEN_CLIMATE_TABLE_READ"} for item in findings)
    panel_outcome_data_parsed = any(item["finding"] in {"FORBIDDEN_PANEL_TABLE_READ", "FORBIDDEN_COLUMN_LITERAL"} for item in findings)
    report = {
        "audit": "NO_OUTCOME_SNOOPING_STAGE_A",
        "scanned_files": scanned,
        "findings": findings,
        "finding_count": len(findings),
        "forbidden_stage_b_outputs": forbidden_outputs,
        "transient_production_firewall": {key: value for key, value in production_firewall.items() if key != "findings"},
        "climate_parsed_for_analysis": climate_parsed_for_analysis,
        "panel_outcome_data_parsed": panel_outcome_data_parsed,
        "status": "PASS" if not findings else "FAIL",
    }
    write_json(QA / "no_outcome_snooping_audit.json", report)
    return report


def file_exists(rel_path: str) -> bool:
    return (ROOT / rel_path).exists()


def count_csv_rows(rel_path: str) -> int:
    import pandas as pd

    return int(len(pd.read_csv(ROOT / rel_path)))


def aggregate_gates(no_snoop: dict[str, Any]) -> dict[str, Any]:
    upstream = read_json(QA / "upstream_integrity_report.json")
    evidence = read_json(QA / "evidence_gate_report.json")
    temporal = read_json(QA / "temporal_source_integrity_report.json")
    reproducibility = read_json(QA / "phenology_stage_a_reproducibility_report.json")
    lag_exists = file_exists("outputs/phenology/qa/transient_lag_compatibility.csv")
    crossing_exists = file_exists("outputs/phenology/qa/year_crossing_audit.csv")
    truncation_exists = file_exists("outputs/phenology/qa/left_truncation_2016.csv")
    schema_exists = file_exists("outputs/phenology/qa/stage_a_schema.json")

    forbidden_existing = []
    for root in [ROOT / "data" / "processed" / "phenology", ROOT / "outputs" / "phenology"]:
        if root.exists():
            forbidden_existing.extend(str(path.relative_to(ROOT)) for path in root.rglob("*") if path.is_file() and path.name in FORBIDDEN_OUTPUT_NAMES)

    truncation_pass = False
    if truncation_exists:
        import pandas as pd

        truncation = pd.read_csv(ROOT / "outputs" / "phenology" / "qa" / "left_truncation_2016.csv")
        truncation_pass = (
            len(truncation) > 0
            and (truncation["DECISION_STATUS"] == "PENDING_EVIDENCE_FREEZE").all()
            and (truncation["IMPUTATION_USED"].astype(str).str.upper().isin(["FALSE", "0"])).all()
        )

    crossing_pass = False
    if crossing_exists:
        import pandas as pd

        crossing = pd.read_csv(ROOT / "outputs" / "phenology" / "qa" / "year_crossing_audit.csv")
        crossing_pass = len(crossing) > 0 and not crossing["ATTRIBUTION_STATUS"].astype(str).str.contains("CAUSAL", case=False, na=False).any()

    g0 = upstream["status"] == "PASS" and not protected_diff() and not protected_status()
    g1 = evidence["status"] == "PASS"
    g2 = no_snoop["status"] == "PASS"
    g3 = temporal["status"] == "PASS"
    g4 = truncation_pass
    g5 = crossing_pass
    g6 = g2 and not forbidden_existing and not protected_diff() and not protected_status()
    g7 = reproducibility["status"] == "PASS" and reproducibility["deterministic_core_outputs_identical"] is True and schema_exists
    gates = {
        "G0_UPSTREAM_FREEZE_INTEGRITY": "PASS" if g0 else "FAIL",
        "G1_EVIDENCE_REGISTRY_PROVENANCE": "PASS" if g1 else "FAIL",
        "G2_NO_OUTCOME_DRIVEN_SELECTION": "PASS" if g2 else "FAIL",
        "G3_TEMPORAL_SOURCE_INTEGRITY": "PASS" if g3 else "FAIL",
        "G4_LEFT_TRUNCATION_AUDIT_COMPLETENESS": "PASS" if g4 else "FAIL",
        "G5_YEAR_CROSSING_AUDIT_COMPLETENESS": "PASS" if g5 else "FAIL",
        "G6_STAGE_SCOPE_FIREWALL": "PASS" if g6 else "FAIL",
        "G7_DETERMINISTIC_STAGE_A_CORE_OUTPUTS": "PASS" if g7 else "FAIL",
    }
    report = {
        "stage": "PHENOLOGY_MASTER_v1_STAGE_A",
        "gates": gates,
        "forbidden_stage_b_outputs": forbidden_existing,
        "protected_diff_vs_base": protected_diff(),
        "protected_working_tree_status": protected_status(),
        "row_counts": {
            "evidence_registry": count_csv_rows("data/processed/phenology/phenology_evidence_registry.csv"),
            "temporal_monthly": count_csv_rows("data/processed/phenology/temporal_structure_monthly.csv"),
            "temporal_summary": count_csv_rows("data/processed/phenology/temporal_structure_summary.csv"),
            "transient_lag": count_csv_rows("outputs/phenology/qa/transient_lag_compatibility.csv") if lag_exists else 0,
            "year_crossing": count_csv_rows("outputs/phenology/qa/year_crossing_audit.csv") if crossing_exists else 0,
            "left_truncation": count_csv_rows("outputs/phenology/qa/left_truncation_2016.csv") if truncation_exists else 0,
        },
        "status": "PASS" if all(value == "PASS" for value in gates.values()) else "FAIL",
    }
    write_json(QA / "stage_a_gate_report.json", report)
    return report


def write_readiness(gate_report: dict[str, Any]) -> None:
    evidence = read_json(QA / "evidence_gate_report.json")
    temporal = read_json(QA / "temporal_source_integrity_report.json")
    no_snoop = read_json(QA / "no_outcome_snooping_audit.json")
    reproducibility = read_json(QA / "phenology_stage_a_reproducibility_report.json")
    execution = "PASS" if gate_report["status"] == "PASS" else "FAIL"
    text = f"""# PHENOLOGY MASTER v1 - Stage A Readiness

STAGE_A_EXECUTION: {execution}
STAGE_A_CONCLUSION: {"PASS_FOR_DIRECTOR_REVIEW" if execution == "PASS" else "HOLD"}
EVIDENCE_REGISTRY_INTEGRITY: {evidence["status"]}
TEMPORAL_AUDIT: {"PASS" if temporal["status"] == "PASS" else "FAIL"}
NO_OUTCOME_SNOOPING: {no_snoop["status"]}
UPSTREAM_FREEZE: {gate_report["gates"]["G0_UPSTREAM_FREEZE_INTEGRITY"]}
TWO_RUN_REPRODUCIBILITY: {reproducibility["status"]}
EVIDENCE_FREEZE: HOLD_PENDING_DIRECTOR_FULLTEXT_REVIEW
EXPOSURE_BUILD: BLOCKED
ECONOMETRICS: BLOCKED
NEXT_ACTION: DIRECTOR_REVIEW_STAGE_A

Stage A generated registry-ingestion and temporal-structure diagnostics only. No final crop architecture, phenology window, climate exposure, econometric result, ENSO scenario, or optimization output was created.
"""
    READINESS.parent.mkdir(parents=True, exist_ok=True)
    READINESS.write_text(text, encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit PHENOLOGY MASTER v1 Stage A scope and gates.")
    parser.parse_args()
    no_snoop = scan_processing_code()
    gate_report = aggregate_gates(no_snoop)
    write_readiness(gate_report)
    print(json.dumps({"stage": "PHENOLOGY_MASTER_v1_STAGE_A", "status": gate_report["status"]}, sort_keys=True))
    return 0 if gate_report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
