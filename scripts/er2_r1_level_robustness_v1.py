from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import er1_primary_real_estimation_v1 as er1
import er2_robustness_protocol_v1 as er2p

ed1 = er1.ed1
ER2P_SHA = "3fd1f657e79d7e0ae93903239fd3690dcade56a4"
ER2P_BRANCH = "phase/er2p-robustness-protocol-v1"
ER2P_TAG = "er2p-robustness-protocol-v1-freeze"
PROTOCOL_SHA = "13519fb5c86fdf690d233c54dd45c3242ba348f3c7f66587238e6965ed1c49ff"
PROTOCOL_HASHES = {
    er2p.CONFIG_REL.as_posix(): PROTOCOL_SHA,
    er2p.REPORT_REL.as_posix(): "a8148dae123b8699f7451885d2e029d3c06d21110fea0b9917d31c326c9a2aa3",
    er2p.TIERS_REL.as_posix(): "2ff57eadb872ca6aa10cb84aa4fdf9b7250715df5ca77d2f3e9d22621e7d762a",
    er2p.SCRIPT_REL.as_posix(): "9e95512e292bdfb85105401b8783542677ece785897a0c63a7e767f5b8c6fc41",
    er2p.TEST_REL.as_posix(): "b2f698b6eda6c3eeaabd887f2d1df6b4a948e54f02a2ea096ac93f549d91296f",
}
FROZEN_HASHES = {**er1.FROZEN_HASHES, **er2p.FROZEN_HASHES, **PROTOCOL_HASHES}
SCRIPT_REL = Path("scripts/er2_r1_level_robustness_v1.py")
TEST_REL = Path("tests/test_er2_r1_level_robustness_v1.py")
RESULTS_REL = Path("outputs/econometrics/ER2_R1_LEVEL_RESULTS.csv")
JOINT_REL = Path("outputs/econometrics/ER2_R1_LEVEL_JOINT_TESTS.csv")
EQUIVALENCE_REL = Path("outputs/econometrics/ER2_R1_PERENNIAL_EQUIVALENCE.csv")
REPORT_REL = Path("outputs/econometrics/ER2_R1_REPORT.md")
LOCK_REL = Path("outputs/econometrics/ER2_R1_RESULTS_LOCK.json")
OUTPUT_RELS = (RESULTS_REL, JOINT_REL, EQUIVALENCE_REL, REPORT_REL, LOCK_REL)
CANDIDATE_RELS = (*OUTPUT_RELS, SCRIPT_REL, TEST_REL)
LEVEL = ("RAIN_MM", "TMAX_C", "TMIN_C")
ANOMALY = ("RAIN_ANOM_MM", "TMAX_ANOM_C", "TMIN_ANOM_C")
TOLERANCE = 1e-9
VERIFICATION_TOLERANCE = 1e-8
PASS = "ER2_R1_PASS_RESULTS_LOCKED_READY_FOR_DIRECTOR_REVIEW"
HOLD = "ER2_R1_HOLD_PERENNIAL_EQUIVALENCE_ADJUDICATION"
NUMERICAL_FAIL = "ER2_R1_FAIL_NUMERICAL_VERIFICATION"
MULTIPLICITY = "HOLM_STEP_DOWN_WITHIN_CROP_R1_COEFFICIENT_P_VALUES"
CI_SEMANTICS = "UNADJUSTED_95_PERCENT_CR2_SATTERTHWAITE"
FIREWALL = {
    **{f"R{i}": "NOT_EXECUTED" for i in range(2, 7)},
    **{name: "NOT_EXECUTED" for name in ("ENSO_SCENARIOS", "GVP", "VAR_CVAR", "A1_A2", "OPTIMIZATION")},
    "PRIMARY_REPLACEMENT": "PROHIBITED",
    "KNOWN_PRIMARY_RESULTS_CHANGED_R1_CONTRACT": False,
    "BANANA_SPECIFIC_TEST": "PROHIBITED",
    "LEMON_SPECIFIC_TEST": "PROHIBITED",
    "R3_ADAPTER_IMPLEMENTED": False,
    "ROBUSTNESS_SCORE": "PROHIBITED",
    "SIGNIFICANCE_VOTE_COUNTING": "PROHIBITED",
    "GLOBAL_FWER": "NOT_CLAIMED",
    "CLAIM_CEILING": er1.CLAIM_CEILING,
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False) + "\n").encode("utf-8")


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def verify_inputs() -> dict:
    actual = {rel: sha((ROOT / rel).read_bytes()) for rel in FROZEN_HASHES}
    require(actual == FROZEN_HASHES, "ER2_R1_FAIL_UPSTREAM_IMMUTABILITY")
    return actual


