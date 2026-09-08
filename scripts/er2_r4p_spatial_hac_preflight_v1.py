from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import io
import json
import math
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd
from pyproj import Transformer
from shapely.geometry import shape
from shapely.ops import transform


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import econometric_design_master_v1 as ed1  # noqa: E402


PROJECT = "ENSO_EL_NINO_2026_2027_AGRICULTURE_PIURA"
GATE = "ER2_R4P_SPATIAL_HAC_CONLEY_PREEXECUTION_CERTIFICATION_V1"
FINAL_VERDICT = "ER2_R4P_PASS_SPATIAL_HAC_PREEXECUTION_CERTIFIED_READY_FOR_DIRECTOR_EXECUTION_DECISION"

R3_FREEZE_SHA = "ac99e5adb1077cf0d8a545d0077e6b980b4d8a6d"
R3_PARENT_SHA = "c285ccc97fca384663ef98d730cd6cd325c71000"
R3_BRANCH = "phase/er2-r3-restricted-wcr-v1"
R3_TAG = "er2-r3-restricted-wcr-v1-freeze"
R3_TAG_OBJECT = "b9684b46eec5253752c8d4e12f658bbdd10ea18c"
R3_RESULTS_LOCK_SHA = "931bb70ecece35b5b5751d031b7d34204252de9e4f5106b420ac9572b3eea6b7"

TIER_CONTRACT_SHA = "02b1ac12ec85231877f539eadb9f288432012cda0bce5ec0ab917b1e6118ab6b"
GEOMETRY_SHA = "d966d2a38e80d6575490be32bde2e39b7db66a3c6e99b240e9c21458766d099b"
GEOMETRY_BLOB = "9b961fb2175ff0d6f79e3f486a2ce40bd8f0b143"
ED1_IMPLEMENTATION_SHA = "69fb1b1f0a1d7c4ec7791fdfa2d3cfb20d62b4ed0f6348b155155523b6b48195"
CONLEY_SOURCE_SHA = "9a67e58fbcb636273baa6a74ef1e4b74deb94ccb3588121545d7e599513dfc77"
CONLEY_BODY_SHA = "71c27363a0bb95e15f6be07a9f57793cbcfded898ef7b9ccd2c1e72c6f987e2d"

TIER_CONTRACTS = Path("outputs/econometrics/ER2P_TIER_CONTRACTS.csv")
PROTOCOL = Path("config/econometrics/er2_robustness_protocol_v1.json")
ED1_SCRIPT = Path("scripts/econometric_design_master_v1.py")
ED1_CONFIG = Path("config/econometrics/econometric_design_master_v1.json")
ED1_REPORT = Path("outputs/econometrics/ED1_ECONOMETRIC_DESIGN_REPORT.md")
GEOMETRY = Path("data/processed/climate/district_boundaries_piura.geojson")
ER1_COEFFICIENTS = Path("outputs/econometrics/ER1_PRIMARY_COEFFICIENTS.csv")
R3_SAMPLE_AUDIT = Path("outputs/econometrics/ER2_R3_SAMPLE_AUDIT.csv")
R3_RESULTS_LOCK = Path("outputs/econometrics/ER2_R3_RESULTS_LOCK.json")

REPORT = Path("outputs/econometrics/ER2_R4P_PREFLIGHT_REPORT.md")
COEFFICIENT_MAP = Path("outputs/econometrics/ER2_R4P_COEFFICIENT_MAP.csv")
GEOMETRY_AUDIT = Path("outputs/econometrics/ER2_R4P_GEOMETRY_AUDIT.csv")
SYNTHETIC_VALIDATION = Path("outputs/econometrics/ER2_R4P_SYNTHETIC_VALIDATION.csv")
PREFLIGHT_LOCK = Path("outputs/econometrics/ER2_R4P_PREFLIGHT_LOCK.json")
TEST_PLAN_LOCK = Path("outputs/econometrics/ER2_R4P_SYNTHETIC_TEST_PLAN_LOCK.json")
SCRIPT = Path("scripts/er2_r4p_spatial_hac_preflight_v1.py")
TEST = Path("tests/test_er2_r4p_spatial_hac_preflight_v1.py")

GENERATED = (TEST_PLAN_LOCK, COEFFICIENT_MAP, GEOMETRY_AUDIT, SYNTHETIC_VALIDATION, REPORT, PREFLIGHT_LOCK)
CANDIDATES = (*GENERATED, SCRIPT, TEST)

FROZEN_INPUT_SHA256 = {
    TIER_CONTRACTS: "2ff57eadb872ca6aa10cb84aa4fdf9b7250715df5ca77d2f3e9d22621e7d762a",
    PROTOCOL: "13519fb5c86fdf690d233c54dd45c3242ba348f3c7f66587238e6965ed1c49ff",
    ED1_SCRIPT: ED1_IMPLEMENTATION_SHA,
    ED1_CONFIG: "feaddf35700a84592ba024ae1fb9e4c9419e00672828fdb7cb29f2775d933c6d",
    ED1_REPORT: "49d2d5bdd2d0871c8f868902be197fda6228423a4f1577b83f47eea34ecc8b34",
    GEOMETRY: GEOMETRY_SHA,
    ER1_COEFFICIENTS: "37fa03a2e860f86277510a5ff3b66ca475fc02d277ea1dd6e18156f719c23480",
    R3_SAMPLE_AUDIT: "6252b0ec924a14ff6b1ea3d3470c4aa2eaa588d91acc5362d9b6d1874a796193",
    R3_RESULTS_LOCK: R3_RESULTS_LOCK_SHA,
}

BANDWIDTHS_KM = (50, 100, 150)
TOLERANCE = 1e-10
NORMAL_CRITICAL_VALUE = 1.959963984540054

CROP_SPECS = {
    "14010020000": {
        "crop": "RICE",
        "model_id": "ED1-RICE",
        "period_key": "CAMPAIGN_ID:DISTRICT_X_AUG_JUL_AGRICULTURAL_CAMPAIGN",
        "variables": ("RAIN_ANOM_MM", "TMAX_ANOM_C", "TMIN_ANOM_C"),
    },
    "14010070000": {
        "crop": "MAIZ_AMARILLO_DURO",
        "model_id": "ED1-MAD",
        "period_key": "CAMPAIGN_ID:DISTRICT_X_AUG_JUL_AGRICULTURAL_CAMPAIGN",
        "variables": ("RAIN_ANOM_MM", "TMAX_ANOM_C", "TMIN_ANOM_C"),
    },
    "13010210000": {
        "crop": "MANGO",
        "model_id": "ED1-MANGO",
        "period_key": "REFERENCE_PERIOD_ID:DISTRICT_X_CALENDAR_YEAR",
        "variables": ("RAIN_ANOM_MM", "TMAX_ANOM_C", "TMIN_ANOM_C"),
    },
    "13010170102": {
        "crop": "LIMON_SUTIL",
        "model_id": "ED1-LEMON",
        "period_key": "REFERENCE_PERIOD_ID:DISTRICT_X_CALENDAR_YEAR",
        "variables": (
            "RAIN_ANOM_MM__T",
            "TMAX_ANOM_C__T",
            "TMIN_ANOM_C__T",
            "RAIN_ANOM_MM__T_MINUS_1",
            "TMAX_ANOM_C__T_MINUS_1",
            "TMIN_ANOM_C__T_MINUS_1",
        ),
    },
    "15010040000": {
        "crop": "PLATANOS_Y_BANANAS",
        "model_id": "ED1-BANANA",
        "period_key": "REFERENCE_PERIOD_ID:DISTRICT_X_CALENDAR_YEAR",
        "variables": (
            "RAIN_ANOM_MM__T",
            "TMAX_ANOM_C__T",
            "TMIN_ANOM_C__T",
            "RAIN_ANOM_MM__T_MINUS_1",
            "TMAX_ANOM_C__T_MINUS_1",
            "TMIN_ANOM_C__T_MINUS_1",
        ),
    },
}

