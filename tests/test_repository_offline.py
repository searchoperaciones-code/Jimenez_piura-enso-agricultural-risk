from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
QA = ROOT / "outputs" / "qa"
CLIMATE_QA = QA / "climate"
PROCESSED = ROOT / "data" / "processed"
CLIMATE_PROCESSED = PROCESSED / "climate"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def local_report_path(path_text: str) -> Path:
    return ROOT / Path(path_text.replace("\\", "/"))


class RepositoryOfflineTests(unittest.TestCase):
    def test_dataset_master_gate_is_frozen_pass(self):
        report = read_json(QA / "execution_report.json")["supervision_report"]
        gate = read_json(QA / "gate_report.json")
        self.assertEqual(report["execution_status"], "PASS")
        self.assertEqual(report["gates"]["overall"], "PASS")
        self.assertEqual(report["dataset_version"], "DATASET_MASTER_v1")
        self.assertEqual(gate["dataset_version"], "DATASET_MASTER_v1")

    def test_dataset_processed_counts(self):
        panel = pd.read_csv(PROCESSED / "panel_master.csv")
        balanced = pd.read_csv(PROCESSED / "panel_balanceado.csv")
        balanced_districts = pd.read_csv(QA / "balanced_districts.csv")
        self.assertEqual(len(panel), 1701)
        self.assertEqual(len(balanced), 480)
        self.assertEqual(len(balanced_districts), 12)
        self.assertIn("YIELD_RAW", panel.columns)

    def test_yield_raw_unit_unresolved_is_documented(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("`YIELD_RAW` physical unit remains UNRESOLVED", readme)
        self.assertIn("Do not call `YIELD_RAW` t/ha", readme)

    def test_climate_master_gate_is_frozen_pass(self):
        execution = read_json(CLIMATE_QA / "climate_execution_report.json")["supervision_report"]
        gate = read_json(CLIMATE_QA / "climate_gate_report.json")
        self.assertEqual(execution["execution_status"], "PASS")
        self.assertEqual(gate["overall_gate"], "PASS")
        self.assertEqual(execution["selected_boundary_source"], "INEI_IDE_DISTRITO_2023")

    def test_climate_processed_counts(self):
        primary = pd.read_parquet(CLIMATE_PROCESSED / "climate_monthly_primary.parquet")
        main = pd.read_parquet(CLIMATE_PROCESSED / "climate_main_period_2016_2023.parquet")
        overlap = pd.read_parquet(CLIMATE_PROCESSED / "climate_overlap_2015_2024.parquet")
        normals = pd.read_parquet(CLIMATE_PROCESSED / "climate_normals_1991_2020.parquet")
        self.assertEqual(len(primary), 22440)
        self.assertEqual(len(main), 5280)
        self.assertEqual(len(overlap), 6215)
        self.assertEqual(len(normals), 660)

    def test_climate_linkage_independent_and_tests_preserved(self):
        linkage = pd.read_csv(CLIMATE_QA / "climate_panel_linkage_report.csv").iloc[0]
        independent = read_json(CLIMATE_QA / "independent_extraction_audit.json")
        tests = read_json(CLIMATE_QA / "automated_tests_report.json")
        self.assertEqual(int(linkage["agricultural_rows_total"]), 1701)
        self.assertEqual(int(linkage["agricultural_rows_complete_climate"]), 1701)
        self.assertEqual(float(linkage["linkage_rate"]), 1.0)
        self.assertEqual(independent["checks_run"], 36)
        self.assertEqual(independent["checks_passed"], 36)
        self.assertEqual(tests["tests_run"], 37)
        self.assertEqual(tests["tests_passed"], 37)

    def test_climate_manifest_counts_do_not_require_raw_files(self):
        manifest = pd.read_csv(CLIMATE_QA / "climate_data_manifest.csv")
        counts = manifest.groupby("VARIABLE").size().to_dict()
        self.assertEqual(counts.get("RAIN"), 528)
        self.assertEqual(counts.get("TMAX"), 408)
        self.assertEqual(counts.get("TMIN"), 408)
        self.assertTrue(manifest["SHA256"].astype(str).str.fullmatch(r"[0-9a-f]{64}").all())

    def test_deterministic_output_hashes_match_execution_report(self):
        execution = read_json(CLIMATE_QA / "climate_execution_report.json")["supervision_report"]
        run1_hashes = execution["reproducibility"]["run1_hashes"]
        self.assertGreaterEqual(len(run1_hashes), 8)
        for report_path, expected_hash in run1_hashes.items():
            path = local_report_path(report_path)
            self.assertTrue(path.exists(), report_path)
            self.assertEqual(sha256_file(path), expected_hash, report_path)

    def test_readiness_and_nonclaims_documented(self):
        readiness = (CLIMATE_QA / "Q1_climate_readiness.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("GO_TO_PHENOLOGY_PHASE", readiness)
        self.assertIn("does not yet", readme)
        self.assertIn("construct climate exposure variables", readme)
        self.assertIn("estimate climate-yield causal effects", readme)
        self.assertIn("PHENOLOGY MASTER v1 - Evidence/Architecture Freeze | PASS - FROZEN", readme)
        self.assertIn("PHENOLOGY MASTER v1 - Climate Exposure Build | READY", readme)

    def test_freeze_docs_and_root_requirements_exist(self):
        for path in [
            ROOT / "docs" / "REPRODUCIBILITY.md",
            ROOT / "docs" / "FREEZE_POLICY.md",
            ROOT / "docs" / "LICENSING_STATUS.md",
            ROOT / "docs" / "CITATION_PENDING.md",
            ROOT / "data" / "README.md",
            ROOT / "requirements-dataset.txt",
            ROOT / "requirements-climate.txt",
            ROOT / "requirements.txt",
        ]:
            self.assertTrue(path.exists(), str(path))


if __name__ == "__main__":
    unittest.main()
