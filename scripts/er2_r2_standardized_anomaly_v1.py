from __future__ import annotations

import argparse
import csv
import io
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import er2_r1_numerical_adjudication_v1 as r1a

r1, er1, er2p, ed1 = r1a.legacy, r1a.er1, r1a.er2p, r1a.ed1
sha, json_bytes, git = r1.sha, r1.json_bytes, r1.git
R1_SHA = "b5614bb02bad3a40d90ca55688e19d71ee272877"
R1_BRANCH = "phase/er2-r1-level-robustness-v1"
R1_TAG = "er2-r1-level-robustness-v1-freeze"
PREDECESSOR_SHA = "d035e999b213b7e8af8d7c26c7246bd7a17d30eeb75a79667e4e00e3810869b8"
TIER_SHA = "22d27c741ad28f1be971c63a9eafdbf2e88ae16644645c2ece0970150323b0fd"
TIER_ID = "R2_STANDARDIZED_ANOMALY_COMPARABILITY"
FAMILY = "STANDARDIZED_ANOMALY"
PASS = "ER2_R2_PASS_RESULTS_LOCKED_READY_FOR_DIRECTOR_REVIEW"
HOLD = "ER2_R2_HOLD_NUMERICAL_ADJUDICATION_REQUIRED"
INTERPRETATION = "ONE_LOCAL_CLIMATE_SD_CHANGE_IN_NATIVE_CROP_YIELD_UNITS"
MULTIPLICITY = "HOLM_STEP_DOWN_WITHIN_CROP_R2_COEFFICIENT_P_VALUES"
CI_SEMANTICS = "UNADJUSTED_95_PERCENT_CR2_SATTERTHWAITE"
SCRIPT_REL = Path("scripts/er2_r2_standardized_anomaly_v1.py")
TEST_REL = Path("tests/test_er2_r2_standardized_anomaly_v1.py")
RESULTS_REL = Path("outputs/econometrics/ER2_R2_STANDARDIZED_RESULTS.csv")
JOINT_REL = Path("outputs/econometrics/ER2_R2_STANDARDIZED_JOINT_TESTS.csv")
SAMPLE_REL = Path("outputs/econometrics/ER2_R2_SAMPLE_AUDIT.csv")
PROVENANCE_REL = Path("outputs/econometrics/ER2_R2_STANDARDIZATION_PROVENANCE.csv")
REPORT_REL = Path("outputs/econometrics/ER2_R2_REPORT.md")
LOCK_REL = Path("outputs/econometrics/ER2_R2_RESULTS_LOCK.json")
OUTPUT_RELS = (RESULTS_REL, JOINT_REL, SAMPLE_REL, PROVENANCE_REL, REPORT_REL, LOCK_REL)
CANDIDATE_RELS = (*OUTPUT_RELS, SCRIPT_REL, TEST_REL)
REPORTING_LOCK_REL = Path("outputs/econometrics/ER2_R2_RESULTS_LOCK_REPORTING_CERTIFIED.json")
REPORTING_OUTPUT_RELS = (REPORT_REL, REPORTING_LOCK_REL)
REPORTING_CANDIDATE_RELS = (*CANDIDATE_RELS, REPORTING_LOCK_REL)
REPORTING_PASS = "ER2_R2R_PASS_REPORTING_HARDENED_READY_FOR_R2_FREEZE_DECISION"
REPORTING_FAIL = "ER2_R2R_FAIL_REPORTING_SEMANTICS"
INITIAL_LOCK_SHA = "117a3fe5da88f44d31b176495409f6e84189148f1020417f046b0df3dd4c5f6b"
INITIAL_REPORT_SHA = "7aba59037f2dcbe5712a923cfa8ff14f25c239a086b53cbc8da260e439bd858e"
INITIAL_SCRIPT_SHA = "30a00d1e7db670f159d0f413d827165cd4f64098ed646e037bdafe60b0c57aaf"
INITIAL_TEST_SHA = "fd0c58bde0037cee27b52e0c61328decc66d8c06622beab90f6c03dc717cef35"
PROTECTED_R2_HASHES = {
    RESULTS_REL: "2185b8c78fef50c07c7d6e6789761f0fdd066940df1f132ab8676d61c71f7f7b",
    JOINT_REL: "c62a3c3e7797a970449376e2990af6578a556ccbda0f267087083eaf43cdfb32",
    SAMPLE_REL: "586070e1e104a99dbf5b984446b89c115b110521b7b3796fe7590d65f55e0192",
    PROVENANCE_REL: "55cdbd916a8e661c3e85ea113b1b6ab00ea52d740bd1490c0df33db0cb52983d",
    LOCK_REL: INITIAL_LOCK_SHA,
}
CORRECTED_INTERPRETATION = "ONE_UNIT_INCREASE_IN_PHENOLOGY_ALIGNED_STANDARDIZED_ANOMALY_EXPOSURE_INDEX_IN_NATIVE_CROP_YIELD_UNITS"
HUMAN_INTERPRETATION = "Change in crop yield (TM/ha) associated with a one-unit increase in the phenology-aligned exposure index constructed from locally standardized monthly climate anomalies."
INDEX_CLARIFICATION = "Each underlying monthly anomaly is standardized by its district x calendar-month 1991-2020 standard deviation; the aggregated crop/window exposure itself is not asserted to have standard deviation one."
MONTHLY_FORMULA = "Z_(district,calendar_month,year) = (x - district_calendar_month_1991_2020_mean) / district_calendar_month_1991_2020_sample_SD"
REPORTING_CLARIFICATION = "FINAL_AGGREGATED_INDEX_IS_BUILT_FROM_LOCAL_SD_STANDARDIZED_MONTHLY_COMPONENTS_BUT_IS_NOT_ITSELF_ASSERTED_TO_HAVE_SD_ONE"
BANANA_COMPONENT_STATEMENT = "BANANA_CLIMATE_RESPONSE_EVIDENCE_APPEARS_UNDER_MULTIPLE_EXPOSURE_DEFINITIONS_BUT_COMPONENT_IDENTITY_IS_NOT_INVARIANT"
EXPECTED_AHT_P = {
    "14010020000": 0.8176225560839411, "14010070000": 0.21906295155553884,
    "13010210000": 0.001230981629089468, "13010170102": 0.022744950644943394,
    "15010040000": 0.07257504530128239,
}
NORMALS_REL = "data/processed/climate/climate_normals_1991_2020.parquet"
MONTHLY_REL = "data/processed/climate/climate_anomalies.parquet"
CLIMATE_SCRIPT_REL = "scripts/climate_v1_1_pipeline.py"
EXPOSURE_SPEC_REL = "config/climate_exposure/climate_exposure_spec_v1.json"
FROZEN_HASHES = {
    **r1.FROZEN_HASHES, **r1a.ORIGINAL_HASHES,
    r1a.SCRIPT_REL.as_posix(): "ea7e9652960506ad2582051ca967322bb2a23e520bba33a500e1c96351b240be",
    r1a.TEST_REL.as_posix(): "a51acaec0976d643b309d2eeee97dce48ab0e19203ec6ac1cdf5d8a09cc564fe",
    r1a.JSON_REL.as_posix(): "ea91217b2e9cf8daf9eed157a2de99d0a856146ec9d778ab37394967e10ef2f6",
    r1a.REPORT_REL.as_posix(): "d9de296f6855e69f43d5091f7970219c7cc5b521d4420178505d5c07e399f721",
    r1a.CERTIFIED_REL.as_posix(): PREDECESSOR_SHA,
    NORMALS_REL: "b9dfb3bb1c51229b68f06c49c2b815c086f931896f39ad70f9a96852a9a07717",
    MONTHLY_REL: "11a1fc61cab062faf70e3f12d2a06f050a2ccf094273807192943ad130deb6df",
    CLIMATE_SCRIPT_REL: "2d2c058afefd801f1eccc9365f849a0b8f47668aacf8da585bde52c720bedaa6",
    EXPOSURE_SPEC_REL: "e2e1eabbf8530cb0dfe8538d12f12d73a6a8e77c0e773351b593a14cbe1e268a",
    "scripts/build_perennial_exposures.py": "0b24919c326c985b71e3f022696d21a865f6088f82001e62612af33b1be0c95b",
    "scripts/build_transient_cohort_exposures.py": "1b8c23dcc76b13bbfba3559e56c4ea85d361d0907124028d7ae981674956186b",
    "data/processed/phenology/transient_cohort_exposures.parquet": "e4ce7922f00a516643a5de832cc38377e20b3755ac46152cfb79900441564b39",
}
# Reuse the frozen R1A scale-aware envelope before any R2 outcome fit.
NUMERICAL_POLICY = {
    "source": r1a.SCRIPT_REL.as_posix(), "source_sha256": FROZEN_HASHES[r1a.SCRIPT_REL.as_posix()],
    "beta_relative_l2": r1a.BETA_RELATIVE_TOLERANCE,
    "covariance_relative_frobenius": r1a.ADJUDICATION_RELATIVE_TOLERANCE,
    "df_relative_l2_and_each_coefficient": r1a.ADJUDICATION_RELATIVE_TOLERANCE,
    "aht_scalar_relative": r1a.ADJUDICATION_RELATIVE_TOLERANCE,
    "ed1_absolute_alarm": er1.REFERENCE_TOLERANCE,
    "design_svd_rcond": 1e-12, "rank_and_zero_singularity_agreement_required": True,
    "policy_fixed_before_first_r2_estimation": True, "post_result_tolerance_change": False,
    "absolute_alarm_alone_is_certification": False,
}
FIREWALL = {
    **{f"R{i}": "NOT_EXECUTED" for i in range(3, 7)},
    **{name: "NOT_EXECUTED" for name in ("BOOTSTRAP", "CONLEY", "LOO", "B3", "ENSO_SCENARIOS", "GVP", "VAR_CVAR", "A1_A2", "OPTIMIZATION")},
    "PRIMARY_REPLACEMENT": "PROHIBITED", "R3_ADAPTER_IMPLEMENTED": False,
    "R3_AUTHORIZATION_STATUS": "NOT_AUTHORIZED", "Y_STANDARDIZED": False,
    "FULLY_STANDARDIZED_EFFECT": False, "STANDARDIZATION_RECOMPUTED": False,
    "CROSS_CROP_COEFFICIENT_MAGNITUDE_RANKING": "NOT_AUTHORIZED",
    "CROSS_CROP_SIGNIFICANCE_RANKING": "NOT_AUTHORIZED",
    "SIGNIFICANCE_VOTE_COUNTING": "PROHIBITED", "ROBUSTNESS_SCORE": "PROHIBITED",
    "BANANA_SPECIFIC_MODEL": "PROHIBITED", "LEMON_SPECIFIC_MODEL": "PROHIBITED",
    "GLOBAL_FWER": "NOT_CLAIMED", "MULTIPLICITY_ADJUSTED_CI": "NOT_CONSTRUCTED_NOT_CLAIMED",
    "CLAIM_CEILING": er1.CLAIM_CEILING,
}


