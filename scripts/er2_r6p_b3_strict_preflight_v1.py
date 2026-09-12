from __future__ import annotations

import argparse
import ast
import copy
import csv
import hashlib
import inspect
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
import econometric_design_master_v1 as ed1

PROJECT = "ENSO_EL_NINO_2026_2027_AGRICULTURE_PIURA"
GATE = "ER2_R6P_B3_STRICT_EXPOSURE_PREEXECUTION_CERTIFICATION_V1"
VERDICT = "ER2_R6P_PASS_B3_STRICT_PREEXECUTION_CERTIFIED_READY_FOR_DIRECTOR_FREEZE_DECISION"
PARENT = "fec889f71f97397c320c3f911306d10676439a5c"
BRANCH = "phase/er2-r5-leave-one-period-out-v1"
TAG = "er2-r5-leave-one-period-out-v1-freeze"
TAG_OBJECT = "a121c66e6f365c9eb4f70ac1f2df1e4406b7b730"
TIER_SHA = "f0b589050a7ec2ee198683e951e8e4ee049235540c686e996471f719a14d3c1c"
B3 = "data/processed/phenology/transient_campaign_exposures_strict.parquet"
D0 = "data/processed/outcomes/transient_campaign_outcomes_master.csv"
PROTOCOL = "config/econometrics/er2_robustness_protocol_v1.json"
HIERARCHY = "outputs/econometrics/ED1_ROBUSTNESS_HIERARCHY.csv"
TIERS = "outputs/econometrics/ER2P_TIER_CONTRACTS.csv"
ESTIMATOR = "scripts/econometric_design_master_v1.py"
R5_LOCK = "outputs/econometrics/ER2_R5_RESULTS_LOCK.json"
FROZEN_SHA = {
    B3: "349413312568d0d423675bf58320ade41d2d9e700f138e7fbec55fc580bc1fb5",
    D0: "9cae62fb1417fa41274f6d504515571abd428b71fecaa0d138d3b786aa538760",
    PROTOCOL: "13519fb5c86fdf690d233c54dd45c3242ba348f3c7f66587238e6965ed1c49ff",
    HIERARCHY: "87959f394c3b6d486523e216dc61a0a7fca29a99d2e688ac5e80317162a4c3e1",
    TIERS: "2ff57eadb872ca6aa10cb84aa4fdf9b7250715df5ca77d2f3e9d22621e7d762a",
    ESTIMATOR: "69fb1b1f0a1d7c4ec7791fdfa2d3cfb20d62b4ed0f6348b155155523b6b48195",
    R5_LOCK: "d3395ea24d8f03a81f95f51ce0b49286729db6fe6f64204b4fa2a3bdd6dd28d2",
}
PREFIX = "outputs/econometrics/ER2_R6P_"
REPORT = PREFIX + "PREFLIGHT_REPORT.md"
SUPPORT = PREFIX + "SUPPORT_AUDIT.csv"
VALIDATION = PREFIX + "SYNTHETIC_VALIDATION.csv"
PLAN = PREFIX + "SYNTHETIC_TEST_PLAN_LOCK.json"
LOCK = PREFIX + "PREFLIGHT_LOCK.json"
SCRIPT = "scripts/er2_r6p_b3_strict_preflight_v1.py"
TEST = "tests/test_er2_r6p_b3_strict_preflight_v1.py"
GENERATED = (REPORT, SUPPORT, VALIDATION, PLAN, LOCK)
CANDIDATES = (*GENERATED, SCRIPT, TEST)
RICE, MAD = "14010020000", "14010070000"
PERENNIALS = ("13010210000", "13010170102", "15010040000")
X = ("RAIN_ANOM_MM", "TMAX_ANOM_C", "TMIN_ANOM_C")
KEY = ("COD_CULTIVO", "UBIGEO", "CAMPAIGN_ID")
B3_META = (*KEY, "WINDOW_ID", "CAMPAIGN_WEIGHTED_EXPOSURE_VALID", "FAILURE_REASON")
D0_META = ("CROP_CODE", "UBIGEO", "CAMPAIGN", "OUTCOME_VALID_FLAG")
Y = "TRANSIENT_CAMPAIGN_YIELD_RAW"
SAMPLE_RULE = "EXACT_D0_OUTCOME_AND_B3_VALID_EXPOSURE_INTERSECTION"
ADMISSIBLE = "R6_RICE_INFERENTIALLY_ADMISSIBLE"
INADMISSIBLE = "R6_RICE_NOT_INFERENTIALLY_ADMISSIBLE"
MAD_STATUS = "NOT_ESTIMABLE_UNDER_PRIMARY_DESIGN"
TERMINAL = "MAD_STRUCTURAL_NONESTIMABILITY_AND_DECLARED_RICE_INADMISSIBILITY_ARE_REPORTED_NOT_SUBSTITUTED"
ADMISSIBILITY = "FULL_WITHIN_RANK_VALID_CR2_ADJUSTMENTS_POSITIVE_FINITE_SE_AND_DF_VALID_FINITE_AHT"
TOL = 1e-10
MODEL = {
    "outcome": "YIELD_LEVEL_TM_PER_HA", "windows": "EXACT_ED1_FROZEN",
    "functional_form": "LINEAR_ADDITIVE", "district_fe": "REQUIRED",
    "campaign_fe": "REQUIRED", "weighting": "UNWEIGHTED",
    "district_trends": "PROHIBITED", "regressors": list(X),
    "estimator": "fit_two_way_fe_cr2", "substitute_model": "PROHIBITED",
}
GATES = ("N_31", "DISTRICTS_12", "PERIODS_7", "FULL_DESIGN_RANK",
         "WITHIN_RANK_3", "CR2_ADJUSTMENTS", "POSITIVE_FINITE_SE",
         "POSITIVE_FINITE_DF", "FINITE_COEFFICIENT_STATISTICS", "VALID_FINITE_AHT")
