from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import phenology_stage_a as stage_a  # noqa: E402
import audit_phenology_stage_a as stage_a_audit  # noqa: E402


QA = ROOT / "outputs" / "phenology" / "qa"
PROC = ROOT / "data" / "processed" / "phenology"
BASE_SHA = "e4710b1429ed54c557e6c0a88212a24a6fdd7d47"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class PhenologyStageATests(unittest.TestCase):
    def test_01_exact_base_sha_ancestry(self):
        result = subprocess.run(["git", "merge-base", "--is-ancestor", BASE_SHA, "HEAD"], cwd=ROOT)
        self.assertEqual(result.returncode, 0)

    def test_02_exact_raw_hashes(self):
        for rel_path, expected in stage_a.INPUT_HASHES.items():
            if rel_path.startswith("data/raw/"):
                self.assertEqual(sha256_file(ROOT / rel_path), expected, rel_path)

    def test_03_exact_panel_and_climate_hashes_byte_only(self):
        for rel_path in [
            "data/processed/panel_master.csv",
            "data/processed/panel_balanceado.csv",
            "data/processed/climate/climate_monthly_primary.parquet",
        ]:
            self.assertEqual(sha256_file(ROOT / rel_path), stage_a.INPUT_HASHES[rel_path], rel_path)

    def test_04_exact_seed_hash(self):
        rel_path = "config/phenology/PHENOLOGY_EVIDENCE_REGISTRY_SEED.csv"
        self.assertEqual(sha256_file(ROOT / rel_path), stage_a.INPUT_HASHES[rel_path])

    def test_05_target_crop_codes_preserved_as_strings(self):
        registry = pd.read_csv(PROC / "phenology_evidence_registry.csv", dtype={"crop_code": "string"})
        crop_codes = set(registry["crop_code"].astype(str))
        self.assertTrue(set(stage_a.TARGET_CROPS).issubset(crop_codes))
        for code in stage_a.TARGET_CROPS:
            self.assertIsInstance(code, str)

    def test_06_raw_monthly_source_key_unique(self):
        raw = pd.read_csv(stage_a.RAW_GORE, usecols=["UBIGEO", "MES", "COD_CULTIVO"], dtype={"UBIGEO": "string", "COD_CULTIVO": "string"})
        self.assertEqual(int(raw.duplicated(["UBIGEO", "MES", "COD_CULTIVO"]).sum()), 0)

    def test_07_certified_row_counts_match(self):
        temporal = read_json(QA / "temporal_source_integrity_report.json")
        self.assertEqual(temporal["raw_rows"], 124514)
        self.assertEqual(temporal["target_crop_raw_rows"], 23540)
        self.assertEqual(temporal["observed_raw_month_min"], 201508)
        self.assertEqual(temporal["observed_raw_month_max"], 202412)

    def test_08_blanks_are_not_coerced_to_zero(self):
        temporal = read_json(QA / "temporal_source_integrity_report.json")
        self.assertFalse(temporal["blank_zero_semantics"]["missing_filled_with_zero"])
        self.assertGreater(temporal["blank_zero_semantics"]["numeric_missing_cells"]["COSECHA"], 0)
        self.assertGreater(temporal["blank_zero_semantics"]["numeric_zero_cells"]["COSECHA"], 0)

    def test_09_entropy_synthetic_cases(self):
        single = np.zeros(12)
        single[0] = 1.0
        uniform = np.ones(12) / 12
        self.assertAlmostEqual(stage_a.normalized_entropy(single), 0.0, places=12)
        self.assertAlmostEqual(stage_a.normalized_entropy(uniform), 1.0, places=12)

    def test_10_circular_concentration_synthetic_cases(self):
        jan = np.zeros(12)
        jan[0] = 1.0
        uniform = np.ones(12) / 12
        r_jan, _, month_jan = stage_a.circular_concentration(jan)
        r_uniform, angle_uniform, month_uniform = stage_a.circular_concentration(uniform)
        self.assertAlmostEqual(r_jan, 1.0, places=12)
        self.assertAlmostEqual(month_jan, 1.0, places=12)
        self.assertLess(r_uniform, 1e-12)
        self.assertIsNone(angle_uniform)
        self.assertIsNone(month_uniform)

    def test_11_cyclic_k_algorithm_december_january_wrap(self):
        shares = np.zeros(12)
        shares[0] = 0.5
        shares[11] = 0.5
        k50 = stage_a.cyclic_k_arc(shares, 0.50)
        k75 = stage_a.cyclic_k_arc(shares, 0.75)
        self.assertEqual(k50["k"], 1)
        self.assertEqual(k50["start_month"], 1)
        self.assertEqual(k75["k"], 2)
        self.assertEqual(k75["start_month"], 12)
        self.assertEqual(k75["end_month"], 1)

    def test_12_diagnostic_lag_mapping_crosses_calendar_year(self):
        self.assertEqual(stage_a.add_months(2016, 1, -2), (2015, 11, 201511))
        self.assertEqual(stage_a.add_months(2016, 3, -6), (2015, 9, 201509))

    def test_13_no_selected_lag_field_exists(self):
        lag = pd.read_csv(QA / "transient_lag_compatibility.csv")
        lowered = [col.lower() for col in lag.columns]
        self.assertNotIn("best_lag", lowered)
        self.assertNotIn("selected_lag", lowered)
        self.assertTrue((lag["DIAGNOSTIC_ONLY"].astype(str).str.upper().isin(["TRUE", "1"])).all())
        self.assertTrue((lag["SELECTION_STATUS"] == "NOT_SELECTED_STAGE_A").all())

    def test_14_2016_pre_august_support_gap_synthetic_case(self):
        harvest_share = np.zeros(12)
        harvest_share[0] = 1.0
        pred_mes = stage_a.add_months(2016, 1, -6)[2]
        unsupported_share = float(harvest_share[0]) if pred_mes < 201508 else 0.0
        self.assertEqual(pred_mes, 201507)
        self.assertEqual(unsupported_share, 1.0)

    def test_15_permanent_production_shares_are_descriptive_only(self):
        monthly = pd.read_csv(PROC / "temporal_structure_monthly.csv", dtype={"COD_CULTIVO": "string"})
        permanent = monthly[monthly["COD_CULTIVO"].isin(stage_a.PERMANENT_CROPS)]
        self.assertGreater(permanent["PRODUCTION_SHARE"].notna().sum(), 0)
        summary = pd.read_csv(PROC / "temporal_structure_summary.csv", dtype={"COD_CULTIVO": "string"})
        permanent_summary = summary[(summary["COD_CULTIVO"].isin(stage_a.PERMANENT_CROPS)) & (summary["VARIABLE"] == "PRODUCCION")]
        self.assertTrue((permanent_summary["DESCRIPTIVE_ONLY"].astype(str).str.upper().isin(["TRUE", "1"])).all())
        self.assertTrue((permanent_summary["SELECTION_STATUS"] == "NOT_SELECTED_STAGE_A").all())

    def test_15a_transient_monthly_produccion_is_null(self):
        monthly = pd.read_csv(PROC / "temporal_structure_monthly.csv", dtype={"COD_CULTIVO": "string"})
        transient = monthly[monthly["COD_CULTIVO"].isin(stage_a.TRANSIENT_CROPS)]
        self.assertEqual(int(transient["PRODUCCION"].notna().sum()), 0)

    def test_15b_transient_production_metadata_is_null_except_status(self):
        monthly = pd.read_csv(PROC / "temporal_structure_monthly.csv", dtype={"COD_CULTIVO": "string"})
        transient = monthly[monthly["COD_CULTIVO"].isin(stage_a.TRANSIENT_CROPS)]
        metadata_cols = [
            "PRODUCTION_ANNUAL_DENOMINATOR",
            "PRODUCTION_MISSING_MONTH_COUNT",
            "PRODUCTION_POSITIVE_MONTH_COUNT",
            "PRODUCTION_SHARE",
        ]
        self.assertEqual(int(transient[metadata_cols].notna().sum().sum()), 0)
        self.assertTrue((transient["PRODUCTION_DENOMINATOR_STATUS"] == "NOT_COMPUTED_TRANSIENT").all())

    def test_15c_no_transient_production_summary_rows(self):
        summary = pd.read_csv(PROC / "temporal_structure_summary.csv", dtype={"COD_CULTIVO": "string"})
        transient_production = summary[(summary["COD_CULTIVO"].isin(stage_a.TRANSIENT_CROPS)) & (summary["VARIABLE"] == "PRODUCCION")]
        self.assertEqual(len(transient_production), 0)

    def test_15d_transient_year_crossing_production_values_are_null(self):
        crossing = pd.read_csv(QA / "year_crossing_audit.csv", dtype={"COD_CULTIVO": "string"})
        transient = crossing[crossing["COD_CULTIVO"].isin(stage_a.TRANSIENT_CROPS)]
        production_cols = [col for col in transient.columns if "PRODUCTION" in col.upper()]
        self.assertEqual(int(transient[production_cols].notna().sum().sum()) if production_cols else 0, 0)

    def test_16_no_forbidden_outcome_fields_in_stage_a_outputs(self):
        forbidden = {"YIELD_RAW", "YIELD_UNIT", "PRECIO", "PRECIO_CHACRA"}
        for path in list(PROC.glob("*.csv")) + list(QA.glob("*.csv")):
            columns = set(pd.read_csv(path, nrows=0).columns)
            self.assertTrue(columns.isdisjoint(forbidden), str(path))

    def test_17_no_climate_variables_in_temporal_outputs(self):
        forbidden = {"RAIN_MM", "TMAX_C", "TMIN_C", "RAIN_ANOM_MM", "TMAX_ANOM_C", "TMIN_ANOM_C"}
        for path in [PROC / "temporal_structure_monthly.csv", PROC / "temporal_structure_summary.csv"]:
            columns = set(pd.read_csv(path, nrows=0).columns)
            self.assertTrue(columns.isdisjoint(forbidden), str(path))

    def test_18_forbidden_stage_b_outputs_absent(self):
        forbidden_stage_b_outputs = {"crop_exposure_architecture.csv", "phenology_exposures_panel.parquet", "phenology_exposures_long.parquet"}
        for root in [ROOT / "data" / "processed" / "phenology", ROOT / "outputs" / "phenology"]:
            for path in root.rglob("*"):
                self.assertNotIn(path.name, forbidden_stage_b_outputs)

    def test_19_no_outcome_snooping_audit_pass(self):
        audit = read_json(QA / "no_outcome_snooping_audit.json")
        self.assertEqual(audit["status"], "PASS")
        self.assertEqual(audit["finding_count"], 0)
        self.assertFalse(audit["climate_parsed_for_analysis"])
        self.assertFalse(audit["panel_outcome_data_parsed"])
        self.assertEqual(audit["transient_production_firewall"]["status"], "PASS")
        self.assertEqual(audit["transient_production_firewall"]["transient_produccion_nonnull_cells"], 0)
        self.assertEqual(audit["transient_production_firewall"]["transient_production_metadata_nonnull_cells"], 0)
        self.assertEqual(audit["transient_production_firewall"]["transient_production_summary_rows"], 0)
        self.assertEqual(audit["transient_production_firewall"]["transient_year_crossing_production_values"], 0)
        self.assertTrue(audit["transient_production_firewall"]["permanent_production_seasonality_preserved"])

    def test_19a_independent_auditor_detects_synthetic_crop_scope_violation(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            processed = tmp_root / "processed"
            qa = tmp_root / "qa"
            processed.mkdir()
            qa.mkdir()
            pd.DataFrame(
                [
                    {
                        "COD_CULTIVO": "14010020000",
                        "PRODUCCION": 10.0,
                        "PRODUCTION_ANNUAL_DENOMINATOR": 10.0,
                        "PRODUCTION_MISSING_MONTH_COUNT": 0,
                        "PRODUCTION_POSITIVE_MONTH_COUNT": 1,
                        "PRODUCTION_SHARE": 1.0,
                        "PRODUCTION_DENOMINATOR_STATUS": "POSITIVE",
                    },
                    {
                        "COD_CULTIVO": "13010210000",
                        "PRODUCCION": 20.0,
                        "PRODUCTION_ANNUAL_DENOMINATOR": 20.0,
                        "PRODUCTION_MISSING_MONTH_COUNT": 0,
                        "PRODUCTION_POSITIVE_MONTH_COUNT": 1,
                        "PRODUCTION_SHARE": 1.0,
                        "PRODUCTION_DENOMINATOR_STATUS": "POSITIVE",
                    },
                ]
            ).to_csv(processed / "temporal_structure_monthly.csv", index=False)
            pd.DataFrame([{"COD_CULTIVO": "14010070000", "VARIABLE": "PRODUCCION"}]).to_csv(
                processed / "temporal_structure_summary.csv", index=False
            )
            pd.DataFrame([{"COD_CULTIVO": "14010020000", "PRODUCTION_DENOMINATOR": 1.0}]).to_csv(
                qa / "year_crossing_audit.csv", index=False
            )
            result = stage_a_audit.evaluate_transient_production_firewall(processed, qa)
            finding_names = {finding["finding"] for finding in result["findings"]}
            self.assertEqual(result["status"], "FAIL")
            self.assertIn("TRANSIENT_PRODUCCION_VALUE_EXPOSED", finding_names)
            self.assertIn("TRANSIENT_PRODUCTION_METADATA_EXPOSED", finding_names)
            self.assertIn("TRANSIENT_PRODUCTION_SUMMARY_ROW", finding_names)
            self.assertIn("TRANSIENT_YEAR_CROSSING_PRODUCTION_VALUE", finding_names)

    def test_20_two_run_deterministic_core_hashes_identical(self):
        report = read_json(QA / "phenology_stage_a_reproducibility_report.json")
        self.assertEqual(report["status"], "PASS")
        self.assertTrue(report["deterministic_core_outputs_identical"])
        self.assertEqual(report["run1_hashes"], report["run2_hashes"])

    def test_21_protected_upstream_paths_unchanged(self):
        diff = subprocess.run(["git", "diff", "--name-only", BASE_SHA, "--", *stage_a.PROTECTED_PATHS], cwd=ROOT, text=True, capture_output=True, check=True)
        status = subprocess.run(["git", "status", "--short", "--", *stage_a.PROTECTED_PATHS], cwd=ROOT, text=True, capture_output=True, check=True)
        self.assertEqual(diff.stdout.strip(), "")
        self.assertEqual(status.stdout.strip(), "")


if __name__ == "__main__":
    unittest.main()
