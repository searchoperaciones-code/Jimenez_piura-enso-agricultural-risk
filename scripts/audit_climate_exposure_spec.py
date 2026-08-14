from __future__ import annotations

import calendar
import csv
import hashlib
import json
import subprocess
from datetime import date, timedelta
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "config" / "climate_exposure" / "climate_exposure_spec_v1.json"
CERTIFICATE = ROOT / "outputs" / "phenology" / "CLIMATE_EXPOSURE_SPEC_V1_FREEZE.md"
WINDOWS = ROOT / "data" / "processed" / "phenology" / "phenology_windows_frozen.csv"
PHENOLOGY_CERTIFICATE = ROOT / "outputs" / "phenology" / "PHENOLOGY_MASTER_V1_FREEZE.md"
CLIMATE = ROOT / "data" / "processed" / "climate" / "climate_anomalies.parquet"
REPORT = ROOT / "outputs" / "phenology" / "qa" / "climate_exposure_spec_gate_report.json"

EXPECTED_BASE_SHA = "ba2eab1e5ab04da88b86cc1b7b36594e9ab9e17c"
EXPECTED_PHENOLOGY_TAG = "v0.3.0-phenology-freeze"
EXPECTED_WINDOWS_SHA = "ea25d949be9834a9e35352d970bb1b2172cac7d49db7eabb101ddfde9cfb657d"
EXPECTED_PHENOLOGY_CERTIFICATE_SHA = "f9447e10918547011512d629b902dc71ec15b8d2ad74d28901f40f4afffa0ee9"
EXPECTED_CLIMATE_SHA = "11a1fc61cab062faf70e3f12d2a06f050a2ccf094273807192943ad130deb6df"

TRANSIENT_CROPS = {"14010020000", "14010070000"}
PERENNIAL_CROPS = {"13010210000", "13010170102", "15010040000"}
EXPECTED_CROP_CODES = TRANSIENT_CROPS | PERENNIAL_CROPS
EXPECTED_WINDOW_IDS = {
    "RICE_FLOWERING_95_110_DAS",
    "MAD_MPLUS1_MPLUS3",
    "MANGO_MAY_JUN_CURRENT_YEAR",
    "LEMON_FULL_YEAR_T",
    "LEMON_FULL_YEAR_T_MINUS_1",
    "BANANA_FULL_YEAR_T",
    "BANANA_FULL_YEAR_T_MINUS_1",
}
EXPECTED_TOP_LEVEL_KEYS = {
    "CLIMATE_CANONICAL_PATH",
    "CLIMATE_CANONICAL_SHA256",
    "CLIMATE_EXPOSURE_BUILD_CONFORMANCE",
    "DIRECTOR_FREEZE_DECISION",
    "EXPOSURE_DATA_BUILD",
    "PHENOLOGY_CERTIFICATE_SHA256",
    "PHENOLOGY_FREEZE_SHA",
    "PHENOLOGY_FREEZE_TAG",
    "PHENOLOGY_WINDOWS_SHA256",
    "SPEC_ID",
    "SPEC_STATUS",
    "SPEC_VERSION",
    "UPSTREAM_BASE_SHA",
    "boundary_contract",
    "climate_family_contract",
    "econometric_status",
    "evidence_rationale",
    "frozen_phenology_windows",
    "future_transient_outcome_contract",
    "outcome_firewall",
    "perennial_exposure_contract",
    "stage_b_artifacts",
    "strict_campaign_identification",
    "time_basis_contract",
    "transient_campaign_mappings",
    "unified_exposure_long_format",
    "within_month_uncertainty",
}
EXPECTED_CLIMATE_FAMILIES = {
    "LEVEL": ["RAIN_MM", "TMAX_C", "TMIN_C"],
    "PHYSICAL_ANOMALY": ["RAIN_ANOM_MM", "TMAX_ANOM_C", "TMIN_ANOM_C"],
    "STANDARDIZED_ANOMALY": ["RAIN_Z", "TMAX_Z", "TMIN_Z"],
}
EXPECTED_AGGREGATION = {
    "RAIN_MM": "SUM",
    "RAIN_ANOM_MM": "SUM",
    "RAIN_Z": "ARITHMETIC_MEAN",
    "TMAX_C": "ARITHMETIC_MEAN",
    "TMAX_ANOM_C": "ARITHMETIC_MEAN",
    "TMAX_Z": "ARITHMETIC_MEAN",
    "TMIN_C": "ARITHMETIC_MEAN",
    "TMIN_ANOM_C": "ARITHMETIC_MEAN",
    "TMIN_Z": "ARITHMETIC_MEAN",
}
FORBIDDEN_EXPOSURE_SCHEMA_FIELDS = {"YIELD_RAW", "PRODUCCION", "PRECIO", "PRECIO_CHACRA", "COSECHA"}


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8"))


