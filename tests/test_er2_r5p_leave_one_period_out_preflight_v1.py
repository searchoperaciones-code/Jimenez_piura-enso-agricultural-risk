from __future__ import annotations

from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import er2_r5p_leave_one_period_out_preflight_v1 as r5p  # noqa: E402


def read_csv(relative: Path) -> list[dict[str, str]]:
    with (ROOT / relative).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256(relative: Path) -> str:
    return hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()


class TestER2R5PLeaveOnePeriodOutPreflightV1(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.lock = json.loads((ROOT / r5p.PREFLIGHT_LOCK).read_text(encoding="utf-8"))
        cls.plan_lock = json.loads((ROOT / r5p.TEST_PLAN_LOCK).read_text(encoding="utf-8"))
        cls.omissions = read_csv(r5p.OMISSION_PLAN)
        cls.mapping = read_csv(r5p.COEFFICIENT_MAP)
        cls.validation = read_csv(r5p.SYNTHETIC_VALIDATION)
        cls.report = (ROOT / r5p.REPORT).read_text(encoding="utf-8")

    def test_01_exact_r4_frozen_predecessor(self) -> None:
        state = r5p.preflight()
        identity = state["identity"]
        self.assertEqual(identity["head"], r5p.R4_FREEZE_SHA)
        self.assertEqual(identity["branch"], r5p.R4_BRANCH)
        self.assertEqual(identity["remote_branch"], r5p.R4_FREEZE_SHA)
        self.assertEqual(identity["tag_object"], r5p.R4_TAG_OBJECT)
        self.assertEqual(identity["tag_target"], r5p.R4_FREEZE_SHA)
        self.assertEqual(self.lock["governing_state"]["r4_results_lock_sha256"], r5p.R4_RESULTS_LOCK_SHA)

    def test_02_exact_eight_candidate_paths_and_clean_index(self) -> None:
        untracked = set(
            subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=ROOT, text=True).splitlines()
        )
        self.assertEqual(untracked, {path.as_posix() for path in r5p.CANDIDATES})
        self.assertFalse(subprocess.check_output(["git", "diff", "--name-only"], cwd=ROOT, text=True).strip())
        self.assertFalse(subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=ROOT, text=True).strip())

    def test_03_exact_r5_tier_contract(self) -> None:
        row, tier = r5p.r5_contract()
        self.assertEqual(row["TIER_CONTRACT_SHA256"], r5p.R5_TIER_CONTRACT_SHA)
        self.assertEqual(tier["order"], 5)
        self.assertEqual(tier["tier_id"], "R5_LEAVE_ONE_PERIOD_OUT_ALL_PERIODS")
        self.assertEqual(tier["role"], "ALL_PERIOD_INFLUENCE_DESCRIPTION")
        self.assertEqual(tier["family"], "PHYSICAL_ANOMALY")
        self.assertEqual(tier["previous_tier"], "R4")
        self.assertEqual(tier["next_tier"], "R6")

    def test_04_period_id_architecture_and_source_rule(self) -> None:
        architecture = self.lock["period_id_architecture"]
        self.assertEqual(architecture["transient"], "CAMPAIGN_ID")
        self.assertEqual(architecture["perennial"], "REFERENCE_PERIOD_ID")
        self.assertEqual(architecture["source_rule"], "SORTED_UNIQUE_PERIODS_OF_EACH_EXACT_ER1_ANALYTICAL_SAMPLE")

    def test_05_exact_mechanically_derived_period_lists(self) -> None:
        audit = self.lock["period_id_architecture"]["crop_audit"]
        for crop_code, expected in r5p.EXPECTED_PERIODS.items():
            self.assertEqual(audit[crop_code]["periods"], list(expected))
            self.assertEqual(audit[crop_code]["period_count"], len(expected))
            self.assertEqual(audit[crop_code]["sample_n"], r5p.EXPECTED_SAMPLE_N[crop_code])
            self.assertEqual(audit[crop_code]["source"], "ER2_R2_RESULTS_LOCK.sample_identity.er1_ordered_keys")

    def test_06_exact_period_counts_7_7_8_8_8(self) -> None:
        actual = {code: self.lock["period_id_architecture"]["crop_audit"][code]["period_count"] for code in r5p.CROP_ORDER}
        self.assertEqual(actual, {"14010020000": 7, "14010070000": 7, "13010210000": 8, "13010170102": 8, "15010040000": 8})

    def test_07_exact_38_omission_refits(self) -> None:
        self.assertEqual(len(self.omissions), 38)
        self.assertEqual([int(row["REFIT_ORDER"]) for row in self.omissions], list(range(1, 39)))
        counts = Counter(row["CROP_CODE"] for row in self.omissions)
        self.assertEqual(counts, {"14010020000": 7, "14010070000": 7, "13010210000": 8, "13010170102": 8, "15010040000": 8})
        self.assertEqual(len({(row["CROP_CODE"], row["OMITTED_PERIOD_ID"]) for row in self.omissions}), 38)

    def test_08_one_period_only_and_all_periods_reported(self) -> None:
        self.assertEqual({row["OMISSION_SCOPE"] for row in self.omissions}, {"ONE_ENTIRE_PERIOD_OMITTED_PER_MODEL_ONLY"})
        self.assertEqual({row["REPORT_ALL_PERIODS"] for row in self.omissions}, {"TRUE"})
        self.assertEqual({row["ESTIMATION_EXECUTED"] for row in self.omissions}, {"FALSE"})
        self.assertEqual(self.lock["omission_plan"]["baseline_refits_counted"], 0)
        self.assertEqual(self.lock["omission_plan"]["second_period_omissions"], 0)
        self.assertEqual(self.lock["omission_plan"]["district_omissions"], 0)

    def test_09_exact_162_coefficient_omission_rows(self) -> None:
        self.assertEqual(len(self.mapping), 162)
        self.assertEqual([int(row["COEFFICIENT_OMISSION_ORDER"]) for row in self.mapping], list(range(1, 163)))
        self.assertEqual(len({(row["CROP_CODE"], row["VARIABLE"], row["OMITTED_PERIOD_ID"]) for row in self.mapping}), 162)
        self.assertEqual({row["REAL_LOO_BETA_COMPUTED"] for row in self.mapping}, {"FALSE"})

    def test_10_exact_coefficient_dimensions(self) -> None:
        counts = Counter(row["CROP_CODE"] for row in self.mapping)
        self.assertEqual(counts, {"14010020000": 21, "14010070000": 21, "13010210000": 24, "13010170102": 48, "15010040000": 48})
        self.assertEqual(self.lock["coefficient_omission_map"]["summary_rows_future"], 21)

    def test_11_2017_mapping_is_exact(self) -> None:
        named = self.lock["mandatory_named_reporting"]
        self.assertEqual(named["transient"]["LEAVE_2017_OUT"], "2016/2017")
        self.assertEqual(named["perennial"]["LEAVE_2017_OUT"], "2017")
        rows = [row for row in self.omissions if row["MANDATORY_NAMED_CASE"] == "LEAVE_2017_OUT"]
        self.assertEqual(len(rows), 5)

    def test_12_2023_mapping_is_exact(self) -> None:
        named = self.lock["mandatory_named_reporting"]
        self.assertEqual(named["transient"]["LEAVE_2023_OUT"], "2022/2023")
        self.assertEqual(named["perennial"]["LEAVE_2023_OUT"], "2023")
        rows = [row for row in self.omissions if row["MANDATORY_NAMED_CASE"] == "LEAVE_2023_OUT"]
        self.assertEqual(len(rows), 5)
        self.assertIs(named["frozen_pre_result"], True)
        self.assertEqual(named["estimator_effect"], "NONE_REPORTING_LABELS_ONLY")

    def test_13_fixed_model_components(self) -> None:
        fixed = self.lock["fixed_model_components"]
        self.assertEqual(fixed["outcome"], "YIELD_LEVEL_TM_PER_HA")
        self.assertEqual(fixed["climate_family"], "PHYSICAL_ANOMALY")
        self.assertEqual(fixed["windows"], "EXACT_ED1_FROZEN")
        self.assertEqual(fixed["functional_form"], "LINEAR_ADDITIVE")
        self.assertEqual(fixed["district_fe"], "REQUIRED")
        self.assertEqual(fixed["remaining_period_fe"], "REQUIRED")
        self.assertEqual(fixed["weighting"], "UNWEIGHTED_PRIMARY_ESTIMATION")
        self.assertEqual(fixed["regressors"], "EXACT_ER1_REGRESSORS")
        self.assertEqual(fixed["second_period_omission"], "PROHIBITED")
        self.assertEqual(fixed["district_deletion"], "PROHIBITED")

    def test_14_estimation_api_identity(self) -> None:
        api = self.lock["estimation_api"]
        self.assertEqual(api["file_sha256"], r5p.ED1_IMPLEMENTATION_SHA)
        self.assertEqual(api["functions"]["fit_two_way_fe_cr2"]["source_sha256"], r5p.FIT_SOURCE_SHA)
        self.assertEqual(api["functions"]["fit_two_way_fe_cr2"]["body_sha256"], r5p.FIT_BODY_SHA)
        self.assertEqual(api["functions"]["fe_matrix"]["source_sha256"], r5p.FE_SOURCE_SHA)
        self.assertEqual(api["functions"]["absorb_fixed_effects"]["source_sha256"], r5p.ABSORB_SOURCE_SHA)
        self.assertEqual(api["executor_architecture"], "R5_EXECUTOR_CAN_REUSE_FROZEN_PRIMARY_ESTIMATION_DIRECTLY")

    def test_15_r5_inference_outputs_not_authorized(self) -> None:
        self.assertEqual(self.lock["r5_loo_inference_outputs"], "NOT_AUTHORIZED")
        self.assertEqual(self.lock["estimation_api"]["inference_outputs"], "NOT_AUTHORIZED")
        forbidden = {"CR2_STANDARD_ERROR", "SATTERTHWAITE_P", "AHT", "WCR", "CONLEY"}
        self.assertTrue(forbidden.isdisjoint(self.lock["future_real_r5_detail_schema"]))
        self.assertTrue(forbidden.isdisjoint(self.lock["future_real_r5_summary_schema"]))

    def test_16_sign_and_exact_zero_rules(self) -> None:
        self.assertEqual(r5p.classify_sign(1e-300), "POSITIVE")
        self.assertEqual(r5p.classify_sign(-1e-300), "NEGATIVE")
        self.assertEqual(r5p.classify_sign(0.0), "ZERO")
        rules = self.lock["sign_rules"]
        self.assertEqual(rules["zero"], "BETA_EXACTLY_ZERO_REPORTED_SEPARATELY")

    def test_17_sign_reversal_is_strict_product_rule(self) -> None:
        self.assertTrue(r5p.sign_reversal(1.0, -1.0))
        self.assertTrue(r5p.sign_reversal(-1.0, 1.0))
        self.assertFalse(r5p.sign_reversal(0.0, -1.0))
        self.assertFalse(r5p.sign_reversal(1.0, 0.0))
        self.assertEqual(self.lock["sign_rules"]["sign_reversal"], "PRODUCT_OF_LOO_AND_PRIMARY_BETA_STRICTLY_NEGATIVE")

    def test_18_summary_metrics_and_beta_range(self) -> None:
        contract = self.lock["summary_metric_contract"]
        self.assertEqual(contract["metrics"], list(r5p.SUMMARY_METRICS))
        self.assertEqual(contract["beta_range"], "MAX_LOO_BETA_MINUS_MIN_LOO_BETA")
        self.assertEqual(contract["standardized_influence_score"], "NOT_AUTHORIZED")
        summary = r5p.summarize_loo(1.0, [("C", 2.0), ("A", 0.0), ("B", 1.0)])
        self.assertEqual(summary["BETA_RANGE"], 2.0)
        self.assertEqual((summary["POSITIVE_COUNT"], summary["NEGATIVE_COUNT"], summary["ZERO_COUNT"]), (2, 0, 1))

    def test_19_max_deviation_all_ties_sorted(self) -> None:
        summary = r5p.summarize_loo(1.0, [("P3", 2.0), ("P1", 0.0), ("P2", 1.0)])
        self.assertEqual(summary["MAX_ABSOLUTE_BETA_DEVIATION"], 1.0)
        self.assertEqual(summary["PERIODS_CAUSING_MAX_ABSOLUTE_DEVIATION"], ["P1", "P3"])
        self.assertEqual(self.lock["summary_metric_contract"]["max_deviation_tie_rule"], "REPORT_ALL_TIED_PERIOD_IDS_SORTED_NO_POST_RESULT_TIE_SELECTION")

    def test_20_no_arbitrary_stability_or_vote_counting(self) -> None:
        role = self.lock["scientific_role"]
        self.assertEqual(role["stability_classification"], "DESCRIPTIVE_NO_ARBITRARY_PASS_FAIL_THRESHOLD")
        self.assertEqual(role["significance_vote_counting"], "PROHIBITED")
        self.assertEqual(role["primary_replacement"], "PROHIBITED")
        self.assertIs(role["no_omission_result_becomes_primary"], True)
        self.assertEqual(self.lock["r5_concordance_contract"]["robustness_score"], "PROHIBITED")

    def test_21_synthetic_test_plan_was_locked_first(self) -> None:
        self.assertEqual(self.plan_lock, r5p.SYNTHETIC_PLAN)
        self.assertEqual(self.plan_lock["seed"], 20260905)
        self.assertEqual(self.plan_lock["rng"], "NUMPY_GENERATOR_PCG64")
        self.assertGreaterEqual(self.plan_lock["districts"], 6)
        self.assertGreaterEqual(self.plan_lock["periods"], 5)
        self.assertEqual(self.plan_lock["regressors"], 3)
        self.assertIs(self.plan_lock["balanced_core"], True)
        self.assertEqual(self.plan_lock["controlled_unbalanced_cell"], "DROP_D06_X_P05")
        self.assertEqual(self.plan_lock["continuous_tolerance"], 1e-10)
        self.assertIs(self.plan_lock["frozen_before_first_synthetic_refit"], True)

    def test_22_production_reference_equivalence(self) -> None:
        summary = self.lock["synthetic_validation"]
        self.assertEqual(summary["status"], "PASS")
        self.assertEqual(summary["production_reference_omissions"], 5)
        self.assertLessEqual(summary["maximum_absolute_beta_difference"], 1e-10)
        equivalence = [row for row in self.validation if row["CATEGORY"] == "PRODUCTION_REFERENCE"]
        self.assertEqual(len(equivalence), 5)
        self.assertTrue(all(row["STATUS"] == "PASS" for row in equivalence))

    def test_23_all_required_edge_cases_pass(self) -> None:
        rows = {row["CHECK_ID"]: row for row in self.validation}
        self.assertTrue(set(r5p.EDGE_CASES).issubset(rows))
        self.assertTrue(all(rows[name]["STATUS"] == "PASS" for name in r5p.EDGE_CASES))
        self.assertEqual(self.lock["synthetic_validation"]["edge_cases_passed"], len(r5p.EDGE_CASES))

    def test_24_fail_closed_extensions_pass(self) -> None:
        rows = {row["CHECK_ID"]: row for row in self.validation}
        for name in (
            "Y_MISSING_TARGET_COEFFICIENT_FAILS_CLOSED",
            "Z_NONFINITE_INPUT_FAILS_CLOSED",
            "AA_MALFORMED_PERIOD_KEY_FAILS_CLOSED",
            "AB_INSUFFICIENT_REMAINING_PERIODS_FAILS_CLOSED",
        ):
            self.assertEqual(rows[name]["STATUS"], "PASS")

    def test_25_result_specific_branch_audit(self) -> None:
        self.assertEqual(self.lock["result_specific_r5_branches"], 0)
        self.assertNotIn("BANANA", str(r5p.inspect.signature(r5p.production_loo_beta)))
        self.assertNotIn("LEMON", str(r5p.inspect.signature(r5p.production_loo_beta)))

    def test_26_real_r5_firewall(self) -> None:
        firewall = self.lock["real_result_firewall"]
        self.assertIs(firewall["REAL_SAMPLE_KEYS_READ"], True)
        self.assertIs(firewall["REAL_PERIOD_LABELS_READ"], True)
        self.assertIs(firewall["REAL_OUTCOME_NUMERICAL_VALUES_READ"], False)
        self.assertIs(firewall["REAL_CLIMATE_REGRESSOR_NUMERICAL_VALUES_READ"], False)
        self.assertEqual(firewall["REAL_R5_REFITS_EXECUTED"], 0)
        self.assertIs(firewall["REAL_R5_BETAS_COMPUTED"], False)
        self.assertIs(firewall["REAL_R5_P_VALUES_COMPUTED"], False)
        self.assertIs(firewall["REAL_R5_SIGN_REVERSALS_KNOWN"], False)
        self.assertIs(firewall["REAL_R5_BETA_RANGES_KNOWN"], False)
        self.assertIs(firewall["REAL_R5_MAX_DEVIATION_PERIODS_KNOWN"], False)

    def test_27_future_output_schemas_only(self) -> None:
        self.assertEqual(self.lock["future_real_r5_detail_schema"], list(r5p.FUTURE_DETAIL_SCHEMA))
        self.assertEqual(self.lock["future_real_r5_summary_schema"], list(r5p.FUTURE_SUMMARY_SCHEMA))
        self.assertEqual(self.lock["coefficient_omission_map"]["real_detail_rows_current"], 0)
        self.assertEqual(self.lock["coefficient_omission_map"]["real_summary_rows_current"], 0)
        forbidden = (
            "ER2_R5_LOO_RESULTS.csv",
            "ER2_R5_LOO_SUMMARY.csv",
            "ER2_R5_RESULTS_LOCK.json",
        )
        self.assertTrue(all(not (ROOT / "outputs/econometrics" / name).exists() for name in forbidden))

    def test_28_two_independent_builds_are_byte_identical(self) -> None:
        with tempfile.TemporaryDirectory(prefix="er2_r5p_test_run1_") as first_dir, tempfile.TemporaryDirectory(prefix="er2_r5p_test_run2_") as second_dir:
            first = r5p.build_package(Path(first_dir))
            second = r5p.build_package(Path(second_dir))
        self.assertEqual(first, second)
        for relative, payload in first.items():
            self.assertEqual(payload, (ROOT / relative).read_bytes())

    def test_29_artifact_hashes_are_exact(self) -> None:
        artifact_sha = self.lock["artifact_sha256"]
        self.assertNotIn(r5p.PREFLIGHT_LOCK.as_posix(), artifact_sha)
        expected = {
            relative.as_posix(): sha256(relative)
            for relative in (r5p.REPORT, r5p.OMISSION_PLAN, r5p.COEFFICIENT_MAP, r5p.SYNTHETIC_VALIDATION, r5p.TEST_PLAN_LOCK, r5p.SCRIPT, r5p.TEST)
        }
        self.assertEqual(artifact_sha, expected)

    def test_30_utf8_lf_byte_contract_for_all_eight(self) -> None:
        for relative in r5p.CANDIDATES:
            payload = (ROOT / relative).read_bytes()
            payload.decode("utf-8")
            self.assertFalse(payload.startswith(b"\xef\xbb\xbf"), relative)
            self.assertNotIn(b"\r", payload, relative)
            self.assertTrue(payload.endswith(b"\n"), relative)
            self.assertFalse(payload.endswith(b"\n\n"), relative)

    def test_31_report_and_final_verdict(self) -> None:
        self.assertIn("R5_REFIT_MODELS=38", self.report)
        self.assertIn("R5_COEFFICIENT_OMISSION_ROWS=162", self.report)
        self.assertIn("REAL_R5_REFITS_EXECUTED=0", self.report)
        self.assertIn("R5_LOO_INFERENCE_OUTPUTS=NOT_AUTHORIZED", self.report)
        self.assertEqual(self.lock["final_verdict"], r5p.FINAL_VERDICT)
        self.assertEqual(self.lock["status"], "PASS_PREEXECUTION_CERTIFIED_PENDING_DIRECTOR_REVIEW")

    def test_32_r6_and_downstream_firewalls(self) -> None:
        firewall = self.lock["execution_firewall"]
        self.assertEqual(firewall["REAL_R5_EXECUTION_AUTHORIZATION_STATUS"], "NOT_AUTHORIZED")
        self.assertEqual(firewall["R6_AUTHORIZATION_STATUS"], "NOT_AUTHORIZED")
        self.assertIs(firewall["R6_EXECUTED"], False)
        self.assertIs(firewall["B3_STRICT_RESULTS_READ"], False)
        for field in ("ENSO_SCENARIOS", "GVP", "VAR_CVAR", "A1_A2", "OPTIMIZATION"):
            self.assertEqual(firewall[field], "NOT_EXECUTED")
        self.assertEqual(self.lock["NEXT_TIER_AUTHORIZATION_STATUS"], "NOT_AUTHORIZED")


    def test_33_wrong_predecessor_commit_fails_before_blob_read(self) -> None:
        with patch.object(r5p.subprocess, "check_output") as plumbing:
            with self.assertRaisesRegex(RuntimeError, "wrong frozen commit"):
                r5p.verify_frozen_blob(r5p.R4_PARENT_SHA, r5p.PROTOCOL, r5p.FROZEN_INPUT_SHA256[r5p.PROTOCOL])
        plumbing.assert_not_called()

    def test_34_absent_predecessor_path_fails_closed(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "missing or unreadable frozen blob"):
            r5p.verify_frozen_blob(r5p.R4_FREEZE_SHA, Path("__R5P1_ABSENT_FROZEN_BLOB__"), "0" * 64)

    def test_35_changed_raw_blob_fails_closed(self) -> None:
        blob = r5p.read_frozen_blob(r5p.R4_FREEZE_SHA, r5p.PROTOCOL)
        with patch.object(r5p.subprocess, "check_output", return_value=blob + b"substantive drift\n"):
            with self.assertRaisesRegex(RuntimeError, "frozen blob SHA"):
                r5p.verify_frozen_blob(r5p.R4_FREEZE_SHA, r5p.PROTOCOL, r5p.FROZEN_INPUT_SHA256[r5p.PROTOCOL])

    def test_36_wrong_expected_sha_fails_closed(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "frozen blob SHA"):
            r5p.verify_frozen_blob(r5p.R4_FREEZE_SHA, r5p.PROTOCOL, "0" * 64)

    def test_37_lf_blob_with_crlf_materialization_passes(self) -> None:
        blob = r5p.read_frozen_blob(r5p.R4_FREEZE_SHA, r5p.PROTOCOL)
        self.assertNotIn(b"\r", blob)
        self.assertIn(b"\n", blob)
        materialized = blob.replace(b"\n", b"\r\n")
        with patch.object(Path, "read_bytes", side_effect=AssertionError("worktree bytes must not be authoritative")):
            actual = r5p.verify_frozen_blob(r5p.R4_FREEZE_SHA, r5p.PROTOCOL, r5p.sha_bytes(blob))
        self.assertEqual(actual, r5p.FROZEN_INPUT_SHA256[r5p.PROTOCOL])
        diagnostic = r5p.worktree_eol_diagnostic(blob, materialized)
        self.assertEqual(diagnostic["diagnostic"], "EOL_ONLY_MATERIALIZATION")
        self.assertIs(diagnostic["worktree_eol_only_materialization"], True)
        self.assertEqual(diagnostic["crlf_count"], blob.count(b"\n"))

    def test_38_substantive_difference_is_not_eol_only(self) -> None:
        diagnostic = r5p.worktree_eol_diagnostic(b"frozen\n", b"changed\r\n")
        self.assertEqual(diagnostic["diagnostic"], "SUBSTANTIVE_DIFFERENCE")
        self.assertIs(diagnostic["worktree_eol_only_materialization"], False)

    def test_39_all_thirteen_frozen_inputs_use_exact_raw_blobs(self) -> None:
        self.assertEqual(len(r5p.FROZEN_INPUT_SHA256), 13)
        for relative, expected in r5p.FROZEN_INPUT_SHA256.items():
            with self.subTest(path=relative.as_posix()):
                self.assertEqual(r5p.verify_frozen_blob(r5p.R4_FREEZE_SHA, relative, expected), expected)
        self.assertEqual(self.lock["FROZEN_INPUT_BYTE_SOURCE"], "RAW_GIT_OBJECT")
        self.assertIs(self.lock["WORKTREE_BYTES_ARE_AUTHORITATIVE"], False)
        self.assertEqual(self.lock["R4_PREDECESSOR_SCIENTIFIC_IDENTITY"], "PASS")

    def test_40_failed_attempt_and_superseded_lock_are_preserved(self) -> None:
        self.assertEqual(self.lock["PREVIOUS_HOLD_VERDICT"], "ER2_R5P_HOLD_INTERRUPTED_LOCAL_STATE_REQUIRES_ADJUDICATION")
        self.assertEqual(self.lock["PREVIOUS_FAILED_VERDICT"], "ER2_R5P_FAIL_R4_PREDECESSOR_IDENTITY")
        self.assertEqual(self.lock["PREVIOUS_FAILURE_ROOT_CAUSE"], "WINDOWS_CHECKOUT_EOL_MATERIALIZATION_IN_BYTE_VERIFIER")
        self.assertEqual(self.lock["PREVIOUS_DEDICATED_TESTS"], "32_RUN_30_PASS_0_FAIL_2_ERROR")
        self.assertEqual(self.lock["SUPERSEDED_R5P_LOCK_SHA"], "8024092d5b85179046462cac3b7e5ad02f22492ef8eb170c55e9252291b0c683")
        self.assertEqual(self.lock["SUPERSEDED_R5P_LOCK_STATUS"], "SUPERSEDED_PRE_REMEDIATION_CANDIDATE_LOCK")

    def test_41_tracked_and_staged_state_guards_still_fail(self) -> None:
        original_git = r5p.git
        for guarded_args, marker in ((('diff', '--name-only'), 'tracked diff'), (('diff', '--cached', '--name-only'), 'staged diff')):
            with self.subTest(guard=marker):
                def changed_git(*args: str) -> str:
                    return r5p.PROTOCOL.as_posix() if args == guarded_args else original_git(*args)

                with patch.object(r5p, "git", side_effect=changed_git):
                    with self.assertRaisesRegex(RuntimeError, marker):
                        r5p.preflight()


if __name__ == "__main__":
    unittest.main()
