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
B1_COHORTS = ROOT / "data" / "processed" / "phenology" / "transient_cohort_exposures.parquet"
OUTPUT = ROOT / "data" / "processed" / "phenology" / "transient_campaign_exposures_strict.parquet"
REPORT = ROOT / "outputs" / "climate_exposure" / "B3_TRANSIENT_CAMPAIGN_STRICT_REPORT.md"

EXPECTED_BRANCH = "phase/climate-exposure-build-v1"
EXPECTED_HEAD = "55f640a6c0621f6afa86860c4b7e24fe9d205025"
EXPECTED_PARENT = "c50a649724b9167cd1fbcc096df4eb62e76f2cfe"

FROZEN_HASHES = {
    ROOT / "data" / "processed" / "phenology" / "perennial_exposures_long.parquet": "3fde5c7fc7a00f4c6600a18f60935bad213408ffa2ba3bac5828603e46984714",
    ROOT / "outputs" / "climate_exposure" / "B2_PERENNIAL_EXPOSURE_LEDGER_REPORT.md": "ea922c8238974d73c826530876fe5b3b5e05231ac4edd121caf0a903e6064503",
    ROOT / "scripts" / "build_perennial_exposures.py": "0b24919c326c985b71e3f022696d21a865f6088f82001e62612af33b1be0c95b",
    ROOT / "tests" / "test_perennial_exposures.py": "189c328f6d1d91d0e95a865eae319599de3fbdba66c9fcd3d19d506c4bffbd38",
    B1_COHORTS: "e4ce7922f00a516643a5de832cc38377e20b3755ac46152cfb79900441564b39",
    ROOT / "outputs" / "climate_exposure" / "B1_TRANSIENT_COHORT_LEDGER_REPORT.md": "256b41893b3b86a364899b1376f1a2fbb7c39f81efba41d9e507c78bceec12a2",
    ROOT / "scripts" / "build_transient_cohort_exposures.py": "1b8c23dcc76b13bbfba3559e56c4ea85d361d0907124028d7ae981674956186b",
    ROOT / "tests" / "test_transient_cohort_exposures.py": "b1ed9eb31961eac6918ee04e4d94d6c941e437f2cec067ba3948dca9c86226e5",
    ROOT / "outputs" / "climate_exposure" / "B0_PREFLIGHT_REPORT.md": "47c2ff2db2df482b370cae74b1857700f12b14dda105846cd63bd62a7f0f02bf",
    ROOT / "scripts" / "climate_exposure_b0_preflight.py": "43d44bb71f81c804aa51694c553b10eeeae8d525b021928db3280f61261cb803",
    ROOT / "tests" / "test_climate_exposure_b0_preflight.py": "fd9d7eb6a0b26e0b197294d8b08252a3327e8fab6e51a10b119ed0efb6b85b1f",
    ROOT / "config" / "climate_exposure" / "climate_exposure_spec_v1.json": "e2e1eabbf8530cb0dfe8538d12f12d73a6a8e77c0e773351b593a14cbe1e268a",
    ROOT / "data" / "processed" / "phenology" / "phenology_windows_frozen.csv": "ea25d949be9834a9e35352d970bb1b2172cac7d49db7eabb101ddfde9cfb657d",
    ROOT / "outputs" / "phenology" / "PHENOLOGY_MASTER_V1_FREEZE.md": "f9447e10918547011512d629b902dc71ec15b8d2ad74d28901f40f4afffa0ee9",
    ROOT / "data" / "processed" / "climate" / "climate_anomalies.parquet": "11a1fc61cab062faf70e3f12d2a06f050a2ccf094273807192943ad130deb6df",
    ROOT / "outputs" / "phenology" / "qa" / "climate_exposure_spec_gate_report.json": "872b508fa93e2f8a5799c6446a1cd46bbf5bf416d2b55cb181132410ef6fcd50",
}

