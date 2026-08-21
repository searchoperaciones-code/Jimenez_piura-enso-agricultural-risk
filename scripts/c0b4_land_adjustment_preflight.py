"""Read-only preflight and deterministic diagnostics for C0B4."""

from __future__ import annotations

import ast
import csv
import hashlib
import json
import math
import statistics
import subprocess
import sys
from collections import Counter, defaultdict
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_UP
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_BRANCH = "phase/c0b4-land-adjustment-feasibility-v1"
EXPECTED_HEAD = "ed5543da18ce3a1a5e72a2ab2519b8e2f2363893"
EXPECTED_SUBJECT = "Freeze C0B3 perennial feasibility and architecture"

REGISTRY_PATH = ROOT / "outputs/decision_feasibility/C0B4_LAND_EVIDENCE_REGISTRY.csv"
OCCUPANCY_PATH = ROOT / "outputs/decision_feasibility/C0B4_TRANSIENT_OCCUPANCY_ADJUDICATION.csv"
ADJUSTMENT_PATH = ROOT / "outputs/decision_feasibility/C0B4_ADJUSTMENT_ENVELOPE_AUDIT.csv"
REPORT_PATH = ROOT / "outputs/decision_feasibility/C0B4_LAND_ADJUSTMENT_REPORT.md"
CONFIG_PATH = ROOT / "config/decision_ontology/transient_land_adjustment_v1.json"
SCRIPT_PATH = ROOT / "scripts/c0b4_land_adjustment_preflight.py"
TEST_PATH = ROOT / "tests/test_c0b4_land_adjustment.py"

RAW_PATH = ROOT / "data/raw/Formato_dataset_productos_dra__ (2).csv"
LAND_PATH = ROOT / "data/processed/land_physical.csv"
MODEL_DISTRICTS_PATH = ROOT / "outputs/decision_feasibility/C0B2_DISTRICT_SPATIAL_ELIGIBILITY.csv"

AUTHORIZED_SCOPE = {
    "outputs/decision_feasibility/C0B4_LAND_EVIDENCE_REGISTRY.csv",
    "outputs/decision_feasibility/C0B4_TRANSIENT_OCCUPANCY_ADJUDICATION.csv",
    "outputs/decision_feasibility/C0B4_ADJUSTMENT_ENVELOPE_AUDIT.csv",
    "outputs/decision_feasibility/C0B4_LAND_ADJUSTMENT_REPORT.md",
    "config/decision_ontology/transient_land_adjustment_v1.json",
    "scripts/c0b4_land_adjustment_preflight.py",
    "tests/test_c0b4_land_adjustment.py",
}

C0B3_HASHES = {
    "outputs/decision_feasibility/C0B3_PERENNIAL_EVIDENCE_REGISTRY.csv": "6f54dd9280da30966ca1ec62b2ac94de7796af372899110ac0b56324ad309452",
    "outputs/decision_feasibility/C0B3_CROP_STATE_ADJUDICATION.csv": "84dc3cffcc7743d8dc68ad68d5861ae1370ba4841c163b0b220c7810ff1f0b46",
    "outputs/decision_feasibility/C0B3_BIOLOGICAL_PARAMETER_EVIDENCE.csv": "fee134f743f6fda9919f150f294562d57c31e4b5aae79a9a971fc3929a582cf2",
    "outputs/decision_feasibility/C0B3_PERENNIAL_DECISION_REPORT.md": "6b43fd96a527bc026181c34f9e3b9a42a28e22fdcd9d2ce48cd06833e568da6c",
    "config/decision_ontology/perennial_state_adjudication_v1.json": "35d752b94b2aaf29e3b7f1512fa817ca18af8c817455a60467a1cc31cab2e86e",
    "scripts/c0b3_perennial_preflight.py": "ee061fb41da6553a7d72a28da469ab894cbec40eb9a6f8e922856237e5440f6e",
    "tests/test_c0b3_perennial.py": "fe7e76f3360b1390ae2bad711a095a80d602deaafa47fd166582ab3f1dd87e64",
}

FROZEN_DATA_HASHES = {
    "data/raw/Formato_dataset_productos_dra__ (2).csv": "7953e95f532b97f3db1ad42dfb517dc0b5f6e98a80b1f1b0954fc1b52419c489",
    "data/processed/land_physical.csv": "dba3d5263a14daddf0f5c1d33dfae2c209f9d531fdec983f193fb8c9d83ef517",
    "outputs/decision_feasibility/C0B2_DISTRICT_SPATIAL_ELIGIBILITY.csv": "a394b4727a7cb8a649ffd82fc704ab5db42d2673fc174a68c20e279146e875ad",
    "config/decision_ontology/decision_variable_ontology_v1.json": "a8f28394ea1c007413938600623f8e418491c69a9f9351d83d6256122ad4c534",
}

EXTERNAL_PDF_HASHES = {
    "SIEA_METHODOLOGY": "8fe81dcf74acc74803f9fa0c19ace73d54024133a527854e9f95e7d846df2230",
    "INIA_RICE_508": "17b7959a68e81dc53561e187d632f2fd09d7b122b9968d814534ce61d07abbc5",
    "INIA_RICE_502": "2335129ff8e43dc79c9bd52a7e2ebb7531d994a45705c308c917d41d517c4b93",
    "INIA_MAD_619": "ca20da761daedb97ec4b0ea52e1b956e3a791d5cf6729f4ab3cad0a72301a5e4",
    "MIDAGRI_RICE_OBSERVATORY": "21032cbca52b0ee7785e2c3f80494afccf5c745f960ba86444fcf82c0e17467e",
    "SENAMHI_PIURA_RICE_BULLETIN": "39632b2f4c16637f793e457893bb2b359dc5cf8a044ccc5f202bd5ab6876a511",
}

