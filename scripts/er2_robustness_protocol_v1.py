from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ER1_SHA = "43de46ecd46248f1e4e2822a30e69cfadbc8260f"
ED1_SHA = "ed1c7cb79e7842356abd41f7a7af60d2fac1b5a6"
ER1_BRANCH = "phase/er1-primary-real-results-v1"
ED1_BRANCH = "phase/ed1-econometric-design-master-v1"
ER1_TAG = "er1-primary-real-results-v1-freeze"
ED1_TAG = "ed1-econometric-design-master-v1-freeze"
NUMERICAL_IDENTITY = "40e0f58269dda309e83a1fa3da17ef4d5dc5523efc72a666f734d0ebacb76b24"
REPORTING_IDENTITY = "83eea5e179b5e3504bd1144d744dcdbeddbbdf6a554f4d10ab03b92a30278841"
CLAIM_CEILING = "EMPIRICAL_ASSOCIATION_CLIMATE_RESPONSE_ONLY"
FINAL_VERDICT = "ER2P_PASS_ROBUSTNESS_PROTOCOL_READY_FOR_DIRECTOR_FREEZE_DECISION"
CONFIG_REL = Path("config/econometrics/er2_robustness_protocol_v1.json")
REPORT_REL = Path("outputs/econometrics/ER2P_ROBUSTNESS_PROTOCOL_REPORT.md")
TIERS_REL = Path("outputs/econometrics/ER2P_TIER_CONTRACTS.csv")
SCRIPT_REL = Path("scripts/er2_robustness_protocol_v1.py")
TEST_REL = Path("tests/test_er2_robustness_protocol_v1.py")
OUTPUT_RELS = (CONFIG_REL, REPORT_REL, TIERS_REL)
CANDIDATE_RELS = (*OUTPUT_RELS, SCRIPT_REL, TEST_REL)
ED1_CONFIG_REL = Path("config/econometrics/econometric_design_master_v1.json")
ED1_HIERARCHY_REL = Path("outputs/econometrics/ED1_ROBUSTNESS_HIERARCHY.csv")
ER1_LOCK_REL = Path("outputs/econometrics/ER1_PRIMARY_RESULTS_LOCK.json")
FROZEN_HASHES = {
    "config/econometrics/econometric_design_master_v1.json": "feaddf35700a84592ba024ae1fb9e4c9419e00672828fdb7cb29f2775d933c6d",
    "config/exposure_adjudication/primary_transient_exposure_v1.json": "283d57a21ba23c30c43f63e4c5327496ab59d760d8ca44a609b365151222a285",
    "config/joint_c0/outcome_decision_integration_v1.json": "53158bdb19d29de772f5061c0b110079500ff7a6d0b86e42b403879ed65b9899",
    "config/outcome/transient_campaign_outcome_v1.json": "b41b96bf307e066b819365e59a93c59050b3151293ac36a72303401bd00766ba",
    "data/processed/climate/district_boundaries_piura.geojson": "d966d2a38e80d6575490be32bde2e39b7db66a3c6e99b240e9c21458766d099b",
    "data/processed/outcomes/transient_campaign_outcomes_master.csv": "9cae62fb1417fa41274f6d504515571abd428b71fecaa0d138d3b786aa538760",
    "data/processed/panel_master.csv": "ab9b4ce53c008a1bc3ceb7d3e4c5d617d2544ad48632b747079c33e8b95d1214",
    "data/processed/phenology/perennial_exposures_long.parquet": "3fde5c7fc7a00f4c6600a18f60935bad213408ffa2ba3bac5828603e46984714",
    "data/processed/phenology/phenology_windows_frozen.csv": "ea25d949be9834a9e35352d970bb1b2172cac7d49db7eabb101ddfde9cfb657d",
    "data/processed/phenology/transient_campaign_exposures_strict.parquet": "349413312568d0d423675bf58320ade41d2d9e700f138e7fbec55fc580bc1fb5",
    "data/processed/phenology/transient_econometric_exposures_v1.parquet": "ed90c70a7538318234a0390176b468a66f8a24a99fa59717efe5e8974cf09a67",
    "outputs/econometrics/ED1_ECONOMETRIC_DESIGN_REPORT.md": "49d2d5bdd2d0871c8f868902be197fda6228423a4f1577b83f47eea34ecc8b34",
    "outputs/econometrics/ED1_INFERENCE_MATRIX.csv": "5cabcf5ab6d7cba1b6bf765e7727f9de1f090cc9b8a503364582a539701c7fab",
    "outputs/econometrics/ED1_MODEL_CONTRACTS.csv": "7dcd316c7b47b3a2e15939ed25dea8e034f1ca7c5076013c7640ef11da74cbcf",
    "outputs/econometrics/ED1_ROBUSTNESS_HIERARCHY.csv": "87959f394c3b6d486523e216dc61a0a7fca29a99d2e688ac5e80317162a4c3e1",
    "outputs/econometrics/ED1_X_GEOMETRY.csv": "08d569170ebc5bc3a5a4a35cdc702807be46a34df371e9363af510d7d0cca962",
    "outputs/exposure_adjudication/E1_CANDIDATE_MATRIX.csv": "09bca9fb778759fc0b66656e6057d0f99daf0c9265be1f2b2eb1eb688e226e73",
    "outputs/exposure_adjudication/E1_PRIMARY_TRANSIENT_EXPOSURE_REPORT.md": "085c5efb0f8abbd9f7f9443f28ed6d4d26fe5af3289a94a27219937b12883b91",
    "outputs/exposure_adjudication/E1_SUPPORT_OVERLAY.csv": "b59894c59485b6c4c92de8be0424f1f6c6211b333ea7609696874b457ac567a8",
    "outputs/joint_c0/C0_JOINT_REPORT.md": "92e4902b0f5ee4cc8a4ef4411ef741efe79399a7a83398cbe177c7b4fa1ad582",
    "outputs/qa/panel_support.csv": "b57fde70640d112c410f48164a27bf6e80ca310ae4dfdf2c3a93296f767564c6",
    "scripts/econometric_design_master_v1.py": "69fb1b1f0a1d7c4ec7791fdfa2d3cfb20d62b4ed0f6348b155155523b6b48195",
    "scripts/primary_transient_exposure_v1.py": "e53677b3284dd4d8c564838fd868d094e675705fc5d7baf56748ec38dc7dc3a8",
    "tests/test_econometric_design_master_v1.py": "02b68ede20688775b03d2c0d05914485a513f0f17265cc49bbcb160c7db444d8",
    "tests/test_primary_transient_exposure_v1.py": "867150d91d094e05939a7f68a1710787325e2eb5962cca3beeef20e42a11e522",
    "outputs/econometrics/ER1_PRIMARY_COEFFICIENTS.csv": "37fa03a2e860f86277510a5ff3b66ca475fc02d277ea1dd6e18156f719c23480",
    "outputs/econometrics/ER1_PRIMARY_JOINT_TESTS.csv": "8d00e0ef866488c8f7ce7a418d58ae165e87f05053db9861fed1b0f181e412e3",
    "outputs/econometrics/ER1_PRIMARY_SAMPLE_AUDIT.csv": "d5a2b42b7f8f68be5a387c9726f76d081c83e1b242fea2edfba829f963040854",
    "outputs/econometrics/ER1_PRIMARY_ESTIMATION_REPORT.md": "2caa57a6836363f1187d9cff9da0c70a02a81a96df1fc91af27ca97a8146a615",
    "outputs/econometrics/ER1_PRIMARY_RESULTS_LOCK.json": "83eea5e179b5e3504bd1144d744dcdbeddbbdf6a554f4d10ab03b92a30278841",
    "scripts/er1_primary_real_estimation_v1.py": "4df41b3f1b151d0dc956447e0bbe773391d382ad5282ad5f38124ad7b98f99c9",
    "tests/test_er1_primary_real_estimation_v1.py": "0755a178efb90f0394068d98c63e098d1ee5c954fe0dc38ebbabd4a7cac57ba8"
}
TIER_ORDER = (
    "R1_LEVEL_CLIMATE_FAMILY",
    "R2_STANDARDIZED_ANOMALY_COMPARABILITY",
    "R3_RESTRICTED_WILD_CLUSTER_BOOTSTRAP",
    "R4_SPATIAL_HAC",
    "R5_LEAVE_ONE_PERIOD_OUT_ALL_PERIODS",
    "R6_B3_STRICT_EXPOSURE",
)
TRANSIENT = ("14010020000", "14010070000")
PERENNIAL = ("13010210000", "13010170102", "15010040000")
CROP_ORDER = (*TRANSIENT, *PERENNIAL)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False) + "\n").encode("utf-8")


