from __future__ import annotations

import argparse
import ast
import csv
from functools import lru_cache
import hashlib
import io
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import econometric_design_master_v1 as ed1
import er1_primary_real_estimation_v1 as er1
import er2_r4_spatial_hac_real_v1 as r4
import er2_r5p_leave_one_period_out_preflight_v1 as r5p

PARENT = "377a158e0e54b95ce4578fb28f64f601b31e4f5c"
BRANCH = "phase/er2-r5p-leave-one-period-out-preflight-v1"
TAG = "er2-r5p-leave-one-period-out-preflight-v1-freeze"
TAG_OBJECT = "af5ba135229554054b3f3abfde7d21e17e83cecb"
GATE = "ER2_R5_LEAVE_ONE_PERIOD_OUT_REAL_EXECUTION_V1"
VERDICT = "ER2_R5_PASS_RESULTS_LOCKED_READY_FOR_DIRECTOR_REVIEW"
PLAN = Path("outputs/econometrics/ER2_R5_EXECUTION_PLAN_LOCK.json")
DETAIL = Path("outputs/econometrics/ER2_R5_LOO_DETAIL_RESULTS.csv")
SUMMARY = Path("outputs/econometrics/ER2_R5_LOO_SUMMARY.csv")
AUDIT = Path("outputs/econometrics/ER2_R5_REFIT_AUDIT.csv")
CONCORDANCE = Path("outputs/econometrics/ER2_R5_CONCORDANCE.csv")
REPORT = Path("outputs/econometrics/ER2_R5_REPORT.md")
LOCK = Path("outputs/econometrics/ER2_R5_RESULTS_LOCK.json")
SCRIPT = Path("scripts/er2_r5_leave_one_period_out_real_v1.py")
TEST = Path("tests/test_er2_r5_leave_one_period_out_real_v1.py")
GENERATED = (PLAN, DETAIL, SUMMARY, AUDIT, CONCORDANCE, REPORT, LOCK)
CANDIDATES = (*GENERATED, SCRIPT, TEST)
R1_RESULTS = Path("outputs/econometrics/ER2_R1_LEVEL_RESULTS.csv")
R2_RESULTS = Path("outputs/econometrics/ER2_R2_STANDARDIZED_RESULTS.csv")
PREFLIGHT_SHA = "54a2d3ea35b3687bfb8806a092ae3c301f64ff210878d00ccaaf89130b0d334a"
R5P_HASHES = dict(zip(r5p.CANDIDATES, (
    "94adf7161b02e8c052d947443a69534b7c9e738769a1b861e0709c3df042bbf9",
    "55f1409a4b2e40fe98f7cbf69e7ebcb00654640b7c52371cb88aa9ac1f9928e9",
    "7aa322eed652102811974e139458b4470bd6f459753e12f3585b369c8f416bd5",
    "af82df4b5eb8b3fa122299ed47dd264eac28adb79a0a676188f1fbaa3805dca3",
    "a68afb62fbf733943a2e459bff1c565457527b4e179513ffe8c0ab5a422324ed",
    PREFLIGHT_SHA,
    "c907b5bf15d7a8de83abbd66bf916be879c5098ec2cf1d214f2e84b7bc0b0387",
    "7e922dd96b36d7592b66470c8fdf084e35f3b0f7871082d7178af0095f0daf82",
)))
DETAIL_FIELDS = r5p.FUTURE_DETAIL_SCHEMA
SUMMARY_FIELDS = r5p.FUTURE_SUMMARY_SCHEMA
AUDIT_FIELDS = (
    "REFIT_ORDER", "CROP", "CROP_CODE", "MODEL_ID", "PERIOD_ID_COLUMN",
    "OMITTED_PERIOD_ID", "MANDATORY_NAMED_CASE", "FULL_SAMPLE_N", "OMITTED_ROWS",
    "RETAINED_N", "FULL_PERIODS", "RETAINED_PERIODS", "RETAINED_DISTRICTS",
    "OMITTED_PERIOD_ROWS_REMAINING", "EXTRA_ROWS_REMOVED", "FULL_DESIGN_RANK_VALID",
    "WITHIN_CLIMATE_RANK_VALID", "ALL_TARGET_BETAS_FINITE", "MODEL_VALID", "STATUS",
    "FULL_ORDERED_KEY_SHA256", "RETAINED_ORDERED_KEY_SHA256", "EXPECTED_RETAINED_KEY_SHA256",
    "DISTRICT_FE", "REMAINING_PERIOD_FE", "REGRESSORS", "FULL_DESIGN_RANK",
    "FULL_DESIGN_COLUMNS", "WITHIN_CLIMATE_RANK",
)
CONCORDANCE_FIELDS = (
    "CROP", "CROP_CODE", "MODEL_ID", "VARIABLE", "PRIMARY_BETA_REFERENCE",
    "PRIMARY_SIGN", "R1_SIGN_WHERE_DISTINCT", "R2_SIGN", "WCR_P",
    "CONLEY_CI_ZERO_INCLUSION_50_100_150", "R5_SIGN_REVERSAL_COUNT", "R5_BETA_RANGE",
)
FORMULAS = {
    "BETA_DIFFERENCE": "LOO_BETA - PRIMARY_BETA_REFERENCE",
    "ABS_BETA_DEVIATION": "abs(LOO_BETA - PRIMARY_BETA_REFERENCE)",
    "SIGN": "POSITIVE if beta > 0; NEGATIVE if beta < 0; ZERO if beta == 0; no tolerance",
    "SIGN_REVERSAL": "LOO_BETA * PRIMARY_BETA_REFERENCE < 0; FALSE if either is exactly zero",
    "MIN_LOO_BETA": "min(all LOO betas)", "MAX_LOO_BETA": "max(all LOO betas)",
    "BETA_RANGE": "MAX_LOO_BETA - MIN_LOO_BETA", "MEDIAN_LOO_BETA": "ordinary numerical median",
    "POSITIVE_COUNT": "count(beta > 0)", "NEGATIVE_COUNT": "count(beta < 0)",
    "ZERO_COUNT": "count(beta == 0)", "SIGN_REVERSAL_COUNT": "count(LOO_BETA * PRIMARY_BETA_REFERENCE < 0)",
    "MAX_ABSOLUTE_BETA_DEVIATION": "max(abs(LOO_BETA - PRIMARY_BETA_REFERENCE))",
    "PERIODS_CAUSING_MAX_ABSOLUTE_DEVIATION": "REPORT_ALL_TIED_PERIOD_IDS_SORTED_NO_POST_RESULT_TIE_SELECTION; exact equality; pipe separated",
    "LEAVE_2017_OUT_BETA": "2016/2017 for transient; 2017 for perennial",
    "LEAVE_2023_OUT_BETA": "2022/2023 for transient; 2023 for perennial",
}
TEMPORAL = {key: True for key in (
    "PRIMARY_RESULTS_KNOWN", "R1_RESULTS_KNOWN", "R2_RESULTS_KNOWN", "R3_RESULTS_KNOWN",
    "R4_RESULTS_KNOWN", "R5P_FROZEN_BEFORE_REAL_R5", "R5_PERIOD_INVENTORY_FROZEN_BEFORE_RESULTS",
    "R5_SUMMARY_RULES_FROZEN_BEFORE_RESULTS", "R5_INFERENCE_FIREWALL_FROZEN_BEFORE_RESULTS",
)}
TEMPORAL.update(REAL_R5_RESULTS_KNOWN_BEFORE_EXECUTION=False, REAL_R5_REFITS_AT_LOCK=0)
FAIL_CLOSED = (
    "exact parent/local/remote/tag and raw predecessor identities",
    "unmodified frozen implementation, executor, tests and pre-result plan",
    "exact 38 omissions / 162 mapped rows / 21 targets / frozen period inventory",
    "exact frozen ER1 primary beta and numerical result identities",
    "full sample ordered keys, X/Y float64 SHA identities and exact regressors",
    "one scalar period omitted, all other ordered keys retained, no manual district deletion",
    "nonempty retained sample, exact retained periods, unique nonmissing keys, finite X/Y",
    "district and remaining-period fixed effects active",
    "full required design rank, full within climate rank, all named finite betas",
    "no per-omission inference output, primary replacement, result-specific branch or R6",
    "exact byte reproduction across two independent processes",
    "full-suite differential: no unrelated regression and no unresolved failure",
)

