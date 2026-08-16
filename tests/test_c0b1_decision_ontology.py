import csv
import hashlib
import json
import unittest
from pathlib import Path

from scripts import c0b1_decision_ontology_preflight as c0b1


ROOT = Path(__file__).resolve().parents[1]


def read_csv(path: Path):
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class C0B1DecisionOntologyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ontology = json.loads(c0b1.ONTOLOGY_PATH.read_text(encoding="utf-8"))
        cls.architectures = read_csv(c0b1.ARCHITECTURE_PATH)
        cls.report = c0b1.REPORT_PATH.read_text(encoding="utf-8")

    def test_01_branch_ancestry_checkpoint(self):
        gate = c0b1.checkpoint_parentage()
        self.assertEqual(gate["status"], "PASS")

    def test_02_c0b0_checkpoint_files_are_immutable(self):
        gate = c0b1.c0b0_immutability()
        self.assertEqual(gate["status"], "PASS")

    def test_03_exact_five_new_c0b1_files(self):
        scope = c0b1.persistent_scope()
        self.assertEqual(scope["status"], "PASS")
        self.assertEqual(set(scope["observed"]), c0b1.AUTHORIZED_SCOPE)

    def test_04_architecture_schema_and_all_six_options(self):
        self.assertEqual(list(self.architectures[0].keys()), c0b1.ARCHITECTURE_SCHEMA)
        self.assertEqual({row["ARCHITECTURE_ID"] for row in self.architectures}, c0b1.EXPECTED_ARCHITECTURES)

    def test_05_exactly_one_primary_and_at_most_two_fallbacks(self):
        verdicts = [row["VERDICT"] for row in self.architectures]
        self.assertEqual(verdicts.count("PRIMARY_CANDIDATE"), 1)
        self.assertLessEqual(verdicts.count("FALLBACK_CANDIDATE"), 2)

    def test_06_arch_a_cannot_be_primary(self):
        arch_a = next(row for row in self.architectures if row["ARCHITECTURE_ID"] == "ARCH_A")
        self.assertNotEqual(arch_a["VERDICT"], "PRIMARY_CANDIDATE")
        self.assertEqual(arch_a["VERDICT"], "REJECT")

    def test_07_arch_e_primary_and_arch_f_fallback(self):
        arch_e = next(row for row in self.architectures if row["ARCHITECTURE_ID"] == "ARCH_E")
        arch_f = next(row for row in self.architectures if row["ARCHITECTURE_ID"] == "ARCH_F")
        self.assertEqual(arch_e["VERDICT"], "PRIMARY_CANDIDATE")
        self.assertEqual(arch_f["VERDICT"], "FALLBACK_CANDIDATE")
        self.assertEqual(self.ontology["primary_architecture"], "ARCH_E_MIXED_STOCK_FLOW_PLUS_MARGINAL_ADJUSTMENT")
        self.assertEqual(self.ontology["fallback_architectures"], ["ARCH_F_TRANSIENT_ENDOGENOUS_PERENNIAL_EXOGENOUS"])

    def test_08_land_cap_is_not_direct_campaign_hectare_cap(self):
        land = self.ontology["land_ontology"]
        self.assertEqual(land["AREA_HA_future_role"], "HARD_CAP_COMPATIBLE_AFTER_OCCUPANCY_MAPPING")
        self.assertFalse(land["direct_campaign_hectare_cap_authorized"])
        self.assertIn("Direct `SUM campaign hectares <= AREA_HA` is not authorized.", self.report)

    def test_09_sequential_cropping_not_assumed_absent(self):
        self.assertEqual(
            self.ontology["sequential_cropping_assumption"],
            "NOT_ASSUMED_ABSENT_AGGREGATE_DATA_CANNOT_PROVE_PARCEL_SEQUENCE",
        )
        self.assertIn("Sequential or multiple cropping cannot be assumed absent.", self.report)
        self.assertIn("cannot prove parcel-level double cropping", self.report)

    def test_10_stock_flow_distinction_is_explicit(self):
        crops = self.ontology["target_crops"]
        self.assertEqual(crops["14010020000"]["decision_variable_role"], "CAMPAIGN_AREA_FLOW")
        self.assertEqual(crops["14010070000"]["decision_variable_role"], "CAMPAIGN_AREA_FLOW")
        self.assertIn("INSTALLED_AREA_STOCK", crops["13010210000"]["decision_variable_role"])
        self.assertIn("INSTALLED_AREA_STOCK", crops["13010170102"]["decision_variable_role"])
        self.assertIn("INSTALLED_AREA_STOCK", crops["15010040000"]["decision_variable_role"])
        self.assertTrue(self.ontology["stock_flow_distinction"]["same_unit_label_not_same_decision_object"])

    def test_11_no_numeric_optimization_bounds_are_authorized(self):
        gate = c0b1.numeric_parameter_gate()
        self.assertEqual(gate["status"], "PASS")
        self.assertEqual(self.ontology["numeric_parameter_policy"], "NO_NUMERIC_OPTIMIZATION_PARAMETERS_AUTHORIZED_IN_C0B1")
        self.assertIn("No numeric optimization parameters are authorized in C0B1.", self.report)

    def test_11a_json_master_contains_prompt_required_keys(self):
        required = {
            "ontology_version",
            "planning_interpretation",
            "planning_horizon_interpretation",
            "primary_architecture",
            "fallback_architectures",
            "rejected_architectures",
            "target_crops",
            "transient_crops",
            "perennial_or_semipermanent_crops",
            "primary_transient_resolution",
            "fallback_transient_resolution",
            "primary_transient_resolution_status",
            "t3_numeric_shares_defined",
            "t3_share_parameterization_status",
            "t3_share_provenance_rule_status",
            "t3_forbidden_share_selection_inputs",
            "planting_timing_adaptation_status",
            "primary_perennial_resolution",
            "perennial_stock_state_definitions",
            "perennial_installed_stock_status",
            "perennial_productive_stock_distinction_status",
            "new_establishment_immediate_productivity_assumption",
            "immediate_productivity_assumption",
            "establishment_to_productivity_lag_status",
            "perennial_removal_replacement_timing_status",
            "numeric_maturity_parameters_created",
            "productive_age_distribution_status",
            "yield_age_relationship_status",
            "arch_e_to_arch_f_fallback_if_c0b3_fails",
            "c0b3_perennial_productivity_adjudication",
            "endogeneity_set_primary",
            "endogeneity_set_fallback",
            "primary_architecture_operational_authorization",
            "physical_land_interpretation",
            "AREA_HA_future_role",
            "climate_response_window_role",
            "climate_response_window_is_physical_occupancy_window",
            "physical_land_occupancy_mapping_status",
            "physical_land_occupancy_evidence_status",
            "occupancy_mapping_may_reuse_climate_windows_without_independent_support",
            "occupancy_numeric_parameters_created",
            "land_hard_constraint_currently_authorized",
            "sequential_cropping_assumption",
            "decision_spatial_scale",
            "constraint_multiscale_allowed",
            "parcel_level_interpretation",
            "governance_interpretation",
            "required_future_evidence",
            "forbidden_interpretations",
            "known_lifecycle_failure_ledger",
            "raw_full_suite_status",
            "adjudicated_validation_status",
            "phase_aware_validator_future_need",
        }
        self.assertLessEqual(required, set(self.ontology))

    def test_12_no_water_coefficient_or_district_hard_water_cap(self):
        water = self.ontology["multiscale_water_compatibility"]
        self.assertFalse(water["district_hard_water_cap_authorized"])
        self.assertFalse(water["water_coefficient_authorized"])
        self.assertIn("No district hard water constraint", self.report)

    def test_13_no_optimizer_cvar_objective_or_scenario_artifacts(self):
        self.assertEqual(c0b1.no_optimization_artifacts()["status"], "PASS")
        self.assertIn("no optimizer, no objective function, no CVaR, no scenario set", self.report)

    def test_14_parcel_level_interpretation_forbidden(self):
        self.assertTrue(self.ontology["parcel_level_interpretation"].startswith("FORBIDDEN"))
        self.assertIn("Parcel-level interpretation is forbidden.", self.report)

    def test_15_governance_is_normative_not_command(self):
        self.assertIn("NORMATIVE_REGIONAL_DECISION_SUPPORT", self.ontology["governance_interpretation"])
        self.assertIn("does not claim command over farmer-level allocations", self.report)

    def test_16_all_five_endogeneity_not_silently_assumed(self):
        set1 = self.ontology["endogeneity_sets"]["SET_1_ALL_FIVE_ENDOGENOUS"]
        self.assertEqual(set1["verdict"], "CONDITIONAL_ON_C0B3")
        self.assertNotEqual(self.ontology["primary_endogeneity_set"], "SET_1_ALL_FIVE_ENDOGENOUS")

    def test_17_endogeneity_primary_and_fallback_sets(self):
        self.assertEqual(
            self.ontology["primary_endogeneity_set"],
            "SET_2_RICE_MAIZE_FULLY_ENDOGENOUS_PERENNIALS_MARGINALLY_ENDOGENOUS",
        )
        self.assertEqual(
            self.ontology["fallback_endogeneity_set"],
            "SET_3_RICE_MAIZE_ENDOGENOUS_PERENNIAL_STOCKS_EXOGENOUS",
        )

    def test_18_frozen_phenology_and_climate_paths_unmodified(self):
        gate = c0b1.frozen_paths_gate()
        self.assertEqual(gate["status"], "PASS")
        self.assertEqual(self.ontology["phenology_compatibility"]["status"], "COMPATIBLE_WITH_FROZEN_STAGE_B_NO_REOPEN")

    def test_19_transient_and_perennial_resolution_choices(self):
        self.assertEqual(
            self.ontology["primary_transient_decision_resolution"],
            c0b1.PRIMARY_T3_RESOLUTION,
        )
        self.assertEqual(self.ontology["fallback_transient_decision_resolution"], "T2_MONTHLY_OR_COHORT_PLANTED_AREA_FLOWS")
        self.assertEqual(
            self.ontology["primary_perennial_resolution"],
            "P2_INSTALLED_STOCK_PLUS_ANNUAL_ESTABLISHMENT_REMOVAL_FLOWS_CONDITIONAL_ON_C0B3",
        )

    def test_20_report_has_required_25_sections(self):
        self.assertEqual(c0b1.report_gate()["status"], "PASS")

    def test_21_c0b1_preflight_passes(self):
        gates = c0b1.run_all_gates()
        failures = {name: gate for name, gate in gates.items() if gate["status"] != "PASS"}
        self.assertEqual(failures, {})

    def test_22_t3_has_conditional_primary_status(self):
        self.assertEqual(self.ontology["primary_transient_resolution"], c0b1.PRIMARY_T3_RESOLUTION)
        self.assertEqual(self.ontology["primary_transient_resolution_status"], "CONDITIONAL_PRIMARY")

    def test_23_no_numeric_share_vector_exists(self):
        gate = c0b1.t3_provenance_gate()
        self.assertEqual(gate["status"], "PASS")
        self.assertFalse(self.ontology["t3_numeric_shares_defined"])
        self.assertEqual(gate["numeric_share_fields"], [])

    def test_24_t3_parameterization_not_yet_defined(self):
        self.assertEqual(self.ontology["t3_share_parameterization_status"], "NOT_YET_DEFINED")
        self.assertNotIn(c0b1.LEGACY_T3_RESOLUTION, json.dumps(self.ontology, sort_keys=True))

    def test_25_future_share_provenance_must_be_prespecified(self):
        self.assertEqual(
            self.ontology["t3_share_provenance_rule_status"],
            "REQUIRED_BEFORE_NUMERICAL_IMPLEMENTATION",
        )
        self.assertIn("PRESPECIFIED_BEFORE_DOWNSTREAM_OUTCOME_ANALYSIS", self.ontology["t3_future_share_rule_requirements"])
        self.assertIn(
            "DOCUMENTED_PROVENANCE_BEFORE_NUMERICAL_IMPLEMENTATION",
            self.ontology["t3_future_share_rule_requirements"],
        )

    def test_26_outcome_variables_cannot_select_shares(self):
        self.assertIn("OUTCOME_VARIABLES", self.ontology["t3_forbidden_share_selection_inputs"])
        self.assertIn("YIELD_IMPROVEMENT", self.ontology["t3_forbidden_share_selection_inputs"])

    def test_27_climate_response_estimates_cannot_select_shares(self):
        forbidden = self.ontology["t3_forbidden_share_selection_inputs"]
        self.assertIn("CLIMATE_RESPONSE_ESTIMATES", forbidden)
        self.assertIn("WEATHER_YIELD_RESPONSE_ESTIMATES", forbidden)

    def test_28_enso_scenario_results_cannot_select_shares(self):
        self.assertIn("ENSO_SCENARIO_OUTCOMES", self.ontology["t3_forbidden_share_selection_inputs"])

    def test_29_optimization_results_cannot_select_shares(self):
        forbidden = self.ontology["t3_forbidden_share_selection_inputs"]
        self.assertIn("ECONOMIC_OPTIMIZATION_RESULTS", forbidden)
        self.assertIn("PROFIT_IMPROVEMENT", forbidden)
        self.assertIn("CVAR_IMPROVEMENT", forbidden)
        self.assertIn("GVP_IMPROVEMENT", forbidden)

    def test_30_arch_e_primary_but_operationally_blocked(self):
        self.assertEqual(self.ontology["primary_architecture"], "ARCH_E_MIXED_STOCK_FLOW_PLUS_MARGINAL_ADJUSTMENT")
        self.assertEqual(
            self.ontology["primary_architecture_operational_authorization"],
            "BLOCKED_PENDING_C0B2_C0B3_AND_PARAMETER_GATES",
        )

    def test_31_arch_f_remains_explicit_fallback(self):
        self.assertEqual(self.ontology["fallback_architectures"], ["ARCH_F_TRANSIENT_ENDOGENOUS_PERENNIAL_EXOGENOUS"])
        arch_f = next(row for row in self.architectures if row["ARCHITECTURE_ID"] == "ARCH_F")
        self.assertEqual(arch_f["VERDICT"], "FALLBACK_CANDIDATE")

    def test_32_p2_remains_conditional_on_c0b3(self):
        self.assertEqual(self.ontology["p2_status"], "CONDITIONAL_ON_C0B3")
        self.assertIn("CONDITIONAL_ON_C0B3", self.ontology["primary_perennial_resolution"])

    def test_33_p3_remains_fallback(self):
        self.assertEqual(self.ontology["p3_fallback_status"], "EXPLICIT_FALLBACK_IF_C0B3_FAILS")
        self.assertEqual(self.ontology["perennial_resolutions"]["P3_FIXED_STOCK_NEAR_TERM_HORIZON"], "FALLBACK_CANDIDATE")

    def test_34_area_ha_hard_constraint_currently_unauthorized(self):
        self.assertFalse(self.ontology["land_hard_constraint_currently_authorized"])
        self.assertFalse(self.ontology["land_ontology"]["direct_campaign_hectare_cap_authorized"])

    def test_35_exact_three_c0b0_lifecycle_failures_recorded(self):
        ledger = self.ontology["known_lifecycle_failure_ledger"]
        tests = [item["test"] for item in ledger["c0b0_expected_post_checkpoint_failures"]]
        self.assertEqual(tests, c0b1.EXPECTED_C0B0_POST_CHECKPOINT_FAILURES)
        self.assertTrue(
            all(
                item["classification"] == "EXPECTED_POST_CHECKPOINT_STATE_FAILURE"
                for item in ledger["c0b0_expected_post_checkpoint_failures"]
            )
        )

    def test_36_lifecycle_tolerance_conditioned_on_checkpoint_ancestor(self):
        ledger = self.ontology["known_lifecycle_failure_ledger"]
        self.assertEqual(ledger["checkpoint_descendant"], c0b1.EXPECTED_HEAD)
        self.assertIn(
            "CHECKPOINT_77526C9CB41B20062A5FA61A95167AF5859295F2_REMAINS_ANCESTOR",
            ledger["tolerance_conditions"],
        )

    def test_37_c0b0_checkpoint_files_remain_byte_identical(self):
        gate = c0b1.c0b0_immutability()
        self.assertEqual(gate["status"], "PASS")
        self.assertEqual(set(gate["failures"]), set())

    def test_38_unknown_ninth_full_suite_failure_not_allowed(self):
        ledger = self.ontology["known_lifecycle_failure_ledger"]
        self.assertEqual(ledger["total_known_state_failures"], 8)
        self.assertEqual(ledger["unknown_failure_count"], 0)
        self.assertIn("ANY_DIFFERENT_OR_NINTH_FAILURE_IS_UNEXPECTED_FAILURE", ledger["unknown_failure_policy"])

    def test_39_lifecycle_failure_ledger_gate_passes(self):
        self.assertEqual(c0b1.lifecycle_failure_ledger_gate()["status"], "PASS")

    def test_40_climate_response_window_is_not_physical_occupancy_window(self):
        self.assertEqual(self.ontology["climate_response_window_role"], "EMPIRICAL_CLIMATE_EXPOSURE_ONLY")
        self.assertFalse(self.ontology["climate_response_window_is_physical_occupancy_window"])

    def test_41_physical_occupancy_mapping_required_before_hard_cap(self):
        self.assertEqual(self.ontology["physical_land_occupancy_mapping_status"], "REQUIRED_BEFORE_LAND_HARD_CAP")
        self.assertEqual(self.ontology["physical_land_occupancy_evidence_status"], "NOT_YET_ADJUDICATED")

    def test_42_no_occupancy_duration_numeric_coefficient_exists(self):
        gate = c0b1.climate_occupancy_gate()
        self.assertEqual(gate["status"], "PASS")
        self.assertEqual(gate["numeric_occupancy"], [])
        self.assertFalse(self.ontology["occupancy_numeric_parameters_created"])

    def test_43_stage_b_climate_windows_cannot_substitute_for_occupancy_evidence(self):
        self.assertFalse(self.ontology["occupancy_mapping_may_reuse_climate_windows_without_independent_support"])
        self.assertIn("CLIMATE_RESPONSE_WINDOW != PHYSICAL_LAND_OCCUPANCY_WINDOW", self.report)
        self.assertIn("Frozen Stage-A and Stage-B climate exposure windows do not define physical occupancy duration.", self.report)

    def test_44_installed_perennial_stock_not_silently_productive_stock(self):
        definitions = self.ontology["perennial_stock_state_definitions"]
        self.assertIn("INSTALLED_PERENNIAL_STOCK", definitions)
        self.assertIn("PRODUCTIVE_OR_BEARING_PERENNIAL_STOCK", definitions)
        self.assertNotEqual(definitions["INSTALLED_PERENNIAL_STOCK"], definitions["PRODUCTIVE_OR_BEARING_PERENNIAL_STOCK"])

    def test_45_new_establishment_immediate_productivity_not_authorized(self):
        self.assertEqual(self.ontology["new_establishment_immediate_productivity_assumption"], "NOT_AUTHORIZED")
        self.assertEqual(self.ontology["immediate_productivity_assumption"], "NOT_AUTHORIZED_WITHOUT_C0B3_EVIDENCE")

    def test_46_no_numeric_maturity_lag_exists(self):
        gate = c0b1.perennial_stock_gate()
        self.assertEqual(gate["status"], "PASS")
        self.assertEqual(gate["numeric_maturity"], [])
        self.assertFalse(self.ontology["numeric_maturity_parameters_created"])

    def test_47_c0b3_must_adjudicate_productive_stock_distinction(self):
        self.assertEqual(self.ontology["perennial_productive_stock_distinction_status"], "REQUIRES_C0B3_ADJUDICATION")
        for crop in ("MANGO", "LEMON", "BANANA"):
            self.assertIn(
                "INSTALLED_VERSUS_PRODUCTIVE_OR_BEARING_STOCK_DISTINCTION",
                self.ontology["c0b3_perennial_productivity_adjudication"][crop],
            )

    def test_48_c0b3_must_adjudicate_establishment_to_productivity_timing(self):
        self.assertEqual(self.ontology["establishment_to_productivity_lag_status"], "UNRESOLVED_REQUIRES_C0B3")
        for crop in ("MANGO", "LEMON", "BANANA"):
            self.assertIn(
                "ESTABLISHMENT_TO_PRODUCTIVITY_LAG",
                self.ontology["c0b3_perennial_productivity_adjudication"][crop],
            )

    def test_49_arch_e_remains_primary_ontology(self):
        self.assertEqual(self.ontology["primary_architecture"], "ARCH_E_MIXED_STOCK_FLOW_PLUS_MARGINAL_ADJUSTMENT")
        arch_e = next(row for row in self.architectures if row["ARCHITECTURE_ID"] == "ARCH_E")
        self.assertEqual(arch_e["VERDICT"], "PRIMARY_CANDIDATE")

    def test_50_arch_e_remains_operationally_blocked(self):
        self.assertEqual(
            self.ontology["primary_architecture_operational_authorization"],
            "BLOCKED_PENDING_C0B2_C0B3_AND_PARAMETER_GATES",
        )

    def test_51_arch_f_remains_fallback(self):
        self.assertEqual(self.ontology["fallback_architectures"], ["ARCH_F_TRANSIENT_ENDOGENOUS_PERENNIAL_EXOGENOUS"])
        arch_f = next(row for row in self.architectures if row["ARCHITECTURE_ID"] == "ARCH_F")
        self.assertEqual(arch_f["VERDICT"], "FALLBACK_CANDIDATE")

    def test_52_arch_e_to_arch_f_scope_reduction_allowed_if_c0b3_fails(self):
        self.assertEqual(self.ontology["arch_e_to_arch_f_fallback_if_c0b3_fails"], "AUTHORIZED_SCOPE_REDUCTION_PATH")
        self.assertEqual(
            self.ontology["fallback_endogeneity_set"],
            "SET_3_RICE_MAIZE_ENDOGENOUS_PERENNIAL_STOCKS_EXOGENOUS",
        )

    def test_53_architecture_comparison_csv_hash_unchanged(self):
        digest = hashlib.sha256(c0b1.ARCHITECTURE_PATH.read_bytes()).hexdigest()
        self.assertEqual(digest, c0b1.ARCHITECTURE_COMPARISON_SHA256)

    def test_54_c0b0_files_remain_byte_identical_after_c0b1d(self):
        self.assertEqual(c0b1.c0b0_immutability()["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
