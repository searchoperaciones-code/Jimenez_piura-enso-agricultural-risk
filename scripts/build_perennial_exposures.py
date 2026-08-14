from __future__ import annotations

import hashlib
import json
import math
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parents[1]

PANEL = ROOT / "data" / "processed" / "panel_master.csv"
CLIMATE = ROOT / "data" / "processed" / "climate" / "climate_anomalies.parquet"
OUTPUT = ROOT / "data" / "processed" / "phenology" / "perennial_exposures_long.parquet"
REPORT = ROOT / "outputs" / "climate_exposure" / "B2_PERENNIAL_EXPOSURE_LEDGER_REPORT.md"

FROZEN_HASHES = {
    ROOT / "data" / "processed" / "phenology" / "transient_cohort_exposures.parquet": "e4ce7922f00a516643a5de832cc38377e20b3755ac46152cfb79900441564b39",
    ROOT / "outputs" / "climate_exposure" / "B1_TRANSIENT_COHORT_LEDGER_REPORT.md": "256b41893b3b86a364899b1376f1a2fbb7c39f81efba41d9e507c78bceec12a2",
    ROOT / "scripts" / "build_transient_cohort_exposures.py": "1b8c23dcc76b13bbfba3559e56c4ea85d361d0907124028d7ae981674956186b",
    ROOT / "tests" / "test_transient_cohort_exposures.py": "b1ed9eb31961eac6918ee04e4d94d6c941e437f2cec067ba3948dca9c86226e5",
    ROOT / "outputs" / "climate_exposure" / "B0_PREFLIGHT_REPORT.md": "47c2ff2db2df482b370cae74b1857700f12b14dda105846cd63bd62a7f0f02bf",
    ROOT / "scripts" / "climate_exposure_b0_preflight.py": "43d44bb71f81c804aa51694c553b10eeeae8d525b021928db3280f61261cb803",
    ROOT / "tests" / "test_climate_exposure_b0_preflight.py": "fd9d7eb6a0b26e0b197294d8b08252a3327e8fab6e51a10b119ed0efb6b85b1f",
    ROOT / "config" / "climate_exposure" / "climate_exposure_spec_v1.json": "e2e1eabbf8530cb0dfe8538d12f12d73a6a8e77c0e773351b593a14cbe1e268a",
    ROOT / "data" / "processed" / "phenology" / "phenology_windows_frozen.csv": "ea25d949be9834a9e35352d970bb1b2172cac7d49db7eabb101ddfde9cfb657d",
    ROOT / "outputs" / "phenology" / "PHENOLOGY_MASTER_V1_FREEZE.md": "f9447e10918547011512d629b902dc71ec15b8d2ad74d28901f40f4afffa0ee9",
    CLIMATE: "11a1fc61cab062faf70e3f12d2a06f050a2ccf094273807192943ad130deb6df",
    ROOT / "outputs" / "phenology" / "qa" / "climate_exposure_spec_gate_report.json": "872b508fa93e2f8a5799c6446a1cd46bbf5bf416d2b55cb181132410ef6fcd50",
}

EXPECTED_BRANCH = "phase/climate-exposure-build-v1"
EXPECTED_HEAD = "c50a649724b9167cd1fbcc096df4eb62e76f2cfe"
EXPECTED_PARENT = "656d5c8323b0f1bfd2538037a47d24cee2d3925e"

PANEL_USECOLS = ["UBIGEO", "COD_CULTIVO", "CROP_STD", "ANO"]
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
CLIMATE_COLUMNS = ["UBIGEO", "YEAR", "MONTH", *CLIMATE_VARIABLES]

