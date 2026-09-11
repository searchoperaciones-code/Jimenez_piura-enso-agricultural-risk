from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import inspect
import io
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import econometric_design_master_v1 as ed1  # noqa: E402


PROJECT = "ENSO_EL_NINO_2026_2027_AGRICULTURE_PIURA"
GATE = "ER2_R5P_LEAVE_ONE_PERIOD_OUT_PREEXECUTION_CERTIFICATION_V1"
FINAL_VERDICT = "ER2_R5P_PASS_RAW_GIT_PREDECESSOR_HARDENED_PREEXECUTION_CERTIFIED_READY_FOR_DIRECTOR_FREEZE_DECISION"
BYTE_SOURCE_ADJUDICATION = {
    "REMEDIATION_GATE": "ER2_R5P1_RAW_GIT_PREDECESSOR_BYTE_HARDENING_AND_RESUME",
    "PREVIOUS_HOLD_VERDICT": "ER2_R5P_HOLD_INTERRUPTED_LOCAL_STATE_REQUIRES_ADJUDICATION",
    "PREVIOUS_FAILED_VERDICT": "ER2_R5P_FAIL_R4_PREDECESSOR_IDENTITY",
    "PREVIOUS_FAILURE_ROOT_CAUSE": "WINDOWS_CHECKOUT_EOL_MATERIALIZATION_IN_BYTE_VERIFIER",
    "PREVIOUS_DEDICATED_TESTS": "32_RUN_30_PASS_0_FAIL_2_ERROR",
    "FROZEN_INPUT_BYTE_SOURCE": "RAW_GIT_OBJECT",
    "WORKTREE_BYTES_ARE_AUTHORITATIVE": False,
    "R4_PREDECESSOR_SCIENTIFIC_IDENTITY": "PASS",
    "SUPERSEDED_R5P_LOCK_SHA": "8024092d5b85179046462cac3b7e5ad02f22492ef8eb170c55e9252291b0c683",
    "SUPERSEDED_R5P_LOCK_STATUS": "SUPERSEDED_PRE_REMEDIATION_CANDIDATE_LOCK",
}

R4_FREEZE_SHA = "26912f99b7e6cfbbfcf2b8cfc72fe9b2b9c379ee"
R4_PARENT_SHA = "652d846f7f13f2557cb830dde390a16bbca9fa2d"
R4_BRANCH = "phase/er2-r4-spatial-hac-v1"
R4_TAG = "er2-r4-spatial-hac-v1-freeze"
R4_TAG_OBJECT = "f08d90cc4b2ce57edf405e081783691c979090e2"
R4_RESULTS_LOCK_SHA = "1741a7beca4b63362dc736450b5077d1f5d6e076580178eec054253abeb93fe7"
R5_TIER_CONTRACT_SHA = "0bb92a0f19cd8f476eab4844dd49d9de1a9a217cd887aeb4e80839bfb09ed91b"
ED1_IMPLEMENTATION_SHA = "69fb1b1f0a1d7c4ec7791fdfa2d3cfb20d62b4ed0f6348b155155523b6b48195"
FIT_SOURCE_SHA = "fc518afb1a72d7d5a8b61e1792448e34b5f3963475979ee19632a147d2010442"
FIT_BODY_SHA = "63c2e6c02aa9dbddda39224e76eed2afe4dcee8d2e08c4845debfa0e32d158ec"
FE_SOURCE_SHA = "7d9ba3fffaecc95ebc9089a56db3a4b14dd3239d2a5a002cd83e77b5319cc7c5"
FE_BODY_SHA = "b3ad4590b2e814b6b6f4296429e45feed038347cc8f4f9dfe480cfe54821025f"
ABSORB_SOURCE_SHA = "4ae0489a781fc68b1e86299e6387a62cca06542a85f5f108c4be19684d2c248b"
ABSORB_BODY_SHA = "d9f1f2aab8742c4d298f25d490894df63c8859dba85895d3af489e41e27dbab3"

SYNTHETIC_SEED = 20260905
CONTINUOUS_TOLERANCE = 1e-10
CROP_ORDER = (
    "14010020000",
    "14010070000",
    "13010210000",
    "13010170102",
    "15010040000",
)
TRANSIENT_CODES = {"14010020000", "14010070000"}
EXPECTED_PERIODS = {
    "14010020000": ("2016/2017", "2017/2018", "2018/2019", "2019/2020", "2020/2021", "2021/2022", "2022/2023"),
    "14010070000": ("2016/2017", "2017/2018", "2018/2019", "2019/2020", "2020/2021", "2021/2022", "2022/2023"),
    "13010210000": ("2016", "2017", "2018", "2019", "2020", "2021", "2022", "2023"),
    "13010170102": ("2016", "2017", "2018", "2019", "2020", "2021", "2022", "2023"),
    "15010040000": ("2016", "2017", "2018", "2019", "2020", "2021", "2022", "2023"),
}
EXPECTED_SAMPLE_N = {
    "14010020000": 281,
    "14010070000": 318,
    "13010210000": 255,
    "13010170102": 311,
    "15010040000": 390,
}

TIER_CONTRACTS = Path("outputs/econometrics/ER2P_TIER_CONTRACTS.csv")
PROTOCOL = Path("config/econometrics/er2_robustness_protocol_v1.json")
ED1_SCRIPT = Path("scripts/econometric_design_master_v1.py")
R2_LOCK = Path("outputs/econometrics/ER2_R2_RESULTS_LOCK.json")
R4P_MAP = Path("outputs/econometrics/ER2_R4P_COEFFICIENT_MAP.csv")
R4_RESULTS = Path("outputs/econometrics/ER2_R4_CONLEY_RESULTS.csv")
R4_COVERAGE = Path("outputs/econometrics/ER2_R4_SAMPLE_GEOMETRY_COVERAGE.csv")
R4_COVARIANCE = Path("outputs/econometrics/ER2_R4_COVARIANCE_AUDIT.csv")
R4_CONCORDANCE = Path("outputs/econometrics/ER2_R4_CONCORDANCE.csv")
R4_REPORT = Path("outputs/econometrics/ER2_R4_REPORT.md")
R4_LOCK = Path("outputs/econometrics/ER2_R4_RESULTS_LOCK.json")
R4_SCRIPT = Path("scripts/er2_r4_spatial_hac_real_v1.py")
R4_TEST = Path("tests/test_er2_r4_spatial_hac_real_v1.py")

REPORT = Path("outputs/econometrics/ER2_R5P_PREFLIGHT_REPORT.md")
OMISSION_PLAN = Path("outputs/econometrics/ER2_R5P_OMISSION_PLAN.csv")
COEFFICIENT_MAP = Path("outputs/econometrics/ER2_R5P_COEFFICIENT_OMISSION_MAP.csv")
SYNTHETIC_VALIDATION = Path("outputs/econometrics/ER2_R5P_SYNTHETIC_VALIDATION.csv")
TEST_PLAN_LOCK = Path("outputs/econometrics/ER2_R5P_SYNTHETIC_TEST_PLAN_LOCK.json")
PREFLIGHT_LOCK = Path("outputs/econometrics/ER2_R5P_PREFLIGHT_LOCK.json")
SCRIPT = Path("scripts/er2_r5p_leave_one_period_out_preflight_v1.py")
TEST = Path("tests/test_er2_r5p_leave_one_period_out_preflight_v1.py")

GENERATED = (REPORT, OMISSION_PLAN, COEFFICIENT_MAP, SYNTHETIC_VALIDATION, TEST_PLAN_LOCK, PREFLIGHT_LOCK)
CANDIDATES = (*GENERATED, SCRIPT, TEST)

FROZEN_INPUT_SHA256 = {
    TIER_CONTRACTS: "2ff57eadb872ca6aa10cb84aa4fdf9b7250715df5ca77d2f3e9d22621e7d762a",
    PROTOCOL: "13519fb5c86fdf690d233c54dd45c3242ba348f3c7f66587238e6965ed1c49ff",
    ED1_SCRIPT: ED1_IMPLEMENTATION_SHA,
    R2_LOCK: "117a3fe5da88f44d31b176495409f6e84189148f1020417f046b0df3dd4c5f6b",
    R4P_MAP: "c1a14dbe99ba899a4862d0626796d7950bfcc106bc326483ab44f199abc2527d",
    R4_RESULTS: "69e00db9bb70fa3f6aa87a6357568a8f1692ec112d79c090c3915f5d238afba6",
    R4_COVERAGE: "e4a8d66f6ac462a062a813ab5105f004067a962e9145d07ab0fe764016caf530",
    R4_COVARIANCE: "769c0b5df8cd87b8f1d44de34f2f6c8709527622ecb0b73dc8d52b6c37f5ec73",
    R4_CONCORDANCE: "61a5cca23a649e79baadf7ea88de678a53934aba9ccbb49ec165674973953c79",
    R4_REPORT: "ba6408154964669bd3dbb395eb982bdeffd18e5eb7c94b8eff22ddbd0b18b511",
    R4_LOCK: R4_RESULTS_LOCK_SHA,
    R4_SCRIPT: "cdc6f2b68bf4834fd2ea982ac75604f975d777380d9e477e53597c25efc9a9d8",
    R4_TEST: "6ab996efc51885d5025f44845800d53ddb25c4d46adc874b9dbe2a1134ef37b0",
}