def require(condition: bool, code: str, detail: str = "") -> None:
    if not condition:
        raise RuntimeError(code + (": " + detail if detail else ""))


def csv_bytes(rows: list[dict]) -> bytes:
    # JSON transport sorts object keys; fix CSV column order before and after transport.
    fields = sorted(rows[0])
    return r1.csv_bytes([{key: row[key] for key in fields} for row in rows])


def verify_inputs() -> dict:
    actual = {p: sha((ROOT / p).read_bytes()) for p in sorted(FROZEN_HASHES)}
    require(actual == FROZEN_HASHES, "ER2_R2_FAIL_UPSTREAM_IMMUTABILITY")
    return actual


def preflight(live_remote: bool = False) -> dict:
    require(git("rev-parse", "HEAD") == R1_SHA and git("branch", "--show-current") == R1_BRANCH,
            "ER2_R2_FAIL_FROZEN_CONTRACT", "exact R1 build parent")
    require(git("rev-parse", "HEAD^") == r1.ER2P_SHA, "ER2_R2_FAIL_FROZEN_CONTRACT", "R1 parent")
    for branch, tag, expected in ((R1_BRANCH, R1_TAG, R1_SHA),
                                  (r1.ER2P_BRANCH, r1.ER2P_TAG, r1.ER2P_SHA),
                                  (er2p.ER1_BRANCH, er2p.ER1_TAG, er2p.ER1_SHA),
                                  (er2p.ED1_BRANCH, er2p.ED1_TAG, er2p.ED1_SHA)):
        require(git("rev-parse", branch) == git("rev-parse", "origin/" + branch)
                == git("rev-parse", tag + "^{}") == expected,
                "ER2_R2_FAIL_UPSTREAM_IMMUTABILITY", branch)
    if live_remote:
        refs = dict(line.split()[::-1] for line in git("ls-remote", "origin",
                    "refs/heads/" + R1_BRANCH, "refs/tags/" + R1_TAG + "^{}").splitlines())
        require(refs == {"refs/heads/" + R1_BRANCH: R1_SHA, "refs/tags/" + R1_TAG + "^{}": R1_SHA},
                "ER2_R2_FAIL_FROZEN_CONTRACT", "live R1 remote refs")
    require(not git("diff", "--name-only") and not git("diff", "--cached", "--name-only"),
            "ER2_R2_FAIL_UPSTREAM_IMMUTABILITY", "tracked tree/index")
    allowed = {p.as_posix() for p in REPORTING_CANDIDATE_RELS}
    require(set(git("ls-files", "--others", "--exclude-standard").splitlines()) <= allowed,
            "ER2_R2_FAIL_FROZEN_CONTRACT", "original eight files plus one reporting lock only")
    prior = {p for p in FROZEN_HASHES if Path(p).name.startswith("ER2_R1_")}
    require(set(er2p.forbidden_result_paths(ROOT)) <= prior | allowed,
            "ER2_R2_FAIL_FROZEN_CONTRACT", "unauthorized tier artifact")
    inputs = verify_inputs()
    predecessor = (ROOT / r1a.CERTIFIED_REL).read_bytes()
    committed = subprocess.check_output(["git", "show", R1_SHA + ":" + r1a.CERTIFIED_REL.as_posix()], cwd=ROOT)
    require(predecessor == committed and sha(committed) == PREDECESSOR_SHA,
            "ER2_R2_FAIL_FROZEN_CONTRACT", "certified predecessor committed bytes")
    certified = json.loads(predecessor)
    require(certified["NUMERICAL_ADJUDICATION_STATUS"] == "PASS"
            and certified["er2p_freeze_sha"] == r1.ER2P_SHA,
            "ER2_R2_FAIL_FROZEN_CONTRACT", "R1 certification")
    primary_lock = json.loads((ROOT / er1.LOCK_REL).read_bytes())
    identity = sha(json.dumps(primary_lock["result_table_sha256"], sort_keys=True, separators=(",", ":")).encode("utf-8"))
    require(identity == er2p.NUMERICAL_IDENTITY == certified["er1_numerical_results_identity"],
            "ER2_R2_FAIL_FROZEN_CONTRACT", "ER1 numerical identity")
    tier = json.loads((ROOT / er2p.CONFIG_REL).read_bytes())["tiers"][1]
    rows = list(csv.DictReader(io.StringIO((ROOT / er2p.TIERS_REL).read_text(encoding="utf-8"))))
    require(sha(er2p.json_bytes(tier)) == rows[1]["TIER_CONTRACT_SHA256"] == TIER_SHA,
            "ER2_R2_FAIL_FROZEN_CONTRACT", "R2 tier hash")
    require(tier["tier_id"] == TIER_ID and tier["order"] == 2 and tier["family"] == FAMILY
            and tier["multiplicity"] == MULTIPLICITY and tier["same_primary_sample"]
            and tuple(tier["regressors"]) == ed1.FAMILIES[FAMILY],
            "ER2_R2_FAIL_FROZEN_CONTRACT", "R2 contract")
    er1.verify_ed1_contract()
    return {"status": "PASS", "r1_freeze_sha": R1_SHA, "predecessor_committed_byte_identity": True,
            "previous_tier_lock_sha256": PREDECESSOR_SHA, "tier_contract": tier,
            "tier_contract_sha256": TIER_SHA, "exact_input_sha256": inputs,
            "remote_r1_ref_requirement": R1_SHA,
            "execution_authorization": "SCIENTIFIC_DIRECTOR_ER2_R2_AUTHORIZATION_NOT_PREDECESSOR_LOCK"}


def keys(frame: pd.DataFrame, period: str) -> list[list[str]]:
    require(not frame.duplicated(["UBIGEO", period]).any(),
            "ER2_R2_FAIL_SAMPLE_IDENTITY_OR_STANDARDIZED_SUPPORT", "duplicate keys")
    return frame[["UBIGEO", period]].astype(str).values.tolist()


def align_standardized(primary: pd.DataFrame, standardized: pd.DataFrame, columns: list[str], period: str) -> pd.DataFrame:
    require(keys(primary, period) == keys(standardized, period),
            "ER2_R2_FAIL_SAMPLE_IDENTITY_OR_STANDARDIZED_SUPPORT", "ordered keys differ; no deletion allowed")
    require(all(column in standardized for column in columns)
            and np.isfinite(standardized[columns].to_numpy(dtype=float)).all(),
            "ER2_R2_FAIL_SAMPLE_IDENTITY_OR_STANDARDIZED_SUPPORT", "missing standardized X; no deletion allowed")
    result = standardized.copy()
    result["YIELD"] = primary["YIELD"].to_numpy(dtype=float)
    require(np.array_equal(result["YIELD"], primary["YIELD"])
            and np.array_equal(ed1.fe_matrix(primary, period), ed1.fe_matrix(result, period)),
            "ER2_R2_FAIL_FROZEN_CONTRACT", "Y/FE identity")
    return result


def array_sha(value: np.ndarray) -> str:
    return sha(np.asarray(value, dtype="<f8").tobytes(order="C"))


