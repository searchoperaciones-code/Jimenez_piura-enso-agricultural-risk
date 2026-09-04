from __future__ import annotations

import ast
import csv
import hashlib
import inspect
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import primary_transient_exposure_v1 as e1  # noqa: E402


CONFIG = ROOT / e1.CONFIG_REL
EXPOSURE = ROOT / e1.EXPOSURE_REL
REPORT = ROOT / e1.REPORT_REL
MATRIX = ROOT / e1.CANDIDATE_MATRIX_REL
OVERLAY = ROOT / e1.SUPPORT_OVERLAY_REL
SCRIPT = ROOT / "scripts/primary_transient_exposure_v1.py"
TEST = ROOT / "tests/test_primary_transient_exposure_v1.py"

EXPECTED_STAGE_A_SHA = "283d57a21ba23c30c43f63e4c5327496ab59d760d8ca44a609b365151222a285"
EXPECTED_HASHES = {
    CONFIG: EXPECTED_STAGE_A_SHA,
    EXPOSURE: "ed90c70a7538318234a0390176b468a66f8a24a99fa59717efe5e8974cf09a67",
    REPORT: "085c5efb0f8abbd9f7f9443f28ed6d4d26fe5af3289a94a27219937b12883b91",
    MATRIX: "09bca9fb778759fc0b66656e6057d0f99daf0c9265be1f2b2eb1eb688e226e73",
    OVERLAY: "b59894c59485b6c4c92de8be0424f1f6c6211b333ea7609696874b457ac567a8",
}
EXPECTED_SCOPE = {
    "config/exposure_adjudication/primary_transient_exposure_v1.json",
    "data/processed/phenology/transient_econometric_exposures_v1.parquet",
    "outputs/exposure_adjudication/E1_CANDIDATE_MATRIX.csv",
    "outputs/exposure_adjudication/E1_PRIMARY_TRANSIENT_EXPOSURE_REPORT.md",
    "outputs/exposure_adjudication/E1_SUPPORT_OVERLAY.csv",
    "scripts/primary_transient_exposure_v1.py",
    "tests/test_primary_transient_exposure_v1.py",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=True, capture_output=True, text=True, encoding="utf-8"
    ).stdout.strip()


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


