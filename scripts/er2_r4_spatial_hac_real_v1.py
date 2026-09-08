from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import io
import json
import math
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
import er2_r4p_spatial_hac_preflight_v1 as r4p  # noqa: E402


PROJECT = "ENSO_EL_NINO_2026_2027_AGRICULTURE_PIURA"
GATE = "ER2_R4_SPATIAL_HAC_CONLEY_REAL_EXECUTION_V1"
FINAL_VERDICT = "ER2_R4_PASS_RESULTS_LOCKED_READY_FOR_DIRECTOR_REVIEW"

R4P_FREEZE_SHA = "652d846f7f13f2557cb830dde390a16bbca9fa2d"
R4P_BRANCH = "phase/er2-r4p-spatial-hac-preflight-v1"
R4P_TAG = "er2-r4p-spatial-hac-preflight-v1-freeze"
R4P_TAG_OBJECT = "1d164fb61a5549f6338ad82df51bb6a556229526"
R4P_LOCK_SHA = "024b2bf87e3707235f52206a3043eb8daad47569731559cf6bbd637efc4750f4"
R4P_TEST_PLAN_LOCK_SHA = "c25f7b5cf3074425735ce82e2483007d45ede254435dce63b618ffbc4e233f50"
R4P_SCRIPT_SHA = "6e53c7f281fc4b27d93f3974d752664892bdf64fb085a596029c70f9452de564"
R3_FREEZE_SHA = "ac99e5adb1077cf0d8a545d0077e6b980b4d8a6d"
R3_RESULTS_LOCK_SHA = "931bb70ecece35b5b5751d031b7d34204252de9e4f5106b420ac9572b3eea6b7"
R4_TIER_CONTRACT_SHA = "02b1ac12ec85231877f539eadb9f288432012cda0bce5ec0ab917b1e6118ab6b"
ER1_NUMERICAL_IDENTITY = "40e0f58269dda309e83a1fa3da17ef4d5dc5523efc72a666f734d0ebacb76b24"
GEOMETRY_SHA = "d966d2a38e80d6575490be32bde2e39b7db66a3c6e99b240e9c21458766d099b"
ED1_IMPLEMENTATION_SHA = "69fb1b1f0a1d7c4ec7791fdfa2d3cfb20d62b4ed0f6348b155155523b6b48195"
CONLEY_SOURCE_SHA = "9a67e58fbcb636273baa6a74ef1e4b74deb94ccb3588121545d7e599513dfc77"
CONLEY_BODY_SHA = "71c27363a0bb95e15f6be07a9f57793cbcfded898ef7b9ccd2c1e72c6f987e2d"

BANDWIDTHS_KM = (50, 100, 150)
NORMAL_CRITICAL_VALUE = 1.959963984540054
MODEL_IDENTITY_TOLERANCE = 1e-10
COVARIANCE_SYMMETRY_TOLERANCE = 1e-12
CROP_ORDER = (
    "14010020000",
    "14010070000",
    "13010210000",
    "13010170102",
    "15010040000",
)

RESULTS = Path("outputs/econometrics/ER2_R4_CONLEY_RESULTS.csv")
COVERAGE = Path("outputs/econometrics/ER2_R4_SAMPLE_GEOMETRY_COVERAGE.csv")
COVARIANCE_AUDIT = Path("outputs/econometrics/ER2_R4_COVARIANCE_AUDIT.csv")
CONCORDANCE = Path("outputs/econometrics/ER2_R4_CONCORDANCE.csv")
REPORT = Path("outputs/econometrics/ER2_R4_REPORT.md")
LOCK = Path("outputs/econometrics/ER2_R4_RESULTS_LOCK.json")
SCRIPT = Path("scripts/er2_r4_spatial_hac_real_v1.py")
TEST = Path("tests/test_er2_r4_spatial_hac_real_v1.py")
OUTPUTS = (RESULTS, COVERAGE, COVARIANCE_AUDIT, CONCORDANCE, REPORT, LOCK)
CANDIDATES = (*OUTPUTS, SCRIPT, TEST)

R4P_LOCK = Path("outputs/econometrics/ER2_R4P_PREFLIGHT_LOCK.json")
R4P_TEST_PLAN_LOCK = Path("outputs/econometrics/ER2_R4P_SYNTHETIC_TEST_PLAN_LOCK.json")
R4P_MAP = Path("outputs/econometrics/ER2_R4P_COEFFICIENT_MAP.csv")
R4P_SCRIPT = Path("scripts/er2_r4p_spatial_hac_preflight_v1.py")
R3_LOCK = Path("outputs/econometrics/ER2_R3_RESULTS_LOCK.json")
R3_SAMPLES = Path("outputs/econometrics/ER2_R3_SAMPLE_AUDIT.csv")
R3_COEFFICIENTS = Path("outputs/econometrics/ER2_R3_WCR_COEFFICIENT_RESULTS.csv")
R2_LOCK = Path("outputs/econometrics/ER2_R2_RESULTS_LOCK.json")
ER1_COEFFICIENTS = Path("outputs/econometrics/ER1_PRIMARY_COEFFICIENTS.csv")
ER1_LOCK = Path("outputs/econometrics/ER1_PRIMARY_RESULTS_LOCK.json")
ED1_SCRIPT = Path("scripts/econometric_design_master_v1.py")
GEOMETRY = Path("data/processed/climate/district_boundaries_piura.geojson")

FROZEN_INPUT_SHA256 = {
    R4P_LOCK: R4P_LOCK_SHA,
    R4P_TEST_PLAN_LOCK: R4P_TEST_PLAN_LOCK_SHA,
    R4P_MAP: "c1a14dbe99ba899a4862d0626796d7950bfcc106bc326483ab44f199abc2527d",
    R4P_SCRIPT: R4P_SCRIPT_SHA,
    R3_LOCK: R3_RESULTS_LOCK_SHA,
    R3_SAMPLES: "6252b0ec924a14ff6b1ea3d3470c4aa2eaa588d91acc5362d9b6d1874a796193",
    R3_COEFFICIENTS: "9d6578588c36681ba996f352d5298c6cd69cfd9cceff8b6ed21f9f87fbb54e15",
    R2_LOCK: "117a3fe5da88f44d31b176495409f6e84189148f1020417f046b0df3dd4c5f6b",
    ER1_COEFFICIENTS: "37fa03a2e860f86277510a5ff3b66ca475fc02d277ea1dd6e18156f719c23480",
    ER1_LOCK: "83eea5e179b5e3504bd1144d744dcdbeddbbdf6a554f4d10ab03b92a30278841",
    ED1_SCRIPT: ED1_IMPLEMENTATION_SHA,
    GEOMETRY: GEOMETRY_SHA,
    Path("data/processed/phenology/transient_econometric_exposures_v1.parquet"):
        "ed90c70a7538318234a0390176b468a66f8a24a99fa59717efe5e8974cf09a67",
    Path("data/processed/phenology/perennial_exposures_long.parquet"):
        "3fde5c7fc7a00f4c6600a18f60935bad213408ffa2ba3bac5828603e46984714",
    er1.TRANSIENT_OUTCOME_REL: er1.TRANSIENT_OUTCOME_SHA,
    er1.PERENNIAL_OUTCOME_REL: er1.PERENNIAL_OUTCOME_SHA,
}