def model_contract(code: str, columns: list[str]) -> dict:
    return {**r1.model_contract(code, columns), "family": FAMILY, "role": "STANDARDIZED_X_COMPARABILITY",
            "interpretation": INTERPRETATION, "same_primary_sample": True,
            "outcome_standardized": False, "fully_standardized_effect": False}


def prepare_designs() -> tuple[dict, dict]:
    transient_outcomes, perennial_outcomes, sources = er1.read_outcome_sources()
    transient = pq.read_table(ed1.TRANSIENT_PATH, columns=list(ed1.TRANSIENT_COLUMNS)).to_pandas()
    transient_primary = ed1.read_transient_primary()
    perennial = ed1.read_perennial_primary()
    old = json.loads((ROOT / r1.LOCK_REL).read_bytes())
    frozen_keys = {c: v["er1_ordered_keys"] for c, v in old["sample_identity"].items()}
    frozen_keys.update({v["crop_code"]: v["ordered_sample_keys"] for v in old["perennial_equivalence_diagnostics"]})
    er1_sample = {v["CROP_CODE"]: v for v in json.loads((ROOT / er1.LOCK_REL).read_bytes())["sample_identities"]}
    designs = {}
    for code in er2p.CROP_ORDER:
        crop, expected = ed1.CROPS[code], er1.EXPECTED_SAMPLE[code]
        period = crop["period_column"]
        if code in er2p.TRANSIENT:
            primary, physical_columns = er1.transient_design_with_outcome(transient, transient_outcomes, code)
        else:
            primary, physical_columns = er1.perennial_design_with_outcome(perennial, perennial_outcomes, code)
        standardized, columns = ed1.primary_design_frame(transient_primary, perennial, code, FAMILY)
        standardized[period] = standardized[period].astype(str)
        primary[period] = primary[period].astype(str)
        frame = align_standardized(primary, standardized, columns, period)
        sample_keys = keys(primary, period)
        require(sample_keys == frozen_keys[code], "ER2_R2_FAIL_SAMPLE_IDENTITY_OR_STANDARDIZED_SUPPORT",
                "ER1 ordered keys recorded in frozen R1")
        actual = {"n": len(frame), "districts": int(frame["UBIGEO"].nunique()), "periods": int(frame[period].nunique())}
        require(actual == {k: expected[k] for k in actual}, "ER2_R2_FAIL_SAMPLE_IDENTITY_OR_STANDARDIZED_SUPPORT", "counts")
        y = frame["YIELD"].to_numpy(dtype=float)
        support = er1.outcome_support(y)
        require(all(support[k] == er1_sample[code][v] for k,v in (("minimum", "Y_MIN"), ("median", "Y_MEDIAN"), ("maximum", "Y_MAX"))),
                "ER2_R2_FAIL_SAMPLE_IDENTITY_OR_STANDARDIZED_SUPPORT", "frozen Y support")
        if code in er2p.TRANSIENT:
            require(array_sha(y) == old["sample_identity"][code]["outcome_sha256"],
                    "ER2_R2_FAIL_SAMPLE_IDENTITY_OR_STANDARDIZED_SUPPORT", "frozen Y bytes")
        designs[code] = {"frame": frame, "primary": primary, "columns": columns, "physical_columns": physical_columns,
                         "contract": model_contract(code, columns), "sample": {**actual,
                            "key_columns": ["UBIGEO", period], "er1_ordered_keys": sample_keys,
                            "r2_ordered_keys": keys(frame, period), "key_sha256": sha(json_bytes(sample_keys)),
                            "frozen_key_record": r1.LOCK_REL.as_posix(), "outcome_sha256": array_sha(y),
                            "outcome_support": support, "y_exact_identity": True, "fe_exact_identity": True,
                            "fe_sha256": array_sha(ed1.fe_matrix(frame, period)), "missing_x_cells": 0,
                            "removed_primary_rows": 0, "added_primary_rows": 0}}
    return designs, sources


def standardization_provenance(designs: dict) -> list[dict]:
    normals = pq.read_table(ROOT / NORMALS_REL).to_pandas()
    require(not normals.duplicated(["UBIGEO", "MONTH"]).any()
            and (normals[["RAIN_N_YEARS", "TMAX_N_YEARS", "TMIN_N_YEARS"]] == 30).all().all()
            and (normals[["RAIN_SD", "TMAX_SD", "TMIN_SD"]] > 0).all().all(),
            "ER2_R2_FAIL_STANDARDIZED_EXPOSURE_PROVENANCE", "frozen local reference population/scale")
    rows = []
    for code, design in designs.items():
        transient = code in er2p.TRANSIENT
        source = (ed1.TRANSIENT_PATH if transient else ed1.PERENNIAL_PATH).relative_to(ROOT).as_posix()
        schema = pq.read_schema(ROOT / source)
        for index, (variable, physical) in enumerate(zip(design["columns"], design["physical_columns"])):
            source_column = ed1.FAMILIES[FAMILY][index % 3]
            require(source_column in schema.names and variable == source_column + physical[len(ed1.FAMILIES["PHYSICAL_ANOMALY"][index % 3]):],
                    "ER2_R2_FAIL_STANDARDIZED_EXPOSURE_PROVENANCE", "exact frozen ED1 mapping")
            stem = source_column.removesuffix("_Z")
            rows.append({"CROP_CODE": code, "CROP": ed1.CROPS[code]["crop"], "VARIABLE": variable,
                "WINDOW": er1.window_for_variable(ed1.CROPS[code], variable), "SOURCE_FILE": source,
                "SOURCE_COLUMN": source_column, "SOURCE_SHA256": FROZEN_HASHES[source], "SOURCE_CLIMATE_FAMILY": FAMILY,
                "ER1_VARIABLE": physical, "UPSTREAM_MONTHLY_FORMULA": f"({ed1.FAMILIES['LEVEL'][index % 3]}-{stem}_NORMAL)/{stem}_SD; SD>0 else NaN",
                "REFERENCE_POPULATION": "WHOLE_DISTRICT_UBIGEO_X_CALENDAR_MONTH_1991_2020_30_ANNUAL_VALUES",
                "REFERENCE_SD": "SAMPLE_SD_DDOF_1_PANDAS_GROUPBY_STD",
                "NORMALS_FILE": NORMALS_REL, "NORMALS_SHA256": FROZEN_HASHES[NORMALS_REL],
                "MONTHLY_FILE": MONTHLY_REL, "MONTHLY_SHA256": FROZEN_HASHES[MONTHLY_REL],
                "FORMULA_IMPLEMENTATION": CLIMATE_SCRIPT_REL + ":build_primary_tables",
                "FORMULA_IMPLEMENTATION_SHA256": FROZEN_HASHES[CLIMATE_SCRIPT_REL],
                "EXPOSURE_SPEC_FILE": EXPOSURE_SPEC_REL, "EXPOSURE_SPEC_SHA256": FROZEN_HASHES[EXPOSURE_SPEC_REL],
                "AGGREGATION": "MEAN_MONTHLY_Z_PER_COHORT_THEN_POSITIVE_OBSERVED_UNAMBIGUOUS_SIEMBRA_WEIGHTED_MEAN" if transient else "ARITHMETIC_MEAN_MONTHLY_Z_IN_FROZEN_WINDOW",
                "AGGREGATION_IMPLEMENTATION": "scripts/build_transient_cohort_exposures.py|scripts/primary_transient_exposure_v1.py" if transient else "scripts/build_perennial_exposures.py",
                "REFERENCE_PERIOD_SELECTED_USING_OUTCOMES": False, "STANDARDIZATION_RECOMPUTED": False,
                "FINAL_ANALYTICAL_X_UNIT_SD_CLAIMED": False, "AUDIT_STAGE": "BEFORE_ANY_R2_ESTIMATION"})
    require(len(rows) == 21, "ER2_R2_FAIL_STANDARDIZED_EXPOSURE_PROVENANCE", "inventory")
    return rows


def transformation_relation(physical: np.ndarray, standardized: np.ndarray) -> dict:
    x, z = np.asarray(physical, dtype=float), np.asarray(standardized, dtype=float)
    require(x.shape == z.shape and np.isfinite(x).all() and np.isfinite(z).all(),
            "ER2_R2_FAIL_STANDARDIZED_EXPOSURE_PROVENANCE", "relation support")
    scalar = float(x @ z / (x @ x)) if float(x @ x) > 0 else 0.
    residual = z - scalar * x
    maximum = float(np.max(np.abs(residual)))
    bound = float(128 * np.finfo(float).eps * max(1., np.max(np.abs(z)), np.max(np.abs(scalar * x))))
    pure = scalar > 0 and maximum <= bound
    return {"STANDARDIZATION_RELATION_TO_PHYSICAL_ANOMALY": "PURE_POSITIVE_SCALAR_RESCALING" if pure else "LOCALLY_VARYING_STANDARDIZATION_TRANSFORMATION",
            "EXPOSURE_ONLY_SCALAR_PROJECTION": scalar, "PROJECTION_MAX_ABS_RESIDUAL": maximum,
            "PROJECTION_RELATIVE_L2_RESIDUAL": float(np.linalg.norm(residual) / max(np.linalg.norm(z), r1a.TINY)),
            "SOURCE_REPRESENTATION_BOUND": bound, "OUTCOMES_USED_IN_DIAGNOSTIC": False,
            "DIAGNOSTIC_ALTERS_R2": False}


