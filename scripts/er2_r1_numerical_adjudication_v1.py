from __future__ import annotations

import argparse
import ctypes
import itertools
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import scipy
from scipy import linalg, stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import er2_r1_level_robustness_v1 as legacy

ed1, er1, er2p = legacy.ed1, legacy.er1, legacy.er2p
ORIGINAL_HASHES = {
    "outputs/econometrics/ER2_R1_LEVEL_RESULTS.csv": "53d705be497d66ea7a8aef743da4f3a524d1a53a7cffc11df3a1fed708c03fad",
    "outputs/econometrics/ER2_R1_LEVEL_JOINT_TESTS.csv": "46d05494e1f3bfda255f9030f4f5c0128eac98c57aeab193b84c4ffbe81bdb59",
    "outputs/econometrics/ER2_R1_PERENNIAL_EQUIVALENCE.csv": "a3a52850763a7bd1f161469718af9d743e145138cec833a0fc18b1d112ed44a3",
    "outputs/econometrics/ER2_R1_REPORT.md": "070dea4c92401e27dd6abb489c15030672a4e1cfa4e07509be13316c40f3d307",
    "outputs/econometrics/ER2_R1_RESULTS_LOCK.json": "c7ae05b96b4155df5fe1d74484784c02c7fe32084b443aa7a02107b37a5c1963",
    "scripts/er2_r1_level_robustness_v1.py": "542cfc1ef7e4f094613d286f8435260dab8232e64c4d5ee9d7ae48323ce0e0c2",
    "tests/test_er2_r1_level_robustness_v1.py": "e2f81b5e190613dd4dee889c86c8c00d03f918cad41a6c36cb243c703e503dbd",
}
FIRST_LOCK_SHA = ORIGINAL_HASHES[legacy.LOCK_REL.as_posix()]
JSON_REL = Path("outputs/econometrics/ER2_R1_NUMERICAL_ADJUDICATION.json")
REPORT_REL = Path("outputs/econometrics/ER2_R1_NUMERICAL_ADJUDICATION_REPORT.md")
SCRIPT_REL = Path("scripts/er2_r1_numerical_adjudication_v1.py")
TEST_REL = Path("tests/test_er2_r1_numerical_adjudication_v1.py")
CERTIFIED_REL = Path("outputs/econometrics/ER2_R1_RESULTS_LOCK_CERTIFIED.json")
CANDIDATE_RELS = (JSON_REL, REPORT_REL, SCRIPT_REL, TEST_REL, CERTIFIED_REL)
PASS = "ER2_R1A_PASS_NUMERICAL_ROUNDOFF_ADJUDICATED_READY_FOR_R1_FREEZE_DECISION"
BLOCKED_NUMERICAL = "ER2_R1A_BLOCKED_THIRD_PATH_DISAGREEMENT"
BLOCKED_ALGEBRA = "ER2_R1A_BLOCKED_PERENNIAL_ALGEBRAIC_EQUIVALENCE_NOT_CONFIRMED"
THIRD_PATH = "COLUMN_L2_SCALED_PIVOTED_QR_DGEQP3_TRIANGULAR_SOLVES_DIRECT_CR2_CHOLESKY_HTZ"
EPS = float(np.finfo(np.float64).eps)
TINY = float(np.finfo(np.float64).tiny)
BETA_RELATIVE_TOLERANCE = 1e-10
ADJUDICATION_RELATIVE_TOLERANCE = 1e-6
POLICY = {
    "beta_relative_l2": BETA_RELATIVE_TOLERANCE,
    "covariance_relative_frobenius": ADJUDICATION_RELATIVE_TOLERANCE,
    "df_relative_l2_and_each_coefficient": ADJUDICATION_RELATIVE_TOLERANCE,
    "aht_scalar_relative": ADJUDICATION_RELATIVE_TOLERANCE,
    "tiny": TINY, "qr_rank_rcond": 1e-12,
    "source_representation_bound": "128*FLOAT64_EPS*MAX_ABS_PAIRED_SOURCE_VALUE_OR_1_PER_COLUMN",
    "coefficient_rounding": "12_SIGNIFICANT_DIGITS_FIXED_BEFORE_THIRD_PATH",
    "df_f_p_rounding": "6_DECIMAL_PLACES_DESCRIPTIVE_NOT_A_PASS_GATE",
    "perennial_drift_rule": "STABLE_QR_LEVEL_VS_ANOMALY_MUST_PASS_DIRECTOR_ENVELOPE; LEGACY_DRIFT_MUST_BE_CONDITIONING_CONSISTENT_WITH_NO_RANK_OR_SINGULARITY_CHANGE",
    "conditioning_consistency_budget": "ETA/(1-ETA); ETA=COND2(Z_TRANSPOSE_Z)*GAMMA_N; GAMMA_N=N*EPS/(1-N*EPS); REQUIRE_ETA_LT_1",
    "conditioning_budget_interpretation": "NORMWISE_ERROR_AMPLIFICATION_DIAGNOSTIC_NOT_A_RIGOROUS_END_TO_END_CR2_FORWARD_ERROR_BOUND",
    "no_p_value_selection": True, "strict_legacy_rule": "ABSOLUTE_1E-8_ALARM_REMAINS_FAIL_PRESERVED",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def verify_originals() -> dict:
    actual = {p: legacy.sha((ROOT / p).read_bytes()) for p in ORIGINAL_HASHES}
    require(actual == ORIGINAL_HASHES, "ER2_R1A_FAIL_ORIGINAL_RESULT_DRIFT")
    require(legacy.VERIFICATION_TOLERANCE == 1e-8, "ER2_R1A_FAIL_ORIGINAL_RESULT_DRIFT: strict rule")
    return actual


def preflight(live_remote: bool = False) -> dict:
    originals = verify_originals()
    inputs = legacy.verify_inputs()
    require(legacy.git("rev-parse", "HEAD") == legacy.ER2P_SHA,
            "ER2_R1A_FAIL_UPSTREAM_IMMUTABILITY: HEAD")
    require(legacy.git("rev-parse", "HEAD^") == er2p.ER1_SHA,
            "ER2_R1A_FAIL_UPSTREAM_IMMUTABILITY: parent")
    for branch, tag, expected in ((legacy.ER2P_BRANCH, legacy.ER2P_TAG, legacy.ER2P_SHA),
                                  (er2p.ER1_BRANCH, er2p.ER1_TAG, er2p.ER1_SHA),
                                  (er2p.ED1_BRANCH, er2p.ED1_TAG, er2p.ED1_SHA)):
        require(legacy.git("rev-parse", branch) == legacy.git("rev-parse", "origin/" + branch)
                == legacy.git("rev-parse", tag + "^{}") == expected,
                "ER2_R1A_FAIL_UPSTREAM_IMMUTABILITY: refs")
    if live_remote:
        refs = dict(line.split()[::-1] for line in legacy.git(
            "ls-remote", "origin", "refs/heads/" + legacy.ER2P_BRANCH,
            "refs/tags/" + legacy.ER2P_TAG + "^{}",
        ).splitlines())
        require(refs == {"refs/heads/" + legacy.ER2P_BRANCH: legacy.ER2P_SHA,
                         "refs/tags/" + legacy.ER2P_TAG + "^{}": legacy.ER2P_SHA},
                "ER2_R1A_FAIL_UPSTREAM_IMMUTABILITY: remote")
    require(not legacy.git("diff", "--name-only") and not legacy.git("diff", "--cached", "--name-only"),
            "ER2_R1A_FAIL_UPSTREAM_IMMUTABILITY: tracked files/index")
    allowed = set(ORIGINAL_HASHES) | {p.as_posix() for p in CANDIDATE_RELS}
    require(set(legacy.git("ls-files", "--others", "--exclude-standard").splitlines()) <= allowed,
            "ER2_R1A_FAIL_UPSTREAM_IMMUTABILITY: unauthorized candidate")
    require(set(er2p.forbidden_result_paths(ROOT)) <= allowed,
            "ER2_R1A_FAIL_UPSTREAM_IMMUTABILITY: unauthorized result")
    return {"status": "PASS", "original_r1_sha256": originals, "upstream_sha256": inputs,
            "er2p_freeze_sha": legacy.ER2P_SHA, "er1_freeze_sha": er2p.ER1_SHA,
            "er1_numerical_results_identity": er2p.NUMERICAL_IDENTITY, "er2p_protocol_sha256": legacy.PROTOCOL_SHA}


def environment_record() -> dict:
    builds = {}
    for name, module in (("numpy", np), ("scipy", scipy)):
        config = module.show_config(mode="dicts")
        builds[name] = {
            "full_build_configuration_sha256": legacy.sha(legacy.json_bytes(config)),
            "blas_lapack": {kind: {k: v for k, v in config["Build Dependencies"][kind].items()
                                    if "directory" not in k} for kind in ("blas", "lapack")},
            "machine_information": config["Machine Information"],
            "compilers": {k: {field: value for field, value in v.items() if "directory" not in field}
                          for k, v in config["Compilers"].items()},
        }
    pools = []
    for name, module in (("numpy", np), ("scipy", scipy)):
        folder = Path(module.__file__).resolve().parent.parent / (name + ".libs")
        for dll in sorted(folder.glob("*openblas*.dll")):
            library = ctypes.CDLL(str(dll))
            record = {"package": name, "library": dll.name, "active_threads": None}
            for symbol in ("scipy_openblas_get_num_threads64_", "scipy_openblas_get_num_threads",
                           "openblas_get_num_threads64_", "openblas_get_num_threads"):
                if hasattr(library, symbol):
                    function = getattr(library, symbol)
                    function.restype, function.argtypes = ctypes.c_int, []
                    record.update(active_threads=int(function()), observation_symbol=symbol)
                    break
            pools.append(record)
    return {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__,
            "cpu_architecture": platform.machine(), "cpu_processor": platform.processor(),
            "floating_type": "IEEE754_BINARY64_NUMPY_FLOAT64", "eps": EPS, "tiny": TINY,
            "build_configurations": builds, "observable_blas_pools": pools,
            "thread_environment": {k: os.environ.get(k) for k in (
                "OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "BLIS_NUM_THREADS",
                "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS", "GOTO_NUM_THREADS")},
            "environment_changed": False, "packages_installed": False,
            "optional_r_reference": "NOT_RUN_RSCRIPT_NOT_ON_PATH" if shutil.which("Rscript") is None else "AVAILABLE_NOT_REQUIRED_NOT_RUN",
            "non_numerical_build_paths": "OMITTED_CONFIGURATION_HASH_PRESERVES_IDENTITY"}


def spectrum(matrix: np.ndarray, rcond: float = 1e-12) -> dict:
    singular = np.linalg.svd(matrix, compute_uv=False)
    cutoff = float(rcond * singular[0])
    retained = singular[singular > cutoff]
    return {"singular_values": singular.tolist(), "largest": float(singular[0]),
            "smallest": float(singular[-1]), "smallest_retained": float(retained[-1]) if len(retained) else None,
            "condition_2": float(singular[0] / singular[-1]) if singular[-1] > 0 else None,
            "rank_at_rcond": int(len(retained)), "default_matrix_rank": int(np.linalg.matrix_rank(matrix)),
            "rcond": rcond, "absolute_cutoff": cutoff}


def adjustment_record(block: np.ndarray, indices: np.ndarray) -> dict:
    eigen = np.linalg.eigvalsh(block)
    tolerance = EPS * len(indices) * max(1., float(np.max(np.abs(eigen)))) * 128.
    kept = eigen[eigen > tolerance]
    rank = int(len(kept))
    return {"cluster_size": len(indices), "eigenvalues": eigen.tolist(), "cutoff": tolerance,
            "retained_rank": rank, "expected_rank": max(len(indices)-1, 0),
            "unexpected_singularity": rank < max(len(indices)-1, 0) or bool(eigen[0] < -tolerance),
            "positive_subspace_condition": float(kept[-1]/kept[0]) if rank else None,
            "adjustment_positive_subspace_condition": float(np.sqrt(kept[-1]/kept[0])) if rank else None}


def ht_z_from_influences(beta: np.ndarray, covariance: np.ndarray, influences: np.ndarray) -> tuple[dict, dict]:
    # Cholesky whitening and cluster-pair traces replace the frozen symmetric-root tensor formulation.
    q = len(beta)
    omega = sum(v @ v.T for v in influences)
    chol = linalg.cholesky(omega, lower=True, check_finite=True)
    white = np.stack([linalg.solve_triangular(chol, v, lower=True) for v in influences])
    terms = []
    for left in white:
        for right in white:
            product = left @ right.T
            terms.append(float(np.trace(product @ product) + np.trace(product)**2))
    nu = float(q*(q+1)/np.sum(terms, dtype=np.float64))
    denominator_df = nu-q+1
    require(denominator_df > 0, "THIRD_PATH_INVALID_AHT_DF")
    wald = float(beta @ linalg.solve(covariance, beta, assume_a="pos"))
    delta = denominator_df/nu
    f_value = delta*wald/q
    return {"numerator_df": float(q), "denominator_df": denominator_df, "f_statistic": f_value,
            "p_value": float(stats.f.sf(f_value, q, denominator_df)), "wald_chi_square": wald, "delta": delta}, {
                "omega": spectrum(omega), "contrast_covariance": spectrum(covariance),
                "whitening": "CHOLESKY_LOWER_TRIANGULAR", "moment_nu": nu}


def qr_full_design(frame: pd.DataFrame, columns: list[str], period: str) -> tuple[np.ndarray, int]:
    fields = [np.ones(len(frame), dtype=np.float64)]
    for key in ("UBIGEO", period):
        values = frame[key].astype(str).to_numpy()
        fields.extend((values == label).astype(np.float64) for label in sorted(set(values))[1:])
    fixed_count = len(fields)
    return np.column_stack([*fields, frame[columns].to_numpy(dtype=np.float64)]), fixed_count


def third_fit(frame: pd.DataFrame, columns: list[str], period: str, y: np.ndarray) -> dict:
    z, offset = qr_full_design(frame, columns, period)
    require(np.isfinite(z).all() and np.isfinite(y).all(), "THIRD_PATH_NONFINITE_INPUT")
    scales = np.linalg.norm(z, axis=0)
    require(bool(np.all(scales > 0)), "THIRD_PATH_ZERO_COLUMN")
    scaled = z/scales
    q_matrix, triangular, pivots = linalg.qr(scaled, mode="economic", pivoting=True, check_finite=True)
    qr_cutoff = 1e-12 * abs(triangular[0, 0])
    rank = int(np.sum(np.abs(np.diag(triangular)) > qr_cutoff))
    require(rank == z.shape[1], "THIRD_PATH_RANK_DISAGREEMENT")
    scaled_inverse = np.empty((z.shape[1], len(frame)), dtype=np.float64)
    scaled_inverse[pivots] = linalg.solve_triangular(triangular, q_matrix.T)
    inverse = scaled_inverse/scales[:, None]
    beta_full = inverse @ y
    residual = y - q_matrix @ (q_matrix.T @ y)
    residual_maker = np.eye(len(frame)) - q_matrix @ q_matrix.T
    residual_maker = (residual_maker+residual_maker.T)/2
    slopes_inverse = inverse[offset:]
    districts = frame["UBIGEO"].astype(str).to_numpy()
    scores, influence_vectors, adjustments = [], [], []
    for district in sorted(set(districts)):
        ix = np.flatnonzero(districts == district)
        block = residual_maker[np.ix_(ix, ix)]
        eigenvalues, vectors = linalg.eigh(block, driver="evr", check_finite=True)
        cutoff = EPS*len(ix)*max(1., float(np.max(np.abs(eigenvalues))))*128.
        keep = eigenvalues > cutoff
        adjustment = (vectors[:, keep]/np.sqrt(eigenvalues[keep])) @ vectors[:, keep].T
        influence = slopes_inverse[:, ix] @ adjustment
        scores.append(influence @ residual[ix])
        influence_vectors.append(influence @ residual_maker[ix, :])
        record = adjustment_record(block, ix)
        record.update(ubigeo=district, actual_retained_rank=int(keep.sum()), actual_eigen_cutoff=cutoff)
        adjustments.append(record)
    covariance = np.asarray(scores).T @ np.asarray(scores)
    influences = np.stack(influence_vectors)
    dfs = []
    for index in range(len(columns)):
        gram = influences[:, index, :] @ influences[:, index, :].T
        dfs.append(float(np.trace(gram)**2/np.sum(gram*gram)))
    aht, aht_condition = ht_z_from_influences(beta_full[offset:], covariance, influences)
    return {"beta": beta_full[offset:], "covariance": covariance, "satterthwaite_df": np.array(dfs),
            "aht": aht, "full_beta": beta_full, "residual": residual, "rank": rank,
            "singularities": sum(r["unexpected_singularity"] for r in adjustments),
            "diagnostics": {"path": THIRD_PATH, "column_scales": scales.tolist(), "pivot_order": pivots.tolist(),
                "full_design": spectrum(z), "scaled_design": spectrum(scaled),
                "qr_diagonal": np.diag(triangular).tolist(), "qr_rank_cutoff": qr_cutoff,
                "qr_rank": rank, "qr_reconstruction_relative_frobenius": relative_error(scaled[:, pivots], q_matrix @ triangular),
                "least_squares_normal_equation_relative_residual": float(np.linalg.norm(z.T @ residual)/max(np.linalg.norm(z)*np.linalg.norm(y), TINY)),
                "cr2_adjustments": adjustments, "aht": aht_condition,
                "coefficient_back_transform": "GAMMA/S_COLUMN; COVARIANCE_IN_ORIGINAL_UNITS_FROM_LEFT_INVERSE/S_COLUMN"}}


def relative_error(a: np.ndarray | float, b: np.ndarray | float) -> float:
    first, second = np.asarray(a, dtype=np.float64), np.asarray(b, dtype=np.float64)
    require(first.shape == second.shape and np.isfinite(first).all() and np.isfinite(second).all(),
            "NONFINITE_OR_SHAPE_DISAGREEMENT")
    return float(np.linalg.norm(first-second)/max(np.linalg.norm(first), np.linalg.norm(second), TINY))


def compare_paths(first: dict, second: dict) -> dict:
    metrics = {"beta_relative_l2": relative_error(first["beta"], second["beta"]),
               "cr2_covariance_relative_frobenius": relative_error(first["covariance"], second["covariance"]),
               "satterthwaite_df_relative_l2": relative_error(first["satterthwaite_df"], second["satterthwaite_df"]),
               "satterthwaite_df_max_component_relative": max(relative_error(a, b) for a, b in zip(first["satterthwaite_df"], second["satterthwaite_df"]))}
    for field in ("f_statistic", "denominator_df", "p_value"):
        metrics["aht_"+field+"_symmetric_relative"] = relative_error(first["aht"][field], second["aht"][field])
    sign_equal = bool(np.array_equal(np.sign(first["beta"]), np.sign(second["beta"])))
    rank_equal = first["rank"] == second["rank"]
    singularity_equal = first["singularities"] == second["singularities"] == 0
    passes = metrics["beta_relative_l2"] <= BETA_RELATIVE_TOLERANCE and all(
        v <= ADJUDICATION_RELATIVE_TOLERANCE for k, v in metrics.items() if k != "beta_relative_l2")
    return {"metrics": metrics, "sign_agreement": sign_equal, "rank_agreement": rank_equal,
            "cr2_singularity_status_agreement": singularity_equal, "nonfinite_count": 0,
            "status": "PASS" if passes and sign_equal and rank_equal and singularity_equal else "FAIL"}


def frozen_path_diagnostics(frame: pd.DataFrame, columns: list[str], period: str, main: dict, path: str) -> dict:
    z = main["design"]
    inverse = np.linalg.pinv(z, rcond=1e-12)
    residual_maker = np.eye(len(frame)) - z @ inverse
    residual_maker = (residual_maker+residual_maker.T)/2
    bread = main["bread"] if path == "MAIN" else inverse @ inverse.T
    offset = z.shape[1]-len(columns)
    vectors, adjustments = [], []
    for indices in main["cluster_indices"]:
        block = residual_maker[np.ix_(indices, indices)]
        if path == "MAIN":
            adjustment = ed1.symmetric_inverse_sqrt_psd(block)[0]
        else:
            left, singular, right = np.linalg.svd(block, full_matrices=False)
            cutoff = EPS*max(block.shape)*max(1., float(singular.max()))*128.
            weights = np.zeros_like(singular)
            weights[singular > cutoff] = 1/np.sqrt(singular[singular > cutoff])
            adjustment = (right.T*weights) @ left.T
        vectors.append((residual_maker[:, indices] @ adjustment @ z[indices] @ bread[:, offset:]).T)
        record = adjustment_record(block, indices)
        record["ubigeo"] = str(frame.iloc[indices[0]]["UBIGEO"])
        adjustments.append(record)
    omega = sum(v @ v.T for v in vectors)
    normal = z.T @ z
    normal_spectrum = spectrum(normal)
    gamma = len(frame)*EPS/(1-len(frame)*EPS)
    eta = float(normal_spectrum["condition_2"]*gamma)
    return {"path": path, "within_transformed_x": spectrum(main["x_within"]),
            "full_design": spectrum(z), "normal_matrix": normal_spectrum,
            "least_squares_rcond": "NUMPY_LSTSQ_DEFAULT_EPS_TIMES_MAX_DIMENSION" if path == "MAIN" else 1e-12,
            "bread_algorithm": "PINV_Z_TRANSPOSE_Z_HERMITIAN_RCOND_1E-12" if path == "MAIN" else "PINV_Z_RCOND_1E-12_TIMES_ITS_TRANSPOSE",
            "bread_pseudoinverse_rcond": 1e-12, "cr2_adjustments": adjustments,
            "cr2_singularity_count": sum(v["unexpected_singularity"] for v in adjustments),
            "aht_omega": spectrum(omega), "gamma_n": gamma, "condition_amplification_eta": eta,
            "condition_amplification_budget": eta/(1-eta) if eta < 1 else None,
            "bread_relative_difference_from_svd": relative_error(bread, inverse @ inverse.T)}


def reporting_objects(fit: dict, crop: str, columns: list[str]) -> dict:
    se = np.sqrt(np.diag(fit["covariance"]))
    t_values = fit["beta"]/se
    p_values = 2*stats.t.sf(np.abs(t_values), fit["satterthwaite_df"])
    ci_width = stats.t.ppf(.975, fit["satterthwaite_df"])*se
    return {"coefficient_sign": np.sign(fit["beta"]).astype(int).tolist(),
            "ci_zero_inclusion": ((fit["beta"]-ci_width <= 0) & (fit["beta"]+ci_width >= 0)).tolist(),
            "effective_df_flags": [er1.effective_df_flag(crop, df) for df in fit["satterthwaite_df"]],
            "holm_ordering": [columns[i] for i in np.argsort(p_values, kind="mergesort")],
            "aht_numerical_result": {"df6": format(fit["aht"]["denominator_df"], ".6f"),
                                     "f6": format(fit["aht"]["f_statistic"], ".6f"),
                                     "p6": format(fit["aht"]["p_value"], ".6f")},
            "coefficient_df6": [format(v, ".6f") for v in fit["satterthwaite_df"]],
            "beta12_significant_digits": [format(v, ".12g") for v in fit["beta"]],
            "p_below_0_05_used_as_gate": False}


def algebraic_projection(level: np.ndarray, anomaly: np.ndarray, districts: np.ndarray, columns: list[str]) -> dict:
    difference = level-anomaly
    labels = sorted(set(districts))
    dummy = np.column_stack([(districts == label).astype(float) for label in labels])
    constants = (dummy.T @ difference)/dummy.sum(axis=0)[:, None]
    residual = difference-dummy @ constants
    precision = 128*EPS*np.maximum(1., np.maximum(np.max(np.abs(level), axis=0), np.max(np.abs(anomaly), axis=0)))
    rows = []
    for i, column in enumerate(columns):
        ranges = [float(np.ptp(difference[districts == district, i])) for district in labels]
        norm = float(np.linalg.norm(residual[:, i]))
        maximum = float(np.max(np.abs(residual[:, i])))
        rows.append({"level_variable": column, "max_within_district_time_range": max(ranges),
                     "district_time_ranges": dict(zip(labels, ranges)),
                     "district_constants": dict(zip(labels, constants[:, i].tolist())),
                     "projection_residual_l2": norm, "projection_residual_max_abs": maximum,
                     "projection_relative_l2": norm/max(float(np.linalg.norm(difference[:, i])), TINY),
                     "source_representation_bound": float(precision[i]),
                     "time_invariance_and_projection_pass": bool(max(ranges) <= precision[i] and maximum <= precision[i])})
    passes = all(r["time_invariance_and_projection_pass"] for r in rows)
    return {"status": "ALGEBRAIC_FE_EQUIVALENCE_CONFIRMED_FLOAT64_NONEXACT" if passes else "NOT_CONFIRMED",
            "columns": rows, "district_dummy_rank": len(labels),
            "projection_residual_frobenius": float(np.linalg.norm(residual)),
            "projection_residual_max_abs": float(np.max(np.abs(residual))),
            "projection_relative_frobenius": float(np.linalg.norm(residual)/max(np.linalg.norm(difference), TINY)),
            "representation_precision_policy": POLICY["source_representation_bound"],
            "identity_scope": "SOURCE_PRECISION_CONSISTENCY_NOT_BITWISE_IDENTITY",
            "exact_arithmetic_implication": "IF_LEVEL_EQUALS_ANOMALY_PLUS_DISTRICT_CONSTANT_THEN_M_FE_LEVEL_EQUALS_M_FE_ANOMALY",
            "fitted_value_implication": "SAME_SLOPE_ESTIMAND_AND_FITTED_VALUES_AFTER_FE_REPARAMETERIZATION",
            "distinct_evidence_contribution": 0}


def serializable_fit(fit: dict) -> dict:
    return {"beta": fit["beta"].tolist(), "covariance": fit["covariance"].tolist(),
            "satterthwaite_df": fit["satterthwaite_df"].tolist(), "aht": fit["aht"],
            "rank": fit["rank"], "cr2_singularities": fit["singularities"]}


def main_view(fit: dict) -> dict:
    return {"beta": fit["beta"], "covariance": fit["climate_covariance"],
            "satterthwaite_df": fit["satterthwaite_df"], "aht": fit["aht"],
            "rank": int(np.linalg.matrix_rank(fit["design"])), "singularities": fit["cr2_adjustment_singularities"]}


def audit_transient(code: str, frame: pd.DataFrame, columns: list[str], old: dict) -> dict:
    y = frame["YIELD"].to_numpy(dtype=float)
    period = ed1.CROPS[code]["period_column"]
    require(legacy.sample_keys(frame, period) == old["sample_identity"][code]["er1_ordered_keys"],
            "ER2_R1A_FAIL_ORIGINAL_RESULT_DRIFT: sample")
    raw_main = ed1.fit_two_way_fe_cr2(frame, columns, period, y)
    main = main_view(raw_main)
    svd = ed1._reference_svd_fit(frame, columns, period, y)
    diagnostics = {p: frozen_path_diagnostics(frame, columns, period, raw_main, p) for p in ("MAIN", "SVD")}
    svd.update(rank=diagnostics["SVD"]["full_design"]["rank_at_rcond"], singularities=diagnostics["SVD"]["cr2_singularity_count"])
    strict = legacy.numerical_verification(frame, columns, period, y, raw_main)
    require(strict == old["independent_numerical_verification"][code],
            "ER2_R1A_FAIL_ORIGINAL_RESULT_DRIFT: historical discrepancies not reproduced")
    require(strict["status"] == "FAIL", "STRICT_LEGACY_FAILURE_NOT_PRESERVED")
    third = third_fit(frame, columns, period, y)
    paths = {"MAIN": main, "SVD": svd, "THIRD": third}
    pairs = {a+"_VS_"+b: compare_paths(paths[a], paths[b]) for a, b in itertools.combinations(paths, 2)}
    report = {k: reporting_objects(v, ed1.CROPS[code]["crop"], columns) for k, v in paths.items()}
    invariant = {key: all(report[p][key] == report["MAIN"][key] for p in paths)
                 for key in report["MAIN"] if key != "p_below_0_05_used_as_gate"}
    diagnostics["THIRD"] = third["diagnostics"]
    diagnostics["MAIN"]["aht_contrast_covariance"] = spectrum(main["covariance"])
    diagnostics["SVD"]["aht_contrast_covariance"] = spectrum(svd["covariance"])
    return {"crop": ed1.CROPS[code]["crop"], "crop_code": code, "columns": columns,
            "strict_legacy_status": "FAIL_PRESERVED", "strict_recomputed_verification": strict,
            "paths": {k: serializable_fit(v) for k, v in paths.items()}, "conditioning": diagnostics,
            "pairwise": pairs, "reporting_objects": report, "reporting_invariance": invariant,
            "reporting_invariance_used_as_pass_criterion": False,
            "status": "PASS" if all(p["status"] == "PASS" for p in pairs.values()) else "FAIL"}


def inference_vector(fit: dict) -> np.ndarray:
    se = np.sqrt(np.diag(fit["covariance"]))
    critical = stats.t.ppf(.975, fit["satterthwaite_df"])
    return np.concatenate([se, fit["beta"]/se, 2*stats.t.sf(np.abs(fit["beta"]/se), fit["satterthwaite_df"]),
                           fit["beta"]-critical*se, fit["beta"]+critical*se])


def perennial_audit(code: str, primary: pd.DataFrame, level: pd.DataFrame,
                     anomaly_columns: list[str], columns: list[str], old_diagnostic: dict) -> dict:
    period = ed1.CROPS[code]["period_column"]
    keys = legacy.require_same_sample(primary, level, period)
    require(keys == old_diagnostic["ordered_sample_keys"], "ER2_R1A_FAIL_ORIGINAL_RESULT_DRIFT: perennial sample")
    y = primary["YIELD"].to_numpy(dtype=float)
    reproduced = legacy.perennial_diagnostic(code, primary, level, anomaly_columns, columns, y)
    require(reproduced == old_diagnostic, "ER2_R1A_FAIL_ORIGINAL_RESULT_DRIFT: perennial discrepancies")
    algebra = algebraic_projection(level[columns].to_numpy(dtype=float), primary[anomaly_columns].to_numpy(dtype=float),
                                   primary["UBIGEO"].astype(str).to_numpy(), columns)
    if algebra["status"] == "NOT_CONFIRMED":
        return {"crop_code": code, "algebra": algebra, "status": "FAIL", "original_diagnostic": old_diagnostic}
    main_level_raw = ed1.fit_two_way_fe_cr2(level, columns, period, y)
    main_anomaly_raw = ed1.fit_two_way_fe_cr2(primary, anomaly_columns, period, y)
    main_level, main_anomaly = main_view(main_level_raw), main_view(main_anomaly_raw)
    stable_level = third_fit(level, columns, period, y)
    stable_anomaly = third_fit(primary, anomaly_columns, period, y)
    legacy_pair = compare_paths(main_level, main_anomaly)
    stable_pair = compare_paths(stable_level, stable_anomaly)
    conditioning = {"LEVEL_MAIN": frozen_path_diagnostics(level, columns, period, main_level_raw, "MAIN"),
                    "ANOMALY_MAIN": frozen_path_diagnostics(primary, anomaly_columns, period, main_anomaly_raw, "MAIN"),
                    "LEVEL_QR": stable_level["diagnostics"], "ANOMALY_QR": stable_anomaly["diagnostics"]}
    budget_values = [conditioning[k]["condition_amplification_budget"] for k in ("LEVEL_MAIN", "ANOMALY_MAIN")]
    budget = sum(budget_values) if all(b is not None for b in budget_values) else None
    downstream = {k: v for k, v in legacy_pair["metrics"].items() if k != "beta_relative_l2"}
    downstream["coefficient_inference_vector_relative_l2"] = relative_error(inference_vector(main_level), inference_vector(main_anomaly))
    bound_consistency = budget is not None and max(downstream.values()) <= budget
    no_rank_loss = all(conditioning[k]["normal_matrix"]["rank_at_rcond"] == conditioning[k]["full_design"]["rank_at_rcond"]
                       for k in ("LEVEL_MAIN", "ANOMALY_MAIN"))
    gates = {"stable_qr_equivalence": stable_pair["status"] == "PASS", "error_amplification_consistency": bound_consistency,
             "no_normal_equation_rank_loss": no_rank_loss,
             "legacy_rank_and_singularity_agreement": legacy_pair["rank_agreement"] and legacy_pair["cr2_singularity_status_agreement"]}
    return {"crop_code": code, "crop": ed1.CROPS[code]["crop"], "algebra": algebra,
            "source_hashes": {ed1.PERENNIAL_PATH.relative_to(ROOT).as_posix(): legacy.FROZEN_HASHES[ed1.PERENNIAL_PATH.relative_to(ROOT).as_posix()]},
            "original_float64_status": old_diagnostic["status"], "original_absolute_discrepancies": old_diagnostic["metrics"],
            "legacy_level_vs_anomaly": legacy_pair, "legacy_downstream_relative_differences": downstream,
            "third_qr_level_vs_anomaly": stable_pair, "conditioning": conditioning,
            "condition_amplification_budget_sum": budget, "inference_drift_gates": gates,
            "interpretation": "CONSISTENT_WITH_FLOAT64_ERROR_AMPLIFICATION" if all(gates.values()) else "NOT_SUFFICIENTLY_EXPLAINED_BLOCKED",
            "third_paths": {"LEVEL": serializable_fit(stable_level), "ANOMALY": serializable_fit(stable_anomaly)},
            "distinct_evidence_contribution": 0, "status": "PASS" if all(gates.values()) else "FAIL"}


def comparison_passes(pair: dict) -> bool:
    return (pair["status"] == "PASS" and pair["nonfinite_count"] == 0
            and pair["sign_agreement"] and pair["rank_agreement"] and pair["cr2_singularity_status_agreement"]
            and all(np.isfinite(v) and v <= (BETA_RELATIVE_TOLERANCE if k == "beta_relative_l2" else
                                            ADJUDICATION_RELATIVE_TOLERANCE) for k, v in pair["metrics"].items()))


def certification_allowed(result: dict) -> bool:
    return (set(result["transient"]) == set(er2p.TRANSIENT)
            and all(v["status"] == "PASS" and set(v["pairwise"]) == {"MAIN_VS_SVD", "MAIN_VS_THIRD", "SVD_VS_THIRD"}
                    and all(comparison_passes(p) for p in v["pairwise"].values()) for v in result["transient"].values())
            and set(result["perennial"]) == set(er2p.PERENNIAL)
            and all(v["status"] == "PASS" and all(v["inference_drift_gates"].values())
                    and comparison_passes(v["third_qr_level_vs_anomaly"])
                    and v["algebra"]["status"] == "ALGEBRAIC_FE_EQUIVALENCE_CONFIRMED_FLOAT64_NONEXACT"
                    for v in result["perennial"].values()))


def calculate() -> dict:
    pre = preflight()
    old = json.loads((ROOT / legacy.LOCK_REL).read_bytes())
    transient_outcomes, perennial_outcomes, _ = er1.read_outcome_sources()
    transient = legacy.pq.read_table(ed1.TRANSIENT_PATH, columns=list(ed1.TRANSIENT_COLUMNS)).to_pandas()
    perennial = ed1.read_perennial_primary()
    record = {"schema_version": "1.0.0", "gate": "ER2_R1A_TARGETED_NUMERICAL_ADJUDICATION_V1",
              "preflight": pre, "environment": environment_record(), "policy": POLICY,
              "implementation_sha256": legacy.sha((ROOT / SCRIPT_REL).read_bytes()),
              "test_sha256": legacy.sha((ROOT / TEST_REL).read_bytes()),
              "third_numerical_path": THIRD_PATH, "transient": {}, "perennial": {},
              "strict_legacy_1e8_status": "FAIL_PRESERVED", "r1_results_numerically_changed": False,
              "r1_specification_changed": False, "r1_first_attempt_lock_sha256": FIRST_LOCK_SHA,
              "distinct_robustness_evidence_count": 2, "perennial_distinct_evidence_count": 0,
              "execution_firewall": legacy.FIREWALL, "next_tier_authorization_status": "NOT_AUTHORIZED"}
    for code in er2p.TRANSIENT:
        frame, _ = er1.transient_design_with_outcome(transient, transient_outcomes, code)
        record["transient"][code] = audit_transient(code, frame, list(legacy.LEVEL), old)
        if record["transient"][code]["status"] != "PASS":
            record["verdict"] = BLOCKED_NUMERICAL
            return record
    old_diagnostics = {d["crop_code"]: d for d in old["perennial_equivalence_diagnostics"]}
    for code in er2p.PERENNIAL:
        primary, anomalies = er1.perennial_design_with_outcome(perennial, perennial_outcomes, code)
        level, columns = ed1.primary_design_frame(pd.DataFrame(), perennial, code, "LEVEL")
        period = ed1.CROPS[code]["period_column"]
        level[period] = level[period].astype(str)
        record["perennial"][code] = perennial_audit(code, primary, level, anomalies, columns, old_diagnostics[code])
        if record["perennial"][code]["status"] != "PASS":
            record["verdict"] = BLOCKED_ALGEBRA if record["perennial"][code]["algebra"]["status"] == "NOT_CONFIRMED" else BLOCKED_NUMERICAL
            return record
    require(certification_allowed(record), "ER2_R1A_FAIL_ADJUDICATION_TESTS: certification predicate")
    record["verdict"] = PASS
    verify_originals()
    legacy.verify_inputs()
    return record


def render_report(result: dict) -> str:
    lines = ["# ER2 R1A Numerical Adjudication v1", "", "FINAL_VERDICT="+result["verdict"], "",
             "The seven original R1 files and the provisional failure lock are immutable. No result table, specification, tolerance or historical test is replaced.",
             "The historical absolute 1e-8 rule is an alarm across heterogeneous units, not a scale-free distance; it remains FAIL_PRESERVED, not incorrect or erased.",
             "R2-R6 remain unauthorized and unexecuted. No path averaging, result selection, or new significance criterion.", "",
             "## Numerical environment", "", "```json", json.dumps(result["environment"], sort_keys=True, indent=2), "```", "",
             "## Prespecified adjudication policy", "", "```json", json.dumps(POLICY, sort_keys=True, indent=2), "```", "",
             "The third path uses explicit district/period FE, deterministic column L2 scaling, pivoted QR, triangular solves and back-transformation to original units. CR2 is reconstructed directly from cluster influence matrices; HTZ uses Cholesky whitening and cluster-pair traces.",
             "References: [SciPy pivoted QR](https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.qr.html); [clubSandwich HTZ](https://jepusto.github.io/clubSandwich/reference/Wald_test.html).", ""]
    for code, audit in result["transient"].items():
        lines.extend(["## "+audit["crop"], "", "THREE_PATH_STATUS="+audit["status"],
                      "Strict historical discrepancies reproduce exactly: "+json.dumps(audit["strict_recomputed_verification"]["differences"], sort_keys=True), ""])
        for name, pair in audit["pairwise"].items():
            lines.append(name+": "+json.dumps(pair, sort_keys=True))
        for path in ("MAIN", "SVD"):
            d = audit["conditioning"][path]
            lines.append(f"{path}: condition(within X)={d['within_transformed_x']['condition_2']:.12g}; condition(Z)={d['full_design']['condition_2']:.12g}; condition(Z'Z)={d['normal_matrix']['condition_2']:.12g}; bread drift={d['bread_relative_difference_from_svd']:.12g}.")
        lines.extend(["Reporting invariance (descriptive only): "+json.dumps(audit["reporting_invariance"], sort_keys=True), ""])
    for audit in result["perennial"].values():
        lines.extend(["## Perennial "+audit["crop_code"], "", "ALGEBRA="+audit["algebra"]["status"],
                      "Original float64 nonexact status is preserved; distinct evidence contribution remains zero.",
                      "Projection maximum absolute residual: "+str(audit["algebra"]["projection_residual_max_abs"]),
                      "The exposure difference is tested against district constants at source representation precision. If LEVEL=ANOMALY+district constant, M_FE annihilates that constant in exact arithmetic, preserving slopes and fitted values after FE reparameterization.", ""])
        if "legacy_downstream_relative_differences" in audit:
            lines.extend(["Legacy downstream relative discrepancies: "+json.dumps(audit["legacy_downstream_relative_differences"], sort_keys=True),
                          "Original absolute discrepancies: "+json.dumps({k: v["max_abs_difference"] for k, v in audit["original_absolute_discrepancies"].items()}, sort_keys=True),
                          "Stable QR LEVEL/anomaly: "+json.dumps(audit["third_qr_level_vs_anomaly"], sort_keys=True),
                          "Drift gates: "+json.dumps(audit["inference_drift_gates"], sort_keys=True),
                          "Interpretation: "+audit["interpretation"], ""])
    lines.extend(["## Certification and provenance", "",
                  "The JSON records full spectra, CR2 block eigenvalues, AHT conditioning, all pairwise numerical distances and reporting objects. The conditioning budget is a diagnostic scale for amplification, not a rigorous end-to-end error guarantee.",
                  "Original R1 result CSV hashes remain the scientific result identities; QR results are verification only.",
                  "R1_FIRST_ATTEMPT_PROVISIONAL_FAILURE_LOCK_SHA256="+FIRST_LOCK_SHA,
                  "CERTIFIED_LOCK_CREATION_AUTHORIZED_BY_ADJUDICATION="+str(certification_allowed(result)).upper(),
                  "NEXT_TIER_AUTHORIZATION_STATUS=NOT_AUTHORIZED", "",
                  "NEXT_ACTION=RETURN_TO_SCIENTIFIC_DIRECTOR_FOR_R1_FREEZE_DECISION_IF_PASS", ""])
    return "\n".join(lines)


def certified_lock(result: dict, adjudication_hash: str, report_hash: str) -> dict | None:
    if not certification_allowed(result) or result["verdict"] != PASS:
        return None
    old = json.loads((ROOT / legacy.LOCK_REL).read_bytes())
    return {"schema_version": "1.0.0", "gate": result["gate"], "status": "R1_NUMERICALLY_CERTIFIED_PENDING_DIRECTOR_FREEZE_DECISION",
            "er2p_freeze_sha": legacy.ER2P_SHA, "er1_freeze_sha": er2p.ER1_SHA, "ed1_freeze_sha": er2p.ED1_SHA,
            "er1_numerical_results_identity": er2p.NUMERICAL_IDENTITY, "er2p_protocol_sha256": legacy.PROTOCOL_SHA,
            "tier_id": old["tier_id"], "tier_order": 1, "tier_contract_sha256": old["tier_contract_sha256"],
            "R1_FIRST_ATTEMPT_PROVISIONAL_FAILURE_LOCK_SHA256": FIRST_LOCK_SHA,
            "STRICT_LEGACY_1E8_STATUS": "FAIL_PRESERVED", "NUMERICAL_ADJUDICATION_STATUS": "PASS",
            "R1_RESULTS_NUMERICALLY_CHANGED": False, "R1_SPECIFICATION_CHANGED": False,
            "PERENNIAL_DISTINCT_EVIDENCE_COUNT": 0, "R1_DISTINCT_ROBUSTNESS_EVIDENCE_COUNT": 2,
            "NEXT_TIER_AUTHORIZATION_STATUS": "NOT_AUTHORIZED", "previous_tier_lock_sha256": None,
            "original_r1_sha256": ORIGINAL_HASHES, "original_result_artifact_sha256": old["artifact_sha256"],
            "adjudication_sha256": adjudication_hash, "adjudication_report_sha256": report_hash,
            "adjudication_implementation_sha256": result["implementation_sha256"], "adjudication_test_sha256": result["test_sha256"],
            "execution_firewall": legacy.FIREWALL, "final_verdict": PASS,
            "next_action": "RETURN_TO_SCIENTIFIC_DIRECTOR_FOR_R1_FREEZE_DECISION_IF_PASS"}


def render_outputs() -> dict[Path, bytes]:
    result = calculate()
    outputs = {JSON_REL: legacy.json_bytes(result), REPORT_REL: render_report(result).encode("utf-8")}
    lock = certified_lock(result, legacy.sha(outputs[JSON_REL]), legacy.sha(outputs[REPORT_REL]))
    if lock is not None:
        outputs[CERTIFIED_REL] = legacy.json_bytes(lock)
    return outputs


def publish(outputs: dict[Path, bytes], destination: Path) -> dict:
    destination = destination.resolve()
    require(destination == ROOT or not destination.is_relative_to(ROOT), "External temporary output root required")
    result = json.loads(outputs[JSON_REL])
    require((CERTIFIED_REL in outputs) == certification_allowed(result), "CERTIFIED_LOCK_GATE_VIOLATION")
    require(set(outputs) == {JSON_REL, REPORT_REL} | ({CERTIFIED_REL} if certification_allowed(result) else set()),
            "ADJUDICATION_OUTPUT_SCOPE_VIOLATION")
    if CERTIFIED_REL not in outputs:
        require(not (destination / CERTIFIED_REL).exists(), "STALE_CERTIFIED_LOCK_FOR_FAILED_ADJUDICATION")
    for rel, payload in outputs.items():
        target = destination / rel
        require(not target.exists() or target.read_bytes() == payload, "IMMUTABLE_ADJUDICATION_REVISION_PROHIBITED: "+rel.as_posix())
    for rel, payload in outputs.items():
        target = destination / rel
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload)
    return {p.as_posix(): legacy.sha(b) for p, b in outputs.items()}


def run(destination: Path = ROOT) -> dict:
    return publish(render_outputs(), destination)


def main() -> int:
    parser = argparse.ArgumentParser(description="R1A numerical adjudication only; preserve the original R1 attempt.")
    parser.add_argument("--output-root", type=Path, default=ROOT)
    parser.add_argument("--live-preflight", action="store_true")
    args = parser.parse_args()
    preflight(live_remote=args.live_preflight)
    hashes = run(args.output_root)
    result = json.loads((args.output_root / JSON_REL).read_bytes())
    print(json.dumps({"verdict": result["verdict"], "sha256": hashes}, sort_keys=True))
    return 0 if result["verdict"] == PASS else 1


if __name__ == "__main__":
    raise SystemExit(main())
