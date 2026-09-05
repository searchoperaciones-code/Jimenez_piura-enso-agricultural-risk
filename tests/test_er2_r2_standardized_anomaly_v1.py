from __future__ import annotations

import ast
import csv
import io
import json
import subprocess
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import er2_r2_standardized_anomaly_v1 as r2


class ER2R2StandardizedAnomalyV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for name in ("fit_two_way_fe_cr2", "_reference_svd_fit"):
            guard = patch.object(r2.ed1, name, side_effect=AssertionError("R2R forbids re-estimation"))
            guard.start()
            cls.addClassCleanup(guard.stop)
        cls.pre = r2.reporting_preflight()
        cls.protected_before = {p: ((ROOT / p).read_bytes(), (ROOT / p).stat().st_mtime_ns) for p in r2.PROTECTED_R2_HASHES}
        cls.designs, _ = r2.prepare_designs()
        cls.temporary = tempfile.TemporaryDirectory(prefix="er2-r2-tests-")
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.output = Path(cls.temporary.name)
        cls.build = r2.build_reporting(cls.output)
        cls.payloads = {p: (ROOT / p).read_bytes() for p in r2.OUTPUT_RELS}
        cls.lock = json.loads(cls.payloads[r2.LOCK_REL])
        # The initial manifest describes the initial report, not its authorized reporting revision.
        cls.payloads[r2.REPORT_REL] = r2.report_text(r2.initial_report_data(cls.lock), cls.lock["reproducibility"]).encode("utf-8")
        cls.reporting_payloads = {p: (cls.output / p).read_bytes() for p in r2.REPORTING_OUTPUT_RELS}
        cls.certified = json.loads(cls.reporting_payloads[r2.REPORTING_LOCK_REL])
        cls.coefficients = cls.lock["coefficient_inventory"]
        cls.joint = cls.lock["aht_joint_tests"]

    def test_01_exact_r1_parent_and_local_refs(self):
        self.assertEqual(r2.git("rev-parse", "HEAD"), "b5614bb02bad3a40d90ca55688e19d71ee272877")
        for ref in (r2.R1_BRANCH, "origin/" + r2.R1_BRANCH, r2.R1_TAG + "^{}"):
            self.assertEqual(r2.git("rev-parse", ref), r2.R1_SHA)

    def test_02_predecessor_certified_lock_is_exact_committed_blob(self):
        payload = subprocess.check_output(["git", "show", r2.R1_SHA + ":" + r2.r1a.CERTIFIED_REL.as_posix()], cwd=ROOT)
        self.assertEqual(payload, (ROOT / r2.r1a.CERTIFIED_REL).read_bytes())
        self.assertEqual(r2.sha(payload), "d035e999b213b7e8af8d7c26c7246bd7a17d30eeb75a79667e4e00e3810869b8")

    def test_03_exact_r2_tier_contract_hash(self):
        self.assertEqual(r2.sha(r2.er2p.json_bytes(self.pre["tier_contract"])), "22d27c741ad28f1be971c63a9eafdbf2e88ae16644645c2ece0970150323b0fd")
        self.assertEqual(self.lock["tier_contract_sha256"], self.pre["tier_contract_sha256"])

    def test_04_wrong_build_parent_rejected(self):
        original = r2.git
        with patch.object(r2, "git", side_effect=lambda *a: r2.r1.ER2P_SHA if a == ("rev-parse", "HEAD") else original(*a)):
            with self.assertRaisesRegex(RuntimeError, "exact R1 build parent"):
                r2.preflight()

    def test_05_upstream_hashes_exact(self):
        self.assertEqual(r2.verify_inputs(), r2.FROZEN_HASHES)
        self.assertEqual(self.lock["exact_frozen_input_sha256"], r2.FROZEN_HASHES)

    def test_06_exact_five_models(self):
        self.assertEqual(set(self.lock["exact_model_contracts"]), set(r2.ed1.CROPS))
        self.assertEqual(self.lock["models"], 5)

    def test_07_exact_21_unique_coefficients(self):
        self.assertEqual(len(self.coefficients), 21)
        self.assertEqual(len({(r["CROP_CODE"], r["VARIABLE"]) for r in self.coefficients}), 21)

    def test_08_exact_five_ahts(self):
        self.assertEqual(len(self.joint), 5)
        self.assertEqual([r["NUMERATOR_DF"] for r in self.joint], [3., 3., 3., 6., 6.])

    def test_09_exact_per_crop_inventory(self):
        self.assertEqual(Counter(r["CROP_CODE"] for r in self.coefficients),
                         {"14010020000": 3, "14010070000": 3, "13010210000": 3, "13010170102": 6, "15010040000": 6})

    def test_10_ordered_er1_keys_exact(self):
        old = json.loads((ROOT / r2.r1.LOCK_REL).read_bytes())
        expected = {c: v["er1_ordered_keys"] for c,v in old["sample_identity"].items()}
        expected.update({v["crop_code"]: v["ordered_sample_keys"] for v in old["perennial_equivalence_diagnostics"]})
        for code, value in self.lock["sample_identity"].items():
            self.assertEqual(value["er1_ordered_keys"], expected[code])
            self.assertEqual(value["r2_ordered_keys"], expected[code])

    def test_11_exact_sample_counts(self):
        for code, value in self.lock["sample_identity"].items():
            expected = r2.er1.EXPECTED_SAMPLE[code]
            self.assertEqual((value["n"], value["districts"], value["effective_districts"], value["periods"]),
                             (expected["n"], expected["districts"], expected["effective"], expected["periods"]))

    def test_12_missing_standardized_x_stops_without_deletion(self):
        d = self.designs["14010020000"]
        broken = d["frame"].copy()
        broken.loc[broken.index[0], d["columns"][0]] = np.nan
        with self.assertRaisesRegex(RuntimeError, "missing standardized X"):
            r2.align_standardized(d["primary"], broken, d["columns"], "CAMPAIGN_ID")
        self.assertEqual(len(broken), 281)

    def test_13_missing_key_stops(self):
        d = self.designs["14010020000"]
        with self.assertRaisesRegex(RuntimeError, "ordered keys differ"):
            r2.align_standardized(d["primary"], d["frame"].iloc[1:], d["columns"], "CAMPAIGN_ID")

    def test_14_reordered_keys_stop(self):
        d = self.designs["14010020000"]
        with self.assertRaisesRegex(RuntimeError, "ordered keys differ"):
            r2.align_standardized(d["primary"], d["frame"].iloc[::-1], d["columns"], "CAMPAIGN_ID")

    def test_15_duplicate_key_stops(self):
        d = self.designs["14010020000"]
        with self.assertRaisesRegex(RuntimeError, "duplicate keys"):
            r2.keys(pd.concat([d["frame"], d["frame"].iloc[:1]]), "CAMPAIGN_ID")

    def test_16_provenance_has_21_exact_source_mappings(self):
        rows = self.lock["standardization_provenance"]
        self.assertEqual(rows, r2.standardization_provenance(self.designs))
        self.assertEqual(len(rows), 21)
        self.assertEqual({r["SOURCE_COLUMN"] for r in rows}, {"RAIN_Z", "TMAX_Z", "TMIN_Z"})
        self.assertTrue(all(r["SOURCE_SHA256"] == r2.FROZEN_HASHES[r["SOURCE_FILE"]] for r in rows))

    def test_17_actual_z_values_equal_frozen_source_columns(self):
        for code, d in self.designs.items():
            period = r2.ed1.CROPS[code]["period_column"]
            path = r2.ed1.TRANSIENT_PATH if code in r2.er2p.TRANSIENT else r2.ed1.PERENNIAL_PATH
            raw = pd.read_parquet(path)
            raw = raw[raw["COD_CULTIVO"] == code].copy()
            raw[period] = raw[period].astype(str)
            for i, column in enumerate(d["columns"]):
                window = r2.er1.window_for_variable(r2.ed1.CROPS[code], column)
                source = raw[raw["WINDOW_ID"] == window].set_index(["UBIGEO", period])
                expected = source.loc[pd.MultiIndex.from_frame(d["frame"][["UBIGEO", period]]), r2.ed1.FAMILIES[r2.FAMILY][i % 3]]
                np.testing.assert_array_equal(expected.to_numpy(), d["frame"][column].to_numpy())

    def test_18_no_outcome_driven_standardization(self):
        for row in self.lock["standardization_provenance"]:
            self.assertFalse(row["REFERENCE_PERIOD_SELECTED_USING_OUTCOMES"])
            self.assertEqual(row["REFERENCE_POPULATION"], "WHOLE_DISTRICT_UBIGEO_X_CALENDAR_MONTH_1991_2020_30_ANNUAL_VALUES")

    def test_19_no_z_recomputation(self):
        self.assertFalse(self.lock["standardization_recomputed"])
        self.assertTrue(all(not r["STANDARDIZATION_RECOMPUTED"] for r in self.lock["standardization_provenance"]))
        source = ast.parse((ROOT / r2.SCRIPT_REL).read_text(encoding="utf-8"))
        names = [n.func.attr for n in ast.walk(source) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)]
        self.assertNotIn("zscore", names)
        self.assertNotIn("StandardScaler", names)

    def test_20_same_y_and_fe_bytes(self):
        for code, d in self.designs.items():
            period = r2.ed1.CROPS[code]["period_column"]
            np.testing.assert_array_equal(d["frame"]["YIELD"], d["primary"]["YIELD"])
            np.testing.assert_array_equal(r2.ed1.fe_matrix(d["frame"], period), r2.ed1.fe_matrix(d["primary"], period))
            self.assertEqual(r2.array_sha(d["frame"]["YIELD"]), self.lock["sample_identity"][code]["outcome_sha256"])

    def test_21_native_y_equals_authoritative_outcomes(self):
        t, p, _ = r2.er1.read_outcome_sources()
        for code, d in self.designs.items():
            if code in r2.er2p.TRANSIENT:
                source = t[t["CROP_CODE"] == code].set_index(["UBIGEO", "CAMPAIGN"])["TRANSIENT_CAMPAIGN_YIELD_RAW"]
            else:
                source = p[p["COD_CULTIVO"] == code].copy()
                source["ANO"] = source["ANO"].astype(int).astype(str)
                source = source.set_index(["UBIGEO", "ANO"])["YIELD_RAW"]
            expected = [source.loc[tuple(key)] for key in self.lock["sample_identity"][code]["er1_ordered_keys"]]
            np.testing.assert_array_equal(expected, d["frame"]["YIELD"])

    def test_22_windows_form_weighting_clustering_frozen(self):
        for code, c in self.lock["exact_model_contracts"].items():
            self.assertEqual(c["windows"], list(r2.ed1.CROPS[code]["windows"]))
            self.assertEqual((c["functional_form"], c["weighting"], c["cluster"]), ("LINEAR_ADDITIVE", "UNWEIGHTED", "UBIGEO"))
            self.assertEqual((c["district_fe"], c["period_fe"]), ("REQUIRED", "REQUIRED"))

    def test_23_lemon_joint_t_and_lag_exact(self):
        self.assertEqual(self.lock["exact_model_contracts"]["13010170102"]["regressors"],
                         ["RAIN_Z__T", "TMAX_Z__T", "TMIN_Z__T", "RAIN_Z__T_MINUS_1", "TMAX_Z__T_MINUS_1", "TMIN_Z__T_MINUS_1"])

    def test_24_banana_joint_t_and_lag_exact(self):
        self.assertEqual(self.lock["exact_model_contracts"]["15010040000"]["regressors"],
                         ["RAIN_Z__T", "TMAX_Z__T", "TMIN_Z__T", "RAIN_Z__T_MINUS_1", "TMAX_Z__T_MINUS_1", "TMIN_Z__T_MINUS_1"])

    def test_25_holm_independently_recomputed_within_crop(self):
        for code in r2.ed1.CROPS:
            rows = [r for r in self.coefficients if r["CROP_CODE"] == code]
            ordered = sorted(range(len(rows)), key=lambda i: rows[i]["P_TWO_SIDED"])
            running = 0.
            for rank, i in enumerate(ordered):
                running = min(1., max(running, (len(rows) - rank) * rows[i]["P_TWO_SIDED"]))
                self.assertEqual(rows[i]["HOLM_P"], running)
                self.assertEqual(rows[i]["HOLM_FAMILY_SIZE"], len(rows))

    def test_26_ci_unadjusted_satterthwaite_formula(self):
        for r in self.coefficients:
            width = stats.t.ppf(.975, r["SATTERTHWAITE_DF"]) * r["CR2_SE"]
            self.assertEqual(r["CI95_LOWER"], r["BETA"] - width)
            self.assertEqual(r["CI95_UPPER"], r["BETA"] + width)
            self.assertEqual(r["CI_SEMANTICS"], r2.CI_SEMANTICS)

    def test_27_no_adjusted_ci_or_global_fwer(self):
        self.assertEqual(self.lock["global_fwer"], "NOT_CLAIMED")
        self.assertEqual(self.lock["multiplicity_adjusted_confidence_intervals"], "NOT_CONSTRUCTED_NOT_CLAIMED")

    def test_28_native_y_not_fully_standardized_effect(self):
        self.assertEqual(self.lock["interpretation"], r2.INTERPRETATION)
        self.assertFalse(self.lock["interpretation_and_execution_firewall"]["Y_STANDARDIZED"])
        self.assertFalse(self.lock["interpretation_and_execution_firewall"]["FULLY_STANDARDIZED_EFFECT"])
        self.assertTrue(all(c["outcome"] == "YIELD_LEVEL_TM_PER_HA" for c in self.lock["exact_model_contracts"].values()))

    def test_29_magnitude_ranking_not_authorized(self):
        self.assertEqual(self.lock["interpretation_and_execution_firewall"]["CROSS_CROP_COEFFICIENT_MAGNITUDE_RANKING"], "NOT_AUTHORIZED")

    def test_30_significance_ranking_not_authorized(self):
        self.assertEqual(self.lock["interpretation_and_execution_firewall"]["CROSS_CROP_SIGNIFICANCE_RANKING"], "NOT_AUTHORIZED")

    def test_31_no_primary_replacement(self):
        self.assertTrue(all(r["PRIMARY_REPLACEMENT"] == "PROHIBITED" for r in self.coefficients))
        self.assertEqual(self.lock["er1_numerical_results_identity"], r2.er2p.NUMERICAL_IDENTITY)

    def test_32_no_special_banana_lemon_models_or_subset_aht(self):
        self.assertEqual(Counter(r["CROP_CODE"] for r in self.joint), {c: 1 for c in r2.ed1.CROPS})
        for r in self.joint:
            self.assertEqual(r["NULL"], "=".join(self.lock["exact_model_contracts"][r["CROP_CODE"]]["regressors"]) + "=0")

    def test_33_er1_reference_betas_and_signs_exact(self):
        raw = list(csv.DictReader(io.StringIO((ROOT / r2.er1.COEFFICIENTS_REL).read_text(encoding="utf-8"))))
        refs = {(r["CROP_CODE"], r["CLIMATE_VARIABLE"]): float(r["BETA"]) for r in raw}
        for r in self.coefficients:
            self.assertEqual(r["ER1_BETA_REFERENCE"], refs[(r["CROP_CODE"], r["ER1_VARIABLE"])])
            self.assertEqual(r["ER1_SIGN"], int(np.sign(r["ER1_BETA_REFERENCE"])))
            self.assertEqual(r["R2_SIGN"], int(np.sign(r["BETA"])))
            self.assertEqual(r["SIGN_AGREEMENT"], r["ER1_SIGN"] == r["R2_SIGN"])

    def test_34_positive_scalar_diagnostic_fixture(self):
        x = np.array([-4., -1., 2., 3.])
        self.assertEqual(r2.transformation_relation(x, x / 2)["STANDARDIZATION_RELATION_TO_PHYSICAL_ANOMALY"], "PURE_POSITIVE_SCALAR_RESCALING")

    def test_35_local_scale_diagnostic_fixture(self):
        x = np.array([-4., -1., 2., 3.])
        result = r2.transformation_relation(x, x / np.array([2., 3., 4., 5.]))
        self.assertEqual(result["STANDARDIZATION_RELATION_TO_PHYSICAL_ANOMALY"], "LOCALLY_VARYING_STANDARDIZATION_TRANSFORMATION")
        self.assertFalse(result["OUTCOMES_USED_IN_DIAGNOSTIC"])
        self.assertFalse(result["DIAGNOSTIC_ALTERS_R2"])

    def test_36_numerical_policy_frozen_before_results(self):
        self.assertEqual(self.lock["numerical_policy"], r2.NUMERICAL_POLICY)
        self.assertEqual(r2.NUMERICAL_POLICY["beta_relative_l2"], 1e-10)
        self.assertEqual(r2.NUMERICAL_POLICY["covariance_relative_frobenius"], 1e-6)
        self.assertEqual(r2.NUMERICAL_POLICY["ed1_absolute_alarm"], 1e-8)
        self.assertFalse(r2.NUMERICAL_POLICY["post_result_tolerance_change"])

    def test_37_all_five_independent_numerical_paths_pass(self):
        self.assertEqual(set(self.lock["independent_numerical_verification"]), set(r2.ed1.CROPS))
        for value in self.lock["independent_numerical_verification"].values():
            self.assertEqual(value["status"], "PASS")
            self.assertEqual(len(value["paths"]), 2)
            self.assertTrue(value["scale_aware"]["rank_agreement"])
            self.assertTrue(value["scale_aware"]["cr2_singularity_status_agreement"])

    def test_38_absolute_and_scale_aware_discrepancies_preserved(self):
        for v in self.lock["independent_numerical_verification"].values():
            self.assertEqual(len(v["absolute_discrepancies"]), 9)
            self.assertIn("satterthwaite_df_max_component_relative", v["scale_aware"]["metrics"])
            self.assertIn("covariance", v["main"])
            self.assertIn("covariance", v["reference"])

    def test_39_large_relative_error_is_not_certified(self):
        v = self.lock["independent_numerical_verification"]["14010020000"]
        first, second = json.loads(json.dumps(v["main"])), json.loads(json.dumps(v["reference"]))
        for item in (first, second):
            item["singularities"] = item.pop("cr2_singularities")
            for field in ("beta", "covariance", "satterthwaite_df"):
                item[field] = np.array(item[field])
        second["beta"] *= 1.01
        self.assertEqual(r2.r1a.compare_paths(first, second)["status"], "FAIL")

    def test_40_coefficient_p_and_t_formulas(self):
        for r in self.coefficients:
            self.assertEqual(r["T"], r["BETA"] / r["CR2_SE"])
            self.assertEqual(r["P_TWO_SIDED"], 2 * stats.t.sf(abs(r["T"]), r["SATTERTHWAITE_DF"]))

    def test_41_aht_p_formula(self):
        for r in self.joint:
            self.assertEqual(r["P"], stats.f.sf(r["F"], r["NUMERATOR_DF"], r["DENOMINATOR_DF"]))

    def test_42_r3_to_r6_not_executed(self):
        for tier in ("R3", "R4", "R5", "R6"):
            self.assertEqual(self.lock["interpretation_and_execution_firewall"][tier], "NOT_EXECUTED")
        self.assertFalse(self.lock["interpretation_and_execution_firewall"]["R3_ADAPTER_IMPLEMENTED"])

    def test_43_downstream_not_executed(self):
        for name in ("BOOTSTRAP", "CONLEY", "LOO", "B3", "ENSO_SCENARIOS", "GVP", "VAR_CVAR", "A1_A2", "OPTIMIZATION"):
            self.assertEqual(self.lock["interpretation_and_execution_firewall"][name], "NOT_EXECUTED")

    def test_44_next_tier_not_authorized(self):
        self.assertEqual(self.lock["NEXT_TIER_AUTHORIZATION_STATUS"], "NOT_AUTHORIZED")
        self.assertEqual(self.lock["interpretation_and_execution_firewall"]["R3_AUTHORIZATION_STATUS"], "NOT_AUTHORIZED")

    def test_45_two_independent_process_hashes_equal(self):
        rep = self.lock["reproducibility"]
        self.assertEqual(rep["status"], "PASS")
        self.assertEqual(rep["independent_processes"], 2)
        self.assertEqual(rep["calculation_run1_sha256"], rep["calculation_run2_sha256"])
        self.assertEqual(rep["provenance_run1_sha256"], rep["provenance_run2_sha256"])
        self.assertEqual(rep["provenance_run1_sha256"], r2.sha(self.payloads[r2.PROVENANCE_REL]))

    def test_46_canonical_json_lock_and_non_circular_hash(self):
        self.assertEqual(self.payloads[r2.LOCK_REL], r2.json_bytes(self.lock))
        self.assertNotIn(r2.LOCK_REL.as_posix(), self.lock["artifact_sha256"])
        self.assertNotIn("ER2_R2_RESULTS_LOCK_SHA256", self.lock)

    def test_47_utf8_lf_no_bom_one_final_lf(self):
        for payload in [*self.payloads.values(), (ROOT / r2.SCRIPT_REL).read_bytes(), (ROOT / r2.TEST_REL).read_bytes()]:
            r2.require_byte_contract(payload)
            self.assertNotIn(b"\r", payload)
            self.assertFalse(payload.endswith(b"\n\n"))

    def test_48_no_runtime_timestamps_or_absolute_paths(self):
        for payload in self.payloads.values():
            self.assertNotIn(str(ROOT).encode("utf-8"), payload)
            self.assertNotIn(b"C:/Users/", payload)
        for forbidden_key in ("timestamp", "generated_at", "created_at", "runtime_seconds"):
            self.assertNotIn(('"' + forbidden_key + '":').encode("utf-8"), self.payloads[r2.LOCK_REL])

    def test_49_output_hash_manifest_exact(self):
        for rel, expected in self.lock["artifact_sha256"].items():
            self.assertEqual(r2.sha(self.payloads[Path(rel)]), expected)
        self.assertEqual(self.lock["implementation_sha256"], r2.INITIAL_SCRIPT_SHA)
        self.assertEqual(self.lock["test_sha256"], r2.INITIAL_TEST_SHA)
        self.assertEqual(self.certified["implementation_sha256"], r2.sha((ROOT / r2.SCRIPT_REL).read_bytes()))
        self.assertEqual(self.certified["test_sha256"], r2.sha((ROOT / r2.TEST_REL).read_bytes()))

    def test_50_existing_published_artifacts_exact(self):
        for rel, payload in self.payloads.items():
            if rel == r2.REPORT_REL:
                self.assertIn((ROOT / rel).read_bytes(), (payload, self.reporting_payloads[rel]))
            else:
                self.assertEqual((ROOT / rel).read_bytes(), payload)
        if (ROOT / r2.REPORTING_LOCK_REL).exists():
            self.assertEqual((ROOT / r2.REPORTING_LOCK_REL).read_bytes(), self.reporting_payloads[r2.REPORTING_LOCK_REL])

    def test_51_existing_identical_artifact_not_rewritten(self):
        path = self.output / r2.REPORTING_LOCK_REL
        before = path.stat().st_mtime_ns
        r2.write_exact(path, self.reporting_payloads[r2.REPORTING_LOCK_REL])
        self.assertEqual(before, path.stat().st_mtime_ns)

    def test_52_different_artifact_overwrite_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "refusing to overwrite"):
            r2.write_exact(self.output / r2.REPORTING_LOCK_REL, b"different\n")

    def test_53_nested_repository_output_and_worker_root_rejected(self):
        for path, worker in ((ROOT / "outputs/nested", False), (ROOT, True)):
            with self.assertRaisesRegex(RuntimeError, "nested repository output root"):
                r2.check_destination(path, worker)

    def test_54_exact_eight_candidate_paths_no_git_changes(self):
        self.assertEqual(len(r2.CANDIDATE_RELS), 8)
        self.assertEqual(set(r2.REPORTING_CANDIDATE_RELS) - set(r2.CANDIDATE_RELS), {r2.REPORTING_LOCK_REL})
        self.assertEqual(r2.git("diff", "--name-only"), "")
        self.assertEqual(r2.git("diff", "--cached", "--name-only"), "")
        self.assertTrue(set(r2.git("ls-files", "--others", "--exclude-standard").splitlines()) <= {p.as_posix() for p in r2.REPORTING_CANDIDATE_RELS})

    def test_55_forbidden_r3_result_rejected(self):
        with patch.object(r2.er2p, "forbidden_result_paths", return_value=["outputs/econometrics/ER2_R3_RESULTS.csv"]):
            with self.assertRaisesRegex(RuntimeError, "unauthorized tier artifact"):
                r2.preflight()

    def test_56_provenance_written_before_first_estimation(self):
        events = []
        actual_write = r2.write_exact
        def record_write(path, payload):
            events.append(path.name)
            actual_write(path, payload)
        def stop_before_fit(*args):
            self.assertEqual(events, [r2.PROVENANCE_REL.name])
            raise RuntimeError("PRE_ESTIMATION_TEST_STOP")
        with tempfile.TemporaryDirectory(prefix="r2-order-test-") as temp:
            with patch.object(r2, "preflight", return_value=self.pre), patch.object(r2, "prepare_designs", return_value=(self.designs, {})), patch.object(r2, "write_exact", side_effect=record_write), patch.object(r2, "calculate", side_effect=stop_before_fit):
                with self.assertRaisesRegex(RuntimeError, "PRE_ESTIMATION_TEST_STOP"):
                    r2.worker(Path(temp))

    def test_57_no_final_exposure_unit_sd_claim(self):
        self.assertTrue(all(not r["FINAL_ANALYTICAL_X_UNIT_SD_CLAIMED"] for r in self.lock["standardization_provenance"]))
        self.assertIn("not asserted to have unit SD", self.payloads[r2.REPORT_REL].decode("utf-8"))

    def test_58_missing_column_and_nonfinite_x_rejected(self):
        d = self.designs["14010020000"]
        for broken in (d["frame"].drop(columns=d["columns"][0]), d["frame"].assign(RAIN_Z=np.inf)):
            with self.assertRaisesRegex(RuntimeError, "missing standardized X"):
                r2.align_standardized(d["primary"], broken, d["columns"], "CAMPAIGN_ID")

    def test_59_byte_contract_rejects_cr_bom_and_double_final_lf(self):
        for payload in (b"x\r\n", b"x\r\n\n", b"x\n\n", b"\xef\xbb\xbfx\n", b"x"):
            with self.assertRaises(RuntimeError):
                r2.require_byte_contract(payload)

    def test_60_completion_requires_numerical_pass_not_significance(self):
        self.assertEqual(self.lock["completion_status"], r2.PASS)
        self.assertEqual(self.lock["scientific_lock_status"], "RESULTS_LOCKED_PENDING_DIRECTOR_REVIEW")
        self.assertTrue(all(v["status"] == "PASS" for v in self.lock["independent_numerical_verification"].values()))
        self.assertEqual(self.lock["next_action"], "RETURN_TO_SCIENTIFIC_DIRECTOR_FOR_R2_REVIEW")

    def test_61_r2r_four_csv_hashes_exact(self):
        for path in (r2.RESULTS_REL, r2.JOINT_REL, r2.SAMPLE_REL, r2.PROVENANCE_REL):
            self.assertEqual(r2.sha((ROOT / path).read_bytes()), r2.PROTECTED_R2_HASHES[path])

    def test_62_r2r_initial_lock_and_report_identity(self):
        self.assertEqual(r2.sha((ROOT / r2.LOCK_REL).read_bytes()), r2.INITIAL_LOCK_SHA)
        self.assertEqual(self.certified["R2_INITIAL_RESULTS_LOCK_SHA256"], r2.INITIAL_LOCK_SHA)
        self.assertEqual(r2.sha(self.payloads[r2.REPORT_REL]), r2.INITIAL_REPORT_SHA)

    def test_63_r2r_protected_bytes_and_mtimes_not_changed(self):
        for path, (payload, mtime) in self.protected_before.items():
            self.assertEqual((ROOT / path).read_bytes(), payload)
            self.assertEqual((ROOT / path).stat().st_mtime_ns, mtime)

    def test_64_r2r_corrected_index_interpretation_exact(self):
        self.assertEqual(self.certified["R2R_CORRECTED_INTERPRETATION"],
            "ONE_UNIT_INCREASE_IN_PHENOLOGY_ALIGNED_STANDARDIZED_ANOMALY_EXPOSURE_INDEX_IN_NATIVE_CROP_YIELD_UNITS")
        self.assertIn(r2.CORRECTED_INTERPRETATION.encode("utf-8"), self.reporting_payloads[r2.REPORT_REL])

    def test_65_r2r_human_interpretation_and_aggregation_caveat(self):
        report = self.reporting_payloads[r2.REPORT_REL].decode("utf-8")
        self.assertIn(r2.HUMAN_INTERPRETATION, report)
        self.assertIn(r2.INDEX_CLARIFICATION, report)
        self.assertIn("not claimed to equal one empirical standard deviation", report)

    def test_66_r2r_exact_monthly_reference_definition(self):
        self.assertEqual(self.certified["MONTHLY_FORMULA"], r2.MONTHLY_FORMULA)
        self.assertEqual((self.certified["REFERENCE_PERIOD"], self.certified["REFERENCE_ANNUAL_VALUES"], self.certified["SAMPLE_SD_DDOF"]), ("1991-2020", 30, 1))
        self.assertTrue(self.certified["MONTHLY_COMPONENTS_STANDARDIZED_LOCALLY"])
        self.assertFalse(self.certified["OUTCOME_BASED_SELECTION"])

    def test_67_r2r_exact_aggregation_semantics(self):
        self.assertEqual(self.certified["PERENNIAL_FINAL_R2_X"], "ARITHMETIC_MEAN_OF_MONTHLY_LOCAL_Z_WITHIN_FROZEN_WINDOW")
        self.assertEqual(self.certified["TRANSIENT_FINAL_R2_X"], "MONTHLY_LOCAL_Z_TO_COHORT_WINDOW_MEAN_Z_TO_POSITIVE_OBSERVED_UNAMBIGUOUS_SIEMBRA_WEIGHTED_AGGREGATION")
        self.assertFalse(self.certified["R2_STANDARDIZATION_RECOMPUTED"])

    def test_68_r2r_final_x_sd_one_not_claimed(self):
        self.assertFalse(self.certified["FINAL_ANALYTICAL_X_UNIT_SD_CLAIMED"])
        self.assertEqual(self.certified["FINAL_ANALYTICAL_EXPOSURE_STANDARD_DEVIATION_EQUALS_ONE"], "NOT_CLAIMED")

    def test_69_r2r_historical_shorthand_not_rewritten(self):
        self.assertEqual(self.certified["ED1_ORIGINAL_INTERPRETATION_LABEL"], r2.INTERPRETATION)
        self.assertEqual(self.lock["interpretation"], r2.INTERPRETATION)
        self.assertEqual(self.certified["R2R_REPORTING_CLARIFICATION"], r2.REPORTING_CLARIFICATION)

    def test_70_r2r_no_fully_standardized_effect_or_ranking(self):
        for key in ("Y_STANDARDIZED", "FULLY_STANDARDIZED_EFFECT"):
            self.assertFalse(self.certified[key])
        for key in ("CROSS_CROP_EFFECT_SIZE_COMPARABILITY", "CROSS_CROP_COEFFICIENT_MAGNITUDE_RANKING", "CROSS_CROP_SIGNIFICANCE_RANKING"):
            self.assertEqual(self.certified[key], "NOT_AUTHORIZED")

    def test_71_r2r_12_sign_changes_and_9_agreements(self):
        self.assertEqual(sum(not r["SIGN_AGREEMENT"] for r in self.coefficients), 12)
        self.assertEqual(sum(r["SIGN_AGREEMENT"] for r in self.coefficients), 9)
        self.assertEqual(self.certified["ER1_R2_SIGN_CHANGES"], 12)
        self.assertEqual(self.certified["ER1_R2_SIGN_AGREEMENTS"], 9)
        self.assertEqual(self.certified["SIGN_CHANGE_INTERPRETATION"], "EXPOSURE_DEFINITION_SENSITIVITY_DESCRIPTIVE_ONLY")
        self.assertFalse(self.certified["GLOBAL_POSITIVE_SCALAR_REEXPRESSION_OF_ER1"])
        self.assertEqual(self.certified["SIGN_T_STATISTIC_P_VALUE_INVARIANCE"], "NOT_EXPECTED")

    def test_72_r2r_exact_sole_holm_survivor(self):
        rows = self.certified["HOLM_SURVIVORS"]
        self.assertEqual(rows, [r for r in self.coefficients if r["HOLM_P"] < .05])
        self.assertEqual(len(rows), 1)
        self.assertEqual((rows[0]["CROP"], rows[0]["VARIABLE"]), ("PLATANOS_Y_BANANAS", "RAIN_Z__T_MINUS_1"))
        self.assertEqual((rows[0]["BETA"], rows[0]["P_TWO_SIDED"], rows[0]["HOLM_P"]), (-6.712270305566657, .0008485894443823592, .005091536666294155))

    def test_73_r2r_all_five_aht_values_no_new_multiplicity(self):
        self.assertEqual({r["CROP_CODE"]:r["P"] for r in self.certified["AHT_CERTIFICATION"]}, r2.EXPECTED_AHT_P)
        self.assertEqual(self.certified["AHT_P_ADJUSTMENT"], "NONE")
        self.assertEqual(self.certified["CROSS_CROP_AHT_MULTIPLICITY_FAMILY"], "NOT_AUTHORIZED")

    def test_74_r2r_joint_individual_distinctions(self):
        rows = {r["CROP_CODE"]:r for r in self.certified["AHT_CERTIFICATION"]}
        for code in ("13010210000", "13010170102"):
            self.assertTrue(rows[code]["P_LT_0_05"])
            self.assertEqual(rows[code]["WITHIN_CROP_HOLM_SURVIVORS"], 0)
        self.assertFalse(rows["15010040000"]["P_LT_0_05"])
        self.assertEqual(rows["15010040000"]["WITHIN_CROP_HOLM_SURVIVORS"], 1)
        self.assertEqual(self.certified["JOINT_INDIVIDUAL_DISTINCTION"], "DIFFERENT_NULL_HYPOTHESES_NOT_LOGICALLY_CONTRADICTORY")

    def test_75_r2r_same_banana_channel_claim_prohibited(self):
        self.assertEqual(self.certified["ER1_BANANA_INDIVIDUAL_COMPONENT"], "TMIN_ANOM_C__T_MINUS_1")
        self.assertEqual(self.certified["R2_BANANA_HOLM_SURVIVING_COMPONENT"], "RAIN_Z__T_MINUS_1")
        self.assertEqual(self.certified["SAME_BANANA_CHANNEL_ROBUSTLY_CONFIRMED"], "PROHIBITED")
        self.assertEqual(self.certified["BANANA_ALLOWED_STATEMENT"], r2.BANANA_COMPONENT_STATEMENT)

    def test_76_r2r_er1_remains_primary(self):
        self.assertEqual(self.certified["PRIMARY_SPECIFICATION"], "ER1_PHYSICAL_ANOMALY")
        self.assertEqual(self.certified["R2_ROLE"], "SECONDARY_STANDARDIZED_EXPOSURE_SENSITIVITY")
        self.assertEqual(self.certified["PRIMARY_REPLACEMENT"], "PROHIBITED")
        self.assertEqual(self.certified["R2_FREEZE_AUTHORIZED"], "NO")

    def test_77_r2r_next_tiers_and_downstream_not_authorized(self):
        self.assertEqual(self.certified["NEXT_TIER_AUTHORIZATION_STATUS"], "NOT_AUTHORIZED")
        self.assertEqual(self.certified["EXECUTION_FIREWALL"]["R3_AUTHORIZATION_STATUS"], "NOT_AUTHORIZED")
        for name in ("R3", "R4", "R5", "R6", "BOOTSTRAP", "CONLEY", "LOO", "B3", "ENSO_SCENARIOS", "GVP", "VAR_CVAR", "A1_A2", "OPTIMIZATION"):
            self.assertEqual(self.certified["EXECUTION_FIREWALL"][name], "NOT_EXECUTED")

    def test_78_r2r_two_reporting_runs_and_canonical_bytes(self):
        rep = self.certified["reproducibility"]
        self.assertEqual(rep["status"], "PASS")
        self.assertEqual(rep["independent_processes"], 2)
        self.assertEqual(rep["run1_basis_sha256"], rep["run2_basis_sha256"])
        self.assertEqual(rep["r2_models_reestimated"], 0)
        for b in self.reporting_payloads.values():
            r2.require_byte_contract(b)
        self.assertEqual(r2.json_bytes(self.certified), self.reporting_payloads[r2.REPORTING_LOCK_REL])
        self.assertEqual(self.certified["corrected_report_sha256"], r2.sha(self.reporting_payloads[r2.REPORT_REL]))

    def test_79_r2r_legacy_reestimation_entrypoints_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "re-estimation prohibited"):
            r2.build(self.output)
        cli = subprocess.run([sys.executable, str(ROOT / r2.SCRIPT_REL), "--worker", "--output-root", str(self.output)], cwd=ROOT, capture_output=True, text=True)
        self.assertNotEqual(cli.returncode, 0)
        self.assertIn("numerical worker prohibited", cli.stderr)

    def test_80_r2r_reporting_worker_never_prepares_or_estimates_models(self):
        with tempfile.TemporaryDirectory(prefix="r2r-no-fit-") as temp:
            with patch.object(r2, "prepare_designs", side_effect=AssertionError("No design reconstruction")), patch.object(r2, "calculate", side_effect=AssertionError("No model estimation")), patch.object(r2, "numerical_verification", side_effect=AssertionError("No numerical rerun")):
                r2.reporting_worker(Path(temp))
                self.assertTrue((Path(temp) / "reporting_basis.json").exists())

    def test_81_r2r_csv_hash_drift_stops(self):
        with patch.dict(r2.PROTECTED_R2_HASHES, {r2.RESULTS_REL: "0" * 64}):
            with self.assertRaisesRegex(RuntimeError, "ER2_R2R_FAIL_NUMERICAL_OR_PROVENANCE_DRIFT"):
                r2.reporting_basis()

    def test_82_r2r_separate_lock_no_circular_hash(self):
        self.assertNotEqual(r2.LOCK_REL, r2.REPORTING_LOCK_REL)
        self.assertNotIn("R2_REPORTING_CERTIFIED_LOCK_SHA256", self.certified)
        self.assertEqual(self.certified["immutable_r2_sha256"], {p.as_posix():h for p,h in r2.PROTECTED_R2_HASHES.items()})

    def test_83_r2r_no_coefficient_aht_sample_or_model_change(self):
        for field, key in (("coefficient_inventory", "coefficient_inventory_sha256"), ("aht_joint_tests", "aht_inventory_sha256"), ("sample_identity", "sample_identity_sha256"), ("exact_model_contracts", "model_contracts_sha256")):
            self.assertEqual(r2.sha(r2.json_bytes(self.lock[field])), self.certified[key])
        for key in ("R2_NUMERICAL_RESULT_CHANGE", "R2_SAMPLE_CHANGE", "R2_STANDARDIZATION_CHANGE", "R2_MODEL_CHANGE"):
            self.assertFalse(self.certified[key])
        self.assertTrue(self.certified["R2_REPORTING_SEMANTICS_HARDENED"])

    def test_84_r2r_preflight_cli_read_only(self):
        before = {p: ((ROOT / p).read_bytes(), (ROOT / p).stat().st_mtime_ns) for p in r2.REPORTING_CANDIDATE_RELS if (ROOT / p).exists()}
        cli = subprocess.run([sys.executable, str(ROOT / r2.SCRIPT_REL), "--preflight-only"], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(cli.returncode, 0, cli.stderr)
        self.assertEqual(json.loads(cli.stdout)["status"], "PASS")
        self.assertEqual(before, {p: ((ROOT / p).read_bytes(), (ROOT / p).stat().st_mtime_ns) for p in before})


if __name__ == "__main__":
    unittest.main(verbosity=2)