def numerical_verification(frame: pd.DataFrame, columns: list[str], period: str, y: np.ndarray, fit: dict) -> dict:
    reference = ed1._reference_svd_fit(frame, columns, period, y)
    diagnostics = r1a.frozen_path_diagnostics(frame, columns, period, fit, "SVD")
    reference.update(rank=diagnostics["full_design"]["rank_at_rcond"], singularities=diagnostics["cr2_singularity_count"])
    main = r1a.main_view(fit)
    comparison = r1a.compare_paths(main, reference)
    absolute = {name + "_max_abs": float(np.max(np.abs(np.asarray(main[name]) - np.asarray(reference[name]))))
                for name in ("beta", "covariance", "satterthwaite_df")}
    absolute.update({"aht_" + k + "_abs": abs(main["aht"][k] - reference["aht"][k]) for k in main["aht"]})
    extra = {k: r1a.relative_error(main["aht"][k], reference["aht"][k]) for k in ("wald_chi_square", "delta", "numerator_df")}
    require(all(np.isfinite(v) for v in absolute.values()), HOLD, "nonfinite verification")
    status = "PASS" if comparison["status"] == "PASS" and max(extra.values()) <= NUMERICAL_POLICY["aht_scalar_relative"] else "HOLD"
    return {"status": status, "paths": ["FROZEN_ED1_FULL_DESIGN_LSTSQ_CR2", "FROZEN_ED1_INDEPENDENT_FULL_DESIGN_SVD_CR2"],
            "absolute_discrepancies": absolute, "scale_aware": comparison, "additional_aht_relative": extra,
            "ed1_strict_absolute_1e_8_alarm": "PASS" if max(absolute.values()) <= er1.REFERENCE_TOLERANCE else "FAIL_PRESERVED",
            "main": r1a.serializable_fit(main), "reference": r1a.serializable_fit(reference),
            "reference_design_diagnostics": diagnostics}


def calculate(pre: dict, designs: dict, provenance: list[dict], sources: dict) -> dict:
    table = list(csv.DictReader(io.StringIO((ROOT / er1.COEFFICIENTS_REL).read_text(encoding="utf-8"))))
    primary_lookup = {(v["CROP_CODE"], v["CLIMATE_VARIABLE"]): v for v in table}
    coefficients, joint, sample_rows, samples, contracts, verification, relations = [], [], [], {}, {}, {}, []
    for code, design in designs.items():
        frame, columns, crop = design["frame"], design["columns"], ed1.CROPS[code]
        period, y = crop["period_column"], frame["YIELD"].to_numpy(dtype=float)
        fit = ed1.fit_two_way_fe_cr2(frame, columns, period, y)
        require(not fit["nonfinite_count"] and not fit["cr2_adjustment_singularities"], HOLD, "main inference engine")
        effective = ed1.effective_cluster_audit(frame, fit["x_within"])
        require(effective["effective_contributing_clusters"] == er1.EXPECTED_SAMPLE[code]["effective"],
                "ER2_R2_FAIL_SAMPLE_IDENTITY_OR_STANDARDIZED_SUPPORT", "effective districts")
        verification[code] = numerical_verification(frame, columns, period, y, fit)
        se = np.sqrt(np.diag(fit["climate_covariance"]))
        dfs, beta = fit["satterthwaite_df"], fit["beta"]
        require(np.all(se > 0) and np.all(dfs > 0) and fit["aht"]["denominator_df"] > 0, HOLD, "inference support")
        t_values = beta / se
        p_values = 2 * stats.t.sf(np.abs(t_values), dfs)
        holm, width = er1.holm_adjust(p_values), stats.t.ppf(.975, dfs) * se
        for i, variable in enumerate(columns):
            physical = design["physical_columns"][i]
            old_beta = float(primary_lookup[(code, physical)]["BETA"])
            coefficients.append({"CROP_CODE": code, "CROP": crop["crop"], "VARIABLE": variable,
                "SOURCE_COLUMN": ed1.FAMILIES[FAMILY][i % 3], "WINDOW": er1.window_for_variable(crop, variable),
                "BETA": float(beta[i]), "CR2_SE": float(se[i]), "SATTERTHWAITE_DF": float(dfs[i]),
                "T": float(t_values[i]), "P_TWO_SIDED": float(p_values[i]),
                "CI95_LOWER": float(beta[i] - width[i]), "CI95_UPPER": float(beta[i] + width[i]),
                "HOLM_P": float(holm[i]), "HOLM_FAMILY_SIZE": len(columns), "MULTIPLICITY": MULTIPLICITY,
                "CI_SEMANTICS": CI_SEMANTICS, "ER1_VARIABLE": physical, "ER1_BETA_REFERENCE": old_beta,
                "ER1_SIGN": int(np.sign(old_beta)), "R2_SIGN": int(np.sign(beta[i])),
                "SIGN_AGREEMENT": bool(np.sign(old_beta) == np.sign(beta[i])),
                "INTERPRETATION": INTERPRETATION, "PRIMARY_REPLACEMENT": "PROHIBITED",
                "EFFECTIVE_DF_FLAG": er1.effective_df_flag(crop["crop"], float(dfs[i]))})
            relations.append({"CROP_CODE": code, "VARIABLE": variable,
                **transformation_relation(design["primary"][physical].to_numpy(dtype=float), frame[variable].to_numpy(dtype=float))})
        joint.append({"CROP_CODE": code, "CROP": crop["crop"], "NULL": "=".join(columns) + "=0",
                      "NUMERATOR_DF": fit["aht"]["numerator_df"], "DENOMINATOR_DF": fit["aht"]["denominator_df"],
                      "F": fit["aht"]["f_statistic"], "P": fit["aht"]["p_value"], "METHOD": "CR2_AHT_HTZ"})
        samples[code] = {**design["sample"], "effective_districts": effective["effective_contributing_clusters"], "cluster_audit": effective}
        contracts[code] = design["contract"]
        sample_rows.append({"CROP_CODE": code, "CROP": crop["crop"], "N": len(frame),
            "NOMINAL_DISTRICTS": effective["nominal_clusters"], "EFFECTIVE_DISTRICTS": effective["effective_contributing_clusters"],
            "PERIODS": samples[code]["periods"], "KEY_COLUMNS": "UBIGEO|" + period,
            "ER1_KEY_SHA256": samples[code]["key_sha256"], "R2_KEY_SHA256": sha(json_bytes(keys(frame, period))),
            "ORDERED_KEYS_IDENTICAL": True, "Y_IDENTICAL": True, "FE_IDENTICAL": True,
            "OUTCOME_SHA256": samples[code]["outcome_sha256"], "MISSING_STANDARDIZED_X": 0,
            "ROWS_ADDED": 0, "ROWS_REMOVED": 0, "TRIMMING": False, "WINSORIZATION": False, "IMPUTATION": False})
    require(len(coefficients) == 21 and len(joint) == len(contracts) == 5,
            "ER2_R2_FAIL_FROZEN_CONTRACT", "5/21/5 inventory")
    verify_inputs()
    return {"preflight": pre, "standardization_provenance": provenance, "outcome_sources": sources,
            "coefficients": coefficients, "joint": joint, "sample_rows": sample_rows, "samples": samples,
            "contracts": contracts, "numerical_verification": verification, "relations": relations,
            "numerical_policy": NUMERICAL_POLICY, "runtime_versions": ed1.runtime_engine_versions(),
            "execution_sequence": ["FROZEN_INPUTS_VERIFIED", "ALL_FIVE_SAMPLES_VERIFIED", "PROVENANCE_WRITTEN_AND_READBACK_VERIFIED", "FIVE_R2_MODELS_ESTIMATED", "SECOND_PATH_VERIFIED", "UPSTREAM_HASHES_RECHECKED"],
            "verdict": PASS if all(v["status"] == "PASS" for v in verification.values()) else HOLD}