TRANSIENT_CROPS = {
    "14010020000": "ARROZ",
    "14010070000": "MAIZ AMARILLO DURO",
}
TARGET_CODES = set(TRANSIENT_CROPS) | {
    "13010210000", "13010170102", "15010040000",
}
CAMPAIGN_START_YEARS = tuple(range(2015, 2024))
CAMPAIGN_MONTHS = (8, 9, 10, 11, 12, 1, 2, 3, 4, 5, 6, 7)

REGISTRY_COLUMNS = [
    "EVIDENCE_ID", "EVIDENCE_DOMAIN", "CROP_CODE", "CROP_STD",
    "DISTRICT_SCOPE", "SOURCE_TIER", "SOURCE_AUTHORITY", "SOURCE_TITLE",
    "SOURCE_DATE", "SOURCE_URL", "PAGE_OR_SECTION", "RAW_TERM",
    "LAND_CONCEPT", "UNIT", "QUANTITATIVE_VALUE", "VALUE_LOWER",
    "VALUE_UPPER", "TIME_UNIT", "GEOGRAPHIC_RELEVANCE",
    "EVIDENCE_STRENGTH", "MODEL_ADMISSIBILITY", "EXACT_FINDING",
    "LIMITATION", "NOTES",
]
ALLOWED_EVIDENCE_DOMAINS = {
    "AREA_HA_SEMANTICS", "PHYSICAL_FOOTPRINT", "OTHER_CROP_OCCUPANCY",
    "CROP_DURATION", "LAND_OCCUPANCY", "SEQUENTIAL_CROPPING",
    "REALLOCABLE_AREA", "ADJUSTMENT_BOUND", "PLANNING_AREA",
    "T3_SHARE_RULE", "BASELINE", "OTHER",
}
OCCUPANCY_COLUMNS = [
    "CROP_CODE", "CROP_STD", "DECISION_RESOLUTION", "PLANTING_FLOW_ANCHOR",
    "OCCUPANCY_DURATION_STATUS", "OCCUPANCY_DURATION_VALUE",
    "OCCUPANCY_DURATION_LOWER", "OCCUPANCY_DURATION_UPPER",
    "OCCUPANCY_TIME_UNIT", "SIMULTANEOUS_OCCUPANCY_MAPPING_STATUS",
    "AREA_HA_COMPATIBILITY_STATUS", "REALLOCABLE_LAND_STATUS",
    "LAND_HARD_CAP_STATUS", "T3_SHARE_RULE_STATUS",
    "T3_SHARE_RULE_PROVENANCE", "CRITICAL_GAPS", "EVIDENCE_IDS", "NOTES",
]
ADJUSTMENT_COLUMNS = [
    "UBIGEO", "DISTRICT_NAME", "CROP_CODE", "CROP_STD",
    "N_HISTORICAL_PERIODS", "BASELINE_STATUS", "HIST_MIN_HA",
    "HIST_MAX_HA", "HIST_MEDIAN_HA", "MAX_ABS_YOY_CHANGE_HA",
    "MAX_REL_YOY_CHANGE", "P25_ABS_YOY_CHANGE_HA",
    "P50_ABS_YOY_CHANGE_HA", "P75_ABS_YOY_CHANGE_HA",
    "ZERO_ENTRY_OBSERVED", "ZERO_EXIT_OBSERVED", "OFFICIAL_BOUND_AVAILABLE",
    "ADJUSTMENT_BOUND_STATUS", "AUTHORIZED_LOWER_RULE",
    "AUTHORIZED_UPPER_RULE", "MODEL_BOUND_AUTHORIZED", "LIMITATION", "NOTES",
]


def _git(*args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args], cwd=ROOT, text=True, encoding="utf-8",
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=check,
    )
    return result.stdout.strip()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def _split_lines(value: str) -> set[str]:
    return {line.replace("\\", "/") for line in value.splitlines() if line}


def _decimal(value: str | None) -> Decimal | None:
    value = (value or "").strip()
    return None if value == "" else Decimal(value)


def _format_decimal(value: Decimal | None, places: int = 6) -> str:
    if value is None:
        return ""
    quantum = Decimal(1).scaleb(-places)
    text = format(value.quantize(quantum, rounding=ROUND_HALF_UP), "f")
    text = text.rstrip("0").rstrip(".")
    return "0" if text in {"", "-0"} else text


def _quantile(values: list[Decimal], probability: Decimal) -> Decimal | None:
    if not values:
        return None
    ordered = sorted(values)
    position = Decimal(len(ordered) - 1) * probability
    lower = int(position.to_integral_value(rounding=ROUND_FLOOR))
    upper = int(position.to_integral_value(rounding=ROUND_CEILING))
    if lower == upper:
        return ordered[lower]
    weight = position - Decimal(lower)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * weight


def model_districts() -> list[tuple[str, str]]:
    _, rows = _read_csv(MODEL_DISTRICTS_PATH)
    districts = [
        (row["UBIGEO"], row["DISTRICT_NAME"])
        for row in rows if row["IN_MODEL_UNIVERSE"] == "TRUE"
    ]
    return sorted(districts)


def transient_monthly_data() -> dict[tuple[str, str, int], Decimal | None]:
    monthly: dict[tuple[str, str, int], Decimal | None] = {}
    with RAW_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            crop_code = row["COD_CULTIVO"]
            if crop_code not in TRANSIENT_CROPS:
                continue
            key = (row["UBIGEO"], crop_code, int(row["MES"]))
            if key in monthly:
                raise ValueError(f"duplicate raw district-crop-month key: {key}")
            monthly[key] = _decimal(row["SIEMBRA"])
    return monthly