def preflight(live_remote: bool = False) -> dict:
    require(git("rev-parse", "HEAD") == ER2P_SHA, "ER2_R1_FAIL_FROZEN_CONTRACT: HEAD")
    require(git("rev-parse", "HEAD^") == er2p.ER1_SHA, "ER2_R1_FAIL_FROZEN_CONTRACT: parent")
    for branch, tag, expected in (
        (ER2P_BRANCH, ER2P_TAG, ER2P_SHA),
        (er2p.ER1_BRANCH, er2p.ER1_TAG, er2p.ER1_SHA),
        (er2p.ED1_BRANCH, er2p.ED1_TAG, er2p.ED1_SHA),
    ):
        require(git("rev-parse", branch) == git("rev-parse", "origin/" + branch)
                == git("rev-parse", tag + "^{}") == expected,
                "ER2_R1_FAIL_UPSTREAM_IMMUTABILITY: refs")
    if live_remote:
        refs = dict(line.split()[::-1] for line in git(
            "ls-remote", "origin", "refs/heads/" + ER2P_BRANCH,
            "refs/tags/" + ER2P_TAG + "^{}",
        ).splitlines())
        require(refs == {"refs/heads/" + ER2P_BRANCH: ER2P_SHA,
                         "refs/tags/" + ER2P_TAG + "^{}": ER2P_SHA},
                "ER2_R1_FAIL_FROZEN_CONTRACT: live remote")
    require(not git("diff", "--name-only") and not git("diff", "--cached", "--name-only"),
            "ER2_R1_FAIL_UPSTREAM_IMMUTABILITY: tracked tree/index")
    untracked = set(git("ls-files", "--others", "--exclude-standard").splitlines())
    require(untracked <= {p.as_posix() for p in CANDIDATE_RELS}, "ER2_R1_FAIL_FROZEN_CONTRACT: scope")
    require(set(er2p.forbidden_result_paths(ROOT)) <= {p.as_posix() for p in OUTPUT_RELS},
            "ER2_R1_FAIL_FROZEN_CONTRACT: unauthorized tier artifact")
    inputs = verify_inputs()
    er1_lock = json.loads((ROOT / er1.LOCK_REL).read_bytes())
    identity = sha(json.dumps(er1_lock["result_table_sha256"], sort_keys=True,
                              separators=(",", ":")).encode("utf-8"))
    require(identity == er2p.NUMERICAL_IDENTITY == er1.NUMERICAL_RESULTS_IDENTITY,
            "ER2_R1_FAIL_FROZEN_CONTRACT: ER1 identity")
    protocol = json.loads((ROOT / er2p.CONFIG_REL).read_bytes())
    tier = protocol["tiers"][0]
    tier_hash = sha(er2p.json_bytes(tier))
    contracts = list(csv.DictReader(io.StringIO((ROOT / er2p.TIERS_REL).read_text(encoding="utf-8"))))
    require(contracts[0]["TIER_CONTRACT_SHA256"] == tier_hash, "ER2_R1_FAIL_FROZEN_CONTRACT: tier hash")
    require(tier["tier"] == "R1" and tier["order"] == 1 and tier["family"] == "LEVEL"
            and tier["distinct_models"] == 2 and tier["distinct_coefficients"] == 6
            and tuple(tier["regressors"]) == LEVEL
            and tier["perennial_equivalence"]["exact_coefficient_and_fitted_value_equality_required_for_status"] is True,
            "ER2_R1_FAIL_FROZEN_CONTRACT: R1")
    er1.verify_ed1_contract()
    return {"status": "PASS", "exact_input_sha256": inputs, "tier_contract": tier,
            "tier_contract_sha256": tier_hash, "er1_numerical_results_identity": identity}


def sample_keys(frame: pd.DataFrame, period: str) -> list[list[str]]:
    require(not frame.duplicated(["UBIGEO", period]).any(), "ER2_R1_FAIL_SAMPLE_IDENTITY: duplicate")
    return frame[["UBIGEO", period]].astype(str).values.tolist()