def report_text(data: dict, reproduction: dict) -> str:
    lines = ["# ER2 R2 Standardized-Anomaly Comparability v1", "", "FINAL_VERDICT=" + data["verdict"], "",
             "## Frozen authorization and predecessor", "", "R1_FREEZE_SHA=" + R1_SHA,
             "ER2P_FREEZE_SHA=" + r1.ER2P_SHA, "PREVIOUS_TIER_LOCK_SHA256=" + PREDECESSOR_SHA,
             "R2_TIER_CONTRACT_SHA256=" + TIER_SHA,
             "The new Director instruction authorizes R2 only. The predecessor lock itself does not authorize execution.", "",
             "## Standardization provenance audited before estimation", "",
             "The provenance CSV records all 21 exact source columns, frozen source hashes and upstream formula references.",
             "Monthly Z = (district-month climate - 1991-2020 district/calendar-month mean) / the corresponding sample SD (ddof=1, 30 annual values).",
             "All frozen reference scales are positive. R2 reads existing frozen exposures; it does not recalculate Z-scores or use Y, residuals or results to select a reference population.",
             "Perennial exposures average monthly Z over the frozen window. E1 transient exposures first average monthly Z per cohort, then use positive observed unambiguously assigned SIEMBRA weights.",
             "The final window/cohort exposure is not asserted to have unit SD in the analytical sample. A unit is defined by the upstream local monthly climate standardization and aggregation, not by a newly calculated sample SD.", "",
             "R2_STANDARDIZATION_RECOMPUTED=FALSE", "INTERPRETATION=" + INTERPRETATION, "",
             "## Exact sample and model architecture", "",
             *r1.markdown_table(data["sample_rows"], ["CROP", "N", "NOMINAL_DISTRICTS", "EFFECTIVE_DISTRICTS", "PERIODS", "ORDERED_KEYS_IDENTICAL", "Y_IDENTICAL", "FE_IDENTICAL"]), "",
             "Ordered keys are checked against the unchanged ER1 construction and the ER1 key records committed in R1. No row deletion, addition, trimming, winsorization, imputation or campaign redefinition.",
             "Unweighted linear additive yield-level TM/ha models retain district and period FE and district-clustered CR2/Satterthwaite inference. Lemon and Banana retain a single joint t plus t-1 model each.", "",
             "## All 21 R2 coefficient results", "",
             *r1.markdown_table(data["coefficients"], ["CROP", "VARIABLE", "WINDOW", "BETA", "CR2_SE", "SATTERTHWAITE_DF", "T", "P_TWO_SIDED", "CI95_LOWER", "CI95_UPPER", "HOLM_P"]), "",
             "Intervals are unadjusted 95% CR2/Satterthwaite intervals. Holm is applied separately to 3, 3, 3, 6 and 6 R2 coefficient p-values. No adjusted confidence intervals or global 21-coefficient FWER claim.", "",
             "## Five complete crop-level AHT/HTZ tests", "",
             *r1.markdown_table(data["joint"], ["CROP", "NULL", "NUMERATOR_DF", "DENOMINATOR_DF", "F", "P"]), "",
             "## ER1 versus R2 descriptive signs", "",
             *r1.markdown_table(data["coefficients"], ["CROP", "ER1_VARIABLE", "VARIABLE", "ER1_BETA_REFERENCE", "BETA", "ER1_SIGN", "R2_SIGN", "SIGN_AGREEMENT"]), "",
             "These are descriptive sign comparisons. Physical and standardized predictor units differ; raw beta magnitudes are not same-unit comparisons. No percentage improvement, significance voting, selected coefficient or primary replacement.", "",
             "## Exposure-only transformation diagnostic", "",
             *r1.markdown_table(data["relations"], ["CROP_CODE", "VARIABLE", "STANDARDIZATION_RELATION_TO_PHYSICAL_ANOMALY", "PROJECTION_RELATIVE_L2_RESIDUAL"]), "",
             "The positive-scalar diagnostic is a projection of frozen Z onto frozen physical X through the origin, without Y. Its 128*epsilon source-representation bound is fixed before results; it never cancels or changes R2.", "",
             "## Interpretation and execution firewalls", "",
             "Y_STANDARDIZED=FALSE", "FULLY_STANDARDIZED_EFFECT=FALSE",
             "CROSS_CROP_COEFFICIENT_MAGNITUDE_RANKING=NOT_AUTHORIZED", "CROSS_CROP_SIGNIFICANCE_RANKING=NOT_AUTHORIZED",
             "Associations remain in crop-specific native TM/ha units. There is no causal claim, cross-crop sensitivity ranking or vulnerability ranking.",
             "R3-R6, bootstrap, Conley, LOO, B3, scenarios, GVP, VaR/CVaR, A1/A2 and optimization are NOT_EXECUTED. The R3 adapter is not implemented.",
             "NEXT_TIER_AUTHORIZATION_STATUS=NOT_AUTHORIZED", "",
             "## Numerical verification", "",
             "Frozen ED1 main and independent full-design SVD paths reproduce beta, CR2 covariance, coefficient-specific df and complete AHT. The frozen R1A envelope was adopted before R2 fits: beta relative L2 <=1e-10; covariance Frobenius, df L2/componentwise and AHT relative errors <=1e-6. Full-rank and zero extra CR2 singularities must agree.",
             "The lock preserves all absolute discrepancies and the unchanged ED1 absolute 1e-8 alarm separately. No solver, engine or tolerance is changed after results."]
    for code, value in data["numerical_verification"].items():
        lines.extend(["", code + ": " + value["status"] + "; ED1 absolute alarm=" + value["ed1_strict_absolute_1e_8_alarm"],
                      "Absolute: " + json.dumps(value["absolute_discrepancies"], sort_keys=True),
                      "Relative: " + json.dumps(value["scale_aware"]["metrics"], sort_keys=True)])
    lines.extend(["", "## Limitations", "",
                  "Finite district clusters, coefficient-specific effective degrees of freedom, conditional transient cohort support and observational associations remain limitations. Nonsignificance or a sign change is not failure of the R2 execution gate.", "",
                  "## Two-run byte reproduction", "", "R2_TWO_RUN_REPRODUCIBILITY=" + reproduction["status"],
                  "Two separate Python worker processes each write and verify the provenance audit before fitting. Their complete serialized calculations and provenance bytes are compared, then both rendered output packages must match before publication.",
                  "UTF-8, LF only, no BOM, exactly one final LF, no timestamps or absolute local paths. The lock hash is computed externally; no circular self-hash.", "",
                  "## Exact next action", "", "RETURN_TO_SCIENTIFIC_DIRECTOR_FOR_R2_REVIEW", "R3_AUTHORIZATION_STATUS=NOT_AUTHORIZED"])
    return "\n".join(lines) + "\n"


def render(data: dict, reproduction: dict) -> dict[Path, bytes]:
    payloads = {RESULTS_REL: csv_bytes(data["coefficients"]), JOINT_REL: csv_bytes(data["joint"]),
                SAMPLE_REL: csv_bytes(data["sample_rows"]), PROVENANCE_REL: csv_bytes(data["standardization_provenance"]),
                REPORT_REL: report_text(data, reproduction).encode("utf-8")}
    lock = {"schema_version": "1.0.0", "project": "ENSO_EL_NINO_2026_2027_AGRICULTURE_PIURA",
            "gate": "ER2_R2_STANDARDIZED_ANOMALY_COMPARABILITY_EXECUTION_V1", "tier_id": TIER_ID, "tier_order": 2,
            "tier_contract_sha256": TIER_SHA, "frozen_r2_tier_contract": data["preflight"]["tier_contract"],
            "r1_freeze_sha": R1_SHA, "r1_status": "PASS_FROZEN", "er2p_freeze_sha": r1.ER2P_SHA,
            "er1_freeze_sha": er2p.ER1_SHA, "ed1_freeze_sha": er2p.ED1_SHA,
            "er1_numerical_results_identity": er2p.NUMERICAL_IDENTITY,
            "previous_tier_lock_sha256": PREDECESSOR_SHA, "certified_r1_predecessor_lock_sha256": PREDECESSOR_SHA,
            "preflight": data["preflight"], "exact_frozen_input_sha256": data["preflight"]["exact_input_sha256"],
            "standardization_provenance": data["standardization_provenance"], "standardization_recomputed": False,
            "exact_model_contracts": data["contracts"], "sample_identity": data["samples"],
            "coefficient_inventory": data["coefficients"], "aht_joint_tests": data["joint"],
            "models": 5, "coefficients": 21, "aht_tests": 5,
            "multiplicity": MULTIPLICITY, "confidence_intervals": CI_SEMANTICS,
            "multiplicity_adjusted_confidence_intervals": "NOT_CONSTRUCTED_NOT_CLAIMED", "global_fwer": "NOT_CLAIMED",
            "interpretation": INTERPRETATION, "interpretation_and_execution_firewall": FIREWALL,
            "standardization_relation_diagnostic": data["relations"], "outcome_provenance": data["outcome_sources"],
            "numerical_policy": data["numerical_policy"], "independent_numerical_verification": data["numerical_verification"],
            "reproducibility": reproduction, "execution_sequence": data["execution_sequence"],
            "runtime_versions": data["runtime_versions"], "r2_calculations_complete": True,
            "artifact_sha256": {p.as_posix(): sha(b) for p,b in payloads.items()},
            "implementation_sha256": sha((ROOT / SCRIPT_REL).read_bytes()), "test_sha256": sha((ROOT / TEST_REL).read_bytes()),
            "completion_status": data["verdict"],
            "scientific_lock_status": "RESULTS_LOCKED_PENDING_DIRECTOR_REVIEW" if data["verdict"] == PASS else "HOLD_NUMERICAL_ADJUDICATION_REQUIRED",
            "NEXT_TIER_AUTHORIZATION_STATUS": "NOT_AUTHORIZED", "next_action": "RETURN_TO_SCIENTIFIC_DIRECTOR_FOR_R2_REVIEW"}
    payloads[LOCK_REL] = json_bytes(lock)
    return payloads