CASES = {
    "A": "N_31", "B": "DISTRICTS_12", "C": "PERIODS_7",
    "D": "WITHIN_RANK_3", "E": "FULL_DESIGN_RANK", "F": "CR2_ADJUSTMENTS",
    "G": "POSITIVE_FINITE_SE", "H": "POSITIVE_FINITE_SE",
    "I": "POSITIVE_FINITE_DF", "J": "VALID_FINITE_AHT",
    "K": "REQUIRED_COLUMNS", "L": "UNIQUE_KEYS", "M": "VALID_B3_ONLY",
    "N": "EXACT_INTERSECTION", "O": "MAD_ESTIMATION_PROHIBITED",
    "P": "PERENNIAL_ESTIMATION_PROHIBITED", "Q": "FROZEN_MODEL",
    "R": "FROZEN_MODEL",
}
COEFFICIENT_FIELDS = (
    "CROP", "CROP_CODE", "VARIABLE", "ER1_BETA_REFERENCE", "R6_B3_BETA",
    "CR2_SE", "SATTERTHWAITE_DF", "T_STATISTIC", "RAW_P", "CI_LOWER",
    "CI_UPPER", "SIGN", "ADMISSIBILITY_STATUS",
)
AHT_MAPPING = {
    "JOINT_WALD_CHI_SQUARE": "wald_chi_square", "JOINT_F": "f_statistic",
    "NUMERATOR_DF": "numerator_df", "DENOMINATOR_DF": "denominator_df",
    "RAW_JOINT_P": "p_value", "HTZ_DELTA": "delta",
}


def payload(value):
    return (json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, reason):
    if not condition:
        raise RuntimeError(reason)


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def frozen_bytes(path):
    raw = git("show", f"{PARENT}:{path}")
    require(sha(raw) == FROZEN_SHA[path], "FROZEN_RAW_BLOB_IDENTITY: " + path)
    local = (ROOT / path).read_bytes()
    if path.endswith(".parquet"):
        require(local == raw, "BINARY_WORKTREE_IDENTITY: " + path)
    else:
        require(local.replace(b"\r\n", b"\n") == raw, "TEXT_WORKTREE_SEMANTIC_IDENTITY: " + path)
    return raw


def predecessor():
    for ref in ("HEAD", "@{upstream}", TAG + "^{}"):
        require(git("rev-parse", ref).decode().strip() == PARENT, "R5_PREDECESSOR: " + ref)
    require(git("branch", "--show-current").decode().strip() == BRANCH, "R5_BRANCH")
    require(git("rev-parse", TAG).decode().strip() == TAG_OBJECT, "R5_TAG_OBJECT")
    require(not git("diff", "--name-only").strip(), "TRACKED_CHANGES")
    require(not git("diff", "--cached", "--name-only").strip(), "STAGED_CHANGES")
    return {"head": PARENT, "branch": BRANCH, "tag": TAG, "tag_object": TAG_OBJECT}


def contracts():
    for path in FROZEN_SHA:
        frozen_bytes(path)
    protocol = json.loads(frozen_bytes(PROTOCOL))
    tier = next(t for t in protocol["tiers"] if t["tier"] == "R6")
    require(sha(payload(tier)) == TIER_SHA, "R6_TIER_IDENTITY")
    rows = list(csv.DictReader(io.StringIO(frozen_bytes(TIERS).decode())))
    tier_row = next(r for r in rows if r["ORDER"] == "6")
    require(tier_row["TIER_CONTRACT_SHA256"] == TIER_SHA, "TIER_CSV_IDENTITY")
    hierarchy = next(r for r in csv.DictReader(io.StringIO(frozen_bytes(HIERARCHY).decode())) if r["ORDER"] == "6")
    expected = {
        "ORDER": "6", "TIER": "R6_B3_STRICT_EXPOSURE",
        "STATUS": "RICE_ESTIMABLE_SEVERE_SUPPORT_LIMITATION_MAD_NOT_ESTIMABLE",
        "CHANGE_FROM_PRIMARY": "STRICT_TRANSIENT_EXPOSURE_SAMPLE_AND_VALUES",
        "FIXED_COMPONENTS": "OUTCOME_LEVEL|WINDOWS|LINEAR_FORM|DISTRICT_FE|PERIOD_FE|UNWEIGHTED",
        "INTERPRETATION": "ATTRIBUTION_QUALITY_SENSITIVITY_RICE_ONLY",
        "NO_WINNER_RULE": "B3_CANNOT_REPLACE_PRIMARY_OR_WEAKEN_FE",
    }
    require(hierarchy == expected, "HIERARCHY_IDENTITY")
    rice = next(r for r in protocol["crop_model_contracts"] if r["CROP_CODE"] == RICE)
    require(rice["PRIMARY_REGRESSORS"].split("|") == list(X), "RICE_X_IDENTITY")
    require(rice["OBSERVATIONS"] == 281, "ER1_SUPPORT_IDENTITY")
    return protocol, tier, hierarchy


