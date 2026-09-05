from __future__ import annotations

import ast
import copy
import csv
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import er2_r1_level_robustness_v1 as r1


class ER2R1LevelRobustnessV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.outputs = r1.render_outputs()
        cls.lock = json.loads(cls.outputs[r1.LOCK_REL])
        cls.rows = cls.lock["rice_result_inventory"] + cls.lock["mad_result_inventory"]
        cls.diagnostics = cls.lock["perennial_equivalence_diagnostics"]

    def test_01_exact_frozen_parent(self):
        self.assertEqual(r1.git("rev-parse", "HEAD"), "3fd1f657e79d7e0ae93903239fd3690dcade56a4")
        self.assertEqual(r1.preflight()["status"], "PASS")

    def test_02_exact_er1_numerical_and_reporting_identity(self):
        self.assertEqual(self.lock["er1_numerical_results_identity"],
                         "40e0f58269dda309e83a1fa3da17ef4d5dc5523efc72a666f734d0ebacb76b24")
        self.assertEqual(self.lock["er1_reporting_lock_sha256"],
                         "83eea5e179b5e3504bd1144d744dcdbeddbbdf6a554f4d10ab03b92a30278841")

    def test_03_frozen_bytes_exact(self):
        self.assertEqual(r1.verify_inputs(), r1.FROZEN_HASHES)

    def test_04_r1_only_authorized(self):
        self.assertEqual(self.lock["execution_authorization"],
                         {"R1": "DIRECTOR_AUTHORIZED", **{f"R{i}": "NOT_AUTHORIZED" for i in range(2, 7)}})

    def test_05_exact_two_distinct_models(self):
        self.assertEqual(self.lock["distinct_models"], 2)
        self.assertEqual({r["CROP_CODE"] for r in self.rows}, {"14010020000", "14010070000"})

    def test_06_exact_six_distinct_coefficients(self):
        self.assertEqual(len(self.rows), self.lock["distinct_coefficients"])
        self.assertEqual(len({(r["CROP_CODE"], r["VARIABLE"]) for r in self.rows}), 6)

    def test_07_exact_er1_ordered_sample_keys(self):
        transient, _, _ = r1.er1.read_outcome_sources()
        exposures = r1.pq.read_table(r1.ed1.TRANSIENT_PATH, columns=list(r1.ed1.TRANSIENT_COLUMNS)).to_pandas()
        for code, sample in self.lock["sample_identity"].items():
            frame, _ = r1.er1.transient_design_with_outcome(exposures, transient, code)
            self.assertEqual(sample["er1_ordered_keys"], r1.sample_keys(frame, "CAMPAIGN_ID"))
            self.assertEqual(sample["r1_ordered_keys"], sample["er1_ordered_keys"])
            self.assertEqual(sample["key_sha256"], r1.sha(r1.json_bytes(sample["r1_ordered_keys"])))

    def test_08_sample_counts_and_effective_clusters(self):
        for code, n, nominal, effective in (("14010020000", 281, 44, 43), ("14010070000", 318, 54, 52)):
            s = self.lock["sample_identity"][code]
            self.assertEqual((s["n"], s["districts"], s["effective_districts"], s["periods"]), (n, nominal, effective, 7))

    def test_09_added_deleted_reordered_or_duplicate_keys_rejected(self):
        frame = pd.DataFrame({"UBIGEO": ["01", "02"], "period": ["2017", "2018"]})
        altered = [frame.iloc[:1], frame.iloc[::-1], pd.concat([frame, frame.iloc[:1]]),
                   pd.DataFrame({"UBIGEO": ["01", "03"], "period": ["2017", "2018"]})]
        for value in altered:
            with self.subTest(value=value.to_dict()):
                with self.assertRaisesRegex(RuntimeError, "FAIL_SAMPLE_IDENTITY"):
                    r1.require_same_sample(frame, value, "period")

    def test_10_exact_level_regressors(self):
        for code in r1.er2p.TRANSIENT:
            self.assertEqual(self.lock["exact_model_contract"][code]["regressors"], ["RAIN_MM", "TMAX_C", "TMIN_C"])

    def test_11_exact_frozen_windows(self):
        self.assertEqual({r["WINDOW"] for r in self.lock["rice_result_inventory"]}, {"RICE_FLOWERING_95_110_DAS"})
        self.assertEqual({r["WINDOW"] for r in self.lock["mad_result_inventory"]}, {"MAD_MPLUS1_MPLUS3"})

    def test_12_exact_fixed_effects_and_cluster(self):
        for code, c in self.lock["exact_model_contract"].items():
            self.assertEqual((c["district_fe"], c["period_fe"], c["cluster"]), ("REQUIRED", "REQUIRED", "UBIGEO"))
            self.assertEqual(c["period_column"], r1.ed1.CROPS[code]["period_column"])

    def test_13_unweighted_linear_yield_level(self):
        for c in self.lock["exact_model_contract"].values():
            self.assertEqual((c["weighting"], c["functional_form"], c["outcome"]),
                             ("UNWEIGHTED", "LINEAR_ADDITIVE", "YIELD_LEVEL_TM_PER_HA"))

    def test_14_two_full_aht_tests(self):
        rows = self.lock["aht_joint_tests"]
        self.assertEqual(len(rows), 2)
        for r in rows:
            self.assertEqual((r["NULL"], r["NUMERATOR_DF"], r["METHOD"]),
                             ("RAIN_MM=TMAX_C=TMIN_C=0", 3, "CR2_AHT_HTZ"))
            self.assertAlmostEqual(r["P"], stats.f.sf(r["F"], r["NUMERATOR_DF"], r["DENOMINATOR_DF"]), places=14)

    def test_15_holm_independently_within_each_crop(self):
        for group in (self.lock["rice_result_inventory"], self.lock["mad_result_inventory"]):
            order = sorted(range(3), key=lambda i: group[i]["P_TWO_SIDED"])
            values = [min(1., max((3-j)*group[order[j]]["P_TWO_SIDED"] for j in range(k+1))) for k in range(3)]
            for i, value in zip(order, values):
                self.assertAlmostEqual(group[i]["HOLM_P"], value, places=14)
        self.assertEqual(self.lock["multiplicity"], "HOLM_STEP_DOWN_WITHIN_CROP_R1_COEFFICIENT_P_VALUES")

    def test_16_unadjusted_satterthwaite_intervals(self):
        for r in self.rows:
            width = stats.t.ppf(.975, r["SATTERTHWAITE_DF"]) * r["CR2_SE"]
            self.assertAlmostEqual(r["CI95_LOWER"], r["BETA"] - width, places=12)
            self.assertAlmostEqual(r["CI95_UPPER"], r["BETA"] + width, places=12)
        self.assertEqual(self.lock["confidence_intervals"], "UNADJUSTED_95_PERCENT_CR2_SATTERTHWAITE")

    def test_17_no_adjusted_ci_or_global_fwer(self):
        self.assertEqual(self.lock["multiplicity_adjusted_confidence_intervals"], "NOT_CONSTRUCTED_NOT_CLAIMED")
        self.assertEqual(self.lock["global_fwer"], "NOT_CLAIMED")

    def test_18_coefficient_t_and_p_values(self):
        for r in self.rows:
            self.assertAlmostEqual(r["T"], r["BETA"] / r["CR2_SE"], places=13)
            self.assertAlmostEqual(r["P_TWO_SIDED"], 2*stats.t.sf(abs(r["T"]), r["SATTERTHWAITE_DF"]), places=14)

    def test_19_all_three_perennial_diagnostics(self):
        self.assertEqual(len(self.diagnostics), 3)
        self.assertEqual([d["crop_code"] for d in self.diagnostics], list(r1.er2p.PERENNIAL))

    def test_20_full_perennial_window_architecture(self):
        for d, count in zip(self.diagnostics, (3, 6, 6)):
            self.assertEqual(len(d["variable_pairing"]), count)
            self.assertEqual(np.array(d["transformed_level_design"]).shape[1], count)
            self.assertEqual(self.lock["exact_model_contract"][d["crop_code"]]["windows"],
                             list(r1.ed1.CROPS[d["crop_code"]]["windows"]))

    def test_21_diagnostics_never_inflate_distinct_evidence(self):
        self.assertTrue(all(d["distinct_evidence_contribution"] == 0 and d["diagnostic_only"] for d in self.diagnostics))
        self.assertEqual(self.lock["distinct_robustness_evidence_count"], 2)
        self.assertEqual(self.lock["perennial_diagnostic_models"], 3)

    def test_22_exact_tolerance_and_nonequivalent_distinguished(self):
        a = np.array([1., 2.])
        for delta, status in ((0., "EXACT_EQUALITY"), (1e-10, "WITHIN_1E-9_TOLERANCE_BUT_NOT_EXACT"), (1e-6, "NON_EQUIVALENT")):
            metrics = {k: r1.compare_arrays(a, a+delta) for k in ("transformed_x", "coefficients", "fitted_values")}
            self.assertEqual(r1.equality_status(metrics), status)

    def test_23_hold_on_any_nonexact_perennial(self):
        exact = [{"status": "EXACT_EQUALITY"} for _ in range(3)]
        self.assertEqual(r1.completion_status(exact), r1.PASS)
        for position in range(3):
            for status in ("WITHIN_1E-9_TOLERANCE_BUT_NOT_EXACT", "NON_EQUIVALENT"):
                altered = copy.deepcopy(exact)
                altered[position]["status"] = status
                self.assertEqual(r1.completion_status(altered), r1.HOLD)

    def test_24_no_result_specific_statistical_tests(self):
        f = self.lock["interpretation_firewall"]
        self.assertFalse(f["KNOWN_PRIMARY_RESULTS_CHANGED_R1_CONTRACT"])
        self.assertEqual(f["BANANA_SPECIFIC_TEST"], f["LEMON_SPECIFIC_TEST"])
        self.assertEqual(f["BANANA_SPECIFIC_TEST"], "PROHIBITED")
        source = (ROOT / r1.SCRIPT_REL).read_text(encoding="utf-8")
        tree = ast.parse(source)
        calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                 and n.func.id == "perennial_diagnostic"]
        self.assertEqual(len(calls), 1)

    def test_25_no_standardized_or_other_tier_execution(self):
        tree = ast.parse((ROOT / r1.SCRIPT_REL).read_bytes())
        calls = {n.func.attr for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
        self.assertTrue(calls.isdisjoint({"restricted_wild_cluster_bootstrap_t", "wild_bootstrap_validation",
                                         "conley_covariance", "read_b3_sensitivity", "estimate_primary_models",
                                         "implementation_feasibility", "build_geometry_rows"}))
        for c in self.lock["exact_model_contract"].values():
            self.assertTrue(all(v.split("__")[0] in r1.LEVEL for v in c["regressors"]))
        for i in range(2, 7):
            self.assertEqual(self.lock["interpretation_firewall"][f"R{i}"], "NOT_EXECUTED")
        self.assertFalse(self.lock["interpretation_firewall"]["R3_ADAPTER_IMPLEMENTED"])

    def test_26_independent_numerical_verification(self):
        self.assertEqual(set(self.lock["independent_numerical_verification"]), set(r1.er2p.TRANSIENT))
        for v in self.lock["independent_numerical_verification"].values():
            self.assertEqual(v["status"], "PASS")
            self.assertLessEqual(max(v["differences"].values()), 1e-8)
            self.assertEqual(v["reference_path"], "INDEPENDENT_FULL_DESIGN_SVD_CALCULATION")

    def test_27_transformed_design_metrics_recomputed(self):
        for d in self.diagnostics:
            level, anomaly = np.array(d["transformed_level_design"]), np.array(d["transformed_anomaly_design"])
            self.assertEqual(d["metrics"]["transformed_x"], r1.compare_arrays(level, anomaly))
            self.assertEqual(d["status"], r1.equality_status(d["metrics"]))

    def test_28_diagnostic_equality_covariance_and_inference_recorded(self):
        for d in self.diagnostics:
            self.assertEqual(set(d["metrics"]), {"transformed_x", "coefficients", "fitted_values", "residuals",
                                                  "cr2_covariance", "satterthwaite_df", "aht", "coefficient_inference"})
            self.assertIn("equivalent_within_tolerance", d["column_space"])

    def test_29_no_nonfinite_output_or_machine_paths(self):
        for p, payload in self.outputs.items():
            text = payload.decode("utf-8")
            self.assertNotIn(str(ROOT), text)
            self.assertNotIn("NaN", text)
            self.assertNotIn("Infinity", text)
        with self.assertRaises(ValueError):
            r1.json_bytes({"invalid": float("nan")})

    def test_30_canonical_utf8_lf_and_one_final_lf(self):
        for payload in [*self.outputs.values(), (ROOT / r1.SCRIPT_REL).read_bytes(), (ROOT / r1.TEST_REL).read_bytes()]:
            payload.decode("utf-8")
            self.assertNotIn(b"\r", payload)
            self.assertFalse(payload.startswith(b"\xef\xbb\xbf"))
            self.assertTrue(payload.endswith(b"\n"))
            self.assertFalse(payload.endswith(b"\n\n"))
        self.assertEqual(self.outputs[r1.LOCK_REL], r1.json_bytes(self.lock))

    def test_31_two_independent_builds_identical(self):
        second = r1.render_outputs()
        self.assertEqual(second, self.outputs)
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as other:
            self.assertEqual(r1.publish(self.outputs, Path(first)), r1.publish(second, Path(other)))
            for rel in r1.OUTPUT_RELS:
                self.assertEqual((Path(first) / rel).read_bytes(), (Path(other) / rel).read_bytes())

    def test_32_existing_identical_bytes_never_rewritten(self):
        with tempfile.TemporaryDirectory() as temporary:
            r1.publish(self.outputs, Path(temporary))
            with patch.object(Path, "write_bytes", side_effect=AssertionError("rewrite forbidden")):
                r1.publish(self.outputs, Path(temporary))

    def test_33_existing_different_lock_never_overwritten(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / r1.LOCK_REL
            target.parent.mkdir(parents=True)
            target.write_bytes(b"{}\n")
            with self.assertRaisesRegex(RuntimeError, "LOCKED_ARTIFACT_REVISION_PROHIBITED"):
                r1.publish(self.outputs, root)
            self.assertEqual(target.read_bytes(), b"{}\n")
            self.assertFalse((root / r1.RESULTS_REL).exists())

    def test_34_lock_hash_external_no_self_reference(self):
        self.assertNotIn(r1.sha(self.outputs[r1.LOCK_REL]), self.outputs[r1.LOCK_REL].decode())
        self.assertEqual(self.lock["artifact_sha256"],
                         {p.as_posix(): r1.sha(b) for p, b in self.outputs.items() if p != r1.LOCK_REL})

    def test_35_next_tier_not_authorized_previous_null(self):
        self.assertIsNone(self.lock["previous_tier_lock_sha256"])
        self.assertEqual(self.lock["next_tier_authorization_status"], "NOT_AUTHORIZED")
        self.assertEqual(self.lock["tier_order"], 1)

    def test_36_implementation_and_test_hashes_in_lock(self):
        self.assertEqual(self.lock["implementation_sha256"], r1.sha((ROOT / r1.SCRIPT_REL).read_bytes()))
        self.assertEqual(self.lock["test_sha256"], r1.sha((ROOT / r1.TEST_REL).read_bytes()))

    def test_37_exact_r1_frozen_tier_hash(self):
        self.assertEqual(self.lock["tier_contract_sha256"], r1.sha(r1.er2p.json_bytes(self.lock["frozen_r1_tier_contract"])))
        self.assertEqual(self.lock["er2p_protocol_sha256"], "13519fb5c86fdf690d233c54dd45c3242ba348f3c7f66587238e6965ed1c49ff")

    def test_38_primary_references_unchanged_and_descriptive_only(self):
        lookup = {(r["CROP_CODE"], r["CLIMATE_VARIABLE"]): r for r in
                  csv.DictReader(io.StringIO((ROOT / r1.er1.COEFFICIENTS_REL).read_text(encoding="utf-8")))}
        for r in self.rows:
            self.assertEqual(r["ER1_BETA_REFERENCE"], float(lookup[(r["CROP_CODE"], r["ER1_VARIABLE"])]["BETA"]))
            self.assertEqual(r["R1_MINUS_ER1_BETA_DESCRIPTIVE_ONLY"], r["BETA"] - r["ER1_BETA_REFERENCE"])
            self.assertEqual(r["PRIMARY_REPLACEMENT"], "PROHIBITED")
        self.assertIn("not directly comparable effect sizes", self.outputs[r1.REPORT_REL].decode())

    def test_39_no_scores_scenarios_or_causal_claim(self):
        f = self.lock["interpretation_firewall"]
        self.assertEqual(f["ROBUSTNESS_SCORE"], f["SIGNIFICANCE_VOTE_COUNTING"])
        self.assertEqual(f["ROBUSTNESS_SCORE"], "PROHIBITED")
        for key in ("ENSO_SCENARIOS", "GVP", "VAR_CVAR", "A1_A2", "OPTIMIZATION"):
            self.assertEqual(f[key], "NOT_EXECUTED")
        self.assertEqual(f["CLAIM_CEILING"], "EMPIRICAL_ASSOCIATION_CLIMATE_RESPONSE_ONLY")

    def test_40_upstream_and_wrong_head_mutations_rejected(self):
        with patch.object(r1, "sha", return_value="0" * 64):
            with self.assertRaisesRegex(RuntimeError, "FAIL_UPSTREAM_IMMUTABILITY"):
                r1.verify_inputs()
        with patch.object(r1, "git", return_value="0" * 40):
            with self.assertRaisesRegex(RuntimeError, "FAIL_FROZEN_CONTRACT: HEAD"):
                r1.preflight()

    def test_41_exact_output_inventory_no_other_tier(self):
        self.assertEqual(set(self.outputs), set(r1.OUTPUT_RELS))
        self.assertEqual(len(r1.CANDIDATE_RELS), 7)
        self.assertTrue(all(p.name.startswith("ER2_R1_") for p in self.outputs))
        with self.assertRaisesRegex(RuntimeError, "External temporary output root"):
            r1.publish(self.outputs, ROOT / "outputs/not_authorized")

    def test_42_missing_values_rejected_without_imputation(self):
        frame = pd.DataFrame({"RAIN_MM": [np.nan], "TMAX_C": [1.], "TMIN_C": [1.]})
        with self.assertRaisesRegex(RuntimeError, "FAIL_SAMPLE_IDENTITY"):
            r1.checked_fit(frame, list(r1.LEVEL), "period", np.array([1.]))

    def test_43_numerical_failure_cannot_receive_pass_or_hold_only(self):
        failed = any(max(v["differences"].values()) > 1e-8
                     for v in self.lock["independent_numerical_verification"].values())
        expected = r1.NUMERICAL_FAIL if failed else r1.completion_status(self.diagnostics)
        self.assertEqual(self.lock["completion_status"], expected)
        for v in self.lock["independent_numerical_verification"].values():
            self.assertEqual(v["status"], "FAIL" if max(v["differences"].values()) > 1e-8 else "PASS")


if __name__ == "__main__":
    unittest.main()
