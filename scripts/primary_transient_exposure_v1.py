from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import subprocess
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parents[1]

S1_FREEZE_SHA = "2e5823e6aaf842dfd60da968e7423471d6b32f1d"
S1_TAG = "s1-scientific-identity-v1-freeze"
D0_FREEZE_SHA = "1598a09c9a871d81834164d7ee4383e25988d8a5"

S1_CONFIG = ROOT / "config/scientific_identity/scientific_identity_v1.json"
B1_PATH = ROOT / "data/processed/phenology/transient_cohort_exposures.parquet"
B3_PATH = ROOT / "data/processed/phenology/transient_campaign_exposures_strict.parquet"
D0_MASTER_PATH = ROOT / "data/processed/outcomes/transient_campaign_outcomes_master.csv"
D0_LEDGER_PATH = ROOT / "outputs/outcome/D0_TRANSIENT_OUTCOME_EXCLUSION_LEDGER.csv"
PHENOLOGY_PATH = ROOT / "data/processed/phenology/phenology_windows_frozen.csv"

CONFIG_REL = Path("config/exposure_adjudication/primary_transient_exposure_v1.json")
EXPOSURE_REL = Path("data/processed/phenology/transient_econometric_exposures_v1.parquet")
REPORT_REL = Path("outputs/exposure_adjudication/E1_PRIMARY_TRANSIENT_EXPOSURE_REPORT.md")
CANDIDATE_MATRIX_REL = Path("outputs/exposure_adjudication/E1_CANDIDATE_MATRIX.csv")
SUPPORT_OVERLAY_REL = Path("outputs/exposure_adjudication/E1_SUPPORT_OVERLAY.csv")

FROZEN_HASHES = {
    S1_CONFIG: "a5cf4f73eb242528b5dcdbfa87e9adccf8fd43978821cf0c744a96f63042804c",
    B1_PATH: "e4ce7922f00a516643a5de832cc38377e20b3755ac46152cfb79900441564b39",
    B3_PATH: "349413312568d0d423675bf58320ade41d2d9e700f138e7fbec55fc580bc1fb5",
    D0_MASTER_PATH: "9cae62fb1417fa41274f6d504515571abd428b71fecaa0d138d3b786aa538760",
    D0_LEDGER_PATH: "6f7efe29c49b6a1edfaf47743f0b10639a9f56995f742e7513046aff63e814d8",
    PHENOLOGY_PATH: "ea25d949be9834a9e35352d970bb1b2172cac7d49db7eabb101ddfde9cfb657d",
}

CROPS = {
    "14010020000": {
        "name": "Rice",
        "window_id": "RICE_FLOWERING_95_110_DAS",
        "anchor_semantics": "TRANSPLANT_ESTABLISHMENT_PROXY",
        "operational_window": "m+3:m+4",
    },
    "14010070000": {
        "name": "Maiz Amarillo Duro",
        "window_id": "MAD_MPLUS1_MPLUS3",
        "anchor_semantics": "SOWING_MONTH",
        "operational_window": "m+1:m+3",
    },
}

CAMPAIGNS = tuple(f"{year}/{year + 1}" for year in range(2016, 2023))
CLIMATE_VARIABLES = (
    "RAIN_MM",
    "TMAX_C",
    "TMIN_C",
    "RAIN_ANOM_MM",
    "TMAX_ANOM_C",
    "TMIN_ANOM_C",
    "RAIN_Z",
    "TMAX_Z",
    "TMIN_Z",
)

D0_STAGE_A_COLUMNS = (
    "CROP_CODE",
    "CROP_STD",
    "UBIGEO",
    "CAMPAIGN",
    "CAMPAIGN_START_YEAR",
    "CAMPAIGN_END_YEAR",
)
D0_STAGE_B_COLUMNS = (*D0_STAGE_A_COLUMNS, "OUTCOME_VALID_FLAG", "EXCLUSION_REASON")

B1_COLUMNS = (
    "UBIGEO",
    "COD_CULTIVO",
    "CROP_STD",
    "ANCHOR_YYYYMM",
    "WINDOW_ID",
    "SIEMBRA",
    "SIEMBRA_OBSERVED",
    "CLIMATE_WINDOW_COMPLETE",
    "COHORT_EXPOSURE_VALID",
    "FAILURE_REASON",
    *CLIMATE_VARIABLES,
)

OUTPUT_COLUMNS = (
    "UBIGEO",
    "COD_CULTIVO",
    "CROP_STD",
    "CAMPAIGN_ID",
    "WINDOW_ID",
    "EXPECTED_COHORT_COUNT",
    "OBSERVED_COHORT_COUNT",
    "UNAMBIGUOUS_COHORT_COUNT",
    "AMBIGUOUS_COHORT_COUNT",
    "POSITIVE_UNAMBIGUOUS_COHORT_COUNT",
    "POSITIVE_AMBIGUOUS_COHORT_COUNT",
    "MISSING_EXPECTED_COHORT_COUNT",
    "OBSERVED_SIEMBRA_TOTAL",
    "ASSIGNED_UNAMBIGUOUS_SIEMBRA",
    "UNRESOLVED_AMBIGUOUS_SIEMBRA",
    "MISSING_SIEMBRA_WEIGHT",
    "CLIMATE_SUPPORTED_SIEMBRA",
    "IDENTIFIED_OBSERVED_WEIGHT_FRACTION",
    "EXPOSURE_WEIGHT_DENOMINATOR",
    "EXPOSURE_WEIGHT_SUM",
    *CLIMATE_VARIABLES,
    "LEFT_BOUNDARY_FLAG",
    "RIGHT_BOUNDARY_FLAG",
    "UNRESOLVED_AMBIGUOUS_WEIGHT_PRESERVED",
    "SIEMBRA_MISSINGNESS_STATUS",
    "NORMALIZATION_SCOPE",
    "EXPOSURE_VALID",
    "FAILURE_REASON",
)

