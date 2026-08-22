"""Read-only preflight and deterministic diagnostics for C0B5."""

from __future__ import annotations

import csv
import hashlib
import itertools
import json
import subprocess
import sys
from decimal import Decimal
from fractions import Fraction
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_BRANCH = "phase/c0b5-decision-domain-adjudication-v1"
EXPECTED_HEAD = "c7ac7b870cf76d6ed2d199d5619e07f6bb32f6cb"
EXPECTED_SUBJECT = "Freeze C0B4 land adjustment feasibility"

REGISTRY_PATH = ROOT / "outputs/decision_feasibility/C0B5_DECISION_DOMAIN_EVIDENCE_REGISTRY.csv"
ROUTES_PATH = ROOT / "outputs/decision_feasibility/C0B5_ROUTE_ADJUDICATION.csv"
PORTFOLIO_PATH = ROOT / "outputs/decision_feasibility/C0B5_FINITE_PORTFOLIO_AUDIT.csv"
REPORT_PATH = ROOT / "outputs/decision_feasibility/C0B5_DECISION_DOMAIN_REPORT.md"
CONFIG_PATH = ROOT / "config/decision_ontology/decision_domain_adjudication_v1.json"
SCRIPT_PATH = ROOT / "scripts/c0b5_decision_domain_preflight.py"
TEST_PATH = ROOT / "tests/test_c0b5_decision_domain.py"

RAW_PATH = ROOT / "data/raw/Formato_dataset_productos_dra__ (2).csv"
MODEL_DISTRICTS_PATH = ROOT / "outputs/decision_feasibility/C0B2_DISTRICT_SPATIAL_ELIGIBILITY.csv"

AUTHORIZED_SCOPE = {
    "outputs/decision_feasibility/C0B5_DECISION_DOMAIN_EVIDENCE_REGISTRY.csv",
    "outputs/decision_feasibility/C0B5_ROUTE_ADJUDICATION.csv",
    "outputs/decision_feasibility/C0B5_FINITE_PORTFOLIO_AUDIT.csv",
    "outputs/decision_feasibility/C0B5_DECISION_DOMAIN_REPORT.md",
    "config/decision_ontology/decision_domain_adjudication_v1.json",
    "scripts/c0b5_decision_domain_preflight.py",
    "tests/test_c0b5_decision_domain.py",
}

C0B4_HASHES = {
    "outputs/decision_feasibility/C0B4_LAND_EVIDENCE_REGISTRY.csv": "5176822690c51d0621ab4cbd16c29ce7f184af52226b448a37cf7ab05198afab",
    "outputs/decision_feasibility/C0B4_TRANSIENT_OCCUPANCY_ADJUDICATION.csv": "1cbf03a51e6de2f6ddba3bcccff43ae9ba8b0d38822b08f3731d54a8e5d4bb76",
    "outputs/decision_feasibility/C0B4_ADJUSTMENT_ENVELOPE_AUDIT.csv": "6b66389af0edbdcf8149ccc8e159fe64cf9b6b79ee7df7a852483434f87cadab",
    "outputs/decision_feasibility/C0B4_LAND_ADJUSTMENT_REPORT.md": "20ba44d5a9fceb37d7458c0fe0a24afc2fe42eaf06376fd9958df3165a728c43",
    "config/decision_ontology/transient_land_adjustment_v1.json": "e96ca212221a7ebf8262fb8b7bff04d142a51c999dccecc5543e3378f288fa7e",
    "scripts/c0b4_land_adjustment_preflight.py": "96e2da2b119c88e8a74db07e3fe214d2e0a6e9a02100dfe427d4cc5e5c4197ee",
    "tests/test_c0b4_land_adjustment.py": "44f6e4de2ff8ebbfae53eab0ce13370cac0611ebcc9b74d4610249c3dd0cf05c",
}

FROZEN_DATA_HASHES = {
    "data/raw/Formato_dataset_productos_dra__ (2).csv": "7953e95f532b97f3db1ad42dfb517dc0b5f6e98a80b1f1b0954fc1b52419c489",
    "outputs/decision_feasibility/C0B2_DISTRICT_SPATIAL_ELIGIBILITY.csv": "a394b4727a7cb8a649ffd82fc704ab5db42d2673fc174a68c20e279146e875ad",
    "config/decision_ontology/perennial_state_adjudication_v1.json": "35d752b94b2aaf29e3b7f1512fa817ca18af8c817455a60467a1cc31cab2e86e",
}