def metadata_only():
    frozen_bytes(B3)
    frozen_bytes(D0)
    schema = pq.read_schema(ROOT / B3)
    d0_schema = pd.read_csv(ROOT / D0, nrows=0).columns.tolist()
    require(set((*B3_META, *X)) <= set(schema.names), "B3_SCHEMA")
    require(set((*D0_META, Y)) <= set(d0_schema), "D0_SCHEMA")
    # Projection is the real-data firewall: no Y or X numerical column is loaded.
    b = pq.read_table(ROOT / B3, columns=list(B3_META)).to_pandas()
    d = pd.read_csv(ROOT / D0, usecols=list(D0_META), dtype=str)
    require(not b[list(KEY)].isna().any().any(), "B3_NULL_KEY")
    require(not b.duplicated(list(KEY)).any(), "B3_DUPLICATE_KEY")
    require(not d[list(D0_META)].isna().any().any(), "D0_NULL_METADATA")
    require(not d.duplicated(["CROP_CODE", "UBIGEO", "CAMPAIGN"]).any(), "D0_DUPLICATE_KEY")
    require(set(d.OUTCOME_VALID_FLAG) <= {"TRUE", "FALSE"}, "D0_VALIDITY_DOMAIN")
    valid = b[b.CAMPAIGN_WEIGHTED_EXPOSURE_VALID]
    require(set(valid.FAILURE_REASON) == {"NONE"}, "AMBIGUOUS_VALID_B3_ROW")
    inventory = {"total": len(b), "valid": len(valid), "invalid": len(b) - len(valid),
                 "rice": int((valid.COD_CULTIVO == RICE).sum()), "mad": int((valid.COD_CULTIVO == MAD).sum())}
    require(inventory == dict(total=745, valid=38, invalid=707, rice=31, mad=7), "B3_SUPPORT_IDENTITY")
    d = d[d.OUTCOME_VALID_FLAG == "TRUE"].rename(columns={"CROP_CODE": "COD_CULTIVO", "CAMPAIGN": "CAMPAIGN_ID"})
    intersection = valid.merge(d, on=list(KEY), how="inner", validate="one_to_one").sort_values(list(KEY))
    support, keys = [], {}
    for code, name in ((RICE, "RICE"), (MAD, "MAD"), (PERENNIALS[0], "MANGO"), (PERENNIALS[1], "LEMON"), (PERENNIALS[2], "BANANA")):
        part = intersection[intersection.COD_CULTIVO == code]
        keys[code] = part[list(KEY)].values.tolist()
        status = "ESTIMABLE_WITH_SEVERE_SUPPORT_LIMITATION" if code == RICE else MAD_STATUS if code == MAD else "NOT_APPLICABLE"
        support.append({"CROP": name, "CROP_CODE": code,
                        "B3_VALID_ROWS": int((valid.COD_CULTIVO == code).sum()) if code not in PERENNIALS else None,
                        "INTERSECTION_N": len(part) if code not in PERENNIALS else None,
                        "DISTRICTS": int(part.UBIGEO.nunique()) if code not in PERENNIALS else None,
                        "PERIODS": int(part.CAMPAIGN_ID.nunique()) if code not in PERENNIALS else None,
                        "STATUS": status, "REAL_ESTIMATION_EXECUTED": False})
    rice = support[0]
    require((rice["INTERSECTION_N"], rice["DISTRICTS"], rice["PERIODS"]) == (31, 12, 7), "ER2_R6P_HOLD_RICE_SUPPORT_IDENTITY_MISMATCH")
    require(support[1]["INTERSECTION_N"] == 7, "MAD_INTERSECTION_IDENTITY")
    mapping = {"b3_key": list(KEY), "d0_key": ["CROP_CODE", "UBIGEO", "CAMPAIGN"],
               "d0_to_b3_key": {"CROP_CODE": "COD_CULTIVO", "UBIGEO": "UBIGEO", "CAMPAIGN": "CAMPAIGN_ID"},
               "b3_validity": "CAMPAIGN_WEIGHTED_EXPOSURE_VALID", "b3_validity_required": True,
               "b3_failure_reason_required": "NONE", "d0_validity": "OUTCOME_VALID_FLAG", "d0_validity_required": "TRUE",
               "future_y": Y, "future_y_estimator_argument": "response", "future_x": list(X),
               "future_x_mapping": {x: x for x in X}, "future_period": "CAMPAIGN_ID",
               "b3_schema": [{"name": f.name, "type": str(f.type), "nullable": f.nullable} for f in schema],
               "d0_schema": d0_schema, "b3_projected_columns": list(B3_META), "d0_projected_columns": list(D0_META)}
    return {"inventory": inventory, "support": support, "intersection_keys": keys,
            "intersection_keys_sha256": sha(payload(keys)), "mapping": mapping}


def estimator_identity():
    raw = frozen_bytes(ESTIMATOR)
    source = raw.decode()
    tree = ast.parse(source)
    identities = {}
    for name in ("fit_two_way_fe_cr2", "_aht_htz", "fe_matrix", "absorb_fixed_effects"):
        node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
        text = "\n".join(source.splitlines()[node.lineno - 1:node.end_lineno]) + "\n"
        require(inspect.getsource(getattr(ed1, name)) == text, "LOADED_ESTIMATOR_API_IDENTITY: " + name)
        identities[name] = {"source_sha256": sha(text.encode()), "signature": str(inspect.signature(getattr(ed1, name)))}
    return {"scientific_sha256": sha(raw), "byte_source": "RAW_GIT_OBJECT", "functions": identities, "mathematical_alteration": False}


def synthetic_plan():
    return {"gate": GATE, "seed": 20260906, "rng": "NUMPY_GENERATOR_PCG64", "tolerance": TOL,
            "domain": "SYNTHETIC_ONLY_NO_REAL_VALUES", "n": 31, "districts": 12, "campaigns": 7,
            "regressors": list(X), "model": MODEL,
            "graph": "FOR_DISTRICT_i_0_TO_11_USE_CAMPAIGNS_i_MOD_7_AND_i_PLUS_1_MOD_7_THEN_FOR_i_0_TO_6_ADD_i_PLUS_3_MOD_7",
            "row_order": "SORTED_DISTRICT_CAMPAIGN", "x": "PCG64_STANDARD_NORMAL_31_BY_3",
            "y": "X_DOT_[0.4,-0.3,0.2]_PLUS_0.1_DISTRICT_INDEX_MINUS_0.2_CAMPAIGN_INDEX_PLUS_PCG64_NORMAL_NOISE",
            "coefficient_reference": "INDEPENDENT_NUMPY_FULL_DUMMY_LEAST_SQUARES",
            "mapping_reference": "DIRECT_FROZEN_ARRAY_POSITIONS_AND_AHT_KEYS_PLUS_DISTINCT_SENTINEL_INJECTION",
            "admissible_status": ADMISSIBLE, "gates": list(GATES), "fail_closed_cases": CASES,
            "extra_checks": ["NONFINITE_BETA", "MALFORMED_MAPPING", "MULTIPLE_FAILED_GATES", "NO_PARTIAL_PROMOTION", "SYNTHETIC_NAMESPACE", "NO_ESTIMATOR_RETRY"],
            "real_r6_execution_authorized": False}


