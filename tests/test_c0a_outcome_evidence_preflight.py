from __future__ import annotations

import ast
import csv
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import c0a_outcome_evidence_preflight as c0a  # noqa: E402


class C0AOutcomeEvidencePreflightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = c0a.evaluate()
        cls.registry_rows = cls.report["rows"]
        cls.report_text = c0a.REPORT.read_text(encoding="utf-8")
        cls.script_source = (ROOT / "scripts" / "c0a_outcome_evidence_preflight.py").read_text(encoding="utf-8")

    def test_01_required_frozen_base(self):
        gate = self.report["gates"]["branch"]
        self.assertEqual(gate["status"], "PASS")
        self.assertEqual(gate["branch"], c0a.EXPECTED_BRANCH)
        self.assertTrue(gate["base_is_ancestor"])
        self.assertTrue(gate["stage_b_tag_at_head"])

    def test_02_exact_four_file_c0a_persistent_scope(self):
        gate = self.report["gates"]["persistent_scope"]
        self.assertEqual(gate["status"], "PASS")
        self.assertEqual(
            gate["actual"],
            sorted(f"?? {c0a.rel(path)}" for path in c0a.C0A_FILES),
        )

    def test_03_existing_upstream_files_unchanged(self):
        gate = self.report["gates"]["upstream"]
        self.assertEqual(gate["status"], "PASS")
        self.assertEqual(gate["hash_mismatches"], [])

    def test_04_registry_exact_schema(self):
        with c0a.REGISTRY.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            self.assertEqual(reader.fieldnames, c0a.REGISTRY_COLUMNS)

    def test_05_deterministic_evidence_ids_and_sort(self):
        expected_ids = [f"C0A-E{i:03d}" for i in range(1, len(self.registry_rows) + 1)]
        self.assertEqual([row["EVIDENCE_ID"] for row in self.registry_rows], expected_ids)
        sorted_rows = sorted(
            self.registry_rows,
            key=lambda row: (row["VARIABLE"], row["CLAIM_CATEGORY"], row["SOURCE_TIER"], row["SOURCE_TITLE"], row["CLAIM"]),
        )
        self.assertEqual(self.registry_rows, sorted_rows)

    def test_06_allowed_decision_statuses_only(self):
        self.assertTrue(all(row["DECISION_STATUS"] in c0a.ALLOWED_STATUSES for row in self.registry_rows))

    def test_07_allowed_source_tiers_only(self):
        self.assertTrue(all(row["SOURCE_TIER"] in c0a.ALLOWED_TIERS for row in self.registry_rows))

    def test_08_no_processed_outcome_dataset_exists(self):
        self.assertFalse((ROOT / "data" / "processed" / "outcome").exists())

    def test_09_no_phenology_exposures_long_exists(self):
        self.assertFalse((ROOT / "data" / "processed" / "phenology" / "phenology_exposures_long.parquet").exists())

    def test_10_no_regression_model_or_optimization_artifact_exists(self):
        gate = self.report["gates"]["outcome_firewall"]
        self.assertEqual(gate["status"], "PASS")
        self.assertEqual(gate["artifact_hits"], [])

    def test_11_no_modification_of_stage_b_products(self):
        paths = [
            "data/processed/phenology/transient_cohort_exposures.parquet",
            "data/processed/phenology/perennial_exposures_long.parquet",
            "data/processed/phenology/transient_campaign_exposures_strict.parquet",
            "config/climate_exposure/climate_exposure_spec_v1.json",
        ]
        result = subprocess.run(["git", "diff", "--quiet", "--", *paths], cwd=ROOT, check=False)
        self.assertEqual(result.returncode, 0)

    def test_12_report_includes_all_seven_source_variables(self):
        for variable in ["PRODUCCION", "COSECHA", "SIEMBRA", "VERDE_ACTUAL", "PRECIO_CHACRA", "ANO", "MES"]:
            self.assertIn(variable, self.report_text)

    def test_13_report_states_yield_raw_unit_adjudication(self):
        self.assertIn("YIELD_UNIT_DECISION=TM_PER_HA", self.report_text)
        self.assertIn("does not modify frozen upstream YIELD_UNIT", self.report_text)

    def test_14_report_blocks_monetary_gvp_construction(self):
        self.assertIn("GVP construction is blocked", self.report_text)
        self.assertIn("DIMENSIONALLY_AUTHORIZED_NOT_BUILT", self.report_text)

    def test_15_no_blanket_claim_of_causal_interpretation(self):
        lowered = self.report_text.lower()
        self.assertIn("causal interpretation is not authorized", lowered)
        self.assertNotIn("causal effect is certified", lowered)

    def test_16_static_modelling_firewall(self):
        gate = self.report["gates"]["static_modelling"]
        self.assertEqual(gate["status"], "PASS")

    def test_17_script_does_not_import_modelling_libraries(self):
        tree = ast.parse(self.script_source)
        imported = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.extend(alias.name.split(".")[0] for alias in node.names)
            if isinstance(node, ast.ImportFrom) and node.module:
                imported.append(node.module.split(".")[0])
        self.assertTrue(c0a.MODELLING_IMPORT_PREFIXES.isdisjoint(imported))

    def test_18_institutional_convergence_requires_two_tier2_same_authority_sources(self):
        gate = self.report["gates"]["institutional_convergence"]
        self.assertEqual(gate["status"], "PASS")
        self.assertGreaterEqual(gate["same_authority_tier2_count"], 2)

    def test_19_no_tier4_source_can_certify_produccion_unit(self):
        gate = self.report["gates"]["institutional_convergence"]
        self.assertEqual(gate["tier4_certifiers"], [])

    def test_20_exact_dataset_publisher_author_linkage_recorded(self):
        self.assertTrue(self.report["gates"]["institutional_convergence"]["exact_dataset_linkage"])
        self.assertIn("Oficina de Estadistica - Direccion Regional de Agricultura", self.report_text)

    def test_21_numerical_concordance_never_mixes_calendar_and_campaign_periods(self):
        gate = self.report["gates"]["numerical_concordance"]
        self.assertEqual(gate["status"], "PASS")
        self.assertTrue(gate["no_calendar_campaign_mix"])
        self.assertEqual(gate["status_value"], "NO_EXACT_NUMERICAL_CONCORDANCE_AVAILABLE")

    def test_22_export_volume_cannot_be_used_as_production_concordance(self):
        self.assertTrue(self.report["gates"]["numerical_concordance"]["export_volume_not_used"])
        self.assertIn("Export volume cannot be used as agricultural production-volume concordance", self.report_text)

    def test_23_metric_tonne_and_hectare_imply_yield_tm_per_ha(self):
        produccion = c0a.decision_lookup(self.registry_rows, "PRODUCCION", "UNIT", "Final adjudication")
        cosecha = c0a.decision_lookup(self.registry_rows, "COSECHA", "UNIT")
        yield_unit = c0a.decision_lookup(self.registry_rows, "YIELD_RAW", "UNIT")
        if produccion["DECISION_VALUE"] == "METRIC_TONNE" and cosecha["DECISION_VALUE"] == "ha":
            self.assertEqual(yield_unit["DECISION_VALUE"], "TM_PER_HA")

    def test_24_if_produccion_unresolved_yield_would_remain_unresolved(self):
        produccion = c0a.decision_lookup(self.registry_rows, "PRODUCCION", "UNIT", "Final adjudication")
        yield_unit = c0a.decision_lookup(self.registry_rows, "YIELD_RAW", "UNIT")
        if produccion["DECISION_STATUS"] == "UNRESOLVED":
            self.assertEqual(yield_unit["DECISION_VALUE"], "UNRESOLVED")
        else:
            self.assertNotEqual(produccion["DECISION_STATUS"], "UNRESOLVED")

    def test_25_gvp_remains_not_built_in_every_case(self):
        self.assertFalse((ROOT / "data" / "processed" / "outcome").exists())
        self.assertIn("GVP_NOT_BUILT", "\n".join(c0a.terminal_summary(self.report)))

    def test_26_all_frozen_upstream_hashes_remain_unchanged(self):
        gate = self.report["gates"]["upstream"]
        self.assertEqual(gate["status"], "PASS")
        self.assertEqual(gate["hash_mismatches"], [])

    def test_27_git_status_contains_exactly_four_allowed_c0a_files(self):
        gate = self.report["gates"]["persistent_scope"]
        self.assertEqual(gate["status"], "PASS")
        self.assertEqual(len(gate["actual"]), 4)

    def test_28_rice_2025_published_yield_caveat_documented(self):
        self.assertIn("Rice 2025 published-yield aggregation caveat", self.report_text)
        self.assertIn("516469 / 51711", self.report_text)
        self.assertIn("9,987.604 kg/ha", self.report_text)
        self.assertIn("not numerically equal to the simple quotient", self.report_text)
        self.assertIn("must not be interpreted as a contradiction of the physical unit of PRODUCCION", self.report_text)
        self.assertIn("must not be treated as numerical validation", self.report_text)
        self.assertIn("YIELD_RAW = SUM(PRODUCCION) / SUM(COSECHA)", self.report_text)
        self.assertIn("EXACT_NUMERICAL_CONCORDANCE = NO_EXACT_NUMERICAL_CONCORDANCE_AVAILABLE", self.report_text)
        self.assertIn("lemon and mango 2025 arithmetic comparisons are external dimensional-consistency checks only", self.report_text)
        self.assertIn("No inference about the official yield-aggregation procedure is invented", self.report_text)


if __name__ == "__main__":
    unittest.main()