def read_windows() -> list[dict[str, str]]:
    with WINDOWS.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_certificate_statuses() -> dict[str, str]:
    if not CERTIFICATE.exists():
        return {}
    statuses: dict[str, str] = {}
    for raw_line in CERTIFICATE.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        statuses[key.strip()] = value.strip()
    return statuses


def git_rev_list(tag: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-list", "-n", "1", tag],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip()


def check(condition: bool, name: str, checks: list[dict[str, Any]], detail: Any = None) -> None:
    checks.append({"check": name, "status": "PASS" if condition else "FAIL", "detail": detail})


def campaign_start_year(day: date) -> int:
    return day.year if day.month >= 8 else day.year - 1


def campaign_id(start_year: int) -> str:
    return f"{start_year}/{start_year + 1}"


def campaign_for_date(day: date) -> str:
    return campaign_id(campaign_start_year(day))


def transient_attribution(crop_code: str, anchor_year: int, anchor_month: int) -> dict[str, Any]:
    if crop_code == "14010020000":
        l_min, l_max = 110, 138
    elif crop_code == "14010070000":
        l_min, l_max = 120, 170
    else:
        raise ValueError(f"Unsupported transient crop code: {crop_code}")

    anchor_min = date(anchor_year, anchor_month, 1)
    anchor_max = date(anchor_year, anchor_month, calendar.monthrange(anchor_year, anchor_month)[1])
    harvest_min = anchor_min + timedelta(days=l_min)
    harvest_max = anchor_max + timedelta(days=l_max)
    campaign_min = campaign_for_date(harvest_min)
    campaign_max = campaign_for_date(harvest_max)
    status = "UNAMBIGUOUS_AGRONOMIC_CAMPAIGN" if campaign_min == campaign_max else "AMBIGUOUS_CROSS_CAMPAIGN"
    return {
        "ANCHOR_DATE_MIN": anchor_min.isoformat(),
        "ANCHOR_DATE_MAX": anchor_max.isoformat(),
        "HARVEST_DATE_MIN": harvest_min.isoformat(),
        "HARVEST_DATE_MAX": harvest_max.isoformat(),
        "CAMPAIGN_MIN": campaign_min,
        "CAMPAIGN_MAX": campaign_max,
        "CAMPAIGN_ATTRIBUTION_STATUS": status,
        "ASSIGNED_CAMPAIGN_ID": campaign_min if status == "UNAMBIGUOUS_AGRONOMIC_CAMPAIGN" else None,
    }


def yyyymm(year: int, month: int) -> int:
    return year * 100 + month


def strict_domains(crop_code: str, campaign_start: int) -> dict[str, list[int]]:
    if crop_code == "14010020000":
        return {
            "U": [yyyymm(campaign_start, m) for m in range(5, 13)]
            + [yyyymm(campaign_start + 1, m) for m in (1, 2)],
            "A": [yyyymm(campaign_start, m) for m in (3, 4)]
            + [yyyymm(campaign_start + 1, m) for m in (3, 4)],
        }
    if crop_code == "14010070000":
        return {
            "U": [yyyymm(campaign_start, m) for m in range(5, 13)] + [yyyymm(campaign_start + 1, 1)],
            "A": [yyyymm(campaign_start, m) for m in (2, 3, 4)]
            + [yyyymm(campaign_start + 1, m) for m in (2, 3, 4)],
        }
    raise ValueError(f"Unsupported transient crop code: {crop_code}")


def spec_domain_yyyymm(spec_domain: list[dict[str, Any]], campaign_start: int) -> list[int]:
    values: list[int] = []
    for block in spec_domain:
        year = campaign_start + int(block["year_offset_from_campaign_start"])
        values.extend(yyyymm(year, int(month)) for month in block["months"])
    return values


def exposure_schema_fields(spec: dict[str, Any]) -> set[str]:
    fields: set[str] = set()
    fields.update(spec["stage_b_artifacts"]["transient_cohort_exposures"]["schema"])
    fields.update(spec["stage_b_artifacts"]["transient_campaign_exposures_strict"]["schema"])
    fields.update(spec["perennial_exposure_contract"]["perennial_schema"])
    fields.update(spec["unified_exposure_long_format"]["schema"])
    return fields


def evaluate() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    check(SPEC.exists(), "SPEC_EXISTS", checks, rel(SPEC))
    check(CERTIFICATE.exists(), "CERTIFICATE_EXISTS", checks, rel(CERTIFICATE))
    if not SPEC.exists():
        return {"checks": checks, "failed_checks": checks, "stage": "CLIMATE_EXPOSURE_SPEC_V1", "status": "FAIL"}

    spec = read_json(SPEC)
    certificate_statuses = read_certificate_statuses()
    check(set(spec) == EXPECTED_TOP_LEVEL_KEYS, "EXACT_SPEC_TOP_LEVEL_SCHEMA", checks, sorted(spec))
    check(spec.get("SPEC_ID") == "CLIMATE_EXPOSURE_MASTER_V1", "SPEC_ID", checks)
    check(spec.get("SPEC_VERSION") == "v1", "SPEC_VERSION", checks)
    check(spec.get("SPEC_STATUS") == "PASS_FROZEN", "SPEC_STATUS", checks)
    check(spec.get("DIRECTOR_FREEZE_DECISION") == "PASS", "DIRECTOR_FREEZE_DECISION", checks)
    check(spec.get("EXPOSURE_DATA_BUILD") == "READY_FROM_FROZEN_SPEC", "EXPOSURE_DATA_BUILD", checks)
    check(
        spec.get("CLIMATE_EXPOSURE_BUILD_CONFORMANCE") == "MUST_CONFORM_EXACTLY_TO_THIS_FROZEN_CONTRACT",
        "CLIMATE_EXPOSURE_BUILD_CONFORMANCE",
        checks,
    )
    check(certificate_statuses.get("SPECIFICATION_STATUS") == "PASS_FROZEN", "CERTIFICATE_SPECIFICATION_STATUS", checks)
    check(certificate_statuses.get("DIRECTOR_FREEZE_DECISION") == "PASS", "CERTIFICATE_DIRECTOR_FREEZE_DECISION", checks)
    check(certificate_statuses.get("EXPOSURE_DATA_BUILD") == "READY_FROM_FROZEN_SPEC", "CERTIFICATE_EXPOSURE_DATA_BUILD", checks)
    check(spec.get("UPSTREAM_BASE_SHA") == EXPECTED_BASE_SHA, "UPSTREAM_BASE_SHA", checks)
    check(spec.get("PHENOLOGY_FREEZE_TAG") == EXPECTED_PHENOLOGY_TAG, "PHENOLOGY_FREEZE_TAG", checks)
    check(spec.get("PHENOLOGY_FREEZE_SHA") == EXPECTED_BASE_SHA, "PHENOLOGY_FREEZE_SHA", checks)
    check(git_rev_list(EXPECTED_PHENOLOGY_TAG) == EXPECTED_BASE_SHA, "PHENOLOGY_FREEZE_TAG_SHA", checks)
    check(spec.get("PHENOLOGY_WINDOWS_SHA256") == EXPECTED_WINDOWS_SHA, "SPEC_PHENOLOGY_WINDOWS_SHA", checks)
    check(spec.get("PHENOLOGY_CERTIFICATE_SHA256") == EXPECTED_PHENOLOGY_CERTIFICATE_SHA, "SPEC_PHENOLOGY_CERTIFICATE_SHA", checks)
    check(spec.get("CLIMATE_CANONICAL_PATH") == rel(CLIMATE), "CLIMATE_CANONICAL_PATH", checks)
    check(spec.get("CLIMATE_CANONICAL_SHA256") == EXPECTED_CLIMATE_SHA, "SPEC_CLIMATE_SHA", checks)
    check(WINDOWS.exists() and sha256_file(WINDOWS) == EXPECTED_WINDOWS_SHA, "ACTUAL_PHENOLOGY_WINDOWS_SHA", checks)
    check(PHENOLOGY_CERTIFICATE.exists() and sha256_file(PHENOLOGY_CERTIFICATE) == EXPECTED_PHENOLOGY_CERTIFICATE_SHA, "ACTUAL_PHENOLOGY_CERTIFICATE_SHA", checks)
    check(CLIMATE.exists() and sha256_file(CLIMATE) == EXPECTED_CLIMATE_SHA, "ACTUAL_CLIMATE_SHA", checks)

    windows = read_windows() if WINDOWS.exists() else []
    check(len(windows) == 7, "EXACT_SEVEN_FROZEN_PHENOLOGY_WINDOWS", checks, len(windows))
    check({row["COD_CULTIVO"] for row in windows} == EXPECTED_CROP_CODES, "EXACT_FIVE_CROP_CODES_IN_WINDOWS", checks)
    check({row["WINDOW_ID"] for row in windows} == EXPECTED_WINDOW_IDS, "EXACT_WINDOW_IDS_IN_WINDOWS", checks)

    spec_windows = spec.get("frozen_phenology_windows", [])
    check(len(spec_windows) == 7, "EXACT_SEVEN_SPEC_WINDOWS", checks, len(spec_windows))
    check({row["COD_CULTIVO"] for row in spec_windows} == EXPECTED_CROP_CODES, "EXACT_FIVE_CROP_CODES_IN_SPEC", checks)
    check({row["WINDOW_ID"] for row in spec_windows} == EXPECTED_WINDOW_IDS, "EXACT_WINDOW_IDS_IN_SPEC", checks)

    time_basis = spec["time_basis_contract"]
    check(
        set(time_basis["transient_crops"]) == TRANSIENT_CROPS
        and all(row["TIME_BASIS"] == "AGRICULTURAL_CAMPAIGN_AUG_JUL" for row in time_basis["transient_crops"].values()),
        "TRANSIENT_TIME_BASIS_ASSIGNMENTS",
        checks,
    )
    check(
        set(time_basis["perennial_crops"]) == PERENNIAL_CROPS
        and all(row["TIME_BASIS"] == "CALENDAR_YEAR" for row in time_basis["perennial_crops"].values()),
        "PERENNIAL_TIME_BASIS_ASSIGNMENTS",
        checks,
    )
    check(time_basis["transient_campaign"]["CAMPAIGN_START_MONTH"] == 8, "CAMPAIGN_START_MONTH", checks)
    check(time_basis["transient_campaign"]["CAMPAIGN_END_MONTH"] == 7, "CAMPAIGN_END_MONTH", checks)
    check(time_basis["transient_campaign"]["do_not_silently_use_ANO"] is True, "DO_NOT_SILENTLY_USE_ANO", checks)

    rice = next((row for row in spec_windows if row["COD_CULTIVO"] == "14010020000"), {})
    mad = next((row for row in spec_windows if row["COD_CULTIVO"] == "14010070000"), {})
    check(rice.get("ATTRIBUTION_L_MIN_DAYS") == 110 and rice.get("ATTRIBUTION_L_MAX_DAYS") == 138, "RICE_TRANSIENT_L_MIN_L_MAX", checks)
    check(mad.get("ATTRIBUTION_L_MIN_DAYS") == 120 and mad.get("ATTRIBUTION_L_MAX_DAYS") == 170, "MAD_TRANSIENT_L_MIN_L_MAX", checks)
    check(rice.get("CLIMATE_WINDOW") == "m+3:m+4", "RICE_CLIMATE_WINDOW", checks)
    check(mad.get("CLIMATE_WINDOW") == "m+1:m+3", "MAD_CLIMATE_WINDOW", checks)

    families = spec["climate_family_contract"]
    check(families["families"] == EXPECTED_CLIMATE_FAMILIES, "EXACT_CLIMATE_FAMILY_NAMES", checks)
    check(families["aggregation"] == EXPECTED_AGGREGATION, "EXACT_CLIMATE_AGGREGATION", checks)
    check(families["primary_secondary_robustness_roles"] == "BLOCKED_UNTIL_ECONOMETRIC_DESIGN_MASTER", "NO_ECONOMETRIC_ROLE_SELECTION", checks)

    for crop_code in TRANSIENT_CROPS:
        spec_domains = spec["strict_campaign_identification"]["strict_domains"][crop_code]
        derived = strict_domains(crop_code, 2016)
        check(spec_domain_yyyymm(spec_domains["U"], 2016) == derived["U"], f"{crop_code}_STRICT_U_DOMAIN", checks)
        check(spec_domain_yyyymm(spec_domains["A"], 2016) == derived["A"], f"{crop_code}_STRICT_A_DOMAIN", checks)

    check(transient_attribution("14010020000", 2020, 3)["CAMPAIGN_ATTRIBUTION_STATUS"] == "AMBIGUOUS_CROSS_CAMPAIGN", "RICE_MARCH_AMBIGUOUS_MAPPING", checks)
    check(transient_attribution("14010020000", 2020, 5)["ASSIGNED_CAMPAIGN_ID"] == "2020/2021", "RICE_MAY_CAMPAIGN_MAPPING", checks)
    check(transient_attribution("14010070000", 2020, 2)["CAMPAIGN_ATTRIBUTION_STATUS"] == "AMBIGUOUS_CROSS_CAMPAIGN", "MAD_FEBRUARY_AMBIGUOUS_MAPPING", checks)
    check(transient_attribution("14010070000", 2020, 5)["ASSIGNED_CAMPAIGN_ID"] == "2020/2021", "MAD_MAY_CAMPAIGN_MAPPING", checks)

    forbidden_schema_fields = exposure_schema_fields(spec) & FORBIDDEN_EXPOSURE_SCHEMA_FIELDS
    check(not forbidden_schema_fields, "NO_FORBIDDEN_OUTCOME_FIELDS_IN_EXPOSURE_SCHEMAS", checks, sorted(forbidden_schema_fields))
    strict_layer = spec["stage_b_artifacts"]["transient_campaign_exposures_strict"]
    cohort_layer = spec["stage_b_artifacts"]["transient_cohort_exposures"]
    check(cohort_layer["artifact_role"] == "PRIMARY_STAGE_B_DATA_PRODUCT", "COHORT_LEDGER_PRIMARY_STAGE_B", checks)
    check(strict_layer["is_primary_econometric_exposure"] is False, "STRICT_LAYER_NOT_PRIMARY_ECONOMETRIC", checks)
    check("PRIMARY" not in strict_layer["artifact_role"], "STRICT_LAYER_ROLE_NOT_PRIMARY", checks)
    check(spec["future_transient_outcome_contract"]["status"] == "DEFINED_NOT_BUILT", "CAMPAIGN_OUTCOME_DEFINED_NOT_BUILT", checks)
    check(spec["future_transient_outcome_contract"]["belongs_to"] == "TRANSIENT_OUTCOME_MASTER", "CAMPAIGN_OUTCOME_SEPARATE_MASTER", checks)
    check(spec["econometric_status"]["ECONOMETRICS"] == "BLOCKED", "ECONOMETRICS_BLOCKED", checks)
    check(spec["econometric_status"]["PRIMARY_TRANSIENT_ECONOMETRIC_EXPOSURE"] == "NOT_YET_SELECTED", "PRIMARY_TRANSIENT_ECONOMETRIC_EXPOSURE_NOT_SELECTED", checks)
    check(spec["strict_campaign_identification"]["weight_sum_tolerance_abs"] == 1e-12, "WEIGHT_TOLERANCE", checks)
    check(spec["evidence_rationale"]["diagnostics_selected_time_basis"] is False, "FEASIBILITY_N_DID_NOT_SELECT_TIME_BASIS", checks)

    status = "PASS" if checks and all(item["status"] == "PASS" for item in checks) else "FAIL"
    return {
        "artifact": rel(SPEC),
        "checks": checks,
        "failed_checks": [item for item in checks if item["status"] != "PASS"],
        "stage": "CLIMATE_EXPOSURE_SPEC_V1",
        "status": status,
    }


def main() -> int:
    report = evaluate()
    write_json(REPORT, report)
    print(json.dumps({"stage": report["stage"], "status": report["status"]}, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