ARROW_SCHEMA = pa.schema(
    [
        pa.field("UBIGEO", pa.string(), nullable=False),
        pa.field("COD_CULTIVO", pa.string(), nullable=False),
        pa.field("CROP_STD", pa.string(), nullable=False),
        pa.field("CAMPAIGN_ID", pa.string(), nullable=False),
        pa.field("WINDOW_ID", pa.string(), nullable=False),
        pa.field("EXPECTED_COHORT_COUNT", pa.int16(), nullable=False),
        pa.field("OBSERVED_COHORT_COUNT", pa.int16(), nullable=False),
        pa.field("UNAMBIGUOUS_COHORT_COUNT", pa.int16(), nullable=False),
        pa.field("AMBIGUOUS_COHORT_COUNT", pa.int16(), nullable=False),
        pa.field("POSITIVE_UNAMBIGUOUS_COHORT_COUNT", pa.int16(), nullable=False),
        pa.field("POSITIVE_AMBIGUOUS_COHORT_COUNT", pa.int16(), nullable=False),
        pa.field("MISSING_EXPECTED_COHORT_COUNT", pa.int16(), nullable=False),
        pa.field("OBSERVED_SIEMBRA_TOTAL", pa.float64(), nullable=False),
        pa.field("ASSIGNED_UNAMBIGUOUS_SIEMBRA", pa.float64(), nullable=False),
        pa.field("UNRESOLVED_AMBIGUOUS_SIEMBRA", pa.float64(), nullable=False),
        pa.field("MISSING_SIEMBRA_WEIGHT", pa.float64(), nullable=True),
        pa.field("CLIMATE_SUPPORTED_SIEMBRA", pa.float64(), nullable=False),
        pa.field("IDENTIFIED_OBSERVED_WEIGHT_FRACTION", pa.float64(), nullable=True),
        pa.field("EXPOSURE_WEIGHT_DENOMINATOR", pa.float64(), nullable=False),
        pa.field("EXPOSURE_WEIGHT_SUM", pa.float64(), nullable=True),
        *[pa.field(column, pa.float64(), nullable=True) for column in CLIMATE_VARIABLES],
        pa.field("LEFT_BOUNDARY_FLAG", pa.bool_(), nullable=False),
        pa.field("RIGHT_BOUNDARY_FLAG", pa.bool_(), nullable=False),
        pa.field("UNRESOLVED_AMBIGUOUS_WEIGHT_PRESERVED", pa.bool_(), nullable=False),
        pa.field("SIEMBRA_MISSINGNESS_STATUS", pa.string(), nullable=False),
        pa.field("NORMALIZATION_SCOPE", pa.string(), nullable=False),
        pa.field("EXPOSURE_VALID", pa.bool_(), nullable=False),
        pa.field("FAILURE_REASON", pa.string(), nullable=False),
    ]
)

PARQUET_WRITER = {
    "compression": "zstd",
    "data_page_version": "2.0",
    "use_dictionary": False,
    "version": "2.6",
    "write_statistics": True,
}

DOMAINS = (
    "BIOLOGICAL_ALIGNMENT",
    "CAMPAIGN_ATTRIBUTION_IDENTIFICATION",
    "MEASUREMENT_INTERPRETABILITY",
    "SIEMBRA_WEIGHT_INTEGRITY",
    "CLIMATE_WINDOW_COMPLETENESS",
    "TEMPORAL_BOUNDARY_INTEGRITY",
    "DISTRICT_CAMPAIGN_SUPPORT",
    "SUSCEPTIBILITY_TO_SELECTION",
    "FUTURE_SCENARIO_COMPATIBILITY",
    "REPRODUCIBILITY",
)