def complete_campaign_values(
    monthly: dict[tuple[str, str, int], Decimal | None],
    ubigeo: str,
    crop_code: str,
    start_year: int,
) -> list[Decimal] | None:
    values: list[Decimal] = []
    for month in CAMPAIGN_MONTHS:
        year = start_year if month >= 8 else start_year + 1
        key = (ubigeo, crop_code, year * 100 + month)
        if key not in monthly or monthly[key] is None:
            return None
        values.append(monthly[key] or Decimal(0))
    return values


def build_adjustment_rows() -> list[dict[str, str]]:
    monthly = transient_monthly_data()
    result: list[dict[str, str]] = []
    for ubigeo, district_name in model_districts():
        for crop_code, crop_name in TRANSIENT_CROPS.items():
            periods: list[tuple[int, Decimal]] = []
            for start_year in CAMPAIGN_START_YEARS:
                values = complete_campaign_values(monthly, ubigeo, crop_code, start_year)
                if values is not None:
                    periods.append((start_year, sum(values, Decimal(0))))

            changes: list[Decimal] = []
            relative_changes: list[Decimal] = []
            zero_entry = False
            zero_exit = False
            for (previous_year, previous), (current_year, current) in zip(periods, periods[1:]):
                if current_year != previous_year + 1:
                    continue
                change = abs(current - previous)
                changes.append(change)
                if previous > 0:
                    relative_changes.append(change / previous)
                zero_entry |= previous == 0 and current > 0
                zero_exit |= previous > 0 and current == 0

            totals = [value for _, value in periods]
            n_periods = len(totals)
            status = "SENSITIVITY_ONLY" if n_periods >= 2 else "UNRESOLVED"
            result.append({
                "UBIGEO": ubigeo,
                "DISTRICT_NAME": district_name,
                "CROP_CODE": crop_code,
                "CROP_STD": crop_name,
                "N_HISTORICAL_PERIODS": str(n_periods),
                "BASELINE_STATUS": "NOT_YET_FROZEN",
                "HIST_MIN_HA": _format_decimal(min(totals) if totals else None),
                "HIST_MAX_HA": _format_decimal(max(totals) if totals else None),
                "HIST_MEDIAN_HA": _format_decimal(Decimal(str(statistics.median(totals))) if totals else None),
                "MAX_ABS_YOY_CHANGE_HA": _format_decimal(max(changes) if changes else None),
                "MAX_REL_YOY_CHANGE": _format_decimal(max(relative_changes) if relative_changes else None),
                "P25_ABS_YOY_CHANGE_HA": _format_decimal(_quantile(changes, Decimal("0.25"))),
                "P50_ABS_YOY_CHANGE_HA": _format_decimal(_quantile(changes, Decimal("0.50"))),
                "P75_ABS_YOY_CHANGE_HA": _format_decimal(_quantile(changes, Decimal("0.75"))),
                "ZERO_ENTRY_OBSERVED": str(zero_entry).upper(),
                "ZERO_EXIT_OBSERVED": str(zero_exit).upper(),
                "OFFICIAL_BOUND_AVAILABLE": "FALSE",
                "ADJUSTMENT_BOUND_STATUS": status,
                "AUTHORIZED_LOWER_RULE": "",
                "AUTHORIZED_UPPER_RULE": "",
                "MODEL_BOUND_AUTHORIZED": "FALSE",
                "LIMITATION": "Complete August-July district-crop campaigns only; aggregate history does not identify parcel reuse, reallocable land, or a future hard bound.",
                "NOTES": "DESCRIPTIVE_DIAGNOSTIC_ONLY; HISTORICAL_SUPPORT_AS_DECISION_DOMAIN_STATUS=EMPIRICAL_CONTEXT_ONLY; MODEL_BOUND_AUTHORIZED=FALSE; RAW_SHA256=7953e95f532b97f3db1ad42dfb517dc0b5f6e98a80b1f1b0954fc1b52419c489",
            })
    return result


def compute_universe_audit() -> dict[str, int]:
    crop_codes: set[str] = set()
    other_positive: dict[tuple[str, int], set[str]] = defaultdict(set)
    joint_campaign: dict[tuple[str, str], Decimal] = defaultdict(Decimal)
    model = {ubigeo for ubigeo, _ in model_districts()}
    land_columns, land_rows = _read_csv(LAND_PATH)
    if land_columns != ["UBIGEO", "DISTRITO", "AREA_HA", "FUENTE"]:
        raise ValueError("land schema changed")
    land = {row["UBIGEO"]: Decimal(row["AREA_HA"]) for row in land_rows}

    with RAW_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            crop_code = row["COD_CULTIVO"]
            crop_codes.add(crop_code)
            month_code = int(row["MES"])
            year, month = divmod(month_code, 100)
            sowing = _decimal(row["SIEMBRA"])
            if crop_code not in TARGET_CODES and sowing is not None and sowing > 0:
                other_positive[(row["UBIGEO"], year)].add(crop_code)
            if crop_code in TRANSIENT_CROPS and sowing is not None:
                start_year = year if month >= 8 else year - 1
                joint_campaign[(row["UBIGEO"], f"{start_year}/{start_year + 1}")] += sowing

    model_district_years = {(ubigeo, year) for ubigeo in model for year in range(2016, 2024)}
    other_crop_counts = [len(other_positive.get(key, set())) for key in model_district_years]
    exceedances = sum(
        total > land[ubigeo]
        for (ubigeo, _), total in joint_campaign.items()
        if ubigeo in model and ubigeo in land
    )
    return {
        "raw_crop_codes": len(crop_codes),
        "target_crop_codes": len(TARGET_CODES),
        "other_crop_codes": len(crop_codes - TARGET_CODES),
        "model_district_years_2016_2023": len(model_district_years),
        "model_district_years_with_positive_other_crop_sowing": sum(
            bool(other_positive.get(key)) for key in model_district_years
        ),
        "median_positive_other_crop_codes_per_relevant_district_year": statistics.median(other_crop_counts),
        "rice_mad_campaign_totals_exceeding_area_ha": exceedances,
    }