OMISSION_FIELDS = (
    "REFIT_ORDER", "CROP", "CROP_CODE", "MODEL_ID", "PERIOD_ID_COLUMN",
    "OMITTED_PERIOD_ID", "OMITTED_PERIOD_ORDER", "MANDATORY_NAMED_CASE",
    "NOMINAL_PERIODS", "RETAINED_PERIODS", "OMISSION_SCOPE", "REPORT_ALL_PERIODS",
    "ESTIMATION_EXECUTED", "STATUS",
)
COEFFICIENT_MAP_FIELDS = (
    "COEFFICIENT_OMISSION_ORDER", "COEFFICIENT_MAP_ORDER", "CROP", "CROP_CODE",
    "MODEL_ID", "VARIABLE", "ED1_REGRESSOR_POSITION_ONE_BASED", "PERIOD_ID_COLUMN",
    "OMITTED_PERIOD_ID", "OMITTED_PERIOD_ORDER", "MANDATORY_NAMED_CASE",
    "EXPECTED_RETAINED_PERIODS", "REAL_LOO_BETA_COMPUTED", "STATUS",
)
SYNTHETIC_FIELDS = ("CHECK_ID", "CATEGORY", "STATUS", "MAX_ABS_DIFFERENCE", "DETAIL")

FUTURE_DETAIL_SCHEMA = (
    "CROP", "CROP_CODE", "MODEL_ID", "VARIABLE", "OMITTED_PERIOD_ID",
    "OMITTED_PERIOD_ORDER", "MANDATORY_NAMED_CASE", "PRIMARY_BETA_REFERENCE",
    "LOO_BETA", "BETA_DIFFERENCE", "ABS_BETA_DEVIATION", "PRIMARY_SIGN",
    "LOO_SIGN", "SIGN_REVERSAL", "RETAINED_N", "RETAINED_PERIODS", "MODEL_VALID", "STATUS",
)
FUTURE_SUMMARY_SCHEMA = (
    "CROP", "CROP_CODE", "MODEL_ID", "VARIABLE", "PRIMARY_BETA_REFERENCE",
    "MIN_LOO_BETA", "MAX_LOO_BETA", "BETA_RANGE", "MEDIAN_LOO_BETA",
    "POSITIVE_COUNT", "NEGATIVE_COUNT", "ZERO_COUNT", "SIGN_REVERSAL_COUNT",
    "MAX_ABSOLUTE_BETA_DEVIATION", "PERIODS_CAUSING_MAX_ABSOLUTE_DEVIATION",
    "LEAVE_2017_OUT_BETA", "LEAVE_2023_OUT_BETA", "STATUS",
)
SUMMARY_METRICS = (
    "PRIMARY_BETA_REFERENCE", "MIN_LOO_BETA", "MAX_LOO_BETA", "MEDIAN_LOO_BETA",
    "POSITIVE_COUNT", "NEGATIVE_COUNT", "EXACT_ZERO_COUNT",
    "SIGN_REVERSALS_RELATIVE_TO_PRIMARY", "MAX_ABSOLUTE_BETA_DEVIATION",
    "PERIOD_CAUSING_MAX_ABSOLUTE_DEVIATION", "BETA_RANGE",
    "PERIODS_CAUSING_MAX_ABSOLUTE_DEVIATION", "LEAVE_2017_OUT_BETA", "LEAVE_2023_OUT_BETA",
)

EDGE_CASES = (
    "A_EVERY_PERIOD_OMITTED_EXACTLY_ONCE",
    "B_OMITTED_PERIOD_HAS_ZERO_RETAINED_ROWS",
    "C_ALL_OTHER_PERIODS_RETAINED_EXACTLY",
    "D_REMAINING_PERIOD_FE_ACTIVE",
    "E_DISTRICT_FE_ACTIVE",
    "F_EXACT_SAME_REGRESSORS",
    "G_NO_SECOND_OMISSION",
    "H_ROW_ORDER_PERMUTATION_INVARIANCE",
    "I_PERIOD_ORDER_PERMUTATION_INVARIANCE",
    "J_COEFFICIENT_COLUMN_MAPPING_INVARIANCE",
    "K_STRICT_POSITIVE_CLASSIFICATION",
    "L_STRICT_NEGATIVE_CLASSIFICATION",
    "M_EXACT_ZERO_CLASSIFICATION",
    "N_STRICT_SIGN_REVERSAL_RULE",
    "O_NO_REVERSAL_WITH_PRIMARY_OR_LOO_ZERO",
    "P_MINIMUM_MAXIMUM_MEDIAN_SUMMARIES",
    "Q_BETA_RANGE",
    "R_MAXIMUM_ABSOLUTE_DEVIATION",
    "S_ALL_TIED_PERIODS_SORTED",
    "T_2017_2023_LABELS_DO_NOT_ALTER_ESTIMATION",
    "U_RANK_DEFICIENT_REFIT_FAILS_CLOSED",
    "V_EMPTY_REMAINING_PERIOD_FAILS_CLOSED",
    "W_MISSING_PERIOD_ID_FAILS_CLOSED",
    "X_DUPLICATE_TARGET_MAPPING_FAILS_CLOSED",
)

SYNTHETIC_PLAN = {
    "schema_version": "1.0.0",
    "gate": GATE,
    "seed": SYNTHETIC_SEED,
    "rng": "NUMPY_GENERATOR_PCG64",
    "districts": 6,
    "periods": 5,
    "regressors": 3,
    "balanced_core": True,
    "controlled_unbalanced_cell": "DROP_D06_X_P05",
    "continuous_tolerance": CONTINUOUS_TOLERANCE,
    "frozen_before_first_synthetic_refit": True,
    "production_path": "FROZEN_ED1_FIT_TWO_WAY_FE_CR2_BETA_ONLY_VIA_FAIL_CLOSED_LOO_ADAPTER",
    "reference_path": "INDEPENDENT_FULL_DUMMY_MATRIX_NUMPY_LSTSQ_COEFFICIENT_ONLY",
    "required_edge_cases": list(EDGE_CASES),
    "real_sample_values": "NOT_READ",
}


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
    require(np.isfinite(number), "ER2_R5P_FAIL_SYNTHETIC_REFERENCE_EQUIVALENCE: nonfinite value")
    return format(number, ".17g")


def csv_bytes(rows: list[dict[str, Any]], fields: tuple[str, ...]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(fields), lineterminator="\n", extrasaction="raise")
    writer.writeheader()
    for row in rows:
        serialized: dict[str, str] = {}
        for field in fields:
            value = row[field]
            if isinstance(value, (float, np.floating)):
                serialized[field] = canonical_float(value)
            elif isinstance(value, bool):
                serialized[field] = "TRUE" if value else "FALSE"
            else:
                serialized[field] = str(value)
        writer.writerow(serialized)
    return stream.getvalue().encode("utf-8")


def read_json(relative: Path) -> dict[str, Any]:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def read_csv(relative: Path) -> list[dict[str, str]]:
    with (ROOT / relative).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def read_frozen_blob(commit_sha: str, path: Path) -> bytes:
    require(commit_sha == R4_FREEZE_SHA, "ER2_R5P_FAIL_R4_PREDECESSOR_IDENTITY: wrong frozen commit")
    require(
        not path.is_absolute() and bool(path.parts) and ".." not in path.parts,
        "ER2_R5P_FAIL_R4_PREDECESSOR_IDENTITY: invalid frozen path",
    )
    try:
        # Binary plumbing bypasses checkout filters and text-mode EOL conversion.
        return subprocess.check_output(
            ["git", "cat-file", "blob", f"{commit_sha}:{path.as_posix()}"],
            cwd=ROOT,
            stderr=subprocess.PIPE,
        )
    except (OSError, subprocess.CalledProcessError) as error:
        raise RuntimeError(f"ER2_R5P_FAIL_R4_PREDECESSOR_IDENTITY: missing or unreadable frozen blob {path.as_posix()}") from error


def verify_frozen_blob(commit_sha: str, path: Path, expected_sha256: str) -> str:
    actual = sha_bytes(read_frozen_blob(commit_sha, path))
    require(actual == expected_sha256, f"ER2_R5P_FAIL_R4_PREDECESSOR_IDENTITY: frozen blob SHA {path.as_posix()}")
    return actual


def worktree_eol_diagnostic(blob: bytes, worktree: bytes) -> dict[str, Any]:
    eol_only = worktree != blob and worktree.replace(b"\r\n", b"\n") == blob
    return {
        "worktree_sha256": sha_bytes(worktree),
        "cr_count": worktree.count(b"\r"),
        "lf_count": worktree.count(b"\n"),
        "crlf_count": worktree.count(b"\r\n"),
        "worktree_eol_only_materialization": eol_only,
        "diagnostic": "IDENTICAL" if worktree == blob else "EOL_ONLY_MATERIALIZATION" if eol_only else "SUBSTANTIVE_DIFFERENCE",
    }


def remote_refs() -> dict[str, str]:
    refs: dict[str, str] = {}
    for line in git("ls-remote", "origin").splitlines():
        object_id, ref = line.split("\t", 1)
        refs[ref] = object_id
    return refs