def require_same_sample(primary: pd.DataFrame, level: pd.DataFrame, period: str) -> list[list[str]]:
    keys = sample_keys(primary, period)
    require(keys == sample_keys(level, period), "ER2_R1_FAIL_SAMPLE_IDENTITY: key/order drift")
    return keys


def model_contract(code: str, columns: list[str]) -> dict:
    crop = ed1.CROPS[code]
    return {"crop_code": code, "crop": crop["crop"], "regressors": columns,
            "windows": list(crop["windows"]), "period_column": crop["period_column"],
            "district_fe": "REQUIRED", "period_fe": "REQUIRED", "cluster": "UBIGEO",
            "weighting": "UNWEIGHTED", "functional_form": "LINEAR_ADDITIVE",
            "outcome": "YIELD_LEVEL_TM_PER_HA", "family": "LEVEL",
            "inference": "CR2_SATTERTHWAITE_AND_CROP_AHT",
            "role": "DISTINCT_LEVEL_ROBUSTNESS" if code in er2p.TRANSIENT else "FE_EQUIVALENT_DIAGNOSTIC",
            "primary_replacement": "PROHIBITED"}


def compare_arrays(first: np.ndarray, second: np.ndarray) -> dict:
    first, second = np.asarray(first, dtype="<f8"), np.asarray(second, dtype="<f8")
    require(first.shape == second.shape and np.isfinite(first).all() and np.isfinite(second).all(),
            "ER2_R1_FAIL_NUMERICAL_VERIFICATION: nonfinite/shape")
    difference = float(np.max(np.abs(first - second)))
    return {"max_abs_difference": difference, "numeric_exact": bool(np.array_equal(first, second)),
            "byte_exact": first.tobytes(order="C") == second.tobytes(order="C"),
            "within_1e_9": difference <= TOLERANCE,
            "level_array_sha256": sha(first.tobytes(order="C")),
            "anomaly_array_sha256": sha(second.tobytes(order="C"))}


def equality_status(metrics: dict) -> str:
    required = [metrics[name] for name in ("transformed_x", "coefficients", "fitted_values")]
    if all(m["numeric_exact"] and m["byte_exact"] for m in required):
        return "EXACT_EQUALITY"
    if all(m["within_1e_9"] for m in required):
        return "WITHIN_1E-9_TOLERANCE_BUT_NOT_EXACT"
    return "NON_EQUIVALENT"


def completion_status(diagnostics: list[dict]) -> str:
    return PASS if all(d["status"] == "EXACT_EQUALITY" for d in diagnostics) else HOLD


def checked_fit(frame: pd.DataFrame, columns: list[str], period: str, y: np.ndarray) -> dict:
    require(np.isfinite(frame[columns].to_numpy(dtype=float)).all() and np.isfinite(y).all(),
            "ER2_R1_FAIL_SAMPLE_IDENTITY: missing/nonfinite no deletion allowed")
    fit = ed1.fit_two_way_fe_cr2(frame, columns, period, y)
    require(not fit["nonfinite_count"] and not fit["cr2_adjustment_singularities"],
            "ER2_R1_FAIL_NUMERICAL_VERIFICATION: inference engine")
    return fit


def numerical_verification(frame: pd.DataFrame, columns: list[str], period: str,
                           y: np.ndarray, fit: dict) -> dict:
    reference = ed1._reference_svd_fit(frame, columns, period, y)
    differences = {
        "beta_max_abs_difference": float(np.max(np.abs(fit["beta"] - reference["beta"]))),
        "cr2_covariance_max_abs_difference": float(np.max(np.abs(fit["climate_covariance"] - reference["covariance"]))),
        "satterthwaite_df_max_abs_difference": float(np.max(np.abs(fit["satterthwaite_df"] - reference["satterthwaite_df"]))),
        "aht_f_max_abs_difference": abs(fit["aht"]["f_statistic"] - reference["aht"]["f_statistic"]),
        "aht_denominator_df_max_abs_difference": abs(fit["aht"]["denominator_df"] - reference["aht"]["denominator_df"]),
        "aht_p_max_abs_difference": abs(fit["aht"]["p_value"] - reference["aht"]["p_value"]),
    }
    require(all(np.isfinite(v) for v in differences.values()), "ER2_R1_FAIL_NUMERICAL_VERIFICATION: nonfinite reference")
    # Retain failed comparisons in the lock; do not change the engine or tolerance.
    return {"status": "PASS" if max(differences.values()) <= VERIFICATION_TOLERANCE else "FAIL",
            "reference_path": "INDEPENDENT_FULL_DESIGN_SVD_CALCULATION", "absolute_tolerance": VERIFICATION_TOLERANCE,
            "differences": differences, "main_beta": fit["beta"].tolist(), "reference_beta": reference["beta"].tolist(),
            "main_cr2_covariance": fit["climate_covariance"].tolist(), "reference_cr2_covariance": reference["covariance"].tolist(),
            "main_satterthwaite_df": fit["satterthwaite_df"].tolist(), "reference_satterthwaite_df": reference["satterthwaite_df"].tolist(),
            "main_aht": fit["aht"], "reference_aht": reference["aht"]}