sha = r5p.sha_bytes
json_bytes = r5p.json_bytes
csv_bytes = r5p.csv_bytes
compact = r5p.compact_json_bytes


def require(ok: bool, marker: str, detail: str = "") -> None:
    if not ok:
        raise RuntimeError(f"ER2_R5_{marker}: {detail}")


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


@lru_cache(maxsize=None)
def blob(path: Path) -> bytes:
    return subprocess.check_output(["git", "cat-file", "blob", f"{PARENT}:{path.as_posix()}"], cwd=ROOT)


def frozen_json(path: Path) -> Any:
    return json.loads(blob(path))


def frozen_csv(path: Path) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(blob(path).decode("utf-8"))))


def immutable_write(path: Path, payload: bytes) -> None:
    if path.exists():
        require(path.read_bytes() == payload, "HOLD_POST_RESULT_CODE_CHANGE_REQUIRES_DIRECTOR_ADJUDICATION", str(path))
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as handle:
            handle.write(payload)


def verify_parent(remote: bool = True) -> None:
    refs = ("HEAD", BRANCH, f"origin/{BRANCH}", f"{TAG}^{{}}")
    require(all(git("rev-parse", ref) == PARENT for ref in refs), "FAIL_R5P_PREDECESSOR_IDENTITY")
    require(git("rev-parse", TAG) == TAG_OBJECT, "FAIL_R5P_PREDECESSOR_IDENTITY", "tag object")
    if remote:
        live = dict(line.split("\t")[::-1] for line in git("ls-remote", "origin", f"refs/heads/{BRANCH}", f"refs/tags/{TAG}", f"refs/tags/{TAG}^{{}}").splitlines())
        require(live == {f"refs/heads/{BRANCH}": PARENT, f"refs/tags/{TAG}": TAG_OBJECT, f"refs/tags/{TAG}^{{}}": PARENT}, "FAIL_R5P_PREDECESSOR_IDENTITY", "live remote")
    require(not git("diff", "--name-only") and not git("diff", "--cached", "--name-only"), "FAIL_UPSTREAM_IMMUTABILITY")
    require(set(git("ls-files", "--others", "--exclude-standard").splitlines()).issubset({p.as_posix() for p in CANDIDATES}), "FAIL_UPSTREAM_IMMUTABILITY", "ninth-path scope")