TRANSIENT_CROPS = {
    "14010020000": "ARROZ",
    "14010070000": "MAIZ AMARILLO DURO",
}
CAMPAIGN_START_YEARS = tuple(range(2015, 2024))
CAMPAIGN_MONTHS = (8, 9, 10, 11, 12, 1, 2, 3, 4, 5, 6, 7)
SELECTED_ARCHITECTURE = (
    "ROUTE_B_FINITE_PRESPECIFIED_EMPIRICALLY_REALIZED_"
    "REFERENCE_CONFIGURATION_ANALYSIS"
)
SHORT_ANALYTICAL_LABEL = "RISK_AWARE_FINITE_REFERENCE_CONFIGURATION_ANALYSIS"
EXPECTED_ALTERNATIVES = (
    ("C0B5-A2020-2021", "2020/2021", 2020),
    ("C0B5-A2023-2024", "2023/2024", 2023),
)
EXPECTED_DISTRICTS = (
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
EXPECTED_COVERAGE_FRONTIER = {
    2: (13, ((2020, 2023),)),
    3: (9, ((2017, 2019, 2020), (2019, 2020, 2023))),
    4: (7, ((2017, 2019, 2020, 2023),)),
    5: (5, ((2016, 2017, 2019, 2020, 2023),)),
    6: (3, (
        (2015, 2016, 2017, 2019, 2020, 2023),
        (2016, 2017, 2019, 2020, 2021, 2023),
    )),
    7: (2, ((2016, 2017, 2018, 2019, 2020, 2021, 2023),)),
    8: (0, tuple(itertools.combinations(CAMPAIGN_START_YEARS, 8))),
    9: (0, (CAMPAIGN_START_YEARS,)),
}
SELECTION_FIELDS = {
    "UBIGEO",
    "DISTRICT_NAME",
    "COD_CULTIVO",
    "CULTIVO",
    "MES",
    "SIEMBRA",
    "ROW_PRESENCE",
    "BLANK_STATUS",
    "CAMPAIGN_COMPLETENESS",
}

REGISTRY_COLUMNS = [
    "EVIDENCE_ID", "EVIDENCE_DOMAIN", "SOURCE_TIER", "SOURCE_AUTHORITY",
    "SOURCE_TITLE", "SOURCE_DATE", "SOURCE_URL", "PAGE_OR_SECTION",
    "GEOGRAPHIC_LEVEL", "TEMPORAL_SCOPE", "CROP_SCOPE", "RAW_TERM",
    "EXACT_FINDING", "QUANTITATIVE_VALUE", "UNIT", "ROUTE_RELEVANCE",
    "MODEL_ADMISSIBILITY", "LIMITATION", "NOTES",
]
ALLOWED_EVIDENCE_DOMAINS = {
    "PROSPECTIVE_PLANTING_INTENTION", "OFFICIAL_PROGRAMMED_AREA", "BASELINE",
    "ADJUSTMENT_RULE", "HISTORICAL_CONFIGURATION", "CAMPAIGN_COMPLETENESS",
    "DISTRICT_COVERAGE", "TIMING_PROFILE", "SUBSTITUTABILITY",
    "FINITE_DECISION_SET", "RQ_COMPATIBILITY", "OTHER",
}
ROUTE_COLUMNS = [
    "ROUTE_ID", "ROUTE_NAME", "BASELINE_REQUIREMENT", "ADJUSTMENT_REQUIREMENT",
    "LAND_CAP_REQUIREMENT", "SUBSTITUTABILITY_REQUIREMENT",
    "FINITE_SET_REQUIREMENT", "TIMING_REQUIREMENT", "SPATIAL_SCOPE_REQUIREMENT",
    "EVIDENCE_STATUS", "CRITICAL_BLOCKERS", "AUTHORIZATION_STATUS",
    "SCIENTIFIC_INTERPRETATION", "RQ_IMPLICATION", "EVIDENCE_IDS", "NOTES",
]
PORTFOLIO_COLUMNS = [
    "ALTERNATIVE_ID", "SOURCE_CAMPAIGN", "ALTERNATIVE_LEVEL",
    "DISTRICT_SCOPE_RULE", "RICE_NUMERIC_COMPLETE", "MAD_NUMERIC_COMPLETE",
    "TIMING_PROFILE_COMPLETE", "MISSING_AS_ZERO_USED", "EMPIRICALLY_REALIZED",
    "WHOLE_CONFIGURATION", "DISTRICT_MIX_AND_MATCH",
    "FIXED_PERENNIAL_COMPATIBLE", "WATER_FEASIBILITY_CLAIM",
    "FUTURE_PHYSICAL_FEASIBILITY_CLAIM", "REFERENCE_CONFIGURATION_ADMISSIBILITY",
    "EXCLUSION_REASON", "NOTES",
]

SEMANTIC_REJECTION_GATES = {
    "AREA_HA_RESCUED_CAPACITY",
    "ARBITRARY_PERCENTAGE_BOUNDS",
    "HISTORICAL_EXTREMA_AS_MODEL_BOUNDS",
    "HISTORICAL_CONVEX_HULL_AS_CONTINUOUS_DOMAIN",
    "RICE_MAD_FIXED_TOTAL_WITHOUT_SUBSTITUTION_EVIDENCE",
    "OUTCOME_TUNED_BASELINE",
    "OUTCOME_TUNED_ALTERNATIVES",
    "ENSO_YEAR_SELECTION",
    "HIGH_YIELD_OR_HIGH_PROFIT_YEAR_SELECTION",
    "MISSING_AS_ZERO",
    "DISTRICT_MIX_AND_MATCH",
    "HISTORICAL_REALIZATION_AS_GUARANTEED_FUTURE_FEASIBILITY",
    "HISTORICAL_PERENNIAL_STOCK_IMPORT",
    "WATER_FEASIBILITY_CLAIM",
    "CONTINUOUS_OPTIMIZATION_AFTER_ROUTE_A_FAILURE",
    "FINITE_RANKING_OR_OPTIMIZATION_IN_C0B5",
    "MULTIPLE_SELECTED_ROUTES",
    "NO_SELECTED_ROUTE",
    "C0B4_MODIFICATION",
    "OLD_ROUTE_B_ARCHITECTURE_LABEL",
    "DECISION_ANALYSIS_IMPLIES_FUTURE_FEASIBILITY",
    "HISTORICAL_REALIZATION_EQUALS_FUTURE_FEASIBILITY",
    "REPRESENTATIVE_PIURA_CLAIM",
    "ALTERNATIVE_INTERPOLATION",
    "CROP_YEAR_MIXING",
    "TIMING_PROFILE_MIXING",
    "GENERIC_T3_FROM_ALTERNATIVE_TIMING",
    "ARBITRARY_K2_SELECTION",
    "LEXICOGRAPHIC_TIEBREAK_FALSELY_INVOKED",
    "UNFROZEN_ALTERNATIVE_OR_SCOPE",
}


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


def _decimal(value: str | None) -> Decimal | None:
    if value is None or not value.strip():
        return None
    return Decimal(value)


def _bool(value: bool) -> str:
    return "TRUE" if value else "FALSE"


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
        value = monthly[key]
        assert value is not None
        values.append(value)
    return values


def joint_complete_districts(
    monthly: dict[tuple[str, str, int], Decimal | None],
    start_year: int,
) -> set[str]:
    complete: set[str] = set()
    for ubigeo, _ in model_districts():
        if all(
            complete_campaign_values(monthly, ubigeo, crop_code, start_year) is not None
            for crop_code in TRANSIENT_CROPS
        ):
            complete.add(ubigeo)
    return complete


def compute_coverage_frontier() -> dict[int, tuple[int, tuple[tuple[int, ...], ...]]]:
    monthly = transient_monthly_data()
    coverage = {
        year: joint_complete_districts(monthly, year)
        for year in CAMPAIGN_START_YEARS
    }
    frontier: dict[int, tuple[int, tuple[tuple[int, ...], ...]]] = {}
    for count in range(2, len(CAMPAIGN_START_YEARS) + 1):
        candidates = []
        for years in itertools.combinations(CAMPAIGN_START_YEARS, count):
            common = set.intersection(*(coverage[year] for year in years))
            candidates.append((len(common), years))
        maximum = max(district_count for district_count, _ in candidates)
        winners = tuple(years for district_count, years in candidates if district_count == maximum)
        frontier[count] = (maximum, winners)
    return frontier


def compute_scope_selection() -> dict[str, object]:
    monthly = transient_monthly_data()
    coverage = {
        year: joint_complete_districts(monthly, year)
        for year in CAMPAIGN_START_YEARS
    }
    candidates: list[tuple[int, int, tuple[int, ...], set[str]]] = []
    for count in range(2, len(CAMPAIGN_START_YEARS) + 1):
        for years in itertools.combinations(CAMPAIGN_START_YEARS, count):
            common = set.intersection(*(coverage[year] for year in years))
            candidates.append((len(common), len(years), years, common))
    candidates.sort(key=lambda item: (-item[0], -item[1], item[2]))
    district_count, _, seed_years, scope = candidates[0]
    admitted = tuple(
        year for year in CAMPAIGN_START_YEARS if scope <= coverage[year]
    )
    names = dict(model_districts())
    return {
        "authorized_districts_n": district_count,
        "authorized_districts": tuple((code, names[code]) for code in sorted(scope)),
        "seed_years": seed_years,
        "admitted_years": admitted,
        "coverage": coverage,
    }


def configuration_fingerprint(
    monthly: dict[tuple[str, str, int], Decimal | None],
    scope: tuple[str, ...],
    start_year: int,
) -> tuple[str, dict[str, Decimal], int]:
    rows: list[list[object]] = []
    totals = {crop_code: Decimal(0) for crop_code in TRANSIENT_CROPS}
    for ubigeo in scope:
        for crop_code in TRANSIENT_CROPS:
            values = complete_campaign_values(monthly, ubigeo, crop_code, start_year)
            if values is None:
                raise ValueError("fingerprint requested for incomplete configuration")
            totals[crop_code] += sum(values, Decimal(0))
            for campaign_month, value in enumerate(values, 1):
                rows.append([ubigeo, crop_code, campaign_month, format(value, "f")])
    payload = json.dumps(rows, ensure_ascii=True, separators=(",", ":")) + "\n"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest(), totals, len(rows)


def compute_reference_diagnostics() -> dict[str, object]:
    selection = compute_scope_selection()
    scope_pairs = selection["authorized_districts"]
    assert isinstance(scope_pairs, tuple)
    scope = tuple(code for code, _ in scope_pairs)
    monthly = transient_monthly_data()

    campaign_totals: dict[int, dict[str, Decimal]] = {}
    profile_totals: dict[int, dict[tuple[str, str], Decimal]] = {}
    timing_profiles: dict[int, dict[tuple[str, str], tuple[Fraction, ...]]] = {}
    for year in (2020, 2023):
        campaign_totals[year] = {crop: Decimal(0) for crop in TRANSIENT_CROPS}
        profile_totals[year] = {}
        timing_profiles[year] = {}
        for ubigeo in scope:
            for crop in TRANSIENT_CROPS:
                values = complete_campaign_values(monthly, ubigeo, crop, year)
                if values is None:
                    raise ValueError("diagnostic requested for incomplete reference configuration")
                total = sum(values, Decimal(0))
                if total <= 0:
                    raise ValueError("reference timing profile has non-positive total")
                key = (ubigeo, crop)
                campaign_totals[year][crop] += total
                profile_totals[year][key] = total
                shares = tuple(Fraction(value) / Fraction(total) for value in values)
                if sum(shares, Fraction(0)) != Fraction(1):
                    raise ValueError("reference timing profile does not normalize exactly")
                timing_profiles[year][key] = shares

    keys = sorted(profile_totals[2020])
    differences = [abs(profile_totals[2020][key] - profile_totals[2023][key]) for key in keys]
    timing_differences = [
        sum(
            (abs(left - right) for left, right in zip(
                timing_profiles[2020][key], timing_profiles[2023][key]
            )),
            Fraction(0),
        )
        for key in keys
    ]
    return {
        "expected_numeric_cells": 2 * len(scope) * len(TRANSIENT_CROPS),
        "observed_complete_numeric_cells": sum(len(values) for values in profile_totals.values()),
        "missing_numeric_cells": 0,
        "timing_profiles_complete": {year: len(profiles) for year, profiles in timing_profiles.items()},
        "campaign_totals": campaign_totals,
        "alternative_l1_distance_ha": sum(differences, Decimal(0)),
        "alternative_different_cells_n": sum(value != 0 for value in differences),
        "alternative_equal_cells_n": sum(value == 0 for value in differences),
        "timing_different_profiles_n": sum(value != 0 for value in timing_differences),
    }


def build_portfolio_rows() -> list[dict[str, str]]:
    selection = compute_scope_selection()
    scope_pairs = selection["authorized_districts"]
    assert isinstance(scope_pairs, tuple)
    scope = tuple(code for code, _ in scope_pairs)
    admitted = set(selection["admitted_years"])
    monthly = transient_monthly_data()
    rows: list[dict[str, str]] = []
    for year in CAMPAIGN_START_YEARS:
        rice_count = sum(
            complete_campaign_values(monthly, code, "14010020000", year) is not None
            for code in scope
        )
        mad_count = sum(
            complete_campaign_values(monthly, code, "14010070000", year) is not None
            for code in scope
        )
        joint_count = sum(
            all(
                complete_campaign_values(monthly, code, crop, year) is not None
                for crop in TRANSIENT_CROPS
            )
            for code in scope
        )
        is_admitted = year in admitted
        if is_admitted:
            fingerprint, totals, values_n = configuration_fingerprint(monthly, scope, year)
            notes = (
                f"13 districts x 2 crops x 12 present numeric months = {values_n} values; "
                f"Rice={totals['14010020000']} ha; MAD={totals['14010070000']} ha; "
                f"CONFIGURATION_SHA256={fingerprint}."
            )
        else:
            notes = (
                f"RICE_COMPLETE={rice_count}/13; MAD_COMPLETE={mad_count}/13; "
                f"JOINT_COMPLETE={joint_count}/13; no missing value was converted to zero."
            )
        rows.append({
            "ALTERNATIVE_ID": f"C0B5-A{year}-{year + 1}",
            "SOURCE_CAMPAIGN": f"{year}/{year + 1}",
            "ALTERNATIVE_LEVEL": "EMPIRICALLY_REALIZED_REFERENCE_CONFIGURATION",
            "DISTRICT_SCOPE_RULE": "COVERAGE_QUALIFIED_COMMON_SUPPORT_SUBREGIONAL_SCOPE",
            "RICE_NUMERIC_COMPLETE": _bool(is_admitted),
            "MAD_NUMERIC_COMPLETE": _bool(is_admitted),
            "TIMING_PROFILE_COMPLETE": _bool(is_admitted),
            "MISSING_AS_ZERO_USED": "FALSE",
            "EMPIRICALLY_REALIZED": "TRUE",
            "WHOLE_CONFIGURATION": _bool(is_admitted),
            "DISTRICT_MIX_AND_MATCH": "FALSE",
            "FIXED_PERENNIAL_COMPATIBLE": "TRUE",
            "WATER_FEASIBILITY_CLAIM": "FALSE",
            "FUTURE_PHYSICAL_FEASIBILITY_CLAIM": "FALSE",
            "REFERENCE_CONFIGURATION_ADMISSIBILITY": (
                "ADMISSIBLE_REFERENCE_CONFIGURATION" if is_admitted else "NOT_ADMISSIBLE"
            ),
            "EXCLUSION_REASON": "" if is_admitted else (
                "INCOMPLETE_RICE_AND_OR_MAD_MONTHLY_DATA_FOR_AUTHORIZED_SCOPE"
            ),
            "NOTES": notes,
        })
    return rows


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_preflight() -> list[str]:
    require(_git("branch", "--show-current") == EXPECTED_BRANCH, "wrong C0B5 branch")
    require(_git("rev-parse", "HEAD") == EXPECTED_HEAD, "wrong C0B4 frozen parent")
    require(_git("show", "-s", "--format=%s", "HEAD") == EXPECTED_SUBJECT, "wrong parent subject")
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", EXPECTED_HEAD, "HEAD"], cwd=ROOT,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    require(ancestor.returncode == 0, "C0B4 is not an ancestor")

    for relative, expected in {**C0B4_HASHES, **FROZEN_DATA_HASHES}.items():
        require(_sha256(ROOT / relative) == expected, f"frozen hash changed: {relative}")
    frozen_paths = [*C0B4_HASHES, *FROZEN_DATA_HASHES]
    changed = set(filter(None, _git("diff", "--name-only", "--", *frozen_paths).splitlines()))
    changed |= set(filter(None, _git("diff", "--cached", "--name-only", "--", *frozen_paths).splitlines()))
    require(not changed, f"frozen paths modified: {sorted(changed)}")

    tracked = set(filter(None, _git("diff", "--name-only").splitlines()))
    tracked |= set(filter(None, _git("diff", "--cached", "--name-only").splitlines()))
    untracked = {
        line.replace("\\", "/")
        for line in _git("ls-files", "--others", "--exclude-standard").splitlines()
        if line
    }
    require(not tracked, f"tracked or staged diff exists: {sorted(tracked)}")
    require(untracked == AUTHORIZED_SCOPE, f"C0B5 scope mismatch: {sorted(untracked)}")

    registry_columns, registry = _read_csv(REGISTRY_PATH)
    route_columns, routes = _read_csv(ROUTES_PATH)
    portfolio_columns, portfolio = _read_csv(PORTFOLIO_PATH)
    require(registry_columns == REGISTRY_COLUMNS, "evidence registry schema mismatch")
    require(route_columns == ROUTE_COLUMNS, "route adjudication schema mismatch")
    require(portfolio_columns == PORTFOLIO_COLUMNS, "finite portfolio schema mismatch")
    require(len({row["EVIDENCE_ID"] for row in registry}) == len(registry), "duplicate evidence ID")
    require(
        all(row["EVIDENCE_DOMAIN"] in ALLOWED_EVIDENCE_DOMAINS for row in registry),
        "unsupported evidence domain",
    )

    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    report = REPORT_PATH.read_text(encoding="utf-8")
    require(config["frozen_parent"]["c0b4_freeze"] == EXPECTED_HEAD, "C0B4 identity mismatch")
    require(config["route_hierarchy"]["test_order"] == ["ROUTE_A", "ROUTE_B", "ROUTE_C"], "route order changed")
    require(config["route_hierarchy"]["selected_routes_n"] == 1, "selected route count mismatch")
    require(not config["route_hierarchy"]["preference_scoring_used"], "preference scoring used")
    require(not config["route_hierarchy"]["ad_hoc_hybrid_used"], "ad hoc hybrid used")

    route_by_id = {row["ROUTE_ID"]: row for row in routes}
    require(set(route_by_id) == {"ROUTE_A", "ROUTE_B", "ROUTE_C"}, "route rows mismatch")
    selected = [row for row in routes if row["AUTHORIZATION_STATUS"] == "SELECTED"]
    require(len(selected) == 1 and selected[0]["ROUTE_ID"] == "ROUTE_B", "Route B not uniquely selected")
    require(config["route_a"]["status"] == "NOT_SUPPORTED", "Route A status changed")
    require(config["route_a"]["baseline_status"] == "OFFICIAL_NON_DISTRICT_BASELINE_NOT_USABLE", "Route A baseline invented")
    require(config["route_a"]["adjustment_rule_status"] == "NOT_AVAILABLE", "Route A adjustment rule invented")
    require(not config["route_a"]["operationally_numerical_before_optimization"], "Route A incorrectly numerical")

    search = config["targeted_official_evidence_search"]
    require(search["enis_2026_2027_exists"], "ENIS 2026/2027 omitted")
    require(search["enis_crops_include_rice"] and search["enis_crops_include_mad"], "ENIS crop scope mismatch")
    require(not search["public_numeric_piura_district_rice_table_identified"], "unsupported Rice district table")
    require(not search["public_numeric_piura_district_mad_table_identified"], "unsupported MAD district table")
    require(not search["public_piura_district_crop_adjustment_envelope_identified"], "unsupported adjustment envelope")
    require(not search["regional_or_national_values_disaggregated_to_districts"], "silent district disaggregation")

    selection = compute_scope_selection()
    require(selection["authorized_districts_n"] == 13, "supported district count mismatch")
    require(selection["seed_years"] == (2020, 2023), "coverage-maximizing seed campaigns changed")
    require(selection["admitted_years"] == (2020, 2023), "admitted campaigns changed")
    configured_districts = tuple(
        (item["ubigeo"], item["district_name"])
        for item in config["finite_portfolio_selection"]["authorized_districts"]
    )
    require(selection["authorized_districts"] == EXPECTED_DISTRICTS, "computed scope mismatch")
    require(configured_districts == EXPECTED_DISTRICTS, "configured scope mismatch")
    frontier = compute_coverage_frontier()
    require(frontier == EXPECTED_COVERAGE_FRONTIER, "coverage frontier changed")
    require(portfolio == build_portfolio_rows(), "finite portfolio audit does not reproduce")

    admitted = [
        row for row in portfolio
        if row["REFERENCE_CONFIGURATION_ADMISSIBILITY"] == "ADMISSIBLE_REFERENCE_CONFIGURATION"
    ]
    require(len(portfolio) == 9 and len(admitted) == 2, "candidate or admitted count mismatch")
    require(
        tuple((row["ALTERNATIVE_ID"], row["SOURCE_CAMPAIGN"]) for row in admitted)
        == tuple((alternative_id, campaign) for alternative_id, campaign, _ in EXPECTED_ALTERNATIVES),
        "admitted alternative identities changed",
    )
    require(all(row["MISSING_AS_ZERO_USED"] == "FALSE" for row in portfolio), "missing converted to zero")
    require(all(row["DISTRICT_MIX_AND_MATCH"] == "FALSE" for row in portfolio), "district mix-and-match used")
    require(all(row["WATER_FEASIBILITY_CLAIM"] == "FALSE" for row in portfolio), "water feasibility claimed")
    require(all(row["FUTURE_PHYSICAL_FEASIBILITY_CLAIM"] == "FALSE" for row in portfolio), "future physical feasibility claimed")
    require(all(row["TIMING_PROFILE_COMPLETE"] == "TRUE" for row in admitted), "admitted timing incomplete")

    finite = config["finite_portfolio_selection"]
    require(finite["status"] == "SUPPORTED", "finite portfolio status changed")
    require(finite["candidate_configurations_n"] == 9, "candidate count config mismatch")
    require(finite["admissible_configurations_n"] == 2, "admissible count config mismatch")
    require(finite["primary_reference_configurations_n"] == 2, "primary reference count mismatch")
    require(
        tuple(
            (item["alternative_id"], item["source_campaign"])
            for item in finite["primary_reference_configurations"]
        ) == tuple((alternative_id, campaign) for alternative_id, campaign, _ in EXPECTED_ALTERNATIVES),
        "primary reference identities mismatch",
    )
    require(finite["authorized_districts_n"] == 13, "scope count config mismatch")
    require(
        finite["spatial_scope_semantics"]
        == "COVERAGE_QUALIFIED_COMMON_SUPPORT_SUBREGIONAL_SCOPE",
        "spatial scope semantics changed",
    )
    require(finite["representativeness_status"] == "NOT_ESTABLISHED", "representativeness invented")
    require(not finite["full_55_district_scope_supported"], "full district scope invented")
    require(finite["district_mix_and_match_status"] == "NOT_AUTHORIZED", "district mixing authorized")
    require(not finite["convex_interpolation_authorized"], "convex interpolation authorized")
    require(not finite["generic_future_t3_rule_authorized"], "generic T3 rule invented")
    require(not finite["missing_as_zero_used"], "missing-to-zero config mismatch")
    require(not finite["future_physical_feasibility_claim_allowed"], "future feasibility claim authorized")
    require(not finite["water_feasibility_claim_allowed"], "water claim authorized")
    require(not finite["ranking_executed"], "finite ranking executed")
    require(all(finite["authorization_conditions"].values()), "Route B condition failed")
    require(
        finite["primary_scope_selection_principle"]
        == "MAXIMIZE_COMMON_DISTRICT_COVERAGE_SUBJECT_TO_AT_LEAST_TWO_SOURCE_COMPLETE_CONFIGURATIONS",
        "primary scope principle changed",
    )
    require(
        finite["maximize_spatial_coverage_first_status"]
        == "PROSPECTIVELY_RESEARCHER_DEFINED_BUT_OUTCOME_INDEPENDENT",
        "coverage priority provenance overstated",
    )
    require(
        finite["secondary_priority"] == "MAXIMIZE_CONFIGURATION_COUNT_AT_MAXIMUM_COMMON_SUPPORT",
        "secondary scope priority changed",
    )
    require(finite["final_technical_tiebreak"] == "LEXICOGRAPHIC_ONLY_IF_NEEDED", "tie-break changed")
    require(not finite["lexicographic_tiebreak_actually_invoked"], "lexicographic tie-break falsely invoked")
    require(
        finite["why_exactly_two"]
        == "ONLY_TWO_CONFIGURATIONS_SATISFY_THE_UNIQUE_MAXIMUM_13_DISTRICT_COMMON_SUPPORT",
        "K=2 rationale changed",
    )
    configured_frontier = {
        item["configurations_n"]: (
            item["max_common_districts_n"],
            tuple(tuple(int(campaign[:4]) for campaign in subset) for subset in item["maximum_subsets"]),
        )
        for item in finite["coverage_frontier"]
    }
    require(configured_frontier == frontier, "configured coverage frontier mismatch")
    require(
        all(
            item["maximum_subsets_n"] == len(item["maximum_subsets"])
            for item in finite["coverage_frontier"]
        ),
        "coverage frontier tie count mismatch",
    )

    diagnostics = compute_reference_diagnostics()
    require(diagnostics["expected_numeric_cells"] == 52, "expected numeric cell count changed")
    require(diagnostics["observed_complete_numeric_cells"] == 52, "observed numeric cell count changed")
    require(diagnostics["missing_numeric_cells"] == 0, "missing numeric cell found")
    require(diagnostics["timing_profiles_complete"] == {2020: 26, 2023: 26}, "timing profile count changed")
    require(diagnostics["campaign_totals"][2020]["14010020000"] == 15213, "alternative 1 Rice total changed")
    require(diagnostics["campaign_totals"][2020]["14010070000"] == 5704, "alternative 1 MAD total changed")
    require(diagnostics["campaign_totals"][2023]["14010020000"] == 22592, "alternative 2 Rice total changed")
    require(diagnostics["campaign_totals"][2023]["14010070000"] == 5937, "alternative 2 MAD total changed")
    require(diagnostics["alternative_l1_distance_ha"] == 12100, "alternative L1 distance changed")
    require(diagnostics["alternative_different_cells_n"] == 26, "different-cell count changed")
    require(diagnostics["alternative_equal_cells_n"] == 0, "equal-cell count changed")
    require(diagnostics["timing_different_profiles_n"] == 26, "timing distinctness changed")
    require(finite["expected_numeric_cells"] == 52, "configured expected cell count changed")
    require(finite["observed_complete_numeric_cells"] == 52, "configured observed cell count changed")
    require(finite["missing_numeric_cells"] == 0, "configured missing cell count changed")
    require(not finite["silent_missing_to_zero_used"], "silent missing-to-zero configured")
    require(
        finite["alternative_timing_profiles_complete"]
        == {"C0B5-A2020-2021": "26/26", "C0B5-A2023-2024": "26/26"},
        "configured timing completeness changed",
    )
    require(not finite["district_mix_and_match_detected"], "district mix detected")
    require(not finite["crop_year_mixing_detected"], "crop-year mixing detected")
    require(not finite["timing_profile_mixing_detected"], "timing-profile mixing detected")
    require(
        finite["observed_alternative_timing_profile_status"]
        == "SUPPORTED_ALTERNATIVE_SPECIFIC_ONLY_NO_GENERIC_T3_RULE",
        "timing semantics changed",
    )
    numeric = finite["alternative_numeric_diagnostics"]
    require(numeric["alternative_1_rice_ha"] == 15213, "configured alternative 1 Rice total changed")
    require(numeric["alternative_1_mad_ha"] == 5704, "configured alternative 1 MAD total changed")
    require(numeric["alternative_2_rice_ha"] == 22592, "configured alternative 2 Rice total changed")
    require(numeric["alternative_2_mad_ha"] == 5937, "configured alternative 2 MAD total changed")
    require(numeric["alternative_l1_distance_ha"] == 12100, "configured L1 distance changed")
    require(numeric["alternative_different_cells_n"] == 26, "configured different-cell count changed")
    require(numeric["alternative_equal_cells_n"] == 0, "configured equal-cell count changed")
    require(numeric["alternative_numeric_distinctness_status"] == "MATERIALLY_DISTINCT", "numeric distinctness changed")
    require(
        numeric["alternative_timing_distinctness_status"]
        == "BOTH_AREA_AND_TIMING_CONFIGURATIONS_DIFFER",
        "timing distinctness status changed",
    )
    require(finite["route_b_information_depth"] == "THIN_BUT_USABLE", "information depth suppressed")

    require(config["route_b"]["status"] == "SUPPORTED", "Route B status changed")
    require(config["route_c"]["status"] == "NOT_REQUIRED_ROUTE_B_SUPPORTED", "Route C status changed")
    require(config["selected_decision_architecture"] == SELECTED_ARCHITECTURE, "selected architecture mismatch")
    require(config["final_architecture_verdict"] == SELECTED_ARCHITECTURE, "final architecture mismatch")
    require(config["continuous_numerical_optimization_status"] == "NOT_AUTHORIZED", "continuous optimization authorized")
    require(config["water_model"] == "NOT_AUTHORIZED", "water model status changed")
    route_b = config["route_b"]
    require(route_b["short_analytical_label"] == SHORT_ANALYTICAL_LABEL, "short label mismatch")
    require(route_b["historical_realization_status"] == "CERTIFIED_BY_SOURCE_OBSERVATION", "historical realization status changed")
    require(route_b["prospective_physical_feasibility_status"] == "NOT_CERTIFIED", "physical feasibility overstated")
    require(route_b["prospective_institutional_feasibility_status"] == "NOT_CERTIFIED", "institutional feasibility overstated")
    require(
        route_b["reference_configuration_role"]
        == "EMPIRICALLY_REALIZED_COMPARATOR_FOR_PROSPECTIVE_RISK_STRESS_TESTING",
        "reference role changed",
    )
    require(route_b["route_b_architecture_status"] == "SUPPORTED", "Route B architecture status changed")
    require(route_b["exact_2_configuration_13_district_scope_status"] == "SUPPORTED", "exact scope status changed")
    require(not route_b["alternative_interpolation_authorized"], "alternative interpolation authorized")
    require(not route_b["alternative_identities_may_change_after_downstream_results"], "alternative identity drift authorized")
    require(not config["route_b"]["finite_alternative_ranking_executed_in_c0b5"], "finite ranking executed")
    require(config["route_b"]["selected_alternative"] is None, "an alternative was selected")
    require(
        config["finite_risk_aware_reference_configuration_analysis_status"]
        == "SUPPORTED_ARCHITECTURE_PENDING_DOWNSTREAM_GATES",
        "reference-configuration analysis status changed",
    )

    perennial = config["perennial_firewall"]
    require(perennial["resolution"] == "P3_FIXED_STOCK_NEAR_TERM_HORIZON", "perennial resolution changed")
    require(not perennial["mango_altered_by_transient_alternatives"], "Mango altered")
    require(not perennial["limon_altered_by_transient_alternatives"], "Limon altered")
    require(not perennial["banana_altered_by_transient_alternatives"], "Banana altered")
    require(not perennial["historical_perennial_stock_imported_into_alternatives"], "historical perennial stock imported")
    require(perennial["baseline_numeric_status"] == "NOT_YET_NUMERICALLY_FROZEN_SEPARATE_INITIALIZATION_GATE", "perennial baseline invented")
    require(not perennial["perennial_initialization_blocks_c0b5_architecture_freeze"], "perennial initialization incorrectly blocks C0B5")
    require(perennial["perennial_initialization_blocks_full_reference_configuration_scenario_evaluation"], "downstream perennial gate bypassed")

    require(config["research_question_compatibility"]["status"] == "CURRENT_RQ_REQUIRES_MATERIAL_REFRAMING", "RQ action mismatch")
    require(config["research_question_compatibility"]["rq_rewording_status"] == "REQUIRED_BEFORE_MANUSCRIPT_FREEZE", "RQ rewording gate changed")
    require(not config["research_question_compatibility"]["upstream_file_edited"], "upstream RQ file edited")
    require(config["model_authorized_land_parameters_n"] == 0, "land parameter invented")
    require(config["model_authorized_adjustment_bounds_n"] == 0, "adjustment bound invented")
    require(set(config["input_firewall"]["allowed_rule_inputs"]) == SELECTION_FIELDS, "selection field allowlist changed")

    firewalls = config["firewalls"]
    require(firewalls["c0b4_immutable"], "C0B4 firewall disabled")
    require(not firewalls["area_ha_used_as_rescued_capacity"], "AREA_HA capacity invented")
    require(not firewalls["arbitrary_percentage_bound_used"], "arbitrary bound used")
    require(not firewalls["historical_extrema_used_as_model_bounds"], "historical extrema promoted")
    require(not firewalls["historical_convex_hull_used_as_continuous_domain"], "convex hull promoted")
    require(not firewalls["rice_mad_fixed_total_substitution_assumed"], "substitution assumed")
    require(not firewalls["outcome_tuned_baseline_or_alternative"], "outcome leakage")
    require(not firewalls["enso_year_selection_used"], "ENSO-year selection used")
    require(not firewalls["missing_treated_as_zero"], "missing treated as zero")
    require(not firewalls["district_mix_and_match_used"], "district mix used")
    require(not firewalls["water_feasibility_claimed"], "water model claimed")
    require(not firewalls["continuous_optimization_executed"], "continuous optimization executed")
    require(not firewalls["finite_ranking_executed"], "finite ranking executed")
    require(not firewalls["objective_function_constructed"], "objective constructed")

    authorizations = config["authorizations"]
    require(authorizations["route_b_finite_reference_set"], "Route B reference set not authorized")
    require(not authorizations["continuous_optimizer"], "continuous optimizer authorized")
    require(not authorizations["finite_optimizer_or_ranking"], "finite optimizer authorized")
    require(not authorizations["economic_objective"], "economic objective authorized")
    require(not authorizations["water_model"], "water model authorized")
    require(not authorizations["future_physical_feasibility_claim"], "physical feasibility claim authorized")
    require(not authorizations["district_mix_and_match"], "district mix authorized")
    require(not authorizations["convex_interpolation"], "convex interpolation authorized")
    require(
        config["next_required_gate_after_c0b5"]
        == "ALTERNATIVE_DATA_MASTER_AND_REFERENCE_CONFIGURATION_FREEZE_WITH_EXACT_IDS_13_DISTRICT_SCOPE_OBSERVED_TIMING_AND_NUMERIC_FIXED_PERENNIAL_INITIALIZATION_BEFORE_ECONOMIC_OR_RISK_COMPARISON",
        "next required gate changed",
    )

    require(
        route_by_id["ROUTE_B"]["ROUTE_NAME"]
        == "FINITE_PRESPECIFIED_EMPIRICALLY_REALIZED_REFERENCE_CONFIGURATION_ANALYSIS",
        "Route B CSV label mismatch",
    )
    artifact_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (REGISTRY_PATH, ROUTES_PATH, PORTFOLIO_PATH, REPORT_PATH, CONFIG_PATH, SCRIPT_PATH, TEST_PATH)
    )
    old_label = "ROUTE_B_FINITE_PRESPECIFIED_" + "EMPIRICAL_DECISION_ANALYSIS"
    require(old_label not in artifact_text, "old Route B architecture label remains")
    lower_artifacts = artifact_text.lower()
    forbidden_claims = (
        "risk-aware finite " + "decision analysis",
        "certified future " + "feasible allocations",
        "implementable future " + "allocations",
        "optimal " + "allocations",
        "land-reallocation " + "decisions",
        "representative piura " + "portfolio",
        "representative agricultural " + "districts",
    )
    require(
        all(claim not in lower_artifacts for claim in forbidden_claims),
        "forbidden Route B feasibility or representativeness wording remains",
    )

    report_sections = [
        "## 1. Executive adjudication", "## 2. Frozen C0B4 constraints",
        "## 3. Why continuous allocation currently fails", "## 4. Route A evidence test",
        "## 5. Prospective planning evidence", "## 6. Baseline test",
        "## 7. Adjustment-envelope test", "## 8. Route A verdict",
        "## 9. Route B conceptual test", "## 10. Historical configuration universe",
        "## 11. Campaign completeness", "## 12. Spatial coverage",
        "## 13. Whole-configuration vs district mixing", "## 14. Timing-profile test",
        "## 15. Fixed-perennial compatibility", "## 16. Route B verdict",
        "## 17. Route C implications", "## 18. Hierarchical route adjudication",
        "## 19. Research-question compatibility",
        "## 20. Implications for downstream econometrics/ENSO/risk",
        "## 21. Forbidden interpretations", "## 22. Final architecture verdict",
    ]
    positions = [report.find(section) for section in report_sections]
    require(all(position >= 0 for position in positions), "required report section missing")
    require(positions == sorted(positions), "report sections out of order")
    for token in (
        "ROUTE_A_STATUS=NOT_SUPPORTED",
        "ROUTE_B_STATUS=SUPPORTED",
        "ROUTE_C_STATUS=NOT_REQUIRED_ROUTE_B_SUPPORTED",
        f"SELECTED_DECISION_ARCHITECTURE={SELECTED_ARCHITECTURE}",
        f"SHORT_ANALYTICAL_LABEL={SHORT_ANALYTICAL_LABEL}",
        "FINITE_CANDIDATE_CONFIGURATIONS_N=9",
        "FINITE_ADMISSIBLE_CONFIGURATIONS_N=2",
        "PRIMARY_REFERENCE_CONFIGURATIONS_N=2",
        "HISTORICAL_REALIZATION_STATUS=CERTIFIED_BY_SOURCE_OBSERVATION",
        "PROSPECTIVE_PHYSICAL_FEASIBILITY_STATUS=NOT_CERTIFIED",
        "PROSPECTIVE_INSTITUTIONAL_FEASIBILITY_STATUS=NOT_CERTIFIED",
        "COMMON_SUPPORT_DISTRICTS_N=13",
        "REPRESENTATIVENESS_STATUS=NOT_ESTABLISHED",
        "EXPECTED_NUMERIC_CELLS=52",
        "OBSERVED_COMPLETE_NUMERIC_CELLS=52",
        "MISSING_NUMERIC_CELLS=0",
        "SILENT_MISSING_TO_ZERO_USED=FALSE",
        "LEXICOGRAPHIC_TIEBREAK_ACTUALLY_INVOKED=FALSE",
        "ALTERNATIVE_L1_DISTANCE_HA=12100",
        "ROUTE_B_INFORMATION_DEPTH=THIN_BUT_USABLE",
        "DISTRICT_MIX_AND_MATCH_STATUS=NOT_AUTHORIZED",
        "CONTINUOUS_NUMERICAL_OPTIMIZATION_STATUS=NOT_AUTHORIZED",
        "WATER_MODEL=NOT_AUTHORIZED",
        "NO_OUTCOME_LEAKAGE_GATE=PASS",
        "NO_INVENTED_CAPACITY_GATE=PASS",
        "NO_WATER_MODEL_GATE=PASS",
        "NO_OPTIMIZATION_EXECUTED_GATE=PASS",
    ):
        require(token in report, f"report token missing: {token}")

    require(len(SEMANTIC_REJECTION_GATES) == 30, "preflight semantic coverage changed")
    for path in (REGISTRY_PATH, ROUTES_PATH, PORTFOLIO_PATH, REPORT_PATH, CONFIG_PATH, SCRIPT_PATH, TEST_PATH):
        raw = path.read_bytes()
        require(not raw.startswith(b"\xef\xbb\xbf"), f"UTF-8 BOM found: {path.name}")
        require(b"\r" not in raw, f"non-LF line ending found: {path.name}")
        require(raw.endswith(b"\n") and not raw.endswith(b"\n\n"), f"final LF mismatch: {path.name}")

    return [
        "C0B4_IMMUTABILITY_GATE=PASS",
        "PERSISTENT_SCOPE_GATE=PASS",
        "ROUTE_HIERARCHY_GATE=PASS",
        "PROSPECTIVE_EVIDENCE_GATE=PASS",
        "FINITE_PORTFOLIO_GATE=PASS",
        "MISSING_ZERO_GATE=PASS",
        "DISTRICT_MIX_GATE=PASS",
        "PERENNIAL_FIREWALL_GATE=PASS",
        "NO_OUTCOME_LEAKAGE_GATE=PASS",
        "NO_INVENTED_CAPACITY_GATE=PASS",
        "NO_WATER_MODEL_GATE=PASS",
        "NO_OPTIMIZATION_EXECUTED_GATE=PASS",
        "REPORT_CONSISTENCY_GATE=PASS",
        "C0B5_PREFLIGHT=PASS",
    ]


def main() -> int:
    try:
        for line in run_preflight():
            print(line)
    except Exception as exc:  # pragma: no cover - terminal diagnostic
        print(f"C0B5_PREFLIGHT=FAIL: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
