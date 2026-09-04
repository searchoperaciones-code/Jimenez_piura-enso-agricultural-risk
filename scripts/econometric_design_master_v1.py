from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import platform
import subprocess
from importlib.metadata import version as package_version
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import scipy
from scipy import stats
from pyproj import Transformer
from shapely.geometry import shape
from shapely.ops import transform


ROOT = Path(__file__).resolve().parents[1]

E1_FREEZE_SHA = "cdeb14bdda8bdebf33afdebcf0e135179bd2f485"
E1_BRANCH = "phase/e1-primary-transient-exposure-v1"
E1_TAG = "e1-primary-transient-exposure-v1-freeze"
S1_FREEZE_SHA = "2e5823e6aaf842dfd60da968e7423471d6b32f1d"
D0_FREEZE_SHA = "1598a09c9a871d81834164d7ee4383e25988d8a5"

E1_CONFIG_PATH = ROOT / "config/exposure_adjudication/primary_transient_exposure_v1.json"
TRANSIENT_PATH = ROOT / "data/processed/phenology/transient_econometric_exposures_v1.parquet"
E1_REPORT_PATH = ROOT / "outputs/exposure_adjudication/E1_PRIMARY_TRANSIENT_EXPOSURE_REPORT.md"
E1_MATRIX_PATH = ROOT / "outputs/exposure_adjudication/E1_CANDIDATE_MATRIX.csv"
E1_OVERLAY_PATH = ROOT / "outputs/exposure_adjudication/E1_SUPPORT_OVERLAY.csv"
E1_SCRIPT_PATH = ROOT / "scripts/primary_transient_exposure_v1.py"
E1_TEST_PATH = ROOT / "tests/test_primary_transient_exposure_v1.py"
PERENNIAL_PATH = ROOT / "data/processed/phenology/perennial_exposures_long.parquet"
B3_PATH = ROOT / "data/processed/phenology/transient_campaign_exposures_strict.parquet"
BOUNDARY_PATH = ROOT / "data/processed/climate/district_boundaries_piura.geojson"
PANEL_SUPPORT_PATH = ROOT / "outputs/qa/panel_support.csv"
JOINT_REPORT_PATH = ROOT / "outputs/joint_c0/C0_JOINT_REPORT.md"
PHENOLOGY_PATH = ROOT / "data/processed/phenology/phenology_windows_frozen.csv"

CONFIG_REL = Path("config/econometrics/econometric_design_master_v1.json")
REPORT_REL = Path("outputs/econometrics/ED1_ECONOMETRIC_DESIGN_REPORT.md")
MODEL_CONTRACTS_REL = Path("outputs/econometrics/ED1_MODEL_CONTRACTS.csv")
X_GEOMETRY_REL = Path("outputs/econometrics/ED1_X_GEOMETRY.csv")
INFERENCE_MATRIX_REL = Path("outputs/econometrics/ED1_INFERENCE_MATRIX.csv")
ROBUSTNESS_REL = Path("outputs/econometrics/ED1_ROBUSTNESS_HIERARCHY.csv")

OUTPUT_RELS = (
    CONFIG_REL,
    REPORT_REL,
    MODEL_CONTRACTS_REL,
    X_GEOMETRY_REL,
    INFERENCE_MATRIX_REL,
    ROBUSTNESS_REL,
)

FROZEN_HASHES = {
    E1_CONFIG_PATH: "283d57a21ba23c30c43f63e4c5327496ab59d760d8ca44a609b365151222a285",
    TRANSIENT_PATH: "ed90c70a7538318234a0390176b468a66f8a24a99fa59717efe5e8974cf09a67",
    E1_REPORT_PATH: "085c5efb0f8abbd9f7f9443f28ed6d4d26fe5af3289a94a27219937b12883b91",
    E1_MATRIX_PATH: "09bca9fb778759fc0b66656e6057d0f99daf0c9265be1f2b2eb1eb688e226e73",
    E1_OVERLAY_PATH: "b59894c59485b6c4c92de8be0424f1f6c6211b333ea7609696874b457ac567a8",
    E1_SCRIPT_PATH: "e53677b3284dd4d8c564838fd868d094e675705fc5d7baf56748ec38dc7dc3a8",
    E1_TEST_PATH: "867150d91d094e05939a7f68a1710787325e2eb5962cca3beeef20e42a11e522",
    PERENNIAL_PATH: "3fde5c7fc7a00f4c6600a18f60935bad213408ffa2ba3bac5828603e46984714",
    B3_PATH: "349413312568d0d423675bf58320ade41d2d9e700f138e7fbec55fc580bc1fb5",
    BOUNDARY_PATH: "d966d2a38e80d6575490be32bde2e39b7db66a3c6e99b240e9c21458766d099b",
    PANEL_SUPPORT_PATH: "b57fde70640d112c410f48164a27bf6e80ca310ae4dfdf2c3a93296f767564c6",
    JOINT_REPORT_PATH: "92e4902b0f5ee4cc8a4ef4411ef741efe79399a7a83398cbe177c7b4fa1ad582",
    PHENOLOGY_PATH: "ea25d949be9834a9e35352d970bb1b2172cac7d49db7eabb101ddfde9cfb657d",
}

CROPS = {
    "14010020000": {
        "model_id": "ED1-RICE",
        "crop": "RICE",
        "crop_std": "ARROZ",
        "regime": "DISTRICT_X_AUG_JUL_AGRICULTURAL_CAMPAIGN",
        "period_column": "CAMPAIGN_ID",
        "windows": ("RICE_FLOWERING_95_110_DAS",),
        "architecture": "SINGLE_FROZEN_WINDOW_LINEAR",
    },
    "14010070000": {
        "model_id": "ED1-MAD",
        "crop": "MAIZ_AMARILLO_DURO",
        "crop_std": "MAIZ AMARILLO DURO",
        "regime": "DISTRICT_X_AUG_JUL_AGRICULTURAL_CAMPAIGN",
        "period_column": "CAMPAIGN_ID",
        "windows": ("MAD_MPLUS1_MPLUS3",),
        "architecture": "SINGLE_FROZEN_WINDOW_LINEAR",
    },
    "13010210000": {
        "model_id": "ED1-MANGO",
        "crop": "MANGO",
        "crop_std": "MANGO",
        "regime": "DISTRICT_X_CALENDAR_YEAR",
        "period_column": "REFERENCE_PERIOD_ID",
        "windows": ("MANGO_MAY_JUN_CURRENT_YEAR",),
        "architecture": "SINGLE_FROZEN_WINDOW_LINEAR",
    },
    "13010170102": {
        "model_id": "ED1-LEMON",
        "crop": "LIMON_SUTIL",
        "crop_std": "LIMON SUTIL",
        "regime": "DISTRICT_X_CALENDAR_YEAR",
        "period_column": "REFERENCE_PERIOD_ID",
        "windows": ("LEMON_FULL_YEAR_T", "LEMON_FULL_YEAR_T_MINUS_1"),
        "architecture": "P1_JOINT_T_AND_T_MINUS_1_LINEAR",
    },
    "15010040000": {
        "model_id": "ED1-BANANA",
        "crop": "PLATANOS_Y_BANANAS",
        "crop_std": "PLATANOS Y BANANAS",
        "regime": "DISTRICT_X_CALENDAR_YEAR",
        "period_column": "REFERENCE_PERIOD_ID",
        "windows": ("BANANA_FULL_YEAR_T", "BANANA_FULL_YEAR_T_MINUS_1"),
        "architecture": "P1_JOINT_T_AND_T_MINUS_1_LINEAR",
    },
}

FAMILIES = {
    "LEVEL": ("RAIN_MM", "TMAX_C", "TMIN_C"),
    "PHYSICAL_ANOMALY": ("RAIN_ANOM_MM", "TMAX_ANOM_C", "TMIN_ANOM_C"),
    "STANDARDIZED_ANOMALY": ("RAIN_Z", "TMAX_Z", "TMIN_Z"),
}

TRANSIENT_COLUMNS = (
    "UBIGEO",
    "COD_CULTIVO",
    "CROP_STD",
    "CAMPAIGN_ID",
    "WINDOW_ID",
    "IDENTIFIED_OBSERVED_WEIGHT_FRACTION",
    "EXPOSURE_VALID",
    *tuple(variable for variables in FAMILIES.values() for variable in variables),
)
PERENNIAL_COLUMNS = (
    "UBIGEO",
    "COD_CULTIVO",
    "CROP_STD",
    "REFERENCE_PERIOD_ID",
    "WINDOW_ID",
    "EXPOSURE_VALID",
    *tuple(variable for variables in FAMILIES.values() for variable in variables),
)
B3_COLUMNS = (
    "UBIGEO",
    "COD_CULTIVO",
    "CROP_STD",
    "CAMPAIGN_ID",
    "CAMPAIGN_WEIGHTED_EXPOSURE_VALID",
    *tuple(variable for variables in FAMILIES.values() for variable in variables),
)
OVERLAY_COLUMNS = (
    "UBIGEO",
    "COD_CULTIVO",
    "CAMPAIGN_ID",
    "OUTCOME_VALID_FLAG",
    "EXPOSURE_VALID",
    "IDENTIFIED_OBSERVED_WEIGHT_FRACTION",
)
PANEL_SUPPORT_COLUMNS = ("COD_CULTIVO", "districts", "years", "district_years")

# This tuple is asserted by tests and documents the numerical outcome firewall.
OUTCOME_VALUE_COLUMNS_READ: tuple[str, ...] = ()
REAL_REGRESSIONS = 0
ED1_SUBSTANTIVE_VERDICT = "ED1_PASS_ECONOMETRIC_DESIGN_READY_FOR_DIRECTOR_FREEZE_DECISION"
FINAL_VERDICT = "ED1H_PASS_HARDENED_DESIGN_READY_FOR_DIRECTOR_FREEZE_DECISION"
SPATIAL_BANDWIDTHS_KM = (50, 100, 150)
WILD_BOOTSTRAP_REPLICATIONS = 9999
WILD_BOOTSTRAP_SEED = 20260903
ENGINE_VERSIONS = {
    "python": "3.11.7",
    "numpy": "2.3.5",
    "scipy": "1.16.3",
    "pandas": "3.0.2",
    "pyarrow": "25.0.1",
    "pyproj": "3.7.2",
    "shapely": "2.1.2",
}

PRE_ED1H_HASHES = {
    CONFIG_REL.as_posix(): "a8ff4d220f84a9dd34613c991035ce5445eb04c5a14d84d2037eb70c7441720b",
    REPORT_REL.as_posix(): "2fed424ea7b373c6e1a8a743babfeb2f0f4e09b0dff403aa41e011bef305c781",
    MODEL_CONTRACTS_REL.as_posix(): "7dcd316c7b47b3a2e15939ed25dea8e034f1ca7c5076013c7640ef11da74cbcf",
    X_GEOMETRY_REL.as_posix(): "08d569170ebc5bc3a5a4a35cdc702807be46a34df371e9363af510d7d0cca962",
    INFERENCE_MATRIX_REL.as_posix(): "1ab0c99d1602d563b32edca1a3c2a15447e17d1f57fb0a718d2a66e9c9d0efd5",
    ROBUSTNESS_REL.as_posix(): "b42c741b19bdcf9f5c46b1e0e7d3e622e55d50bdd46767170a0b9bf501a0cb7c",
    "scripts/econometric_design_master_v1.py": "2066222c47bff20178245d829eea02032fc1d1bdcd99f4be81ada025edcc6d37",
    "tests/test_econometric_design_master_v1.py": "aeac3a5749e3b0849d5a89e8907730c048209476ab96c7a2e41da5def97f5977",
}

METHOD_ANCHORS = (
    {
        "authors": "MacKinnon, Nielsen and Webb",
        "title": "Cluster-robust inference: A guide to empirical practice",
        "journal": "Journal of Econometrics",
        "year": 2023,
        "doi": "10.1016/j.jeconom.2022.04.001",
        "verified_url": "https://doi.org/10.1016/j.jeconom.2022.04.001",
        "verification": "VERIFIED_PUBLISHER_METADATA_AND_ABSTRACT",
        "design_role": "Cluster choice, finite-sample disclosure, and restricted wild cluster bootstrap robustness.",
    },
    {
        "authors": "Pustejovsky and Tipton",
        "title": "Small-Sample Methods for Cluster-Robust Variance Estimation and Hypothesis Testing in Fixed Effects Models",
        "journal": "Journal of Business & Economic Statistics",
        "year": 2018,
        "doi": "10.1080/07350015.2016.1247004",
        "verified_url": "https://doi.org/10.1080/07350015.2016.1247004",
        "verification": "VERIFIED_PUBLISHER_METADATA_AND_ABSTRACT",
        "design_role": "CR2 bias-reduced linearization and Satterthwaite tests after fixed-effect absorption.",
    },
    {
        "authors": "Driscoll and Kraay",
        "title": "Consistent Covariance Matrix Estimation with Spatially Dependent Panel Data",
        "journal": "Review of Economics and Statistics",
        "year": 1998,
        "doi": "10.1162/003465398557825",
        "verified_url": "https://doi.org/10.1162/003465398557825",
        "verification": "VERIFIED_PUBLISHER_METADATA_AND_ABSTRACT",
        "design_role": "Large-time-dimension requirement supports non-authorization at T=7/8.",
    },
    {
        "authors": "Conley",
        "title": "GMM estimation with cross sectional dependence",
        "journal": "Journal of Econometrics",
        "year": 1999,
        "doi": "10.1016/S0304-4076(98)00084-0",
        "verified_url": "https://doi.org/10.1016/S0304-4076(98)00084-0",
        "verification": "VERIFIED_PUBLISHER_METADATA_AND_ABSTRACT",
        "design_role": "Distance-based covariance robustness defined from geography before estimation.",
    },
)

