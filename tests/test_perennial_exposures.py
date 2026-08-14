from __future__ import annotations

import ast
import hashlib
import math
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_perennial_exposures as b2  # noqa: E402


OUTPUT = ROOT / "data" / "processed" / "phenology" / "perennial_exposures_long.parquet"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class PerennialExposureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not OUTPUT.exists():
            raise unittest.SkipTest("B2 perennial parquet has not been built")
        cls.table = pq.read_table(OUTPUT)
        cls.df = cls.table.to_pandas()
        cls.schema = pq.read_schema(OUTPUT).remove_metadata()
        cls.source = (ROOT / "scripts" / "build_perennial_exposures.py").read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.source)

    def test_01_frozen_hashes_unchanged(self):
        gate = b2.frozen_hash_gate()
        self.assertEqual(gate["status"], "PASS")
        for path, expected in b2.FROZEN_HASHES.items():
            self.assertEqual(sha256_file(path), expected)

    def test_02_schema_and_column_order_exact(self):
        self.assertEqual(self.df.columns.tolist(), b2.OUTPUT_COLUMNS)
        self.assertEqual(self.schema, b2.ARROW_SCHEMA)

    def test_03_panel_universe_and_output_counts(self):
        panel = b2.validate_panel(b2.read_panel_keys())
        self.assertEqual(panel["status"], "PASS")
        self.assertEqual(panel["panel_perennial_keys"], 956)
        self.assertEqual(panel["by_crop"], b2.EXPECTED_PANEL_COUNTS)
        self.assertEqual(len(self.df), 1657)
        self.assertEqual(self.df.groupby("COD_CULTIVO").size().to_dict(), b2.EXPECTED_OUTPUT_COUNTS)

    def test_04_window_expansion_counts(self):
        counts = {
            "|".join(str(part) for part in key): int(value)
            for key, value in self.df.groupby(["COD_CULTIVO", "WINDOW_ID"]).size().items()
        }
        self.assertEqual(counts, b2.EXPECTED_WINDOW_COUNTS)

    def test_05_identifier_and_key_integrity(self):
        self.assertTrue(self.df["UBIGEO"].str.fullmatch(r"\d{6}").all())
        self.assertTrue(self.df["COD_CULTIVO"].str.fullmatch(r"\d{11}").all())
        self.assertEqual(self.df.duplicated(["UBIGEO", "COD_CULTIVO", "REFERENCE_CALENDAR_YEAR", "WINDOW_ID"]).sum(), 0)

    def test_06_reference_period_contract(self):
        self.assertEqual(set(self.df["TIME_BASIS"]), {"CALENDAR_YEAR"})
        self.assertTrue((self.df["REFERENCE_PERIOD_ID"] == self.df["REFERENCE_CALENDAR_YEAR"].astype(str)).all())
        self.assertTrue(self.df["REFERENCE_PERIOD_ID"].str.fullmatch(r"\d{4}").all())

    def test_07_climate_completeness_and_failure_reason(self):
        self.assertTrue(self.df["EXPOSURE_VALID"].all())
        self.assertEqual(set(self.df["FAILURE_REASON"]), {"NONE"})
        self.assertEqual(int(self.df[b2.CLIMATE_VARIABLES].isna().sum().sum()), 0)
        for variable in b2.CLIMATE_VARIABLES:
            self.assertTrue(np.isfinite(self.df[variable].to_numpy(dtype=float)).all())

    def test_08_climate_aggregation_sanity(self):
        self.assertEqual(int((self.df["RAIN_MM"] < 0).sum()), 0)
        self.assertEqual(int((self.df["TMIN_C"] > self.df["TMAX_C"]).sum()), 0)

    def test_09_independent_numerical_recomputation(self):
        result = b2.independent_recomputation_cases(self.df, b2.read_climate())
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(len(result["cases"]), 8)

    def test_10_reproducibility_contract(self):
        check = b2.reproducibility_check(self.df)
        self.assertEqual(check["status"], "PASS")
        self.assertEqual(check["run1_sha256"], check["run2_sha256"])
        self.assertEqual(check["run1_sha256"], sha256_file(OUTPUT))

    def test_11_static_outcome_firewall(self):
        read_csv_calls = [call for call in self._reader_calls("read_csv")]
        read_parquet_calls = [call for call in self._reader_calls("read_parquet")]
        self.assertEqual(len(read_csv_calls), 1)
        self.assertEqual(len(read_parquet_calls), 1)
        self.assertIn("PANEL", ast.unparse(read_csv_calls[0].args[0]))
        self.assertIn("CLIMATE", ast.unparse(read_parquet_calls[0].args[0]))
        self.assertEqual(self._literal_keyword(read_csv_calls[0], "usecols"), b2.PANEL_USECOLS)
        self.assertEqual(self._literal_keyword(read_parquet_calls[0], "columns"), b2.CLIMATE_COLUMNS)
        forbidden = ["panel_balanceado", "temporal_structure_monthly", "icen_clean", "COSECHA", "PRODUCCION", "YIELD_RAW", "PRECIO"]
        for token in forbidden:
            self.assertNotIn(token, self.source)

    def test_12_forbidden_artifacts_absent(self):
        self.assertEqual(b2.forbidden_artifact_check()["status"], "PASS")

    def test_13_report_is_utf8_lf_deterministic_shape(self):
        report = ROOT / "outputs" / "climate_exposure" / "B2_PERENNIAL_EXPOSURE_LEDGER_REPORT.md"
        data = report.read_bytes()
        self.assertNotIn(b"\r", data)
        self.assertTrue(data.endswith(b"\n"))
        self.assertFalse(data.endswith(b"\n\n"))
        self.assertNotIn(str(ROOT).encode("utf-8"), data)

    def _reader_calls(self, name: str):
        for node in ast.walk(self.tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if isinstance(func, ast.Attribute) and func.attr == name:
                yield node

    def _literal_keyword(self, call: ast.Call, keyword_name: str) -> list[str]:
        for keyword in call.keywords:
            if keyword.arg == keyword_name:
                if isinstance(keyword.value, ast.Name):
                    return list(getattr(b2, keyword.value.id))
                return list(ast.literal_eval(keyword.value))
        return []


if __name__ == "__main__":
    unittest.main()
