"""Regression tests for Joint C0 outcome and decision integration."""

from __future__ import annotations

import ast
import csv
import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import c0_joint_integration_preflight as joint  # noqa: E402


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=ROOT, text=True, encoding="utf-8",
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    )
    return result.stdout.strip()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


class JointC0IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.evidence_columns, cls.evidence = read_csv(joint.EVIDENCE_PATH)
        cls.compatibility_columns, cls.compatibility = read_csv(joint.COMPATIBILITY_PATH)
        cls.authorization_columns, cls.authorization = read_csv(joint.AUTHORIZATION_PATH)
        cls.config = json.loads(joint.CONFIG_PATH.read_text(encoding="utf-8"))
        cls.report = joint.REPORT_PATH.read_text(encoding="utf-8")

    def test_01_exact_joint_branch_and_c0b6_head(self) -> None:
        self.assertEqual(git("branch", "--show-current"), joint.EXPECTED_BRANCH)
        self.assertEqual(git("rev-parse", "HEAD"), joint.C0B6_FREEZE)

    def test_02_c0b6_is_current_ancestor(self) -> None:
        result = subprocess.run(
            ["git", "merge-base", "--is-ancestor", joint.C0B6_FREEZE, "HEAD"], cwd=ROOT,
        )
        self.assertEqual(result.returncode, 0)

    def test_03_c0a_sibling_exists_and_is_not_merged(self) -> None:
        exists = subprocess.run(["git", "cat-file", "-e", f"{joint.C0A_FREEZE}^{{commit}}"], cwd=ROOT)
        merged = subprocess.run(["git", "merge-base", "--is-ancestor", joint.C0A_FREEZE, "HEAD"], cwd=ROOT)
        self.assertEqual(exists.returncode, 0)
        self.assertNotEqual(merged.returncode, 0)

    def test_04_c0a_exact_four_introduced_files(self) -> None:
        self.assertEqual(joint.c0a_introduced_files(), {path: "A" for path in joint.C0A_FILES})

    def test_05_c0a_object_hashes_are_exact(self) -> None:
        for path, expected in joint.C0A_FILES.items():
            payload = joint.git_bytes("show", f"{joint.C0A_FREEZE}:{path}")
            self.assertEqual(hashlib.sha256(payload).hexdigest(), expected, path)

    def test_06_c0a_files_are_not_copied_into_worktree(self) -> None:
        self.assertTrue(all(not (ROOT / path).exists() for path in joint.C0A_FILES))

    def test_07_c0b6_artifacts_are_byte_identical(self) -> None:
        for path, expected in joint.C0B6_FILES.items():
            self.assertEqual(sha256(ROOT / path), expected, path)

    def test_08_frozen_outcome_and_exposure_inputs_are_byte_identical(self) -> None:
        for path, expected in joint.FROZEN_UPSTREAM_HASHES.items():
            self.assertEqual(sha256(ROOT / path), expected, path)

    def test_09_exact_seven_file_joint_scope(self) -> None:
        tracked = set(filter(None, git("diff", "--name-only").splitlines()))
        staged = set(filter(None, git("diff", "--cached", "--name-only").splitlines()))
        untracked = {
            line.replace("\\", "/")
            for line in git("ls-files", "--others", "--exclude-standard").splitlines()
            if line
        }
        self.assertEqual(tracked, set())
        self.assertEqual(staged, set())
        self.assertEqual(untracked, joint.AUTHORIZED_SCOPE)

    def test_10_output_schemas_are_exact(self) -> None:
        self.assertEqual(self.evidence_columns, joint.EVIDENCE_COLUMNS)
        self.assertEqual(self.compatibility_columns, joint.COMPATIBILITY_COLUMNS)
        self.assertEqual(self.authorization_columns, joint.AUTHORIZATION_COLUMNS)

    def test_11_c0a_outcome_conclusions_are_recovered_from_objects(self) -> None:
        conclusions = joint.c0a_conclusions()
        self.assertEqual(conclusions["produccion"]["DECISION_VALUE"], "METRIC_TONNE")
        self.assertEqual(conclusions["yield"]["DECISION_VALUE"], "TM_PER_HA")
        self.assertEqual(conclusions["cosecha"]["DECISION_VALUE"], "ha")
        self.assertEqual(conclusions["siembra"]["DECISION_VALUE"], "ha")
        self.assertEqual(conclusions["precio"]["DECISION_VALUE"], "SOL_PER_KG")
        self.assertTrue(conclusions["report_gvp_not_built"])
        self.assertTrue(conclusions["report_causal_not_authorized"])

    def test_12_integrated_outcome_semantics_are_exact(self) -> None:
        semantics = self.config["outcome_semantics"]
        self.assertEqual(semantics["PRODUCCION"]["unit"], "METRIC_TONNE")
        self.assertEqual(semantics["YIELD_RAW"]["unit"], "TM_PER_HA")
        self.assertEqual(semantics["YIELD_RAW"]["denominator_semantics"], "HARVESTED_AREA_HA")
        self.assertEqual(semantics["PRECIO_CHACRA"]["unit"], "S_PER_KG")
        self.assertEqual(semantics["monetary_translation_status"], "DIMENSIONALLY_AUTHORIZED_NOT_BUILT")
        self.assertFalse(semantics["gvp_built"])

    def test_13_transient_outcome_contract_is_august_july_ratio(self) -> None:
        contract = self.config["transient_outcome_contract"]
        self.assertEqual(contract["variable"], "TRANSIENT_CAMPAIGN_YIELD_RAW")
        self.assertEqual(
            contract["formula"],
            "SUM(PRODUCCION within Aug-Jul campaign) / SUM(COSECHA within Aug-Jul campaign)",
        )
        self.assertEqual(contract["unit"], "TM_PER_HA")
        self.assertEqual(contract["status"], "COHERENT_DEFINED_NOT_BUILT_REQUIRES_TRANSIENT_OUTCOME_MASTER")

    def test_14_monthly_yield_replacements_are_forbidden(self) -> None:
        forbidden = set(self.config["transient_outcome_contract"]["forbidden_replacements"])
        self.assertEqual(
            forbidden,
            {"MEAN_MONTHLY_YIELD", "SUM_MONTHLY_YIELD", "MAX_MONTHLY_YIELD", "CALENDAR_YEAR_YIELD"},
        )

    def test_15_perennial_outcomes_are_authorized_for_design(self) -> None:
        contracts = self.config["perennial_outcome_contracts"]
        self.assertEqual(set(contracts), {"MANGO", "LEMON", "BANANA"})
        for contract in contracts.values():
            self.assertEqual(contract["status"], "AUTHORIZED_FOR_ECONOMETRIC_DESIGN")
            self.assertEqual(contract["unit"], "TM_PER_HA")
            self.assertEqual(contract["observation_unit"], "DISTRICT_CROP_CALENDAR_YEAR")

    def test_16_no_productive_stock_or_installed_stock_substitution(self) -> None:
        self.assertFalse(self.config["outcome_semantics"]["VERDE_ACTUAL"]["productive_stock_inference_authorized"])
        for contract in self.config["perennial_outcome_contracts"].values():
            self.assertFalse(contract["verde_actual_used_as_productive_stock"])
            self.assertFalse(contract["cosecha_used_as_installed_stock"])

    def test_17_dual_layers_are_exact_and_nonaggregated(self) -> None:
        layers = self.config["dual_analytical_layers"]
        self.assertEqual(layers["status"], "SUPPORTED_WITH_STRICT_NONAGGREGATION_FIREWALL")
        self.assertEqual(layers["layer_1"]["name"], "FIVE_CROP_CLIMATE_ECONOMIC_RISK_CHARACTERIZATION")
        self.assertEqual(len(layers["layer_1"]["crop_codes"]), 5)
        self.assertFalse(layers["layer_1"]["combined_portfolio_authorized"])
        self.assertEqual(layers["layer_2"]["name"], "RICE_MAD_FINITE_REFERENCE_CONFIGURATION_STRESS_TEST")
        self.assertEqual(len(layers["layer_2"]["crop_codes"]), 2)

    def test_18_a1_a2_and_13_district_scope_are_exact(self) -> None:
        layer = self.config["dual_analytical_layers"]["layer_2"]
        self.assertEqual(layer["alternative_ids"], ["C0B5-A2020-2021", "C0B5-A2023-2024"])
        self.assertEqual(layer["districts_n"], 13)
        self.assertFalse(layer["perennials_included"])

    def test_19_yield_area_mapping_does_not_equate_sown_and_harvested_area(self) -> None:
        mapping = self.config["yield_area_mapping"]
        self.assertEqual(mapping["status"], "REQUIRES_SOWN_TO_HARVESTED_AREA_MAPPING_GATE")
        self.assertEqual(mapping["yield_object"], "Y_d,c,s_TM_PER_HARVESTED_HA")
        self.assertEqual(mapping["reference_area_object"], "A_d,c,k_SIEMBRA_HA")
        self.assertFalse(mapping["physical_production_mapping_authorized"])

    def test_20_alternative_timing_maps_without_generic_t3(self) -> None:
        mapping = self.config["alternative_timing_to_climate_mapping"]
        self.assertEqual(mapping["status"], "STRUCTURALLY_COMPATIBLE_REQUIRES_SCENARIO_EXPOSURE_BUILD")
        self.assertTrue(mapping["use_frozen_alternative_specific_timing_weights"])
        self.assertFalse(mapping["generic_t3_rule_authorized"])
        self.assertFalse(mapping["pooled_timing_profile_authorized"])

    def test_21_monetary_dimensional_identity_passes(self) -> None:
        economic = self.config["economic_translation"]
        self.assertEqual(
            economic["monetary_dimensional_identity"],
            "PASS_TM_PER_HA_X_HA_X_1000_KG_PER_TM_X_S_PER_KG_EQUALS_S",
        )

    def test_22_price_mapping_requires_a_future_gate(self) -> None:
        economic = self.config["economic_translation"]
        self.assertEqual(economic["price_temporal_mapping_status"], "REQUIRES_PRICE_MAPPING_GATE")
        self.assertEqual(economic["invented_price_rules"], [])

    def test_23_economic_structural_form_is_not_numerical_gvp(self) -> None:
        economic = self.config["economic_translation"]
        self.assertEqual(economic["structural_form_status"], "STRUCTURAL_FORM_AUTHORIZED")
        self.assertEqual(economic["numerical_status"], "NUMERICAL_MAPPING_PENDING")
        self.assertFalse(economic["gvp_built"])

    def test_24_nominal_comparability_requires_explicit_treatment(self) -> None:
        self.assertEqual(
            self.config["economic_translation"]["nominal_price_comparability_status"],
            "REQUIRES_EXPLICIT_MONETARY_TREATMENT_GATE",
        )

    def test_25_five_crop_aggregations_are_not_authorized(self) -> None:
        aggregation = self.config["aggregation_and_risk"]
        self.assertEqual(aggregation["layer1_five_crop_aggregation_status"], "NOT_YET_AUTHORIZED")
        self.assertEqual(aggregation["five_crop_a1_a2_aggregation_status"], "NOT_AUTHORIZED")

    def test_26_risk_scope_is_transient_only_without_perennial_cancellation(self) -> None:
        aggregation = self.config["aggregation_and_risk"]
        self.assertEqual(aggregation["a1_a2_risk_metric_scope"], "TRANSIENT_BLOCK_ONLY")
        self.assertFalse(aggregation["common_perennial_random_component_can_be_assumed_to_cancel_in_cvar"])

    def test_27_rice_sample_contract_is_exact(self) -> None:
        sample = self.config["sample_contracts"]["RICE"]
        self.assertEqual(sample["available_periods"], list(joint.CAMPAIGNS))
        self.assertEqual(sample["districts_n"], 46)
        self.assertEqual(sample["usable_outcome_observations"], 294)
        self.assertEqual(sample["expected_observations_if_complete"], 322)

    def test_28_mad_sample_contract_is_exact(self) -> None:
        sample = self.config["sample_contracts"]["MAD"]
        self.assertEqual(sample["available_periods"], list(joint.CAMPAIGNS))
        self.assertEqual(sample["districts_n"], 55)
        self.assertEqual(sample["usable_outcome_observations"], 352)
        self.assertEqual(sample["expected_observations_if_complete"], 385)

    def test_29_mango_sample_contract_is_exact(self) -> None:
        sample = self.config["sample_contracts"]["MANGO"]
        self.assertEqual(sample["available_periods"], list(range(2016, 2024)))
        self.assertEqual(sample["districts_n"], 36)
        self.assertEqual(sample["usable_outcome_observations"], 255)
        self.assertEqual(sample["expected_observations_if_complete"], 288)

    def test_30_lemon_sample_contract_is_exact(self) -> None:
        sample = self.config["sample_contracts"]["LEMON"]
        self.assertEqual(sample["available_periods"], list(range(2016, 2024)))
        self.assertEqual(sample["districts_n"], 44)
        self.assertEqual(sample["usable_outcome_observations"], 311)
        self.assertEqual(sample["expected_observations_if_complete"], 352)

    def test_31_banana_sample_contract_is_exact(self) -> None:
        sample = self.config["sample_contracts"]["BANANA"]
        self.assertEqual(sample["available_periods"], list(range(2016, 2024)))
        self.assertEqual(sample["districts_n"], 54)
        self.assertEqual(sample["usable_outcome_observations"], 390)
        self.assertEqual(sample["expected_observations_if_complete"], 432)

    def test_32_perennial_outcome_and_exposure_keys_match(self) -> None:
        samples = joint.perennial_sample_contracts()
        self.assertEqual({name: samples[name]["usable_outcome_observations"] for name in samples}, {"MANGO": 255, "LEMON": 311, "BANANA": 390})

    def test_33_c0b6_support_transient_candidates_are_recorded(self) -> None:
        samples = self.config["sample_contracts"]
        self.assertEqual(samples["RICE"]["c0b6_support_usable_observations"], 90)
        self.assertEqual(samples["MAD"]["c0b6_support_usable_observations"], 91)
        self.assertEqual(samples["RICE"]["c0b6_support_expected_if_complete"], 91)
        self.assertEqual(samples["MAD"]["c0b6_support_expected_if_complete"], 91)

    def test_34_temporal_depth_is_short_and_unbalanced(self) -> None:
        self.assertEqual(
            self.config["temporal_depth_status"],
            "SHORT_T_UNBALANCED_7_CAMPAIGN_TRANSIENT_8_YEAR_PERENNIAL_NO_LONG_PANEL_CLAIM",
        )
        self.assertTrue(self.config["extreme_year_influence_diagnostic_required"])

    def test_35_econometric_claim_ceiling_is_noncausal(self) -> None:
        self.assertEqual(
            self.config["maximum_econometric_claim_status"],
            "EMPIRICAL_ASSOCIATION_CLIMATE_RESPONSE_ONLY",
        )

    def test_36_out_of_support_control_is_required(self) -> None:
        self.assertTrue(self.config["out_of_support_control_required"])

    def test_37_scenario_model_order_is_exact(self) -> None:
        separation = self.config["scenario_model_separation"]
        self.assertEqual(separation["status"], "PASS")
        self.assertEqual(separation["required_order"][0], "OUTCOME_CONTRACT")
        self.assertEqual(separation["required_order"][-1], "RISK_METRICS")
        self.assertFalse(separation["scenario_tuning_may_influence_econometric_specification"])

    def test_38_joint_rq_architecture_is_two_linked_nonmerged_questions(self) -> None:
        self.assertEqual(
            self.config["joint_rq_architecture_status"],
            "SUPPORTED_AS_TWO_LINKED_NONMERGED_ANALYTICAL_QUESTIONS",
        )

    def test_39_authorization_matrix_has_exact_components(self) -> None:
        expected = {
            "Rice climate-yield model", "MAD climate-yield model", "Mango climate-yield model",
            "Lemon climate-yield model", "Banana climate-yield model", "A1/A2 transient area master",
            "alternative-specific timing", "five-crop combined portfolio", "A1/A2 five-crop aggregation",
            "A1/A2 transient economic aggregation", "price mapping", "GVP construction", "VaR", "CVaR",
            "ENSO scenario prediction", "continuous optimization", "water-constrained model",
        }
        self.assertEqual(len(self.authorization), 17)
        self.assertEqual({row["COMPONENT"] for row in self.authorization}, expected)

    def test_40_authorization_matrix_has_no_ambiguous_booleans(self) -> None:
        self.assertTrue(all(row["AUTHORIZED_NEXT_PHASE"] in {"TRUE", "FALSE"} for row in self.authorization))
        self.assertTrue(all(row["FORBIDDEN"] in {"TRUE", "FALSE"} for row in self.authorization))
        self.assertTrue(all(row["CURRENT_STATUS"] and row["REQUIRES_FUTURE_GATE"] for row in self.authorization))

    def test_41_econometric_design_phase_has_targeted_gates(self) -> None:
        self.assertEqual(
            self.config["econometric_design_phase_status"],
            "AUTHORIZED_WITH_TARGETED_PRE_ESTIMATION_GATES",
        )
        self.assertEqual(len(self.config["targeted_pre_estimation_gates"]), 3)

    def test_42_no_model_fitting_or_downstream_calculation(self) -> None:
        firewalls = self.config["firewalls"]
        for key in (
            "no_model_fitting", "no_outcome_driven_architecture_selection", "no_causal_claim",
            "no_enso_scenario", "no_economic_result", "no_var_cvar", "no_alternative_ranking",
        ):
            self.assertTrue(firewalls[key], key)

    def test_43_script_imports_no_modelling_library(self) -> None:
        tree = ast.parse(joint.SCRIPT_PATH.read_text(encoding="utf-8"))
        imported = {
            alias.name.split(".")[0]
            for node in ast.walk(tree) if isinstance(node, ast.Import)
            for alias in node.names
        } | {
            (node.module or "").split(".")[0]
            for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
        }
        self.assertTrue(imported.isdisjoint({"statsmodels", "sklearn", "linearmodels"}))

    def test_44_no_water_land_capacity_or_optimization(self) -> None:
        firewalls = self.config["firewalls"]
        self.assertEqual(firewalls["water_model_status"], "NOT_AUTHORIZED")
        self.assertEqual(firewalls["continuous_optimization_status"], "NOT_AUTHORIZED")
        self.assertFalse(firewalls["land_capacity_inference_used"])

    def test_45_evidence_registry_is_complete_and_adjudicated(self) -> None:
        self.assertEqual(len(self.evidence), 20)
        self.assertEqual([row["EVIDENCE_ID"] for row in self.evidence], [f"JC0-E{i:03d}" for i in range(1, 21)])
        self.assertEqual({row["STATUS"] for row in self.evidence}, {"PASS_ADJUDICATED"})
        c0a_refs = [row for row in self.evidence if row["DOMAIN"] == "C0A_OBJECT_PROVENANCE"]
        self.assertEqual(len(c0a_refs), 4)

    def test_46_compatibility_matrix_records_all_required_gates(self) -> None:
        self.assertEqual(len(self.compatibility), 20)
        self.assertTrue(all(row["COMPATIBILITY_STATUS"] in {"PASS", "PASS_WITH_GATE"} for row in self.compatibility))
        gates = {row["REQUIRED_GATE"] for row in self.compatibility}
        self.assertTrue({"TRANSIENT_OUTCOME_MASTER", "PRICE_MAPPING_GATE", "EMPIRICAL_SUPPORT_ENVELOPE"} <= gates)

    def test_47_report_contains_required_integration_sections(self) -> None:
        for number in range(1, 23):
            self.assertIn(f"## {number}.", self.report)
        for token in (
            "JOINT_C0_STATUS=PASS_WITH_TARGETED_PRE_ESTIMATION_GATES",
            "REQUIRES_SOWN_TO_HARVESTED_AREA_MAPPING_GATE",
            "TRANSIENT_BLOCK_ONLY",
            "EMPIRICAL_ASSOCIATION_CLIMATE_RESPONSE_ONLY",
        ):
            self.assertIn(token, self.report)

    def test_48_artifact_hashes_are_consistent(self) -> None:
        expected = {
            joint.EVIDENCE_PATH.relative_to(ROOT).as_posix(),
            joint.COMPATIBILITY_PATH.relative_to(ROOT).as_posix(),
            joint.AUTHORIZATION_PATH.relative_to(ROOT).as_posix(),
        }
        self.assertEqual(set(self.config["artifact_sha256"]), expected)
        for path, digest in self.config["artifact_sha256"].items():
            self.assertEqual(sha256(ROOT / path), digest, path)

    def test_49_outputs_reproduce_byte_for_byte(self) -> None:
        outputs, config = joint.build_output_bytes()
        self.assertEqual(set(outputs), {joint.EVIDENCE_PATH, joint.COMPATIBILITY_PATH, joint.AUTHORIZATION_PATH, joint.CONFIG_PATH, joint.REPORT_PATH})
        for path, payload in outputs.items():
            self.assertEqual(path.read_bytes(), payload, path.name)
        self.assertEqual(self.config, config)

    def test_50_joint_files_are_utf8_lf_with_one_final_lf(self) -> None:
        for path in joint.AUTHORIZED_SCOPE:
            raw = (ROOT / path).read_bytes()
            self.assertFalse(raw.startswith(b"\xef\xbb\xbf"), path)
            self.assertNotIn(b"\r", raw, path)
            self.assertTrue(raw.endswith(b"\n"), path)
            self.assertFalse(raw.endswith(b"\n\n"), path)

    def test_51_preflight_passes_all_material_gates(self) -> None:
        lines, config = joint.run_preflight()
        self.assertIn("C0A_IMMUTABILITY_GATE=PASS", lines)
        self.assertIn("C0B6_IMMUTABILITY_GATE=PASS", lines)
        self.assertIn("PERSISTENT_SCOPE_GATE=PASS", lines)
        self.assertIn(f"JOINT_C0_PREFLIGHT={joint.FINAL_STATUS}", lines)
        self.assertEqual(config["final_status"], joint.FINAL_STATUS)

    def test_52_default_cli_is_read_only(self) -> None:
        paths = [joint.EVIDENCE_PATH, joint.COMPATIBILITY_PATH, joint.AUTHORIZATION_PATH, joint.CONFIG_PATH, joint.REPORT_PATH]
        before = {path: sha256(path) for path in paths}
        result = subprocess.run(
            [sys.executable, "-B", str(joint.SCRIPT_PATH)], cwd=ROOT,
            text=True, encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f"JOINT_C0_PREFLIGHT={joint.FINAL_STATUS}", result.stdout)
        self.assertEqual({path: sha256(path) for path in paths}, before)


if __name__ == "__main__":
    unittest.main()