FULL_SUITE_NONPASSES = (
    ("FAIL", "test_c0_joint_integration.JointC0IntegrationTests.test_01_exact_joint_branch_and_c0b6_head", "EXPECTED_HISTORICAL_LIFECYCLE_STATE", "Joint C0 test requires its historical branch and head."),
    ("FAIL", "test_c0_joint_integration.JointC0IntegrationTests.test_09_exact_seven_file_joint_scope", "EXPECTED_HISTORICAL_LIFECYCLE_STATE", "Joint C0 test requires its historical untracked candidate scope."),
    ("FAIL", "test_c0_joint_integration.JointC0IntegrationTests.test_51_preflight_passes_all_material_gates", "EXPECTED_HISTORICAL_LIFECYCLE_STATE", "Joint C0 preflight rejects the later E1 branch."),
    ("FAIL", "test_c0_joint_integration.JointC0IntegrationTests.test_52_default_cli_is_read_only", "EXPECTED_HISTORICAL_LIFECYCLE_STATE", "Joint C0 CLI preflight rejects the later E1 branch."),
    ("FAIL", "test_c0b1_decision_ontology.C0B1DecisionOntologyTests.test_01_branch_ancestry_checkpoint", "EXPECTED_HISTORICAL_LIFECYCLE_STATE", "C0B1 test requires its historical branch checkpoint."),
    ("FAIL", "test_c0b1_decision_ontology.C0B1DecisionOntologyTests.test_03_exact_five_new_c0b1_files", "EXPECTED_HISTORICAL_LIFECYCLE_STATE", "C0B1 test requires its historical candidate scope."),
    ("FAIL", "test_c0b1_decision_ontology.C0B1DecisionOntologyTests.test_13_no_optimizer_cvar_objective_or_scenario_artifacts", "EXPECTED_ACTIVE_PHASE_FIREWALL", "C0B1 absence firewall encounters authorized later-phase artifacts."),
    ("FAIL", "test_c0b1_decision_ontology.C0B1DecisionOntologyTests.test_21_c0b1_preflight_passes", "EXPECTED_HISTORICAL_LIFECYCLE_STATE", "C0B1 preflight combines historical branch and scope gates."),
    ("FAIL", "test_c0b2_spatial_hydraulic.C0B2SpatialHydraulicTests.test_01_exact_c0b1_freeze_ancestor", "EXPECTED_HISTORICAL_LIFECYCLE_STATE", "C0B2 test requires its historical execution branch."),
    ("FAIL", "test_c0b2_spatial_hydraulic.C0B2SpatialHydraulicTests.test_03_exact_seven_file_c0b2_scope", "EXPECTED_HISTORICAL_LIFECYCLE_STATE", "C0B2 test requires its historical candidate scope."),
    ("FAIL", "test_c0b2_spatial_hydraulic.C0B2SpatialHydraulicTests.test_25_c0b2_preflight_passes", "EXPECTED_HISTORICAL_LIFECYCLE_STATE", "C0B2 preflight combines historical branch and scope gates."),
    ("FAIL", "test_c0b3_perennial.C0B3PerennialTests.test_01_exact_c0b2_freeze_ancestry", "EXPECTED_HISTORICAL_LIFECYCLE_STATE", "C0B3 test requires its historical execution branch."),
    ("FAIL", "test_c0b3_perennial.C0B3PerennialTests.test_03_exact_seven_file_c0b3_scope", "EXPECTED_HISTORICAL_LIFECYCLE_STATE", "C0B3 test requires its historical candidate scope."),
    ("FAIL", "test_c0b3_perennial.C0B3PerennialTests.test_21_preflight_passes", "EXPECTED_HISTORICAL_LIFECYCLE_STATE", "C0B3 preflight sees the later ED1 candidate scope."),
    ("FAIL", "test_c0b4_land_adjustment.C0B4LandAdjustmentTests.test_01_exact_c0b3_freeze_identity", "EXPECTED_HISTORICAL_LIFECYCLE_STATE", "C0B4 test requires its historical execution branch."),
    ("FAIL", "test_c0b4_land_adjustment.C0B4LandAdjustmentTests.test_03_exact_seven_file_c0b4_scope", "EXPECTED_HISTORICAL_LIFECYCLE_STATE", "C0B4 test requires its historical candidate scope."),
    ("FAIL", "test_c0b4_land_adjustment.C0B4LandAdjustmentTests.test_32_preflight_passes", "EXPECTED_HISTORICAL_LIFECYCLE_STATE", "C0B4 preflight sees the later ED1 candidate scope."),
    ("FAIL", "test_c0b5_decision_domain.C0B5DecisionDomainTests.test_01_exact_c0b4_freeze_ancestry", "EXPECTED_HISTORICAL_LIFECYCLE_STATE", "C0B5 test requires its historical execution branch."),
    ("FAIL", "test_c0b5_decision_domain.C0B5DecisionDomainTests.test_04_exact_seven_file_c0b5_scope", "EXPECTED_HISTORICAL_LIFECYCLE_STATE", "C0B5 test requires its historical candidate scope."),
    ("FAIL", "test_c0b5_decision_domain.C0B5DecisionDomainTests.test_50_preflight_passes", "EXPECTED_HISTORICAL_LIFECYCLE_STATE", "C0B5 preflight rejects the later E1 branch."),
    ("FAIL", "test_c0b6_alternative_data_master.C0B6AlternativeDataMasterTests.test_01_exact_c0b5_freeze_ancestry", "EXPECTED_HISTORICAL_LIFECYCLE_STATE", "C0B6 test requires its historical execution branch."),
    ("FAIL", "test_c0b6_alternative_data_master.C0B6AlternativeDataMasterTests.test_03_exact_seven_file_c0b6_scope", "EXPECTED_HISTORICAL_LIFECYCLE_STATE", "C0B6 test requires its historical candidate scope."),
    ("FAIL", "test_c0b6_alternative_data_master.C0B6AlternativeDataMasterTests.test_44_preflight_reports_rebuild_pass", "EXPECTED_HISTORICAL_LIFECYCLE_STATE", "C0B6 preflight rejects the later E1 branch."),
    ("FAIL", "test_c0b6_alternative_data_master.C0B6AlternativeDataMasterTests.test_45_default_and_check_only_modes_are_read_only", "EXPECTED_HISTORICAL_LIFECYCLE_STATE", "C0B6 CLI preflight rejects the later E1 branch."),
    ("FAIL", "test_c0b_decision_feasibility_preflight.C0BDecisionFeasibilityPreflightTests.test_01_exact_branch", "EXPECTED_HISTORICAL_LIFECYCLE_STATE", "C0B.0 test requires its historical execution branch."),
    ("FAIL", "test_c0b_decision_feasibility_preflight.C0BDecisionFeasibilityPreflightTests.test_02_exact_frozen_base", "EXPECTED_HISTORICAL_LIFECYCLE_STATE", "C0B.0 test requires its historical base commit."),
    ("FAIL", "test_c0b_decision_feasibility_preflight.C0BDecisionFeasibilityPreflightTests.test_03_exact_five_file_scope", "EXPECTED_HISTORICAL_LIFECYCLE_STATE", "C0B.0 test requires its historical candidate scope."),
    ("FAIL", "test_c0b_decision_feasibility_preflight.C0BDecisionFeasibilityPreflightTests.test_11_no_optimizer_model_file_exists", "EXPECTED_ACTIVE_PHASE_FIREWALL", "C0B.0 absence firewall encounters authorized later-phase model-design artifacts."),
    ("FAIL", "test_c0b_decision_feasibility_preflight.C0BDecisionFeasibilityPreflightTests.test_21_preflight_script_passes", "EXPECTED_HISTORICAL_LIFECYCLE_STATE", "C0B.0 preflight combines historical identity and active-phase absence gates."),
    ("FAIL", "test_climate_exposure_b0_preflight.ClimateExposureB0PreflightTests.test_02_base_commit_and_tag", "EXPECTED_HISTORICAL_LIFECYCLE_STATE", "Climate B0 test requires its historical build branch and base."),
    ("FAIL", "test_climate_exposure_b0_preflight.ClimateExposureB0PreflightTests.test_03_no_forbidden_exposure_output_exists", "EXPECTED_ACTIVE_PHASE_FIREWALL", "Climate B0 absence firewall encounters frozen later exposure outputs."),
    ("FAIL", "test_climate_exposure_b0_preflight.ClimateExposureB0PreflightTests.test_16_no_stage_b_parquet_output_has_been_built", "EXPECTED_ACTIVE_PHASE_FIREWALL", "Climate B0 expects the later Stage B parquet to be absent."),
    ("FAIL", "test_d0_transient_campaign_outcome_master.D0TransientCampaignOutcomeMasterTests.test_01_exact_authorized_d0_parent_identity", "EXPECTED_HISTORICAL_LIFECYCLE_STATE", "D0 test requires its historical execution branch."),
    ("FAIL", "test_d0_transient_campaign_outcome_master.D0TransientCampaignOutcomeMasterTests.test_02a_old_joint_c0_head_is_rejected", "EXPECTED_HISTORICAL_LIFECYCLE_STATE", "D0 negative fixture reaches the later-branch guard before its intended parent guard."),
    ("FAIL", "test_d0_transient_campaign_outcome_master.D0TransientCampaignOutcomeMasterTests.test_02b_arbitrary_joint_c0_child_identity_is_rejected", "EXPECTED_HISTORICAL_LIFECYCLE_STATE", "D0 negative fixture reaches the later-branch guard before its intended parent guard."),
    ("FAIL", "test_d0_transient_campaign_outcome_master.D0TransientCampaignOutcomeMasterTests.test_02c_arbitrary_r0h_child_identity_is_rejected", "EXPECTED_HISTORICAL_LIFECYCLE_STATE", "D0 negative fixture reaches the later-branch guard before its intended parent guard."),
    ("FAIL", "test_d0_transient_campaign_outcome_master.D0TransientCampaignOutcomeMasterTests.test_02d_unrelated_commit_identity_is_rejected", "EXPECTED_HISTORICAL_LIFECYCLE_STATE", "D0 negative fixture reaches the later-branch guard before its intended parent guard."),
    ("FAIL", "test_d0_transient_campaign_outcome_master.D0TransientCampaignOutcomeMasterTests.test_04_exact_seven_file_d0_scope", "EXPECTED_HISTORICAL_LIFECYCLE_STATE", "D0 test requires its historical candidate scope."),
    ("FAIL", "test_d0_transient_campaign_outcome_master.D0TransientCampaignOutcomeMasterTests.test_36_config_is_exact_and_complete", "EXPECTED_HISTORICAL_LIFECYCLE_STATE", "D0 expected reconstruction embeds the current later HEAD while the frozen artifact preserves D0 execution identity."),
    ("FAIL", "test_d0_transient_campaign_outcome_master.D0TransientCampaignOutcomeMasterTests.test_40_outputs_reproduce_in_memory_byte_for_byte", "EXPECTED_HISTORICAL_LIFECYCLE_STATE", "D0 in-memory reconstruction embeds the later HEAD rather than frozen D0 identity."),
    ("FAIL", "test_d0_transient_campaign_outcome_master.D0TransientCampaignOutcomeMasterTests.test_41_default_rebuild_is_deterministic", "EXPECTED_HISTORICAL_LIFECYCLE_STATE", "D0 rebuild correctly rejects the later E1 branch."),
    ("FAIL", "test_d0_transient_campaign_outcome_master.D0TransientCampaignOutcomeMasterTests.test_41a_default_rebuild_does_not_rewrite_scientific_artifacts", "EXPECTED_HISTORICAL_LIFECYCLE_STATE", "D0 rebuild correctly rejects the later E1 branch."),
    ("FAIL", "test_d0_transient_campaign_outcome_master.D0TransientCampaignOutcomeMasterTests.test_42_check_only_is_strictly_read_only", "EXPECTED_HISTORICAL_LIFECYCLE_STATE", "D0 check-only mode correctly rejects the later E1 branch."),
    ("FAIL", "test_d0_transient_campaign_outcome_master.D0TransientCampaignOutcomeMasterTests.test_44_preflight_passes_all_material_gates", "EXPECTED_HISTORICAL_LIFECYCLE_STATE", "D0 preflight correctly rejects the later E1 branch."),
    ("FAIL", "test_perennial_exposures.PerennialExposureTests.test_12_forbidden_artifacts_absent", "EXPECTED_ACTIVE_PHASE_FIREWALL", "Perennial Stage B absence firewall encounters authorized later econometric artifacts."),
    ("FAIL", "test_primary_transient_exposure_v1.PrimaryTransientExposureV1Tests.test_01_s1_freeze_identity_is_exact", "EXPECTED_HISTORICAL_LIFECYCLE_STATE", "E1 authoring test requires the S1 parent branch before E1 freeze."),
    ("FAIL", "test_primary_transient_exposure_v1.PrimaryTransientExposureV1Tests.test_02_exact_seven_file_candidate_scope", "EXPECTED_HISTORICAL_LIFECYCLE_STATE", "E1 authoring test requires its historical untracked candidate scope."),
    ("FAIL", "test_scientific_identity_v1.ScientificIdentityV1Tests.test_01_d0_freeze_identity_and_ancestry_are_exact", "EXPECTED_HISTORICAL_LIFECYCLE_STATE", "S1 authoring test requires its D0 parent branch."),
    ("FAIL", "test_scientific_identity_v1.ScientificIdentityV1Tests.test_02_exact_five_file_candidate_scope", "EXPECTED_HISTORICAL_LIFECYCLE_STATE", "S1 authoring test requires its historical untracked candidate scope."),
    ("FAIL", "test_transient_cohort_exposures.TransientCohortExposureTests.test_16_forbidden_artifacts_absent", "EXPECTED_ACTIVE_PHASE_FIREWALL", "Transient Stage B1 absence firewall encounters authorized later econometric artifacts."),
    ("ERROR", "test_primary_transient_exposure_v1.PrimaryTransientExposureV1Tests.test_28_two_independent_builds_are_byte_identical", "EXPECTED_HISTORICAL_LIFECYCLE_STATE", "E1 rebuild preflight requires S1 HEAD but the active frozen state is E1 HEAD."),
)

