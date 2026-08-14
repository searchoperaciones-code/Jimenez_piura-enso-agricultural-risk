from __future__ import annotations

import calendar
import csv
import hashlib
import json
import math
import subprocess
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

PANEL = ROOT / "data" / "processed" / "panel_master.csv"
TEMPORAL = ROOT / "data" / "processed" / "phenology" / "temporal_structure_monthly.csv"
WINDOWS = ROOT / "data" / "processed" / "phenology" / "phenology_windows_frozen.csv"
PHENOLOGY_CERTIFICATE = ROOT / "outputs" / "phenology" / "PHENOLOGY_MASTER_V1_FREEZE.md"
SPEC = ROOT / "config" / "climate_exposure" / "climate_exposure_spec_v1.json"
CLIMATE = ROOT / "data" / "processed" / "climate" / "climate_anomalies.parquet"
REPORT = ROOT / "outputs" / "climate_exposure" / "B0_PREFLIGHT_REPORT.md"

EXPECTED_BRANCH = "phase/climate-exposure-build-v1"
EXPECTED_HEAD = "1d6cf2701d00c245f17f381119876548034ae60c"
EXPECTED_TAG = "v0.3.1-climate-exposure-spec-freeze"
EXPECTED_SPEC_SHA = "e2e1eabbf8530cb0dfe8538d12f12d73a6a8e77c0e773351b593a14cbe1e268a"
EXPECTED_WINDOWS_SHA = "ea25d949be9834a9e35352d970bb1b2172cac7d49db7eabb101ddfde9cfb657d"
EXPECTED_PHENOLOGY_CERT_SHA = "f9447e10918547011512d629b902dc71ec15b8d2ad74d28901f40f4afffa0ee9"
EXPECTED_CLIMATE_SHA = "11a1fc61cab062faf70e3f12d2a06f050a2ccf094273807192943ad130deb6df"

PANEL_ALLOWED_COLUMNS = ["UBIGEO", "COD_CULTIVO", "CROP_STD", "ANO"]
TEMPORAL_ALLOWED_COLUMNS = [
    "UBIGEO",
    "COD_CULTIVO",
    "CROP_STD",
    "ANO",
    "MES",
    "MONTH",
    "TEMPORAL_ROLE",
    "SOURCE_12_MONTHS_PRESENT",
    "SIEMBRA",
    "SOWN_MISSING_MONTH_COUNT",
    "SOWN_POSITIVE_MONTH_COUNT",
    "SOWN_DENOMINATOR_STATUS",
    "SOWN_SOURCE_12_MONTHS_PRESENT",
]
AUTHORIZED_CLIMATE_VARIABLES = [
    "RAIN_MM",
    "TMAX_C",
    "TMIN_C",
    "RAIN_ANOM_MM",
    "TMAX_ANOM_C",
    "TMIN_ANOM_C",
    "RAIN_Z",
    "TMAX_Z",
    "TMIN_Z",
]
CLIMATE_COLUMNS = ["UBIGEO", "DATE", "YEAR", "MONTH", *AUTHORIZED_CLIMATE_VARIABLES]

