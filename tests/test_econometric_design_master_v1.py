from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import econometric_design_master_v1 as ed1  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class EconometricDesignMasterV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config_path = ROOT / ed1.CONFIG_REL
        cls.report_path = ROOT / ed1.REPORT_REL
        cls.model_path = ROOT / ed1.MODEL_CONTRACTS_REL
        cls.geometry_path = ROOT / ed1.X_GEOMETRY_REL
        cls.inference_path = ROOT / ed1.INFERENCE_MATRIX_REL
        cls.robustness_path = ROOT / ed1.ROBUSTNESS_REL
        cls.config = json.loads(cls.config_path.read_text(encoding="utf-8"))
        cls.report = cls.report_path.read_text(encoding="utf-8")
        cls.models = read_csv(cls.model_path)
        cls.geometry = read_csv(cls.geometry_path)
        cls.inference = read_csv(cls.inference_path)
        cls.robustness = read_csv(cls.robustness_path)

        cls.parquet_columns: list[set[str]] = []
        cls.csv_columns: list[set[str]] = []
        original_parquet = ed1.pq.read_table
        original_csv = ed1.pd.read_csv

        def tracked_parquet(*args, **kwargs):
            cls.parquet_columns.append(set(kwargs.get("columns") or []))
            return original_parquet(*args, **kwargs)

        def tracked_csv(*args, **kwargs):
            usecols = kwargs.get("usecols")
            cls.csv_columns.append(set(usecols or []))
            return original_csv(*args, **kwargs)

        cls.temp_one = tempfile.TemporaryDirectory()
        cls.temp_two = tempfile.TemporaryDirectory()
        root_one = Path(cls.temp_one.name)
        root_two = Path(cls.temp_two.name)
        with patch.object(ed1.pq, "read_table", side_effect=tracked_parquet), patch.object(
            ed1.pd, "read_csv", side_effect=tracked_csv
        ):
            cls.hashes_one = ed1.run(root_one)
        cls.hashes_two = ed1.run(root_two)
        cls.bytes_one = {relative: (root_one / relative).read_bytes() for relative in ed1.OUTPUT_RELS}
        cls.bytes_two = {relative: (root_two / relative).read_bytes() for relative in ed1.OUTPUT_RELS}

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp_one.cleanup()
        cls.temp_two.cleanup()

    def test_01_e1_frozen_identity(self) -> None:
        preflight = ed1.preflight()
        self.assertEqual(preflight["status"], "PASS")
        self.assertEqual(preflight["identity"]["branch"], ed1.E1_BRANCH)
        self.assertEqual(preflight["identity"]["head"], ed1.E1_FREEZE_SHA)
        self.assertEqual(preflight["identity"]["remote_e1"], ed1.E1_FREEZE_SHA)
        self.assertEqual(preflight["identity"]["e1_tag_target"], ed1.E1_FREEZE_SHA)

    def test_02_all_pinned_upstream_hashes_match(self) -> None:
        for path, expected in ed1.FROZEN_HASHES.items():
            self.assertEqual(sha256(path), expected, path.relative_to(ROOT).as_posix())
        self.assertEqual(self.config["preflight"]["changed_frozen_paths"], [])

    def test_03_no_numerical_outcome_columns_are_read(self) -> None:
        forbidden = {
            "YIELD_RAW",
            "TRANSIENT_CAMPAIGN_YIELD_RAW",
            "PRODUCCION",
            "COSECHA",
            "PRECIO_CHACRA",
            "GVP",
            "profit",
        }
        self.assertEqual(ed1.OUTCOME_VALUE_COLUMNS_READ, ())
        for columns in [*self.parquet_columns, *self.csv_columns]:
            self.assertTrue(columns.isdisjoint(forbidden), columns & forbidden)
        self.assertNotIn("data/processed/panel_master.csv", {path.as_posix() for path in ed1.FROZEN_HASHES})
        self.assertFalse(self.config["outcome_blindness"]["outcome_values_read_during_ed1"])

    def test_04_no_regression_or_fit_execution(self) -> None:
        self.assertEqual(ed1.REAL_REGRESSIONS, 0)
        self.assertEqual(self.config["real_regressions"], 0)
        blindness = self.config["outcome_blindness"]
        self.assertFalse(blindness["coefficients_estimated"])
        self.assertFalse(blindness["residuals_computed"])
        self.assertFalse(blindness["model_fit_read"])

    def test_05_five_separate_crop_contracts(self) -> None:
        self.assertEqual(len(self.models), 5)
        self.assertEqual({row["CROP_CODE"] for row in self.models}, set(ed1.CROPS))
        self.assertEqual(self.config["primary_model_architecture"], "FIVE_CROP_SPECIFIC_MODELS_NO_POOLED_COEFFICIENTS")
        self.assertEqual(self.config["firewalls"]["pooled_five_crop_coefficients"], "PROHIBITED")

    def test_06_required_fixed_effects(self) -> None:
        self.assertTrue(all(row["DISTRICT_FE"] == "REQUIRED" for row in self.models))
        self.assertTrue(all(row["PERIOD_FE"] == "REQUIRED" for row in self.models))
        self.assertEqual(self.config["fixed_effects"]["district"], "REQUIRED")
        self.assertEqual(self.config["fixed_effects"]["period"], "REQUIRED")

    def test_07_forbidden_primary_architectures_remain_forbidden(self) -> None:
        form = self.config["functional_form"]
        self.assertEqual(form["district_specific_trends"], "PROHIBITED")
        self.assertEqual(form["dynamic_dependent_variable"], "PROHIBITED")
        self.assertEqual(form["interactions"], "NOT_AUTHORIZED")
        self.assertIn("SEPARATE_PRESPECIFIED_GATE", form["nonlinearities"])

    def test_08_outcome_scale_is_frozen_without_outcome_inspection(self) -> None:
        scale = self.config["outcome_scale"]
        self.assertEqual(scale["primary"], "YIELD_LEVEL_TM_PER_HA")
        self.assertEqual(scale["adjudication"], "SELECTED_OUTCOME_BLIND")
        self.assertIn("NOT_AUTHORIZED", scale["log_yield"])
        self.assertEqual(scale["winsorization"], "PROHIBITED")

    def test_09_climate_family_roles_are_explicit(self) -> None:
        self.assertEqual(
            self.config["climate_family_roles"],
            {
                "PERENNIAL_LEVEL": "FE_EQUIVALENT_DIAGNOSTIC_NOT_DISTINCT_ROBUSTNESS",
                "PRIMARY": "PHYSICAL_ANOMALY",
                "SECONDARY_COMPARABILITY": "STANDARDIZED_ANOMALY",
                "TRANSIENT_ROBUSTNESS": "LEVEL_DISTINCT_CLIMATE_FAMILY_ROBUSTNESS",
                "selection_uses_outcomes": False,
            },
        )

    def test_10_climate_complexity_budget(self) -> None:
        counts = {row["CROP_CODE"]: int(row["CLIMATE_COEFFICIENT_COUNT"]) for row in self.models}
        self.assertEqual(counts["14010020000"], 3)
        self.assertEqual(counts["14010070000"], 3)
        self.assertEqual(counts["13010210000"], 3)
        self.assertEqual(counts["13010170102"], 6)
        self.assertEqual(counts["15010040000"], 6)

    def test_11_exact_perennial_window_architecture(self) -> None:
        models = {row["CROP_CODE"]: row for row in self.models}
        self.assertEqual(models["13010210000"]["WINDOW_IDS"], "MANGO_MAY_JUN_CURRENT_YEAR")
        self.assertEqual(models["13010170102"]["WINDOW_ARCHITECTURE"], "P1_JOINT_T_AND_T_MINUS_1_LINEAR")
        self.assertEqual(models["15010040000"]["WINDOW_ARCHITECTURE"], "P1_JOINT_T_AND_T_MINUS_1_LINEAR")
        self.assertEqual(
            models["13010170102"]["WINDOW_IDS"], "LEMON_FULL_YEAR_T|LEMON_FULL_YEAR_T_MINUS_1"
        )
        self.assertEqual(
            models["15010040000"]["WINDOW_IDS"], "BANANA_FULL_YEAR_T|BANANA_FULL_YEAR_T_MINUS_1"
        )
        self.assertEqual(self.config["perennial_window_adjudication"]["outcome_based_window_winner"], "PROHIBITED")

    def test_12_primary_transient_sample_is_exact(self) -> None:
        sample = self.config["primary_transient_sample"]
        self.assertEqual(sample["rule"], "D0_VALID_OUTCOME_AND_E1_VALID_EXPOSURE_FROZEN_INTERSECTION")
        self.assertEqual((sample["observations"], sample["rice"], sample["mad"]), (599, 281, 318))
        self.assertEqual(sample["additional_outcome_or_influence_restrictions"], "PROHIBITED")

    def test_13_identified_weight_rule(self) -> None:
        rule = self.config["identified_weight"]
        self.assertEqual(rule["usage"], "DIAGNOSTIC_ONLY_NOT_REGRESSION_WEIGHT_NOT_PRIMARY_FILTER")
        self.assertTrue(rule["retain_all_e1_valid_primary_observations"])
        self.assertEqual(rule["outcome_derived_cutoff"], "PROHIBITED")

    def test_14_primary_regression_is_unweighted(self) -> None:
        weighting = self.config["regression_weighting"]
        self.assertEqual(weighting["primary"], "UNWEIGHTED_PRIMARY_ESTIMATION")
        self.assertEqual(weighting["outcome_component_weights"], "PROHIBITED")
        self.assertTrue(all(row["PRIMARY_WEIGHTING"] == "UNWEIGHTED_PRIMARY_ESTIMATION" for row in self.models))

    def test_15_primary_cr2_satterthwaite_inference(self) -> None:
        primary = next(row for row in self.inference if row["INFERENCE_ID"] == "PRIMARY_CR2")
        self.assertEqual(primary["ROLE"], "PRIMARY")
        self.assertEqual(primary["STATUS"], "REQUIRED")
        self.assertEqual(primary["CLUSTER"], "DISTRICT")
        self.assertIn("SATTERTHWAITE", primary["SMALL_SAMPLE_RULE"])
        self.assertIn("AHT", primary["SMALL_SAMPLE_RULE"])

    def test_16_restricted_wild_cluster_bootstrap_is_mandatory(self) -> None:
        wild = next(row for row in self.inference if row["INFERENCE_ID"] == "RESTRICTED_WILD_CLUSTER_BOOTSTRAP")
        self.assertEqual(wild["ROLE"], "MANDATORY_ROBUSTNESS")
        self.assertEqual(wild["CLUSTER"], "DISTRICT")
        self.assertIn("RADEMACHER_WEIGHTS_9999", wild["SMALL_SAMPLE_RULE"])
        self.assertIn("NO_VARIABLE_SELECTION", wild["PRESPECIFICATION"])

    def test_17_driscoll_kraay_is_not_authorized(self) -> None:
        row = next(item for item in self.inference if item["INFERENCE_ID"] == "DRISCOLL_KRAAY")
        self.assertEqual(row["STATUS"], "NOT_AUTHORIZED")
        self.assertIn("T_7_OR_8", row["SMALL_SAMPLE_RULE"])

    def test_18_two_way_few_period_clustering_is_not_authorized(self) -> None:
        row = next(item for item in self.inference if item["INFERENCE_ID"] == "TWO_WAY_DISTRICT_PERIOD_CLUSTER")
        self.assertEqual(row["STATUS"], "NOT_AUTHORIZED")
        self.assertIn("7_OR_8_PERIOD_CLUSTERS", row["SMALL_SAMPLE_RULE"])

    def test_19_spatial_hac_is_geography_only_robustness(self) -> None:
        rows = [row for row in self.inference if row["INFERENCE_ID"].startswith("SPATIAL_HAC_")]
        self.assertEqual([row["INFERENCE_ID"] for row in rows], ["SPATIAL_HAC_50KM", "SPATIAL_HAC_100KM", "SPATIAL_HAC_150KM"])
        self.assertTrue(all(row["ROLE"] == "ROBUSTNESS_ONLY" for row in rows))
        spatial = self.config["spatial_diagnostics"]
        self.assertEqual(spatial["prespecified_bandwidths_km"], [50, 100, 150])
        self.assertEqual(spatial["distance_crs"], "EPSG:32717")
        self.assertIn("NO_RESIDUAL_OR_OUTCOME_INPUT", spatial["selection_rule"])

    def test_20_extreme_years_retained_and_all_periods_checked(self) -> None:
        policy = self.config["extreme_year_policy"]
        self.assertTrue(policy["retain_2017"])
        self.assertTrue(policy["retain_2023"])
        self.assertEqual(policy["trimming"], "PROHIBITED")
        self.assertEqual(policy["winsorization"], "PROHIBITED")
        self.assertEqual(policy["influence_exercise"], "LEAVE_ONE_PERIOD_OUT_ALL_PERIODS")
        self.assertEqual(policy["mandatory_named_reporting"], ["LEAVE_2017_OUT", "LEAVE_2023_OUT"])

    def test_21_b3_is_mapped_without_weakening_fixed_effects(self) -> None:
        b3 = self.config["b3_econometric_sensitivity"]
        self.assertIn("RICE_ESTIMABLE_WITH_SEVERE_SUPPORT_LIMITATION", b3["overall_role"])
        self.assertEqual(b3["mad"], "B3_ECONOMETRIC_SENSITIVITY_NOT_ESTIMABLE_UNDER_PRIMARY_DESIGN")
        self.assertTrue(b3["same_outcome_scale_family_form_and_fe"])
        self.assertFalse(b3["may_weaken_primary_design"])

    def test_22_no_significance_based_model_revision(self) -> None:
        multiplicity = self.config["multiplicity"]
        self.assertTrue(multiplicity["all_prespecified_coefficients_reported"])
        self.assertEqual(multiplicity["variable_removal_by_p_value"], "PROHIBITED")
        self.assertEqual(multiplicity["star_count_conclusions"], "PROHIBITED")
        self.assertEqual(self.config["firewalls"]["significance_selection"], "PROHIBITED")

    def test_23_multiplicity_rule_is_prespecified(self) -> None:
        multiplicity = self.config["multiplicity"]
        self.assertEqual(
            multiplicity["adjustment"], "HOLM_STEP_DOWN_WITHIN_CROP_PRIMARY_CLIMATE_COEFFICIENTS"
        )
        self.assertTrue(multiplicity["unadjusted_results_also_reported"])
        self.assertEqual(multiplicity["coefficient_family"], "WITHIN_CROP_PRIMARY_CLIMATE_COEFFICIENTS")
        self.assertIn("ONE_PRESPECIFIED", multiplicity["omnibus_test"])

    def test_24_cross_crop_comparability_firewall(self) -> None:
        comparison = self.config["cross_crop_comparability"]
        self.assertEqual(comparison["channel"], "STANDARDIZED_ANOMALY_SECONDARY_MODELS")
        self.assertEqual(comparison["raw_physical_coefficient_magnitude_comparison"], "NOT_AUTHORIZED")
        self.assertEqual(comparison["shared_coefficients"], "NOT_AUTHORIZED")

    def test_25_future_scenario_period_fe_firewall(self) -> None:
        covenant = self.config["future_scenario_covenant"]
        self.assertFalse(covenant["scenarios_built_during_ed1"])
        self.assertEqual(covenant["future_period_fe"], "MUST_NOT_BE_INVENTED_OR_PROPAGATED")
        self.assertEqual(len(covenant["components_to_separate"]), 5)
        self.assertEqual(covenant["authorization"], "REQUIRES_LATER_SCENARIO_GATE")

    def test_26_robustness_hierarchy_is_exact(self) -> None:
        expected = [
            "PRIMARY",
            "R1_LEVEL_CLIMATE_FAMILY",
            "R2_STANDARDIZED_ANOMALY_COMPARABILITY",
            "R3_RESTRICTED_WILD_CLUSTER_BOOTSTRAP",
            "R4_SPATIAL_HAC",
            "R5_LEAVE_ONE_PERIOD_OUT_ALL_PERIODS",
            "R6_B3_STRICT_EXPOSURE",
        ]
        self.assertEqual([row["TIER"] for row in self.robustness], expected)
        self.assertEqual([int(row["ORDER"]) for row in self.robustness], list(range(7)))

    def test_27_x_geometry_inventory_is_complete(self) -> None:
        self.assertEqual(len(self.geometry), 29)
        self.assertEqual({row["CLIMATE_FAMILY"] for row in self.geometry}, set(ed1.FAMILIES))
        self.assertTrue(all(int(row["MISSING_X_CELLS"]) == 0 for row in self.geometry))

    def test_28_all_primary_x_matrices_pass(self) -> None:
        primary_candidates = {"PRIMARY_SINGLE_WINDOW", "P1_JOINT_T_AND_T_MINUS_1_LINEAR"}
        primary = [
            row
            for row in self.geometry
            if row["CLIMATE_FAMILY"] == "PHYSICAL_ANOMALY" and row["CANDIDATE"] in primary_candidates
        ]
        self.assertEqual(len(primary), 5)
        for row in primary:
            self.assertEqual(int(row["WITHIN_RANK"]), int(row["REGRESSORS"]))
            self.assertGreater(int(row["IMPLIED_RESIDUAL_DF"]), 0)
            self.assertLess(float(row["CONDITION_NUMBER"]), 30.0)
            self.assertLess(float(row["MAX_VIF"]), 10.0)
            self.assertEqual(row["PRIMARY_INFERENCE_COMPUTATION_FEASIBLE"], "TRUE")
            self.assertEqual(row["GEOMETRY_VERDICT"], "PASS")

    def test_29_joint_lemon_and_banana_geometry_is_full_rank(self) -> None:
        rows = [row for row in self.geometry if row["CANDIDATE"] == "P1_JOINT_T_AND_T_MINUS_1_LINEAR"]
        self.assertEqual(len(rows), 6)
        self.assertTrue(all(int(row["WITHIN_RANK"]) == 6 for row in rows))
        self.assertTrue(all(float(row["CONDITION_NUMBER"]) < 3.0 for row in rows))

    def test_30_b3_geometry_has_crop_specific_verdicts(self) -> None:
        rows = {row["CROP_CODE"]: row for row in self.geometry if row["CANDIDATE"] == "B3_STRICT_SENSITIVITY"}
        self.assertEqual(rows["14010020000"]["GEOMETRY_VERDICT"], "PASS_WITH_SEVERE_SUPPORT_LIMITATION")
        self.assertEqual(rows["14010070000"]["GEOMETRY_VERDICT"], "BLOCKED_X_RANK_AFTER_REQUIRED_FE")
        self.assertEqual(int(rows["14010070000"]["WITHIN_RANK"]), 1)
        self.assertEqual(int(rows["14010070000"]["IMPLIED_RESIDUAL_DF"]), 0)

    def test_31_method_anchors_are_verified_and_exact(self) -> None:
        anchors = self.config["method_literature_anchors"]
        self.assertEqual(
            {row["doi"] for row in anchors},
            {
                "10.1016/j.jeconom.2022.04.001",
                "10.1080/07350015.2016.1247004",
                "10.1162/003465398557825",
                "10.1016/S0304-4076(98)00084-0",
            },
        )
        self.assertTrue(all(row["verification"] == "VERIFIED_PUBLISHER_METADATA_AND_ABSTRACT" for row in anchors))
        self.assertTrue(all(row["verified_url"].startswith("https://doi.org/") for row in anchors))

    def test_32_two_rebuilds_are_byte_identical(self) -> None:
        self.assertEqual(self.hashes_one, self.hashes_two)
        self.assertEqual(self.bytes_one, self.bytes_two)
        for relative in ed1.OUTPUT_RELS:
            self.assertEqual(self.bytes_one[relative], (ROOT / relative).read_bytes(), relative.as_posix())

    def test_33_candidate_artifacts_are_utf8_lf_with_one_final_lf(self) -> None:
        for relative in ed1.OUTPUT_RELS:
            data = (ROOT / relative).read_bytes()
            self.assertNotIn(b"\xef\xbb\xbf", data[:3], relative.as_posix())
            self.assertNotIn(b"\r", data, relative.as_posix())
            self.assertTrue(data.endswith(b"\n"), relative.as_posix())
            self.assertFalse(data.endswith(b"\n\n"), relative.as_posix())
            data.decode("utf-8")

    def test_34_report_has_exact_thirty_director_sections(self) -> None:
        headings = [line for line in self.report.splitlines() if line.startswith("## ")]
        self.assertEqual(len(headings), 30)
        self.assertEqual(headings[0], "## 1. ED1 verdict")
        self.assertEqual(headings[-1], "## 30. Exact next action")

    def test_35_machine_summary_and_final_verdict_are_exact(self) -> None:
        self.assertIn("OUTCOME_VALUES_READ =\nFALSE", self.report)
        self.assertIn("REAL_REGRESSIONS = 0", self.report)
        self.assertIn("UNRESOLVED_FAILURES = 0", self.report)
        self.assertIn(f"FINAL_VERDICT = {ed1.FINAL_VERDICT}", self.report)
        self.assertIn("ED1H_FREEZE_AUTHORIZED =\nNO", self.report)
        self.assertEqual(self.config["final_verdict"], ed1.FINAL_VERDICT)
        self.assertFalse(self.config["ed1_freeze_authorized"])

    def test_36_only_authorized_candidate_artifacts_exist(self) -> None:
        expected = {relative.as_posix() for relative in ed1.OUTPUT_RELS}
        expected.update(
            {
                "scripts/econometric_design_master_v1.py",
                "tests/test_econometric_design_master_v1.py",
            }
        )
        actual = set(
            subprocess.run(
                ["git", "ls-files", "--others", "--exclude-standard"],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            ).stdout.splitlines()
        )
        self.assertEqual(actual, expected)

    def test_37_no_coefficient_or_result_table_is_created(self) -> None:
        names = {relative.name for relative in ed1.OUTPUT_RELS}
        self.assertFalse(any("COEFFICIENT" in name or "RESULT" in name for name in names))
        self.assertEqual(self.config["firewalls"]["coefficient_estimation"], "PROHIBITED_NOT_EXECUTED")
        self.assertEqual(self.config["firewalls"]["future_scenarios"], "PROHIBITED_NOT_BUILT")

    def test_38_freeze_is_not_authorized(self) -> None:
        self.assertFalse(self.config["freeze_authorized"])
        self.assertFalse(self.config["ed1_freeze_authorized"])
        self.assertEqual(
            self.config["next_action"], "RETURN_TO_SCIENTIFIC_DIRECTOR_FOR_ED1_FREEZE_DECISION_IF_PASS"
        )

    def test_39_concrete_inference_engine_is_pinned(self) -> None:
        feasibility = self.config["inference_engine_feasibility"]
        self.assertEqual(feasibility["status"], "PASS")
        self.assertEqual(feasibility["engine"]["language"], "Python")
        self.assertEqual(feasibility["engine"]["runtime_versions"], ed1.ENGINE_VERSIONS)
        self.assertEqual(feasibility["engine"]["two_way_fe_api"], "fit_two_way_fe_cr2 + absorb_fixed_effects")
        self.assertIn("PROJECT_LOCAL", feasibility["engine"]["cr2_api"])
        self.assertIn("CLUBSANDWICH_HTZ_FORMULA", feasibility["engine"]["aht_api"])

    def test_40_synthetic_response_uses_structural_keys_only(self) -> None:
        transient = ed1.read_transient_primary()
        frame, columns = ed1.primary_design_frame(transient, ed1.read_perennial_primary(), "14010020000")
        original = ed1.synthetic_response(frame, "CAMPAIGN_ID")
        modified = frame.copy()
        modified[columns] = modified[columns] + 12345.0
        self.assertTrue((original == ed1.synthetic_response(modified, "CAMPAIGN_ID")).all())
        self.assertFalse(self.config["inference_engine_feasibility"]["real_outcome_values_read"])
        self.assertEqual(
            self.config["inference_engine_feasibility"]["synthetic_response_source"],
            "SHA256_OF_STRUCTURAL_DISTRICT_AND_PERIOD_KEYS_ONLY",
        )

    def test_41_effective_cluster_counts_are_exact(self) -> None:
        diagnostics = self.config["inference_engine_feasibility"]["crop_diagnostics"]
        expected = {
            "14010020000": (44, 43, 1, 1),
            "14010070000": (54, 52, 2, 2),
            "13010210000": (36, 35, 1, 1),
            "13010170102": (44, 43, 1, 1),
            "15010040000": (54, 50, 4, 4),
        }
        actual = {
            code: (
                row["nominal_clusters"],
                row["effective_contributing_clusters"],
                row["zero_effective_clusters"],
                row["singleton_clusters"],
            )
            for code, row in diagnostics.items()
        }
        self.assertEqual(actual, expected)
        for row in diagnostics.values():
            leverage = row["cluster_leverage"]
            self.assertLessEqual(leverage["minimum"], leverage["median"])
            self.assertLessEqual(leverage["median"], leverage["maximum"])

    def test_42_cr2_adjustments_have_no_extra_singularities(self) -> None:
        feasibility = self.config["inference_engine_feasibility"]
        self.assertEqual(feasibility["total_cr2_adjustment_singularities"], 0)
        for row in feasibility["crop_diagnostics"].values():
            self.assertEqual(row["cr2_adjustment_singularities"], 0)
            self.assertEqual(row["cr2_adjustment_status"], "PASS_NO_EXTRA_SINGULARITY_BEYOND_CLUSTER_FE_NULLSPACE")

    def test_43_satterthwaite_and_aht_are_finite_for_all_crops(self) -> None:
        diagnostics = self.config["inference_engine_feasibility"]["crop_diagnostics"]
        for row in diagnostics.values():
            self.assertGreater(row["coefficient_specific_satterthwaite_df_minimum"], 0)
            self.assertGreaterEqual(
                row["coefficient_specific_satterthwaite_df_maximum"],
                row["coefficient_specific_satterthwaite_df_minimum"],
            )
            self.assertGreater(row["aht_denominator_df"], 0)
            self.assertEqual(row["nonfinite_quantities"], 0)

    def test_44_cr2_reference_calculation_is_independent_and_equal(self) -> None:
        validation = self.config["inference_engine_feasibility"]["independent_reference_validation"]
        self.assertEqual(validation["status"], "PASS")
        self.assertEqual(validation["reference_path"], "INDEPENDENT_FULL_DESIGN_SVD_CALCULATION")
        self.assertEqual(validation["production_synthetic_beta"], validation["reference_synthetic_beta"])
        self.assertTrue(all(value <= validation["tolerance"] for value in validation["differences"].values()))

    def test_45_restricted_wild_bootstrap_is_deterministic_at_9999(self) -> None:
        validation = self.config["inference_engine_feasibility"]["wild_cluster_bootstrap_validation"]
        self.assertEqual(validation["status"], "PASS")
        self.assertTrue(validation["deterministic"])
        self.assertEqual(validation["smoke_test_replications"], 9999)
        self.assertEqual(validation["run_one"]["seed"], 20260903)
        self.assertEqual(validation["run_one"]["invalid_replications"], 0)
        self.assertEqual(
            validation["run_one"]["bootstrap_t_sha256"], validation["run_two_sha256"]
        )
        self.assertEqual(validation["joint_run_one"]["restriction_kind"], "ALL_CLIMATE_COEFFICIENTS")
        self.assertEqual(validation["joint_run_one"]["invalid_replications"], 0)
        self.assertEqual(
            validation["joint_run_one"]["bootstrap_t_sha256"], validation["joint_run_two_sha256"]
        )

    def test_46_conley_synthetic_covariances_are_finite(self) -> None:
        feasibility = self.config["inference_engine_feasibility"]
        self.assertEqual(feasibility["conley_engine_validation"], "PASS_ALL_FIVE_CROPS_ALL_THREE_BANDWIDTHS")
        for row in feasibility["crop_diagnostics"].values():
            self.assertEqual(set(row["conley_covariance"]), {"50", "100", "150"})
            self.assertTrue(all(item["finite"] for item in row["conley_covariance"].values()))

    def test_47_level_anomaly_fe_equivalence_is_crop_specific(self) -> None:
        equivalence = self.config["level_physical_anomaly_fe_equivalence"]
        for code in ("14010020000", "14010070000"):
            self.assertFalse(equivalence[code]["elementwise_equal_within_tolerance"])
            self.assertEqual(equivalence[code]["level_role"], "DISTINCT_CLIMATE_FAMILY_ROBUSTNESS")
        for code in ("13010210000", "13010170102", "15010040000"):
            self.assertTrue(equivalence[code]["elementwise_equal_within_tolerance"])
            self.assertTrue(equivalence[code]["column_space_equivalent"])
            self.assertTrue(equivalence[code]["proportional_within_tolerance"])
            self.assertEqual(
                equivalence[code]["level_role"], "FE_EQUIVALENT_DIAGNOSTIC_NOT_DISTINCT_ROBUSTNESS"
            )

    def test_48_standardized_x_does_not_authorize_magnitude_ranking(self) -> None:
        comparison = self.config["cross_crop_comparability"]
        self.assertEqual(
            comparison["standardized_x_interpretation"],
            "ONE_LOCAL_CLIMATE_SD_CHANGE_IN_NATIVE_CROP_YIELD_UNITS",
        )
        self.assertEqual(comparison["coefficient_magnitude_ranking"], "NOT_AUTHORIZED")
        self.assertIn("OUTCOME_REMAINS_NATIVE_YIELD", comparison["fully_standardized_effect_size"])

    def test_49_no_global_five_crop_fwer_claim(self) -> None:
        multiplicity = self.config["multiplicity"]
        self.assertEqual(multiplicity["global_five_crop_familywise_error_control"], "NOT_CLAIMED")
        self.assertEqual(multiplicity["cross_crop_significance_ranking"], "PROHIBITED")
        self.assertEqual(multiplicity["future_global_family"], "REQUIRES_SEPARATELY_PRESPECIFIED_GATE")

    def test_50_previous_full_suite_error_is_exactly_adjudicated(self) -> None:
        error = self.config["previous_full_suite_error"]
        self.assertEqual(error["test_path"], "tests/test_primary_transient_exposure_v1.py")
        self.assertEqual(
            error["test_method"],
            "PrimaryTransientExposureV1Tests.test_28_two_independent_builds_are_byte_identical",
        )
        self.assertEqual(error["exception_class"], "RuntimeError")
        self.assertEqual(error["classification"], "EXPECTED_HISTORICAL_LIFECYCLE_STATE")
        self.assertIn("S1 identity mismatch", error["traceback"])
        self.assertEqual(error["historical_reproduction"]["status"], "PASS")
        self.assertEqual(error["historical_reproduction"]["test_result"], "RAN_1_OK")
        self.assertTrue(error["historical_reproduction"]["temporary_worktree_removed"])

    def test_51_all_previous_nonpasses_are_machine_adjudicated(self) -> None:
        suite = self.config["previous_full_suite"]
        self.assertEqual((suite["tests_run"], suite["tests_passed"], suite["failures"], suite["errors"]), (693, 642, 50, 1))
        self.assertEqual(len(suite["nonpass_adjudication"]), 51)
        self.assertEqual(
            suite["category_counts"],
            {
                "ENVIRONMENTAL_BLOCKER": 0,
                "EXPECTED_ACTIVE_PHASE_FIREWALL": 6,
                "EXPECTED_HISTORICAL_LIFECYCLE_STATE": 45,
                "REAL_REGRESSION": 0,
                "UNRESOLVED": 0,
            },
        )
        self.assertEqual(sum(row["result"] == "ERROR" for row in suite["nonpass_adjudication"]), 1)
        self.assertEqual(suite["real_regressions"], 0)
        self.assertEqual(suite["unresolved"], 0)


if __name__ == "__main__":
    unittest.main()