def compute_baseline_coverage() -> dict[str, object]:
    monthly = transient_monthly_data()
    districts = [ubigeo for ubigeo, _ in model_districts()]
    complete_2023_2024: dict[str, int] = {}
    complete_2024_2025: dict[str, int] = {}
    for crop_code, crop_name in TRANSIENT_CROPS.items():
        complete_2023_2024[crop_name] = sum(
            complete_campaign_values(monthly, ubigeo, crop_code, 2023) is not None
            for ubigeo in districts
        )
        complete_2024_2025[crop_name] = sum(
            complete_campaign_values(monthly, ubigeo, crop_code, 2024) is not None
            for ubigeo in districts
        )
    return {
        "latest_complete_campaign_candidate": "2023/2024",
        "rice_complete_districts": complete_2023_2024["ARROZ"],
        "mad_complete_districts": complete_2023_2024["MAIZ AMARILLO DURO"],
        "model_districts": len(districts),
        "partial_2024_2025_campaign_complete_district_crop_rows": sum(complete_2024_2025.values()),
        "source_last_month": max(month_code for _, _, month_code in monthly),
    }


def compute_joint_portfolio_audit() -> dict[str, object]:
    monthly = transient_monthly_data()
    district_periods: dict[str, dict[int, tuple[Decimal, Decimal]]] = defaultdict(dict)
    rice_code, mad_code = tuple(TRANSIENT_CROPS)
    for ubigeo, _ in model_districts():
        for start_year in CAMPAIGN_START_YEARS:
            rice_values = complete_campaign_values(monthly, ubigeo, rice_code, start_year)
            mad_values = complete_campaign_values(monthly, ubigeo, mad_code, start_year)
            if rice_values is None or mad_values is None:
                continue
            district_periods[ubigeo][start_year] = (
                sum(rice_values, Decimal(0)),
                sum(mad_values, Decimal(0)),
            )

    changes: list[tuple[Decimal, Decimal]] = []
    within_rice: list[float] = []
    within_mad: list[float] = []
    for periods in district_periods.values():
        ordered = sorted(periods.items())
        for (previous_year, previous), (current_year, current) in zip(ordered, ordered[1:]):
            if current_year == previous_year + 1:
                changes.append((current[0] - previous[0], current[1] - previous[1]))
        if len(ordered) >= 2:
            rice_mean = sum((values[0] for _, values in ordered), Decimal(0)) / len(ordered)
            mad_mean = sum((values[1] for _, values in ordered), Decimal(0)) / len(ordered)
            within_rice.extend(float(values[0] - rice_mean) for _, values in ordered)
            within_mad.extend(float(values[1] - mad_mean) for _, values in ordered)

    return {
        "joint_complete_district_campaign_observations": sum(len(periods) for periods in district_periods.values()),
        "districts_with_any_joint_complete_campaign": len(district_periods),
        "adjacent_joint_campaign_changes": len(changes),
        "reciprocal_direction_changes": sum(rice * mad < 0 for rice, mad in changes),
        "same_direction_changes": sum(rice * mad > 0 for rice, mad in changes),
        "one_or_both_unchanged": sum(rice * mad == 0 for rice, mad in changes),
        "exact_fixed_total_changes": sum(rice + mad == 0 for rice, mad in changes),
        "within_district_level_correlation": round(statistics.correlation(within_rice, within_mad), 6),
    }


def compute_t3_diagnostics() -> dict[str, dict[str, object]]:
    monthly = transient_monthly_data()
    districts = [ubigeo for ubigeo, _ in model_districts()]
    result: dict[str, dict[str, object]] = {}
    month_names = ("AUG", "SEP", "OCT", "NOV", "DEC", "JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL")
    for crop_code, crop_name in TRANSIENT_CROPS.items():
        profiles: list[list[float]] = []
        profiles_by_district: dict[str, list[list[float]]] = defaultdict(list)
        dominant = Counter()
        for ubigeo in districts:
            for start_year in CAMPAIGN_START_YEARS:
                values = complete_campaign_values(monthly, ubigeo, crop_code, start_year)
                if values is None:
                    continue
                total = sum(values, Decimal(0))
                if total <= 0:
                    continue
                profile = [float(value / total) for value in values]
                profiles.append(profile)
                profiles_by_district[ubigeo].append(profile)
                dominant[month_names[max(range(12), key=lambda index: profile[index])]] += 1

        l1_distances: list[float] = []
        for district_profiles in profiles_by_district.values():
            if len(district_profiles) < 2:
                continue
            mean_profile = [
                sum(profile[index] for profile in district_profiles) / len(district_profiles)
                for index in range(12)
            ]
            l1_distances.extend(
                sum(abs(profile[index] - mean_profile[index]) for index in range(12))
                for profile in district_profiles
            )

        nonzero_months = [sum(value > 0 for value in profile) for profile in profiles]
        result[crop_name] = {
            "complete_positive_district_campaign_profiles": len(profiles),
            "districts_with_positive_complete_profile": len(profiles_by_district),
            "districts_requiring_pooling_or_external_rule": len(districts) - len(profiles_by_district),
            "nonzero_months_min": min(nonzero_months),
            "nonzero_months_median": statistics.median(nonzero_months),
            "nonzero_months_max": max(nonzero_months),
            "median_l1_distance_from_district_mean": round(statistics.median(l1_distances), 6),
            "dominant_campaign_month_counts": dict(sorted(dominant.items())),
            "status": "CANDIDATE_NOT_YET_AUTHORIZED",
            "model_share_parameters_authorized": 0,
        }
    return result