def write_plan(root):
    path = Path(root) / PLAN
    data = payload(synthetic_plan())
    if path.exists():
        require(path.read_bytes() == data, "SYNTHETIC_PLAN_CHANGED")
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    return sha(data)


def require_plan(root):
    data = (Path(root) / PLAN).read_bytes()
    require(data == payload(synthetic_plan()), "PRETEST_SYNTHETIC_PLAN_IDENTITY")
    return sha(data)


def synthetic_fixture(plan_root=ROOT):
    require_plan(plan_root)
    pairs = [(i, j) for i in range(12) for j in (i % 7, (i + 1) % 7)]
    pairs += [(i, (i + 3) % 7) for i in range(7)]
    pairs.sort()
    rng = np.random.Generator(np.random.PCG64(20260906))
    x = rng.normal(size=(31, 3))
    y = x @ np.array([0.4, -0.3, 0.2]) + np.array([0.1 * i - 0.2 * j for i, j in pairs]) + rng.normal(size=31)
    frame = pd.DataFrame(x, columns=X)
    frame["UBIGEO"] = [f"SYN_D{i:02d}" for i, _ in pairs]
    frame["CAMPAIGN_ID"] = [f"SYN_C{j:02d}" for _, j in pairs]
    frame["COD_CULTIVO"] = RICE
    frame["CAMPAIGN_WEIGHTED_EXPOSURE_VALID"] = True
    frame["FAILURE_REASON"] = "NONE"
    frame["OUTCOME_VALID_FLAG"] = "TRUE"
    frame["WINDOW_ID"] = "RICE_FLOWERING_95_110_DAS"
    frame[Y] = y
    return frame


def key_set(frame):
    return set(frame[list(KEY)].itertuples(index=False, name=None))


def evaluate_frame(frame, exact_keys, crop=RICE, model=None):
    """Validate structure before invoking any estimator; never select on results."""
    model = MODEL if model is None else model
    failed = []
    if crop == MAD:
        return {"status": MAD_STATUS, "failed_gates": ["MAD_ESTIMATION_PROHIBITED"], "support": {}, "coefficients": [], "joint": None}
    if crop in PERENNIALS:
        return {"status": "NOT_APPLICABLE", "failed_gates": ["PERENNIAL_ESTIMATION_PROHIBITED"], "support": {}, "coefficients": [], "joint": None}
    if crop != RICE or model != MODEL:
        failed.append("FROZEN_MODEL")
    required = {*KEY, *X, Y, "CAMPAIGN_WEIGHTED_EXPOSURE_VALID", "FAILURE_REASON", "OUTCOME_VALID_FLAG", "WINDOW_ID"}
    if not required <= set(frame.columns):
        return rejected([*failed, "REQUIRED_COLUMNS"], {})
    support = {"n": len(frame), "districts": int(frame.UBIGEO.nunique()), "periods": int(frame.CAMPAIGN_ID.nunique())}
    for name, actual, expected in zip(GATES[:3], support.values(), (31, 12, 7)):
        if actual != expected:
            failed.append(name)
    if frame.duplicated(list(KEY)).any():
        failed.append("UNIQUE_KEYS")
    if key_set(frame) != set(exact_keys):
        failed.append("EXACT_INTERSECTION")
    if not (frame.COD_CULTIVO == RICE).all():
        failed.append("RICE_ONLY")
    if not ((frame.CAMPAIGN_WEIGHTED_EXPOSURE_VALID == True) & (frame.FAILURE_REASON == "NONE")).all():
        failed.append("VALID_B3_ONLY")
    if not (frame.OUTCOME_VALID_FLAG == "TRUE").all():
        failed.append("VALID_D0_ONLY")
    if not (frame.WINDOW_ID == "RICE_FLOWERING_95_110_DAS").all():
        failed.append("FROZEN_WINDOW")
    if failed:
        return rejected(failed, support)
    if not np.isfinite(frame[[*X, Y]].to_numpy(dtype=float)).all():
        return rejected(["FINITE_MODEL_VALUES"], support)
    fe = ed1.fe_matrix(frame, "CAMPAIGN_ID")
    x = frame[list(X)].to_numpy(dtype=float)
    within = ed1.absorb_fixed_effects(x, fe)
    design = np.column_stack([fe, x])
    support.update(within_rank=int(np.linalg.matrix_rank(within)), design_rank=int(np.linalg.matrix_rank(design)), design_columns=design.shape[1])
    if support["design_rank"] != support["design_columns"]:
        failed.append("FULL_DESIGN_RANK")
    if support["within_rank"] != 3:
        failed.append("WITHIN_RANK_3")
    return rejected(failed, support) if failed else {"status": "STRUCTURALLY_ADMISSIBLE", "failed_gates": [], "support": support}


def rejected(failed, support):
    return {"status": INADMISSIBLE, "failed_gates": failed, "support": support,
            "coefficients": [], "joint": None, "terminal": "R6_COMPLETE_WITH_DECLARED_NONADMISSIBILITY"}