PREVIOUS_FULL_SUITE_ERROR_TRACEBACK = (
    "Traceback (most recent call last):\n"
    "  File tests/test_primary_transient_exposure_v1.py, line 293, in test_28_two_independent_builds_are_byte_identical\n"
    "    stage_a_sha = e1.run_stage_a(root)\n"
    "  File scripts/primary_transient_exposure_v1.py, line 687, in run_stage_a\n"
    "    preflight_result = preflight()\n"
    "  File scripts/primary_transient_exposure_v1.py, line 273, in preflight\n"
    "    raise RuntimeError(f\"S1 identity mismatch: {identity}\")\n"
    "RuntimeError: S1 identity mismatch: {'head': 'cdeb14bdda8bdebf33afdebcf0e135179bd2f485', "
    "'remote_s1': '2e5823e6aaf842dfd60da968e7423471d6b32f1d', "
    "'s1_tag_target': '2e5823e6aaf842dfd60da968e7423471d6b32f1d'}"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_output(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=True, capture_output=True, text=True, encoding="utf-8"
    ).stdout.strip()


def preflight() -> dict[str, Any]:
    expected = {path.relative_to(ROOT).as_posix(): digest for path, digest in FROZEN_HASHES.items()}
    actual = {path.relative_to(ROOT).as_posix(): sha256_file(path) for path in FROZEN_HASHES}
    if actual != expected:
        raise RuntimeError("Frozen upstream input hash mismatch")
    identity = {
        "branch": git_output("branch", "--show-current"),
        "head": git_output("rev-parse", "HEAD"),
        "remote_e1": git_output("rev-parse", f"origin/{E1_BRANCH}"),
        "e1_tag_target": git_output("rev-list", "-n", "1", E1_TAG),
    }
    if identity["branch"] != E1_BRANCH:
        raise RuntimeError(f"ED1 must run on {E1_BRANCH}: {identity}")
    if {identity["head"], identity["remote_e1"], identity["e1_tag_target"]} != {E1_FREEZE_SHA}:
        raise RuntimeError(f"E1 identity mismatch: {identity}")
    changed_frozen = [
        path.relative_to(ROOT).as_posix()
        for path in FROZEN_HASHES
        if git_output("diff", "--name-only", "HEAD", "--", path.relative_to(ROOT).as_posix())
    ]
    if changed_frozen:
        raise RuntimeError(f"Frozen upstream paths modified: {changed_frozen}")
    return {
        "status": "PASS",
        "identity": identity,
        "frozen_input_hashes": actual,
        "changed_frozen_paths": changed_frozen,
    }


def read_transient_primary() -> pd.DataFrame:
    exposures = pq.read_table(TRANSIENT_PATH, columns=list(TRANSIENT_COLUMNS)).to_pandas()
    overlay = pd.read_csv(
        E1_OVERLAY_PATH,
        usecols=list(OVERLAY_COLUMNS),
        dtype={column: "string" for column in OVERLAY_COLUMNS},
    )
    overlay["OUTCOME_VALID_FLAG"] = overlay["OUTCOME_VALID_FLAG"].eq("TRUE")
    overlay["EXPOSURE_VALID_OVERLAY"] = overlay["EXPOSURE_VALID"].eq("TRUE")
    overlay = overlay.drop(columns="EXPOSURE_VALID")
    merged = exposures.merge(
        overlay,
        on=["UBIGEO", "COD_CULTIVO", "CAMPAIGN_ID"],
        how="left",
        validate="one_to_one",
        suffixes=("", "_OVERLAY"),
    )
    if merged["OUTCOME_VALID_FLAG"].isna().any():
        raise RuntimeError("E1 overlay does not cover every transient exposure key")
    if not (merged["EXPOSURE_VALID"] == merged["EXPOSURE_VALID_OVERLAY"]).all():
        raise RuntimeError("E1 exposure validity mismatch")
    data = merged[merged["OUTCOME_VALID_FLAG"] & merged["EXPOSURE_VALID"]].copy()
    data = data.sort_values(["COD_CULTIVO", "UBIGEO", "CAMPAIGN_ID"], kind="mergesort")
    counts = data.groupby("COD_CULTIVO").size().to_dict()
    if counts != {"14010020000": 281, "14010070000": 318}:
        raise RuntimeError(f"Frozen transient intersection mismatch: {counts}")
    return data.reset_index(drop=True)


def read_perennial_primary() -> pd.DataFrame:
    data = pq.read_table(PERENNIAL_PATH, columns=list(PERENNIAL_COLUMNS)).to_pandas()
    if not data["EXPOSURE_VALID"].all():
        raise RuntimeError("Invalid row present in frozen perennial exposure layer")
    support = pd.read_csv(
        PANEL_SUPPORT_PATH,
        usecols=list(PANEL_SUPPORT_COLUMNS),
        dtype={"COD_CULTIVO": "string"},
    )
    expected = {
        str(row.COD_CULTIVO): (int(row.districts), int(row.years), int(row.district_years))
        for row in support.itertuples(index=False)
        if str(row.COD_CULTIVO) in {"13010210000", "13010170102", "15010040000"}
    }
    unique_keys = data.drop_duplicates(["UBIGEO", "COD_CULTIVO", "REFERENCE_PERIOD_ID"])
    actual = {
        str(code): (
            int(group["UBIGEO"].nunique()),
            int(group["REFERENCE_PERIOD_ID"].nunique()),
            int(len(group)),
        )
        for code, group in unique_keys.groupby("COD_CULTIVO", sort=True)
    }
    if actual != expected:
        raise RuntimeError(f"Perennial structural outcome/exposure support mismatch: {actual} != {expected}")
    return data.sort_values(
        ["COD_CULTIVO", "UBIGEO", "REFERENCE_PERIOD_ID", "WINDOW_ID"], kind="mergesort"
    ).reset_index(drop=True)


def read_b3_sensitivity() -> pd.DataFrame:
    data = pq.read_table(B3_PATH, columns=list(B3_COLUMNS)).to_pandas()
    overlay = pd.read_csv(
        E1_OVERLAY_PATH,
        usecols=["UBIGEO", "COD_CULTIVO", "CAMPAIGN_ID", "OUTCOME_VALID_FLAG"],
        dtype="string",
    )
    overlay["OUTCOME_VALID_FLAG"] = overlay["OUTCOME_VALID_FLAG"].eq("TRUE")
    data = data.merge(
        overlay,
        on=["UBIGEO", "COD_CULTIVO", "CAMPAIGN_ID"],
        how="left",
        validate="one_to_one",
    )
    data = data[data["CAMPAIGN_WEIGHTED_EXPOSURE_VALID"] & data["OUTCOME_VALID_FLAG"]].copy()
    counts = data.groupby("COD_CULTIVO").size().to_dict()
    if counts != {"14010020000": 31, "14010070000": 7}:
        raise RuntimeError(f"B3 joint-valid support mismatch: {counts}")
    return data.sort_values(["COD_CULTIVO", "UBIGEO", "CAMPAIGN_ID"], kind="mergesort")


def single_window_frame(data: pd.DataFrame, crop_code: str, family: str, window: str) -> tuple[pd.DataFrame, list[str]]:
    variables = list(FAMILIES[family])
    frame = data[(data["COD_CULTIVO"] == crop_code) & (data["WINDOW_ID"] == window)].copy()
    return frame, variables


def joint_window_frame(data: pd.DataFrame, crop_code: str, family: str) -> tuple[pd.DataFrame, list[str]]:
    crop = CROPS[crop_code]
    variables = list(FAMILIES[family])
    keys = ["UBIGEO", "COD_CULTIVO", "CROP_STD", "REFERENCE_PERIOD_ID"]
    selected = data[data["COD_CULTIVO"] == crop_code].copy()
    if set(selected["WINDOW_ID"].unique()) != set(crop["windows"]):
        raise RuntimeError(f"Perennial window set mismatch for {crop_code}")
    indexed = selected.set_index([*keys, "WINDOW_ID"])[variables]
    if indexed.index.duplicated().any():
        raise RuntimeError(f"Duplicate perennial window key for {crop_code}")
    wide = indexed.unstack("WINDOW_ID")
    x_columns: list[str] = []
    output = wide.index.to_frame(index=False)
    for window in crop["windows"]:
        suffix = "T_MINUS_1" if window.endswith("T_MINUS_1") else "T"
        for variable in variables:
            name = f"{variable}__{suffix}"
            output[name] = wide[(variable, window)].to_numpy()
            x_columns.append(name)
    return output, x_columns


def fe_matrix(frame: pd.DataFrame, period_column: str) -> np.ndarray:
    columns = [np.ones(len(frame), dtype=float)]
    for field in ("UBIGEO", period_column):
        values = frame[field].astype(str).to_numpy()
        for level in sorted(set(values))[1:]:
            columns.append((values == level).astype(float))
    return np.column_stack(columns)


def runtime_engine_versions() -> dict[str, str]:
    return {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "pandas": pd.__version__,
        "pyarrow": package_version("pyarrow"),
        "pyproj": package_version("pyproj"),
        "shapely": package_version("shapely"),
    }


def primary_design_frame(
    transient: pd.DataFrame,
    perennial: pd.DataFrame,
    crop_code: str,
    family: str = "PHYSICAL_ANOMALY",
) -> tuple[pd.DataFrame, list[str]]:
    crop = CROPS[crop_code]
    if crop_code in {"14010020000", "14010070000"}:
        frame = transient[transient["COD_CULTIVO"] == crop_code].copy()
        columns = list(FAMILIES[family])
    elif len(crop["windows"]) == 1:
        frame, columns = single_window_frame(perennial, crop_code, family, str(crop["windows"][0]))
    else:
        frame, columns = joint_window_frame(perennial, crop_code, family)
    period_column = str(crop["period_column"])
    return frame.sort_values(["UBIGEO", period_column], kind="mergesort").reset_index(drop=True), columns


def synthetic_response(frame: pd.DataFrame, period_column: str) -> np.ndarray:
    values: list[float] = []
    for district, period in frame[["UBIGEO", period_column]].astype(str).itertuples(index=False, name=None):
        digest = hashlib.sha256(f"ED1H_SYNTHETIC_Y|{district}|{period}".encode("ascii")).digest()
        unsigned = int.from_bytes(digest[:8], byteorder="big", signed=False)
        values.append((unsigned + 0.5) / float(2**64) - 0.5)
    return np.asarray(values, dtype=float)


def absorb_fixed_effects(values: np.ndarray, fixed_effects: np.ndarray) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    return array - fixed_effects @ np.linalg.lstsq(fixed_effects, array, rcond=None)[0]


def symmetric_inverse_sqrt_psd(matrix: np.ndarray) -> tuple[np.ndarray, int, float, float]:
    symmetric = (np.asarray(matrix, dtype=float) + np.asarray(matrix, dtype=float).T) / 2.0
    eigenvalues, eigenvectors = np.linalg.eigh(symmetric)
    scale = max(1.0, float(np.max(np.abs(eigenvalues))))
    tolerance = float(np.finfo(float).eps * max(symmetric.shape) * scale * 128.0)
    positive = eigenvalues > tolerance
    inverse_sqrt = (eigenvectors[:, positive] / np.sqrt(eigenvalues[positive])) @ eigenvectors[:, positive].T
    return inverse_sqrt, int(positive.sum()), float(eigenvalues.min()), tolerance


def _aht_htz(
    beta: np.ndarray,
    covariance: np.ndarray,
    contrast: np.ndarray,
    q_vectors: np.ndarray,
) -> dict[str, float]:
    q = int(contrast.shape[0])
    contrast_covariance = contrast @ covariance @ contrast.T
    inverse_contrast_covariance = np.linalg.inv(contrast_covariance)
    contrast_beta = contrast @ beta
    wald = float(contrast_beta @ inverse_contrast_covariance @ contrast_beta)

    clusters = int(q_vectors.shape[1])
    p_array = np.empty((q, q, clusters, clusters), dtype=float)
    for left in range(q):
        for right in range(q):
            p_array[left, right] = q_vectors[left] @ q_vectors[right].T
    omega = np.empty((q, q), dtype=float)
    for left in range(q):
        for right in range(q):
            omega[left, right] = float(np.trace(p_array[left, right]))
    omega_inverse_sqrt, rank, _, _ = symmetric_inverse_sqrt_psd(omega)
    if rank != q:
        raise RuntimeError("AHT Omega matrix is not full rank")

    b_array = np.empty_like(p_array)
    for cluster_left in range(clusters):
        for cluster_right in range(clusters):
            b_array[:, :, cluster_left, cluster_right] = (
                omega_inverse_sqrt
                @ p_array[:, :, cluster_left, cluster_right]
                @ omega_inverse_sqrt
            )
    variance_matrix = np.empty((q, q), dtype=float)
    for left in range(q):
        for right in range(q):
            variance_matrix[left, right] = float(
                np.sum(b_array[left, right] * b_array[right, left])
                + np.sum(b_array[left, left] * b_array[right, right])
            )
    nu = float(q * (q + 1) / np.sum(variance_matrix))
    denominator_df = float(nu - q + 1)
    delta = float(max(denominator_df / nu, 0.0))
    f_statistic = float(delta * wald / q)
    p_value = float(stats.f.sf(f_statistic, q, denominator_df))
    return {
        "wald_chi_square": wald,
        "f_statistic": f_statistic,
        "delta": delta,
        "numerator_df": float(q),
        "denominator_df": denominator_df,
        "p_value": p_value,
    }


def fit_two_way_fe_cr2(
    frame: pd.DataFrame,
    x_columns: list[str],
    period_column: str,
    response: np.ndarray,
) -> dict[str, Any]:
    x = frame[x_columns].to_numpy(dtype=float)
    y = np.asarray(response, dtype=float)
    fixed_effects = fe_matrix(frame, period_column)
    x_within = absorb_fixed_effects(x, fixed_effects)
    y_within = absorb_fixed_effects(y, fixed_effects)
    beta_within = np.linalg.lstsq(x_within, y_within, rcond=None)[0]

    design = np.column_stack([fixed_effects, x])
    if np.linalg.matrix_rank(design) != design.shape[1]:
        raise RuntimeError("Primary synthetic design is not full rank")
    beta = np.linalg.lstsq(design, y, rcond=None)[0]
    bread = np.linalg.pinv(design.T @ design, rcond=1e-12, hermitian=True)
    residual = y - design @ beta
    residual_maker = np.eye(len(frame), dtype=float) - design @ np.linalg.pinv(design, rcond=1e-12)
    residual_maker = (residual_maker + residual_maker.T) / 2.0
    cluster_values = frame["UBIGEO"].astype(str).to_numpy()
    cluster_labels = sorted(set(cluster_values))
    cluster_indices = [np.flatnonzero(cluster_values == label) for label in cluster_labels]

    adjustments: list[np.ndarray] = []
    adjusted_scores: list[np.ndarray] = []
    extra_singularities = 0
    minimum_adjustment_eigenvalue = float("inf")
    for indices in cluster_indices:
        design_cluster = design[indices]
        residual_block = residual_maker[np.ix_(indices, indices)]
        adjustment, adjustment_rank, minimum_eigenvalue, adjustment_tolerance = symmetric_inverse_sqrt_psd(
            residual_block
        )
        expected_rank = max(len(indices) - 1, 0)
        if adjustment_rank < expected_rank or minimum_eigenvalue < -adjustment_tolerance:
            extra_singularities += 1
        minimum_adjustment_eigenvalue = min(minimum_adjustment_eigenvalue, minimum_eigenvalue)
        adjustments.append(adjustment)
        adjusted_scores.append(design_cluster.T @ adjustment @ residual[indices])

    meat = sum((np.outer(score, score) for score in adjusted_scores), np.zeros_like(bread))
    covariance = bread @ meat @ bread
    climate_offset = fixed_effects.shape[1]
    climate_slice = slice(climate_offset, design.shape[1])
    coefficient_contrasts = np.eye(design.shape[1], dtype=float)[climate_slice]
    q_vectors = np.empty((len(x_columns), len(cluster_indices), len(frame)), dtype=float)
    satterthwaite_df: list[float] = []
    for coefficient, contrast in enumerate(coefficient_contrasts):
        for cluster_number, (indices, adjustment) in enumerate(zip(cluster_indices, adjustments)):
            influence = adjustment @ design[indices] @ bread @ contrast
            q_vectors[coefficient, cluster_number] = residual_maker[:, indices] @ influence
        p_matrix = q_vectors[coefficient] @ q_vectors[coefficient].T
        denominator = float(np.sum(p_matrix**2))
        satterthwaite_df.append(float(np.trace(p_matrix) ** 2 / denominator))

    joint_contrast = coefficient_contrasts
    aht = _aht_htz(beta, covariance, joint_contrast, q_vectors)
    climate_covariance = covariance[climate_slice, climate_slice]
    nonfinite_count = int(
        (~np.isfinite(beta_within)).sum()
        + (~np.isfinite(climate_covariance)).sum()
        + (~np.isfinite(np.asarray(satterthwaite_df))).sum()
        + sum(not np.isfinite(value) for value in aht.values())
    )
    return {
        "beta": beta[climate_slice],
        "beta_within": beta_within,
        "full_beta": beta,
        "covariance": covariance,
        "climate_covariance": climate_covariance,
        "satterthwaite_df": np.asarray(satterthwaite_df, dtype=float),
        "aht": aht,
        "design": design,
        "fixed_effects": fixed_effects,
        "x_within": x_within,
        "y_within": y_within,
        "residual": residual,
        "bread": bread,
        "cluster_indices": cluster_indices,
        "cluster_labels": cluster_labels,
        "adjustments": adjustments,
        "cr2_adjustment_singularities": extra_singularities,
        "minimum_adjustment_eigenvalue": minimum_adjustment_eigenvalue,
        "nonfinite_count": nonfinite_count,
    }


def effective_cluster_audit(frame: pd.DataFrame, x_within: np.ndarray) -> dict[str, Any]:
    cluster_values = frame["UBIGEO"].astype(str).to_numpy()
    labels = sorted(set(cluster_values))
    tolerance = float(np.finfo(float).eps * max(x_within.shape) * max(1.0, np.linalg.norm(x_within, ord=2)) * 128.0)
    contributions = [float(np.linalg.norm(x_within[cluster_values == label], ord="fro")) for label in labels]
    effective = [value > tolerance for value in contributions]
    bread = np.linalg.pinv(x_within.T @ x_within, rcond=1e-12, hermitian=True)
    observation_leverage = np.einsum("ij,jk,ik->i", x_within, bread, x_within)
    cluster_leverage = np.asarray(
        [float(observation_leverage[cluster_values == label].sum()) for label in labels], dtype=float
    )
    sizes = [int(np.sum(cluster_values == label)) for label in labels]
    quantiles = np.quantile(cluster_leverage, [0.0, 0.1, 0.5, 0.9, 1.0])
    return {
        "nominal_clusters": len(labels),
        "zero_effective_clusters": int(effective.count(False)),
        "effective_contributing_clusters": int(effective.count(True)),
        "singleton_clusters": int(sum(size == 1 for size in sizes)),
        "effective_contribution_tolerance": rounded(tolerance),
        "cluster_leverage": {
            "minimum": rounded(quantiles[0]),
            "q10": rounded(quantiles[1]),
            "median": rounded(quantiles[2]),
            "q90": rounded(quantiles[3]),
            "maximum": rounded(quantiles[4]),
        },
    }


def _reference_svd_fit(
    frame: pd.DataFrame,
    x_columns: list[str],
    period_column: str,
    response: np.ndarray,
) -> dict[str, Any]:
    fixed_effects = fe_matrix(frame, period_column)
    design = np.column_stack([fixed_effects, frame[x_columns].to_numpy(dtype=float)])
    y = np.asarray(response, dtype=float)
    design_inverse = np.linalg.pinv(design, rcond=1e-12)
    normal_inverse = design_inverse @ design_inverse.T
    beta = design_inverse @ y
    residual = y - design @ beta
    hat = design @ design_inverse
    residual_maker = (np.eye(len(frame)) - hat + (np.eye(len(frame)) - hat).T) / 2.0
    covariance_meat = np.zeros((design.shape[1], design.shape[1]), dtype=float)
    clusters = frame["UBIGEO"].astype(str).to_numpy()
    labels = sorted(set(clusters))
    indices_list = [np.flatnonzero(clusters == label) for label in labels]
    adjustments: list[np.ndarray] = []
    for indices in indices_list:
        block = residual_maker[np.ix_(indices, indices)]
        left, singular, right = np.linalg.svd(block, full_matrices=False)
        tolerance = np.finfo(float).eps * max(block.shape) * max(1.0, float(singular.max())) * 128.0
        inverse_root = np.zeros_like(singular)
        inverse_root[singular > tolerance] = 1.0 / np.sqrt(singular[singular > tolerance])
        adjustment = (right.T * inverse_root) @ left.T
        adjustments.append(adjustment)
        score = design[indices].T @ adjustment @ residual[indices]
        covariance_meat += np.outer(score, score)
    covariance = normal_inverse @ covariance_meat @ normal_inverse
    offset = fixed_effects.shape[1]
    contrasts = np.eye(design.shape[1], dtype=float)[offset:]
    q_vectors = np.empty((len(x_columns), len(labels), len(frame)), dtype=float)
    dfs: list[float] = []
    for coefficient, contrast in enumerate(contrasts):
        for cluster_number, (indices, adjustment) in enumerate(zip(indices_list, adjustments)):
            influence = adjustment @ design[indices] @ normal_inverse @ contrast
            q_vectors[coefficient, cluster_number] = residual_maker[:, indices] @ influence
        p_matrix = q_vectors[coefficient] @ q_vectors[coefficient].T
        dfs.append(float(np.trace(p_matrix) ** 2 / np.square(p_matrix).sum()))
    contrast_covariance = contrasts @ covariance @ contrasts.T
    contrast_beta = contrasts @ beta
    wald = float(contrast_beta @ np.linalg.inv(contrast_covariance) @ contrast_beta)
    q = len(x_columns)
    p_array = np.einsum("sgi,thi->stgh", q_vectors, q_vectors)
    omega = np.einsum("stgg->st", p_array)
    left, singular, right = np.linalg.svd(omega, full_matrices=False)
    omega_tolerance = np.finfo(float).eps * max(omega.shape) * max(1.0, float(singular.max())) * 128.0
    if int(np.sum(singular > omega_tolerance)) != q:
        raise RuntimeError("Reference AHT Omega matrix is not full rank")
    omega_inverse_sqrt = (right.T * (1.0 / np.sqrt(singular))) @ left.T
    b_array = np.einsum("as,stgh,tb->abgh", omega_inverse_sqrt, p_array, omega_inverse_sqrt)
    variance_matrix = np.empty((q, q), dtype=float)
    for left_index in range(q):
        for right_index in range(q):
            variance_matrix[left_index, right_index] = float(
                np.sum(b_array[left_index, right_index] * b_array[right_index, left_index])
                + np.sum(b_array[left_index, left_index] * b_array[right_index, right_index])
            )
    nu = float(q * (q + 1) / variance_matrix.sum())
    denominator_df = float(nu - q + 1)
    delta = float(max(denominator_df / nu, 0.0))
    aht = {
        "wald_chi_square": wald,
        "f_statistic": float(delta * wald / q),
        "delta": delta,
        "numerator_df": float(q),
        "denominator_df": denominator_df,
        "p_value": float(stats.f.sf(delta * wald / q, q, denominator_df)),
    }
    return {
        "beta": beta[offset:],
        "covariance": covariance[offset:, offset:],
        "satterthwaite_df": np.asarray(dfs),
        "aht": aht,
    }


def synthetic_reference_fixture() -> tuple[pd.DataFrame, list[str], np.ndarray]:
    rows: list[dict[str, Any]] = []
    for district_number in range(8):
        for period_number in range(5):
            rows.append(
                {
                    "UBIGEO": f"D{district_number:02d}",
                    "PERIOD": f"P{period_number:02d}",
                    "X1": np.sin((district_number + 1) * (period_number + 2)),
                    "X2": np.cos((district_number + 2) * (period_number + 1)),
                    "X3": ((district_number + 3) * (period_number + 4) % 11) / 7.0,
                }
            )
    frame = pd.DataFrame(rows)
    return frame, ["X1", "X2", "X3"], synthetic_response(frame, "PERIOD")


def reference_implementation_validation() -> dict[str, Any]:
    frame, columns, response = synthetic_reference_fixture()
    production = fit_two_way_fe_cr2(frame, columns, "PERIOD", response)
    reference = _reference_svd_fit(frame, columns, "PERIOD", response)
    tolerance = 1e-9
    differences = {
        "coefficient_max_abs_difference": float(np.max(np.abs(production["beta"] - reference["beta"]))),
        "cr2_covariance_max_abs_difference": float(
            np.max(np.abs(production["climate_covariance"] - reference["covariance"]))
        ),
        "satterthwaite_df_max_abs_difference": float(
            np.max(np.abs(production["satterthwaite_df"] - reference["satterthwaite_df"]))
        ),
        "aht_f_max_abs_difference": abs(production["aht"]["f_statistic"] - reference["aht"]["f_statistic"]),
        "aht_denominator_df_max_abs_difference": abs(
            production["aht"]["denominator_df"] - reference["aht"]["denominator_df"]
        ),
    }
    return {
        "status": "PASS" if max(differences.values()) <= tolerance else "FAIL",
        "fixture": "BALANCED_8_DISTRICT_X_5_PERIOD_SYNTHETIC_PANEL_STRUCTURAL_KEY_Y_ONLY",
        "production_synthetic_beta": [rounded(value) for value in production["beta"]],
        "reference_synthetic_beta": [rounded(value) for value in reference["beta"]],
        "production_aht_f": rounded(production["aht"]["f_statistic"]),
        "reference_aht_f": rounded(reference["aht"]["f_statistic"]),
        "production_aht_denominator_df": rounded(production["aht"]["denominator_df"]),
        "reference_aht_denominator_df": rounded(reference["aht"]["denominator_df"]),
        "tolerance": tolerance,
        "differences": {key: rounded(value) for key, value in differences.items()},
        "reference_path": "INDEPENDENT_FULL_DESIGN_SVD_CALCULATION",
    }


def restricted_wild_cluster_bootstrap_t(
    frame: pd.DataFrame,
    x_columns: list[str],
    period_column: str,
    response: np.ndarray,
    replications: int,
    seed: int,
    restriction_kind: str = "FIRST_CLIMATE_COEFFICIENT",
) -> dict[str, Any]:
    fit = fit_two_way_fe_cr2(frame, x_columns, period_column, response)
    design = fit["design"]
    beta = fit["full_beta"]
    bread = fit["bread"]
    if restriction_kind == "FIRST_CLIMATE_COEFFICIENT":
        contrast = np.zeros((1, design.shape[1]), dtype=float)
        contrast[0, -len(x_columns)] = 1.0
        statistic_kind = "ABSOLUTE_BOOTSTRAP_T"
    elif restriction_kind == "ALL_CLIMATE_COEFFICIENTS":
        contrast = np.eye(design.shape[1], dtype=float)[-len(x_columns):]
        statistic_kind = "BOOTSTRAP_WALD_F"
    else:
        raise ValueError(f"Unknown bootstrap restriction kind: {restriction_kind}")
    restriction_covariance = contrast @ bread @ contrast.T
    beta_null = beta - bread @ contrast.T @ np.linalg.solve(restriction_covariance, contrast @ beta)
    restricted_residual = np.asarray(response, dtype=float) - design @ beta_null
    observed_contrast_covariance = contrast @ fit["covariance"] @ contrast.T
    observed_contrast_beta = contrast @ beta
    if len(contrast) == 1:
        observed_statistic = abs(float(observed_contrast_beta[0] / np.sqrt(observed_contrast_covariance[0, 0])))
    else:
        observed_statistic = float(
            observed_contrast_beta @ np.linalg.solve(observed_contrast_covariance, observed_contrast_beta)
            / len(contrast)
        )

    rng = np.random.Generator(np.random.PCG64(seed))
    exceedances = 0
    invalid = 0
    digest = hashlib.sha256()
    completed = 0
    batch_size = 1000
    while completed < replications:
        count = min(batch_size, replications - completed)
        cluster_weights = rng.integers(0, 2, size=(len(fit["cluster_indices"]), count), dtype=np.int8)
        cluster_weights = cluster_weights.astype(float) * 2.0 - 1.0
        row_weights = np.empty((len(frame), count), dtype=float)
        for cluster_number, indices in enumerate(fit["cluster_indices"]):
            row_weights[indices] = cluster_weights[cluster_number]
        shock = restricted_residual[:, None] * row_weights
        beta_delta = bread @ design.T @ shock
        bootstrap_beta = beta_null[:, None] + beta_delta
        bootstrap_residual = shock - design @ beta_delta
        contrast_covariance = np.zeros((len(contrast), len(contrast), count), dtype=float)
        for indices, adjustment in zip(fit["cluster_indices"], fit["adjustments"]):
            projected_score = contrast @ bread @ design[indices].T @ adjustment @ bootstrap_residual[indices]
            contrast_covariance += np.einsum("ir,jr->ijr", projected_score, projected_score)
        bootstrap_contrast_beta = contrast @ bootstrap_beta
        statistics = np.full(count, np.nan, dtype=float)
        if len(contrast) == 1:
            variance = contrast_covariance[0, 0]
            valid = np.isfinite(variance) & (variance > 0)
            statistics[valid] = np.abs(bootstrap_contrast_beta[0, valid] / np.sqrt(variance[valid]))
        else:
            valid = np.isfinite(contrast_covariance).all(axis=(0, 1))
            for replication in np.flatnonzero(valid):
                try:
                    statistics[replication] = float(
                        bootstrap_contrast_beta[:, replication]
                        @ np.linalg.solve(
                            contrast_covariance[:, :, replication], bootstrap_contrast_beta[:, replication]
                        )
                        / len(contrast)
                    )
                except np.linalg.LinAlgError:
                    valid[replication] = False
        exceedances += int(np.sum(statistics[valid] >= observed_statistic))
        invalid += int((~valid).sum())
        digest.update(np.asarray(statistics, dtype="<f8").tobytes())
        completed += count
    p_value = float((1 + exceedances) / (replications + 1))
    return {
        "replications": replications,
        "seed": seed,
        "weight_distribution": "RADEMACHER",
        "null_imposed": True,
        "restricted": True,
        "restriction_kind": restriction_kind,
        "statistic_kind": statistic_kind,
        "finite_replication_correction": "(1+EXCEEDANCES)/(B+1)",
        "invalid_replications": invalid,
        "synthetic_p_value": rounded(p_value),
        "bootstrap_t_sha256": digest.hexdigest(),
    }


def wild_bootstrap_validation() -> dict[str, Any]:
    frame, columns, response = synthetic_reference_fixture()
    run_one = restricted_wild_cluster_bootstrap_t(
        frame, columns, "PERIOD", response, WILD_BOOTSTRAP_REPLICATIONS, WILD_BOOTSTRAP_SEED
    )
    run_two = restricted_wild_cluster_bootstrap_t(
        frame, columns, "PERIOD", response, WILD_BOOTSTRAP_REPLICATIONS, WILD_BOOTSTRAP_SEED
    )
    joint_run_one = restricted_wild_cluster_bootstrap_t(
        frame,
        columns,
        "PERIOD",
        response,
        WILD_BOOTSTRAP_REPLICATIONS,
        WILD_BOOTSTRAP_SEED,
        restriction_kind="ALL_CLIMATE_COEFFICIENTS",
    )
    joint_run_two = restricted_wild_cluster_bootstrap_t(
        frame,
        columns,
        "PERIOD",
        response,
        WILD_BOOTSTRAP_REPLICATIONS,
        WILD_BOOTSTRAP_SEED,
        restriction_kind="ALL_CLIMATE_COEFFICIENTS",
    )
    deterministic = run_one == run_two and joint_run_one == joint_run_two
    return {
        "status": (
            "PASS"
            if deterministic
            and run_one["invalid_replications"] == 0
            and joint_run_one["invalid_replications"] == 0
            else "FAIL"
        ),
        "fixture": "BALANCED_8_DISTRICT_X_5_PERIOD_SYNTHETIC_PANEL_STRUCTURAL_KEY_Y_ONLY",
        "future_contract_replications": WILD_BOOTSTRAP_REPLICATIONS,
        "smoke_test_replications": WILD_BOOTSTRAP_REPLICATIONS,
        "run_one": run_one,
        "run_two_sha256": run_two["bootstrap_t_sha256"],
        "joint_run_one": joint_run_one,
        "joint_run_two_sha256": joint_run_two["bootstrap_t_sha256"],
        "deterministic": deterministic,
    }


def district_centroids() -> dict[str, tuple[float, float]]:
    source = json.loads(BOUNDARY_PATH.read_text(encoding="utf-8"))
    projector = Transformer.from_crs("EPSG:4326", "EPSG:32717", always_xy=True).transform
    result: dict[str, tuple[float, float]] = {}
    for feature in source["features"]:
        centroid = transform(projector, shape(feature["geometry"])).centroid
        result[str(feature["properties"]["UBIGEO"])] = (float(centroid.x), float(centroid.y))
    return result


def conley_covariance(
    frame: pd.DataFrame,
    x_within: np.ndarray,
    synthetic_residual: np.ndarray,
    period_column: str,
    bandwidth_km: int,
    centroids: dict[str, tuple[float, float]],
) -> np.ndarray:
    districts = frame["UBIGEO"].astype(str).to_numpy()
    coordinates = np.asarray([centroids[district] for district in districts], dtype=float)
    periods = frame[period_column].astype(str).to_numpy()
    meat = np.zeros((x_within.shape[1], x_within.shape[1]), dtype=float)
    for period in sorted(set(periods)):
        indices = np.flatnonzero(periods == period)
        period_coordinates = coordinates[indices]
        distances_km = np.sqrt(
            ((period_coordinates[:, None, :] - period_coordinates[None, :, :]) ** 2).sum(axis=2)
        ) / 1000.0
        kernel = np.maximum(1.0 - distances_km / float(bandwidth_km), 0.0)
        scores = x_within[indices] * synthetic_residual[indices, None]
        meat += scores.T @ kernel @ scores
    bread = np.linalg.pinv(x_within.T @ x_within, rcond=1e-12, hermitian=True)
    return bread @ meat @ bread


def level_anomaly_equivalence(
    transient: pd.DataFrame, perennial: pd.DataFrame
) -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}
    tolerance = 1e-9
    for crop_code, crop in CROPS.items():
        level_frame, level_columns = primary_design_frame(transient, perennial, crop_code, "LEVEL")
        anomaly_frame, anomaly_columns = primary_design_frame(transient, perennial, crop_code, "PHYSICAL_ANOMALY")
        keys = ["UBIGEO", str(crop["period_column"])]
        if not level_frame[keys].equals(anomaly_frame[keys]):
            raise RuntimeError(f"LEVEL/anomaly key mismatch for {crop_code}")
        fixed_effects = fe_matrix(level_frame, str(crop["period_column"]))
        level_within = absorb_fixed_effects(level_frame[level_columns].to_numpy(dtype=float), fixed_effects)
        anomaly_within = absorb_fixed_effects(anomaly_frame[anomaly_columns].to_numpy(dtype=float), fixed_effects)
        discrepancy = float(np.max(np.abs(level_within - anomaly_within)))
        level_rank = int(np.linalg.matrix_rank(level_within))
        anomaly_rank = int(np.linalg.matrix_rank(anomaly_within))
        combined_rank = int(np.linalg.matrix_rank(np.column_stack([level_within, anomaly_within])))
        equality = discrepancy <= tolerance
        column_space_equivalence = combined_rank == level_rank == anomaly_rank
        slopes: list[float] = []
        proportional_residuals: list[float] = []
        for level_column, anomaly_column in zip(level_within.T, anomaly_within.T):
            slope = float(level_column @ anomaly_column / (level_column @ level_column))
            slopes.append(slope)
            proportional_residuals.append(float(np.max(np.abs(anomaly_column - slope * level_column))))
        proportional = max(proportional_residuals) <= tolerance
        results[crop_code] = {
            "crop": crop["crop"],
            "variable_pairing": list(zip(level_columns, anomaly_columns)),
            "maximum_absolute_transformed_x_discrepancy": rounded(discrepancy),
            "level_within_rank": level_rank,
            "physical_anomaly_within_rank": anomaly_rank,
            "combined_within_rank": combined_rank,
            "column_space_equivalent": column_space_equivalence,
            "elementwise_equal_within_tolerance": equality,
            "proportional_within_tolerance": proportional,
            "pairwise_slopes": [rounded(value) for value in slopes],
            "expected_coefficient_and_fitted_value_status": (
                "FE_EQUIVALENT" if equality else "DISTINCT_TRANSFORMED_DESIGN"
            ),
            "level_role": (
                "FE_EQUIVALENT_DIAGNOSTIC_NOT_DISTINCT_ROBUSTNESS"
                if equality
                else "DISTINCT_CLIMATE_FAMILY_ROBUSTNESS"
            ),
            "tolerance": tolerance,
        }
    return results


