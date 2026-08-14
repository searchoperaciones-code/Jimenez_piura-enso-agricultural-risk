from __future__ import annotations

import ast
import hashlib
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import climate_exposure_b0_preflight as b0  # noqa: E402


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class ClimateExposureB0PreflightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = b0.build_report_payload()
        cls.source = b0.Path(__file__).resolve().parents[1].joinpath(
            "scripts", "climate_exposure_b0_preflight.py"
        ).read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.source)

    def test_01_upstream_hashes_frozen(self):
        gate = self.payload["upstream_hash_gate"]
        self.assertEqual(gate["status"], "PASS")
        self.assertEqual(sha256_file(b0.SPEC), b0.EXPECTED_SPEC_SHA)
        self.assertEqual(sha256_file(b0.WINDOWS), b0.EXPECTED_WINDOWS_SHA)
        self.assertEqual(sha256_file(b0.PHENOLOGY_CERTIFICATE), b0.EXPECTED_PHENOLOGY_CERT_SHA)
        self.assertEqual(sha256_file(b0.CLIMATE), b0.EXPECTED_CLIMATE_SHA)

    def test_02_base_commit_and_tag(self):
        baseline = self.payload["baseline"]
        self.assertEqual(baseline["branch"], b0.EXPECTED_BRANCH)
        self.assertEqual(baseline["head"], b0.EXPECTED_HEAD)
        self.assertEqual(baseline["tag_target"], b0.EXPECTED_HEAD)

    def test_03_no_forbidden_exposure_output_exists(self):
        self.assertEqual(b0.no_forbidden_outputs()["status"], "PASS")

    def test_04_preflight_script_does_not_read_forbidden_panel_fields(self):
        forbidden = {"YIELD_RAW", "PRODUCCION", "PRECIO", "PRECIO_CHACRA"}
        for call in self._pandas_reader_calls("read_csv"):
            path_text = ast.unparse(call.args[0]) if call.args else ""
            if "PANEL" not in path_text:
                continue
            loaded = self._literal_usecols(call)
            self.assertTrue(loaded)
            self.assertFalse(forbidden & set(loaded))

    def test_05_preflight_script_does_not_read_harvest_or_production_values(self):
        forbidden = {"COSECHA", "PRODUCCION"}
        for call in self._pandas_reader_calls("read_csv"):
            path_text = ast.unparse(call.args[0]) if call.args else ""
            if "TEMPORAL" not in path_text:
                continue
            loaded = self._literal_usecols(call)
            self.assertTrue(loaded)
            self.assertFalse(forbidden & set(loaded))

    def test_06_icen_is_not_read(self):
        for call in self._pandas_reader_calls("read_csv"):
            call_text = ast.unparse(call).lower()
            self.assertNotIn("icen_clean", call_text)
        self.assertNotIn("data/processed/icen", self.source.lower())

    def test_07_five_crop_codes_exact(self):
        self.assertTrue(self.payload["frozen_contract_checks"]["five_crop_codes_exact"])

    def test_08_seven_frozen_windows_exact(self):
        self.assertTrue(self.payload["frozen_contract_checks"]["seven_window_ids_exact"])

    def test_09_climate_family_and_aggregation_contract_exact(self):
        self.assertTrue(self.payload["frozen_contract_checks"]["climate_families_exact"])
        self.assertTrue(self.payload["frozen_contract_checks"]["aggregation_exact"])

    def test_10_strict_campaign_diagnostic_reproduces_38_of_745(self):
        strict = self.payload["strict_diagnostic_reproduction"]
        self.assertEqual(strict["status"], "PASS")
        self.assertEqual(strict["combined"], {"valid": 38, "total": 745})
        self.assertEqual(strict["by_crop"]["14010020000"], {"valid": 31, "total": 340})
        self.assertEqual(strict["by_crop"]["14010070000"], {"valid": 7, "total": 405})

    def test_11_perennial_structural_candidate_count(self):
        perennial = self.payload["perennial_structural_count"]
        self.assertEqual(perennial["candidate_rows"], 1657)
        self.assertEqual(perennial["status"], "PASS")

    def test_12_zero_sowing_is_not_treated_as_missing(self):
        sowing = self.payload["sowing_missing_zero_summary"]
        for values in sowing.values():
            self.assertGreaterEqual(values["sowing_zero"], 0)
            self.assertEqual(values["sowing_missing"], 0)
        self.assertGreater(sowing["14010020000|ARROZ"]["sowing_zero"], 0)
        self.assertGreater(sowing["14010070000|MAIZ AMARILLO DURO"]["sowing_zero"], 0)

    def test_13_leap_year_arithmetic(self):
        rice = b0.transient_attribution("14010020000", 2020, 2)
        mad = b0.transient_attribution("14010070000", 2020, 2)
        self.assertEqual(rice["ANCHOR_DATE_MAX"], "2020-02-29")
        self.assertEqual(rice["HARVEST_DATE_MAX"], "2020-07-16")
        self.assertEqual(mad["ANCHOR_DATE_MAX"], "2020-02-29")
        self.assertEqual(mad["HARVEST_DATE_MAX"], "2020-08-17")

    def test_14_2015_structural_left_boundary_detected(self):
        boundary = self.payload["boundary_findings"]
        self.assertEqual(boundary["structural_left_truncation_campaign"], "2015/2016")
        self.assertEqual(boundary["left_truncation_panel_keys"], 95)
        self.assertEqual(boundary["left_truncation_required_sowing_months"], 527)

    def test_15_2024_12_right_boundary_explicitly_assessed(self):
        boundary = self.payload["boundary_findings"]
        self.assertEqual(boundary["climate_end_yyyymm"], 202412)
        self.assertEqual(boundary["right_edge_affected_rows"], 253)
        self.assertEqual(boundary["right_edge_candidate_months"], [202409, 202410, 202411, 202412])

    def test_16_no_stage_b_parquet_output_has_been_built(self):
        for path in b0.FORBIDDEN_STAGE_B_OUTPUTS:
            self.assertFalse(path.exists(), path)

    def test_17_canonical_transient_universe_is_all_observed_source_rows(self):
        universe = self.payload["transient_candidate_universes"]
        self.assertEqual(universe["canonical_universe_name"], b0.CANONICAL_TRANSIENT_UNIVERSE)
        self.assertEqual(universe["canonical_universe_rows"], 8977)
        self.assertEqual(universe["A_all_transient_temporal_rows"]["rows"], 8977)
        self.assertEqual(universe["canonical_universe_status"], "DIRECTOR_APPROVED_B0_2")

    def test_18_main_panel_universe_remains_diagnostic_only(self):
        universe = self.payload["transient_candidate_universes"]
        self.assertEqual(
            universe["B_transient_rows_in_main_panel_key_years"]["role"],
            "DIAGNOSTIC_ONLY_NOT_CANONICAL_UNIVERSE",
        )
        self.assertEqual(universe["B_transient_rows_in_main_panel_key_years"]["rows"], 7417)

    def test_19_no_cohort_ledger_densification(self):
        universe = self.payload["transient_candidate_universes"]
        self.assertTrue(universe["no_synthetic_month_densification"])
        self.assertTrue(universe["no_main_panel_restriction"])
        self.assertTrue(universe["no_strict_slot_universe"])
        self.assertGreater(
            universe["C_strict_required_campaign_sowing_rows"]["required_rows"],
            universe["canonical_universe_rows"],
        )

    def test_20_pipe_delimited_month_representation_contract(self):
        self.assertEqual(b0.format_month_list([202501, 202412, 202411]), "202411|202412|202501")
        self.assertEqual(b0.format_month_list([]), "")
        contract = self.payload["director_technical_adjudication_b0_2"]["contract"]["month_list_representation"]
        self.assertEqual(contract, b0.MONTH_LIST_REPRESENTATION_CONTRACT)
        self.assertNotIn("[", b0.format_month_list([202401]))
        self.assertNotIn(" ", b0.format_month_list([202401, 202402]))

    def test_21_incomplete_windows_prohibit_partial_aggregates(self):
        policy = b0.cohort_aggregation_policy([202411, 202412, 202501], [202411, 202412])
        self.assertFalse(policy["CLIMATE_WINDOW_COMPLETE"])
        self.assertFalse(policy["COHORT_EXPOSURE_VALID"])
        self.assertFalse(policy["PARTIAL_AGGREGATION_ALLOWED"])
        self.assertEqual(set(policy["AGGREGATED_CLIMATE_VALUES"]), set(b0.AUTHORIZED_CLIMATE_VARIABLES))
        self.assertTrue(all(value is None for value in policy["AGGREGATED_CLIMATE_VALUES"].values()))

    def test_22_right_edge_vs_internal_gap_distinction(self):
        self.assertEqual(
            b0.window_failure_reason([202411, 202412, 202501], [202411, 202412]),
            "CLIMATE_WINDOW_RIGHT_TRUNCATED",
        )
        self.assertEqual(
            b0.window_failure_reason([202410, 202411], [202410]),
            "CLIMATE_WINDOW_INTERNAL_GAP",
        )
        self.assertEqual(
            b0.window_failure_reason([202410, 202501], []),
            "CLIMATE_WINDOW_RIGHT_TRUNCATED|CLIMATE_WINDOW_INTERNAL_GAP",
        )

    def test_23_zero_sowing_remains_valid_when_climate_complete(self):
        preview = b0.cohort_validity_preview(0.0, [202401, 202402], [202401, 202402])
        self.assertEqual(
            preview,
            {
                "SIEMBRA_OBSERVED": True,
                "CLIMATE_WINDOW_COMPLETE": True,
                "COHORT_EXPOSURE_VALID": True,
                "FAILURE_REASON": "NONE",
            },
        )

    def test_24_exact_arrow_dtype_contract(self):
        expected = {
            "string": [
                "UBIGEO",
                "COD_CULTIVO",
                "CROP_STD",
                "WINDOW_ID",
                "ARCHITECTURE",
                "CAMPAIGN_MIN",
                "CAMPAIGN_MAX",
                "CAMPAIGN_ATTRIBUTION_STATUS",
                "ASSIGNED_CAMPAIGN_ID",
                "CAMPAIGN_ID",
                "TIME_BASIS",
                "REFERENCE_PERIOD_ID",
                "FAILURE_REASON",
                "EXPECTED_CLIMATE_MONTHS",
                "SUPPORTED_CLIMATE_MONTHS",
            ],
            "int16": [
                "ANCHOR_YEAR",
                "CAMPAIGN_START_YEAR",
                "CAMPAIGN_END_YEAR",
                "REFERENCE_START_YEAR",
                "REFERENCE_END_YEAR",
                "REFERENCE_CALENDAR_YEAR",
                "ATTRIBUTION_L_MIN_DAYS",
                "ATTRIBUTION_L_MAX_DAYS",
                "UNAMBIGUOUS_COHORT_COUNT",
                "AMBIGUOUS_COHORT_COUNT",
            ],
            "int8": ["ANCHOR_MONTH"],
            "int32": ["ANCHOR_YYYYMM", "CLIMATE_WINDOW_START_YYYYMM", "CLIMATE_WINDOW_END_YYYYMM"],
            "date32": ["ANCHOR_DATE_MIN", "ANCHOR_DATE_MAX", "HARVEST_DATE_MIN", "HARVEST_DATE_MAX"],
            "float64": [
                "SIEMBRA",
                "RAIN_MM",
                "TMAX_C",
                "TMIN_C",
                "RAIN_ANOM_MM",
                "TMAX_ANOM_C",
                "TMIN_ANOM_C",
                "RAIN_Z",
                "TMAX_Z",
                "TMIN_Z",
                "CAMPAIGN_SIEMBRA_DENOMINATOR",
                "COHORT_WEIGHT_SUM",
                "EXPECTED_WEIGHT",
                "SUPPORTED_WEIGHT",
                "MISSING_WEIGHT",
            ],
            "bool": [
                "SIEMBRA_OBSERVED",
                "CLIMATE_WINDOW_COMPLETE",
                "COHORT_EXPOSURE_VALID",
                "CAMPAIGN_WEIGHTED_EXPOSURE_VALID",
                "EXPOSURE_VALID",
            ],
        }
        self.assertEqual(b0.ARROW_DTYPE_CONTRACT_BY_TYPE, expected)
        by_artifact = self.payload["director_technical_adjudication_b0_2"]["contract"]["arrow_dtype_contract"][
            "by_artifact"
        ]
        for artifact_schema in by_artifact.values():
            self.assertTrue(artifact_schema)
            self.assertTrue(set(artifact_schema.values()).issubset(set(expected)))

    def test_25_exact_failure_code_vocabulary_and_order(self):
        contract = self.payload["director_technical_adjudication_b0_2"]["contract"]["failure_reason_contract"]
        self.assertEqual(contract["success"], "NONE")
        self.assertEqual(
            contract["transient_cohort_order"],
            ["CLIMATE_WINDOW_RIGHT_TRUNCATED", "CLIMATE_WINDOW_INTERNAL_GAP"],
        )
        self.assertFalse(contract["ambiguous_cross_campaign_is_failure"])
        self.assertEqual(
            contract["strict_campaign_order"],
            [
                "STRUCTURAL_LEFT_TRUNCATION",
                "REQUIRED_U_SIEMBRA_NOT_OBSERVED",
                "REQUIRED_A_SIEMBRA_NOT_OBSERVED",
                "AMBIGUOUS_COHORT_SIEMBRA_NONZERO",
                "NO_POSITIVE_UNAMBIGUOUS_SIEMBRA",
                "POSITIVE_WEIGHT_COHORT_CLIMATE_INCOMPLETE",
                "WEIGHT_SUM_TOLERANCE_FAIL",
            ],
        )
        self.assertEqual(
            contract["perennial_order"],
            ["CLIMATE_WINDOW_OUTSIDE_AVAILABLE_RANGE", "CLIMATE_WINDOW_INTERNAL_GAP"],
        )

    def test_26_unified_long_build_hold(self):
        self.assertEqual(self.payload["unified_long_build_status"]["status"], "UNIFIED_LONG_BUILD = HOLD")
        contract = self.payload["director_technical_adjudication_b0_2"]["contract"]["unified_long_contract"]
        self.assertEqual(contract["UNIFIED_LONG_BUILD"], "HOLD")
        self.assertTrue(contract["do_not_build_during_climate_exposure_master_v1"])

    def test_27_report_contains_b0_2_adjudication_section(self):
        report = b0.render_markdown(self.payload)
        self.assertIn("## DIRECTOR TECHNICAL ADJUDICATION — B0.2", report)
        self.assertIn("## B0.1 Empirical Findings", report)

    def _pandas_reader_calls(self, method_name: str):
        for node in ast.walk(self.tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if isinstance(func, ast.Attribute) and func.attr == method_name:
                yield node

    def _literal_usecols(self, call: ast.Call) -> list[str]:
        for keyword in call.keywords:
            if keyword.arg != "usecols":
                continue
            if isinstance(keyword.value, ast.Name):
                return list(getattr(b0, keyword.value.id))
            return list(ast.literal_eval(keyword.value))
        return []


if __name__ == "__main__":
    unittest.main()