def extract_inference(fit, support):
    failed = []
    try:
        beta = np.asarray(fit["beta"], dtype=float)
        cov = np.asarray(fit["climate_covariance"], dtype=float)
        dfs = np.asarray(fit["satterthwaite_df"], dtype=float)
        require(beta.shape == (3,) and cov.shape == (3, 3) and dfs.shape == (3,), "NAMED_OUTPUT_SHAPES")
        joint = {name: float(fit["aht"][source]) for name, source in AHT_MAPPING.items()}
        adjustments = fit["adjustments"]
        indices = fit["cluster_indices"]
        adjustment_ok = len(adjustments) == len(indices) == 12 and fit["cr2_adjustment_singularities"] == 0
        for a, ix in zip(adjustments, indices):
            a = np.asarray(a, dtype=float)
            valid = a.shape == (len(ix), len(ix)) and np.isfinite(a).all()
            if valid:
                scale = TOL * max(1.0, np.linalg.norm(a, ord=2))
                eigenvalues = np.linalg.eigvalsh(a)
                valid = np.allclose(a, a.T, atol=TOL, rtol=0) and eigenvalues.min() >= -scale and int((eigenvalues > scale).sum()) == max(len(ix) - 1, 0)
            adjustment_ok = adjustment_ok and valid
        if not adjustment_ok:
            failed.append("CR2_ADJUSTMENTS")
        with np.errstate(invalid="ignore", divide="ignore"):
            se = np.sqrt(np.diag(cov))
            t = beta / se
            p = 2 * stats.t.sf(np.abs(t), dfs)
            critical = stats.t.ppf(0.975, dfs)
            lower, upper = beta - critical * se, beta + critical * se
        if not (np.isfinite(se).all() and (se > 0).all() and np.isfinite(cov).all()):
            failed.append("POSITIVE_FINITE_SE")
        if not (np.isfinite(dfs).all() and (dfs > 0).all()):
            failed.append("POSITIVE_FINITE_DF")
        if not np.isfinite(np.concatenate([beta, t, p, lower, upper])).all():
            failed.append("FINITE_COEFFICIENT_STATISTICS")
        aht_ok = all(np.isfinite(v) for v in joint.values())
        aht_ok = aht_ok and joint["NUMERATOR_DF"] == 3 and joint["DENOMINATOR_DF"] > 0 and 0 < joint["HTZ_DELTA"] <= 1
        aht_ok = aht_ok and joint["JOINT_F"] >= 0 and joint["JOINT_WALD_CHI_SQUARE"] >= 0 and 0 <= joint["RAW_JOINT_P"] <= 1
        if not aht_ok:
            failed.append("VALID_FINITE_AHT")
    except (KeyError, TypeError, ValueError, RuntimeError, np.linalg.LinAlgError) as error:
        return rejected([*failed, "FROZEN_OUTPUT_MAPPING:" + type(error).__name__], support)
    if failed:
        return rejected(failed, support)
    rows = []
    for i, name in enumerate(X):
        rows.append(dict(zip(COEFFICIENT_FIELDS, ["RICE", RICE, name, None, float(beta[i]), float(se[i]), float(dfs[i]), float(t[i]), float(p[i]), float(lower[i]), float(upper[i]), int(np.sign(beta[i])), ADMISSIBLE])))
    joint.update(CROP="RICE", CROP_CODE=RICE, ADMISSIBILITY_STATUS=ADMISSIBLE)
    return {"status": ADMISSIBLE, "failed_gates": [], "support": support, "coefficients": rows, "joint": joint,
            "terminal": "R6_COMPLETE_WITH_RICE_ADMISSIBLE_AND_MAD_NONESTIMABLE"}


def synthetic_adapter(frame, exact_keys, crop=RICE, model=None, estimator=None):
    # There is deliberately no real-data execution entry point in R6P.
    require(frame.UBIGEO.astype(str).str.startswith("SYN_D").all() and frame.CAMPAIGN_ID.astype(str).str.startswith("SYN_C").all(), "REAL_R6_EXECUTION_NOT_AUTHORIZED")
    checked = evaluate_frame(frame, exact_keys, crop, model)
    if checked["status"] != "STRUCTURALLY_ADMISSIBLE":
        return checked
    estimator = ed1.fit_two_way_fe_cr2 if estimator is None else estimator
    try:
        fit = estimator(frame, list(X), "CAMPAIGN_ID", frame[Y].to_numpy(dtype=float))
    except (RuntimeError, ValueError, np.linalg.LinAlgError, FloatingPointError) as error:
        return rejected(["FROZEN_ESTIMATOR_EXCEPTION:" + type(error).__name__ + ":" + str(error)], checked["support"])
    return extract_inference(fit, checked["support"])


def independent_dummy_beta(frame):
    districts = sorted(set(frame.UBIGEO))
    campaigns = sorted(set(frame.CAMPAIGN_ID))
    columns = [np.ones(len(frame))]
    columns += [(frame.UBIGEO == d).to_numpy(dtype=float) for d in districts[1:]]
    columns += [(frame.CAMPAIGN_ID == c).to_numpy(dtype=float) for c in campaigns[1:]]
    columns += [frame[v].to_numpy(dtype=float) for v in X]
    return np.linalg.lstsq(np.column_stack(columns), frame[Y].to_numpy(), rcond=None)[0][-3:]