def run_preflight() -> list[str]:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    require(_git("branch", "--show-current") == EXPECTED_BRANCH, "wrong branch")
    require(_git("rev-parse", "HEAD") == EXPECTED_HEAD, "HEAD is not the C0B3 freeze")
    require(_git("show", "-s", "--format=%s", "HEAD") == EXPECTED_SUBJECT, "C0B3 freeze subject mismatch")
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", EXPECTED_HEAD, "HEAD"], cwd=ROOT,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    require(ancestor.returncode == 0, "C0B3 freeze is not an ancestor")

    for relative, expected_hash in {**C0B3_HASHES, **FROZEN_DATA_HASHES}.items():
        path = ROOT / relative
        require(path.is_file(), f"missing frozen file: {relative}")
        if path.is_file():
            require(_sha256(path) == expected_hash, f"frozen hash mismatch: {relative}")

    tracked = _split_lines(_git("diff", "--name-only"))
    staged = _split_lines(_git("diff", "--cached", "--name-only"))
    untracked = _split_lines(_git("ls-files", "--others", "--exclude-standard"))
    require(not tracked, f"tracked files changed: {sorted(tracked)}")
    require(not staged, f"staged files changed: {sorted(staged)}")
    require(untracked == AUTHORIZED_SCOPE, f"persistent scope mismatch: {sorted(untracked)}")

    required_paths = [REGISTRY_PATH, OCCUPANCY_PATH, ADJUSTMENT_PATH, REPORT_PATH, CONFIG_PATH, SCRIPT_PATH, TEST_PATH]
    for path in required_paths:
        require(path.is_file(), f"missing C0B4 file: {path.relative_to(ROOT)}")
    if any(not path.is_file() for path in required_paths):
        return errors

    registry_columns, registry = _read_csv(REGISTRY_PATH)
    occupancy_columns, occupancy = _read_csv(OCCUPANCY_PATH)
    adjustment_columns, adjustment = _read_csv(ADJUSTMENT_PATH)
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    report = REPORT_PATH.read_text(encoding="utf-8")

    require(registry_columns == REGISTRY_COLUMNS, "evidence registry schema mismatch")
    require(occupancy_columns == OCCUPANCY_COLUMNS, "occupancy schema mismatch")
    require(adjustment_columns == ADJUSTMENT_COLUMNS, "adjustment schema mismatch")
    require({row["EVIDENCE_DOMAIN"] for row in registry} <= ALLOWED_EVIDENCE_DOMAINS, "invalid evidence domain")
    evidence_ids = [row["EVIDENCE_ID"] for row in registry]
    require(len(evidence_ids) == len(set(evidence_ids)), "duplicate evidence IDs")
    evidence_set = set(evidence_ids)
    require({f"C0B4-E{number:03d}" for number in range(20, 27)} <= evidence_set, "C0B4A adjudication evidence missing")
    require(all(row["MODEL_ADMISSIBILITY"] != "MODEL_ADMISSIBLE" for row in registry), "evidence row promoted to model parameter")

    require(len(occupancy) == 2, "occupancy table must have two rows")
    require({row["CROP_CODE"] for row in occupancy} == set(TRANSIENT_CROPS), "transient crop codes mismatch")
    require(all(row["CROP_STD"] == TRANSIENT_CROPS[row["CROP_CODE"]] for row in occupancy), "crop labels mismatch")
    referenced = {
        evidence_id
        for row in occupancy for evidence_id in row["EVIDENCE_IDS"].split(";") if evidence_id
    }
    require(referenced <= evidence_set, f"unresolved evidence IDs: {sorted(referenced - evidence_set)}")
    require(all(row["DECISION_RESOLUTION"] == "T3_CAMPAIGN_TOTAL_DECISION_WITH_FUTURE_PRESPECIFIED_EXOGENOUS_WITHIN_CAMPAIGN_SHARES" for row in occupancy), "T3 resolution changed")
    require(all(row["PLANTING_FLOW_ANCHOR"] == "SIEMBRA_MONTHLY_GROSS_SOWN_OR_TRANSPLANTED_AREA_HA" for row in occupancy), "SIEMBRA flow anchor changed")
    require(all(row["OCCUPANCY_DURATION_STATUS"] == "SENSITIVITY_ONLY_RANGE" for row in occupancy), "occupancy duration over-authorized")
    require(all(not row["OCCUPANCY_DURATION_VALUE"] for row in occupancy), "single occupancy value invented")
    expected_ranges = {"ARROZ": ("142", "155"), "MAIZ AMARILLO DURO": ("140", "170")}
    require(all((row["OCCUPANCY_DURATION_LOWER"], row["OCCUPANCY_DURATION_UPPER"]) == expected_ranges[row["CROP_STD"]] for row in occupancy), "sensitivity duration range mismatch")
    require(all(row["SIMULTANEOUS_OCCUPANCY_MAPPING_STATUS"] == "SENSITIVITY_ONLY_NOT_MODEL_AUTHORIZED" for row in occupancy), "occupancy mapping over-authorized")
    require(all(row["AREA_HA_COMPATIBILITY_STATUS"] == "INCOMPATIBLE_WITH_DIRECT_CAMPAIGN_CAP" for row in occupancy), "direct AREA_HA cap authorized")
    require(all(row["REALLOCABLE_LAND_STATUS"] == "NOT_OBSERVED" for row in occupancy), "reallocable land invented")
    require(all(row["LAND_HARD_CAP_STATUS"] == "NOT_AUTHORIZED" for row in occupancy), "land hard cap authorized")
    require(all(row["T3_SHARE_RULE_STATUS"] == "CANDIDATE_NOT_YET_AUTHORIZED" for row in occupancy), "T3 shares over-authorized")

    expected_adjustment = build_adjustment_rows()
    require(adjustment == expected_adjustment, "adjustment audit does not reproduce from raw SIEMBRA")
    require(len(adjustment) == 110, "adjustment audit must have 55 x 2 rows")
    require(len({(row["UBIGEO"], row["CROP_CODE"]) for row in adjustment}) == 110, "duplicate adjustment key")
    require(all(row["BASELINE_STATUS"] == "NOT_YET_FROZEN" for row in adjustment), "baseline year invented")
    require(all(row["OFFICIAL_BOUND_AVAILABLE"] == "FALSE" for row in adjustment), "district official bound invented")
    require(all(row["ADJUSTMENT_BOUND_STATUS"] in {"SENSITIVITY_ONLY", "UNRESOLVED"} for row in adjustment), "adjustment bound over-authorized")
    require(all(not row["AUTHORIZED_LOWER_RULE"] and not row["AUTHORIZED_UPPER_RULE"] for row in adjustment), "numeric bound rule invented")
    require(all(row["MODEL_BOUND_AUTHORIZED"] == "FALSE" for row in adjustment), "historical diagnostic promoted to model bound")

    land = config["land_ontology"]
    require(land["AREA_HA_status"] == "PHYSICAL_AGRICULTURAL_FOOTPRINT_ONLY", "AREA_HA semantics changed")
    require(not land["direct_campaign_hectare_hard_cap_authorized"], "AREA_HA used as campaign hard cap")
    require(not land["perennial_subtraction_yields_reallocable_transient_land"], "perennial residual promoted to reallocable land")
    require(land["other_crop_occupancy_relevant"], "other crops ignored")
    require(not land["all_remaining_physical_land_reallocable"], "residual land declared reallocable")
    require(not land["siembra_month_equals_occupancy_month"], "SIEMBRA month equated to occupancy")
    require(not land["climate_response_window_is_physical_occupancy_window"], "climate window reused as occupancy")
    require(not land["parcel_sequential_cropping_inferred_from_district_aggregates"], "parcel reuse inferred")

    universe = compute_universe_audit()
    require(universe == config["other_crop_universe_audit"], "other-crop universe audit mismatch")
    require(universe == {
        "raw_crop_codes": 96,
        "target_crop_codes": 5,
        "other_crop_codes": 91,
        "model_district_years_2016_2023": 440,
        "model_district_years_with_positive_other_crop_sowing": 429,
        "median_positive_other_crop_codes_per_relevant_district_year": 7,
        "rice_mad_campaign_totals_exceeding_area_ha": 18,
    }, "other-crop audit expected counts changed")

    decision_domain = config["decision_domain_adjudication"]
    require(decision_domain["physical_land_capacity_model_feasibility"] == "NOT_FEASIBLE", "physical land-capacity failure changed")
    require(decision_domain["strategic_transient_decision_domain_feasibility"] == "POTENTIALLY_RECOVERABLE_BUT_NOT_CURRENTLY_MODEL_ADMISSIBLE", "strategic decision-domain status changed")
    require(not decision_domain["land_hard_cap_necessary_for_any_valid_decision_model"], "physical hard cap declared necessary for every architecture")
    require(not decision_domain["alternative_decision_domain_currently_authorized"], "alternative decision domain silently authorized")

    require(config["reallocable_land"]["status"] == "NOT_OBSERVED", "reallocable land status mismatch")
    require(config["land_hard_cap"]["status"] == "NOT_AUTHORIZED", "land hard-cap status mismatch")
    require(config["baseline"]["status"] == "NOT_YET_FROZEN", "baseline status mismatch")
    require(config["baseline"]["year"] is None, "baseline year invented")
    baseline = config["baseline"]
    require(baseline["latest_complete_period_status"] == "NOT_AVAILABLE_AS_COMMON_DISTRICT_CROP_BASELINE", "latest year silently selected as common baseline")
    require(baseline["latest_complete_period_diagnostics"] == compute_baseline_coverage(), "latest-period coverage audit mismatch")
    require(baseline["multiyear_reference_status"] == "METHOD_DEFINED_BUT_NOT_SOURCE_MANDATED", "historical median silently selected as baseline")
    require(not baseline["district_official_planning_baseline_available"], "district official planning baseline invented")
    require(not baseline["pcr_agency_hectares_as_district_baseline_authorized"], "PCR agency hectares used as district baseline")

    historical_support = config["historical_support_decision_domain"]
    require(historical_support["status"] == "EMPIRICAL_CONTEXT_ONLY", "historical support promoted to decision domain")
    require(not historical_support["historical_convex_hull_authorized"], "historical convex hull promoted to feasible set")
    require(not historical_support["historically_observed_equals_future_feasible"], "historical observation equated to future feasibility")
    require(not historical_support["current_feasible_set_authorized"], "historical feasible set silently authorized")

    fixed_total = config["fixed_total_rice_mad_composition_domain"]
    joint_audit = compute_joint_portfolio_audit()
    require(fixed_total["status"] == "NOT_SUPPORTED", "fixed Rice-MAD total authorized without substitution evidence")
    require(not fixed_total["crop_substitutability_established"], "Rice-MAD substitutability invented")
    require(not fixed_total["negative_correlation_proves_substitutability"], "negative correlation treated as substitution proof")
    for key, value in joint_audit.items():
        if key != "districts_with_any_joint_complete_campaign":
            require(fixed_total[key] == value, f"joint portfolio audit mismatch: {key}")

    crop_specific = config["crop_specific_baseline_relative_domain"]
    require(crop_specific["status"] == "SENSITIVITY_ONLY_NOT_MODEL_AUTHORIZED", "crop-specific decision domain over-authorized")
    require(not crop_specific["historical_variation_is_authorized_bound"], "historical variation promoted to bound")
    soft_bound = config["soft_policy_adjustment_bound"]
    require(soft_bound["ontology_allowed_by_c0b1"] == "YES_CONDITIONAL_ON_PROSPECTIVE_PRESPECIFIED_EVIDENCE_RULE", "soft-bound ontology status changed")
    require(not soft_bound["actual_bound_exists"], "soft policy bound invented")
    require(not soft_bound["model_authorized"], "soft policy bound promoted to model bound")
    require(not soft_bound["arbitrary_percentage_allowed"], "arbitrary percentage bound authorized")

    require(config["t3_share_rule"]["ARROZ"]["status"] == "CANDIDATE_NOT_YET_AUTHORIZED", "rice T3 status mismatch")
    require(config["t3_share_rule"]["MAIZ AMARILLO DURO"]["status"] == "CANDIDATE_NOT_YET_AUTHORIZED", "MAD T3 status mismatch")
    require(compute_t3_diagnostics() == config["t3_share_diagnostics"], "T3 diagnostics mismatch")
    require(config["model_authorized_land_parameters_n"] == 0, "land parameter invented")
    require(config["model_authorized_adjustment_bounds_n"] == 0, "adjustment bound invented")
    require(config["decision_feasibility_endstate"] == "DECISION_MODEL_NOT_YET_FEASIBLE", "decision endstate mismatch")
    require(config["decision_feasibility_endstate_definition"] == "NO_MODEL_ADMISSIBLE_CONTINUOUS_NUMERICAL_RICE_MAD_ALLOCATION_DOMAIN_IS_CURRENTLY_IDENTIFIED", "decision endstate definition weakened")
    require(config["numerical_optimization_feasibility"] == "NOT_AUTHORIZED", "optimization authorized while decision domain is unidentified")

    future_gate = config["future_decision_domain_gate"]
    require(future_gate["required"], "next decision-domain gate bypassed")
    require(future_gate["minimum_defensible_decision_scope_candidate"] == "FINITE_PRESPECIFIED_OBSERVED_PORTFOLIOS_FOR_SUPPORTED_DISTRICTS_REQUIRES_FORMAL_SCOPE_ADJUDICATION", "minimum future candidate changed")
    require(future_gate["finite_prespecified_decision_alternatives_status"] == "POTENTIALLY_FEASIBLE_AS_SCENARIO_EVALUATION_REQUIRES_FORMAL_REFRAMING", "finite-alternative status changed")
    require(not future_gate["finite_portfolio_candidate_currently_authorized"], "finite portfolio candidate marked currently feasible")
    require(not future_gate["historical_portfolios_selected"], "historical portfolios silently selected")
    require(not future_gate["finite_scenario_evaluation_is_continuous_optimization"], "scenario evaluation mislabeled continuous optimization")

    allowed_inputs = set(config["input_firewall"]["allowed_computational_fields"])
    forbidden_inputs = set(config["input_firewall"]["forbidden_selection_inputs"])
    require(allowed_inputs == {"UBIGEO", "DISTRICT_NAME", "COD_CULTIVO", "CULTIVO", "ANO", "MES", "SIEMBRA", "VERDE_ACTUAL", "AREA_HA"}, "computational field allowlist changed")
    require(allowed_inputs.isdisjoint(forbidden_inputs), "outcome leakage in allowed fields")
    require(forbidden_inputs == {"YIELD", "PRODUCCION", "YIELD_RAW", "CLIMATE_RESPONSE_COEFFICIENT", "ECONOMETRIC_P_VALUE", "ENSO_SCENARIO_PERFORMANCE", "PROFIT", "GVP", "CVAR", "OPTIMIZER_OBJECTIVE_VALUE"}, "outcome firewall vocabulary changed")

    authorizations = config["authorizations"]
    require(not authorizations["land_hard_cap"], "land hard cap authorized")
    require(not authorizations["reallocable_transient_land"], "reallocable land authorized")
    require(not authorizations["occupancy_kernel"], "occupancy kernel authorized")
    require(not authorizations["adjustment_bound"], "adjustment bound authorized")
    require(not authorizations["t3_share_rule"], "T3 share rule authorized")
    require(not authorizations["continuous_decision_domain"], "continuous decision domain authorized")
    require(not authorizations["finite_portfolio_decision_set"], "finite portfolio set authorized")
    require(not authorizations["finite_scenario_evaluation"], "finite scenario evaluation authorized")
    require(not authorizations["water_model"], "water model authorized")
    require(not authorizations["water_hard_constraint"], "water hard constraint authorized")
    require(not authorizations["optimizer"], "optimizer authorized")

    registry_blob = "\n".join(row["NOTES"] for row in registry)
    for source_name, expected_hash in EXTERNAL_PDF_HASHES.items():
        require(f"{source_name}_SHA256={expected_hash}" in registry_blob, f"external PDF provenance missing: {source_name}")

    headings = [f"## {number}. {title}" for number, title in enumerate([
        "Executive verdict", "Frozen upstream identity", "Physical land ontology",
        "AREA_HA interpretation", "Five-crop vs full agricultural universe",
        "Fixed perennial-stock implications", "Rice occupancy evidence",
        "MAD occupancy evidence", "Sequential-cropping limitation",
        "Simultaneous occupancy mapping", "Reallocable-land evidence",
        "Land-hard-cap adjudication", "Historical Rice adjustment diagnostics",
        "Historical MAD adjustment diagnostics", "Adjustment-bound adjudication",
        "Baseline status", "T3 within-campaign share evidence", "T3 share adjudication",
        "Implications for future decision model", "Forbidden interpretations",
        "Remaining gaps", "Final C0B4 verdict",
    ], start=1)]
    require(all(heading in report for heading in headings), "report section missing")
    for token in (
        "AREA_HA_STATUS=PHYSICAL_AGRICULTURAL_FOOTPRINT_ONLY",
        "OTHER_CROP_OCCUPANCY_RELEVANT=TRUE",
        "CLIMATE_RESPONSE_WINDOW != PHYSICAL_LAND_OCCUPANCY_WINDOW",
        "SIEMBRA_m != OCCUPANCY_m",
        "PERENNIAL_SUBTRACTION_AS_REALLOCABLE_TRANSIENT_LAND=NOT_AUTHORIZED",
        "REALLOCABLE_TRANSIENT_LAND_STATUS=NOT_OBSERVED",
        "LAND_HARD_CAP_STATUS=NOT_AUTHORIZED",
        "BASELINE_YEAR_STATUS=NOT_YET_FROZEN",
        "MODEL_AUTHORIZED_LAND_PARAMETERS_N=0",
        "MODEL_AUTHORIZED_ADJUSTMENT_BOUNDS_N=0",
        "C0B4_DECISION_ENDSTATE=DECISION_MODEL_NOT_YET_FEASIBLE",
        "PHYSICAL_LAND_CAPACITY_MODEL_FEASIBILITY=NOT_FEASIBLE",
        "STRATEGIC_TRANSIENT_DECISION_DOMAIN_FEASIBILITY=POTENTIALLY_RECOVERABLE_BUT_NOT_CURRENTLY_MODEL_ADMISSIBLE",
        "LAND_HARD_CAP_NECESSARY_FOR_ANY_VALID_DECISION_MODEL=NO",
        "LATEST_COMPLETE_PERIOD_BASELINE_STATUS=NOT_AVAILABLE_AS_COMMON_DISTRICT_CROP_BASELINE",
        "MULTIYEAR_REFERENCE_BASELINE_STATUS=METHOD_DEFINED_BUT_NOT_SOURCE_MANDATED",
        "DISTRICT_OFFICIAL_PLANNING_BASELINE_AVAILABLE=FALSE",
        "HISTORICAL_SUPPORT_AS_DECISION_DOMAIN_STATUS=EMPIRICAL_CONTEXT_ONLY",
        "HISTORICAL_CONVEX_HULL_AUTHORIZED=FALSE",
        "FIXED_TOTAL_RICE_MAD_COMPOSITION_MODEL_STATUS=NOT_SUPPORTED",
        "CROP_SPECIFIC_BASELINE_RELATIVE_DOMAIN_STATUS=SENSITIVITY_ONLY_NOT_MODEL_AUTHORIZED",
        "FINITE_SCENARIO_EVALUATION != CONTINUOUS_CROP_ALLOCATION_OPTIMIZATION",
        "NUMERICAL_OPTIMIZATION_FEASIBILITY=NOT_AUTHORIZED",
        "NEXT_DECISION_DOMAIN_GATE_REQUIRED=TRUE",
    ):
        require(token in report, f"report token missing: {token}")

    imported_modules: set[str] = set()
    for path in (SCRIPT_PATH, TEST_PATH):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.add(node.module)
    forbidden_modules = {"pulp", "cvxpy", "pyomo", "scipy.optimize"}
    require(not any(module in forbidden_modules or module.startswith("scipy.optimize.") for module in imported_modules), "optimizer implementation detected")
    require(config["final_status"] == "PASS_FOR_FINAL_INDEPENDENT_C0B4_FREEZE_AUDIT", "final C0B4 status mismatch")
    return errors


def main() -> int:
    errors = run_preflight()
    if errors:
        for error in errors:
            print(f"C0B4_PREFLIGHT_ERROR={error}")
        print("C0B3_IMMUTABILITY_GATE=FAIL")
        print("PERSISTENT_SCOPE_GATE=FAIL")
        print("NO_OUTCOME_LEAKAGE_GATE=FAIL")
        print("NO_INVENTED_LAND_GATE=FAIL")
        print("NO_WATER_MODEL_GATE=FAIL")
        print("NO_OPTIMIZATION_GATE=FAIL")
        print("C0B4_PREFLIGHT=FAIL")
        return 1

    print("C0B3_IMMUTABILITY_GATE=PASS")
    print("PERSISTENT_SCOPE_GATE=PASS")
    print("NO_OUTCOME_LEAKAGE_GATE=PASS")
    print("NO_INVENTED_LAND_GATE=PASS")
    print("NO_WATER_MODEL_GATE=PASS")
    print("NO_OPTIMIZATION_GATE=PASS")
    print("C0B4_PREFLIGHT=PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
