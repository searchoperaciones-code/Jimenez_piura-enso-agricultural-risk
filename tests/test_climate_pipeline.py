from __future__ import annotations

import json
import unittest
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
QA = ROOT / "outputs" / "qa" / "climate"
PROC = ROOT / "data" / "processed" / "climate"


def read_json(name: str):
    return json.loads((QA / name).read_text(encoding="utf-8"))


class ClimatePipelineV11Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.boundary = gpd.read_file(PROC / "district_boundaries_piura.geojson")
        cls.all_sources = pd.read_parquet(PROC / "climate_monthly_all_sources.parquet")
        cls.primary = pd.read_parquet(PROC / "climate_monthly_primary.parquet")
        cls.normals = pd.read_parquet(PROC / "climate_normals_1991_2020.parquet")
        cls.anomalies = pd.read_parquet(PROC / "climate_anomalies.parquet")
        cls.main = pd.read_parquet(PROC / "climate_main_period_2016_2023.parquet")
        cls.overlap = pd.read_parquet(PROC / "climate_overlap_2015_2024.parquet")

    def test_01_upstream_hashes_match(self):
        report = read_json("upstream_dataset_integrity_v1_1.json")
        self.assertTrue(report["all_match"])
        self.assertGreaterEqual(len(report["checks"]), 4)

    def test_02_previous_failure_archive_preserved(self):
        hist = QA / "history" / "v1_failed_boundary_attempt"
        self.assertTrue((hist / "climate_execution_report.json").exists())
        self.assertTrue((QA / "history" / "README.md").exists())

    def test_03_boundary_recovery_certificate_pass(self):
        cert = read_json("boundary_recovery_certificate.json")["boundary_recovery"]
        self.assertEqual(cert["status"], "PASS")
        self.assertEqual(cert["selected_institution"], "INEI")
        self.assertEqual(cert["panel_districts_matched"], 55)

    def test_04_boundary_source_is_official_and_allowed(self):
        cert = read_json("boundary_recovery_certificate.json")["boundary_recovery"]
        self.assertEqual(cert["selected_source"], "INEI_IDE_DISTRITO_2023")
        self.assertNotIn(cert["selected_source"], {"GADM", "OSM", "GE0BOUNDARIES", "NATURAL_EARTH"})

    def test_05_boundary_recovery_table_has_hierarchy(self):
        recovery = pd.read_csv(QA / "boundary_source_recovery.csv")
        self.assertTrue({"A1.1", "A1.2", "A1.3", "A2.1", "A2.2", "A3", "B.1", "B.2", "B.3", "C.1", "C.2"}.issubset(set(recovery["priority"])))

    def test_06_boundary_manifest_counts(self):
        manifest = read_json("boundary_manifest.json")
        self.assertEqual(manifest["analytical_feature_count"], 55)
        self.assertEqual(manifest["ubigeo_match"]["matched"], 55)
        self.assertEqual(manifest["processed_crs"], "EPSG:4326")

    def test_07_boundary_geojson_feature_count(self):
        self.assertEqual(len(self.boundary), 55)

    def test_08_boundary_geometries_are_valid_polygons(self):
        self.assertTrue(self.boundary.geometry.is_valid.all())
        self.assertTrue(set(self.boundary.geometry.geom_type).issubset({"Polygon", "MultiPolygon"}))

    def test_09_boundary_ubigeo_unique(self):
        self.assertFalse(self.boundary["UBIGEO"].duplicated().any())

    def test_10_boundary_ubigeo_length_six(self):
        self.assertTrue(self.boundary["UBIGEO"].astype(str).str.fullmatch(r"\d{6}").all())

    def test_11_boundary_name_crosswalk_complete(self):
        crosswalk = pd.read_csv(QA / "boundary_name_crosswalk.csv", dtype={"UBIGEO": "string"})
        self.assertEqual(len(crosswalk), 55)
        self.assertFalse(crosswalk[["GORE_PROVINCIA", "GORE_DISTRITO", "BOUNDARY_PROVINCIA", "BOUNDARY_DISTRITO"]].isna().any().any())

    def test_12_cross_source_comparison_documented_unavailable(self):
        summary = read_json("boundary_cross_source_summary.json")
        self.assertFalse(summary["available"])
        self.assertTrue((QA / "boundary_cross_source_comparison.csv").exists())

    def test_13_chirps_final_only(self):
        sources = pd.read_csv(QA / "climate_sources_frozen.csv")
        chirps = sources[sources["SOURCE_ID"] == "CHIRPS_V3_FINAL"].iloc[0]
        self.assertIn("FINAL", chirps["VERSION"])
        self.assertNotIn("prelim", " ".join(sources.astype(str).stack()).lower())

    def test_14_raw_climate_manifest_counts(self):
        manifest = pd.read_csv(QA / "climate_data_manifest.csv")
        counts = manifest.groupby("VARIABLE").size().to_dict()
        self.assertEqual(counts.get("RAIN"), 528)
        self.assertEqual(counts.get("TMAX"), 408)
        self.assertEqual(counts.get("TMIN"), 408)

    def test_15_raw_climate_hashes_and_files_exist(self):
        manifest = pd.read_csv(QA / "climate_data_manifest.csv")
        self.assertTrue(manifest["SHA256"].astype(str).str.fullmatch(r"[0-9a-f]{64}").all())
        self.assertTrue(all((ROOT / p).exists() for p in manifest["LOCAL_FILE"]))

    def test_16_all_sources_row_count(self):
        self.assertEqual(len(self.all_sources), 73920)

    def test_17_primary_row_count(self):
        self.assertEqual(len(self.primary), 22440)

    def test_18_main_period_row_count(self):
        self.assertEqual(len(self.main), 5280)

    def test_19_overlap_row_count(self):
        self.assertEqual(len(self.overlap), 6215)

    def test_20_monthly_date_completeness(self):
        counts = self.primary.groupby("UBIGEO")["DATE"].nunique()
        self.assertEqual(int(counts.min()), 408)
        self.assertEqual(int(counts.max()), 408)

    def test_21_rainfall_nonnegative(self):
        self.assertTrue((self.primary["RAIN_MM"] >= 0).all())

    def test_22_tmin_not_above_tmax(self):
        self.assertTrue((self.primary["TMIN_C"] <= self.primary["TMAX_C"]).all())

    def test_23_required_values_finite(self):
        self.assertTrue(np.isfinite(self.primary[["RAIN_MM", "TMAX_C", "TMIN_C"]]).all().all())

    def test_24_no_duplicate_district_months(self):
        self.assertFalse(self.primary.duplicated(["UBIGEO", "DATE"]).any())

    def test_25_normals_complete(self):
        self.assertEqual(len(self.normals), 660)
        self.assertTrue((self.normals["N_YEARS_AVAILABLE"] == 30).all())

    def test_26_anomaly_zero_property(self):
        zero = pd.read_csv(QA / "anomaly_zero_check.csv")
        self.assertTrue(zero["PASS"].all())

    def test_27_spatial_coverage_passes_hard_gate(self):
        coverage = pd.read_csv(QA / "spatial_coverage_report.csv")
        self.assertTrue((coverage["min_valid_area_fraction"] >= 0.80).all())
        self.assertTrue(coverage["PASS"].all())

    def test_28_coastal_nodata_no_failures(self):
        coastal = pd.read_csv(QA / "coastal_nodata_audit.csv")
        self.assertFalse((coastal["STATUS"] == "FAIL").any())

    def test_29_pixel_support_report_complete(self):
        support = pd.read_csv(QA / "pixel_support_by_district.csv")
        self.assertEqual(len(support), 55 * 3)
        self.assertTrue((support["minimum_contributing_pixels"] > 0).all())

    def test_30_panel_linkage_complete(self):
        linkage = pd.read_csv(QA / "climate_panel_linkage_report.csv").iloc[0]
        self.assertEqual(int(linkage["agricultural_rows_total"]), 1701)
        self.assertEqual(int(linkage["agricultural_rows_complete_climate"]), 1701)
        self.assertAlmostEqual(float(linkage["linkage_rate"]), 1.0)

    def test_31_independent_extraction_audit_pass(self):
        audit = read_json("independent_extraction_audit.json")
        self.assertEqual(audit["status"], "PASS")
        self.assertGreaterEqual(audit["checks_run"], 30)
        self.assertGreaterEqual(audit["districts_sampled"], 10)
        self.assertEqual(set(audit["variables_sampled"]), {"RAIN", "TMAX", "TMIN"})

    def test_32_event_diagnostics_present(self):
        for year in [2017, 2023]:
            event = pd.read_csv(QA / f"event_diagnostics_{year}.csv")
            self.assertEqual(len(event), 55)
            self.assertTrue(event["EVENT_DIAGNOSTIC_PASS"].all())

    def test_33_no_temporal_leakage(self):
        leakage = read_json("climate_temporal_leakage_audit.json")
        self.assertEqual(leakage["status"], "NONE")
        self.assertFalse(leakage["temporal_leakage"])

    def test_34_no_unauthorized_modelling(self):
        scope = read_json("scientific_scope_audit.json")
        self.assertEqual(scope["status"], "NO")
        self.assertFalse(scope["unauthorized_modelling"])

    def test_35_two_run_reproducibility_passes(self):
        repro = read_json("climate_reproducibility_report.json")
        self.assertTrue(repro["deterministic_outputs_identical"])

    def test_36_gate_report_passes(self):
        gate = read_json("climate_gate_report.json")
        self.assertEqual(gate["overall_gate"], "PASS")

    def test_37_q1_readiness_go_to_phenology(self):
        readiness = (QA / "Q1_climate_readiness.md").read_text(encoding="utf-8")
        self.assertIn("Final recommendation: GO_TO_PHENOLOGY_PHASE", readiness)


if __name__ == "__main__":
    unittest.main()