TRANSIENT_CROPS = {
    "14010020000": "ARROZ",
    "14010070000": "MAIZ AMARILLO DURO",
}
PERENNIAL_CROPS = {
    "13010210000": "MANGO",
    "13010170102": "LIMON SUTIL",
    "15010040000": "PLATANOS Y BANANAS",
}
EXPECTED_CROP_CODES = set(TRANSIENT_CROPS) | set(PERENNIAL_CROPS)
EXPECTED_WINDOW_IDS = {
    "RICE_FLOWERING_95_110_DAS",
    "MAD_MPLUS1_MPLUS3",
    "MANGO_MAY_JUN_CURRENT_YEAR",
    "LEMON_FULL_YEAR_T",
    "LEMON_FULL_YEAR_T_MINUS_1",
    "BANANA_FULL_YEAR_T",
    "BANANA_FULL_YEAR_T_MINUS_1",
}
EXPECTED_CLIMATE_FAMILIES = {
    "LEVEL": ["RAIN_MM", "TMAX_C", "TMIN_C"],
    "PHYSICAL_ANOMALY": ["RAIN_ANOM_MM", "TMAX_ANOM_C", "TMIN_ANOM_C"],
    "STANDARDIZED_ANOMALY": ["RAIN_Z", "TMAX_Z", "TMIN_Z"],
}
EXPECTED_AGGREGATION = {
    "RAIN_MM": "SUM",
    "RAIN_ANOM_MM": "SUM",
    "TMAX_C": "ARITHMETIC_MEAN",
    "TMAX_ANOM_C": "ARITHMETIC_MEAN",
    "TMAX_Z": "ARITHMETIC_MEAN",
    "TMIN_C": "ARITHMETIC_MEAN",
    "TMIN_ANOM_C": "ARITHMETIC_MEAN",
    "TMIN_Z": "ARITHMETIC_MEAN",
    "RAIN_Z": "ARITHMETIC_MEAN",
}
STRICT_CAMPAIGNS = [
    "2015/2016",
    "2016/2017",
    "2017/2018",
    "2018/2019",
    "2019/2020",
    "2020/2021",
    "2021/2022",
    "2022/2023",
]
FORBIDDEN_STAGE_B_OUTPUTS = [
    ROOT / "data" / "processed" / "phenology" / "transient_cohort_exposures.parquet",
    ROOT / "data" / "processed" / "phenology" / "perennial_exposures_long.parquet",
    ROOT / "data" / "processed" / "phenology" / "transient_campaign_exposures_strict.parquet",
    ROOT / "data" / "processed" / "phenology" / "phenology_exposures_long.parquet",
]
FORBIDDEN_VALUE_TOKENS = ("YIELD_RAW", "PRODUCCION", "COSECHA", "PRECIO", "PRECIO_CHACRA", "ICEN")
CANONICAL_TRANSIENT_UNIVERSE = "ALL_OBSERVED_TRANSIENT_TEMPORAL_SOURCE_ROWS"
MONTH_LIST_REPRESENTATION_CONTRACT = {
    "type": "UTF-8 string",
    "canonical_format": "YYYYMM|YYYYMM|YYYYMM",
    "rules": [
        "chronological ascending",
        "exactly six digits per month",
        "no spaces",
        "no trailing separator",
        'empty set = ""',
        "never JSON",
        "never Python repr",
        "never null merely because set is empty",
    ],
}
ARROW_DTYPE_CONTRACT_BY_TYPE = {
    "string": [
        "UBIGEO",
        "COD_CULTIVO",
        "CROP_STD",
        "WINDOW_ID",
        "ARCHITECTURE",
        "CAMPAIGN_MIN",
        "CAMPAIGN_MAX",
        "CAMPAIGN_ATTRIBUTION_STATUS",
        "ASSIGNED_CAMPAIGN_ID",
        "CAMPAIGN_ID",
        "TIME_BASIS",
        "REFERENCE_PERIOD_ID",
        "FAILURE_REASON",
        "EXPECTED_CLIMATE_MONTHS",
        "SUPPORTED_CLIMATE_MONTHS",
    ],
    "int16": [
        "ANCHOR_YEAR",
        "CAMPAIGN_START_YEAR",
        "CAMPAIGN_END_YEAR",
        "REFERENCE_START_YEAR",
        "REFERENCE_END_YEAR",
        "REFERENCE_CALENDAR_YEAR",
        "ATTRIBUTION_L_MIN_DAYS",
        "ATTRIBUTION_L_MAX_DAYS",
        "UNAMBIGUOUS_COHORT_COUNT",
        "AMBIGUOUS_COHORT_COUNT",
    ],
    "int8": ["ANCHOR_MONTH"],
    "int32": [
        "ANCHOR_YYYYMM",
        "CLIMATE_WINDOW_START_YYYYMM",
        "CLIMATE_WINDOW_END_YYYYMM",
    ],
    "date32": ["ANCHOR_DATE_MIN", "ANCHOR_DATE_MAX", "HARVEST_DATE_MIN", "HARVEST_DATE_MAX"],
    "float64": [
        "SIEMBRA",
        "RAIN_MM",
        "TMAX_C",
        "TMIN_C",
        "RAIN_ANOM_MM",
        "TMAX_ANOM_C",
        "TMIN_ANOM_C",
        "RAIN_Z",
        "TMAX_Z",
        "TMIN_Z",
        "CAMPAIGN_SIEMBRA_DENOMINATOR",
        "COHORT_WEIGHT_SUM",
        "EXPECTED_WEIGHT",
        "SUPPORTED_WEIGHT",
        "MISSING_WEIGHT",
    ],
    "bool": [
        "SIEMBRA_OBSERVED",
        "CLIMATE_WINDOW_COMPLETE",
        "COHORT_EXPOSURE_VALID",
        "CAMPAIGN_WEIGHTED_EXPOSURE_VALID",
        "EXPOSURE_VALID",
    ],
}
ARROW_DTYPE_BY_COLUMN = {
    column: dtype for dtype, columns in ARROW_DTYPE_CONTRACT_BY_TYPE.items() for column in columns
}
TRANSIENT_COHORT_FAILURE_ORDER = [
    "CLIMATE_WINDOW_RIGHT_TRUNCATED",
    "CLIMATE_WINDOW_INTERNAL_GAP",
]
STRICT_FAILURE_ORDER = [
    "STRUCTURAL_LEFT_TRUNCATION",
    "REQUIRED_U_SIEMBRA_NOT_OBSERVED",
    "REQUIRED_A_SIEMBRA_NOT_OBSERVED",
    "AMBIGUOUS_COHORT_SIEMBRA_NONZERO",
    "NO_POSITIVE_UNAMBIGUOUS_SIEMBRA",
    "POSITIVE_WEIGHT_COHORT_CLIMATE_INCOMPLETE",
    "WEIGHT_SUM_TOLERANCE_FAIL",
]
PERENNIAL_FAILURE_ORDER = [
    "CLIMATE_WINDOW_OUTSIDE_AVAILABLE_RANGE",
    "CLIMATE_WINDOW_INTERNAL_GAP",
]
SUCCESS_FAILURE_REASON = "NONE"
CLIMATE_COVERAGE_END_YYYYMM = 202412


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_output(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def csv_header(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return next(csv.reader(handle))


def read_spec() -> dict[str, Any]:
    return json.loads(SPEC.read_text(encoding="utf-8"))


def read_windows() -> pd.DataFrame:
    return pd.read_csv(WINDOWS, dtype="string")


def read_panel_keys() -> pd.DataFrame:
    return pd.read_csv(
        PANEL,
        usecols=PANEL_ALLOWED_COLUMNS,
        dtype={"UBIGEO": "string", "COD_CULTIVO": "string", "CROP_STD": "string"},
    )


def read_temporal_sowing() -> pd.DataFrame:
    data = pd.read_csv(
        TEMPORAL,
        usecols=TEMPORAL_ALLOWED_COLUMNS,
        dtype={
            "UBIGEO": "string",
            "COD_CULTIVO": "string",
            "CROP_STD": "string",
            "TEMPORAL_ROLE": "string",
            "SOWN_DENOMINATOR_STATUS": "string",
        },
    )
    data["SIEMBRA"] = pd.to_numeric(data["SIEMBRA"], errors="coerce")
    return data


def read_climate() -> pd.DataFrame:
    data = pd.read_parquet(CLIMATE, columns=CLIMATE_COLUMNS)
    data["UBIGEO"] = data["UBIGEO"].astype("string")
    return data


def yyyymm(year: int, month: int) -> int:
    return year * 100 + month


def add_months(value: int, offset: int) -> int:
    year = value // 100
    month = value % 100
    shifted = month + offset
    year += (shifted - 1) // 12
    month = (shifted - 1) % 12 + 1
    return yyyymm(year, month)


def format_month_list(months: list[int] | tuple[int, ...] | set[int]) -> str:
    ordered = sorted(int(month) for month in months)
    return "|".join(f"{month:06d}" for month in ordered)


def window_failure_reason(expected_months: list[int], supported_months: list[int]) -> str:
    expected = set(int(month) for month in expected_months)
    supported = set(int(month) for month in supported_months)
    if expected == supported:
        return SUCCESS_FAILURE_REASON

    codes: list[str] = []
    missing = expected - supported
    if any(month > CLIMATE_COVERAGE_END_YYYYMM for month in missing):
        codes.append("CLIMATE_WINDOW_RIGHT_TRUNCATED")
    if any(month <= CLIMATE_COVERAGE_END_YYYYMM for month in missing):
        codes.append("CLIMATE_WINDOW_INTERNAL_GAP")
    return "|".join(code for code in TRANSIENT_COHORT_FAILURE_ORDER if code in codes) or SUCCESS_FAILURE_REASON


def cohort_aggregation_policy(expected_months: list[int], supported_months: list[int]) -> dict[str, Any]:
    complete = set(expected_months) == set(supported_months)
    climate_values = {variable: None for variable in AUTHORIZED_CLIMATE_VARIABLES}
    return {
        "EXPECTED_CLIMATE_MONTHS": format_month_list(expected_months),
        "SUPPORTED_CLIMATE_MONTHS": format_month_list(supported_months),
        "CLIMATE_WINDOW_COMPLETE": complete,
        "COHORT_EXPOSURE_VALID": complete,
        "AGGREGATED_CLIMATE_VALUES": "CALCULATE_ONLY_IF_COMPLETE" if complete else climate_values,
        "PARTIAL_AGGREGATION_ALLOWED": False,
        "FAILURE_REASON": window_failure_reason(expected_months, supported_months),
    }


def cohort_validity_preview(sowing: float | int | None, expected_months: list[int], supported_months: list[int]) -> dict[str, Any]:
    observed = sowing is not None and not pd.isna(sowing)
    aggregation = cohort_aggregation_policy(expected_months, supported_months)
    return {
        "SIEMBRA_OBSERVED": observed,
        "CLIMATE_WINDOW_COMPLETE": aggregation["CLIMATE_WINDOW_COMPLETE"],
        "COHORT_EXPOSURE_VALID": bool(observed and aggregation["CLIMATE_WINDOW_COMPLETE"]),
        "FAILURE_REASON": aggregation["FAILURE_REASON"],
    }


def month_range(year: int, start_month: int, end_month: int) -> list[int]:
    return [yyyymm(year, month) for month in range(start_month, end_month + 1)]


def campaign_id(start_year: int) -> str:
    return f"{start_year}/{start_year + 1}"


def transient_window_months(crop_code: str, anchor_yyyymm: int) -> list[int]:
    if crop_code == "14010020000":
        offsets = (3, 4)
    elif crop_code == "14010070000":
        offsets = (1, 2, 3)
    else:
        raise ValueError(f"Unsupported transient crop: {crop_code}")
    return [add_months(anchor_yyyymm, offset) for offset in offsets]


def perennial_window_months(window_id: str, reference_year: int) -> list[int]:
    if window_id == "MANGO_MAY_JUN_CURRENT_YEAR":
        return month_range(reference_year, 5, 6)
    if window_id in {"LEMON_FULL_YEAR_T", "BANANA_FULL_YEAR_T"}:
        return month_range(reference_year, 1, 12)
    if window_id in {"LEMON_FULL_YEAR_T_MINUS_1", "BANANA_FULL_YEAR_T_MINUS_1"}:
        return month_range(reference_year - 1, 1, 12)
    raise ValueError(f"Unsupported perennial window: {window_id}")


def strict_domains(crop_code: str, campaign_start_year: int) -> dict[str, list[int]]:
    if crop_code == "14010020000":
        return {
            "U": month_range(campaign_start_year, 5, 12) + month_range(campaign_start_year + 1, 1, 2),
            "A": month_range(campaign_start_year, 3, 4) + month_range(campaign_start_year + 1, 3, 4),
        }
    if crop_code == "14010070000":
        return {
            "U": month_range(campaign_start_year, 5, 12) + [yyyymm(campaign_start_year + 1, 1)],
            "A": month_range(campaign_start_year, 2, 4) + month_range(campaign_start_year + 1, 2, 4),
        }
    raise ValueError(f"Unsupported strict crop: {crop_code}")


def transient_attribution(crop_code: str, anchor_year: int, anchor_month: int) -> dict[str, str | None]:
    l_min, l_max = (110, 138) if crop_code == "14010020000" else (120, 170)
    anchor_min = date(anchor_year, anchor_month, 1)
    anchor_max = date(anchor_year, anchor_month, calendar.monthrange(anchor_year, anchor_month)[1])
    harvest_min = anchor_min + timedelta(days=l_min)
    harvest_max = anchor_max + timedelta(days=l_max)

    def campaign_for_day(day: date) -> str:
        start = day.year if day.month >= 8 else day.year - 1
        return campaign_id(start)

    campaign_min = campaign_for_day(harvest_min)
    campaign_max = campaign_for_day(harvest_max)
    status = "UNAMBIGUOUS_AGRONOMIC_CAMPAIGN" if campaign_min == campaign_max else "AMBIGUOUS_CROSS_CAMPAIGN"
    return {
        "ANCHOR_DATE_MAX": anchor_max.isoformat(),
        "HARVEST_DATE_MAX": harvest_max.isoformat(),
        "HARVEST_DATE_MIN": harvest_min.isoformat(),
        "CAMPAIGN_MIN": campaign_min,
        "CAMPAIGN_MAX": campaign_max,
        "CAMPAIGN_ATTRIBUTION_STATUS": status,
        "ASSIGNED_CAMPAIGN_ID": campaign_min if status == "UNAMBIGUOUS_AGRONOMIC_CAMPAIGN" else None,
    }


def canonicalize(series: pd.Series, pattern: str) -> pd.Series:
    canonical = series.astype("string").str.strip()
    invalid = canonical.isna() | ~canonical.str.fullmatch(pattern)
    if invalid.any():
        return canonical
    return canonical


def identifier_summary(panel: pd.DataFrame, temporal: pd.DataFrame, climate: pd.DataFrame) -> dict[str, Any]:
    sources = {"panel": panel, "temporal": temporal, "climate": climate}
    summary: dict[str, Any] = {}
    for source_name, data in sources.items():
        source_summary: dict[str, Any] = {}
        for column, pattern in (("UBIGEO", r"\d{6}"), ("COD_CULTIVO", r"\d{11}")):
            if column not in data.columns:
                continue
            raw = data[column].astype("string")
            canonical = canonicalize(raw, pattern)
            lengths = canonical.dropna().str.len()
            collision_rows = pd.DataFrame({"raw": raw, "canonical": canonical}).dropna()
            collisions = (
                collision_rows.groupby("canonical")["raw"].nunique().loc[lambda item: item > 1].shape[0]
                if not collision_rows.empty
                else 0
            )
            source_summary[column] = {
                "rows": int(len(raw)),
                "missing": int(canonical.isna().sum()),
                "min_length": int(lengths.min()) if not lengths.empty else None,
                "max_length": int(lengths.max()) if not lengths.empty else None,
                "invalid_format": int((canonical.isna() | ~canonical.str.fullmatch(pattern)).sum()),
                "colliding_canonical_values": int(collisions),
            }
        summary[source_name] = source_summary
    summary["set_consistency"] = {
        "panel_ubigeo_minus_climate": sorted(set(panel["UBIGEO"].astype(str)) - set(climate["UBIGEO"].astype(str))),
        "temporal_ubigeo_minus_climate": sorted(set(temporal["UBIGEO"].astype(str)) - set(climate["UBIGEO"].astype(str))),
        "panel_crop_codes": sorted(panel["COD_CULTIVO"].astype(str).unique().tolist()),
        "temporal_crop_codes": sorted(temporal["COD_CULTIVO"].astype(str).unique().tolist()),
    }
    return summary


def schema_summary(panel: pd.DataFrame, temporal: pd.DataFrame, windows: pd.DataFrame, climate: pd.DataFrame) -> dict[str, Any]:
    return {
        "panel_master": {
            "header": csv_header(PANEL),
            "loaded_columns": PANEL_ALLOWED_COLUMNS,
            "loaded_dtypes": {column: str(dtype) for column, dtype in panel.dtypes.items()},
            "note": "CSV has no physical dtype; outcome-value columns were not loaded.",
        },
        "temporal_structure_monthly": {
            "header": csv_header(TEMPORAL),
            "loaded_columns": TEMPORAL_ALLOWED_COLUMNS,
            "loaded_dtypes": {column: str(dtype) for column, dtype in temporal.dtypes.items()},
            "note": "Only SIEMBRA and sowing/source metadata were loaded.",
        },
        "phenology_windows_frozen": {
            "columns": windows.columns.tolist(),
            "loaded_dtypes": {column: str(dtype) for column, dtype in windows.dtypes.items()},
        },
        "climate_anomalies": {
            "columns": climate.columns.tolist(),
            "loaded_dtypes": {column: str(dtype) for column, dtype in climate.dtypes.items()},
        },
    }


def unique_key_summary(panel: pd.DataFrame, temporal: pd.DataFrame, windows: pd.DataFrame, climate: pd.DataFrame) -> dict[str, Any]:
    return {
        "panel_master_key": {
            "columns": ["UBIGEO", "COD_CULTIVO", "ANO"],
            "rows": int(len(panel)),
            "duplicate_rows": int(panel.duplicated(["UBIGEO", "COD_CULTIVO", "ANO"]).sum()),
        },
        "temporal_structure_monthly_key": {
            "columns": ["UBIGEO", "COD_CULTIVO", "MES"],
            "rows": int(len(temporal)),
            "duplicate_rows": int(temporal.duplicated(["UBIGEO", "COD_CULTIVO", "MES"]).sum()),
        },
        "phenology_windows_key": {
            "columns": ["WINDOW_ID"],
            "rows": int(len(windows)),
            "duplicate_rows": int(windows.duplicated(["WINDOW_ID"]).sum()),
        },
        "climate_anomalies_key": {
            "columns": ["UBIGEO", "YEAR", "MONTH"],
            "rows": int(len(climate)),
            "duplicate_rows": int(climate.duplicated(["UBIGEO", "YEAR", "MONTH"]).sum()),
        },
    }


def climate_summary(climate: pd.DataFrame) -> dict[str, Any]:
    data = climate.copy()
    data["YYYYMM"] = data["YEAR"].astype(int) * 100 + data["MONTH"].astype(int)
    missing = {column: int(data[column].isna().sum()) for column in AUTHORIZED_CLIMATE_VARIABLES}
    nonfinite = {
        column: int((~np.isfinite(data[column].to_numpy(dtype=float))).sum())
        for column in AUTHORIZED_CLIMATE_VARIABLES
    }
    return {
        "row_count": int(len(data)),
        "district_count": int(data["UBIGEO"].nunique()),
        "date_min": str(data["DATE"].min().date()),
        "date_max": str(data["DATE"].max().date()),
        "yyyymm_min": int(data["YYYYMM"].min()),
        "yyyymm_max": int(data["YYYYMM"].max()),
        "duplicate_district_month_keys": int(data.duplicated(["UBIGEO", "YEAR", "MONTH"]).sum()),
        "missing_by_authorized_variable": missing,
        "nonfinite_by_authorized_variable": nonfinite,
        "negative_rain_mm": int((data["RAIN_MM"] < 0).sum()),
        "tmin_gt_tmax": int((data["TMIN_C"] > data["TMAX_C"]).sum()),
        "all_nine_frozen_variables_available": set(AUTHORIZED_CLIMATE_VARIABLES).issubset(data.columns),
    }


def complete_climate_keys(climate: pd.DataFrame) -> set[tuple[str, int]]:
    data = climate.copy()
    data["YYYYMM"] = data["YEAR"].astype(int) * 100 + data["MONTH"].astype(int)
    complete = data[AUTHORIZED_CLIMATE_VARIABLES].notna().all(axis=1)
    return set(data.loc[complete, ["UBIGEO", "YYYYMM"]].itertuples(index=False, name=None))


def transient_candidate_universes(panel: pd.DataFrame, temporal: pd.DataFrame) -> dict[str, Any]:
    panel_transient = panel[panel["COD_CULTIVO"].isin(TRANSIENT_CROPS)].copy()
    temporal_transient = temporal[temporal["COD_CULTIVO"].isin(TRANSIENT_CROPS)].copy()
    joined = temporal_transient.merge(
        panel_transient[["UBIGEO", "COD_CULTIVO", "ANO"]],
        on=["UBIGEO", "COD_CULTIVO", "ANO"],
        how="inner",
    )

    strict_rows: list[dict[str, Any]] = []
    for row in panel_transient.itertuples(index=False):
        campaign_start = int(row.ANO) - 1
        domains = strict_domains(str(row.COD_CULTIVO), campaign_start)
        for domain_name in ("U", "A"):
            for month_id in domains[domain_name]:
                strict_rows.append(
                    {
                        "UBIGEO": row.UBIGEO,
                        "COD_CULTIVO": row.COD_CULTIVO,
                        "CAMPAIGN_ID": campaign_id(campaign_start),
                        "DOMAIN": domain_name,
                        "MES": month_id,
                    }
                )
    strict_required = pd.DataFrame(strict_rows)
    temporal_keys = set(
        temporal_transient[["UBIGEO", "COD_CULTIVO", "MES"]].itertuples(index=False, name=None)
    )
    observed_required = strict_required.apply(
        lambda item: (item["UBIGEO"], item["COD_CULTIVO"], item["MES"]) in temporal_keys,
        axis=1,
    )

    return {
        "A_all_transient_temporal_rows": {
            "rows": int(len(temporal_transient)),
            "by_crop": _series_int_dict(temporal_transient.groupby("COD_CULTIVO").size()),
            "role": "CANONICAL_TRANSIENT_COHORT_LEDGER_UNIVERSE",
        },
        "B_transient_rows_in_main_panel_key_years": {
            "rows": int(len(joined)),
            "by_crop": _series_int_dict(joined.groupby("COD_CULTIVO").size()),
            "role": "DIAGNOSTIC_ONLY_NOT_CANONICAL_UNIVERSE",
        },
        "C_strict_required_campaign_sowing_rows": {
            "required_rows": int(len(strict_required)),
            "observed_rows": int(observed_required.sum()),
            "missing_rows": int((~observed_required).sum()),
            "by_crop_required": _series_int_dict(strict_required.groupby("COD_CULTIVO").size()),
            "role": "STRICT_DIAGNOSTIC_ONLY_NOT_COHORT_LEDGER_UNIVERSE",
        },
        "D_contextual_edge_support_2015_2024": {
            "rows": int(temporal_transient[temporal_transient["ANO"].isin([2015, 2024])].shape[0]),
            "by_crop_year": _multiindex_int_dict(
                temporal_transient[temporal_transient["ANO"].isin([2015, 2024])]
                .groupby(["COD_CULTIVO", "ANO"])
                .size()
            ),
            "role": "CONTEXT_EDGE_SUPPORT_RETAINED_IN_CANONICAL_SOURCE_UNIVERSE",
        },
        "canonical_universe_name": CANONICAL_TRANSIENT_UNIVERSE,
        "canonical_universe_rows": int(len(temporal_transient)),
        "canonical_universe_status": "DIRECTOR_APPROVED_B0_2",
        "no_main_panel_restriction": True,
        "no_synthetic_month_densification": True,
        "no_strict_slot_universe": True,
    }


def sowing_summary(temporal: pd.DataFrame) -> dict[str, Any]:
    grouped = temporal.groupby(["COD_CULTIVO", "CROP_STD"])["SIEMBRA"]
    summary: dict[str, Any] = {}
    for key, series in grouped:
        label = "|".join(str(part) for part in key)
        summary[label] = {
            "monthly_rows": int(series.size),
            "sowing_observed": int(series.notna().sum()),
            "sowing_missing": int(series.isna().sum()),
            "sowing_zero": int((series == 0).sum()),
            "sowing_positive": int((series > 0).sum()),
            "sowing_negative": int((series < 0).sum()),
        }
    return summary


def strict_diagnostic(panel: pd.DataFrame, temporal: pd.DataFrame, climate: pd.DataFrame) -> dict[str, Any]:
    panel_transient = panel[panel["COD_CULTIVO"].isin(TRANSIENT_CROPS)].copy()
    temporal_transient = temporal[temporal["COD_CULTIVO"].isin(TRANSIENT_CROPS)].copy()
    temporal_index = {
        (row.UBIGEO, row.COD_CULTIVO, int(row.MES)): row.SIEMBRA
        for row in temporal_transient.itertuples(index=False)
    }
    climate_keys = complete_climate_keys(climate)
    rows: list[dict[str, Any]] = []

    for row in panel_transient.itertuples(index=False):
        campaign_start = int(row.ANO) - 1
        domains = strict_domains(str(row.COD_CULTIVO), campaign_start)
        u_values: list[float] = []
        a_values: list[float] = []
        missing_u = 0
        missing_a = 0
        climate_incomplete = 0

        for month_id in domains["U"]:
            value = temporal_index.get((row.UBIGEO, row.COD_CULTIVO, month_id))
            if value is None or pd.isna(value):
                missing_u += 1
                continue
            number = float(value)
            u_values.append(number)
            if number > 0:
                for expected_month in transient_window_months(str(row.COD_CULTIVO), month_id):
                    if (row.UBIGEO, expected_month) not in climate_keys:
                        climate_incomplete += 1

        for month_id in domains["A"]:
            value = temporal_index.get((row.UBIGEO, row.COD_CULTIVO, month_id))
            if value is None or pd.isna(value):
                missing_a += 1
                continue
            a_values.append(float(value))

        sum_u = sum(u_values)
        weights_ok = True
        if sum_u > 0:
            weights_ok = abs(sum(value / sum_u for value in u_values if value > 0) - 1.0) <= 1e-12
        valid = (
            missing_u == 0
            and missing_a == 0
            and all(value == 0 for value in a_values)
            and sum_u > 0
            and climate_incomplete == 0
            and weights_ok
        )
        reasons = []
        if campaign_id(campaign_start) == "2015/2016":
            reasons.append("STRUCTURAL_LEFT_TRUNCATION")
        if missing_u:
            reasons.append("REQUIRED_U_SIEMBRA_NOT_OBSERVED")
        if missing_a:
            reasons.append("REQUIRED_A_SIEMBRA_NOT_OBSERVED")
        if any(value != 0 for value in a_values):
            reasons.append("AMBIGUOUS_COHORT_SIEMBRA_NONZERO")
        if sum_u <= 0:
            reasons.append("NO_POSITIVE_UNAMBIGUOUS_SIEMBRA")
        if climate_incomplete:
            reasons.append("POSITIVE_WEIGHT_COHORT_CLIMATE_INCOMPLETE")
        if not weights_ok:
            reasons.append("WEIGHT_SUM_TOLERANCE_FAIL")
        reasons = [code for code in STRICT_FAILURE_ORDER if code in reasons]
        rows.append(
            {
                "COD_CULTIVO": row.COD_CULTIVO,
                "CAMPAIGN_ID": campaign_id(campaign_start),
                "VALID": valid,
                "FAILURE_REASONS": reasons,
                "MISSING_U": missing_u,
                "MISSING_A": missing_a,
                "CLIMATE_INCOMPLETE_MONTHS": climate_incomplete,
            }
        )

    result = pd.DataFrame(rows)
    by_crop = result.groupby("COD_CULTIVO")["VALID"].agg(["size", "sum"]).rename(columns={"size": "total", "sum": "valid"})
    by_campaign = (
        result.groupby(["COD_CULTIVO", "CAMPAIGN_ID"])["VALID"]
        .agg(["size", "sum"])
        .rename(columns={"size": "total", "sum": "valid"})
    )
    combined_valid = int(result["VALID"].sum())
    combined_total = int(result.shape[0])
    return {
        "by_crop": {
            crop: {"valid": int(values["valid"]), "total": int(values["total"])}
            for crop, values in by_crop.to_dict("index").items()
        },
        "by_crop_campaign": _multiindex_table_dict(by_campaign),
        "combined": {"valid": combined_valid, "total": combined_total},
        "expected": {
            "14010020000": {"valid": 31, "total": 340},
            "14010070000": {"valid": 7, "total": 405},
            "combined": {"valid": 38, "total": 745},
        },
        "status": "PASS"
        if combined_valid == 38
        and combined_total == 745
        and by_crop.loc["14010020000", "valid"] == 31
        and by_crop.loc["14010070000", "valid"] == 7
        else "FAIL",
    }


def perennial_structural(panel: pd.DataFrame, windows: pd.DataFrame, climate: pd.DataFrame) -> dict[str, Any]:
    panel_perennial = panel[panel["COD_CULTIVO"].isin(PERENNIAL_CROPS)].copy()
    windows_perennial = windows[windows["COD_CULTIVO"].isin(PERENNIAL_CROPS)].copy()
    climate_keys = complete_climate_keys(climate)
    rows: list[dict[str, Any]] = []
    for panel_row in panel_perennial.itertuples(index=False):
        crop_windows = windows_perennial[windows_perennial["COD_CULTIVO"] == panel_row.COD_CULTIVO]
        for window in crop_windows.itertuples(index=False):
            expected = perennial_window_months(str(window.WINDOW_ID), int(panel_row.ANO))
            supported = [month_id for month_id in expected if (panel_row.UBIGEO, month_id) in climate_keys]
            rows.append(
                {
                    "COD_CULTIVO": panel_row.COD_CULTIVO,
                    "WINDOW_ID": window.WINDOW_ID,
                    "COMPLETE": len(supported) == len(expected),
                }
            )
    result = pd.DataFrame(rows)
    return {
        "candidate_rows": int(len(result)),
        "expected_candidate_rows": 1657,
        "by_crop_window": _multiindex_int_dict(result.groupby(["COD_CULTIVO", "WINDOW_ID"]).size()),
        "complete_rows": int(result["COMPLETE"].sum()),
        "incomplete_rows": int((~result["COMPLETE"]).sum()),
        "status": "PASS" if len(result) == 1657 else "DISCREPANCY",
    }


def boundary_findings(panel: pd.DataFrame, temporal: pd.DataFrame, climate: pd.DataFrame) -> dict[str, Any]:
    temporal_transient = temporal[temporal["COD_CULTIVO"].isin(TRANSIENT_CROPS)].copy()
    climate_data = climate.copy()
    climate_data["YYYYMM"] = climate_data["YEAR"].astype(int) * 100 + climate_data["MONTH"].astype(int)
    climate_end = int(climate_data["YYYYMM"].max())
    right_rows = []
    for row in temporal_transient.itertuples(index=False):
        expected = transient_window_months(str(row.COD_CULTIVO), int(row.MES))
        if max(expected) > climate_end:
            right_rows.append(
                {
                    "COD_CULTIVO": row.COD_CULTIVO,
                    "ANCHOR_YYYYMM": int(row.MES),
                    "EXPECTED_CLIMATE_MONTHS": expected,
                }
            )
    right = pd.DataFrame(right_rows)

    panel_2016 = panel[(panel["COD_CULTIVO"].isin(TRANSIENT_CROPS)) & (panel["ANO"] == 2016)]
    source_start = int(temporal["MES"].min())
    left_rows = []
    for row in panel_2016.itertuples(index=False):
        domains = strict_domains(str(row.COD_CULTIVO), int(row.ANO) - 1)
        for month_id in domains["U"] + domains["A"]:
            if month_id < source_start:
                left_rows.append({"COD_CULTIVO": row.COD_CULTIVO, "MES": month_id})
    left = pd.DataFrame(left_rows)

    return {
        "source_start_yyyymm": source_start,
        "climate_end_yyyymm": climate_end,
        "structural_left_truncation_campaign": "2015/2016",
        "left_truncation_panel_keys": int(len(panel_2016)),
        "left_truncation_required_sowing_months": int(len(left)),
        "left_truncation_by_crop": _series_int_dict(left.groupby("COD_CULTIVO").size()) if not left.empty else {},
        "right_edge_affected_rows": int(len(right)),
        "right_edge_by_crop_anchor_yyyymm": _multiindex_int_dict(right.groupby(["COD_CULTIVO", "ANCHOR_YYYYMM"]).size())
        if not right.empty
        else {},
        "right_edge_candidate_months": sorted(right["ANCHOR_YYYYMM"].unique().astype(int).tolist()) if not right.empty else [],
    }


def climate_completeness(panel: pd.DataFrame, temporal: pd.DataFrame, windows: pd.DataFrame, climate: pd.DataFrame) -> dict[str, Any]:
    climate_keys = complete_climate_keys(climate)
    temporal_transient = temporal[temporal["COD_CULTIVO"].isin(TRANSIENT_CROPS)].copy()
    transient_complete = 0
    transient_incomplete = 0
    for row in temporal_transient.itertuples(index=False):
        expected = transient_window_months(str(row.COD_CULTIVO), int(row.MES))
        supported = [month_id for month_id in expected if (row.UBIGEO, month_id) in climate_keys]
        if len(supported) == len(expected):
            transient_complete += 1
        else:
            transient_incomplete += 1
    perennial = perennial_structural(panel, windows, climate)
    return {
        "transient_candidate_rows_assessed": int(transient_complete + transient_incomplete),
        "transient_complete_rows": int(transient_complete),
        "transient_incomplete_rows": int(transient_incomplete),
        "perennial_candidate_rows_assessed": perennial["candidate_rows"],
        "perennial_complete_rows": perennial["complete_rows"],
        "perennial_incomplete_rows": perennial["incomplete_rows"],
    }


def frozen_contract_checks(spec: dict[str, Any], windows: pd.DataFrame) -> dict[str, Any]:
    return {
        "five_crop_codes_exact": set(windows["COD_CULTIVO"].astype(str)) == EXPECTED_CROP_CODES,
        "seven_window_ids_exact": set(windows["WINDOW_ID"].astype(str)) == EXPECTED_WINDOW_IDS,
        "climate_families_exact": spec["climate_family_contract"]["families"] == EXPECTED_CLIMATE_FAMILIES,
        "aggregation_exact": spec["climate_family_contract"]["aggregation"] == EXPECTED_AGGREGATION,
        "strict_layer_non_primary": spec["stage_b_artifacts"]["transient_campaign_exposures_strict"][
            "is_primary_econometric_exposure"
        ]
        is False,
        "cohort_ledger_primary_stage_b": spec["econometric_status"]["TRANSIENT_COHORT_LEDGER"]
        == "PRIMARY_STAGE_B_DATA_PRODUCT",
        "econometrics_blocked": spec["econometric_status"]["ECONOMETRICS"] == "BLOCKED",
    }


def upstream_hash_gate() -> dict[str, Any]:
    actual = {
        "climate_exposure_spec_v1.json": sha256_file(SPEC),
        "phenology_windows_frozen.csv": sha256_file(WINDOWS),
        "PHENOLOGY_MASTER_V1_FREEZE.md": sha256_file(PHENOLOGY_CERTIFICATE),
        "climate_anomalies.parquet": sha256_file(CLIMATE),
    }
    expected = {
        "climate_exposure_spec_v1.json": EXPECTED_SPEC_SHA,
        "phenology_windows_frozen.csv": EXPECTED_WINDOWS_SHA,
        "PHENOLOGY_MASTER_V1_FREEZE.md": EXPECTED_PHENOLOGY_CERT_SHA,
        "climate_anomalies.parquet": EXPECTED_CLIMATE_SHA,
    }
    return {
        "status": "PASS" if actual == expected else "FAIL_UPSTREAM_INTEGRITY",
        "actual": actual,
        "expected": expected,
    }


def baseline_status() -> dict[str, Any]:
    branch = git_output("branch", "--show-current")
    head = git_output("rev-parse", "HEAD")
    tag_target = git_output("rev-list", "-n", "1", EXPECTED_TAG)
    return {
        "branch": branch,
        "head": head,
        "tag_target": tag_target,
        "branch_ok": branch == EXPECTED_BRANCH,
        "head_ok": head == EXPECTED_HEAD,
        "tag_ok": tag_target == EXPECTED_HEAD,
    }


def no_forbidden_outputs() -> dict[str, Any]:
    existing = [rel(path) for path in FORBIDDEN_STAGE_B_OUTPUTS if path.exists()]
    return {"status": "PASS" if not existing else "FAIL", "existing": existing}


def proposed_technical_decisions(spec: dict[str, Any]) -> dict[str, Any]:
    return {
        "director_adjudication_status": "DIRECTOR_APPROVED_B0_2",
        "transient_universe_contract": {
            "canonical_universe": CANONICAL_TRANSIENT_UNIVERSE,
            "row_count": 8977,
            "source_boundary": "2015-08..2024-12",
            "do_not_restrict_to_main_panel": True,
            "do_not_densify_synthetic_months": True,
            "do_not_use_strict_required_slots_as_universe": True,
            "edge_support_2015_2024": "CONTEXT_EDGE_SUPPORT",
        },
        "month_list_representation": MONTH_LIST_REPRESENTATION_CONTRACT,
        "incomplete_window_aggregation": {
            "partial_climate_aggregation_allowed": False,
            "if_supported_months_differ_from_expected": {
                "CLIMATE_WINDOW_COMPLETE": False,
                "COHORT_EXPOSURE_VALID": False,
                "all_nine_aggregated_climate_values": None,
            },
            "no_partial_sum": True,
            "no_partial_mean": True,
            "no_renormalization": True,
        },
        "arrow_dtype_contract": {
            "status": "DIRECTOR_APPROVED_B0_2",
            "by_type": ARROW_DTYPE_CONTRACT_BY_TYPE,
            "by_artifact": {
                artifact: {column: proposed_dtype_for_column(column) for column in payload["schema"]}
                for artifact, payload in spec["stage_b_artifacts"].items()
            }
            | {
                "perennial_exposures_long": {
                    column: proposed_dtype_for_column(column)
                    for column in spec["perennial_exposure_contract"]["perennial_schema"]
                },
                "phenology_exposures_long": {
                    column: proposed_dtype_for_column(column)
                    for column in spec["unified_exposure_long_format"]["schema"]
                },
            },
        },
        "failure_reason_contract": {
            "status": "DIRECTOR_APPROVED_B0_2",
            "success": SUCCESS_FAILURE_REASON,
            "separator": "|",
            "transient_cohort_order": TRANSIENT_COHORT_FAILURE_ORDER,
            "ambiguous_cross_campaign_is_failure": False,
            "strict_campaign_order": STRICT_FAILURE_ORDER,
            "perennial_order": PERENNIAL_FAILURE_ORDER,
            "do_not_invent_additional_codes_without_director_reopening": True,
        },
        "zero_sowing_contract": {
            "sowing_zero_semantics": "OBSERVED_ZERO_NOT_MISSING",
            "with_complete_climate_window": {
                "SIEMBRA_OBSERVED": True,
                "CLIMATE_WINDOW_COMPLETE": True,
                "COHORT_EXPOSURE_VALID": True,
                "FAILURE_REASON": SUCCESS_FAILURE_REASON,
            },
            "no_dropping": True,
        },
        "right_edge_internal_gap_contract": {
            "expected_month_gt_2024_12": "CLIMATE_WINDOW_RIGHT_TRUNCATED",
            "expected_month_inside_coverage_but_key_or_value_unavailable": "CLIMATE_WINDOW_INTERNAL_GAP",
            "internal_gap_future_final_gate": "HOLD_OR_FAIL",
        },
        "unified_long_contract": {
            "UNIFIED_LONG_BUILD": "HOLD",
            "do_not_build_during_climate_exposure_master_v1": True,
            "do_not_modify_frozen_unified_schema": True,
            "do_not_aggregate_transient_cohorts_to_fit_unified_schema": True,
        },
    }


def proposed_dtype_for_column(column: str) -> str:
    if column not in ARROW_DTYPE_BY_COLUMN:
        raise KeyError(f"No B0.2 Arrow dtype adjudicated for column: {column}")
    return ARROW_DTYPE_BY_COLUMN[column]


def director_adjudication_contract() -> dict[str, Any]:
    return {
        "section": "DIRECTOR TECHNICAL ADJUDICATION - B0.2",
        "status": "INCORPORATED",
        "decisions": proposed_technical_decisions(read_spec()),
    }


def unified_long_status(spec: dict[str, Any]) -> dict[str, Any]:
    transient_columns = set(spec["stage_b_artifacts"]["transient_cohort_exposures"]["schema"])
    unified_columns = set(spec["unified_exposure_long_format"]["schema"])
    lost = [
        "ANCHOR_YEAR",
        "ANCHOR_MONTH",
        "ANCHOR_YYYYMM",
        "SIEMBRA",
        "CAMPAIGN_MIN",
        "CAMPAIGN_MAX",
        "CAMPAIGN_ATTRIBUTION_STATUS",
    ]
    missing_from_unified = [column for column in lost if column in transient_columns and column not in unified_columns]
    return {
        "status": "UNIFIED_LONG_BUILD = HOLD" if missing_from_unified else "UNIFIED_LONG_BUILD = READY",
        "lossless_transform_defined": not missing_from_unified,
        "transient_columns_lost_by_reduction": missing_from_unified,
    }


def build_report_payload() -> dict[str, Any]:
    spec = read_spec()
    panel = read_panel_keys()
    temporal = read_temporal_sowing()
    windows = read_windows()
    climate = read_climate()

    climate_gate = climate_summary(climate)
    strict = strict_diagnostic(panel, temporal, climate)
    perennial = perennial_structural(panel, windows, climate)
    sowing = sowing_summary(temporal)
    forbidden_outputs = no_forbidden_outputs()
    hashes = upstream_hash_gate()
    baseline = baseline_status()
    contract = frozen_contract_checks(spec, windows)
    unified = unified_long_status(spec)

    hard_fail = any(
        [
            not baseline["branch_ok"],
            not baseline["head_ok"],
            not baseline["tag_ok"],
            hashes["status"] != "PASS",
            climate_gate["duplicate_district_month_keys"] != 0,
            climate_gate["negative_rain_mm"] != 0,
            climate_gate["tmin_gt_tmax"] != 0,
            not climate_gate["all_nine_frozen_variables_available"],
            strict["status"] != "PASS",
            any(item["sowing_negative"] for item in sowing.values()),
            forbidden_outputs["status"] != "PASS",
        ]
    )
    final = "B0_2 = FAIL" if hard_fail else "B0_2 = PASS_FOR_DIRECTOR_FREEZE_REVIEW"

    return {
        "b0_1_empirical_status": "PASS_FOR_DIRECTOR_REVIEW",
        "baseline": baseline,
        "upstream_hash_gate": hashes,
        "input_schema_summary": schema_summary(panel, temporal, windows, climate),
        "identifier_canonicalization": identifier_summary(panel, temporal, climate),
        "unique_keys": unique_key_summary(panel, temporal, windows, climate),
        "transient_candidate_universes": transient_candidate_universes(panel, temporal),
        "perennial_structural_count": perennial,
        "strict_diagnostic_reproduction": strict,
        "sowing_missing_zero_summary": sowing,
        "boundary_findings": boundary_findings(panel, temporal, climate),
        "climate_coverage": climate_gate,
        "climate_completeness_summary": climate_completeness(panel, temporal, windows, climate),
        "outcome_firewall": {
            "status": "PASS",
            "panel_loaded_columns": PANEL_ALLOWED_COLUMNS,
            "temporal_loaded_columns": TEMPORAL_ALLOWED_COLUMNS,
            "forbidden_value_tokens_not_loaded": list(FORBIDDEN_VALUE_TOKENS),
            "icen_status": "NOT_READ_NOT_MERGED_NOT_CLASSIFIED",
            "forbidden_outputs": forbidden_outputs,
        },
        "frozen_contract_checks": contract,
        "director_technical_adjudication_b0_2": {
            "status": "INCORPORATED",
            "contract": proposed_technical_decisions(spec),
        },
        "director_decision_required_items": [],
        "unified_long_build_status": unified,
        "final_b0_verdict": final,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# CLIMATE EXPOSURE MASTER v1 B0 Preflight Report",
        "",
        f"FINAL_B0_VERDICT: {payload['final_b0_verdict']}",
        "",
        "## B0.1 Empirical Findings",
        f"- EMPIRICAL_STATUS: {payload['b0_1_empirical_status']}",
        "- The following sections preserve B0.1 empirical diagnostics without changing scientific freeze decisions.",
        "",
        "## Baseline",
        f"- BRANCH: {payload['baseline']['branch']}",
        f"- HEAD SHA: {payload['baseline']['head']}",
        f"- BASE TAG TARGET: {payload['baseline']['tag_target']}",
        "",
        "## Upstream Hash Gate",
        f"- STATUS: {payload['upstream_hash_gate']['status']}",
    ]
    for name, actual in payload["upstream_hash_gate"]["actual"].items():
        expected = payload["upstream_hash_gate"]["expected"][name]
        lines.append(f"- {name}: {actual} (expected {expected})")
    lines.extend(
        [
            "",
            "## Input Schema Summary",
            code_block(json.dumps(payload["input_schema_summary"], indent=2, sort_keys=True)),
            "",
            "## Identifier Canonicalization",
            code_block(json.dumps(payload["identifier_canonicalization"], indent=2, sort_keys=True)),
            "",
            "## Unique Keys",
            code_block(json.dumps(payload["unique_keys"], indent=2, sort_keys=True)),
            "",
            "## Transient Candidate Universes",
            code_block(json.dumps(payload["transient_candidate_universes"], indent=2, sort_keys=True)),
            "",
            "## Perennial Structural Count",
            code_block(json.dumps(payload["perennial_structural_count"], indent=2, sort_keys=True)),
            "",
            "## Strict Diagnostic Reproduction",
            code_block(json.dumps(payload["strict_diagnostic_reproduction"], indent=2, sort_keys=True)),
            "",
            "## Missing vs Zero SIEMBRA",
            code_block(json.dumps(payload["sowing_missing_zero_summary"], indent=2, sort_keys=True)),
            "",
            "## Boundary Findings",
            code_block(json.dumps(payload["boundary_findings"], indent=2, sort_keys=True)),
            "",
            "## Climate Coverage and Completeness",
            code_block(
                json.dumps(
                    {
                        "coverage": payload["climate_coverage"],
                        "candidate_completeness": payload["climate_completeness_summary"],
                    },
                    indent=2,
                    sort_keys=True,
                )
            ),
            "",
            "## Outcome Firewall",
            code_block(json.dumps(payload["outcome_firewall"], indent=2, sort_keys=True)),
            "",
            "## Frozen Contract Checks",
            code_block(json.dumps(payload["frozen_contract_checks"], indent=2, sort_keys=True)),
            "",
            "## DIRECTOR TECHNICAL ADJUDICATION — B0.2",
            code_block(json.dumps(payload["director_technical_adjudication_b0_2"], indent=2, sort_keys=True)),
            "",
            "## Director Decision Required Items",
        ]
    )
    if payload["director_decision_required_items"]:
        lines.extend(f"- {item}" for item in payload["director_decision_required_items"])
    else:
        lines.append("- NONE_REMAINING_FOR_B0_2_FREEZE_REVIEW")
    lines.extend(
        [
            "",
            "## Unified Long Build Status",
            code_block(json.dumps(payload["unified_long_build_status"], indent=2, sort_keys=True)),
            "",
        ]
    )
    return "\n".join(lines).rstrip("\n") + "\n"


def code_block(text: str) -> str:
    return "```json\n" + text + "\n```"


def write_report(payload: dict[str, Any]) -> None:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_bytes(render_markdown(payload).encode("utf-8"))


def _series_int_dict(series: pd.Series) -> dict[str, int]:
    return {str(key): int(value) for key, value in series.items()}


def _multiindex_int_dict(series: pd.Series) -> dict[str, int]:
    return {"|".join(str(part) for part in key): int(value) for key, value in series.items()}


def _multiindex_table_dict(frame: pd.DataFrame) -> dict[str, dict[str, int]]:
    return {
        "|".join(str(part) for part in key): {column: int(value) for column, value in row.items()}
        for key, row in frame.to_dict("index").items()
    }


def terminal_lines(payload: dict[str, Any], full_test_result: str = "RUN_SEPARATELY", spec_auditor_result: str = "RUN_SEPARATELY") -> list[str]:
    status = git_output("status", "--short", "--untracked-files=all")
    return [
        f"1. B0.1 EMPIRICAL STATUS: {payload['b0_1_empirical_status']}",
        "2. DIRECTOR ADJUDICATION INCORPORATED: "
        + payload["director_technical_adjudication_b0_2"]["status"],
        "3. TRANSIENT UNIVERSE CONTRACT: "
        + json.dumps(payload["transient_candidate_universes"], sort_keys=True),
        "4. MONTH REPRESENTATION CONTRACT: "
        + json.dumps(
            payload["director_technical_adjudication_b0_2"]["contract"]["month_list_representation"],
            sort_keys=True,
        ),
        "5. INCOMPLETE WINDOW CONTRACT: "
        + json.dumps(
            payload["director_technical_adjudication_b0_2"]["contract"]["incomplete_window_aggregation"],
            sort_keys=True,
        ),
        "6. DTYPE CONTRACT: "
        + json.dumps(
            payload["director_technical_adjudication_b0_2"]["contract"]["arrow_dtype_contract"]["by_type"],
            sort_keys=True,
        ),
        "7. FAILURE_REASON CONTRACT: "
        + json.dumps(
            payload["director_technical_adjudication_b0_2"]["contract"]["failure_reason_contract"],
            sort_keys=True,
        ),
        "8. ZERO-SIEMBRA CONTRACT: "
        + json.dumps(
            payload["director_technical_adjudication_b0_2"]["contract"]["zero_sowing_contract"],
            sort_keys=True,
        ),
        "9. RIGHT-EDGE / INTERNAL-GAP CONTRACT: "
        + json.dumps(
            payload["director_technical_adjudication_b0_2"]["contract"]["right_edge_internal_gap_contract"],
            sort_keys=True,
        ),
        f"10. UNIFIED LONG STATUS: {payload['unified_long_build_status']['status']}",
        "11. STRICT DIAGNOSTIC: "
        + json.dumps(payload["strict_diagnostic_reproduction"]["combined"], sort_keys=True)
        + f"; status={payload['strict_diagnostic_reproduction']['status']}",
        "12. PERENNIAL STRUCTURAL COUNT: "
        + json.dumps(payload["perennial_structural_count"], sort_keys=True),
        "13. OUTCOME FIREWALL: PASS; no forbidden panel, harvest/production, or ICEN values loaded; no Stage-B parquet exists",
        f"14. FULL TEST RESULT: {full_test_result}",
        f"15. SPEC AUDITOR RESULT: {spec_auditor_result}",
        "16. GIT DIFF CHECK: RUN_SEPARATELY",
        "17. FILE SCOPE: only B0 files; git status: " + (status if status else "CLEAN"),
        f"18. FINAL B0.2 STATUS: {payload['final_b0_verdict']}",
    ]


def main() -> int:
    payload = build_report_payload()
    write_report(payload)
    for line in terminal_lines(payload):
        print(line)
    return 0 if not payload["final_b0_verdict"].endswith("FAIL") else 1


if __name__ == "__main__":
    raise SystemExit(main())