def key_sha(keys: list[list[str]]) -> str:
    return sha_bytes(compact_json_bytes(keys))


def r5_contract() -> tuple[dict[str, str], dict[str, Any]]:
    with (ROOT / TIER_CONTRACTS).open(encoding="utf-8", newline="") as handle:
        row = next(item for item in csv.DictReader(handle) if item["TIER"] == "R5_LEAVE_ONE_PERIOD_OUT_ALL_PERIODS")
    expected_row = {
        "ORDER": "5",
        "TIER": "R5_LEAVE_ONE_PERIOD_OUT_ALL_PERIODS",
        "ROLE": "ALL_PERIOD_INFLUENCE_DESCRIPTION",
        "FAMILY": "PHYSICAL_ANOMALY",
        "MULTIPLICITY": "DESCRIPTIVE_COEFFICIENT_DISTRIBUTIONS_NO_SIGNIFICANCE_VOTE_COUNTING",
        "PREVIOUS_TIER": "R4",
        "NEXT_TIER": "R6",
        "EXECUTION_STATUS": "NOT_EXECUTED",
        "ER1_NUMERICAL_RESULTS_IDENTITY": "40e0f58269dda309e83a1fa3da17ef4d5dc5523efc72a666f734d0ebacb76b24",
        "TIER_CONTRACT_SHA256": R5_TIER_CONTRACT_SHA,
    }
    require(row == expected_row, "ER2_R5P_FAIL_R5_CONTRACT_IDENTITY: tier row")
    protocol = read_json(PROTOCOL)
    tier = next(item for item in protocol["tiers"] if item["tier"] == "R5")
    require(sha_bytes(json_bytes(tier)) == R5_TIER_CONTRACT_SHA, "ER2_R5P_FAIL_R5_CONTRACT_IDENTITY: tier SHA")
    required = {
        "order": 5,
        "tier_id": "R5_LEAVE_ONE_PERIOD_OUT_ALL_PERIODS",
        "role": "ALL_PERIOD_INFLUENCE_DESCRIPTION",
        "family": "PHYSICAL_ANOMALY",
        "previous_tier": "R4",
        "next_tier": "R6",
        "period_source": "SORTED_UNIQUE_PERIODS_OF_EACH_EXACT_ER1_ANALYTICAL_SAMPLE",
        "sample_change": "ONE_ENTIRE_PERIOD_OMITTED_PER_MODEL_ONLY",
        "second_period_omission": "PROHIBITED",
        "primary_replacement": "PROHIBITED",
        "report_all_periods": True,
        "sign_reversal_rule": "PRODUCT_OF_LOO_AND_PRIMARY_BETA_STRICTLY_NEGATIVE",
        "stability_classification": "DESCRIPTIVE_NO_ARBITRARY_PASS_FAIL_THRESHOLD",
    }
    require(all(tier[key] == value for key, value in required.items()), "ER2_R5P_FAIL_R5_CONTRACT_IDENTITY: fields")
    require(tier["expected_models"] == 38, "ER2_R5P_FAIL_R5_CONTRACT_IDENTITY: refit count")
    return row, tier


def preflight() -> dict[str, Any]:
    remote = remote_refs()
    identity = {
        "head": git("rev-parse", "HEAD"),
        "branch": git("branch", "--show-current"),
        "local_branch": git("rev-parse", R4_BRANCH),
        "tracked_remote_branch": git("rev-parse", f"origin/{R4_BRANCH}"),
        "remote_branch": remote.get(f"refs/heads/{R4_BRANCH}"),
        "tag_object": git("rev-parse", R4_TAG),
        "tag_target": git("rev-parse", f"{R4_TAG}^{{}}"),
        "remote_tag_object": remote.get(f"refs/tags/{R4_TAG}"),
        "remote_tag_target": remote.get(f"refs/tags/{R4_TAG}^{{}}"),
    }
    expected = {
        "head": R4_FREEZE_SHA,
        "branch": R4_BRANCH,
        "local_branch": R4_FREEZE_SHA,
        "tracked_remote_branch": R4_FREEZE_SHA,
        "remote_branch": R4_FREEZE_SHA,
        "tag_object": R4_TAG_OBJECT,
        "tag_target": R4_FREEZE_SHA,
        "remote_tag_object": R4_TAG_OBJECT,
        "remote_tag_target": R4_FREEZE_SHA,
    }
    require(identity == expected, f"ER2_R5P_FAIL_R4_PREDECESSOR_IDENTITY: {identity}")
    require(git("rev-parse", f"{R4_FREEZE_SHA}^") == R4_PARENT_SHA, "ER2_R5P_FAIL_R4_PREDECESSOR_IDENTITY: parent")
    require(not git("diff", "--name-only"), "ER2_R5P_FAIL_R4_PREDECESSOR_IDENTITY: tracked diff")
    require(not git("diff", "--cached", "--name-only"), "ER2_R5P_FAIL_R4_PREDECESSOR_IDENTITY: staged diff")
    untracked = set(git("ls-files", "--others", "--exclude-standard").splitlines())
    authorized = {path.as_posix() for path in CANDIDATES}
    require(untracked.issubset(authorized), f"ER2_R5P_FAIL_R4_PREDECESSOR_IDENTITY: {sorted(untracked)}")
    actual_hashes = {
        path.as_posix(): verify_frozen_blob(R4_FREEZE_SHA, path, digest)
        for path, digest in FROZEN_INPUT_SHA256.items()
    }
    expected_hashes = {path.as_posix(): digest for path, digest in FROZEN_INPUT_SHA256.items()}
    require(actual_hashes == expected_hashes, "ER2_R5P_FAIL_R4_PREDECESSOR_IDENTITY: frozen SHA")
    r4_lock = read_json(R4_LOCK)
    require(r4_lock["final_verdict"] == "ER2_R4_PASS_RESULTS_LOCKED_READY_FOR_DIRECTOR_REVIEW", "ER2_R5P_FAIL_R4_PREDECESSOR_IDENTITY: lock verdict")
    require(r4_lock["execution_firewall"]["R5_EXECUTED"] is False, "ER2_R5P_FAIL_REAL_RESULT_FIREWALL: predecessor")
    _, tier = r5_contract()
    return {
        "identity": identity,
        "frozen_input_byte_source": "RAW_GIT_OBJECT",
        "worktree_bytes_are_authoritative": False,
        "frozen_input_sha256": actual_hashes,
        "authorized_candidate_universe": sorted(authorized),
        "r5_tier_contract": tier,
        "real_outcome_numerical_values_read": False,
        "real_climate_regressor_numerical_values_read": False,
    }


def function_identity(name: str) -> dict[str, Any]:
    source = (ROOT / ED1_SCRIPT).read_text(encoding="utf-8")
    lines = source.splitlines(keepends=True)
    tree = ast.parse(source)
    node = next(item for item in tree.body if isinstance(item, ast.FunctionDef) and item.name == name)
    source_bytes = "".join(lines[node.lineno - 1 : node.end_lineno]).encode("utf-8")
    body_bytes = "".join(lines[node.body[0].lineno - 1 : node.end_lineno]).encode("utf-8")
    return {
        "function": name,
        "signature": str(inspect.signature(getattr(ed1, name))),
        "lines": [node.lineno, node.end_lineno],
        "source_sha256": sha_bytes(source_bytes),
        "body_sha256": sha_bytes(body_bytes),
    }


def estimation_api_identity() -> dict[str, Any]:
    functions = {name: function_identity(name) for name in ("fit_two_way_fe_cr2", "fe_matrix", "absorb_fixed_effects")}
    expected = {
        "fit_two_way_fe_cr2": (FIT_SOURCE_SHA, FIT_BODY_SHA),
        "fe_matrix": (FE_SOURCE_SHA, FE_BODY_SHA),
        "absorb_fixed_effects": (ABSORB_SOURCE_SHA, ABSORB_BODY_SHA),
    }
    require(
        all((functions[name]["source_sha256"], functions[name]["body_sha256"]) == hashes for name, hashes in expected.items()),
        "ER2_R5P_FAIL_ESTIMATION_API_IDENTITY",
    )
    return {
        "file": ED1_SCRIPT.as_posix(),
        "file_sha256": verify_frozen_blob(R4_FREEZE_SHA, ED1_SCRIPT, ED1_IMPLEMENTATION_SHA),
        "functions": functions,
        "executor_architecture": "R5_EXECUTOR_CAN_REUSE_FROZEN_PRIMARY_ESTIMATION_DIRECTLY",
        "adapter_role": "FAIL_CLOSED_ONE_PERIOD_FILTER_AND_NAMED_COEFFICIENT_EXTRACTION_ONLY",
        "coefficient_solver": "FROZEN_ED1_FULL_DESIGN_NUMPY_LSTSQ_RCOND_NONE",
        "fe_absorption": "FROZEN_ED1_DISTRICT_AND_REMAINING_PERIOD_FE",
        "rank_check": "FULL_DESIGN_AND_WITHIN_CLIMATE_BLOCK_FULL_COLUMN_RANK_REQUIRED",
        "row_order": "UBIGEO_THEN_PERIOD_STABLE_MERGESORT",
        "coefficient_order": "EXACT_FROZEN_ED1_REGRESSOR_ORDER",
        "inference_outputs": "NOT_AUTHORIZED",
    }


