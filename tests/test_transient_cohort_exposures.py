from __future__ import annotations

import ast
import hashlib
import math
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_transient_cohort_exposures as b1  # noqa: E402


OUTPUT = ROOT / "data" / "processed" / "phenology" / "transient_cohort_exposures.parquet"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class TransientCohortExposureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not OUTPUT.exists():
            raise unittest.SkipTest("B1 transient cohort parquet has not been built")
        cls.table = pq.read_table(OUTPUT)
        cls.df = cls.table.to_pandas()
        cls.schema = pq.read_schema(OUTPUT).remove_metadata()
        cls.source = (ROOT / "scripts" / "build_transient_cohort_exposures.py").read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.source)

    def test_01_upstream_and_b0_hashes_unchanged(self):
        gate = b1.hash_gate()
        self.assertEqual(gate["status"], "PASS")
        for path, expected in b1.EXPECTED_HASHES.items():
            self.assertEqual(sha256_file(path), expected)

    def test_02_output_schema_and_column_order_exact(self):
        self.assertEqual(self.df.columns.tolist(), b1.OUTPUT_COLUMNS)
        self.assertEqual(self.schema, b1.ARROW_SCHEMA)

    def test_03_row_counts_and_crop_counts_exact(self):
        self.assertEqual(len(self.df), 8977)
        self.assertEqual(self.df.groupby("COD_CULTIVO").size().to_dict(), b1.EXPECTED_ROW_COUNTS)

    def test_04_source_and_output_keys_unique(self):
        source = b1.read_temporal_source()
        transient = source[source["COD_CULTIVO"].isin(b1.TRANSIENT_WINDOWS)]
        self.assertEqual(transient.duplicated(["UBIGEO", "COD_CULTIVO", "MES"]).sum(), 0)
        self.assertEqual(self.df.duplicated(["UBIGEO", "COD_CULTIVO", "ANCHOR_YYYYMM", "WINDOW_ID"]).sum(), 0)

    def test_05_identifier_and_mes_integrity(self):
        self.assertTrue(self.df["UBIGEO"].str.fullmatch(r"\d{6}").all())
        self.assertTrue(self.df["COD_CULTIVO"].str.fullmatch(r"\d{11}").all())
        self.assertTrue(self.df["ANCHOR_MONTH"].between(1, 12).all())
        expected_yyyymm = self.df["ANCHOR_YEAR"].astype(int) * 100 + self.df["ANCHOR_MONTH"].astype(int)
        self.assertTrue((self.df["ANCHOR_YYYYMM"].astype(int) == expected_yyyymm).all())

    def test_06_climate_completeness_counts(self):
        self.assertEqual(int(self.df["CLIMATE_WINDOW_COMPLETE"].sum()), 8724)
        self.assertEqual(int((~self.df["CLIMATE_WINDOW_COMPLETE"]).sum()), 253)
        self.assertEqual(int((self.df["FAILURE_REASON"] == "CLIMATE_WINDOW_RIGHT_TRUNCATED").sum()), 253)
        self.assertEqual(int(self.df["FAILURE_REASON"].str.contains("CLIMATE_WINDOW_INTERNAL_GAP", regex=False).sum()), 0)

    def test_07_incomplete_rows_have_null_climate_and_remain_retained(self):
        incomplete = self.df[~self.df["CLIMATE_WINDOW_COMPLETE"]]
        self.assertEqual(len(incomplete), 253)
        self.assertEqual(int(incomplete[b1.CLIMATE_VARIABLES].notna().sum().sum()), 0)
        self.assertFalse(incomplete["COHORT_EXPOSURE_VALID"].any())

    def test_08_complete_rows_have_finite_climate_values(self):
        complete = self.df[self.df["CLIMATE_WINDOW_COMPLETE"]]
        self.assertEqual(int(complete[b1.CLIMATE_VARIABLES].isna().sum().sum()), 0)
        for variable in b1.CLIMATE_VARIABLES:
            self.assertTrue(np.isfinite(complete[variable].to_numpy(dtype=float)).all())
        self.assertTrue(complete["COHORT_EXPOSURE_VALID"].all())

    def test_09_aggregation_domain_invariants(self):
        complete = self.df[self.df["CLIMATE_WINDOW_COMPLETE"]]
        self.assertEqual(int((complete["RAIN_MM"] < 0).sum()), 0)
        self.assertEqual(int((complete["TMIN_C"] > complete["TMAX_C"]).sum()), 0)

    def test_10_siembras_preserved_and_zero_not_missing(self):
        source = b1.read_temporal_source()
        transient = source[source["COD_CULTIVO"].isin(b1.TRANSIENT_WINDOWS)].copy()
        merged = self.df.merge(
            transient[["UBIGEO", "COD_CULTIVO", "MES", "SIEMBRA"]],
            left_on=["UBIGEO", "COD_CULTIVO", "ANCHOR_YYYYMM"],
            right_on=["UBIGEO", "COD_CULTIVO", "MES"],
            how="inner",
            suffixes=("_out", "_src"),
        )
        self.assertEqual(len(merged), len(self.df))
        self.assertTrue(merged["SIEMBRA_out"].fillna(-999999).equals(merged["SIEMBRA_src"].fillna(-999999)))
        zero = self.df[self.df["SIEMBRA"] == 0]
        self.assertGreater(len(zero), 0)
        self.assertTrue(zero["SIEMBRA_OBSERVED"].all())
        self.assertTrue(zero[zero["CLIMATE_WINDOW_COMPLETE"]]["COHORT_EXPOSURE_VALID"].all())

    def test_11_allowed_vocabularies_exact(self):
        self.assertEqual(set(self.df["COD_CULTIVO"]), set(b1.TRANSIENT_WINDOWS))
        self.assertEqual(set(self.df["WINDOW_ID"]), {"RICE_FLOWERING_95_110_DAS", "MAD_MPLUS1_MPLUS3"})
        self.assertEqual(set(self.df["ARCHITECTURE"]), {"SOWING_COHORT_WEIGHTED"})
        self.assertEqual(set(self.df["FAILURE_REASON"]), {"NONE", "CLIMATE_WINDOW_RIGHT_TRUNCATED"})
        self.assertEqual(
            set(self.df["CAMPAIGN_ATTRIBUTION_STATUS"]),
            {"UNAMBIGUOUS_AGRONOMIC_CAMPAIGN", "AMBIGUOUS_CROSS_CAMPAIGN"},
        )

    def test_12_expected_month_representation_contract(self):
        self.assertEqual(b1.format_months([202402, 202401, 202403]), "202401|202402|202403")
        self.assertEqual(b1.format_months([]), "")
        for value in self.df["EXPECTED_CLIMATE_MONTHS"].head(100):
            self.assertNotIn(" ", value)
            self.assertNotIn("[", value)
            self.assertNotRegex(value, r"\|$")

    def test_13_campaign_mapping_emerges(self):
        rice = self.df[self.df["COD_CULTIVO"] == "14010020000"]
        mad = self.df[self.df["COD_CULTIVO"] == "14010070000"]
        self.assertEqual(set(rice[rice["ANCHOR_MONTH"].isin([1, 2])]["CAMPAIGN_ATTRIBUTION_STATUS"]), {"UNAMBIGUOUS_AGRONOMIC_CAMPAIGN"})
        self.assertEqual(set(rice[rice["ANCHOR_MONTH"].isin([3, 4])]["CAMPAIGN_ATTRIBUTION_STATUS"]), {"AMBIGUOUS_CROSS_CAMPAIGN"})
        self.assertEqual(set(rice[rice["ANCHOR_MONTH"].isin(range(5, 13))]["CAMPAIGN_ATTRIBUTION_STATUS"]), {"UNAMBIGUOUS_AGRONOMIC_CAMPAIGN"})
        self.assertEqual(set(mad[mad["ANCHOR_MONTH"] == 1]["CAMPAIGN_ATTRIBUTION_STATUS"]), {"UNAMBIGUOUS_AGRONOMIC_CAMPAIGN"})
        self.assertEqual(set(mad[mad["ANCHOR_MONTH"].isin([2, 3, 4])]["CAMPAIGN_ATTRIBUTION_STATUS"]), {"AMBIGUOUS_CROSS_CAMPAIGN"})
        self.assertEqual(set(mad[mad["ANCHOR_MONTH"].isin(range(5, 13))]["CAMPAIGN_ATTRIBUTION_STATUS"]), {"UNAMBIGUOUS_AGRONOMIC_CAMPAIGN"})

    def test_14_independent_numerical_recomputation_cases(self):
        climate = b1.read_climate_source()
        result = b1.independent_recomputation_cases(self.df, climate)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(len(result["cases"]), 7)

    def test_15_static_outcome_firewall(self):
        for call in self._reader_calls():
            call_text = ast.unparse(call)
            self.assertNotIn("panel_master", call_text)
            self.assertNotIn("panel_balanceado", call_text)
        temporal_calls = [call for call in self._reader_calls() if "TEMPORAL" in ast.unparse(call)]
        self.assertEqual(len(temporal_calls), 1)
        self.assertEqual(self._literal_usecols(temporal_calls[0]), b1.TEMPORAL_USECOLS)
        climate_calls = [call for call in self._reader_calls() if "CLIMATE" in ast.unparse(call)]
        self.assertEqual(len(climate_calls), 1)
        self.assertEqual(self._literal_columns(climate_calls[0]), b1.CLIMATE_USECOLS)

    def test_16_forbidden_artifacts_absent(self):
        self.assertEqual(b1.forbidden_artifact_check()["status"], "PASS")

    def test_17_report_exists_and_is_lf_utf8(self):
        report = ROOT / "outputs" / "climate_exposure" / "B1_TRANSIENT_COHORT_LEDGER_REPORT.md"
        data = report.read_bytes()
        self.assertNotIn(b"\r", data)
        self.assertTrue(data.endswith(b"\n"))
        self.assertFalse(data.endswith(b"\n\n"))

    def _reader_calls(self):
        for node in ast.walk(self.tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if isinstance(func, ast.Attribute) and func.attr in {"read_csv", "read_parquet"}:
                yield node

    def _literal_usecols(self, call: ast.Call) -> list[str]:
        for keyword in call.keywords:
            if keyword.arg == "usecols":
                if isinstance(keyword.value, ast.Name):
                    return list(getattr(b1, keyword.value.id))
                return list(ast.literal_eval(keyword.value))
        return []

    def _literal_columns(self, call: ast.Call) -> list[str]:
        for keyword in call.keywords:
            if keyword.arg == "columns":
                if isinstance(keyword.value, ast.Name):
                    return list(getattr(b1, keyword.value.id))
                return list(ast.literal_eval(keyword.value))
        return []


if __name__ == "__main__":
    unittest.main()