RESULT_FIELDS = (
    "MAP_ORDER", "CROP", "CROP_CODE", "MODEL_ID", "VARIABLE", "WINDOW",
    "BANDWIDTH_KM", "ER1_BETA_REFERENCE", "CONLEY_VARIANCE", "CONLEY_SE", "Z",
    "TWO_SIDED_ASYMPTOTIC_P", "NORMAL_CRITICAL_VALUE", "CI95_LOWER", "CI95_UPPER",
    "CI_ZERO_INCLUDED", "SAMPLE_N", "NOMINAL_DISTRICTS", "PERIODS", "CRS", "KERNEL",
    "SAME_PERIOD_ONLY", "STATUS",
)
COVERAGE_FIELDS = (
    "CROP", "CROP_CODE", "UBIGEO", "IN_FROZEN_SAMPLE", "CENTROID_PRESENT",
    "CENTROID_UNIQUE", "CENTROID_X_M", "CENTROID_Y_M", "FINITE_XY", "COVERAGE_STATUS",
)
COVARIANCE_FIELDS = (
    "CROP", "CROP_CODE", "MODEL_ID", "BANDWIDTH_KM", "N", "DISTRICTS", "PERIODS", "K",
    "MATRIX_FINITE", "MAX_SYMMETRY_DIFFERENCE", "MIN_DIAGONAL_VARIANCE",
    "MAX_DIAGONAL_VARIANCE", "NONPOSITIVE_DIAGONAL_COUNT", "NONFINITE_DIAGONAL_COUNT", "STATUS",
)
CONCORDANCE_FIELDS = (
    "MAP_ORDER", "CROP", "CROP_CODE", "MODEL_ID", "VARIABLE", "WINDOW", "ER1_BETA",
    "ER1_SIGN", "ER1_CR2_P", "ER1_CR2_HOLM_P", "ER1_CR2_HOLM_STATUS", "R3_WCR_P",
    "R3_WCR_HOLM_P", "R3_WCR_HOLM_STATUS", "R4_50_CI_ZERO_INCLUDED",
    "R4_100_CI_ZERO_INCLUDED", "R4_150_CI_ZERO_INCLUDED", "BANDWIDTH_SENSITIVITY",
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
    require(np.isfinite(number), "ER2_R4_HOLD_NONPOSITIVE_OR_NONFINITE_CONLEY_VARIANCE")
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


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def read_json(relative: Path) -> dict[str, Any]:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def read_csv(relative: Path) -> list[dict[str, str]]:
    with (ROOT / relative).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def array_sha(values: Any) -> str:
    return sha_bytes(np.asarray(values, dtype="<f8").tobytes(order="C"))


def key_sha(keys: list[list[str]]) -> str:
    return sha_bytes(compact_json_bytes(keys))


def remote_refs() -> dict[str, str]:
    refs: dict[str, str] = {}
    for line in git("ls-remote", "origin").splitlines():
        object_id, ref = line.split("\t", 1)
        refs[ref] = object_id
    return refs


def preflight() -> dict[str, Any]:
    remote = remote_refs()
    identity = {
        "head": git("rev-parse", "HEAD"),
        "branch": git("branch", "--show-current"),
        "local_branch": git("rev-parse", R4P_BRANCH),
        "tracked_remote_branch": git("rev-parse", f"origin/{R4P_BRANCH}"),
        "remote_branch": remote.get(f"refs/heads/{R4P_BRANCH}"),
        "tag_object": git("rev-parse", R4P_TAG),
        "tag_target": git("rev-parse", f"{R4P_TAG}^{{}}"),
        "remote_tag_object": remote.get(f"refs/tags/{R4P_TAG}"),
        "remote_tag_target": remote.get(f"refs/tags/{R4P_TAG}^{{}}"),
    }
    expected = {
        "head": R4P_FREEZE_SHA,
        "branch": R4P_BRANCH,
        "local_branch": R4P_FREEZE_SHA,
        "tracked_remote_branch": R4P_FREEZE_SHA,
        "remote_branch": R4P_FREEZE_SHA,
        "tag_object": R4P_TAG_OBJECT,
        "tag_target": R4P_FREEZE_SHA,
        "remote_tag_object": R4P_TAG_OBJECT,
        "remote_tag_target": R4P_FREEZE_SHA,
    }
    require(identity == expected, f"ER2_R4_FAIL_R4P_PREREQUISITE: {identity}")
    require(not git("diff", "--name-only"), "ER2_R4_FAIL_UPSTREAM_IMMUTABILITY: tracked")
    require(not git("diff", "--cached", "--name-only"), "ER2_R4_FAIL_UPSTREAM_IMMUTABILITY: staged")
    untracked = set(git("ls-files", "--others", "--exclude-standard").splitlines())
    authorized = {path.as_posix() for path in CANDIDATES}
    require(untracked.issubset(authorized), f"ER2_R4_FAIL_UPSTREAM_IMMUTABILITY: {sorted(untracked)}")

    actual_hashes = {path.as_posix(): sha_file(ROOT / path) for path in FROZEN_INPUT_SHA256}
    expected_hashes = {path.as_posix(): digest for path, digest in FROZEN_INPUT_SHA256.items()}
    require(actual_hashes == expected_hashes, "ER2_R4_FAIL_UPSTREAM_IMMUTABILITY: frozen SHA")
    require(git("rev-parse", f"{R4P_FREEZE_SHA}^") == R3_FREEZE_SHA, "ER2_R4_FAIL_R4P_PREREQUISITE: R3 parent")

    r4p_lock = read_json(R4P_LOCK)
    require(
        r4p_lock["r4_tier_contract_sha256"] == R4_TIER_CONTRACT_SHA
        and r4p_lock["final_verdict"]
        == "ER2_R4P_PASS_SPATIAL_HAC_PREEXECUTION_CERTIFIED_READY_FOR_DIRECTOR_EXECUTION_DECISION",
        "ER2_R4_FAIL_FROZEN_CONTRACT: R4P lock",
    )
    tier_row, tier = r4p.r4_contract()
    require(tier_row["TIER_CONTRACT_SHA256"] == R4_TIER_CONTRACT_SHA, "ER2_R4_FAIL_FROZEN_CONTRACT: tier SHA")
    require(
        tier["tier_id"] == "R4_SPATIAL_HAC"
        and tier["role"] == "ASYMPTOTIC_SPATIAL_HAC_ROBUSTNESS_DIAGNOSTIC"
        and tier["family"] == "PHYSICAL_ANOMALY"
        and tier["previous_tier"] == "R3"
        and tier["next_tier"] == "R5"
        and tier["bandwidths_km"] == list(BANDWIDTHS_KM)
        and tier["kernel"] == "BARTLETT"
        and tier["pairing"] == "SAME_PERIOD_ONLY",
        "ER2_R4_FAIL_FROZEN_CONTRACT: tier fields",
    )
    api = r4p.conley_api_identity()
    require(
        api["file_sha256"] == ED1_IMPLEMENTATION_SHA
        and api["function_source_sha256"] == CONLEY_SOURCE_SHA
        and api["function_body_sha256"] == CONLEY_BODY_SHA,
        "ER2_R4_FAIL_FROZEN_CONTRACT: Conley API",
    )
    er1_lock = read_json(ER1_LOCK)
    require(
        er1_lock["er1_numerical_results_identity"]["sha256"] == ER1_NUMERICAL_IDENTITY,
        "ER2_R4_FAIL_PRIMARY_MODEL_IDENTITY: ER1 numerical identity",
    )
    require(read_json(R3_LOCK)["status"] == "RESULTS_LOCKED_PENDING_DIRECTOR_REVIEW", "ER2_R4_FAIL_R4P_PREREQUISITE: R3 lock")
    return {
        "identity": identity,
        "frozen_input_sha256": actual_hashes,
        "r4_tier_contract": tier,
        "conley_api": api,
        "authorized_candidate_universe": sorted(authorized),
        "real_outcome_values_read": False,
    }


def load_frozen_references() -> dict[str, Any]:
    mapping = read_csv(R4P_MAP)
    require(len(mapping) == 21, "ER2_R4_FAIL_FROZEN_CONTRACT: target count")
    require([int(row["MAP_ORDER"]) for row in mapping] == list(range(1, 22)), "ER2_R4_FAIL_FROZEN_CONTRACT: target order")
    require(all(row["EXPECTED_REAL_R4_BANDWIDTHS_KM"] == "50|100|150" for row in mapping), "ER2_R4_FAIL_FROZEN_CONTRACT: bandwidth map")
    require(len({(row["CROP_CODE"], row["COEFFICIENT_NAME"]) for row in mapping}) == 21, "ER2_R4_FAIL_FROZEN_CONTRACT: duplicate target")
    er1_rows = read_csv(ER1_COEFFICIENTS)
    r3_rows = read_csv(R3_COEFFICIENTS)
    r3_samples = read_csv(R3_SAMPLES)
    require(len(er1_rows) == len(r3_rows) == 21 and len(r3_samples) == 5, "ER2_R4_FAIL_PRIMARY_MODEL_IDENTITY: reference inventory")
    return {
        "mapping": mapping,
        "er1": {(row["CROP_CODE"], row["CLIMATE_VARIABLE"]): row for row in er1_rows},
        "r3": {(row["CROP_CODE"], row["CLIMATE_VARIABLE"]): row for row in r3_rows},
        "r3_samples": {row["CROP_CODE"]: row for row in r3_samples},
        "r2_sample_identity": read_json(R2_LOCK)["sample_identity"],
    }


def frozen_centroids() -> tuple[dict[str, tuple[float, float]], Counter[str]]:
    source = read_json(GEOMETRY)
    identifiers = [str(feature["properties"]["UBIGEO"]) for feature in source["features"]]
    counts = Counter(identifiers)
    require(len(identifiers) == len(counts) == 55 and all(value == 1 for value in counts.values()), "ER2_R4_HOLD_SAMPLE_GEOMETRY_COVERAGE")
    centroids = ed1.district_centroids()
    require(len(centroids) == 55, "ER2_R4_HOLD_SAMPLE_GEOMETRY_COVERAGE")
    for coordinate in centroids.values():
        values = np.asarray(coordinate, dtype=float)
        require(values.shape == (2,) and np.isfinite(values).all(), "ER2_R4_HOLD_SAMPLE_GEOMETRY_COVERAGE")
    return centroids, counts


def prepare_real_samples(references: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    transient_outcomes, perennial_outcomes, source_metadata = er1.read_outcome_sources()
    transient_exposures = pq.read_table(ed1.TRANSIENT_PATH, columns=list(ed1.TRANSIENT_COLUMNS)).to_pandas()
    perennial_exposures = ed1.read_perennial_primary()
    samples: dict[str, dict[str, Any]] = {}

    for crop_code in CROP_ORDER:
        crop = ed1.CROPS[crop_code]
        if crop_code in {"14010020000", "14010070000"}:
            frame, columns = er1.transient_design_with_outcome(
                transient_exposures, transient_outcomes, crop_code
            )
            source_sha = source_metadata["transient"]["sha256"]
        else:
            frame, columns = er1.perennial_design_with_outcome(
                perennial_exposures, perennial_outcomes, crop_code
            )
            source_sha = source_metadata["perennial"]["sha256"]
        period = str(crop["period_column"])
        frame = frame.sort_values(["UBIGEO", period], kind="mergesort").reset_index(drop=True)
        frame["UBIGEO"] = frame["UBIGEO"].astype(str)
        frame[period] = frame[period].astype(str)
        y = pd.to_numeric(frame["YIELD"], errors="coerce").to_numpy(dtype=float)
        x = frame[columns].to_numpy(dtype=float)
        keys = frame[["UBIGEO", period]].astype(str).to_numpy().tolist()
        expected = er1.EXPECTED_SAMPLE[crop_code]
        actual = {
            "n": len(frame),
            "districts": int(frame["UBIGEO"].nunique()),
            "effective": int(
                ed1.effective_cluster_audit(
                    frame, ed1.absorb_fixed_effects(x, ed1.fe_matrix(frame, period))
                )["effective_contributing_clusters"]
            ),
            "periods": int(frame[period].nunique()),
        }
        r3_sample = references["r3_samples"][crop_code]
        r2_sample = references["r2_sample_identity"][crop_code]
        require(actual == expected, f"ER2_R4_FAIL_PRIMARY_MODEL_IDENTITY: sample {crop_code}")
        require(keys == r2_sample["er1_ordered_keys"], f"ER2_R4_FAIL_PRIMARY_MODEL_IDENTITY: ordered keys {crop_code}")
        require(key_sha(keys) == r3_sample["ORDERED_KEY_SHA256"], f"ER2_R4_FAIL_PRIMARY_MODEL_IDENTITY: key SHA {crop_code}")
        require(array_sha(y) == r3_sample["Y_FLOAT64_SHA256"], f"ER2_R4_FAIL_PRIMARY_MODEL_IDENTITY: Y SHA {crop_code}")
        require(array_sha(x) == r3_sample["X_FLOAT64_SHA256"], f"ER2_R4_FAIL_PRIMARY_MODEL_IDENTITY: X SHA {crop_code}")
        require(np.isfinite(y).all() and np.isfinite(x).all(), f"ER2_R4_FAIL_PRIMARY_MODEL_IDENTITY: finite {crop_code}")
        require(not frame.duplicated(["UBIGEO", period]).any(), f"ER2_R4_FAIL_PRIMARY_MODEL_IDENTITY: duplicate key {crop_code}")
        samples[crop_code] = {
            "frame": frame,
            "columns": columns,
            "period": period,
            "y": y,
            "x": x,
            "keys": keys,
            "actual": actual,
            "source_sha256": source_sha,
            "ordered_key_sha256": key_sha(keys),
            "y_float64_sha256": array_sha(y),
            "x_float64_sha256": array_sha(x),
        }
    return samples, source_metadata


def certify_sample_geometry_coverage(
    samples: dict[str, dict[str, Any]],
    centroids: dict[str, tuple[float, float]],
    source_counts: Counter[str],
) -> tuple[list[dict[str, Any]], dict[str, Any], bytes]:
    rows: list[dict[str, Any]] = []
    crop_summaries: dict[str, Any] = {}
    all_pass = True
    for crop_code in CROP_ORDER:
        crop = ed1.CROPS[crop_code]
        districts = sorted(set(samples[crop_code]["frame"]["UBIGEO"].astype(str)))
        expected = er1.EXPECTED_SAMPLE[crop_code]["districts"]
        crop_rows: list[dict[str, Any]] = []
        for ubigeo in districts:
            present = ubigeo in centroids
            unique = source_counts.get(ubigeo, 0) == 1
            coordinate = centroids.get(ubigeo, (float("nan"), float("nan")))
            finite = bool(np.isfinite(np.asarray(coordinate, dtype=float)).all())
            passed = present and unique and finite
            crop_rows.append(
                {
                    "CROP": crop["crop"],
                    "CROP_CODE": crop_code,
                    "UBIGEO": ubigeo,
                    "IN_FROZEN_SAMPLE": True,
                    "CENTROID_PRESENT": present,
                    "CENTROID_UNIQUE": unique,
                    "CENTROID_X_M": coordinate[0],
                    "CENTROID_Y_M": coordinate[1],
                    "FINITE_XY": finite,
                    "COVERAGE_STATUS": "PASS" if passed else "HOLD",
                }
            )
        crop_pass = len(districts) == expected and all(row["COVERAGE_STATUS"] == "PASS" for row in crop_rows)
        all_pass = all_pass and crop_pass
        rows.extend(crop_rows)
        crop_summaries[crop_code] = {
            "crop": crop["crop"],
            "expected_nominal_districts": expected,
            "unique_sample_districts": len(districts),
            "centroids_present": sum(row["CENTROID_PRESENT"] for row in crop_rows),
            "centroids_unique": sum(row["CENTROID_UNIQUE"] for row in crop_rows),
            "finite_coordinates": sum(row["FINITE_XY"] for row in crop_rows),
            "missing_centroids": sum(not row["CENTROID_PRESENT"] for row in crop_rows),
            "duplicate_centroid_records": sum(not row["CENTROID_UNIQUE"] for row in crop_rows),
            "status": "PASS" if crop_pass else "HOLD",
        }
    ledger = csv_bytes(rows, COVERAGE_FIELDS)
    require(len(rows) == 232 and all_pass, "ER2_R4_HOLD_SAMPLE_GEOMETRY_COVERAGE")
    return rows, {
        "status": "PASS_ALL_FIVE_CROPS",
        "rows": len(rows),
        "frozen_geometry_centroids": len(centroids),
        "source_crs": "EPSG:4326",
        "target_crs": "EPSG:32717",
        "coordinate_construction": "PROJECT_FULL_FROZEN_GEOMETRY_THEN_CENTROID",
        "crop_summaries": crop_summaries,
        "coverage_ledger_sha256_before_covariance": sha_bytes(ledger),
    }, ledger


def execute_conley(
    samples: dict[str, dict[str, Any]],
    centroids: dict[str, tuple[float, float]],
    references: dict[str, Any],
) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    audits: list[dict[str, Any]] = []
    model_identity: dict[str, Any] = {}
    covariance_matrices = 0
    max_beta_difference = 0.0

    for crop_code in CROP_ORDER:
        sample = samples[crop_code]
        crop = ed1.CROPS[crop_code]
        frame = sample["frame"]
        columns = sample["columns"]
        fit = ed1.fit_two_way_fe_cr2(frame, columns, sample["period"], sample["y"])
        mapped = [row for row in references["mapping"] if row["CROP_CODE"] == crop_code]
        require([row["COEFFICIENT_NAME"] for row in mapped] == columns, f"ER2_R4_FAIL_PRIMARY_MODEL_IDENTITY: column order {crop_code}")
        differences: list[float] = []
        for position, variable in enumerate(columns):
            er1_row = references["er1"][(crop_code, variable)]
            difference = abs(float(fit["beta"][position]) - float(er1_row["BETA"]))
            differences.append(difference)
        crop_max_difference = max(differences)
        max_beta_difference = max(max_beta_difference, crop_max_difference)
        require(crop_max_difference <= MODEL_IDENTITY_TOLERANCE, f"ER2_R4_FAIL_PRIMARY_MODEL_IDENTITY: beta {crop_code}")
        model_identity[crop_code] = {
            "crop": crop["crop"],
            "model_id": crop["model_id"],
            "sample_n": sample["actual"]["n"],
            "nominal_districts": sample["actual"]["districts"],
            "effective_districts": sample["actual"]["effective"],
            "periods": sample["actual"]["periods"],
            "ordered_key_sha256": sample["ordered_key_sha256"],
            "y_float64_sha256": sample["y_float64_sha256"],
            "x_float64_sha256": sample["x_float64_sha256"],
            "maximum_beta_absolute_difference": crop_max_difference,
            "tolerance": MODEL_IDENTITY_TOLERANCE,
            "model_specification_change": False,
            "status": "PASS",
        }

        covariance_by_bandwidth: dict[int, np.ndarray] = {}
        for bandwidth in BANDWIDTHS_KM:
            covariance = ed1.conley_covariance(
                frame,
                fit["x_within"],
                fit["residual"],
                sample["period"],
                bandwidth,
                centroids,
            )
            covariance_matrices += 1
            matrix_finite = bool(np.isfinite(covariance).all())
            shape_valid = covariance.shape == (len(columns), len(columns))
            asymmetry = float(np.max(np.abs(covariance - covariance.T)))
            diagonal = np.diag(covariance)
            nonfinite = int((~np.isfinite(diagonal)).sum())
            nonpositive = int(np.sum(diagonal <= 0.0)) if nonfinite == 0 else 0
            valid = (
                shape_valid
                and matrix_finite
                and asymmetry <= COVARIANCE_SYMMETRY_TOLERANCE
                and nonfinite == 0
                and nonpositive == 0
            )
            require(valid, "ER2_R4_HOLD_NONPOSITIVE_OR_NONFINITE_CONLEY_VARIANCE")
            covariance_by_bandwidth[bandwidth] = covariance
            audits.append(
                {
                    "CROP": crop["crop"],
                    "CROP_CODE": crop_code,
                    "MODEL_ID": crop["model_id"],
                    "BANDWIDTH_KM": bandwidth,
                    "N": sample["actual"]["n"],
                    "DISTRICTS": sample["actual"]["districts"],
                    "PERIODS": sample["actual"]["periods"],
                    "K": len(columns),
                    "MATRIX_FINITE": matrix_finite,
                    "MAX_SYMMETRY_DIFFERENCE": asymmetry,
                    "MIN_DIAGONAL_VARIANCE": float(np.min(diagonal)),
                    "MAX_DIAGONAL_VARIANCE": float(np.max(diagonal)),
                    "NONPOSITIVE_DIAGONAL_COUNT": nonpositive,
                    "NONFINITE_DIAGONAL_COUNT": nonfinite,
                    "STATUS": "PASS",
                }
            )

        for target in mapped:
            variable = target["COEFFICIENT_NAME"]
            position = int(target["ED1_REGRESSOR_POSITION_ZERO_BASED"])
            er1_row = references["er1"][(crop_code, variable)]
            beta = float(er1_row["BETA"])
            for bandwidth in BANDWIDTHS_KM:
                variance = float(covariance_by_bandwidth[bandwidth][position, position])
                require(np.isfinite(variance) and variance > 0.0, "ER2_R4_HOLD_NONPOSITIVE_OR_NONFINITE_CONLEY_VARIANCE")
                standard_error = math.sqrt(variance)
                z_value = beta / standard_error
                p_value = math.erfc(abs(z_value) / math.sqrt(2.0))
                lower = beta - NORMAL_CRITICAL_VALUE * standard_error
                upper = beta + NORMAL_CRITICAL_VALUE * standard_error
                results.append(
                    {
                        "MAP_ORDER": int(target["MAP_ORDER"]),
                        "CROP": crop["crop"],
                        "CROP_CODE": crop_code,
                        "MODEL_ID": crop["model_id"],
                        "VARIABLE": variable,
                        "WINDOW": er1_row["WINDOW"],
                        "BANDWIDTH_KM": bandwidth,
                        "ER1_BETA_REFERENCE": beta,
                        "CONLEY_VARIANCE": variance,
                        "CONLEY_SE": standard_error,
                        "Z": z_value,
                        "TWO_SIDED_ASYMPTOTIC_P": p_value,
                        "NORMAL_CRITICAL_VALUE": NORMAL_CRITICAL_VALUE,
                        "CI95_LOWER": lower,
                        "CI95_UPPER": upper,
                        "CI_ZERO_INCLUDED": lower <= 0.0 <= upper,
                        "SAMPLE_N": sample["actual"]["n"],
                        "NOMINAL_DISTRICTS": sample["actual"]["districts"],
                        "PERIODS": sample["actual"]["periods"],
                        "CRS": "EPSG:32717",
                        "KERNEL": "BARTLETT",
                        "SAME_PERIOD_ONLY": True,
                        "STATUS": "PASS",
                    }
                )

    results.sort(key=lambda row: (int(row["MAP_ORDER"]), int(row["BANDWIDTH_KM"])))
    require(len(results) == 63 and len(audits) == 15 and covariance_matrices == 15, "ER2_R4_FAIL_RESULT_ROW_INVENTORY")
    require([int(row["BANDWIDTH_KM"]) for row in results] == list(BANDWIDTHS_KM) * 21, "ER2_R4_FAIL_RESULT_ROW_INVENTORY: order")
    invalid_count = sum(
        int(row["NONPOSITIVE_DIAGONAL_COUNT"]) + int(row["NONFINITE_DIAGONAL_COUNT"])
        for row in audits
    )
    require(invalid_count == 0, "ER2_R4_HOLD_NONPOSITIVE_OR_NONFINITE_CONLEY_VARIANCE")
    return {
        "results": results,
        "covariance_audits": audits,
        "model_identity": model_identity,
        "maximum_er1_beta_absolute_difference": max_beta_difference,
        "covariance_matrices": covariance_matrices,
        "invalid_variance_count": invalid_count,
    }


def descriptive_concordance(
    results: list[dict[str, Any]], references: dict[str, Any]
) -> list[dict[str, Any]]:
    indexed = {
        (row["CROP_CODE"], row["VARIABLE"], int(row["BANDWIDTH_KM"])): row
        for row in results
    }
    rows: list[dict[str, Any]] = []
    for target in references["mapping"]:
        key = (target["CROP_CODE"], target["COEFFICIENT_NAME"])
        er1_row = references["er1"][key]
        r3_row = references["r3"][key]
        beta = float(er1_row["BETA"])
        states = [bool(indexed[(key[0], key[1], bandwidth)]["CI_ZERO_INCLUDED"]) for bandwidth in BANDWIDTHS_KM]
        sensitivity = (
            "CI_ZERO_INCLUSION_STABLE_ACROSS_PRESPECIFIED_BANDWIDTHS"
            if len(set(states)) == 1
            else "CI_ZERO_INCLUSION_VARIES_BY_BANDWIDTH"
        )
        rows.append(
            {
                "MAP_ORDER": int(target["MAP_ORDER"]),
                "CROP": target["CROP"],
                "CROP_CODE": key[0],
                "MODEL_ID": target["MODEL_ID"],
                "VARIABLE": key[1],
                "WINDOW": er1_row["WINDOW"],
                "ER1_BETA": beta,
                "ER1_SIGN": "POSITIVE" if beta > 0.0 else "NEGATIVE" if beta < 0.0 else "ZERO",
                "ER1_CR2_P": float(er1_row["P_VALUE_TWO_SIDED"]),
                "ER1_CR2_HOLM_P": float(er1_row["HOLM_ADJUSTED_P_VALUE"]),
                "ER1_CR2_HOLM_STATUS": r3_row["CR2_HOLM_STATUS"],
                "R3_WCR_P": float(r3_row["WCR_RAW_P"]),
                "R3_WCR_HOLM_P": float(r3_row["WITHIN_CROP_HOLM_WCR_P"]),
                "R3_WCR_HOLM_STATUS": r3_row["WCR_HOLM_STATUS"],
                "R4_50_CI_ZERO_INCLUDED": states[0],
                "R4_100_CI_ZERO_INCLUDED": states[1],
                "R4_150_CI_ZERO_INCLUDED": states[2],
                "BANDWIDTH_SENSITIVITY": sensitivity,
            }
        )
    require(len(rows) == 21, "ER2_R4_FAIL_RESULT_ROW_INVENTORY: concordance")
    return rows


def real_calculation() -> dict[str, Any]:
    pre = preflight()
    references = load_frozen_references()
    centroids, source_counts = frozen_centroids()
    samples, source_metadata = prepare_real_samples(references)

    coverage_rows, coverage_summary, coverage_payload = certify_sample_geometry_coverage(
        samples, centroids, source_counts
    )
    require(
        coverage_summary["status"] == "PASS_ALL_FIVE_CROPS",
        "ER2_R4_HOLD_SAMPLE_GEOMETRY_COVERAGE",
    )

    conley = execute_conley(samples, centroids, references)
    concordance = descriptive_concordance(conley["results"], references)
    return {
        "preflight": pre,
        "temporal_governance_before_execution": {
            "PRIMARY_RESULTS_KNOWN": True,
            "R1_RESULTS_KNOWN": True,
            "R2_RESULTS_KNOWN": True,
            "R3_RESULTS_KNOWN": True,
            "R4P_FROZEN_BEFORE_REAL_R4": True,
            "REAL_R4_RESULTS_KNOWN_BEFORE_EXECUTION": False,
            "R4_BANDWIDTHS_FROZEN_BEFORE_RESULTS": True,
            "R4_KERNEL_FROZEN_BEFORE_RESULTS": True,
            "R4_GEOMETRY_FROZEN_BEFORE_RESULTS": True,
            "R4_TARGETS_FROZEN_BEFORE_RESULTS": True,
        },
        "source_metadata": source_metadata,
        "sample_geometry_coverage": coverage_summary,
        "coverage_rows": coverage_rows,
        "coverage_ledger_sha256_before_covariance": sha_bytes(coverage_payload),
        "execution_sequence": [
            "R4P_FROZEN_IDENTITY_VERIFIED",
            "REAL_SAMPLES_RECONSTRUCTED_AND_IDENTIFIED",
            "COMPLETE_232_ROW_SAMPLE_GEOMETRY_LEDGER_CERTIFIED",
            "SAMPLE_GEOMETRY_COVERAGE_PASS_ALL_FIVE_CROPS",
            "FIFTEEN_CONLEY_COVARIANCE_MATRICES_COMPUTED",
            "SIXTY_THREE_DIAGNOSTIC_ROWS_DERIVED",
        ],
        "model_identity": conley["model_identity"],
        "maximum_er1_beta_absolute_difference": conley["maximum_er1_beta_absolute_difference"],
        "results": conley["results"],
        "covariance_audits": conley["covariance_audits"],
        "covariance_matrices": conley["covariance_matrices"],
        "invalid_variance_count": conley["invalid_variance_count"],
        "concordance": concordance,
        "result_specific_r4_branches": 0,
        "final_verdict": FINAL_VERDICT,
    }


def zero_exclusion_counts(results: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = {}
    for crop_code in CROP_ORDER:
        counts[crop_code] = {}
        for bandwidth in BANDWIDTHS_KM:
            rows = [
                row for row in results
                if row["CROP_CODE"] == crop_code and int(row["BANDWIDTH_KM"]) == bandwidth
            ]
            counts[crop_code][str(bandwidth)] = sum(not bool(row["CI_ZERO_INCLUDED"]) for row in rows)
    return counts


def report_bytes(data: dict[str, Any]) -> bytes:
    counts = zero_exclusion_counts(data["results"])
    crop_names = {code: ed1.CROPS[code]["crop"] for code in CROP_ORDER}
    lines = [
        "# ER2-R4 Real Spatial HAC / Conley Execution v1",
        "",
        f"FINAL_VERDICT={FINAL_VERDICT}",
        f"R4P_FREEZE_SHA={R4P_FREEZE_SHA}",
        f"R4_TIER_CONTRACT_SHA={R4_TIER_CONTRACT_SHA}",
        "SAMPLE_GEOMETRY_COVERAGE=PASS_ALL_FIVE_CROPS",
        "R4_MODEL_SPECIFICATION_CHANGE=FALSE",
        f"MAX_ER1_BETA_ABS_DIFFERENCE={canonical_float(data['maximum_er1_beta_absolute_difference'])}",
        "",
        "## Frozen inference contract",
        "",
        "R4 changes covariance and inference only. It preserves the exact ER1/R3 outcome, physical-anomaly regressors, windows, linear form, unweighted sample, district fixed effects, period fixed effects, coefficients, and ordered keys.",
        "All 21 coefficients are reported at all three prespecified bandwidths (50, 100, and 150 km) using the frozen Bartlett same-period-only Conley function and EPSG:32717 district centroids.",
        "Intervals are unadjusted asymptotic-normal diagnostics using beta +/- 1.959963984540054 times the Conley standard error.",
        "",
        "## Coverage and covariance audit",
        "",
        f"COVERAGE_LEDGER_ROWS={data['sample_geometry_coverage']['rows']}",
        f"COVERAGE_LEDGER_SHA256_BEFORE_COVARIANCE={data['coverage_ledger_sha256_before_covariance']}",
        f"R4_COVARIANCE_MATRICES={data['covariance_matrices']}",
        f"R4_INVALID_VARIANCE_COUNT={data['invalid_variance_count']}",
        "",
        "| Crop | Nominal districts | N | Periods | 50 km exclusions | 100 km exclusions | 150 km exclusions |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for crop_code in CROP_ORDER:
        identity = data["model_identity"][crop_code]
        lines.append(
            f"| {crop_names[crop_code]} | {identity['nominal_districts']} | {identity['sample_n']} | "
            f"{identity['periods']} | {counts[crop_code]['50']} | {counts[crop_code]['100']} | "
            f"{counts[crop_code]['150']} |"
        )
    lines += [
        "",
        "## Descriptive concordance",
        "",
        "| Crop | Variable | ER1 beta | ER1 Holm status | R3 WCR Holm status | 50 km zero | 100 km zero | 150 km zero | Spatial covariance sensitivity |",
        "|---|---|---:|---|---|---|---|---|---|",
    ]
    for row in data["concordance"]:
        lines.append(
            f"| {row['CROP']} | {row['VARIABLE']} | {row['ER1_BETA']:.9g} | "
            f"{row['ER1_CR2_HOLM_STATUS']} | {row['R3_WCR_HOLM_STATUS']} | "
            f"{str(row['R4_50_CI_ZERO_INCLUDED']).upper()} | "
            f"{str(row['R4_100_CI_ZERO_INCLUDED']).upper()} | "
            f"{str(row['R4_150_CI_ZERO_INCLUDED']).upper()} | {row['BANDWIDTH_SENSITIVITY']} |"
        )
    varying = sum(row["BANDWIDTH_SENSITIVITY"] == "CI_ZERO_INCLUSION_VARIES_BY_BANDWIDTH" for row in data["concordance"])
    lines += [
        "",
        "## Interpretation firewall",
        "",
        f"COEFFICIENTS_WITH_CI_ZERO_INCLUSION_VARIATION_ACROSS_BANDWIDTHS={varying}",
        "All bandwidth-specific findings are retained as spatial-covariance sensitivity. No bandwidth was selected and no vote, robustness score, joint Conley test, Holm adjustment, or global FWER claim was constructed.",
        "No result triggered model, sample, target, geometry, kernel, or bandwidth redesign. R5 and R6 were not executed.",
        "",
        "R4_JOINT_CONLEY_TESTS=NOT_AUTHORIZED",
        "R4_HOLM=NOT_AUTHORIZED",
        "GLOBAL_FIVE_CROP_FWER=NOT_CLAIMED",
        "MULTIPLICITY_ADJUSTED_CI=NOT_CONSTRUCTED_NOT_CLAIMED",
        "RESULT_SPECIFIC_R4_BRANCHES=0",
        "R5_AUTHORIZATION_STATUS=NOT_AUTHORIZED",
        "R5_EXECUTED=FALSE",
        "R6_AUTHORIZATION_STATUS=NOT_AUTHORIZED",
        "R6_EXECUTED=FALSE",
        "NEXT_ACTION=RETURN_TO_SCIENTIFIC_DIRECTOR_FOR_R4_REVIEW",
        "",
    ]
    return "\n".join(lines).encode("utf-8")


def render(data: dict[str, Any], reproduction: dict[str, Any]) -> dict[Path, bytes]:
    payloads: dict[Path, bytes] = {
        RESULTS: csv_bytes(data["results"], RESULT_FIELDS),
        COVERAGE: csv_bytes(data["coverage_rows"], COVERAGE_FIELDS),
        COVARIANCE_AUDIT: csv_bytes(data["covariance_audits"], COVARIANCE_FIELDS),
        CONCORDANCE: csv_bytes(data["concordance"], CONCORDANCE_FIELDS),
        REPORT: report_bytes(data),
    }
    artifact_sha = {path.as_posix(): sha_bytes(payload) for path, payload in payloads.items()}
    artifact_sha[SCRIPT.as_posix()] = sha_file(ROOT / SCRIPT)
    artifact_sha[TEST.as_posix()] = sha_file(ROOT / TEST)
    lock = {
        "schema_version": "1.0.0",
        "project": PROJECT,
        "gate": GATE,
        "status": "RESULTS_LOCKED_PENDING_DIRECTOR_REVIEW",
        "final_verdict": FINAL_VERDICT,
        "tier_id": "R4_SPATIAL_HAC",
        "tier_order": 4,
        "r4_tier_contract_sha256": R4_TIER_CONTRACT_SHA,
        "r4p_freeze_sha": R4P_FREEZE_SHA,
        "r4p_lock_sha256": R4P_LOCK_SHA,
        "r4p_synthetic_test_plan_lock_sha256": R4P_TEST_PLAN_LOCK_SHA,
        "r3_freeze_sha": R3_FREEZE_SHA,
        "r3_results_lock_sha256": R3_RESULTS_LOCK_SHA,
        "er1_numerical_results_identity": ER1_NUMERICAL_IDENTITY,
        "temporal_governance_before_execution": data["temporal_governance_before_execution"],
        "r4_scientific_role": {
            "role": "ASYMPTOTIC_SPATIAL_HAC_ROBUSTNESS_DIAGNOSTIC",
            "family": "PHYSICAL_ANOMALY",
            "outcome": "YIELD_LEVEL_TM_PER_HA",
            "functional_form": "LINEAR_ADDITIVE",
            "district_fixed_effects": True,
            "period_fixed_effects": True,
            "weighting": "UNWEIGHTED",
            "model_specification_change": False,
            "primary_replacement": "PROHIBITED",
        },
        "bandwidths_km": list(BANDWIDTHS_KM),
        "best_bandwidth_selection": "PROHIBITED",
        "kernel": "BARTLETT",
        "bartlett_rule": "w(d,h)=max(1-d_km/h_km,0)",
        "temporal_rule": "SAME_PERIOD_ONLY",
        "geometry": {
            "source": GEOMETRY.as_posix(),
            "source_sha256": GEOMETRY_SHA,
            "source_crs": "EPSG:4326",
            "target_crs": "EPSG:32717",
            "construction": "PROJECT_FULL_FROZEN_GEOMETRY_THEN_CENTROID",
            "distance": "EUCLIDEAN_PROJECTED_METRES_DIVIDED_BY_1000",
        },
        "conley_api": data["preflight"]["conley_api"],
        "sample_geometry_coverage": data["sample_geometry_coverage"],
        "coverage_rows": data["coverage_rows"],
        "coverage_ledger_sha256_before_covariance": data["coverage_ledger_sha256_before_covariance"],
        "execution_sequence": data["execution_sequence"],
        "model_identity": data["model_identity"],
        "maximum_er1_beta_absolute_difference": data["maximum_er1_beta_absolute_difference"],
        "model_identity_tolerance": MODEL_IDENTITY_TOLERANCE,
        "targets": data["preflight"]["r4_tier_contract"].get("coefficients", "EXACT_ER1_PRIMARY"),
        "target_map": load_frozen_references()["mapping"],
        "result_rows": data["results"],
        "result_row_count": len(data["results"]),
        "covariance_audits": data["covariance_audits"],
        "covariance_matrix_count": data["covariance_matrices"],
        "concordance_rows": data["concordance"],
        "concordance_row_count": len(data["concordance"]),
        "invalid_variance_inventory": {
            "count": data["invalid_variance_count"],
            "policy": "HOLD_NO_CLIPPING_OR_COVARIANCE_SUBSTITUTION",
        },
        "interval_contract": {
            "formula": "ER1_BETA_PLUS_MINUS_1.959963984540054_TIMES_CONLEY_SE",
            "critical_value": NORMAL_CRITICAL_VALUE,
            "distribution": "ASYMPTOTIC_STANDARD_NORMAL",
            "adjusted": False,
        },
        "multiplicity_firewall": {
            "R4_HOLM": "NOT_AUTHORIZED",
            "GLOBAL_FIVE_CROP_FWER": "NOT_CLAIMED",
            "MULTIPLICITY_ADJUSTED_CI": "NOT_CONSTRUCTED_NOT_CLAIMED",
            "VOTE_COUNTING": "PROHIBITED",
            "ROBUSTNESS_SCORE": "PROHIBITED",
        },
        "joint_conley_tests": [],
        "joint_conley_status": "NOT_AUTHORIZED",
        "result_specific_r4_branches": data["result_specific_r4_branches"],
        "two_run_reproducibility": reproduction,
        "frozen_input_sha256": data["preflight"]["frozen_input_sha256"],
        "outcome_sources": data["source_metadata"],
        "artifact_sha256": artifact_sha,
        "execution_firewall": {
            "R4_EXECUTED": True,
            "R5_AUTHORIZATION_STATUS": "NOT_AUTHORIZED",
            "R5_EXECUTED": False,
            "R6_AUTHORIZATION_STATUS": "NOT_AUTHORIZED",
            "R6_EXECUTED": False,
            "ENSO_SCENARIOS": "NOT_EXECUTED",
            "GVP": "NOT_EXECUTED",
            "VAR_CVAR": "NOT_EXECUTED",
            "A1_A2": "NOT_EXECUTED",
            "OPTIMIZATION": "NOT_EXECUTED",
        },
        "NEXT_TIER_AUTHORIZATION_STATUS": "NOT_AUTHORIZED",
        "next_action": "RETURN_TO_SCIENTIFIC_DIRECTOR_FOR_R4_REVIEW",
    }
    payloads[LOCK] = json_bytes(lock)
    return payloads


def run_worker(path: Path) -> None:
    path.write_bytes(json_bytes(real_calculation()))


def build(output_root: Path) -> dict[str, str]:
    preflight()
    if output_root != ROOT:
        try:
            output_root.relative_to(ROOT)
        except ValueError:
            pass
        else:
            raise RuntimeError("ER2_R4_FAIL_UPSTREAM_IMMUTABILITY: nested repository output root")
    with tempfile.TemporaryDirectory(prefix="er2_r4_real_") as temporary:
        temporary_path = Path(temporary)
        worker_paths = (temporary_path / "run1.json", temporary_path / "run2.json")
        for worker_path in worker_paths:
            subprocess.run(
                [sys.executable, str(ROOT / SCRIPT), "--worker", str(worker_path)],
                cwd=ROOT,
                check=True,
            )
        run_bytes = [path.read_bytes() for path in worker_paths]
        require(run_bytes[0] == run_bytes[1], "ER2_R4_HOLD_NONDETERMINISTIC_REAL_R4")
        calculation_sha = sha_bytes(run_bytes[0])
        reproduction = {
            "status": "PASS",
            "independent_processes": 2,
            "run_1_calculation_sha256": calculation_sha,
            "run_2_calculation_sha256": sha_bytes(run_bytes[1]),
            "calculation_bytes_exact": True,
            "rendered_output_bytes_exact": True,
            "rng": "NONE_DETERMINISTIC_CONLEY",
        }
        data_one = json.loads(run_bytes[0].decode("utf-8"))
        data_two = json.loads(run_bytes[1].decode("utf-8"))
        rendered_one = render(data_one, reproduction)
        rendered_two = render(data_two, reproduction)
        require(rendered_one == rendered_two, "ER2_R4_HOLD_NONDETERMINISTIC_REAL_R4")
        for relative, payload in rendered_one.items():
            destination = output_root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(payload)
    return {path.as_posix(): sha_file(output_root / path) for path in OUTPUTS}


def check_existing() -> dict[str, str]:
    before = {path: (ROOT / path).read_bytes() for path in OUTPUTS}
    with tempfile.TemporaryDirectory(prefix="er2_r4_check_") as temporary:
        output_root = Path(temporary)
        hashes = build(output_root)
        for relative in OUTPUTS:
            require(
                (output_root / relative).read_bytes() == before[relative],
                f"ER2_R4_FAIL_TEST_REGRESSION: {relative}",
            )
    after = {path: (ROOT / path).read_bytes() for path in OUTPUTS}
    require(before == after, "ER2_R4_FAIL_TEST_REGRESSION: check-only write")
    return hashes


def main() -> int:
    parser = argparse.ArgumentParser(description="Execute frozen real ER2-R4 spatial HAC / Conley inference.")
    parser.add_argument("--worker", type=Path)
    parser.add_argument("--output-root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.worker:
        run_worker(args.worker)
        return 0
    hashes = check_existing() if args.check else build(args.output_root.resolve())
    lock = json.loads((args.output_root.resolve() / LOCK).read_text(encoding="utf-8"))
    print("R4P_FROZEN_PREFLIGHT=PASS")
    print(f"SAMPLE_GEOMETRY_COVERAGE={lock['sample_geometry_coverage']['status']}")
    print("R4_EXECUTED=TRUE")
    print(f"R4_RESULT_ROWS={lock['result_row_count']}")
    print(f"R4_COVARIANCE_MATRICES={lock['covariance_matrix_count']}")
    print(f"R4_INVALID_VARIANCE_COUNT={lock['invalid_variance_inventory']['count']}")
    print(f"R4_TWO_RUN_REPRODUCIBILITY={lock['two_run_reproducibility']['status']}")
    for relative, digest in hashes.items():
        print(f"SHA256 {relative} {digest}")
    print(f"ER2_R4_RESULTS_LOCK_SHA256={hashes[LOCK.as_posix()]}")
    print(f"FINAL_VERDICT={lock['final_verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