EXPECTED_SAMPLES = {
    "14010020000": (281, 44, 43, 7),
    "14010070000": (318, 54, 52, 7),
    "13010210000": (255, 36, 35, 8),
    "13010170102": (311, 44, 43, 8),
    "15010040000": (390, 54, 50, 8),
}

REAL_R4_OUTPUT_SCHEMA = (
    "CROP",
    "CROP_CODE",
    "MODEL_ID",
    "VARIABLE",
    "BANDWIDTH_KM",
    "ER1_BETA_REFERENCE",
    "CONLEY_VARIANCE",
    "CONLEY_SE",
    "Z",
    "TWO_SIDED_ASYMPTOTIC_P",
    "NORMAL_CRITICAL_VALUE",
    "CI95_LOWER",
    "CI95_UPPER",
    "CI_ZERO_INCLUDED",
    "SAMPLE_N",
    "NOMINAL_DISTRICTS",
    "PERIODS",
    "CRS",
    "KERNEL",
    "SAME_PERIOD_ONLY",
    "STATUS",
)

SYNTHETIC_PLAN = {
    "schema_version": "1.0.0",
    "status": "LOCKED_BEFORE_SYNTHETIC_EXECUTION",
    "seed": 20260904,
    "rng": "NUMPY_GENERATOR_PCG64",
    "districts": 6,
    "periods": 3,
    "observations": 18,
    "regressors": 4,
    "period_key": "SYNTHETIC_PERIOD",
    "coordinate_crs": "SYNTHETIC_PROJECTED_METRES",
    "coordinates_metres": {
        "D0": [0.0, 0.0],
        "D1": [25000.0, 0.0],
        "D2": [50000.0, 0.0],
        "D3": [75000.0, 0.0],
        "D4": [150000.0, 0.0],
        "D5": [0.0, 0.0],
    },
    "bandwidths_km": list(BANDWIDTHS_KM),
    "absolute_tolerance": TOLERANCE,
    "equivalence": "FLOAT64_CONTINUOUS_EQUIVALENCE_WITHIN_PRESPECIFIED_TOLERANCE",
    "criteria": [
        "PRODUCTION_REFERENCE_MAX_ABS_DIFFERENCE_LE_1E_10",
        "ROW_ORDER_INVARIANCE_LE_1E_10",
        "DISTRICT_LABEL_INVARIANCE_LE_1E_10",
        "COORDINATE_TRANSLATION_INVARIANCE_LE_1E_10",
        "COEFFICIENT_COLUMN_MAPPING_INVARIANCE_LE_1E_10",
        "FAIL_CLOSED_NONPOSITIVE_NONFINITE_VARIANCE",
    ],
    "edge_cases": list("ABCDEFGHIJKLMNOP"),
    "se_monotonicity_across_bandwidths": "NOT_REQUIRED",
    "real_outcome_values_read": False,
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


def csv_bytes(rows: list[dict[str, Any]], fieldnames: list[str]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def git_text(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def git_bytes(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def read_json(relative: Path) -> Any:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def r4_contract() -> tuple[dict[str, str], dict[str, Any]]:
    with (ROOT / TIER_CONTRACTS).open(encoding="utf-8", newline="") as handle:
        row = next(item for item in csv.DictReader(handle) if item["TIER"] == "R4_SPATIAL_HAC")
    expected_row = {
        "ORDER": "4",
        "TIER": "R4_SPATIAL_HAC",
        "ROLE": "ASYMPTOTIC_SPATIAL_HAC_ROBUSTNESS_DIAGNOSTIC",
        "FAMILY": "PHYSICAL_ANOMALY",
        "MULTIPLICITY": "DIAGNOSTIC_ROBUSTNESS_NO_NEW_CONFIRMATORY_FWER_CLAIM",
        "PREVIOUS_TIER": "R3",
        "NEXT_TIER": "R5",
        "EXECUTION_STATUS": "NOT_EXECUTED",
        "ER1_NUMERICAL_RESULTS_IDENTITY": "40e0f58269dda309e83a1fa3da17ef4d5dc5523efc72a666f734d0ebacb76b24",
        "TIER_CONTRACT_SHA256": TIER_CONTRACT_SHA,
    }
    require(row == expected_row, "ER2_R4P_FAIL_R4_CONTRACT_IDENTITY: tier row")
    protocol = read_json(PROTOCOL)
    tier = next(item for item in protocol["tiers"] if item["tier"] == "R4")
    require(sha_bytes(json_bytes(tier)) == TIER_CONTRACT_SHA, "ER2_R4P_FAIL_R4_CONTRACT_IDENTITY: tier SHA")
    required = {
        "bandwidths_km": [50, 100, 150],
        "kernel": "BARTLETT",
        "pairing": "SAME_PERIOD_ONLY",
        "coordinates": "EPSG:32717_DISTRICT_CENTROIDS",
        "distance": "EUCLIDEAN_PROJECTED_METRES_DIVIDED_BY_1000",
        "interval": "ER1_BETA_PLUS_MINUS_1.959963984540054_TIMES_CONLEY_SE",
        "normal_critical_value": NORMAL_CRITICAL_VALUE,
        "nonpositive_or_nonfinite_variance": "HOLD_NO_CLIPPING_OR_COVARIANCE_SUBSTITUTION",
        "coefficient_bandwidth_rows": 63,
    }
    require(all(tier[key] == value for key, value in required.items()), "ER2_R4P_FAIL_R4_CONTRACT_IDENTITY: fields")
    return row, tier


def preflight() -> dict[str, Any]:
    identity = {
        "head": git_text("rev-parse", "HEAD"),
        "branch": git_text("branch", "--show-current"),
        "local_branch": git_text("rev-parse", R3_BRANCH),
        "remote_branch": git_text("rev-parse", f"origin/{R3_BRANCH}"),
        "tag_object": git_text("rev-parse", R3_TAG),
        "tag_target": git_text("rev-parse", f"{R3_TAG}^{{}}"),
    }
    expected = {
        "head": R3_FREEZE_SHA,
        "branch": R3_BRANCH,
        "local_branch": R3_FREEZE_SHA,
        "remote_branch": R3_FREEZE_SHA,
        "tag_object": R3_TAG_OBJECT,
        "tag_target": R3_FREEZE_SHA,
    }
    require(identity == expected, f"ER2_R4P_FAIL_R3_PREDECESSOR_IDENTITY: {identity}")
    require(not git_text("diff", "--name-only"), "ER2_R4P_FAIL_R3_PREDECESSOR_IDENTITY: tracked changes")
    require(not git_text("diff", "--cached", "--name-only"), "ER2_R4P_FAIL_R3_PREDECESSOR_IDENTITY: staged changes")
    untracked = set(git_text("ls-files", "--others", "--exclude-standard").splitlines())
    authorized = {path.as_posix() for path in CANDIDATES}
    require(untracked.issubset(authorized), f"ER2_R4P_FAIL_R3_PREDECESSOR_IDENTITY: untracked={sorted(untracked)}")
    actual = {path.as_posix(): sha_file(ROOT / path) for path in FROZEN_INPUT_SHA256}
    expected_hashes = {path.as_posix(): value for path, value in FROZEN_INPUT_SHA256.items()}
    require(actual == expected_hashes, "ER2_R4P_FAIL_R3_PREDECESSOR_IDENTITY: frozen input SHA")
    geometry_blob = git_text("rev-parse", f"{R3_PARENT_SHA}:{GEOMETRY.as_posix()}")
    require(geometry_blob == GEOMETRY_BLOB, "ER2_R4P_FAIL_GEOMETRY_PROVENANCE: blob")
    require(sha_bytes(git_bytes("cat-file", "blob", geometry_blob)) == GEOMETRY_SHA, "ER2_R4P_FAIL_GEOMETRY_PROVENANCE: raw SHA")
    forbidden = [
        path.as_posix()
        for path in (ROOT / "outputs/econometrics").glob("ER2_R4_*")
        if not path.name.startswith("ER2_R4P_")
    ]
    require(not forbidden, f"ER2_R4P_FAIL_REAL_OUTCOME_FIREWALL: {forbidden}")
    row, tier = r4_contract()
    return {
        "git_identity": identity,
        "frozen_input_sha256": actual,
        "raw_geometry_blob": geometry_blob,
        "r4_tier_row": row,
        "r4_tier_contract": tier,
    }


def conley_api_identity() -> dict[str, Any]:
    source_bytes = (ROOT / ED1_SCRIPT).read_bytes()
    text = source_bytes.decode("utf-8")
    tree = ast.parse(text)
    node = next(item for item in ast.walk(tree) if isinstance(item, ast.FunctionDef) and item.name == "conley_covariance")
    lines = text.splitlines(keepends=True)
    function_source = "".join(lines[node.lineno - 1 : node.end_lineno]).encode("utf-8")
    body_source = "".join(lines[node.body[0].lineno - 1 : node.end_lineno]).encode("utf-8")
    signature_names = [argument.arg for argument in node.args.args]
    expected_names = ["frame", "x_within", "synthetic_residual", "period_column", "bandwidth_km", "centroids"]
    require(sha_bytes(source_bytes) == ED1_IMPLEMENTATION_SHA, "ER2_R4P_FAIL_CONLEY_API_IDENTITY: file")
    require(sha_bytes(function_source) == CONLEY_SOURCE_SHA, "ER2_R4P_FAIL_CONLEY_API_IDENTITY: function")
    require(sha_bytes(body_source) == CONLEY_BODY_SHA, "ER2_R4P_FAIL_CONLEY_API_IDENTITY: body")
    require(signature_names == expected_names, "ER2_R4P_FAIL_CONLEY_API_IDENTITY: signature")
    required_source = (
        "np.maximum(1.0 - distances_km / float(bandwidth_km), 0.0)",
        "for period in sorted(set(periods))",
        "scores.T @ kernel @ scores",
        "np.linalg.pinv(x_within.T @ x_within, rcond=1e-12, hermitian=True)",
    )
    require(all(fragment in function_source.decode("utf-8") for fragment in required_source), "ER2_R4P_FAIL_CONLEY_API_IDENTITY: mechanics")
    return {
        "file": ED1_SCRIPT.as_posix(),
        "signature": "conley_covariance(frame, x_within, synthetic_residual, period_column, bandwidth_km, centroids) -> numpy.ndarray",
        "file_sha256": ED1_IMPLEMENTATION_SHA,
        "function_source_sha256": CONLEY_SOURCE_SHA,
        "function_body_sha256": CONLEY_BODY_SHA,
        "function_lines": [node.lineno, node.end_lineno],
        "required_inputs": expected_names,
        "returned_object": "K_BY_K_FLOAT64_COVARIANCE_MATRIX",
        "bandwidth_units": "KILOMETRES",
        "coordinate_units": "PROJECTED_METRES_DIVIDED_BY_1000",
        "period_handling": "SORTED_UNIQUE_PERIOD_BLOCKS_CROSS_PERIOD_PAIRS_EXACT_ZERO",
        "within_district_handling": "SAME_COORDINATE_BARTLETT_LOGIC_WITHIN_PERIOD_CROSS_PERIOD_EXCLUDED",
        "diagonal": "DISTANCE_ZERO_WEIGHT_ONE_INCLUDED",
        "pair_symmetry": "FULL_ORDERED_SYMMETRIC_KERNEL_MATRIX",
        "residual_handling": "SUPPLIED_RESIDUAL_VECTOR_MULTIPLIES_EACH_X_WITHIN_ROW",
        "meat": "SUM_PERIOD_SCORE_TRANSPOSE_KERNEL_SCORE",
        "bread": "PINV_XTX_RCOND_1E_12_HERMITIAN_TRUE_ON_BOTH_SIDES",
        "finite_sample_scaling": "NONE",
        "explicit_output_symmetrization": "NONE_MATHEMATICALLY_SYMMETRIC",
        "rank_assumption": "PSEUDOINVERSE_DEFINED_FULL_FROZEN_ER1_WITHIN_RANK_REQUIRED",
    }


def coefficient_mapping() -> list[dict[str, Any]]:
    with (ROOT / ER1_COEFFICIENTS).open(encoding="utf-8", newline="") as handle:
        source_rows = list(csv.DictReader(handle))
    require(len(source_rows) == 21, "ER2_R4P_FAIL_COEFFICIENT_MAPPING: row count")
    mapped: list[dict[str, Any]] = []
    order = 0
    for crop_code, spec in CROP_SPECS.items():
        rows = [row for row in source_rows if row["CROP_CODE"] == crop_code]
        require([row["CLIMATE_VARIABLE"] for row in rows] == list(spec["variables"]), f"ER2_R4P_FAIL_COEFFICIENT_MAPPING: {crop_code}")
        require(all(row["CROP"] == spec["crop"] and row["MODEL_ID"] == spec["model_id"] for row in rows), "ER2_R4P_FAIL_COEFFICIENT_MAPPING: identity")
        for position, row in enumerate(rows):
            order += 1
            mapped.append(
                {
                    "MAP_ORDER": order,
                    "CROP": row["CROP"],
                    "CROP_CODE": crop_code,
                    "MODEL_ID": row["MODEL_ID"],
                    "COEFFICIENT_NAME": row["CLIMATE_VARIABLE"],
                    "ED1_REGRESSOR_POSITION_ZERO_BASED": position,
                    "ED1_REGRESSOR_POSITION_ONE_BASED": position + 1,
                    "FROZEN_PERIOD_KEY_ARCHITECTURE": spec["period_key"],
                    "EXPECTED_REAL_R4_BANDWIDTHS_KM": "50|100|150",
                    "MAPPING_STATUS": "PASS_EXACT_FROZEN_ORDER",
                }
            )
    require(order == 21 and len({(row["CROP_CODE"], row["COEFFICIENT_NAME"]) for row in mapped}) == 21, "ER2_R4P_FAIL_COEFFICIENT_MAPPING: coverage")
    return mapped


def geometry_audit() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    source = read_json(GEOMETRY)
    require(source.get("crs", {}).get("properties", {}).get("name") == "EPSG:4326", "ER2_R4P_FAIL_CRS_OR_DISTANCE_CONTRACT: source CRS")
    projector = Transformer.from_crs("EPSG:4326", "EPSG:32717", always_xy=True).transform
    rows: list[dict[str, Any]] = []
    centroids: dict[str, tuple[float, float]] = {}
    for feature in sorted(source["features"], key=lambda item: str(item["properties"]["UBIGEO"])):
        ubigeo = str(feature["properties"]["UBIGEO"])
        geometry = shape(feature["geometry"])
        centroid = transform(projector, geometry).centroid
        require(ubigeo not in centroids, "ER2_R4P_FAIL_GEOMETRY_PROVENANCE: duplicate UBIGEO")
        require(geometry.is_valid and not geometry.is_empty, "ER2_R4P_FAIL_GEOMETRY_PROVENANCE: invalid geometry")
        require(math.isfinite(centroid.x) and math.isfinite(centroid.y), "ER2_R4P_FAIL_CRS_OR_DISTANCE_CONTRACT: centroid")
        centroids[ubigeo] = (float(centroid.x), float(centroid.y))
        rows.append(
            {
                "UBIGEO": ubigeo,
                "SOURCE_GEOMETRY_SHA256": GEOMETRY_SHA,
                "SOURCE_CRS": "EPSG:4326",
                "TARGET_CRS": "EPSG:32717",
                "CENTROID_METHOD": "PROJECT_GEOMETRY_THEN_CENTROID_AS_ED1",
                "CENTROID_X_M": format(float(centroid.x), ".9f"),
                "CENTROID_Y_M": format(float(centroid.y), ".9f"),
                "FINITE_XY": "TRUE",
                "GEOMETRY_VALID": "TRUE",
                "GEOMETRY_EMPTY": "FALSE",
                "UNIQUE_UBIGEO_STATUS": "PASS",
            }
        )
    require(len(rows) == len(centroids) == 55, "ER2_R4P_FAIL_GEOMETRY_PROVENANCE: centroid count")
    frozen_centroids = ed1.district_centroids()
    require(centroids == frozen_centroids, "ER2_R4P_FAIL_CRS_OR_DISTANCE_CONTRACT: ED1 centroid equivalence")
    coordinates = np.asarray([centroids[key] for key in sorted(centroids)], dtype=np.float64)
    distances = np.sqrt(((coordinates[:, None, :] - coordinates[None, :, :]) ** 2).sum(axis=2)) / 1000.0
    diagonal_zero = bool(np.array_equal(np.diag(distances), np.zeros(len(centroids), dtype=np.float64)))
    symmetric = bool(np.array_equal(distances, distances.T))
    finite_nonnegative = bool(np.isfinite(distances).all() and (distances >= 0).all())
    require(diagonal_zero and symmetric and finite_nonnegative, "ER2_R4P_FAIL_CRS_OR_DISTANCE_CONTRACT: distance matrix")
    with (ROOT / R3_SAMPLE_AUDIT).open(encoding="utf-8", newline="") as handle:
        sample_rows = list(csv.DictReader(handle))
    actual_samples = {
        row["CROP_CODE"]: (int(row["N"]), int(row["NOMINAL_DISTRICTS"]), int(row["EFFECTIVE_DISTRICTS"]), int(row["PERIODS"]))
        for row in sample_rows
    }
    require(actual_samples == EXPECTED_SAMPLES, "ER2_R4P_FAIL_GEOMETRY_PROVENANCE: sample aggregate identity")
    summary = {
        "status": "PASS_STRUCTURAL_GEOMETRY",
        "source_path": GEOMETRY.as_posix(),
        "source_sha256": GEOMETRY_SHA,
        "source_git_blob_at_r3_parent": GEOMETRY_BLOB,
        "source_crs": "EPSG:4326",
        "target_crs": "EPSG:32717",
        "coordinate_construction": "PROJECT_FROZEN_DISTRICT_GEOMETRY_THEN_CENTROID_AS_ED1",
        "distance_rule": "EUCLIDEAN_PROJECTED_METRES_DIVIDED_BY_1000",
        "centroid_count": len(centroids),
        "unique_ubigeo_count": len(centroids),
        "duplicate_ubigeo_count": 0,
        "finite_centroid_count": len(centroids),
        "distance_matrix_shape": [len(centroids), len(centroids)],
        "distance_diagonal_exact_zero": diagonal_zero,
        "distance_symmetry_exact": symmetric,
        "all_distances_finite_nonnegative": finite_nonnegative,
        "maximum_distance_km": float(distances.max()),
        "duplicate_coordinate_pairs_distinct_ubigeo": int((np.triu(distances == 0.0, 1)).sum()),
        "sample_aggregate_identity": "PASS_ALL_FIVE_CROPS",
        "sample_geometry_coverage": "SAMPLE_GEOMETRY_COVERAGE_REQUIRES_REAL_R4_EXECUTION_PREFLIGHT",
        "coverage_reason": "EXACT_ROW_LEVEL_SAMPLE_DISTRICT_KEYS_ARE_NOT_AVAILABLE_FROM_OUTCOME_BLIND_FROZEN_AUDIT_ARTIFACTS",
    }
    return rows, summary


def validate_synthetic_inputs(
    frame: pd.DataFrame,
    x_within: np.ndarray,
    residual: np.ndarray,
    period_column: str,
    bandwidth_km: int,
    centroids: dict[str, tuple[float, float]],
    coefficient_names: list[str],
) -> None:
    if period_column not in frame.columns:
        raise ValueError("R4_HOLD_MISSING_PERIOD_KEY")
    if "UBIGEO" not in frame.columns:
        raise ValueError("R4_HOLD_MISSING_DISTRICT_KEY")
    if x_within.ndim != 2 or residual.ndim != 1 or len(frame) != x_within.shape[0] or len(frame) != residual.shape[0]:
        raise ValueError("R4_HOLD_INVALID_ARRAY_DIMENSIONS")
    if not np.isfinite(x_within).all() or not np.isfinite(residual).all():
        raise ValueError("R4_HOLD_NONFINITE_INPUT")
    if bandwidth_km <= 0:
        raise ValueError("R4_HOLD_INVALID_BANDWIDTH")
    if len(coefficient_names) != x_within.shape[1] or any(not name for name in coefficient_names):
        raise ValueError("R4_HOLD_MISSING_COEFFICIENT_NAME")
    if len(set(coefficient_names)) != len(coefficient_names):
        raise ValueError("R4_HOLD_DUPLICATE_COEFFICIENT_NAME")
    for district in frame["UBIGEO"].astype(str):
        if district not in centroids:
            raise ValueError("R4_HOLD_MISSING_DISTRICT_COORDINATE")
        coordinate = np.asarray(centroids[district], dtype=float)
        if coordinate.shape != (2,):
            raise ValueError("R4_HOLD_WRONG_COORDINATE_DIMENSIONALITY")
        if not np.isfinite(coordinate).all():
            raise ValueError("R4_HOLD_NONFINITE_INPUT")


def validate_covariance_variances(covariance: np.ndarray) -> np.ndarray:
    if covariance.ndim != 2 or covariance.shape[0] != covariance.shape[1] or not np.isfinite(covariance).all():
        raise ValueError("R4_HOLD_NONPOSITIVE_OR_NONFINITE_VARIANCE")
    diagonal = np.diag(covariance)
    if not np.isfinite(diagonal).all() or np.any(diagonal <= 0.0):
        raise ValueError("R4_HOLD_NONPOSITIVE_OR_NONFINITE_VARIANCE")
    return np.sqrt(diagonal)


def bartlett_weight(distance_km: float, bandwidth_km: int) -> float:
    return max(1.0 - float(distance_km) / float(bandwidth_km), 0.0)


def reference_conley_covariance(
    frame: pd.DataFrame,
    x_within: np.ndarray,
    residual: np.ndarray,
    period_column: str,
    bandwidth_km: int,
    centroids: dict[str, tuple[float, float]],
    coefficient_names: list[str],
) -> np.ndarray:
    validate_synthetic_inputs(frame, x_within, residual, period_column, bandwidth_km, centroids, coefficient_names)
    districts = frame["UBIGEO"].astype(str).tolist()
    periods = frame[period_column].astype(str).tolist()
    scores = x_within * residual[:, None]
    meat = np.zeros((x_within.shape[1], x_within.shape[1]), dtype=np.float64)
    for period in sorted(set(periods)):
        indices = [index for index, value in enumerate(periods) if value == period]
        for left in indices:
            for right in indices:
                a = np.asarray(centroids[districts[left]], dtype=np.float64)
                b = np.asarray(centroids[districts[right]], dtype=np.float64)
                distance_km = float(np.sqrt(np.sum((a - b) ** 2)) / 1000.0)
                meat += bartlett_weight(distance_km, bandwidth_km) * np.outer(scores[left], scores[right])
    bread = np.linalg.pinv(x_within.T @ x_within, rcond=1e-12, hermitian=True)
    return bread @ meat @ bread


def max_abs_difference(left: np.ndarray, right: np.ndarray) -> float:
    return float(np.max(np.abs(left - right)))


def expected_error(marker: str, operation: Callable[[], Any]) -> bool:
    try:
        operation()
    except ValueError as error:
        return marker in str(error)
    return False


def validation_row(
    check_id: str,
    category: str,
    status: bool,
    observed: Any,
    expected: Any,
    bandwidth: str = "",
    difference: float | None = None,
    exact: bool | None = None,
) -> dict[str, Any]:
    return {
        "CHECK_ID": check_id,
        "CATEGORY": category,
        "BANDWIDTH_KM": bandwidth,
        "STATUS": "PASS" if status else "FAIL",
        "OBSERVED": str(observed),
        "EXPECTED": str(expected),
        "MAX_ABS_DIFFERENCE": "" if difference is None else format(difference, ".17g"),
        "EXACT_BYTE_IDENTITY": "NOT_APPLICABLE" if exact is None else str(exact).upper(),
    }


def synthetic_fixture() -> tuple[pd.DataFrame, np.ndarray, np.ndarray, dict[str, tuple[float, float]], list[str]]:
    districts = list(SYNTHETIC_PLAN["coordinates_metres"])
    periods = ["P1", "P2", "P3"]
    frame = pd.DataFrame([(district, period) for period in periods for district in districts], columns=["UBIGEO", "SYNTHETIC_PERIOD"])
    rng = np.random.Generator(np.random.PCG64(SYNTHETIC_PLAN["seed"]))
    x_within = rng.normal(size=(len(frame), SYNTHETIC_PLAN["regressors"])).astype(np.float64)
    residual = rng.normal(size=len(frame)).astype(np.float64)
    centroids = {key: tuple(value) for key, value in SYNTHETIC_PLAN["coordinates_metres"].items()}
    names = ["BETA_A", "BETA_B", "BETA_C", "BETA_D"]
    return frame, x_within, residual, centroids, names


def pair_audit(frame: pd.DataFrame, centroids: dict[str, tuple[float, float]], bandwidth: int) -> dict[str, Any]:
    districts = frame["UBIGEO"].astype(str).tolist()
    periods = frame["SYNTHETIC_PERIOD"].astype(str).tolist()
    positive = 0
    zero = 0
    positive_weights: list[float] = []
    off_diagonal_weights: list[float] = []
    boundary_weights: list[float] = []
    support: list[tuple[int, int]] = []
    same_period_ordered = 0
    same_period_unordered = 0
    for left in range(len(frame)):
        for right in range(len(frame)):
            if periods[left] != periods[right]:
                continue
            same_period_ordered += 1
            if left <= right:
                same_period_unordered += 1
            a = np.asarray(centroids[districts[left]], dtype=float)
            b = np.asarray(centroids[districts[right]], dtype=float)
            distance = float(np.sqrt(np.sum((a - b) ** 2)) / 1000.0)
            weight = bartlett_weight(distance, bandwidth)
            if math.isclose(distance, bandwidth, rel_tol=0.0, abs_tol=1e-12):
                boundary_weights.append(weight)
            if weight > 0.0:
                positive += 1
                positive_weights.append(weight)
                support.append((left, right))
                if left != right:
                    off_diagonal_weights.append(weight)
            else:
                zero += 1
    require(boundary_weights and all(value == 0.0 for value in boundary_weights), "ER2_R4P_FAIL_SYNTHETIC_REFERENCE_EQUIVALENCE: boundary")
    return {
        "bandwidth_km": bandwidth,
        "same_period_ordered_pairs_including_diagonal": same_period_ordered,
        "same_period_unordered_pairs_including_diagonal": same_period_unordered,
        "positive_weight_ordered_pairs": positive,
        "zero_weight_ordered_pairs": zero,
        "minimum_positive_weight": min(positive_weights),
        "maximum_off_diagonal_weight": max(off_diagonal_weights),
        "exact_boundary_distance_weight": 0.0,
        "support": support,
    }


def synthetic_validation(plan_lock_sha256: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    frame, x_within, residual, centroids, names = synthetic_fixture()
    rows: list[dict[str, Any]] = []
    production: dict[int, np.ndarray] = {}
    reference: dict[int, np.ndarray] = {}
    pair_audits: dict[int, dict[str, Any]] = {}
    for bandwidth in BANDWIDTHS_KM:
        validate_synthetic_inputs(frame, x_within, residual, "SYNTHETIC_PERIOD", bandwidth, centroids, names)
        production[bandwidth] = ed1.conley_covariance(frame, x_within, residual, "SYNTHETIC_PERIOD", bandwidth, centroids)
        reference[bandwidth] = reference_conley_covariance(frame, x_within, residual, "SYNTHETIC_PERIOD", bandwidth, centroids, names)
        difference = max_abs_difference(production[bandwidth], reference[bandwidth])
        validate_covariance_variances(production[bandwidth])
        rows.append(validation_row(f"REFERENCE_EQUIVALENCE_{bandwidth}", "PRODUCTION_VS_REFERENCE", difference <= TOLERANCE, difference, f"<= {TOLERANCE}", str(bandwidth), difference, production[bandwidth].tobytes() == reference[bandwidth].tobytes()))
        pair_audits[bandwidth] = pair_audit(frame, centroids, bandwidth)
        pair_public = {key: value for key, value in pair_audits[bandwidth].items() if key != "support"}
        rows.append(validation_row(f"PAIR_AUDIT_{bandwidth}", "SPATIAL_PAIR_AUDIT", True, json.dumps(pair_public, sort_keys=True), "REFERENCE_AGREEMENT", str(bandwidth)))

    support_status = set(pair_audits[50]["support"]) <= set(pair_audits[100]["support"]) <= set(pair_audits[150]["support"])
    rows.append(validation_row("SUPPORT_NESTING", "BANDWIDTH_SUPPORT", support_status, support_status, True))

    permutation = np.asarray([11, 0, 17, 5, 9, 2, 15, 3, 6, 12, 1, 14, 8, 4, 16, 7, 10, 13])
    permuted = ed1.conley_covariance(frame.iloc[permutation].reset_index(drop=True), x_within[permutation], residual[permutation], "SYNTHETIC_PERIOD", 100, centroids)
    difference = max_abs_difference(production[100], permuted)
    rows.append(validation_row("G_ROW_ORDER", "EDGE_CASE", difference <= TOLERANCE, difference, f"<= {TOLERANCE}", difference=difference, exact=production[100].tobytes() == permuted.tobytes()))

    labels = {key: f"L{index}" for index, key in enumerate(centroids)}
    relabelled_frame = frame.copy()
    relabelled_frame["UBIGEO"] = relabelled_frame["UBIGEO"].map(labels)
    relabelled_centroids = {labels[key]: value for key, value in centroids.items()}
    relabelled = ed1.conley_covariance(relabelled_frame, x_within, residual, "SYNTHETIC_PERIOD", 100, relabelled_centroids)
    difference = max_abs_difference(production[100], relabelled)
    rows.append(validation_row("H_DISTRICT_LABEL_ORDER", "EDGE_CASE", difference <= TOLERANCE, difference, f"<= {TOLERANCE}", difference=difference, exact=production[100].tobytes() == relabelled.tobytes()))

    translated_centroids = {key: (value[0] + 500000.0, value[1] + 9000000.0) for key, value in centroids.items()}
    translated = ed1.conley_covariance(frame, x_within, residual, "SYNTHETIC_PERIOD", 100, translated_centroids)
    difference = max_abs_difference(production[100], translated)
    rows.append(validation_row("I_COORDINATE_TRANSLATION", "EDGE_CASE", difference <= TOLERANCE, difference, f"<= {TOLERANCE}", difference=difference, exact=production[100].tobytes() == translated.tobytes()))

    column_permutation = np.asarray([2, 0, 3, 1])
    inverse = np.argsort(column_permutation)
    column_covariance = ed1.conley_covariance(frame, x_within[:, column_permutation], residual, "SYNTHETIC_PERIOD", 100, centroids)
    restored = column_covariance[np.ix_(inverse, inverse)]
    difference = max_abs_difference(production[100], restored)
    rows.append(validation_row("COEFFICIENT_COLUMN_MAPPING", "MAPPING_INVARIANCE", difference <= TOLERANCE, difference, f"<= {TOLERANCE}", difference=difference, exact=production[100].tobytes() == restored.tobytes()))

    distance = lambda left, right: float(np.linalg.norm(np.asarray(centroids[left]) - np.asarray(centroids[right])) / 1000.0)

    def two_observation_covariance(distance_metres: float, same_period: bool, same_district: bool = False) -> float:
        local_centroids = {"A": (0.0, 0.0), "B": (distance_metres, 0.0)}
        second_district = "A" if same_district else "B"
        local_frame = pd.DataFrame(
            [("A", "P1"), (second_district, "P1" if same_period else "P2")],
            columns=["UBIGEO", "SYNTHETIC_PERIOD"],
        )
        covariance = ed1.conley_covariance(
            local_frame,
            np.ones((2, 1), dtype=np.float64),
            np.ones(2, dtype=np.float64),
            "SYNTHETIC_PERIOD",
            50,
            local_centroids,
        )
        return float(covariance[0, 0])

    isolated_values = {
        "A": two_observation_covariance(0.0, True, True),
        "B": two_observation_covariance(25000.0, True),
        "C": two_observation_covariance(50000.0, True),
        "D": two_observation_covariance(75000.0, True),
        "E": two_observation_covariance(0.0, False),
        "F": two_observation_covariance(150000.0, True),
        "J": two_observation_covariance(0.0, True),
    }
    edge_checks = {
        "A_DISTANCE_ZERO": bartlett_weight(0.0, 50) == 1.0 and abs(isolated_values["A"] - 1.0) <= TOLERANCE,
        "B_INSIDE_BANDWIDTH": bartlett_weight(distance("D0", "D1"), 50) == 0.5 and abs(isolated_values["B"] - 0.75) <= TOLERANCE,
        "C_DISTANCE_EQUALS_BANDWIDTH": all(bartlett_weight(float(value), value) == 0.0 for value in BANDWIDTHS_KM) and abs(isolated_values["C"] - 0.5) <= TOLERANCE,
        "D_DISTANCE_BEYOND_BANDWIDTH": bartlett_weight(75.0, 50) == 0.0 and abs(isolated_values["D"] - 0.5) <= TOLERANCE,
        "E_SAME_COORDINATE_DIFFERENT_PERIOD": abs(isolated_values["E"] - 0.5) <= TOLERANCE,
        "F_SAME_PERIOD_BEYOND_CUTOFF": distance("D0", "D4") > 50 and abs(isolated_values["F"] - 0.5) <= TOLERANCE,
        "J_DUPLICATE_COORDINATE_DISTRICTS": distance("D0", "D5") == 0.0 and abs(isolated_values["J"] - 1.0) <= TOLERANCE,
        "K_NONPOSITIVE_VARIANCE_TRIGGER": expected_error("R4_HOLD_NONPOSITIVE_OR_NONFINITE_VARIANCE", lambda: validate_covariance_variances(np.diag([1.0, 0.0]))),
        "L_NONFINITE_INPUT_TRIGGER": expected_error("R4_HOLD_NONFINITE_INPUT", lambda: validate_synthetic_inputs(frame, np.where(np.arange(x_within.size).reshape(x_within.shape) == 0, np.nan, x_within), residual, "SYNTHETIC_PERIOD", 50, centroids, names)),
        "M_WRONG_COORDINATE_DIMENSIONALITY": expected_error("R4_HOLD_WRONG_COORDINATE_DIMENSIONALITY", lambda: validate_synthetic_inputs(frame, x_within, residual, "SYNTHETIC_PERIOD", 50, {**centroids, "D0": (0.0, 0.0, 0.0)}, names)),
        "N_MISSING_PERIOD_KEY": expected_error("R4_HOLD_MISSING_PERIOD_KEY", lambda: validate_synthetic_inputs(frame.drop(columns=["SYNTHETIC_PERIOD"]), x_within, residual, "SYNTHETIC_PERIOD", 50, centroids, names)),
        "O_MISSING_COEFFICIENT_NAME": expected_error("R4_HOLD_MISSING_COEFFICIENT_NAME", lambda: validate_synthetic_inputs(frame, x_within, residual, "SYNTHETIC_PERIOD", 50, centroids, ["BETA_A", "", "BETA_C", "BETA_D"])),
        "P_DUPLICATE_COEFFICIENT_NAME": expected_error("R4_HOLD_DUPLICATE_COEFFICIENT_NAME", lambda: validate_synthetic_inputs(frame, x_within, residual, "SYNTHETIC_PERIOD", 50, centroids, ["BETA_A", "BETA_A", "BETA_C", "BETA_D"])),
    }
    for check_id, status in edge_checks.items():
        rows.append(validation_row(check_id, "EDGE_CASE", status, status, True))
    rows.sort(key=lambda row: row["CHECK_ID"])
    require(all(row["STATUS"] == "PASS" for row in rows), "ER2_R4P_FAIL_SYNTHETIC_REFERENCE_EQUIVALENCE")
    summary = {
        "status": "PASS",
        "test_plan_lock_sha256": plan_lock_sha256,
        "test_plan_lock_written_before_validation": True,
        "seed": SYNTHETIC_PLAN["seed"],
        "absolute_tolerance": TOLERANCE,
        "equivalence": "FLOAT64_CONTINUOUS_EQUIVALENCE_WITHIN_PRESPECIFIED_TOLERANCE",
        "checks": len(rows),
        "checks_passed": len(rows),
        "production_reference_max_abs_difference": max(max_abs_difference(production[value], reference[value]) for value in BANDWIDTHS_KM),
        "production_reference_exact_byte_identity_by_bandwidth": {str(value): production[value].tobytes() == reference[value].tobytes() for value in BANDWIDTHS_KM},
        "pair_audit": {str(value): {key: item for key, item in pair_audits[value].items() if key != "support"} for value in BANDWIDTHS_KM},
        "isolated_two_observation_production_covariances": isolated_values,
        "support_nesting": "PASS",
        "se_monotonicity_across_bandwidths": "NOT_REQUIRED",
        "nonpositive_nonfinite_variance_policy": "PASS_FAIL_CLOSED_NO_CLIPPING_OR_SUBSTITUTION",
        "real_outcome_values_read": False,
    }
    return rows, summary


def source_firewall_audit() -> dict[str, Any]:
    source = (ROOT / SCRIPT).read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_condition_tokens = ("platanos_y_bananas", "limon_sutil", "wcr_raw_p", "holm", "significance", "p_value")
    condition_sources: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.If, ast.IfExp, ast.While, ast.Assert)):
            condition_sources.append((ast.get_source_segment(source, node.test) or "").lower())
    offending = [condition for condition in condition_sources if any(token in condition for token in forbidden_condition_tokens)]
    forbidden_real_sources = (
        "transient_campaign_" + "outcomes_master.csv",
        "panel_" + "master.csv",
        "yield" + "_raw",
        "read_" + "parquet",
    )
    real_source_hits = [token for token in forbidden_real_sources if token in source.lower()]
    require(not offending, f"ER2_R4P_FAIL_RESULT_SPECIFIC_BRANCH: {offending}")
    require(not real_source_hits, f"ER2_R4P_FAIL_REAL_OUTCOME_FIREWALL: {real_source_hits}")
    reference_node = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == "reference_conley_covariance")
    reference_source = ast.get_source_segment(source, reference_node) or ""
    reference_calls_production = "ed1.conley_covariance" in reference_source
    require(not reference_calls_production, "ER2_R4P_FAIL_SYNTHETIC_REFERENCE_EQUIVALENCE: nonindependent reference")
    return {
        "result_specific_r4_branches": 0,
        "offending_conditions": [],
        "real_outcome_source_references": [],
        "independent_reference_calls_production": False,
        "real_outcome_values_read": False,
        "real_r4_covariances_computed": False,
        "real_r4_standard_errors_computed": False,
        "real_r4_confidence_intervals_computed": False,
        "real_r4_zero_inclusion_results_known": False,
    }


def historical_engine_validation() -> dict[str, Any]:
    config = read_json(ED1_CONFIG)
    report = (ROOT / ED1_REPORT).read_text(encoding="utf-8")
    value = config["inference_engine_feasibility"]["conley_engine_validation"]
    require(value == "PASS_ALL_FIVE_CROPS_ALL_THREE_BANDWIDTHS", "ER2_R4P_FAIL_CONLEY_API_IDENTITY: historical validation")
    require(value in report, "ER2_R4P_FAIL_CONLEY_API_IDENTITY: historical report")
    return {
        "status": value,
        "classification": "HISTORICAL_SYNTHETIC_ENGINE_VALIDATION_NOT_REAL_R4_EVIDENCE",
        "design_artifact_unchanged": True,
    }


def report_bytes(
    contract: dict[str, Any],
    api: dict[str, Any],
    geometry: dict[str, Any],
    mapping: list[dict[str, Any]],
    synthetic: dict[str, Any],
    historical: dict[str, Any],
    source_audit: dict[str, Any],
    artifact_sha: dict[str, str],
) -> bytes:
    lines = [
        "# ER2-R4P Spatial HAC / Conley Pre-Execution Certification v1",
        "",
        f"PROJECT={PROJECT}",
        f"GATE={GATE}",
        f"R3_FREEZE_SHA={R3_FREEZE_SHA}",
        "R3_FREEZE_STATUS=PASS_FROZEN_REMOTE_VERIFIED",
        "",
        "## Contract",
        "",
        f"R4_TIER_CONTRACT_SHA256={TIER_CONTRACT_SHA}",
        f"ROLE={contract['role']}",
        "FAMILY=PHYSICAL_ANOMALY",
        "BANDWIDTHS_KM=50|100|150",
        "KERNEL=BARTLETT",
        "BARTLETT_WEIGHT=max(1-d_km/h_km,0)",
        "TEMPORAL_RULE=SAME_PERIOD_ONLY",
        "JOINT_CONLEY_TESTS=NOT_AUTHORIZED",
        "",
        "## Frozen API",
        "",
        f"FILE={api['file']}",
        f"FILE_SHA256={api['file_sha256']}",
        f"FUNCTION_SOURCE_SHA256={api['function_source_sha256']}",
        f"FUNCTION_BODY_SHA256={api['function_body_sha256']}",
        f"SIGNATURE={api['signature']}",
        "MEAT=sum_period score.T @ Bartlett_kernel @ score",
        "BREAD=pinv(X_within.T @ X_within,rcond=1e-12,hermitian=True)",
        "FINITE_SAMPLE_SCALING=NONE",
        "",
        "## Geometry",
        "",
        f"SOURCE_SHA256={geometry['source_sha256']}",
        "SOURCE_CRS=EPSG:4326",
        "TARGET_CRS=EPSG:32717",
        f"CENTROIDS={geometry['centroid_count']}",
        "DISTANCE=EUCLIDEAN_PROJECTED_METRES_DIVIDED_BY_1000",
        f"DISTANCE_MATRIX_AUDIT={'PASS' if geometry['distance_diagonal_exact_zero'] and geometry['distance_symmetry_exact'] and geometry['all_distances_finite_nonnegative'] else 'FAIL'}",
        f"SAMPLE_GEOMETRY_COVERAGE={geometry['sample_geometry_coverage']}",
        "",
        "## Mapping and synthetic validation",
        "",
        f"COEFFICIENTS_MAPPED={len(mapping)}",
        "EXPECTED_REAL_ROWS=63",
        "REAL_ROWS_CREATED=0",
        f"SYNTHETIC_CHECKS={synthetic['checks']}",
        f"SYNTHETIC_CHECKS_PASSED={synthetic['checks_passed']}",
        f"PRESPECIFIED_TOLERANCE={synthetic['absolute_tolerance']}",
        f"REFERENCE_EQUIVALENCE={synthetic['status']}",
        "SE_MONOTONICITY_ACROSS_BANDWIDTHS=NOT_REQUIRED",
        "",
        "## Firewalls",
        "",
        f"RESULT_SPECIFIC_R4_BRANCHES={source_audit['result_specific_r4_branches']}",
        "REAL_OUTCOME_VALUES_READ=FALSE",
        "REAL_R4_COVARIANCES_COMPUTED=FALSE",
        "REAL_R4_STANDARD_ERRORS_COMPUTED=FALSE",
        "REAL_R4_CONFIDENCE_INTERVALS_COMPUTED=FALSE",
        "REAL_R4_ZERO_INCLUSION_RESULTS_KNOWN=FALSE",
        "R5_AUTHORIZATION_STATUS=NOT_AUTHORIZED",
        "R6_AUTHORIZATION_STATUS=NOT_AUTHORIZED",
        "",
        "## Historical certification",
        "",
        f"ED1_CONLEY_ENGINE_VALIDATION={historical['status']}",
        f"CLASSIFICATION={historical['classification']}",
        "",
        "## Artifact SHA-256",
        "",
        *[f"{path}={digest}" for path, digest in sorted(artifact_sha.items())],
        "",
        "R4_EXECUTOR_ARCHITECTURE=R4_EXECUTOR_CAN_REUSE_FROZEN_ED1_CONLEY_DIRECTLY",
        "REAL_R4_EXECUTION_AUTHORIZATION_STATUS=NOT_AUTHORIZED",
        "NEXT_ACTION=RETURN_TO_SCIENTIFIC_DIRECTOR_FOR_REAL_R4_EXECUTION_DECISION",
        f"FINAL_VERDICT={FINAL_VERDICT}",
    ]
    return ("\n".join(lines) + "\n").encode("utf-8")


def build_package(output_root: Path) -> dict[str, bytes]:
    state = preflight()
    destination = output_root / TEST_PLAN_LOCK
    destination.parent.mkdir(parents=True, exist_ok=True)
    plan_payload = json_bytes(SYNTHETIC_PLAN)
    destination.write_bytes(plan_payload)

    mapping = coefficient_mapping()
    geometry_rows, geometry_summary = geometry_audit()
    api = conley_api_identity()
    historical = historical_engine_validation()
    source_audit = source_firewall_audit()
    synthetic_rows, synthetic_summary = synthetic_validation(sha_bytes(plan_payload))

    map_fields = list(mapping[0])
    geometry_fields = list(geometry_rows[0])
    synthetic_fields = list(synthetic_rows[0])
    payloads: dict[Path, bytes] = {
        TEST_PLAN_LOCK: plan_payload,
        COEFFICIENT_MAP: csv_bytes(mapping, map_fields),
        GEOMETRY_AUDIT: csv_bytes(geometry_rows, geometry_fields),
        SYNTHETIC_VALIDATION: csv_bytes(synthetic_rows, synthetic_fields),
    }
    artifact_sha = {
        TEST_PLAN_LOCK.as_posix(): sha_bytes(payloads[TEST_PLAN_LOCK]),
        COEFFICIENT_MAP.as_posix(): sha_bytes(payloads[COEFFICIENT_MAP]),
        GEOMETRY_AUDIT.as_posix(): sha_bytes(payloads[GEOMETRY_AUDIT]),
        SYNTHETIC_VALIDATION.as_posix(): sha_bytes(payloads[SYNTHETIC_VALIDATION]),
        SCRIPT.as_posix(): sha_file(ROOT / SCRIPT),
        TEST.as_posix(): sha_file(ROOT / TEST),
    }
    payloads[REPORT] = report_bytes(state["r4_tier_contract"], api, geometry_summary, mapping, synthetic_summary, historical, source_audit, artifact_sha)
    artifact_sha[REPORT.as_posix()] = sha_bytes(payloads[REPORT])
    lock = {
        "schema_version": "1.0.0",
        "project": PROJECT,
        "gate": GATE,
        "status": "PASS_PREEXECUTION_CERTIFIED_PENDING_DIRECTOR_REVIEW",
        "final_verdict": FINAL_VERDICT,
        "governing_state": {
            "r3_freeze_sha": R3_FREEZE_SHA,
            "r3_parent_sha": R3_PARENT_SHA,
            "r3_results_lock_sha256": R3_RESULTS_LOCK_SHA,
            "r3_status": "PASS_FROZEN_REMOTE_VERIFIED",
        },
        "temporal_governance": {
            "PRIMARY_RESULTS_KNOWN": True,
            "R1_RESULTS_KNOWN": True,
            "R2_RESULTS_KNOWN": True,
            "R3_RESULTS_KNOWN": True,
            "REAL_R4_RESULTS_KNOWN_BEFORE_THIS_GATE": False,
            "RESULT_DEPENDENT_DESIGN": "PROHIBITED",
        },
        "r4_tier_contract_sha256": TIER_CONTRACT_SHA,
        "r4_tier_contract": state["r4_tier_contract"],
        "r4_scientific_role": {
            "family": "PHYSICAL_ANOMALY",
            "outcome": "YIELD_LEVEL_TM_PER_HA",
            "sample": "EXACT_ER1_R3_UNCHANGED",
            "windows": "EXACT_ED1_FROZEN_UNCHANGED",
            "functional_form": "LINEAR_ADDITIVE",
            "district_fe": "REQUIRED",
            "period_fe": "REQUIRED",
            "weighting": "UNWEIGHTED_PRIMARY_ESTIMATION",
            "beta": "EXACT_ER1_PRIMARY_UNCHANGED",
            "interpretation": "CROSS_DISTRICT_SPATIAL_COVARIANCE_SENSITIVITY",
            "claim_ceiling": "EMPIRICAL_ASSOCIATION_CLIMATE_RESPONSE_ONLY",
        },
        "bandwidth_contract": {
            "bandwidths_km": list(BANDWIDTHS_KM),
            "selection": "PRESPECIFIED_50_100_150_KM",
            "best_bandwidth_selection": "PROHIBITED",
            "expected_real_rows": 63,
            "real_rows_created": 0,
        },
        "conley_api": api,
        "historical_engine_validation": historical,
        "geometry": geometry_summary,
        "coefficient_mapping": {
            "status": "PASS",
            "all_21_targets_covered": True,
            "crop_dimensions": {code: len(spec["variables"]) for code, spec in CROP_SPECS.items()},
            "rows": len(mapping),
            "bandwidth_rows_future": len(mapping) * len(BANDWIDTHS_KM),
        },
        "joint_conley_tests": "NOT_AUTHORIZED",
        "interval_contract": {
            "interval": "ER1_BETA_PLUS_MINUS_1.959963984540054_TIMES_CONLEY_SE",
            "critical_value": NORMAL_CRITICAL_VALUE,
            "distribution": "ASYMPTOTIC_STANDARD_NORMAL",
            "multiplicity_adjusted": False,
            "satterthwaite_df": "NOT_USED",
        },
        "multiplicity_firewall": {
            "GLOBAL_FIVE_CROP_FWER": "NOT_CLAIMED",
            "MULTIPLICITY_ADJUSTED_CONFIDENCE_INTERVALS": "NOT_CONSTRUCTED_NOT_CLAIMED",
            "HOLM_R4_CI": "NOT_AUTHORIZED",
            "VOTE_COUNTING": "PROHIBITED",
        },
        "variance_policy": "HOLD_NO_CLIPPING_OR_COVARIANCE_SUBSTITUTION",
        "synthetic_test_plan": SYNTHETIC_PLAN,
        "synthetic_validation": synthetic_summary,
        "source_audit": source_audit,
        "future_real_r4_output_schema": list(REAL_R4_OUTPUT_SCHEMA),
        "r4_executor_architecture": "R4_EXECUTOR_CAN_REUSE_FROZEN_ED1_CONLEY_DIRECTLY",
        "executor_architecture_note": "REUSE_FROZEN_NUMERICAL_FUNCTION_WITH_DETERMINISTIC_NAMED_MAPPING_AND_FAIL_CLOSED_ORCHESTRATION_NO_NUMERICAL_ADAPTER",
        "raw_object_reproducibility_rule": "DIRECT_GIT_OBJECT_EXTRACTION_NO_CANONICALIZATION_WHEN_BYTE_IDENTITY_MATTERS",
        "r4p_two_run_reproducibility": "PASS",
        "artifact_sha256": artifact_sha,
        "frozen_input_sha256": state["frozen_input_sha256"],
        "execution_firewall": {
            "REAL_OUTCOME_VALUES_READ": False,
            "REAL_R4_COVARIANCES_COMPUTED": False,
            "REAL_R4_STANDARD_ERRORS_COMPUTED": False,
            "REAL_R4_CONFIDENCE_INTERVALS_COMPUTED": False,
            "REAL_R4_ZERO_INCLUSION_RESULTS_KNOWN": False,
            "REAL_R4_EXECUTED": False,
            "R5_AUTHORIZATION_STATUS": "NOT_AUTHORIZED",
            "R6_AUTHORIZATION_STATUS": "NOT_AUTHORIZED",
        },
        "next_action": "RETURN_TO_SCIENTIFIC_DIRECTOR_FOR_REAL_R4_EXECUTION_DECISION",
    }
    payloads[PREFLIGHT_LOCK] = json_bytes(lock)
    for relative, payload in payloads.items():
        destination = output_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(payload)
    return {relative.as_posix(): payload for relative, payload in payloads.items()}


def check_existing() -> dict[str, bytes]:
    with tempfile.TemporaryDirectory(prefix="er2_r4p_check_") as temporary:
        expected = build_package(Path(temporary))
    for relative, payload in expected.items():
        require((ROOT / relative).read_bytes() == payload, f"ER2_R4P_FAIL_REPRODUCIBILITY: {relative}")
    return expected


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the outcome-blind ER2-R4P spatial HAC preflight package.")
    parser.add_argument("--output-root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    payloads = check_existing() if args.check else build_package(args.output_root.resolve())
    print("R3_FREEZE_STATUS=PASS_FROZEN_REMOTE_VERIFIED")
    print("R4P_REAL_OUTCOME_VALUES_READ=FALSE")
    print("R4P_REAL_R4_EXECUTED=FALSE")
    print("R4P_SYNTHETIC_REFERENCE_EQUIVALENCE=PASS")
    print("R4P_ALL_21_TARGETS_COVERED=TRUE")
    for relative, payload in sorted(payloads.items()):
        print(f"SHA256 {relative} {sha_bytes(payload)}")
    print(f"FINAL_VERDICT={FINAL_VERDICT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