def frozen_hashes() -> dict[str, str]:
    expected = {**r5p.FROZEN_INPUT_SHA256, **r4.FROZEN_INPUT_SHA256, **R5P_HASHES}
    extra = [R1_RESULTS, R2_RESULTS, er1.SCRIPT_REL, Path("scripts/er2_r4p_spatial_hac_preflight_v1.py")]
    result = {}
    for path in dict.fromkeys([*expected, *extra]):
        payload = blob(path)
        digest = sha(payload)
        require(digest == expected.get(path, digest), "FAIL_UPSTREAM_IMMUTABILITY", path.as_posix())
        local = (ROOT / path).read_bytes()
        equal = local == payload
        if path.suffix in {".py", ".csv", ".json", ".md"}:
            equal = equal or local.replace(b"\r\n", b"\n") == payload
        require(equal, "FAIL_UPSTREAM_IMMUTABILITY", "substantive worktree drift " + path.as_posix())
        result[path.as_posix()] = digest
    return result


def estimator_identity() -> dict[str, Any]:
    source = blob(r5p.ED1_SCRIPT).decode("utf-8")
    lines = source.splitlines(keepends=True)
    node = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == "fit_two_way_fe_cr2")
    identity = {
        "file_sha256": sha(source.encode("utf-8")),
        "function": node.name,
        "source_sha256": sha("".join(lines[node.lineno - 1:node.end_lineno]).encode("utf-8")),
        "body_sha256": sha("".join(lines[node.body[0].lineno - 1:node.end_lineno]).encode("utf-8")),
        "architecture": "R5_EXECUTOR_CAN_REUSE_FROZEN_PRIMARY_ESTIMATION_DIRECTLY",
        "adapter_role": "FAIL_CLOSED_ONE_PERIOD_FILTER_AND_NAMED_COEFFICIENT_EXTRACTION_ONLY",
    }
    require([identity[k] for k in ("file_sha256", "source_sha256", "body_sha256")] == [r5p.ED1_IMPLEMENTATION_SHA, r5p.FIT_SOURCE_SHA, r5p.FIT_BODY_SHA], "FAIL_FROZEN_CONTRACT", "estimator identity")
    return identity


def plan_record() -> dict[str, Any]:
    hashes = frozen_hashes()
    tier = next(t for t in frozen_json(r5p.PROTOCOL)["tiers"] if t["tier"] == "R5")
    require(sha(json_bytes(tier)) == r5p.R5_TIER_CONTRACT_SHA, "FAIL_FROZEN_CONTRACT")
    omissions = frozen_csv(r5p.OMISSION_PLAN)
    mapping = frozen_csv(r5p.COEFFICIENT_MAP)
    targets = [row for row in mapping if row["OMITTED_PERIOD_ORDER"] == "1"]
    require((len(omissions), len(mapping), len(targets)) == (38, 162, 21), "FAIL_ROW_INVENTORY")
    return {
        "schema_version": "1.0.0", "project": r5p.PROJECT, "gate": GATE,
        "r5p_freeze_sha": PARENT, "r5p_preflight_lock_sha256": PREFLIGHT_SHA,
        "r5_tier_contract_sha256": r5p.R5_TIER_CONTRACT_SHA, "r5_tier_contract": tier,
        "temporal_governance": TEMPORAL, "omissions": omissions, "coefficient_omission_map": mapping,
        "summary_targets": targets, "summary_formulas": FORMULAS, "estimator": estimator_identity(),
        "sample_identity": {c: frozen_json(r5p.R2_LOCK)["sample_identity"][c]["er1_ordered_keys"] for c in r5p.CROP_ORDER},
        "sample_difference": "FULL_ER1_SAMPLE - ALL_ROWS_WITH_OMITTED_PERIOD; exact ordered-key difference",
        "row_order": "UBIGEO_THEN_PERIOD_STABLE_MERGESORT", "coefficient_order": "EXACT_FROZEN_ED1_REGRESSOR_ORDER",
        "detail_order": "EXACT_FROZEN_162_ROW_COEFFICIENT_OMISSION_MAP",
        "fixed_model_components": frozen_json(r5p.PREFLIGHT_LOCK)["fixed_model_components"],
        "schemas": {DETAIL.as_posix(): list(DETAIL_FIELDS), SUMMARY.as_posix(): list(SUMMARY_FIELDS), AUDIT.as_posix(): list(AUDIT_FIELDS), CONCORDANCE.as_posix(): list(CONCORDANCE_FIELDS)},
        "artifact_names": [p.as_posix() for p in CANDIDATES], "fail_closed": FAIL_CLOSED,
        "frozen_input_byte_source": "RAW_GIT_OBJECT", "frozen_input_sha256": hashes,
        "executor_sha256": sha((ROOT / SCRIPT).read_bytes()), "tests_sha256": sha((ROOT / TEST).read_bytes()),
        "float_serialization": "ROUNDTRIP_17_SIGNIFICANT_DIGITS_FINITE_ONLY", "encoding": "UTF-8_LF_NO_BOM_EXACTLY_ONE_FINAL_LF",
        "concordance": "Copy frozen R1/R2 signs, R3 WCR p, R4 zero inclusion; add R5 reversals/range only. R1 absent coefficient is NOT_DISTINCT_EQUIVALENCE_ONLY.",
        "primary_reference": "FROZEN_ER1_PRIMARY_BETA", "primary_numerical_identity": er1.NUMERICAL_RESULTS_IDENTITY,
        "inference_outputs": "NOT_AUTHORIZED", "stability_classification": "DESCRIPTIVE_NO_ARBITRARY_PASS_FAIL_THRESHOLD",
        "primary_replacement": "PROHIBITED", "result_specific_r5_branches": 0,
        "execution": "Two fresh subprocesses, exactly 38 real refits each; compare full calculation bytes before rendering both packages. No baseline refit, no RNG.",
        "certification_lifecycle": "Render PENDING full-suite status after two runs; run dedicated then full suite; certify external differential; render final report/lock from SAME saved calculations without refitting. Compare all seven outputs again. No code or plan changes.",
        "full_suite_baseline_ledger_sha256": "ed8d75917f3244bcd102aa2a1e54e3419c4918ac8747e3b36c316af0bc37dd29",
        "r6_authorization_status": "NOT_AUTHORIZED", "r6_executed": False,
    }