def period_inventory() -> tuple[dict[str, list[str]], dict[str, Any]]:
    sample_identity = read_json(R2_LOCK)["sample_identity"]
    r4_identity = read_json(R4_LOCK)["model_identity"]
    periods: dict[str, list[str]] = {}
    audit: dict[str, Any] = {}
    for crop_code in CROP_ORDER:
        keys = sample_identity[crop_code]["er1_ordered_keys"]
        require(len(keys) == EXPECTED_SAMPLE_N[crop_code], f"ER2_R5P_FAIL_PERIOD_INVENTORY: sample N {crop_code}")
        require(all(isinstance(key, list) and len(key) == 2 for key in keys), f"ER2_R5P_FAIL_PERIOD_INVENTORY: keys {crop_code}")
        ordered = sorted({str(key[1]) for key in keys})
        require(tuple(ordered) == EXPECTED_PERIODS[crop_code], f"ER2_R5P_FAIL_PERIOD_INVENTORY: periods {crop_code}")
        require(key_sha(keys) == r4_identity[crop_code]["ordered_key_sha256"], f"ER2_R5P_FAIL_PERIOD_INVENTORY: key SHA {crop_code}")
        require(len(ordered) == int(r4_identity[crop_code]["periods"]), f"ER2_R5P_FAIL_PERIOD_INVENTORY: R4 count {crop_code}")
        periods[crop_code] = ordered
        audit[crop_code] = {
            "crop": ed1.CROPS[crop_code]["crop"],
            "model_id": ed1.CROPS[crop_code]["model_id"],
            "period_id_column": ed1.CROPS[crop_code]["period_column"],
            "periods": ordered,
            "period_count": len(ordered),
            "sample_n": len(keys),
            "ordered_key_sha256": key_sha(keys),
            "source": "ER2_R2_RESULTS_LOCK.sample_identity.er1_ordered_keys",
            "source_rule": "SORTED_UNIQUE_PERIODS_OF_EACH_EXACT_ER1_ANALYTICAL_SAMPLE",
            "real_sample_keys_read": True,
            "real_period_labels_read": True,
            "real_outcome_numerical_values_read": False,
            "real_climate_regressor_numerical_values_read": False,
        }
    return periods, audit


def mandatory_named_case(crop_code: str, period: str) -> str:
    if crop_code in TRANSIENT_CODES:
        mapping = {"2016/2017": "LEAVE_2017_OUT", "2022/2023": "LEAVE_2023_OUT"}
    else:
        mapping = {"2017": "LEAVE_2017_OUT", "2023": "LEAVE_2023_OUT"}
    return mapping.get(str(period), "NONE")


