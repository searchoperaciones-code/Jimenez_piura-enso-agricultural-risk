from __future__ import annotations

import ast
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import er2_r1_numerical_adjudication_v1 as a


class ER2R1NumericalAdjudicationV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.outputs = a.render_outputs()
        cls.audit = json.loads(cls.outputs[a.JSON_REL])
        cls.old = json.loads((ROOT / a.legacy.LOCK_REL).read_bytes())

    def test_01_all_seven_original_hashes_exact(self):
        self.assertEqual(a.verify_originals(), a.ORIGINAL_HASHES)
        self.assertEqual(len(a.ORIGINAL_HASHES), 7)

    def test_02_provisional_failure_lock_unchanged(self):
        self.assertEqual(a.legacy.sha((ROOT / a.legacy.LOCK_REL).read_bytes()),
                         "c7ae05b96b4155df5fe1d74484784c02c7fe32084b443aa7a02107b37a5c1963")
        self.assertEqual(self.old["completion_status"], "ER2_R1_FAIL_NUMERICAL_VERIFICATION")

    def test_03_historical_absolute_alarm_preserved(self):
        self.assertEqual(a.legacy.VERIFICATION_TOLERANCE, 1e-8)
        self.assertEqual(self.audit["strict_legacy_1e8_status"], "FAIL_PRESERVED")
        for code, t in self.audit["transient"].items():
            self.assertEqual(t["strict_recomputed_verification"], self.old["independent_numerical_verification"][code])
            self.assertEqual(t["strict_recomputed_verification"]["status"], "FAIL")

    def test_04_no_upstream_modifications_or_staging(self):
        self.assertEqual(a.legacy.verify_inputs(), a.legacy.FROZEN_HASHES)
        self.assertEqual(a.legacy.git("diff", "--name-only"), "")
        self.assertEqual(a.legacy.git("diff", "--cached", "--name-only"), "")
        self.assertEqual(a.legacy.git("rev-parse", "HEAD"), a.legacy.ER2P_SHA)

    def test_05_environment_is_recorded_without_changes(self):
        e = self.audit["environment"]
        self.assertTrue({"python", "numpy", "scipy", "cpu_architecture", "floating_type", "eps",
                         "build_configurations", "thread_environment", "observable_blas_pools"} <= set(e))
        self.assertEqual(e["eps"], np.finfo(np.float64).eps)
        self.assertFalse(e["environment_changed"])
        self.assertFalse(e["packages_installed"])
        for config in e["build_configurations"].values():
            self.assertEqual(set(config["blas_lapack"]), {"blas", "lapack"})

    def test_06_third_path_is_independent_of_frozen_fit_calls(self):
        frame, columns, y = a.ed1.synthetic_reference_fixture()
        with patch.object(a.ed1, "fit_two_way_fe_cr2", side_effect=AssertionError("not independent")), \
             patch.object(a.ed1, "_reference_svd_fit", side_effect=AssertionError("not independent")), \
             patch.object(a.ed1, "_aht_htz", side_effect=AssertionError("not independent")), \
             patch.object(a.ed1, "fe_matrix", side_effect=AssertionError("independent explicit design required")):
            result = a.third_fit(frame, columns, "PERIOD", y)
        self.assertEqual(result["diagnostics"]["path"], a.THIRD_PATH)

    def test_07_synthetic_numerical_crosscheck(self):
        frame, columns, y = a.ed1.synthetic_reference_fixture()
        main = a.main_view(a.ed1.fit_two_way_fe_cr2(frame, columns, "PERIOD", y))
        third = a.third_fit(frame, columns, "PERIOD", y)
        pair = a.compare_paths(main, third)
        self.assertEqual(pair["status"], "PASS")
        self.assertLess(max(pair["metrics"].values()), 1e-10)

    def test_08_column_scaling_backtransforms_original_units(self):
        frame, columns, y = a.ed1.synthetic_reference_fixture()
        base = a.third_fit(frame, columns, "PERIOD", y)
        factors = np.array([100., .1, 2.])[:len(columns)]
        changed = frame.copy()
        changed[columns] = changed[columns]*factors
        other = a.third_fit(changed, columns, "PERIOD", y)
        np.testing.assert_allclose(other["beta"]*factors, base["beta"], rtol=1e-10, atol=1e-12)
        np.testing.assert_allclose(other["covariance"]*np.outer(factors, factors), base["covariance"], rtol=1e-10, atol=1e-12)

    def test_09_fixed_prespecified_tolerances(self):
        self.assertEqual(a.BETA_RELATIVE_TOLERANCE, 1e-10)
        self.assertEqual(a.ADJUDICATION_RELATIVE_TOLERANCE, 1e-6)
        self.assertEqual(a.TINY, np.finfo(np.float64).tiny)
        self.assertEqual(self.audit["policy"], a.POLICY)

    def test_10_relative_vector_matrix_and_scalar_formulas(self):
        for first, second in ((np.array([1., 2.]), np.array([1.1, 2.2])),
                              (np.eye(2), np.eye(2)*2), (1., 1.5), (0., 0.)):
            expected = np.linalg.norm(np.asarray(first)-second)/max(np.linalg.norm(first), np.linalg.norm(second), a.TINY)
            self.assertEqual(a.relative_error(first, second), expected)
            self.assertEqual(a.relative_error(second, first), expected)

    def test_11_nonfinite_and_shape_drift_rejected(self):
        for first, second in ((np.array([np.nan]), np.array([1.])), (np.array([1.]), np.array([1., 2.]))):
            with self.assertRaisesRegex(RuntimeError, "NONFINITE_OR_SHAPE_DISAGREEMENT"):
                a.relative_error(first, second)

    def test_12_complete_three_path_pair_inventory(self):
        self.assertEqual(set(self.audit["transient"]), set(a.er2p.TRANSIENT))
        for t in self.audit["transient"].values():
            self.assertEqual(set(t["paths"]), {"MAIN", "SVD", "THIRD"})
            self.assertEqual(set(t["pairwise"]), {"MAIN_VS_SVD", "MAIN_VS_THIRD", "SVD_VS_THIRD"})

    def test_13_pairwise_distances_recomputed_from_serialized_paths(self):
        for t in self.audit["transient"].values():
            for pair, record in t["pairwise"].items():
                left, right = pair.split("_VS_")
                first, second = copy.deepcopy(t["paths"][left]), copy.deepcopy(t["paths"][right])
                for value in (first, second):
                    for key in ("beta", "covariance", "satterthwaite_df"):
                        value[key] = np.asarray(value[key])
                    value["singularities"] = value["cr2_singularities"]
                self.assertEqual(record, a.compare_paths(first, second))

    def test_14_pairwise_envelopes_pass(self):
        for t in self.audit["transient"].values():
            self.assertEqual(t["status"], "PASS")
            for p in t["pairwise"].values():
                self.assertEqual(p["status"], "PASS")
                self.assertTrue(p["sign_agreement"] and p["rank_agreement"] and p["cr2_singularity_status_agreement"])

    def test_15_condition_spectra_ranks_and_cutoffs_recorded(self):
        for t in self.audit["transient"].values():
            for p in ("MAIN", "SVD"):
                d = t["conditioning"][p]
                for matrix in ("within_transformed_x", "full_design", "normal_matrix", "aht_omega", "aht_contrast_covariance"):
                    s = d[matrix]
                    self.assertAlmostEqual(s["condition_2"], s["largest"]/s["smallest"])
                    self.assertEqual(s["absolute_cutoff"], s["rcond"]*s["largest"])
                    self.assertEqual(len(s["singular_values"]), s["default_matrix_rank"])
                self.assertTrue(d["cr2_adjustments"])
                self.assertEqual(d["cr2_singularity_count"], 0)

    def test_16_qr_geometry_and_original_design_identical(self):
        frame, columns, y = a.ed1.synthetic_reference_fixture()
        design, offset = a.qr_full_design(frame, columns, "PERIOD")
        expected = np.column_stack([a.ed1.fe_matrix(frame, "PERIOD"), frame[columns].to_numpy()])
        np.testing.assert_array_equal(design, expected)
        self.assertEqual(offset, a.ed1.fe_matrix(frame, "PERIOD").shape[1])
        for t in self.audit["transient"].values():
            self.assertLess(t["conditioning"]["THIRD"]["qr_reconstruction_relative_frobenius"], 1e-12)

    def test_17_reporting_invariance_is_descriptive(self):
        for t in self.audit["transient"].values():
            self.assertFalse(t["reporting_invariance_used_as_pass_criterion"])
            for r in t["reporting_objects"].values():
                self.assertFalse(r["p_below_0_05_used_as_gate"])
                self.assertEqual(len(r["coefficient_sign"]), 3)
                self.assertEqual(len(r["ci_zero_inclusion"]), 3)
                self.assertEqual(len(r["holm_ordering"]), 3)
                self.assertEqual(set(r["aht_numerical_result"]), {"df6", "f6", "p6"})

    def test_18_no_result_averaging_or_selection(self):
        for code, t in self.audit["transient"].items():
            self.assertEqual(t["paths"]["MAIN"]["beta"], self.old["independent_numerical_verification"][code]["main_beta"])
        self.assertFalse(self.audit["r1_results_numerically_changed"])
        self.assertFalse(self.audit["r1_specification_changed"])

    def test_19_result_and_aht_csvs_unchanged(self):
        for p in (a.legacy.RESULTS_REL, a.legacy.JOINT_REL):
            self.assertEqual(a.legacy.sha((ROOT / p).read_bytes()), a.ORIGINAL_HASHES[p.as_posix()])

    def test_20_perennial_algebra_all_three_crops(self):
        self.assertEqual(set(self.audit["perennial"]), set(a.er2p.PERENNIAL))
        for p in self.audit["perennial"].values():
            self.assertEqual(p["algebra"]["status"], "ALGEBRAIC_FE_EQUIVALENCE_CONFIRMED_FLOAT64_NONEXACT")
            self.assertTrue(all(c["time_invariance_and_projection_pass"] for c in p["algebra"]["columns"]))

    def test_21_projection_identity_recomputed_from_source(self):
        source = a.ed1.read_perennial_primary()
        for code, audit in self.audit["perennial"].items():
            level, columns = a.ed1.primary_design_frame(a.pd.DataFrame(), source, code, "LEVEL")
            anomaly, pairs = a.ed1.primary_design_frame(a.pd.DataFrame(), source, code, "PHYSICAL_ANOMALY")
            proof = a.algebraic_projection(level[columns].to_numpy(), anomaly[pairs].to_numpy(), level["UBIGEO"].astype(str).to_numpy(), columns)
            self.assertEqual(proof, audit["algebra"])
            for path, digest in audit["source_hashes"].items():
                self.assertEqual(a.legacy.sha((ROOT / path).read_bytes()), digest)

    def test_22_time_varying_difference_fails_algebra(self):
        districts = np.array(["a", "a", "b", "b"])
        anomaly = np.zeros((4, 1))
        level = np.array([[1.], [1.], [2.], [2.]])
        self.assertNotEqual(a.algebraic_projection(level, anomaly, districts, ["X"])["status"], "NOT_CONFIRMED")
        level[0, 0] += .001
        self.assertEqual(a.algebraic_projection(level, anomaly, districts, ["X"])["status"], "NOT_CONFIRMED")

    def test_23_original_perennial_nonexact_metrics_preserved(self):
        original = {d["crop_code"]: d for d in self.old["perennial_equivalence_diagnostics"]}
        for code, audit in self.audit["perennial"].items():
            self.assertEqual(audit["original_float64_status"], "WITHIN_1E-9_TOLERANCE_BUT_NOT_EXACT")
            self.assertEqual(audit["original_absolute_discrepancies"], original[code]["metrics"])

    def test_24_perennial_downstream_differences_not_hidden(self):
        for p in self.audit["perennial"].values():
            self.assertIn("coefficient_inference_vector_relative_l2", p["legacy_downstream_relative_differences"])
            self.assertIn("cr2_covariance_relative_frobenius", p["legacy_downstream_relative_differences"])
            self.assertEqual(p["third_qr_level_vs_anomaly"]["status"], "PASS")
            self.assertTrue(all(p["inference_drift_gates"].values()))

    def test_25_condition_amplification_budget_formula(self):
        for p in self.audit["perennial"].values():
            for k in ("LEVEL_MAIN", "ANOMALY_MAIN"):
                d = p["conditioning"][k]
                eta = d["normal_matrix"]["condition_2"]*d["gamma_n"]
                self.assertEqual(d["condition_amplification_budget"], eta/(1-eta))

    def test_26_distinct_count_is_never_five(self):
        self.assertEqual(self.audit["distinct_robustness_evidence_count"], 2)
        self.assertEqual(self.audit["perennial_distinct_evidence_count"], 0)
        self.assertTrue(all(v["distinct_evidence_contribution"] == 0 for v in self.audit["perennial"].values()))

    def test_27_no_unauthorized_tier_execution(self):
        for i in range(2, 7):
            self.assertEqual(self.audit["execution_firewall"][f"R{i}"], "NOT_EXECUTED")
        self.assertFalse(self.audit["execution_firewall"]["R3_ADAPTER_IMPLEMENTED"])
        tree = ast.parse((ROOT / a.SCRIPT_REL).read_bytes())
        calls = {n.func.attr for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
        self.assertTrue(calls.isdisjoint({"restricted_wild_cluster_bootstrap_t", "conley_covariance", "read_b3_sensitivity",
                                         "estimate_primary_models", "wild_bootstrap_validation"}))

    def test_28_certified_lock_only_after_all_gates_pass(self):
        self.assertEqual(a.CERTIFIED_REL in self.outputs, a.certification_allowed(self.audit))
        self.assertTrue(a.certification_allowed(self.audit))
        mutations = [("transient", "14010020000", "status"),
                     ("transient", "14010070000", "pairwise", "SVD_VS_THIRD", "status"),
                     ("perennial", "13010170102", "algebra", "status"),
                     ("perennial", "15010040000", "third_qr_level_vs_anomaly", "status")]
        for path in mutations:
            altered = copy.deepcopy(self.audit)
            node = altered
            for key in path[:-1]:
                node = node[key]
            node[path[-1]] = "FAIL"
            self.assertFalse(a.certification_allowed(altered))
            self.assertIsNone(a.certified_lock(altered, "0"*64, "1"*64))

    def test_29_certified_lock_references_provisional_and_exact_results(self):
        lock = json.loads(self.outputs[a.CERTIFIED_REL])
        self.assertEqual(lock["R1_FIRST_ATTEMPT_PROVISIONAL_FAILURE_LOCK_SHA256"], a.FIRST_LOCK_SHA)
        self.assertEqual(lock["original_result_artifact_sha256"], self.old["artifact_sha256"])
        self.assertEqual(lock["STRICT_LEGACY_1E8_STATUS"], "FAIL_PRESERVED")
        self.assertEqual(lock["original_r1_sha256"], a.ORIGINAL_HASHES)

    def test_30_next_tier_remains_not_authorized(self):
        self.assertEqual(self.audit["next_tier_authorization_status"], "NOT_AUTHORIZED")
        self.assertEqual(json.loads(self.outputs[a.CERTIFIED_REL])["NEXT_TIER_AUTHORIZATION_STATUS"], "NOT_AUTHORIZED")

    def test_31_sorted_json_utf8_lf_one_final_lf_no_timestamps(self):
        for p, payload in self.outputs.items():
            text = payload.decode("utf-8")
            self.assertNotIn(b"\r", payload)
            self.assertFalse(payload.startswith(b"\xef\xbb\xbf"))
            self.assertTrue(payload.endswith(b"\n"))
            self.assertFalse(payload.endswith(b"\n\n"))
            self.assertNotIn(str(ROOT), text)
            self.assertNotIn("NaN", text)
            if p.suffix == ".json":
                self.assertEqual(payload, a.legacy.json_bytes(json.loads(payload)))

    def test_32_two_runs_identical(self):
        self.assertEqual(self.outputs, a.render_outputs())

    def test_33_existing_locked_bytes_not_rewritten(self):
        with tempfile.TemporaryDirectory() as folder:
            a.publish(self.outputs, Path(folder))
            with patch.object(Path, "write_bytes", side_effect=AssertionError("no rewriting")):
                a.publish(self.outputs, Path(folder))

    def test_34_existing_different_adjudication_not_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/a.JSON_REL
            path.parent.mkdir(parents=True)
            path.write_bytes(b"{}\n")
            with self.assertRaisesRegex(RuntimeError, "IMMUTABLE_ADJUDICATION_REVISION_PROHIBITED"):
                a.publish(self.outputs, Path(folder))
            self.assertEqual(path.read_bytes(), b"{}\n")

    def test_35_certified_lock_has_external_hash(self):
        lock = json.loads(self.outputs[a.CERTIFIED_REL])
        self.assertEqual(lock["adjudication_sha256"], a.legacy.sha(self.outputs[a.JSON_REL]))
        self.assertEqual(lock["adjudication_report_sha256"], a.legacy.sha(self.outputs[a.REPORT_REL]))
        self.assertNotIn(a.legacy.sha(self.outputs[a.CERTIFIED_REL]), self.outputs[a.CERTIFIED_REL].decode())

    def test_36_original_drift_rejected(self):
        with patch.object(a.legacy, "sha", return_value="0"*64):
            with self.assertRaisesRegex(RuntimeError, "ER2_R1A_FAIL_ORIGINAL_RESULT_DRIFT"):
                a.verify_originals()

    def test_37_certificate_implementation_identity(self):
        self.assertEqual(self.audit["implementation_sha256"], a.legacy.sha((ROOT/a.SCRIPT_REL).read_bytes()))
        self.assertEqual(self.audit["test_sha256"], a.legacy.sha((ROOT/a.TEST_REL).read_bytes()))

    def test_38_third_path_disagreement_fails_prespecified_envelope(self):
        t = self.audit["transient"]["14010020000"]["paths"]["THIRD"]
        base = {**t, "singularities": t["cr2_singularities"]}
        base = {k: np.array(v) if k in ("beta", "covariance", "satterthwaite_df") else v for k, v in base.items()}
        for key in ("beta", "covariance", "satterthwaite_df"):
            changed = copy.deepcopy(base)
            changed[key] *= 1.001
            self.assertEqual(a.compare_paths(base, changed)["status"], "FAIL")

    def test_39_stale_pass_status_does_not_override_numerical_failure(self):
        altered = copy.deepcopy(self.audit)
        p = altered["transient"]["14010020000"]["pairwise"]["MAIN_VS_THIRD"]
        p["metrics"]["beta_relative_l2"] = 1e-3
        self.assertEqual(p["status"], "PASS")
        self.assertFalse(a.certification_allowed(altered))
        self.assertIsNone(a.certified_lock(altered, "0"*64, "1"*64))

    def test_40_publication_rejects_extra_or_historical_path(self):
        altered = {**self.outputs, a.legacy.RESULTS_REL: b"must not overwrite original\n"}
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(RuntimeError, "ADJUDICATION_OUTPUT_SCOPE_VIOLATION"):
                a.publish(altered, Path(folder))
            self.assertEqual(list(Path(folder).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
