"""Regression tests for the C0B5 decision-domain adjudication package."""

from __future__ import annotations

import ast
import csv
import hashlib
import inspect
import itertools
import json
import subprocess
import sys
import unittest
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import c0b5_decision_domain_preflight as preflight  # noqa: E402


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


class C0B5DecisionDomainTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry_columns, cls.registry = read_csv(preflight.REGISTRY_PATH)
        cls.route_columns, cls.routes = read_csv(preflight.ROUTES_PATH)
        cls.portfolio_columns, cls.portfolio = read_csv(preflight.PORTFOLIO_PATH)
        cls.config = json.loads(preflight.CONFIG_PATH.read_text(encoding="utf-8"))
        cls.report = preflight.REPORT_PATH.read_text(encoding="utf-8")

    def test_01_exact_c0b4_freeze_ancestry(self) -> None:
        self.assertEqual(git("branch", "--show-current"), preflight.EXPECTED_BRANCH)
        self.assertEqual(git("rev-parse", "HEAD"), preflight.EXPECTED_HEAD)
        self.assertEqual(git("show", "-s", "--format=%s", "HEAD"), preflight.EXPECTED_SUBJECT)
        result = subprocess.run(
            ["git", "merge-base", "--is-ancestor", preflight.EXPECTED_HEAD, "HEAD"],
            cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        self.assertEqual(result.returncode, 0)

    def test_02_c0b4_is_byte_identical(self) -> None:
        for relative, expected in preflight.C0B4_HASHES.items():
            actual = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
            self.assertEqual(actual, expected, relative)
        changed = set(filter(None, git("diff", "--name-only", "--", *preflight.C0B4_HASHES).splitlines()))
        changed |= set(filter(None, git("diff", "--cached", "--name-only", "--", *preflight.C0B4_HASHES).splitlines()))
        self.assertEqual(changed, set())

    def test_03_frozen_data_is_byte_identical(self) -> None:
        for relative, expected in preflight.FROZEN_DATA_HASHES.items():
            actual = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
            self.assertEqual(actual, expected, relative)

    def test_04_exact_seven_file_c0b5_scope(self) -> None:
        tracked = set(filter(None, git("diff", "--name-only").splitlines()))
        tracked |= set(filter(None, git("diff", "--cached", "--name-only").splitlines()))
        untracked = {
            line.replace("\\", "/")
            for line in git("ls-files", "--others", "--exclude-standard").splitlines()
            if line
        }
        self.assertEqual(tracked, set())
        self.assertEqual(untracked, preflight.AUTHORIZED_SCOPE)

    def test_05_artifact_schemas_are_exact(self) -> None:
        self.assertEqual(self.registry_columns, preflight.REGISTRY_COLUMNS)
        self.assertEqual(self.route_columns, preflight.ROUTE_COLUMNS)
        self.assertEqual(self.portfolio_columns, preflight.PORTFOLIO_COLUMNS)

    def test_06_evidence_registry_ids_and_domains(self) -> None:
        ids = [row["EVIDENCE_ID"] for row in self.registry]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(ids, [f"C0B5-E{number:03d}" for number in range(1, 12)])
        self.assertTrue(all(row["EVIDENCE_DOMAIN"] in preflight.ALLOWED_EVIDENCE_DOMAINS for row in self.registry))

    def test_07_route_hierarchy_is_exact(self) -> None:
        self.assertEqual(self.config["route_hierarchy"]["test_order"], ["ROUTE_A", "ROUTE_B", "ROUTE_C"])
        self.assertFalse(self.config["route_hierarchy"]["preference_scoring_used"])
        self.assertFalse(self.config["route_hierarchy"]["ad_hoc_hybrid_used"])

    def test_08_one_and_only_one_route_is_selected(self) -> None:
        selected = [row for row in self.routes if row["AUTHORIZATION_STATUS"] == "SELECTED"]
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0]["ROUTE_ID"], "ROUTE_B")
        self.assertEqual(self.config["route_hierarchy"]["selected_routes_n"], 1)

    def test_09_route_a_cannot_pass_without_baseline_and_domain(self) -> None:
        route = self.config["route_a"]
        self.assertEqual(route["status"], "NOT_SUPPORTED")
        self.assertEqual(route["baseline_status"], "OFFICIAL_NON_DISTRICT_BASELINE_NOT_USABLE")
        self.assertEqual(route["adjustment_rule_status"], "NOT_AVAILABLE")
        self.assertFalse(route["district_crop_numerical_baseline_available"])
        self.assertFalse(route["model_admissible_numerical_adjustment_rule_available"])
        self.assertFalse(route["operationally_numerical_before_optimization"])

    def test_10_prospective_sources_do_not_become_district_values(self) -> None:
        search = self.config["targeted_official_evidence_search"]
        self.assertTrue(search["enis_2026_2027_exists"])
        self.assertTrue(search["enis_crops_include_rice"])
        self.assertTrue(search["enis_crops_include_mad"])
        self.assertFalse(search["public_numeric_piura_district_rice_table_identified"])
        self.assertFalse(search["public_numeric_piura_district_mad_table_identified"])
        self.assertFalse(search["regional_or_national_values_disaggregated_to_districts"])

    def test_11_planting_intention_firewall(self) -> None:
        firewall = self.config["official_planning_evidence_firewall"]
        self.assertTrue(all(value is False for value in firewall.values()))

    def test_12_campaign_candidate_universe_is_exact(self) -> None:
        finite = self.config["finite_portfolio_selection"]
        self.assertEqual(finite["campaign_candidate_start_years"], list(range(2015, 2024)))
        self.assertEqual(finite["candidate_configurations_n"], 9)
        self.assertEqual(len(self.portfolio), 9)

    def test_13_scope_selection_recomputes(self) -> None:
        selection = preflight.compute_scope_selection()
        self.assertEqual(selection["authorized_districts_n"], 13)
        self.assertEqual(selection["seed_years"], (2020, 2023))
        self.assertEqual(selection["admitted_years"], (2020, 2023))

    def test_14_coverage_maximum_is_unique(self) -> None:
        monthly = preflight.transient_monthly_data()
        coverage = {
            year: preflight.joint_complete_districts(monthly, year)
            for year in preflight.CAMPAIGN_START_YEARS
        }
        pairs = []
        for years in itertools.combinations(preflight.CAMPAIGN_START_YEARS, 2):
            common = coverage[years[0]] & coverage[years[1]]
            pairs.append((len(common), years))
        maximum = max(count for count, _ in pairs)
        winners = [years for count, years in pairs if count == maximum]
        self.assertEqual(maximum, 13)
        self.assertEqual(winners, [(2020, 2023)])

    def test_15_supported_district_scope_is_exact(self) -> None:
        expected = {
            "200101", "200105", "200108", "200111", "200114", "200201",
            "200205", "200304", "200802", "200803", "200804", "200805", "200806",
        }
        actual = {
            item["ubigeo"] for item in self.config["finite_portfolio_selection"]["authorized_districts"]
        }
        self.assertEqual(actual, expected)
        self.assertFalse(self.config["finite_portfolio_selection"]["full_55_district_scope_supported"])

    def test_16_portfolio_audit_reproduces_from_raw(self) -> None:
        self.assertEqual(self.portfolio, preflight.build_portfolio_rows())

    def test_17_route_b_has_two_complete_alternatives(self) -> None:
        admitted = [
            row for row in self.portfolio
            if row["REFERENCE_CONFIGURATION_ADMISSIBILITY"] == "ADMISSIBLE_REFERENCE_CONFIGURATION"
        ]
        self.assertEqual(len(admitted), 2)
        self.assertEqual({row["SOURCE_CAMPAIGN"] for row in admitted}, {"2020/2021", "2023/2024"})
        self.assertTrue(all(row["RICE_NUMERIC_COMPLETE"] == "TRUE" for row in admitted))
        self.assertTrue(all(row["MAD_NUMERIC_COMPLETE"] == "TRUE" for row in admitted))

    def test_18_route_b_would_fail_below_two_alternatives(self) -> None:
        conditions = self.config["finite_portfolio_selection"]["authorization_conditions"]
        admitted_n = self.config["finite_portfolio_selection"]["admissible_configurations_n"]
        self.assertEqual(conditions["B2_at_least_two_distinct_alternatives"], admitted_n >= 2)
        self.assertGreaterEqual(admitted_n, 2)

    def test_19_no_missing_value_is_converted_to_zero(self) -> None:
        self.assertTrue(all(row["MISSING_AS_ZERO_USED"] == "FALSE" for row in self.portfolio))
        synthetic = {}
        self.assertIsNone(preflight.complete_campaign_values(synthetic, "200101", "14010020000", 2020))

    def test_20_explicit_zero_semantics_are_preserved(self) -> None:
        synthetic = {}
        for month in preflight.CAMPAIGN_MONTHS:
            year = 2020 if month >= 8 else 2021
            synthetic[("200101", "14010020000", year * 100 + month)] = Decimal(0)
        values = preflight.complete_campaign_values(synthetic, "200101", "14010020000", 2020)
        self.assertEqual(values, [Decimal(0)] * 12)

    def test_21_admitted_timing_profiles_are_complete_and_positive(self) -> None:
        selection = preflight.compute_scope_selection()
        scope = [code for code, _ in selection["authorized_districts"]]
        monthly = preflight.transient_monthly_data()
        for year in selection["admitted_years"]:
            for ubigeo in scope:
                for crop_code in preflight.TRANSIENT_CROPS:
                    values = preflight.complete_campaign_values(monthly, ubigeo, crop_code, year)
                    self.assertIsNotNone(values)
                    assert values is not None
                    self.assertEqual(len(values), 12)
                    self.assertGreater(sum(values), 0)

    def test_22_configuration_fingerprints_are_exact(self) -> None:
        expected = {
            "2020/2021": "d9d1481588d73535716b71de732586d0acf9f12e7316358aafb996de9845bc93",
            "2023/2024": "9750808bed2848863a5a739ce1d9209f6f46df9b6375485a749a1930eb97144e",
        }
        actual = {
            campaign: values["sha256"]
            for campaign, values in self.config["finite_portfolio_selection"]["configuration_fingerprints"].items()
        }
        self.assertEqual(actual, expected)

    def test_23_convex_interpolation_is_prohibited(self) -> None:
        finite = self.config["finite_portfolio_selection"]
        self.assertFalse(finite["convex_interpolation_authorized"])
        self.assertFalse(self.config["authorizations"]["convex_interpolation"])

    def test_24_district_mix_and_match_is_prohibited(self) -> None:
        finite = self.config["finite_portfolio_selection"]
        self.assertEqual(finite["district_mix_and_match_status"], "NOT_AUTHORIZED")
        self.assertTrue(all(row["DISTRICT_MIX_AND_MATCH"] == "FALSE" for row in self.portfolio))
        self.assertFalse(self.config["authorizations"]["district_mix_and_match"])

    def test_25_historical_realization_is_not_future_feasibility(self) -> None:
        self.assertTrue(all(row["EMPIRICALLY_REALIZED"] == "TRUE" for row in self.portfolio))
        self.assertTrue(all(row["FUTURE_PHYSICAL_FEASIBILITY_CLAIM"] == "FALSE" for row in self.portfolio))
        self.assertFalse(self.config["finite_portfolio_selection"]["future_physical_feasibility_claim_allowed"])

    def test_26_fixed_perennials_remain_fixed(self) -> None:
        perennial = self.config["perennial_firewall"]
        self.assertEqual(perennial["resolution"], "P3_FIXED_STOCK_NEAR_TERM_HORIZON")
        self.assertFalse(perennial["mango_altered_by_transient_alternatives"])
        self.assertFalse(perennial["limon_altered_by_transient_alternatives"])
        self.assertFalse(perennial["banana_altered_by_transient_alternatives"])
        self.assertFalse(perennial["historical_perennial_stock_imported_into_alternatives"])

    def test_27_perennial_baseline_remains_a_separate_gate(self) -> None:
        perennial = self.config["perennial_firewall"]
        self.assertTrue(perennial["baseline_initialization_authorized_by_c0b3"])
        self.assertEqual(
            perennial["baseline_numeric_status"],
            "NOT_YET_NUMERICALLY_FROZEN_SEPARATE_INITIALIZATION_GATE",
        )

    def test_28_no_water_claim_or_model(self) -> None:
        self.assertTrue(all(row["WATER_FEASIBILITY_CLAIM"] == "FALSE" for row in self.portfolio))
        self.assertFalse(self.config["authorizations"]["water_model"])
        self.assertFalse(self.config["authorizations"]["water_hard_constraint"])
        self.assertFalse(self.config["firewalls"]["water_feasibility_claimed"])

    def test_29_no_outcome_field_enters_selection_computation(self) -> None:
        source = inspect.getsource(preflight.transient_monthly_data)
        tree = ast.parse(source)
        keys = {
            node.slice.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Subscript)
            and isinstance(node.slice, ast.Constant)
            and isinstance(node.slice.value, str)
        }
        self.assertEqual(keys, {"COD_CULTIVO", "UBIGEO", "MES", "SIEMBRA"})
        forbidden = set(self.config["input_firewall"]["forbidden_route_selection_inputs"])
        self.assertTrue(forbidden.isdisjoint(self.config["input_firewall"]["allowed_rule_inputs"]))

    def test_30_no_optimization_or_ranking_is_executed(self) -> None:
        route_b = self.config["route_b"]
        self.assertFalse(route_b["continuous_crop_allocation_optimization"])
        self.assertFalse(route_b["finite_alternative_ranking_executed_in_c0b5"])
        self.assertIsNone(route_b["selected_alternative"])
        self.assertFalse(self.config["authorizations"]["continuous_optimizer"])
        self.assertFalse(self.config["authorizations"]["finite_optimizer_or_ranking"])
        self.assertFalse(self.config["authorizations"]["economic_objective"])

    def test_31_route_b_conditions_all_pass(self) -> None:
        conditions = self.config["finite_portfolio_selection"]["authorization_conditions"]
        self.assertEqual(set(conditions), {f"B{number}_{suffix}" for number, suffix in [
            (1, "outcome_independent_inclusion_rule"),
            (2, "at_least_two_distinct_alternatives"),
            (3, "numerically_fully_specified_for_authorized_scope"),
            (4, "no_missing_to_zero"),
            (5, "no_convex_interpolation"),
            (6, "no_district_mix_and_match"),
            (7, "reference_not_guaranteed_future_feasible"),
            (8, "fixed_perennials_remain_fixed"),
            (9, "no_water_feasibility_claim"),
            (10, "alternatives_fixed_before_downstream_evaluation"),
        ]})
        self.assertTrue(all(conditions.values()))

    def test_32_selected_architecture_is_consistent(self) -> None:
        selected = preflight.SELECTED_ARCHITECTURE
        self.assertEqual(self.config["selected_decision_architecture"], selected)
        self.assertEqual(self.config["final_architecture_verdict"], selected)
        self.assertIn(f"SELECTED_DECISION_ARCHITECTURE={selected}", self.report)
        selected_csv = [row for row in self.routes if row["AUTHORIZATION_STATUS"] == "SELECTED"]
        self.assertEqual(
            selected_csv[0]["ROUTE_NAME"],
            "FINITE_PRESPECIFIED_EMPIRICALLY_REALIZED_REFERENCE_CONFIGURATION_ANALYSIS",
        )

    def test_33_rq_compatibility_and_action_are_recorded(self) -> None:
        rq = self.config["research_question_compatibility"]
        self.assertEqual(rq["status"], "CURRENT_RQ_REQUIRES_MATERIAL_REFRAMING")
        self.assertFalse(rq["current_working_title_compatible"])
        self.assertIn("PRESPECIFIED_EMPIRICALLY_REALIZED_REFERENCE_CONFIGURATIONS", rq["required_action"])
        self.assertFalse(rq["upstream_file_edited"])

    def test_34_zero_land_parameters_and_adjustment_bounds(self) -> None:
        self.assertEqual(self.config["model_authorized_land_parameters_n"], 0)
        self.assertEqual(self.config["model_authorized_adjustment_bounds_n"], 0)
        self.assertFalse(self.config["firewalls"]["area_ha_used_as_rescued_capacity"])
        self.assertFalse(self.config["firewalls"]["arbitrary_percentage_bound_used"])

    def test_35_preflight_semantic_coverage_is_complete(self) -> None:
        required = {
            "AREA_HA_RESCUED_CAPACITY", "ARBITRARY_PERCENTAGE_BOUNDS",
            "HISTORICAL_EXTREMA_AS_MODEL_BOUNDS", "HISTORICAL_CONVEX_HULL_AS_CONTINUOUS_DOMAIN",
            "RICE_MAD_FIXED_TOTAL_WITHOUT_SUBSTITUTION_EVIDENCE", "OUTCOME_TUNED_BASELINE",
            "OUTCOME_TUNED_ALTERNATIVES", "ENSO_YEAR_SELECTION",
            "HIGH_YIELD_OR_HIGH_PROFIT_YEAR_SELECTION", "MISSING_AS_ZERO",
            "DISTRICT_MIX_AND_MATCH", "HISTORICAL_REALIZATION_AS_GUARANTEED_FUTURE_FEASIBILITY",
            "HISTORICAL_PERENNIAL_STOCK_IMPORT", "WATER_FEASIBILITY_CLAIM",
            "CONTINUOUS_OPTIMIZATION_AFTER_ROUTE_A_FAILURE", "FINITE_RANKING_OR_OPTIMIZATION_IN_C0B5",
            "MULTIPLE_SELECTED_ROUTES", "NO_SELECTED_ROUTE", "C0B4_MODIFICATION",
            "OLD_ROUTE_B_ARCHITECTURE_LABEL", "DECISION_ANALYSIS_IMPLIES_FUTURE_FEASIBILITY",
            "HISTORICAL_REALIZATION_EQUALS_FUTURE_FEASIBILITY", "REPRESENTATIVE_PIURA_CLAIM",
            "ALTERNATIVE_INTERPOLATION", "CROP_YEAR_MIXING", "TIMING_PROFILE_MIXING",
            "GENERIC_T3_FROM_ALTERNATIVE_TIMING", "ARBITRARY_K2_SELECTION",
            "LEXICOGRAPHIC_TIEBREAK_FALSELY_INVOKED", "UNFROZEN_ALTERNATIVE_OR_SCOPE",
        }
        self.assertEqual(preflight.SEMANTIC_REJECTION_GATES, required)

    def test_36_report_has_22_required_sections_in_order(self) -> None:
        sections = [f"## {number}." for number in range(1, 23)]
        positions = [self.report.index(section) for section in sections]
        self.assertEqual(positions, sorted(positions))

    def test_37_report_records_required_firewalls(self) -> None:
        for token in (
            "NO_OUTCOME_LEAKAGE_GATE=PASS",
            "NO_INVENTED_CAPACITY_GATE=PASS",
            "NO_WATER_MODEL_GATE=PASS",
            "NO_OPTIMIZATION_EXECUTED_GATE=PASS",
            "FINITE_SCENARIO_EVALUATION == CONTINUOUS_CROP_ALLOCATION_OPTIMIZATION",
        ):
            self.assertIn(token, self.report)

    def test_38_c0b5_files_are_utf8_lf_with_one_final_lf(self) -> None:
        for relative in preflight.AUTHORIZED_SCOPE:
            raw = (ROOT / relative).read_bytes()
            self.assertFalse(raw.startswith(b"\xef\xbb\xbf"), relative)
            self.assertNotIn(b"\r", raw, relative)
            self.assertTrue(raw.endswith(b"\n"), relative)
            self.assertFalse(raw.endswith(b"\n\n"), relative)

    def test_39_required_next_gate_cannot_change_alternatives(self) -> None:
        gate = self.config["required_next_gate"]
        self.assertTrue(gate["required"])
        self.assertFalse(gate["may_change_frozen_alternative_membership_retroactively"])
        self.assertIn("FORMAL_RESEARCH_QUESTION_AND_MANUSCRIPT_REFRAMING", gate["items"])

    def test_40_reference_configuration_labels_are_exact(self) -> None:
        self.assertEqual(self.config["selected_decision_architecture"], preflight.SELECTED_ARCHITECTURE)
        self.assertEqual(
            self.config["route_b"]["short_analytical_label"],
            preflight.SHORT_ANALYTICAL_LABEL,
        )
        self.assertEqual(
            self.config["finite_risk_aware_reference_configuration_analysis_status"],
            "SUPPORTED_ARCHITECTURE_PENDING_DOWNSTREAM_GATES",
        )

    def test_41_future_feasibility_firewall_is_explicit(self) -> None:
        route_b = self.config["route_b"]
        self.assertEqual(route_b["historical_realization_status"], "CERTIFIED_BY_SOURCE_OBSERVATION")
        self.assertEqual(route_b["prospective_physical_feasibility_status"], "NOT_CERTIFIED")
        self.assertEqual(route_b["prospective_institutional_feasibility_status"], "NOT_CERTIFIED")
        self.assertEqual(
            route_b["reference_configuration_role"],
            "EMPIRICALLY_REALIZED_COMPARATOR_FOR_PROSPECTIVE_RISK_STRESS_TESTING",
        )

    def test_42_primary_reference_ids_and_campaigns_are_exact(self) -> None:
        finite = self.config["finite_portfolio_selection"]
        expected = [
            {"alternative_id": "C0B5-A2020-2021", "source_campaign": "2020/2021"},
            {"alternative_id": "C0B5-A2023-2024", "source_campaign": "2023/2024"},
        ]
        self.assertEqual(finite["primary_reference_configurations_n"], 2)
        self.assertEqual(finite["primary_reference_configurations"], expected)

    def test_43_common_support_semantics_and_representativeness_are_exact(self) -> None:
        finite = self.config["finite_portfolio_selection"]
        self.assertEqual(finite["authorized_districts_n"], 13)
        self.assertEqual(
            tuple((item["ubigeo"], item["district_name"]) for item in finite["authorized_districts"]),
            preflight.EXPECTED_DISTRICTS,
        )
        self.assertEqual(
            finite["spatial_scope_semantics"],
            "COVERAGE_QUALIFIED_COMMON_SUPPORT_SUBREGIONAL_SCOPE",
        )
        self.assertEqual(finite["representativeness_status"], "NOT_ESTABLISHED")

    def test_44_numeric_and_timing_completeness_are_exact(self) -> None:
        finite = self.config["finite_portfolio_selection"]
        self.assertEqual(finite["expected_numeric_cells"], 52)
        self.assertEqual(finite["observed_complete_numeric_cells"], 52)
        self.assertEqual(finite["missing_numeric_cells"], 0)
        self.assertFalse(finite["silent_missing_to_zero_used"])
        self.assertEqual(
            finite["alternative_timing_profiles_complete"],
            {"C0B5-A2020-2021": "26/26", "C0B5-A2023-2024": "26/26"},
        )

    def test_45_no_mixing_and_no_generic_t3_inference(self) -> None:
        finite = self.config["finite_portfolio_selection"]
        self.assertFalse(finite["district_mix_and_match_detected"])
        self.assertFalse(finite["crop_year_mixing_detected"])
        self.assertFalse(finite["timing_profile_mixing_detected"])
        self.assertEqual(
            finite["observed_alternative_timing_profile_status"],
            "SUPPORTED_ALTERNATIVE_SPECIFIC_ONLY_NO_GENERIC_T3_RULE",
        )

    def test_46_coverage_frontier_and_selection_rationale_recompute(self) -> None:
        finite = self.config["finite_portfolio_selection"]
        self.assertEqual(preflight.compute_coverage_frontier(), preflight.EXPECTED_COVERAGE_FRONTIER)
        primary = finite["coverage_frontier"][0]
        self.assertEqual((primary["configurations_n"], primary["max_common_districts_n"]), (2, 13))
        self.assertEqual(
            finite["maximize_spatial_coverage_first_status"],
            "PROSPECTIVELY_RESEARCHER_DEFINED_BUT_OUTCOME_INDEPENDENT",
        )
        self.assertFalse(finite["lexicographic_tiebreak_actually_invoked"])
        self.assertEqual(
            finite["why_exactly_two"],
            "ONLY_TWO_CONFIGURATIONS_SATISFY_THE_UNIQUE_MAXIMUM_13_DISTRICT_COMMON_SUPPORT",
        )

    def test_47_numeric_distinctness_recomputes(self) -> None:
        diagnostics = preflight.compute_reference_diagnostics()
        self.assertEqual(diagnostics["alternative_l1_distance_ha"], 12100)
        self.assertEqual(diagnostics["alternative_different_cells_n"], 26)
        self.assertEqual(diagnostics["alternative_equal_cells_n"], 0)
        self.assertEqual(diagnostics["timing_different_profiles_n"], 26)
        numeric = self.config["finite_portfolio_selection"]["alternative_numeric_diagnostics"]
        self.assertEqual(
            [numeric[key] for key in (
                "alternative_1_rice_ha", "alternative_1_mad_ha",
                "alternative_2_rice_ha", "alternative_2_mad_ha",
            )],
            [15213, 5704, 22592, 5937],
        )
        self.assertEqual(numeric["alternative_numeric_distinctness_status"], "MATERIALLY_DISTINCT")
        self.assertEqual(
            numeric["alternative_timing_distinctness_status"],
            "BOTH_AREA_AND_TIMING_CONFIGURATIONS_DIFFER",
        )

    def test_48_information_depth_and_rq_reframing_are_explicit(self) -> None:
        finite = self.config["finite_portfolio_selection"]
        rq = self.config["research_question_compatibility"]
        self.assertEqual(finite["route_b_information_depth"], "THIN_BUT_USABLE")
        self.assertEqual(rq["status"], "CURRENT_RQ_REQUIRES_MATERIAL_REFRAMING")
        self.assertEqual(rq["rq_rewording_status"], "REQUIRED_BEFORE_MANUSCRIPT_FREEZE")

    def test_49_route_b_and_downstream_firewalls_are_exact(self) -> None:
        route_b = self.config["route_b"]
        perennial = self.config["perennial_firewall"]
        self.assertEqual(route_b["route_b_architecture_status"], "SUPPORTED")
        self.assertEqual(route_b["exact_2_configuration_13_district_scope_status"], "SUPPORTED")
        self.assertTrue(all(self.config["finite_portfolio_selection"]["authorization_conditions"].values()))
        self.assertFalse(perennial["perennial_initialization_blocks_c0b5_architecture_freeze"])
        self.assertTrue(perennial["perennial_initialization_blocks_full_reference_configuration_scenario_evaluation"])
        self.assertEqual(self.config["model_authorized_land_parameters_n"], 0)
        self.assertEqual(self.config["model_authorized_adjustment_bounds_n"], 0)
        self.assertEqual(self.config["water_model"], "NOT_AUTHORIZED")
        self.assertFalse(self.config["authorizations"]["water_model"])
        self.assertFalse(self.config["authorizations"]["continuous_optimizer"])

    def test_50_preflight_passes(self) -> None:
        lines = preflight.run_preflight()
        self.assertIn("C0B4_IMMUTABILITY_GATE=PASS", lines)
        self.assertIn("PERSISTENT_SCOPE_GATE=PASS", lines)
        self.assertIn("C0B5_PREFLIGHT=PASS", lines)


if __name__ == "__main__":
    unittest.main()