def perennial_diagnostic(code: str, primary: pd.DataFrame, level: pd.DataFrame,
                         anomaly_columns: list[str], level_columns: list[str], y: np.ndarray) -> dict:
    period = ed1.CROPS[code]["period_column"]
    keys = require_same_sample(primary, level, period)
    a = checked_fit(primary, anomaly_columns, period, y)
    b = checked_fit(level, level_columns, period, y)
    metrics = {
        "transformed_x": compare_arrays(b["x_within"], a["x_within"]),
        "coefficients": compare_arrays(b["beta"], a["beta"]),
        "fitted_values": compare_arrays(b["design"] @ b["full_beta"], a["design"] @ a["full_beta"]),
        "residuals": compare_arrays(b["residual"], a["residual"]),
        "cr2_covariance": compare_arrays(b["climate_covariance"], a["climate_covariance"]),
        "satterthwaite_df": compare_arrays(b["satterthwaite_df"], a["satterthwaite_df"]),
        "aht": compare_arrays(np.array(list(b["aht"].values())), np.array(list(a["aht"].values()))),
    }
    for name, fit in (("level", b), ("anomaly", a)):
        se = np.sqrt(np.diag(fit["climate_covariance"]))
        fit["inference_vector"] = np.concatenate([
            se, fit["beta"] / se,
            2 * stats.t.sf(np.abs(fit["beta"] / se), fit["satterthwaite_df"]),
            fit["beta"] - stats.t.ppf(.975, fit["satterthwaite_df"]) * se,
            fit["beta"] + stats.t.ppf(.975, fit["satterthwaite_df"]) * se,
        ])
    metrics["coefficient_inference"] = compare_arrays(b["inference_vector"], a["inference_vector"])
    ranks = [int(np.linalg.matrix_rank(x, tol=TOLERANCE)) for x in
             (b["x_within"], a["x_within"], np.column_stack([b["x_within"], a["x_within"]]))]
    projector_differences = [float(np.max(np.abs(x - z @ np.linalg.lstsq(z, x, rcond=None)[0])))
                             for x, z in ((a["x_within"], b["x_within"]), (b["x_within"], a["x_within"]))]
    return {"crop_code": code, "crop": ed1.CROPS[code]["crop"], "status": equality_status(metrics),
            "distinct_evidence_contribution": 0, "diagnostic_only": True,
            "metrics": metrics, "absolute_tolerance": TOLERANCE,
            "column_space": {"level_rank": ranks[0], "anomaly_rank": ranks[1], "combined_rank": ranks[2],
                             "equivalent_within_tolerance": len(set(ranks)) == 1 and max(projector_differences) <= TOLERANCE,
                             "bidirectional_projection_max_abs": projector_differences},
            "variable_pairing": list(map(list, zip(level_columns, anomaly_columns))),
            "ordered_sample_keys": keys, "transformed_level_design": b["x_within"].tolist(),
            "transformed_anomaly_design": a["x_within"].tolist(),
            "level_coefficients": b["beta"].tolist(), "anomaly_coefficients": a["beta"].tolist(),
            "fitted_value_definition": "FULL_FITTED_VALUES_INCLUDING_DISTRICT_AND_PERIOD_FE",
            "array_hash_encoding": "LITTLE_ENDIAN_FLOAT64_C_ORDER_NO_HEADER"}