def verify_plan(payload: bytes) -> dict[str, Any]:
    require(payload == json_bytes(plan_record()), "HOLD_POST_RESULT_CODE_CHANGE_REQUIRES_DIRECTOR_ADJUDICATION", "pre-result lock/code/input drift")
    return json.loads(payload)


def exact_retained(frame: pd.DataFrame, period: str, omitted: str, expected_keys: list[list[str]]) -> pd.DataFrame:
    require(isinstance(omitted, str) and bool(omitted) and period in frame, "HOLD_INVALID_LOO_REFIT", "one period only")
    require(not frame[["UBIGEO", period]].isna().any().any(), "HOLD_INVALID_LOO_REFIT", "missing key")
    ordered = frame.sort_values(["UBIGEO", period], kind="mergesort").reset_index(drop=True)
    keys = ordered[["UBIGEO", period]].astype(str).values.tolist()
    require(keys == expected_keys and len({tuple(k) for k in keys}) == len(keys), "HOLD_INVALID_LOO_REFIT", "original keys")
    require(all(all(k) for k in keys), "HOLD_INVALID_LOO_REFIT", "empty key")
    periods = sorted({k[1] for k in keys})
    require(omitted in periods, "HOLD_INVALID_LOO_REFIT", "absent omission")
    retained = ordered[ordered[period].astype(str) != omitted].reset_index(drop=True)
    expected = [k for k in expected_keys if k[1] != omitted]
    require(retained[["UBIGEO", period]].astype(str).values.tolist() == expected and bool(expected), "HOLD_INVALID_LOO_REFIT", "ordered set difference")
    require(sorted(set(retained[period].astype(str))) == [p for p in periods if p != omitted] and len(periods) >= 3, "HOLD_INVALID_LOO_REFIT", "remaining periods")
    return retained


def refit(sample: dict[str, Any], omission: dict[str, Any]) -> tuple[dict[str, float], dict[str, Any]]:
    frame, columns, period = sample["frame"], sample["columns"], sample["period"]
    omitted = omission["OMITTED_PERIOD_ID"]
    require(len(columns) == len(set(columns)) and bool(columns) and all(c in frame for c in columns), "HOLD_INVALID_LOO_REFIT", "named regressors")
    retained = exact_retained(frame, period, omitted, sample["keys"])
    require(retained[period].nunique() == int(omission["RETAINED_PERIODS"]), "HOLD_INVALID_LOO_REFIT", "period count")
    x = retained[columns].to_numpy(dtype=float)
    y = retained["YIELD"].to_numpy(dtype=float)
    require(np.isfinite(x).all() and np.isfinite(y).all(), "HOLD_INVALID_LOO_REFIT", "nonfinite X/Y")
    fe = ed1.fe_matrix(retained, period)
    require(fe.shape[1] == retained.UBIGEO.nunique() + retained[period].nunique() - 1, "HOLD_INVALID_LOO_REFIT", "two-way FE")
    within_rank = int(np.linalg.matrix_rank(ed1.absorb_fixed_effects(x, fe)))
    design_columns = fe.shape[1] + len(columns)
    design_rank = int(np.linalg.matrix_rank(np.column_stack([fe, x])))
    require(within_rank == len(columns) and design_rank == design_columns, "HOLD_INVALID_LOO_REFIT", "required ranks")
    try:
        fitted = ed1.fit_two_way_fe_cr2(retained, columns, period, y)
    except Exception as error:
        raise RuntimeError("ER2_R5_HOLD_INVALID_LOO_REFIT: frozen estimator failed") from error
    beta = np.asarray(fitted["beta"], dtype=float)
    require(beta.shape == (len(columns),) and np.isfinite(beta).all(), "HOLD_INVALID_LOO_REFIT", "finite target betas")
    retained_keys = retained[["UBIGEO", period]].astype(str).values.tolist()
    expected = [k for k in sample["keys"] if k[1] != omitted]
    audit = {field: omission[field] for field in ("REFIT_ORDER", "CROP", "CROP_CODE", "MODEL_ID", "PERIOD_ID_COLUMN", "OMITTED_PERIOD_ID", "MANDATORY_NAMED_CASE")}
    audit.update(FULL_SAMPLE_N=len(frame), OMITTED_ROWS=len(frame)-len(retained), RETAINED_N=len(retained),
                 FULL_PERIODS=int(frame[period].nunique()), RETAINED_PERIODS=int(retained[period].nunique()),
                 RETAINED_DISTRICTS=int(retained.UBIGEO.nunique()), OMITTED_PERIOD_ROWS_REMAINING=0,
                 EXTRA_ROWS_REMOVED=0, FULL_DESIGN_RANK_VALID=True, WITHIN_CLIMATE_RANK_VALID=True,
                 ALL_TARGET_BETAS_FINITE=True, MODEL_VALID=True, STATUS="PASS_VALID_DESCRIPTIVE_REFIT",
                 FULL_ORDERED_KEY_SHA256=sha(compact(sample["keys"])), RETAINED_ORDERED_KEY_SHA256=sha(compact(retained_keys)),
                 EXPECTED_RETAINED_KEY_SHA256=sha(compact(expected)), DISTRICT_FE="REQUIRED_ACTIVE",
                 REMAINING_PERIOD_FE="REQUIRED_ACTIVE", REGRESSORS="|".join(columns),
                 FULL_DESIGN_RANK=design_rank, FULL_DESIGN_COLUMNS=design_columns, WITHIN_CLIMATE_RANK=within_rank)
    return dict(zip(columns, map(float, beta))), audit


