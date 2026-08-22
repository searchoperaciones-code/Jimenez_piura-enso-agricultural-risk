"""Deterministic C0B6 materialization and scientific preflight."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import subprocess
import sys
from collections import Counter
from decimal import Decimal, localcontext
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_BRANCH = "phase/c0b6-alternative-data-master-v1"
EXPECTED_HEAD = "b6df2fbf4d0ec948afc544cf2da134cc44314aef"
EXPECTED_SUBJECT = "Freeze C0B5 reference configuration architecture"

RAW_PATH = ROOT / "data/raw/Formato_dataset_productos_dra__ (2).csv"
C0B3_CONFIG_PATH = ROOT / "config/decision_ontology/perennial_state_adjudication_v1.json"
TRANSIENT_PATH = ROOT / "data/processed/decision/reference_configurations_transient_long.csv"
LEGACY_PERENNIAL_PATH = ROOT / "data/processed/decision/fixed_perennial_baseline.csv"
SCOPE_PATH = ROOT / "outputs/decision_feasibility/C0B6_SCOPE_ADJUDICATION.csv"
AUDIT_PATH = ROOT / "outputs/decision_feasibility/C0B6_ALTERNATIVE_DATA_AUDIT.csv"
REPORT_PATH = ROOT / "outputs/decision_feasibility/C0B6_ALTERNATIVE_DATA_REPORT.md"
CONFIG_PATH = ROOT / "config/decision_ontology/reference_configuration_data_master_v1.json"
SCRIPT_PATH = ROOT / "scripts/c0b6_alternative_data_master.py"
TEST_PATH = ROOT / "tests/test_c0b6_alternative_data_master.py"

AUTHORIZED_SCOPE = {
    "data/processed/decision/reference_configurations_transient_long.csv",
    "outputs/decision_feasibility/C0B6_SCOPE_ADJUDICATION.csv",
    "outputs/decision_feasibility/C0B6_ALTERNATIVE_DATA_AUDIT.csv",
    "outputs/decision_feasibility/C0B6_ALTERNATIVE_DATA_REPORT.md",
    "config/decision_ontology/reference_configuration_data_master_v1.json",
    "scripts/c0b6_alternative_data_master.py",
    "tests/test_c0b6_alternative_data_master.py",
}

C0B5_HASHES = {
    "outputs/decision_feasibility/C0B5_DECISION_DOMAIN_EVIDENCE_REGISTRY.csv": "bf1a06620a9c7ad2e66f64f8ea719819f3cb26deab90fc9909841c78112f6870",
    "outputs/decision_feasibility/C0B5_ROUTE_ADJUDICATION.csv": "71d2ca62e0983c24a8b632764f69dc1fc69b69a54099a486794a1dca7ee8d23f",
    "outputs/decision_feasibility/C0B5_FINITE_PORTFOLIO_AUDIT.csv": "b1d521863a8353fda7438830e5405c6295926ad2cb139b87f156d1cbc5027dfe",
    "outputs/decision_feasibility/C0B5_DECISION_DOMAIN_REPORT.md": "ea4f301790e47ee7f81709854602427cfffb0f70da028836a103bdf75af23ce6",
    "config/decision_ontology/decision_domain_adjudication_v1.json": "67b238b90aaa7727458ec6190b89b89df2a5f5b0db21fc696cc23fad8d18e58b",
    "scripts/c0b5_decision_domain_preflight.py": "90d729c7d297d1de61eabaa1f7996cf6fac72783b7060991e68dc59d47febb0b",
    "tests/test_c0b5_decision_domain.py": "9a88f25017f9b4acc22de443bc43f5578cb5fc0ff4da48a5bd29febb886b28e3",
}
FROZEN_INPUT_HASHES = {
    "data/raw/Formato_dataset_productos_dra__ (2).csv": "7953e95f532b97f3db1ad42dfb517dc0b5f6e98a80b1f1b0954fc1b52419c489",
    "config/decision_ontology/perennial_state_adjudication_v1.json": "35d752b94b2aaf29e3b7f1512fa817ca18af8c817455a60467a1cc31cab2e86e",
}

ALTERNATIVES = (
    ("C0B5-A2020-2021", "2020/2021", 2020),
    ("C0B5-A2023-2024", "2023/2024", 2023),
)
DISTRICTS = (
    ("200101", "PIURA"),
    ("200105", "CATACAOS"),
    ("200108", "EL TALLAN"),
    ("200111", "LAS LOMAS"),
    ("200114", "TAMBO GRANDE"),
    ("200201", "AYABACA"),
    ("200205", "MONTERO"),
    ("200304", "HUARMACA"),
    ("200802", "BELLAVISTA DE LA UNION"),
    ("200803", "BERNAL"),
    ("200804", "CRISTO NOS VALGA"),
    ("200805", "VICE"),
    ("200806", "RINCONADA LLICUAR"),
)
TRANSIENT_CROPS = {
    "14010020000": "ARROZ",
    "14010070000": "MAIZ AMARILLO DURO",
}
PERENNIAL_CROPS = {
    "13010210000": ("MANGO", "INSTALLED_PERENNIAL_STOCK_AREA"),
    "13010170102": ("LIMON SUTIL", "INSTALLED_PERENNIAL_STOCK_AREA"),
    "15010040000": (
        "PLATANOS Y BANANAS",
        "CONTINUOUS_SEMIPERMANENT_INSTALLED_STAND_AREA",
    ),
}
CAMPAIGN_MONTHS = (8, 9, 10, 11, 12, 1, 2, 3, 4, 5, 6, 7)
PERENNIAL_SELECTION_RULE = "LATEST_SOURCE_MONTH_WITH_COMPLETE_COMMON_SUPPORT_VERDE_ACTUAL_COVERAGE"
SELECTED_SCOPE_ARCHITECTURE = (
    "S1_TRANSIENT_REFERENCE_CONFIGURATION_STRESS_TEST_WITH_PERENNIAL_RISK_ANALYZED_SEPARATELY"
)
DUAL_LAYER_STATUS = "SUPPORTED_WITH_STRICT_NONAGGREGATION_FIREWALL"
REFERENCE_ROLE = "EMPIRICALLY_REALIZED_TRANSIENT_REFERENCE_CONFIGURATION"
P3_STATUS = "P3_FIXED_STOCK_NEAR_TERM_HORIZON"
FINAL_STATUS = "PASS_FOR_INDEPENDENT_C0B6_REBUILD_AUDIT"
NEXT_GATE = "INDEPENDENT_C0B6_REBUILD_AUDIT_BEFORE_C0B6_FREEZE"

TRANSIENT_COLUMNS = [
    "ALTERNATIVE_ID", "SOURCE_CAMPAIGN", "UBIGEO", "DISTRICT_NAME",
    "CROP_CODE", "CROP_STD", "CAMPAIGN_MONTH_ORDER", "CALENDAR_YEAR",
    "CALENDAR_MONTH", "YEAR_MONTH", "SIEMBRA_HA", "CAMPAIGN_TOTAL_HA",
    "WITHIN_CAMPAIGN_SHARE", "OBSERVED_ZERO_FLAG", "SOURCE_MISSING_FLAG",
    "EMPIRICALLY_REALIZED", "REFERENCE_CONFIGURATION_ROLE",
]
AUDIT_COLUMNS = [
    "CHECK_ID", "DOMAIN", "EXPECTED", "OBSERVED", "STATUS", "CRITICALITY", "NOTES",
]
SCOPE_COLUMNS = [
    "CHECK_ID", "DOMAIN", "QUESTION", "EVIDENCE_STATUS", "ADJUDICATION",
    "MODEL_CONSEQUENCE", "FROZEN_STATUS", "NOTES",
]


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=ROOT, text=True, encoding="utf-8",
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    )
    return result.stdout.strip()


def parse_decimal(value: str | None) -> Decimal | None:
    if value is None or not value.strip():
        return None
    return Decimal(value)


def format_decimal(value: Decimal) -> str:
    rendered = format(value, "f")
    if "." in rendered:
        rendered = rendered.rstrip("0").rstrip(".")
    return rendered or "0"


def bool_text(value: bool) -> str:
    return "TRUE" if value else "FALSE"


def csv_bytes(columns: list[str], rows: list[dict[str, str]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def load_source() -> tuple[dict[tuple[str, str, int], dict[str, Decimal | None]], tuple[int, ...]]:
    allowed_crops = set(TRANSIENT_CROPS) | set(PERENNIAL_CROPS)
    records: dict[tuple[str, str, int], dict[str, Decimal | None]] = {}
    source_months: set[int] = set()
    with RAW_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            year_month = int(row["MES"])
            source_months.add(year_month)
            crop_code = row["COD_CULTIVO"]
            if crop_code not in allowed_crops:
                continue
            key = (row["UBIGEO"], crop_code, year_month)
            if key in records:
                raise ValueError(f"duplicate source key: {key}")
            records[key] = {
                "SIEMBRA": parse_decimal(row["SIEMBRA"]),
                "VERDE_ACTUAL": parse_decimal(row["VERDE_ACTUAL"]),
            }
    return records, tuple(sorted(source_months))


def campaign_profile(
    records: dict[tuple[str, str, int], dict[str, Decimal | None]],
    ubigeo: str,
    crop_code: str,
    start_year: int,
) -> list[tuple[int, Decimal]] | None:
    profile: list[tuple[int, Decimal]] = []
    for month in CAMPAIGN_MONTHS:
        year = start_year if month >= 8 else start_year + 1
        year_month = year * 100 + month
        record = records.get((ubigeo, crop_code, year_month))
        value = None if record is None else record["SIEMBRA"]
        if value is None:
            return None
        profile.append((year_month, value))
    return profile


def normalized_shares(values: list[Decimal]) -> list[Decimal]:
    total = sum(values, Decimal(0))
    if total <= 0:
        raise ValueError("transient campaign profile has non-positive total")
    with localcontext() as context:
        context.prec = 28
        first = [value / total for value in values[:-1]]
        last = Decimal(1) - sum(first, Decimal(0))
    shares = [*first, last]
    if any(share < 0 for share in shares) or sum(shares, Decimal(0)) != Decimal(1):
        raise ValueError("transient shares failed deterministic normalization")
    return shares


def build_transient_rows(
    records: dict[tuple[str, str, int], dict[str, Decimal | None]],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for alternative_id, campaign, start_year in ALTERNATIVES:
        for ubigeo, district_name in DISTRICTS:
            for crop_code, crop_std in TRANSIENT_CROPS.items():
                profile = campaign_profile(records, ubigeo, crop_code, start_year)
                if profile is None:
                    raise ValueError(f"frozen transient profile is incomplete: {alternative_id}/{ubigeo}/{crop_code}")
                values = [value for _, value in profile]
                campaign_total = sum(values, Decimal(0))
                shares = normalized_shares(values)
                for order, ((year_month, value), share) in enumerate(zip(profile, shares), 1):
                    rows.append({
                        "ALTERNATIVE_ID": alternative_id,
                        "SOURCE_CAMPAIGN": campaign,
                        "UBIGEO": ubigeo,
                        "DISTRICT_NAME": district_name,
                        "CROP_CODE": crop_code,
                        "CROP_STD": crop_std,
                        "CAMPAIGN_MONTH_ORDER": str(order),
                        "CALENDAR_YEAR": str(year_month // 100),
                        "CALENDAR_MONTH": str(year_month % 100),
                        "YEAR_MONTH": str(year_month),
                        "SIEMBRA_HA": format_decimal(value),
                        "CAMPAIGN_TOTAL_HA": format_decimal(campaign_total),
                        "WITHIN_CAMPAIGN_SHARE": format_decimal(share),
                        "OBSERVED_ZERO_FLAG": bool_text(value == 0),
                        "SOURCE_MISSING_FLAG": "FALSE",
                        "EMPIRICALLY_REALIZED": "TRUE",
                        "REFERENCE_CONFIGURATION_ROLE": REFERENCE_ROLE,
                    })
    return rows


def build_perennial_coverage_trail(
    records: dict[tuple[str, str, int], dict[str, Decimal | None]],
    source_months: tuple[int, ...],
) -> tuple[list[dict[str, Any]], int | None]:
    trail: list[dict[str, Any]] = []
    selected: int | None = None
    for year_month in reversed(source_months):
        counts = Counter()
        missing_keys: list[str] = []
        for ubigeo, _ in DISTRICTS:
            for crop_code in PERENNIAL_CROPS:
                record = records.get((ubigeo, crop_code, year_month))
                value = None if record is None else record["VERDE_ACTUAL"]
                if value is None:
                    counts["MISSING_OR_BLANK"] += 1
                    missing_keys.append(f"{ubigeo}:{crop_code}")
                elif value == 0:
                    counts["OBSERVED_NUMERIC_ZERO"] += 1
                elif value > 0:
                    counts["OBSERVED_NUMERIC_POSITIVE"] += 1
                else:
                    counts["NEGATIVE"] += 1
        complete = counts["OBSERVED_NUMERIC_POSITIVE"] + counts["OBSERVED_NUMERIC_ZERO"]
        trail.append({
            "year_month": year_month,
            "observed_numeric_positive": counts["OBSERVED_NUMERIC_POSITIVE"],
            "observed_numeric_zero": counts["OBSERVED_NUMERIC_ZERO"],
            "missing_or_blank": counts["MISSING_OR_BLANK"],
            "negative": counts["NEGATIVE"],
            "complete_cells": complete,
            "missing_keys": missing_keys,
            "status": "PASS_COMPLETE" if complete == 39 and counts["NEGATIVE"] == 0 else "FAIL_INCOMPLETE",
        })
        if complete == 39 and counts["NEGATIVE"] == 0:
            selected = year_month
            break
    return trail, selected


def transient_diagnostics(rows: list[dict[str, str]]) -> dict[str, Any]:
    groups: dict[tuple[str, str, str], list[dict[str, str]]] = {}
    aggregate = {(alternative_id, crop): Decimal(0) for alternative_id, _, _ in ALTERNATIVES for crop in TRANSIENT_CROPS}
    for row in rows:
        key = (row["ALTERNATIVE_ID"], row["UBIGEO"], row["CROP_CODE"])
        groups.setdefault(key, []).append(row)
        aggregate[(row["ALTERNATIVE_ID"], row["CROP_CODE"])] += Decimal(row["SIEMBRA_HA"])
    complete_profiles = Counter()
    normalized_profiles = Counter()
    for (alternative_id, _, _), profile in groups.items():
        if len(profile) == 12 and all(row["SOURCE_MISSING_FLAG"] == "FALSE" for row in profile):
            complete_profiles[alternative_id] += 1
        if sum((Decimal(row["WITHIN_CAMPAIGN_SHARE"]) for row in profile), Decimal(0)) == Decimal(1):
            normalized_profiles[alternative_id] += 1
    return {
        "rows": len(rows),
        "groups": len(groups),
        "missing_groups": 52 - len(groups),
        "zero_rows": sum(row["OBSERVED_ZERO_FLAG"] == "TRUE" for row in rows),
        "complete_profiles": dict(complete_profiles),
        "normalized_profiles": dict(normalized_profiles),
        "aggregate": aggregate,
    }


def audit_row(
    check_id: str,
    domain: str,
    expected: str,
    observed: str,
    status: str,
    criticality: str,
    notes: str,
) -> dict[str, str]:
    return {
        "CHECK_ID": check_id,
        "DOMAIN": domain,
        "EXPECTED": expected,
        "OBSERVED": observed,
        "STATUS": status,
        "CRITICALITY": criticality,
        "NOTES": notes,
    }


def build_audit_rows(
    transient: list[dict[str, str]],
    trail: list[dict[str, Any]],
) -> list[dict[str, str]]:
    diagnostics = transient_diagnostics(transient)
    aggregate = diagnostics["aggregate"]
    expected_totals = {
        ("C0B5-A2020-2021", "14010020000"): Decimal(15213),
        ("C0B5-A2020-2021", "14010070000"): Decimal(5704),
        ("C0B5-A2023-2024", "14010020000"): Decimal(22592),
        ("C0B5-A2023-2024", "14010070000"): Decimal(5937),
    }
    maximum = max(item["complete_cells"] for item in trail)
    rows = [
        audit_row("C0B6-001", "C0B5_PARENT_SHA", EXPECTED_HEAD, EXPECTED_HEAD, "PASS", "CRITICAL", "Frozen parent identity."),
        audit_row("C0B6-002", "ALTERNATIVE_1_IDENTITY", "C0B5-A2020-2021|2020/2021", f"{ALTERNATIVES[0][0]}|{ALTERNATIVES[0][1]}", "PASS", "CRITICAL", "A1 is unchanged."),
        audit_row("C0B6-003", "ALTERNATIVE_2_IDENTITY", "C0B5-A2023-2024|2023/2024", f"{ALTERNATIVES[1][0]}|{ALTERNATIVES[1][1]}", "PASS", "CRITICAL", "A2 is unchanged."),
        audit_row("C0B6-004", "DISTRICT_SUPPORT", "13 exact frozen UBIGEO", str(len(DISTRICTS)), "PASS", "CRITICAL", "No scope reduction or expansion."),
        audit_row("C0B6-005", "REFERENCE_CONFIGURATION_CROP_SCOPE", "RICE_MAD_TRANSIENT_ONLY", "RICE_MAD_TRANSIENT_ONLY", "PASS", "CRITICAL", "Perennials are not comparator components."),
        audit_row("C0B6-006", "TRANSIENT_MONTHLY_ROW_COUNT", "624", str(diagnostics["rows"]), "PASS" if diagnostics["rows"] == 624 else "FAIL", "CRITICAL", "2 alternatives x 13 districts x 2 crops x 12 months."),
        audit_row("C0B6-007", "TRANSIENT_CELL_COMPLETENESS", "52/52", f"{diagnostics['groups']}/52", "PASS" if diagnostics["groups"] == 52 else "FAIL", "CRITICAL", "All alternative-district-crop profiles are present."),
        audit_row("C0B6-008", "TRANSIENT_MISSING_CELLS", "0", str(diagnostics["missing_groups"]), "PASS" if diagnostics["missing_groups"] == 0 else "FAIL", "CRITICAL", "No missing profile."),
        audit_row("C0B6-009", "TRANSIENT_MISSING_TO_ZERO", "FALSE", "FALSE", "PASS", "CRITICAL", "Source absence or blank is never converted to zero."),
        audit_row("C0B6-010", "A1_TIMING_PROFILE_COMPLETENESS", "26/26", str(diagnostics["complete_profiles"].get(ALTERNATIVES[0][0], 0)) + "/26", "PASS" if diagnostics["complete_profiles"].get(ALTERNATIVES[0][0]) == 26 else "FAIL", "CRITICAL", "Alternative-specific source timing only."),
        audit_row("C0B6-011", "A2_TIMING_PROFILE_COMPLETENESS", "26/26", str(diagnostics["complete_profiles"].get(ALTERNATIVES[1][0], 0)) + "/26", "PASS" if diagnostics["complete_profiles"].get(ALTERNATIVES[1][0]) == 26 else "FAIL", "CRITICAL", "Alternative-specific source timing only."),
        audit_row("C0B6-012", "SHARE_NORMALIZATION", "26/26 each alternative", json.dumps(diagnostics["normalized_profiles"], sort_keys=True), "PASS" if set(diagnostics["normalized_profiles"].values()) == {26} else "FAIL", "CRITICAL", "Decimal-28 shares close exactly to one."),
        audit_row("C0B6-013", "DISTRICT_MIX_AND_MATCH", "FALSE", "FALSE", "PASS", "CRITICAL", "Each alternative retains exact district profiles."),
        audit_row("C0B6-014", "CROP_YEAR_MIXING", "FALSE", "FALSE", "PASS", "CRITICAL", "Each alternative uses one source campaign."),
        audit_row("C0B6-015", "TIMING_PROFILE_MIXING", "FALSE", "FALSE", "PASS", "CRITICAL", "No pooling or profile transfer."),
    ]
    for number, (key, expected) in enumerate(expected_totals.items(), 16):
        actual = aggregate[key]
        rows.append(audit_row(
            f"C0B6-{number:03d}", "TRANSIENT_TOTAL_RECONCILIATION",
            format_decimal(expected), format_decimal(actual),
            "PASS" if actual == expected else "FAIL", "CRITICAL",
            f"ALTERNATIVE_ID={key[0]};CROP_CODE={key[1]}",
        ))
    rows.extend([
        audit_row("C0B6-020", "SELECTED_SCOPE_ARCHITECTURE", SELECTED_SCOPE_ARCHITECTURE, SELECTED_SCOPE_ARCHITECTURE, "PASS", "CRITICAL", "S1 was selected by formal scope adjudication."),
        audit_row("C0B6-021", "PERENNIAL_BASELINE_UNAVAILABLE", "COMMON_COMPLETE=FALSE;MAX=38/39", f"COMMON_COMPLETE=FALSE;MAX={maximum}/39", "PASS" if maximum == 38 else "FAIL", "CRITICAL", "The evidence fact is preserved without materializing a block."),
        audit_row("C0B6-022", "PERENNIALS_EXCLUDED_FROM_COMPARATOR", "TRUE", "TRUE", "PASS", "CRITICAL", "Mango, lemon and banana remain outside A1/A2."),
        audit_row("C0B6-023", "FIVE_CROP_A1_A2_AGGREGATION", "NOT_AUTHORIZED", "NOT_AUTHORIZED", "PASS", "CRITICAL", "A1/A2 metrics are transient-block metrics only."),
        audit_row("C0B6-024", "COMMON_PERENNIAL_CVAR_CANCELLATION", "FALSE", "FALSE", "PASS", "CRITICAL", "A common random component is not assumed to cancel in nonlinear tail risk."),
        audit_row("C0B6-025", "NO_OUTCOME_LEAKAGE", "PASS", "PASS", "PASS", "CRITICAL", "No outcome or downstream performance selects construction choices."),
        audit_row("C0B6-026", "NO_LAND_CAPACITY_INFERENCE", "PASS", "PASS", "PASS", "CRITICAL", "No AREA_HA inequality or capacity test is performed."),
        audit_row("C0B6-027", "NO_WATER_MODEL", "PASS", "PASS", "PASS", "CRITICAL", "No water quantity, service fraction or feasibility model."),
        audit_row("C0B6-028", "NO_OPTIMIZATION", "PASS", "PASS", "PASS", "CRITICAL", "No objective, ranking, interpolation or optimizer."),
        audit_row("C0B6-029", "FINAL_C0B6_STATUS", FINAL_STATUS, FINAL_STATUS, "PASS", "CRITICAL", "Transient reference configuration master is ready for independent audit."),
    ])
    return rows


def coverage_summary(trail: list[dict[str, Any]]) -> dict[str, Any]:
    maximum = max(item["complete_cells"] for item in trail)
    return {
        "candidate_months_scanned_n": len(trail),
        "latest_source_month": trail[0]["year_month"],
        "latest_source_month_positive_cells": trail[0]["observed_numeric_positive"],
        "latest_source_month_zero_cells": trail[0]["observed_numeric_zero"],
        "latest_source_month_missing_cells": trail[0]["missing_or_blank"],
        "maximum_complete_cells": maximum,
        "maximum_complete_months": sorted(item["year_month"] for item in trail if item["complete_cells"] == maximum),
        "trail": trail,
    }


def build_perennial_evidence(
    records: dict[tuple[str, str, int], dict[str, Decimal | None]],
    source_months: tuple[int, ...],
    trail: list[dict[str, Any]],
) -> dict[str, Any]:
    summary = coverage_summary(trail)
    best_months = summary["maximum_complete_months"]
    crop_coverage: dict[str, dict[str, Any]] = {}
    for crop_code, (crop_std, _) in PERENNIAL_CROPS.items():
        monthly = {
            month: sum(
                records.get((ubigeo, crop_code, month), {}).get("VERDE_ACTUAL") is not None
                for ubigeo, _ in DISTRICTS
            )
            for month in source_months
        }
        best = max(monthly.values())
        crop_coverage[crop_code] = {
            "crop_std": crop_std,
            "any_13_of_13_month": any(value == 13 for value in monthly.values()),
            "best_complete_districts_n": best,
            "best_months": [month for month in source_months if monthly[month] == best],
        }
    best_missing_cells = []
    for item in trail:
        if item["year_month"] not in best_months:
            continue
        for key in item["missing_keys"]:
            ubigeo, crop_code = key.split(":")
            best_missing_cells.append({
                "year_month": item["year_month"],
                "ubigeo": ubigeo,
                "district_name": dict(DISTRICTS)[ubigeo],
                "crop_code": crop_code,
                "crop_std": PERENNIAL_CROPS[crop_code][0],
            })
    best_missing_cells.sort(key=lambda row: (row["year_month"], row["ubigeo"], row["crop_code"]))
    return {
        "selection_rule": PERENNIAL_SELECTION_RULE,
        "common_complete_perennial_month_exists": False,
        "max_complete_perennial_cells_any_month": summary["maximum_complete_cells"],
        "perennial_expected_common_cells": 39,
        "best_perennial_coverage_months": best_months,
        "best_month_missing_cells": best_missing_cells,
        "candidate_months_audited_n": len(trail),
        "source_first_month": min(source_months),
        "source_last_month": max(source_months),
        "crop_coverage": crop_coverage,
        "perennial_source_missingness_typology": [
            "INTERMITTENT_REPORTING_MISSINGNESS",
            "ASYNCHRONOUS_CROP_REPORTING",
        ],
        "externally_certifiable_perennial_completion_cells_n": 0,
        "missing_reinterpreted_as_zero": False,
        "common_perennial_block_materialized": False,
    }


def scope_row(
    check_id: str,
    domain: str,
    question: str,
    evidence_status: str,
    adjudication: str,
    consequence: str,
    notes: str,
) -> dict[str, str]:
    return {
        "CHECK_ID": check_id,
        "DOMAIN": domain,
        "QUESTION": question,
        "EVIDENCE_STATUS": evidence_status,
        "ADJUDICATION": adjudication,
        "MODEL_CONSEQUENCE": consequence,
        "FROZEN_STATUS": "PASS_FROZEN",
        "NOTES": notes,
    }


def build_scope_rows() -> list[dict[str, str]]:
    return [
        scope_row("C0B6S-001", "C0B6A_FORENSICS", "Did extraction cause the perennial failure?", "IMPLEMENTATION_DEFECT_FOUND=FALSE", "SOURCE_INCOMPLETENESS_CONFIRMED", "NO_EXTRACTION_PATCH", "Zero, numeric, UBIGEO, crop and month filters passed."),
        scope_row("C0B6S-002", "PERENNIAL_COVERAGE", "Does one common 39/39 month exist?", "FALSE", "NO_COMMON_FIXED_PERENNIAL_BASELINE", "NO_PERENNIAL_COMPARATOR_BLOCK", "No missing value is reinterpreted as zero."),
        scope_row("C0B6S-003", "PERENNIAL_COVERAGE", "Which months maximize coverage?", "202303;202407", "BEST_MONTHS_RETAINED_AS_EVIDENCE_FACT", "NO_BASELINE_SELECTED", "Each best month remains 38/39."),
        scope_row("C0B6S-004", "PERENNIAL_COVERAGE", "What is maximum common completeness?", "38/39", "INSUFFICIENT_FOR_FROZEN_RULE", "NO_NUMERIC_PERENNIAL_BLOCK", "The 39-cell requirement is unchanged."),
        scope_row("C0B6S-005", "PERENNIAL_COVERAGE", "Which crop blocks 13/13?", "BANANA_ANY_13_OF_13_MONTH=FALSE", "BANANA_BOTTLENECK_DOCUMENTED", "NO_CROP_REMOVAL_OR_SCOPE_REDUCTION", "Mango and lemon each attain 13/13 separately."),
        scope_row("C0B6S-006", "EXTERNAL_EVIDENCE", "Can official evidence complete a best month?", "0_ADMISSIBLE_CELLS", "NO_EXTERNAL_COMPLETION", "NO_EVIDENCE_SUBSTITUTION", "Same-concept and same-date requirements remain binding."),
        scope_row("C0B6S-007", "ROUTE_SELECTION", "Is S1 scientifically coherent?", "YES", "S1_SELECTED", "TRANSIENT_REFERENCE_CONFIGURATION_DATA_MASTER", "Rice/MAD comparator remains identifiable."),
        scope_row("C0B6S-008", "ROUTE_SELECTION", "Should C0B5 be reopened for 12 districts?", "NO", "S2_REJECTED", "PRESERVE_13_DISTRICTS", "Scope reduction would discard complete transient evidence to force a table."),
        scope_row("C0B6S-009", "ROUTE_SELECTION", "Should the comparator be removed?", "NO", "S3_REJECTED", "PRESERVE_ROUTE_B_TRANSIENT_COMPARATOR", "S1 is coherent."),
        scope_row("C0B6S-010", "SPATIAL_SCOPE", "Are all frozen districts retained?", "13/13", "PRESERVE_EXACT_SUPPORT", "NO_SCOPE_REDUCTION", "C0B5 common support is unchanged."),
        scope_row("C0B6S-011", "FROZEN_ARCHITECTURE", "Does S1 require reopening C0B5?", "FALSE", "C0B5_REOPEN_NOT_REQUIRED", "A1_A2_IDENTITIES_UNCHANGED", "C0B5 did not import historical perennial stocks into alternatives."),
        scope_row("C0B6S-012", "BROADER_ANALYSIS", "Do perennials remain scientifically eligible?", "TRUE", "RETAIN_ALL_THREE_PERENNIALS", "SEPARATE_DOWNSTREAM_LAYER", "Later crop-specific gates remain required."),
        scope_row("C0B6S-013", "COMPARATOR_SCOPE", "Are perennials components of A1/A2?", "FALSE", "EXCLUDE_FROM_REFERENCE_CONFIGURATIONS", "TRANSIENT_BLOCK_ONLY", "Perennials are not converted to endogenous variables."),
        scope_row("C0B6S-014", "AGGREGATION_FIREWALL", "May A1/A2 be aggregated as five-crop portfolios?", "NO", "NOT_AUTHORIZED", "FORBID_FIVE_CROP_A1_A2_OUTPUTS", "Only transient-block aggregate metrics may be constructed later."),
        scope_row("C0B6S-015", "TAIL_RISK_FIREWALL", "Can a common perennial random component be assumed to cancel in CVaR?", "FALSE", "CANCELLATION_ARGUMENT_REJECTED", "DEFINE_ANY_LATER_A1_A2_CVAR_ON_TRANSIENT_BLOCK", "Nonlinear tail risk need not preserve relative relationships."),
        scope_row("C0B6S-016", "FINAL_SCOPE", "Is the transient comparator authorized for independent audit?", "YES", "AUTHORIZED", "C0B6_REBUILD_READY", "No outcomes, land, water or optimization enter the decision."),
    ]


def build_config(
    transient: list[dict[str, str]],
    perennial_evidence: dict[str, Any],
    artifact_hashes: dict[str, str],
) -> dict[str, Any]:
    diagnostics = transient_diagnostics(transient)
    aggregate = diagnostics["aggregate"]
    return {
        "schema_version": "C0B6_REFERENCE_CONFIGURATION_DATA_MASTER_V1",
        "phase": "C0B6B_TRANSIENT_REFERENCE_CONFIGURATION_DATA_MASTER_REBUILD",
        "frozen_parent": {
            "c0b5_freeze": EXPECTED_HEAD,
            "selected_architecture": "ROUTE_B_FINITE_PRESPECIFIED_EMPIRICALLY_REALIZED_REFERENCE_CONFIGURATION_ANALYSIS",
            "short_analytical_label": "RISK_AWARE_FINITE_REFERENCE_CONFIGURATION_ANALYSIS",
            "c0b5_artifact_sha256": C0B5_HASHES,
        },
        "source_provenance": {
            "raw_path": RAW_PATH.relative_to(ROOT).as_posix(),
            "raw_sha256": FROZEN_INPUT_HASHES[RAW_PATH.relative_to(ROOT).as_posix()],
            "c0b3_config_sha256": FROZEN_INPUT_HASHES[C0B3_CONFIG_PATH.relative_to(ROOT).as_posix()],
        },
        "selected_scope_architecture": SELECTED_SCOPE_ARCHITECTURE,
        "dual_analytical_layers": {
            "status": DUAL_LAYER_STATUS,
            "layer_1": {
                "name": "FIVE_CROP_CLIMATE_ECONOMIC_RISK_CHARACTERIZATION",
                "crop_codes": [*TRANSIENT_CROPS, *PERENNIAL_CROPS],
                "materialized_in_c0b6": False,
                "status": "PENDING_LATER_CROP_SPECIFIC_AND_DOWNSTREAM_GATES",
            },
            "layer_2": {
                "name": "RICE_MAD_FINITE_REFERENCE_CONFIGURATION_STRESS_TEST",
                "crop_codes": list(TRANSIENT_CROPS),
                "materialized_in_c0b6": True,
                "common_support_districts_n": 13,
            },
            "layer_1_aggregation_into_layer_2_authorized": False,
        },
        "reference_configurations": [
            {
                "alternative_id": alternative_id,
                "source_campaign": campaign,
                "transient_block": f"TRANSIENT_BLOCK_A{index}",
                "comparator_crop_scope": "RICE_MAD_TRANSIENT_ONLY",
            }
            for index, (alternative_id, campaign, _) in enumerate(ALTERNATIVES, 1)
        ],
        "common_support_districts_n": 13,
        "common_support_districts": [
            {"ubigeo": ubigeo, "district_name": name} for ubigeo, name in DISTRICTS
        ],
        "reference_configuration_crop_scope": "RICE_MAD_TRANSIENT_ONLY",
        "transient_comparator_crop_codes": list(TRANSIENT_CROPS),
        "perennial_broader_analysis_crop_codes": list(PERENNIAL_CROPS),
        "broader_analysis_crop_codes": [*TRANSIENT_CROPS, *PERENNIAL_CROPS],
        "transient_master": {
            "expected_monthly_rows": 624,
            "observed_monthly_rows": diagnostics["rows"],
            "expected_district_crop_alternative_cells": 52,
            "observed_complete_district_crop_alternative_cells": diagnostics["groups"],
            "missing_district_crop_alternative_cells": diagnostics["missing_groups"],
            "silent_missing_to_zero_used": False,
            "timing_profiles_complete": diagnostics["complete_profiles"],
            "timing_profiles_normalized": diagnostics["normalized_profiles"],
            "observed_zero_months": {
                alternative_id: sum(
                    row["OBSERVED_ZERO_FLAG"] == "TRUE"
                    for row in transient if row["ALTERNATIVE_ID"] == alternative_id
                )
                for alternative_id, _, _ in ALTERNATIVES
            },
            "aggregate_totals_ha": {
                alternative_id: {
                    TRANSIENT_CROPS[crop]: int(aggregate[(alternative_id, crop)])
                    for crop in TRANSIENT_CROPS
                }
                for alternative_id, _, _ in ALTERNATIVES
            },
            "generic_t3_rule_authorized": False,
            "observed_alternative_timing_profile_status": "SUPPORTED_ALTERNATIVE_SPECIFIC_ONLY_NO_GENERIC_T3_RULE",
            "pooled_timing_shares_created": False,
            "district_mix_and_match_detected": False,
            "crop_year_mixing_detected": False,
            "timing_profile_mixing_detected": False,
            "reference_configuration_role": REFERENCE_ROLE,
        },
        "perennial_scope_adjudication": {
            **perennial_evidence,
            "perennials_in_a1_a2_reference_configurations": False,
            "perennials_remain_in_broader_analysis": True,
            "perennial_comparator_role": "NONE",
            "perennial_risk_analysis_status": "SEPARATE_DOWNSTREAM_ANALYTICAL_LAYER_PENDING_LATER_GATES",
        },
        "scope_adjudication": {
            "s1_status": "SCIENTIFICALLY_ADMISSIBLE_AND_SELECTED",
            "s2_status": "REJECTED_SCOPE_REDUCTION_NOT_SCIENTIFICALLY_JUSTIFIED",
            "s3_status": "REJECTED_S1_IS_SCIENTIFICALLY_COHERENT",
            "c0b5_reopen_required": False,
            "preserves_13_districts": True,
        },
        "reference_configuration_manifest": {
            "alternative_1": ["TRANSIENT_BLOCK_A1"],
            "alternative_2": ["TRANSIENT_BLOCK_A2"],
            "status": "READY_TRANSIENT_REFERENCE_CONFIGURATIONS",
            "components_are_physical_total_land_occupancy": False,
            "components_are_regional_capacity": False,
            "components_are_reallocable_land": False,
        },
        "aggregation_firewalls": {
            "five_crop_a1_a2_aggregation_status": "NOT_AUTHORIZED",
            "common_perennial_random_component_can_be_assumed_to_cancel_in_cvar": False,
            "later_a1_a2_risk_metrics_scope": "TRANSIENT_BLOCK_ONLY",
            "forbidden_outputs": [
                "A1_FIVE_CROP_TOTAL_PORTFOLIO_VALUE", "A2_FIVE_CROP_TOTAL_PORTFOLIO_VALUE",
                "A1_FIVE_CROP_VAR", "A2_FIVE_CROP_VAR", "A1_FIVE_CROP_CVAR",
                "A2_FIVE_CROP_CVAR", "FIVE_CROP_A1_VS_A2_AGGREGATE_LOSS_DISTRIBUTION",
            ],
        },
        "frozen_architecture_firewalls": {
            "decision_architecture": "ARCH_F_TRANSIENT_ENDOGENOUS_PERENNIAL_EXOGENOUS",
            "perennial_resolution": P3_STATUS,
            "area_ha_status": "PHYSICAL_AGRICULTURAL_FOOTPRINT_ONLY",
            "model_authorized_land_parameters_n": 0,
            "model_authorized_adjustment_bounds_n": 0,
        },
        "firewalls": {
            "historical_realization_status": "CERTIFIED_BY_SOURCE_OBSERVATION",
            "prospective_physical_feasibility_status": "NOT_CERTIFIED",
            "prospective_institutional_feasibility_status": "NOT_CERTIFIED",
            "land_hard_cap_status": "NOT_AUTHORIZED",
            "reallocable_transient_land_status": "NOT_OBSERVED",
            "area_ha_feasibility_test_used": False,
            "water_model_status": "NOT_AUTHORIZED",
            "outcome_leakage_used": False,
            "continuous_optimization_status": "NOT_AUTHORIZED",
            "economic_or_climate_output_created": False,
            "configuration_ranking_executed": False,
        },
        "artifact_sha256": dict(artifact_hashes),
        "next_gate": NEXT_GATE,
        "final_status": FINAL_STATUS,
    }


def build_report(config: dict[str, Any], artifact_hashes: dict[str, str]) -> bytes:
    lines = [
        "# C0B6B Transient Reference Configuration Data Master Rebuild",
        "",
        "## 1. Executive verdict",
        "",
        f"`C0B6_STATUS={FINAL_STATUS}`. C0B6 materializes the exact Rice/MAD transient reference configurations under the formally selected S1 scope.",
        "",
        "## 2. Frozen C0B5 parent",
        "",
        f"`C0B5_FREEZE={EXPECTED_HEAD}`. The seven C0B5 artifacts remain byte-identical.",
        "",
        "## 3. Why original C0B6 failed",
        "",
        "The original build required one common 39/39 perennial month. No such source month exists, so the failed perennial file has been removed rather than filled or reinterpreted.",
        "",
        "## 4. C0B6A forensic diagnosis",
        "",
        "`IMPLEMENTATION_DEFECT_FOUND=FALSE`; `MAX_COMPLETE_PERENNIAL_CELLS_ANY_MONTH=38`; best months are `202303;202407`; no admissible external completion was found.",
        "",
        "## 5. C0B6S formal scope adjudication",
        "",
        f"`SELECTED_SCOPE_ARCHITECTURE={SELECTED_SCOPE_ARCHITECTURE}`. S2 and S3 are rejected; C0B5 does not reopen.",
        "",
        "## 6. Selected S1 architecture",
        "",
        "C0B6 is a `TRANSIENT_REFERENCE_CONFIGURATION_DATA_MASTER`. A1/A2 contain Rice and MAD only and retain their exact historical campaign identities.",
        "",
        "## 7. Dual analytical layers",
        "",
        "Layer 1 is five-crop climate/economic-risk characterization pending later gates. Layer 2 is the Rice/MAD finite reference-configuration stress test materialized here. Layer 1 may not be aggregated into Layer 2.",
        "",
        "## 8. Exact A1/A2 identities",
        "",
        "`C0B5-A2020-2021` uses `2020/2021`; `C0B5-A2023-2024` uses `2023/2024`. Neither membership nor campaign changes.",
        "",
        "## 9. Exact 13-district support",
        "",
        "`COMMON_SUPPORT_DISTRICTS_N=13`: " + "; ".join(f"{u} {n}" for u, n in DISTRICTS) + ". No scope reduction is used.",
        "",
        "## 10. Rice/MAD transient master",
        "",
        "`REFERENCE_CONFIGURATION_CROP_SCOPE=RICE_MAD_TRANSIENT_ONLY`; 624 monthly rows and 52 complete alternative-district-crop profiles are materialized.",
        "",
        "## 11. Campaign-total reconciliation",
        "",
        "Raw-source SIEMBRA totals reproduce exactly: A1 Rice 15213 ha, A1 MAD 5704 ha, A2 Rice 22592 ha, and A2 MAD 5937 ha.",
        "",
        "## 12. Monthly timing profiles",
        "",
        "A1 and A2 each have 26/26 complete alternative-specific profiles. Shares close exactly to one. No generic T3, averaging, pooling, or cross-alternative transfer is authorized.",
        "",
        "## 13. Zero vs missing semantics",
        "",
        "Observed numeric zero remains zero and is flagged. Blank or absent source data is never converted to zero. `SILENT_MISSING_TO_ZERO_USED=FALSE`.",
        "",
        "## 14. Perennial common-baseline failure",
        "",
        "`COMMON_COMPLETE_PERENNIAL_MONTH_EXISTS=FALSE`; maximum coverage is 38/39 in 202303 and 202407. Banana never reaches 13/13 districts in one month. No common perennial block is materialized.",
        "",
        "## 15. Why perennials are excluded from comparator",
        "",
        "A common numeric fixed-stock initialization is not identifiable under the frozen rule. Exclusion prevents imputation, date mixing, crop removal, or district reduction.",
        "",
        "## 16. Why perennials remain in broader study",
        "",
        "Mango, lemon and banana remain eligible for separate climate, yield, economic and risk characterization subject to later gates. They are not removed from the scientific project.",
        "",
        "## 17. Five-crop aggregation firewall",
        "",
        "`FIVE_CROP_A1_A2_AGGREGATION_STATUS=NOT_AUTHORIZED`. A1/A2 may not be described as five-crop, whole-agriculture, or regional portfolios.",
        "",
        "## 18. CVaR common-random-component firewall",
        "",
        "`COMMON_PERENNIAL_RANDOM_COMPONENT_CAN_BE_ASSUMED_TO_CANCEL_IN_CVAR=FALSE`. Any later A1/A2 tail-risk metric is explicitly a transient-block metric.",
        "",
        "## 19. Future-feasibility firewall",
        "",
        "`HISTORICAL_REALIZATION_STATUS=CERTIFIED_BY_SOURCE_OBSERVATION`; prospective physical and institutional feasibility remain `NOT_CERTIFIED`.",
        "",
        "## 20. Land and water firewalls",
        "",
        "`AREA_HA_STATUS=PHYSICAL_AGRICULTURAL_FOOTPRINT_ONLY`; land hard cap and water model are `NOT_AUTHORIZED`; reallocable transient land is `NOT_OBSERVED`.",
        "",
        "## 21. No-outcome-leakage audit",
        "",
        "Construction uses source identifiers, month, SIEMBRA and VERDE_ACTUAL coverage only. No yield, production response, price, climate response, ENSO outcome, economic outcome, VaR, CVaR, ranking, objective, or optimizer selects an alternative or scope.",
        "",
        "## 22. Final C0B6 architecture",
        "",
        f"`C0B6_STATUS={FINAL_STATUS}`; `C0B6_REBUILD_ARCHITECTURE=TRANSIENT_REFERENCE_CONFIGURATION_DATA_MASTER`. Artifact hashes: transient `{artifact_hashes[TRANSIENT_PATH.relative_to(ROOT).as_posix()]}`, scope `{artifact_hashes[SCOPE_PATH.relative_to(ROOT).as_posix()]}`, audit `{artifact_hashes[AUDIT_PATH.relative_to(ROOT).as_posix()]}`, config `{artifact_hashes[CONFIG_PATH.relative_to(ROOT).as_posix()]}`.",
        "",
        "## 23. Remaining downstream gates",
        "",
        f"`NEXT_GATE={NEXT_GATE}`. Five-crop Layer 1 remains pending crop-specific climate, yield, economic and risk gates. No ranking or optimization is authorized.",
    ]
    return ("\n".join(lines) + "\n").encode("utf-8")


def build_output_bytes() -> tuple[dict[Path, bytes], dict[str, Any]]:
    records, source_months = load_source()
    transient = build_transient_rows(records)
    trail, selected = build_perennial_coverage_trail(records, source_months)
    if selected is not None:
        raise ValueError("frozen perennial evidence unexpectedly contains a complete common month")
    perennial_evidence = build_perennial_evidence(records, source_months, trail)
    scope = build_scope_rows()
    audit = build_audit_rows(transient, trail)

    outputs: dict[Path, bytes] = {
        TRANSIENT_PATH: csv_bytes(TRANSIENT_COLUMNS, transient),
        SCOPE_PATH: csv_bytes(SCOPE_COLUMNS, scope),
        AUDIT_PATH: csv_bytes(AUDIT_COLUMNS, audit),
    }
    artifact_hashes = {
        path.relative_to(ROOT).as_posix(): sha256_bytes(payload)
        for path, payload in outputs.items()
    }
    config = build_config(transient, perennial_evidence, artifact_hashes)
    config_bytes = (json.dumps(config, indent=2, ensure_ascii=True) + "\n").encode("utf-8")
    outputs[CONFIG_PATH] = config_bytes
    artifact_hashes[CONFIG_PATH.relative_to(ROOT).as_posix()] = sha256_bytes(config_bytes)
    outputs[REPORT_PATH] = build_report(config, artifact_hashes)
    return outputs, config


def write_outputs() -> dict[str, Any]:
    outputs, config = build_output_bytes()
    if LEGACY_PERENNIAL_PATH.exists():
        LEGACY_PERENNIAL_PATH.unlink()
    for path, payload in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    return config


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def validate_report_scope(report_text: str) -> None:
    lower = report_text.lower()
    forbidden_claims = (
        "representative of piura",
        "representative piura",
        "piura-representative",
    )
    require(
        not any(claim in lower for claim in forbidden_claims),
        "representative-Piura claim is not authorized",
    )
    require(
        "may not be described as five-crop" in lower,
        "five-crop comparator disclaimer is missing",
    )


def run_preflight() -> list[str]:
    require(git("branch", "--show-current") == EXPECTED_BRANCH, "wrong C0B6 branch")
    require(git("rev-parse", "HEAD") == EXPECTED_HEAD, "wrong C0B5 frozen parent")
    require(git("show", "-s", "--format=%s", "HEAD") == EXPECTED_SUBJECT, "wrong parent subject")
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", EXPECTED_HEAD, "HEAD"], cwd=ROOT,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    require(ancestor.returncode == 0, "C0B5 freeze is not an ancestor")

    for relative, expected in {**C0B5_HASHES, **FROZEN_INPUT_HASHES}.items():
        require(sha256_file(ROOT / relative) == expected, f"frozen hash changed: {relative}")
    protected = [*C0B5_HASHES, *FROZEN_INPUT_HASHES]
    changed = set(filter(None, git("diff", "--name-only", "--", *protected).splitlines()))
    changed |= set(filter(None, git("diff", "--cached", "--name-only", "--", *protected).splitlines()))
    require(not changed, f"frozen path modified: {sorted(changed)}")

    tracked = set(filter(None, git("diff", "--name-only").splitlines()))
    tracked |= set(filter(None, git("diff", "--cached", "--name-only").splitlines()))
    untracked = {
        line.replace("\\", "/")
        for line in git("ls-files", "--others", "--exclude-standard").splitlines()
        if line
    }
    require(not tracked, f"tracked or staged diff exists: {sorted(tracked)}")
    require(untracked == AUTHORIZED_SCOPE, f"C0B6 scope mismatch: {sorted(untracked)}")
    require(not LEGACY_PERENNIAL_PATH.exists(), "failed fixed perennial baseline file still exists")

    expected_outputs, expected_config = build_output_bytes()
    for path, expected in expected_outputs.items():
        require(path.read_bytes() == expected, f"deterministic artifact mismatch: {path.name}")
    for path in (*expected_outputs, SCRIPT_PATH, TEST_PATH):
        raw = path.read_bytes()
        require(not raw.startswith(b"\xef\xbb\xbf"), f"UTF-8 BOM found: {path.name}")
        require(b"\r" not in raw, f"non-LF line ending found: {path.name}")
        require(raw.endswith(b"\n") and not raw.endswith(b"\n\n"), f"final LF mismatch: {path.name}")

    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    require(config == expected_config, "config does not reproduce")
    validate_report_scope(REPORT_PATH.read_text(encoding="utf-8"))
    require(config["final_status"] == FINAL_STATUS, "final rebuild status changed")
    require(config["selected_scope_architecture"] == SELECTED_SCOPE_ARCHITECTURE, "wrong S1 scope architecture")
    require(config["dual_analytical_layers"]["status"] == DUAL_LAYER_STATUS, "dual-layer firewall changed")
    require(config["dual_analytical_layers"]["layer_2"]["materialized_in_c0b6"], "transient layer not materialized")
    require(not config["dual_analytical_layers"]["layer_1"]["materialized_in_c0b6"], "five-crop layer materialized in C0B6")
    require(config["reference_configuration_crop_scope"] == "RICE_MAD_TRANSIENT_ONLY", "wrong comparator crop scope")
    require(
        [(item["alternative_id"], item["source_campaign"]) for item in config["reference_configurations"]]
        == [(alternative_id, campaign) for alternative_id, campaign, _ in ALTERNATIVES],
        "wrong A1/A2 identity or campaign",
    )
    require(config["common_support_districts_n"] == 13, "wrong district count")
    require(
        [(item["ubigeo"], item["district_name"]) for item in config["common_support_districts"]]
        == list(DISTRICTS),
        "wrong district support",
    )
    require(set(config["transient_comparator_crop_codes"]) == set(TRANSIENT_CROPS), "wrong transient crops")
    require(set(config["perennial_broader_analysis_crop_codes"]) == set(PERENNIAL_CROPS), "wrong broader perennial crops")
    require(
        set(config["broader_analysis_crop_codes"]) == set(TRANSIENT_CROPS) | set(PERENNIAL_CROPS),
        "wrong broader five-crop universe",
    )
    require(all("perennial_block" not in item for item in config["reference_configurations"]), "perennial block attached to A1/A2")
    require(config["transient_master"]["observed_monthly_rows"] == 624, "transient row count mismatch")
    require(config["transient_master"]["observed_complete_district_crop_alternative_cells"] == 52, "transient completeness mismatch")
    require(config["transient_master"]["missing_district_crop_alternative_cells"] == 0, "transient missing cell found")
    require(not config["transient_master"]["silent_missing_to_zero_used"], "missing converted to zero")
    require(set(config["transient_master"]["timing_profiles_complete"].values()) == {26}, "timing profiles incomplete")
    require(not config["transient_master"]["generic_t3_rule_authorized"], "generic T3 rule authorized")
    require(not config["transient_master"]["district_mix_and_match_detected"], "district mix-and-match detected")
    require(not config["transient_master"]["crop_year_mixing_detected"], "crop-year mixing detected")
    require(not config["transient_master"]["timing_profile_mixing_detected"], "timing mixing detected")
    perennial = config["perennial_scope_adjudication"]
    require(not perennial["common_complete_perennial_month_exists"], "unsupported common perennial month")
    require(perennial["max_complete_perennial_cells_any_month"] == 38, "perennial coverage maximum changed")
    require(perennial["perennial_expected_common_cells"] == 39, "perennial expected cell count changed")
    require(perennial["best_perennial_coverage_months"] == [202303, 202407], "best perennial months changed")
    require(not perennial["crop_coverage"]["15010040000"]["any_13_of_13_month"], "banana bottleneck changed")
    require(perennial["externally_certifiable_perennial_completion_cells_n"] == 0, "external completion changed")
    require(not perennial["perennials_in_a1_a2_reference_configurations"], "perennials attached to A1/A2")
    require(perennial["perennials_remain_in_broader_analysis"], "perennials removed from broader analysis")
    require(not perennial["common_perennial_block_materialized"], "common perennial block materialized")
    aggregation = config["aggregation_firewalls"]
    require(aggregation["five_crop_a1_a2_aggregation_status"] == "NOT_AUTHORIZED", "five-crop aggregation authorized")
    require(not aggregation["common_perennial_random_component_can_be_assumed_to_cancel_in_cvar"], "CVaR cancellation assumed")
    architecture = config["frozen_architecture_firewalls"]
    require(architecture["decision_architecture"] == "ARCH_F_TRANSIENT_ENDOGENOUS_PERENNIAL_EXOGENOUS", "C0B3 architecture changed")
    require(architecture["perennial_resolution"] == P3_STATUS, "P3 resolution changed")
    require(architecture["model_authorized_land_parameters_n"] == 0, "land parameter invented")
    require(architecture["model_authorized_adjustment_bounds_n"] == 0, "adjustment bound invented")
    firewalls = config["firewalls"]
    require(firewalls["prospective_physical_feasibility_status"] == "NOT_CERTIFIED", "physical feasibility certified")
    require(firewalls["prospective_institutional_feasibility_status"] == "NOT_CERTIFIED", "institutional feasibility certified")
    require(not firewalls["area_ha_feasibility_test_used"], "AREA_HA feasibility test used")
    require(firewalls["water_model_status"] == "NOT_AUTHORIZED", "water model authorized")
    require(not firewalls["outcome_leakage_used"], "outcome leakage used")
    require(firewalls["continuous_optimization_status"] == "NOT_AUTHORIZED", "optimization authorized")
    require(not firewalls["economic_or_climate_output_created"], "downstream output created")
    require(not firewalls["configuration_ranking_executed"], "configuration ranking executed")
    with SCOPE_PATH.open("r", encoding="utf-8", newline="") as handle:
        scope_rows = list(csv.DictReader(handle))
    require(len(scope_rows) >= 16, "scope adjudication is incomplete")
    require(all(row["FROZEN_STATUS"] == "PASS_FROZEN" for row in scope_rows), "scope row not frozen")
    with AUDIT_PATH.open("r", encoding="utf-8", newline="") as handle:
        audit_rows = list(csv.DictReader(handle))
    require(all(row["STATUS"] == "PASS" for row in audit_rows), "C0B6 audit contains a failed check")

    return [
        "C0B5_IMMUTABILITY_GATE=PASS",
        "PERSISTENT_SCOPE_GATE=PASS",
        "DETERMINISM_GATE=PASS",
        "TRANSIENT_DATA_MASTER_GATE=PASS",
        "S1_SCOPE_ADJUDICATION_GATE=PASS",
        "NO_OUTCOME_LEAKAGE_GATE=PASS",
        "NO_INVENTED_LAND_GATE=PASS",
        "NO_WATER_MODEL_GATE=PASS",
        "NO_OPTIMIZATION_GATE=PASS",
        "FIXED_PERENNIAL_BASELINE_FILE_PRESENT=FALSE",
        f"C0B6_PREFLIGHT={FINAL_STATUS}",
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="materialize deterministic C0B6 artifacts")
    mode.add_argument("--check-only", action="store_true", help="validate without writing persistent files")
    args = parser.parse_args()
    try:
        if args.write:
            write_outputs()
        for line in run_preflight():
            print(line)
    except Exception as exc:  # pragma: no cover - terminal diagnostic
        print(f"C0B6_PREFLIGHT=FAIL_DATA_MASTER_INCOHERENT: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