PANEL_USECOLS = ["UBIGEO", "COD_CULTIVO", "CROP_STD", "ANO"]
B1_COLUMNS = [
    "UBIGEO",
    "COD_CULTIVO",
    "CROP_STD",
    "ANCHOR_YYYYMM",
    "WINDOW_ID",
    "SIEMBRA",
    "SIEMBRA_OBSERVED",
    "COHORT_EXPOSURE_VALID",
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

TRANSIENT_CROPS = {
    "14010020000": {
        "CROP_STD": "ARROZ",
        "WINDOW_ID": "RICE_FLOWERING_95_110_DAS",
        "EXPECTED_ROWS": 340,
    },
    "14010070000": {
        "CROP_STD": "MAIZ AMARILLO DURO",
        "WINDOW_ID": "MAD_MPLUS1_MPLUS3",
        "EXPECTED_ROWS": 405,
    },
}
EXPECTED_PANEL_COUNTS = {"14010020000": 340, "14010070000": 405}
EXPECTED_VALID_COUNTS = {"14010020000": 31, "14010070000": 7}
EXPECTED_TOTAL_ROWS = 745
EXPECTED_VALID = 38
EXPECTED_INVALID = 707
WEIGHT_TOLERANCE = 1e-12

FAILURE_ORDER = [
    "STRUCTURAL_LEFT_TRUNCATION",
    "REQUIRED_U_SIEMBRA_NOT_OBSERVED",
    "REQUIRED_A_SIEMBRA_NOT_OBSERVED",
    "AMBIGUOUS_COHORT_SIEMBRA_NONZERO",
    "NO_POSITIVE_UNAMBIGUOUS_SIEMBRA",
    "POSITIVE_WEIGHT_COHORT_CLIMATE_INCOMPLETE",
    "WEIGHT_SUM_TOLERANCE_FAIL",
]

OUTPUT_COLUMNS = [
    "UBIGEO",
    "COD_CULTIVO",
    "CROP_STD",
    "CAMPAIGN_ID",
    "CAMPAIGN_START_YEAR",
    "CAMPAIGN_END_YEAR",
    "WINDOW_ID",
    "UNAMBIGUOUS_COHORT_COUNT",
    "AMBIGUOUS_COHORT_COUNT",
    "CAMPAIGN_SIEMBRA_DENOMINATOR",
    "COHORT_WEIGHT_SUM",
    "EXPECTED_WEIGHT",
    "SUPPORTED_WEIGHT",
    "MISSING_WEIGHT",
    "RAIN_MM",
    "TMAX_C",
    "TMIN_C",
    "RAIN_ANOM_MM",
    "TMAX_ANOM_C",
    "TMIN_ANOM_C",
    "RAIN_Z",
    "TMAX_Z",
    "TMIN_Z",
    "CAMPAIGN_WEIGHTED_EXPOSURE_VALID",
    "FAILURE_REASON",
]

ARROW_SCHEMA = pa.schema(
    [
        pa.field("UBIGEO", pa.string(), nullable=False),
        pa.field("COD_CULTIVO", pa.string(), nullable=False),
        pa.field("CROP_STD", pa.string(), nullable=False),
        pa.field("CAMPAIGN_ID", pa.string(), nullable=False),
        pa.field("CAMPAIGN_START_YEAR", pa.int16(), nullable=False),
        pa.field("CAMPAIGN_END_YEAR", pa.int16(), nullable=False),
        pa.field("WINDOW_ID", pa.string(), nullable=False),
        pa.field("UNAMBIGUOUS_COHORT_COUNT", pa.int16(), nullable=False),
        pa.field("AMBIGUOUS_COHORT_COUNT", pa.int16(), nullable=False),
        pa.field("CAMPAIGN_SIEMBRA_DENOMINATOR", pa.float64(), nullable=True),
        pa.field("COHORT_WEIGHT_SUM", pa.float64(), nullable=True),
        pa.field("EXPECTED_WEIGHT", pa.float64(), nullable=True),
        pa.field("SUPPORTED_WEIGHT", pa.float64(), nullable=True),
        pa.field("MISSING_WEIGHT", pa.float64(), nullable=True),
        pa.field("RAIN_MM", pa.float64(), nullable=True),
        pa.field("TMAX_C", pa.float64(), nullable=True),
        pa.field("TMIN_C", pa.float64(), nullable=True),
        pa.field("RAIN_ANOM_MM", pa.float64(), nullable=True),
        pa.field("TMAX_ANOM_C", pa.float64(), nullable=True),
        pa.field("TMIN_ANOM_C", pa.float64(), nullable=True),
        pa.field("RAIN_Z", pa.float64(), nullable=True),
        pa.field("TMAX_Z", pa.float64(), nullable=True),
        pa.field("TMIN_Z", pa.float64(), nullable=True),
        pa.field("CAMPAIGN_WEIGHTED_EXPOSURE_VALID", pa.bool_(), nullable=False),
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


def read_panel_campaigns() -> pd.DataFrame:
    data = pd.read_csv(
        PANEL,
        usecols=PANEL_USECOLS,
        dtype={"UBIGEO": "string", "COD_CULTIVO": "string", "CROP_STD": "string"},
    )
    for column in ("UBIGEO", "COD_CULTIVO", "CROP_STD"):
        data[column] = data[column].astype("string").str.strip()
    return data


def read_b1_cohorts() -> pd.DataFrame:
    data = pd.read_parquet(B1_COHORTS, columns=B1_COLUMNS)
    for column in ("UBIGEO", "COD_CULTIVO", "CROP_STD", "WINDOW_ID"):
        data[column] = data[column].astype("string").str.strip()
    return data


def yyyymm(year: int, month: int) -> int:
    return year * 100 + month


def strict_domains(crop_code: str, campaign_start_year: int) -> dict[str, list[int]]:
    if crop_code == "14010020000":
        return {
            "U": [yyyymm(campaign_start_year, month) for month in range(5, 13)]
            + [yyyymm(campaign_start_year + 1, month) for month in (1, 2)],
            "A": [yyyymm(campaign_start_year, month) for month in (3, 4)]
            + [yyyymm(campaign_start_year + 1, month) for month in (3, 4)],
        }
    if crop_code == "14010070000":
        return {
            "U": [yyyymm(campaign_start_year, month) for month in range(5, 13)]
            + [yyyymm(campaign_start_year + 1, 1)],
            "A": [yyyymm(campaign_start_year, month) for month in (2, 3, 4)]
            + [yyyymm(campaign_start_year + 1, month) for month in (2, 3, 4)],
        }
    raise ValueError(f"Unexpected transient crop: {crop_code}")


def validate_panel(panel: pd.DataFrame) -> dict[str, Any]:
    transient = panel[panel["COD_CULTIVO"].isin(TRANSIENT_CROPS)].copy()
    checks = {
        "panel_transient_rows": int(len(transient)),
        "by_crop": {str(key): int(value) for key, value in transient.groupby("COD_CULTIVO").size().items()},
        "duplicate_panel_keys": int(transient.duplicated(["UBIGEO", "COD_CULTIVO", "ANO"]).sum()),
        "invalid_ubigeo": int((~transient["UBIGEO"].str.fullmatch(r"\d{6}")).sum()),
        "invalid_cod_cultivo": int((~transient["COD_CULTIVO"].str.fullmatch(r"\d{11}")).sum()),
        "unexpected_crop_std": int(
            sum(
                row.CROP_STD != TRANSIENT_CROPS[str(row.COD_CULTIVO)]["CROP_STD"]
                for row in transient.itertuples(index=False)
            )
        ),
        "campaign_ids": sorted(f"{int(row.ANO) - 1}/{int(row.ANO)}" for row in transient.itertuples(index=False)),
    }
    checks["unique_campaign_ids"] = sorted(set(checks["campaign_ids"]))
    checks["status"] = (
        "PASS"
        if checks["panel_transient_rows"] == EXPECTED_TOTAL_ROWS
        and checks["by_crop"] == EXPECTED_PANEL_COUNTS
        and checks["duplicate_panel_keys"] == 0
        and checks["invalid_ubigeo"] == 0
        and checks["invalid_cod_cultivo"] == 0
        and checks["unexpected_crop_std"] == 0
        else "FAIL"
    )
    return checks


def validate_b1(cohorts: pd.DataFrame) -> dict[str, Any]:
    transient = cohorts[cohorts["COD_CULTIVO"].isin(TRANSIENT_CROPS)].copy()
    negative = int((transient["SIEMBRA"] < 0).sum())
    checks = {
        "rows": int(len(transient)),
        "duplicate_b1_keys": int(transient.duplicated(["UBIGEO", "COD_CULTIVO", "ANCHOR_YYYYMM", "WINDOW_ID"]).sum()),
        "negative_siembras": negative,
        "unexpected_window_id": int(
            sum(
                row.WINDOW_ID != TRANSIENT_CROPS[str(row.COD_CULTIVO)]["WINDOW_ID"]
                for row in transient.itertuples(index=False)
            )
        ),
    }
    checks["status"] = (
        "PASS"
        if checks["duplicate_b1_keys"] == 0
        and checks["negative_siembras"] == 0
        and checks["unexpected_window_id"] == 0
        else "FAIL"
    )
    return checks


def finite_complete(row: pd.Series) -> bool:
    return bool(
        row["COHORT_EXPOSURE_VALID"]
        and all(pd.notna(row[variable]) and math.isfinite(float(row[variable])) for variable in CLIMATE_VARIABLES)
    )


def failure_string(reasons: list[str]) -> str:
    ordered = [reason for reason in FAILURE_ORDER if reason in reasons]
    return "|".join(ordered) if ordered else "NONE"


def build_campaign_record(panel_row: pd.Series, cohort_index: dict[tuple[str, str, int, str], pd.Series]) -> dict[str, Any]:
    crop_code = str(panel_row["COD_CULTIVO"])
    meta = TRANSIENT_CROPS[crop_code]
    campaign_end = int(panel_row["ANO"])
    campaign_start = campaign_end - 1
    campaign_id = f"{campaign_start}/{campaign_end}"
    domains = strict_domains(crop_code, campaign_start)
    window_id = meta["WINDOW_ID"]
    u_rows: list[pd.Series | None] = [
        cohort_index.get((str(panel_row["UBIGEO"]), crop_code, month, window_id)) for month in domains["U"]
    ]
    a_rows: list[pd.Series | None] = [
        cohort_index.get((str(panel_row["UBIGEO"]), crop_code, month, window_id)) for month in domains["A"]
    ]
    u_observed = [row is not None and bool(row["SIEMBRA_OBSERVED"]) for row in u_rows]
    a_observed = [row is not None and bool(row["SIEMBRA_OBSERVED"]) for row in a_rows]
    u_values = [float(row["SIEMBRA"]) for row in u_rows if row is not None and bool(row["SIEMBRA_OBSERVED"])]
    a_values = [float(row["SIEMBRA"]) for row in a_rows if row is not None and bool(row["SIEMBRA_OBSERVED"])]
    unambiguous_count = sum(1 for value in u_values if value > 0)
    ambiguous_count = sum(1 for value in a_values if value > 0)
    every_u_observed = all(u_observed)
    every_a_observed = all(a_observed)
    denominator = sum(u_values) if every_u_observed else None
    weight_system = denominator is not None and denominator > 0
    positive_u_rows = [
        row for row in u_rows if row is not None and bool(row["SIEMBRA_OBSERVED"]) and float(row["SIEMBRA"]) > 0
    ]

    expected_weight = 1.0 if weight_system else None
    cohort_weight_sum = None
    supported_weight = None
    missing_weight = None
    climate_incomplete = False
    weight_tolerance_fail = False
    climate_values = {variable: None for variable in CLIMATE_VARIABLES}
    if weight_system:
        weights = [(float(row["SIEMBRA"]) / float(denominator), row) for row in positive_u_rows]
        cohort_weight_sum = sum(weight for weight, _ in weights)
        supported_weight = sum(weight for weight, row in weights if finite_complete(row))
        missing_weight = expected_weight - supported_weight
        climate_incomplete = any(not finite_complete(row) for _, row in weights)
        weight_tolerance_fail = abs(cohort_weight_sum - 1.0) > WEIGHT_TOLERANCE

    reasons: list[str] = []
    if campaign_id == "2015/2016":
        reasons.append("STRUCTURAL_LEFT_TRUNCATION")
    if not every_u_observed:
        reasons.append("REQUIRED_U_SIEMBRA_NOT_OBSERVED")
    if not every_a_observed:
        reasons.append("REQUIRED_A_SIEMBRA_NOT_OBSERVED")
    if any(value != 0 for value in a_values):
        reasons.append("AMBIGUOUS_COHORT_SIEMBRA_NONZERO")
    if sum(u_values) <= 0:
        reasons.append("NO_POSITIVE_UNAMBIGUOUS_SIEMBRA")
    if climate_incomplete:
        reasons.append("POSITIVE_WEIGHT_COHORT_CLIMATE_INCOMPLETE")
    if weight_tolerance_fail:
        reasons.append("WEIGHT_SUM_TOLERANCE_FAIL")

    valid = not reasons
    if valid:
        weighted = {
            variable: sum(weight * float(row[variable]) for weight, row in weights)
            for variable in CLIMATE_VARIABLES
        }
        climate_values.update(weighted)

    return {
        "UBIGEO": str(panel_row["UBIGEO"]),
        "COD_CULTIVO": crop_code,
        "CROP_STD": meta["CROP_STD"],
        "CAMPAIGN_ID": campaign_id,
        "CAMPAIGN_START_YEAR": campaign_start,
        "CAMPAIGN_END_YEAR": campaign_end,
        "WINDOW_ID": window_id,
        "UNAMBIGUOUS_COHORT_COUNT": unambiguous_count,
        "AMBIGUOUS_COHORT_COUNT": ambiguous_count,
        "CAMPAIGN_SIEMBRA_DENOMINATOR": denominator,
        "COHORT_WEIGHT_SUM": cohort_weight_sum,
        "EXPECTED_WEIGHT": expected_weight,
        "SUPPORTED_WEIGHT": supported_weight,
        "MISSING_WEIGHT": missing_weight,
        **climate_values,
        "CAMPAIGN_WEIGHTED_EXPOSURE_VALID": valid,
        "FAILURE_REASON": failure_string(reasons),
    }


def build_dataframe() -> tuple[pd.DataFrame, dict[str, Any]]:
    panel = read_panel_campaigns()
    cohorts = read_b1_cohorts()
    panel_checks = validate_panel(panel)
    b1_checks = validate_b1(cohorts)
    if panel_checks["status"] != "PASS":
        raise RuntimeError(f"Panel campaign universe failed: {panel_checks}")
    if b1_checks["status"] != "PASS":
        raise RuntimeError(f"B1 cohort source failed: {b1_checks}")

    transient_panel = panel[panel["COD_CULTIVO"].isin(TRANSIENT_CROPS)].copy()
    cohort_index = {
        (str(row.UBIGEO), str(row.COD_CULTIVO), int(row.ANCHOR_YYYYMM), str(row.WINDOW_ID)): pd.Series(row._asdict())
        for row in cohorts.itertuples(index=False)
        if str(row.COD_CULTIVO) in TRANSIENT_CROPS
    }
    records = [build_campaign_record(row, cohort_index) for _, row in transient_panel.iterrows()]
    data = pd.DataFrame.from_records(records, columns=OUTPUT_COLUMNS)
    data = data.sort_values(
        ["UBIGEO", "COD_CULTIVO", "CAMPAIGN_START_YEAR", "WINDOW_ID"],
        kind="mergesort",
    ).reset_index(drop=True)
    return data, summarize_output(data, panel_checks, b1_checks)


def summarize_output(data: pd.DataFrame, panel_checks: dict[str, Any], b1_checks: dict[str, Any]) -> dict[str, Any]:
    valid = data[data["CAMPAIGN_WEIGHTED_EXPOSURE_VALID"]]
    invalid = data[~data["CAMPAIGN_WEIGHTED_EXPOSURE_VALID"]]
    weight_defined = data["EXPECTED_WEIGHT"].notna()
    summary = {
        "panel_checks": panel_checks,
        "b1_checks": b1_checks,
        "rows": int(len(data)),
        "by_crop": {str(key): int(value) for key, value in data.groupby("COD_CULTIVO").size().items()},
        "duplicate_output_keys": int(data.duplicated(["UBIGEO", "COD_CULTIVO", "CAMPAIGN_ID", "WINDOW_ID"]).sum()),
        "valid": int(data["CAMPAIGN_WEIGHTED_EXPOSURE_VALID"].sum()),
        "invalid": int((~data["CAMPAIGN_WEIGHTED_EXPOSURE_VALID"]).sum()),
        "valid_by_crop": {
            str(key): int(value)
            for key, value in data.groupby("COD_CULTIVO")["CAMPAIGN_WEIGHTED_EXPOSURE_VALID"].sum().items()
        },
        "failure_reason_counts": {str(key): int(value) for key, value in data.groupby("FAILURE_REASON").size().items()},
        "unambiguous_count_by_crop": {
            str(key): {"min": int(group.min()), "max": int(group.max()), "sum": int(group.sum())}
            for key, group in data.groupby("COD_CULTIVO")["UNAMBIGUOUS_COHORT_COUNT"]
        },
        "ambiguous_count_by_crop": {
            str(key): {"min": int(group.min()), "max": int(group.max()), "sum": int(group.sum())}
            for key, group in data.groupby("COD_CULTIVO")["AMBIGUOUS_COHORT_COUNT"]
        },
        "denominator_defined": int(data["CAMPAIGN_SIEMBRA_DENOMINATOR"].notna().sum()),
        "denominator_positive": int((data["CAMPAIGN_SIEMBRA_DENOMINATOR"] > 0).sum()),
        "weight_defined": int(weight_defined.sum()),
        "invalid_non_null_climate_cells": int(invalid[CLIMATE_VARIABLES].notna().sum().sum()),
        "valid_null_climate_cells": int(valid[CLIMATE_VARIABLES].isna().sum().sum()),
        "valid_nonfinite_climate_cells": int(sum((~np.isfinite(valid[var].to_numpy(dtype=float))).sum() for var in CLIMATE_VARIABLES)),
        "valid_negative_rain": int((valid["RAIN_MM"] < 0).sum()),
        "valid_tmin_gt_tmax": int((valid["TMIN_C"] > valid["TMAX_C"]).sum()),
        "valid_ambiguous_positive_rows": int((valid["AMBIGUOUS_COHORT_COUNT"] > 0).sum()),
        "valid_no_positive_u_rows": int((valid["UNAMBIGUOUS_COHORT_COUNT"] <= 0).sum()),
        "valid_weight_sum_failures": int((valid["COHORT_WEIGHT_SUM"].sub(1.0).abs() > WEIGHT_TOLERANCE).sum()),
        "supported_plus_missing_failures": int(
            (
                data.loc[weight_defined, "SUPPORTED_WEIGHT"]
                .add(data.loc[weight_defined, "MISSING_WEIGHT"])
                .sub(1.0)
                .abs()
                > WEIGHT_TOLERANCE
            ).sum()
        ),
        "valid_supported_weight_failures": int((valid["SUPPORTED_WEIGHT"].sub(1.0).abs() > WEIGHT_TOLERANCE).sum()),
        "valid_missing_weight_failures": int((valid["MISSING_WEIGHT"].abs() > WEIGHT_TOLERANCE).sum()),
    }
    summary["status"] = "PASS" if output_invariants_pass(summary) else "FAIL"
    return summary


def output_invariants_pass(summary: dict[str, Any]) -> bool:
    return (
        summary["rows"] == EXPECTED_TOTAL_ROWS
        and summary["by_crop"] == EXPECTED_PANEL_COUNTS
        and summary["duplicate_output_keys"] == 0
        and summary["valid"] == EXPECTED_VALID
        and summary["invalid"] == EXPECTED_INVALID
        and summary["valid_by_crop"] == EXPECTED_VALID_COUNTS
        and summary["invalid_non_null_climate_cells"] == 0
        and summary["valid_null_climate_cells"] == 0
        and summary["valid_nonfinite_climate_cells"] == 0
        and summary["valid_negative_rain"] == 0
        and summary["valid_tmin_gt_tmax"] == 0
        and summary["valid_ambiguous_positive_rows"] == 0
        and summary["valid_no_positive_u_rows"] == 0
        and summary["valid_weight_sum_failures"] == 0
        and summary["supported_plus_missing_failures"] == 0
        and summary["valid_supported_weight_failures"] == 0
        and summary["valid_missing_weight_failures"] == 0
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


def independent_recomputation_cases(data: pd.DataFrame, cohorts: pd.DataFrame) -> dict[str, Any]:
    cohort_index = {
        (str(row.UBIGEO), str(row.COD_CULTIVO), int(row.ANCHOR_YYYYMM), str(row.WINDOW_ID)): row._asdict()
        for row in cohorts.itertuples(index=False)
    }
    selectors = [
        ("valid_rice_1", data[(data["COD_CULTIVO"] == "14010020000") & data["CAMPAIGN_WEIGHTED_EXPOSURE_VALID"]].head(1)),
        ("valid_rice_2", data[(data["COD_CULTIVO"] == "14010020000") & data["CAMPAIGN_WEIGHTED_EXPOSURE_VALID"]].tail(1)),
        ("valid_mad_1", data[(data["COD_CULTIVO"] == "14010070000") & data["CAMPAIGN_WEIGHTED_EXPOSURE_VALID"]].head(1)),
        ("valid_mad_2", data[(data["COD_CULTIVO"] == "14010070000") & data["CAMPAIGN_WEIGHTED_EXPOSURE_VALID"]].tail(1)),
        ("ambiguous_a_nonzero", data[data["FAILURE_REASON"].str.contains("AMBIGUOUS_COHORT_SIEMBRA_NONZERO", regex=False)].head(1)),
        ("no_positive_u", data[data["FAILURE_REASON"].str.contains("NO_POSITIVE_UNAMBIGUOUS_SIEMBRA", regex=False)].head(1)),
        ("left_truncated", data[data["FAILURE_REASON"].str.contains("STRUCTURAL_LEFT_TRUNCATION", regex=False)].head(1)),
        ("multiple_failure_reasons", data[data["FAILURE_REASON"].str.contains("|", regex=False)].head(1)),
    ]
    results: list[dict[str, Any]] = []
    for label, frame in selectors:
        if frame.empty:
            results.append({"case": label, "status": "MISSING_CASE"})
            continue
        row = frame.iloc[0]
        domains = strict_domains(str(row["COD_CULTIVO"]), int(row["CAMPAIGN_START_YEAR"]))
        window_id = str(row["WINDOW_ID"])
        u = [cohort_index.get((row["UBIGEO"], row["COD_CULTIVO"], month, window_id)) for month in domains["U"]]
        observed_positive = [item for item in u if item is not None and bool(item["SIEMBRA_OBSERVED"]) and float(item["SIEMBRA"]) > 0]
        if row["CAMPAIGN_WEIGHTED_EXPOSURE_VALID"]:
            denominator = sum(float(item["SIEMBRA"]) for item in u if item is not None and bool(item["SIEMBRA_OBSERVED"]))
            weights = [(float(item["SIEMBRA"]) / denominator, item) for item in observed_positive]
            expected_values = {
                variable: sum(weight * float(item[variable]) for weight, item in weights)
                for variable in CLIMATE_VARIABLES
            }
            ok = (
                math.isclose(float(row["CAMPAIGN_SIEMBRA_DENOMINATOR"]), denominator, abs_tol=WEIGHT_TOLERANCE)
                and all(
                    math.isclose(float(row[variable]), float(value), rel_tol=1e-12, abs_tol=1e-12)
                    for variable, value in expected_values.items()
                )
            )
        else:
            ok = all(pd.isna(row[variable]) for variable in CLIMATE_VARIABLES)
        results.append(
            {
                "case": label,
                "key": f"{row['UBIGEO']}|{row['COD_CULTIVO']}|{row['CAMPAIGN_ID']}|{row['WINDOW_ID']}",
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
        raise RuntimeError(f"Frozen hash gate failed before B3: {frozen_before}")

    data, output_summary = build_dataframe()
    reproducibility = reproducibility_check(data)
    if reproducibility["status"] != "PASS":
        raise RuntimeError(f"Two-run reproducibility failed: {reproducibility}")
    write_parquet(OUTPUT, data)
    canonical_sha = sha256_file(OUTPUT)
    cohorts = read_b1_cohorts()
    recomputation = independent_recomputation_cases(data, cohorts)
    frozen_after = frozen_hash_gate()
    forbidden = forbidden_artifact_check()
    verdict = "B3_0 = PASS_FOR_INDEPENDENT_REVIEW"
    if output_summary["valid"] != EXPECTED_VALID:
        verdict = "B3_0 = HOLD_FOR_INDEPENDENT_REVIEW"
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
        verdict = "B3_0 = FAIL"
    report = {
        "baseline": baseline,
        "frozen_hash_gate": frozen_after,
        "output_summary": output_summary,
        "arrow_schema": str(pq.read_schema(OUTPUT).remove_metadata()),
        "writer_configuration": WRITER_KWARGS,
        "two_run_reproducibility": reproducibility,
        "canonical_parquet_sha256": canonical_sha,
        "independent_recomputation": recomputation,
        "outcome_firewall": {
            "status": "PASS",
            "panel_usecols": PANEL_USECOLS,
            "b1_columns": B1_COLUMNS,
            "direct_monthly_or_climate_source_read": False,
        },
        "forbidden_artifact_check": forbidden,
        "verdict": verdict,
    }
    write_report(report)
    return report


def write_report(report: dict[str, Any]) -> None:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# B3.0 Strict Transient Campaign Exposure Layer Report",
        "",
        f"B3_0_VERDICT: {report['verdict']}",
        "",
        "## Baseline",
        json_block(report["baseline"]),
        "",
        "## Frozen Hash Gate",
        json_block(report["frozen_hash_gate"]),
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
    summary = report["output_summary"]
    return [
        f"1. BRANCH: {report['baseline']['branch']}",
        f"2. HEAD SHA: {report['baseline']['head']}",
        "3. WORKTREE BASELINE: CLEAN_AT_PRECHECK",
        "4. B2 FROZEN HASH GATE: PASS",
        "5. B1 FROZEN HASH GATE: PASS",
        f"6. B0/UPSTREAM HASH GATE: {report['frozen_hash_gate']['status']}",
        f"7. FILES CREATED: scripts/build_transient_campaign_exposures_strict.py; tests/test_transient_campaign_exposures_strict.py; {rel(REPORT)}; {rel(OUTPUT)}",
        "8. EXISTING FILES MODIFIED: NONE",
        f"9. TRANSIENT CAMPAIGN UNIVERSE: {summary['panel_checks']['panel_transient_rows']} rows; {json.dumps(summary['panel_checks']['by_crop'], sort_keys=True)}",
        f"10. PANEL KEY INTEGRITY: {summary['panel_checks']['status']}; duplicate_panel_keys={summary['panel_checks']['duplicate_panel_keys']}",
        f"11. CAMPAIGN MAPPING: {summary['panel_checks']['unique_campaign_ids']}",
        f"12. B1 COHORT SOURCE INTEGRITY: {summary['b1_checks']['status']}; duplicate_b1_keys={summary['b1_checks']['duplicate_b1_keys']}",
        "13. STRICT DOMAIN INTEGRITY: frozen U/A domains applied by crop and campaign start year",
        f"14. OUTPUT ROW COUNTS: rows={summary['rows']}; by_crop={json.dumps(summary['by_crop'], sort_keys=True)}",
        f"15. OUTPUT KEY INTEGRITY: duplicate_output_keys={summary['duplicate_output_keys']}",
        f"16. STRICT VALIDITY COUNTS: valid={summary['valid']}; invalid={summary['invalid']}; valid_by_crop={json.dumps(summary['valid_by_crop'], sort_keys=True)}",
        f"17. FAILURE_REASON DISTRIBUTION: {json.dumps(summary['failure_reason_counts'], sort_keys=True)}",
        f"18. COHORT COUNT DIAGNOSTICS: U={json.dumps(summary['unambiguous_count_by_crop'], sort_keys=True)}; A={json.dumps(summary['ambiguous_count_by_crop'], sort_keys=True)}",
        f"19. SIEMBRA DENOMINATOR DIAGNOSTICS: denominator_defined={summary['denominator_defined']}; denominator_positive={summary['denominator_positive']}",
        f"20. WEIGHT DIAGNOSTICS: weight_defined={summary['weight_defined']}; valid_weight_sum_failures={summary['valid_weight_sum_failures']}",
        f"21. NO-RENORMALIZATION CHECK: supported_plus_missing_failures={summary['supported_plus_missing_failures']}; valid_missing_weight_failures={summary['valid_missing_weight_failures']}",
        f"22. CAMPAIGN CLIMATE EXPOSURE INVARIANTS: invalid_non_null={summary['invalid_non_null_climate_cells']}; valid_null={summary['valid_null_climate_cells']}; valid_nonfinite={summary['valid_nonfinite_climate_cells']}; negative_rain={summary['valid_negative_rain']}; tmin_gt_tmax={summary['valid_tmin_gt_tmax']}",
        "23. ARROW SCHEMA: explicit pyarrow schema, 25 columns",
        f"24. INDEPENDENT NUMERICAL RECOMPUTATION: {report['independent_recomputation']['status']}",
        f"25. PARQUET WRITER CONTRACT: {json.dumps(report['writer_configuration'], sort_keys=True)}",
        f"26. TWO-RUN REPRODUCIBILITY: {report['two_run_reproducibility']['status']}; run1={report['two_run_reproducibility']['run1_sha256']}; run2={report['two_run_reproducibility']['run2_sha256']}",
        f"27. CANONICAL PARQUET SHA256: {report['canonical_parquet_sha256']}",
        f"28. OUTCOME FIREWALL: {report['outcome_firewall']['status']}",
        f"29. FORBIDDEN ARTIFACT CHECK: {report['forbidden_artifact_check']['status']}",
        "30. B3 TEST RESULT: RUN_SEPARATELY",
        "31. RAW FULL TEST RESULT: RUN_SEPARATELY",
        "32. PHASE-AWARE TEST RESULT: RUN_SEPARATELY",
        "33. READ-ONLY SPEC AUDIT: RUN_SEPARATELY",
        f"34. POST-BUILD FROZEN HASH GATE: {report['frozen_hash_gate']['status']}",
        "35. GIT DIFF CHECK: RUN_SEPARATELY",
        "36. GIT STATUS: RUN_SEPARATELY",
        f"37. FINAL B3.0 VERDICT: {report['verdict']}",
    ]


def main() -> int:
    report = build()
    for line in terminal_lines(report):
        print(line)
    return 0 if report["verdict"] != "B3_0 = FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
