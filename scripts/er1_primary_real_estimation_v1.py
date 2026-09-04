from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from scipy import stats


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import econometric_design_master_v1 as ed1  # noqa: E402


ED1_FREEZE_SHA = "ed1c7cb79e7842356abd41f7a7af60d2fac1b5a6"
ED1_BRANCH = "phase/ed1-econometric-design-master-v1"
ED1_TAG = "ed1-econometric-design-master-v1-freeze"
D0_FREEZE_SHA = "1598a09c9a871d81834164d7ee4383e25988d8a5"
JOINT_C0_FREEZE_SHA = "fca5d6e519cdff764d1ca53791ae1829ef29aa00"
C0A_FREEZE_SHA = "5e2b32edba2e4b3eee471c669f427ef9a70fe4b6"
DATASET_MASTER_FREEZE_SHA = "38e957e3c01fbffef242c386099b0a219d83ca70"
DATASET_MASTER_TAG = "v0.2.0-data-climate-freeze"

TRANSIENT_OUTCOME_REL = Path("data/processed/outcomes/transient_campaign_outcomes_master.csv")
PERENNIAL_OUTCOME_REL = Path("data/processed/panel_master.csv")
TRANSIENT_OUTCOME_SHA = "9cae62fb1417fa41274f6d504515571abd428b71fecaa0d138d3b786aa538760"
PERENNIAL_OUTCOME_SHA = "ab9b4ce53c008a1bc3ceb7d3e4c5d617d2544ad48632b747079c33e8b95d1214"

COEFFICIENTS_REL = Path("outputs/econometrics/ER1_PRIMARY_COEFFICIENTS.csv")
JOINT_TESTS_REL = Path("outputs/econometrics/ER1_PRIMARY_JOINT_TESTS.csv")
SAMPLE_AUDIT_REL = Path("outputs/econometrics/ER1_PRIMARY_SAMPLE_AUDIT.csv")
REPORT_REL = Path("outputs/econometrics/ER1_PRIMARY_ESTIMATION_REPORT.md")
LOCK_REL = Path("outputs/econometrics/ER1_PRIMARY_RESULTS_LOCK.json")
SCRIPT_REL = Path("scripts/er1_primary_real_estimation_v1.py")
TEST_REL = Path("tests/test_er1_primary_real_estimation_v1.py")

OUTPUT_RELS = (COEFFICIENTS_REL, JOINT_TESTS_REL, SAMPLE_AUDIT_REL, REPORT_REL, LOCK_REL)
CANDIDATE_RELS = (*OUTPUT_RELS, SCRIPT_REL, TEST_REL)

ED1_FILE_HASHES = {
    "config/econometrics/econometric_design_master_v1.json": "feaddf35700a84592ba024ae1fb9e4c9419e00672828fdb7cb29f2775d933c6d",
    "outputs/econometrics/ED1_ECONOMETRIC_DESIGN_REPORT.md": "49d2d5bdd2d0871c8f868902be197fda6228423a4f1577b83f47eea34ecc8b34",
    "outputs/econometrics/ED1_MODEL_CONTRACTS.csv": "7dcd316c7b47b3a2e15939ed25dea8e034f1ca7c5076013c7640ef11da74cbcf",
    "outputs/econometrics/ED1_X_GEOMETRY.csv": "08d569170ebc5bc3a5a4a35cdc702807be46a34df371e9363af510d7d0cca962",
    "outputs/econometrics/ED1_INFERENCE_MATRIX.csv": "5cabcf5ab6d7cba1b6bf765e7727f9de1f090cc9b8a503364582a539701c7fab",
    "outputs/econometrics/ED1_ROBUSTNESS_HIERARCHY.csv": "87959f394c3b6d486523e216dc61a0a7fca29a99d2e688ac5e80317162a4c3e1",
    "scripts/econometric_design_master_v1.py": "69fb1b1f0a1d7c4ec7791fdfa2d3cfb20d62b4ed0f6348b155155523b6b48195",
    "tests/test_econometric_design_master_v1.py": "02b68ede20688775b03d2c0d05914485a513f0f17265cc49bbcb160c7db444d8",
}

CONTRACT_HASHES = {
    "config/outcome/transient_campaign_outcome_v1.json": "b41b96bf307e066b819365e59a93c59050b3151293ac36a72303401bd00766ba",
    "config/joint_c0/outcome_decision_integration_v1.json": "53158bdb19d29de772f5061c0b110079500ff7a6d0b86e42b403879ed65b9899",
    TRANSIENT_OUTCOME_REL.as_posix(): TRANSIENT_OUTCOME_SHA,
    PERENNIAL_OUTCOME_REL.as_posix(): PERENNIAL_OUTCOME_SHA,
}

FROZEN_HASHES = {
    **{path.relative_to(ROOT).as_posix(): digest for path, digest in ed1.FROZEN_HASHES.items()},
    **ED1_FILE_HASHES,
    **CONTRACT_HASHES,
}

EXPECTED_SAMPLE = {
    "14010020000": {"n": 281, "districts": 44, "effective": 43, "periods": 7},
    "14010070000": {"n": 318, "districts": 54, "effective": 52, "periods": 7},
    "13010210000": {"n": 255, "districts": 36, "effective": 35, "periods": 8},
    "13010170102": {"n": 311, "districts": 44, "effective": 43, "periods": 8},
    "15010040000": {"n": 390, "districts": 54, "effective": 50, "periods": 8},
}

