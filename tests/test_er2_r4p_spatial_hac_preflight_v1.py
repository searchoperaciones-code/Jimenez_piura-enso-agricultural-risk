from __future__ import annotations

import ast
import csv
import hashlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import er2_r4p_spatial_hac_preflight_v1 as r4p  # noqa: E402


class TestER2R4PSpatialHACPreflightV1(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.lock = json.loads((ROOT / r4p.PREFLIGHT_LOCK).read_text(encoding="utf-8"))
        cls.plan = json.loads((ROOT / r4p.TEST_PLAN_LOCK).read_text(encoding="utf-8"))
        cls.report = (ROOT / r4p.REPORT).read_text(encoding="utf-8")
        cls.mapping = list(csv.DictReader(io.StringIO((ROOT / r4p.COEFFICIENT_MAP).read_text(encoding="utf-8"))))
        cls.geometry = list(csv.DictReader(io.StringIO((ROOT / r4p.GEOMETRY_AUDIT).read_text(encoding="utf-8"))))
        cls.synthetic = list(csv.DictReader(io.StringIO((ROOT / r4p.SYNTHETIC_VALIDATION).read_text(encoding="utf-8"))))

    def test_01_exact_r3_frozen_predecessor(self) -> None:
        state = self.lock["governing_state"]
        self.assertEqual(state["r3_freeze_sha"], r4p.R3_FREEZE_SHA)
        self.assertEqual(state["r3_parent_sha"], r4p.R3_PARENT_SHA)
        self.assertEqual(state["r3_results_lock_sha256"], r4p.R3_RESULTS_LOCK_SHA)
        self.assertEqual(state["r3_status"], "PASS_FROZEN_REMOTE_VERIFIED")

    def test_02_r4_contract_identity(self) -> None:
        tier = self.lock["r4_tier_contract"]
        self.assertEqual(self.lock["r4_tier_contract_sha256"], r4p.TIER_CONTRACT_SHA)
        self.assertEqual(tier["tier_id"], "R4_SPATIAL_HAC")
        self.assertEqual(tier["role"], "ASYMPTOTIC_SPATIAL_HAC_ROBUSTNESS_DIAGNOSTIC")
        self.assertEqual(tier["bandwidths_km"], [50, 100, 150])

    def test_03_temporal_governance_is_prespecified(self) -> None:
        temporal = self.lock["temporal_governance"]
        self.assertTrue(all(temporal[key] for key in ("PRIMARY_RESULTS_KNOWN", "R1_RESULTS_KNOWN", "R2_RESULTS_KNOWN", "R3_RESULTS_KNOWN")))
        self.assertFalse(temporal["REAL_R4_RESULTS_KNOWN_BEFORE_THIS_GATE"])
        self.assertEqual(temporal["RESULT_DEPENDENT_DESIGN"], "PROHIBITED")

    def test_04_scientific_role_and_bandwidths(self) -> None:
        role = self.lock["r4_scientific_role"]
        self.assertEqual(role["family"], "PHYSICAL_ANOMALY")
        self.assertEqual(role["outcome"], "YIELD_LEVEL_TM_PER_HA")
        self.assertEqual(role["beta"], "EXACT_ER1_PRIMARY_UNCHANGED")
        self.assertEqual(self.lock["bandwidth_contract"]["bandwidths_km"], [50, 100, 150])
        self.assertEqual(self.lock["bandwidth_contract"]["real_rows_created"], 0)

    def test_05_bartlett_and_same_period_api(self) -> None:
        tier = self.lock["r4_tier_contract"]
        api = self.lock["conley_api"]
        self.assertEqual(tier["kernel"], "BARTLETT")
        self.assertEqual(tier["pairing"], "SAME_PERIOD_ONLY")
        self.assertEqual(api["period_handling"], "SORTED_UNIQUE_PERIOD_BLOCKS_CROSS_PERIOD_PAIRS_EXACT_ZERO")
        self.assertEqual(api["diagonal"], "DISTANCE_ZERO_WEIGHT_ONE_INCLUDED")
        self.assertEqual(api["finite_sample_scaling"], "NONE")

    def test_06_geometry_provenance_and_distance_matrix(self) -> None:
        summary = self.lock["geometry"]
        self.assertEqual(summary["source_sha256"], r4p.GEOMETRY_SHA)
        self.assertEqual(summary["source_git_blob_at_r3_parent"], r4p.GEOMETRY_BLOB)
        self.assertEqual((summary["source_crs"], summary["target_crs"]), ("EPSG:4326", "EPSG:32717"))
        self.assertEqual(len(self.geometry), summary["centroid_count"])
        self.assertEqual(len({row["UBIGEO"] for row in self.geometry}), 55)
        self.assertTrue(summary["distance_diagonal_exact_zero"] and summary["distance_symmetry_exact"] and summary["all_distances_finite_nonnegative"])

    def test_07_sample_geometry_coverage_is_not_guessed(self) -> None:
        summary = self.lock["geometry"]
        self.assertEqual(summary["sample_aggregate_identity"], "PASS_ALL_FIVE_CROPS")
        self.assertEqual(summary["sample_geometry_coverage"], "SAMPLE_GEOMETRY_COVERAGE_REQUIRES_REAL_R4_EXECUTION_PREFLIGHT")

    def test_08_frozen_conley_api_hashes(self) -> None:
        api = self.lock["conley_api"]
        self.assertEqual(api["file_sha256"], r4p.ED1_IMPLEMENTATION_SHA)
        self.assertEqual(api["function_source_sha256"], r4p.CONLEY_SOURCE_SHA)
        self.assertEqual(api["function_body_sha256"], r4p.CONLEY_BODY_SHA)
        self.assertEqual(api["function_lines"], [977, 999])

    def test_09_historical_engine_validation_is_not_real_r4(self) -> None:
        historical = self.lock["historical_engine_validation"]
        self.assertEqual(historical["status"], "PASS_ALL_FIVE_CROPS_ALL_THREE_BANDWIDTHS")
        self.assertEqual(historical["classification"], "HISTORICAL_SYNTHETIC_ENGINE_VALIDATION_NOT_REAL_R4_EVIDENCE")

    def test_10_exact_21_coefficient_mapping(self) -> None:
        self.assertEqual(len(self.mapping), 21)
        self.assertEqual([int(row["MAP_ORDER"]) for row in self.mapping], list(range(1, 22)))
        self.assertEqual([sum(row["CROP_CODE"] == code for row in self.mapping) for code in r4p.CROP_SPECS], [3, 3, 3, 6, 6])
        self.assertEqual(len({(row["CROP_CODE"], row["COEFFICIENT_NAME"]) for row in self.mapping}), 21)
        self.assertTrue(all(row["EXPECTED_REAL_R4_BANDWIDTHS_KM"] == "50|100|150" for row in self.mapping))

    def test_11_no_joint_conley_and_exact_interval(self) -> None:
        self.assertEqual(self.lock["joint_conley_tests"], "NOT_AUTHORIZED")
        interval = self.lock["interval_contract"]
        self.assertEqual(interval["critical_value"], 1.959963984540054)
        self.assertFalse(interval["multiplicity_adjusted"])
        self.assertEqual(interval["satterthwaite_df"], "NOT_USED")

    def test_12_multiplicity_and_variance_firewalls(self) -> None:
        multiplicity = self.lock["multiplicity_firewall"]
        self.assertEqual(multiplicity["GLOBAL_FIVE_CROP_FWER"], "NOT_CLAIMED")
        self.assertEqual(multiplicity["VOTE_COUNTING"], "PROHIBITED")
        self.assertEqual(self.lock["variance_policy"], "HOLD_NO_CLIPPING_OR_COVARIANCE_SUBSTITUTION")

    def test_13_synthetic_plan_was_locked_first(self) -> None:
        validation = self.lock["synthetic_validation"]
        self.assertEqual(self.plan["status"], "LOCKED_BEFORE_SYNTHETIC_EXECUTION")
        self.assertEqual(self.plan["absolute_tolerance"], 1e-10)
        self.assertEqual(self.plan["edge_cases"], list("ABCDEFGHIJKLMNOP"))
        self.assertTrue(validation["test_plan_lock_written_before_validation"])
        self.assertEqual(validation["test_plan_lock_sha256"], hashlib.sha256((ROOT / r4p.TEST_PLAN_LOCK).read_bytes()).hexdigest())

    def test_14_production_reference_equivalence(self) -> None:
        validation = self.lock["synthetic_validation"]
        self.assertEqual(validation["status"], "PASS")
        self.assertLessEqual(validation["production_reference_max_abs_difference"], 1e-10)
        self.assertTrue(all(row["STATUS"] == "PASS" for row in self.synthetic if row["CATEGORY"] == "PRODUCTION_VS_REFERENCE"))
        source = (ROOT / r4p.SCRIPT).read_text(encoding="utf-8")
        tree = ast.parse(source)
        node = next(item for item in ast.walk(tree) if isinstance(item, ast.FunctionDef) and item.name == "reference_conley_covariance")
        self.assertNotIn("ed1.conley_covariance", ast.get_source_segment(source, node) or "")

    def test_15_all_sixteen_edge_cases_pass(self) -> None:
        passed = {row["CHECK_ID"].split("_", 1)[0] for row in self.synthetic if row["CATEGORY"] == "EDGE_CASE" and row["STATUS"] == "PASS"}
        self.assertEqual(passed, set("ABCDEFGHIJKLMNOP"))

    def test_16_bandwidth_support_nesting_and_pair_audit(self) -> None:
        validation = self.lock["synthetic_validation"]
        self.assertEqual(validation["support_nesting"], "PASS")
        self.assertEqual(validation["se_monotonicity_across_bandwidths"], "NOT_REQUIRED")
        for bandwidth in ("50", "100", "150"):
            audit = validation["pair_audit"][bandwidth]
            self.assertEqual(audit["same_period_ordered_pairs_including_diagonal"], 108)
            self.assertEqual(audit["same_period_unordered_pairs_including_diagonal"], 63)
            self.assertEqual(audit["exact_boundary_distance_weight"], 0.0)

    def test_17_result_specific_branch_audit(self) -> None:
        audit = self.lock["source_audit"]
        self.assertEqual(audit["result_specific_r4_branches"], 0)
        self.assertEqual(audit["offending_conditions"], [])

    def test_18_real_outcome_and_downstream_firewalls(self) -> None:
        firewall = self.lock["execution_firewall"]
        self.assertFalse(firewall["REAL_OUTCOME_VALUES_READ"])
        self.assertFalse(firewall["REAL_R4_COVARIANCES_COMPUTED"])
        self.assertFalse(firewall["REAL_R4_STANDARD_ERRORS_COMPUTED"])
        self.assertFalse(firewall["REAL_R4_CONFIDENCE_INTERVALS_COMPUTED"])
        self.assertFalse(firewall["REAL_R4_ZERO_INCLUSION_RESULTS_KNOWN"])
        self.assertFalse(firewall["REAL_R4_EXECUTED"])
        self.assertEqual(firewall["R5_AUTHORIZATION_STATUS"], "NOT_AUTHORIZED")
        self.assertEqual(firewall["R6_AUTHORIZATION_STATUS"], "NOT_AUTHORIZED")

    def test_19_future_schema_only_and_direct_reuse(self) -> None:
        self.assertEqual(self.lock["future_real_r4_output_schema"], list(r4p.REAL_R4_OUTPUT_SCHEMA))
        self.assertEqual(self.lock["bandwidth_contract"]["expected_real_rows"], 63)
        self.assertEqual(self.lock["bandwidth_contract"]["real_rows_created"], 0)
        self.assertEqual(self.lock["r4_executor_architecture"], "R4_EXECUTOR_CAN_REUSE_FROZEN_ED1_CONLEY_DIRECTLY")
        real_paths = [path for path in (ROOT / "outputs/econometrics").glob("ER2_R4_*") if not path.name.startswith("ER2_R4P_")]
        self.assertEqual(real_paths, [])

    def test_20_deterministic_scope_bytes_and_two_run_build(self) -> None:
        untracked = set(subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=ROOT, text=True).splitlines())
        self.assertEqual(untracked, {path.as_posix() for path in r4p.CANDIDATES})
        for relative in r4p.CANDIDATES:
            payload = (ROOT / relative).read_bytes()
            self.assertNotIn(b"\r", payload)
            self.assertFalse(payload.startswith(b"\xef\xbb\xbf"))
            self.assertTrue(payload.endswith(b"\n"))
            self.assertFalse(payload.endswith(b"\n\n"))
        for relative, expected in self.lock["artifact_sha256"].items():
            self.assertEqual(hashlib.sha256((ROOT / relative).read_bytes()).hexdigest(), expected)
        with tempfile.TemporaryDirectory(prefix="er2_r4p_test_one_") as one, tempfile.TemporaryDirectory(prefix="er2_r4p_test_two_") as two:
            run_one = r4p.build_package(Path(one))
            run_two = r4p.build_package(Path(two))
        self.assertEqual(run_one, run_two)
        self.assertEqual(run_one, {relative.as_posix(): (ROOT / relative).read_bytes() for relative in r4p.GENERATED})


if __name__ == "__main__":
    unittest.main()