def require_byte_contract(payload: bytes) -> None:
    payload.decode("utf-8", errors="strict")
    require(not payload.startswith(b"\xef\xbb\xbf") and b"\r" not in payload
            and payload.endswith(b"\n") and not payload.endswith(b"\n\n"),
            "ER2_R2_FAIL_FROZEN_CONTRACT", "UTF-8/LF byte contract")


def write_exact(path: Path, payload: bytes) -> None:
    require_byte_contract(payload)
    if path.exists():
        require(path.read_bytes() == payload, "ER2_R2_FAIL_FROZEN_CONTRACT", "refusing to overwrite different candidate")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def check_destination(destination: Path, worker: bool = False) -> Path:
    destination = destination.resolve()
    permitted = not destination.is_relative_to(ROOT) or (destination == ROOT and not worker)
    require(permitted,
            "ER2_R2_FAIL_FROZEN_CONTRACT", "nested repository output root prohibited")
    return destination


def worker(destination: Path) -> None:
    destination = check_destination(destination, worker=True)
    pre = preflight()
    designs, sources = prepare_designs()
    provenance = standardization_provenance(designs)
    payload = csv_bytes(provenance)
    write_exact(destination / PROVENANCE_REL, payload)
    require((destination / PROVENANCE_REL).read_bytes() == payload,
            "ER2_R2_FAIL_STANDARDIZED_EXPOSURE_PROVENANCE", "pre-estimation audit readback")
    data = calculate(pre, designs, provenance, sources)
    write_exact(destination / "calculation.json", json_bytes(data))


def build(destination: Path, live_remote: bool = False) -> dict:
    require(not (ROOT / LOCK_REL).exists(), REPORTING_FAIL, "R2 re-estimation prohibited after initial results lock")
    destination = check_destination(destination)
    preflight(live_remote)
    with tempfile.TemporaryDirectory(prefix="er2-r2-two-run-") as directory:
        roots = [Path(directory) / name for name in ("run1", "run2")]
        for root in roots:
            subprocess.run([sys.executable, str(ROOT / SCRIPT_REL), "--worker", "--output-root", str(root)], cwd=ROOT, check=True)
        raw = [(root / "calculation.json").read_bytes() for root in roots]
        provenance = [(root / PROVENANCE_REL).read_bytes() for root in roots]
        require(raw[0] == raw[1] and provenance[0] == provenance[1], HOLD, "two independent worker bytes differ")
        reproduction = {"status": "PASS", "independent_processes": 2,
                        "calculation_run1_sha256": sha(raw[0]), "calculation_run2_sha256": sha(raw[1]),
                        "provenance_run1_sha256": sha(provenance[0]), "provenance_run2_sha256": sha(provenance[1]),
                        "serialized_calculations_byte_identical": True, "all_rendered_outputs_byte_identical": True,
                        "input_environment_unchanged": True, "standardization_recomputed": False}
        rendered = [render(json.loads(value), reproduction) for value in raw]
        require(rendered[0] == rendered[1], HOLD, "two rendered packages differ")
        require(rendered[0][PROVENANCE_REL] == provenance[0],
                "ER2_R2_FAIL_STANDARDIZED_EXPOSURE_PROVENANCE", "published audit differs from pre-estimation audit")
        verify_inputs()
        for rel, payload in rendered[0].items():
            write_exact(destination / rel, payload)
    return {"verdict": json.loads(rendered[0][LOCK_REL])["completion_status"],
            "artifact_sha256": {p.as_posix(): sha(b) for p,b in rendered[0].items()}, "reproducibility": reproduction}


def protected_r2_identity() -> dict:
    actual = {p.as_posix(): sha((ROOT / p).read_bytes()) for p in PROTECTED_R2_HASHES}
    require(actual == {p.as_posix(): h for p,h in PROTECTED_R2_HASHES.items()},
            "ER2_R2R_FAIL_NUMERICAL_OR_PROVENANCE_DRIFT")
    return actual


def initial_report_data(initial: dict) -> dict:
    sample_rows = list(csv.DictReader(io.StringIO((ROOT / SAMPLE_REL).read_text(encoding="utf-8"))))
    for row in sample_rows:
        for field in ("N", "NOMINAL_DISTRICTS", "EFFECTIVE_DISTRICTS", "PERIODS"):
            row[field] = int(row[field])
        for field in ("ORDERED_KEYS_IDENTICAL", "Y_IDENTICAL", "FE_IDENTICAL"):
            row[field] = row[field] == "TRUE"
    return {"verdict": initial["completion_status"], "coefficients": initial["coefficient_inventory"],
            "joint": initial["aht_joint_tests"], "sample_rows": sample_rows,
            "relations": initial["standardization_relation_diagnostic"],
            "numerical_verification": initial["independent_numerical_verification"]}


def reporting_semantics(initial: dict) -> dict:
    coefficients, joint = initial["coefficient_inventory"], initial["aht_joint_tests"]
    require((initial["models"], len(coefficients), len(joint)) == (5, 21, 5), REPORTING_FAIL, "5/21/5 inventory")
    for rel, rows in ((RESULTS_REL, coefficients), (JOINT_REL, joint), (PROVENANCE_REL, initial["standardization_provenance"])):
        require(csv_bytes(rows) == (ROOT / rel).read_bytes(), "ER2_R2R_FAIL_NUMERICAL_OR_PROVENANCE_DRIFT", "CSV/initial-lock identity")
    require(all(v["STANDARDIZATION_RELATION_TO_PHYSICAL_ANOMALY"] == "LOCALLY_VARYING_STANDARDIZATION_TRANSFORMATION"
                for v in initial["standardization_relation_diagnostic"])
            and len(initial["standardization_relation_diagnostic"]) == 21, REPORTING_FAIL, "relation inventory")
    changes = [r for r in coefficients if not r["SIGN_AGREEMENT"]]
    survivors = [r for r in coefficients if r["HOLM_P"] < .05]
    require(len(changes) == 12 and len(coefficients) - len(changes) == 9, REPORTING_FAIL, "sign inventory")
    require([(r["CROP_CODE"], r["VARIABLE"]) for r in survivors] == [("15010040000", "RAIN_Z__T_MINUS_1")], REPORTING_FAIL, "Holm survivor inventory")
    require((survivors[0]["BETA"], survivors[0]["P_TWO_SIDED"], survivors[0]["HOLM_P"])
            == (-6.712270305566657, 0.0008485894443823592, 0.005091536666294155), REPORTING_FAIL, "survivor values")
    require({r["CROP_CODE"]: r["P"] for r in joint} == EXPECTED_AHT_P, REPORTING_FAIL, "five AHT p-values")
    require(initial["interpretation"] == INTERPRETATION and not initial["standardization_recomputed"], REPORTING_FAIL, "historical interpretation/source")
    primary_rows = list(csv.DictReader(io.StringIO((ROOT / er1.COEFFICIENTS_REL).read_text(encoding="utf-8"))))
    primary_banana = [r for r in primary_rows if r["CROP_CODE"] == "15010040000"]
    primary_survivors = [r for r in primary_banana if float(r["HOLM_ADJUSTED_P_VALUE"]) < .05]
    require([r["CLIMATE_VARIABLE"] for r in primary_survivors] == ["TMIN_ANOM_C__T_MINUS_1"], REPORTING_FAIL, "historical ER1 Banana component")
    aht = [{**r, "P_LT_0_05": r["P"] < .05,
            "WITHIN_CROP_HOLM_SURVIVORS": sum(v["CROP_CODE"] == r["CROP_CODE"] for v in survivors)} for r in joint]
    return {"R2_NUMERICAL_RESULT_CHANGE": False, "R2_SAMPLE_CHANGE": False, "R2_STANDARDIZATION_CHANGE": False,
            "R2_MODEL_CHANGE": False, "R2_MODELS_REESTIMATED_DURING_R2R": 0,
            "R2_NUMERICAL_RESULTS": "PASS", "R2_FREEZE_AUTHORIZED": "NO", "R2_REPORTING_SEMANTICS_HARDENED": True,
            "MONTHLY_FORMULA": MONTHLY_FORMULA, "REFERENCE_PERIOD": "1991-2020", "REFERENCE_ANNUAL_VALUES": 30,
            "SAMPLE_SD_DDOF": 1, "OUTCOME_BASED_SELECTION": False, "R2_STANDARDIZATION_RECOMPUTED": False,
            "PERENNIAL_FINAL_R2_X": "ARITHMETIC_MEAN_OF_MONTHLY_LOCAL_Z_WITHIN_FROZEN_WINDOW",
            "TRANSIENT_FINAL_R2_X": "MONTHLY_LOCAL_Z_TO_COHORT_WINDOW_MEAN_Z_TO_POSITIVE_OBSERVED_UNAMBIGUOUS_SIEMBRA_WEIGHTED_AGGREGATION",
            "MONTHLY_COMPONENTS_STANDARDIZED_LOCALLY": True,
            "FINAL_ANALYTICAL_EXPOSURE_STANDARD_DEVIATION_EQUALS_ONE": "NOT_CLAIMED",
            "FINAL_ANALYTICAL_X_UNIT_SD_CLAIMED": False, "ED1_ORIGINAL_INTERPRETATION_LABEL": INTERPRETATION,
            "R2R_CORRECTED_INTERPRETATION": CORRECTED_INTERPRETATION,
            "HUMAN_INTERPRETATION": HUMAN_INTERPRETATION, "INDEX_CLARIFICATION": INDEX_CLARIFICATION,
            "R2R_REPORTING_CLARIFICATION": REPORTING_CLARIFICATION,
            "Y_STANDARDIZED": False, "FULLY_STANDARDIZED_EFFECT": False,
            "CROSS_CROP_EFFECT_SIZE_COMPARABILITY": "NOT_AUTHORIZED",
            "CROSS_CROP_COEFFICIENT_MAGNITUDE_RANKING": "NOT_AUTHORIZED", "CROSS_CROP_SIGNIFICANCE_RANKING": "NOT_AUTHORIZED",
            "STANDARDIZATION_RELATION_COUNT": 21, "STANDARDIZATION_RELATION": "LOCALLY_VARYING_STANDARDIZATION_TRANSFORMATION",
            "GLOBAL_POSITIVE_SCALAR_REEXPRESSION_OF_ER1": False,
            "SIGN_T_STATISTIC_P_VALUE_INVARIANCE": "NOT_EXPECTED",
            "ER1_R2_SIGN_CHANGES": 12, "ER1_R2_SIGN_AGREEMENTS": 9,
            "SIGN_CHANGE_INTERPRETATION": "EXPOSURE_DEFINITION_SENSITIVITY_DESCRIPTIVE_ONLY",
            "HOLM_THRESHOLD": .05, "HOLM_MULTIPLICITY": MULTIPLICITY, "HOLM_SURVIVORS": survivors,
            "AHT_CERTIFICATION": aht, "AHT_P_ADJUSTMENT": "NONE", "CROSS_CROP_AHT_MULTIPLICITY_FAMILY": "NOT_AUTHORIZED",
            "MANGO_LEMON_JOINT_WITHOUT_INDIVIDUAL_HOLM": True,
            "BANANA_INDIVIDUAL_HOLM_WITHOUT_JOINT_AHT_AT_0_05": True,
            "JOINT_INDIVIDUAL_DISTINCTION": "DIFFERENT_NULL_HYPOTHESES_NOT_LOGICALLY_CONTRADICTORY",
            "ER1_BANANA_INDIVIDUAL_COMPONENT": "TMIN_ANOM_C__T_MINUS_1",
            "R2_BANANA_HOLM_SURVIVING_COMPONENT": "RAIN_Z__T_MINUS_1",
            "BANANA_ALLOWED_STATEMENT": BANANA_COMPONENT_STATEMENT,
            "SAME_BANANA_CHANNEL_ROBUSTLY_CONFIRMED": "PROHIBITED",
            "PRIMARY_SPECIFICATION": "ER1_PHYSICAL_ANOMALY", "R2_ROLE": "SECONDARY_STANDARDIZED_EXPOSURE_SENSITIVITY",
            "PRIMARY_REPLACEMENT": "PROHIBITED", "NEXT_TIER_AUTHORIZATION_STATUS": "NOT_AUTHORIZED",
            "EXECUTION_FIREWALL": {**FIREWALL, "R2_REESTIMATION": "PROHIBITED"}}