def implementation_feasibility(
    transient: pd.DataFrame, perennial: pd.DataFrame
) -> dict[str, Any]:
    versions = runtime_engine_versions()
    if versions != ENGINE_VERSIONS:
        raise RuntimeError(f"Inference engine version mismatch: {versions} != {ENGINE_VERSIONS}")
    centroids = district_centroids()
    crop_diagnostics: dict[str, Any] = {}
    total_singularities = 0
    all_conley_finite = True
    for crop_code, crop in CROPS.items():
        frame, columns = primary_design_frame(transient, perennial, crop_code)
        response = synthetic_response(frame, str(crop["period_column"]))
        fit = fit_two_way_fe_cr2(frame, columns, str(crop["period_column"]), response)
        cluster_audit = effective_cluster_audit(frame, fit["x_within"])
        conley: dict[str, Any] = {}
        for bandwidth in SPATIAL_BANDWIDTHS_KM:
            covariance = conley_covariance(
                frame,
                fit["x_within"],
                fit["residual"],
                str(crop["period_column"]),
                bandwidth,
                centroids,
            )
            finite = bool(np.isfinite(covariance).all())
            all_conley_finite = all_conley_finite and finite
            conley[str(bandwidth)] = {
                "finite": finite,
                "symmetric_max_abs_difference": rounded(np.max(np.abs(covariance - covariance.T))),
                "maximum_absolute_entry": rounded(np.max(np.abs(covariance))),
            }
        total_singularities += int(fit["cr2_adjustment_singularities"])
        crop_diagnostics[crop_code] = {
            "crop": crop["crop"],
            **cluster_audit,
            "cr2_adjustment_singularities": int(fit["cr2_adjustment_singularities"]),
            "cr2_adjustment_status": (
                "PASS_NO_EXTRA_SINGULARITY_BEYOND_CLUSTER_FE_NULLSPACE"
                if fit["cr2_adjustment_singularities"] == 0
                else "FAIL_EXTRA_SINGULARITY"
            ),
            "minimum_cr2_adjustment_block_eigenvalue": rounded(fit["minimum_adjustment_eigenvalue"]),
            "coefficient_specific_satterthwaite_df_minimum": rounded(fit["satterthwaite_df"].min()),
            "coefficient_specific_satterthwaite_df_maximum": rounded(fit["satterthwaite_df"].max()),
            "aht_numerator_df": int(fit["aht"]["numerator_df"]),
            "aht_denominator_df": rounded(fit["aht"]["denominator_df"]),
            "cr2_covariance_minimum_eigenvalue": rounded(np.linalg.eigvalsh(fit["climate_covariance"]).min()),
            "nonfinite_quantities": int(fit["nonfinite_count"]),
            "conley_covariance": conley,
        }
    reference = reference_implementation_validation()
    wild = wild_bootstrap_validation()
    if reference["status"] != "PASS" or wild["status"] != "PASS" or not all_conley_finite:
        raise RuntimeError("One or more synthetic inference-engine validations failed")
    return {
        "status": "PASS",
        "real_outcome_values_read": False,
        "synthetic_response_source": "SHA256_OF_STRUCTURAL_DISTRICT_AND_PERIOD_KEYS_ONLY",
        "engine": {
            "language": "Python",
            "runtime_versions": versions,
            "external_libraries": "NUMPY_SCIPY_PANDAS_PYARROW_PYPROJ_SHAPELY",
            "two_way_fe_api": "fit_two_way_fe_cr2 + absorb_fixed_effects",
            "cr2_api": "fit_two_way_fe_cr2 PROJECT_LOCAL_CR2_IDENTITY_TARGET",
            "satterthwaite_api": "fit_two_way_fe_cr2 COEFFICIENT_SPECIFIC_P_MATRIX_MOMENT_MATCHING",
            "aht_api": "_aht_htz CLUBSANDWICH_HTZ_FORMULA",
            "wild_cluster_api": "restricted_wild_cluster_bootstrap_t",
            "conley_api": "conley_covariance",
            "numerical_conventions": (
                "FLOAT64;SVD_LSTSQ_FE_ABSORPTION;MOORE_PENROSE_RCOND_1E-12;"
                "SYMMETRIC_EIGEN_PSEUDOINVERSE_ROOT;CR2_IDENTITY_WORKING_TARGET;"
                "DISTRICT_CLUSTER;BARTLETT_DISTANCE_KERNEL_SAME_PERIOD"
            ),
        },
        "published_formula_reference": {
            "implementation": "clubSandwich R source",
            "cr2_url": "https://github.com/jepusto/clubSandwich/blob/main/R/CR-adjustments.R",
            "satterthwaite_url": "https://github.com/jepusto/clubSandwich/blob/main/R/coef_test.R",
            "aht_htz_url": "https://github.com/jepusto/clubSandwich/blob/main/R/Wald_test.R",
        },
        "independent_reference_validation": reference,
        "crop_diagnostics": crop_diagnostics,
        "total_cr2_adjustment_singularities": total_singularities,
        "wild_cluster_bootstrap_validation": wild,
        "conley_engine_validation": "PASS_ALL_FIVE_CROPS_ALL_THREE_BANDWIDTHS" if all_conley_finite else "FAIL",
    }