class PrimaryTransientExposureV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(CONFIG.read_text(encoding="utf-8"))
        cls.report = REPORT.read_text(encoding="utf-8")
        cls.matrix_columns, cls.matrix = read_csv(MATRIX)
        cls.overlay_columns, cls.overlay = read_csv(OVERLAY)
        cls.exposure = pd.read_parquet(EXPOSURE)

    def test_01_s1_freeze_identity_is_exact(self) -> None:
        self.assertEqual(git("branch", "--show-current"), "phase/s1-scientific-identity-master-v1")
        self.assertEqual(git("rev-parse", "HEAD"), e1.S1_FREEZE_SHA)
        self.assertEqual(git("rev-parse", "origin/phase/s1-scientific-identity-master-v1"), e1.S1_FREEZE_SHA)
        self.assertEqual(git("rev-list", "-n", "1", e1.S1_TAG), e1.S1_FREEZE_SHA)

    def test_02_exact_seven_file_candidate_scope(self) -> None:
        self.assertEqual(git("diff", "--name-only"), "")
        self.assertEqual(git("diff", "--cached", "--name-only"), "")
        observed = {
            line.replace("\\", "/")
            for line in git("ls-files", "--others", "--exclude-standard").splitlines()
            if line
        }
        self.assertEqual(observed, EXPECTED_SCOPE)

    def test_03_frozen_input_hashes_are_exact(self) -> None:
        self.assertEqual(sha256(e1.B1_PATH), e1.FROZEN_HASHES[e1.B1_PATH])
        self.assertEqual(sha256(e1.B3_PATH), e1.FROZEN_HASHES[e1.B3_PATH])
        self.assertEqual(sha256(e1.D0_MASTER_PATH), e1.FROZEN_HASHES[e1.D0_MASTER_PATH])
        self.assertEqual(sha256(e1.D0_LEDGER_PATH), e1.FROZEN_HASHES[e1.D0_LEDGER_PATH])
        self.assertEqual(sha256(e1.PHENOLOGY_PATH), e1.FROZEN_HASHES[e1.PHENOLOGY_PATH])

    def test_04_candidate_artifact_hashes_are_exact(self) -> None:
        self.assertEqual({path: sha256(path) for path in EXPECTED_HASHES}, EXPECTED_HASHES)

    def test_05_stage_a_decision_status_is_exact(self) -> None:
        self.assertEqual(self.config["gate"], "PRIMARY_TRANSIENT_ECONOMETRIC_EXPOSURE_ADJUDICATION_V1")
        self.assertEqual(self.config["status"], "PRIMARY_TRANSIENT_EXPOSURE_SELECTED")
        self.assertFalse(self.config["freeze_authorized"])
        self.assertEqual(self.config["governing_state"]["identification_ceiling"], "EMPIRICAL_ASSOCIATION_CLIMATE_RESPONSE_ONLY")

    def test_06_stage_a_reads_only_structural_d0_columns(self) -> None:
        expected = {
            "CROP_CODE", "CROP_STD", "UBIGEO", "CAMPAIGN", "CAMPAIGN_START_YEAR", "CAMPAIGN_END_YEAR",
        }
        self.assertEqual(set(e1.D0_STAGE_A_COLUMNS), expected)
        self.assertEqual(set(self.config["outcome_blindness"]["d0_stage_a_columns"]), expected)
        source = inspect.getsource(e1.read_stage_a_grid)
        self.assertNotIn("OUTCOME_VALID_FLAG", source)
        self.assertNotIn("EXCLUSION_REASON", source)

    def test_07_outcome_blindness_flags_are_false(self) -> None:
        blind = self.config["outcome_blindness"]
        self.assertFalse(blind["outcome_values_read_during_stage_a"])
        self.assertFalse(blind["outcome_validity_read_before_decision"])
        self.assertFalse(blind["selection_uses_outcome_support"])
        self.assertFalse(blind["selection_uses_model_fit"])

    def test_08_exposure_has_no_outcome_or_model_result_columns(self) -> None:
        forbidden = {
            "TRANSIENT_CAMPAIGN_YIELD_RAW", "PRODUCCION", "COSECHA", "PRECIO", "PRECIO_CHACRA",
            "GVP", "COEFFICIENT", "P_VALUE", "AIC", "BIC", "R2", "RMSE",
        }
        self.assertTrue(forbidden.isdisjoint(self.exposure.columns))
        self.assertTrue(forbidden.isdisjoint(self.config["output_columns"]))

    def test_09_crop_campaign_and_window_scope_is_exact(self) -> None:
        self.assertEqual(set(self.exposure["COD_CULTIVO"]), set(e1.CROPS))
        self.assertEqual(set(self.exposure["CAMPAIGN_ID"]), set(e1.CAMPAIGNS))
        observed = set(zip(self.exposure["COD_CULTIVO"], self.exposure["WINDOW_ID"]))
        expected = {(crop, values["window_id"]) for crop, values in e1.CROPS.items()}
        self.assertEqual(observed, expected)

    def test_10_frozen_phenology_contract_is_unchanged(self) -> None:
        contracts = self.config["phenology_contract"]
        self.assertEqual(contracts["14010020000"]["window_id"], "RICE_FLOWERING_95_110_DAS")
        self.assertEqual(contracts["14010020000"]["operational_window"], "m+3:m+4")
        self.assertEqual(contracts["14010070000"]["window_id"], "MAD_MPLUS1_MPLUS3")
        self.assertEqual(contracts["14010070000"]["operational_window"], "m+1:m+3")

    def test_11_candidate_inventory_is_exact(self) -> None:
        self.assertEqual(self.config["candidate_count"], 4)
        self.assertEqual(
            {item["candidate_id"] for item in self.config["candidate_inventory"]},
            {"E1-C1", "E1-C2", "E1-C3", "E1-C4"},
        )

    def test_12_candidate_matrix_has_all_domains_and_ordinal_statuses(self) -> None:
        self.assertEqual(self.matrix_columns, ["CANDIDATE_ID", "ARCHITECTURE", "DOMAIN", "STATUS", "REASON"])
        self.assertEqual(len(self.matrix), 40)
        self.assertEqual({row["DOMAIN"] for row in self.matrix}, set(e1.DOMAINS))
        self.assertTrue({row["STATUS"] for row in self.matrix} <= {"PASS", "PASS_WITH_LIMITATION", "FAIL", "NOT_IDENTIFIED"})
        for candidate in ("E1-C1", "E1-C2", "E1-C3", "E1-C4"):
            self.assertEqual(sum(row["CANDIDATE_ID"] == candidate for row in self.matrix), 10)

    def test_13_selected_architecture_is_c2_conditional_mean(self) -> None:
        selected = self.config["selected_architecture"]
        self.assertEqual(selected["candidate_id"], "E1-C2")
        self.assertEqual(selected["name"], "UNAMBIGUOUS_ASSIGNED_COHORT_CONDITIONAL_SIEMBRA_WEIGHTED_EXPOSURE")
        self.assertFalse(selected["full_campaign_exposure_claim"])

    def test_14_ambiguous_cohorts_are_never_assigned(self) -> None:
        self.assertEqual(
            self.config["ambiguity_rule"],
            "EXCLUDE_FROM_POINT_EXPOSURE_PRESERVE_WEIGHT_AND_COUNTS_NO_ASSIGNMENT",
        )
        self.assertTrue(
            (
                self.exposure["UNRESOLVED_AMBIGUOUS_WEIGHT_PRESERVED"]
                == (self.exposure["UNRESOLVED_AMBIGUOUS_SIEMBRA"] > 0)
            ).all()
        )

    def test_15_siembra_rule_is_explicit_and_missing_weight_is_not_zero_filled(self) -> None:
        self.assertEqual(
            self.config["siembra_weight_rule"],
            "NORMALIZE_ONLY_OVER_POSITIVE_OBSERVED_UNAMBIGUOUS_ASSIGNED_SIEMBRA_AS_EXPLICIT_CONDITIONAL_ESTIMAND_NO_FULL_CAMPAIGN_CLAIM",
        )
        missing = self.exposure["MISSING_EXPECTED_COHORT_COUNT"] > 0
        self.assertTrue(self.exposure.loc[missing, "MISSING_SIEMBRA_WEIGHT"].isna().all())
        self.assertTrue((self.exposure.loc[~missing, "MISSING_SIEMBRA_WEIGHT"] == 0).all())

    def test_16_climate_family_roles_are_deferred_and_all_metrics_preserved(self) -> None:
        self.assertEqual(
            self.config["climate_family_role_selection"],
            "DEFERRED_TO_ECONOMETRIC_DESIGN_MASTER",
        )
        self.assertEqual(tuple(self.config["climate_variables_preserved"]), e1.CLIMATE_VARIABLES)
        self.assertTrue(set(e1.CLIMATE_VARIABLES) <= set(self.exposure.columns))

    def test_17_b3_role_and_support_are_explicit(self) -> None:
        self.assertEqual(self.config["b3_role"], "STRICT_SENSITIVITY")
        support = self.config["b3_stage_a_support"]
        self.assertEqual(support["structural_grid_rows"], 707)
        self.assertEqual(support["b3_matched_structural_rows"], 650)
        self.assertEqual(support["b3_absent_structural_rows"], 57)
        self.assertEqual(support["strict_valid_rows"], 38)

    def test_18_candidate_exposure_shape_and_validity_are_exact(self) -> None:
        self.assertEqual(list(self.exposure.columns), list(e1.OUTPUT_COLUMNS))
        self.assertEqual(len(self.exposure), 707)
        self.assertEqual(int(self.exposure["EXPOSURE_VALID"].sum()), 608)
        self.assertEqual(self.exposure.duplicated(["UBIGEO", "COD_CULTIVO", "CAMPAIGN_ID"]).sum(), 0)
        self.assertEqual(
            self.exposure.groupby("COD_CULTIVO")["EXPOSURE_VALID"].sum().to_dict(),
            {"14010020000": 285, "14010070000": 323},
        )

    def test_19_valid_exposures_have_complete_physical_metrics(self) -> None:
        valid = self.exposure[self.exposure["EXPOSURE_VALID"]]
        invalid = self.exposure[~self.exposure["EXPOSURE_VALID"]]
        self.assertEqual(int(valid[list(e1.CLIMATE_VARIABLES)].isna().sum().sum()), 0)
        self.assertEqual(int(invalid[list(e1.CLIMATE_VARIABLES)].notna().sum().sum()), 0)
        self.assertTrue(np.isfinite(valid[list(e1.CLIMATE_VARIABLES)].to_numpy(dtype=float)).all())
        self.assertTrue((valid["RAIN_MM"] >= 0).all())
        self.assertTrue((valid["TMIN_C"] <= valid["TMAX_C"]).all())

    def test_20_conditional_normalization_is_exact_and_disclosed(self) -> None:
        valid = self.exposure[self.exposure["EXPOSURE_VALID"]]
        self.assertTrue((valid["EXPOSURE_WEIGHT_DENOMINATOR"] > 0).all())
        self.assertTrue((valid["EXPOSURE_WEIGHT_SUM"].sub(1.0).abs() <= 1e-12).all())
        self.assertTrue(
            (valid["NORMALIZATION_SCOPE"] == "POSITIVE_OBSERVED_UNAMBIGUOUS_ASSIGNED_SIEMBRA_ONLY").all()
        )
        expected = valid["ASSIGNED_UNAMBIGUOUS_SIEMBRA"] / valid["OBSERVED_SIEMBRA_TOTAL"]
        self.assertTrue((valid["IDENTIFIED_OBSERVED_WEIGHT_FRACTION"].sub(expected).abs() <= 1e-12).all())

    def test_21_stage_a_metrics_are_complete_by_crop_campaign(self) -> None:
        metrics = self.config["stage_a_metrics"]
        self.assertEqual(metrics["structural_grid_rows"], 707)
        self.assertEqual(metrics["exposure_valid_rows"], 608)
        self.assertEqual(len(metrics["by_crop_campaign"]), 14)
        self.assertTrue(all(item["structural_rows"] > 0 for item in metrics["by_crop_campaign"]))

    def test_22_measurement_error_assessment_covers_all_required_mechanisms(self) -> None:
        mechanisms = {item["mechanism"] for item in self.config["measurement_error_assessment"]}
        self.assertEqual(
            mechanisms,
            {
                "MONTHLY_SIEMBRA_COHORT_WEIGHTS", "RICE_TRANSPLANT_ESTABLISHMENT_PROXY",
                "BROAD_ATTRIBUTION_LAG_INTERVAL", "CROSS_CAMPAIGN_AMBIGUITY",
                "DISTRICT_LEVEL_CLIMATE_AGGREGATION", "MONTHLY_PHENOLOGICAL_EXPOSURE",
            },
        )
        self.assertTrue(all("NOT_QUANTIFIED" in item["classification"] or "UNCERTAINTY" in item["classification"] or "MASS" in item["classification"] for item in self.config["measurement_error_assessment"]))

    def test_23_future_scenario_compatibility_is_nonprivileging(self) -> None:
        scenario = self.config["future_scenario_compatibility"]
        self.assertEqual(scenario["status"], "PASS_WITH_LIMITATION")
        self.assertEqual(scenario["future_calendar_assumption"], "REQUIRES_FUTURE_SCENARIO_GATE")
        self.assertEqual(scenario["reference_configuration_privilege"], "NONE")

    def test_24_stage_b_overlay_counts_are_exact_and_post_decision(self) -> None:
        self.assertEqual(len(self.overlay), 707)
        d0_valid = sum(row["OUTCOME_VALID_FLAG"] == "TRUE" for row in self.overlay)
        exposure_valid = sum(row["EXPOSURE_VALID"] == "TRUE" for row in self.overlay)
        joint = sum(row["OUTCOME_VALID_FLAG"] == "TRUE" and row["EXPOSURE_VALID"] == "TRUE" for row in self.overlay)
        self.assertEqual((d0_valid, exposure_valid, joint), (646, 608, 599))
        self.assertIn("POST_DECISION_DIAGNOSTIC_NOT_SELECTION_EVIDENCE", self.report)

    def test_25_stage_b_did_not_revise_locked_stage_a_artifacts(self) -> None:
        before = {path: sha256(path) for path in (CONFIG, MATRIX, EXPOSURE)}
        summary = e1.run_stage_b(ROOT, EXPECTED_STAGE_A_SHA)
        after = {path: sha256(path) for path in before}
        self.assertEqual(before, after)
        self.assertFalse(summary["decision_changed_after_overlay"])
        self.assertFalse(self.config["decision_changed_after_d0_overlay"])

    def test_26_stage_a_record_predates_overlay_and_hash_is_recorded(self) -> None:
        self.assertLessEqual(CONFIG.stat().st_mtime_ns, OVERLAY.stat().st_mtime_ns)
        self.assertEqual(sha256(CONFIG), EXPECTED_STAGE_A_SHA)
        self.assertIn(f"STAGE_A_DECISION_SHA256={EXPECTED_STAGE_A_SHA}", self.report)

    def test_27_stage_b_reader_is_limited_to_structure_and_validity(self) -> None:
        self.assertEqual(set(e1.D0_STAGE_B_COLUMNS) - set(e1.D0_STAGE_A_COLUMNS), {"OUTCOME_VALID_FLAG", "EXCLUSION_REASON"})
        source = inspect.getsource(e1.read_stage_b_d0_support)
        for forbidden in ("TRANSIENT_CAMPAIGN_YIELD_RAW", "PRODUCCION", "COSECHA", "PRECIO"):
            self.assertNotIn(forbidden, source)

    def test_28_two_independent_builds_are_byte_identical(self) -> None:
        generated = (e1.CONFIG_REL, e1.EXPOSURE_REL, e1.REPORT_REL, e1.CANDIDATE_MATRIX_REL, e1.SUPPORT_OVERLAY_REL)
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            roots = (Path(first), Path(second))
            digests = []
            for root in roots:
                stage_a_sha = e1.run_stage_a(root)
                self.assertEqual(stage_a_sha, EXPECTED_STAGE_A_SHA)
                e1.run_stage_b(root, stage_a_sha)
                digests.append({relative.as_posix(): sha256(root / relative) for relative in generated})
            self.assertEqual(digests[0], digests[1])
            self.assertEqual(digests[0], {relative.as_posix(): EXPECTED_HASHES[ROOT / relative] for relative in generated})

    def test_29_text_artifacts_are_utf8_lf_with_one_final_lf(self) -> None:
        for path in (CONFIG, REPORT, MATRIX, OVERLAY, SCRIPT, TEST):
            payload = path.read_bytes()
            self.assertFalse(payload.startswith(b"\xef\xbb\xbf"), str(path))
            self.assertNotIn(b"\r", payload, str(path))
            self.assertTrue(payload.endswith(b"\n"), str(path))
            self.assertFalse(payload.endswith(b"\n\n"), str(path))
            payload.decode("utf-8")

    def test_30_parquet_schema_and_writer_contract_are_exact(self) -> None:
        self.assertEqual(pq.read_schema(EXPOSURE).remove_metadata(), e1.ARROW_SCHEMA)
        self.assertEqual(self.config["parquet_writer"], e1.PARQUET_WRITER)
        self.assertEqual(pq.ParquetFile(EXPOSURE).metadata.num_row_groups, 1)

    def test_31_no_econometric_or_optimization_library_is_imported(self) -> None:
        tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertTrue({"statsmodels", "linearmodels", "sklearn", "pymc", "cvxpy", "pyomo"}.isdisjoint(imports))

    def test_32_no_forbidden_attribution_shortcut_is_authorized(self) -> None:
        firewalls = self.config["firewalls"]
        for key in (
            "random_assignment", "probability_allocation", "equal_or_fractional_splitting",
            "nearest_or_midpoint_assignment", "uniform_weighting", "outcome_based_assignment",
            "sample_size_maximization", "silent_renormalization", "silent_interpolation", "siembra_imputation",
        ):
            self.assertEqual(firewalls[key], "PROHIBITED")

    def test_33_overlay_is_complete_by_crop_campaign_and_district(self) -> None:
        frame = pd.DataFrame(self.overlay)
        self.assertEqual(frame.groupby(["COD_CULTIVO", "CAMPAIGN_ID"]).ngroups, 14)
        self.assertEqual(frame.groupby("COD_CULTIVO").size().to_dict(), {"14010020000": 322, "14010070000": 385})
        self.assertEqual(frame.duplicated(["UBIGEO", "COD_CULTIVO", "CAMPAIGN_ID"]).sum(), 0)

    def test_34_selection_uses_no_numerical_score(self) -> None:
        self.assertEqual(
            self.config["selected_architecture"]["selection_basis"],
            "INDISPENSABLE_DOMAIN_ADJUDICATION_NOT_NUMERICAL_SCORE_OR_OUTCOME_SUPPORT",
        )
        self.assertNotIn("SCORE", self.matrix_columns)

    def test_35_b3_rejection_is_not_based_on_sample_size_alone(self) -> None:
        b3 = next(item for item in self.config["candidate_inventory"] if item["candidate_id"] == "E1-C1")
        self.assertIn("selectively supported", b3["reason"])
        statuses = {row["DOMAIN"]: row["STATUS"] for row in self.matrix if row["CANDIDATE_ID"] == "E1-C1"}
        self.assertEqual(statuses["CAMPAIGN_ATTRIBUTION_IDENTIFICATION"], "PASS")
        self.assertEqual(statuses["SUSCEPTIBILITY_TO_SELECTION"], "FAIL")

    def test_36_report_config_matrix_and_artifact_are_consistent(self) -> None:
        self.assertIn(self.config["selected_architecture"]["name"], self.report)
        self.assertIn(f"B3_ROLE={self.config['b3_role']}", self.report)
        self.assertIn(f"AMBIGUOUS_COHORT_RULE={self.config['ambiguity_rule']}", self.report)
        self.assertIn(f"SIEMBRA_WEIGHT_RULE={self.config['siembra_weight_rule']}", self.report)
        self.assertIn(f"CLIMATE_FAMILY_ROLE_SELECTION={self.config['climate_family_role_selection']}", self.report)
        self.assertIn("DECISION_CHANGED_AFTER_D0_OVERLAY=FALSE", self.report)
        self.assertIn(self.config["next_action"], self.report)


if __name__ == "__main__":
    unittest.main()