PRIMARY_INFERENCE = "DISTRICT_CLUSTERED_CR2_BIAS_REDUCED_LINEARIZATION_WITH_SATTERTHWAITE_DF"
CLAIM_CEILING = "EMPIRICAL_ASSOCIATION_CLIMATE_RESPONSE_ONLY"
REFERENCE_TOLERANCE = 1e-8
FINAL_VERDICT = "ER1R_PASS_REPORTING_CORRECTED_RESULTS_READY_FOR_FREEZE_DECISION"
PREVIOUS_RESULTS_LOCK_SHA256 = "d2ceab1655ae3cb220e8adfe3be7fce56dc77c35121ad6a06350532c3cb7c118"
ACCEPTED_NUMERICAL_TABLE_SHA256 = {
    COEFFICIENTS_REL.as_posix(): "37fa03a2e860f86277510a5ff3b66ca475fc02d277ea1dd6e18156f719c23480",
    JOINT_TESTS_REL.as_posix(): "8d00e0ef866488c8f7ce7a418d58ae165e87f05053db9861fed1b0f181e412e3",
    SAMPLE_AUDIT_REL.as_posix(): "d5a2b42b7f8f68be5a387c9726f76d081c83e1b242fea2edfba829f963040854",
}
NUMERICAL_RESULTS_IDENTITY = hashlib.sha256(
    json.dumps(ACCEPTED_NUMERICAL_TABLE_SHA256, sort_keys=True, separators=(",", ":")).encode("utf-8")
).hexdigest()
REPORTING_SEMANTICS = {
    "COEFFICIENT_CONFIDENCE_INTERVALS": "UNADJUSTED_95_PERCENT_CR2_SATTERTHWAITE",
    "MULTIPLICITY_ADJUSTMENT": "HOLM_STEP_DOWN_WITHIN_CROP_P_VALUES",
    "MULTIPLICITY_ADJUSTED_CONFIDENCE_INTERVALS": "NOT_CONSTRUCTED_NOT_CLAIMED",
    "GLOBAL_FIVE_CROP_FAMILYWISE_ERROR_CONTROL": "NOT_CLAIMED",
    "INFERENCE_PRECISION_STATUS": "HETEROGENEOUS_ACROSS_CROPS_AND_COEFFICIENTS",
}
REPORTING_SUMMARY = (
    "Most coefficient-specific 95% CR2/Satterthwaite confidence intervals include zero. "
    "After the prespecified within-crop Holm adjustment of coefficient p-values, only Banana "
    "lagged Tmin remains below 0.05. Lemon lagged Tmin has an unadjusted p-value below 0.05 "
    "but does not remain below 0.05 after Holm adjustment."
)

COEFFICIENT_FIELDS = (
    "CROP_CODE",
    "CROP",
    "MODEL_ID",
    "CLIMATE_VARIABLE",
    "WINDOW",
    "BETA",
    "CR2_STANDARD_ERROR",
    "SATTERTHWAITE_DF",
    "EFFECTIVE_DF_FLAG",
    "T_STATISTIC",
    "P_VALUE_TWO_SIDED",
    "CI95_LOWER",
    "CI95_UPPER",
    "HOLM_ADJUSTED_P_VALUE",
    "OUTCOME_SCALE",
    "PRIMARY_CLIMATE_FAMILY",
    "FUNCTIONAL_FORM",
    "DISTRICT_FE",
    "PERIOD_FE",
    "WEIGHTING",
    "INFERENCE",
    "CLAIM_CEILING",
)

JOINT_FIELDS = (
    "CROP_CODE",
    "CROP",
    "MODEL_ID",
    "COEFFICIENTS_TESTED",
    "NUMERATOR_DF",
    "DENOMINATOR_DF",
    "F_STATISTIC",
    "P_VALUE",
    "JOINT_TEST",
    "CLAIM_CEILING",
)

SAMPLE_FIELDS = (
    "CROP_CODE",
    "CROP",
    "MODEL_ID",
    "N",
    "NOMINAL_DISTRICTS",
    "EFFECTIVE_CONTRIBUTING_DISTRICTS",
    "PERIODS",
    "MISSING_Y",
    "MISSING_X",
    "DUPLICATE_KEYS",
    "FINITE_Y",
    "NONFINITE_Y",
    "ZERO_Y",
    "NEGATIVE_Y",
    "Y_MIN",
    "Y_MEDIAN",
    "Y_MAX",
    "OUTCOME_SOURCE",
    "OUTCOME_SOURCE_SHA256",
    "OUTCOME_COLUMN",
    "KEY_COLUMNS",
    "OUTCOME_SCALE",
)