def rounded(value: Any) -> float | None:
    if value is None or not np.isfinite(float(value)):
        return None
    return round(float(value), 12)


def geometry_row(
    frame: pd.DataFrame,
    x_columns: list[str],
    crop_code: str,
    family: str,
    candidate: str,
    window_set: str,
) -> dict[str, Any]:
    crop = CROPS[crop_code]
    period_column = str(crop["period_column"])
    data = frame.sort_values(["UBIGEO", period_column], kind="mergesort").reset_index(drop=True)
    x = data[x_columns].to_numpy(dtype=float)
    missing_x = int((~np.isfinite(x)).sum())
    if missing_x:
        raise RuntimeError(f"Missing X in {crop_code}/{candidate}/{family}")
    fixed_effects = fe_matrix(data, period_column)
    within = x - fixed_effects @ np.linalg.lstsq(fixed_effects, x, rcond=None)[0]
    regressor_count = int(x.shape[1])
    within_rank = int(np.linalg.matrix_rank(within))
    variances = np.var(within, axis=0, ddof=1)
    condition_number: float | None = None
    max_correlation: float | None = None
    max_vif: float | None = None
    observation_leverage: float | None = None
    cluster_leverages: list[float] = []
    if within_rank == regressor_count and np.all(variances > 0):
        standardized = within / np.sqrt(variances)
        correlation = np.corrcoef(standardized, rowvar=False)
        if regressor_count == 1:
            correlation = np.array([[1.0]])
        condition_number = float(np.linalg.cond(standardized))
        max_correlation = float(np.max(np.abs(correlation - np.eye(regressor_count))))
        max_vif = float(np.max(np.diag(np.linalg.inv(correlation))))
        gram_inverse = np.linalg.inv(within.T @ within)
        leverage = np.einsum("ij,jk,ik->i", within, gram_inverse, within)
        observation_leverage = float(np.max(leverage))
        districts = data["UBIGEO"].astype(str).to_numpy()
        cluster_leverages = [float(leverage[districts == value].sum()) for value in sorted(set(districts))]
    full_design_rank = int(np.linalg.matrix_rank(np.column_stack([fixed_effects, x])))
    residual_df = int(len(data) - full_design_rank)
    cluster_sizes = data.groupby("UBIGEO", sort=True).size()
    period_sizes = data.groupby(period_column, sort=True).size()
    near_singular = bool(
        condition_number is not None
        and max_vif is not None
        and (condition_number > 30.0 or max_vif > 10.0)
    )
    technically_feasible = bool(
        within_rank == regressor_count
        and np.all(variances > 0)
        and residual_df > 0
        and data["UBIGEO"].nunique() >= 10
        and not near_singular
    )
    if within_rank != regressor_count:
        verdict = "BLOCKED_X_RANK_AFTER_REQUIRED_FE"
    elif residual_df <= 0:
        verdict = "BLOCKED_NO_RESIDUAL_DEGREES_OF_FREEDOM"
    elif near_singular:
        verdict = "BLOCKED_NEAR_SINGULAR_X_GEOMETRY"
    elif candidate == "B3_STRICT_SENSITIVITY":
        verdict = "PASS_WITH_SEVERE_SUPPORT_LIMITATION"
    else:
        verdict = "PASS"
    return {
        "MODEL_ID": crop["model_id"],
        "CROP_CODE": crop_code,
        "CROP": crop["crop"],
        "TEMPORAL_REGIME": crop["regime"],
        "CANDIDATE": candidate,
        "CLIMATE_FAMILY": family,
        "WINDOW_SET": window_set,
        "OBSERVATIONS": int(len(data)),
        "DISTRICTS": int(data["UBIGEO"].nunique()),
        "PERIODS": int(data[period_column].nunique()),
        "CLUSTER_SIZE_MIN": int(cluster_sizes.min()),
        "CLUSTER_SIZE_MEDIAN": rounded(cluster_sizes.median()),
        "CLUSTER_SIZE_MAX": int(cluster_sizes.max()),
        "PERIOD_SIZE_MIN": int(period_sizes.min()),
        "PERIOD_SIZE_MEDIAN": rounded(period_sizes.median()),
        "PERIOD_SIZE_MAX": int(period_sizes.max()),
        "MISSING_X_CELLS": missing_x,
        "WITHIN_VARIANCE_JSON": json.dumps(
            {name: rounded(value) for name, value in zip(x_columns, variances)}, sort_keys=True, separators=(",", ":")
        ),
        "WITHIN_RANK": within_rank,
        "REGRESSORS": regressor_count,
        "MAX_ABS_PAIRWISE_CORRELATION": rounded(max_correlation),
        "CONDITION_NUMBER": rounded(condition_number),
        "MAX_VIF": rounded(max_vif),
        "PARTIAL_OBSERVATION_LEVERAGE_MAX": rounded(observation_leverage),
        "PARTIAL_CLUSTER_LEVERAGE_MEDIAN": rounded(np.median(cluster_leverages)) if cluster_leverages else None,
        "PARTIAL_CLUSTER_LEVERAGE_MAX": rounded(max(cluster_leverages)) if cluster_leverages else None,
        "FULL_DESIGN_RANK": full_design_rank,
        "IMPLIED_RESIDUAL_DF": residual_df,
        "PRIMARY_INFERENCE_COMPUTATION_FEASIBLE": "TRUE" if technically_feasible else "FALSE",
        "GEOMETRY_VERDICT": verdict,
    }