def case_result(case, frame, fit):
    f, changed = frame.copy(deep=True), copy.deepcopy(fit)
    exact, crop, model = key_set(frame), RICE, copy.deepcopy(MODEL)
    if case == "A":
        f = f.iloc[:-1].copy()
    elif case == "B":
        f.loc[f.UBIGEO == "SYN_D11", "UBIGEO"] = "SYN_D10"
    elif case == "C":
        f.loc[f.CAMPAIGN_ID == "SYN_C06", "CAMPAIGN_ID"] = "SYN_C05"
    elif case == "D":
        f[X[2]] = f[X[1]]
    elif case == "E":
        pairs = [(d, (d + j) % 3) for d in range(6) for j in (0, 1)] + [(d, (d + 2) % 3) for d in range(4)]
        pairs += [(d, 3 + (d + j) % 4) for d in range(6, 12) for j in (0, 1)] + [(d, 3 + (d + 2) % 4) for d in range(6, 9)]
        f = frame.copy()
        f["UBIGEO"] = [f"SYN_D{d:02d}" for d, _ in pairs]
        f["CAMPAIGN_ID"] = [f"SYN_C{c:02d}" for _, c in pairs]
        exact = key_set(f)
    elif case == "F":
        changed["adjustments"][0][0, 0] = np.nan
    elif case == "G":
        changed["climate_covariance"][0, 0] = 0
    elif case == "H":
        changed["climate_covariance"][0, 0] = np.inf
    elif case == "I":
        changed["satterthwaite_df"][0] = np.nan
    elif case == "J":
        changed["aht"]["denominator_df"] = np.nan
    elif case == "K":
        f = f.drop(columns=X[0])
    elif case == "L":
        f.iloc[-1] = f.iloc[0]
    elif case == "M":
        f.loc[0, "CAMPAIGN_WEIGHTED_EXPOSURE_VALID"] = False
    elif case == "N":
        exact.remove(next(iter(sorted(exact))))
    elif case == "O":
        crop = MAD
    elif case == "P":
        crop = PERENNIALS[0]
    elif case == "Q":
        model["campaign_fe"] = "REMOVED"
    elif case == "R":
        model["estimator"] = "SUBSTITUTE"
    else:
        raise ValueError("Unknown synthetic case")
    return synthetic_adapter(f, exact, crop, model, estimator=lambda *args: changed)


def synthetic_validation(plan_root):
    require_plan(plan_root)
    frame = synthetic_fixture(plan_root)
    fit = ed1.fit_two_way_fe_cr2(frame, list(X), "CAMPAIGN_ID", frame[Y].to_numpy())
    result = synthetic_adapter(frame, key_set(frame))
    require(result["status"] == ADMISSIBLE, "SYNTHETIC_ADMISSIBLE_CASE: " + str(result["failed_gates"]))
    difference = float(np.max(np.abs(np.array([r["R6_B3_BETA"] for r in result["coefficients"]]) - independent_dummy_beta(frame))))
    require(difference <= TOL, "INDEPENDENT_DUMMY_REFERENCE")
    rows = [{"CHECK_ID": "ADMISSIBLE_CORE", "STATUS": "PASS", "EXPECTED_GATE": "ALL_TEN", "OBSERVED_STATUS": result["status"], "MAX_ABS_DIFFERENCE": None},
            {"CHECK_ID": "FULL_DUMMY_REFERENCE", "STATUS": "PASS", "EXPECTED_GATE": "MAX_ABS_DIFF_LE_1E_MINUS_10", "OBSERVED_STATUS": "VALIDATED", "MAX_ABS_DIFFERENCE": difference}]
    for case, gate in CASES.items():
        rejected_case = case_result(case, frame, fit)
        require(gate in rejected_case["failed_gates"] and not rejected_case["coefficients"] and rejected_case["joint"] is None, "FAIL_CLOSED_CASE_" + case)
        rows.append({"CHECK_ID": "FAIL_CLOSED_" + case, "STATUS": "PASS", "EXPECTED_GATE": gate, "OBSERVED_STATUS": rejected_case["status"], "MAX_ABS_DIFFERENCE": None})
    for i, row in enumerate(result["coefficients"]):
        require(row["VARIABLE"] == X[i] and row["CR2_SE"] == float(np.sqrt(fit["climate_covariance"][i, i])) and row["SATTERTHWAITE_DF"] == float(fit["satterthwaite_df"][i]), "FROZEN_POSITION_MAPPING")
    for target, source in AHT_MAPPING.items():
        require(result["joint"][target] == fit["aht"][source], "FROZEN_AHT_MAPPING")
    sentinel = copy.deepcopy(fit)
    sentinel.update(beta=np.array([11., 22., 33.]), climate_covariance=np.diag([4., 9., 25.]), satterthwaite_df=np.array([5., 7., 9.]))
    sentinel["aht"] = dict(wald_chi_square=8., f_statistic=2., numerator_df=3., denominator_df=6., p_value=.123, delta=.75)
    mapped = extract_inference(sentinel, result["support"])
    require(mapped["status"] == ADMISSIBLE, "SENTINEL_ADMISSIBILITY")
    require([r["CR2_SE"] for r in mapped["coefficients"]] == [2., 3., 5.], "SENTINEL_SE_MAPPING")
    require([r["SATTERTHWAITE_DF"] for r in mapped["coefficients"]] == [5., 7., 9.], "SENTINEL_DF_MAPPING")
    for target, source in AHT_MAPPING.items():
        require(mapped["joint"][target] == sentinel["aht"][source], "SENTINEL_AHT_MAPPING")
    for name in ("CR2_SE_MAPPING", "SATTERTHWAITE_DF_MAPPING", "AHT_MAPPING", "DISTINCT_SENTINEL_MAPPING"):
        rows.append({"CHECK_ID": name, "STATUS": "PASS", "EXPECTED_GATE": "EXACT_NAMED_MAPPING", "OBSERVED_STATUS": "VALIDATED", "MAX_ABS_DIFFERENCE": 0.0})
    return rows, difference, result["support"]