def reporting_basis() -> dict:
    protected = protected_r2_identity()
    verify_inputs()
    initial = json.loads((ROOT / LOCK_REL).read_bytes())
    require(initial["artifact_sha256"][REPORT_REL.as_posix()] == INITIAL_REPORT_SHA
            and initial["implementation_sha256"] == INITIAL_SCRIPT_SHA and initial["test_sha256"] == INITIAL_TEST_SHA,
            REPORTING_FAIL, "initial manifest references")
    original_report = report_text(initial_report_data(initial), initial["reproducibility"])
    require(sha(original_report.encode("utf-8")) == INITIAL_REPORT_SHA, REPORTING_FAIL, "original report reconstruction without fitting")
    return {"original_report": original_report, "semantics": reporting_semantics(initial),
            "protected_sha256": protected, "upstream_sha256": initial["exact_frozen_input_sha256"],
            "sample_identity_sha256": sha(json_bytes(initial["sample_identity"])),
            "model_contracts_sha256": sha(json_bytes(initial["exact_model_contracts"])),
            "coefficient_inventory_sha256": sha(json_bytes(initial["coefficient_inventory"])),
            "aht_inventory_sha256": sha(json_bytes(initial["aht_joint_tests"])),
            "implementation_sha256": sha((ROOT / SCRIPT_REL).read_bytes()), "test_sha256": sha((ROOT / TEST_REL).read_bytes())}


def reporting_reproduction(basis: dict) -> dict:
    identity = sha(json_bytes(basis))
    return {"status": "PASS", "independent_processes": 2, "run1_basis_sha256": identity, "run2_basis_sha256": identity,
            "corrected_report_byte_identical": True, "reporting_lock_byte_identical": True,
            "r2_models_reestimated": 0, "protected_files_rewritten": 0}


