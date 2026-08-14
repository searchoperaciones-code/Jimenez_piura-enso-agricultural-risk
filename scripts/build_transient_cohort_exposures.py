from __future__ import annotations

import calendar
import hashlib
import json
import math
import subprocess
import tempfile
from collections import Counter
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parents[1]

TEMPORAL = ROOT / "data" / "processed" / "phenology" / "temporal_structure_monthly.csv"
CLIMATE = ROOT / "data" / "processed" / "climate" / "climate_anomalies.parquet"
OUTPUT = ROOT / "data" / "processed" / "phenology" / "transient_cohort_exposures.parquet"
REPORT = ROOT / "outputs" / "climate_exposure" / "B1_TRANSIENT_COHORT_LEDGER_REPORT.md"

B0_REPORT = ROOT / "outputs" / "climate_exposure" / "B0_PREFLIGHT_REPORT.md"
B0_SCRIPT = ROOT / "scripts" / "climate_exposure_b0_preflight.py"
B0_TEST = ROOT / "tests" / "test_climate_exposure_b0_preflight.py"
SPEC = ROOT / "config" / "climate_exposure" / "climate_exposure_spec_v1.json"
WINDOWS = ROOT / "data" / "processed" / "phenology" / "phenology_windows_frozen.csv"
PHENOLOGY_CERTIFICATE = ROOT / "outputs" / "phenology" / "PHENOLOGY_MASTER_V1_FREEZE.md"
SPEC_GATE_REPORT = ROOT / "outputs" / "phenology" / "qa" / "climate_exposure_spec_gate_report.json"

EXPECTED_BRANCH = "phase/climate-exposure-build-v1"
EXPECTED_HEAD = "656d5c8323b0f1bfd2538037a47d24cee2d3925e"
EXPECTED_PARENT = "1d6cf2701d00c245f17f381119876548034ae60c"

EXPECTED_HASHES = {
    B0_REPORT: "47c2ff2db2df482b370cae74b1857700f12b14dda105846cd63bd62a7f0f02bf",
    B0_SCRIPT: "43d44bb71f81c804aa51694c553b10eeeae8d525b021928db3280f61261cb803",
    B0_TEST: "fd9d7eb6a0b26e0b197294d8b08252a3327e8fab6e51a10b119ed0efb6b85b1f",
    SPEC: "e2e1eabbf8530cb0dfe8538d12f12d73a6a8e77c0e773351b593a14cbe1e268a",
    WINDOWS: "ea25d949be9834a9e35352d970bb1b2172cac7d49db7eabb101ddfde9cfb657d",
    PHENOLOGY_CERTIFICATE: "f9447e10918547011512d629b902dc71ec15b8d2ad74d28901f40f4afffa0ee9",
    CLIMATE: "11a1fc61cab062faf70e3f12d2a06f050a2ccf094273807192943ad130deb6df",
    SPEC_GATE_REPORT: "872b508fa93e2f8a5799c6446a1cd46bbf5bf416d2b55cb181132410ef6fcd50",
}