CANDIDATES = (
    {
        "candidate_id": "E1-C1",
        "architecture": "EXISTING_B3_STRICT_CAMPAIGN_WEIGHTED_EXPOSURE",
        "overall_status": "REJECT_PRIMARY_RETAIN_STRICT_SENSITIVITY",
        "reason": "Identification is strict, but validity depends on complete expected SIEMBRA observation and zero ambiguous weight, producing sparse and selectively supported keys.",
        "domains": {
            "BIOLOGICAL_ALIGNMENT": ("PASS", "Uses the frozen crop-specific windows."),
            "CAMPAIGN_ATTRIBUTION_IDENTIFICATION": ("PASS", "Only strictly unambiguous campaign weight contributes."),
            "MEASUREMENT_INTERPRETABILITY": ("PASS", "Valid rows represent a full strict unambiguous weighting domain."),
            "SIEMBRA_WEIGHT_INTEGRITY": ("PASS", "No ambiguous positive weight or missing required SIEMBRA is accepted."),
            "CLIMATE_WINDOW_COMPLETENESS": ("PASS", "Every positive contributing cohort must be complete."),
            "TEMPORAL_BOUNDARY_INTEGRITY": ("PASS", "The excluded 2015/2016 layer is explicitly left truncated."),
            "DISTRICT_CAMPAIGN_SUPPORT": ("FAIL", "Only 38 of 707 D0 structural keys are strict-valid."),
            "SUSCEPTIBILITY_TO_SELECTION": ("FAIL", "Validity selects keys with complete monthly records and no positive ambiguous mass."),
            "FUTURE_SCENARIO_COMPATIBILITY": ("PASS_WITH_LIMITATION", "Construction is reproducible, but strict support is too selective for a primary layer."),
            "REPRODUCIBILITY": ("PASS", "The frozen B3 artifact is byte-deterministic."),
        },
    },
    {
        "candidate_id": "E1-C2",
        "architecture": "UNAMBIGUOUS_ASSIGNED_COHORT_CONDITIONAL_SIEMBRA_WEIGHTED_EXPOSURE",
        "overall_status": "SELECTED_PRIMARY_WITH_LIMITATIONS",
        "reason": "It produces an identified point exposure from already assigned cohorts while preserving unresolved and missing weight diagnostics and making no full-campaign exposure claim.",
        "domains": {
            "BIOLOGICAL_ALIGNMENT": ("PASS", "Uses the frozen Rice and MAD windows without modification."),
            "CAMPAIGN_ATTRIBUTION_IDENTIFICATION": ("PASS", "Only cohorts already unambiguously assigned by frozen harvest bounds enter the point exposure."),
            "MEASUREMENT_INTERPRETABILITY": ("PASS_WITH_LIMITATION", "The estimand is conditional on identified observed SIEMBRA, not the entire campaign."),
            "SIEMBRA_WEIGHT_INTEGRITY": ("PASS_WITH_LIMITATION", "The conditional denominator is explicit; ambiguous mass and absent expected rows remain visible."),
            "CLIMATE_WINDOW_COMPLETENESS": ("PASS", "All positive contributing assigned weight must have all nine climate metrics."),
            "TEMPORAL_BOUNDARY_INTEGRITY": ("PASS", "Only the seven D0 campaigns are constructed; 2015/2016 is excluded."),
            "DISTRICT_CAMPAIGN_SUPPORT": ("PASS_WITH_LIMITATION", "608 of 707 structural keys have positive complete assigned weight, with limitations disclosed by key."),
            "SUSCEPTIBILITY_TO_SELECTION": ("PASS_WITH_LIMITATION", "Identification fractions vary and must be retained in later design and reporting."),
            "FUTURE_SCENARIO_COMPATIBILITY": ("PASS_WITH_LIMITATION", "Historical weights can be held fixed; future-calendar assumptions require a later scenario gate."),
            "REPRODUCIBILITY": ("PASS", "The rule is deterministic from frozen B1 and structural D0 keys."),
        },
    },
    {
        "candidate_id": "E1-C3",
        "architecture": "AMBIGUITY_PRESERVING_PARTIAL_IDENTIFICATION_WITHOUT_ASSIGNMENT",
        "overall_status": "REJECT_AS_POINT_PRIMARY_NOT_IDENTIFIED",
        "reason": "Frozen evidence supports preserving ambiguous mass but not allocating it to one campaign or converting it into one point exposure.",
        "domains": {
            "BIOLOGICAL_ALIGNMENT": ("PASS", "Frozen windows are retained."),
            "CAMPAIGN_ATTRIBUTION_IDENTIFICATION": ("NOT_IDENTIFIED", "Ambiguous weight has no frozen single-campaign assignment."),
            "MEASUREMENT_INTERPRETABILITY": ("NOT_IDENTIFIED", "No unique campaign-level point exposure follows."),
            "SIEMBRA_WEIGHT_INTEGRITY": ("PASS_WITH_LIMITATION", "Ambiguous mass can be retained only as unresolved QA."),
            "CLIMATE_WINDOW_COMPLETENESS": ("PASS", "Cohort climate values are available when windows are complete."),
            "TEMPORAL_BOUNDARY_INTEGRITY": ("PASS", "Campaign boundaries remain unchanged."),
            "DISTRICT_CAMPAIGN_SUPPORT": ("NOT_IDENTIFIED", "Point-exposure support is undefined without an attribution rule."),
            "SUSCEPTIBILITY_TO_SELECTION": ("PASS_WITH_LIMITATION", "No assignment is induced, but no point estimand exists."),
            "FUTURE_SCENARIO_COMPATIBILITY": ("NOT_IDENTIFIED", "A scenario point exposure would require a new ambiguity rule."),
            "REPRODUCIBILITY": ("PASS", "The blocked determination is reproducible."),
        },
    },
    {
        "candidate_id": "E1-C4",
        "architecture": "NO_ADDITIONAL_FROZEN_ARCHITECTURE",
        "overall_status": "NOT_AVAILABLE",
        "reason": "No other point architecture is authorized by frozen evidence without inventing assignment, splitting, imputation, or interpolation.",
        "domains": {domain: ("NOT_IDENTIFIED", "No additional frozen candidate exists.") for domain in DOMAINS},
    },
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_output(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=True, capture_output=True, text=True, encoding="utf-8"
    ).stdout.strip()


def preflight() -> dict[str, Any]:
    actual = {path.relative_to(ROOT).as_posix(): sha256_file(path) for path in FROZEN_HASHES}
    expected = {path.relative_to(ROOT).as_posix(): value for path, value in FROZEN_HASHES.items()}
    identity = {
        "head": git_output("rev-parse", "HEAD"),
        "remote_s1": git_output("rev-parse", "origin/phase/s1-scientific-identity-master-v1"),
        "s1_tag_target": git_output("rev-list", "-n", "1", S1_TAG),
    }
    if actual != expected:
        raise RuntimeError("Frozen input hash mismatch")
    if set(identity.values()) != {S1_FREEZE_SHA}:
        raise RuntimeError(f"S1 identity mismatch: {identity}")
    return {"status": "PASS", "identity": identity, "actual_hashes": actual}


def read_stage_a_grid() -> pd.DataFrame:
    data = pd.read_csv(
        D0_MASTER_PATH,
        usecols=list(D0_STAGE_A_COLUMNS),
        dtype={"CROP_CODE": "string", "CROP_STD": "string", "UBIGEO": "string", "CAMPAIGN": "string"},
    )
    for column in ("CROP_CODE", "CROP_STD", "UBIGEO", "CAMPAIGN"):
        data[column] = data[column].astype("string").str.strip()
    data = data[data["CROP_CODE"].isin(CROPS)].copy()
    data = data.sort_values(["UBIGEO", "CROP_CODE", "CAMPAIGN"], kind="mergesort").reset_index(drop=True)
    if len(data) != 707 or data.duplicated(["UBIGEO", "CROP_CODE", "CAMPAIGN"]).any():
        raise RuntimeError("D0 structural grid mismatch")
    if tuple(sorted(data["CAMPAIGN"].unique())) != CAMPAIGNS:
        raise RuntimeError("D0 campaign contract mismatch")
    return data


def read_b1() -> pd.DataFrame:
    data = pd.read_parquet(B1_PATH, columns=list(B1_COLUMNS))
    for column in ("UBIGEO", "COD_CULTIVO", "CROP_STD", "WINDOW_ID", "FAILURE_REASON"):
        data[column] = data[column].astype("string").str.strip()
    return data[data["COD_CULTIVO"].isin(CROPS)].copy()


def yyyymm(year: int, month: int) -> int:
    return year * 100 + month


def cohort_domains(crop_code: str, campaign_start: int) -> tuple[list[int], list[int]]:
    if crop_code == "14010020000":
        unambiguous = [yyyymm(campaign_start, month) for month in range(5, 13)]
        unambiguous += [yyyymm(campaign_start + 1, month) for month in (1, 2)]
        ambiguous = [yyyymm(campaign_start, month) for month in (3, 4)]
        ambiguous += [yyyymm(campaign_start + 1, month) for month in (3, 4)]
        return unambiguous, ambiguous
    if crop_code == "14010070000":
        unambiguous = [yyyymm(campaign_start, month) for month in range(5, 13)]
        unambiguous += [yyyymm(campaign_start + 1, 1)]
        ambiguous = [yyyymm(campaign_start, month) for month in (2, 3, 4)]
        ambiguous += [yyyymm(campaign_start + 1, month) for month in (2, 3, 4)]
        return unambiguous, ambiguous
    raise ValueError(f"Unexpected crop: {crop_code}")


def finite_climate(row: Any) -> bool:
    return bool(
        row.COHORT_EXPOSURE_VALID
        and row.CLIMATE_WINDOW_COMPLETE
        and all(value is not None and math.isfinite(float(value)) for value in (getattr(row, item) for item in CLIMATE_VARIABLES))
    )


def build_exposures(grid: pd.DataFrame, b1: pd.DataFrame) -> pd.DataFrame:
    index = {
        (str(row.UBIGEO), str(row.COD_CULTIVO), int(row.ANCHOR_YYYYMM), str(row.WINDOW_ID)): row
        for row in b1.itertuples(index=False)
    }
    records: list[dict[str, Any]] = []
    for key in grid.itertuples(index=False):
        crop_code = str(key.CROP_CODE)
        campaign_id = str(key.CAMPAIGN)
        campaign_start = int(campaign_id.split("/")[0])
        window_id = str(CROPS[crop_code]["window_id"])
        unambiguous_months, ambiguous_months = cohort_domains(crop_code, campaign_start)
        unambiguous = [
            index.get((str(key.UBIGEO), crop_code, month, window_id)) for month in unambiguous_months
        ]
        ambiguous = [index.get((str(key.UBIGEO), crop_code, month, window_id)) for month in ambiguous_months]
        observed_u = [row for row in unambiguous if row is not None and bool(row.SIEMBRA_OBSERVED)]
        observed_a = [row for row in ambiguous if row is not None and bool(row.SIEMBRA_OBSERVED)]
        positive_u = [row for row in observed_u if float(row.SIEMBRA) > 0]
        positive_a = [row for row in observed_a if float(row.SIEMBRA) > 0]

        assigned = sum(float(row.SIEMBRA) for row in observed_u)
        unresolved = sum(float(row.SIEMBRA) for row in observed_a)
        observed_total = assigned + unresolved
        supported = sum(float(row.SIEMBRA) for row in positive_u if finite_climate(row))
        missing_count = len(unambiguous_months) + len(ambiguous_months) - len(observed_u) - len(observed_a)
        identified_fraction = assigned / observed_total if observed_total > 0 else None
        right_boundary = any(
            float(row.SIEMBRA) > 0 and "RIGHT_TRUNCATED" in str(row.FAILURE_REASON)
            for row in observed_u
        )
        left_boundary = campaign_id == "2015/2016"

        reasons: list[str] = []
        if left_boundary:
            reasons.append("STRUCTURAL_LEFT_BOUNDARY")
        if right_boundary:
            reasons.append("CLIMATE_RIGHT_BOUNDARY")
        if assigned <= 0:
            reasons.append("NO_POSITIVE_UNAMBIGUOUS_ASSIGNED_SIEMBRA")
        if assigned > 0 and not math.isclose(supported, assigned, abs_tol=1e-9):
            reasons.append("POSITIVE_UNAMBIGUOUS_COHORT_CLIMATE_INCOMPLETE")
        valid = not reasons

        climate_values: dict[str, float | None] = {variable: None for variable in CLIMATE_VARIABLES}
        weight_sum: float | None = None
        if valid:
            weight_sum = sum(float(row.SIEMBRA) / assigned for row in positive_u)
            if not math.isclose(weight_sum, 1.0, abs_tol=1e-12):
                raise RuntimeError("Conditional exposure weights do not sum to one")
            climate_values = {
                variable: sum(float(row.SIEMBRA) * float(getattr(row, variable)) for row in positive_u) / assigned
                for variable in CLIMATE_VARIABLES
            }

        records.append(
            {
                "UBIGEO": str(key.UBIGEO),
                "COD_CULTIVO": crop_code,
                "CROP_STD": str(key.CROP_STD),
                "CAMPAIGN_ID": campaign_id,
                "WINDOW_ID": window_id,
                "EXPECTED_COHORT_COUNT": len(unambiguous_months) + len(ambiguous_months),
                "OBSERVED_COHORT_COUNT": len(observed_u) + len(observed_a),
                "UNAMBIGUOUS_COHORT_COUNT": len(observed_u),
                "AMBIGUOUS_COHORT_COUNT": len(observed_a),
                "POSITIVE_UNAMBIGUOUS_COHORT_COUNT": len(positive_u),
                "POSITIVE_AMBIGUOUS_COHORT_COUNT": len(positive_a),
                "MISSING_EXPECTED_COHORT_COUNT": missing_count,
                "OBSERVED_SIEMBRA_TOTAL": observed_total,
                "ASSIGNED_UNAMBIGUOUS_SIEMBRA": assigned,
                "UNRESOLVED_AMBIGUOUS_SIEMBRA": unresolved,
                "MISSING_SIEMBRA_WEIGHT": 0.0 if missing_count == 0 else None,
                "CLIMATE_SUPPORTED_SIEMBRA": supported,
                "IDENTIFIED_OBSERVED_WEIGHT_FRACTION": identified_fraction,
                "EXPOSURE_WEIGHT_DENOMINATOR": assigned,
                "EXPOSURE_WEIGHT_SUM": weight_sum,
                **climate_values,
                "LEFT_BOUNDARY_FLAG": left_boundary,
                "RIGHT_BOUNDARY_FLAG": right_boundary,
                "UNRESOLVED_AMBIGUOUS_WEIGHT_PRESERVED": unresolved > 0,
                "SIEMBRA_MISSINGNESS_STATUS": (
                    "ZERO_NO_EXPECTED_COHORT_ROWS_MISSING"
                    if missing_count == 0
                    else "NOT_IDENTIFIED_ABSENT_EXPECTED_COHORT_ROWS"
                ),
                "NORMALIZATION_SCOPE": "POSITIVE_OBSERVED_UNAMBIGUOUS_ASSIGNED_SIEMBRA_ONLY",
                "EXPOSURE_VALID": valid,
                "FAILURE_REASON": "|".join(reasons) if reasons else "NONE",
            }
        )
    data = pd.DataFrame.from_records(records, columns=OUTPUT_COLUMNS)
    return data.sort_values(["UBIGEO", "COD_CULTIVO", "CAMPAIGN_ID"], kind="mergesort").reset_index(drop=True)


def b3_support_on_grid(grid: pd.DataFrame) -> dict[str, Any]:
    b3 = pd.read_parquet(
        B3_PATH,
        columns=["UBIGEO", "COD_CULTIVO", "CAMPAIGN_ID", "CAMPAIGN_WEIGHTED_EXPOSURE_VALID"],
    )
    merged = grid.merge(
        b3,
        how="left",
        left_on=["UBIGEO", "CROP_CODE", "CAMPAIGN"],
        right_on=["UBIGEO", "COD_CULTIVO", "CAMPAIGN_ID"],
        validate="one_to_one",
    )
    matched = merged["CAMPAIGN_WEIGHTED_EXPOSURE_VALID"].notna()
    merged["CAMPAIGN_WEIGHTED_EXPOSURE_VALID"] = (
        merged["CAMPAIGN_WEIGHTED_EXPOSURE_VALID"].fillna(False).astype(bool)
    )
    return {
        "structural_grid_rows": int(len(merged)),
        "b3_matched_structural_rows": int(matched.sum()),
        "b3_absent_structural_rows": int((~matched).sum()),
        "strict_valid_rows": int(merged["CAMPAIGN_WEIGHTED_EXPOSURE_VALID"].sum()),
        "strict_valid_by_crop": {
            str(key): int(value)
            for key, value in merged.groupby("CROP_CODE")["CAMPAIGN_WEIGHTED_EXPOSURE_VALID"].sum().items()
        },
    }


def rounded(value: Any) -> float | None:
    if value is None or pd.isna(value):
        return None
    return round(float(value), 12)


def summarize_stage_a(exposures: pd.DataFrame) -> dict[str, Any]:
    positive = exposures[exposures["OBSERVED_SIEMBRA_TOTAL"] > 0]
    valid = exposures[exposures["EXPOSURE_VALID"]]
    quantile_points = [0.0, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0]
    by_crop_campaign: list[dict[str, Any]] = []
    for (crop, campaign), group in exposures.groupby(["COD_CULTIVO", "CAMPAIGN_ID"], sort=True):
        fractions = group.loc[group["OBSERVED_SIEMBRA_TOTAL"] > 0, "IDENTIFIED_OBSERVED_WEIGHT_FRACTION"]
        by_crop_campaign.append(
            {
                "crop_code": str(crop),
                "campaign_id": str(campaign),
                "structural_rows": int(len(group)),
                "exposure_valid_rows": int(group["EXPOSURE_VALID"].sum()),
                "positive_ambiguous_weight_rows": int((group["UNRESOLVED_AMBIGUOUS_SIEMBRA"] > 0).sum()),
                "missing_expected_cohort_rows": int((group["MISSING_EXPECTED_COHORT_COUNT"] > 0).sum()),
                "median_identified_observed_weight_fraction": rounded(fractions.median()) if not fractions.empty else None,
            }
        )
    district_support = (
        exposures.groupby(["COD_CULTIVO", "UBIGEO"], sort=True)["EXPOSURE_VALID"]
        .sum()
        .value_counts()
        .sort_index()
    )
    return {
        "structural_grid_rows": int(len(exposures)),
        "duplicate_keys": int(exposures.duplicated(["UBIGEO", "COD_CULTIVO", "CAMPAIGN_ID"]).sum()),
        "exposure_valid_rows": int(exposures["EXPOSURE_VALID"].sum()),
        "exposure_valid_by_crop": {
            str(key): int(value)
            for key, value in exposures.groupby("COD_CULTIVO")["EXPOSURE_VALID"].sum().items()
        },
        "structural_rows_by_crop": {
            str(key): int(value) for key, value in exposures.groupby("COD_CULTIVO").size().items()
        },
        "positive_ambiguous_weight_rows": int((exposures["UNRESOLVED_AMBIGUOUS_SIEMBRA"] > 0).sum()),
        "missing_expected_cohort_rows": int((exposures["MISSING_EXPECTED_COHORT_COUNT"] > 0).sum()),
        "zero_observed_weight_rows": int((exposures["OBSERVED_SIEMBRA_TOTAL"] <= 0).sum()),
        "identified_fraction_quantiles_positive_observed_weight": {
            str(point): rounded(value)
            for point, value in positive["IDENTIFIED_OBSERVED_WEIGHT_FRACTION"].quantile(quantile_points).items()
        },
        "identified_fraction_quantiles_valid_exposure": {
            str(point): rounded(value)
            for point, value in valid["IDENTIFIED_OBSERVED_WEIGHT_FRACTION"].quantile(quantile_points).items()
        },
        "valid_campaign_count_by_district_crop_distribution": {
            str(int(key)): int(value) for key, value in district_support.items()
        },
        "by_crop_campaign": by_crop_campaign,
    }


def candidate_matrix_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for candidate in CANDIDATES:
        for domain in DOMAINS:
            status, reason = candidate["domains"][domain]
            rows.append(
                {
                    "CANDIDATE_ID": str(candidate["candidate_id"]),
                    "ARCHITECTURE": str(candidate["architecture"]),
                    "DOMAIN": domain,
                    "STATUS": status,
                    "REASON": reason,
                }
            )
    return rows


def measurement_error_assessment() -> list[dict[str, str]]:
    return [
        {
            "mechanism": "MONTHLY_SIEMBRA_COHORT_WEIGHTS",
            "classification": "AGGREGATION_AND_RECORDING_ERROR_DIRECTION_NOT_QUANTIFIED",
            "treatment": "Preserve observed, assigned, ambiguous, and missingness diagnostics by key.",
        },
        {
            "mechanism": "RICE_TRANSPLANT_ESTABLISHMENT_PROXY",
            "classification": "ANCHOR_TIMING_PROXY_ERROR_DIRECTION_NOT_QUANTIFIED",
            "treatment": "Retain the frozen operational semantics and do not reinterpret SIEMBRA as a precise biological date.",
        },
        {
            "mechanism": "BROAD_ATTRIBUTION_LAG_INTERVAL",
            "classification": "CAMPAIGN_CLASSIFICATION_UNCERTAINTY",
            "treatment": "Only frozen unambiguous assignments enter the point exposure.",
        },
        {
            "mechanism": "CROSS_CAMPAIGN_AMBIGUITY",
            "classification": "UNRESOLVED_ATTRIBUTION_MASS",
            "treatment": "Exclude it from the point numerator and denominator while preserving its mass and counts as QA.",
        },
        {
            "mechanism": "DISTRICT_LEVEL_CLIMATE_AGGREGATION",
            "classification": "WITHIN_DISTRICT_SPATIAL_SMOOTHING_DIRECTION_NOT_QUANTIFIED",
            "treatment": "Retain the frozen whole-district climate geography.",
        },
        {
            "mechanism": "MONTHLY_PHENOLOGICAL_EXPOSURE",
            "classification": "WITHIN_MONTH_TIMING_COARSENING_DIRECTION_NOT_QUANTIFIED",
            "treatment": "Retain the frozen monthly windows; no daily or threshold transformation is introduced.",
        },
    ]


def build_stage_a_record(preflight_result: dict[str, Any], stage_a: dict[str, Any], b3: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "gate": "PRIMARY_TRANSIENT_ECONOMETRIC_EXPOSURE_ADJUDICATION_V1",
        "gate_id": "E1",
        "status": "PRIMARY_TRANSIENT_EXPOSURE_SELECTED",
        "freeze_authorized": False,
        "governing_state": {
            "s1_freeze_sha": S1_FREEZE_SHA,
            "s1_status": "PASS_FROZEN",
            "d0_freeze_sha": D0_FREEZE_SHA,
            "identification_ceiling": "EMPIRICAL_ASSOCIATION_CLIMATE_RESPONSE_ONLY",
        },
        "preflight": preflight_result,
        "stage_a_lock": {
            "record_name": "E1_STAGE_A_DECISION_RECORD",
            "hash_scope": CONFIG_REL.as_posix(),
            "sequence": "WRITE_AND_HASH_THIS_RECORD_BEFORE_ANY_D0_VALIDITY_READ",
            "stage_b_may_modify_record": False,
        },
        "outcome_blindness": {
            "outcome_values_read_during_stage_a": False,
            "outcome_validity_read_before_decision": False,
            "d0_stage_a_columns": list(D0_STAGE_A_COLUMNS),
            "d0_stage_a_use": "STRUCTURAL_GRID_ONLY",
            "selection_uses_outcome_support": False,
            "selection_uses_model_fit": False,
        },
        "scope": {
            "crop_codes": list(CROPS),
            "campaigns": list(CAMPAIGNS),
            "time_basis": "AGRICULTURAL_CAMPAIGN_AUG_JUL",
            "excluded_campaign": "2015/2016_STRUCTURAL_LEFT_BOUNDARY_NOT_D0_ESTIMATION_CAMPAIGN",
        },
        "phenology_contract": {
            crop_code: {
                "window_id": details["window_id"],
                "anchor_semantics": details["anchor_semantics"],
                "operational_window": details["operational_window"],
            }
            for crop_code, details in CROPS.items()
        },
        "candidate_inventory": [
            {
                "candidate_id": candidate["candidate_id"],
                "architecture": candidate["architecture"],
                "overall_status": candidate["overall_status"],
                "reason": candidate["reason"],
            }
            for candidate in CANDIDATES
        ],
        "candidate_count": len(CANDIDATES),
        "adjudication_domains": list(DOMAINS),
        "selected_architecture": {
            "candidate_id": "E1-C2",
            "name": "UNAMBIGUOUS_ASSIGNED_COHORT_CONDITIONAL_SIEMBRA_WEIGHTED_EXPOSURE",
            "interpretation": "SIEMBRA_WEIGHTED_MEAN_CLIMATE_AMONG_POSITIVE_OBSERVED_COHORTS_ALREADY_UNAMBIGUOUSLY_ASSIGNED_TO_THE_CAMPAIGN",
            "full_campaign_exposure_claim": False,
            "selection_basis": "INDISPENSABLE_DOMAIN_ADJUDICATION_NOT_NUMERICAL_SCORE_OR_OUTCOME_SUPPORT",
        },
        "b3_role": "STRICT_SENSITIVITY",
        "b3_stage_a_support": b3,
        "ambiguity_rule": "EXCLUDE_FROM_POINT_EXPOSURE_PRESERVE_WEIGHT_AND_COUNTS_NO_ASSIGNMENT",
        "siembra_weight_rule": "NORMALIZE_ONLY_OVER_POSITIVE_OBSERVED_UNAMBIGUOUS_ASSIGNED_SIEMBRA_AS_EXPLICIT_CONDITIONAL_ESTIMAND_NO_FULL_CAMPAIGN_CLAIM",
        "missing_siembra_rule": "ABSENT_EXPECTED_COHORT_WEIGHT_IS_NOT_IDENTIFIED_NOT_ZERO_NOT_IMPUTED",
        "climate_family_role_selection": "DEFERRED_TO_ECONOMETRIC_DESIGN_MASTER",
        "climate_variables_preserved": list(CLIMATE_VARIABLES),
        "stage_a_metrics": stage_a,
        "measurement_error_assessment": measurement_error_assessment(),
        "future_scenario_compatibility": {
            "status": "PASS_WITH_LIMITATION",
            "historical_weights": "FIXED_OBSERVED_CAMPAIGN_SPECIFIC_WEIGHTS",
            "common_scenario_propagation": "COMPATIBLE",
            "future_calendar_assumption": "REQUIRES_FUTURE_SCENARIO_GATE",
            "reference_configuration_privilege": "NONE",
        },
        "firewalls": {
            "random_assignment": "PROHIBITED",
            "probability_allocation": "PROHIBITED",
            "equal_or_fractional_splitting": "PROHIBITED",
            "nearest_or_midpoint_assignment": "PROHIBITED",
            "uniform_weighting": "PROHIBITED",
            "outcome_based_assignment": "PROHIBITED",
            "sample_size_maximization": "PROHIBITED",
            "silent_renormalization": "PROHIBITED",
            "silent_interpolation": "PROHIBITED",
            "siembra_imputation": "PROHIBITED",
            "econometric_estimation": "PROHIBITED_NOT_EXECUTED",
            "a1_a2_outcomes_read": False,
        },
        "parquet_writer": PARQUET_WRITER,
        "output_columns": list(OUTPUT_COLUMNS),
        "post_decision_overlay_role": "POST_DECISION_DIAGNOSTIC_NOT_SELECTION_EVIDENCE",
        "decision_changed_after_d0_overlay": False,
        "next_action": "RETURN_TO_SCIENTIFIC_DIRECTOR_FOR_E1_FREEZE_DECISION_OR_REDESIGN",
    }


def arrow_table(data: pd.DataFrame) -> pa.Table:
    arrays = [pa.array(data[field.name].tolist(), type=field.type) for field in ARROW_SCHEMA]
    return pa.Table.from_arrays(arrays, schema=ARROW_SCHEMA)


def write_parquet(path: Path, data: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(arrow_table(data), path, **PARQUET_WRITER)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    path.write_bytes(text.encode("utf-8"))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, lineterminator="\n", quoting=csv.QUOTE_MINIMAL)
    writer.writeheader()
    writer.writerows(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(buffer.getvalue().encode("utf-8"))


def run_stage_a(output_root: Path) -> str:
    preflight_result = preflight()
    grid = read_stage_a_grid()
    exposures = build_exposures(grid, read_b1())
    stage_a = summarize_stage_a(exposures)
    b3 = b3_support_on_grid(grid)
    if stage_a["exposure_valid_rows"] != 608 or b3["strict_valid_rows"] != 38:
        raise RuntimeError("Outcome-blind support invariants changed")

    write_parquet(output_root / EXPOSURE_REL, exposures)
    matrix_rows = candidate_matrix_rows()
    write_csv(output_root / CANDIDATE_MATRIX_REL, list(matrix_rows[0]), matrix_rows)
    write_json(output_root / CONFIG_REL, build_stage_a_record(preflight_result, stage_a, b3))
    return sha256_file(output_root / CONFIG_REL)


def read_stage_b_d0_support() -> pd.DataFrame:
    data = pd.read_csv(
        D0_MASTER_PATH,
        usecols=list(D0_STAGE_B_COLUMNS),
        dtype={
            "CROP_CODE": "string",
            "CROP_STD": "string",
            "UBIGEO": "string",
            "CAMPAIGN": "string",
            "OUTCOME_VALID_FLAG": "string",
            "EXCLUSION_REASON": "string",
        },
    )
    for column in ("CROP_CODE", "CROP_STD", "UBIGEO", "CAMPAIGN", "OUTCOME_VALID_FLAG", "EXCLUSION_REASON"):
        data[column] = data[column].astype("string").str.strip()
    return data[data["CROP_CODE"].isin(CROPS)].copy()


def build_support_overlay(output_root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    d0 = read_stage_b_d0_support()
    exposure_columns = [
        "UBIGEO",
        "COD_CULTIVO",
        "CROP_STD",
        "CAMPAIGN_ID",
        "EXPOSURE_VALID",
        "FAILURE_REASON",
        "IDENTIFIED_OBSERVED_WEIGHT_FRACTION",
    ]
    exposure = pd.read_parquet(output_root / EXPOSURE_REL, columns=exposure_columns)
    merged = d0.merge(
        exposure,
        how="left",
        left_on=["UBIGEO", "CROP_CODE", "CAMPAIGN"],
        right_on=["UBIGEO", "COD_CULTIVO", "CAMPAIGN_ID"],
        suffixes=("_D0", "_EXPOSURE"),
        validate="one_to_one",
    )
    if len(merged) != 707 or merged["EXPOSURE_VALID"].isna().any():
        raise RuntimeError("Stage-B overlay grid mismatch")
    merged["OUTCOME_VALID"] = merged["OUTCOME_VALID_FLAG"].eq("TRUE")
    merged["INTERSECTION_STATUS"] = [
        ("OUTCOME_VALID" if outcome else "OUTCOME_INVALID")
        + "_"
        + ("EXPOSURE_VALID" if exposure_valid else "EXPOSURE_INVALID")
        for outcome, exposure_valid in zip(merged["OUTCOME_VALID"], merged["EXPOSURE_VALID"])
    ]
    merged = merged.sort_values(["UBIGEO", "CROP_CODE", "CAMPAIGN"], kind="mergesort").reset_index(drop=True)
    rows = [
        {
            "UBIGEO": str(row.UBIGEO),
            "COD_CULTIVO": str(row.CROP_CODE),
            "CROP_STD": str(row.CROP_STD_D0),
            "CAMPAIGN_ID": str(row.CAMPAIGN),
            "OUTCOME_VALID_FLAG": str(row.OUTCOME_VALID_FLAG),
            "EXCLUSION_REASON": str(row.EXCLUSION_REASON),
            "EXPOSURE_VALID": "TRUE" if bool(row.EXPOSURE_VALID) else "FALSE",
            "EXPOSURE_FAILURE_REASON": str(row.FAILURE_REASON),
            "IDENTIFIED_OBSERVED_WEIGHT_FRACTION": (
                "" if pd.isna(row.IDENTIFIED_OBSERVED_WEIGHT_FRACTION) else format(float(row.IDENTIFIED_OBSERVED_WEIGHT_FRACTION), ".17g")
            ),
            "INTERSECTION_STATUS": str(row.INTERSECTION_STATUS),
        }
        for row in merged.itertuples(index=False)
    ]
    by_crop_campaign = []
    for (crop, campaign), group in merged.groupby(["CROP_CODE", "CAMPAIGN"], sort=True):
        by_crop_campaign.append(
            {
                "crop_code": str(crop),
                "campaign_id": str(campaign),
                "d0_grid_rows": int(len(group)),
                "d0_valid_rows": int(group["OUTCOME_VALID"].sum()),
                "exposure_valid_rows": int(group["EXPOSURE_VALID"].sum()),
                "valid_intersection_rows": int((group["OUTCOME_VALID"] & group["EXPOSURE_VALID"]).sum()),
            }
        )
    summary = {
        "role": "POST_DECISION_DIAGNOSTIC_NOT_SELECTION_EVIDENCE",
        "d0_grid_intersection": int(len(merged)),
        "d0_valid_intersection": int(merged["OUTCOME_VALID"].sum()),
        "exposure_valid_rows": int(merged["EXPOSURE_VALID"].sum()),
        "valid_outcome_and_exposure_intersection": int((merged["OUTCOME_VALID"] & merged["EXPOSURE_VALID"]).sum()),
        "valid_outcome_missing_exposure": int((merged["OUTCOME_VALID"] & ~merged["EXPOSURE_VALID"]).sum()),
        "by_crop": {
            str(crop): {
                "d0_grid_rows": int(len(group)),
                "d0_valid_rows": int(group["OUTCOME_VALID"].sum()),
                "exposure_valid_rows": int(group["EXPOSURE_VALID"].sum()),
                "valid_intersection_rows": int((group["OUTCOME_VALID"] & group["EXPOSURE_VALID"]).sum()),
            }
            for crop, group in merged.groupby("CROP_CODE", sort=True)
        },
        "by_crop_campaign": by_crop_campaign,
        "district_rows_available_in_overlay": True,
        "decision_changed_after_overlay": False,
    }
    return rows, summary


def report_text(record: dict[str, Any], stage_a_sha: str, overlay: dict[str, Any], hashes: dict[str, str]) -> str:
    candidates = record["candidate_inventory"]
    candidate_lines = [
        f"| {item['candidate_id']} | {item['architecture']} | {item['overall_status']} | {item['reason']} |"
        for item in candidates
    ]
    domain_lines = [
        f"| {row['CANDIDATE_ID']} | {row['DOMAIN']} | {row['STATUS']} | {row['REASON']} |"
        for row in candidate_matrix_rows()
    ]
    measurement_lines = [
        f"| {item['mechanism']} | {item['classification']} | {item['treatment']} |"
        for item in record["measurement_error_assessment"]
    ]
    crop_lines = [
        f"| {crop} | {values['d0_grid_rows']} | {values['d0_valid_rows']} | {values['exposure_valid_rows']} | {values['valid_intersection_rows']} |"
        for crop, values in overlay["by_crop"].items()
    ]
    lines = [
        "# E1 Primary Transient Econometric Exposure Adjudication v1",
        "",
        "## 1. Verdict",
        "",
        "`E1_PASS_PRIMARY_TRANSIENT_EXPOSURE_READY_FOR_DIRECTOR_FREEZE_DECISION`",
        "",
        "`E1_FREEZE_AUTHORIZED=NO`.",
        "",
        "## 2. Outcome-blind Stage A",
        "",
        "Stage A used B1, B3, frozen phenology, and only the structural D0 grid columns recorded in the decision file. No outcome value or D0 validity field was loaded before the decision record was written and hashed.",
        "",
        f"`STAGE_A_DECISION_SHA256={stage_a_sha}`",
        "",
        "## 3. Candidate inventory",
        "",
        "| ID | Architecture | Overall status | Reason |",
        "|---|---|---|---|",
        *candidate_lines,
        "",
        "## 4. Domain adjudication",
        "",
        "| Candidate | Domain | Status | Reason |",
        "|---|---|---|---|",
        *domain_lines,
        "",
        "## 5. Selected architecture",
        "",
        "`UNAMBIGUOUS_ASSIGNED_COHORT_CONDITIONAL_SIEMBRA_WEIGHTED_EXPOSURE` is selected with limitations. It is a conditional mean over positive observed SIEMBRA already assigned without ambiguity. It is not a full-campaign exposure claim.",
        "",
        "## 6. Ambiguity and SIEMBRA rules",
        "",
        f"`AMBIGUOUS_COHORT_RULE={record['ambiguity_rule']}`",
        "",
        f"`SIEMBRA_WEIGHT_RULE={record['siembra_weight_rule']}`",
        "",
        "Unresolved ambiguous weight is never assigned, split, interpolated, or silently discarded. It remains visible by key. Missing expected-cohort weight is not assumed to be zero.",
        "",
        "## 7. B3 role",
        "",
        f"`B3_ROLE={record['b3_role']}`. B3 remains the strict-identification sensitivity because its strict-valid keys are sparse and selected by complete expected SIEMBRA observation plus zero ambiguous positive weight.",
        "",
        "## 8. Outcome-blind support",
        "",
        f"The structural grid contains {record['stage_a_metrics']['structural_grid_rows']} keys. The selected architecture has {record['stage_a_metrics']['exposure_valid_rows']} valid exposure rows; B3 has {record['b3_stage_a_support']['strict_valid_rows']} strict-valid rows. These are exposure-feasibility facts, not outcome support or a numerical selection objective.",
        "",
        "## 9. Climate-family firewall",
        "",
        f"`CLIMATE_FAMILY_ROLE_SELECTION={record['climate_family_role_selection']}`. All nine frozen metrics are preserved without fit-based designation.",
        "",
        "## 10. Measurement-error assessment",
        "",
        "| Mechanism | Classification | Treatment |",
        "|---|---|---|",
        *measurement_lines,
        "",
        "## 11. Scenario compatibility",
        "",
        "The architecture is compatible with common scenario propagation when historical campaign-specific SIEMBRA weights are held fixed. Any future calendar assumption requires a later scenario gate. Neither historical reference configuration is privileged.",
        "",
        "## 12. Stage-B support overlay",
        "",
        "`POST_DECISION_DIAGNOSTIC_NOT_SELECTION_EVIDENCE`",
        "",
        f"D0 grid rows: {overlay['d0_grid_intersection']}. D0-valid rows: {overlay['d0_valid_intersection']}. Exposure-valid rows: {overlay['exposure_valid_rows']}. Joint valid intersection: {overlay['valid_outcome_and_exposure_intersection']}. D0-valid rows lacking valid exposure: {overlay['valid_outcome_missing_exposure']}.",
        "",
        "| Crop code | D0 grid | D0 valid | Exposure valid | Joint valid |",
        "|---|---:|---:|---:|---:|",
        *crop_lines,
        "",
        "District and campaign detail is preserved row by row in `E1_SUPPORT_OVERLAY.csv`; campaign summaries are retained in the deterministic Stage-B summary.",
        "",
        "## 13. Nonrevision audit",
        "",
        "`DECISION_CHANGED_AFTER_D0_OVERLAY=FALSE`. Stage B did not modify the decision record, candidate matrix, exposure artifact, ambiguity rule, weighting rule, exclusion rule, or B3 role.",
        "",
        "## 14. Candidate artifact",
        "",
        f"`transient_econometric_exposures_v1.parquet` contains {record['stage_a_metrics']['structural_grid_rows']} rows and {record['stage_a_metrics']['exposure_valid_rows']} exposure-valid rows. It contains identifiers, nine climate metrics, and explicit QA fields only.",
        "",
        "## 15. Deterministic hashes",
        "",
        *[f"- `{path}={value}`" for path, value in sorted(hashes.items())],
        "",
        "## 16. Scientific limitations",
        "",
        "The primary point exposure is conditional on identifiable observed cohort weight. Cross-campaign mass remains unresolved, expected monthly SIEMBRA records are incomplete for many keys, and monthly district-level aggregation introduces timing and spatial measurement error whose direction is not quantified.",
        "",
        "## 17. Next action",
        "",
        "`RETURN_TO_SCIENTIFIC_DIRECTOR_FOR_E1_FREEZE_DECISION_OR_REDESIGN`",
        "",
    ]
    return "\n".join(lines)


def run_stage_b(output_root: Path, expected_stage_a_sha: str) -> dict[str, Any]:
    config_path = output_root / CONFIG_REL
    matrix_path = output_root / CANDIDATE_MATRIX_REL
    exposure_path = output_root / EXPOSURE_REL
    if sha256_file(config_path) != expected_stage_a_sha:
        raise RuntimeError("Stage-A decision hash mismatch before Stage B")
    locked_hashes = {path: sha256_file(path) for path in (config_path, matrix_path, exposure_path)}
    record = json.loads(config_path.read_text(encoding="utf-8"))

    rows, overlay = build_support_overlay(output_root)
    overlay_fields = list(rows[0])
    write_csv(output_root / SUPPORT_OVERLAY_REL, overlay_fields, rows)

    if locked_hashes != {path: sha256_file(path) for path in locked_hashes}:
        raise RuntimeError("Stage-B nonrevision firewall failed")
    artifact_hashes = {
        CONFIG_REL.as_posix(): sha256_file(config_path),
        CANDIDATE_MATRIX_REL.as_posix(): sha256_file(matrix_path),
        EXPOSURE_REL.as_posix(): sha256_file(exposure_path),
        SUPPORT_OVERLAY_REL.as_posix(): sha256_file(output_root / SUPPORT_OVERLAY_REL),
    }
    report = report_text(record, expected_stage_a_sha, overlay, artifact_hashes)
    report_path = output_root / REPORT_REL
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_bytes(report.encode("utf-8"))
    overlay["stage_a_decision_sha256"] = expected_stage_a_sha
    overlay["artifact_hashes_before_report"] = artifact_hashes
    return overlay


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the outcome-blind E1 exposure decision in two locked stages.")
    parser.add_argument("stage", choices=("stage-a", "stage-b"))
    parser.add_argument("--stage-a-sha")
    parser.add_argument("--output-root", type=Path, default=ROOT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_root = args.output_root.resolve()
    if args.stage == "stage-a":
        digest = run_stage_a(output_root)
        print(f"STAGE_A_DECISION_SHA256={digest}")
        return 0
    if not args.stage_a_sha:
        raise SystemExit("--stage-a-sha is required for stage-b")
    overlay = run_stage_b(output_root, args.stage_a_sha)
    print(json.dumps(overlay, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