def load_references() -> dict[str, Any]:
    primary = frozen_csv(r4.ER1_COEFFICIENTS)
    identity = sha(compact(er1.ACCEPTED_NUMERICAL_TABLE_SHA256))
    require(identity == er1.NUMERICAL_RESULTS_IDENTITY == "40e0f58269dda309e83a1fa3da17ef4d5dc5523efc72a666f734d0ebacb76b24", "FAIL_PRIMARY_BETA_IDENTITY")
    require(sha(blob(r4.ER1_COEFFICIENTS)) == "37fa03a2e860f86277510a5ff3b66ca475fc02d277ea1dd6e18156f719c23480", "FAIL_PRIMARY_BETA_IDENTITY")
    require(len(primary) == 21 and len({(r["CROP_CODE"], r["CLIMATE_VARIABLE"]) for r in primary}) == 21, "FAIL_PRIMARY_BETA_IDENTITY")
    return {
        "er1": {(r["CROP_CODE"], r["CLIMATE_VARIABLE"]): r for r in primary},
        "r3_samples": {r["CROP_CODE"]: r for r in frozen_csv(r4.R3_SAMPLES)},
        "r2_sample_identity": frozen_json(r4.R2_LOCK)["sample_identity"],
    }


def detail_row(target: dict[str, Any], primary: float, beta: float, audit: dict[str, Any]) -> dict[str, Any]:
    row = {k: target[k] for k in DETAIL_FIELDS[:7]}
    row.update(PRIMARY_BETA_REFERENCE=primary, LOO_BETA=beta, BETA_DIFFERENCE=beta-primary,
               ABS_BETA_DEVIATION=abs(beta-primary), PRIMARY_SIGN=r5p.classify_sign(primary),
               LOO_SIGN=r5p.classify_sign(beta), SIGN_REVERSAL=r5p.sign_reversal(primary, beta),
               RETAINED_N=audit["RETAINED_N"], RETAINED_PERIODS=audit["RETAINED_PERIODS"],
               MODEL_VALID=True, STATUS="DESCRIPTIVE_ONLY")
    return row