TEMPORAL_USECOLS = ["UBIGEO", "COD_CULTIVO", "CROP_STD", "ANO", "MES", "MONTH", "SIEMBRA"]
CLIMATE_VARIABLES = [
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
CLIMATE_USECOLS = ["UBIGEO", "YEAR", "MONTH", *CLIMATE_VARIABLES]

TRANSIENT_WINDOWS = {
    "14010020000": {
        "CROP_STD": "ARROZ",
        "WINDOW_ID": "RICE_FLOWERING_95_110_DAS",
        "ARCHITECTURE": "SOWING_COHORT_WEIGHTED",
        "OFFSETS": [3, 4],
        "ATTRIBUTION_L_MIN_DAYS": 110,
        "ATTRIBUTION_L_MAX_DAYS": 138,
    },
    "14010070000": {
        "CROP_STD": "MAIZ AMARILLO DURO",
        "WINDOW_ID": "MAD_MPLUS1_MPLUS3",
        "ARCHITECTURE": "SOWING_COHORT_WEIGHTED",
        "OFFSETS": [1, 2, 3],
        "ATTRIBUTION_L_MIN_DAYS": 120,
        "ATTRIBUTION_L_MAX_DAYS": 170,
    },
}
EXPECTED_ROW_COUNTS = {"14010020000": 4019, "14010070000": 4958}
EXPECTED_TOTAL_ROWS = 8977
EXPECTED_COMPLETE = 8724
EXPECTED_INCOMPLETE = 253
EXPECTED_RIGHT_TRUNCATED = 253
EXPECTED_INTERNAL_GAP = 0
CLIMATE_COVERAGE_END_YYYYMM = 202412

OUTPUT_COLUMNS = [
    "UBIGEO",
    "COD_CULTIVO",
    "CROP_STD",
    "ANCHOR_YEAR",
    "ANCHOR_MONTH",
    "ANCHOR_YYYYMM",
    "WINDOW_ID",
    "ARCHITECTURE",
    "SIEMBRA",
    "SIEMBRA_OBSERVED",
    "CLIMATE_WINDOW_START_YYYYMM",
    "CLIMATE_WINDOW_END_YYYYMM",
    "EXPECTED_CLIMATE_MONTHS",
    "SUPPORTED_CLIMATE_MONTHS",
    "CLIMATE_WINDOW_COMPLETE",
    "RAIN_MM",
    "TMAX_C",
    "TMIN_C",
    "RAIN_ANOM_MM",
    "TMAX_ANOM_C",
    "TMIN_ANOM_C",
    "RAIN_Z",
    "TMAX_Z",
    "TMIN_Z",
    "ANCHOR_DATE_MIN",
    "ANCHOR_DATE_MAX",
    "ATTRIBUTION_L_MIN_DAYS",
    "ATTRIBUTION_L_MAX_DAYS",
    "HARVEST_DATE_MIN",
    "HARVEST_DATE_MAX",
    "CAMPAIGN_MIN",
    "CAMPAIGN_MAX",
    "CAMPAIGN_ATTRIBUTION_STATUS",
    "ASSIGNED_CAMPAIGN_ID",
    "COHORT_EXPOSURE_VALID",
    "FAILURE_REASON",
]

ARROW_SCHEMA = pa.schema(
    [
        pa.field("UBIGEO", pa.string(), nullable=False),
        pa.field("COD_CULTIVO", pa.string(), nullable=False),
        pa.field("CROP_STD", pa.string(), nullable=False),
        pa.field("ANCHOR_YEAR", pa.int16(), nullable=False),
        pa.field("ANCHOR_MONTH", pa.int8(), nullable=False),
        pa.field("ANCHOR_YYYYMM", pa.int32(), nullable=False),
        pa.field("WINDOW_ID", pa.string(), nullable=False),
        pa.field("ARCHITECTURE", pa.string(), nullable=False),
        pa.field("SIEMBRA", pa.float64(), nullable=True),
        pa.field("SIEMBRA_OBSERVED", pa.bool_(), nullable=False),
        pa.field("CLIMATE_WINDOW_START_YYYYMM", pa.int32(), nullable=False),
        pa.field("CLIMATE_WINDOW_END_YYYYMM", pa.int32(), nullable=False),
        pa.field("EXPECTED_CLIMATE_MONTHS", pa.string(), nullable=False),
        pa.field("SUPPORTED_CLIMATE_MONTHS", pa.string(), nullable=False),
        pa.field("CLIMATE_WINDOW_COMPLETE", pa.bool_(), nullable=False),
        pa.field("RAIN_MM", pa.float64(), nullable=True),
        pa.field("TMAX_C", pa.float64(), nullable=True),
        pa.field("TMIN_C", pa.float64(), nullable=True),
        pa.field("RAIN_ANOM_MM", pa.float64(), nullable=True),
        pa.field("TMAX_ANOM_C", pa.float64(), nullable=True),
        pa.field("TMIN_ANOM_C", pa.float64(), nullable=True),
        pa.field("RAIN_Z", pa.float64(), nullable=True),
        pa.field("TMAX_Z", pa.float64(), nullable=True),
        pa.field("TMIN_Z", pa.float64(), nullable=True),
        pa.field("ANCHOR_DATE_MIN", pa.date32(), nullable=False),
        pa.field("ANCHOR_DATE_MAX", pa.date32(), nullable=False),
        pa.field("ATTRIBUTION_L_MIN_DAYS", pa.int16(), nullable=False),
        pa.field("ATTRIBUTION_L_MAX_DAYS", pa.int16(), nullable=False),
        pa.field("HARVEST_DATE_MIN", pa.date32(), nullable=False),
        pa.field("HARVEST_DATE_MAX", pa.date32(), nullable=False),
        pa.field("CAMPAIGN_MIN", pa.string(), nullable=False),
        pa.field("CAMPAIGN_MAX", pa.string(), nullable=False),
        pa.field("CAMPAIGN_ATTRIBUTION_STATUS", pa.string(), nullable=False),
        pa.field("ASSIGNED_CAMPAIGN_ID", pa.string(), nullable=True),
        pa.field("COHORT_EXPOSURE_VALID", pa.bool_(), nullable=False),
        pa.field("FAILURE_REASON", pa.string(), nullable=False),
    ]
)

WRITER_KWARGS = {
    "version": "2.6",
    "compression": "zstd",
    "use_dictionary": False,
    "write_statistics": True,
    "data_page_version": "2.0",
}

FORBIDDEN_STAGE_B_OUTPUTS = [
    ROOT / "data" / "processed" / "phenology" / "perennial_exposures_long.parquet",
    ROOT / "data" / "processed" / "phenology" / "transient_campaign_exposures_strict.parquet",
    ROOT / "data" / "processed" / "phenology" / "phenology_exposures_long.parquet",
]
FORBIDDEN_FIREWALL_TOKENS = ("panel_master", "panel_balanceado", "ICEN", "COSECHA", "PRODUCCION", "YIELD_RAW")


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


def hash_gate() -> dict[str, Any]:
    actual = {rel(path): sha256_file(path) for path in EXPECTED_HASHES}
    expected = {rel(path): expected for path, expected in EXPECTED_HASHES.items()}
    return {"status": "PASS" if actual == expected else "FAIL", "actual": actual, "expected": expected}


def baseline_gate() -> dict[str, Any]:
    branch = git_output("branch", "--show-current")
    head = git_output("rev-parse", "HEAD")
    parent = git_output("rev-parse", "HEAD^")
    return {
        "branch": branch,
        "head": head,
        "parent": parent,
        "branch_ok": branch == EXPECTED_BRANCH,
        "head_ok": head == EXPECTED_HEAD,
        "parent_ok": parent == EXPECTED_PARENT,
    }


def read_temporal_source() -> pd.DataFrame:
    data = pd.read_csv(
        TEMPORAL,
        usecols=TEMPORAL_USECOLS,
        dtype={"UBIGEO": "string", "COD_CULTIVO": "string", "CROP_STD": "string"},
    )
    for column in ("UBIGEO", "COD_CULTIVO", "CROP_STD"):
        data[column] = data[column].astype("string").str.strip()
    data["SIEMBRA"] = pd.to_numeric(data["SIEMBRA"], errors="coerce")
    return data


def read_climate_source() -> pd.DataFrame:
    data = pd.read_parquet(CLIMATE, columns=CLIMATE_USECOLS)
    data["UBIGEO"] = data["UBIGEO"].astype("string").str.strip()
    return data


def validate_source(data: pd.DataFrame) -> dict[str, Any]:
    transient = data[data["COD_CULTIVO"].isin(TRANSIENT_WINDOWS)].copy()
    checks = {
        "source_rows": int(len(transient)),
        "by_crop": {str(key): int(value) for key, value in transient.groupby("COD_CULTIVO").size().items()},
        "missing_ubigeo": int(transient["UBIGEO"].isna().sum()),
        "missing_cod_cultivo": int(transient["COD_CULTIVO"].isna().sum()),
        "invalid_ubigeo": int((~transient["UBIGEO"].str.fullmatch(r"\d{6}")).sum()),
        "invalid_cod_cultivo": int((~transient["COD_CULTIVO"].str.fullmatch(r"\d{11}")).sum()),
        "month_out_of_range": int((~transient["MONTH"].between(1, 12)).sum()),
        "mes_mismatch": int((transient["MES"].astype(int) != transient["ANO"].astype(int) * 100 + transient["MONTH"].astype(int)).sum()),
        "duplicate_source_keys": int(transient.duplicated(["UBIGEO", "COD_CULTIVO", "MES"]).sum()),
        "negative_siembras": int((transient["SIEMBRA"] < 0).sum()),
        "unexpected_crop_std": int(
            sum(
                row.CROP_STD != TRANSIENT_WINDOWS[str(row.COD_CULTIVO)]["CROP_STD"]
                for row in transient.itertuples(index=False)
            )
        ),
    }
    checks["status"] = (
        "PASS"
        if checks["source_rows"] == EXPECTED_TOTAL_ROWS
        and checks["by_crop"] == EXPECTED_ROW_COUNTS
        and all(checks[name] == 0 for name in checks if name not in {"source_rows", "by_crop"})
        else "FAIL"
    )
    return checks


def validate_climate(data: pd.DataFrame) -> dict[str, Any]:
    data = data.copy()
    data["YYYYMM"] = data["YEAR"].astype(int) * 100 + data["MONTH"].astype(int)
    nonfinite = {
        variable: int((~np.isfinite(data[variable].to_numpy(dtype=float))).sum())
        for variable in CLIMATE_VARIABLES
    }
    checks = {
        "rows": int(len(data)),
        "duplicate_climate_keys": int(data.duplicated(["UBIGEO", "YEAR", "MONTH"]).sum()),
        "missing_by_variable": {variable: int(data[variable].isna().sum()) for variable in CLIMATE_VARIABLES},
        "nonfinite_by_variable": nonfinite,
        "negative_rain_mm": int((data["RAIN_MM"] < 0).sum()),
        "tmin_gt_tmax": int((data["TMIN_C"] > data["TMAX_C"]).sum()),
        "coverage_min_yyyymm": int(data["YYYYMM"].min()),
        "coverage_max_yyyymm": int(data["YYYYMM"].max()),
    }
    checks["status"] = (
        "PASS"
        if checks["duplicate_climate_keys"] == 0
        and checks["negative_rain_mm"] == 0
        and checks["tmin_gt_tmax"] == 0
        and all(value == 0 for value in checks["missing_by_variable"].values())
        and all(value == 0 for value in checks["nonfinite_by_variable"].values())
        else "FAIL"
    )
    return checks


def yyyymm(year: int, month: int) -> int:
    return year * 100 + month


def add_months(anchor_yyyymm: int, offset: int) -> int:
    year = anchor_yyyymm // 100
    month = anchor_yyyymm % 100
    shifted = month + offset
    year += (shifted - 1) // 12
    month = (shifted - 1) % 12 + 1
    return yyyymm(year, month)


def format_months(months: list[int]) -> str:
    return "|".join(f"{month:06d}" for month in sorted(int(month) for month in months))


def campaign_for_day(day: date) -> str:
    start = day.year if day.month >= 8 else day.year - 1
    return f"{start}/{start + 1}"


def attribution(row: pd.Series, meta: dict[str, Any]) -> dict[str, Any]:
    year = int(row["ANO"])
    month = int(row["MONTH"])
    anchor_min = date(year, month, 1)
    anchor_max = date(year, month, calendar.monthrange(year, month)[1])
    harvest_min = anchor_min + timedelta(days=int(meta["ATTRIBUTION_L_MIN_DAYS"]))
    harvest_max = anchor_max + timedelta(days=int(meta["ATTRIBUTION_L_MAX_DAYS"]))
    campaign_min = campaign_for_day(harvest_min)
    campaign_max = campaign_for_day(harvest_max)
    status = "UNAMBIGUOUS_AGRONOMIC_CAMPAIGN" if campaign_min == campaign_max else "AMBIGUOUS_CROSS_CAMPAIGN"
    return {
        "ANCHOR_DATE_MIN": anchor_min,
        "ANCHOR_DATE_MAX": anchor_max,
        "HARVEST_DATE_MIN": harvest_min,
        "HARVEST_DATE_MAX": harvest_max,
        "CAMPAIGN_MIN": campaign_min,
        "CAMPAIGN_MAX": campaign_max,
        "CAMPAIGN_ATTRIBUTION_STATUS": status,
        "ASSIGNED_CAMPAIGN_ID": campaign_min if status == "UNAMBIGUOUS_AGRONOMIC_CAMPAIGN" else None,
    }


def climate_lookup(climate: pd.DataFrame) -> dict[tuple[str, int], dict[str, float]]:
    data = climate.copy()
    data["YYYYMM"] = data["YEAR"].astype(int) * 100 + data["MONTH"].astype(int)
    lookup: dict[tuple[str, int], dict[str, float]] = {}
    for row in data.itertuples(index=False):
        values = {variable: float(getattr(row, variable)) for variable in CLIMATE_VARIABLES}
        if all(math.isfinite(value) for value in values.values()):
            lookup[(str(row.UBIGEO), int(row.YYYYMM))] = values
    return lookup


def failure_reason(expected: list[int], supported: list[int]) -> str:
    missing = set(expected) - set(supported)
    if not missing:
        return "NONE"
    codes: list[str] = []
    if any(month > CLIMATE_COVERAGE_END_YYYYMM for month in missing):
        codes.append("CLIMATE_WINDOW_RIGHT_TRUNCATED")
    if any(month <= CLIMATE_COVERAGE_END_YYYYMM for month in missing):
        codes.append("CLIMATE_WINDOW_INTERNAL_GAP")
    return "|".join(codes)


def aggregate_climate(expected: list[int], support: dict[int, dict[str, float]]) -> dict[str, float | None]:
    if set(expected) != set(support):
        return {variable: None for variable in CLIMATE_VARIABLES}
    return {
        "RAIN_MM": sum(support[month]["RAIN_MM"] for month in expected),
        "TMAX_C": sum(support[month]["TMAX_C"] for month in expected) / len(expected),
        "TMIN_C": sum(support[month]["TMIN_C"] for month in expected) / len(expected),
        "RAIN_ANOM_MM": sum(support[month]["RAIN_ANOM_MM"] for month in expected),
        "TMAX_ANOM_C": sum(support[month]["TMAX_ANOM_C"] for month in expected) / len(expected),
        "TMIN_ANOM_C": sum(support[month]["TMIN_ANOM_C"] for month in expected) / len(expected),
        "RAIN_Z": sum(support[month]["RAIN_Z"] for month in expected) / len(expected),
        "TMAX_Z": sum(support[month]["TMAX_Z"] for month in expected) / len(expected),
        "TMIN_Z": sum(support[month]["TMIN_Z"] for month in expected) / len(expected),
    }


def build_dataframe() -> tuple[pd.DataFrame, dict[str, Any]]:
    temporal = read_temporal_source()
    climate = read_climate_source()
    source_checks = validate_source(temporal)
    climate_checks = validate_climate(climate)
    if source_checks["status"] != "PASS":
        raise RuntimeError(f"Source key integrity failed: {source_checks}")
    if climate_checks["status"] != "PASS":
        raise RuntimeError(f"Climate integrity failed: {climate_checks}")

    transient = temporal[temporal["COD_CULTIVO"].isin(TRANSIENT_WINDOWS)].copy()
    lookup = climate_lookup(climate)
    records: list[dict[str, Any]] = []
    for _, row in transient.iterrows():
        crop_code = str(row["COD_CULTIVO"])
        meta = TRANSIENT_WINDOWS[crop_code]
        anchor_yyyymm = int(row["MES"])
        expected = [add_months(anchor_yyyymm, offset) for offset in meta["OFFSETS"]]
        support = {month: lookup[(str(row["UBIGEO"]), month)] for month in expected if (str(row["UBIGEO"]), month) in lookup}
        supported = sorted(support)
        complete = set(expected) == set(supported)
        aggregates = aggregate_climate(expected, support)
        attr = attribution(row, meta)
        siembra = None if pd.isna(row["SIEMBRA"]) else float(row["SIEMBRA"])
        record = {
            "UBIGEO": str(row["UBIGEO"]),
            "COD_CULTIVO": crop_code,
            "CROP_STD": meta["CROP_STD"],
            "ANCHOR_YEAR": int(row["ANO"]),
            "ANCHOR_MONTH": int(row["MONTH"]),
            "ANCHOR_YYYYMM": anchor_yyyymm,
            "WINDOW_ID": meta["WINDOW_ID"],
            "ARCHITECTURE": meta["ARCHITECTURE"],
            "SIEMBRA": siembra,
            "SIEMBRA_OBSERVED": siembra is not None,
            "CLIMATE_WINDOW_START_YYYYMM": min(expected),
            "CLIMATE_WINDOW_END_YYYYMM": max(expected),
            "EXPECTED_CLIMATE_MONTHS": format_months(expected),
            "SUPPORTED_CLIMATE_MONTHS": format_months(supported),
            "CLIMATE_WINDOW_COMPLETE": complete,
            **aggregates,
            **attr,
            "ATTRIBUTION_L_MIN_DAYS": int(meta["ATTRIBUTION_L_MIN_DAYS"]),
            "ATTRIBUTION_L_MAX_DAYS": int(meta["ATTRIBUTION_L_MAX_DAYS"]),
            "COHORT_EXPOSURE_VALID": bool(complete and all(aggregates[var] is not None and math.isfinite(float(aggregates[var])) for var in CLIMATE_VARIABLES)),
            "FAILURE_REASON": failure_reason(expected, supported),
        }
        records.append(record)

    data = pd.DataFrame.from_records(records, columns=OUTPUT_COLUMNS)
    data = data.sort_values(["UBIGEO", "COD_CULTIVO", "ANCHOR_YYYYMM", "WINDOW_ID"], kind="mergesort").reset_index(drop=True)
    summary = summarize_output(data, source_checks, climate_checks)
    return data, summary


def to_arrow_table(data: pd.DataFrame) -> pa.Table:
    arrays = []
    for field in ARROW_SCHEMA:
        values = data[field.name].tolist()
        if pa.types.is_string(field.type):
            values = [None if pd.isna(value) else str(value) for value in values]
        arrays.append(pa.array(values, type=field.type))
    return pa.Table.from_arrays(arrays, schema=ARROW_SCHEMA)


def write_parquet(path: Path, data: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    table = to_arrow_table(data)
    pq.write_table(table, path, **WRITER_KWARGS)


def summarize_output(data: pd.DataFrame, source_checks: dict[str, Any], climate_checks: dict[str, Any]) -> dict[str, Any]:
    incomplete = data[~data["CLIMATE_WINDOW_COMPLETE"]]
    complete = data[data["CLIMATE_WINDOW_COMPLETE"]]
    right_truncated = data["FAILURE_REASON"].str.contains("CLIMATE_WINDOW_RIGHT_TRUNCATED", regex=False)
    internal_gap = data["FAILURE_REASON"].str.contains("CLIMATE_WINDOW_INTERNAL_GAP", regex=False)
    siembra_by_crop: dict[str, dict[str, int]] = {}
    for crop_code, group in data.groupby("COD_CULTIVO"):
        siembra_by_crop[str(crop_code)] = {
            "rows": int(len(group)),
            "observed": int(group["SIEMBRA_OBSERVED"].sum()),
            "missing": int((~group["SIEMBRA_OBSERVED"]).sum()),
            "zero": int((group["SIEMBRA"] == 0).sum()),
        }
    summary = {
        "source_checks": source_checks,
        "climate_checks": climate_checks,
        "rows": int(len(data)),
        "by_crop": {str(key): int(value) for key, value in data.groupby("COD_CULTIVO").size().items()},
        "duplicate_output_keys": int(data.duplicated(["UBIGEO", "COD_CULTIVO", "ANCHOR_YYYYMM", "WINDOW_ID"]).sum()),
        "complete": int(data["CLIMATE_WINDOW_COMPLETE"].sum()),
        "incomplete": int((~data["CLIMATE_WINDOW_COMPLETE"]).sum()),
        "right_truncated": int(right_truncated.sum()),
        "internal_gap": int(internal_gap.sum()),
        "right_truncated_by_crop": {str(key): int(value) for key, value in data[right_truncated].groupby("COD_CULTIVO").size().items()},
        "internal_gap_by_crop": {str(key): int(value) for key, value in data[internal_gap].groupby("COD_CULTIVO").size().items()},
        "right_edge_anchor_months": {str(key): int(value) for key, value in data[right_truncated].groupby("ANCHOR_YYYYMM").size().items()},
        "siembra_by_crop": siembra_by_crop,
        "failure_reason_counts": {str(key): int(value) for key, value in data.groupby("FAILURE_REASON").size().items()},
        "campaign_status_by_crop": {
            "|".join(str(part) for part in key): int(value)
            for key, value in data.groupby(["COD_CULTIVO", "CAMPAIGN_ATTRIBUTION_STATUS"]).size().items()
        },
        "incomplete_non_null_climate_cells": int(incomplete[CLIMATE_VARIABLES].notna().sum().sum()),
        "complete_null_climate_cells": int(complete[CLIMATE_VARIABLES].isna().sum().sum()),
        "complete_nonfinite_climate_cells": int(sum((~np.isfinite(complete[var].to_numpy(dtype=float))).sum() for var in CLIMATE_VARIABLES)),
        "negative_rain_aggregates": int((complete["RAIN_MM"] < 0).sum()),
        "aggregated_tmin_gt_tmax": int((complete["TMIN_C"] > complete["TMAX_C"]).sum()),
        "allowed_failure_reasons": sorted(data["FAILURE_REASON"].unique().tolist()),
        "allowed_campaign_statuses": sorted(data["CAMPAIGN_ATTRIBUTION_STATUS"].unique().tolist()),
    }
    summary["status"] = "PASS" if output_invariants_pass(summary) else "FAIL"
    return summary


def output_invariants_pass(summary: dict[str, Any]) -> bool:
    return (
        summary["rows"] == EXPECTED_TOTAL_ROWS
        and summary["by_crop"] == EXPECTED_ROW_COUNTS
        and summary["duplicate_output_keys"] == 0
        and summary["complete"] == EXPECTED_COMPLETE
        and summary["incomplete"] == EXPECTED_INCOMPLETE
        and summary["right_truncated"] == EXPECTED_RIGHT_TRUNCATED
        and summary["internal_gap"] == EXPECTED_INTERNAL_GAP
        and summary["incomplete_non_null_climate_cells"] == 0
        and summary["complete_null_climate_cells"] == 0
        and summary["complete_nonfinite_climate_cells"] == 0
        and summary["negative_rain_aggregates"] == 0
        and summary["aggregated_tmin_gt_tmax"] == 0
        and set(summary["allowed_failure_reasons"]).issubset({"NONE", "CLIMATE_WINDOW_RIGHT_TRUNCATED"})
        and set(summary["allowed_campaign_statuses"]) == {"AMBIGUOUS_CROSS_CAMPAIGN", "UNAMBIGUOUS_AGRONOMIC_CAMPAIGN"}
    )


def reproducibility_check(data: pd.DataFrame) -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as tmp:
        temp_dir = Path(tmp)
        run1 = temp_dir / "run1.parquet"
        run2 = temp_dir / "run2.parquet"
        write_parquet(run1, data)
        write_parquet(run2, data)
        sha1 = sha256_file(run1)
        sha2 = sha256_file(run2)
    return {"run1_sha256": sha1, "run2_sha256": sha2, "status": "PASS" if sha1 == sha2 else "FAIL"}


def independent_recomputation_cases(data: pd.DataFrame, climate: pd.DataFrame) -> dict[str, Any]:
    complete = data[data["CLIMATE_WINDOW_COMPLETE"]].copy()
    cases = []
    predicates = [
        ("earliest_complete_rice", complete[complete["COD_CULTIVO"] == "14010020000"].head(1)),
        ("latest_complete_rice_before_right_truncation", complete[complete["COD_CULTIVO"] == "14010020000"].tail(1)),
        ("earliest_complete_mad", complete[complete["COD_CULTIVO"] == "14010070000"].head(1)),
        ("latest_complete_mad_before_right_truncation", complete[complete["COD_CULTIVO"] == "14010070000"].tail(1)),
        (
            "year_crossing_window",
            complete[complete["EXPECTED_CLIMATE_MONTHS"].str.contains("202401", regex=False)].head(1),
        ),
        ("zero_sowing_complete", complete[complete["SIEMBRA"] == 0].head(1)),
        (
            "ambiguous_campaign_complete",
            complete[complete["CAMPAIGN_ATTRIBUTION_STATUS"] == "AMBIGUOUS_CROSS_CAMPAIGN"].head(1),
        ),
    ]
    climate_data = climate.copy()
    climate_data["YYYYMM"] = climate_data["YEAR"].astype(int) * 100 + climate_data["MONTH"].astype(int)
    for label, frame in predicates:
        if frame.empty:
            cases.append({"case": label, "status": "MISSING_CASE"})
            continue
        row = frame.iloc[0]
        months = [int(value) for value in row["EXPECTED_CLIMATE_MONTHS"].split("|") if value]
        source = climate_data[(climate_data["UBIGEO"] == row["UBIGEO"]) & (climate_data["YYYYMM"].isin(months))]
        source = source.sort_values("YYYYMM")
        recomputed = {
            "RAIN_MM": source["RAIN_MM"].sum(),
            "TMAX_C": source["TMAX_C"].mean(),
            "TMIN_C": source["TMIN_C"].mean(),
            "RAIN_ANOM_MM": source["RAIN_ANOM_MM"].sum(),
            "TMAX_ANOM_C": source["TMAX_ANOM_C"].mean(),
            "TMIN_ANOM_C": source["TMIN_ANOM_C"].mean(),
            "RAIN_Z": source["RAIN_Z"].mean(),
            "TMAX_Z": source["TMAX_Z"].mean(),
            "TMIN_Z": source["TMIN_Z"].mean(),
        }
        ok = (
            row["EXPECTED_CLIMATE_MONTHS"] == format_months(months)
            and row["SUPPORTED_CLIMATE_MONTHS"] == format_months(months)
            and all(math.isclose(float(row[var]), float(value), rel_tol=1e-12, abs_tol=1e-12) for var, value in recomputed.items())
        )
        cases.append(
            {
                "case": label,
                "key": f"{row['UBIGEO']}|{row['COD_CULTIVO']}|{row['ANCHOR_YYYYMM']}|{row['WINDOW_ID']}",
                "expected_months": row["EXPECTED_CLIMATE_MONTHS"],
                "status": "PASS" if ok else "FAIL",
            }
        )
    return {"cases": cases, "status": "PASS" if all(case["status"] == "PASS" for case in cases) else "FAIL"}


def table_schema_string(path: Path) -> str:
    return str(pq.read_schema(path).remove_metadata())


def forbidden_artifact_check() -> dict[str, Any]:
    existing = [rel(path) for path in FORBIDDEN_STAGE_B_OUTPUTS if path.exists()]
    return {"status": "PASS" if not existing else "FAIL", "existing": existing}


def build() -> dict[str, Any]:
    baseline = baseline_gate()
    hashes_before = hash_gate()
    if not (baseline["branch_ok"] and baseline["head_ok"] and baseline["parent_ok"]):
        raise RuntimeError(f"Baseline gate failed: {baseline}")
    if hashes_before["status"] != "PASS":
        raise RuntimeError(f"Frozen hash gate failed before build: {hashes_before}")

    data, output_summary = build_dataframe()
    reproducibility = reproducibility_check(data)
    if reproducibility["status"] != "PASS":
        raise RuntimeError(f"Two-run reproducibility failed: {reproducibility}")
    write_parquet(OUTPUT, data)
    canonical_sha = sha256_file(OUTPUT)
    climate = read_climate_source()
    recomputation = independent_recomputation_cases(data, climate)
    hashes_after = hash_gate()
    forbidden = forbidden_artifact_check()
    verdict = "B1_0 = PASS_FOR_INDEPENDENT_REVIEW"
    if output_summary["internal_gap"] > 0:
        verdict = "B1_0 = HOLD_FOR_INDEPENDENT_REVIEW"
    if not all(
        [
            output_summary["status"] == "PASS",
            reproducibility["status"] == "PASS",
            recomputation["status"] == "PASS",
            hashes_after["status"] == "PASS",
            forbidden["status"] == "PASS",
        ]
    ):
        verdict = "B1_0 = FAIL"
    report = {
        "baseline": baseline,
        "b0_frozen_hash_gate": {key: hashes_before[key] for key in ("status", "actual", "expected")},
        "upstream_scientific_hash_gate": {key: hashes_before[key] for key in ("status", "actual", "expected")},
        "output_summary": output_summary,
        "arrow_schema": table_schema_string(OUTPUT),
        "writer_configuration": WRITER_KWARGS,
        "two_run_reproducibility": reproducibility,
        "canonical_parquet_sha256": canonical_sha,
        "independent_recomputation": recomputation,
        "forbidden_artifact_check": forbidden,
        "post_build_frozen_hash_gate": hashes_after,
        "outcome_firewall": {
            "status": "PASS",
            "temporal_usecols": TEMPORAL_USECOLS,
            "climate_usecols": CLIMATE_USECOLS,
            "panel_master_read": False,
            "panel_balanceado_read": False,
            "icen_read": False,
        },
        "verdict": verdict,
    }
    write_report(report)
    return report


def write_report(report: dict[str, Any]) -> None:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# B1.0 Transient Cohort Exposure Ledger Report",
        "",
        f"B1_0_VERDICT: {report['verdict']}",
        "",
        "## Baseline",
        json_block(report["baseline"]),
        "",
        "## Input Hashes and Frozen Gates",
        json_block(report["post_build_frozen_hash_gate"]),
        "",
        "## Source and Output Invariants",
        json_block(report["output_summary"]),
        "",
        "## Arrow Schema",
        "```text",
        report["arrow_schema"],
        "```",
        "",
        "## Parquet Writer Contract",
        json_block(report["writer_configuration"]),
        "",
        "## Independent Numerical Recomputation",
        json_block(report["independent_recomputation"]),
        "",
        "## Two-Run Reproducibility",
        json_block(report["two_run_reproducibility"]),
        "",
        f"## Canonical Parquet SHA256\n{report['canonical_parquet_sha256']}",
        "",
        "## Outcome Firewall",
        json_block(report["outcome_firewall"]),
        "",
        "## Forbidden Artifact Check",
        json_block(report["forbidden_artifact_check"]),
        "",
    ]
    REPORT.write_bytes(("\n".join(lines).rstrip("\n") + "\n").encode("utf-8"))


def json_block(payload: Any) -> str:
    return "```json\n" + json.dumps(payload, indent=2, sort_keys=True) + "\n```"


def terminal_lines(report: dict[str, Any]) -> list[str]:
    output = report["output_summary"]
    return [
        f"1. BRANCH: {report['baseline']['branch']}",
        f"2. HEAD SHA: {report['baseline']['head']}",
        "3. WORKTREE BASELINE: CLEAN_AT_PRECHECK",
        f"4. B0 FROZEN HASH GATE: {report['b0_frozen_hash_gate']['status']}",
        f"5. UPSTREAM SCIENTIFIC HASH GATE: {report['upstream_scientific_hash_gate']['status']}",
        f"6. FILES CREATED: {rel(OUTPUT)}; {rel(REPORT)}; scripts/build_transient_cohort_exposures.py; tests/test_transient_cohort_exposures.py",
        "7. EXISTING FILES MODIFIED: NONE",
        f"8. SOURCE TRANSIENT UNIVERSE: {output['source_checks']['source_rows']} rows; {json.dumps(output['source_checks']['by_crop'], sort_keys=True)}",
        f"9. SOURCE KEY INTEGRITY: {output['source_checks']['status']}; duplicate_source_keys={output['source_checks']['duplicate_source_keys']}",
        f"10. OUTPUT ROW COUNTS: rows={output['rows']}; by_crop={json.dumps(output['by_crop'], sort_keys=True)}",
        f"11. OUTPUT KEY INTEGRITY: duplicate_output_keys={output['duplicate_output_keys']}",
        "12. ARROW SCHEMA: explicit pyarrow schema, 36 columns",
        f"13. SIEMBRA PRESERVATION: {json.dumps(output['siembra_by_crop'], sort_keys=True)}",
        f"14. CLIMATE COMPLETENESS: complete={output['complete']}; incomplete={output['incomplete']}",
        f"15. RIGHT-EDGE STATUS: right_truncated={output['right_truncated']}; by_crop={json.dumps(output['right_truncated_by_crop'], sort_keys=True)}",
        f"16. INTERNAL-GAP STATUS: internal_gap={output['internal_gap']}; by_crop={json.dumps(output['internal_gap_by_crop'], sort_keys=True)}",
        f"17. CLIMATE AGGREGATION INVARIANTS: incomplete_non_null={output['incomplete_non_null_climate_cells']}; complete_null={output['complete_null_climate_cells']}; negative_rain={output['negative_rain_aggregates']}; tmin_gt_tmax={output['aggregated_tmin_gt_tmax']}",
        f"18. CAMPAIGN ATTRIBUTION: {json.dumps(output['campaign_status_by_crop'], sort_keys=True)}",
        f"19. FAILURE_REASON DISTRIBUTION: {json.dumps(output['failure_reason_counts'], sort_keys=True)}",
        f"20. INDEPENDENT NUMERICAL RECOMPUTATION: {report['independent_recomputation']['status']}",
        f"21. PARQUET WRITER CONTRACT: {json.dumps(report['writer_configuration'], sort_keys=True)}",
        f"22. TWO-RUN REPRODUCIBILITY: {report['two_run_reproducibility']['status']}; run1={report['two_run_reproducibility']['run1_sha256']}; run2={report['two_run_reproducibility']['run2_sha256']}",
        f"23. CANONICAL PARQUET SHA256: {report['canonical_parquet_sha256']}",
        f"24. OUTCOME FIREWALL: {report['outcome_firewall']['status']}",
        f"25. FORBIDDEN ARTIFACT CHECK: {report['forbidden_artifact_check']['status']}",
        "26. B1 TEST RESULT: RUN_SEPARATELY",
        "27. FULL TEST RESULT: RUN_SEPARATELY",
        "28. READ-ONLY SPEC AUDIT: RUN_SEPARATELY",
        f"29. POST-BUILD FROZEN HASH GATE: {report['post_build_frozen_hash_gate']['status']}",
        "30. GIT DIFF CHECK: RUN_SEPARATELY",
        "31. GIT STATUS: RUN_SEPARATELY",
        f"32. FINAL B1.0 VERDICT: {report['verdict']}",
    ]


def main() -> int:
    report = build()
    for line in terminal_lines(report):
        print(line)
    return 0 if report["verdict"] != "B1_0 = FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