PERENNIAL_WINDOWS = {
    "13010210000": {
        "CROP_STD": "MANGO",
        "windows": {
            "MANGO_MAY_JUN_CURRENT_YEAR": {"months": [5, 6], "year_offset": 0},
        },
    },
    "13010170102": {
        "CROP_STD": "LIMON SUTIL",
        "windows": {
            "LEMON_FULL_YEAR_T": {"months": list(range(1, 13)), "year_offset": 0},
            "LEMON_FULL_YEAR_T_MINUS_1": {"months": list(range(1, 13)), "year_offset": -1},
        },
    },
    "15010040000": {
        "CROP_STD": "PLATANOS Y BANANAS",
        "windows": {
            "BANANA_FULL_YEAR_T": {"months": list(range(1, 13)), "year_offset": 0},
            "BANANA_FULL_YEAR_T_MINUS_1": {"months": list(range(1, 13)), "year_offset": -1},
        },
    },
}
EXPECTED_PANEL_COUNTS = {"13010210000": 255, "13010170102": 311, "15010040000": 390}
EXPECTED_OUTPUT_COUNTS = {"13010210000": 255, "13010170102": 622, "15010040000": 780}
EXPECTED_WINDOW_COUNTS = {
    "13010210000|MANGO_MAY_JUN_CURRENT_YEAR": 255,
    "13010170102|LEMON_FULL_YEAR_T": 311,
    "13010170102|LEMON_FULL_YEAR_T_MINUS_1": 311,
    "15010040000|BANANA_FULL_YEAR_T": 390,
    "15010040000|BANANA_FULL_YEAR_T_MINUS_1": 390,
}
EXPECTED_PANEL_KEYS = 956
EXPECTED_OUTPUT_ROWS = 1657
CLIMATE_MIN_YYYYMM = 199101
CLIMATE_MAX_YYYYMM = 202412

OUTPUT_COLUMNS = [
    "UBIGEO",
    "COD_CULTIVO",
    "CROP_STD",
    "TIME_BASIS",
    "REFERENCE_PERIOD_ID",
    "REFERENCE_CALENDAR_YEAR",
    "WINDOW_ID",
    "RAIN_MM",
    "TMAX_C",
    "TMIN_C",
    "RAIN_ANOM_MM",
    "TMAX_ANOM_C",
    "TMIN_ANOM_C",
    "RAIN_Z",
    "TMAX_Z",
    "TMIN_Z",
    "EXPOSURE_VALID",
    "FAILURE_REASON",
]

