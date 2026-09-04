from __future__ import annotations

import ast
import copy
import csv
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import er2_robustness_protocol_v1 as er2p


class ER2RobustnessProtocolV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.protocol = er2p.build_protocol()
        cls.tiers = {t["tier"]: t for t in cls.protocol["tiers"]}
        cls.outputs = er2p.render_outputs()

    def test_01_exact_er1_and_ed1_freezes(self):
        result = er2p.preflight()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["er1_freeze_sha"], "43de46ecd46248f1e4e2822a30e69cfadbc8260f")
        self.assertEqual(result["ed1_freeze_sha"], "ed1c7cb79e7842356abd41f7a7af60d2fac1b5a6")

    def test_02_frozen_dependencies_unchanged(self):
        self.assertEqual(er2p.verify_frozen_inputs(), er2p.FROZEN_HASHES)
        self.assertEqual(len(er2p.FROZEN_HASHES), 32)

    def test_03_numerical_identity_reconstructed_from_three_csvs(self):
        lock = er2p.read_json(er2p.ER1_LOCK_REL)
        mapping = {p: er2p.sha256_file(ROOT / p) for p in lock["result_table_sha256"]}
        payload = json.dumps(mapping, sort_keys=True, separators=(",", ":")).encode("utf-8")
        self.assertEqual(len(mapping), 3)
        self.assertEqual(er2p.sha256_bytes(payload), "40e0f58269dda309e83a1fa3da17ef4d5dc5523efc72a666f734d0ebacb76b24")

    def test_04_reporting_identity_exact(self):
        self.assertEqual(er2p.sha256_file(ROOT / er2p.ER1_LOCK_REL),
                         "83eea5e179b5e3504bd1144d744dcdbeddbbdf6a554f4d10ab03b92a30278841")

    def test_05_timing_disclosure_is_not_retrospectively_blind(self):
        timing = self.protocol["timing"]
        self.assertIs(timing["primary_results_known"], True)
        self.assertIs(timing["robustness_results_known"], False)
        self.assertIs(timing["outcome_unsealed"], True)
        self.assertFalse(timing["claim_all_operational_details_were_pre_outcome"])
        self.assertEqual(timing["robustness_hierarchy_timing"], "PRE_OUTCOME_FROZEN_IN_ED1")
        self.assertEqual(timing["robustness_operationalization_timing"], "POST_PRIMARY_RESULTS_PRE_ROBUSTNESS_RESULTS")

    def test_06_ed1_hierarchy_and_crop_contracts_are_unchanged(self):
        ed1 = er2p.read_json(er2p.ED1_CONFIG_REL)
        self.assertEqual(self.protocol["ed1_hierarchy_unchanged"], ed1["robustness_hierarchy"])
        self.assertEqual(self.protocol["crop_model_contracts"], ed1["crop_model_contracts"])

    def test_07_exact_r1_to_r6_order(self):
        self.assertEqual(self.protocol["robustness_order"], [
            "R1_LEVEL_CLIMATE_FAMILY", "R2_STANDARDIZED_ANOMALY_COMPARABILITY",
            "R3_RESTRICTED_WILD_CLUSTER_BOOTSTRAP", "R4_SPATIAL_HAC",
            "R5_LEAVE_ONE_PERIOD_OUT_ALL_PERIODS", "R6_B3_STRICT_EXPOSURE"])
        self.assertEqual([t["order"] for t in self.protocol["tiers"]], list(range(1, 7)))

    def test_08_lock_every_tier_before_the_next(self):
        governance = self.protocol["tier_lock_governance"]
        self.assertEqual(governance["locking"], "MANDATORY_BEFORE_NEXT_TIER")
        self.assertEqual(governance["sequence"], [v for i in range(1, 7) for v in (f"EXECUTE_R{i}", f"LOCK_R{i}")])
        self.assertEqual(governance["cross_contamination"], "PROHIBITED")

    def test_09_primary_replacement_prohibited_everywhere(self):
        self.assertEqual(self.protocol["tier_lock_governance"]["primary_replacement"], "PROHIBITED")
        self.assertTrue(all(t["primary_replacement"] == "PROHIBITED" for t in self.protocol["tiers"]))

    def test_10_r1_only_two_distinct_transient_models(self):
        t = self.tiers["R1"]
        self.assertEqual(t["distinct_crops"], ["14010020000", "14010070000"])
        self.assertEqual((t["distinct_models"], t["distinct_coefficients"]), (2, 6))
        self.assertTrue(t["same_primary_sample"])

    def test_11_r1_perennial_equivalence_not_extra_robustness(self):
        t = self.tiers["R1"]
        self.assertEqual(t["diagnostic_crops"], ["13010210000", "13010170102", "15010040000"])
        self.assertEqual(t["perennial_status_on_exact_equivalence"], "FE_EQUIVALENT_DIAGNOSTIC_NOT_DISTINCT_MODEL")
        e = t["perennial_equivalence"]
        self.assertEqual(e["distinct_robustness_count_contribution"], 0)
        self.assertTrue(e["exact_coefficient_and_fitted_value_equality_required_for_status"])
        self.assertTrue(e["record_exact_equality_separately_from_tolerance_diagnostic"])
        self.assertEqual(e["ed1_design_absolute_tolerance"], 1e-9)
        self.assertIn("HOLD_FOR_ADJUDICATION", e["on_nonexact_equality"])

    def test_12_r1_level_regressors_and_inference(self):
        t = self.tiers["R1"]
        self.assertEqual(t["regressors"], ["RAIN_MM", "TMAX_C", "TMIN_C"])
        self.assertEqual(t["inference"], "CR2_SATTERTHWAITE_AND_CROP_AHT")
        self.assertEqual(t["weighting"], "UNWEIGHTED_PRIMARY_ESTIMATION")

    def test_13_r1_holm_is_within_crop_only_not_adjusted_intervals(self):
        t = self.tiers["R1"]
        self.assertEqual(t["multiplicity"], "HOLM_STEP_DOWN_WITHIN_CROP_R1_COEFFICIENT_P_VALUES")
        self.assertEqual(t["confidence_intervals"], "UNADJUSTED_95_PERCENT_CR2_SATTERTHWAITE")
        self.assertEqual(t["global_five_crop_fwer"], "NOT_CLAIMED")
        self.assertEqual(t["multiplicity_adjusted_confidence_intervals"], "NOT_CONSTRUCTED_NOT_CLAIMED")

    def test_14_r2_exact_all_crop_design(self):
        t = self.tiers["R2"]
        self.assertEqual((t["models"], t["coefficient_count"]), (5, 21))
        self.assertEqual(t["regressors"], ["RAIN_Z", "TMAX_Z", "TMIN_Z"])
        self.assertEqual(t["time_variants"], "EXACT_ED1_T_AND_T_MINUS_1_WHERE_APPLICABLE")
        self.assertTrue(t["same_primary_sample"])

    def test_15_r2_native_yield_unit_interpretation_not_crop_ranking(self):
        t = self.tiers["R2"]
        self.assertEqual(t["interpretation"], "ONE_LOCAL_CLIMATE_SD_CHANGE_IN_NATIVE_CROP_YIELD_UNITS")
        self.assertEqual(t["fully_standardized_effect_sizes"], "NOT_CLAIMED")
        self.assertEqual(t["cross_crop_magnitude_ranking"], "PROHIBITED")
        self.assertEqual(t["cross_crop_significance_ranking"], "PROHIBITED")

    def test_16_r2_multiplicity(self):
        self.assertEqual(self.tiers["R2"]["multiplicity"], "HOLM_STEP_DOWN_WITHIN_CROP_R2_COEFFICIENT_P_VALUES")
        self.assertEqual(self.tiers["R2"]["global_five_crop_fwer"], "NOT_CLAIMED")

    def test_17_r3_exact_bootstrap_contract(self):
        t = self.tiers["R3"]
        self.assertEqual((t["replications"], t["seed"], t["weights"]), (9999, 20260903, "RADEMACHER"))
        self.assertTrue(t["restricted"])
        self.assertTrue(t["null_imposed"])
        self.assertEqual(t["cluster"], "DISTRICT")
        self.assertEqual(t["finite_replication_correction"], "(1 + exceedances)/(B + 1)")

    def test_18_r3_all_twenty_one_primary_coefficients(self):
        t = self.tiers["R3"]
        self.assertEqual(t["role"], "INFERENCE_ONLY")
        self.assertEqual(t["coefficients"], "EXACT_ER1_PRIMARY_UNCHANGED")
        self.assertEqual(t["coefficient_tests"], 21)
        self.assertEqual(t["reported_fields"], ["ER1_BETA_REFERENCE", "ER1_CR2_P_REFERENCE", "WCR_P", "WITHIN_CROP_HOLM_WCR_P"])

    def test_19_r3_holm_never_mixes_cr2_and_wcr(self):
        self.assertEqual(self.tiers["R3"]["multiplicity"], "WITHIN_CROP_WCR_COEFFICIENT_P_VALUES")
        self.assertEqual(self.tiers["R3"]["mixed_cr2_wcr_holm_family"], "PROHIBITED")

    def test_20_r3_five_joint_tests_preserve_aht_null(self):
        t = self.tiers["R3"]
        self.assertEqual(t["joint_tests"], 5)
        self.assertEqual(t["joint_null"], "ALL_PRIMARY_CLIMATE_COEFFICIENTS_EQUAL_ZERO_WITHIN_CROP")
        self.assertEqual(t["joint_statistic"], "BOOTSTRAP_WALD_F")
        self.assertTrue(t["joint_null_matches_aht"])

    def test_21_r3_deterministic_stream_and_named_contrast_adapter(self):
        d = self.tiers["R3"]["determinism"]
        self.assertEqual(d["rng"], "NUMPY_GENERATOR_PCG64")
        self.assertEqual(d["batch_size"], 1000)
        self.assertEqual(d["seed_reset"], "EACH_CROP_CONTRAST_AND_JOINT_TEST")
        self.assertEqual(d["cluster_order"], "SORTED_UBIGEO")
        self.assertIn("each named coefficient", self.tiers["R3"]["implementation_requirement"])
        self.assertIn("synthetic data", self.tiers["R3"]["implementation_requirement"])

    def test_22_r3_invalid_draws_cannot_change_denominator(self):
        self.assertEqual(self.tiers["R3"]["invalid_replications"],
                         "REQUIRE_ZERO_OTHERWISE_HOLD_NO_DROPPING_OR_REDRAWING_OR_DENOMINATOR_CHANGE")

    def test_23_r4_spatial_contract(self):
        t = self.tiers["R4"]
        self.assertEqual(t["bandwidths_km"], [50, 100, 150])
        self.assertEqual(t["kernel"], "BARTLETT")
        self.assertEqual(t["coordinates"], "EPSG:32717_DISTRICT_CENTROIDS")
        self.assertEqual(t["pairing"], "SAME_PERIOD_ONLY")
        self.assertEqual(t["bandwidth_selection"], "PROHIBITED")

    def test_24_r4_asymptotic_inference_not_satterthwaite(self):
        t = self.tiers["R4"]
        self.assertEqual(t["role"], "ASYMPTOTIC_SPATIAL_HAC_ROBUSTNESS_DIAGNOSTIC")
        self.assertEqual(t["normal_critical_value"], 1.959963984540054)
        self.assertEqual(t["coefficient_bandwidth_rows"], 63)
        self.assertEqual(t["satterthwaite_df"], "NOT_CLAIMED")
        self.assertFalse(t["replaces_primary_cr2"])

    def test_25_r4_raw_p_values_no_bandwidth_holm_families(self):
        t = self.tiers["R4"]
        self.assertEqual(t["multiplicity"], "DIAGNOSTIC_ROBUSTNESS_NO_NEW_CONFIRMATORY_FWER_CLAIM")
        self.assertEqual(t["p_values"], "RAW_ALL_THREE_BANDWIDTHS_NO_SEPARATE_HOLM_FAMILIES")

    def test_26_r5_exact_thirty_eight_omissions(self):
        t = self.tiers["R5"]
        self.assertEqual(t["expected_models_by_crop"], {
            "14010020000": 7, "14010070000": 7, "13010210000": 8, "13010170102": 8, "15010040000": 8})
        self.assertEqual(t["expected_models"], 38)
        self.assertEqual(sum(t["expected_models_by_crop"].values()), 38)

    def test_27_r5_all_periods_and_named_2017_2023(self):
        t = self.tiers["R5"]
        self.assertTrue(t["report_all_periods"])
        self.assertEqual(t["mandatory_named_reporting"], ["LEAVE_2017_OUT", "LEAVE_2023_OUT"])
        self.assertEqual(t["named_transient_mapping"], {"LEAVE_2017_OUT": "2016/2017", "LEAVE_2023_OUT": "2022/2023"})
        self.assertEqual(t["named_perennial_mapping"], {"LEAVE_2017_OUT": "2017", "LEAVE_2023_OUT": "2023"})

    def test_28_r5_preserves_model_and_omits_only_one_period(self):
        t = self.tiers["R5"]
        self.assertEqual(t["family"], "PHYSICAL_ANOMALY")
        self.assertTrue(t["same_regressors"])
        self.assertEqual(t["remaining_period_fe"], "REQUIRED")
        self.assertEqual(t["second_period_omission"], "PROHIBITED")
        self.assertEqual(t["influential_district_deletion"], "PROHIBITED")

    def test_29_r5_complete_descriptive_metrics(self):
        self.assertEqual(self.tiers["R5"]["summary_metrics"], [
            "PRIMARY_BETA_REFERENCE", "MIN_LOO_BETA", "MAX_LOO_BETA", "MEDIAN_LOO_BETA",
            "POSITIVE_COUNT", "NEGATIVE_COUNT", "SIGN_REVERSALS_RELATIVE_TO_PRIMARY",
            "MAX_ABSOLUTE_BETA_DEVIATION", "PERIOD_CAUSING_MAX_ABSOLUTE_DEVIATION"])

    def test_30_r5_no_arbitrary_stability_threshold(self):
        t = self.tiers["R5"]
        self.assertEqual(t["stability_classification"], "DESCRIPTIVE_NO_ARBITRARY_PASS_FAIL_THRESHOLD")
        self.assertEqual(t["sign_reversal_rule"], "PRODUCT_OF_LOO_AND_PRIMARY_BETA_STRICTLY_NEGATIVE")
        self.assertIn("ALL_TIED_PERIOD_IDS", t["max_deviation_tie_rule"])
        self.assertIn("NULL", t["zero_primary_sign_rule"])
        self.assertIn("HOLD_FOR_ADJUDICATION", t["failed_omission"])

    def test_31_r6_rice_strict_support_and_inadmissibility(self):
        rice = self.tiers["R6"]["rice"]
        self.assertEqual((rice["expected_observations"], rice["expected_districts"], rice["expected_periods"]), (31, 12, 7))
        self.assertEqual((rice["required_within_rank"], rice["coefficient_count"]), (3, 3))
        self.assertEqual(rice["status"], "ESTIMABLE_WITH_SEVERE_SUPPORT_LIMITATION")
        self.assertEqual(rice["on_inadmissibility"], "R6_RICE_NOT_INFERENTIALLY_ADMISSIBLE")
        self.assertFalse(rice["may_weaken_fe"])

    def test_32_r6_mad_not_estimated_or_substituted(self):
        mad = self.tiers["R6"]["mad"]
        self.assertEqual(mad["status"], "NOT_ESTIMABLE_UNDER_PRIMARY_DESIGN")
        self.assertFalse(mad["estimate"])
        self.assertEqual(mad["substitute_model"], "PROHIBITED")

    def test_33_r6_support_not_exposure_truth_claim(self):
        self.assertTrue(self.tiers["R6"]["prominent_support_comparison_to_er1"])
        self.assertFalse(self.tiers["R6"]["disagreement_proves_correct_exposure"])
        self.assertEqual(self.tiers["R6"]["perennials"], "NOT_APPLICABLE")

    def test_34_tier_lock_schema_required_identity_contract_results(self):
        fields = set(self.protocol["tier_lock_governance"]["required_fields"])
        self.assertTrue({
            "er1_freeze_sha", "ed1_freeze_sha", "tier_id", "exact_input_sha256",
            "exact_model_contract", "results", "interpretation_firewall", "next_tier_authorization_status",
            "previous_tier_lock_sha256", "er2p_protocol_sha256", "tier_contract_sha256"} <= fields)

    def test_35_lock_hash_alone_is_not_execution_authorization(self):
        g = self.protocol["tier_lock_governance"]
        self.assertEqual(g["initial_next_tier_authorization_status"], "NOT_AUTHORIZED")
        self.assertIn("SEPARATE_DIRECTOR_EXECUTION_AUTHORIZATION_REQUIRED", g["before_next_tier"])
        self.assertIn("PREDECESSOR_INPUT_AND_RESULT_ARTIFACT_HASHES_RECOMPUTE_EXACTLY", g["before_next_tier"])
        self.assertEqual(g["previous_lock"], "R1_NULL_R2_TO_R6_EXACT_PREDECESSOR_SHA256")

    def test_36_locked_tiers_immutable_without_extra_commit_requirement(self):
        g = self.protocol["tier_lock_governance"]
        self.assertEqual(g["post_lock_revision"], "PROHIBITED_NEW_SCIENTIFIC_GATE_REQUIRED_NO_OVERWRITE")
        self.assertTrue(g["one_controlled_session_permitted"])
        self.assertFalse(g["separate_commit_per_tier_required"])
        self.assertEqual(g["hash"], "SHA256_OF_EXACT_SERIALIZED_BYTES_EXTERNAL_TO_OWN_LOCK")

    def test_37_future_result_files_and_locks_are_not_created(self):
        paths = self.protocol["future_artifact_paths_not_created_in_er2p"]
        self.assertEqual(len(paths), 16)
        self.assertTrue(all(not (ROOT / p).exists() for p in paths))
        self.assertEqual(er2p.forbidden_result_paths(ROOT), [])

    def test_38_concordance_all_coefficients_no_zero_for_inapplicability(self):
        c = self.protocol["concordance"]
        self.assertEqual(c["rows"], "ALL_21_ER1_PRIMARY_COEFFICIENT_IDENTIFIERS")
        self.assertEqual(c["nonapplicability"], "EXPLICIT_STATUS_NOT_ZERO_OR_FAILED_ROBUSTNESS_VOTE")
        self.assertIn("R5_BETA_RANGE", c["fields"])
        self.assertIn("CONLEY_CI_ZERO_INCLUSION_50_100_150", c["fields"])

    def test_39_no_scores_or_vote_counting(self):
        c = self.protocol["concordance"]
        self.assertEqual(c["robustness_score"], "PROHIBITED")
        self.assertEqual(c["vote_counting"], "PROHIBITED")
        self.assertEqual(c["prohibited_summaries"], ["ROBUSTNESS_SCORE", "NUMBER_OF_SIGNIFICANT_MODELS", "MAJORITY_SIGNIFICANT", "5_OF_7_ROBUST"])

    def test_40_banana_and_lemon_cannot_expand_specification(self):
        f = self.protocol["result_specific_firewalls"]
        self.assertFalse(f["known_primary_results_may_change_contract"])
        self.assertEqual(f["banana"], "NO_SPECIAL_TESTS_NONLINEAR_TMIN_BANDWIDTH_OR_PERIOD_SELECTION")
        self.assertEqual(f["lemon"], "NO_SPECIAL_TESTS_OR_POST_PRIMARY_SPECIFICATION_EXPANSION")
        self.assertEqual(f["selection_by_p_sign_ci_fit_or_biological_narrative"], "PROHIBITED")

    def test_41_association_only_claim_ceiling(self):
        self.assertEqual(self.protocol["claim_ceiling"], "EMPIRICAL_ASSOCIATION_CLIMATE_RESPONSE_ONLY")
        self.assertTrue(all(t["claim_ceiling"] == self.protocol["claim_ceiling"] for t in self.protocol["tiers"]))

    def test_42_no_models_scenarios_gvp_cvar_a1a2_or_optimization(self):
        f = self.protocol["execution_firewall"]
        self.assertEqual(f["robustness_models_executed"], 0)
        self.assertFalse(f["primary_estimation_executed"])
        self.assertFalse(f["raw_outcome_values_parsed"])
        for key in (*er2p.TIER_ORDER, "ENSO_SCENARIOS", "GVP", "VAR_CVAR", "A1_A2", "OPTIMIZATION"):
            self.assertEqual(f[key], "NOT_EXECUTED")
        self.assertFalse(self.protocol["robustness_execution_authorized"])
        self.assertFalse(self.protocol["er2p_freeze_authorized"])

    def test_43_builder_has_no_econometric_import_or_engine_call(self):
        tree = ast.parse((ROOT / er2p.SCRIPT_REL).read_bytes())
        allowed = {"__future__", "argparse", "csv", "hashlib", "io", "json", "subprocess", "pathlib"}
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported.add(node.module)
        self.assertLessEqual(imported, allowed)
        calls = {node.func.attr for node in ast.walk(tree)
                 if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)}
        self.assertTrue(calls.isdisjoint({"fit_two_way_fe_cr2", "restricted_wild_cluster_bootstrap_t",
                                         "conley_covariance", "estimate_primary_models", "read_table", "read_parquet"}))

    def test_44_exact_five_candidate_paths(self):
        actual = set(er2p.git_text("ls-files", "--others", "--exclude-standard").splitlines())
        self.assertEqual(actual, {p.as_posix() for p in er2p.CANDIDATE_RELS})
        self.assertEqual(len(actual), 5)

    def test_45_protocol_outputs_utf8_lf_one_final_lf(self):
        for relative in er2p.CANDIDATE_RELS:
            actual = (ROOT / relative).read_bytes()
            if relative in self.outputs:
                self.assertEqual(actual, self.outputs[relative])
            self.assertNotIn(b"\r", actual)
            self.assertFalse(actual.startswith(b"\xef\xbb\xbf"))
            self.assertTrue(actual.endswith(b"\n"))
            self.assertFalse(actual.endswith(b"\n\n"))
            actual.decode("utf-8")

    def test_46_two_independent_protocol_builds_are_identical(self):
        with tempfile.TemporaryDirectory(prefix="er2p-one-") as first, tempfile.TemporaryDirectory(prefix="er2p-two-") as second:
            one = er2p.run(Path(first))
            two = er2p.run(Path(second))
            self.assertEqual(one, two)
            for relative in er2p.OUTPUT_RELS:
                self.assertEqual((Path(first) / relative).read_bytes(), (Path(second) / relative).read_bytes())
                self.assertEqual((ROOT / relative).read_bytes(), (Path(first) / relative).read_bytes())

    def test_47_check_only_never_writes(self):
        with patch.object(Path, "write_bytes", side_effect=AssertionError("check-only cannot write")):
            self.assertEqual(er2p.run(check_only=True)["mode"], "CHECK_ONLY")

    def test_48_existing_identical_artifacts_are_not_rewritten(self):
        with patch.object(Path, "write_bytes", side_effect=AssertionError("identical files cannot be rewritten")):
            self.assertEqual(er2p.run()["robustness_models_executed"], 0)

    def test_49_frozen_input_hash_drift_is_rejected(self):
        original = er2p.sha256_file
        def changed(path):
            return "0" * 64 if path == ROOT / er2p.ER1_LOCK_REL else original(path)
        with patch.object(er2p, "sha256_file", side_effect=changed):
            with self.assertRaisesRegex(RuntimeError, "UPSTREAM_IMMUTABILITY"):
                er2p.verify_frozen_inputs()

    def test_50_nested_forbidden_result_is_detected_case_insensitively(self):
        with tempfile.TemporaryDirectory(prefix="er2p-firewall-") as temporary:
            root = Path(temporary)
            path = root / "outputs/econometrics/nested/er2_r1_results_lock.json"
            path.parent.mkdir(parents=True)
            path.write_bytes(b"{}\n")
            self.assertEqual(er2p.forbidden_result_paths(root), ["outputs/econometrics/nested/er2_r1_results_lock.json"])

    def test_51_semantic_mutations_fail_validation(self):
        paths = [
            ("timing", "primary_results_known"), ("timing", "robustness_results_known"),
            ("robustness_execution_authorized",), ("er2p_freeze_authorized",),
            ("robustness_order",), ("tiers", 0, "distinct_crops"),
            ("tiers", 1, "interpretation"), ("tiers", 2, "replications"), ("tiers", 2, "seed"),
            ("tiers", 2, "multiplicity"), ("tiers", 3, "bandwidths_km"), ("tiers", 3, "normal_critical_value"),
            ("tiers", 4, "expected_models"), ("tiers", 4, "stability_classification"),
            ("tiers", 5, "rice", "may_weaken_fe"), ("tiers", 5, "mad", "estimate"),
            ("tier_lock_governance", "locking"), ("concordance", "vote_counting"),
            ("result_specific_firewalls", "known_primary_results_may_change_contract"),
        ]
        for path in paths:
            with self.subTest(path=path):
                mutated = copy.deepcopy(self.protocol)
                target = mutated
                for key in path[:-1]:
                    target = target[key]
                target[path[-1]] = "UNAUTHORIZED_MUTATION"
                with self.assertRaisesRegex(RuntimeError, "TIER_CONTRACT_INCONSISTENCY"):
                    er2p.validate_protocol(mutated)

    def test_52_nonpass_adjudication_rejects_new_missing_changed_or_duplicate(self):
        rows = self.protocol["full_suite_policy"]["accepted_inventory"]
        self.assertEqual(er2p.adjudicate_nonpasses(rows, self.protocol)["status"], "PASS")
        for altered in (
            rows[:-1], rows + [rows[0]],
            rows + [{"result": "FAIL", "test": "unexpected.new_test"}],
            [{**rows[0], "result": "FAIL" if rows[0]["result"] == "ERROR" else "ERROR"}, *rows[1:]],
        ):
            self.assertEqual(er2p.adjudicate_nonpasses(altered, self.protocol)["status"], "FAIL")

    def test_53_report_contains_exact_protocol_hash_and_timing(self):
        report = self.outputs[er2p.REPORT_REL].decode("utf-8")
        self.assertIn("PROTOCOL_SHA256=" + er2p.sha256_bytes(self.outputs[er2p.CONFIG_REL]), report)
        self.assertIn("after primary results and before robustness results", report)
        self.assertIn("ROBUSTNESS_RESULTS_KNOWN=FALSE", report)
        self.assertIn("An unchanged historical inventory is not an all-green test suite.", report)

    def test_54_tier_csv_hashes_exact_six_contracts(self):
        rows = list(csv.DictReader(io.StringIO(self.outputs[er2p.TIERS_REL].decode("utf-8"))))
        self.assertEqual(len(rows), 6)
        for row, tier in zip(rows, self.protocol["tiers"]):
            self.assertEqual(row["TIER"], tier["tier_id"])
            self.assertEqual(row["ER1_NUMERICAL_RESULTS_IDENTITY"], er2p.NUMERICAL_IDENTITY)
            self.assertEqual(row["EXECUTION_STATUS"], "NOT_EXECUTED")
            self.assertEqual(row["TIER_CONTRACT_SHA256"], er2p.sha256_bytes(er2p.json_bytes(tier)))

    def test_55_primary_result_values_are_not_copied_to_protocol(self):
        self.assertNotIn("primary_coefficients", self.protocol)
        self.assertNotIn("aht_joint_tests", self.protocol)
        self.assertFalse(self.protocol["execution_firewall"]["primary_numerical_results_copied_to_protocol"])
        for payload in self.outputs.values():
            for value in (b"-6.5645586917721594", b"0.0042059006200269294", b"0.13760490078583698"):
                self.assertNotIn(value, payload)

    def test_56_check_only_cli_read_only(self):
        before = {p: ((ROOT / p).read_bytes(), (ROOT / p).stat().st_mtime_ns) for p in er2p.CANDIDATE_RELS}
        result = subprocess.run([sys.executable, str(ROOT / er2p.SCRIPT_REL), "--check-only"],
                                cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        after = {p: ((ROOT / p).read_bytes(), (ROOT / p).stat().st_mtime_ns) for p in er2p.CANDIDATE_RELS}
        self.assertEqual(before, after)

    def test_57_no_robustness_execution_cli_option(self):
        result = subprocess.run([sys.executable, str(ROOT / er2p.SCRIPT_REL), "--execute-r1"],
                                cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("unrecognized arguments", result.stderr)
        self.assertEqual(er2p.forbidden_result_paths(ROOT), [])

    def test_58_historical_tracked_tree_and_index_unchanged(self):
        self.assertEqual(er2p.git_text("diff", "--name-only"), "")
        self.assertEqual(er2p.git_text("diff", "--cached", "--name-only"), "")
        self.assertEqual(er2p.git_text("rev-parse", "HEAD"), "43de46ecd46248f1e4e2822a30e69cfadbc8260f")

    def test_59_lifecycle_inventory_fifty_three_exact_categories(self):
        rows = self.protocol["full_suite_policy"]["accepted_inventory"]
        self.assertEqual(len(rows), 53)
        self.assertEqual(sum(r["result"] == "FAIL" for r in rows), 50)
        self.assertEqual(sum(r["result"] == "ERROR" for r in rows), 3)
        self.assertEqual(sum(r["category"] == "EXPECTED_HISTORICAL_LIFECYCLE_STATE" for r in rows), 47)
        self.assertEqual(sum(r["category"] == "EXPECTED_ACTIVE_PHASE_FIREWALL" for r in rows), 6)

    def test_60_nested_repository_output_root_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "external temporary output root"):
            er2p.run(ROOT / "outputs/unauthorized_nested_protocol")


if __name__ == "__main__":
    unittest.main()
