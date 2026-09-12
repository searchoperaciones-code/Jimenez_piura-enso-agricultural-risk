from __future__ import annotations

import copy
import inspect
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
import er2_r6p_b3_strict_preflight_v1 as r6


class R6PreflightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        r6.require_plan(ROOT)
        cls.frame = r6.synthetic_fixture()
        cls.keys = r6.key_set(cls.frame)
        cls.fit = r6.ed1.fit_two_way_fe_cr2(cls.frame, list(r6.X), "CAMPAIGN_ID", cls.frame[r6.Y].to_numpy())
        cls.result = r6.synthetic_adapter(cls.frame, cls.keys)

    def test_01_parent_and_candidate_scope(self):
        self.assertEqual(r6.predecessor()["head"], r6.PARENT)
        actual = r6.git("ls-files", "--others", "--exclude-standard").decode().splitlines()
        self.assertEqual(set(actual), set(r6.CANDIDATES))
        self.assertEqual(len(actual), 7)

    def test_02_frozen_contracts(self):
        protocol, tier, hierarchy = r6.contracts()
        self.assertEqual(r6.sha(r6.payload(tier)), r6.TIER_SHA)
        self.assertEqual(tier["order"], 6)
        self.assertEqual(tier["previous_tier"], "R5")
        self.assertIsNone(tier["next_tier"])
        self.assertEqual(hierarchy["NO_WINNER_RULE"], "B3_CANNOT_REPLACE_PRIMARY_OR_WEAKEN_FE")
        self.assertEqual(len(protocol["crop_model_contracts"]), 5)

    def test_03_estimator_loaded_identity(self):
        identity = r6.estimator_identity()
        self.assertEqual(identity["scientific_sha256"], r6.FROZEN_SHA[r6.ESTIMATOR])
        self.assertFalse(identity["mathematical_alteration"])

    def test_04_metadata_projection_firewall(self):
        table_reader, csv_reader = r6.pq.read_table, r6.pd.read_csv
        calls = []

        def parquet(path, **kwargs):
            self.assertEqual(kwargs, {"columns": list(r6.B3_META)})
            self.assertFalse(set(r6.X) & set(kwargs["columns"]))
            calls.append("B3_PROJECTED")
            return table_reader(path, **kwargs)

        def csv(path, **kwargs):
            if kwargs.get("nrows") == 0:
                self.assertEqual(kwargs, {"nrows": 0})
                calls.append("D0_SCHEMA")
            else:
                self.assertEqual(kwargs, {"usecols": list(r6.D0_META), "dtype": str})
                self.assertNotIn(r6.Y, kwargs["usecols"])
                calls.append("D0_PROJECTED")
            return csv_reader(path, **kwargs)

        with patch.object(r6.pq, "read_table", side_effect=parquet), patch.object(r6.pd, "read_csv", side_effect=csv):
            meta = r6.metadata_only()
        self.assertEqual(calls, ["D0_SCHEMA", "B3_PROJECTED", "D0_PROJECTED"])
        self.assertEqual(meta["inventory"], dict(total=745, valid=38, invalid=707, rice=31, mad=7))
        self.assertEqual([meta["support"][0][x] for x in ("INTERSECTION_N", "DISTRICTS", "PERIODS")], [31, 12, 7])
        self.assertEqual(len(meta["intersection_keys"][r6.RICE]), 31)
        self.assertEqual(meta["support"][1]["STATUS"], r6.MAD_STATUS)
        for row in meta["support"][2:]:
            self.assertIsNone(row["INTERSECTION_N"])
            self.assertEqual(row["STATUS"], "NOT_APPLICABLE")

    def test_05_plan_precedes_synthetic(self):
        self.assertEqual(r6.require_plan(ROOT), r6.sha(r6.payload(r6.synthetic_plan())))
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(FileNotFoundError):
                r6.synthetic_fixture(directory)
            r6.write_plan(directory)
            self.assertEqual(len(r6.synthetic_fixture(directory)), 31)

    def test_06_plan_tampering_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            r6.write_plan(directory)
            (Path(directory) / r6.PLAN).write_bytes(b"{}\n")
            with self.assertRaisesRegex(RuntimeError, "PLAN"):
                r6.synthetic_fixture(directory)

    def test_07_admissible_all_ten_gates(self):
        self.assertEqual(self.result["status"], r6.ADMISSIBLE)
        self.assertEqual(self.result["failed_gates"], [])
        self.assertEqual(self.result["support"], dict(n=31, districts=12, periods=7, within_rank=3, design_rank=21, design_columns=21))
        self.assertEqual(len(self.result["coefficients"]), 3)
        self.assertTrue(all(row["CR2_SE"] > 0 and row["SATTERTHWAITE_DF"] > 0 for row in self.result["coefficients"]))
        self.assertGreater(self.result["joint"]["DENOMINATOR_DF"], 0)

    def test_08_independent_full_dummy_reference(self):
        actual = np.array([r["R6_B3_BETA"] for r in self.result["coefficients"]])
        self.assertLessEqual(float(np.max(np.abs(actual - r6.independent_dummy_beta(self.frame)))), 1e-10)

    def test_09_named_mapping_se_df_aht(self):
        for i, row in enumerate(self.result["coefficients"]):
            self.assertEqual(row["VARIABLE"], r6.X[i])
            self.assertEqual(row["CR2_SE"], float(np.sqrt(self.fit["climate_covariance"][i, i])))
            self.assertEqual(row["SATTERTHWAITE_DF"], float(self.fit["satterthwaite_df"][i]))
        for target, source in r6.AHT_MAPPING.items():
            self.assertEqual(self.result["joint"][target], self.fit["aht"][source])

    def test_10_seed_reproducibility(self):
        self.assertTrue(self.frame.equals(r6.synthetic_fixture()))
        plan = r6.synthetic_plan()
        self.assertEqual(plan["seed"], 20260906)
        self.assertEqual(plan["rng"], "NUMPY_GENERATOR_PCG64")
        self.assertEqual(plan["tolerance"], 1e-10)

    def check_case(self, case):
        result = r6.case_result(case, self.frame, self.fit)
        self.assertIn(r6.CASES[case], result["failed_gates"])
        self.assertEqual(result["coefficients"], [])
        self.assertIsNone(result["joint"])
        expected = r6.MAD_STATUS if case == "O" else "NOT_APPLICABLE" if case == "P" else r6.INADMISSIBLE
        self.assertEqual(result["status"], expected)

    def test_11_A_observations(self): self.check_case("A")
    def test_12_B_districts(self): self.check_case("B")
    def test_13_C_periods(self): self.check_case("C")
    def test_14_D_within_rank(self): self.check_case("D")
    def test_15_E_full_design_rank(self):
        self.check_case("E")
        support = r6.case_result("E", self.frame, self.fit)["support"]
        self.assertEqual((support["n"], support["districts"], support["periods"], support["within_rank"]), (31, 12, 7, 3))
    def test_16_F_cr2_adjustment(self): self.check_case("F")
    def test_17_G_nonpositive_se(self): self.check_case("G")
    def test_18_H_nonfinite_se(self): self.check_case("H")
    def test_19_I_df(self): self.check_case("I")
    def test_20_J_aht(self): self.check_case("J")
    def test_21_K_missing_column(self): self.check_case("K")
    def test_22_L_duplicate_key(self): self.check_case("L")
    def test_23_M_invalid_b3(self): self.check_case("M")
    def test_24_N_intersection(self): self.check_case("N")
    def test_25_O_mad(self): self.check_case("O")
    def test_26_P_perennial(self): self.check_case("P")
    def test_27_Q_fe_weakening(self): self.check_case("Q")
    def test_28_R_substitute_model(self): self.check_case("R")

    def test_29_no_real_namespace_execution(self):
        frame = self.frame.copy()
        frame["UBIGEO"] = "200101"
        with patch.object(r6.ed1, "fit_two_way_fe_cr2") as fit:
            with self.assertRaisesRegex(RuntimeError, "REAL_R6_EXECUTION_NOT_AUTHORIZED"):
                r6.synthetic_adapter(frame, r6.key_set(frame))
            fit.assert_not_called()

    def test_30_scope_rejected_before_estimator(self):
        with patch.object(r6.ed1, "fit_two_way_fe_cr2") as fit:
            for crop in (r6.MAD, *r6.PERENNIALS):
                result = r6.synthetic_adapter(self.frame, self.keys, crop=crop)
                self.assertIn(result["status"], (r6.MAD_STATUS, "NOT_APPLICABLE"))
            fit.assert_not_called()

    def test_31_no_retry_or_substitution(self):
        with patch.object(r6.ed1, "fit_two_way_fe_cr2", side_effect=np.linalg.LinAlgError("synthetic failure")) as fit:
            result = r6.synthetic_adapter(self.frame, self.keys)
        self.assertEqual(fit.call_count, 1)
        self.assertEqual(result["status"], r6.INADMISSIBLE)
        self.assertIn("synthetic failure", result["failed_gates"][0])

    def test_32_multiple_failures_no_partial_promotion(self):
        fit = copy.deepcopy(self.fit)
        fit["climate_covariance"][0, 0] = 0
        fit["satterthwaite_df"][1] = -1
        fit["aht"]["p_value"] = 2
        result = r6.extract_inference(fit, self.result["support"])
        for gate in ("POSITIVE_FINITE_SE", "POSITIVE_FINITE_DF", "VALID_FINITE_AHT"):
            self.assertIn(gate, result["failed_gates"])
        self.assertEqual(result["coefficients"], [])
        self.assertIsNone(result["joint"])
        self.assertEqual(result["terminal"], "R6_COMPLETE_WITH_DECLARED_NONADMISSIBILITY")

    def test_33_nonfinite_coefficient_rejected(self):
        fit = copy.deepcopy(self.fit)
        fit["beta"][0] = np.nan
        self.assertIn("FINITE_COEFFICIENT_STATISTICS", r6.extract_inference(fit, {})["failed_gates"])

    def test_34_malformed_mapping_rejected(self):
        for key in ("beta", "climate_covariance", "satterthwaite_df", "aht", "adjustments"):
            with self.subTest(key=key):
                fit = copy.deepcopy(self.fit)
                del fit[key]
                self.assertEqual(r6.extract_inference(fit, {})["status"], r6.INADMISSIBLE)

    def test_35_invalid_adjustment_variants(self):
        for mode in ("negative", "zero_rank", "extra_singularity", "missing_matrix"):
            with self.subTest(mode=mode):
                fit = copy.deepcopy(self.fit)
                if mode == "negative": fit["adjustments"][0] = -np.eye(len(fit["adjustments"][0]))
                if mode == "zero_rank": fit["adjustments"][0][:] = 0
                if mode == "extra_singularity": fit["cr2_adjustment_singularities"] = 1
                if mode == "missing_matrix": fit["adjustments"].pop()
                self.assertIn("CR2_ADJUSTMENTS", r6.extract_inference(fit, {})["failed_gates"])

    def test_36_df_and_aht_domain_rejected(self):
        for value in (0, -1, np.inf, np.nan):
            with self.subTest(df=value):
                fit = copy.deepcopy(self.fit)
                fit["satterthwaite_df"][0] = value
                self.assertIn("POSITIVE_FINITE_DF", r6.extract_inference(fit, {})["failed_gates"])
        for key, value in (("numerator_df", 2), ("denominator_df", 0), ("p_value", -0.1), ("f_statistic", -1), ("delta", 0)):
            with self.subTest(aht=key):
                fit = copy.deepcopy(self.fit)
                fit["aht"][key] = value
                self.assertIn("VALID_FINITE_AHT", r6.extract_inference(fit, {})["failed_gates"])

    def test_37_frozen_model_dimensions(self):
        for key, value in (("district_fe", "REMOVED"), ("regressors", list(r6.X[:2])), ("weighting", "WEIGHTED"), ("district_trends", "INCLUDED")):
            with self.subTest(key=key):
                model = copy.deepcopy(r6.MODEL)
                model[key] = value
                with patch.object(r6.ed1, "fit_two_way_fe_cr2") as fit:
                    result = r6.synthetic_adapter(self.frame, self.keys, model=model)
                    self.assertIn("FROZEN_MODEL", result["failed_gates"])
                    fit.assert_not_called()

    def test_38_validity_and_window_no_relaxation(self):
        for column, value, gate in (("OUTCOME_VALID_FLAG", "FALSE", "VALID_D0_ONLY"), ("FAILURE_REASON", "AMBIGUOUS", "VALID_B3_ONLY"), ("WINDOW_ID", "OTHER", "FROZEN_WINDOW")):
            with self.subTest(column=column):
                frame = self.frame.copy()
                frame.loc[0, column] = value
                self.assertIn(gate, r6.synthetic_adapter(frame, self.keys)["failed_gates"])

    def test_39_static_result_branch_audit(self):
        self.assertEqual(r6.branch_audit()["result_specific_r6_branches"], 0)
        for condition in ("beta[0] > 0", "raw_p < 0.05", "year == 2017", "r5_result == 'PASS'"):
            source = f"def evaluate_frame():\n    if {condition}:\n        return True\n"
            with self.assertRaisesRegex(RuntimeError, "RESULT_SPECIFIC"):
                r6.branch_audit(source)

    def test_40_future_21_dimension_schema(self):
        protocol = json.loads(r6.frozen_bytes(r6.PROTOCOL))
        schema = r6.future_schema(protocol)
        self.assertEqual(len(schema["concordance"]), 21)
        for code, count, status in ((r6.RICE, 3, "R6_RICE_RESULT_WHERE_ADMISSIBLE"), (r6.MAD, 3, r6.MAD_STATUS), (r6.PERENNIALS[0], 3, "NOT_APPLICABLE"), (r6.PERENNIALS[1], 6, "NOT_APPLICABLE"), (r6.PERENNIALS[2], 6, "NOT_APPLICABLE")):
            rows = [r for r in schema["concordance"] if r["CROP_CODE"] == code]
            self.assertEqual(len(rows), count)
            self.assertEqual({r["R6_STATUS"] for r in rows}, {status})
        self.assertFalse(any("HOLM" in f or "VOTE" in f for f in schema["coefficient_fields"]))
        self.assertFalse(schema["nonapplicability_is_failed_robustness"])

    def test_41_byte_contract_and_lock_manifest(self):
        for path in r6.CANDIDATES:
            with self.subTest(path=path):
                data = (ROOT / path).read_bytes()
                data.decode("utf-8")
                self.assertNotIn(b"\r", data)
                self.assertFalse(data.startswith(b"\xef\xbb\xbf"))
                self.assertTrue(data.endswith(b"\n"))
                self.assertFalse(data.endswith(b"\n\n"))
        lock = json.loads((ROOT / r6.LOCK).read_bytes())
        for path, expected in lock["artifact_sha256_excluding_self"].items():
            self.assertEqual(r6.sha((ROOT / path).read_bytes()), expected)
        for name, value in lock["firewall"].items():
            if name.startswith("REAL_R6") and not name.endswith("AUTHORIZATION_STATUS"):
                self.assertIs(value, False)

    def test_42_full_validation_and_sentinel_mapping(self):
        rows, difference, support = r6.synthetic_validation(ROOT)
        self.assertEqual(len(rows), 24)
        self.assertEqual({row["STATUS"] for row in rows}, {"PASS"})
        self.assertLessEqual(difference, r6.TOL)
        self.assertEqual(support["within_rank"], 3)

    def test_43_two_independent_builds(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            for directory in (first, second):
                run = subprocess.run([sys.executable, str(ROOT / r6.SCRIPT), "--output-root", directory], cwd=ROOT, capture_output=True, text=True)
                self.assertEqual(run.returncode, 0, run.stderr)
            for path in r6.GENERATED:
                self.assertEqual((Path(first) / path).read_bytes(), (Path(second) / path).read_bytes())
                self.assertEqual((Path(first) / path).read_bytes(), (ROOT / path).read_bytes())

    def test_44_no_real_loader_entry_point(self):
        source = inspect.getsource(r6)
        self.assertNotIn("read_b3_sensitivity(", source)
        self.assertNotIn("read_parquet(", source)
        self.assertIn("columns=list(B3_META)", source)
        self.assertIn("usecols=list(D0_META)", source)
        self.assertNotIn("--execute", source)


if __name__ == "__main__":
    unittest.main()