def branch_audit(source=None):
    source = (ROOT / SCRIPT).read_text(encoding="utf-8") if source is None else source
    tree = ast.parse(source)
    findings, inspected = [], 0
    names = {"evaluate_frame", "extract_inference", "synthetic_adapter", "metadata_only"}
    forbidden = ("2017", "2023", "el nino", "el ni", "er1_beta", "r3_result", "r4_result", "r5_result", "significance", "beta_sign", "beta[", "raw_p", "robustness_score")
    for function in tree.body:
        if isinstance(function, ast.FunctionDef) and function.name in names:
            for node in ast.walk(function):
                if isinstance(node, (ast.If, ast.IfExp, ast.While, ast.Assert, ast.comprehension)):
                    expressions = node.ifs if isinstance(node, ast.comprehension) else [node.test]
                    for expression in expressions:
                        inspected += 1
                        condition = ast.unparse(expression).lower()
                        if any(word in condition for word in forbidden):
                            findings.append({"function": function.name, "condition": condition})
    require(not findings, "RESULT_SPECIFIC_R6_BRANCHES")
    return {"result_specific_r6_branches": len(findings), "conditions_inspected": inspected,
            "scope": sorted(names), "source_sha256": sha(source.encode()),
            "policy": "ONLY_CROP_SCOPE_METADATA_STRUCTURE_FINITE_RANGE_AND_ADMISSIBILITY_BRANCHES",
            "no_significance_threshold_or_result_driven_selection": True}


def future_schema(protocol):
    dimensions = []
    for crop in protocol["crop_model_contracts"]:
        code = crop["CROP_CODE"]
        status = "R6_RICE_RESULT_WHERE_ADMISSIBLE" if code == RICE else MAD_STATUS if code == MAD else "NOT_APPLICABLE"
        for variable in crop["PRIMARY_REGRESSORS"].split("|"):
            dimensions.append({"CROP": crop["CROP"], "CROP_CODE": code, "VARIABLE": variable, "R6_STATUS": status})
    require(len(dimensions) == 21, "CONCORDANCE_DIMENSIONS")
    return {"coefficient_fields": list(COEFFICIENT_FIELDS), "joint_fields": ["CROP", "CROP_CODE", *AHT_MAPPING, "ADMISSIBILITY_STATUS"],
            "status_fields": ["CROP", "CROP_CODE", "STATUS", "FAILED_GATES", "N", "DISTRICTS", "PERIODS"],
            "concordance": dimensions, "inventory": {"concordance_rows": 21, "rice_coefficients_if_admissible": 3, "rice_aht_if_admissible": 1, "crop_status_rows": 5},
            "missing_result_encoding": "JSON_NULL_OR_EMPTY_CSV_FIELD_WITH_EXPLICIT_STATUS_NEVER_ZERO_OR_FALSE",
            "nonadmissible_rice": "RETAIN_THREE_CONCORDANCE_DIMENSIONS_WITH_NULL_R6_NUMBERS_AND_EXACT_FAILED_GATES_NO_JOINT_PROMOTION",
            "er1_beta_reference": "FUTURE_READ_ONLY_EXACT_ER1_REFERENCE_NOT_READ_DURING_R6P",
            "holm": "NOT_AUTHORIZED", "global_five_crop_fwer": "NOT_CLAIMED", "adjusted_ci": "NOT_CONSTRUCTED_NOT_CLAIMED",
            "nonapplicability_is_failed_robustness": False, "robustness_vote_fields": []}


