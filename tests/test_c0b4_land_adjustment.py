"""Regression tests for the C0B4 transient land feasibility package."""

from __future__ import annotations

import ast
import csv
import hashlib
import json
import subprocess
import sys
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import c0b4_land_adjustment_preflight as preflight  # noqa: E402


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=ROOT, text=True, encoding="utf-8",
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    )
    return result.stdout.strip()


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


class C0B4LandAdjustmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry_columns, cls.registry = read_csv(preflight.REGISTRY_PATH)
        cls.occupancy_columns, cls.occupancy = read_csv(preflight.OCCUPANCY_PATH)
        cls.adjustment_columns, cls.adjustment = read_csv(preflight.ADJUSTMENT_PATH)
        cls.config = json.loads(preflight.CONFIG_PATH.read_text(encoding="utf-8"))
        cls.report = preflight.REPORT_PATH.read_text(encoding="utf-8")

    def test_01_exact_c0b3_freeze_identity(self) -> None:
        self.assertEqual(git("branch", "--show-current"), preflight.EXPECTED_BRANCH)
        self.assertEqual(git("rev-parse", "HEAD"), preflight.EXPECTED_HEAD)
        self.assertEqual(git("show", "-s", "--format=%s", "HEAD"), preflight.EXPECTED_SUBJECT)
        result = subprocess.run(
            ["git", "merge-base", "--is-ancestor", preflight.EXPECTED_HEAD, "HEAD"],
            cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        self.assertEqual(result.returncode, 0)

    def test_02_c0b3_and_frozen_inputs_are_byte_identical(self) -> None:
        for relative, expected in {**preflight.C0B3_HASHES, **preflight.FROZEN_DATA_HASHES}.items():
            self.assertEqual(hashlib.sha256((ROOT / relative).read_bytes()).hexdigest(), expected, relative)
        paths = [*preflight.C0B3_HASHES, *preflight.FROZEN_DATA_HASHES]
        changed = set(filter(None, git("diff", "--name-only", "--", *paths).splitlines()))
        changed |= set(filter(None, git("diff", "--cached", "--name-only", "--", *paths).splitlines()))
        self.assertEqual(changed, set())

    def test_03_exact_seven_file_c0b4_scope(self) -> None:
        tracked = set(filter(None, git("diff", "--name-only").splitlines()))
        tracked |= set(filter(None, git("diff", "--cached", "--name-only").splitlines()))
        untracked = {
            line.replace("\\", "/")
            for line in git("ls-files", "--others", "--exclude-standard").splitlines()
            if line
        }
        self.assertEqual(tracked, set())
        self.assertEqual(untracked, preflight.AUTHORIZED_SCOPE)

    def test_04_artifact_schemas_are_exact(self) -> None:
        self.assertEqual(self.registry_columns, preflight.REGISTRY_COLUMNS)
        self.assertEqual(self.occupancy_columns, preflight.OCCUPANCY_COLUMNS)
        self.assertEqual(self.adjustment_columns, preflight.ADJUSTMENT_COLUMNS)

    def test_05_transient_crop_universe_is_exact(self) -> None:
        self.assertEqual(len(self.occupancy), 2)
        self.assertEqual({row["CROP_CODE"] for row in self.occupancy}, set(preflight.TRANSIENT_CROPS))
        self.assertEqual(
            {row["CROP_STD"] for row in self.occupancy},
            {"ARROZ", "MAIZ AMARILLO DURO"},
        )

    def test_06_area_ha_is_physical_footprint_only(self) -> None:
        land = self.config["land_ontology"]
        self.assertEqual(land["AREA_HA_status"], "PHYSICAL_AGRICULTURAL_FOOTPRINT_ONLY")
        self.assertFalse(land["direct_campaign_hectare_hard_cap_authorized"])
        self.assertTrue(all(row["AREA_HA_COMPATIBILITY_STATUS"] == "INCOMPATIBLE_WITH_DIRECT_CAMPAIGN_CAP" for row in self.occupancy))

    def test_07_land_concepts_remain_distinct(self) -> None:
        concepts = set(self.config["land_ontology"]["distinct_concepts"])
        required = {
            "PHYSICAL_AGRICULTURAL_FOOTPRINT", "PERENNIAL_INSTALLED_STOCK",
            "TRANSIENT_CAMPAIGN_SOWN_AREA", "TRANSIENT_MONTHLY_SOWN_FLOW",
            "SIMULTANEOUS_TRANSIENT_OCCUPANCY", "OTHER_CROP_OCCUPANCY",
            "REALLOCABLE_TRANSIENT_AREA", "SEQUENTIAL_REUSE",
        }
        self.assertTrue(required <= concepts)
        self.assertEqual(len(concepts), len(self.config["land_ontology"]["distinct_concepts"]))

    def test_08_perennial_residual_is_not_reallocable_land(self) -> None:
        land = self.config["land_ontology"]
        self.assertFalse(land["perennial_subtraction_yields_reallocable_transient_land"])
        self.assertFalse(self.config["reallocable_land"]["area_ha_minus_fixed_perennials_authorized"])
        self.assertIn("PERENNIAL_SUBTRACTION_AS_REALLOCABLE_TRANSIENT_LAND=NOT_AUTHORIZED", self.report)

    def test_09_other_crop_universe_is_recomputed(self) -> None:
        self.assertEqual(preflight.compute_universe_audit(), self.config["other_crop_universe_audit"])
        self.assertEqual(self.config["other_crop_universe_audit"]["other_crop_codes"], 91)
        self.assertEqual(
            self.config["other_crop_universe_audit"]["model_district_years_with_positive_other_crop_sowing"],
            429,
        )

    def test_10_five_target_crops_are_not_the_full_land_universe(self) -> None:
        audit = self.config["other_crop_universe_audit"]
        self.assertEqual(audit["target_crop_codes"], 5)
        self.assertEqual(audit["raw_crop_codes"], 96)
        self.assertTrue(self.config["land_ontology"]["other_crop_occupancy_relevant"])
        self.assertFalse(self.config["land_ontology"]["all_remaining_physical_land_reallocable"])

    def test_11_siembra_month_is_not_occupancy_month(self) -> None:
        self.assertFalse(self.config["land_ontology"]["siembra_month_equals_occupancy_month"])
        self.assertTrue(all(row["PLANTING_FLOW_ANCHOR"] == "SIEMBRA_MONTHLY_GROSS_SOWN_OR_TRANSPLANTED_AREA_HA" for row in self.occupancy))
        self.assertIn("SIEMBRA_m != OCCUPANCY_m", self.report)

    def test_12_climate_windows_are_not_land_occupancy_windows(self) -> None:
        self.assertFalse(self.config["land_ontology"]["climate_response_window_is_physical_occupancy_window"])
        self.assertFalse(self.config["simultaneous_occupancy_mapping"]["climate_windows_used"])
        self.assertIn("CLIMATE_RESPONSE_WINDOW != PHYSICAL_LAND_OCCUPANCY_WINDOW", self.report)

    def test_13_no_parcel_reuse_is_inferred(self) -> None:
        self.assertFalse(self.config["land_ontology"]["parcel_sequential_cropping_inferred_from_district_aggregates"])
        self.assertEqual(self.config["other_crop_universe_audit"]["rice_mad_campaign_totals_exceeding_area_ha"], 18)
        self.assertIn("PARCEL_DOUBLE_CROPPING_INFERRED_FROM_DISTRICT_AGGREGATES", self.config["forbidden_interpretations"])

    def test_14_occupancy_duration_ranges_are_sensitivity_only(self) -> None:
        expected = {"ARROZ": (142, 155), "MAIZ AMARILLO DURO": (140, 170)}
        for crop, (lower, upper) in expected.items():
            adjudication = self.config["occupancy_adjudication"][crop]
            self.assertEqual(adjudication["duration_status"], "SENSITIVITY_ONLY_RANGE")
            self.assertIsNone(adjudication["duration_value"])
            self.assertEqual((adjudication["duration_lower"], adjudication["duration_upper"]), (lower, upper))
            self.assertFalse(adjudication["model_parameter_authorized"])

    def test_15_no_duration_midpoint_is_invented(self) -> None:
        self.assertTrue(all(row["OCCUPANCY_DURATION_VALUE"] == "" for row in self.occupancy))
        self.assertEqual(
            {(row["CROP_STD"], row["OCCUPANCY_DURATION_LOWER"], row["OCCUPANCY_DURATION_UPPER"]) for row in self.occupancy},
            {("ARROZ", "142", "155"), ("MAIZ AMARILLO DURO", "140", "170")},
        )

    def test_16_simultaneous_occupancy_mapping_is_not_authorized(self) -> None:
        mapping = self.config["simultaneous_occupancy_mapping"]
        self.assertEqual(mapping["status"], "SENSITIVITY_ONLY_NOT_MODEL_AUTHORIZED")
        self.assertFalse(mapping["crop_general_kernel_certified"])
        self.assertFalse(mapping["field_release_endpoint_certified"])
        self.assertEqual(mapping["model_kernel_parameters_authorized"], 0)

    def test_17_reallocable_land_is_not_observed(self) -> None:
        reallocable = self.config["reallocable_land"]
        self.assertEqual(reallocable["status"], "NOT_OBSERVED")
        self.assertFalse(reallocable["certified_identity_available"])
        self.assertFalse(reallocable["official_district_crop_planning_bound_available"])
        self.assertTrue(all(row["REALLOCABLE_LAND_STATUS"] == "NOT_OBSERVED" for row in self.occupancy))

    def test_18_land_hard_cap_is_not_authorized(self) -> None:
        hard_cap = self.config["land_hard_cap"]
        self.assertEqual(hard_cap["status"], "NOT_AUTHORIZED")
        self.assertFalse(hard_cap["defensible_simultaneous_occupancy_available"])
        self.assertFalse(hard_cap["defensible_available_physical_capacity_available"])
        self.assertTrue(all(row["LAND_HARD_CAP_STATUS"] == "NOT_AUTHORIZED" for row in self.occupancy))

    def test_19_adjustment_audit_has_exact_district_crop_keys(self) -> None:
        self.assertEqual(len(self.adjustment), 110)
        self.assertEqual(len({(row["UBIGEO"], row["CROP_CODE"]) for row in self.adjustment}), 110)
        self.assertEqual(Counter(row["CROP_STD"] for row in self.adjustment), Counter({"ARROZ": 55, "MAIZ AMARILLO DURO": 55}))

    def test_20_adjustment_diagnostics_reproduce_exactly(self) -> None:
        self.assertEqual(self.adjustment, preflight.build_adjustment_rows())

    def test_21_historical_diagnostics_are_not_model_bounds(self) -> None:
        self.assertTrue(all(row["OFFICIAL_BOUND_AVAILABLE"] == "FALSE" for row in self.adjustment))
        self.assertTrue(all(row["MODEL_BOUND_AUTHORIZED"] == "FALSE" for row in self.adjustment))
        self.assertTrue(all(row["AUTHORIZED_LOWER_RULE"] == "" for row in self.adjustment))
        self.assertTrue(all(row["AUTHORIZED_UPPER_RULE"] == "" for row in self.adjustment))
        self.assertEqual(self.config["model_authorized_adjustment_bounds_n"], 0)

    def test_22_adjustment_status_counts_are_exact(self) -> None:
        expected = {
            "ARROZ": Counter({"SENSITIVITY_ONLY": 34, "UNRESOLVED": 21}),
            "MAIZ AMARILLO DURO": Counter({"SENSITIVITY_ONLY": 44, "UNRESOLVED": 11}),
        }
        for crop, counts in expected.items():
            actual = Counter(row["ADJUSTMENT_BOUND_STATUS"] for row in self.adjustment if row["CROP_STD"] == crop)
            self.assertEqual(actual, counts)
        self.assertFalse(self.config["adjustment_envelope"]["arbitrary_percentage_bound_authorized"])

    def test_23_baseline_year_is_not_invented(self) -> None:
        self.assertEqual(self.config["baseline"]["status"], "NOT_YET_FROZEN")
        self.assertIsNone(self.config["baseline"]["year"])
        self.assertFalse(self.config["baseline"]["outcome_tuning_allowed"])
        self.assertTrue(all(row["BASELINE_STATUS"] == "NOT_YET_FROZEN" for row in self.adjustment))

    def test_24_t3_share_diagnostics_reproduce_exactly(self) -> None:
        self.assertEqual(preflight.compute_t3_diagnostics(), self.config["t3_share_diagnostics"])

    def test_25_t3_share_rules_are_candidates_only(self) -> None:
        for crop in ("ARROZ", "MAIZ AMARILLO DURO"):
            rule = self.config["t3_share_rule"][crop]
            self.assertEqual(rule["status"], "CANDIDATE_NOT_YET_AUTHORIZED")
            self.assertFalse(rule["future_fixed_rule_defined"])
            self.assertFalse(rule["pooling_rule_defined"])
            self.assertEqual(rule["model_share_parameters_authorized"], 0)
        self.assertTrue(all(row["T3_SHARE_RULE_STATUS"] == "CANDIDATE_NOT_YET_AUTHORIZED" for row in self.occupancy))

    def test_26_evidence_registry_is_resolved_and_nonparametric(self) -> None:
        evidence_ids = [row["EVIDENCE_ID"] for row in self.registry]
        self.assertEqual(len(evidence_ids), len(set(evidence_ids)))
        self.assertTrue({row["EVIDENCE_DOMAIN"] for row in self.registry} <= preflight.ALLOWED_EVIDENCE_DOMAINS)
        referenced = {
            evidence_id
            for row in self.occupancy
            for evidence_id in row["EVIDENCE_IDS"].split(";")
            if evidence_id
        }
        self.assertTrue(referenced <= set(evidence_ids))
        self.assertTrue(all(row["MODEL_ADMISSIBILITY"] != "MODEL_ADMISSIBLE" for row in self.registry))

    def test_27_official_pdf_hashes_are_recorded(self) -> None:
        self.assertEqual(self.config["source_provenance"]["official_pdf_sha256"], preflight.EXTERNAL_PDF_HASHES)
        notes = "\n".join(row["NOTES"] for row in self.registry)
        for source, digest in preflight.EXTERNAL_PDF_HASHES.items():
            self.assertIn(f"{source}_SHA256={digest}", notes)

    def test_28_no_water_or_optimizer_is_authorized(self) -> None:
        authorizations = self.config["authorizations"]
        self.assertFalse(authorizations["water_model"])
        self.assertFalse(authorizations["water_hard_constraint"])
        self.assertFalse(authorizations["optimizer"])
        modules = set()
        for path in (preflight.SCRIPT_PATH, preflight.TEST_PATH):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    modules.update(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    modules.add(node.module)
        self.assertTrue(modules.isdisjoint({"pulp", "cvxpy", "pyomo", "scipy.optimize"}))

    def test_29_outcome_and_optimizer_leakage_is_forbidden(self) -> None:
        firewall = self.config["input_firewall"]
        allowed = set(firewall["allowed_computational_fields"])
        forbidden = set(firewall["forbidden_selection_inputs"])
        self.assertTrue(allowed.isdisjoint(forbidden))
        self.assertTrue({"YIELD", "PRODUCCION", "YIELD_RAW", "ECONOMETRIC_P_VALUE", "PROFIT", "CVAR", "OPTIMIZER_OBJECTIVE_VALUE"} <= forbidden)
        self.assertFalse(self.config["t3_share_rule"]["selection_may_use_outcomes_or_climate_response"])
        self.assertFalse(self.config["t3_share_rule"]["selection_may_use_optimizer_results"])

    def test_30_report_has_all_required_sections_and_verdicts(self) -> None:
        for number in range(1, 23):
            self.assertIn(f"## {number}.", self.report)
        for token in (
            "AREA_HA_STATUS=PHYSICAL_AGRICULTURAL_FOOTPRINT_ONLY",
            "REALLOCABLE_TRANSIENT_LAND_STATUS=NOT_OBSERVED",
            "LAND_HARD_CAP_STATUS=NOT_AUTHORIZED",
            "BASELINE_YEAR_STATUS=NOT_YET_FROZEN",
            "C0B4_DECISION_ENDSTATE=DECISION_MODEL_NOT_YET_FEASIBLE",
        ):
            self.assertIn(token, self.report)

    def test_31_final_status_preserves_negative_feasibility_finding(self) -> None:
        self.assertEqual(self.config["model_authorized_land_parameters_n"], 0)
        self.assertEqual(self.config["model_authorized_adjustment_bounds_n"], 0)
        self.assertEqual(self.config["decision_feasibility_endstate"], "DECISION_MODEL_NOT_YET_FEASIBLE")
        self.assertEqual(self.config["final_status"], "PASS_FOR_FINAL_INDEPENDENT_C0B4_FREEZE_AUDIT")

    def test_32_preflight_passes(self) -> None:
        self.assertEqual(preflight.run_preflight(), [])

    def test_33_physical_capacity_and_strategic_domain_are_distinct(self) -> None:
        decision = self.config["decision_domain_adjudication"]
        self.assertEqual(decision["physical_land_capacity_model_feasibility"], "NOT_FEASIBLE")
        self.assertEqual(
            decision["strategic_transient_decision_domain_feasibility"],
            "POTENTIALLY_RECOVERABLE_BUT_NOT_CURRENTLY_MODEL_ADMISSIBLE",
        )
        self.assertFalse(decision["alternative_decision_domain_currently_authorized"])

    def test_34_other_crop_c0b4a_diagnostics_are_exact(self) -> None:
        audit = self.config["other_crop_universe_audit"]
        self.assertEqual(audit, preflight.compute_universe_audit())
        self.assertEqual(audit["other_crop_codes"], 91)
        self.assertEqual(audit["model_district_years_2016_2023"], 440)
        self.assertEqual(audit["model_district_years_with_positive_other_crop_sowing"], 429)
        self.assertEqual(audit["median_positive_other_crop_codes_per_relevant_district_year"], 7)

    def test_35_land_hard_cap_is_not_universally_necessary(self) -> None:
        decision = self.config["decision_domain_adjudication"]
        self.assertFalse(decision["land_hard_cap_necessary_for_any_valid_decision_model"])
        self.assertFalse(decision["physical_hard_cap_required_for_current_architecture"])
        self.assertFalse(decision["alternative_decision_domain_currently_authorized"])
        self.assertEqual(self.config["land_hard_cap"]["status"], "NOT_AUTHORIZED")

    def test_36_latest_period_is_not_a_common_baseline(self) -> None:
        baseline = self.config["baseline"]
        self.assertEqual(
            baseline["latest_complete_period_status"],
            "NOT_AVAILABLE_AS_COMMON_DISTRICT_CROP_BASELINE",
        )
        self.assertEqual(baseline["latest_complete_period_diagnostics"], preflight.compute_baseline_coverage())
        self.assertEqual(baseline["latest_complete_period_diagnostics"]["rice_complete_districts"], 19)
        self.assertEqual(baseline["latest_complete_period_diagnostics"]["mad_complete_districts"], 26)
        self.assertEqual(baseline["latest_complete_period_diagnostics"]["partial_2024_2025_campaign_complete_district_crop_rows"], 0)

    def test_37_multiyear_and_official_baselines_remain_unauthorized(self) -> None:
        baseline = self.config["baseline"]
        self.assertEqual(baseline["status"], "NOT_YET_FROZEN")
        self.assertIsNone(baseline["year"])
        self.assertEqual(baseline["multiyear_reference_status"], "METHOD_DEFINED_BUT_NOT_SOURCE_MANDATED")
        self.assertFalse(baseline["district_official_planning_baseline_available"])
        self.assertFalse(baseline["pcr_agency_hectares_as_district_baseline_authorized"])
        self.assertEqual(
            set(baseline["silently_forbidden_choices"]),
            {"2023", "LATEST_OBSERVATION", "HISTORICAL_MEDIAN", "RECENT_MEDIAN", "PCR_AGENCY_HECTARES"},
        )

    def test_38_historical_support_and_convex_hull_are_context_only(self) -> None:
        support = self.config["historical_support_decision_domain"]
        self.assertEqual(support["status"], "EMPIRICAL_CONTEXT_ONLY")
        self.assertFalse(support["historical_convex_hull_authorized"])
        self.assertFalse(support["historically_observed_equals_future_feasible"])
        self.assertFalse(support["current_feasible_set_authorized"])

    def test_39_fixed_total_rice_mad_domain_is_falsified(self) -> None:
        fixed = self.config["fixed_total_rice_mad_composition_domain"]
        recomputed = preflight.compute_joint_portfolio_audit()
        self.assertEqual(fixed["status"], "NOT_SUPPORTED")
        self.assertFalse(fixed["crop_substitutability_established"])
        self.assertFalse(fixed["negative_correlation_proves_substitutability"])
        self.assertEqual(recomputed["joint_complete_district_campaign_observations"], 106)
        self.assertEqual(recomputed["adjacent_joint_campaign_changes"], 40)
        self.assertEqual(recomputed["reciprocal_direction_changes"], 19)
        self.assertEqual(recomputed["same_direction_changes"], 18)
        self.assertEqual(recomputed["exact_fixed_total_changes"], 0)
        for key, value in recomputed.items():
            if key != "districts_with_any_joint_complete_campaign":
                self.assertEqual(fixed[key], value, key)

    def test_40_crop_specific_and_soft_policy_domains_are_not_bounds(self) -> None:
        crop_specific = self.config["crop_specific_baseline_relative_domain"]
        self.assertEqual(crop_specific["status"], "SENSITIVITY_ONLY_NOT_MODEL_AUTHORIZED")
        self.assertFalse(crop_specific["historical_variation_is_authorized_bound"])
        soft = self.config["soft_policy_adjustment_bound"]
        self.assertEqual(
            soft["ontology_allowed_by_c0b1"],
            "YES_CONDITIONAL_ON_PROSPECTIVE_PRESPECIFIED_EVIDENCE_RULE",
        )
        self.assertFalse(soft["actual_bound_exists"])
        self.assertFalse(soft["model_authorized"])
        self.assertFalse(soft["arbitrary_percentage_allowed"])
        self.assertEqual(self.config["model_authorized_adjustment_bounds_n"], 0)

    def test_41_finite_portfolio_candidate_is_future_only(self) -> None:
        future = self.config["future_decision_domain_gate"]
        self.assertTrue(future["required"])
        self.assertEqual(
            future["minimum_defensible_decision_scope_candidate"],
            "FINITE_PRESPECIFIED_OBSERVED_PORTFOLIOS_FOR_SUPPORTED_DISTRICTS_REQUIRES_FORMAL_SCOPE_ADJUDICATION",
        )
        self.assertEqual(
            future["finite_prespecified_decision_alternatives_status"],
            "POTENTIALLY_FEASIBLE_AS_SCENARIO_EVALUATION_REQUIRES_FORMAL_REFRAMING",
        )
        self.assertFalse(future["finite_portfolio_candidate_currently_authorized"])
        self.assertFalse(future["historical_portfolios_selected"])
        self.assertFalse(future["finite_scenario_evaluation_is_continuous_optimization"])

    def test_42_continuous_numerical_optimization_remains_blocked(self) -> None:
        self.assertEqual(self.config["numerical_optimization_feasibility"], "NOT_AUTHORIZED")
        self.assertEqual(
            self.config["decision_feasibility_endstate_definition"],
            "NO_MODEL_ADMISSIBLE_CONTINUOUS_NUMERICAL_RICE_MAD_ALLOCATION_DOMAIN_IS_CURRENTLY_IDENTIFIED",
        )
        authorizations = self.config["authorizations"]
        self.assertFalse(authorizations["continuous_decision_domain"])
        self.assertFalse(authorizations["finite_portfolio_decision_set"])
        self.assertFalse(authorizations["finite_scenario_evaluation"])
        self.assertFalse(authorizations["optimizer"])

    def test_43_t3_and_occupancy_recovery_do_not_rescue_optimization(self) -> None:
        self.assertTrue(all(row["T3_SHARE_RULE_STATUS"] == "CANDIDATE_NOT_YET_AUTHORIZED" for row in self.occupancy))
        self.assertTrue(all(row["OCCUPANCY_DURATION_STATUS"] == "SENSITIVITY_ONLY_RANGE" for row in self.occupancy))
        self.assertTrue(all(row["SIMULTANEOUS_OCCUPANCY_MAPPING_STATUS"] == "SENSITIVITY_ONLY_NOT_MODEL_AUTHORIZED" for row in self.occupancy))
        self.assertTrue(all("T3 share recovery alone" in row["NOTES"] for row in self.occupancy))
        self.assertEqual(self.config["model_authorized_land_parameters_n"], 0)

    def test_44_c0b4a_evidence_rows_are_nonparametric(self) -> None:
        rows = {row["EVIDENCE_ID"]: row for row in self.registry}
        expected = {f"C0B4-E{number:03d}" for number in range(20, 27)}
        self.assertTrue(expected <= set(rows))
        self.assertTrue(all(rows[evidence_id]["MODEL_ADMISSIBILITY"] != "MODEL_ADMISSIBLE" for evidence_id in expected))
        self.assertEqual(rows["C0B4-E023"]["MODEL_ADMISSIBILITY"], "EMPIRICAL_CONTEXT_ONLY")
        self.assertEqual(rows["C0B4-E026"]["MODEL_ADMISSIBILITY"], "FUTURE_GATE_CANDIDATE_ONLY")

    def test_45_report_freezes_decision_domain_hierarchy(self) -> None:
        for token in (
            "LEVEL_1_PHYSICAL_LAND_HARD_CAP=NOT_AUTHORIZED",
            "LEVEL_2_CONTINUOUS_BASELINE_RELATIVE_DECISION_DOMAIN=NOT_AUTHORIZED",
            "LEVEL_3_FIXED_TOTAL_RICE_MAD_COMPOSITION_DOMAIN=NOT_SUPPORTED",
            "LEVEL_4_HISTORICAL_CONVEX_HULL=NOT_AUTHORIZED",
            "LEVEL_5_FINITE_PRESPECIFIED_OBSERVED_PORTFOLIOS=POTENTIAL_FUTURE_CANDIDATE_REQUIRING_FORMAL_SCOPE_ADJUDICATION",
            "FINITE_SCENARIO_EVALUATION != CONTINUOUS_CROP_ALLOCATION_OPTIMIZATION",
            "CONTINUOUS_NUMERICAL_OPTIMIZATION=NOT_AUTHORIZED",
            "POSSIBLE_FUTURE_DECISION_ANALYSIS=NOT_RULED_OUT",
        ):
            self.assertIn(token, self.report)


if __name__ == "__main__":
    unittest.main()
