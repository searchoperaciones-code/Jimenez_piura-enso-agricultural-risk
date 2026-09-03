"""Build and audit the frozen D0 transient campaign outcome master."""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import io
import json
import subprocess
import sys
from collections import Counter, defaultdict
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_BRANCH = "phase/d0-transient-campaign-outcome-master-v1"
JOINT_C0_SCIENTIFIC_BASE_SHA = "fca5d6e519cdff764d1ca53791ae1829ef29aa00"
R0H_HARDENING_SHA = "a50702dbf6a2dc0037e28e0b5ae4ddd8a9c182e5"
AUTHORIZED_D0_PARENT_SHA = "a50702dbf6a2dc0037e28e0b5ae4ddd8a9c182e5"
D0_SCIENTIFIC_CONTRACT_VERSION = "v1"
D0_LINEAGE_CONTRACT_VERSION = "R0H_COMPAT_V1"
FINAL_STATUS = "PASS_FOR_INDEPENDENT_D0_OUTCOME_MASTER_AUDIT"
NEXT_GATE = "INDEPENDENT_D0_OUTCOME_MASTER_AUDIT_BEFORE_FREEZE"

RAW_PATH = ROOT / "data/raw/Formato_dataset_productos_dra__ (2).csv"
MASTER_PATH = ROOT / "data/processed/outcomes/transient_campaign_outcomes_master.csv"
LEDGER_PATH = ROOT / "outputs/outcome/D0_TRANSIENT_OUTCOME_EXCLUSION_LEDGER.csv"
AUDIT_PATH = ROOT / "outputs/outcome/D0_TRANSIENT_OUTCOME_AUDIT.csv"
REPORT_PATH = ROOT / "outputs/outcome/D0_TRANSIENT_OUTCOME_REPORT.md"
CONFIG_PATH = ROOT / "config/outcome/transient_campaign_outcome_v1.json"
SCRIPT_PATH = ROOT / "scripts/d0_transient_campaign_outcome_master.py"
TEST_PATH = ROOT / "tests/test_d0_transient_campaign_outcome_master.py"

RAW_SHA256 = "7953e95f532b97f3db1ad42dfb517dc0b5f6e98a80b1f1b0954fc1b52419c489"
MASTER_SHA256 = "9cae62fb1417fa41274f6d504515571abd428b71fecaa0d138d3b786aa538760"
LEDGER_SHA256 = "6f7efe29c49b6a1edfaf47743f0b10639a9f56995f742e7513046aff63e814d8"
FORMULA = "SUM(PRODUCCION within Aug-Jul campaign) / SUM(COSECHA within Aug-Jul campaign)"
OUTCOME_UNIT = "TM_PER_HA"
OUTCOME_CONTRACT_ID = "JOINT_C0_TRANSIENT_CAMPAIGN_YIELD_RAW_V1"
DECIMAL_PRECISION = 28

R0H_EXPECTED_DIFF_PATHS = (
    "scripts/audit_phenology_stage_a.py",
    "scripts/phenology_stage_a.py",
    "tests/test_phenology_json_serialization.py",
)

FROZEN_SCIENTIFIC_PREFIXES = (
    "config/",
    "data/",
    "outputs/",
)

JOINT_C0_HASHES = {
    "config/joint_c0/outcome_decision_integration_v1.json": "53158bdb19d29de772f5061c0b110079500ff7a6d0b86e42b403879ed65b9899",
    "outputs/joint_c0/C0_JOINT_AUTHORIZATION_MATRIX.csv": "d33a24497625a5a2e9abd4991f5a67a3428fac5a7d269c849dc636a6b0d9abe3",
    "outputs/joint_c0/C0_JOINT_COMPATIBILITY_MATRIX.csv": "7bde825794ee80c111e45cc40715a3118295c09cdd876b34fc36c4c3afa98e4b",
    "outputs/joint_c0/C0_JOINT_EVIDENCE_REGISTRY.csv": "ea9694aee2ac65f70b168b0893e091623b5b6bdb76cf4087f41ba44374d8a4a0",
    "outputs/joint_c0/C0_JOINT_REPORT.md": "92e4902b0f5ee4cc8a4ef4411ef741efe79399a7a83398cbe177c7b4fa1ad582",
    "scripts/c0_joint_integration_preflight.py": "769af295d8df4fae353cfd62f0ed7c608fa8ba9c4924d5cad68e6f6ce80ecff9",
    "tests/test_c0_joint_integration.py": "ce0316d19e667985351b86a011ffaca35023108699d51c85d638b7d99381ef80",
}

RICE_DISTRICTS = (
    "200101", "200104", "200105", "200107", "200108", "200109", "200110", "200111",
    "200114", "200201", "200203", "200204", "200205", "200206", "200207", "200208",
    "200209", "200210", "200302", "200304", "200305", "200306", "200401", "200402",
    "200405", "200406", "200407", "200408", "200409", "200410", "200502", "200503",
    "200504", "200505", "200506", "200601", "200603", "200605", "200607", "200608",
    "200801", "200802", "200803", "200804", "200805", "200806",
)

MAD_DISTRICTS = (
    "200101", "200104", "200105", "200107", "200108", "200109", "200110", "200111",
    "200114", "200201", "200202", "200203", "200204", "200205", "200206", "200207",
    "200208", "200209", "200210", "200301", "200302", "200303", "200304", "200305",
    "200306", "200307", "200308", "200401", "200402", "200403", "200404", "200405",
    "200406", "200407", "200408", "200409", "200410", "200502", "200503", "200504",
    "200505", "200506", "200507", "200601", "200603", "200605", "200606", "200607",
    "200608", "200801", "200802", "200803", "200804", "200805", "200806",
)

CROPS = {
    "14010020000": {"crop_std": "ARROZ", "districts": RICE_DISTRICTS, "expected_valid": 294},
    "14010070000": {"crop_std": "MAIZ AMARILLO DURO", "districts": MAD_DISTRICTS, "expected_valid": 352},
}
CAMPAIGN_START_YEARS = tuple(range(2016, 2023))
CAMPAIGNS = tuple(f"{year}/{year + 1}" for year in CAMPAIGN_START_YEARS)

MASTER_COLUMNS = [
    "CROP_CODE", "CROP_STD", "UBIGEO", "DISTRICT_NAME", "CAMPAIGN",
    "CAMPAIGN_START_YEAR", "CAMPAIGN_END_YEAR", "CAMPAIGN_START_YEARMONTH",
    "CAMPAIGN_END_YEARMONTH", "EXPECTED_MONTHS_N", "SOURCE_MONTHS_PRESENT_N",
    "SOURCE_ROWS_N", "CAMPAIGN_PRODUCCION_TM", "CAMPAIGN_COSECHA_HA",
    "TRANSIENT_CAMPAIGN_YIELD_RAW", "OUTCOME_UNIT", "OUTCOME_VALID_FLAG",
    "EXCLUSION_REASON", "ZERO_DENOMINATOR_FLAG", "NO_SOURCE_ROWS_FLAG",
    "MISSING_NUMERATOR_FLAG", "MISSING_DENOMINATOR_FLAG",
    "SILENT_MISSING_TO_ZERO_USED", "OUTCOME_CONTRACT_ID",
]