def render_reporting(basis: dict, reproduction: dict) -> dict[Path, bytes]:
    semantics = basis["semantics"]
    replacements = {
        "FINAL_VERDICT=" + PASS: "R2_INITIAL_EXECUTION_VERDICT=" + PASS + "\nFINAL_VERDICT=" + REPORTING_PASS,
        "The new Director instruction authorizes R2 only. The predecessor lock itself does not authorize execution.":
            "The original Director instruction authorized R2 execution. R2R authorizes reporting clarification only, with no re-estimation and no further tier execution.",
        "INTERPRETATION=" + INTERPRETATION:
            "ED1_ORIGINAL_INTERPRETATION_LABEL=" + INTERPRETATION + "\nR2R_CORRECTED_INTERPRETATION=" + CORRECTED_INTERPRETATION,
        "## Two-run byte reproduction": "## Original R2 numerical reproduction (retained evidence; not rerun by R2R)",
        "RETURN_TO_SCIENTIFIC_DIRECTOR_FOR_R2_REVIEW": "RETURN_TO_SCIENTIFIC_DIRECTOR_FOR_R2_FREEZE_DECISION_IF_PASS",
    }
    old_lines = basis["original_report"].splitlines()
    require(all(old_lines.count(line) == 1 for line in replacements), REPORTING_FAIL, "targeted report replacements")
    lines = [replacements.get(line, line) for line in old_lines]
    lines.extend(["", "## R2R reporting certification", "", "R2_INITIAL_RESULTS_LOCK_SHA256=" + INITIAL_LOCK_SHA,
                  "ORIGINAL_CANONICAL_REPORT_SHA256=" + INITIAL_REPORT_SHA,
                  "R2_NUMERICAL_RESULTS=PASS", "R2_FREEZE_AUTHORIZED=NO", "R2_MODELS_REESTIMATED_DURING_R2R=0",
                  "The original results lock and all four numerical/sample/provenance CSV files remain byte-identical. Their historical shorthand is retained as lineage, not silently relabeled as the corrected reporting interpretation.",
                  "The original lock continues to reference the original report and implementation hashes. This separate reporting certification does not overwrite or recertify those historical references as current bytes.", "",
                  "### Exact monthly and aggregation definitions", "", MONTHLY_FORMULA,
                  "Reference population: each district x calendar-month, 1991-2020, 30 annual values; sample SD ddof=1. No outcome-based selection and no R2 recomputation.",
                  "PERENNIAL_FINAL_R2_X=" + semantics["PERENNIAL_FINAL_R2_X"],
                  "TRANSIENT_FINAL_R2_X=" + semantics["TRANSIENT_FINAL_R2_X"],
                  "MONTHLY_COMPONENTS_STANDARDIZED_LOCALLY=TRUE",
                  "FINAL_ANALYTICAL_EXPOSURE_STANDARD_DEVIATION_EQUALS_ONE=NOT_CLAIMED",
                  "FINAL_ANALYTICAL_X_UNIT_SD_CLAIMED=FALSE", "", HUMAN_INTERPRETATION, INDEX_CLARIFICATION,
                  "A one-unit increase in final R2 X is not claimed to equal one empirical standard deviation of the final crop/window analytical exposure.",
                  "R2R_REPORTING_CLARIFICATION=" + REPORTING_CLARIFICATION, "",
                  "### Transformation and sign-change interpretation", "",
                  "All 21 relationships remain LOCALLY_VARYING_STANDARDIZATION_TRANSFORMATION. R2 is not a global positive scalar re-expression of ER1. Sign, t-statistic and p-value invariance are therefore not expected.",
                  "ER1_R2_SIGN_CHANGES=12", "ER1_R2_SIGN_AGREEMENTS=9",
                  "SIGN_CHANGE_INTERPRETATION=EXPOSURE_DEFINITION_SENSITIVITY_DESCRIPTIVE_ONLY",
                  "The 12 sign changes are descriptive sensitivity evidence, not robustness failures, a refutation of either specification or evidence that the standardized specification is superior.", "",
                  "### Complete individual Holm certification", "",
                  "Exactly one of all 21 R2 coefficients survives its prespecified within-crop Holm family at p < 0.05:",
                  *r1.markdown_table(semantics["HOLM_SURVIVORS"], ["CROP", "VARIABLE", "BETA", "P_TWO_SIDED", "HOLM_P"]),
                  "No other coefficient survives within-crop R2 Holm at 0.05. All 21 original coefficient rows and Holm p-values above are unchanged.", "",
                  "### Five AHT classifications and distinct hypotheses", "",
                  *r1.markdown_table(semantics["AHT_CERTIFICATION"], ["CROP", "NUMERATOR_DF", "DENOMINATOR_DF", "F", "P", "P_LT_0_05", "WITHIN_CROP_HOLM_SURVIVORS"]),
                  "AHT p-values are unchanged and unadjusted. No Holm adjustment to the five AHT tests and no new cross-crop AHT multiplicity family is authorized.",
                  "Mango and Lemon show crop-level joint AHT evidence under R2, while no individual Mango/Lemon coefficient survives within-crop Holm.",
                  "Banana shows one individual coefficient surviving within-crop Holm while its six-coefficient crop AHT has p > 0.05.",
                  "These outcomes are not logically contradictory: the complete climate-block null and individual-coefficient nulls with within-crop multiplicity control are different hypotheses and inference procedures.", "",
                  "### Banana component and primary-specification firewalls", "",
                  "ER1's strongest individual Banana signal is lagged Tmin; R2's sole Holm-surviving individual Banana signal is lagged rainfall. This is not confirmation of the same component.",
                  "BANANA_ALLOWED_STATEMENT=" + BANANA_COMPONENT_STATEMENT,
                  "SAME_BANANA_CHANNEL_ROBUSTLY_CONFIRMED=PROHIBITED",
                  "PRIMARY_SPECIFICATION=ER1_PHYSICAL_ANOMALY", "R2_ROLE=SECONDARY_STANDARDIZED_EXPOSURE_SENSITIVITY",
                  "Y_STANDARDIZED=FALSE", "FULLY_STANDARDIZED_EFFECT=FALSE", "CROSS_CROP_EFFECT_SIZE_COMPARABILITY=NOT_AUTHORIZED",
                  "No cross-crop coefficient/significance ranking or significance-based replacement of ER1 is authorized.", "",
                  "### Reporting-only reproduction and next action", "", "R2R_TWO_RUN_REPRODUCIBILITY=" + reproduction["status"],
                  "Two separate processes independently read the same immutable results and construct the reporting basis. Corrected report and reporting-lock bytes must match before publication. No model or numerical verification is rerun.",
                  "R2_NUMERICAL_RESULT_CHANGE=FALSE", "R2_SAMPLE_CHANGE=FALSE", "R2_STANDARDIZATION_CHANGE=FALSE", "R2_MODEL_CHANGE=FALSE",
                  "R2_REPORTING_SEMANTICS_HARDENED=TRUE", "NEXT_TIER_AUTHORIZATION_STATUS=NOT_AUTHORIZED",
                  "R3-R6 remain unauthorized and unexecuted. No adapter, bootstrap, Conley, LOO, B3, scenario, GVP, VaR/CVaR, A1/A2 or optimization execution.",
                  "RETURN_TO_SCIENTIFIC_DIRECTOR_FOR_R2_FREEZE_DECISION_IF_PASS"])
    report = ("\n".join(lines) + "\n").encode("utf-8")
    certified = {"schema_version": "1.0.0", "project": "ENSO_EL_NINO_2026_2027_AGRICULTURE_PIURA",
                 "gate": "ER2_R2R_REPORTING_INTERPRETATION_HARDENING_V1", "status": "REPORTING_CERTIFIED_PENDING_DIRECTOR_FREEZE_DECISION",
                 "final_verdict": REPORTING_PASS, "R2_INITIAL_RESULTS_LOCK_SHA256": INITIAL_LOCK_SHA,
                 "original_report_sha256": INITIAL_REPORT_SHA, "original_implementation_sha256": INITIAL_SCRIPT_SHA,
                 "original_test_sha256": INITIAL_TEST_SHA, "immutable_r2_sha256": basis["protected_sha256"],
                 "unchanged_upstream_sha256": basis["upstream_sha256"], "r1_freeze_sha": R1_SHA,
                 "er1_freeze_sha": er2p.ER1_SHA, "er2p_freeze_sha": r1.ER2P_SHA,
                 "previous_tier_lock_sha256": PREDECESSOR_SHA, "r2_tier_contract_sha256": TIER_SHA,
                 "models_preserved": 5, "coefficients_preserved": 21, "aht_tests_preserved": 5,
                 **{k:v for k,v in basis.items() if k.endswith("_sha256") and k not in ("protected_sha256", "upstream_sha256")},
                 **semantics, "corrected_report_sha256": sha(report), "reproducibility": reproduction,
                 "next_action": "RETURN_TO_SCIENTIFIC_DIRECTOR_FOR_R2_FREEZE_DECISION_IF_PASS"}
    return {REPORT_REL: report, REPORTING_LOCK_REL: json_bytes(certified)}


def reporting_preflight(live_remote: bool = False) -> dict:
    protected_r2_identity()
    pre = preflight(live_remote)
    basis = reporting_basis()
    expected = render_reporting(basis, reporting_reproduction(basis))
    require(sha((ROOT / REPORT_REL).read_bytes()) in (INITIAL_REPORT_SHA, sha(expected[REPORT_REL])),
            REPORTING_FAIL, "unrecognized report bytes")
    if (ROOT / REPORTING_LOCK_REL).exists():
        require((ROOT / REPORTING_LOCK_REL).read_bytes() == expected[REPORTING_LOCK_REL], REPORTING_FAIL, "reporting lock drift")
    return pre


def reporting_worker(destination: Path) -> None:
    destination = check_destination(destination, worker=True)
    reporting_preflight()
    write_exact(destination / "reporting_basis.json", json_bytes(reporting_basis()))


def build_reporting(destination: Path, live_remote: bool = False) -> dict:
    destination = check_destination(destination)
    reporting_preflight(live_remote)
    with tempfile.TemporaryDirectory(prefix="er2-r2r-two-run-") as directory:
        roots = [Path(directory) / name for name in ("run1", "run2")]
        for root in roots:
            subprocess.run([sys.executable, str(ROOT / SCRIPT_REL), "--reporting-worker", "--output-root", str(root)], cwd=ROOT, check=True)
        raw = [(root / "reporting_basis.json").read_bytes() for root in roots]
        require(raw[0] == raw[1], REPORTING_FAIL, "independent reporting bases differ")
        reproduction = reporting_reproduction(json.loads(raw[0]))
        rendered = [render_reporting(json.loads(b), reproduction) for b in raw]
        require(rendered[0] == rendered[1], REPORTING_FAIL, "report/reporting-lock byte mismatch")
        protected_r2_identity()
        for rel, payload in rendered[0].items():
            path = destination / rel
            if path.exists() and path.read_bytes() != payload:
                require(rel == REPORT_REL and sha(path.read_bytes()) == INITIAL_REPORT_SHA,
                        REPORTING_FAIL, "only initial report may be replaced")
                require_byte_contract(payload)
                path.write_bytes(payload)
            else:
                write_exact(path, payload)
    protected_r2_identity()
    verify_inputs()
    return {"verdict": REPORTING_PASS, "artifact_sha256": {p.as_posix(): sha(b) for p,b in rendered[0].items()},
            "protected_sha256": protected_r2_identity(), "reproducibility": reproduction, "r2_models_reestimated": 0}


def main() -> int:
    parser = argparse.ArgumentParser(description="R2R reporting-only hardening from immutable R2 results; no estimation or Git writes.")
    parser.add_argument("--output-root", type=Path, default=ROOT)
    parser.add_argument("--live-remote", action="store_true")
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--reporting-worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.preflight_only:
        print(json_bytes(reporting_preflight(args.live_remote)).decode("utf-8"), end="")
        return 0
    if args.worker:
        raise RuntimeError(REPORTING_FAIL + ": R2 numerical worker prohibited during R2R")
    if args.reporting_worker:
        reporting_worker(args.output_root)
        return 0
    result = build_reporting(args.output_root, args.live_remote)
    print(json_bytes(result).decode("utf-8"), end="")
    return 0 if result["verdict"] == REPORTING_PASS else 1


if __name__ == "__main__":
    raise SystemExit(main())