def summarize(detail: list[dict[str, Any]], targets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for target in targets:
        selected = [r for r in detail if (r["CROP_CODE"], r["VARIABLE"]) == (target["CROP_CODE"], target["VARIABLE"])]
        expected = list(r5p.EXPECTED_PERIODS[target["CROP_CODE"]])
        require([r["OMITTED_PERIOD_ID"] for r in selected] == expected, "FAIL_ROW_INVENTORY", "summary periods")
        primary = selected[0]["PRIMARY_BETA_REFERENCE"]
        require(all(r["PRIMARY_BETA_REFERENCE"] == primary and r["MODEL_VALID"] for r in selected), "FAIL_PRIMARY_BETA_IDENTITY")
        result = r5p.summarize_loo(primary, [(r["OMITTED_PERIOD_ID"], r["LOO_BETA"]) for r in selected])
        result = {k: int(v) if isinstance(v, np.integer) else v for k, v in result.items()}
        result["PERIODS_CAUSING_MAX_ABSOLUTE_DEVIATION"] = "|".join(result["PERIODS_CAUSING_MAX_ABSOLUTE_DEVIATION"])
        row = {k: target[k] for k in SUMMARY_FIELDS[:4]}
        row.update(result)
        for year in (2017, 2023):
            row[f"LEAVE_{year}_OUT_BETA"] = next(r["LOO_BETA"] for r in selected if r["MANDATORY_NAMED_CASE"] == f"LEAVE_{year}_OUT")
        row["STATUS"] = "DESCRIPTIVE_NO_ARBITRARY_PASS_FAIL_THRESHOLD"
        rows.append(row)
    return rows


def concordance(summary: list[dict[str, Any]]) -> list[dict[str, Any]]:
    r1 = {(r["CROP_CODE"], r["ER1_VARIABLE"]): r for r in frozen_csv(R1_RESULTS)}
    r2 = {(r["CROP_CODE"], r["ER1_VARIABLE"]): r for r in frozen_csv(R2_RESULTS)}
    previous = {(r["CROP_CODE"], r["VARIABLE"]): r for r in frozen_csv(r5p.R4_CONCORDANCE)}
    rows = []
    for result in summary:
        key = (result["CROP_CODE"], result["VARIABLE"])
        old = previous[key]
        require(float(old["ER1_BETA"]) == result["PRIMARY_BETA_REFERENCE"], "FAIL_PRIMARY_BETA_IDENTITY", "concordance")
        row = {k: result[k] for k in SUMMARY_FIELDS[:5]}
        row.update(PRIMARY_SIGN=r5p.classify_sign(result["PRIMARY_BETA_REFERENCE"]),
                   R1_SIGN_WHERE_DISTINCT=r5p.classify_sign(float(r1[key]["BETA"])) if key in r1 else "NOT_DISTINCT_EQUIVALENCE_ONLY",
                   R2_SIGN=r5p.classify_sign(float(r2[key]["BETA"])), WCR_P=old["R3_WCR_P"],
                   CONLEY_CI_ZERO_INCLUSION_50_100_150="|".join(old[f"R4_{b}_CI_ZERO_INCLUDED"] for b in (50, 100, 150)),
                   R5_SIGN_REVERSAL_COUNT=result["SIGN_REVERSAL_COUNT"], R5_BETA_RANGE=result["BETA_RANGE"])
        rows.append(row)
    return rows


def calculate(plan_payload: bytes) -> dict[str, Any]:
    verify_parent()
    plan = verify_plan(plan_payload)
    refs = load_references()
    # This is the first numerical Y/X reader; the caller has persisted the plan and access marker.
    samples, source_metadata = r4.prepare_real_samples(refs)
    for code, sample in samples.items():
        targets = [t for t in plan["summary_targets"] if t["CROP_CODE"] == code]
        require(sample["columns"] == [t["VARIABLE"] for t in targets], "FAIL_FROZEN_CONTRACT", "regressor order")
        require(sample["keys"] == plan["sample_identity"][code], "FAIL_ROW_INVENTORY", "sample keys")
        require(tuple(sorted(sample["frame"][sample["period"]].unique())) == r5p.EXPECTED_PERIODS[code], "FAIL_ROW_INVENTORY", "period inventory")
    fitted, audits = {}, []
    for omission in plan["omissions"]:
        code, period = omission["CROP_CODE"], omission["OMITTED_PERIOD_ID"]
        betas, audit = refit(samples[code], omission)
        fitted[(code, period)] = (betas, audit)
        audits.append(audit)
    detail = []
    for target in plan["coefficient_omission_map"]:
        key = (target["CROP_CODE"], target["VARIABLE"])
        reference = refs["er1"][key]
        require(reference["MODEL_ID"] == target["MODEL_ID"], "FAIL_PRIMARY_BETA_IDENTITY", "model id")
        betas, audit = fitted[(key[0], target["OMITTED_PERIOD_ID"])]
        detail.append(detail_row(target, float(reference["BETA"]), betas[key[1]], audit))
    summary = summarize(detail, plan["summary_targets"])
    data = {"audits": audits, "detail": detail, "summary": summary, "concordance": concordance(summary)}
    require(tuple(map(len, (audits, detail, summary, data["concordance"]))) == (38, 162, 21, 21), "FAIL_ROW_INVENTORY")
    data["calculation_sha256"] = sha(compact({k: data[k] for k in ("audits", "detail", "summary")}))
    data["primary_coefficient_identities"] = [{"CROP_CODE": k[0], "VARIABLE": k[1], "FROZEN_ER1_BETA_TEXT": r["BETA"]} for k, r in refs["er1"].items()]
    data["sample_identity"] = {c: {k: s[k] for k in ("ordered_key_sha256", "y_float64_sha256", "x_float64_sha256", "actual")} for c, s in samples.items()}
    data["source_metadata"] = source_metadata
    verify_plan(plan_payload)
    return data


def table(rows: list[dict[str, Any]], fields: list[str]) -> list[str]:
    def cell(value: Any) -> str:
        return r5p.canonical_float(value) if isinstance(value, float) else str(value).replace("|", ", ")
    return ["| " + " | ".join(fields) + " |", "| " + " | ".join("---" for _ in fields) + " |", *["| " + " | ".join(cell(r[f]) for f in fields) + " |" for r in rows]]


def report(data: dict[str, Any], plan_sha: str, suite: dict[str, Any]) -> bytes:
    lines = ["# ER2-R5 Real Leave-One-Period-Out All-Periods Results v1", "", f"PROJECT={r5p.PROJECT}", "NO_FREEZE; DESCRIPTIVE_INFLUENCE_ONLY; PRIMARY_REPLACEMENT=PROHIBITED", ""]
    def section(title: str, content: list[str]) -> None:
        lines.extend(["## " + title, "", *content, ""])
    section("1. R5 VERDICT", [VERDICT if suite["status"] == "PASS_ADJUDICATED" else "PENDING_FULL_SUITE_ADJUDICATION"])
    section("2. R5P FROZEN PREDECESSOR", [f"R5P_FREEZE_SHA={PARENT}", f"R5P_LOCK_SHA256={PREFLIGHT_SHA}"])
    section("3. TEMPORAL / PRE-RESULT EXECUTION LOCK", [f"EXECUTION_PLAN_LOCK_SHA256={plan_sha}", *[f"{k}={v}" for k, v in TEMPORAL.items()]])
    section("4. R5 CONTRACT IDENTITY", [r5p.R5_TIER_CONTRACT_SHA, "ALL_PERIOD_INFLUENCE_DESCRIPTION; PHYSICAL_ANOMALY; no significance vote counting."])
    section("5. PRIMARY BETA IDENTITY", [f"FROZEN_ER1_NUMERICAL_IDENTITY={er1.NUMERICAL_RESULTS_IDENTITY}", "All 21 references are copied from frozen ER1; no baseline refit."])
    section("6. SAMPLE / PERIOD INVENTORY", [f"{ed1.CROPS[c]['crop']}: {r5p.EXPECTED_SAMPLE_N[c]} rows; {'|'.join(r5p.EXPECTED_PERIODS[c])}" for c in r5p.CROP_ORDER])
    section("7. 38-REFIT VALIDITY AUDIT", ["38/38 valid. Exact ordered sample difference; no extra row removal. Retained districts recorded descriptively; both fixed effects and rank gates active."])
    section("8. 162-ROW INVENTORY", ["Rice=21; MAD=21; Mango=24; Lemon=48; Banana=48; exact frozen mapping order."])
    section("9. 21-SUMMARY INVENTORY", ["One summary for each frozen primary coefficient, using every planned omission."])
    fields = ["VARIABLE", "PRIMARY_BETA_REFERENCE", "MIN_LOO_BETA", "MAX_LOO_BETA", "BETA_RANGE", "SIGN_REVERSAL_COUNT", "PERIODS_CAUSING_MAX_ABSOLUTE_DEVIATION", "LEAVE_2017_OUT_BETA", "LEAVE_2023_OUT_BETA"]
    for index, code in enumerate(r5p.CROP_ORDER, 10):
        section(f"{index}. {ed1.CROPS[code]['crop'].upper()} SUMMARY - ALL COEFFICIENTS", table([r for r in data["summary"] if r["CROP_CODE"] == code], fields))
    section("15. SIGN-REVERSAL INVENTORY", table([r for r in data["detail"] if r["SIGN_REVERSAL"]], ["CROP", "VARIABLE", "OMITTED_PERIOD_ID", "PRIMARY_BETA_REFERENCE", "LOO_BETA"]) + ["For coefficients with zero reversals: NO SIGN REVERSAL WAS OBSERVED ACROSS THE PRESPECIFIED LEAVE-ONE-PERIOD-OUT REFITS. This is not a robustness classification."])
    section("16. MAXIMUM-DEVIATION PERIOD INVENTORY", table(data["summary"], ["CROP", "VARIABLE", "MAX_ABSOLUTE_BETA_DEVIATION", "PERIODS_CAUSING_MAX_ABSOLUTE_DEVIATION"]))
    for number, year in ((17, 2017), (18, 2023)):
        section(f"{number}. LEAVE-{year} RESULTS - ALL 21 COEFFICIENTS", table(data["summary"], ["CROP", "VARIABLE", f"LEAVE_{year}_OUT_BETA"]))
    section("19. R5 BETA-RANGE INVENTORY", table(data["summary"], ["CROP", "VARIABLE", "BETA_RANGE", "MEDIAN_LOO_BETA", "POSITIVE_COUNT", "NEGATIVE_COUNT", "ZERO_COUNT"]))
    section("20. R1/R2/R3/R4/R5 DESCRIPTIVE CONCORDANCE", table(data["concordance"], list(CONCORDANCE_FIELDS)))
    section("21. INFERENCE / VOTE-COUNTING FIREWALL", ["R5_LOO_INFERENCE_OUTPUTS=NOT_AUTHORIZED. WCR p and Conley zero inclusion in concordance are copied historical R3/R4 quantities, never LOO inference. No scoring, voting or arbitrary stability thresholds."])
    section("22. RESULT-SPECIFIC BRANCH AUDIT", ["RESULT_SPECIFIC_R5_BRANCHES=0; one shared estimator path for every crop, variable and period."])
    section("23. TWO-RUN REAL-R5 REPRODUCIBILITY", ["PASS: two independent 38-refit subprocesses; exact calculation bytes and all seven final artifacts. No RNG."])
    section("24. R5 CALCULATION SHA", [data["calculation_sha256"]])
    section("25. R5 RESULTS LOCK SHA", ["External SHA-256 recorded in the Director return manifest; omitted here to avoid report/lock circular hashing."])
    section("26. CREATED R5 ARTIFACTS AND SHA MANIFEST", ["Exactly nine candidate paths; noncircular artifact hashes in results lock; complete external nine-file manifest.", *[p.as_posix() for p in CANDIDATES]])
    section("27. REAL-R5 DEDICATED TESTS", [suite.get("dedicated_tests", "PENDING; run after deterministic package creation")])
    section("28. FULL-SUITE DIFFERENTIAL ADJUDICATION", [json.dumps(suite, sort_keys=True), "Historical numerical reads are test-only; external evidence is not part of the nine-file candidate."])
    section("29. FINDINGS BY SEVERITY", ["No invalid refit or inference leakage. Descriptive period influence is not a causal identification claim. Full-suite findings are subject to the exact external differential shown above."])
    section("30. EXACT NEXT ACTION", ["RETURN_TO_SCIENTIFIC_DIRECTOR_FOR_R5_RESULTS_REVIEW", "R6_AUTHORIZATION_STATUS=NOT_AUTHORIZED; R6_EXECUTED=FALSE; NO_STAGING_COMMIT_PUSH_TAG."])
    return ("\n".join(lines).rstrip("\n") + "\n").encode("utf-8")


def render(data: dict[str, Any], plan_payload: bytes, suite: dict[str, Any]) -> dict[Path, bytes]:
    plan = json.loads(plan_payload)
    payloads = {PLAN: plan_payload, DETAIL: csv_bytes(data["detail"], DETAIL_FIELDS), SUMMARY: csv_bytes(data["summary"], SUMMARY_FIELDS), AUDIT: csv_bytes(data["audits"], AUDIT_FIELDS), CONCORDANCE: csv_bytes(data["concordance"], CONCORDANCE_FIELDS), REPORT: report(data, sha(plan_payload), suite)}
    lock = {
        "schema_version": "1.0.0", "gate": GATE,
        "status": "RESULTS_LOCKED_READY_FOR_DIRECTOR_REVIEW" if suite["status"] == "PASS_ADJUDICATED" else "RESULTS_COMPUTED_PENDING_FULL_SUITE_ADJUDICATION",
        "final_verdict": VERDICT if suite["status"] == "PASS_ADJUDICATED" else "PENDING_FULL_SUITE_ADJUDICATION",
        "r5p_freeze_sha": PARENT, "r5p_lock_sha256": PREFLIGHT_SHA, "r5_tier_contract_sha256": r5p.R5_TIER_CONTRACT_SHA,
        "execution_plan_lock_sha256": sha(plan_payload), "estimator": plan["estimator"],
        "primary_numerical_identity": er1.NUMERICAL_RESULTS_IDENTITY, "primary_coefficient_identities": data["primary_coefficient_identities"],
        "refit_audit": data["audits"], "detail": data["detail"], "summary": data["summary"], "concordance": data["concordance"],
        "sample_identity": data["sample_identity"], "summary_formulas": FORMULAS,
        "invalid_refit_inventory": [], "result_specific_r5_branches": 0,
        "two_run_reproducibility": {"status": "PASS", "independent_processes": 2, "real_refits_per_process": 38, "calculation_sha256": data["calculation_sha256"], "all_seven_outputs_byte_identical": True},
        "calculation_sha256": data["calculation_sha256"], "full_suite_adjudication": suite,
        "artifact_sha256": {**{p.as_posix(): sha(b) for p, b in payloads.items()}, SCRIPT.as_posix(): plan["executor_sha256"], TEST.as_posix(): plan["tests_sha256"]},
        "primary_replacement": "PROHIBITED", "r5_loo_inference_outputs": "NOT_AUTHORIZED",
        "real_r5_betas_computed": True, "real_r5_refit_models": 38,
        "r6_authorization_status": "NOT_AUTHORIZED", "r6_executed": False,
        "downstream": "ENSO_SCENARIOS_GVP_VAR_CVAR_A1_A2_OPTIMIZATION_NOT_EXECUTED",
    }
    payloads[LOCK] = json_bytes(lock)
    return payloads


def worker(evidence: Path, label: str) -> None:
    plan_payload = (ROOT / PLAN).read_bytes()
    verify_parent()
    verify_plan(plan_payload)
    marker = evidence / f"{label}_before_numerical_access.json"
    require(not marker.exists(), "HOLD_POST_RESULT_CODE_CHANGE_REQUIRES_DIRECTOR_ADJUDICATION", "worker already started")
    immutable_write(marker, json_bytes({"plan_sha256": sha(plan_payload), "temporal_governance": TEMPORAL, "executor_sha256": sha((ROOT / SCRIPT).read_bytes()), "tests_sha256": sha((ROOT / TEST).read_bytes()), "phase": "BEFORE_FIRST_REAL_NUMERICAL_Y_X_ACCESS_IN_THIS_PROCESS"}))
    immutable_write(evidence / f"{label}_calculation.json", json_bytes(calculate(plan_payload)))


def certify(evidence: Path, suite_path: Path | None = None) -> dict[str, str]:
    plan_payload = (ROOT / PLAN).read_bytes()
    verify_plan(plan_payload)
    first = (evidence / "run1_calculation.json").read_bytes()
    second = (evidence / "run2_calculation.json").read_bytes()
    require(first == second, "HOLD_NONDETERMINISTIC_REAL_R5")
    suite = json.loads(suite_path.read_bytes()) if suite_path else {"status": "PENDING_FULL_SUITE_ADJUDICATION"}
    if suite_path:
        require(suite["status"] == "PASS_ADJUDICATED" and suite["unrelated_real_regressions"] == suite["unresolved_failures"] == 0, "FAIL_TEST_REGRESSION")
    one, two = render(json.loads(first), plan_payload, suite), render(json.loads(second), plan_payload, suite)
    require(one == two and tuple(one) == GENERATED, "HOLD_NONDETERMINISTIC_REAL_R5")
    phase = "certified" if suite_path else "pending"
    for number, payloads in enumerate((one, two), 1):
        for relative, payload in payloads.items():
            immutable_write(evidence / f"run{number}_{phase}" / relative, payload)
    for relative, payload in one.items():
        path = ROOT / relative
        if path.exists() and path.read_bytes() != payload:
            require(suite_path is not None and relative in (REPORT, LOCK), "HOLD_POST_RESULT_CODE_CHANGE_REQUIRES_DIRECTOR_ADJUDICATION", "unexpected artifact change")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    return {p.as_posix(): sha((ROOT / p).read_bytes()) for p in CANDIDATES}


def main() -> int:
    parser = argparse.ArgumentParser(description="Locked real R5 execution, coefficient influence only.")
    parser.add_argument("mode", choices=("lock", "worker", "certify"))
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--label", choices=("run1", "run2"))
    parser.add_argument("--suite-evidence", type=Path)
    args = parser.parse_args()
    evidence = args.evidence.resolve()
    require(not evidence.is_relative_to(ROOT), "FAIL_UPSTREAM_IMMUTABILITY", "evidence must be outside repository")
    if args.mode == "lock":
        verify_parent()
        payload = json_bytes(plan_record())
        immutable_write(ROOT / PLAN, payload)
        immutable_write(evidence / "pre_result_execution_plan.json", payload)
        print("ER2_R5_EXECUTION_PLAN_LOCK_SHA256=" + sha(payload), flush=True)
    elif args.mode == "worker":
        require(args.label is not None, "FAIL_FROZEN_CONTRACT", "worker label required")
        worker(evidence, args.label)
        print(args.label + "_38_REAL_REFITS_COMPLETED", flush=True)
    else:
        print(json.dumps(certify(evidence, args.suite_evidence), indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
