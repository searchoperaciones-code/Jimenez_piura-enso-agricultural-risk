from __future__ import annotations

import csv
import io
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import er2_r3_restricted_wcr_v1 as r3  # noqa: E402


class TestER2R3RestrictedWCRRealExecutionV1(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.lock = json.loads((ROOT / r3.LOCK).read_text(encoding="utf-8"))
        cls.coefficients = list(csv.DictReader(io.StringIO((ROOT / r3.COEFFICIENTS).read_text(encoding="utf-8"))))
        cls.joint = list(csv.DictReader(io.StringIO((ROOT / r3.JOINT).read_text(encoding="utf-8"))))
        cls.samples = list(csv.DictReader(io.StringIO((ROOT / r3.SAMPLES).read_text(encoding="utf-8"))))
        cls.execution = list(csv.DictReader(io.StringIO((ROOT / r3.EXECUTION).read_text(encoding="utf-8"))))

    def test_exact_parent_and_predecessor_chain(self) -> None:
        self.assertEqual(self.lock["r3a_freeze_sha"], r3.R3A_FREEZE_SHA)
        self.assertEqual(self.lock["r3a_certified_adapter_lock_sha256"], r3.R3A_LOCK_SHA)
        self.assertEqual(self.lock["er2p_freeze_sha"], r3.ER2P_FREEZE_SHA)
        self.assertEqual(self.lock["r2_freeze_sha"], r3.R2_FREEZE_SHA)
        self.assertEqual(self.lock["r2_final_certified_predecessor_lock_sha256"], r3.R2_REPORTING_LOCK_SHA)

    def test_exact_r3_contract_and_physical_family(self) -> None:
        self.assertEqual(self.lock["tier_contract_sha256"], r3.R3_TIER_SHA)
        self.assertEqual(self.lock["tier_id"], "R3_RESTRICTED_WILD_CLUSTER_BOOTSTRAP")
        self.assertEqual(self.lock["tier_order"], 3)
        self.assertEqual(self.lock["climate_family"], "PHYSICAL_ANOMALY")
        self.assertFalse(self.lock["model_specification_change"])

    def test_exact_samples_and_ordering(self) -> None:
        expected = {code: value["n"] for code, value in r3.er1.EXPECTED_SAMPLE.items()}
        self.assertEqual({row["CROP_CODE"]: int(row["N"]) for row in self.samples}, expected)
        self.assertTrue(all(row["ER1_ORDERED_KEYS_EXACT"] == "TRUE" for row in self.samples))
        self.assertTrue(all(row["ER1_Y_SOURCE_EXACT"] == "TRUE" for row in self.samples))
        self.assertTrue(all(row["ROW_ORDER"] == "SORTED_UBIGEO_THEN_FROZEN_PERIOD" for row in self.samples))
        self.assertTrue(all(row["CLUSTER_ORDER"] == "SORTED_UBIGEO" for row in self.samples))
        self.assertTrue(all(int(row["MISSING_Y"]) == int(row["MISSING_X"]) == int(row["DUPLICATE_KEYS"]) == 0 for row in self.samples))

    def test_exact_21_named_targets_and_five_joint_tests(self) -> None:
        target_pairs = {(row["CROP_CODE"], row["CLIMATE_VARIABLE"]) for row in self.coefficients}
        frozen_pairs = {(row["CROP_CODE"], row["VARIABLE"]) for row in self.lock["targets"]}
        self.assertEqual(target_pairs, frozen_pairs)
        self.assertEqual(len(self.coefficients), 21)
        self.assertEqual(len(self.joint), 5)
        self.assertEqual([int(row["Q"]) for row in self.joint], [3, 3, 3, 6, 6])

    def test_er1_beta_identity_fixed_tolerance(self) -> None:
        self.assertEqual(self.lock["er1_numerical_results_identity"], r3.ER1_NUMERICAL_IDENTITY)
        self.assertTrue(all(value["status"] == "PASS" for value in self.lock["model_identity"].values()))
        self.assertTrue(all(value["maximum_beta_absolute_difference"] <= r3.MODEL_IDENTITY_TOLERANCE
                            for value in self.lock["model_identity"].values()))
        self.assertTrue(all(value["same_y"] and value["same_x"] and value["same_district_fe"]
                            and value["same_period_fe"] and value["same_weighting"]
                            and value["same_cluster_unit"] for value in self.lock["model_identity"].values()))

    def test_restricted_null_imposed_wcr_contract(self) -> None:
        contract = self.lock["bootstrap_contract"]
        self.assertTrue(contract["restricted"] and contract["null_imposed"])
        self.assertEqual(contract["weights"], "RADEMACHER")
        self.assertEqual(contract["cluster"], "DISTRICT")
        self.assertEqual(contract["rng"], "NUMPY_GENERATOR_PCG64")
        self.assertEqual((contract["replications"], contract["seed"], contract["batch_size"]), (9999, 20260903, 1000))
        self.assertEqual(contract["batch_partition"], [1000] * 9 + [999])
        self.assertEqual(contract["seed_reset"], "EACH_CROP_CONTRAST_AND_JOINT_TEST")

    def test_execution_audit_all_26_and_seed_reset(self) -> None:
        self.assertEqual(len(self.execution), 26)
        self.assertTrue(all(row["B"] == "9999" and row["SEED"] == "20260903" for row in self.execution))
        self.assertTrue(all(row["BATCH_PARTITION"] == "1000+1000+1000+1000+1000+1000+1000+1000+1000+999" for row in self.execution))
        self.assertTrue(all(row["SEED_RESET"] == "EACH_CROP_CONTRAST_AND_JOINT_TEST" for row in self.execution))
        for crop in {row["CROP_CODE"] for row in self.execution}:
            hashes = {row["FULL_DRAW_MATRIX_SHA256"] for row in self.execution if row["CROP_CODE"] == crop}
            self.assertEqual(len(hashes), 1)

    def test_finite_correction_and_zero_invalid(self) -> None:
        self.assertEqual(self.lock["invalid_replications_total"], 0)
        for row in [*self.coefficients, *self.joint]:
            exceedances = int(row["WCR_EXCEEDANCE_COUNT"])
            self.assertEqual(int(row["INVALID_REPLICATIONS"]), 0)
            self.assertEqual(int(row["WCR_P_NUMERATOR"]), 1 + exceedances)
            self.assertEqual(int(row["WCR_P_DENOMINATOR"]), 10000)
            self.assertEqual(float(row["WCR_RAW_P"]), (1 + exceedances) / 10000)
            self.assertGreaterEqual(float(row["WCR_RAW_P"]), 0.0001)

    def test_holm_only_within_crop_coefficients(self) -> None:
        self.assertEqual(self.lock["multiplicity"], "HOLM_STEP_DOWN_WITHIN_CROP_WCR_COEFFICIENT_P_VALUES")
        self.assertEqual(self.lock["holm_family_sizes"], [3, 3, 3, 6, 6])
        self.assertEqual(self.lock["joint_holm"], "NOT_APPLIED")
        self.assertEqual(self.lock["global_fwer"], "NOT_CALCULATED")
        self.assertTrue(all(row["JOINT_HOLM"] == "NOT_APPLIED" for row in self.joint))
        for crop in {row["CROP_CODE"] for row in self.coefficients}:
            family = [row for row in self.coefficients if row["CROP_CODE"] == crop]
            expected = r3.er1.holm_adjust([float(row["WCR_RAW_P"]) for row in family])
            self.assertEqual([float(row["WITHIN_CROP_HOLM_WCR_P"]) for row in family], list(expected))

    def test_no_result_specific_skipping(self) -> None:
        self.assertEqual({row["TEST_KIND"] for row in self.execution}, {"COEFFICIENT", "JOINT"})
        self.assertEqual(sum(row["TEST_KIND"] == "COEFFICIENT" for row in self.execution), 21)
        self.assertEqual(sum(row["TEST_KIND"] == "JOINT" for row in self.execution), 5)

    def test_two_independent_runs_are_exact(self) -> None:
        reproduction = self.lock["two_run_reproducibility"]
        self.assertEqual(reproduction["status"], "PASS")
        self.assertEqual(reproduction["independent_processes"], 2)
        self.assertEqual(reproduction["run_1_calculation_sha256"], reproduction["run_2_calculation_sha256"])
        self.assertTrue(reproduction["calculation_bytes_exact"] and reproduction["rendered_output_bytes_exact"])

    def test_artifact_and_implementation_hashes(self) -> None:
        for relative, expected in self.lock["artifact_sha256"].items():
            self.assertEqual(r3.sha_file(ROOT / relative), expected)
        self.assertEqual(self.lock["implementation_sha256"], r3.sha_file(ROOT / r3.SCRIPT))
        self.assertEqual(self.lock["test_sha256"], r3.sha_file(ROOT / r3.TEST))

    def test_deterministic_text_bytes(self) -> None:
        for relative in r3.OUTPUTS:
            payload = (ROOT / relative).read_bytes()
            self.assertNotIn(b"\r", payload)
            self.assertFalse(payload.startswith(b"\xef\xbb\xbf"))
            self.assertTrue(payload.endswith(b"\n"))
            self.assertFalse(payload.endswith(b"\n\n"))

    def test_interpretation_and_downstream_firewalls(self) -> None:
        report = (ROOT / r3.REPORT).read_text(encoding="utf-8")
        self.assertIn("No cross-crop ranking", report)
        self.assertIn("not resolved by selecting", report)
        firewall = self.lock["execution_firewall"]
        self.assertEqual(firewall["R4_AUTHORIZATION_STATUS"], "NOT_AUTHORIZED")
        self.assertFalse(firewall["R4_EXECUTED"] or firewall["R5_EXECUTED"] or firewall["R6_EXECUTED"])
        self.assertTrue(all(firewall[name] == "NOT_EXECUTED" for name in
                            ("ENSO_SCENARIOS", "GVP", "VAR_CVAR", "A1_A2", "OPTIMIZATION")))
        self.assertEqual(self.lock["NEXT_TIER_AUTHORIZATION_STATUS"], "NOT_AUTHORIZED")


if __name__ == "__main__":
    unittest.main()
