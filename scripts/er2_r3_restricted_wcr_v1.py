from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import econometric_design_master_v1 as ed1  # noqa: E402
import er1_primary_real_estimation_v1 as er1  # noqa: E402
import er2_r3_named_wcr_adapter_v1 as r3a  # noqa: E402


PROJECT = "ENSO_EL_NINO_2026_2027_AGRICULTURE_PIURA"
GATE = "ER2_R3_RESTRICTED_WILD_CLUSTER_BOOTSTRAP_REAL_EXECUTION_V1"
R3A_FREEZE_SHA = "c285ccc97fca384663ef98d730cd6cd325c71000"
R3A_BRANCH = "phase/er2-r3a-named-wcr-adapter-v1"
R3A_TAG = "er2-r3a-named-wcr-adapter-v1-freeze"
R3A_TAG_OBJECT = "e0c5a3a481d549ea4451305908c4c97119f1d7fb"
R3A_SCRIPT_SHA = "b0368dfcf93f2675c4b4fdcaff63e905540ff0914808319e53a4ee106eb365a2"
R3A_LOCK_SHA = "53e573343338cfc06a9afc93c447a916777ccd6d95cffb2d431d0a5686b38326"
R2_FREEZE_SHA = "611c91255d5a367127df57dd69855e2df83ac0cb"
R2_REPORTING_LOCK_SHA = "a37ba8ee9fdebe400b638404200d1109fa3045c59ec2b1f6c76b35c3cc3284a4"
ER2P_FREEZE_SHA = "3fd1f657e79d7e0ae93903239fd3690dcade56a4"
ER1_FREEZE_SHA = "43de46ecd46248f1e4e2822a30e69cfadbc8260f"
ER1_NUMERICAL_IDENTITY = "40e0f58269dda309e83a1fa3da17ef4d5dc5523efc72a666f734d0ebacb76b24"
R3_TIER_SHA = "a70eb6398e9073053fd619fc985e9f8e3348be42bc0212f42d99dde475fa0864"

REPLICATIONS = 9999
SEED = 20260903
BATCH_SIZE = 1000
BATCH_PARTITION = [1000] * 9 + [999]
MODEL_IDENTITY_TOLERANCE = 1e-10
ALPHA = 0.05
FINAL_VERDICT = "ER2_R3_PASS_RESULTS_LOCKED_READY_FOR_DIRECTOR_REVIEW"

COEFFICIENTS = Path("outputs/econometrics/ER2_R3_WCR_COEFFICIENT_RESULTS.csv")
JOINT = Path("outputs/econometrics/ER2_R3_WCR_JOINT_TESTS.csv")
SAMPLES = Path("outputs/econometrics/ER2_R3_SAMPLE_AUDIT.csv")
EXECUTION = Path("outputs/econometrics/ER2_R3_WCR_EXECUTION_AUDIT.csv")
REPORT = Path("outputs/econometrics/ER2_R3_REPORT.md")
LOCK = Path("outputs/econometrics/ER2_R3_RESULTS_LOCK.json")
SCRIPT = Path("scripts/er2_r3_restricted_wcr_v1.py")
TEST = Path("tests/test_er2_r3_restricted_wcr_v1.py")
OUTPUTS = (COEFFICIENTS, JOINT, SAMPLES, EXECUTION, REPORT, LOCK)
CANDIDATES = (*OUTPUTS, SCRIPT, TEST)

R3A_SCRIPT = Path("scripts/er2_r3_named_wcr_adapter_v1.py")
R3A_LOCK = Path("outputs/econometrics/ER2_R3A_ADAPTER_LOCK_CERTIFIED.json")
R2_LOCK = Path("outputs/econometrics/ER2_R2_RESULTS_LOCK.json")
R2_REPORTING_LOCK = Path("outputs/econometrics/ER2_R2_RESULTS_LOCK_REPORTING_CERTIFIED.json")
TIER_CONTRACTS = Path("outputs/econometrics/ER2P_TIER_CONTRACTS.csv")
ER2P_PROTOCOL = Path("config/econometrics/er2_robustness_protocol_v1.json")
ER1_COEFFICIENTS = Path("outputs/econometrics/ER1_PRIMARY_COEFFICIENTS.csv")
ER1_JOINT = Path("outputs/econometrics/ER1_PRIMARY_JOINT_TESTS.csv")
ER1_SAMPLES = Path("outputs/econometrics/ER1_PRIMARY_SAMPLE_AUDIT.csv")
ER1_LOCK = Path("outputs/econometrics/ER1_PRIMARY_RESULTS_LOCK.json")

UPSTREAM_HASHES = {
    R3A_SCRIPT.as_posix(): R3A_SCRIPT_SHA,
    R3A_LOCK.as_posix(): R3A_LOCK_SHA,
    R2_REPORTING_LOCK.as_posix(): R2_REPORTING_LOCK_SHA,
    TIER_CONTRACTS.as_posix(): "2ff57eadb872ca6aa10cb84aa4fdf9b7250715df5ca77d2f3e9d22621e7d762a",
    ER1_COEFFICIENTS.as_posix(): "37fa03a2e860f86277510a5ff3b66ca475fc02d277ea1dd6e18156f719c23480",
    ER1_JOINT.as_posix(): "8d00e0ef866488c8f7ce7a418d58ae165e87f05053db9861fed1b0f181e412e3",
    ER1_SAMPLES.as_posix(): "d5a2b42b7f8f68be5a387c9726f76d081c83e1b242fea2edfba829f963040854",
    ER1_LOCK.as_posix(): "83eea5e179b5e3504bd1144d744dcdbeddbbdf6a554f4d10ab03b92a30278841",
}