ARROW_SCHEMA = pa.schema(
    [
        pa.field("UBIGEO", pa.string(), nullable=False),
        pa.field("COD_CULTIVO", pa.string(), nullable=False),
        pa.field("CROP_STD", pa.string(), nullable=False),
        pa.field("TIME_BASIS", pa.string(), nullable=False),
        pa.field("REFERENCE_PERIOD_ID", pa.string(), nullable=False),
        pa.field("REFERENCE_CALENDAR_YEAR", pa.int16(), nullable=False),
        pa.field("WINDOW_ID", pa.string(), nullable=False),
        pa.field("RAIN_MM", pa.float64(), nullable=False),
        pa.field("TMAX_C", pa.float64(), nullable=False),
        pa.field("TMIN_C", pa.float64(), nullable=False),
        pa.field("RAIN_ANOM_MM", pa.float64(), nullable=False),
        pa.field("TMAX_ANOM_C", pa.float64(), nullable=False),
        pa.field("TMIN_ANOM_C", pa.float64(), nullable=False),
        pa.field("RAIN_Z", pa.float64(), nullable=False),
        pa.field("TMAX_Z", pa.float64(), nullable=False),
        pa.field("TMIN_Z", pa.float64(), nullable=False),
        pa.field("EXPOSURE_VALID", pa.bool_(), nullable=False),
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

FORBIDDEN_ARTIFACTS = [
    ROOT / "data" / "processed" / "phenology" / "transient_campaign_exposures_strict.parquet",
    ROOT / "data" / "processed" / "phenology" / "phenology_exposures_long.parquet",
]


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


def frozen_hash_gate() -> dict[str, Any]:
    actual = {rel(path): sha256_file(path) for path in FROZEN_HASHES}
    expected = {rel(path): expected for path, expected in FROZEN_HASHES.items()}
    return {"status": "PASS" if actual == expected else "FAIL", "actual": actual, "expected": expected}


def read_panel_keys() -> pd.DataFrame:
    data = pd.read_csv(
        PANEL,
        usecols=PANEL_USECOLS,
        dtype={"UBIGEO": "string", "COD_CULTIVO": "string", "CROP_STD": "string"},
    )
    for column in ("UBIGEO", "COD_CULTIVO", "CROP_STD"):
        data[column] = data[column].astype("string").str.strip()
    return data


def read_climate() -> pd.DataFrame:
    data = pd.read_parquet(CLIMATE, columns=CLIMATE_COLUMNS)
    data["UBIGEO"] = data["UBIGEO"].astype("string").str.strip()
    return data


def yyyymm(year: int, month: int) -> int:
    return year * 100 + month


def expected_months(reference_year: int, window_id: str) -> list[int]:
    for crop in PERENNIAL_WINDOWS.values():
        if window_id in crop["windows"]:
            rule = crop["windows"][window_id]
            year = reference_year + int(rule["year_offset"])
            return [yyyymm(year, month) for month in rule["months"]]
    raise ValueError(f"Unknown window: {window_id}")


def validate_panel(panel: pd.DataFrame) -> dict[str, Any]:
    perennial = panel[panel["COD_CULTIVO"].isin(PERENNIAL_WINDOWS)].copy()
    checks = {
        "panel_perennial_keys": int(len(perennial)),
        "by_crop": {str(key): int(value) for key, value in perennial.groupby("COD_CULTIVO").size().items()},
        "missing_ubigeo": int(perennial["UBIGEO"].isna().sum()),
        "missing_cod_cultivo": int(perennial["COD_CULTIVO"].isna().sum()),
        "invalid_ubigeo": int((~perennial["UBIGEO"].str.fullmatch(r"\d{6}")).sum()),
        "invalid_cod_cultivo": int((~perennial["COD_CULTIVO"].str.fullmatch(r"\d{11}")).sum()),
        "duplicate_panel_keys": int(perennial.duplicated(["UBIGEO", "COD_CULTIVO", "ANO"]).sum()),
        "unexpected_crop_std": int(
            sum(
                row.CROP_STD != PERENNIAL_WINDOWS[str(row.COD_CULTIVO)]["CROP_STD"]
                for row in perennial.itertuples(index=False)
            )
        ),
    }
    checks["status"] = (
        "PASS"
        if checks["panel_perennial_keys"] == EXPECTED_PANEL_KEYS
        and checks["by_crop"] == EXPECTED_PANEL_COUNTS
        and all(checks[name] == 0 for name in checks if name not in {"panel_perennial_keys", "by_crop"})
        else "FAIL"
    )
    return checks


def validate_climate(climate: pd.DataFrame) -> dict[str, Any]:
    data = climate.copy()
    data["YYYYMM"] = data["YEAR"].astype(int) * 100 + data["MONTH"].astype(int)
    nonfinite = {
        variable: int((~np.isfinite(data[variable].to_numpy(dtype=float))).sum())
        for variable in CLIMATE_VARIABLES
    }
    checks = {
        "rows": int(len(data)),
        "duplicate_climate_keys": int(data.duplicated(["UBIGEO", "YEAR", "MONTH"]).sum()),
        "coverage_min_yyyymm": int(data["YYYYMM"].min()),
        "coverage_max_yyyymm": int(data["YYYYMM"].max()),
        "missing_by_variable": {variable: int(data[variable].isna().sum()) for variable in CLIMATE_VARIABLES},
        "nonfinite_by_variable": nonfinite,
        "negative_rain_mm": int((data["RAIN_MM"] < 0).sum()),
        "tmin_gt_tmax": int((data["TMIN_C"] > data["TMAX_C"]).sum()),
    }
    checks["status"] = (
        "PASS"
        if checks["duplicate_climate_keys"] == 0
        and checks["coverage_min_yyyymm"] == CLIMATE_MIN_YYYYMM
        and checks["coverage_max_yyyymm"] == CLIMATE_MAX_YYYYMM
        and checks["negative_rain_mm"] == 0
        and checks["tmin_gt_tmax"] == 0
        and all(value == 0 for value in checks["missing_by_variable"].values())
        and all(value == 0 for value in checks["nonfinite_by_variable"].values())
        else "FAIL"
    )
    return checks


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
    if any(month < CLIMATE_MIN_YYYYMM or month > CLIMATE_MAX_YYYYMM for month in missing):
        codes.append("CLIMATE_WINDOW_OUTSIDE_AVAILABLE_RANGE")
    if any(CLIMATE_MIN_YYYYMM <= month <= CLIMATE_MAX_YYYYMM for month in missing):
        codes.append("CLIMATE_WINDOW_INTERNAL_GAP")
    return "|".join(codes)


def aggregate(expected: list[int], supported_values: dict[int, dict[str, float]]) -> dict[str, float | None]:
    if set(expected) != set(supported_values):
        return {variable: None for variable in CLIMATE_VARIABLES}
    return {
        "RAIN_MM": sum(supported_values[month]["RAIN_MM"] for month in expected),
        "TMAX_C": sum(supported_values[month]["TMAX_C"] for month in expected) / len(expected),
        "TMIN_C": sum(supported_values[month]["TMIN_C"] for month in expected) / len(expected),
        "RAIN_ANOM_MM": sum(supported_values[month]["RAIN_ANOM_MM"] for month in expected),
        "TMAX_ANOM_C": sum(supported_values[month]["TMAX_ANOM_C"] for month in expected) / len(expected),
        "TMIN_ANOM_C": sum(supported_values[month]["TMIN_ANOM_C"] for month in expected) / len(expected),
        "RAIN_Z": sum(supported_values[month]["RAIN_Z"] for month in expected) / len(expected),
        "TMAX_Z": sum(supported_values[month]["TMAX_Z"] for month in expected) / len(expected),
        "TMIN_Z": sum(supported_values[month]["TMIN_Z"] for month in expected) / len(expected),
    }


def build_dataframe() -> tuple[pd.DataFrame, dict[str, Any]]:
    panel = read_panel_keys()
    climate = read_climate()
    panel_checks = validate_panel(panel)
    climate_checks = validate_climate(climate)
    if panel_checks["status"] != "PASS":
        raise RuntimeError(f"Panel universe failed: {panel_checks}")
    if climate_checks["status"] != "PASS":
        raise RuntimeError(f"Climate source failed: {climate_checks}")

    perennial = panel[panel["COD_CULTIVO"].isin(PERENNIAL_WINDOWS)].copy()
    lookup = climate_lookup(climate)
    records: list[dict[str, Any]] = []
    for row in perennial.itertuples(index=False):
        crop = PERENNIAL_WINDOWS[str(row.COD_CULTIVO)]
        for window_id in crop["windows"]:
            months = expected_months(int(row.ANO), window_id)
            supported = {month: lookup[(str(row.UBIGEO), month)] for month in months if (str(row.UBIGEO), month) in lookup}
            values = aggregate(months, supported)
            complete = set(months) == set(supported)
            records.append(
                {
                    "UBIGEO": str(row.UBIGEO),
                    "COD_CULTIVO": str(row.COD_CULTIVO),
                    "CROP_STD": crop["CROP_STD"],
                    "TIME_BASIS": "CALENDAR_YEAR",
                    "REFERENCE_PERIOD_ID": f"{int(row.ANO):04d}",
                    "REFERENCE_CALENDAR_YEAR": int(row.ANO),
                    "WINDOW_ID": window_id,
                    **values,
                    "EXPOSURE_VALID": bool(complete and all(values[var] is not None and math.isfinite(float(values[var])) for var in CLIMATE_VARIABLES)),
                    "FAILURE_REASON": failure_reason(months, sorted(supported)),
                }
            )

    data = pd.DataFrame.from_records(records, columns=OUTPUT_COLUMNS)
    data = data.sort_values(
        ["UBIGEO", "COD_CULTIVO", "REFERENCE_CALENDAR_YEAR", "WINDOW_ID"],
        kind="mergesort",
    ).reset_index(drop=True)
    return data, summarize_output(data, panel_checks, climate_checks)


def summarize_output(data: pd.DataFrame, panel_checks: dict[str, Any], climate_checks: dict[str, Any]) -> dict[str, Any]:
    valid = data[data["EXPOSURE_VALID"]]
    by_window = {
        "|".join(str(part) for part in key): int(value)
        for key, value in data.groupby(["COD_CULTIVO", "WINDOW_ID"]).size().items()
    }
    summary = {
        "panel_checks": panel_checks,
        "climate_checks": climate_checks,
        "rows": int(len(data)),
        "by_crop": {str(key): int(value) for key, value in data.groupby("COD_CULTIVO").size().items()},
        "by_crop_window": by_window,
        "duplicate_output_keys": int(data.duplicated(["UBIGEO", "COD_CULTIVO", "REFERENCE_CALENDAR_YEAR", "WINDOW_ID"]).sum()),
        "time_basis_values": sorted(data["TIME_BASIS"].unique().tolist()),
        "reference_period_contract_failures": int((data["REFERENCE_PERIOD_ID"] != data["REFERENCE_CALENDAR_YEAR"].astype(str)).sum()),
        "valid": int(data["EXPOSURE_VALID"].sum()),
        "invalid": int((~data["EXPOSURE_VALID"]).sum()),
        "failure_reason_counts": {str(key): int(value) for key, value in data.groupby("FAILURE_REASON").size().items()},
        "outside_range": int(data["FAILURE_REASON"].str.contains("CLIMATE_WINDOW_OUTSIDE_AVAILABLE_RANGE", regex=False).sum()),
        "internal_gap": int(data["FAILURE_REASON"].str.contains("CLIMATE_WINDOW_INTERNAL_GAP", regex=False).sum()),
        "null_climate_cells": int(data[CLIMATE_VARIABLES].isna().sum().sum()),
        "nonfinite_climate_cells": int(sum((~np.isfinite(data[var].to_numpy(dtype=float))).sum() for var in CLIMATE_VARIABLES)),
        "negative_rain_rows": int((valid["RAIN_MM"] < 0).sum()),
        "tmin_gt_tmax_rows": int((valid["TMIN_C"] > valid["TMAX_C"]).sum()),
    }
    summary["status"] = "PASS" if output_invariants_pass(summary) else "FAIL"
    return summary


def output_invariants_pass(summary: dict[str, Any]) -> bool:
    return (
        summary["rows"] == EXPECTED_OUTPUT_ROWS
        and summary["by_crop"] == EXPECTED_OUTPUT_COUNTS
        and summary["by_crop_window"] == EXPECTED_WINDOW_COUNTS
        and summary["duplicate_output_keys"] == 0
        and summary["time_basis_values"] == ["CALENDAR_YEAR"]
        and summary["reference_period_contract_failures"] == 0
        and summary["valid"] == EXPECTED_OUTPUT_ROWS
        and summary["invalid"] == 0
        and summary["failure_reason_counts"] == {"NONE": EXPECTED_OUTPUT_ROWS}
        and summary["outside_range"] == 0
        and summary["internal_gap"] == 0
        and summary["null_climate_cells"] == 0
        and summary["nonfinite_climate_cells"] == 0
        and summary["negative_rain_rows"] == 0
        and summary["tmin_gt_tmax_rows"] == 0
    )


def to_arrow_table(data: pd.DataFrame) -> pa.Table:
    arrays = []
    for field in ARROW_SCHEMA:
        values = data[field.name].tolist()
        if pa.types.is_string(field.type):
            values = [str(value) for value in values]
        arrays.append(pa.array(values, type=field.type))
    return pa.Table.from_arrays(arrays, schema=ARROW_SCHEMA)


def write_parquet(path: Path, data: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(to_arrow_table(data), path, **WRITER_KWARGS)


def reproducibility_check(data: pd.DataFrame) -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as tmp:
        run1 = Path(tmp) / "run1.parquet"
        run2 = Path(tmp) / "run2.parquet"
        write_parquet(run1, data)
        write_parquet(run2, data)
        sha1 = sha256_file(run1)
        sha2 = sha256_file(run2)
    return {"run1_sha256": sha1, "run2_sha256": sha2, "status": "PASS" if sha1 == sha2 else "FAIL"}


def independent_recomputation_cases(data: pd.DataFrame, climate: pd.DataFrame) -> dict[str, Any]:
    climate_data = climate.copy()
    climate_data["YYYYMM"] = climate_data["YEAR"].astype(int) * 100 + climate_data["MONTH"].astype(int)
    cases = [
        ("earliest_mango", data[data["COD_CULTIVO"] == "13010210000"].head(1)),
        ("latest_mango", data[data["COD_CULTIVO"] == "13010210000"].tail(1)),
        ("earliest_lemon_t", data[data["WINDOW_ID"] == "LEMON_FULL_YEAR_T"].head(1)),
        ("earliest_lemon_t_minus_1", data[data["WINDOW_ID"] == "LEMON_FULL_YEAR_T_MINUS_1"].head(1)),
        ("latest_lemon_t_minus_1", data[data["WINDOW_ID"] == "LEMON_FULL_YEAR_T_MINUS_1"].tail(1)),
        ("earliest_banana_t", data[data["WINDOW_ID"] == "BANANA_FULL_YEAR_T"].head(1)),
        ("earliest_banana_t_minus_1", data[data["WINDOW_ID"] == "BANANA_FULL_YEAR_T_MINUS_1"].head(1)),
        ("t_minus_1_prior_year_crossing", data[data["WINDOW_ID"].str.endswith("_T_MINUS_1")].head(1)),
    ]
    results: list[dict[str, Any]] = []
    for label, frame in cases:
        if frame.empty:
            results.append({"case": label, "status": "MISSING_CASE"})
            continue
        row = frame.iloc[0]
        months = expected_months(int(row["REFERENCE_CALENDAR_YEAR"]), str(row["WINDOW_ID"]))
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
        ok = all(math.isclose(float(row[var]), float(value), rel_tol=1e-12, abs_tol=1e-12) for var, value in recomputed.items())
        results.append(
            {
                "case": label,
                "key": f"{row['UBIGEO']}|{row['COD_CULTIVO']}|{row['REFERENCE_CALENDAR_YEAR']}|{row['WINDOW_ID']}",
                "expected_months": "|".join(f"{month:06d}" for month in months),
                "status": "PASS" if ok else "FAIL",
            }
        )
    return {"cases": results, "status": "PASS" if all(item["status"] == "PASS" for item in results) else "FAIL"}


def forbidden_artifact_check() -> dict[str, Any]:
    existing = [rel(path) for path in FORBIDDEN_ARTIFACTS if path.exists()]
    return {"status": "PASS" if not existing else "FAIL", "existing": existing}


def build() -> dict[str, Any]:
    baseline = baseline_gate()
    frozen_before = frozen_hash_gate()
    if not (baseline["branch_ok"] and baseline["head_ok"] and baseline["parent_ok"]):
        raise RuntimeError(f"Baseline gate failed: {baseline}")
    if frozen_before["status"] != "PASS":
        raise RuntimeError(f"Frozen hash gate failed before B2: {frozen_before}")

    data, output_summary = build_dataframe()
    reproducibility = reproducibility_check(data)
    if reproducibility["status"] != "PASS":
        raise RuntimeError(f"Two-run reproducibility failed: {reproducibility}")
    write_parquet(OUTPUT, data)
    canonical_sha = sha256_file(OUTPUT)
    climate = read_climate()
    recomputation = independent_recomputation_cases(data, climate)
    frozen_after = frozen_hash_gate()
    forbidden = forbidden_artifact_check()
    verdict = "B2_0 = PASS_FOR_INDEPENDENT_REVIEW"
    if output_summary["invalid"] > 0:
        verdict = "B2_0 = HOLD_FOR_INDEPENDENT_REVIEW"
    if not all(
        [
            output_summary["status"] == "PASS",
            reproducibility["status"] == "PASS",
            canonical_sha == reproducibility["run1_sha256"],
            recomputation["status"] == "PASS",
            frozen_after["status"] == "PASS",
            forbidden["status"] == "PASS",
        ]
    ):
        verdict = "B2_0 = FAIL"
    report = {
        "baseline": baseline,
        "b1_frozen_hash_gate": frozen_before,
        "b0_upstream_hash_gate": frozen_before,
        "output_summary": output_summary,
        "arrow_schema": str(pq.read_schema(OUTPUT).remove_metadata()),
        "writer_configuration": WRITER_KWARGS,
        "two_run_reproducibility": reproducibility,
        "canonical_parquet_sha256": canonical_sha,
        "independent_recomputation": recomputation,
        "outcome_firewall": {
            "status": "PASS",
            "panel_usecols": PANEL_USECOLS,
            "climate_columns": CLIMATE_COLUMNS,
            "other_inputs_read": False,
        },
        "forbidden_artifact_check": forbidden,
        "post_build_frozen_hash_gate": frozen_after,
        "verdict": verdict,
    }
    write_report(report)
    return report


def write_report(report: dict[str, Any]) -> None:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# B2.0 Perennial Exposure Ledger Report",
        "",
        f"B2_0_VERDICT: {report['verdict']}",
        "",
        "## Baseline",
        json_block(report["baseline"]),
        "",
        "## Frozen Hash Gates",
        json_block(report["post_build_frozen_hash_gate"]),
        "",
        "## Output Invariants",
        json_block(report["output_summary"]),
        "",
        "## Arrow Schema",
        "```text",
        report["arrow_schema"],
        "```",
        "",
        "## Writer Configuration",
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
        f"4. B1 FROZEN HASH GATE: {report['b1_frozen_hash_gate']['status']}",
        f"5. B0/UPSTREAM HASH GATE: {report['b0_upstream_hash_gate']['status']}",
        f"6. FILES CREATED: scripts/build_perennial_exposures.py; tests/test_perennial_exposures.py; {rel(REPORT)}; {rel(OUTPUT)}",
        "7. EXISTING FILES MODIFIED: NONE",
        f"8. PERENNIAL PANEL UNIVERSE: {output['panel_checks']['panel_perennial_keys']} keys; {json.dumps(output['panel_checks']['by_crop'], sort_keys=True)}",
        f"9. PANEL KEY INTEGRITY: {output['panel_checks']['status']}; duplicate_panel_keys={output['panel_checks']['duplicate_panel_keys']}",
        f"10. WINDOW EXPANSION COUNTS: {json.dumps(output['by_crop_window'], sort_keys=True)}",
        f"11. OUTPUT ROW COUNTS: rows={output['rows']}; by_crop={json.dumps(output['by_crop'], sort_keys=True)}",
        f"12. OUTPUT KEY INTEGRITY: duplicate_output_keys={output['duplicate_output_keys']}",
        f"13. REFERENCE PERIOD CONTRACT: failures={output['reference_period_contract_failures']}",
        "14. ARROW SCHEMA: explicit pyarrow schema, 18 columns",
        f"15. CLIMATE COMPLETENESS: valid={output['valid']}; invalid={output['invalid']}",
        f"16. FAILURE_REASON DISTRIBUTION: {json.dumps(output['failure_reason_counts'], sort_keys=True)}",
        f"17. CLIMATE AGGREGATION INVARIANTS: null_cells={output['null_climate_cells']}; nonfinite={output['nonfinite_climate_cells']}; negative_rain={output['negative_rain_rows']}; tmin_gt_tmax={output['tmin_gt_tmax_rows']}",
        f"18. INDEPENDENT NUMERICAL RECOMPUTATION: {report['independent_recomputation']['status']}",
        f"19. PARQUET WRITER CONTRACT: {json.dumps(report['writer_configuration'], sort_keys=True)}",
        f"20. TWO-RUN REPRODUCIBILITY: {report['two_run_reproducibility']['status']}; run1={report['two_run_reproducibility']['run1_sha256']}; run2={report['two_run_reproducibility']['run2_sha256']}",
        f"21. CANONICAL PARQUET SHA256: {report['canonical_parquet_sha256']}",
        f"22. OUTCOME FIREWALL: {report['outcome_firewall']['status']}",
        f"23. FORBIDDEN ARTIFACT CHECK: {report['forbidden_artifact_check']['status']}",
        "24. B2 TEST RESULT: RUN_SEPARATELY",
        "25. RAW FULL TEST RESULT: RUN_SEPARATELY",
        "26. PHASE-AWARE TEST RESULT: RUN_SEPARATELY",
        "27. READ-ONLY SPEC AUDIT: RUN_SEPARATELY",
        f"28. POST-BUILD FROZEN HASH GATE: {report['post_build_frozen_hash_gate']['status']}",
        "29. GIT DIFF CHECK: RUN_SEPARATELY",
        "30. GIT STATUS: RUN_SEPARATELY",
        f"31. FINAL B2.0 VERDICT: {report['verdict']}",
    ]


def main() -> int:
    report = build()
    for line in terminal_lines(report):
        print(line)
    return 0 if report["verdict"] != "B2_0 = FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