LEDGER_COLUMNS = [
    "CROP_CODE", "CROP_STD", "UBIGEO", "DISTRICT_NAME", "CAMPAIGN",
    "SOURCE_MONTHS_PRESENT_N", "SOURCE_ROWS_N", "CAMPAIGN_PRODUCCION_TM",
    "CAMPAIGN_COSECHA_HA", "EXCLUSION_REASON", "ZERO_DENOMINATOR_FLAG",
    "NO_SOURCE_ROWS_FLAG", "MISSING_NUMERATOR_FLAG", "MISSING_DENOMINATOR_FLAG", "NOTES",
]

AUDIT_COLUMNS = ["CHECK_ID", "DOMAIN", "EXPECTED", "OBSERVED", "STATUS", "CRITICALITY", "NOTES"]

AUTHORIZED_SCOPE = {
    "data/processed/outcomes/transient_campaign_outcomes_master.csv",
    "outputs/outcome/D0_TRANSIENT_OUTCOME_EXCLUSION_LEDGER.csv",
    "outputs/outcome/D0_TRANSIENT_OUTCOME_AUDIT.csv",
    "outputs/outcome/D0_TRANSIENT_OUTCOME_REPORT.md",
    "config/outcome/transient_campaign_outcome_v1.json",
    "scripts/d0_transient_campaign_outcome_master.py",
    "tests/test_d0_transient_campaign_outcome_master.py",
}

EXPECTED_REASON_COUNTS = {
    "14010020000": {"ZERO_DENOMINATOR": 8, "INCOMPLETE_CAMPAIGN_NO_SOURCE_ROWS": 20},
    "14010070000": {"ZERO_DENOMINATOR": 11, "INCOMPLETE_CAMPAIGN_NO_SOURCE_ROWS": 22},
}


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=ROOT, check=True, capture_output=True, text=True, encoding="utf-8",
    )
    return result.stdout.strip()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def bool_text(value: bool) -> str:
    return "TRUE" if value else "FALSE"


def decimal_text(value: Decimal | None) -> str:
    if value is None:
        return ""
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def parse_decimal(value: str) -> Decimal | None:
    stripped = value.strip()
    return Decimal(stripped) if stripped else None