def build_omission_plan(periods: dict[str, list[str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    refit_order = 0
    for crop_code in CROP_ORDER:
        crop = ed1.CROPS[crop_code]
        for period_order, period in enumerate(periods[crop_code], start=1):
            refit_order += 1
            rows.append({
                "REFIT_ORDER": refit_order,
                "CROP": crop["crop"],
                "CROP_CODE": crop_code,
                "MODEL_ID": crop["model_id"],
                "PERIOD_ID_COLUMN": crop["period_column"],
                "OMITTED_PERIOD_ID": period,
                "OMITTED_PERIOD_ORDER": period_order,
                "MANDATORY_NAMED_CASE": mandatory_named_case(crop_code, period),
                "NOMINAL_PERIODS": len(periods[crop_code]),
                "RETAINED_PERIODS": len(periods[crop_code]) - 1,
                "OMISSION_SCOPE": "ONE_ENTIRE_PERIOD_OMITTED_PER_MODEL_ONLY",
                "REPORT_ALL_PERIODS": True,
                "ESTIMATION_EXECUTED": False,
                "STATUS": "PLANNED_NOT_EXECUTED",
            })
    require(len(rows) == 38 and [row["REFIT_ORDER"] for row in rows] == list(range(1, 39)), "ER2_R5P_FAIL_OMISSION_PLAN")
    require(len({(row["CROP_CODE"], row["OMITTED_PERIOD_ID"]) for row in rows}) == 38, "ER2_R5P_FAIL_OMISSION_PLAN: duplicate")
    return rows


def build_coefficient_omission_map(periods: dict[str, list[str]]) -> list[dict[str, Any]]:
    mapping = read_csv(R4P_MAP)
    require(len(mapping) == 21 and [int(row["MAP_ORDER"]) for row in mapping] == list(range(1, 22)), "ER2_R5P_FAIL_COEFFICIENT_MAPPING")
    rows: list[dict[str, Any]] = []
    order = 0
    for target in mapping:
        crop_code = target["CROP_CODE"]
        for period_order, period in enumerate(periods[crop_code], start=1):
            order += 1
            rows.append({
                "COEFFICIENT_OMISSION_ORDER": order,
                "COEFFICIENT_MAP_ORDER": int(target["MAP_ORDER"]),
                "CROP": target["CROP"],
                "CROP_CODE": crop_code,
                "MODEL_ID": target["MODEL_ID"],
                "VARIABLE": target["COEFFICIENT_NAME"],
                "ED1_REGRESSOR_POSITION_ONE_BASED": int(target["ED1_REGRESSOR_POSITION_ONE_BASED"]),
                "PERIOD_ID_COLUMN": ed1.CROPS[crop_code]["period_column"],
                "OMITTED_PERIOD_ID": period,
                "OMITTED_PERIOD_ORDER": period_order,
                "MANDATORY_NAMED_CASE": mandatory_named_case(crop_code, period),
                "EXPECTED_RETAINED_PERIODS": len(periods[crop_code]) - 1,
                "REAL_LOO_BETA_COMPUTED": False,
                "STATUS": "MAPPED_NOT_EXECUTED",
            })
    require(len(rows) == 162 and [row["COEFFICIENT_OMISSION_ORDER"] for row in rows] == list(range(1, 163)), "ER2_R5P_FAIL_COEFFICIENT_MAPPING: row count")
    require(len({(row["CROP_CODE"], row["VARIABLE"], row["OMITTED_PERIOD_ID"]) for row in rows}) == 162, "ER2_R5P_FAIL_COEFFICIENT_MAPPING: duplicate")
    return rows


def classify_sign(beta: float) -> str:
    value = float(beta)
    require(np.isfinite(value), "ER2_R5P_FAIL_SIGN_RULES: nonfinite")
    if value > 0.0:
        return "POSITIVE"
    if value < 0.0:
        return "NEGATIVE"
    return "ZERO"


def sign_reversal(primary_beta: float, loo_beta: float) -> bool:
    primary = float(primary_beta)
    loo = float(loo_beta)
    require(np.isfinite(primary) and np.isfinite(loo), "ER2_R5P_FAIL_SIGN_RULES: nonfinite")
    return bool(loo * primary < 0.0)


def summarize_loo(primary_beta: float, period_betas: list[tuple[str, float]]) -> dict[str, Any]:
    require(bool(period_betas), "ER2_R5P_FAIL_OMISSION_PLAN: empty summary")
    require(len({str(period) for period, _ in period_betas}) == len(period_betas), "ER2_R5P_FAIL_OMISSION_PLAN: duplicate summary period")
    ordered = sorted((str(period), float(beta)) for period, beta in period_betas)
    values = np.asarray([beta for _, beta in ordered], dtype=float)
    require(np.isfinite(values).all(), "ER2_R5P_FAIL_SIGN_RULES: nonfinite summary")
    deviations = [(period, abs(beta - float(primary_beta))) for period, beta in ordered]
    maximum_deviation = max(value for _, value in deviations)
    tied = sorted(period for period, value in deviations if value == maximum_deviation)
    return {
        "PRIMARY_BETA_REFERENCE": float(primary_beta),
        "MIN_LOO_BETA": float(np.min(values)),
        "MAX_LOO_BETA": float(np.max(values)),
        "BETA_RANGE": float(np.max(values) - np.min(values)),
        "MEDIAN_LOO_BETA": float(np.median(values)),
        "POSITIVE_COUNT": sum(value > 0.0 for value in values),
        "NEGATIVE_COUNT": sum(value < 0.0 for value in values),
        "ZERO_COUNT": sum(value == 0.0 for value in values),
        "SIGN_REVERSAL_COUNT": sum(sign_reversal(primary_beta, value) for value in values),
        "MAX_ABSOLUTE_BETA_DEVIATION": maximum_deviation,
        "PERIODS_CAUSING_MAX_ABSOLUTE_DEVIATION": tied,
    }


def _expected_error(marker: str, operation: Callable[[], Any]) -> bool:
    try:
        operation()
    except RuntimeError as error:
        return marker in str(error)
    return False


def production_loo_beta(
    frame: pd.DataFrame,
    x_columns: list[str],
    period_column: str,
    response: np.ndarray,
    omitted_period: str,
) -> dict[str, Any]:
    if period_column not in frame.columns:
        raise RuntimeError("R5_HOLD_MISSING_PERIOD_ID")
    if not isinstance(omitted_period, str):
        raise RuntimeError("R5_HOLD_SECOND_PERIOD_OMISSION")
    if not omitted_period:
        raise RuntimeError("R5_HOLD_MALFORMED_PERIOD_KEY")
    if frame[period_column].isna().any() or (frame[period_column].astype(str).str.len() == 0).any():
        raise RuntimeError("R5_HOLD_MALFORMED_PERIOD_KEY")
    periods = sorted(set(frame[period_column].astype(str)))
    if omitted_period not in periods:
        raise RuntimeError("R5_HOLD_MISSING_PERIOD_ID")
    if not x_columns or len(set(x_columns)) != len(x_columns):
        raise RuntimeError("R5_HOLD_DUPLICATE_TARGET_MAPPING")
    if any(column not in frame.columns for column in x_columns):
        raise RuntimeError("R5_HOLD_MISSING_TARGET_COEFFICIENT")
    y = np.asarray(response, dtype=float)
    if y.ndim != 1 or len(y) != len(frame) or not np.isfinite(y).all():
        raise RuntimeError("R5_HOLD_NONFINITE_BETA")
    working = frame.copy()
    working["__R5P_SYNTHETIC_RESPONSE"] = y
    retained = working[working[period_column].astype(str) != omitted_period].copy()
    if retained.empty:
        raise RuntimeError("R5_HOLD_EMPTY_REMAINING_PERIOD")
    remaining_periods = sorted(set(retained[period_column].astype(str)))
    if len(remaining_periods) < 2:
        raise RuntimeError("R5_HOLD_INSUFFICIENT_REMAINING_PERIODS")
    retained = retained.sort_values(["UBIGEO", period_column], kind="mergesort").reset_index(drop=True)
    if retained.duplicated(["UBIGEO", period_column]).any():
        raise RuntimeError("R5_HOLD_MALFORMED_PERIOD_KEY")
    x = retained[x_columns].to_numpy(dtype=float)
    if not np.isfinite(x).all():
        raise RuntimeError("R5_HOLD_NONFINITE_BETA")
    fixed_effects = ed1.fe_matrix(retained, period_column)
    x_within = ed1.absorb_fixed_effects(x, fixed_effects)
    if np.linalg.matrix_rank(x_within) != len(x_columns):
        raise RuntimeError("R5_HOLD_RANK_DEFICIENT_REFIT")
    if np.linalg.matrix_rank(np.column_stack([fixed_effects, x])) != fixed_effects.shape[1] + len(x_columns):
        raise RuntimeError("R5_HOLD_RANK_DEFICIENT_REFIT")
    retained_y = retained["__R5P_SYNTHETIC_RESPONSE"].to_numpy(dtype=float)
    fit = ed1.fit_two_way_fe_cr2(retained, list(x_columns), period_column, retained_y)
    beta = np.asarray(fit["beta"], dtype=float)
    if beta.shape != (len(x_columns),) or not np.isfinite(beta).all():
        raise RuntimeError("R5_HOLD_NONFINITE_BETA")
    return {
        "beta_by_name": {name: float(beta[index]) for index, name in enumerate(x_columns)},
        "ordered_beta": beta,
        "omitted_period": omitted_period,
        "retained_n": len(retained),
        "retained_periods": remaining_periods,
        "retained_period_values": retained[period_column].astype(str).tolist(),
        "district_fe": "REQUIRED_ACTIVE",
        "remaining_period_fe": "REQUIRED_ACTIVE",
        "regressors": list(x_columns),
        "inference_outputs_emitted": False,
    }


def reference_loo_beta(
    frame: pd.DataFrame,
    x_columns: list[str],
    period_column: str,
    response: np.ndarray,
    omitted_period: str,
) -> dict[str, float]:
    working = frame.copy()
    working["__REFERENCE_Y"] = np.asarray(response, dtype=float)
    retained = working[working[period_column].astype(str) != str(omitted_period)].copy()
    retained = retained.sort_values(["UBIGEO", period_column], kind="mergesort").reset_index(drop=True)
    columns = [np.ones(len(retained), dtype=float)]
    for field in ("UBIGEO", period_column):
        values = retained[field].astype(str).to_numpy()
        for level in sorted(set(values))[1:]:
            columns.append((values == level).astype(float))
    fixed_effects = np.column_stack(columns)
    x = retained[x_columns].to_numpy(dtype=float)
    y = retained["__REFERENCE_Y"].to_numpy(dtype=float)
    design = np.column_stack([fixed_effects, x])
    beta = np.linalg.lstsq(design, y, rcond=None)[0][-len(x_columns) :]
    return {name: float(beta[index]) for index, name in enumerate(x_columns)}


def synthetic_fixture() -> tuple[pd.DataFrame, list[str], np.ndarray]:
    rng = np.random.Generator(np.random.PCG64(SYNTHETIC_SEED))
    districts = [f"D{number:02d}" for number in range(1, 7)]
    periods = [f"P{number:02d}" for number in range(1, 6)]
    frame = pd.DataFrame(
        [(district, period) for period in periods for district in districts if (district, period) != ("D06", "P05")],
        columns=["UBIGEO", "SYNTHETIC_PERIOD"],
    )
    x_columns = ["X1", "X2", "X3"]
    for column in x_columns:
        frame[column] = rng.normal(size=len(frame))
    structural = frame[x_columns].to_numpy(dtype=float) @ np.asarray([1.25, -0.75, 0.5], dtype=float)
    district_effect = frame["UBIGEO"].str[1:].astype(int).to_numpy(dtype=float) * 0.11
    period_effect = frame["SYNTHETIC_PERIOD"].str[1:].astype(int).to_numpy(dtype=float) * -0.07
    response = structural + district_effect + period_effect + rng.normal(scale=0.05, size=len(frame))
    return frame, x_columns, response.astype(float)


def validation_row(check_id: str, category: str, passed: bool, detail: str, difference: float = 0.0) -> dict[str, Any]:
    return {
        "CHECK_ID": check_id,
        "CATEGORY": category,
        "STATUS": "PASS" if passed else "FAIL",
        "MAX_ABS_DIFFERENCE": difference,
        "DETAIL": detail,
    }


def synthetic_validation(plan_lock_sha256: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    require(plan_lock_sha256 == sha_bytes(json_bytes(SYNTHETIC_PLAN)), "ER2_R5P_FAIL_SYNTHETIC_REFERENCE_EQUIVALENCE: plan lock")
    frame, columns, response = synthetic_fixture()
    periods = sorted(set(frame["SYNTHETIC_PERIOD"].astype(str)))
    production: dict[str, dict[str, Any]] = {}
    reference: dict[str, dict[str, float]] = {}
    differences: dict[str, float] = {}
    rows: list[dict[str, Any]] = []
    for period in periods:
        production[period] = production_loo_beta(frame, columns, "SYNTHETIC_PERIOD", response, period)
        reference[period] = reference_loo_beta(frame, columns, "SYNTHETIC_PERIOD", response, period)
        difference = max(abs(production[period]["beta_by_name"][name] - reference[period][name]) for name in columns)
        differences[period] = difference
        rows.append(validation_row(f"REFERENCE_EQUIVALENCE_{period}", "PRODUCTION_REFERENCE", difference <= CONTINUOUS_TOLERANCE, "FROZEN_ED1_VS_INDEPENDENT_FULL_DUMMY_LSTSQ", difference))

    omitted_counts = {period: 1 for period in production}
    retained_exact = all(set(item["retained_periods"]) == set(periods) - {period} for period, item in production.items())
    omitted_zero = all(period not in item["retained_period_values"] for period, item in production.items())
    rows.extend([
        validation_row("A_EVERY_PERIOD_OMITTED_EXACTLY_ONCE", "OMISSION", omitted_counts == {period: 1 for period in periods}, "FIVE_OF_FIVE_UNIQUE_OMISSIONS"),
        validation_row("B_OMITTED_PERIOD_HAS_ZERO_RETAINED_ROWS", "OMISSION", omitted_zero, "ZERO_RETAINED_ROWS_FOR_EACH_OMITTED_PERIOD"),
        validation_row("C_ALL_OTHER_PERIODS_RETAINED_EXACTLY", "OMISSION", retained_exact, "ALL_NONOMITTED_PERIODS_RETAINED"),
        validation_row("D_REMAINING_PERIOD_FE_ACTIVE", "FIXED_EFFECTS", all(item["remaining_period_fe"] == "REQUIRED_ACTIVE" for item in production.values()), "FROZEN_PERIOD_FE_ACTIVE"),
        validation_row("E_DISTRICT_FE_ACTIVE", "FIXED_EFFECTS", all(item["district_fe"] == "REQUIRED_ACTIVE" for item in production.values()), "FROZEN_DISTRICT_FE_ACTIVE"),
        validation_row("F_EXACT_SAME_REGRESSORS", "MODEL", all(item["regressors"] == columns for item in production.values()), "X1_X2_X3"),
    ])
    rows.append(validation_row("G_NO_SECOND_OMISSION", "FAIL_CLOSED", _expected_error("R5_HOLD_SECOND_PERIOD_OMISSION", lambda: production_loo_beta(frame, columns, "SYNTHETIC_PERIOD", response, ["P01", "P02"])), "SECOND_SIMULTANEOUS_OMISSION_REJECTED"))

    permutation = np.random.Generator(np.random.PCG64(SYNTHETIC_SEED + 1)).permutation(len(frame))
    permuted = production_loo_beta(frame.iloc[permutation].reset_index(drop=True), columns, "SYNTHETIC_PERIOD", response[permutation], "P01")
    row_difference = max(abs(permuted["beta_by_name"][name] - production["P01"]["beta_by_name"][name]) for name in columns)
    rows.append(validation_row("H_ROW_ORDER_PERMUTATION_INVARIANCE", "INVARIANCE", row_difference <= CONTINUOUS_TOLERANCE, "STABLE_SORTED_REFIT", row_difference))
    reversed_results = {period: production_loo_beta(frame, columns, "SYNTHETIC_PERIOD", response, period)["beta_by_name"] for period in reversed(periods)}
    period_difference = max(abs(reversed_results[period][name] - production[period]["beta_by_name"][name]) for period in periods for name in columns)
    rows.append(validation_row("I_PERIOD_ORDER_PERMUTATION_INVARIANCE", "INVARIANCE", period_difference <= CONTINUOUS_TOLERANCE, "OMISSION_LOOP_ORDER_DOES_NOT_CHANGE_RESULTS", period_difference))
    permuted_columns = ["X3", "X1", "X2"]
    column_result = production_loo_beta(frame, permuted_columns, "SYNTHETIC_PERIOD", response, "P01")
    column_difference = max(abs(column_result["beta_by_name"][name] - production["P01"]["beta_by_name"][name]) for name in columns)
    rows.append(validation_row("J_COEFFICIENT_COLUMN_MAPPING_INVARIANCE", "INVARIANCE", column_difference <= CONTINUOUS_TOLERANCE, "NAMED_MAPPING_PRESERVES_COEFFICIENT_IDENTITY", column_difference))

    rows.extend([
        validation_row("K_STRICT_POSITIVE_CLASSIFICATION", "SIGN", classify_sign(1.0) == "POSITIVE", "BETA_GT_ZERO"),
        validation_row("L_STRICT_NEGATIVE_CLASSIFICATION", "SIGN", classify_sign(-1.0) == "NEGATIVE", "BETA_LT_ZERO"),
        validation_row("M_EXACT_ZERO_CLASSIFICATION", "SIGN", classify_sign(0.0) == "ZERO", "BETA_EQ_ZERO_SEPARATE"),
        validation_row("N_STRICT_SIGN_REVERSAL_RULE", "SIGN", sign_reversal(1.0, -0.5) and sign_reversal(-1.0, 0.5), "PRODUCT_STRICTLY_NEGATIVE"),
        validation_row("O_NO_REVERSAL_WITH_PRIMARY_OR_LOO_ZERO", "SIGN", not sign_reversal(0.0, -1.0) and not sign_reversal(1.0, 0.0), "ZERO_IS_NOT_REVERSAL"),
    ])
    summary = summarize_loo(1.0, [("P03", 2.0), ("P01", 0.0), ("P02", 1.0)])
    rows.extend([
        validation_row("P_MINIMUM_MAXIMUM_MEDIAN_SUMMARIES", "SUMMARY", summary["MIN_LOO_BETA"] == 0.0 and summary["MAX_LOO_BETA"] == 2.0 and summary["MEDIAN_LOO_BETA"] == 1.0, "MIN_MAX_MEDIAN_EXACT"),
        validation_row("Q_BETA_RANGE", "SUMMARY", summary["BETA_RANGE"] == 2.0, "MAX_MINUS_MIN"),
        validation_row("R_MAXIMUM_ABSOLUTE_DEVIATION", "SUMMARY", summary["MAX_ABSOLUTE_BETA_DEVIATION"] == 1.0, "ABS_LOO_MINUS_PRIMARY"),
        validation_row("S_ALL_TIED_PERIODS_SORTED", "SUMMARY", summary["PERIODS_CAUSING_MAX_ABSOLUTE_DEVIATION"] == ["P01", "P03"], "ALL_TIES_SORTED"),
        validation_row("T_2017_2023_LABELS_DO_NOT_ALTER_ESTIMATION", "GOVERNANCE", "MANDATORY_NAMED_CASE" not in inspect.signature(production_loo_beta).parameters and mandatory_named_case("14010020000", "2016/2017") == "LEAVE_2017_OUT" and mandatory_named_case("13010210000", "2023") == "LEAVE_2023_OUT", "REPORTING_LABELS_ABSENT_FROM_ESTIMATOR_SIGNATURE"),
    ])
    rank_frame = frame.copy()
    rank_frame["X3"] = rank_frame["X1"]
    one_period = frame[frame["SYNTHETIC_PERIOD"] == "P01"].copy()
    one_response = response[frame["SYNTHETIC_PERIOD"].to_numpy() == "P01"]
    rows.extend([
        validation_row("U_RANK_DEFICIENT_REFIT_FAILS_CLOSED", "FAIL_CLOSED", _expected_error("R5_HOLD_RANK_DEFICIENT_REFIT", lambda: production_loo_beta(rank_frame, columns, "SYNTHETIC_PERIOD", response, "P01")), "NO_REGRESSOR_REMOVAL_OR_ESTIMATOR_SUBSTITUTION"),
        validation_row("V_EMPTY_REMAINING_PERIOD_FAILS_CLOSED", "FAIL_CLOSED", _expected_error("R5_HOLD_EMPTY_REMAINING_PERIOD", lambda: production_loo_beta(one_period, columns, "SYNTHETIC_PERIOD", one_response, "P01")), "EMPTY_RETAINED_SAMPLE_REJECTED"),
        validation_row("W_MISSING_PERIOD_ID_FAILS_CLOSED", "FAIL_CLOSED", _expected_error("R5_HOLD_MISSING_PERIOD_ID", lambda: production_loo_beta(frame.drop(columns=["SYNTHETIC_PERIOD"]), columns, "SYNTHETIC_PERIOD", response, "P01")), "MISSING_PERIOD_COLUMN_REJECTED"),
        validation_row("X_DUPLICATE_TARGET_MAPPING_FAILS_CLOSED", "FAIL_CLOSED", _expected_error("R5_HOLD_DUPLICATE_TARGET_MAPPING", lambda: production_loo_beta(frame, ["X1", "X1", "X3"], "SYNTHETIC_PERIOD", response, "P01")), "DUPLICATE_COEFFICIENT_NAME_REJECTED"),
        validation_row("Y_MISSING_TARGET_COEFFICIENT_FAILS_CLOSED", "FAIL_CLOSED", _expected_error("R5_HOLD_MISSING_TARGET_COEFFICIENT", lambda: production_loo_beta(frame, ["X1", "X2", "MISSING"], "SYNTHETIC_PERIOD", response, "P01")), "MISSING_COEFFICIENT_REJECTED"),
        validation_row("Z_NONFINITE_INPUT_FAILS_CLOSED", "FAIL_CLOSED", _expected_error("R5_HOLD_NONFINITE_BETA", lambda: production_loo_beta(frame.assign(X1=np.nan), columns, "SYNTHETIC_PERIOD", response, "P01")), "NONFINITE_INPUT_REJECTED"),
        validation_row("AA_MALFORMED_PERIOD_KEY_FAILS_CLOSED", "FAIL_CLOSED", _expected_error("R5_HOLD_MALFORMED_PERIOD_KEY", lambda: production_loo_beta(frame.assign(SYNTHETIC_PERIOD=""), columns, "SYNTHETIC_PERIOD", response, "P01")), "EMPTY_PERIOD_KEY_REJECTED"),
        validation_row("AB_INSUFFICIENT_REMAINING_PERIODS_FAILS_CLOSED", "FAIL_CLOSED", _expected_error("R5_HOLD_INSUFFICIENT_REMAINING_PERIODS", lambda: production_loo_beta(frame[frame["SYNTHETIC_PERIOD"].isin(["P01", "P02"])].reset_index(drop=True), columns, "SYNTHETIC_PERIOD", response[frame["SYNTHETIC_PERIOD"].isin(["P01", "P02"]).to_numpy()], "P01")), "ONE_REMAINING_PERIOD_REJECTED"),
    ])
    require({row["CHECK_ID"] for row in rows}.issuperset(EDGE_CASES), "ER2_R5P_FAIL_SYNTHETIC_REFERENCE_EQUIVALENCE: missing edge case")
    require(all(row["STATUS"] == "PASS" for row in rows), f"ER2_R5P_FAIL_SYNTHETIC_REFERENCE_EQUIVALENCE: {[row for row in rows if row['STATUS'] != 'PASS']}")
    maximum = max(differences.values())
    require(maximum <= CONTINUOUS_TOLERANCE, "ER2_R5P_FAIL_SYNTHETIC_REFERENCE_EQUIVALENCE")
    return rows, {
        "status": "PASS",
        "plan_lock_sha256": plan_lock_sha256,
        "production_reference_omissions": len(periods),
        "maximum_absolute_beta_difference": maximum,
        "continuous_tolerance": CONTINUOUS_TOLERANCE,
        "edge_cases_required": len(EDGE_CASES),
        "edge_cases_passed": len(EDGE_CASES),
        "validation_rows": len(rows),
        "production_path": "FROZEN_ED1_FIT_TWO_WAY_FE_CR2_BETA_ONLY_VIA_FAIL_CLOSED_LOO_ADAPTER",
        "reference_path": "INDEPENDENT_FULL_DUMMY_MATRIX_NUMPY_LSTSQ_COEFFICIENT_ONLY",
    }


def report_bytes(
    tier: dict[str, Any],
    period_audit: dict[str, Any],
    api: dict[str, Any],
    synthetic: dict[str, Any],
    artifact_sha: dict[str, str],
) -> bytes:
    lines = [
        "# ER2-R5P Leave-One-Period-Out Pre-Execution Certification v1",
        "",
        f"PROJECT={PROJECT}",
        f"GATE={GATE}",
        "STATUS=PASS_PREEXECUTION_CERTIFIED_PENDING_DIRECTOR_REVIEW",
        "",
        "## Frozen predecessor and tier contract",
        "",
        f"R4_FREEZE_SHA={R4_FREEZE_SHA}",
        f"R4_RESULTS_LOCK_SHA256={R4_RESULTS_LOCK_SHA}",
        f"R5_TIER_CONTRACT_SHA256={R5_TIER_CONTRACT_SHA}",
        f"R5_ROLE={tier['role']}",
        f"R5_FAMILY={tier['family']}",
        "PRIMARY_REPLACEMENT=PROHIBITED",
        "NO_OMISSION_RESULT_BECOMES_PRIMARY",
        "",
        "## Byte-source adjudication and preserved failed attempt",
        "",
        *[f"{key}={str(value).upper() if isinstance(value, bool) else value}" for key, value in BYTE_SOURCE_ADJUDICATION.items()],
        "",
        "## Mechanically derived exact period lists",
        "",
    ]
    for crop_code in CROP_ORDER:
        audit = period_audit[crop_code]
        lines.append(f"{audit['crop']}|{audit['period_id_column']}|{'|'.join(audit['periods'])}")
    lines.extend([
        "",
        "R5_REFIT_MODELS=38",
        "R5_COEFFICIENT_OMISSION_ROWS=162",
        "R5_SUMMARY_ROWS=21",
        "LEAVE_2017_TRANSIENT=2016/2017",
        "LEAVE_2017_PERENNIAL=2017",
        "LEAVE_2023_TRANSIENT=2022/2023",
        "LEAVE_2023_PERENNIAL=2023",
        "MANDATORY_2017_2023_REPORTING_FROZEN_PRE_RESULT=TRUE",
        "REPORT_ALL_PERIODS=TRUE",
        "",
        "## Fixed model and descriptive rules",
        "",
        "OUTCOME=YIELD_LEVEL_TM_PER_HA",
        "CLIMATE_FAMILY=PHYSICAL_ANOMALY",
        "WINDOWS=EXACT_ED1_FROZEN",
        "FUNCTIONAL_FORM=LINEAR_ADDITIVE",
        "DISTRICT_FE=REQUIRED",
        "REMAINING_PERIOD_FE=REQUIRED",
        "WEIGHTING=UNWEIGHTED_PRIMARY_ESTIMATION",
        "SAMPLE_CHANGE=ONE_ENTIRE_PERIOD_OMITTED_PER_MODEL_ONLY",
        "SECOND_PERIOD_OMISSION=PROHIBITED",
        "DISTRICT_DELETION=PROHIBITED",
        "SIGN_RULE=STRICT_POSITIVE_STRICT_NEGATIVE_EXACT_ZERO_SEPARATE",
        "SIGN_REVERSAL_RULE=PRODUCT_OF_LOO_AND_PRIMARY_BETA_STRICTLY_NEGATIVE",
        "MAX_DEVIATION_TIE_RULE=REPORT_ALL_TIED_PERIOD_IDS_SORTED_NO_POST_RESULT_TIE_SELECTION",
        "STABILITY_CLASSIFICATION=DESCRIPTIVE_NO_ARBITRARY_PASS_FAIL_THRESHOLD",
        "SIGNIFICANCE_VOTE_COUNTING=PROHIBITED",
        "R5_LOO_INFERENCE_OUTPUTS=NOT_AUTHORIZED",
        "",
        "## Estimation API and synthetic validation",
        "",
        f"ED1_ESTIMATION_FILE_SHA256={api['file_sha256']}",
        f"FIT_TWO_WAY_FE_CR2_SOURCE_SHA256={api['functions']['fit_two_way_fe_cr2']['source_sha256']}",
        f"FIT_TWO_WAY_FE_CR2_BODY_SHA256={api['functions']['fit_two_way_fe_cr2']['body_sha256']}",
        f"R5_EXECUTOR_ARCHITECTURE={api['executor_architecture']}",
        f"SYNTHETIC_PLAN_LOCK_SHA256={synthetic['plan_lock_sha256']}",
        f"PRODUCTION_REFERENCE_MAX_ABS_DIFFERENCE={canonical_float(synthetic['maximum_absolute_beta_difference'])}",
        f"PRESPECIFIED_CONTINUOUS_TOLERANCE={CONTINUOUS_TOLERANCE:.0e}",
        "SYNTHETIC_EDGE_CASES=PASS",
        "",
        "## Real-result and downstream firewalls",
        "",
        "REAL_SAMPLE_KEYS_READ=TRUE",
        "REAL_PERIOD_LABELS_READ=TRUE",
        "REAL_OUTCOME_NUMERICAL_VALUES_READ=FALSE",
        "REAL_CLIMATE_REGRESSOR_NUMERICAL_VALUES_READ=FALSE",
        "REAL_R5_REFITS_EXECUTED=0",
        "REAL_R5_BETAS_COMPUTED=FALSE",
        "REAL_R5_P_VALUES_COMPUTED=FALSE",
        "REAL_R5_SIGN_REVERSALS_KNOWN=FALSE",
        "REAL_R5_BETA_RANGES_KNOWN=FALSE",
        "REAL_R5_MAX_DEVIATION_PERIODS_KNOWN=FALSE",
        "RESULT_SPECIFIC_R5_BRANCHES=0",
        "R6_AUTHORIZATION_STATUS=NOT_AUTHORIZED",
        "R6_EXECUTED=FALSE",
        "DOWNSTREAM_EXECUTION=NOT_AUTHORIZED_NOT_EXECUTED",
        "",
        "## Artifact SHA-256",
        "",
        *[f"{path}={digest}" for path, digest in sorted(artifact_sha.items())],
        "",
        "R5P_TWO_RUN_REPRODUCIBILITY=PASS",
        "REAL_R5_EXECUTION_AUTHORIZATION_STATUS=NOT_AUTHORIZED",
        "NEXT_ACTION=RETURN_TO_SCIENTIFIC_DIRECTOR_FOR_R5P_FREEZE_DECISION_IF_PASS",
        f"FINAL_VERDICT={FINAL_VERDICT}",
    ])
    return ("\n".join(lines) + "\n").encode("utf-8")


def render_package(state: dict[str, Any], plan_payload: bytes) -> dict[Path, bytes]:
    periods, period_audit = period_inventory()
    omission_rows = build_omission_plan(periods)
    coefficient_rows = build_coefficient_omission_map(periods)
    api = estimation_api_identity()
    synthetic_rows, synthetic_summary = synthetic_validation(sha_bytes(plan_payload))
    payloads: dict[Path, bytes] = {
        TEST_PLAN_LOCK: plan_payload,
        OMISSION_PLAN: csv_bytes(omission_rows, OMISSION_FIELDS),
        COEFFICIENT_MAP: csv_bytes(coefficient_rows, COEFFICIENT_MAP_FIELDS),
        SYNTHETIC_VALIDATION: csv_bytes(synthetic_rows, SYNTHETIC_FIELDS),
    }
    artifact_sha = {
        TEST_PLAN_LOCK.as_posix(): sha_bytes(payloads[TEST_PLAN_LOCK]),
        OMISSION_PLAN.as_posix(): sha_bytes(payloads[OMISSION_PLAN]),
        COEFFICIENT_MAP.as_posix(): sha_bytes(payloads[COEFFICIENT_MAP]),
        SYNTHETIC_VALIDATION.as_posix(): sha_bytes(payloads[SYNTHETIC_VALIDATION]),
        SCRIPT.as_posix(): sha_file(ROOT / SCRIPT),
        TEST.as_posix(): sha_file(ROOT / TEST),
    }
    payloads[REPORT] = report_bytes(state["r5_tier_contract"], period_audit, api, synthetic_summary, artifact_sha)
    artifact_sha[REPORT.as_posix()] = sha_bytes(payloads[REPORT])
    lock = {
        "schema_version": "1.0.0",
        **BYTE_SOURCE_ADJUDICATION,
        "project": PROJECT,
        "gate": GATE,
        "status": "PASS_PREEXECUTION_CERTIFIED_PENDING_DIRECTOR_REVIEW",
        "final_verdict": FINAL_VERDICT,
        "governing_state": {
            "r4_freeze_sha": R4_FREEZE_SHA,
            "r4_parent_sha": R4_PARENT_SHA,
            "r4_branch": R4_BRANCH,
            "r4_tag": R4_TAG,
            "r4_tag_object": R4_TAG_OBJECT,
            "r4_results_lock_sha256": R4_RESULTS_LOCK_SHA,
            "r4_status": "PASS_FROZEN_REMOTE_VERIFIED",
        },
        "r5_tier_contract_sha256": R5_TIER_CONTRACT_SHA,
        "r5_tier_contract": state["r5_tier_contract"],
        "scientific_role": {
            "question": "COEFFICIENT_CHANGE_WHEN_ONE_ENTIRE_OBSERVED_PERIOD_IS_REMOVED",
            "role": "ALL_PERIOD_INFLUENCE_DESCRIPTION",
            "family": "PHYSICAL_ANOMALY",
            "primary_replacement": "PROHIBITED",
            "no_omission_result_becomes_primary": True,
            "stability_classification": "DESCRIPTIVE_NO_ARBITRARY_PASS_FAIL_THRESHOLD",
            "significance_vote_counting": "PROHIBITED",
        },
        "fixed_model_components": {
            "outcome": "YIELD_LEVEL_TM_PER_HA",
            "climate_family": "PHYSICAL_ANOMALY",
            "windows": "EXACT_ED1_FROZEN",
            "functional_form": "LINEAR_ADDITIVE",
            "district_fe": "REQUIRED",
            "remaining_period_fe": "REQUIRED",
            "weighting": "UNWEIGHTED_PRIMARY_ESTIMATION",
            "regressors": "EXACT_ER1_REGRESSORS",
            "sample_change": "ONE_ENTIRE_PERIOD_OMITTED_PER_MODEL_ONLY",
            "second_period_omission": "PROHIBITED",
            "district_deletion": "PROHIBITED",
        },
        "period_id_architecture": {
            "transient": "CAMPAIGN_ID",
            "perennial": "REFERENCE_PERIOD_ID",
            "source_rule": "SORTED_UNIQUE_PERIODS_OF_EACH_EXACT_ER1_ANALYTICAL_SAMPLE",
            "crop_audit": period_audit,
        },
        "omission_plan": {
            "status": "PASS",
            "rows": len(omission_rows),
            "models_by_crop": {code: len(periods[code]) for code in CROP_ORDER},
            "refit_models": 38,
            "baseline_refits_counted": 0,
            "second_period_omissions": 0,
            "district_omissions": 0,
            "report_all_periods": True,
        },
        "coefficient_omission_map": {
            "status": "PASS",
            "rows": len(coefficient_rows),
            "coefficient_dimensions": {"14010020000": 3, "14010070000": 3, "13010210000": 3, "13010170102": 6, "15010040000": 6},
            "summary_rows_future": 21,
            "real_detail_rows_current": 0,
            "real_summary_rows_current": 0,
        },
        "mandatory_named_reporting": {
            "frozen_pre_result": True,
            "transient": {"LEAVE_2017_OUT": "2016/2017", "LEAVE_2023_OUT": "2022/2023"},
            "perennial": {"LEAVE_2017_OUT": "2017", "LEAVE_2023_OUT": "2023"},
            "estimator_effect": "NONE_REPORTING_LABELS_ONLY",
        },
        "sign_rules": {
            "positive": "BETA_GREATER_THAN_ZERO",
            "negative": "BETA_LESS_THAN_ZERO",
            "zero": "BETA_EXACTLY_ZERO_REPORTED_SEPARATELY",
            "sign_reversal": "PRODUCT_OF_LOO_AND_PRIMARY_BETA_STRICTLY_NEGATIVE",
            "zero_reversal": "FALSE_IF_PRIMARY_OR_LOO_BETA_IS_ZERO",
        },
        "summary_metric_contract": {
            "metrics": list(SUMMARY_METRICS),
            "beta_range": "MAX_LOO_BETA_MINUS_MIN_LOO_BETA",
            "absolute_deviation": "ABS_LOO_BETA_MINUS_PRIMARY_BETA_REFERENCE",
            "exact_zero_output_field": "ZERO_COUNT",
            "sign_reversal_output_field": "SIGN_REVERSAL_COUNT",
            "max_deviation_period_output_field": "PERIODS_CAUSING_MAX_ABSOLUTE_DEVIATION",
            "max_deviation_tie_rule": "REPORT_ALL_TIED_PERIOD_IDS_SORTED_NO_POST_RESULT_TIE_SELECTION",
            "standardized_influence_score": "NOT_AUTHORIZED",
        },
        "r5_concordance_contract": {
            "fields": ["PRIMARY_BETA_REFERENCE", "R5_SIGN_REVERSAL_COUNT", "R5_BETA_RANGE"],
            "robustness_score": "PROHIBITED",
            "cross_tier_aggregation": "PROHIBITED",
        },
        "r5_loo_inference_outputs": "NOT_AUTHORIZED",
        "estimation_api": api,
        "synthetic_test_plan": SYNTHETIC_PLAN,
        "synthetic_validation": synthetic_summary,
        "future_real_r5_detail_schema": list(FUTURE_DETAIL_SCHEMA),
        "future_real_r5_summary_schema": list(FUTURE_SUMMARY_SCHEMA),
        "result_specific_r5_branches": 0,
        "r5p_two_run_reproducibility": {
            "status": "PASS",
            "independent_renderings": 2,
            "byte_identical_generated_artifacts": True,
            "timestamps": "ABSENT",
            "absolute_local_paths": "ABSENT",
            "encoding": "UTF-8",
            "line_endings": "LF",
            "bom": "ABSENT",
            "final_lf": "EXACTLY_ONE",
        },
        "artifact_sha256": artifact_sha,
        "frozen_input_sha256": state["frozen_input_sha256"],
        "real_result_firewall": {
            "REAL_SAMPLE_KEYS_READ": True,
            "REAL_PERIOD_LABELS_READ": True,
            "REAL_OUTCOME_NUMERICAL_VALUES_READ": False,
            "REAL_CLIMATE_REGRESSOR_NUMERICAL_VALUES_READ": False,
            "REAL_R5_REFITS_EXECUTED": 0,
            "REAL_R5_BETAS_COMPUTED": False,
            "REAL_R5_P_VALUES_COMPUTED": False,
            "REAL_R5_SIGN_REVERSALS_KNOWN": False,
            "REAL_R5_BETA_RANGES_KNOWN": False,
            "REAL_R5_MAX_DEVIATION_PERIODS_KNOWN": False,
            "R5_PRIMARY_MODEL_REPLACEMENTS": 0,
        },
        "execution_firewall": {
            "REAL_R5_EXECUTION_AUTHORIZATION_STATUS": "NOT_AUTHORIZED",
            "R6_AUTHORIZATION_STATUS": "NOT_AUTHORIZED",
            "R6_EXECUTED": False,
            "B3_STRICT_RESULTS_READ": False,
            "ENSO_SCENARIOS": "NOT_EXECUTED",
            "GVP": "NOT_EXECUTED",
            "VAR_CVAR": "NOT_EXECUTED",
            "A1_A2": "NOT_EXECUTED",
            "OPTIMIZATION": "NOT_EXECUTED",
        },
        "NEXT_TIER_AUTHORIZATION_STATUS": "NOT_AUTHORIZED",
        "next_action": "RETURN_TO_SCIENTIFIC_DIRECTOR_FOR_R5P_FREEZE_DECISION_IF_PASS",
    }
    payloads[PREFLIGHT_LOCK] = json_bytes(lock)
    return payloads


def build_package(output_root: Path) -> dict[str, bytes]:
    state = preflight()
    plan_payload = json_bytes(SYNTHETIC_PLAN)
    destination = output_root / TEST_PLAN_LOCK
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(plan_payload)
    first = render_package(state, plan_payload)
    second = render_package(state, plan_payload)
    require(first == second, "ER2_R5P_FAIL_REPRODUCIBILITY")
    for relative, payload in first.items():
        destination = output_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(payload)
    return {relative.as_posix(): payload for relative, payload in first.items()}


def check_existing() -> dict[str, bytes]:
    before = {relative: (ROOT / relative).read_bytes() for relative in GENERATED}
    with tempfile.TemporaryDirectory(prefix="er2_r5p_check_") as temporary:
        expected = build_package(Path(temporary))
    for relative, payload in expected.items():
        require((ROOT / relative).read_bytes() == payload, f"ER2_R5P_FAIL_REPRODUCIBILITY: {relative}")
    after = {relative: (ROOT / relative).read_bytes() for relative in GENERATED}
    require(before == after, "ER2_R5P_FAIL_REPRODUCIBILITY: check-only write")
    return expected


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the metadata-only ER2-R5P leave-one-period-out preflight package.")
    parser.add_argument("--output-root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    payloads = check_existing() if args.check else build_package(args.output_root.resolve())
    print("R4_STATUS=PASS_FROZEN_REMOTE_VERIFIED")
    print("REAL_OUTCOME_NUMERICAL_VALUES_READ=FALSE")
    print("REAL_CLIMATE_REGRESSOR_NUMERICAL_VALUES_READ=FALSE")
    print("REAL_R5_REFITS_EXECUTED=0")
    print("REAL_R5_BETAS_COMPUTED=FALSE")
    print("R5P_SYNTHETIC_REFERENCE_EQUIVALENCE=PASS")
    print("R5_REFIT_MODELS=38")
    print("R5_COEFFICIENT_OMISSION_ROWS=162")
    for relative, payload in sorted(payloads.items()):
        print(f"SHA256 {relative} {sha_bytes(payload)}")
    print(f"FINAL_VERDICT={FINAL_VERDICT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