def calculate() -> dict:
    pre = preflight()
    transient_outcomes, perennial_outcomes, sources = er1.read_outcome_sources()
    transient = pq.read_table(ed1.TRANSIENT_PATH, columns=list(ed1.TRANSIENT_COLUMNS)).to_pandas()
    perennial = ed1.read_perennial_primary()
    primary_table = list(csv.DictReader(io.StringIO((ROOT / er1.COEFFICIENTS_REL).read_text(encoding="utf-8"))))
    primary_lookup = {(r["CROP_CODE"], r["CLIMATE_VARIABLE"]): r for r in primary_table}
    frozen_sample = {r["CROP_CODE"]: r for r in json.loads((ROOT / er1.LOCK_REL).read_bytes())["sample_identities"]}
    coefficients, joint, diagnostics, samples, contracts = [], [], [], {}, {}
    verification = {}
    for code in er2p.CROP_ORDER:
        crop = ed1.CROPS[code]
        period = crop["period_column"]
        if code in er2p.TRANSIENT:
            primary, anomaly_columns = er1.transient_design_with_outcome(transient, transient_outcomes, code)
            level, columns = primary.copy(), list(LEVEL)
        else:
            primary, anomaly_columns = er1.perennial_design_with_outcome(perennial, perennial_outcomes, code)
            level, columns = ed1.primary_design_frame(pd.DataFrame(), perennial, code, "LEVEL")
            level[period] = level[period].astype(str)
        keys = require_same_sample(primary, level, period)
        y = primary["YIELD"].to_numpy(dtype=float)
        support = er1.outcome_support(y)
        expected = er1.EXPECTED_SAMPLE[code]
        actual = {"n": len(level), "districts": int(level["UBIGEO"].nunique()),
                  "periods": int(level[period].nunique())}
        require(actual == {k: expected[k] for k in actual}, "ER2_R1_FAIL_SAMPLE_IDENTITY: counts")
        require(support["minimum"] == frozen_sample[code]["Y_MIN"]
                and support["median"] == frozen_sample[code]["Y_MEDIAN"]
                and support["maximum"] == frozen_sample[code]["Y_MAX"], "ER2_R1_FAIL_SAMPLE_IDENTITY: outcome")
        contracts[code] = model_contract(code, columns)
        if code in er2p.PERENNIAL:
            diagnostics.append(perennial_diagnostic(code, primary, level, anomaly_columns, columns, y))
            continue
        require(set(level["WINDOW_ID"]) == set(crop["windows"]), "ER2_R1_FAIL_FROZEN_CONTRACT: window")
        fit = checked_fit(level, columns, period, y)
        effective = ed1.effective_cluster_audit(level, fit["x_within"])
        require(effective["effective_contributing_clusters"] == expected["effective"],
                "ER2_R1_FAIL_SAMPLE_IDENTITY: effective clusters")
        verification[code] = numerical_verification(level, columns, period, y, fit)
        se = np.sqrt(np.diag(fit["climate_covariance"]))
        t_values = fit["beta"] / se
        p_values = 2 * stats.t.sf(np.abs(t_values), fit["satterthwaite_df"])
        holm = er1.holm_adjust(p_values)
        critical = stats.t.ppf(.975, fit["satterthwaite_df"])
        samples[code] = {**actual, "effective_districts": expected["effective"], "key_columns": ["UBIGEO", period],
                         "er1_ordered_keys": keys, "r1_ordered_keys": sample_keys(level, period),
                         "exact_key_set_and_order_equality": True, "key_sha256": sha(json_bytes(keys)),
                         "outcome_sha256": sha(np.asarray(y, dtype="<f8").tobytes()),
                         "outcome_support": support, "cr2_covariance": fit["climate_covariance"].tolist()}
        for i, variable in enumerate(columns):
            ref = primary_lookup[(code, ANOMALY[i])]
            beta, primary_beta = float(fit["beta"][i]), float(ref["BETA"])
            coefficients.append({"CROP_CODE": code, "CROP": crop["crop"], "VARIABLE": variable,
                "WINDOW": crop["windows"][0], "BETA": beta, "CR2_SE": float(se[i]),
                "SATTERTHWAITE_DF": float(fit["satterthwaite_df"][i]), "T": float(t_values[i]),
                "P_TWO_SIDED": float(p_values[i]), "CI95_LOWER": float(beta - critical[i] * se[i]),
                "CI95_UPPER": float(beta + critical[i] * se[i]), "HOLM_P": float(holm[i]),
                "CI_SEMANTICS": CI_SEMANTICS, "MULTIPLICITY": MULTIPLICITY,
                "ER1_VARIABLE": ANOMALY[i], "ER1_BETA_REFERENCE": primary_beta,
                "SIGN_AGREEMENT": bool(np.sign(beta) == np.sign(primary_beta)),
                "R1_MINUS_ER1_BETA_DESCRIPTIVE_ONLY": beta - primary_beta,
                "PRIMARY_REPLACEMENT": "PROHIBITED", "CLAIM_CEILING": er1.CLAIM_CEILING})
        joint.append({"CROP_CODE": code, "CROP": crop["crop"], "NULL": "RAIN_MM=TMAX_C=TMIN_C=0",
                      "NUMERATOR_DF": fit["aht"]["numerator_df"], "DENOMINATOR_DF": fit["aht"]["denominator_df"],
                      "F": fit["aht"]["f_statistic"], "P": fit["aht"]["p_value"], "METHOD": "CR2_AHT_HTZ"})
    require(len(coefficients) == 6 and len(joint) == 2 and len(diagnostics) == 3,
            "ER2_R1_FAIL_FROZEN_CONTRACT: result inventory")
    verify_inputs()
    verdict = NUMERICAL_FAIL if any(v["status"] == "FAIL" for v in verification.values()) else completion_status(diagnostics)
    return {"preflight": pre, "sources": sources, "coefficients": coefficients, "joint": joint,
            "diagnostics": diagnostics, "samples": samples, "contracts": contracts,
            "verification": verification, "verdict": verdict}