def csv_bytes(columns: list[str], rows: list[dict[str, Any]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def json_bytes(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def campaign_months(start_year: int) -> tuple[int, ...]:
    return tuple(
        [start_year * 100 + month for month in range(8, 13)]
        + [(start_year + 1) * 100 + month for month in range(1, 8)]
    )


def campaign_start_from_yearmonth(year_month: int) -> int:
    year, month = divmod(year_month, 100)
    if month < 1 or month > 12:
        raise ValueError(f"invalid source year-month: {year_month}")
    return year if month >= 8 else year - 1


def load_source() -> tuple[dict[tuple[str, str, int], dict[str, Any]], dict[str, str], dict[str, int]]:
    if sha256_file(RAW_PATH) != RAW_SHA256:
        raise ValueError("raw source SHA-256 changed")

    universe_codes = set(RICE_DISTRICTS) | set(MAD_DISTRICTS)
    names: dict[str, set[str]] = defaultdict(set)
    groups: dict[tuple[str, str, int], dict[str, Any]] = defaultdict(
        lambda: {
            "months": set(), "rows": 0, "production": Decimal(0), "production_seen": False,
            "harvest": Decimal(0), "harvest_seen": False, "production_zero_cells": 0,
            "harvest_zero_cells": 0,
        }
    )
    source_counts = {"target_rows": 0, "production_zero_cells": 0, "harvest_zero_cells": 0}

    with RAW_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"DISTRITO", "UBIGEO", "MES", "COD_CULTIVO", "PRODUCCION", "COSECHA"}
        if not required <= set(reader.fieldnames or []):
            raise ValueError("raw source schema is missing D0 fields")
        for row in reader:
            ubigeo = row["UBIGEO"].strip()
            if ubigeo in universe_codes:
                names[ubigeo].add(row["DISTRITO"].strip())

            crop_code = row["COD_CULTIVO"].strip()
            if crop_code not in CROPS or ubigeo not in CROPS[crop_code]["districts"]:
                continue
            year_month = int(row["MES"])
            start_year = campaign_start_from_yearmonth(year_month)
            if start_year not in CAMPAIGN_START_YEARS:
                continue

            group = groups[(crop_code, ubigeo, start_year)]
            group["months"].add(year_month)
            group["rows"] += 1
            source_counts["target_rows"] += 1

            production = parse_decimal(row["PRODUCCION"])
            harvest = parse_decimal(row["COSECHA"])
            if production is not None:
                group["production"] += production
                group["production_seen"] = True
                if production == 0:
                    group["production_zero_cells"] += 1
                    source_counts["production_zero_cells"] += 1
            if harvest is not None:
                group["harvest"] += harvest
                group["harvest_seen"] = True
                if harvest == 0:
                    group["harvest_zero_cells"] += 1
                    source_counts["harvest_zero_cells"] += 1

    district_names: dict[str, str] = {}
    for ubigeo in sorted(universe_codes):
        observed = names.get(ubigeo, set())
        if len(observed) != 1:
            raise ValueError(f"district name is not unique for {ubigeo}: {sorted(observed)}")
        district_names[ubigeo] = next(iter(observed))

    duplicate_month_groups = [
        key for key, group in groups.items() if group["rows"] != len(group["months"])
    ]
    if duplicate_month_groups:
        raise ValueError(f"duplicate source district-crop-month keys: {duplicate_month_groups[:5]}")
    return groups, district_names, source_counts


def exclusion_reason(group: dict[str, Any] | None) -> str:
    if group is None or group["rows"] == 0:
        return "INCOMPLETE_CAMPAIGN_NO_SOURCE_ROWS"
    if not group["production_seen"]:
        return "MISSING_NUMERATOR"
    if not group["harvest_seen"]:
        return "MISSING_DENOMINATOR"
    if group["harvest"] == 0:
        return "ZERO_DENOMINATOR"
    if group["harvest"] < 0 or group["production"] < 0:
        return "OTHER"
    return ""


def ledger_note(reason: str) -> str:
    return {
        "ZERO_DENOMINATOR": (
            "Source rows and numeric fields are observed; summed COSECHA is zero; row preserved without yield."
        ),
        "INCOMPLETE_CAMPAIGN_NO_SOURCE_ROWS": (
            "No source rows exist for the frozen key; aggregates remain missing and the row is preserved."
        ),
        "MISSING_NUMERATOR": "Source rows exist but PRODUCCION is entirely missing; no imputation is used.",
        "MISSING_DENOMINATOR": "Source rows exist but COSECHA is entirely missing; no imputation is used.",
        "OTHER": "Observed negative aggregate is outside the frozen validity rule; row is preserved.",
    }[reason]


def build_records() -> tuple[list[dict[str, str]], list[dict[str, str]], dict[str, Any]]:
    groups, district_names, source_counts = load_source()
    master: list[dict[str, str]] = []
    ledger: list[dict[str, str]] = []

    for crop_code, crop in CROPS.items():
        for ubigeo in crop["districts"]:
            for start_year in CAMPAIGN_START_YEARS:
                group = groups.get((crop_code, ubigeo, start_year))
                reason = exclusion_reason(group)
                source_rows = 0 if group is None else int(group["rows"])
                source_months = 0 if group is None else len(group["months"])
                production = None if group is None or not group["production_seen"] else group["production"]
                harvest = None if group is None or not group["harvest_seen"] else group["harvest"]
                valid = reason == ""
                outcome: Decimal | None = None
                if valid:
                    with localcontext() as context:
                        context.prec = DECIMAL_PRECISION
                        context.rounding = ROUND_HALF_EVEN
                        outcome = production / harvest

                row = {
                    "CROP_CODE": crop_code,
                    "CROP_STD": crop["crop_std"],
                    "UBIGEO": ubigeo,
                    "DISTRICT_NAME": district_names[ubigeo],
                    "CAMPAIGN": f"{start_year}/{start_year + 1}",
                    "CAMPAIGN_START_YEAR": str(start_year),
                    "CAMPAIGN_END_YEAR": str(start_year + 1),
                    "CAMPAIGN_START_YEARMONTH": str(start_year * 100 + 8),
                    "CAMPAIGN_END_YEARMONTH": str((start_year + 1) * 100 + 7),
                    "EXPECTED_MONTHS_N": "12",
                    "SOURCE_MONTHS_PRESENT_N": str(source_months),
                    "SOURCE_ROWS_N": str(source_rows),
                    "CAMPAIGN_PRODUCCION_TM": decimal_text(production),
                    "CAMPAIGN_COSECHA_HA": decimal_text(harvest),
                    "TRANSIENT_CAMPAIGN_YIELD_RAW": decimal_text(outcome),
                    "OUTCOME_UNIT": OUTCOME_UNIT,
                    "OUTCOME_VALID_FLAG": bool_text(valid),
                    "EXCLUSION_REASON": reason,
                    "ZERO_DENOMINATOR_FLAG": bool_text(reason == "ZERO_DENOMINATOR"),
                    "NO_SOURCE_ROWS_FLAG": bool_text(reason == "INCOMPLETE_CAMPAIGN_NO_SOURCE_ROWS"),
                    "MISSING_NUMERATOR_FLAG": bool_text(reason == "MISSING_NUMERATOR"),
                    "MISSING_DENOMINATOR_FLAG": bool_text(reason == "MISSING_DENOMINATOR"),
                    "SILENT_MISSING_TO_ZERO_USED": "FALSE",
                    "OUTCOME_CONTRACT_ID": OUTCOME_CONTRACT_ID,
                }
                master.append(row)
                if not valid:
                    ledger.append(
                        {
                            "CROP_CODE": crop_code,
                            "CROP_STD": crop["crop_std"],
                            "UBIGEO": ubigeo,
                            "DISTRICT_NAME": district_names[ubigeo],
                            "CAMPAIGN": row["CAMPAIGN"],
                            "SOURCE_MONTHS_PRESENT_N": row["SOURCE_MONTHS_PRESENT_N"],
                            "SOURCE_ROWS_N": row["SOURCE_ROWS_N"],
                            "CAMPAIGN_PRODUCCION_TM": row["CAMPAIGN_PRODUCCION_TM"],
                            "CAMPAIGN_COSECHA_HA": row["CAMPAIGN_COSECHA_HA"],
                            "EXCLUSION_REASON": reason,
                            "ZERO_DENOMINATOR_FLAG": row["ZERO_DENOMINATOR_FLAG"],
                            "NO_SOURCE_ROWS_FLAG": row["NO_SOURCE_ROWS_FLAG"],
                            "MISSING_NUMERATOR_FLAG": row["MISSING_NUMERATOR_FLAG"],
                            "MISSING_DENOMINATOR_FLAG": row["MISSING_DENOMINATOR_FLAG"],
                            "NOTES": ledger_note(reason),
                        }
                    )

    diagnostics = summarize(master, ledger, district_names, source_counts)
    enforce_expected_diagnostics(diagnostics)
    return master, ledger, diagnostics


def summarize(
    master: list[dict[str, str]], ledger: list[dict[str, str]],
    district_names: dict[str, str], source_counts: dict[str, int],
) -> dict[str, Any]:
    by_crop: dict[str, dict[str, Any]] = {}
    for crop_code, crop in CROPS.items():
        rows = [row for row in master if row["CROP_CODE"] == crop_code]
        invalid = [row for row in rows if row["OUTCOME_VALID_FLAG"] == "FALSE"]
        by_crop[crop_code] = {
            "crop_std": crop["crop_std"],
            "districts_n": len({row["UBIGEO"] for row in rows}),
            "potential_rows": len(rows),
            "valid_rows": sum(row["OUTCOME_VALID_FLAG"] == "TRUE" for row in rows),
            "invalid_rows": len(invalid),
            "reason_counts": dict(sorted(Counter(row["EXCLUSION_REASON"] for row in invalid).items())),
        }

    keys = [(row["CROP_CODE"], row["UBIGEO"], row["CAMPAIGN"]) for row in master]
    valid_rows = [row for row in master if row["OUTCOME_VALID_FLAG"] == "TRUE"]
    invalid_rows = [row for row in master if row["OUTCOME_VALID_FLAG"] == "FALSE"]
    return {
        "by_crop": by_crop,
        "campaigns": list(CAMPAIGNS),
        "campaigns_n": len(CAMPAIGNS),
        "district_names": district_names,
        "duplicate_keys_n": len(keys) - len(set(keys)),
        "extreme_2017_potential_rows": sum(row["CAMPAIGN_END_YEAR"] == "2017" for row in master),
        "extreme_2017_valid_rows": sum(row["CAMPAIGN_END_YEAR"] == "2017" for row in valid_rows),
        "extreme_2023_potential_rows": sum(row["CAMPAIGN_END_YEAR"] == "2023" for row in master),
        "extreme_2023_valid_rows": sum(row["CAMPAIGN_END_YEAR"] == "2023" for row in valid_rows),
        "invalid_rows": len(invalid_rows),
        "invalid_yield_nonblank_n": sum(bool(row["TRANSIENT_CAMPAIGN_YIELD_RAW"]) for row in invalid_rows),
        "ledger_rows": len(ledger),
        "master_rows": len(master),
        "missing_denominator_rows": sum(row["MISSING_DENOMINATOR_FLAG"] == "TRUE" for row in master),
        "missing_numerator_rows": sum(row["MISSING_NUMERATOR_FLAG"] == "TRUE" for row in master),
        "no_source_aggregate_nonblank_n": sum(
            bool(row["CAMPAIGN_PRODUCCION_TM"] or row["CAMPAIGN_COSECHA_HA"])
            for row in master if row["NO_SOURCE_ROWS_FLAG"] == "TRUE"
        ),
        "other_invalid_rows": sum(row["EXCLUSION_REASON"] == "OTHER" for row in master),
        "source_counts": source_counts,
        "valid_nonpositive_denominator_n": sum(
            Decimal(row["CAMPAIGN_COSECHA_HA"]) <= 0 for row in valid_rows
        ),
        "valid_rows": len(valid_rows),
    }


def enforce_expected_diagnostics(diagnostics: dict[str, Any]) -> None:
    expected = {
        "14010020000": {"districts_n": 46, "potential_rows": 322, "valid_rows": 294, "invalid_rows": 28},
        "14010070000": {"districts_n": 55, "potential_rows": 385, "valid_rows": 352, "invalid_rows": 33},
    }
    if diagnostics["master_rows"] != 707 or diagnostics["valid_rows"] != 646:
        raise ValueError("D0 complete-universe totals differ from the frozen contract")
    if diagnostics["invalid_rows"] != 61 or diagnostics["ledger_rows"] != 61:
        raise ValueError("D0 invalid-row reconciliation failed")
    if diagnostics["duplicate_keys_n"] != 0:
        raise ValueError("duplicate D0 master keys")
    if diagnostics["missing_numerator_rows"] or diagnostics["missing_denominator_rows"]:
        raise ValueError("unexpected missing aggregate in current raw source")
    if diagnostics["other_invalid_rows"]:
        raise ValueError("unexpected D0 invalidity category")
    if diagnostics["valid_nonpositive_denominator_n"] or diagnostics["invalid_yield_nonblank_n"]:
        raise ValueError("D0 denominator/yield validity firewall failed")
    if diagnostics["no_source_aggregate_nonblank_n"]:
        raise ValueError("no-source row was encoded as a numeric aggregate")
    for crop_code, expected_counts in expected.items():
        observed = diagnostics["by_crop"][crop_code]
        for key, value in expected_counts.items():
            if observed[key] != value:
                raise ValueError(f"{crop_code} {key} changed: {observed[key]} != {value}")
        if observed["reason_counts"] != EXPECTED_REASON_COUNTS[crop_code]:
            raise ValueError(f"{crop_code} exclusion reasons changed")


def audit_row(
    check_id: str, domain: str, expected: Any, observed: Any, passed: bool,
    notes: str, criticality: str = "CRITICAL",
) -> dict[str, str]:
    def display(value: Any) -> str:
        if isinstance(value, bool):
            return bool_text(value)
        if isinstance(value, (list, tuple, dict)):
            return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return str(value)

    return {
        "CHECK_ID": check_id,
        "DOMAIN": domain,
        "EXPECTED": display(expected),
        "OBSERVED": display(observed),
        "STATUS": "PASS" if passed else "FAIL",
        "CRITICALITY": criticality,
        "NOTES": notes,
    }


def build_audit_rows(master: list[dict[str, str]], diagnostics: dict[str, Any]) -> list[dict[str, str]]:
    rice = diagnostics["by_crop"]["14010020000"]
    mad = diagnostics["by_crop"]["14010070000"]
    master_fields = set(MASTER_COLUMNS)
    climate_fields = sorted(field for field in master_fields if field.startswith(("RAIN", "TMAX", "TMIN")))
    price_fields = sorted(field for field in master_fields if "PRICE" in field or "PRECIO" in field)
    a1_a2_fields = sorted(field for field in master_fields if "A1" in field or "A2" in field)
    valid = [row for row in master if row["OUTCOME_VALID_FLAG"] == "TRUE"]
    formula_exact = all(
        Decimal(row["TRANSIENT_CAMPAIGN_YIELD_RAW"])
        == divide_decimal(Decimal(row["CAMPAIGN_PRODUCCION_TM"]), Decimal(row["CAMPAIGN_COSECHA_HA"]))
        for row in valid
    )

    lineage = lineage_snapshot()
    joint_c0_resolved = git("rev-parse", f"{JOINT_C0_SCIENTIFIC_BASE_SHA}^{{commit}}")
    checks = [
        ("D0-L001", "JOINT_C0_SCIENTIFIC_BASE", JOINT_C0_SCIENTIFIC_BASE_SHA, joint_c0_resolved, joint_c0_resolved == JOINT_C0_SCIENTIFIC_BASE_SHA, "Frozen scientific base."),
        ("D0-L002", "R0H_AUTHORIZED_PARENT", AUTHORIZED_D0_PARENT_SHA, lineage["r0h_sha"], lineage["r0h_sha"] == R0H_HARDENING_SHA == AUTHORIZED_D0_PARENT_SHA, "Authorized reproducibility hardening is the exact D0 execution base."),
        ("D0-L003", "R0H_DIRECT_PARENT_RELATION", [JOINT_C0_SCIENTIFIC_BASE_SHA], lineage["r0h_parent_shas"], lineage["r0h_parent_shas"] == [JOINT_C0_SCIENTIFIC_BASE_SHA], "Joint C0 is the sole direct parent of R0H."),
        ("D0-L004", "R0H_DIFF_SCOPE", list(R0H_EXPECTED_DIFF_PATHS), lineage["r0h_diff_paths"], lineage["r0h_diff_paths"] == list(R0H_EXPECTED_DIFF_PATHS), "R0H contains only the authorized cross-platform hardening paths."),
        ("D0-L005", "CURRENT_HEAD_EXACT", AUTHORIZED_D0_PARENT_SHA, lineage["head"], lineage["head"] == AUTHORIZED_D0_PARENT_SHA, "Exact authorized execution base; descendants are rejected."),
        ("D0-L006", "R0H_SCIENTIFIC_CONTENT_CHANGE", False, bool(lineage["r0h_scientific_paths"]), not lineage["r0h_scientific_paths"], "No scientific data, output, or configuration path changed."),
        ("D0-002", "RAW_SOURCE_PATH", RAW_PATH.relative_to(ROOT).as_posix(), RAW_PATH.relative_to(ROOT).as_posix(), True, "Authorized local raw source."),
        ("D0-003", "RAW_SOURCE_SHA256", RAW_SHA256, sha256_file(RAW_PATH), sha256_file(RAW_PATH) == RAW_SHA256, "Raw bytes are immutable."),
        ("D0-004", "CROP_CODES", sorted(CROPS), sorted({row["CROP_CODE"] for row in master}), sorted({row["CROP_CODE"] for row in master}) == sorted(CROPS), "Rice and MAD only."),
        ("D0-005", "CAMPAIGN_SET", list(CAMPAIGNS), sorted({row["CAMPAIGN"] for row in master}), sorted({row["CAMPAIGN"] for row in master}) == list(CAMPAIGNS), "Seven Aug-Jul campaigns."),
        ("D0-006", "RICE_DISTRICTS", 46, rice["districts_n"], rice["districts_n"] == 46, "Frozen universe."),
        ("D0-007", "MAD_DISTRICTS", 55, mad["districts_n"], mad["districts_n"] == 55, "Frozen universe."),
        ("D0-008", "TOTAL_POTENTIAL_ROWS", 707, diagnostics["master_rows"], diagnostics["master_rows"] == 707, "Invalid rows are retained."),
        ("D0-009", "RICE_POTENTIAL_ROWS", 322, rice["potential_rows"], rice["potential_rows"] == 322, "46 x 7."),
        ("D0-010", "MAD_POTENTIAL_ROWS", 385, mad["potential_rows"], mad["potential_rows"] == 385, "55 x 7."),
        ("D0-011", "RICE_VALID_ROWS", 294, rice["valid_rows"], rice["valid_rows"] == 294, "Pre-complete-case outcomes."),
        ("D0-012", "MAD_VALID_ROWS", 352, mad["valid_rows"], mad["valid_rows"] == 352, "Pre-complete-case outcomes."),
        ("D0-013", "TOTAL_VALID_ROWS", 646, diagnostics["valid_rows"], diagnostics["valid_rows"] == 646, "No outcome-based redesign."),
        ("D0-014", "RICE_INVALID_ROWS", 28, rice["invalid_rows"], rice["invalid_rows"] == 28, "Rows preserved."),
        ("D0-015", "MAD_INVALID_ROWS", 33, mad["invalid_rows"], mad["invalid_rows"] == 33, "Rows preserved."),
        ("D0-016", "TOTAL_INVALID_ROWS", 61, diagnostics["invalid_rows"], diagnostics["invalid_rows"] == 61, "Ledger reconciliation."),
        ("D0-017", "RICE_ZERO_DENOMINATOR", 8, rice["reason_counts"].get("ZERO_DENOMINATOR", 0), rice["reason_counts"].get("ZERO_DENOMINATOR", 0) == 8, "No division by zero."),
        ("D0-018", "RICE_NO_SOURCE", 20, rice["reason_counts"].get("INCOMPLETE_CAMPAIGN_NO_SOURCE_ROWS", 0), rice["reason_counts"].get("INCOMPLETE_CAMPAIGN_NO_SOURCE_ROWS", 0) == 20, "Absence remains missing."),
        ("D0-019", "MAD_ZERO_DENOMINATOR", 11, mad["reason_counts"].get("ZERO_DENOMINATOR", 0), mad["reason_counts"].get("ZERO_DENOMINATOR", 0) == 11, "No division by zero."),
        ("D0-020", "MAD_NO_SOURCE", 22, mad["reason_counts"].get("INCOMPLETE_CAMPAIGN_NO_SOURCE_ROWS", 0), mad["reason_counts"].get("INCOMPLETE_CAMPAIGN_NO_SOURCE_ROWS", 0) == 22, "Absence remains missing."),
        ("D0-021", "MISSING_NUMERATOR", 0, diagnostics["missing_numerator_rows"], diagnostics["missing_numerator_rows"] == 0, "Explicitly supported without imputation."),
        ("D0-022", "MISSING_DENOMINATOR", 0, diagnostics["missing_denominator_rows"], diagnostics["missing_denominator_rows"] == 0, "Explicitly supported without imputation."),
        ("D0-023", "OTHER_INVALIDITY", 0, diagnostics["other_invalid_rows"], diagnostics["other_invalid_rows"] == 0, "No unexplained exclusion."),
        ("D0-024", "OUTCOME_UNIT", OUTCOME_UNIT, sorted({row["OUTCOME_UNIT"] for row in master}), {row["OUTCOME_UNIT"] for row in master} == {OUTCOME_UNIT}, "Metric tonnes per harvested hectare."),
        ("D0-025", "OUTCOME_FORMULA", FORMULA, FORMULA, formula_exact, "Ratio of campaign sums."),
        ("D0-026", "MONTHLY_YIELD_AVERAGING", False, False, True, "No monthly yield is constructed."),
        ("D0-027", "SILENT_MISSING_TO_ZERO", False, any(row["SILENT_MISSING_TO_ZERO_USED"] == "TRUE" for row in master), all(row["SILENT_MISSING_TO_ZERO_USED"] == "FALSE" for row in master), "No-source aggregates are blank."),
        ("D0-028", "CLIMATE_EXPOSURE_FIELDS", [], climate_fields, not climate_fields, "Outcome-only master."),
        ("D0-029", "PRICE_FIELDS", [], price_fields, not price_fields, "Physical outcome only."),
        ("D0-030", "A1_A2_FIELDS", [], a1_a2_fields, not a1_a2_fields, "No reference-configuration filtering."),
        ("D0-031", "EXTREME_2017_RETAINED", True, diagnostics["extreme_2017_valid_rows"] > 0, diagnostics["extreme_2017_potential_rows"] == 101 and diagnostics["extreme_2017_valid_rows"] > 0, "Campaign ending 2017 retained."),
        ("D0-032", "EXTREME_2023_RETAINED", True, diagnostics["extreme_2023_valid_rows"] > 0, diagnostics["extreme_2023_potential_rows"] == 101 and diagnostics["extreme_2023_valid_rows"] > 0, "Campaign ending 2023 retained."),
        ("D0-033", "NO_MODEL_FITTING", True, True, True, "No model or fitted result is produced."),
        ("D0-034", "NO_WATER_MODEL", True, True, True, "No hydraulic variable is used."),
        ("D0-035", "NO_OPTIMIZATION", True, True, True, "No objective or optimizer is used."),
        ("D0-036", "UNIQUE_KEYS", 0, diagnostics["duplicate_keys_n"], diagnostics["duplicate_keys_n"] == 0, "Unique crop-district-campaign rows."),
        ("D0-037", "EXCLUSION_LEDGER_ROWS", 61, diagnostics["ledger_rows"], diagnostics["ledger_rows"] == 61, "Every invalid row appears once."),
        ("D0-038", "INVALID_YIELD_NONBLANK", 0, diagnostics["invalid_yield_nonblank_n"], diagnostics["invalid_yield_nonblank_n"] == 0, "Invalid yield is missing."),
        ("D0-039", "VALID_NONPOSITIVE_DENOMINATOR", 0, diagnostics["valid_nonpositive_denominator_n"], diagnostics["valid_nonpositive_denominator_n"] == 0, "Every valid denominator is positive."),
        ("D0-040", "EXPECTED_MONTHS", 12, sorted({row["EXPECTED_MONTHS_N"] for row in master}), {row["EXPECTED_MONTHS_N"] for row in master} == {"12"}, "Calendar expectation is fixed independently of source presence."),
    ]
    return [audit_row(*check) for check in checks]


def divide_decimal(production: Decimal, harvest: Decimal) -> Decimal:
    with localcontext() as context:
        context.prec = DECIMAL_PRECISION
        context.rounding = ROUND_HALF_EVEN
        return production / harvest


def build_config(diagnostics: dict[str, Any], artifact_hashes: dict[str, str]) -> dict[str, Any]:
    district_names = diagnostics["district_names"]
    return {
        "artifact_sha256": dict(artifact_hashes),
        "authorized_d0_parent_sha": AUTHORIZED_D0_PARENT_SHA,
        "campaign_calendar": {
            "campaign_id_format": "YYYY/YYYY",
            "campaigns": list(CAMPAIGNS),
            "expected_months_n": 12,
            "first_calendar_year_months": [8, 9, 10, 11, 12],
            "second_calendar_year_months": [1, 2, 3, 4, 5, 6, 7],
            "time_basis": "AGRICULTURAL_CAMPAIGN_AUG_JUL",
        },
        "crop_contracts": {
            code: {
                "crop_std": crop["crop_std"],
                "district_universe": [
                    {"district_name": district_names[ubigeo], "ubigeo": ubigeo}
                    for ubigeo in crop["districts"]
                ],
                "districts_n": len(crop["districts"]),
                "expected_invalid_rows": len(crop["districts"]) * 7 - crop["expected_valid"],
                "expected_potential_rows": len(crop["districts"]) * 7,
                "expected_valid_rows": crop["expected_valid"],
                "expected_exclusion_reasons": EXPECTED_REASON_COUNTS[code],
            }
            for code, crop in CROPS.items()
        },
        "decimal_arithmetic": {
            "precision_significant_digits": DECIMAL_PRECISION,
            "rounding": "ROUND_HALF_EVEN",
            "serialization": "PLAIN_DECIMAL_TRAILING_FRACTIONAL_ZEROS_REMOVED",
        },
        "exclusion_taxonomy": [
            "ZERO_DENOMINATOR", "INCOMPLETE_CAMPAIGN_NO_SOURCE_ROWS",
            "MISSING_NUMERATOR", "MISSING_DENOMINATOR", "OTHER",
        ],
        "expected_counts": {"potential_rows": 707, "valid_rows": 646, "invalid_rows": 61},
        "firewalls": {
            "a1_a2_filtering_used": False,
            "climate_exposure_linkage_used": False,
            "continuous_optimization_status": "NOT_AUTHORIZED",
            "extreme_2017_removed": False,
            "extreme_2023_removed": False,
            "model_fitting_executed": False,
            "monthly_yield_averaging_used": False,
            "price_or_monetary_linkage_used": False,
            "primary_transient_econometric_exposure": "NOT_YET_SELECTED",
            "produccion_divided_by_siembra_used": False,
            "silent_missing_to_zero_used": False,
            "sown_to_harvested_mapping_executed": False,
            "water_model_status": "NOT_AUTHORIZED",
        },
        "d0_lineage_contract_version": D0_LINEAGE_CONTRACT_VERSION,
        "d0_scientific_contract_version": D0_SCIENTIFIC_CONTRACT_VERSION,
        "joint_c0": {
            "frozen_file_sha256": JOINT_C0_HASHES,
            "relationship_to_r0h": "SOLE_DIRECT_PARENT_AND_SCIENTIFIC_BASE",
            "scientific_base_sha": JOINT_C0_SCIENTIFIC_BASE_SHA,
        },
        "joint_c0_scientific_base_sha": JOINT_C0_SCIENTIFIC_BASE_SHA,
        "lineage_contract": {
            "current_head_requirement": "EXACT_AUTHORIZED_D0_PARENT_ONLY",
            "r0h_direct_parent_sha": JOINT_C0_SCIENTIFIC_BASE_SHA,
            "r0h_expected_diff_paths": list(R0H_EXPECTED_DIFF_PATHS),
            "r0h_scientific_content_change": False,
        },
        "next_gate": NEXT_GATE,
        "outcome_contract": {
            "contract_id": OUTCOME_CONTRACT_ID,
            "denominator": "SUM(COSECHA within Aug-Jul campaign)",
            "denominator_semantics": "HA_MONTHLY_HARVEST_FLOW",
            "formula": FORMULA,
            "forbidden_replacements": [
                "MEAN_MONTHLY_YIELD", "SUM_MONTHLY_YIELD", "MEDIAN_MONTHLY_YIELD",
                "CALENDAR_YEAR_YIELD", "MAX_MONTHLY_YIELD", "PRODUCCION_DIVIDED_BY_SIEMBRA",
            ],
            "numerator": "SUM(PRODUCCION within Aug-Jul campaign)",
            "observation_unit": "DISTRICT_CROP_AGRICULTURAL_CAMPAIGN",
            "outcome_unit": OUTCOME_UNIT,
            "variable": "TRANSIENT_CAMPAIGN_YIELD_RAW",
        },
        "phase": "D0_TRANSIENT_CAMPAIGN_OUTCOME_MASTER",
        "raw_source": {
            "path": RAW_PATH.relative_to(ROOT).as_posix(),
            "sha256": RAW_SHA256,
        },
        "r0h_hardening_sha": R0H_HARDENING_SHA,
        "schema_version": "1.0.0",
        "validity_rule": {
            "all_potential_rows_preserved": True,
            "missing_denominator": "INVALID_PRESERVE_ROW_DO_NOT_IMPUTE",
            "missing_numerator": "INVALID_PRESERVE_ROW_DO_NOT_IMPUTE",
            "no_source_row": "INVALID_PRESERVE_ROW_NUMERIC_AGGREGATES_MISSING",
            "numeric_zero_is_observed": True,
            "production_zero_with_positive_harvest_may_be_valid": True,
            "source_presence": "AT_LEAST_ONE_SOURCE_ROW_AND_AGGREGATE_NUMERATOR_AND_DENOMINATOR_OBSERVED",
            "valid": "SOURCE_PRESENCE_RULE_PASSES_AND_CAMPAIGN_COSECHA_HA_STRICTLY_POSITIVE",
            "zero_denominator": "INVALID_PRESERVE_ROW_NO_DIVISION_NO_EPSILON",
        },
    }


def build_report(diagnostics: dict[str, Any], artifact_hashes: dict[str, str]) -> bytes:
    rice = diagnostics["by_crop"]["14010020000"]
    mad = diagnostics["by_crop"]["14010070000"]
    lines = [
        "# D0 Transient Campaign Outcome Master", "",
        "## 1. Executive verdict", "",
        f"`D0_STATUS={FINAL_STATUS}`; `D0_FREEZE_STATUS=UNFROZEN_CANDIDATE`; `D0_SCIENTIFIC_CONTRACT_VERSION={D0_SCIENTIFIC_CONTRACT_VERSION}`; `D0_LINEAGE_CONTRACT_VERSION={D0_LINEAGE_CONTRACT_VERSION}`. The complete 707-row outcome universe is materialized with 646 valid and 61 preserved invalid rows.", "",
        "## 2. Scientific and execution lineage", "",
        f"Joint C0 `{JOINT_C0_SCIENTIFIC_BASE_SHA}` is the frozen scientific base. R0H `{R0H_HARDENING_SHA}` is its sole direct child and the exact authorized D0 execution parent. Its diff is limited to `{', '.join(R0H_EXPECTED_DIFF_PATHS)}` and `SCIENTIFIC_CONTENT_CHANGE=FALSE`. All seven Joint C0 files pass their frozen SHA-256 gate.", "",
        "## 3. Outcome contract", "",
        f"`TRANSIENT_CAMPAIGN_YIELD_RAW = {FORMULA}` with unit `{OUTCOME_UNIT}` and observation unit district x crop x agricultural campaign.", "",
        "## 4. Source-data semantics", "",
        "PRODUCCION is metric tonnes. COSECHA is monthly harvested-area flow in hectares. Numeric zero is observed; source absence and blank numeric data are not zero.", "",
        "## 5. Agricultural campaign calendar", "",
        "Each campaign runs from August of the start year through July of the end year. Every potential row records 12 expected months independently of source-row presence.", "",
        "## 6. Rice universe", "",
        f"Rice uses 46 frozen districts across seven campaigns: {rice['potential_rows']} potential, {rice['valid_rows']} valid, and {rice['invalid_rows']} invalid rows.", "",
        "## 7. MAD universe", "",
        f"MAD uses 55 frozen districts across seven campaigns: {mad['potential_rows']} potential, {mad['valid_rows']} valid, and {mad['invalid_rows']} invalid rows.", "",
        "## 8. Complete 707-row master construction", "",
        "The Cartesian product of each frozen crop-specific district universe and the seven campaigns is retained. No valid-only reduction is used.", "",
        "## 9. Production aggregation", "",
        "CAMPAIGN_PRODUCCION_TM is the sum of observed monthly PRODUCCION values within the Aug-Jul campaign. All-missing remains missing.", "",
        "## 10. Harvested-area aggregation", "",
        "CAMPAIGN_COSECHA_HA is the sum of observed monthly COSECHA flows within the same Aug-Jul campaign. It is not a stock variable.", "",
        "## 11. Yield calculation", "",
        "Yield is calculated only after numerator and denominator presence checks and only when campaign harvested area is strictly positive. No monthly yield is constructed.", "",
        "## 12. Zero denominator treatment", "",
        "The 8 Rice and 11 MAD zero-denominator rows remain in the master with missing yield and `ZERO_DENOMINATOR` exclusion status. No epsilon is used.", "",
        "## 13. No-source-row treatment", "",
        "The 20 Rice and 22 MAD no-source rows remain in the master with missing aggregates and yield. Source absence is never encoded as numeric zero.", "",
        "## 14. Missing vs zero firewall", "",
        "Observed numeric zero is preserved as data. Missing numerator and missing denominator are explicit supported exclusions; both current counts are zero.", "",
        "## 15. Exclusion ledger", "",
        f"The exclusion ledger contains exactly {diagnostics['ledger_rows']} rows and no valid observation.", "",
        "## 16. Rice reconciliation", "",
        f"`322 = 294 + 28`; invalid reasons are {json.dumps(rice['reason_counts'], sort_keys=True)}.", "",
        "## 17. MAD reconciliation", "",
        f"`385 = 352 + 33`; invalid reasons are {json.dumps(mad['reason_counts'], sort_keys=True)}.", "",
        "## 18. 2017/2023 preservation", "",
        f"Campaigns ending 2017 and 2023 retain all 101 potential rows each, with {diagnostics['extreme_2017_valid_rows']} and {diagnostics['extreme_2023_valid_rows']} valid outcomes respectively. No extreme-year deletion occurs.", "",
        "## 19. No outcome-driven selection", "",
        "Yield magnitude, outliers, extreme years, ENSO, climate, and future model performance do not alter campaigns, districts, validity, or exclusions.", "",
        "## 20. No climate/exposure linkage", "",
        "No climate field or exposure artifact is read or merged. The primary transient econometric exposure remains not yet selected.", "",
        "## 21. No price/economic linkage", "",
        "No price, GVP, deflator, monetary value, or A1/A2 economic quantity is read or produced.", "",
        "## 22. No model fitting", "",
        "D0 creates no regression, coefficient, standard error, p-value, R-squared, model selection, cross-validation, forecast, scenario, prediction, VaR, CVaR, or optimization result.", "",
        "## 23. Remaining pre-estimation gates", "",
        "Primary transient exposure selection and cohort-to-campaign mapping remain separate outcome-independent gates, followed by econometric design freeze. Sown-to-harvested mapping remains downstream of econometric design and before production stress testing.", "",
        "## 24. Final D0 verdict", "",
        f"`D0_STATUS={FINAL_STATUS}`; `D0_FREEZE_STATUS=UNFROZEN_CANDIDATE`; `AUTHORIZED_D0_PARENT_SHA={AUTHORIZED_D0_PARENT_SHA}`; `D0_LINEAGE_CONTRACT_VERSION={D0_LINEAGE_CONTRACT_VERSION}`; `NEXT_GATE={NEXT_GATE}`. Artifact SHA-256: master `{artifact_hashes[MASTER_PATH.relative_to(ROOT).as_posix()]}`, ledger `{artifact_hashes[LEDGER_PATH.relative_to(ROOT).as_posix()]}`, audit `{artifact_hashes[AUDIT_PATH.relative_to(ROOT).as_posix()]}`, config `{artifact_hashes[CONFIG_PATH.relative_to(ROOT).as_posix()]}`.", "",
    ]
    return "\n".join(lines).encode("utf-8")


def build_output_bytes() -> tuple[dict[Path, bytes], dict[str, Any], dict[str, Any]]:
    master, ledger, diagnostics = build_records()
    master_payload = csv_bytes(MASTER_COLUMNS, master)
    ledger_payload = csv_bytes(LEDGER_COLUMNS, ledger)
    audit_rows = build_audit_rows(master, diagnostics)
    audit_payload = csv_bytes(AUDIT_COLUMNS, audit_rows)

    artifact_hashes = {
        MASTER_PATH.relative_to(ROOT).as_posix(): sha256_bytes(master_payload),
        LEDGER_PATH.relative_to(ROOT).as_posix(): sha256_bytes(ledger_payload),
        AUDIT_PATH.relative_to(ROOT).as_posix(): sha256_bytes(audit_payload),
    }
    config = build_config(diagnostics, artifact_hashes)
    config_payload = json_bytes(config)
    artifact_hashes[CONFIG_PATH.relative_to(ROOT).as_posix()] = sha256_bytes(config_payload)
    report_payload = build_report(diagnostics, artifact_hashes)

    outputs = {
        MASTER_PATH: master_payload,
        LEDGER_PATH: ledger_payload,
        AUDIT_PATH: audit_payload,
        REPORT_PATH: report_payload,
        CONFIG_PATH: config_payload,
    }
    return outputs, config, diagnostics


def lineage_snapshot() -> dict[str, Any]:
    r0h_diff_paths = sorted(filter(None, git(
        "diff", "--name-only", JOINT_C0_SCIENTIFIC_BASE_SHA, R0H_HARDENING_SHA,
    ).splitlines()))
    return {
        "branch": git("branch", "--show-current"),
        "head": git("rev-parse", "HEAD"),
        "r0h_sha": git("rev-parse", f"{R0H_HARDENING_SHA}^{{commit}}"),
        "r0h_parent_shas": git("show", "-s", "--format=%P", R0H_HARDENING_SHA).split(),
        "r0h_diff_paths": r0h_diff_paths,
        "r0h_scientific_paths": [
            path for path in r0h_diff_paths if path.startswith(FROZEN_SCIENTIFIC_PREFIXES)
        ],
    }


def validate_lineage_snapshot(snapshot: dict[str, Any]) -> None:
    if snapshot["branch"] != EXPECTED_BRANCH:
        raise AssertionError("wrong D0 branch")
    if snapshot["head"] != AUTHORIZED_D0_PARENT_SHA:
        raise AssertionError("HEAD is not the exact authorized D0 execution parent")
    if snapshot["r0h_sha"] != R0H_HARDENING_SHA or snapshot["r0h_sha"] != AUTHORIZED_D0_PARENT_SHA:
        raise AssertionError("R0H is not the exact authorized D0 execution parent")
    if snapshot["r0h_parent_shas"] != [JOINT_C0_SCIENTIFIC_BASE_SHA]:
        raise AssertionError("Joint C0 is not the sole direct parent of R0H")
    if snapshot["r0h_diff_paths"] != list(R0H_EXPECTED_DIFF_PATHS):
        raise AssertionError("R0H diff scope does not match the authorized hardening")
    if snapshot["r0h_scientific_paths"]:
        raise AssertionError(f"R0H changed scientific paths: {snapshot['r0h_scientific_paths']}")


def repository_identity_gate() -> dict[str, Any]:
    snapshot = lineage_snapshot()
    validate_lineage_snapshot(snapshot)
    return snapshot


def immutability_gate() -> None:
    for relative, expected in JOINT_C0_HASHES.items():
        path = ROOT / relative
        if not path.is_file() or sha256_file(path) != expected:
            raise AssertionError(f"Joint C0 frozen file changed: {relative}")
    if sha256_file(RAW_PATH) != RAW_SHA256:
        raise AssertionError("raw source changed")
    if not MASTER_PATH.is_file() or sha256_file(MASTER_PATH) != MASTER_SHA256:
        raise AssertionError("D0L scientific master changed")
    if not LEDGER_PATH.is_file() or sha256_file(LEDGER_PATH) != LEDGER_SHA256:
        raise AssertionError("D0L exclusion ledger changed")


def persistent_scope_gate(*, allow_subset: bool) -> set[str]:
    tracked = set(filter(None, git("diff", "--name-only").splitlines()))
    staged = set(filter(None, git("diff", "--cached", "--name-only").splitlines()))
    untracked = {
        line.replace("\\", "/")
        for line in git("ls-files", "--others", "--exclude-standard").splitlines()
        if line
    }
    if tracked:
        raise AssertionError(f"tracked modifications exist: {sorted(tracked)}")
    if staged:
        raise AssertionError(f"staged files exist: {sorted(staged)}")
    if allow_subset:
        if not untracked <= AUTHORIZED_SCOPE:
            raise AssertionError(f"unrelated untracked files exist: {sorted(untracked - AUTHORIZED_SCOPE)}")
    elif untracked != AUTHORIZED_SCOPE:
        raise AssertionError(f"D0 persistent scope mismatch: {sorted(untracked)}")
    return untracked


def write_outputs(outputs: dict[Path, bytes]) -> None:
    immutable = {MASTER_PATH: MASTER_SHA256, LEDGER_PATH: LEDGER_SHA256}
    for path, expected_hash in immutable.items():
        payload = outputs[path]
        if sha256_bytes(payload) != expected_hash:
            raise AssertionError(f"generated immutable scientific artifact changed: {path.relative_to(ROOT)}")
        if not path.is_file() or path.read_bytes() != payload:
            raise AssertionError(f"immutable scientific artifact differs from deterministic build: {path.relative_to(ROOT)}")
    for path in (AUDIT_PATH, REPORT_PATH, CONFIG_PATH):
        payload = outputs[path]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)


def run_preflight() -> tuple[list[str], dict[str, Any]]:
    repository_identity_gate()
    immutability_gate()
    persistent_scope_gate(allow_subset=False)
    outputs_1, config, diagnostics = build_output_bytes()
    outputs_2, _, _ = build_output_bytes()
    if outputs_1 != outputs_2:
        raise AssertionError("in-memory deterministic rebuild differs")
    for path, expected in outputs_1.items():
        if not path.is_file() or path.read_bytes() != expected:
            raise AssertionError(f"deterministic artifact mismatch: {path.relative_to(ROOT)}")
    for relative in AUTHORIZED_SCOPE:
        payload = (ROOT / relative).read_bytes()
        if payload.startswith(b"\xef\xbb\xbf") or b"\r" in payload:
            raise AssertionError(f"encoding or line ending mismatch: {relative}")
        if not payload.endswith(b"\n") or payload.endswith(b"\n\n"):
            raise AssertionError(f"final LF mismatch: {relative}")

    with MASTER_PATH.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        master = list(reader)
        if list(reader.fieldnames or []) != MASTER_COLUMNS:
            raise AssertionError("master schema changed")
    with AUDIT_PATH.open("r", encoding="utf-8", newline="") as handle:
        audit = list(csv.DictReader(handle))
    if not audit or any(row["STATUS"] != "PASS" for row in audit):
        raise AssertionError("D0 audit contains a failed check")

    forbidden_fields = {
        "RAIN", "RAIN_MM", "TMAX", "TMAX_C", "TMIN", "TMIN_C", "PRECIO", "PRECIO_CHACRA",
        "GVP", "A1", "A2", "COEFFICIENT", "P_VALUE", "R_SQUARED", "VAR", "CVAR",
    }
    if forbidden_fields & set(MASTER_COLUMNS):
        raise AssertionError("forbidden downstream field in D0 master")
    if config["outcome_contract"]["formula"] != FORMULA:
        raise AssertionError("outcome formula changed")
    if config["outcome_contract"]["outcome_unit"] != OUTCOME_UNIT:
        raise AssertionError("outcome unit changed")
    firewalls = config["firewalls"]
    if firewalls["silent_missing_to_zero_used"] or firewalls["monthly_yield_averaging_used"]:
        raise AssertionError("outcome construction firewall failed")
    if firewalls["produccion_divided_by_siembra_used"]:
        raise AssertionError("PRODUCCION divided by SIEMBRA")
    if firewalls["climate_exposure_linkage_used"] or firewalls["price_or_monetary_linkage_used"]:
        raise AssertionError("downstream linkage entered D0")
    if firewalls["a1_a2_filtering_used"] or firewalls["model_fitting_executed"]:
        raise AssertionError("outcome-driven selection or model fitting entered D0")
    if firewalls["water_model_status"] != "NOT_AUTHORIZED":
        raise AssertionError("water model authorized")
    if firewalls["continuous_optimization_status"] != "NOT_AUTHORIZED":
        raise AssertionError("optimization authorized")
    if diagnostics["master_rows"] != 707 or len(master) != 707:
        raise AssertionError("valid-only master detected")

    tree = ast.parse(SCRIPT_PATH.read_text(encoding="utf-8"))
    imported = {
        alias.name.split(".")[0]
        for node in ast.walk(tree) if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        (node.module or "").split(".")[0]
        for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
    }
    if imported & {"statsmodels", "sklearn", "linearmodels", "pymc", "cvxpy", "pyomo"}:
        raise AssertionError("model-fitting or optimization library imported")

    lines = [
        "D0_LINEAGE_CONTRACT_GATE=PASS",
        "R0H_IDENTITY_GATE=PASS",
        "R0H_DIRECT_PARENT_GATE=PASS",
        "R0H_DIFF_SCOPE_GATE=PASS",
        "R0H_SCIENTIFIC_CONTENT_CHANGE=FALSE",
        "JOINT_C0_IMMUTABILITY_GATE=PASS",
        "D0_SCIENTIFIC_ARTIFACT_IMMUTABILITY_GATE=PASS",
        "PERSISTENT_SCOPE_GATE=PASS",
        "DETERMINISM_GATE=PASS",
        "NO_OUTCOME_DRIVEN_SELECTION_GATE=PASS",
        "NO_EXPOSURE_LINKAGE_GATE=PASS",
        "NO_PRICE_LINKAGE_GATE=PASS",
        "NO_MODEL_FITTING_GATE=PASS",
        "NO_WATER_MODEL_GATE=PASS",
        "NO_OPTIMIZATION_GATE=PASS",
        f"D0_PREFLIGHT={FINAL_STATUS}",
    ]
    return lines, diagnostics


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-only", action="store_true", help="validate without writing any file")
    args = parser.parse_args()
    try:
        repository_identity_gate()
        immutability_gate()
        if not args.check_only:
            persistent_scope_gate(allow_subset=True)
            outputs, _, _ = build_output_bytes()
            write_outputs(outputs)
        lines, _ = run_preflight()
        for line in lines:
            print(line)
    except Exception as exc:  # pragma: no cover - terminal diagnostic
        print(f"D0_PREFLIGHT=FAIL: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