COEFFICIENT_FIELDS = (
    "CROP_CODE", "CROP", "MODEL_ID", "CLIMATE_VARIABLE", "WINDOW", "ER1_BETA_REFERENCE",
    "ER1_CR2_STANDARD_ERROR_REFERENCE", "ER1_SATTERTHWAITE_DF_REFERENCE", "ER1_CR2_P_REFERENCE",
    "ER1_CR2_HOLM_P_REFERENCE", "R3_OBSERVED_ABSOLUTE_T", "WCR_EXCEEDANCE_COUNT",
    "INVALID_REPLICATIONS", "WCR_P_NUMERATOR", "WCR_P_DENOMINATOR", "WCR_RAW_P",
    "WITHIN_CROP_HOLM_WCR_P", "CR2_HOLM_STATUS", "WCR_HOLM_STATUS", "INFERENCE_COMPARISON",
    "PRIMARY_CLIMATE_FAMILY", "OUTCOME_SCALE", "R3_MODEL_SPECIFICATION_CHANGE",
)
JOINT_FIELDS = (
    "CROP_CODE", "CROP", "MODEL_ID", "COEFFICIENTS_TESTED", "Q", "JOINT_NULL",
    "ER1_AHT_F_REFERENCE", "ER1_AHT_P_REFERENCE", "R3_OBSERVED_WALD_F",
    "WCR_EXCEEDANCE_COUNT", "INVALID_REPLICATIONS", "WCR_P_NUMERATOR", "WCR_P_DENOMINATOR",
    "WCR_RAW_P", "AHT_STATUS", "WCR_STATUS", "INFERENCE_COMPARISON", "JOINT_HOLM",
)
SAMPLE_FIELDS = (
    "CROP_CODE", "CROP", "MODEL_ID", "N", "NOMINAL_DISTRICTS", "EFFECTIVE_DISTRICTS",
    "PERIODS", "ORDERED_KEY_SHA256", "Y_FLOAT64_SHA256", "X_FLOAT64_SHA256",
    "ER1_ORDERED_KEYS_EXACT", "ER1_Y_SOURCE_EXACT", "MISSING_Y", "MISSING_X",
    "DUPLICATE_KEYS", "ROW_ORDER", "CLUSTER_ORDER", "OUTCOME_SCALE",
)
EXECUTION_FIELDS = (
    "CROP_CODE", "CROP", "TEST_ID", "TEST_KIND", "CLUSTER_COUNT", "SEED", "B",
    "BATCH_SIZE", "BATCH_PARTITION", "RNG", "WEIGHTS", "SEED_RESET", "FULL_DRAW_MATRIX_SHA256",
    "INITIAL_RNG_STATE_SHA256", "FINAL_RNG_STATE_SHA256", "BOOTSTRAP_STATISTIC_SHA256",
    "EXCEEDANCE_COUNT", "INVALID_REPLICATIONS", "FINITE_P_NUMERATOR", "FINITE_P_DENOMINATOR",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def sha_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha_file(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")


def compact_json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def canonical_float(value: Any) -> str:
    number = float(value)
    require(np.isfinite(number), "ER2_R3_HOLD_INVALID_BOOTSTRAP_REPLICATIONS: nonfinite result")
    return format(number, ".17g")


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def read_json(relative: Path) -> dict[str, Any]:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def preflight() -> dict[str, Any]:
    identity = {
        "head": git("rev-parse", "HEAD"),
        "branch": git("branch", "--show-current"),
        "local_branch": git("rev-parse", R3A_BRANCH),
        "remote_branch": git("rev-parse", f"origin/{R3A_BRANCH}"),
        "peeled_tag": git("rev-list", "-n", "1", R3A_TAG),
        "tag_object": git("rev-parse", R3A_TAG),
    }
    expected = {
        "head": R3A_FREEZE_SHA,
        "branch": R3A_BRANCH,
        "local_branch": R3A_FREEZE_SHA,
        "remote_branch": R3A_FREEZE_SHA,
        "peeled_tag": R3A_FREEZE_SHA,
        "tag_object": R3A_TAG_OBJECT,
    }
    require(identity == expected, f"ER2_R3_FAIL_R3A_PREREQUISITE: git identity {identity}")

    tracked = git("diff", "--name-only").splitlines()
    staged = git("diff", "--cached", "--name-only").splitlines()
    untracked = set(git("ls-files", "--others", "--exclude-standard").splitlines())
    authorized = {path.as_posix() for path in CANDIDATES}
    require(not tracked and not staged and untracked.issubset(authorized),
            f"ER2_R3_FAIL_UPSTREAM_IMMUTABILITY: tracked={tracked}, staged={staged}, untracked={sorted(untracked)}")

    actual_hashes = {name: sha_file(ROOT / name) for name in sorted(UPSTREAM_HASHES)}
    require(actual_hashes == dict(sorted(UPSTREAM_HASHES.items())),
            f"ER2_R3_FAIL_UPSTREAM_IMMUTABILITY: {actual_hashes}")

    tier_rows = list(csv.DictReader(io.StringIO((ROOT / TIER_CONTRACTS).read_text(encoding="utf-8"))))
    tier_row = next(row for row in tier_rows if row["TIER"] == "R3_RESTRICTED_WILD_CLUSTER_BOOTSTRAP")
    tier = next(row for row in read_json(ER2P_PROTOCOL)["tiers"] if row["tier"] == "R3")
    require(r3a.sha(r3a.json_bytes(tier)) == tier_row["TIER_CONTRACT_SHA256"] == R3_TIER_SHA,
            "ER2_R3_FAIL_FROZEN_CONTRACT: tier SHA")
    require(tier_row == {
        "ORDER": "3", "TIER": "R3_RESTRICTED_WILD_CLUSTER_BOOTSTRAP", "ROLE": "INFERENCE_ONLY",
        "FAMILY": "PHYSICAL_ANOMALY", "MULTIPLICITY": "WITHIN_CROP_WCR_COEFFICIENT_P_VALUES",
        "PREVIOUS_TIER": "R2", "NEXT_TIER": "R4", "EXECUTION_STATUS": "NOT_EXECUTED",
        "ER1_NUMERICAL_RESULTS_IDENTITY": ER1_NUMERICAL_IDENTITY, "TIER_CONTRACT_SHA256": R3_TIER_SHA,
    }, "ER2_R3_FAIL_FROZEN_CONTRACT: tier fields")

    adapter = read_json(R3A_LOCK)
    source = adapter["source_audit"]
    checks = {
        "R3A_ADAPTER_VALIDATED": adapter["R3A_ADAPTER_VALIDATED"] is True,
        "A_B_EXACT_EQUIVALENCE": adapter["A_B_EXACT_EQUIVALENCE"] == "PASS",
        "R3A_CONTINUOUS_FLOAT64_ADJUDICATION": adapter["R3A_CONTINUOUS_FLOAT64_ADJUDICATION"] == "PASS",
        "DRAW_MATRIX_IDENTITY": adapter["DRAW_MATRIX_IDENTITY"] == "PASS",
        "EXCEEDANCE_COUNT_IDENTITY": adapter["EXCEEDANCE_COUNT_IDENTITY"] == "PASS",
        "ONE_HOT_REFERENCE_INDEPENDENT": source["ONE_HOT_REFERENCE_INDEPENDENT"] is True,
        "JOINT_WCR_NONINTERFERENCE": adapter["JOINT_WCR_NONINTERFERENCE"] == "PASS",
        "ALL_21_TARGETS_COVERED": len(adapter["target_map"]) == 21,
        "RESULT_SPECIFIC_ADAPTER_BRANCHES": source["RESULT_SPECIFIC_ADAPTER_BRANCHES"] == 0,
    }
    require(all(checks.values()), f"ER2_R3_FAIL_R3A_PREREQUISITE: {checks}")
    require(adapter["target_map"] == r3a.target_map(), "ER2_R3_FAIL_R3A_PREREQUISITE: target map")

    er1_lock = read_json(ER1_LOCK)
    require(er1_lock["er1_numerical_results_identity"]["sha256"] == ER1_NUMERICAL_IDENTITY,
            "ER2_R3_FAIL_PRIMARY_MODEL_IDENTITY: ER1 numerical identity")
    r2_lock = read_json(R2_LOCK)
    require(r2_lock["scientific_lock_status"] == "RESULTS_LOCKED_PENDING_DIRECTOR_REVIEW"
            and r2_lock["completion_status"] == "ER2_R2_PASS_RESULTS_LOCKED_READY_FOR_DIRECTOR_REVIEW"
            and git("merge-base", "--is-ancestor", R2_FREEZE_SHA, R3A_FREEZE_SHA) == "",
            "ER2_R3_FAIL_R3A_PREREQUISITE: R2 certified lifecycle")

    return {
        "git_identity": identity,
        "upstream_sha256": actual_hashes,
        "r3_tier_contract": tier,
        "r3a_certification": checks,
        "temporal_firewall_before_execution": {
            "PRIMARY_RESULTS_KNOWN": True,
            "R1_RESULTS_KNOWN": True,
            "R2_RESULTS_KNOWN": True,
            "R3_RESULTS_KNOWN_BEFORE_EXECUTION": False,
            "R3_METHOD_FROZEN_BEFORE_R3_RESULTS": True,
            "R3_TARGETS_FROZEN_BEFORE_R3_RESULTS": True,
        },
    }


def array_sha(values: Any) -> str:
    return sha_bytes(np.asarray(values, dtype="<f8").tobytes(order="C"))


def key_sha(keys: list[list[str]]) -> str:
    return sha_bytes(compact_json_bytes(keys))


def status(p_value: float) -> str:
    return "BELOW_0.05" if float(p_value) < ALPHA else "NOT_BELOW_0.05"


def agreement(left: str, right: str) -> str:
    return "CONSISTENCY" if left == right else "DISAGREEMENT_REPORTED_NOT_RESOLVED_BY_SELECTION"


def bootstrap_summary(audit: dict[str, Any]) -> dict[str, Any]:
    batches = audit["batches"]
    counts = [int(batch["count"]) for batch in batches]
    require(counts == BATCH_PARTITION, "ER2_R3_FAIL_FROZEN_CONTRACT: batch partition")
    draws = np.concatenate([np.asarray(batch["draws"], dtype=np.int8) for batch in batches], axis=1)
    statistics = np.concatenate([np.asarray(batch["statistics"], dtype="<f8") for batch in batches])
    initial_state = np.random.PCG64(SEED).state
    exceedances = int(audit["exceedances"])
    invalid = int(audit["invalid_replications"])
    exact_p = r3a.finite_p(exceedances, REPLICATIONS)
    require(exact_p == audit["exact_p"], "ER2_R3_FAIL_FROZEN_CONTRACT: finite p")
    require(invalid == 0, "ER2_R3_HOLD_INVALID_BOOTSTRAP_REPLICATIONS")
    return {
        "observed_statistic": float(audit["observed_statistic"]),
        "exceedances": exceedances,
        "invalid_replications": invalid,
        "p_numerator": 1 + exceedances,
        "p_denominator": REPLICATIONS + 1,
        "exact_p": exact_p,
        "batch_partition": counts,
        "full_draw_matrix_sha256": sha_bytes(draws.tobytes(order="C")),
        "initial_rng_state_sha256": sha_bytes(compact_json_bytes(initial_state)),
        "final_rng_state_sha256": sha_bytes(compact_json_bytes(batches[-1]["rng_state"])),
        "bootstrap_statistic_sha256": sha_bytes(statistics.tobytes(order="C")),
    }


def load_er1_references() -> tuple[dict[tuple[str, str], dict[str, str]], dict[str, dict[str, str]]]:
    coefficients = list(csv.DictReader(io.StringIO((ROOT / ER1_COEFFICIENTS).read_text(encoding="utf-8"))))
    joint = list(csv.DictReader(io.StringIO((ROOT / ER1_JOINT).read_text(encoding="utf-8"))))
    return ({(row["CROP_CODE"], row["CLIMATE_VARIABLE"]): row for row in coefficients},
            {row["CROP_CODE"]: row for row in joint})


def real_calculation() -> dict[str, Any]:
    pre = preflight()
    er1_coefficients, er1_joint = load_er1_references()
    r2_samples = read_json(R2_LOCK)["sample_identity"]
    target_map = read_json(R3A_LOCK)["target_map"]
    targets_by_crop: dict[str, list[dict[str, Any]]] = {}
    for target in target_map:
        targets_by_crop.setdefault(target["CROP_CODE"], []).append(target)

    transient_outcomes, perennial_outcomes, source_metadata = er1.read_outcome_sources()
    transient_exposures = pq.read_table(ed1.TRANSIENT_PATH, columns=list(ed1.TRANSIENT_COLUMNS)).to_pandas()
    perennial_exposures = ed1.read_perennial_primary()
    coefficients: list[dict[str, Any]] = []
    joint_rows: list[dict[str, Any]] = []
    samples: list[dict[str, Any]] = []
    executions: list[dict[str, Any]] = []
    model_identity: dict[str, Any] = {}

    for crop_code, crop in ed1.CROPS.items():
        if crop_code in {"14010020000", "14010070000"}:
            frame, columns = er1.transient_design_with_outcome(transient_exposures, transient_outcomes, crop_code)
            source_sha = source_metadata["transient"]["sha256"]
        else:
            frame, columns = er1.perennial_design_with_outcome(perennial_exposures, perennial_outcomes, crop_code)
            source_sha = source_metadata["perennial"]["sha256"]
        period = str(crop["period_column"])
        frame = frame.sort_values(["UBIGEO", period], kind="mergesort").reset_index(drop=True)
        y = pd.to_numeric(frame["YIELD"], errors="coerce").to_numpy(dtype=float)
        x = frame[columns].to_numpy(dtype=float)
        keys = frame[["UBIGEO", period]].astype(str).to_numpy().tolist()
        expected = er1.EXPECTED_SAMPLE[crop_code]
        frozen_sample = r2_samples[crop_code]
        actual = {
            "n": len(frame), "districts": int(frame["UBIGEO"].nunique()),
            "effective": int(ed1.effective_cluster_audit(
                frame, ed1.absorb_fixed_effects(x, ed1.fe_matrix(frame, period))
            )["effective_contributing_clusters"]),
            "periods": int(frame[period].nunique()),
        }
        require(actual == expected, f"ER2_R3_FAIL_PRIMARY_MODEL_IDENTITY: sample {crop_code}")
        require(keys == frozen_sample["er1_ordered_keys"],
                f"ER2_R3_FAIL_PRIMARY_MODEL_IDENTITY: ordered keys {crop_code}")
        require(np.isfinite(y).all() and np.isfinite(x).all(),
                f"ER2_R3_FAIL_PRIMARY_MODEL_IDENTITY: nonfinite data {crop_code}")
        require(int(frame.duplicated(["UBIGEO", period]).sum()) == 0,
                f"ER2_R3_FAIL_PRIMARY_MODEL_IDENTITY: duplicate keys {crop_code}")

        fit = ed1.fit_two_way_fe_cr2(frame, columns, period, y)
        differences = []
        signs = []
        for index, variable in enumerate(columns):
            reference = er1_coefficients[(crop_code, variable)]
            difference = abs(float(fit["beta"][index]) - float(reference["BETA"]))
            differences.append(difference)
            signs.append(np.sign(fit["beta"][index]) == np.sign(float(reference["BETA"])))
        require(max(differences) <= MODEL_IDENTITY_TOLERANCE and all(signs),
                f"ER2_R3_FAIL_PRIMARY_MODEL_IDENTITY: beta {crop_code} {differences}")
        model_identity[crop_code] = {
            "status": "PASS", "maximum_beta_absolute_difference": max(differences),
            "absolute_tolerance_frozen_before_outcome_access": MODEL_IDENTITY_TOLERANCE,
            "same_sign_all_coefficients": all(signs), "same_y": True, "same_x": True,
            "same_district_fe": True, "same_period_fe": True, "same_weighting": True,
            "same_cluster_unit": True, "r3_model_specification_change": False,
        }

        samples.append({
            "CROP_CODE": crop_code, "CROP": crop["crop"], "MODEL_ID": crop["model_id"],
            "N": actual["n"], "NOMINAL_DISTRICTS": actual["districts"],
            "EFFECTIVE_DISTRICTS": actual["effective"], "PERIODS": actual["periods"],
            "ORDERED_KEY_SHA256": key_sha(keys), "Y_FLOAT64_SHA256": array_sha(y),
            "X_FLOAT64_SHA256": array_sha(x), "ER1_ORDERED_KEYS_EXACT": True,
            "ER1_Y_SOURCE_EXACT": source_sha in {er1.TRANSIENT_OUTCOME_SHA, er1.PERENNIAL_OUTCOME_SHA},
            "MISSING_Y": int(pd.isna(frame["YIELD"]).sum()), "MISSING_X": int(frame[columns].isna().sum().sum()),
            "DUPLICATE_KEYS": 0, "ROW_ORDER": "SORTED_UBIGEO_THEN_FROZEN_PERIOD",
            "CLUSTER_ORDER": "SORTED_UBIGEO", "OUTCOME_SCALE": "YIELD_LEVEL_TM_PER_HA",
        })

        crop_coefficients: list[dict[str, Any]] = []
        for target in targets_by_crop[crop_code]:
            variable = target["VARIABLE"]
            result = r3a.named_coefficient_wcr_adapter(
                frame, columns, period, y, variable, replications=REPLICATIONS, seed=SEED,
                batch_size=BATCH_SIZE,
            )
            summary = bootstrap_summary(result["audit"])
            reference = er1_coefficients[(crop_code, variable)]
            target_beta = float(result["audit"]["fit"]["beta"][0])
            require(abs(target_beta - float(reference["BETA"])) <= MODEL_IDENTITY_TOLERANCE,
                    f"ER2_R3_FAIL_PRIMARY_MODEL_IDENTITY: adapter beta {crop_code} {variable}")
            cr2_holm_status = status(float(reference["HOLM_ADJUSTED_P_VALUE"]))
            row = {
                "CROP_CODE": crop_code, "CROP": crop["crop"], "MODEL_ID": crop["model_id"],
                "CLIMATE_VARIABLE": variable, "WINDOW": reference["WINDOW"],
                "ER1_BETA_REFERENCE": float(reference["BETA"]),
                "ER1_CR2_STANDARD_ERROR_REFERENCE": float(reference["CR2_STANDARD_ERROR"]),
                "ER1_SATTERTHWAITE_DF_REFERENCE": float(reference["SATTERTHWAITE_DF"]),
                "ER1_CR2_P_REFERENCE": float(reference["P_VALUE_TWO_SIDED"]),
                "ER1_CR2_HOLM_P_REFERENCE": float(reference["HOLM_ADJUSTED_P_VALUE"]),
                "R3_OBSERVED_ABSOLUTE_T": summary["observed_statistic"],
                "WCR_EXCEEDANCE_COUNT": summary["exceedances"],
                "INVALID_REPLICATIONS": summary["invalid_replications"],
                "WCR_P_NUMERATOR": summary["p_numerator"], "WCR_P_DENOMINATOR": summary["p_denominator"],
                "WCR_RAW_P": summary["exact_p"], "WITHIN_CROP_HOLM_WCR_P": None,
                "CR2_HOLM_STATUS": cr2_holm_status, "WCR_HOLM_STATUS": None,
                "INFERENCE_COMPARISON": None, "PRIMARY_CLIMATE_FAMILY": "PHYSICAL_ANOMALY",
                "OUTCOME_SCALE": "YIELD_LEVEL_TM_PER_HA", "R3_MODEL_SPECIFICATION_CHANGE": False,
            }
            crop_coefficients.append(row)
            executions.append(execution_row(crop_code, crop["crop"], variable, "COEFFICIENT", actual["districts"], summary))

        adjusted = er1.holm_adjust(np.asarray([row["WCR_RAW_P"] for row in crop_coefficients], dtype=float))
        for row, adjusted_p in zip(crop_coefficients, adjusted):
            row["WITHIN_CROP_HOLM_WCR_P"] = float(adjusted_p)
            row["WCR_HOLM_STATUS"] = status(float(adjusted_p))
            row["INFERENCE_COMPARISON"] = agreement(row["CR2_HOLM_STATUS"], row["WCR_HOLM_STATUS"])
        coefficients.extend(crop_coefficients)

        joint_audit = r3a.frozen_wcr_audit(
            frame, columns, period, y, REPLICATIONS, SEED, "ALL_CLIMATE_COEFFICIENTS"
        )
        joint_summary = bootstrap_summary(joint_audit)
        reference_joint = er1_joint[crop_code]
        aht_status = status(float(reference_joint["P_VALUE"]))
        wcr_status = status(joint_summary["exact_p"])
        joint_rows.append({
            "CROP_CODE": crop_code, "CROP": crop["crop"], "MODEL_ID": crop["model_id"],
            "COEFFICIENTS_TESTED": "|".join(columns), "Q": len(columns),
            "JOINT_NULL": "ALL_PRIMARY_CLIMATE_COEFFICIENTS_EQUAL_ZERO_WITHIN_CROP",
            "ER1_AHT_F_REFERENCE": float(reference_joint["F_STATISTIC"]),
            "ER1_AHT_P_REFERENCE": float(reference_joint["P_VALUE"]),
            "R3_OBSERVED_WALD_F": joint_summary["observed_statistic"],
            "WCR_EXCEEDANCE_COUNT": joint_summary["exceedances"],
            "INVALID_REPLICATIONS": joint_summary["invalid_replications"],
            "WCR_P_NUMERATOR": joint_summary["p_numerator"],
            "WCR_P_DENOMINATOR": joint_summary["p_denominator"], "WCR_RAW_P": joint_summary["exact_p"],
            "AHT_STATUS": aht_status, "WCR_STATUS": wcr_status,
            "INFERENCE_COMPARISON": agreement(aht_status, wcr_status), "JOINT_HOLM": "NOT_APPLIED",
        })
        executions.append(execution_row(crop_code, crop["crop"], "ALL_PRIMARY_CLIMATE_COEFFICIENTS", "JOINT", actual["districts"], joint_summary))

    require(len(coefficients) == 21 and len(joint_rows) == 5 and len(executions) == 26,
            "ER2_R3_FAIL_FROZEN_CONTRACT: result inventory")
    invalid_total = sum(int(row["INVALID_REPLICATIONS"]) for row in executions)
    require(invalid_total == 0, "ER2_R3_HOLD_INVALID_BOOTSTRAP_REPLICATIONS")
    return {
        "preflight": pre, "samples": samples, "coefficients": coefficients, "joint_tests": joint_rows,
        "execution_audit": executions, "model_identity": model_identity,
        "invalid_replications_total": invalid_total,
        "r3_coefficient_tests": len(coefficients), "r3_joint_tests": len(joint_rows), "r3_models": len(samples),
        "final_verdict": FINAL_VERDICT,
    }


def execution_row(crop_code: str, crop: str, test_id: str, kind: str, clusters: int,
                  summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "CROP_CODE": crop_code, "CROP": crop, "TEST_ID": test_id, "TEST_KIND": kind,
        "CLUSTER_COUNT": clusters, "SEED": SEED, "B": REPLICATIONS, "BATCH_SIZE": BATCH_SIZE,
        "BATCH_PARTITION": "+".join(map(str, BATCH_PARTITION)), "RNG": "NUMPY_GENERATOR_PCG64",
        "WEIGHTS": "RADEMACHER", "SEED_RESET": "EACH_CROP_CONTRAST_AND_JOINT_TEST",
        "FULL_DRAW_MATRIX_SHA256": summary["full_draw_matrix_sha256"],
        "INITIAL_RNG_STATE_SHA256": summary["initial_rng_state_sha256"],
        "FINAL_RNG_STATE_SHA256": summary["final_rng_state_sha256"],
        "BOOTSTRAP_STATISTIC_SHA256": summary["bootstrap_statistic_sha256"],
        "EXCEEDANCE_COUNT": summary["exceedances"], "INVALID_REPLICATIONS": summary["invalid_replications"],
        "FINITE_P_NUMERATOR": summary["p_numerator"], "FINITE_P_DENOMINATOR": summary["p_denominator"],
    }


def csv_bytes(rows: list[dict[str, Any]], fields: tuple[str, ...]) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=list(fields), lineterminator="\n", extrasaction="raise")
    writer.writeheader()
    for row in rows:
        serialized = {}
        for field in fields:
            value = row[field]
            if isinstance(value, (float, np.floating)):
                serialized[field] = canonical_float(value)
            elif isinstance(value, bool):
                serialized[field] = "TRUE" if value else "FALSE"
            else:
                serialized[field] = str(value)
        writer.writerow(serialized)
    return output.getvalue().encode("utf-8")


def report_bytes(data: dict[str, Any]) -> bytes:
    lines = [
        "# ER2 R3 Restricted Wild-Cluster Bootstrap Real Execution v1", "",
        f"FINAL_VERDICT={FINAL_VERDICT}", "", "## Contract", "",
        "R3 changes inference only. The five ER1 physical-anomaly models, samples, outcomes, regressors, windows, fixed effects, unweighted specification, and district clustering are unchanged.",
        "Each restricted null-imposed test uses 9,999 PCG64/Rademacher draws, seed 20260903 reset per contrast and joint test, deterministic sorted clusters/rows, and batches 1000 x 9 + 999.",
        "Finite p-values use (1+EXCEEDANCES)/10000. Invalid replications are zero. Coefficient WCR p-values receive Holm step-down only within crop; joint WCR p-values remain raw.", "",
        "## Coefficient sensitivity", "",
        "| Crop | Variable | ER1 beta | ER1 CR2 p | ER1 Holm p | WCR p | WCR Holm p | Comparison |",
        "|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in data["coefficients"]:
        lines.append(
            f"| {row['CROP']} | {row['CLIMATE_VARIABLE']} | {row['ER1_BETA_REFERENCE']:.9g} | "
            f"{row['ER1_CR2_P_REFERENCE']:.9g} | {row['ER1_CR2_HOLM_P_REFERENCE']:.9g} | "
            f"{row['WCR_RAW_P']:.9g} | {row['WITHIN_CROP_HOLM_WCR_P']:.9g} | {row['INFERENCE_COMPARISON']} |"
        )
    lines += ["", "## Crop-level joint sensitivity", "",
              "| Crop | ER1 AHT p | Joint WCR p | Comparison |", "|---|---:|---:|---|"]
    for row in data["joint_tests"]:
        lines.append(f"| {row['CROP']} | {row['ER1_AHT_P_REFERENCE']:.9g} | {row['WCR_RAW_P']:.9g} | {row['INFERENCE_COMPARISON']} |")
    lines += [
        "", "## Interpretation firewall", "",
        "Differences are reported as inferential sensitivity and are not resolved by selecting the method that yields significance. WCR does not replace ER1 CR2 inference. No cross-crop ranking, robustness score, vote count, global five-crop FWER, or global 21-coefficient Holm was calculated.",
        "R4, R5, R6, ENSO scenarios, GVP, VaR/CVaR, A1/A2, and optimization were not executed.", "",
        "NEXT_TIER_AUTHORIZATION_STATUS=NOT_AUTHORIZED", "NEXT_ACTION=RETURN_TO_SCIENTIFIC_DIRECTOR_FOR_R3_REVIEW", "",
    ]
    return "\n".join(lines).encode("utf-8")


def render(data: dict[str, Any], reproduction: dict[str, Any]) -> dict[Path, bytes]:
    payloads = {
        COEFFICIENTS: csv_bytes(data["coefficients"], COEFFICIENT_FIELDS),
        JOINT: csv_bytes(data["joint_tests"], JOINT_FIELDS),
        SAMPLES: csv_bytes(data["samples"], SAMPLE_FIELDS),
        EXECUTION: csv_bytes(data["execution_audit"], EXECUTION_FIELDS),
        REPORT: report_bytes(data),
    }
    artifact_hashes = {path.as_posix(): sha_bytes(payload) for path, payload in payloads.items()}
    lock = {
        "schema_version": "1.0.0", "project": PROJECT, "gate": GATE,
        "status": "RESULTS_LOCKED_PENDING_DIRECTOR_REVIEW", "final_verdict": FINAL_VERDICT,
        "tier_id": "R3_RESTRICTED_WILD_CLUSTER_BOOTSTRAP", "tier_order": 3,
        "tier_contract_sha256": R3_TIER_SHA, "er2p_freeze_sha": ER2P_FREEZE_SHA,
        "er1_freeze_sha": ER1_FREEZE_SHA, "er1_numerical_results_identity": ER1_NUMERICAL_IDENTITY,
        "r2_freeze_sha": R2_FREEZE_SHA, "r2_final_certified_predecessor_lock_sha256": R2_REPORTING_LOCK_SHA,
        "r3a_freeze_sha": R3A_FREEZE_SHA, "r3a_certified_adapter_lock_sha256": R3A_LOCK_SHA,
        "primary_results_known": True, "r1_results_known": True, "r2_results_known": True,
        "r3_results_known_before_execution": False, "r3_method_frozen_before_results": True,
        "r3_targets_frozen_before_results": True,
        "climate_family": "PHYSICAL_ANOMALY", "outcome_scale": "YIELD_LEVEL_TM_PER_HA",
        "model_specification_change": False, "targets": read_json(R3A_LOCK)["target_map"],
        "joint_tests": [row["CROP_CODE"] for row in data["joint_tests"]],
        "samples": data["samples"], "model_identity": data["model_identity"],
        "bootstrap_contract": {
            "restricted": True, "null_imposed": True, "weights": "RADEMACHER", "cluster": "DISTRICT",
            "rng": "NUMPY_GENERATOR_PCG64", "seed": SEED, "replications": REPLICATIONS,
            "batch_size": BATCH_SIZE, "batch_partition": BATCH_PARTITION,
            "cluster_order": "SORTED_UBIGEO", "row_order": "SORTED_UBIGEO_THEN_FROZEN_PERIOD",
            "coefficient_order": "FROZEN_ED1_REGRESSOR_ORDER",
            "seed_reset": "EACH_CROP_CONTRAST_AND_JOINT_TEST",
            "finite_replication_correction": "(1+EXCEEDANCES)/(B+1)", "finite_p_denominator": 10000,
            "invalid_policy": "HOLD_NO_DROP_NO_REDRAW_NO_SEED_OR_DENOMINATOR_CHANGE",
        },
        "coefficient_results": data["coefficients"], "joint_wcr_results": data["joint_tests"],
        "execution_audit": data["execution_audit"],
        "invalid_replications_total": data["invalid_replications_total"],
        "multiplicity": "HOLM_STEP_DOWN_WITHIN_CROP_WCR_COEFFICIENT_P_VALUES",
        "holm_family_sizes": [3, 3, 3, 6, 6], "joint_holm": "NOT_APPLIED",
        "global_fwer": "NOT_CALCULATED", "comparison_semantics": [
            "INFERENTIAL_SENSITIVITY", "CONSISTENCY", "DISAGREEMENT_REPORTED_NOT_RESOLVED_BY_SELECTION"
        ],
        "two_run_reproducibility": reproduction,
        "implementation_sha256": sha_file(ROOT / SCRIPT), "test_sha256": sha_file(ROOT / TEST),
        "artifact_sha256": artifact_hashes,
        "execution_firewall": {
            "R4_AUTHORIZATION_STATUS": "NOT_AUTHORIZED", "R4_EXECUTED": False,
            "R5_EXECUTED": False, "R6_EXECUTED": False, "ENSO_SCENARIOS": "NOT_EXECUTED",
            "GVP": "NOT_EXECUTED", "VAR_CVAR": "NOT_EXECUTED", "A1_A2": "NOT_EXECUTED",
            "OPTIMIZATION": "NOT_EXECUTED",
        },
        "NEXT_TIER_AUTHORIZATION_STATUS": "NOT_AUTHORIZED",
        "next_action": "RETURN_TO_SCIENTIFIC_DIRECTOR_FOR_R3_REVIEW",
    }
    payloads[LOCK] = json_bytes(lock)
    return payloads


def run_worker(path: Path) -> None:
    path.write_bytes(json_bytes(real_calculation()))


def build(output_root: Path) -> dict[str, str]:
    preflight()
    with tempfile.TemporaryDirectory(prefix="er2_r3_") as temporary:
        temporary_path = Path(temporary)
        runs = [temporary_path / "run1.json", temporary_path / "run2.json"]
        for run in runs:
            subprocess.run([sys.executable, str(ROOT / SCRIPT), "--worker", str(run)], cwd=ROOT, check=True)
        run_bytes = [path.read_bytes() for path in runs]
        require(run_bytes[0] == run_bytes[1], "ER2_R3_HOLD_NONDETERMINISTIC_BOOTSTRAP")
        calculation_sha = sha_bytes(run_bytes[0])
        reproduction = {
            "status": "PASS", "independent_processes": 2,
            "run_1_calculation_sha256": calculation_sha, "run_2_calculation_sha256": sha_bytes(run_bytes[1]),
            "calculation_bytes_exact": True, "rendered_output_bytes_exact": True,
        }
        data = json.loads(run_bytes[0].decode("utf-8"))
        rendered_one = render(data, reproduction)
        rendered_two = render(json.loads(run_bytes[1].decode("utf-8")), reproduction)
        require(rendered_one == rendered_two, "ER2_R3_HOLD_NONDETERMINISTIC_BOOTSTRAP")
        for relative, payload in rendered_one.items():
            destination = output_root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(payload)
    return {path.as_posix(): sha_file(output_root / path) for path in OUTPUTS}


def check_existing() -> dict[str, str]:
    lock = read_json(LOCK)
    require(lock["final_verdict"] == FINAL_VERDICT, "ER2_R3_FAIL_TEST_REGRESSION: verdict")
    for relative, expected in lock["artifact_sha256"].items():
        require(sha_file(ROOT / relative) == expected, f"ER2_R3_FAIL_TEST_REGRESSION: {relative}")
    require(lock["implementation_sha256"] == sha_file(ROOT / SCRIPT), "ER2_R3_FAIL_TEST_REGRESSION: script")
    require(lock["test_sha256"] == sha_file(ROOT / TEST), "ER2_R3_FAIL_TEST_REGRESSION: test")
    return {path.as_posix(): sha_file(ROOT / path) for path in OUTPUTS}


def main() -> int:
    parser = argparse.ArgumentParser(description="Execute frozen real ER2-R3 restricted WCR only.")
    parser.add_argument("--worker", type=Path)
    parser.add_argument("--output-root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.worker:
        run_worker(args.worker)
        return 0
    hashes = check_existing() if args.check else build(args.output_root.resolve())
    lock = json.loads((args.output_root.resolve() / LOCK).read_text(encoding="utf-8"))
    print("R3_PREFLIGHT=PASS")
    print("R3_EXECUTED=TRUE")
    print(f"R3_MODELS={len(lock['samples'])}")
    print(f"R3_COEFFICIENT_TESTS={len(lock['coefficient_results'])}")
    print(f"R3_JOINT_TESTS={len(lock['joint_wcr_results'])}")
    print(f"R3_INVALID_REPLICATIONS_TOTAL={lock['invalid_replications_total']}")
    print(f"R3_TWO_RUN_REPRODUCIBILITY={lock['two_run_reproducibility']['status']}")
    for relative, digest in hashes.items():
        print(f"SHA256 {relative} {digest}")
    print(f"FINAL_VERDICT={lock['final_verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