def csv_bytes(rows: list[dict]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows({key: er1.canonical_float(value) if isinstance(value, float) else
                     str(value).upper() if isinstance(value, bool) else value for key, value in row.items()} for row in rows)
    return buffer.getvalue().encode("utf-8")


def diagnostic_rows(diagnostics: list[dict]) -> list[dict]:
    rows = []
    for d in diagnostics:
        row = {"CROP_CODE": d["crop_code"], "CROP": d["crop"], "STATUS": d["status"],
               "N": len(d["ordered_sample_keys"]), "REGRESSORS": len(d["variable_pairing"]),
               "DISTINCT_EVIDENCE_CONTRIBUTION": 0,
               "COLUMN_SPACE_EQUIVALENT_WITHIN_TOLERANCE": d["column_space"]["equivalent_within_tolerance"]}
        for name, metric in d["metrics"].items():
            for field in ("max_abs_difference", "numeric_exact", "byte_exact", "within_1e_9"):
                row[f"{name}_{field}".upper()] = metric[field]
        rows.append(row)
    return rows


def markdown_table(rows: list[dict], fields: list[str]) -> list[str]:
    return ["| " + " | ".join(fields) + " |", "|" + "---|" * len(fields),
            *["| " + " | ".join(format(r[f], ".12g") if isinstance(r[f], float) else str(r[f])
                                for f in fields) + " |" for r in rows]]


def report_text(results: dict) -> str:
    lines = ["# ER2 R1 Level Climate-Family Results v1", "", f"FINAL_VERDICT={results['verdict']}", "",
             "## Execution and governance", "",
             f"ER2P_FREEZE_SHA={ER2P_SHA}", f"ER1_FREEZE_SHA={er2p.ER1_SHA}",
             f"ER1_NUMERICAL_RESULTS_IDENTITY={er2p.NUMERICAL_IDENTITY}",
             "R1 alone is authorized. ER1 remains PRIMARY. R2-R6 are NOT_AUTHORIZED and NOT_EXECUTED.",
             "Two distinct level models, six coefficients, two AHT tests and three perennial diagnostics.",
             "No outcome-specific specification change, score, vote counting or primary replacement.", "",
             "## Transient results", "",
             "Exact ER1 sample: Rice 281 observations, 44 nominal/43 effective districts; MAD 318, 54/52. Seven campaigns each.",
             "Yield remains TM/ha; unweighted linear additive models include district and campaign fixed effects.",
             "All intervals are unadjusted 95% CR2/Satterthwaite intervals. Holm adjusts only the three R1 p-values within each crop.",
             "No Holm-adjusted confidence intervals or global FWER claim.", "",
             *markdown_table(results["coefficients"], ["CROP", "VARIABLE", "WINDOW", "BETA", "CR2_SE", "SATTERTHWAITE_DF", "T", "P_TWO_SIDED", "CI95_LOWER", "CI95_UPPER", "HOLM_P"]), "",
             "## Crop-level AHT/HTZ tests", "",
             *markdown_table(results["joint"], ["CROP", "NULL", "NUMERATOR_DF", "DENOMINATOR_DF", "F", "P"]), "",
             "## ER1 versus R1 descriptive comparison", "",
             *markdown_table(results["coefficients"], ["CROP", "VARIABLE", "ER1_BETA_REFERENCE", "BETA", "SIGN_AGREEMENT", "R1_MINUS_ER1_BETA_DESCRIPTIVE_ONLY"]), "",
             "These are descriptive level-family sensitivity comparisons, not votes for a best specification. Rainfall exposure constructions differ; raw beta magnitudes and arithmetic differences are not directly comparable effect sizes.",
             "No causal robustness claim. Claim ceiling: EMPIRICAL_ASSOCIATION_CLIMATE_RESPONSE_ONLY.", "",
             "## Perennial FE-equivalence diagnostics", "",
             "The same diagnostic algorithm is applied to every perennial. Lemon and Banana each retain all six t and t-1 regressors.",
             "Full transformed designs, ordered keys, array hashes and all discrepancies are in the lock. Byte equality uses little-endian float64 C-order arrays; tolerance is absolute 1e-9, without rounding.", ""]
    for d in results["diagnostics"]:
        lines.extend([f"### {d['crop']}", "", f"STATUS={d['status']}",
                      f"COLUMN_SPACE_EQUIVALENT_WITHIN_TOLERANCE={d['column_space']['equivalent_within_tolerance']}", "",
                      *markdown_table([{"quantity": k, **v} for k, v in d["metrics"].items()],
                                      ["quantity", "max_abs_difference", "numeric_exact", "byte_exact", "within_1e_9"]), ""])
    lines.extend(["Nonexact equality requires Director adjudication; no perennial is promoted to distinct robustness evidence.", "",
                  "## Independent numerical verification", "",
                  "The frozen ED1 main full-design path and independent SVD path are compared for beta, CR2 covariance, coefficient df and AHT at absolute tolerance 1e-8. Any exceedance fails numerical certification; estimates remain uncertified, even when differences are small.",
                  "The numerical reference is an independent implementation path, not a new climate family or robustness tier.",
                  "Method reference: [clubSandwich HTZ documentation](https://jepusto.github.io/clubSandwich/reference/Wald_test.html).", ""])
    for code, v in results["verification"].items():
        lines.extend([f"{ed1.CROPS[code]['crop']}: {json.dumps(v, sort_keys=True, allow_nan=False)}", ""])
    lines.extend(["## Reproduction and lock", "",
                  "The lock contains the implementation/test hashes and exact table/report hashes. Its SHA-256 is computed externally; no self-hash is embedded.",
                  "Rebuilds only accept existing identical bytes; different locked artifacts are never overwritten.",
                  "Run the R1 unittest suite and two independent temporary-output builds; canonical equality is required.",
                  "Full repository lifecycle failures must be adjudicated separately and must not be represented as an all-green suite.",
                  "NEXT_TIER_AUTHORIZATION_STATUS=NOT_AUTHORIZED", "",
                  "NEXT_ACTION=RETURN_TO_SCIENTIFIC_DIRECTOR_FOR_R1_REVIEW", ""])
    return "\n".join(lines)


def render_outputs() -> dict[Path, bytes]:
    r = calculate()
    outputs = {RESULTS_REL: csv_bytes(r["coefficients"]), JOINT_REL: csv_bytes(r["joint"]),
               EQUIVALENCE_REL: csv_bytes(diagnostic_rows(r["diagnostics"])), REPORT_REL: report_text(r).encode("utf-8")}
    lock = {
        "schema_version": "1.0.0", "project": "ENSO_EL_NINO_2026_2027_AGRICULTURE_PIURA",
        "gate": "ER2_R1_LEVEL_CLIMATE_FAMILY_EXECUTION_V1", "er1_freeze_sha": er2p.ER1_SHA,
        "ed1_freeze_sha": er2p.ED1_SHA, "er1_numerical_results_identity": er2p.NUMERICAL_IDENTITY,
        "er1_reporting_lock_sha256": er2p.REPORTING_IDENTITY, "er2p_freeze_sha": ER2P_SHA,
        "er2p_protocol_sha256": PROTOCOL_SHA, "tier_id": "R1_LEVEL_CLIMATE_FAMILY", "tier_order": 1,
        "tier_contract_sha256": r["preflight"]["tier_contract_sha256"],
        "frozen_r1_tier_contract": r["preflight"]["tier_contract"],
        "implementation_sha256": sha((ROOT / SCRIPT_REL).read_bytes()), "test_sha256": sha((ROOT / TEST_REL).read_bytes()),
        "exact_input_sha256": r["preflight"]["exact_input_sha256"],
        "exact_model_contract": r["contracts"], "sample_identity": r["samples"], "outcome_provenance": r["sources"],
        "rice_result_inventory": [c for c in r["coefficients"] if c["CROP_CODE"] == er2p.TRANSIENT[0]],
        "mad_result_inventory": [c for c in r["coefficients"] if c["CROP_CODE"] == er2p.TRANSIENT[1]],
        "aht_joint_tests": r["joint"], "perennial_equivalence_diagnostics": r["diagnostics"],
        "multiplicity": MULTIPLICITY, "confidence_intervals": CI_SEMANTICS,
        "multiplicity_adjusted_confidence_intervals": "NOT_CONSTRUCTED_NOT_CLAIMED",
        "global_fwer": "NOT_CLAIMED", "interpretation_firewall": FIREWALL,
        "primary_results_known": True, "robustness_results_known": True,
        "execution_authorization": {"R1": "DIRECTOR_AUTHORIZED", **{f"R{i}": "NOT_AUTHORIZED" for i in range(2, 7)}},
        "previous_tier_lock_sha256": None, "completion_status": r["verdict"],
        "scientific_lock_status": "RESULTS_LOCKED_PENDING_DIRECTOR_REVIEW_NOT_GIT_FROZEN",
        "r1_calculations_complete": True, "next_tier_authorization_status": "NOT_AUTHORIZED",
        "distinct_models": 2, "distinct_coefficients": 6, "distinct_robustness_evidence_count": 2,
        "perennial_diagnostic_models": 3, "independent_numerical_verification": r["verification"],
        "artifact_sha256": {p.as_posix(): sha(b) for p, b in outputs.items()},
        "next_action": "RETURN_TO_SCIENTIFIC_DIRECTOR_FOR_R1_REVIEW",
    }
    outputs[LOCK_REL] = json_bytes(lock)
    return outputs


def publish(outputs: dict[Path, bytes], output_root: Path) -> dict:
    output_root = output_root.resolve()
    require(output_root == ROOT or not output_root.is_relative_to(ROOT), "External temporary output root required")
    require(set(outputs) == set(OUTPUT_RELS), "ER2_R1_FAIL_FROZEN_CONTRACT: output inventory")
    for rel, payload in outputs.items():
        destination = output_root / rel
        require(not destination.exists() or destination.read_bytes() == payload,
                "R1_LOCKED_ARTIFACT_REVISION_PROHIBITED: " + rel.as_posix())
    # Validate every destination before any write; the lock is materialized last.
    for rel in (*[p for p in OUTPUT_RELS if p != LOCK_REL], LOCK_REL):
        path = output_root / rel
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(outputs[rel])
    return {rel.as_posix(): sha(payload) for rel, payload in outputs.items()}


def run(output_root: Path = ROOT) -> dict:
    return publish(render_outputs(), output_root)


def main() -> int:
    parser = argparse.ArgumentParser(description="Execute authorized R1 only; lock results without git operations.")
    parser.add_argument("--output-root", type=Path, default=ROOT)
    parser.add_argument("--live-preflight", action="store_true")
    args = parser.parse_args()
    preflight(live_remote=args.live_preflight)
    hashes = run(args.output_root)
    lock = json.loads((args.output_root / LOCK_REL).read_bytes())
    print(json.dumps({"artifact_sha256": hashes, "verdict": lock["completion_status"],
                      "next_tier_authorization_status": "NOT_AUTHORIZED"}, sort_keys=True))
    return 1 if lock["completion_status"] == NUMERICAL_FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
