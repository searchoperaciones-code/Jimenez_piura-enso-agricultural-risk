from __future__ import annotations

import csv
import hashlib
import io
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import er2_r4_spatial_hac_real_v1 as r4  # noqa: E402


def csv_rows(relative: Path) -> list[dict[str, str]]:
    with (ROOT / relative).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def truth(value: str) -> bool:
    if value not in {"TRUE", "FALSE"}:
        raise AssertionError(value)
    return value == "TRUE"


class TestER2R4SpatialHACRealV1(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.lock = json.loads((ROOT / r4.LOCK).read_text(encoding="utf-8"))
        cls.results = csv_rows(r4.RESULTS)
        cls.coverage = csv_rows(r4.COVERAGE)
        cls.audits = csv_rows(r4.COVARIANCE_AUDIT)
        cls.concordance = csv_rows(r4.CONCORDANCE)
        cls.report = (ROOT / r4.REPORT).read_text(encoding="utf-8")

    def test_01_exact_r4p_parent_and_remote_identity(self) -> None:
        state = r4.preflight()
        identity = state["identity"]
        self.assertEqual(identity["head"], r4.R4P_FREEZE_SHA)
        self.assertEqual(identity["branch"], r4.R4P_BRANCH)
        self.assertEqual(identity["remote_branch"], r4.R4P_FREEZE_SHA)
        self.assertEqual(identity["tag_object"], r4.R4P_TAG_OBJECT)
        self.assertEqual(identity["tag_target"], r4.R4P_FREEZE_SHA)

    def test_02_exact_eight_candidate_paths_and_clean_index(self) -> None:
        untracked = set(
            subprocess.check_output(
                ["git", "ls-files", "--others", "--exclude-standard"], cwd=ROOT, text=True
            ).splitlines()
        )
        self.assertEqual(untracked, {path.as_posix() for path in r4.CANDIDATES})
        self.assertFalse(subprocess.check_output(["git", "diff", "--name-only"], cwd=ROOT, text=True).strip())
        self.assertFalse(subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=ROOT, text=True).strip())

    def test_03_r4_contract_is_exact(self) -> None:
        self.assertEqual(self.lock["tier_id"], "R4_SPATIAL_HAC")
        self.assertEqual(self.lock["tier_order"], 4)
        self.assertEqual(self.lock["r4_tier_contract_sha256"], r4.R4_TIER_CONTRACT_SHA)
        self.assertEqual(self.lock["r4_scientific_role"]["role"], "ASYMPTOTIC_SPATIAL_HAC_ROBUSTNESS_DIAGNOSTIC")
        self.assertEqual(self.lock["r4_scientific_role"]["family"], "PHYSICAL_ANOMALY")

    def test_04_pre_result_temporal_governance_is_frozen(self) -> None:
        governance = self.lock["temporal_governance_before_execution"]
        for key in (
            "PRIMARY_RESULTS_KNOWN", "R1_RESULTS_KNOWN", "R2_RESULTS_KNOWN",
            "R3_RESULTS_KNOWN", "R4P_FROZEN_BEFORE_REAL_R4",
            "R4_BANDWIDTHS_FROZEN_BEFORE_RESULTS", "R4_KERNEL_FROZEN_BEFORE_RESULTS",
            "R4_GEOMETRY_FROZEN_BEFORE_RESULTS", "R4_TARGETS_FROZEN_BEFORE_RESULTS",
        ):
            self.assertIs(governance[key], True)
        self.assertIs(governance["REAL_R4_RESULTS_KNOWN_BEFORE_EXECUTION"], False)

    def test_05_coverage_precedes_covariance(self) -> None:
        sequence = self.lock["execution_sequence"]
        coverage_index = sequence.index("SAMPLE_GEOMETRY_COVERAGE_PASS_ALL_FIVE_CROPS")
        covariance_index = sequence.index("FIFTEEN_CONLEY_COVARIANCE_MATRICES_COMPUTED")
        self.assertLess(coverage_index, covariance_index)
        payload = (ROOT / r4.COVERAGE).read_bytes()
        self.assertEqual(hashlib.sha256(payload).hexdigest(), self.lock["coverage_ledger_sha256_before_covariance"])

    def test_06_complete_coverage_ledger(self) -> None:
        self.assertEqual(len(self.coverage), 232)
        self.assertEqual(self.lock["sample_geometry_coverage"]["status"], "PASS_ALL_FIVE_CROPS")
        self.assertTrue(all(row["COVERAGE_STATUS"] == "PASS" for row in self.coverage))
        self.assertTrue(all(truth(row["CENTROID_PRESENT"]) for row in self.coverage))
        self.assertTrue(all(truth(row["CENTROID_UNIQUE"]) for row in self.coverage))
        self.assertTrue(all(truth(row["FINITE_XY"]) for row in self.coverage))

    def test_07_coverage_has_no_outcome_values(self) -> None:
        fields = set(self.coverage[0])
        self.assertFalse(any("YIELD" in field or field == "Y" for field in fields))
        self.assertEqual(fields, set(r4.COVERAGE_FIELDS))

    def test_08_nominal_district_counts_are_exact(self) -> None:
        counts: dict[str, set[str]] = {}
        for row in self.coverage:
            counts.setdefault(row["CROP_CODE"], set()).add(row["UBIGEO"])
        self.assertEqual({key: len(value) for key, value in counts.items()}, {
            "14010020000": 44,
            "14010070000": 54,
            "13010210000": 36,
            "13010170102": 44,
            "15010040000": 54,
        })

    def test_09_sample_identity_is_exact(self) -> None:
        expected = {
            "14010020000": (281, 44, 43, 7),
            "14010070000": (318, 54, 52, 7),
            "13010210000": (255, 36, 35, 8),
            "13010170102": (311, 44, 43, 8),
            "15010040000": (390, 54, 50, 8),
        }
        actual = {
            key: (
                value["sample_n"], value["nominal_districts"],
                value["effective_districts"], value["periods"],
            )
            for key, value in self.lock["model_identity"].items()
        }
        self.assertEqual(actual, expected)

    def test_10_er1_beta_and_model_identity(self) -> None:
        self.assertLessEqual(self.lock["maximum_er1_beta_absolute_difference"], r4.MODEL_IDENTITY_TOLERANCE)
        self.assertTrue(all(item["status"] == "PASS" for item in self.lock["model_identity"].values()))
        self.assertTrue(all(item["model_specification_change"] is False for item in self.lock["model_identity"].values()))

    def test_11_geometry_and_crs_are_frozen(self) -> None:
        geometry = self.lock["geometry"]
        self.assertEqual(geometry["source_sha256"], r4.GEOMETRY_SHA)
        self.assertEqual(geometry["source_crs"], "EPSG:4326")
        self.assertEqual(geometry["target_crs"], "EPSG:32717")
        self.assertEqual(geometry["construction"], "PROJECT_FULL_FROZEN_GEOMETRY_THEN_CENTROID")

    def test_12_conley_api_identity_is_frozen(self) -> None:
        api = self.lock["conley_api"]
        self.assertEqual(api["file_sha256"], r4.ED1_IMPLEMENTATION_SHA)
        self.assertEqual(api["function_source_sha256"], r4.CONLEY_SOURCE_SHA)
        self.assertEqual(api["function_body_sha256"], r4.CONLEY_BODY_SHA)

    def test_13_exact_21_target_map(self) -> None:
        targets = self.lock["target_map"]
        self.assertEqual(len(targets), 21)
        self.assertEqual([int(row["MAP_ORDER"]) for row in targets], list(range(1, 22)))
        self.assertEqual(len({(row["CROP_CODE"], row["COEFFICIENT_NAME"]) for row in targets}), 21)

    def test_14_exact_bandwidth_inventory_and_order(self) -> None:
        self.assertEqual(self.lock["bandwidths_km"], [50, 100, 150])
        grouped: dict[tuple[str, str], list[int]] = {}
        for row in self.results:
            grouped.setdefault((row["CROP_CODE"], row["VARIABLE"]), []).append(int(row["BANDWIDTH_KM"]))
        self.assertEqual(len(grouped), 21)
        self.assertTrue(all(value == [50, 100, 150] for value in grouped.values()))

    def test_15_exact_63_result_rows(self) -> None:
        self.assertEqual(len(self.results), 63)
        self.assertEqual(self.lock["result_row_count"], 63)
        self.assertEqual(set(self.results[0]), set(r4.RESULT_FIELDS))
        self.assertTrue(all(row["STATUS"] == "PASS" for row in self.results))

    def test_16_exact_15_covariance_matrices(self) -> None:
        self.assertEqual(len(self.audits), 15)
        self.assertEqual(self.lock["covariance_matrix_count"], 15)
        pairs = {(row["CROP_CODE"], int(row["BANDWIDTH_KM"])) for row in self.audits}
        self.assertEqual(len(pairs), 15)

    def test_17_covariance_shapes_are_exact(self) -> None:
        expected_k = {"14010020000": 3, "14010070000": 3, "13010210000": 3, "13010170102": 6, "15010040000": 6}
        self.assertTrue(all(int(row["K"]) == expected_k[row["CROP_CODE"]] for row in self.audits))

    def test_18_covariances_are_finite_and_symmetric(self) -> None:
        self.assertTrue(all(truth(row["MATRIX_FINITE"]) for row in self.audits))
        self.assertTrue(all(float(row["MAX_SYMMETRY_DIFFERENCE"]) <= r4.COVARIANCE_SYMMETRY_TOLERANCE for row in self.audits))

    def test_19_target_variances_are_strictly_positive(self) -> None:
        self.assertTrue(all(float(row["CONLEY_VARIANCE"]) > 0.0 for row in self.results))
        self.assertTrue(all(float(row["MIN_DIAGONAL_VARIANCE"]) > 0.0 for row in self.audits))
        self.assertTrue(all(int(row["NONPOSITIVE_DIAGONAL_COUNT"]) == 0 for row in self.audits))
        self.assertTrue(all(int(row["NONFINITE_DIAGONAL_COUNT"]) == 0 for row in self.audits))

    def test_20_no_clipping_or_covariance_substitution(self) -> None:
        inventory = self.lock["invalid_variance_inventory"]
        self.assertEqual(inventory["count"], 0)
        self.assertEqual(inventory["policy"], "HOLD_NO_CLIPPING_OR_COVARIANCE_SUBSTITUTION")
        source = (ROOT / r4.SCRIPT).read_text(encoding="utf-8")
        self.assertNotIn("np.clip", source)
        self.assertNotIn("abs(variance)", source)

    def test_21_standard_error_is_square_root_of_variance(self) -> None:
        for row in self.results:
            self.assertEqual(float(row["CONLEY_SE"]), math.sqrt(float(row["CONLEY_VARIANCE"])))

    def test_22_z_and_normal_p_are_exact(self) -> None:
        for row in self.results:
            beta = float(row["ER1_BETA_REFERENCE"])
            se = float(row["CONLEY_SE"])
            z_value = beta / se
            self.assertAlmostEqual(float(row["Z"]), z_value, places=14)
            self.assertAlmostEqual(float(row["TWO_SIDED_ASYMPTOTIC_P"]), math.erfc(abs(z_value) / math.sqrt(2.0)), places=14)

    def test_23_normal_critical_value_and_ci_formula(self) -> None:
        for row in self.results:
            beta = float(row["ER1_BETA_REFERENCE"])
            se = float(row["CONLEY_SE"])
            self.assertEqual(float(row["NORMAL_CRITICAL_VALUE"]), r4.NORMAL_CRITICAL_VALUE)
            self.assertAlmostEqual(float(row["CI95_LOWER"]), beta - r4.NORMAL_CRITICAL_VALUE * se, places=14)
            self.assertAlmostEqual(float(row["CI95_UPPER"]), beta + r4.NORMAL_CRITICAL_VALUE * se, places=14)

    def test_24_zero_inclusion_is_deterministic(self) -> None:
        for row in self.results:
            expected = float(row["CI95_LOWER"]) <= 0.0 <= float(row["CI95_UPPER"])
            self.assertEqual(truth(row["CI_ZERO_INCLUDED"]), expected)

    def test_25_no_r4_holm_or_global_fwer(self) -> None:
        firewall = self.lock["multiplicity_firewall"]
        self.assertEqual(firewall["R4_HOLM"], "NOT_AUTHORIZED")
        self.assertEqual(firewall["GLOBAL_FIVE_CROP_FWER"], "NOT_CLAIMED")
        self.assertEqual(firewall["MULTIPLICITY_ADJUSTED_CI"], "NOT_CONSTRUCTED_NOT_CLAIMED")

    def test_26_no_joint_conley(self) -> None:
        self.assertEqual(self.lock["joint_conley_tests"], [])
        self.assertEqual(self.lock["joint_conley_status"], "NOT_AUTHORIZED")

    def test_27_concordance_is_descriptive_and_complete(self) -> None:
        self.assertEqual(len(self.concordance), 21)
        self.assertEqual(self.lock["concordance_row_count"], 21)
        allowed = {
            "CI_ZERO_INCLUSION_STABLE_ACROSS_PRESPECIFIED_BANDWIDTHS",
            "CI_ZERO_INCLUSION_VARIES_BY_BANDWIDTH",
        }
        self.assertTrue(all(row["BANDWIDTH_SENSITIVITY"] in allowed for row in self.concordance))

    def test_28_no_bandwidth_winner_or_vote_fields(self) -> None:
        fields = set(self.concordance[0]) | set(self.results[0])
        prohibited = {"BEST_BANDWIDTH", "PREFERRED_BANDWIDTH", "ROBUSTNESS_SCORE", "VOTE_COUNT", "MAJORITY_RESULT"}
        self.assertFalse(fields & prohibited)
        self.assertEqual(self.lock["best_bandwidth_selection"], "PROHIBITED")
        self.assertEqual(self.lock["multiplicity_firewall"]["VOTE_COUNTING"], "PROHIBITED")

    def test_29_no_result_specific_banana_or_lemon_branch(self) -> None:
        self.assertEqual(self.lock["result_specific_r4_branches"], 0)
        source = (ROOT / r4.SCRIPT).read_text(encoding="utf-8").lower()
        self.assertNotIn("banana lagged tmin", source)
        self.assertNotIn("lemon lagged tmin", source)

    def test_30_two_run_reproduction_is_locked(self) -> None:
        reproduction = self.lock["two_run_reproducibility"]
        self.assertEqual(reproduction["status"], "PASS")
        self.assertEqual(reproduction["independent_processes"], 2)
        self.assertEqual(reproduction["run_1_calculation_sha256"], reproduction["run_2_calculation_sha256"])
        self.assertIs(reproduction["calculation_bytes_exact"], True)
        self.assertIs(reproduction["rendered_output_bytes_exact"], True)

    def test_31_fresh_two_process_build_is_byte_identical(self) -> None:
        with tempfile.TemporaryDirectory(prefix="er2_r4_test_") as temporary:
            output_root = Path(temporary)
            r4.build(output_root)
            for relative in r4.OUTPUTS:
                self.assertEqual((output_root / relative).read_bytes(), (ROOT / relative).read_bytes())

    def test_32_results_lock_has_no_circular_self_hash(self) -> None:
        self.assertNotIn(r4.LOCK.as_posix(), self.lock["artifact_sha256"])
        self.assertEqual(self.lock["artifact_sha256"][r4.SCRIPT.as_posix()], sha256(ROOT / r4.SCRIPT))
        self.assertEqual(self.lock["artifact_sha256"][r4.TEST.as_posix()], sha256(ROOT / r4.TEST))

    def test_33_utf8_lf_byte_contract(self) -> None:
        for relative in r4.CANDIDATES:
            payload = (ROOT / relative).read_bytes()
            payload.decode("utf-8")
            self.assertFalse(payload.startswith(b"\xef\xbb\xbf"), relative)
            self.assertNotIn(b"\r", payload, relative)
            self.assertTrue(payload.endswith(b"\n"), relative)
            self.assertFalse(payload.endswith(b"\n\n"), relative)

    def test_34_r5_r6_and_downstream_firewalls(self) -> None:
        firewall = self.lock["execution_firewall"]
        self.assertIs(firewall["R4_EXECUTED"], True)
        self.assertEqual(firewall["R5_AUTHORIZATION_STATUS"], "NOT_AUTHORIZED")
        self.assertIs(firewall["R5_EXECUTED"], False)
        self.assertEqual(firewall["R6_AUTHORIZATION_STATUS"], "NOT_AUTHORIZED")
        self.assertIs(firewall["R6_EXECUTED"], False)
        for key in ("ENSO_SCENARIOS", "GVP", "VAR_CVAR", "A1_A2", "OPTIMIZATION"):
            self.assertEqual(firewall[key], "NOT_EXECUTED")

    def test_35_final_verdict_and_next_action(self) -> None:
        self.assertEqual(self.lock["final_verdict"], r4.FINAL_VERDICT)
        self.assertEqual(self.lock["NEXT_TIER_AUTHORIZATION_STATUS"], "NOT_AUTHORIZED")
        self.assertEqual(self.lock["next_action"], "RETURN_TO_SCIENTIFIC_DIRECTOR_FOR_R4_REVIEW")


if __name__ == "__main__":
    unittest.main()
