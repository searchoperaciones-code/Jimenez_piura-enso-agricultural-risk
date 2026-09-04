from __future__ import annotations

import ast
import csv
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import er1_primary_real_estimation_v1 as er1  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class ER1PrimaryRealEstimationV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.coefficients = read_csv(ROOT / er1.COEFFICIENTS_REL)
        cls.joint = read_csv(ROOT / er1.JOINT_TESTS_REL)
        cls.samples = read_csv(ROOT / er1.SAMPLE_AUDIT_REL)
        cls.lock = json.loads((ROOT / er1.LOCK_REL).read_text(encoding="utf-8"))
        cls.report = (ROOT / er1.REPORT_REL).read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory(prefix="er1-test-one-") as first, tempfile.TemporaryDirectory(
            prefix="er1-test-two-"
        ) as second:
            cls.hashes_one = er1.run(Path(first))
            cls.hashes_two = er1.run(Path(second))
        cls.candidate_hashes = {relative.as_posix(): sha256(ROOT / relative) for relative in er1.OUTPUT_RELS}

    def test_01_ed1_freeze_identity_is_exact(self) -> None:
        preflight = er1.preflight()
        self.assertEqual(preflight["status"], "PASS")
        self.assertEqual(preflight["identity"]["head"], er1.ED1_FREEZE_SHA)
        self.assertEqual(preflight["identity"]["remote_ed1"], er1.ED1_FREEZE_SHA)
        self.assertEqual(preflight["identity"]["ed1_tag_target"], er1.ED1_FREEZE_SHA)

    def test_02_all_frozen_input_hashes_match(self) -> None:
        actual = {relative: sha256(ROOT / relative) for relative in er1.FROZEN_HASHES}
        self.assertEqual(actual, er1.FROZEN_HASHES)

    def test_03_authoritative_outcome_sources_are_exact(self) -> None:
        self.assertEqual(sha256(ROOT / er1.TRANSIENT_OUTCOME_REL), er1.TRANSIENT_OUTCOME_SHA)
        self.assertEqual(sha256(ROOT / er1.PERENNIAL_OUTCOME_REL), er1.PERENNIAL_OUTCOME_SHA)
        sources = self.lock["outcome_sources"]
        self.assertEqual(sources["transient"]["governing_freeze"], er1.D0_FREEZE_SHA)
        self.assertEqual(sources["perennial"]["joint_contract_freeze"], er1.JOINT_C0_FREEZE_SHA)

    def test_04_outcome_source_keys_and_columns_are_frozen(self) -> None:
        transient = self.lock["outcome_sources"]["transient"]
        perennial = self.lock["outcome_sources"]["perennial"]
        self.assertEqual(transient["key_columns"], ["CROP_CODE", "UBIGEO", "CAMPAIGN"])
        self.assertEqual(transient["outcome_column"], "TRANSIENT_CAMPAIGN_YIELD_RAW")
        self.assertEqual(perennial["key_columns"], ["COD_CULTIVO", "UBIGEO", "ANO"])
        self.assertEqual(perennial["outcome_column"], "YIELD_RAW")

    def test_05_exact_seven_file_candidate_scope(self) -> None:
        actual = set(
            subprocess.check_output(
                ["git", "ls-files", "--others", "--exclude-standard"], cwd=ROOT, text=True
            ).splitlines()
        )
        self.assertEqual(actual, {path.as_posix() for path in er1.CANDIDATE_RELS})

    def test_06_exactly_five_primary_models(self) -> None:
        self.assertEqual(self.lock["primary_models_estimated"], 5)
        self.assertEqual({row["MODEL_ID"] for row in self.coefficients}, {crop["model_id"] for crop in er1.ed1.CROPS.values()})

    def test_07_primary_sample_sizes_are_exact(self) -> None:
        actual = {row["CROP_CODE"]: int(row["N"]) for row in self.samples}
        self.assertEqual(actual, {code: values["n"] for code, values in er1.EXPECTED_SAMPLE.items()})

    def test_08_primary_district_and_period_counts_are_exact(self) -> None:
        for row in self.samples:
            expected = er1.EXPECTED_SAMPLE[row["CROP_CODE"]]
            self.assertEqual(int(row["NOMINAL_DISTRICTS"]), expected["districts"])
            self.assertEqual(int(row["EFFECTIVE_CONTRIBUTING_DISTRICTS"]), expected["effective"])
            self.assertEqual(int(row["PERIODS"]), expected["periods"])

    def test_09_no_silent_complete_case_loss(self) -> None:
        for row in self.samples:
            self.assertEqual(int(row["MISSING_Y"]), 0)
            self.assertEqual(int(row["MISSING_X"]), 0)
            self.assertEqual(int(row["DUPLICATE_KEYS"]), 0)

    def test_10_real_outcome_support_is_finite(self) -> None:
        for row in self.samples:
            self.assertEqual(int(row["FINITE_Y"]), int(row["N"]))
            self.assertEqual(int(row["NONFINITE_Y"]), 0)

    def test_11_no_zero_or_negative_primary_yield(self) -> None:
        for row in self.samples:
            self.assertEqual(int(row["ZERO_Y"]), 0)
            self.assertEqual(int(row["NEGATIVE_Y"]), 0)
            self.assertGreater(float(row["Y_MIN"]), 0.0)

    def test_12_all_twenty_one_coefficients_are_reported(self) -> None:
        self.assertEqual(len(self.coefficients), 21)
        self.assertEqual(self.lock["primary_coefficients_reported"], 21)
        counts = {}
        for row in self.coefficients:
            counts[row["CROP_CODE"]] = counts.get(row["CROP_CODE"], 0) + 1
        self.assertEqual(counts, {"14010020000": 3, "14010070000": 3, "13010210000": 3, "13010170102": 6, "15010040000": 6})

    def test_13_exact_frozen_regressor_sets(self) -> None:
        expected = {
            row["CROP_CODE"]: set(row["PRIMARY_REGRESSORS"].split("|"))
            for row in json.loads(
                (ROOT / "config/econometrics/econometric_design_master_v1.json").read_text(encoding="utf-8")
            )["crop_model_contracts"]
        }
        actual = {
            code: {row["CLIMATE_VARIABLE"] for row in self.coefficients if row["CROP_CODE"] == code}
            for code in expected
        }
        self.assertEqual(actual, expected)

    def test_14_exact_frozen_windows(self) -> None:
        for row in self.coefficients:
            windows = set(er1.ed1.CROPS[row["CROP_CODE"]]["windows"])
            self.assertIn(row["WINDOW"], windows)

    def test_15_outcome_scale_is_level_tm_per_ha(self) -> None:
        self.assertEqual({row["OUTCOME_SCALE"] for row in self.coefficients}, {"YIELD_LEVEL_TM_PER_HA"})
        self.assertEqual({row["OUTCOME_SCALE"] for row in self.samples}, {"YIELD_LEVEL_TM_PER_HA"})

    def test_16_primary_climate_family_is_physical_anomaly(self) -> None:
        self.assertEqual({row["PRIMARY_CLIMATE_FAMILY"] for row in self.coefficients}, {"PHYSICAL_ANOMALY"})

    def test_17_functional_form_is_linear_additive(self) -> None:
        self.assertEqual({row["FUNCTIONAL_FORM"] for row in self.coefficients}, {"LINEAR_ADDITIVE"})

    def test_18_district_and_period_fixed_effects_are_required(self) -> None:
        self.assertEqual({row["DISTRICT_FE"] for row in self.coefficients}, {"REQUIRED"})
        self.assertEqual({row["PERIOD_FE"] for row in self.coefficients}, {"REQUIRED"})

    def test_19_primary_estimation_is_unweighted(self) -> None:
        self.assertEqual({row["WEIGHTING"] for row in self.coefficients}, {"UNWEIGHTED_PRIMARY_ESTIMATION"})

    def test_20_primary_inference_is_exact(self) -> None:
        self.assertEqual({row["INFERENCE"] for row in self.coefficients}, {er1.PRIMARY_INFERENCE})

    def test_21_every_coefficient_has_its_satterthwaite_df(self) -> None:
        for row in self.coefficients:
            df = float(row["SATTERTHWAITE_DF"])
            clusters_minus_one = er1.EXPECTED_SAMPLE[row["CROP_CODE"]]["districts"] - 1
            self.assertTrue(np.isfinite(df))
            self.assertGreater(df, 0.0)
            self.assertNotAlmostEqual(df, clusters_minus_one, places=6)

    def test_22_rice_very_low_df_flag_is_exact(self) -> None:
        rice = [row for row in self.coefficients if row["CROP"] == "RICE"]
        flagged = [row for row in rice if row["EFFECTIVE_DF_FLAG"] == "VERY_LOW_EFFECTIVE_DF"]
        self.assertEqual(len(flagged), 1)
        self.assertEqual(flagged[0]["CLIMATE_VARIABLE"], "RAIN_ANOM_MM")
        self.assertLess(float(flagged[0]["SATTERTHWAITE_DF"]), 5.0)

    def test_23_all_coefficient_statistics_are_finite(self) -> None:
        fields = ["BETA", "CR2_STANDARD_ERROR", "SATTERTHWAITE_DF", "T_STATISTIC", "P_VALUE_TWO_SIDED", "CI95_LOWER", "CI95_UPPER", "HOLM_ADJUSTED_P_VALUE"]
        for row in self.coefficients:
            self.assertTrue(all(np.isfinite(float(row[field])) for field in fields))
            self.assertGreater(float(row["CR2_STANDARD_ERROR"]), 0.0)

    def test_24_p_values_and_confidence_intervals_are_valid(self) -> None:
        for row in self.coefficients:
            self.assertLessEqual(0.0, float(row["P_VALUE_TWO_SIDED"]))
            self.assertLessEqual(float(row["P_VALUE_TWO_SIDED"]), 1.0)
            self.assertLessEqual(0.0, float(row["HOLM_ADJUSTED_P_VALUE"]))
            self.assertLessEqual(float(row["HOLM_ADJUSTED_P_VALUE"]), 1.0)
            self.assertLess(float(row["CI95_LOWER"]), float(row["CI95_UPPER"]))

    def test_25_holm_is_recomputed_within_crop_only(self) -> None:
        for code in er1.ed1.CROPS:
            rows = [row for row in self.coefficients if row["CROP_CODE"] == code]
            p_values = np.asarray([float(row["P_VALUE_TWO_SIDED"]) for row in rows])
            expected = er1.holm_adjust(p_values)
            actual = np.asarray([float(row["HOLM_ADJUSTED_P_VALUE"]) for row in rows])
            np.testing.assert_allclose(actual, expected, rtol=0.0, atol=1e-15)

    def test_26_exactly_five_aht_tests(self) -> None:
        self.assertEqual(len(self.joint), 5)
        self.assertEqual(self.lock["aht_tests"], 5)
        self.assertEqual({row["CROP_CODE"] for row in self.joint}, set(er1.ed1.CROPS))

    def test_27_aht_tests_cover_every_primary_coefficient(self) -> None:
        for row in self.joint:
            expected = [
                item["CLIMATE_VARIABLE"]
                for item in self.coefficients
                if item["CROP_CODE"] == row["CROP_CODE"]
            ]
            self.assertEqual(row["COEFFICIENTS_TESTED"].split("|"), expected)

    def test_28_aht_statistics_are_finite_and_prespecified(self) -> None:
        for row in self.joint:
            self.assertEqual(row["JOINT_TEST"], "CR2_APPROXIMATE_HOTELLING_T_SQUARED")
            self.assertTrue(all(np.isfinite(float(row[field])) for field in ("NUMERATOR_DF", "DENOMINATOR_DF", "F_STATISTIC", "P_VALUE")))
            self.assertGreater(float(row["DENOMINATOR_DF"]), 0.0)
            self.assertLessEqual(float(row["P_VALUE"]), 1.0)

    def test_29_independent_reference_path_passes_every_crop(self) -> None:
        checks = self.lock["independent_numerical_verification"]
        self.assertEqual(set(checks), set(er1.ed1.CROPS))
        for check in checks.values():
            self.assertEqual(check["status"], "PASS")
            self.assertEqual(check["reference_path"], "INDEPENDENT_FULL_DESIGN_SVD_CALCULATION")

    def test_30_independent_differences_are_within_tolerance(self) -> None:
        for check in self.lock["independent_numerical_verification"].values():
            self.assertEqual(float(check["absolute_tolerance"]), er1.REFERENCE_TOLERANCE)
            self.assertLessEqual(max(check["differences"].values()), er1.REFERENCE_TOLERANCE)

    def test_31_lock_hashes_the_three_primary_tables(self) -> None:
        expected = {
            relative.as_posix(): sha256(ROOT / relative)
            for relative in (er1.COEFFICIENTS_REL, er1.JOINT_TESTS_REL, er1.SAMPLE_AUDIT_REL)
        }
        self.assertEqual(self.lock["result_table_sha256"], expected)

    def test_32_report_contains_the_results_lock_hash(self) -> None:
        digest = sha256(ROOT / er1.LOCK_REL)
        self.assertIn(f"ER1_PRIMARY_RESULTS_LOCK_SHA256={digest}", self.report)

    def test_33_two_independent_runs_are_byte_identical(self) -> None:
        self.assertEqual(self.hashes_one, self.hashes_two)

    def test_34_candidate_matches_independent_rebuild(self) -> None:
        self.assertEqual(self.candidate_hashes, self.hashes_one)

    def test_35_candidate_artifacts_are_utf8_lf_with_one_final_lf(self) -> None:
        for relative in er1.OUTPUT_RELS:
            payload = (ROOT / relative).read_bytes()
            self.assertFalse(payload.startswith(b"\xef\xbb\xbf"))
            self.assertNotIn(b"\r", payload)
            self.assertTrue(payload.endswith(b"\n"))
            self.assertFalse(payload.endswith(b"\n\n"))
            payload.decode("utf-8")

    def test_36_no_robustness_engine_is_called(self) -> None:
        tree = ast.parse((ROOT / er1.SCRIPT_REL).read_text(encoding="utf-8"))
        called_attributes = {
            node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        }
        self.assertTrue(
            called_attributes.isdisjoint(
                {"restricted_wild_cluster_bootstrap_t", "conley_covariance", "read_b3_sensitivity"}
            )
        )
        self.assertEqual(self.lock["robustness_tiers_executed"], 0)

    def test_37_all_r1_to_r6_tiers_are_not_executed(self) -> None:
        firewall = self.lock["execution_firewall"]
        for tier in (
            "R1_LEVEL_CLIMATE_FAMILY",
            "R2_STANDARDIZED_ANOMALY_COMPARABILITY",
            "R3_RESTRICTED_WILD_CLUSTER_BOOTSTRAP",
            "R4_SPATIAL_HAC",
            "R5_LEAVE_ONE_PERIOD_OUT_ALL_PERIODS",
            "R6_B3_STRICT_EXPOSURE",
        ):
            self.assertEqual(firewall[tier], "NOT_EXECUTED")

    def test_38_no_outcome_transformation_or_observation_deletion(self) -> None:
        firewall = self.lock["execution_firewall"]
        self.assertEqual(firewall["LOG_OUTCOME"], "NOT_EXECUTED")
        self.assertEqual(firewall["WINSORIZATION"], "NOT_EXECUTED")
        self.assertEqual(firewall["TRIMMING"], "NOT_EXECUTED")
        self.assertFalse(self.lock["model_revision_after_results"])

    def test_39_no_scenario_gvp_cvar_a1a2_or_optimization(self) -> None:
        firewall = self.lock["execution_firewall"]
        for key in ("ENSO_SCENARIOS", "GVP", "VAR_CVAR", "A1_A2", "OPTIMIZATION"):
            self.assertEqual(firewall[key], "NOT_EXECUTED")

    def test_40_claim_ceiling_is_empirical_association_only(self) -> None:
        self.assertEqual(self.lock["claim_ceiling"], er1.CLAIM_CEILING)
        self.assertEqual({row["CLAIM_CEILING"] for row in self.coefficients}, {er1.CLAIM_CEILING})
        self.assertEqual({row["CLAIM_CEILING"] for row in self.joint}, {er1.CLAIM_CEILING})

    def test_41_results_lock_is_candidate_not_frozen(self) -> None:
        self.assertTrue(self.lock["outcome_unsealed"])
        self.assertEqual(self.lock["status"], "CANDIDATE_PRIMARY_RESULTS_LOCKED_NOT_FROZEN")
        self.assertFalse(self.lock["er1_freeze_authorized"])
        self.assertEqual(self.lock["final_verdict"], er1.FINAL_VERDICT)

    def test_42_no_runtime_timestamp_is_serialized(self) -> None:
        def keys(value):
            if isinstance(value, dict):
                for key, child in value.items():
                    yield str(key).lower()
                    yield from keys(child)
            elif isinstance(value, list):
                for child in value:
                    yield from keys(child)

        self.assertFalse(any("timestamp" in key or "generated_at" in key or "runtime_date" in key for key in keys(self.lock)))

    def test_43_no_forbidden_result_artifact_exists(self) -> None:
        forbidden = (
            "ER1_ROBUSTNESS_RESULTS.csv",
            "ER1_ENSO_SCENARIOS.csv",
            "ER1_GVP.csv",
            "ER1_CVAR.csv",
            "ER1_A1_A2_RESULTS.csv",
            "ER1_OPTIMIZATION_RESULTS.csv",
        )
        self.assertTrue(all(not (ROOT / "outputs/econometrics" / name).exists() for name in forbidden))

    def test_44_index_and_tracked_tree_remain_unchanged(self) -> None:
        tracked = subprocess.check_output(["git", "diff", "--name-only"], cwd=ROOT, text=True).strip()
        staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=ROOT, text=True).strip()
        self.assertEqual(tracked, "")
        self.assertEqual(staged, "")

    def test_45_director_accepted_numerical_csv_hashes_are_unchanged(self) -> None:
        expected = {
            er1.COEFFICIENTS_REL: "37fa03a2e860f86277510a5ff3b66ca475fc02d277ea1dd6e18156f719c23480",
            er1.JOINT_TESTS_REL: "8d00e0ef866488c8f7ce7a418d58ae165e87f05053db9861fed1b0f181e412e3",
            er1.SAMPLE_AUDIT_REL: "d5a2b42b7f8f68be5a387c9726f76d081c83e1b242fea2edfba829f963040854",
        }
        for relative, digest in expected.items():
            self.assertEqual(sha256(ROOT / relative), digest)
            self.assertEqual(self.hashes_one[relative.as_posix()], digest)
            self.assertEqual(self.hashes_two[relative.as_posix()], digest)

    def test_46_all_accepted_numerical_lock_fields_are_unchanged(self) -> None:
        expected = {
            "primary_coefficients": "87bf17ba03f6265b946d520e4dd05035d36ddcebfce0b6923f7485da47dec6dd",
            "aht_joint_tests": "64b6d71e93521c4d7dd41c0fdb23a2386ada97bf7ddd76156cd0fbca9d0e5b2b",
            "sample_identities": "ecaa32256ce5e2551eee2bc0e0b66d4a363891af9a9316809eb257827fe57dd5",
            "independent_numerical_verification": "9f9eebc8fd5d84cd8a1cda092a0a4652f4729718a1b9191cadbbecf3d170014e",
        }
        for field, digest in expected.items():
            payload = json.dumps(self.lock[field], sort_keys=True, separators=(",", ":"), allow_nan=False)
            self.assertEqual(hashlib.sha256(payload.encode("utf-8")).hexdigest(), digest)
        self.assertEqual(len(self.lock["primary_coefficients"]), 21)
        self.assertEqual(len(self.lock["aht_joint_tests"]), 5)

    def test_47_banana_lagged_tmin_and_aht_values_are_preserved(self) -> None:
        row = next(row for row in self.lock["primary_coefficients"]
                   if row["CROP_CODE"] == "15010040000" and row["CLIMATE_VARIABLE"] == "TMIN_ANOM_C__T_MINUS_1")
        expected = {
            "BETA": -6.5645586917721594,
            "CR2_STANDARD_ERROR": 1.7358859193873584,
            "SATTERTHWAITE_DF": 29.71338120661278,
            "P_VALUE_TWO_SIDED": 0.0007009834366711548,
            "CI95_LOWER": -10.111145249546421,
            "CI95_UPPER": -3.017972133997897,
            "HOLM_ADJUSTED_P_VALUE": 0.0042059006200269294,
        }
        for field, value in expected.items():
            self.assertEqual(row[field], value)
        joint = next(row for row in self.lock["aht_joint_tests"] if row["CROP_CODE"] == "15010040000")
        self.assertEqual(joint["P_VALUE"], 0.023233998721656757)

    def test_48_lemon_lagged_tmin_is_not_below_point05_after_holm(self) -> None:
        row = next(row for row in self.lock["primary_coefficients"]
                   if row["CROP_CODE"] == "13010170102" and row["CLIMATE_VARIABLE"] == "TMIN_ANOM_C__T_MINUS_1")
        self.assertEqual(row["P_VALUE_TWO_SIDED"], 0.02293415013097283)
        self.assertEqual(row["HOLM_ADJUSTED_P_VALUE"], 0.13760490078583698)
        self.assertIn(
            "Lemon lagged Tmin has an unadjusted p-value below 0.05 but does not remain below 0.05 after Holm adjustment.",
            self.report,
        )

    def test_49_confidence_intervals_and_holm_have_distinct_semantics(self) -> None:
        semantics = self.lock["reporting_semantics"]
        self.assertEqual(semantics["COEFFICIENT_CONFIDENCE_INTERVALS"], "UNADJUSTED_95_PERCENT_CR2_SATTERTHWAITE")
        self.assertEqual(semantics["MULTIPLICITY_ADJUSTMENT"], "HOLM_STEP_DOWN_WITHIN_CROP_P_VALUES")
        self.assertEqual(semantics["MULTIPLICITY_ADJUSTED_CONFIDENCE_INTERVALS"], "NOT_CONSTRUCTED_NOT_CLAIMED")
        self.assertIn("unadjusted coefficient-specific 95% CR2/Satterthwaite confidence intervals", self.report)
        self.assertIn("| Unadjusted 95% CR2/Satterthwaite CI | Within-crop Holm p |", self.report)
        self.assertIn("Holm step-down adjusts coefficient p-values within each crop only.", self.report)

    def test_50_no_holm_adjusted_interval_claim(self) -> None:
        forbidden = (
            "holm-adjusted interval evidence",
            "holm-adjusted confidence intervals",
            "confidence intervals span zero after multiplicity control",
            "coefficient intervals span zero after crop-specific multiplicity control",
        )
        for text in (self.report, json.dumps(self.lock), (ROOT / er1.SCRIPT_REL).read_text(encoding="utf-8")):
            for phrase in forbidden:
                self.assertNotIn(phrase, text.lower())

    def test_51_no_global_five_crop_fwer_claim(self) -> None:
        self.assertEqual(self.lock["reporting_semantics"]["GLOBAL_FIVE_CROP_FAMILYWISE_ERROR_CONTROL"], "NOT_CLAIMED")
        self.assertIn("No global five-crop familywise-error claim is made.", self.report)
        self.assertIn("does not control multiplicity across all 21 coefficients in all five crops", self.report)

    def test_52_inference_precision_is_distinct_from_evidence_compatible_with_zero(self) -> None:
        self.assertEqual(
            self.lock["reporting_semantics"]["INFERENCE_PRECISION_STATUS"],
            "HETEROGENEOUS_ACROSS_CROPS_AND_COEFFICIENTS",
        )
        self.assertIn("Statistical evidence compatible with zero does not by itself imply limited effective degrees of freedom", self.report)
        self.assertNotIn("WITH_WEAK_INFERENCE", self.report)
        self.assertNotIn("WITH_WEAK_INFERENCE", self.lock["final_verdict"])
        row = next(row for row in self.lock["primary_coefficients"]
                   if row["CROP"] == "RICE" and row["CLIMATE_VARIABLE"] == "RAIN_ANOM_MM")
        self.assertEqual(row["SATTERTHWAITE_DF"], 4.919993824254409)
        self.assertEqual(row["EFFECTIVE_DF_FLAG"], "VERY_LOW_EFFECTIVE_DF")
        self.assertIn("inferential-precision limitation specific to that coefficient", self.report)

    def test_53_old_lock_identity_is_retained_and_numeric_identity_is_separate(self) -> None:
        identity = self.lock["er1_reporting_lock_identity"]
        previous = "d2ceab1655ae3cb220e8adfe3be7fce56dc77c35121ad6a06350532c3cb7c118"
        self.assertEqual(identity["previous_primary_results_lock_sha256"], previous)
        self.assertEqual(identity["version"], "ER1R-v1")
        self.assertFalse(identity["numerical_result_change"])
        self.assertNotEqual(sha256(ROOT / er1.LOCK_REL), previous)
        mapping = json.dumps(self.lock["result_table_sha256"], sort_keys=True, separators=(",", ":"))
        numerical_identity = hashlib.sha256(mapping.encode("utf-8")).hexdigest()
        self.assertEqual(self.lock["er1_numerical_results_identity"]["sha256"], numerical_identity)
        self.assertIn(f"ER1_REPORTING_LOCK_IDENTITY={sha256(ROOT / er1.LOCK_REL)}", self.report)
        self.assertIn(f"ER1_NUMERICAL_RESULTS_IDENTITY={numerical_identity}", self.report)
        self.assertIn(previous, self.report)

    def test_54_regeneration_does_not_write_existing_accepted_csvs(self) -> None:
        for relative, key, fields in (
            (er1.COEFFICIENTS_REL, "primary_coefficients", er1.COEFFICIENT_FIELDS),
            (er1.JOINT_TESTS_REL, "aht_joint_tests", er1.JOINT_FIELDS),
            (er1.SAMPLE_AUDIT_REL, "sample_identities", er1.SAMPLE_FIELDS),
        ):
            with patch.object(Path, "write_bytes", side_effect=AssertionError("Accepted CSV must not be rewritten")):
                er1.write_csv(ROOT / relative, self.lock[key], fields)

    def test_55_numerical_drift_is_rejected_before_writing(self) -> None:
        rows = [dict(row) for row in self.lock["primary_coefficients"]]
        rows[0]["CI95_LOWER"] += 0.01
        with patch.object(Path, "write_bytes", side_effect=AssertionError("Drift must not be written")):
            with self.assertRaisesRegex(RuntimeError, "ER1R_FAIL_NUMERICAL_RESULT_DRIFT"):
                er1.write_csv(ROOT / er1.COEFFICIENTS_REL, rows, er1.COEFFICIENT_FIELDS)

    def test_56_er1r_remains_reporting_only_and_not_frozen(self) -> None:
        self.assertEqual(self.lock["reporting_gate"], "ER1R_PRIMARY_RESULTS_REPORTING_SEMANTICS_CORRECTION")
        self.assertEqual(self.lock["final_verdict"], "ER1R_PASS_REPORTING_CORRECTED_RESULTS_READY_FOR_FREEZE_DECISION")
        self.assertFalse(self.lock["numerical_result_change"])
        self.assertFalse(self.lock["er1r_freeze_authorized"])
        self.assertFalse(self.lock["model_revision_after_results"])
        self.assertEqual(self.lock["robustness_tiers_executed"], 0)

    def test_57_only_banana_lagged_tmin_remains_below_point05_within_crop(self) -> None:
        below = [(row["CROP_CODE"], row["CLIMATE_VARIABLE"]) for row in self.lock["primary_coefficients"]
                 if row["HOLM_ADJUSTED_P_VALUE"] < 0.05]
        self.assertEqual(below, [("15010040000", "TMIN_ANOM_C__T_MINUS_1")])
        self.assertIn("Most coefficient-specific 95% CR2/Satterthwaite confidence intervals include zero.", self.report)
        self.assertIn("within-crop Holm adjustment of coefficient p-values, only Banana lagged Tmin remains below 0.05", self.report)


if __name__ == "__main__":
    unittest.main()