def git_output(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_float(value: float) -> str:
    number = float(value)
    if not np.isfinite(number):
        raise RuntimeError("Nonfinite numerical result cannot be serialized")
    return format(number, ".17g")


def numeric(value: float) -> float:
    number = float(value)
    if not np.isfinite(number):
        raise RuntimeError("Nonfinite numerical result")
    return number


def verify_ed1_contract() -> dict[str, Any]:
    config = json.loads((ROOT / "config/econometrics/econometric_design_master_v1.json").read_text(encoding="utf-8"))
    if config["primary_model_architecture"] != "FIVE_CROP_SPECIFIC_MODELS_NO_POOLED_COEFFICIENTS":
        raise RuntimeError("Frozen primary model architecture mismatch")
    if config["outcome_scale"]["primary"] != "YIELD_LEVEL_TM_PER_HA":
        raise RuntimeError("Frozen outcome scale mismatch")
    if config["climate_family_roles"]["PRIMARY"] != "PHYSICAL_ANOMALY":
        raise RuntimeError("Frozen climate family mismatch")
    if config["fixed_effects"]["district"] != "REQUIRED" or config["fixed_effects"]["period"] != "REQUIRED":
        raise RuntimeError("Frozen fixed-effect contract mismatch")
    if config["regression_weighting"]["primary"] != "UNWEIGHTED_PRIMARY_ESTIMATION":
        raise RuntimeError("Frozen weighting contract mismatch")
    if config["inference"]["primary"] != PRIMARY_INFERENCE:
        raise RuntimeError("Frozen inference contract mismatch")
    if config["inference"]["joint_tests"] != "CR2_APPROXIMATE_HOTELLING_T_SQUARED":
        raise RuntimeError("Frozen joint-test contract mismatch")
    contracts = config["crop_model_contracts"]
    if len(contracts) != 5 or sum(int(row["CLIMATE_COEFFICIENT_COUNT"]) for row in contracts) != 21:
        raise RuntimeError("Frozen crop contract inventory mismatch")
    for row in contracts:
        expected = EXPECTED_SAMPLE[str(row["CROP_CODE"])]
        if (
            int(row["OBSERVATIONS"]) != expected["n"]
            or int(row["DISTRICTS"]) != expected["districts"]
            or int(row["PERIODS"]) != expected["periods"]
            or row["FUNCTIONAL_FORM"] != "LINEAR_ADDITIVE"
            or row["DISTRICT_FE"] != "REQUIRED"
            or row["PERIOD_FE"] != "REQUIRED"
            or row["PRIMARY_WEIGHTING"] != "UNWEIGHTED_PRIMARY_ESTIMATION"
        ):
            raise RuntimeError(f"Frozen crop contract mismatch: {row['CROP_CODE']}")
    return config


def preflight() -> dict[str, Any]:
    identity = {
        "branch": git_output("branch", "--show-current"),
        "head": git_output("rev-parse", "HEAD"),
        "remote_ed1": git_output("rev-parse", f"origin/{ED1_BRANCH}"),
        "ed1_tag_target": git_output("rev-list", "-n", "1", ED1_TAG),
    }
    if identity != {
        "branch": ED1_BRANCH,
        "head": ED1_FREEZE_SHA,
        "remote_ed1": ED1_FREEZE_SHA,
        "ed1_tag_target": ED1_FREEZE_SHA,
    }:
        raise RuntimeError(f"ED1 identity mismatch: {identity}")
    actual_hashes = {relative: sha256_file(ROOT / relative) for relative in sorted(FROZEN_HASHES)}
    mismatches = {
        relative: {"expected": FROZEN_HASHES[relative], "actual": actual_hashes[relative]}
        for relative in FROZEN_HASHES
        if actual_hashes[relative] != FROZEN_HASHES[relative]
    }
    if mismatches:
        raise RuntimeError(f"Frozen input hash mismatch: {mismatches}")
    tracked = git_output("diff", "--name-only").splitlines()
    staged = git_output("diff", "--cached", "--name-only").splitlines()
    untracked = set(git_output("ls-files", "--others", "--exclude-standard").splitlines())
    authorized = {path.as_posix() for path in CANDIDATE_RELS}
    if tracked or staged or not untracked.issubset(authorized):
        raise RuntimeError(
            f"Working-tree scope mismatch: tracked={tracked}, staged={staged}, untracked={sorted(untracked)}"
        )
    config = verify_ed1_contract()
    return {
        "status": "PASS",
        "identity": identity,
        "frozen_hashes": actual_hashes,
        "candidate_scope_status": "PASS",
        "authorized_candidate_universe": sorted(authorized),
        "primary_architecture": config["primary_model_architecture"],
        "outcome_values_read": False,
    }


def read_outcome_sources() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    transient = pd.read_csv(
        ROOT / TRANSIENT_OUTCOME_REL,
        usecols=["CROP_CODE", "UBIGEO", "CAMPAIGN", "TRANSIENT_CAMPAIGN_YIELD_RAW", "OUTCOME_VALID_FLAG"],
        dtype={"CROP_CODE": "string", "UBIGEO": "string", "CAMPAIGN": "string", "OUTCOME_VALID_FLAG": "string"},
    )
    perennial = pd.read_csv(
        ROOT / PERENNIAL_OUTCOME_REL,
        usecols=["UBIGEO", "COD_CULTIVO", "ANO", "YIELD_RAW"],
        dtype={"UBIGEO": "string", "COD_CULTIVO": "string"},
    )
    if len(transient) != 707 or transient.duplicated(["CROP_CODE", "UBIGEO", "CAMPAIGN"]).any():
        raise RuntimeError("Transient authoritative outcome universe mismatch")
    target_codes = set(ed1.CROPS)
    perennial_target = perennial[perennial["COD_CULTIVO"].isin(target_codes - {"14010020000", "14010070000"})].copy()
    if len(perennial) != 1701 or len(perennial_target) != 956:
        raise RuntimeError("Perennial authoritative outcome universe mismatch")
    if perennial_target.duplicated(["COD_CULTIVO", "UBIGEO", "ANO"]).any():
        raise RuntimeError("Duplicate perennial authoritative outcome key")
    metadata = {
        "transient": {
            "path": TRANSIENT_OUTCOME_REL.as_posix(),
            "sha256": TRANSIENT_OUTCOME_SHA,
            "governing_freeze": D0_FREEZE_SHA,
            "key_columns": ["CROP_CODE", "UBIGEO", "CAMPAIGN"],
            "outcome_column": "TRANSIENT_CAMPAIGN_YIELD_RAW",
            "expected_row_universe": 707,
            "formula": "SUM(PRODUCCION_AUG_JUL) / SUM(COSECHA_AUG_JUL)",
            "unit": "TM_PER_HA",
        },
        "perennial": {
            "path": PERENNIAL_OUTCOME_REL.as_posix(),
            "sha256": PERENNIAL_OUTCOME_SHA,
            "dataset_master_freeze": DATASET_MASTER_FREEZE_SHA,
            "dataset_master_tag": DATASET_MASTER_TAG,
            "semantic_adjudication_freeze": C0A_FREEZE_SHA,
            "joint_contract_freeze": JOINT_C0_FREEZE_SHA,
            "key_columns": ["COD_CULTIVO", "UBIGEO", "ANO"],
            "outcome_column": "YIELD_RAW",
            "expected_full_row_universe": 1701,
            "expected_target_crop_row_universe": 956,
            "formula": "SUM(PRODUCCION_CALENDAR_YEAR) / SUM(COSECHA_CALENDAR_YEAR)",
            "unit": "TM_PER_HA",
        },
    }
    return transient, perennial_target, metadata


def transient_design_with_outcome(
    exposures: pd.DataFrame, outcomes: pd.DataFrame, crop_code: str
) -> tuple[pd.DataFrame, list[str]]:
    source = outcomes[outcomes["CROP_CODE"] == crop_code].rename(
        columns={"CAMPAIGN": "CAMPAIGN_ID", "TRANSIENT_CAMPAIGN_YIELD_RAW": "YIELD"}
    )
    source["OUTCOME_VALID_SOURCE"] = source["OUTCOME_VALID_FLAG"].eq("TRUE")
    merged = exposures[exposures["COD_CULTIVO"] == crop_code].merge(
        source[["UBIGEO", "CAMPAIGN_ID", "YIELD", "OUTCOME_VALID_SOURCE"]],
        on=["UBIGEO", "CAMPAIGN_ID"],
        how="left",
        validate="one_to_one",
    )
    frame = merged[merged["EXPOSURE_VALID"] & merged["OUTCOME_VALID_SOURCE"]].copy()
    frame = frame.sort_values(["UBIGEO", "CAMPAIGN_ID"], kind="mergesort").reset_index(drop=True)
    independent = ed1.read_transient_primary()
    independent = independent[independent["COD_CULTIVO"] == crop_code]
    keys = ["UBIGEO", "CAMPAIGN_ID"]
    if set(map(tuple, frame[keys].astype(str).to_numpy())) != set(map(tuple, independent[keys].astype(str).to_numpy())):
        raise RuntimeError(f"Transient frozen intersection key mismatch: {crop_code}")
    return frame, list(ed1.FAMILIES["PHYSICAL_ANOMALY"])


def perennial_design_with_outcome(
    exposures: pd.DataFrame, outcomes: pd.DataFrame, crop_code: str
) -> tuple[pd.DataFrame, list[str]]:
    empty_transient = pd.DataFrame()
    frame, columns = ed1.primary_design_frame(empty_transient, exposures, crop_code)
    source = outcomes[outcomes["COD_CULTIVO"] == crop_code].copy()
    source["REFERENCE_PERIOD_ID"] = source["ANO"].astype("int64").astype(str)
    source = source.rename(columns={"YIELD_RAW": "YIELD"})
    frame["REFERENCE_PERIOD_ID"] = frame["REFERENCE_PERIOD_ID"].astype(str)
    frame = frame.merge(
        source[["UBIGEO", "REFERENCE_PERIOD_ID", "YIELD"]],
        on=["UBIGEO", "REFERENCE_PERIOD_ID"],
        how="left",
        validate="one_to_one",
    )
    return frame, columns


def outcome_support(y: np.ndarray) -> dict[str, Any]:
    finite = np.isfinite(y)
    finite_values = y[finite]
    if not finite.all() or len(finite_values) == 0:
        raise RuntimeError("Primary outcome contains missing or nonfinite values")
    return {
        "finite": int(finite.sum()),
        "nonfinite": int((~finite).sum()),
        "missing": int(np.isnan(y).sum()),
        "zero": int((finite_values == 0).sum()),
        "negative": int((finite_values < 0).sum()),
        "minimum": numeric(np.min(finite_values)),
        "median": numeric(np.median(finite_values)),
        "maximum": numeric(np.max(finite_values)),
    }


def effective_df_flag(crop: str, degrees_freedom: float) -> str:
    if crop != "RICE":
        return "NONE"
    if degrees_freedom < 5:
        return "VERY_LOW_EFFECTIVE_DF"
    if degrees_freedom < 10:
        return "LOW_EFFECTIVE_DF"
    return "NONE"


def holm_adjust(p_values: np.ndarray) -> np.ndarray:
    values = np.asarray(p_values, dtype=float)
    order = np.argsort(values, kind="mergesort")
    adjusted = np.empty_like(values)
    running = 0.0
    size = len(values)
    for rank, index in enumerate(order):
        running = max(running, (size - rank) * float(values[index]))
        adjusted[index] = min(1.0, running)
    return adjusted


def window_for_variable(crop: dict[str, Any], variable: str) -> str:
    windows = tuple(crop["windows"])
    if len(windows) == 1:
        return str(windows[0])
    return str(windows[1] if variable.endswith("__T_MINUS_1") else windows[0])


def independent_verification(
    frame: pd.DataFrame,
    columns: list[str],
    period_column: str,
    y: np.ndarray,
    fit: dict[str, Any],
) -> dict[str, Any]:
    reference = ed1._reference_svd_fit(frame, columns, period_column, y)
    differences = {
        "beta_max_abs_difference": numeric(np.max(np.abs(fit["beta"] - reference["beta"]))),
        "cr2_covariance_max_abs_difference": numeric(
            np.max(np.abs(fit["climate_covariance"] - reference["covariance"]))
        ),
        "satterthwaite_df_max_abs_difference": numeric(
            np.max(np.abs(fit["satterthwaite_df"] - reference["satterthwaite_df"]))
        ),
        "aht_f_max_abs_difference": numeric(
            abs(fit["aht"]["f_statistic"] - reference["aht"]["f_statistic"])
        ),
        "aht_denominator_df_max_abs_difference": numeric(
            abs(fit["aht"]["denominator_df"] - reference["aht"]["denominator_df"])
        ),
        "aht_p_max_abs_difference": numeric(abs(fit["aht"]["p_value"] - reference["aht"]["p_value"])),
    }
    status = "PASS" if max(differences.values()) <= REFERENCE_TOLERANCE else "FAIL"
    if status != "PASS":
        raise RuntimeError(f"Independent numerical verification failed: {differences}")
    return {
        "status": status,
        "reference_path": "INDEPENDENT_FULL_DESIGN_SVD_CALCULATION",
        "absolute_tolerance": REFERENCE_TOLERANCE,
        "differences": differences,
    }


def estimate_primary_models() -> dict[str, Any]:
    transient_outcomes, perennial_outcomes, source_metadata = read_outcome_sources()
    transient_exposures = pq.read_table(ed1.TRANSIENT_PATH, columns=list(ed1.TRANSIENT_COLUMNS)).to_pandas()
    perennial_exposures = ed1.read_perennial_primary()
    coefficient_rows: list[dict[str, Any]] = []
    joint_rows: list[dict[str, Any]] = []
    sample_rows: list[dict[str, Any]] = []
    verification: dict[str, Any] = {}

    for crop_code, crop in ed1.CROPS.items():
        if crop_code in {"14010020000", "14010070000"}:
            frame, columns = transient_design_with_outcome(transient_exposures, transient_outcomes, crop_code)
            source = source_metadata["transient"]
            outcome_column = "TRANSIENT_CAMPAIGN_YIELD_RAW"
            key_columns = "UBIGEO|CROP_CODE|CAMPAIGN"
        else:
            frame, columns = perennial_design_with_outcome(perennial_exposures, perennial_outcomes, crop_code)
            source = source_metadata["perennial"]
            outcome_column = "YIELD_RAW"
            key_columns = "UBIGEO|COD_CULTIVO|ANO"

        period_column = str(crop["period_column"])
        y = pd.to_numeric(frame["YIELD"], errors="coerce").to_numpy(dtype=float)
        support = outcome_support(y)
        missing_x = int(frame[columns].isna().sum().sum())
        duplicate_keys = int(frame.duplicated(["UBIGEO", period_column]).sum())
        fixed_effects = ed1.fe_matrix(frame, period_column)
        x_within = ed1.absorb_fixed_effects(frame[columns].to_numpy(dtype=float), fixed_effects)
        effective = ed1.effective_cluster_audit(frame, x_within)
        expected = EXPECTED_SAMPLE[crop_code]
        actual = {
            "n": len(frame),
            "districts": int(frame["UBIGEO"].nunique()),
            "effective": int(effective["effective_contributing_clusters"]),
            "periods": int(frame[period_column].nunique()),
        }
        if actual != expected or support["missing"] or missing_x or duplicate_keys:
            raise RuntimeError(
                f"Primary sample identity failed for {crop_code}: actual={actual}, expected={expected}, "
                f"missing_y={support['missing']}, missing_x={missing_x}, duplicates={duplicate_keys}"
            )

        sample_rows.append(
            {
                "CROP_CODE": crop_code,
                "CROP": crop["crop"],
                "MODEL_ID": crop["model_id"],
                "N": actual["n"],
                "NOMINAL_DISTRICTS": actual["districts"],
                "EFFECTIVE_CONTRIBUTING_DISTRICTS": actual["effective"],
                "PERIODS": actual["periods"],
                "MISSING_Y": support["missing"],
                "MISSING_X": missing_x,
                "DUPLICATE_KEYS": duplicate_keys,
                "FINITE_Y": support["finite"],
                "NONFINITE_Y": support["nonfinite"],
                "ZERO_Y": support["zero"],
                "NEGATIVE_Y": support["negative"],
                "Y_MIN": support["minimum"],
                "Y_MEDIAN": support["median"],
                "Y_MAX": support["maximum"],
                "OUTCOME_SOURCE": source["path"],
                "OUTCOME_SOURCE_SHA256": source["sha256"],
                "OUTCOME_COLUMN": outcome_column,
                "KEY_COLUMNS": key_columns,
                "OUTCOME_SCALE": "YIELD_LEVEL_TM_PER_HA",
            }
        )

        fit = ed1.fit_two_way_fe_cr2(frame, columns, period_column, y)
        if fit["nonfinite_count"] or fit["cr2_adjustment_singularities"]:
            raise RuntimeError(f"Primary inference engine failed for {crop_code}")
        verification[crop_code] = independent_verification(frame, columns, period_column, y, fit)
        standard_errors = np.sqrt(np.diag(fit["climate_covariance"]))
        t_statistics = fit["beta"] / standard_errors
        p_values = 2.0 * stats.t.sf(np.abs(t_statistics), fit["satterthwaite_df"])
        holm = holm_adjust(p_values)
        critical = stats.t.ppf(0.975, fit["satterthwaite_df"])
        lower = fit["beta"] - critical * standard_errors
        upper = fit["beta"] + critical * standard_errors
        for index, variable in enumerate(columns):
            coefficient_rows.append(
                {
                    "CROP_CODE": crop_code,
                    "CROP": crop["crop"],
                    "MODEL_ID": crop["model_id"],
                    "CLIMATE_VARIABLE": variable,
                    "WINDOW": window_for_variable(crop, variable),
                    "BETA": numeric(fit["beta"][index]),
                    "CR2_STANDARD_ERROR": numeric(standard_errors[index]),
                    "SATTERTHWAITE_DF": numeric(fit["satterthwaite_df"][index]),
                    "EFFECTIVE_DF_FLAG": effective_df_flag(crop["crop"], fit["satterthwaite_df"][index]),
                    "T_STATISTIC": numeric(t_statistics[index]),
                    "P_VALUE_TWO_SIDED": numeric(p_values[index]),
                    "CI95_LOWER": numeric(lower[index]),
                    "CI95_UPPER": numeric(upper[index]),
                    "HOLM_ADJUSTED_P_VALUE": numeric(holm[index]),
                    "OUTCOME_SCALE": "YIELD_LEVEL_TM_PER_HA",
                    "PRIMARY_CLIMATE_FAMILY": "PHYSICAL_ANOMALY",
                    "FUNCTIONAL_FORM": "LINEAR_ADDITIVE",
                    "DISTRICT_FE": "REQUIRED",
                    "PERIOD_FE": "REQUIRED",
                    "WEIGHTING": "UNWEIGHTED_PRIMARY_ESTIMATION",
                    "INFERENCE": PRIMARY_INFERENCE,
                    "CLAIM_CEILING": CLAIM_CEILING,
                }
            )
        joint_rows.append(
            {
                "CROP_CODE": crop_code,
                "CROP": crop["crop"],
                "MODEL_ID": crop["model_id"],
                "COEFFICIENTS_TESTED": "|".join(columns),
                "NUMERATOR_DF": numeric(fit["aht"]["numerator_df"]),
                "DENOMINATOR_DF": numeric(fit["aht"]["denominator_df"]),
                "F_STATISTIC": numeric(fit["aht"]["f_statistic"]),
                "P_VALUE": numeric(fit["aht"]["p_value"]),
                "JOINT_TEST": "CR2_APPROXIMATE_HOTELLING_T_SQUARED",
                "CLAIM_CEILING": CLAIM_CEILING,
            }
        )

    if len(coefficient_rows) != 21 or len(joint_rows) != 5 or len(sample_rows) != 5:
        raise RuntimeError("Primary result inventory mismatch")
    return {
        "sources": source_metadata,
        "samples": sample_rows,
        "coefficients": coefficient_rows,
        "joint_tests": joint_rows,
        "independent_verification": verification,
    }


def serializable_rows(rows: list[dict[str, Any]], fields: tuple[str, ...]) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    for row in rows:
        serialized: dict[str, str] = {}
        for field in fields:
            value = row[field]
            serialized[field] = canonical_float(value) if isinstance(value, (float, np.floating)) else str(value)
        output.append(serialized)
    return output


def write_csv(path: Path, rows: list[dict[str, Any]], fields: tuple[str, ...]) -> None:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=list(fields), lineterminator="\n", extrasaction="raise")
    writer.writeheader()
    writer.writerows(serializable_rows(rows, fields))
    payload = buffer.getvalue().encode("utf-8")
    accepted = {Path(relative).name: digest for relative, digest in ACCEPTED_NUMERICAL_TABLE_SHA256.items()}
    if hashlib.sha256(payload).hexdigest() != accepted[path.name]:
        raise RuntimeError(f"ER1R_FAIL_NUMERICAL_RESULT_DRIFT: {path.name}")
    # Existing accepted tables are read-only during a reporting correction.
    if path.exists():
        if path.read_bytes() != payload:
            raise RuntimeError(f"ER1R_FAIL_NUMERICAL_RESULT_DRIFT: existing {path.name}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    text = json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True, allow_nan=False) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


def report_text(results: dict[str, Any], lock_sha: str) -> str:
    lines = [
        "# ER1 Primary Real Estimation v1",
        "",
        "## 1. Analytical sample",
        "",
        "All five frozen ED1 samples were reproduced without silent row deletion, imputation, trimming, or winsorization.",
        "",
        "| Crop | N | Districts | Effective districts | Periods | Missing Y | Missing X | Duplicate keys |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in results["samples"]:
        lines.append(
            f"| {row['CROP']} | {row['N']} | {row['NOMINAL_DISTRICTS']} | "
            f"{row['EFFECTIVE_CONTRIBUTING_DISTRICTS']} | {row['PERIODS']} | {row['MISSING_Y']} | "
            f"{row['MISSING_X']} | {row['DUPLICATE_KEYS']} |"
        )
    lines.extend(
        [
            "",
            "## 2. Primary coefficient estimates",
            "",
            "These are conditional historical climate-yield associations under the frozen empirical-association claim ceiling.",
            "",
            "All reported intervals are unadjusted coefficient-specific 95% CR2/Satterthwaite confidence intervals. Holm step-down adjusts coefficient p-values within each crop only. Multiplicity-adjusted confidence intervals were not constructed and are not claimed.",
            "",
            "| Crop | Variable | Window | Beta | CR2 SE | Satterthwaite df | t | Unadjusted p | Unadjusted 95% CR2/Satterthwaite CI | Within-crop Holm p | Flag |",
            "|---|---|---|---:|---:|---:|---:|---:|---|---:|---|",
        ]
    )
    for row in results["coefficients"]:
        interval = f"[{row['CI95_LOWER']:.9g}, {row['CI95_UPPER']:.9g}]"
        lines.append(
            f"| {row['CROP']} | {row['CLIMATE_VARIABLE']} | {row['WINDOW']} | {row['BETA']:.9g} | "
            f"{row['CR2_STANDARD_ERROR']:.9g} | {row['SATTERTHWAITE_DF']:.9g} | "
            f"{row['T_STATISTIC']:.9g} | {row['P_VALUE_TWO_SIDED']:.9g} | {interval} | "
            f"{row['HOLM_ADJUSTED_P_VALUE']:.9g} | {row['EFFECTIVE_DF_FLAG']} |"
        )
    lines.extend(
        [
            "",
            "## 3. Crop-level omnibus climate tests",
            "",
            "| Crop | Numerator df | Denominator df | F | p |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for row in results["joint_tests"]:
        lines.append(
            f"| {row['CROP']} | {row['NUMERATOR_DF']:.9g} | {row['DENOMINATOR_DF']:.9g} | "
            f"{row['F_STATISTIC']:.9g} | {row['P_VALUE']:.9g} |"
        )
    lines.extend(
        [
            "",
            "## 4. Outcome support",
            "",
            "| Crop | Finite | Nonfinite | Missing | Zero | Negative | Min | Median | Max |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in results["samples"]:
        lines.append(
            f"| {row['CROP']} | {row['FINITE_Y']} | {row['NONFINITE_Y']} | {row['MISSING_Y']} | "
            f"{row['ZERO_Y']} | {row['NEGATIVE_Y']} | {row['Y_MIN']:.9g} | {row['Y_MEDIAN']:.9g} | "
            f"{row['Y_MAX']:.9g} |"
        )
    lines.extend(
        [
            "",
            "## 5. Statistical limitations",
            "",
            "Rice rainfall retains `VERY_LOW_EFFECTIVE_DF` with Satterthwaite df `4.919993824254409`. This is an inferential-precision limitation specific to that coefficient and does not alter the frozen model. Other coefficients retain their actual coefficient-specific df.",
            "",
            "Inference precision is heterogeneous across crops and coefficients. Statistical evidence compatible with zero does not by itself imply limited effective degrees of freedom or invalid inference; p-values above 0.05 are not a basis for labeling a coefficient or model weak.",
            "",
            "The panels contain only seven transient campaigns or eight perennial calendar years. Estimates remain empirical associations conditional on district and period fixed effects. No global five-crop familywise-error claim is made.",
            "",
            "No robustness tier, model revision, scenario, GVP calculation, CVaR calculation, A1/A2 comparison, or optimization was executed.",
            "",
            REPORTING_SUMMARY,
            "",
            "Banana lagged Tmin has a negative estimated association. Its within-crop Holm result does not control multiplicity across all 21 coefficients in all five crops. The five prespecified AHT tests are reported separately.",
            "",
            "## 6. Numerical verification and results lock",
            "",
            f"All five independent SVD reference calculations agree within absolute tolerance `{REFERENCE_TOLERANCE:.0e}`. `ER1_PRIMARY_RESULTS_LOCK_SHA256={lock_sha}`.",
            "",
            f"`ER1_NUMERICAL_RESULTS_IDENTITY={NUMERICAL_RESULTS_IDENTITY}` is the SHA-256 of the UTF-8 JSON mapping of the three accepted numerical CSV hashes, with sorted keys and compact separators. It is separate from `ER1_REPORTING_LOCK_IDENTITY={lock_sha}`, the SHA-256 of the complete reporting lock.",
            "",
            f"`PREVIOUS_ER1_PRIMARY_RESULTS_LOCK_SHA256={PREVIOUS_RESULTS_LOCK_SHA256}` is preserved. `NUMERICAL_RESULT_CHANGE=FALSE`; only reporting metadata and wording changed in ER1R.",
            "",
            *[f"`{key}={value}`\n" for key, value in REPORTING_SEMANTICS.items()],
            f"`FINAL_VERDICT={FINAL_VERDICT}`",
            "",
            "`ER1_FREEZE_AUTHORIZED=NO`",
            "",
            "`ER1R_FREEZE_AUTHORIZED=NO`",
            "",
        ]
    )
    return "\n".join(lines)


def run(output_root: Path) -> dict[str, str]:
    preflight_result = preflight()
    results = estimate_primary_models()
    write_csv(output_root / COEFFICIENTS_REL, results["coefficients"], COEFFICIENT_FIELDS)
    write_csv(output_root / JOINT_TESTS_REL, results["joint_tests"], JOINT_FIELDS)
    write_csv(output_root / SAMPLE_AUDIT_REL, results["samples"], SAMPLE_FIELDS)
    core_hashes = {
        relative.as_posix(): sha256_file(output_root / relative)
        for relative in (COEFFICIENTS_REL, JOINT_TESTS_REL, SAMPLE_AUDIT_REL)
    }
    lock = {
        "schema_version": "1.0.0",
        "project": "ENSO_EL_NINO_2026_2027_AGRICULTURE_PIURA",
        "gate": "ER1_FIRST_REAL_PRIMARY_ECONOMETRIC_ESTIMATION_V1",
        "status": "CANDIDATE_PRIMARY_RESULTS_LOCKED_NOT_FROZEN",
        "ed1_freeze_sha": ED1_FREEZE_SHA,
        "ed1_status": "PASS_FROZEN",
        "preflight": preflight_result,
        "outcome_unsealed": True,
        "outcome_sources": results["sources"],
        "sample_identities": results["samples"],
        "primary_coefficients": results["coefficients"],
        "aht_joint_tests": results["joint_tests"],
        "independent_numerical_verification": results["independent_verification"],
        "result_table_sha256": core_hashes,
        "primary_models_estimated": 5,
        "primary_coefficients_reported": 21,
        "aht_tests": 5,
        "holm_within_crop": "PASS",
        "robustness_tiers_executed": 0,
        "model_revision_after_results": False,
        "real_regressions_outside_authorization": 0,
        "execution_firewall": {
            "R1_LEVEL_CLIMATE_FAMILY": "NOT_EXECUTED",
            "R2_STANDARDIZED_ANOMALY_COMPARABILITY": "NOT_EXECUTED",
            "R3_RESTRICTED_WILD_CLUSTER_BOOTSTRAP": "NOT_EXECUTED",
            "R4_SPATIAL_HAC": "NOT_EXECUTED",
            "R5_LEAVE_ONE_PERIOD_OUT_ALL_PERIODS": "NOT_EXECUTED",
            "R6_B3_STRICT_EXPOSURE": "NOT_EXECUTED",
            "LOG_OUTCOME": "NOT_EXECUTED",
            "WINSORIZATION": "NOT_EXECUTED",
            "TRIMMING": "NOT_EXECUTED",
            "ENSO_SCENARIOS": "NOT_EXECUTED",
            "GVP": "NOT_EXECUTED",
            "VAR_CVAR": "NOT_EXECUTED",
            "A1_A2": "NOT_EXECUTED",
            "OPTIMIZATION": "NOT_EXECUTED",
        },
        "claim_ceiling": CLAIM_CEILING,
        "reporting_gate": "ER1R_PRIMARY_RESULTS_REPORTING_SEMANTICS_CORRECTION",
        "reporting_semantics": REPORTING_SEMANTICS,
        "reporting_summary": REPORTING_SUMMARY,
        "er1_numerical_results_identity": {
            "sha256": NUMERICAL_RESULTS_IDENTITY,
            "scope": "UTF8_SORTED_COMPACT_JSON_OF_ACCEPTED_NUMERICAL_CSV_SHA256_MAPPING",
            "table_sha256": ACCEPTED_NUMERICAL_TABLE_SHA256,
        },
        "er1_reporting_lock_identity": {
            "version": "ER1R-v1",
            "sha256_scope": "COMPLETE_LOCK_FILE_REPORTED_IN_REPORT_AND_CLI_TO_AVOID_SELF_REFERENCE",
            "previous_primary_results_lock_sha256": PREVIOUS_RESULTS_LOCK_SHA256,
            "numerical_result_change": False,
        },
        "numerical_result_change": False,
        "final_verdict": FINAL_VERDICT,
        "er1_freeze_authorized": False,
        "er1r_freeze_authorized": False,
        "next_action": "RETURN_TO_SCIENTIFIC_DIRECTOR_FOR_ER1_FREEZE_DECISION_IF_PASS",
    }
    write_json(output_root / LOCK_REL, lock)
    lock_sha = sha256_file(output_root / LOCK_REL)
    report_path = output_root / REPORT_REL
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_bytes(report_text(results, lock_sha).encode("utf-8"))
    return {relative.as_posix(): sha256_file(output_root / relative) for relative in OUTPUT_RELS}


def main() -> int:
    parser = argparse.ArgumentParser(description="Execute the five frozen ED1 primary real-yield models only.")
    parser.add_argument("--output-root", type=Path, default=ROOT)
    args = parser.parse_args()
    hashes = run(args.output_root.resolve())
    lock = json.loads((args.output_root.resolve() / LOCK_REL).read_text(encoding="utf-8"))
    rice_df = min(
        row["SATTERTHWAITE_DF"] for row in lock["primary_coefficients"] if row["CROP"] == "RICE"
    )
    print("ED1_PREFLIGHT=PASS")
    print("OUTCOME_UNSEALED=TRUE")
    print("PRIMARY_MODELS_ESTIMATED=5")
    print("PRIMARY_COEFFICIENTS_REPORTED=21")
    print("AHT_TESTS=5")
    print(f"MIN_EFFECTIVE_DF_RICE={canonical_float(rice_df)}")
    print(f"PRIMARY_RESULTS_LOCK_SHA256={hashes[LOCK_REL.as_posix()]}")
    print(f"PREVIOUS_ER1_PRIMARY_RESULTS_LOCK_SHA256={PREVIOUS_RESULTS_LOCK_SHA256}")
    print(f"ER1_NUMERICAL_RESULTS_IDENTITY={NUMERICAL_RESULTS_IDENTITY}")
    print(f"ER1_REPORTING_LOCK_IDENTITY={hashes[LOCK_REL.as_posix()]}")
    print("NUMERICAL_RESULT_CHANGE=FALSE")
    print("INDEPENDENT_NUMERICAL_VERIFICATION=PASS")
    print("ROBUSTNESS_TIERS_EXECUTED=0")
    for relative, digest in hashes.items():
        print(f"SHA256={digest}  {relative}")
    print(f"FINAL_VERDICT={FINAL_VERDICT}")
    print("ER1_FREEZE_AUTHORIZED=NO")
    print("ER1R_FREEZE_AUTHORIZED=NO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