def csv_bytes(rows):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def build(output_root):
    output_root = Path(output_root)
    parent = predecessor()
    protocol, tier, hierarchy = contracts()
    meta = metadata_only()
    estimator = estimator_identity()
    plan_sha = write_plan(output_root)
    validations, difference, synthetic_support = synthetic_validation(output_root)
    branch = branch_audit()
    schema = future_schema(protocol)
    support_data, validation_data = csv_bytes(meta["support"]), csv_bytes(validations)
    temporal = {f"{phase}_RESULTS_KNOWN": True for phase in ("PRIMARY", "R1", "R2", "R3", "R4", "R5")}
    temporal.update(R6_RESULTS_KNOWN=False, R6_HIERARCHY_TIMING="PRE_OUTCOME_FROZEN_IN_ED1", R6_OPERATIONALIZATION_TIMING="POST_PRIMARY_RESULTS_PRE_ROBUSTNESS_RESULTS")
    firewall = {name: False for name in ("REAL_R6_OUTCOME_NUMERICAL_VALUES_READ", "REAL_R6_CLIMATE_NUMERICAL_VALUES_READ", "REAL_R6_ESTIMATION_EXECUTED", "REAL_R6_COEFFICIENTS_KNOWN", "REAL_R6_INFERENCE_KNOWN", "R6_EXECUTED")}
    firewall.update(R6P_FREEZE_AUTHORIZATION_STATUS="NOT_AUTHORIZED", REAL_R6_EXECUTION_AUTHORIZATION_STATUS="NOT_AUTHORIZED", DOWNSTREAM="ENSO_SCENARIOS_GVP_VAR_CVAR_A1_A2_OPTIMIZATION_NOT_EXECUTED")
    report = "\n".join([
        "# ER2 R6P B3 Strict Exposure Preflight", "", "Status: PASS_CANDIDATE. No real R6 numerical values or model were accessed.",
        "", "## Severe Support Limitation", "", "SEVERE_SUPPORT_LIMITATION: Rice contracts from ER1 N=281 to strict B3 N=31, 12 districts, seven campaigns.",
        f"Descriptive support ratio: {31 / 281:.15f}. This ratio is not a robustness score.",
        "B3 metadata: 745 total, 38 valid, 707 invalid; valid Rice=31 and MAD=7.",
        "Rice admissibility is conditional on future numerical checks; metadata support does not certify real estimability.",
        "MAD: NOT_ESTIMABLE_UNDER_PRIMARY_DESIGN; seven intersection rows. No substitute model.",
        "Mango, Lemon and Banana: NOT_APPLICABLE. No zero results and no failed robustness votes.",
        "", "## Frozen Architecture", "", f"R5 predecessor: `{PARENT}`.", f"R6 tier identity: `{TIER_SHA}`.",
        "Exact valid D0 x B3 key intersection; no imputation, interpolation, relaxed validity, expansion or result-driven deletion.",
        "Yield level tm/ha, exact ED1 windows, three physical-anomaly regressors, district and campaign FE, linear additive, unweighted; no trends.",
        "EMPIRICAL_ASSOCIATION_CLIMATE_RESPONSE_ONLY; exposure-definition and attribution-quality sensitivity, not causal or true-exposure evidence.",
        "PRIMARY_REPLACEMENT=PROHIBITED. DISAGREEMENT_PROVES_CORRECT_EXPOSURE=FALSE.",
        "", "## Inference and Terminal Rule", "", ADMISSIBILITY, TERMINAL,
        "All ten gates must pass. On any failed gate retain diagnostics and report R6_RICE_NOT_INFERENTIALLY_ADMISSIBLE; no partial inference promotion.",
        "R6_COMPLETE_WITH_DECLARED_NONADMISSIBILITY is a legitimate terminal status, not a null result.",
        "Future admissible Rice only: raw CR2/Satterthwaite coefficients, unadjusted 95% intervals and one frozen AHT/HTZ joint test.",
        tier["multiplicity"], "No Holm, WCR, Conley, adjusted intervals, new confirmatory FWER, crop ranking or robustness vote counts.",
        "Future concordance preserves all 21 dimensions with explicit MAD/perennial statuses and null absent numerical results.",
        "", "## Metadata Mapping", "", f"B3 keys: {', '.join(KEY)}; validity: CAMPAIGN_WEIGHTED_EXPOSURE_VALID=True, FAILURE_REASON=NONE.",
        "D0 keys: CROP_CODE, UBIGEO, CAMPAIGN; validity: OUTCOME_VALID_FLAG=TRUE.",
        f"Future Y: {Y}; future X: {', '.join(X)}. Names/schema inspected; real values not loaded.",
        "", "## Synthetic Certification", "", f"Pre-test plan SHA256: `{plan_sha}`.",
        f"Independent full-dummy coefficient maximum absolute difference: {difference:.17g}; tolerance {TOL}.",
        "Synthetic 31/12/7 core passes all ten gates. A-R fail-closed cases and independent named-output mapping pass.",
        "Frozen ED1 fit_two_way_fe_cr2 and AHT/HTZ reused without mathematical alteration; source identities are in the lock.",
        f"RESULT_SPECIFIC_R6_BRANCHES={branch['result_specific_r6_branches']}.",
        "", "## Governance", "", "Primary and R1-R5 known; R6 unknown. Hierarchy PRE_OUTCOME_FROZEN_IN_ED1; operationalization POST_PRIMARY_RESULTS_PRE_ROBUSTNESS_RESULTS.",
        "Dedicated/full-suite and two-build execution evidence is certified externally to avoid circular generated-artifact hashes.",
        "No real R6, downstream execution, staging, commit, push or tag authorized.",
        VERDICT, "RETURN_TO_SCIENTIFIC_DIRECTOR_FOR_R6P_FREEZE_DECISION_IF_PASS", "",
    ]).encode("utf-8")
    lock = {"project": PROJECT, "gate": GATE, "status": "PASS_CANDIDATE", "predecessor": parent,
            "frozen_input_sha256": FROZEN_SHA, "r6_tier_contract_sha256": TIER_SHA, "tier": tier, "hierarchy": hierarchy,
            "temporal": temporal, "claim_ceiling": tier["claim_ceiling"], "sample_rule": SAMPLE_RULE,
            "valid_b3_support_used_for_scope_decision_only": True, "metadata": meta, "model": MODEL,
            "rice_support": {"n": 31, "districts": 12, "periods": 7, "coefficient_count": 3, "required_within_rank": 3},
            "support_comparison": {"er1_n": 281, "r6_n": 31, "ratio_descriptive_only": 31 / 281, "qualification": "SEVERE_SUPPORT_LIMITATION"},
            "mad": tier["mad"], "perennials": "NOT_APPLICABLE", "future_result_schema": schema,
            "admissibility_predicate": ADMISSIBILITY, "all_required_gates": list(GATES), "terminal_rule": TERMINAL,
            "no_partial_promotion": True, "primary_replacement": "PROHIBITED", "may_weaken_fe": False,
            "disagreement_proves_correct_exposure": False, "estimator_api": estimator,
            "synthetic_plan_sha256": plan_sha, "synthetic_validations": validations, "synthetic_support": synthetic_support,
            "synthetic_reference_max_abs_diff": difference, "result_specific_branch_audit": branch, "firewall": firewall,
            "artifact_sha256_excluding_self": {REPORT: sha(report), SUPPORT: sha(support_data), VALIDATION: sha(validation_data), PLAN: plan_sha,
                                               SCRIPT: sha((ROOT / SCRIPT).read_bytes()), TEST: sha((ROOT / TEST).read_bytes())}}
    products = {REPORT: report, SUPPORT: support_data, VALIDATION: validation_data, PLAN: payload(synthetic_plan()), LOCK: payload(lock)}
    for path, data in products.items():
        require(b"\r" not in data and not data.startswith(b"\xef\xbb\xbf") and data.endswith(b"\n") and not data.endswith(b"\n\n"), "CANONICAL_BYTES")
        target = output_root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    return {path: sha(data) for path, data in products.items()}


def main():
    parser = argparse.ArgumentParser(description="Metadata-only R6P and synthetic certification; no real R6 entry point")
    parser.add_argument("--output-root", type=Path, default=ROOT)
    parser.add_argument("--lock-plan-only", action="store_true")
    args = parser.parse_args()
    result = {PLAN: write_plan(args.output_root)} if args.lock_plan_only else build(args.output_root)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