def build_geometry_rows(
    transient: pd.DataFrame, perennial: pd.DataFrame, b3: pd.DataFrame
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for crop_code in ("14010020000", "14010070000"):
        crop_data = transient[transient["COD_CULTIVO"] == crop_code].copy()
        for family in FAMILIES:
            rows.append(
                geometry_row(
                    crop_data,
                    list(FAMILIES[family]),
                    crop_code,
                    family,
                    "PRIMARY_SINGLE_WINDOW",
                    str(CROPS[crop_code]["windows"][0]),
                )
            )
    mango_code = "13010210000"
    for family in FAMILIES:
        frame, columns = single_window_frame(perennial, mango_code, family, str(CROPS[mango_code]["windows"][0]))
        rows.append(
            geometry_row(
                frame,
                columns,
                mango_code,
                family,
                "PRIMARY_SINGLE_WINDOW",
                str(CROPS[mango_code]["windows"][0]),
            )
        )
    for crop_code in ("13010170102", "15010040000"):
        crop = CROPS[crop_code]
        for family in FAMILIES:
            for window in crop["windows"]:
                frame, columns = single_window_frame(perennial, crop_code, family, str(window))
                rows.append(
                    geometry_row(frame, columns, crop_code, family, "P2_SEPARATE_WINDOW_DIAGNOSTIC", str(window))
                )
            frame, columns = joint_window_frame(perennial, crop_code, family)
            rows.append(
                geometry_row(
                    frame,
                    columns,
                    crop_code,
                    family,
                    "P1_JOINT_T_AND_T_MINUS_1_LINEAR",
                    "|".join(str(item) for item in crop["windows"]),
                )
            )
    for crop_code in ("14010020000", "14010070000"):
        crop_data = b3[b3["COD_CULTIVO"] == crop_code].copy()
        rows.append(
            geometry_row(
                crop_data,
                list(FAMILIES["PHYSICAL_ANOMALY"]),
                crop_code,
                "PHYSICAL_ANOMALY",
                "B3_STRICT_SENSITIVITY",
                str(CROPS[crop_code]["windows"][0]),
            )
        )
    return rows


def spatial_diagnostics() -> dict[str, Any]:
    source = json.loads(BOUNDARY_PATH.read_text(encoding="utf-8"))
    projector = Transformer.from_crs("EPSG:4326", "EPSG:32717", always_xy=True).transform
    centroids: list[tuple[str, float, float]] = []
    for feature in source["features"]:
        centroid = transform(projector, shape(feature["geometry"])).centroid
        centroids.append((str(feature["properties"]["UBIGEO"]), float(centroid.x), float(centroid.y)))
    centroids.sort()
    coordinates = np.array([(x, y) for _, x, y in centroids], dtype=float)
    distance_matrix = np.sqrt(((coordinates[:, None, :] - coordinates[None, :, :]) ** 2).sum(axis=2)) / 1000.0
    pairwise = distance_matrix[np.triu_indices(len(centroids), k=1)]
    nearest = np.where(distance_matrix == 0, np.inf, distance_matrix).min(axis=1)
    quantiles = (0.0, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0)
    bandwidth_support: dict[str, Any] = {}
    for bandwidth in SPATIAL_BANDWIDTHS_KM:
        neighbors = ((distance_matrix > 0) & (distance_matrix <= bandwidth)).sum(axis=1)
        bandwidth_support[str(bandwidth)] = {
            "neighbors_min": int(neighbors.min()),
            "neighbors_median": rounded(np.median(neighbors)),
            "neighbors_max": int(neighbors.max()),
        }
    return {
        "boundary_source": BOUNDARY_PATH.relative_to(ROOT).as_posix(),
        "boundary_sha256": FROZEN_HASHES[BOUNDARY_PATH],
        "source_crs": "EPSG:4326",
        "distance_crs": "EPSG:32717",
        "centroid_count": len(centroids),
        "distance_unit": "KM",
        "pairwise_distance_quantiles_km": {
            str(q): rounded(value) for q, value in zip(quantiles, np.quantile(pairwise, quantiles))
        },
        "nearest_neighbor_quantiles_km": {
            str(q): rounded(value) for q, value in zip(quantiles, np.quantile(nearest, quantiles))
        },
        "prespecified_bandwidths_km": list(SPATIAL_BANDWIDTHS_KM),
        "bandwidth_support": bandwidth_support,
        "selection_rule": "GEOGRAPHY_ONLY_ROUND_BANDWIDTH_GRID_SPANNING_LOCAL_TO_REGION_SCALE_NO_RESIDUAL_OR_OUTCOME_INPUT",
    }


def primary_geometry(rows: list[dict[str, Any]], crop_code: str) -> dict[str, Any]:
    expected_candidate = (
        "P1_JOINT_T_AND_T_MINUS_1_LINEAR"
        if crop_code in {"13010170102", "15010040000"}
        else "PRIMARY_SINGLE_WINDOW"
    )
    matches = [
        row
        for row in rows
        if row["CROP_CODE"] == crop_code
        and row["CLIMATE_FAMILY"] == "PHYSICAL_ANOMALY"
        and row["CANDIDATE"] == expected_candidate
    ]
    if len(matches) != 1:
        raise RuntimeError(f"Primary geometry is not unique for {crop_code}")
    return matches[0]


def model_contract_rows(geometry_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for crop_code, crop in CROPS.items():
        geometry = primary_geometry(geometry_rows, crop_code)
        suffixes = ("",) if len(crop["windows"]) == 1 else ("__T", "__T_MINUS_1")
        regressors = [f"{variable}{suffix}" for suffix in suffixes for variable in FAMILIES["PHYSICAL_ANOMALY"]]
        rows.append(
            {
                "MODEL_ID": crop["model_id"],
                "CROP_CODE": crop_code,
                "CROP": crop["crop"],
                "TEMPORAL_REGIME": crop["regime"],
                "INDEX_KEYS": f"UBIGEO|{crop['period_column']}",
                "OUTCOME_SCALE": "YIELD_LEVEL_TM_PER_HA",
                "WINDOW_ARCHITECTURE": crop["architecture"],
                "WINDOW_IDS": "|".join(str(item) for item in crop["windows"]),
                "PRIMARY_CLIMATE_FAMILY": "PHYSICAL_ANOMALY",
                "PRIMARY_REGRESSORS": "|".join(regressors),
                "CLIMATE_COEFFICIENT_COUNT": len(regressors),
                "DISTRICT_FE": "REQUIRED",
                "PERIOD_FE": "REQUIRED",
                "DISTRICT_TRENDS": "PROHIBITED",
                "FUNCTIONAL_FORM": "LINEAR_ADDITIVE",
                "PRIMARY_WEIGHTING": "UNWEIGHTED_PRIMARY_ESTIMATION",
                "OBSERVATIONS": geometry["OBSERVATIONS"],
                "DISTRICTS": geometry["DISTRICTS"],
                "PERIODS": geometry["PERIODS"],
                "PRIMARY_INFERENCE": "DISTRICT_CLUSTERED_CR2_BRL_SATTERTHWAITE",
                "JOINT_TEST": "CR2_APPROXIMATE_HOTELLING_T_SQUARED",
                "IDENTIFICATION_CEILING": "EMPIRICAL_ASSOCIATION_CLIMATE_RESPONSE_ONLY",
                "STATUS": "PASS" if geometry["GEOMETRY_VERDICT"] == "PASS" else geometry["GEOMETRY_VERDICT"],
            }
        )
    return rows


def inference_rows(spatial: dict[str, Any]) -> list[dict[str, Any]]:
    rows = [
        {
            "ORDER": 0,
            "INFERENCE_ID": "PRIMARY_CR2",
            "ROLE": "PRIMARY",
            "STATUS": "REQUIRED",
            "COVARIANCE": "CR2_BIAS_REDUCED_LINEARIZATION",
            "CLUSTER": "DISTRICT",
            "SMALL_SAMPLE_RULE": "SATTERTHWAITE_DF_COEFFICIENT_TESTS_AND_AHT_JOINT_TESTS",
            "IMPLEMENTATION": "PYTHON_3_11_7_PROJECT_LOCAL_fit_two_way_fe_cr2_NUMPY_2_3_5_SCIPY_1_16_3",
            "PRESPECIFICATION": "ALL_PRIMARY_COEFFICIENTS_AND_ONE_OMNIBUS_CLIMATE_CHANNEL_TEST_PER_CROP",
            "LIMITATION": "REPORT_COEFFICIENT_SPECIFIC_DF_AND_CLUSTER_LEVERAGE",
        },
        {
            "ORDER": 1,
            "INFERENCE_ID": "RESTRICTED_WILD_CLUSTER_BOOTSTRAP",
            "ROLE": "MANDATORY_ROBUSTNESS",
            "STATUS": "REQUIRED_WHERE_COMPUTATION_VALID",
            "COVARIANCE": "NULL_IMPOSED_WILD_CLUSTER_BOOTSTRAP_T",
            "CLUSTER": "DISTRICT",
            "SMALL_SAMPLE_RULE": "RADEMACHER_WEIGHTS_9999_REPLICATIONS_SEED_20260903_FINITE_REPLICATION_CORRECTION",
            "IMPLEMENTATION": "PROJECT_LOCAL_restricted_wild_cluster_bootstrap_t_TESTED_AT_9999_REPLICATIONS",
            "PRESPECIFICATION": "REPORT_REGARDLESS_OF_AGREEMENT_WITH_CR2_NO_VARIABLE_SELECTION",
            "LIMITATION": "REPORT_NONCOMPUTABILITY_WITHOUT_SUBSTITUTING_A_MODEL",
        },
    ]
    for offset, bandwidth in enumerate(SPATIAL_BANDWIDTHS_KM, start=2):
        support = spatial["bandwidth_support"][str(bandwidth)]
        rows.append(
            {
                "ORDER": offset,
                "INFERENCE_ID": f"SPATIAL_HAC_{bandwidth}KM",
                "ROLE": "ROBUSTNESS_ONLY",
                "STATUS": "PRESPECIFIED",
                "COVARIANCE": "CONLEY_TYPE_BARTLETT_DISTANCE_KERNEL",
                "CLUSTER": "DISTRICT_CENTROID_DISTANCE_WITHIN_PERIOD",
                "SMALL_SAMPLE_RULE": "NO_PRIMARY_SMALL_SAMPLE_CLAIM",
                "IMPLEMENTATION": f"PROJECT_LOCAL_conley_covariance_BANDWIDTH_{bandwidth}_KM_SAME_PERIOD_SPATIAL_PAIRS",
                "PRESPECIFICATION": (
                    f"GEOGRAPHY_ONLY;NEIGHBORS_MIN_{support['neighbors_min']};"
                    f"MEDIAN_{support['neighbors_median']};MAX_{support['neighbors_max']}"
                ),
                "LIMITATION": "DOES_NOT_REPLACE_PRIMARY_DISTRICT_CR2_SERIAL_DEPENDENCE_PROTECTION",
            }
        )
    rows.extend(
        [
            {
                "ORDER": 5,
                "INFERENCE_ID": "DRISCOLL_KRAAY",
                "ROLE": "NONE",
                "STATUS": "NOT_AUTHORIZED",
                "COVARIANCE": "NOT_APPLICABLE",
                "CLUSTER": "NOT_APPLICABLE",
                "SMALL_SAMPLE_RULE": "T_7_OR_8_IS_NOT_A_LARGE_TIME_DIMENSION",
                "IMPLEMENTATION": "PROHIBITED_IN_ED1_V1",
                "PRESPECIFICATION": "NONE",
                "LIMITATION": "ASYMPTOTIC_RATIONALE_REQUIRES_LARGE_T",
            },
            {
                "ORDER": 6,
                "INFERENCE_ID": "TWO_WAY_DISTRICT_PERIOD_CLUSTER",
                "ROLE": "NONE",
                "STATUS": "NOT_AUTHORIZED",
                "COVARIANCE": "NOT_APPLICABLE",
                "CLUSTER": "NOT_APPLICABLE",
                "SMALL_SAMPLE_RULE": "ONLY_7_OR_8_PERIOD_CLUSTERS",
                "IMPLEMENTATION": "PROHIBITED_IN_ED1_V1",
                "PRESPECIFICATION": "NONE",
                "LIMITATION": "FEW_PERIOD_CLUSTERS_PRECLUDE_PRIMARY_OR_DIAGNOSTIC_TOURNAMENT_ROLE",
            },
        ]
    )
    return rows


def robustness_rows() -> list[dict[str, Any]]:
    fixed = "CROP_SAMPLE|OUTCOME_LEVEL|WINDOWS|LINEAR_FORM|DISTRICT_FE|PERIOD_FE|UNWEIGHTED"
    fixed_without_sample = "OUTCOME_LEVEL|WINDOWS|LINEAR_FORM|DISTRICT_FE|PERIOD_FE|UNWEIGHTED"
    return [
        {
            "ORDER": 0,
            "TIER": "PRIMARY",
            "STATUS": "REQUIRED",
            "CHANGE_FROM_PRIMARY": "NONE",
            "FIXED_COMPONENTS": fixed,
            "INTERPRETATION": "PHYSICAL_ANOMALY_WITH_DISTRICT_CR2_SATTERTHWAITE",
            "NO_WINNER_RULE": "PRIMARY_BY_PRESPECIFICATION_NOT_RESULT",
        },
        {
            "ORDER": 1,
            "TIER": "R1_LEVEL_CLIMATE_FAMILY",
            "STATUS": "CROP_SPECIFIC_ROLE",
            "CHANGE_FROM_PRIMARY": "LEVEL_REPLACES_PHYSICAL_ANOMALY",
            "FIXED_COMPONENTS": fixed,
            "INTERPRETATION": "RICE_MAD_DISTINCT_ROBUSTNESS;MANGO_LEMON_BANANA_FE_EQUIVALENT_DIAGNOSTIC_NOT_DISTINCT_ROBUSTNESS",
            "NO_WINNER_RULE": "CANNOT_REPLACE_PRIMARY_BY_FIT_OR_SIGNIFICANCE",
        },
        {
            "ORDER": 2,
            "TIER": "R2_STANDARDIZED_ANOMALY_COMPARABILITY",
            "STATUS": "REQUIRED_SECONDARY",
            "CHANGE_FROM_PRIMARY": "STANDARDIZED_ANOMALY_REPLACES_PHYSICAL_ANOMALY",
            "FIXED_COMPONENTS": fixed,
            "INTERPRETATION": "ONE_LOCAL_CLIMATE_SD_CHANGE_IN_NATIVE_CROP_YIELD_UNITS",
            "NO_WINNER_RULE": "CROSS_CROP_COEFFICIENT_MAGNITUDE_RANKING_NOT_AUTHORIZED",
        },
        {
            "ORDER": 3,
            "TIER": "R3_RESTRICTED_WILD_CLUSTER_BOOTSTRAP",
            "STATUS": "MANDATORY_WHERE_VALID",
            "CHANGE_FROM_PRIMARY": "INFERENCE_ONLY",
            "FIXED_COMPONENTS": fixed,
            "INTERPRETATION": "FINITE_CLUSTER_INFERENCE_ROBUSTNESS",
            "NO_WINNER_RULE": "DISAGREEMENT_WITH_CR2_REPORTED_NOT_RESOLVED_BY_SELECTION",
        },
        {
            "ORDER": 4,
            "TIER": "R4_SPATIAL_HAC",
            "STATUS": "REQUIRED_ROBUSTNESS",
            "CHANGE_FROM_PRIMARY": "INFERENCE_ONLY_AT_50_100_150_KM",
            "FIXED_COMPONENTS": fixed,
            "INTERPRETATION": "CROSS_DISTRICT_SPATIAL_COVARIANCE_SENSITIVITY",
            "NO_WINNER_RULE": "REPORT_ALL_BANDWIDTHS_NO_BEST_BANDWIDTH",
        },
        {
            "ORDER": 5,
            "TIER": "R5_LEAVE_ONE_PERIOD_OUT_ALL_PERIODS",
            "STATUS": "REQUIRED_INFLUENCE_ROBUSTNESS",
            "CHANGE_FROM_PRIMARY": "OMIT_EACH_PERIOD_ONCE",
            "FIXED_COMPONENTS": fixed_without_sample,
            "INTERPRETATION": "PERIOD_INFLUENCE_WITH_EXPLICIT_2017_AND_2023_REPORTING",
            "NO_WINNER_RULE": "NO_OMISSION_RESULT_BECOMES_PRIMARY",
        },
        {
            "ORDER": 6,
            "TIER": "R6_B3_STRICT_EXPOSURE",
            "STATUS": "RICE_ESTIMABLE_SEVERE_SUPPORT_LIMITATION_MAD_NOT_ESTIMABLE",
            "CHANGE_FROM_PRIMARY": "STRICT_TRANSIENT_EXPOSURE_SAMPLE_AND_VALUES",
            "FIXED_COMPONENTS": fixed_without_sample,
            "INTERPRETATION": "ATTRIBUTION_QUALITY_SENSITIVITY_RICE_ONLY",
            "NO_WINNER_RULE": "B3_CANNOT_REPLACE_PRIMARY_OR_WEAKEN_FE",
        },
    ]


def config_record(
    preflight_result: dict[str, Any],
    geometry_rows: list[dict[str, Any]],
    model_rows: list[dict[str, Any]],
    spatial: dict[str, Any],
    implementation: dict[str, Any],
    equivalence: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    primary_support = {
        row["CROP_CODE"]: {
            "observations": row["OBSERVATIONS"],
            "districts": row["DISTRICTS"],
            "periods": row["PERIODS"],
            "within_rank": row["WITHIN_RANK"],
            "regressors": row["REGRESSORS"],
            "implied_residual_df": row["IMPLIED_RESIDUAL_DF"],
            "geometry_verdict": row["GEOMETRY_VERDICT"],
            "nominal_clusters": implementation["crop_diagnostics"][row["CROP_CODE"]]["nominal_clusters"],
            "effective_contributing_clusters": implementation["crop_diagnostics"][row["CROP_CODE"]][
                "effective_contributing_clusters"
            ],
        }
        for row in (primary_geometry(geometry_rows, code) for code in CROPS)
    }
    return {
        "schema_version": "1.1.0",
        "project": "ENSO_EL_NINO_2026_2027_AGRICULTURE_PIURA",
        "gate": "ED1H_TARGETED_PRE_FREEZE_ECONOMETRIC_DESIGN_HARDENING",
        "parent_gate": "ECONOMETRIC_DESIGN_MASTER_V1",
        "gate_id": "ED1H",
        "status": FINAL_VERDICT,
        "freeze_authorized": False,
        "pre_ed1h_sha256": PRE_ED1H_HASHES,
        "governing_state": {
            "e1_freeze_sha": E1_FREEZE_SHA,
            "e1_status": "PASS_FROZEN",
            "e1_tag": E1_TAG,
            "s1_freeze_sha": S1_FREEZE_SHA,
            "d0_freeze_sha": D0_FREEZE_SHA,
            "identification_ceiling": "EMPIRICAL_ASSOCIATION_CLIMATE_RESPONSE_ONLY",
            "continuous_optimization": "ABANDONED_NOT_AUTHORIZED",
        },
        "preflight": preflight_result,
        "outcome_blindness": {
            "real_outcome_values_read": False,
            "outcome_values_read_during_ed1": False,
            "outcome_value_columns_read": list(OUTCOME_VALUE_COLUMNS_READ),
            "permitted_outcome_information": "FROZEN_VALIDITY_FLAGS_AND_STRUCTURAL_SAMPLE_MEMBERSHIP_ONLY",
            "model_fit_read": False,
            "coefficients_estimated": False,
            "residuals_computed": False,
            "real_regressions": REAL_REGRESSIONS,
        },
        "primary_model_architecture": "FIVE_CROP_SPECIFIC_MODELS_NO_POOLED_COEFFICIENTS",
        "outcome_scale": {
            "primary": "YIELD_LEVEL_TM_PER_HA",
            "adjudication": "SELECTED_OUTCOME_BLIND",
            "basis": "FROZEN_METADATA_CERTIFIES_TM_PER_HA_BUT_NOT_STRICT_POSITIVITY;LEVEL_PRESERVES_ADDITIVE_PHYSICAL_AND_SCENARIO_INTERPRETATION_WITHOUT_LOG_RETRANSFORMATION",
            "log_yield": "NOT_AUTHORIZED_IN_ED1_V1_WITHOUT_SEPARATE_PRE_ESTIMATION_POSITIVITY_AND_RETRANSFORMATION_GATE",
            "winsorization": "PROHIBITED",
        },
        "climate_family_roles": {
            "PRIMARY": "PHYSICAL_ANOMALY",
            "SECONDARY_COMPARABILITY": "STANDARDIZED_ANOMALY",
            "TRANSIENT_ROBUSTNESS": "LEVEL_DISTINCT_CLIMATE_FAMILY_ROBUSTNESS",
            "PERENNIAL_LEVEL": "FE_EQUIVALENT_DIAGNOSTIC_NOT_DISTINCT_ROBUSTNESS",
            "selection_uses_outcomes": False,
        },
        "functional_form": {
            "primary": "LINEAR_ADDITIVE_THREE_CLIMATE_REGRESSORS_PER_WINDOW",
            "maximum_coefficients_single_window": 3,
            "maximum_coefficients_joint_window": 6,
            "nonlinearities": "NOT_AUTHORIZED_REQUIRES_SEPARATE_PRESPECIFIED_GATE",
            "interactions": "NOT_AUTHORIZED",
            "district_specific_trends": "PROHIBITED",
            "dynamic_dependent_variable": "PROHIBITED",
        },
        "fixed_effects": {
            "district": "REQUIRED",
            "period": "REQUIRED",
            "transient_period": "AUG_JUL_AGRICULTURAL_CAMPAIGN",
            "perennial_period": "CALENDAR_YEAR",
            "identification_interpretation": "WITHIN_DISTRICT_CLIMATE_VARIATION_CONDITIONAL_ON_REGION_WIDE_PERIOD_SHOCKS",
            "period_fe_forecastability": "NOT_FORECASTABLE_NOT_PROPAGATED_AS_FUTURE_QUANTITY",
        },
        "crop_model_contracts": model_rows,
        "primary_analytical_support": primary_support,
        "primary_transient_sample": {
            "rule": "D0_VALID_OUTCOME_AND_E1_VALID_EXPOSURE_FROZEN_INTERSECTION",
            "observations": 599,
            "rice": 281,
            "mad": 318,
            "additional_outcome_or_influence_restrictions": "PROHIBITED",
        },
        "identified_weight": {
            "usage": "DIAGNOSTIC_ONLY_NOT_REGRESSION_WEIGHT_NOT_PRIMARY_FILTER",
            "retain_all_e1_valid_primary_observations": True,
            "outcome_derived_cutoff": "PROHIBITED",
            "prespecified_exposure_quality_sensitivity": "B3_STRICT_SENSITIVITY_ONLY",
        },
        "regression_weighting": {
            "primary": "UNWEIGHTED_PRIMARY_ESTIMATION",
            "outcome_component_weights": "PROHIBITED",
            "price_weights": "PROHIBITED",
        },
        "perennial_window_adjudication": {
            "lemon": "P1_JOINT_T_AND_T_MINUS_1_LINEAR",
            "banana": "P1_JOINT_T_AND_T_MINUS_1_LINEAR",
            "basis": "X_ONLY_FULL_RANK_NON_NEAR_SINGULAR_GEOMETRY_AFTER_REQUIRED_FE",
            "outcome_based_window_winner": "PROHIBITED",
        },
        "geometry_gate": {
            "rank_required": "FULL_AFTER_DISTRICT_AND_PERIOD_FE",
            "within_variation_required": "STRICTLY_POSITIVE_FOR_EACH_REGRESSOR",
            "near_singular_diagnostic_thresholds": {"condition_number": 30.0, "max_vif": 10.0},
            "threshold_role": "PRE_ESTIMATION_BLOCK_DIAGNOSTIC_NOT_MODEL_RANKING",
            "geometry_rows": len(geometry_rows),
        },
        "inference": {
            "primary": "DISTRICT_CLUSTERED_CR2_BIAS_REDUCED_LINEARIZATION_WITH_SATTERTHWAITE_DF",
            "joint_tests": "CR2_APPROXIMATE_HOTELLING_T_SQUARED",
            "wild_cluster_bootstrap": "MANDATORY_RESTRICTED_NULL_IMPOSED_WCR_BOOTSTRAP_T_DISTRICT_CLUSTERED_RADEMACHER_9999_SEED_20260903",
            "driscoll_kraay": "NOT_AUTHORIZED_T_7_OR_8",
            "two_way_clustering": "NOT_AUTHORIZED_FEW_PERIOD_CLUSTERS",
            "spatial_hac": "ROBUSTNESS_ONLY_CONLEY_TYPE_BARTLETT_50_100_150_KM_SAME_PERIOD",
        },
        "inference_engine_feasibility": implementation,
        "spatial_diagnostics": spatial,
        "level_physical_anomaly_fe_equivalence": equivalence,
        "extreme_year_policy": {
            "retain_2017": True,
            "retain_2023": True,
            "trimming": "PROHIBITED",
            "winsorization": "PROHIBITED",
            "influence_exercise": "LEAVE_ONE_PERIOD_OUT_ALL_PERIODS",
            "mandatory_named_reporting": ["LEAVE_2017_OUT", "LEAVE_2023_OUT"],
            "primary_replacement": "PROHIBITED",
        },
        "b3_econometric_sensitivity": {
            "overall_role": "CROP_SPECIFIC_RICE_ESTIMABLE_WITH_SEVERE_SUPPORT_LIMITATION_MAD_NOT_ESTIMABLE_UNDER_PRIMARY_DESIGN",
            "rice": "ESTIMABLE_WITH_SEVERE_SUPPORT_LIMITATION_31_OBSERVATIONS_12_DISTRICTS_7_PERIODS",
            "mad": "B3_ECONOMETRIC_SENSITIVITY_NOT_ESTIMABLE_UNDER_PRIMARY_DESIGN",
            "same_outcome_scale_family_form_and_fe": True,
            "may_weaken_primary_design": False,
        },
        "cross_crop_comparability": {
            "channel": "STANDARDIZED_ANOMALY_SECONDARY_MODELS",
            "standardized_x_interpretation": "ONE_LOCAL_CLIMATE_SD_CHANGE_IN_NATIVE_CROP_YIELD_UNITS",
            "fully_standardized_effect_size": "NOT_CLAIMED_OUTCOME_REMAINS_NATIVE_YIELD_LEVEL_TM_PER_HA",
            "coefficient_magnitude_ranking": "NOT_AUTHORIZED",
            "allowed_comparisons": [
                "SIGN_DIRECTION",
                "UNCERTAINTY",
                "QUALITATIVE_PATTERN",
                "CONSISTENCY_ACROSS_CLIMATE_CHANNELS",
                "NATIVE_YIELD_RESPONSE_TO_LOCAL_ONE_SD_CLIMATE_PERTURBATION",
            ],
            "raw_physical_coefficient_magnitude_comparison": "NOT_AUTHORIZED",
            "shared_coefficients": "NOT_AUTHORIZED",
        },
        "multiplicity": {
            "all_prespecified_coefficients_reported": True,
            "coefficient_family": "WITHIN_CROP_PRIMARY_CLIMATE_COEFFICIENTS",
            "adjustment": "HOLM_STEP_DOWN_WITHIN_CROP_PRIMARY_CLIMATE_COEFFICIENTS",
            "unadjusted_results_also_reported": True,
            "global_five_crop_familywise_error_control": "NOT_CLAIMED",
            "cross_crop_significance_ranking": "PROHIBITED",
            "future_global_family": "REQUIRES_SEPARATELY_PRESPECIFIED_GATE",
            "omnibus_test": "ONE_PRESPECIFIED_JOINT_CLIMATE_CHANNEL_TEST_PER_CROP_REPORTED_SEPARATELY",
            "star_count_conclusions": "PROHIBITED",
            "variable_removal_by_p_value": "PROHIBITED",
        },
        "robustness_hierarchy": robustness_rows(),
        "future_scenario_covenant": {
            "scenarios_built_during_ed1": False,
            "future_period_fe": "MUST_NOT_BE_INVENTED_OR_PROPAGATED",
            "components_to_separate": [
                "CLIMATE_RESPONSE_COMPONENT",
                "DISTRICT_HISTORICAL_BASELINE",
                "CLIMATE_SCENARIO_UNCERTAINTY",
                "COEFFICIENT_AND_INFERENCE_UNCERTAINTY",
                "RESIDUAL_AND_PROCESS_UNCERTAINTY",
            ],
            "authorization": "REQUIRES_LATER_SCENARIO_GATE",
        },
        "method_literature_anchors": list(METHOD_ANCHORS),
        "previous_full_suite": {
            "tests_run": 693,
            "tests_passed": 642,
            "failures": 50,
            "errors": 1,
            "real_regressions": 0,
            "environmental_blockers_affecting_ed1": 0,
            "unresolved": 0,
            "category_counts": {
                "EXPECTED_HISTORICAL_LIFECYCLE_STATE": sum(
                    category == "EXPECTED_HISTORICAL_LIFECYCLE_STATE"
                    for _, _, category, _ in FULL_SUITE_NONPASSES
                ),
                "EXPECTED_ACTIVE_PHASE_FIREWALL": sum(
                    category == "EXPECTED_ACTIVE_PHASE_FIREWALL" for _, _, category, _ in FULL_SUITE_NONPASSES
                ),
                "REAL_REGRESSION": 0,
                "ENVIRONMENTAL_BLOCKER": 0,
                "UNRESOLVED": 0,
            },
            "nonpass_adjudication": [
                {"result": result, "test": test, "category": category, "reason": reason}
                for result, test, category, reason in FULL_SUITE_NONPASSES
            ],
        },
        "previous_full_suite_error": {
            "test_path": "tests/test_primary_transient_exposure_v1.py",
            "test_method": "PrimaryTransientExposureV1Tests.test_28_two_independent_builds_are_byte_identical",
            "exception_class": "RuntimeError",
            "traceback": PREVIOUS_FULL_SUITE_ERROR_TRACEBACK,
            "triggering_repository_state": (
                "ACTIVE_HEAD_E1_FREEZE_cdeb14b_WHILE_HISTORICAL_E1_REBUILD_PREFLIGHT_REQUIRES_S1_HEAD_2e5823e"
            ),
            "classification": "EXPECTED_HISTORICAL_LIFECYCLE_STATE",
            "reason": "E1 authoring rebuild guard intentionally requires the S1 parent state; ED1 executes after E1 freeze.",
            "historical_reproduction": {
                "status": "PASS",
                "head": S1_FREEZE_SHA,
                "branch": "phase/s1-scientific-identity-master-v1",
                "candidate_scope_count": 7,
                "test_result": "RAN_1_OK",
                "checkout_byte_policy": "core.autocrlf=false_FOR_TEMPORARY_WORKTREE_TO_PRESERVE_FROZEN_OBJECT_BYTES",
                "temporary_worktree_removed": True,
            },
        },
        "firewalls": {
            "coefficient_estimation": "PROHIBITED_NOT_EXECUTED",
            "synthetic_engine_coefficients": "PERMITTED_IMPLEMENTATION_TEST_ONLY_NOT_SCIENTIFIC_RESULTS",
            "outcome_numerical_read": "PROHIBITED_NOT_EXECUTED",
            "model_fit_selection": "PROHIBITED",
            "significance_selection": "PROHIBITED",
            "outcome_based_window_selection": "PROHIBITED",
            "pooled_five_crop_coefficients": "PROHIBITED",
            "future_scenarios": "PROHIBITED_NOT_BUILT",
            "gvp": "PROHIBITED_NOT_BUILT",
            "var_cvar": "PROHIBITED_NOT_BUILT",
            "optimization": "PROHIBITED_NOT_EXECUTED",
        },
        "real_regressions": REAL_REGRESSIONS,
        "unresolved_failures": 0,
        "critical_findings": 0,
        "major_findings": 0,
        "final_verdict": FINAL_VERDICT,
        "ed1_substantive_verdict_preserved": ED1_SUBSTANTIVE_VERDICT,
        "ed1_freeze_authorized": False,
        "ed1h_freeze_authorized": False,
        "next_action": "RETURN_TO_SCIENTIFIC_DIRECTOR_FOR_ED1_FREEZE_DECISION_IF_PASS",
    }


def report_text(config: dict[str, Any], geometry_rows: list[dict[str, Any]], artifact_hashes: dict[str, str]) -> str:
    lemon = primary_geometry(geometry_rows, "13010170102")
    banana = primary_geometry(geometry_rows, "15010040000")
    b3_rice = next(row for row in geometry_rows if row["CROP_CODE"] == "14010020000" and row["CANDIDATE"] == "B3_STRICT_SENSITIVITY")
    b3_mad = next(row for row in geometry_rows if row["CROP_CODE"] == "14010070000" and row["CANDIDATE"] == "B3_STRICT_SENSITIVITY")
    implementation = config["inference_engine_feasibility"]
    equivalence = config["level_physical_anomaly_fe_equivalence"]
    reference = implementation["independent_reference_validation"]
    wild = implementation["wild_cluster_bootstrap_validation"]
    lines = [
        "# ED1H Econometric Design Master v1 - Targeted pre-freeze hardening",
        "",
        "## 1. ED1 verdict",
        "",
        f"`{FINAL_VERDICT}`. The substantive ED1 design is preserved. This is not authorization to estimate real outcomes or freeze. `ED1H_FREEZE_AUTHORIZED=NO`.",
        "",
        "## 2. E1 / upstream preflight",
        "",
        f"E1 HEAD, `origin/{E1_BRANCH}`, and `{E1_TAG}` resolve to `{E1_FREEZE_SHA}`. All pinned E1, D0/S1-linked, phenology, perennial exposure, B3, boundary, and support artifacts pass SHA-256 verification.",
        "",
        "## 3. Outcome-blindness audit",
        "",
        "`REAL_OUTCOME_VALUES_READ=FALSE`; `REAL_REGRESSIONS=0`. ED1H reads only climate X, frozen validity flags, structural keys, and aggregate support counts. Synthetic responses are SHA-256 functions of district and period keys only; all computed coefficients, residuals, test statistics, and p-values are implementation diagnostics without scientific interpretation.",
        "",
        "## 4. Five crop analytical support",
        "",
        "| Crop | Observations | Districts | Periods | Climate coefficients | Geometry |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for code in CROPS:
        row = primary_geometry(geometry_rows, code)
        lines.append(
            f"| {CROPS[code]['crop']} | {row['OBSERVATIONS']} | {row['DISTRICTS']} | {row['PERIODS']} | {row['REGRESSORS']} | {row['GEOMETRY_VERDICT']} |"
        )
    lines.extend(
        [
            "",
            "## 5. Outcome-scale adjudication",
            "",
            "`YIELD_LEVEL_TM_PER_HA` is primary. Frozen metadata certifies the physical unit but not strict positivity, so a log design would require opening outcome support and a retransformation rule. Level yield preserves additive physical and later scenario interpretation. Log yield is not authorized in ED1 v1 absent a separate pre-estimation gate.",
            "",
            "## 6. Climate-family adjudication",
            "",
        "`PHYSICAL_ANOMALY=PRIMARY` and `STANDARDIZED_ANOMALY=SECONDARY_COMPARABILITY`. Exact required-FE analysis makes `LEVEL` a distinct robustness family only for Rice/MAD; for Mango/Lemon/Banana it is an FE-equivalent diagnostic, not a distinct robustness specification.",
        "",
        "| Crop | Max transformed-X discrepancy | Combined rank | FE-equivalent | LEVEL role |",
        "|---|---:|---:|---|---|",
        *[
            f"| {CROPS[code]['crop']} | {equivalence[code]['maximum_absolute_transformed_x_discrepancy']} | {equivalence[code]['combined_within_rank']} | {'YES' if equivalence[code]['elementwise_equal_within_tolerance'] else 'NO'} | {equivalence[code]['level_role']} |"
            for code in CROPS
        ],
            "",
            "## 7. Fixed-effect contract",
            "",
            "District FE and period FE are required. Period means agricultural campaign for Rice/MAD and calendar year for perennials. District-specific trends are prohibited. Identification is the remaining within-district/cross-district climate variation conditional on region-wide period shocks.",
            "",
            "## 8. Transient model contract",
            "",
            "Rice and MAD are separate unweighted linear models on the frozen D0-valid and E1-valid intersection. Each contains three physical-anomaly regressors, district FE, campaign FE, and no pooled crop coefficient.",
            "",
            "## 9. Mango model contract",
            "",
            "Mango uses `MANGO_MAY_JUN_CURRENT_YEAR`, three physical-anomaly regressors, district FE, and calendar-year FE in a separate crop model.",
            "",
            "## 10. Lemon t / t-1 adjudication",
            "",
            f"`P1_JOINT_T_AND_T_MINUS_1_LINEAR` passes X-only geometry: rank {lemon['WITHIN_RANK']}/{lemon['REGRESSORS']}, condition number {lemon['CONDITION_NUMBER']}, maximum VIF {lemon['MAX_VIF']}, and implied residual df {lemon['IMPLIED_RESIDUAL_DF']}. Both frozen windows remain; no winner is selected.",
            "",
            "## 11. Banana t / t-1 adjudication",
            "",
            f"`P1_JOINT_T_AND_T_MINUS_1_LINEAR` passes X-only geometry: rank {banana['WITHIN_RANK']}/{banana['REGRESSORS']}, condition number {banana['CONDITION_NUMBER']}, maximum VIF {banana['MAX_VIF']}, and implied residual df {banana['IMPLIED_RESIDUAL_DF']}. Both frozen windows remain; no winner is selected.",
            "",
            "## 12. X-only geometry / collinearity",
            "",
            f"The support matrix contains {len(geometry_rows)} prespecified X-only rows across all climate families, separate and joint perennial candidates, and B3. Every primary row has full within rank, nonzero within variance, condition number below 30, maximum VIF below 10, positive residual df, and feasible computation. Leverage is disclosed, never used to delete observations.",
            "",
            "| Crop | Nominal clusters | Effective clusters | Zero contribution | Singletons | CR2 extra singularities |",
            "|---|---:|---:|---:|---:|---:|",
            *[
                f"| {CROPS[code]['crop']} | {implementation['crop_diagnostics'][code]['nominal_clusters']} | {implementation['crop_diagnostics'][code]['effective_contributing_clusters']} | {implementation['crop_diagnostics'][code]['zero_effective_clusters']} | {implementation['crop_diagnostics'][code]['singleton_clusters']} | {implementation['crop_diagnostics'][code]['cr2_adjustment_singularities']} |"
                for code in CROPS
            ],
            "",
            "## 13. Complexity budget",
            "",
            "Rice, MAD, and Mango use exactly three climate coefficients. Lemon and Banana use exactly six in the joint-window architecture. No interaction, quadratic, spline, threshold, bin, GDD, or event transformation is authorized.",
            "",
            "## 14. Primary sample contract",
            "",
            "The transient primary sample is exactly 599 frozen joint-valid observations: Rice 281 and MAD 318. Perennial structural samples are Mango 255, Lemon 311, and Banana 390. No outcome, residual, influence, or significance restriction is added.",
            "",
            "## 15. Identified-weight rule",
            "",
            "`IDENTIFIED_WEIGHT_USAGE=DIAGNOSTIC_ONLY_NOT_REGRESSION_WEIGHT_NOT_PRIMARY_FILTER`. All E1-valid primary observations remain. No cutoff is introduced; B3 is the only prespecified attribution-quality sensitivity.",
            "",
            "## 16. Regression-weighting rule",
            "",
            "`UNWEIGHTED_PRIMARY_ESTIMATION`. Harvest, production, price, outcome-derived precision, and identified-fraction weights are prohibited in the primary design.",
            "",
            "## 17. Primary inference contract",
            "",
            "The executable path is project-local Python 3.11.7 with NumPy 2.3.5 and SciPy 1.16.3: `fit_two_way_fe_cr2` performs SVD two-way-FE absorption, OLS, identity-target CR2, coefficient Satterthwaite df, and `_aht_htz` joint tests. Float64, `rcond=1e-12` Moore-Penrose inverses, symmetric eigen pseudoinverse roots, and district clusters are fixed conventions.",
            "",
            f"Independent full-design SVD validation is `{reference['status']}` at tolerance {reference['tolerance']}: coefficient, CR2 covariance, Satterthwaite df, AHT F, and AHT denominator-df maximum discrepancies are {json.dumps(reference['differences'], sort_keys=True, separators=(',', ':'))}.",
            "",
            "| Crop | Satterthwaite df min | Satterthwaite df max | AHT denominator df | Non-finite |",
            "|---|---:|---:|---:|---:|",
            *[
                f"| {CROPS[code]['crop']} | {implementation['crop_diagnostics'][code]['coefficient_specific_satterthwaite_df_minimum']} | {implementation['crop_diagnostics'][code]['coefficient_specific_satterthwaite_df_maximum']} | {implementation['crop_diagnostics'][code]['aht_denominator_df']} | {implementation['crop_diagnostics'][code]['nonfinite_quantities']} |"
                for code in CROPS
            ],
            "",
            "## 18. Wild cluster bootstrap contract",
            "",
            f"Restricted null-imposed wild cluster bootstrap-t is mandatory where computationally valid: district clusters, Rademacher weights, 9,999 replications, seed 20260903, and `(1+exceedances)/(B+1)`. The actual engine ran all 9,999 synthetic replications twice for an individual coefficient and a joint climate restriction with `{wild['status']}`, zero invalid replications, coefficient digest `{wild['run_one']['bootstrap_t_sha256']}`, and joint digest `{wild['joint_run_one']['bootstrap_t_sha256']}`. Future execution covers each primary climate coefficient and the prespecified omnibus climate test and cannot select variables.",
            "",
            "## 19. Spatial dependence contract",
            "",
            f"`SPATIAL_HAC_ROLE=ROBUSTNESS_ONLY`. `conley_covariance` constructed finite synthetic-residual covariance matrices for all five crops at 50, 100, and 150 km (`{implementation['conley_engine_validation']}`). It uses EPSG:32717 district centroids, Bartlett distance weights, and same-period pairs. None is selected by residuals or outcomes.",
            "",
            "## 20. Driscoll-Kraay / two-way cluster status",
            "",
            "`DRISCOLL_KRAAY=NOT_AUTHORIZED_T_7_OR_8` and `TWO_WAY_CLUSTERING=NOT_AUTHORIZED_FEW_PERIOD_CLUSTERS`. Neither enters an estimator tournament or substitutes for primary district CR2 inference.",
            "",
            "## 21. Extreme-year influence contract",
            "",
            "2017 and 2023 remain in primary samples without trimming or winsorization. `LEAVE_ONE_PERIOD_OUT_ALL_PERIODS` is required later, including named leave-2017-out and leave-2023-out reporting. No omission becomes primary.",
            "",
            "## 22. B3 econometric sensitivity contract",
            "",
            f"Rice B3 is estimable only as a severe-support-limitation sensitivity ({b3_rice['OBSERVATIONS']} observations, {b3_rice['DISTRICTS']} districts, rank {b3_rice['WITHIN_RANK']}/{b3_rice['REGRESSORS']}, residual df {b3_rice['IMPLIED_RESIDUAL_DF']}). MAD B3 is `B3_ECONOMETRIC_SENSITIVITY_NOT_ESTIMABLE_UNDER_PRIMARY_DESIGN` ({b3_mad['OBSERVATIONS']} observations, rank {b3_mad['WITHIN_RANK']}/{b3_mad['REGRESSORS']}, residual df {b3_mad['IMPLIED_RESIDUAL_DF']}). Required FE are not weakened.",
            "",
            "## 23. Cross-crop comparability contract",
            "",
            "Standardized-anomaly secondary models are the comparison channel. Their exact interpretation is `ONE_LOCAL_CLIMATE_SD_CHANGE_IN_NATIVE_CROP_YIELD_UNITS`; the yield outcome remains unstandardized. Direction, uncertainty, qualitative pattern, channel consistency, and native-yield response to a local one-SD climate perturbation may be compared. `CROSS_CROP_COEFFICIENT_MAGNITUDE_RANKING=NOT_AUTHORIZED`.",
            "",
            "## 24. Robustness hierarchy",
            "",
            "The exact order is `PRIMARY`, `R1_LEVEL_CLIMATE_FAMILY`, `R2_STANDARDIZED_ANOMALY_COMPARABILITY`, `R3_RESTRICTED_WILD_CLUSTER_BOOTSTRAP`, `R4_SPATIAL_HAC`, `R5_LEAVE_ONE_PERIOD_OUT_ALL_PERIODS`, and `R6_B3_STRICT_EXPOSURE`. R1 has a crop-specific role: distinct robustness for Rice/MAD and FE-equivalent diagnostic for perennials. No result may reorder or replace this hierarchy.",
            "",
            "Within each crop, Holm step-down applies to primary climate coefficients and unadjusted results remain reported. `GLOBAL_FIVE_CROP_FAMILYWISE_ERROR_CONTROL=NOT_CLAIMED`; `CROSS_CROP_SIGNIFICANCE_RANKING=PROHIBITED`.",
            "",
            "## 25. Future scenario-propagation covenant",
            "",
            "No scenario is built. A later gate must separate the climate-response component, district historical baseline, climate-scenario uncertainty, coefficient/inference uncertainty, and residual/process uncertainty. It must not invent or forecast a future period FE.",
            "",
            "## 26. Created candidate artifacts",
            "",
        ]
    )
    for relative, digest in artifact_hashes.items():
        lines.append(f"- `{relative}`: `{digest}`")
    lines.extend(
        [
            "",
            "The generator and tests are `scripts/econometric_design_master_v1.py` and `tests/test_econometric_design_master_v1.py`. No coefficient or result table exists.",
            "",
            "## 27. ED1 test results",
            "",
            "The ED1 test contract is extended without removing prior tests. It now executes the concrete inference path, structural-key synthetic-response firewall, effective-cluster accounting, CR2/Satterthwaite/AHT feasibility, 9,999-replication WCR determinism, Conley finiteness, FE equivalence, cross-crop interpretation, multiplicity firewalls, and exact prior error adjudication.",
            "",
            "## 28. Full-suite adjudication",
            "",
            "The previous full suite ran 693 tests: 642 pass, 50 fail, and 1 error. All 51 exact nonpasses are machine-readable in the config: 45 expected historical lifecycle states and 6 expected active-phase firewalls; real regression, environmental blocker affecting ED1, and unresolved counts are zero. The sole error is `tests/test_primary_transient_exposure_v1.py::PrimaryTransientExposureV1Tests.test_28_two_independent_builds_are_byte_identical`, a RuntimeError because the historical E1 rebuild guard requires S1 HEAD while ED1 runs at frozen E1 HEAD. Recreated at S1 HEAD with the exact seven-file E1 candidate scope and LF-preserving checkout, that test ran 1/1 OK; the temporary worktree was removed.",
            "",
            "## 29. Findings by severity",
            "",
            "Critical findings: 0. Major findings: 0. All primary inference-engine diagnostics pass. Design limitation: B3 strict sensitivity is sparse for Rice and not estimable for MAD under the required primary FE architecture.",
            "",
            "## 30. Exact next action",
            "",
            "`RETURN_TO_SCIENTIFIC_DIRECTOR_FOR_ED1_FREEZE_DECISION_IF_PASS`. Do not estimate real outcomes, stage, commit, push, or tag under this gate.",
            "",
            "PROJECT =",
            "ENSO_EL_NINO_2026_2027_AGRICULTURE_PIURA",
            "",
            "GATE =",
            "ED1H_TARGETED_PRE_FREEZE_ECONOMETRIC_DESIGN_HARDENING",
            "",
            "E1_FREEZE_SHA =",
            E1_FREEZE_SHA,
            "",
            "E1_STATUS =",
            "PASS_FROZEN",
            "",
            "REAL_OUTCOME_VALUES_READ =",
            "FALSE",
            "",
            "PRIMARY_MODELS =",
            "FIVE_CROP_SPECIFIC_MODELS",
            "",
            "DISTRICT_FE = REQUIRED",
            "",
            "PERIOD_FE = REQUIRED",
            "",
            "OUTCOME_SCALE = YIELD_LEVEL_TM_PER_HA",
            "",
            "PRIMARY_CLIMATE_FAMILY = PHYSICAL_ANOMALY",
            "",
            "SECONDARY_COMPARABILITY_FAMILY = STANDARDIZED_ANOMALY",
            "",
            "TRANSIENT_LEVEL_ROLE = DISTINCT_CLIMATE_FAMILY_ROBUSTNESS",
            "",
            "PERENNIAL_LEVEL_ROLE = FE_EQUIVALENT_DIAGNOSTIC_NOT_DISTINCT_ROBUSTNESS",
            "",
            "PRIMARY_FUNCTIONAL_FORM = LINEAR_ADDITIVE",
            "",
            "TRANSIENT_PRIMARY_SAMPLE = 599",
            "",
            "PRIMARY_REGRESSION_WEIGHTING = UNWEIGHTED_PRIMARY_ESTIMATION",
            "",
            "IDENTIFIED_WEIGHT_USAGE = DIAGNOSTIC_ONLY_NOT_REGRESSION_WEIGHT_NOT_PRIMARY_FILTER",
            "",
            "LEMON_WINDOW_ARCHITECTURE = P1_JOINT_T_AND_T_MINUS_1_LINEAR",
            "",
            "BANANA_WINDOW_ARCHITECTURE = P1_JOINT_T_AND_T_MINUS_1_LINEAR",
            "",
            "PRIMARY_INFERENCE = DISTRICT_CLUSTERED_CR2_BRL_SATTERTHWAITE",
            "",
            "WILD_CLUSTER_BOOTSTRAP = MANDATORY_RESTRICTED_DISTRICT_CLUSTERED_ROBUSTNESS",
            "",
            "DRISCOLL_KRAAY = NOT_AUTHORIZED",
            "",
            "TWO_WAY_CLUSTERING = NOT_AUTHORIZED",
            "",
            "SPATIAL_HAC = ROBUSTNESS_ONLY_50_100_150_KM",
            "",
            "B3_ECONOMETRIC_ROLE = CROP_SPECIFIC_RICE_LIMITED_MAD_NOT_ESTIMABLE",
            "",
            "EXTREME_YEAR_POLICY = RETAIN_2017_AND_2023_LEAVE_ONE_PERIOD_OUT_ALL_PERIODS",
            "",
            "STANDARDIZED_X_CROSS_CROP_INTERPRETATION = ONE_LOCAL_CLIMATE_SD_CHANGE_IN_NATIVE_CROP_YIELD_UNITS",
            "",
            "CROSS_CROP_COEFFICIENT_MAGNITUDE_RANKING = NOT_AUTHORIZED",
            "",
            "GLOBAL_FIVE_CROP_FWER_CONTROL = NOT_CLAIMED",
            "",
            "SCENARIO_PERIOD_FE_POLICY = DO_NOT_INVENT_OR_PROPAGATE_FUTURE_PERIOD_FE",
            "",
            "REAL_REGRESSIONS = 0",
            "",
            "UNRESOLVED_FAILURES = 0",
            "",
            "CRITICAL_FINDINGS = 0",
            "",
            "MAJOR_FINDINGS = 0",
            "",
            "FINAL_VERDICT = " + FINAL_VERDICT,
            "",
            "ED1H_FREEZE_AUTHORIZED =",
            "NO",
            "",
            "NEXT_ACTION =",
            "RETURN_TO_SCIENTIFIC_DIRECTOR_FOR_ED1_FREEZE_DECISION_IF_PASS",
            "",
        ]
    )
    return "\n".join(lines)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode("utf-8"))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise RuntimeError(f"Cannot write empty CSV: {path}")
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(
        buffer,
        fieldnames=list(rows[0]),
        lineterminator="\n",
        quoting=csv.QUOTE_MINIMAL,
        extrasaction="raise",
    )
    writer.writeheader()
    writer.writerows(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(buffer.getvalue().encode("utf-8"))


def run(output_root: Path) -> dict[str, str]:
    preflight_result = preflight()
    transient = read_transient_primary()
    perennial = read_perennial_primary()
    b3 = read_b3_sensitivity()
    geometry_rows = build_geometry_rows(transient, perennial, b3)
    if len(geometry_rows) != 29:
        raise RuntimeError(f"Unexpected X-geometry row count: {len(geometry_rows)}")
    model_rows = model_contract_rows(geometry_rows)
    if len(model_rows) != 5 or any(row["STATUS"] != "PASS" for row in model_rows):
        raise RuntimeError("One or more primary crop designs failed")
    spatial = spatial_diagnostics()
    implementation = implementation_feasibility(transient, perennial)
    equivalence = level_anomaly_equivalence(transient, perennial)
    inference = inference_rows(spatial)
    robustness = robustness_rows()
    config = config_record(
        preflight_result, geometry_rows, model_rows, spatial, implementation, equivalence
    )

    write_json(output_root / CONFIG_REL, config)
    write_csv(output_root / MODEL_CONTRACTS_REL, model_rows)
    write_csv(output_root / X_GEOMETRY_REL, geometry_rows)
    write_csv(output_root / INFERENCE_MATRIX_REL, inference)
    write_csv(output_root / ROBUSTNESS_REL, robustness)

    report_inputs = (CONFIG_REL, MODEL_CONTRACTS_REL, X_GEOMETRY_REL, INFERENCE_MATRIX_REL, ROBUSTNESS_REL)
    report_hashes = {relative.as_posix(): sha256_file(output_root / relative) for relative in report_inputs}
    report_path = output_root / REPORT_REL
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_bytes(report_text(config, geometry_rows, report_hashes).encode("utf-8"))
    return {relative.as_posix(): sha256_file(output_root / relative) for relative in OUTPUT_RELS}


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the outcome-blind ED1 econometric design master.")
    parser.add_argument("--output-root", type=Path, default=ROOT)
    args = parser.parse_args()
    hashes = run(args.output_root.resolve())
    print("ED1H_PREFLIGHT=PASS")
    print("REAL_OUTCOME_VALUES_READ=FALSE")
    print("REAL_REGRESSIONS=0")
    for relative, digest in hashes.items():
        print(f"SHA256={digest}  {relative}")
    print(f"FINAL_VERDICT={FINAL_VERDICT}")
    print("ED1H_FREEZE_AUTHORIZED=NO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