def git_text(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def read_json(relative: Path) -> dict:
    return json.loads((ROOT / relative).read_bytes())


def verify_frozen_inputs() -> dict:
    actual = {relative: sha256_file(ROOT / relative) for relative in FROZEN_HASHES}
    require(actual == FROZEN_HASHES, "ER2P_FAIL_UPSTREAM_IMMUTABILITY: frozen input hash mismatch")
    return actual


def forbidden_result_paths(root: Path) -> list[str]:
    found = []
    for directory in ("outputs", "data/processed"):
        base = root / directory
        if base.exists():
            found.extend(
                p.relative_to(root).as_posix() for p in base.rglob("*")
                if p.is_file() and p.name.upper().startswith("ER2_")
            )
    return sorted(found)


def preflight() -> dict:
    for branch, tag, expected in ((ER1_BRANCH, ER1_TAG, ER1_SHA), (ED1_BRANCH, ED1_TAG, ED1_SHA)):
        require(
            git_text("rev-parse", branch) == git_text("rev-parse", "origin/" + branch)
            == git_text("rev-parse", tag + "^{}") == expected,
            "ER2P_FAIL_UPSTREAM_IMMUTABILITY: frozen reference mismatch",
        )
    require(git_text("branch", "--show-current") == ER1_BRANCH, "ER2P requires frozen ER1 branch")
    require(git_text("rev-parse", "HEAD") == ER1_SHA, "ER2P requires frozen ER1 HEAD")
    require(git_text("rev-parse", "HEAD^") == ED1_SHA, "ER1 parent is not frozen ED1")
    require(not git_text("diff", "--name-only"), "Tracked modifications prohibited")
    require(not git_text("diff", "--cached", "--name-only"), "Staging prohibited")
    untracked = set(git_text("ls-files", "--others", "--exclude-standard").splitlines())
    require(untracked <= {p.as_posix() for p in CANDIDATE_RELS}, "Unauthorized candidate path")
    verify_frozen_inputs()
    require(not forbidden_result_paths(ROOT), "ER2P_FAIL_PRIMARY_RESULTS_CONTAMINATION: ER2 result artifact")
    lock = read_json(ER1_LOCK_REL)
    tables = {
        relative: sha256_file(ROOT / relative)
        for relative in lock["result_table_sha256"]
    }
    require(len(tables) == 3 and tables == lock["result_table_sha256"], "ER1 table identity mismatch")
    identity = sha256_bytes(json.dumps(tables, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    require(identity == lock["er1_numerical_results_identity"]["sha256"] == NUMERICAL_IDENTITY,
            "ER2P_FAIL_PRIMARY_RESULTS_CONTAMINATION: numerical identity mismatch")
    require(sha256_file(ROOT / ER1_LOCK_REL) == REPORTING_IDENTITY, "ER1 reporting identity mismatch")
    require(lock["outcome_unsealed"] is True and lock["model_revision_after_results"] is False,
            "ER1 knowledge/model contract mismatch")
    require(lock["robustness_tiers_executed"] == 0, "Robustness results already known")
    ed1 = read_json(ED1_CONFIG_REL)
    require([r["TIER"] for r in ed1["robustness_hierarchy"]][1:] == list(TIER_ORDER),
            "ER2P_FAIL_HIERARCHY_DRIFT")
    with (ROOT / ED1_HIERARCHY_REL).open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    require(rows == [{k: str(v) for k, v in r.items()} for r in ed1["robustness_hierarchy"]],
            "ED1 hierarchy CSV/config disagreement")
    return {
        "status": "PASS", "er1_freeze_sha": ER1_SHA, "ed1_freeze_sha": ED1_SHA,
        "er1_numerical_results_identity": identity, "er1_reporting_lock_identity": REPORTING_IDENTITY,
        "frozen_inputs_verified": len(FROZEN_HASHES), "primary_results_known": True,
        "robustness_results_known": False, "robustness_models_executed": 0,
        "remote_verification": "OFFLINE_TRACKING_REFS_ONLY_LIVE_LS_REMOTE_REQUIRED_AT_DIRECTOR_RETURN",
    }


def lifecycle_inventory() -> list[dict]:
    rows = read_json(ED1_CONFIG_REL)["previous_full_suite"]["nonpass_adjudication"]
    rows = [dict(row) for row in rows]
    for module, cls, parent in (
        ("test_econometric_design_master_v1", "EconometricDesignMasterV1Tests", "E1"),
        ("test_er1_primary_real_estimation_v1", "ER1PrimaryRealEstimationV1Tests", "ED1"),
    ):
        rows.append({
            "result": "ERROR", "test": f"setUpClass ({module}.{cls})",
            "category": "EXPECTED_HISTORICAL_LIFECYCLE_STATE",
            "reason": f"Historical authoring setUpClass requires the frozen {parent} build parent, not active ER1.",
        })
    return sorted(rows, key=lambda row: (row["result"], row["test"]))


def tier_contracts(ed1: dict) -> list[dict]:
    crops = {row["CROP_CODE"]: row for row in ed1["crop_model_contracts"]}
    common = {
        "outcome_scale": "YIELD_LEVEL_TM_PER_HA", "district_fe": "REQUIRED",
        "period_fe": "REQUIRED", "weighting": "UNWEIGHTED_PRIMARY_ESTIMATION",
        "functional_form": "LINEAR_ADDITIVE", "windows": "EXACT_ED1_FROZEN",
        "primary_replacement": "PROHIBITED", "claim_ceiling": CLAIM_CEILING,
        "status": "NOT_EXECUTED", "execution_authorized": False,
        "er1_numerical_results_identity": NUMERICAL_IDENTITY,
    }
    details = [
        {
            "role": "CROP_SPECIFIC_LEVEL_ROBUSTNESS_AND_FE_EQUIVALENCE_DIAGNOSTIC",
            "family": "LEVEL", "same_primary_sample": True,
            "regressors": ["RAIN_MM", "TMAX_C", "TMIN_C"],
            "distinct_crops": list(TRANSIENT), "distinct_models": 2, "distinct_coefficients": 6,
            "diagnostic_crops": list(PERENNIAL), "diagnostics_not_distinct_models": 3,
            "perennial_status_on_exact_equivalence": "FE_EQUIVALENT_DIAGNOSTIC_NOT_DISTINCT_MODEL",
            "perennial_equivalence": {
                "transformed_design_check": "ED1_FROZEN_GEOMETRY_TOLERANCE",
                "ed1_design_absolute_tolerance": 1e-9,
                "exact_coefficient_and_fitted_value_equality_required_for_status": True,
                "record_exact_equality_separately_from_tolerance_diagnostic": True,
                "on_nonexact_equality": "HOLD_FOR_ADJUDICATION_NO_DISTINCT_ROBUSTNESS_PROMOTION",
                "distinct_robustness_count_contribution": 0,
            },
            "inference": "CR2_SATTERTHWAITE_AND_CROP_AHT",
            "multiplicity": "HOLM_STEP_DOWN_WITHIN_CROP_R1_COEFFICIENT_P_VALUES",
            "confidence_intervals": "UNADJUSTED_95_PERCENT_CR2_SATTERTHWAITE",
        },
        {
            "role": "STANDARDIZED_X_COMPARABILITY", "family": "STANDARDIZED_ANOMALY",
            "same_primary_sample": True, "models": 5, "coefficient_count": 21,
            "regressors": ["RAIN_Z", "TMAX_Z", "TMIN_Z"],
            "time_variants": "EXACT_ED1_T_AND_T_MINUS_1_WHERE_APPLICABLE",
            "inference": "CR2_SATTERTHWAITE_AND_CROP_AHT",
            "interpretation": "ONE_LOCAL_CLIMATE_SD_CHANGE_IN_NATIVE_CROP_YIELD_UNITS",
            "fully_standardized_effect_sizes": "NOT_CLAIMED",
            "cross_crop_magnitude_ranking": "PROHIBITED", "cross_crop_significance_ranking": "PROHIBITED",
            "multiplicity": "HOLM_STEP_DOWN_WITHIN_CROP_R2_COEFFICIENT_P_VALUES",
            "confidence_intervals": "UNADJUSTED_95_PERCENT_CR2_SATTERTHWAITE",
        },
        {
            "role": "INFERENCE_ONLY", "family": "PHYSICAL_ANOMALY", "same_primary_sample": True,
            "coefficients": "EXACT_ER1_PRIMARY_UNCHANGED", "cluster": "DISTRICT",
            "restricted": True, "null_imposed": True, "weights": "RADEMACHER",
            "replications": 9999, "seed": 20260903,
            "finite_replication_correction": "(1 + exceedances)/(B + 1)",
            "coefficient_tests": 21, "coefficient_statistic": "ABSOLUTE_BOOTSTRAP_T",
            "joint_tests": 5, "joint_null": "ALL_PRIMARY_CLIMATE_COEFFICIENTS_EQUAL_ZERO_WITHIN_CROP",
            "joint_statistic": "BOOTSTRAP_WALD_F", "joint_null_matches_aht": True,
            "multiplicity": "WITHIN_CROP_WCR_COEFFICIENT_P_VALUES",
            "mixed_cr2_wcr_holm_family": "PROHIBITED",
            "reported_fields": ["ER1_BETA_REFERENCE", "ER1_CR2_P_REFERENCE", "WCR_P", "WITHIN_CROP_HOLM_WCR_P"],
            "determinism": {
                "rng": "NUMPY_GENERATOR_PCG64", "seed_reset": "EACH_CROP_CONTRAST_AND_JOINT_TEST",
                "cluster_order": "SORTED_UBIGEO", "row_order": "SORTED_UBIGEO_THEN_FROZEN_PERIOD",
                "batch_size": 1000, "weight_draw_layout": "N_CLUSTERS_BY_BATCH_INT8_ZERO_ONE_MAPPED_TO_MINUS_PLUS_ONE",
                "coefficient_order": "FROZEN_ED1_REGRESSOR_ORDER", "crop_order": list(CROP_ORDER),
                "exceedance": "GREATER_THAN_OR_EQUAL_TO_OBSERVED_STATISTIC",
            },
            "implementation_requirement": (
                "Frozen ED1 API targets FIRST_CLIMATE_COEFFICIENT or ALL_CLIMATE_COEFFICIENTS only. "
                "Future coefficient-target adapter must cover each named coefficient without changing "
                "the full model and must validate contrast/permutation equivalence on synthetic data "
                "before real R3 execution. No adapter or bootstrap is executed during ER2P."
            ),
            "invalid_replications": "REQUIRE_ZERO_OTHERWISE_HOLD_NO_DROPPING_OR_REDRAWING_OR_DENOMINATOR_CHANGE",
        },
        {
            "role": "ASYMPTOTIC_SPATIAL_HAC_ROBUSTNESS_DIAGNOSTIC",
            "family": "PHYSICAL_ANOMALY", "same_primary_sample": True,
            "coefficients": "EXACT_ER1_PRIMARY_UNCHANGED", "residual_specification": "EXACT_ER1_PRIMARY",
            "bandwidths_km": [50, 100, 150], "kernel": "BARTLETT",
            "coordinates": "EPSG:32717_DISTRICT_CENTROIDS",
            "coordinate_construction": "PROJECT_FROZEN_DISTRICT_GEOMETRY_THEN_CENTROID_AS_ED1",
            "distance": "EUCLIDEAN_PROJECTED_METRES_DIVIDED_BY_1000",
            "pairing": "SAME_PERIOD_ONLY", "bandwidth_selection": "PROHIBITED",
            "coefficient_bandwidth_rows": 63, "normal_critical_value": 1.959963984540054,
            "reported_fields": ["ER1_BETA_REFERENCE", "CONLEY_SE", "Z", "TWO_SIDED_ASYMPTOTIC_P", "NORMAL_CI95_LOWER", "NORMAL_CI95_UPPER"],
            "p_value": "2_TIMES_STANDARD_NORMAL_SURVIVAL_ABS_Z",
            "interval": "ER1_BETA_PLUS_MINUS_1.959963984540054_TIMES_CONLEY_SE",
            "satterthwaite_df": "NOT_CLAIMED",
            "multiplicity": "DIAGNOSTIC_ROBUSTNESS_NO_NEW_CONFIRMATORY_FWER_CLAIM",
            "p_values": "RAW_ALL_THREE_BANDWIDTHS_NO_SEPARATE_HOLM_FAMILIES",
            "replaces_primary_cr2": False, "nonpositive_or_nonfinite_variance": "HOLD_NO_CLIPPING_OR_COVARIANCE_SUBSTITUTION",
        },
        {
            "role": "ALL_PERIOD_INFLUENCE_DESCRIPTION", "family": "PHYSICAL_ANOMALY",
            "sample_change": "ONE_ENTIRE_PERIOD_OMITTED_PER_MODEL_ONLY",
            "expected_models_by_crop": {code: crops[code]["PERIODS"] for code in CROP_ORDER},
            "expected_models": 38, "same_regressors": True, "remaining_period_fe": "REQUIRED",
            "period_source": "SORTED_UNIQUE_PERIODS_OF_EACH_EXACT_ER1_ANALYTICAL_SAMPLE",
            "period_id_by_regime": {"transient": "CAMPAIGN_ID", "perennial": "REFERENCE_PERIOD_ID"},
            "report_all_periods": True, "mandatory_named_reporting": ["LEAVE_2017_OUT", "LEAVE_2023_OUT"],
            "named_transient_mapping": {"LEAVE_2017_OUT": "2016/2017", "LEAVE_2023_OUT": "2022/2023"},
            "named_perennial_mapping": {"LEAVE_2017_OUT": "2017", "LEAVE_2023_OUT": "2023"},
            "second_period_omission": "PROHIBITED", "influential_district_deletion": "PROHIBITED",
            "summary_metrics": [
                "PRIMARY_BETA_REFERENCE", "MIN_LOO_BETA", "MAX_LOO_BETA", "MEDIAN_LOO_BETA",
                "POSITIVE_COUNT", "NEGATIVE_COUNT", "SIGN_REVERSALS_RELATIVE_TO_PRIMARY",
                "MAX_ABSOLUTE_BETA_DEVIATION", "PERIOD_CAUSING_MAX_ABSOLUTE_DEVIATION",
            ],
            "positive_negative_rule": "STRICTLY_GREATER_LESS_THAN_ZERO_REPORT_EXACT_ZERO_COUNT_SEPARATELY",
            "sign_reversal_rule": "PRODUCT_OF_LOO_AND_PRIMARY_BETA_STRICTLY_NEGATIVE",
            "zero_primary_sign_rule": "REVERSAL_COUNT_NULL_WITH_NOT_DEFINED_PRIMARY_ZERO_STATUS",
            "max_deviation_tie_rule": "REPORT_ALL_TIED_PERIOD_IDS_SORTED_NO_POST_RESULT_TIE_SELECTION",
            "failed_omission": "RETAIN_STATUS_ROW_HOLD_FOR_ADJUDICATION_NO_REPLACEMENT_OR_PARTIAL_DISTRIBUTION_CLAIM",
            "crop_aht_range": "NOT_REQUESTED_OPTIONAL_EXTENSION_NOT_EXECUTED",
            "stability_classification": "DESCRIPTIVE_NO_ARBITRARY_PASS_FAIL_THRESHOLD",
            "multiplicity": "DESCRIPTIVE_COEFFICIENT_DISTRIBUTIONS_NO_SIGNIFICANCE_VOTE_COUNTING",
        },
        {
            "role": "STRICT_CAMPAIGN_ATTRIBUTION_SENSITIVITY_SEVERE_SUPPORT_LIMITATION",
            "family": "PHYSICAL_ANOMALY",
            "sample_change": "EXACT_D0_OUTCOME_AND_B3_VALID_EXPOSURE_INTERSECTION",
            "rice": {
                "crop_code": "14010020000", "status": "ESTIMABLE_WITH_SEVERE_SUPPORT_LIMITATION",
                "expected_observations": 31, "expected_districts": 12, "expected_periods": 7,
                "required_within_rank": 3, "coefficient_count": 3, "campaign_fe": "REQUIRED",
                "inference": "CR2_SATTERTHWAITE_AHT_ONLY_IF_NUMERICALLY_ADMISSIBLE",
                "admissibility": "FULL_WITHIN_RANK_VALID_CR2_ADJUSTMENTS_POSITIVE_FINITE_SE_AND_DF_VALID_FINITE_AHT",
                "on_inadmissibility": "R6_RICE_NOT_INFERENTIALLY_ADMISSIBLE",
                "may_weaken_fe": False,
            },
            "mad": {"crop_code": "14010070000", "status": "NOT_ESTIMABLE_UNDER_PRIMARY_DESIGN", "estimate": False, "substitute_model": "PROHIBITED"},
            "perennials": "NOT_APPLICABLE", "prominent_support_comparison_to_er1": True,
            "disagreement_proves_correct_exposure": False,
            "multiplicity": "DIAGNOSTIC_RAW_CR2_AND_AHT_NO_NEW_CONFIRMATORY_FWER_CLAIM",
        },
    ]
    tiers = []
    for order, (tier_id, detail) in enumerate(zip(TIER_ORDER, details), 1):
        tiers.append({
            **common, **detail, "order": order, "tier_id": tier_id, "tier": f"R{order}",
            "previous_tier": None if order == 1 else f"R{order - 1}",
            "next_tier": None if order == 6 else f"R{order + 1}",
            "global_five_crop_fwer": "NOT_CLAIMED",
            "multiplicity_adjusted_confidence_intervals": "NOT_CONSTRUCTED_NOT_CLAIMED",
        })
    return tiers


def build_protocol() -> dict:
    ed1 = read_json(ED1_CONFIG_REL)
    tiers = tier_contracts(ed1)
    lock_fields = [
        "schema_version", "er1_freeze_sha", "ed1_freeze_sha", "er1_numerical_results_identity",
        "er1_reporting_lock_sha256", "er2p_protocol_sha256", "tier_id", "tier_order",
        "exact_input_sha256", "exact_model_contract", "tier_contract_sha256", "implementation_sha256",
        "environment", "results", "interpretation_firewall", "previous_tier_lock_sha256",
        "completion_status", "next_tier_authorization_status",
    ]
    return {
        "project": "ENSO_EL_NINO_2026_2027_AGRICULTURE_PIURA",
        "gate": "ER2P_PRESPECIFIED_ROBUSTNESS_EXECUTION_PROTOCOL_MASTER_V1", "schema_version": "1.0.0",
        "status": "CANDIDATE_PROTOCOL_NOT_FROZEN", "final_verdict": FINAL_VERDICT,
        "governing_state": {
            "er1_freeze_sha": ER1_SHA, "er1_status": "PASS_FROZEN", "er1_tag": ER1_TAG,
            "ed1_freeze_sha": ED1_SHA, "ed1_status": "PASS_FROZEN", "ed1_tag": ED1_TAG,
            "er1_numerical_results_identity": NUMERICAL_IDENTITY, "er1_reporting_lock_sha256": REPORTING_IDENTITY,
        },
        "timing": {
            "primary_results_known": True, "robustness_results_known": False,
            "robustness_hierarchy_timing": "PRE_OUTCOME_FROZEN_IN_ED1",
            "robustness_operationalization_timing": "POST_PRIMARY_RESULTS_PRE_ROBUSTNESS_RESULTS",
            "outcome_unsealed": True, "claim_all_operational_details_were_pre_outcome": False,
        },
        "frozen_input_sha256": FROZEN_HASHES,
        "ed1_hierarchy_unchanged": ed1["robustness_hierarchy"],
        "crop_model_contracts": ed1["crop_model_contracts"],
        "robustness_order": list(TIER_ORDER), "tiers": tiers,
        "tier_lock_governance": {
            "locking": "MANDATORY_BEFORE_NEXT_TIER",
            "sequence": [item for k in range(1, 7) for item in (f"EXECUTE_R{k}", f"LOCK_R{k}")],
            "cross_contamination": "PROHIBITED", "primary_replacement": "PROHIBITED",
            "lock_name_template": "ER2_Rk_RESULTS_LOCK", "hash_name_template": "ER2_Rk_RESULTS_LOCK_SHA256",
            "required_fields": lock_fields,
            "serialization": "SORT_KEYS_INDENT_2_ENSURE_ASCII_ALLOW_NAN_FALSE_UTF8_LF_ONE_FINAL_LF_NO_BOM",
            "hash": "SHA256_OF_EXACT_SERIALIZED_BYTES_EXTERNAL_TO_OWN_LOCK",
            "previous_lock": "R1_NULL_R2_TO_R6_EXACT_PREDECESSOR_SHA256",
            "results_schema": {
                "required": ["artifact_sha256", "expected_inventory", "observed_inventory", "validation_status", "nonadmissible_status_rows"],
                "coverage": "COMPLETE_PRESPECIFIED_TIER_INVENTORY_NO_SELECTIVE_OMISSION",
                "all_result_tables_required_reference_column": "ER1_NUMERICAL_RESULTS_IDENTITY",
                "nonfinite_serialization": "NULL_WITH_EXPLICIT_STATUS_NOT_NAN_OR_SILENT_ZERO",
            },
            "before_next_tier": [
                "SEPARATE_DIRECTOR_EXECUTION_AUTHORIZATION_REQUIRED",
                "CURRENT_PROTOCOL_AND_TIER_CONTRACT_HASHES_EQUAL_LOCKED_PREEXECUTION_HASHES",
                "PREDECESSOR_LOCK_EXISTS_AND_HASH_RECOMPUTES_EXACTLY",
                "PREDECESSOR_INPUT_AND_RESULT_ARTIFACT_HASHES_RECOMPUTE_EXACTLY",
                "PREDECESSOR_COMPLETE_WITH_NO_UNRESOLVED_FAILURES",
                "PREDECESSOR_NEXT_TIER_AUTHORIZATION_STATUS_AUTHORIZED_UNDER_UNCHANGED_PROTOCOL",
            ],
            "next_tier_authorization_status_enum": ["NOT_AUTHORIZED", "HOLD", "AUTHORIZED_UNDER_UNCHANGED_PROTOCOL", "COMPLETE_NO_NEXT_TIER"],
            "initial_next_tier_authorization_status": "NOT_AUTHORIZED",
            "completion_status_enum": ["COMPLETE", "HOLD", "R6_COMPLETE_WITH_DECLARED_NONADMISSIBILITY"],
            "timestamp_or_runtime_path_content": "PROHIBITED",
            "environment": "VERSIONS_AND_NUMERICAL_BACKEND_METADATA_NOT_WALL_CLOCK_TIMING",
            "post_lock_revision": "PROHIBITED_NEW_SCIENTIFIC_GATE_REQUIRED_NO_OVERWRITE",
            "one_controlled_session_permitted": True, "separate_commit_per_tier_required": False,
            "unexpected_failure": "LOCK_FAILURE_AND_HALT_NO_NEXT_TIER_NO_SILENT_FALLBACK",
            "r6_terminal_rule": "MAD_STRUCTURAL_NONESTIMABILITY_AND_DECLARED_RICE_INADMISSIBILITY_ARE_REPORTED_NOT_SUBSTITUTED",
        },
        "concordance": {
            "role": "DESCRIPTIVE_MULTIDIMENSIONAL_NOT_CONFIRMATORY",
            "rows": "ALL_21_ER1_PRIMARY_COEFFICIENT_IDENTIFIERS",
            "fields": ["PRIMARY_BETA_REFERENCE", "PRIMARY_SIGN", "R1_SIGN_WHERE_DISTINCT", "R2_SIGN",
                       "WCR_P", "CONLEY_CI_ZERO_INCLUSION_50_100_150", "R5_SIGN_REVERSAL_COUNT",
                       "R5_BETA_RANGE", "R6_RICE_RESULT_WHERE_ADMISSIBLE"],
            "nonapplicability": "EXPLICIT_STATUS_NOT_ZERO_OR_FAILED_ROBUSTNESS_VOTE",
            "robustness_score": "PROHIBITED", "vote_counting": "PROHIBITED",
            "prohibited_summaries": ["ROBUSTNESS_SCORE", "NUMBER_OF_SIGNIFICANT_MODELS", "MAJORITY_SIGNIFICANT", "5_OF_7_ROBUST"],
        },
        "result_specific_firewalls": {
            "banana": "NO_SPECIAL_TESTS_NONLINEAR_TMIN_BANDWIDTH_OR_PERIOD_SELECTION",
            "lemon": "NO_SPECIAL_TESTS_OR_POST_PRIMARY_SPECIFICATION_EXPANSION",
            "known_primary_results_may_change_contract": False,
            "selection_by_p_sign_ci_fit_or_biological_narrative": "PROHIBITED",
        },
        "claim_ceiling": CLAIM_CEILING,
        "allowed_language": ["CONSISTENCY", "SENSITIVITY", "SIGN_STABILITY", "INFERENTIAL_SENSITIVITY", "SPATIAL_COVARIANCE_SENSITIVITY", "EXPOSURE_DEFINITION_SENSITIVITY"],
        "execution_firewall": {
            **{tier: "NOT_EXECUTED" for tier in TIER_ORDER},
            **{key: "NOT_EXECUTED" for key in ("ENSO_SCENARIOS", "GVP", "VAR_CVAR", "A1_A2", "OPTIMIZATION")},
            "robustness_models_executed": 0, "primary_estimation_executed": False,
            "raw_outcome_values_parsed": False, "primary_numerical_results_copied_to_protocol": False,
        },
        "full_suite_policy": {
            "accepted_inventory": lifecycle_inventory(),
            "historical_lifecycle_nonpasses": 47, "active_phase_firewalls": 6,
            "baseline_before_er2p_tests": {"run": 655, "pass": 602, "fail": 50, "error": 3},
            "require_exact_identifier_and_result_type_match": True,
            "require_traceback_cause_review": True, "real_regressions_required": 0,
            "unresolved_failures_required": 0, "historical_tests_may_be_weakened": False,
        },
        "future_artifact_paths_not_created_in_er2p": [
            "outputs/econometrics/" + name for name in (
                "ER2_R1_LEVEL_RESULTS.csv", "ER2_R2_STANDARDIZED_RESULTS.csv", "ER2_R3_WCR_RESULTS.csv",
                "ER2_R3_WCR_JOINT_TESTS.csv", "ER2_R4_CONLEY_RESULTS.csv", "ER2_R5_LOPO_RESULTS.csv",
                "ER2_R5_LOPO_SUMMARY.csv", "ER2_R6_B3_RESULTS.csv", "ER2_ROBUSTNESS_CONCORDANCE.csv",
                "ER2_ROBUSTNESS_REPORT.md",
            )
        ] + [f"outputs/econometrics/ER2_R{k}_RESULTS_LOCK.json" for k in range(1, 7)],
        "er2p_freeze_authorized": False, "robustness_execution_authorized": False,
        "next_action": "RETURN_TO_SCIENTIFIC_DIRECTOR_FOR_ER2P_FREEZE_DECISION_IF_PASS",
    }


def validate_protocol(protocol: dict) -> None:
    require(json_bytes(protocol) == json_bytes(build_protocol()), "ER2P_FAIL_TIER_CONTRACT_INCONSISTENCY")


def adjudicate_nonpasses(observed: list[dict], protocol: dict) -> dict:
    expected = {(r["result"], r["test"]): r for r in protocol["full_suite_policy"]["accepted_inventory"]}
    actual = {(r["result"], r["test"]) for r in observed}
    unexpected = sorted(actual - set(expected))
    missing = sorted(set(expected) - actual)
    duplicates = len(observed) != len(actual)
    return {
        "status": "PASS" if not unexpected and not missing and not duplicates else "FAIL",
        "unexpected": unexpected, "missing": missing, "duplicate_inventory": duplicates,
        "new_nonpasses_or_type_changes": len(unexpected),
        "cause_review_required_separately": True,
    }


def render_outputs() -> dict[Path, bytes]:
    protocol = build_protocol()
    validate_protocol(protocol)
    config_payload = json_bytes(protocol)
    stream = io.StringIO(newline="")
    fields = ["ORDER", "TIER", "ROLE", "FAMILY", "MULTIPLICITY", "PREVIOUS_TIER", "NEXT_TIER",
              "EXECUTION_STATUS", "ER1_NUMERICAL_RESULTS_IDENTITY", "TIER_CONTRACT_SHA256"]
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for tier in protocol["tiers"]:
        writer.writerow(dict(zip(fields, (
            tier["order"], tier["tier_id"], tier["role"], tier["family"], tier["multiplicity"],
            tier["previous_tier"] or "NONE", tier["next_tier"] or "NONE", "NOT_EXECUTED",
            NUMERICAL_IDENTITY, sha256_bytes(json_bytes(tier)),
        ))))
    tier_payload = stream.getvalue().encode("utf-8")
    lines = [
        "# ER2P Prespecified Robustness Execution Protocol Master v1", "",
        "## Status and temporal disclosure", "",
        "Candidate protocol only; no ER2P freeze or robustness execution is authorized.",
        "ER1 primary results are known. Robustness results are not known.",
        "The hierarchy was frozen before outcomes in ED1. These operational details are formalized",
        "after primary results and before robustness results. Do not describe all details as pre-outcome.",
        "ER1 remains the sole PRIMARY specification. No primary numerical values are copied here.", "",
        f"ER1_FREEZE_SHA={ER1_SHA}", f"ED1_FREEZE_SHA={ED1_SHA}",
        f"ER1_NUMERICAL_RESULTS_IDENTITY={NUMERICAL_IDENTITY}",
        f"ER1_REPORTING_LOCK_SHA256={REPORTING_IDENTITY}",
        f"PROTOCOL_SHA256={sha256_bytes(config_payload)}", f"TIER_CONTRACTS_CSV_SHA256={sha256_bytes(tier_payload)}", "",
        "## Fixed architecture and ordered locks", "",
        "Order: R1 -> lock R1 -> R2 -> lock R2 -> R3 -> lock R3 -> R4 -> lock R4 -> R5 -> lock R5 -> R6 -> lock R6.",
        "Outcome level TM/ha, frozen crop windows, linear additive form, district and period FE, and",
        "unweighted estimation are retained. Only the designated tier component may change.",
        "All future result tables must reference the immutable ER1 numerical identity.",
        "No smaller p-value, preferred sign, narrower interval, model fit, or biological narrative",
        "may replace ER1 or change a later-tier contract. Cross-tier contamination is prohibited.", "",
    ]
    for tier in protocol["tiers"]:
        lines.extend([f"## {tier['tier_id']}", "", "Protocol fields below are requirements, not computed results.", "",
                      "```json", json.dumps(tier, sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False), "```", ""])
    lines.extend([
        "## Lock schema and failure handling", "",
        "Each future tier lock must contain the following required fields:", "",
        ", ".join(protocol["tier_lock_governance"]["required_fields"]), "",
        "Serialize sorted-key JSON as UTF-8, LF only, exactly one final LF, no BOM, no NaN,",
        "no timestamp or machine-specific runtime path. Record versions/backend metadata.",
        "Compute the SHA-256 outside its own lock, then record it in the next tier's predecessor field.",
        "R1 has no predecessor; R2-R6 must verify the immediately previous immutable lock, all input",
        "and result hashes, complete inventory, unchanged protocol/contract hashes and authorization.",
        "A hash alone is not authorization. A separate Director execution gate is required.",
        "Unexpected failures produce an explicit status and halt progression; no silent substitutions.",
        "Completed locks cannot be revised in response to later results. R6 MAD nonestimability and",
        "declared Rice inferential inadmissibility are terminal reported outcomes, not weaker models.",
        "One controlled future execution session is permitted; separate tier commits are not required.", "",
        "## Concordance and result-specific firewalls", "",
        "After all six locks, describe all 21 primary coefficient identities across sign, WCR, spatial",
        "interval inclusion, complete LOO distributions and applicable strict-support sensitivity.",
        "Do not compute a robustness score, count significant models, vote on a majority, or label",
        "'5 of 7 robust'. Nonapplicability is an explicit status, never a zero or a negative vote.",
        "Known Banana and Lemon results cannot create special tests, nonlinear terms, selected",
        "bandwidths or selected omissions. Do not rank crops by standardized-X coefficient magnitude.", "",
        f"CLAIM_CEILING={CLAIM_CEILING}",
        "Use consistency, sensitivity, sign stability, inferential sensitivity, spatial-covariance",
        "sensitivity or exposure-definition sensitivity. No causal robustness claim is authorized.", "",
        "## Implementation boundaries and audit", "",
        "This builder uses only the standard library: static contracts, hashes and Git identity checks.",
        "It neither imports econometric engines nor fits primary or robustness models.",
        "R3's future target-coefficient adapter is required because the frozen ED1 API exposes only",
        "first-coefficient and all-coefficient contrasts. It must be validated before real R3 execution.",
        "R1 exact numerical equality is not inferred from ED1's 1e-9 transformed-design tolerance.",
        "Nonexact equality requires adjudication and cannot promote equivalent models to distinct evidence.",
        "Repository baseline before the new tests: 655 run, 602 pass, 50 fail, 3 errors.",
        "The 53 expected nonpasses are enumerated with reasons in the protocol: 47 lifecycle and 6 phase firewalls.",
        "ED1 and ER1 class setup guards require E1 and ED1 authoring parents; the E1 rebuild requires S1.",
        "Compare exact identifiers AND result types and review traceback causes after the full suite.",
        "An unchanged historical inventory is not an all-green test suite. New or unexplained failures block ER2P.",
        "Historical scientific inputs, historical tests, README, main and all Git refs must remain unchanged.", "",
        "## Authorization", "",
        "ROBUSTNESS_RESULTS_KNOWN=FALSE", "ER2P_FREEZE_AUTHORIZED=NO", "ROBUSTNESS_EXECUTION_AUTHORIZED=NO",
        "ENSO_SCENARIOS=NOT_EXECUTED; GVP=NOT_EXECUTED; VAR_CVAR=NOT_EXECUTED; A1_A2=NOT_EXECUTED; OPTIMIZATION=NOT_EXECUTED",
        f"FINAL_VERDICT={FINAL_VERDICT}",
        "NEXT_ACTION=RETURN_TO_SCIENTIFIC_DIRECTOR_FOR_ER2P_FREEZE_DECISION_IF_PASS", "",
    ])
    return {CONFIG_REL: config_payload, REPORT_REL: "\n".join(lines).encode("utf-8"), TIERS_REL: tier_payload}


def run(output_root: Path = ROOT, check_only: bool = False) -> dict:
    preflight_result = preflight()
    payloads = render_outputs()
    target_root = output_root.resolve()
    targets = {relative: target_root / relative for relative in payloads}
    require(all(path.resolve().is_relative_to(target_root) for path in targets.values()), "Unsafe output target")
    if target_root != ROOT.resolve():
        require(not target_root.is_relative_to(ROOT.resolve()), "Use an external temporary output root")
        require(not target_root.joinpath(".git").exists(), "Do not write protocol outputs into another Git checkout")
    if check_only:
        for relative, payload in payloads.items():
            require(targets[relative].is_file() and targets[relative].read_bytes() == payload,
                    f"Candidate serialization mismatch: {relative}")
    else:
        for relative, payload in payloads.items():
            path = targets[relative]
            if path.exists() and path.read_bytes() == payload:
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
    return {
        "preflight": preflight_result, "protocol_artifact_sha256": {p.as_posix(): sha256_bytes(b) for p, b in payloads.items()},
        "mode": "CHECK_ONLY" if check_only else "BUILD_PROTOCOL_ONLY", "robustness_models_executed": 0,
        "final_verdict": FINAL_VERDICT,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build or audit ER2P protocol only; no estimation entry point.")
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--output-root", type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        result = run(args.output_root, args.check_only)
    except (RuntimeError, OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"ER2P_PREFLIGHT=FAIL: {exc}")
        return 1
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
