from __future__ import annotations

import ast
import hashlib
import math
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_transient_campaign_exposures_strict as b3  # noqa: E402


OUTPUT = ROOT / "data" / "processed" / "phenology" / "transient_campaign_exposures_strict.parquet"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class TransientCampaignStrictTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not OUTPUT.exists():
            raise unittest.SkipTest("B3 strict campaign parquet has not been built")
        cls.table = pq.read_table(OUTPUT)
        cls.df = cls.table.to_pandas()
        cls.schema = pq.read_schema(OUTPUT).remove_metadata()
        cls.source = (ROOT / "scripts" / "build_transient_campaign_exposures_strict.py").read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.source)

    def test_01_frozen_hashes_unchanged(self):
        gate = b3.frozen_hash_gate()
        self.assertEqual(gate["status"], "PASS")
        for path, expected in b3.FROZEN_HASHES.items():
            self.assertEqual(sha256_file(path), expected)

    def test_02_schema_and_column_order_exact(self):
        self.assertEqual(self.df.columns.tolist(), b3.OUTPUT_COLUMNS)
        self.assertEqual(self.schema, b3.ARROW_SCHEMA)

    def test_03_campaign_universe_counts_and_ids(self):
        self.assertEqual(len(self.df), 745)
        self.assertEqual(self.df.groupby("COD_CULTIVO").size().to_dict(), b3.EXPECTED_PANEL_COUNTS)
        self.assertEqual(sorted(self.df["CAMPAIGN_ID"].unique().tolist()), [
            "2015/2016",
            "2016/2017",
            "2017/2018",
            "2018/2019",
            "2019/2020",
            "2020/2021",
            "2021/2022",
            "2022/2023",
        ])
        self.assertTrue((self.df["CAMPAIGN_ID"] == self.df["CAMPAIGN_START_YEAR"].astype(str) + "/" + self.df["CAMPAIGN_END_YEAR"].astype(str)).all())

    def test_04_keys_unique(self):
        panel = b3.read_panel_campaigns()
        transient = panel[panel["COD_CULTIVO"].isin(b3.TRANSIENT_CROPS)]
        self.assertEqual(transient.duplicated(["UBIGEO", "COD_CULTIVO", "ANO"]).sum(), 0)
        cohorts = b3.read_b1_cohorts()
        self.assertEqual(cohorts.duplicated(["UBIGEO", "COD_CULTIVO", "ANCHOR_YYYYMM", "WINDOW_ID"]).sum(), 0)
        self.assertEqual(self.df.duplicated(["UBIGEO", "COD_CULTIVO", "CAMPAIGN_ID", "WINDOW_ID"]).sum(), 0)

    def test_05_strict_domains_exact(self):
        self.assertEqual(
            b3.strict_domains("14010020000", 2016),
            {
                "U": [201605, 201606, 201607, 201608, 201609, 201610, 201611, 201612, 201701, 201702],
                "A": [201603, 201604, 201703, 201704],
            },
        )
        self.assertEqual(
            b3.strict_domains("14010070000", 2016),
            {
                "U": [201605, 201606, 201607, 201608, 201609, 201610, 201611, 201612, 201701],
                "A": [201602, 201603, 201604, 201702, 201703, 201704],
            },
        )

    def test_06_validity_counts_exact(self):
        self.assertEqual(int(self.df["CAMPAIGN_WEIGHTED_EXPOSURE_VALID"].sum()), 38)
        self.assertEqual(int((~self.df["CAMPAIGN_WEIGHTED_EXPOSURE_VALID"]).sum()), 707)
        valid_by_crop = self.df.groupby("COD_CULTIVO")["CAMPAIGN_WEIGHTED_EXPOSURE_VALID"].sum().to_dict()
        self.assertEqual(valid_by_crop, b3.EXPECTED_VALID_COUNTS)

    def test_07_invalid_campaign_climate_fields_null(self):
        invalid = self.df[~self.df["CAMPAIGN_WEIGHTED_EXPOSURE_VALID"]]
        self.assertEqual(int(invalid[b3.CLIMATE_VARIABLES].notna().sum().sum()), 0)

    def test_08_valid_campaign_climate_fields_finite(self):
        valid = self.df[self.df["CAMPAIGN_WEIGHTED_EXPOSURE_VALID"]]
        self.assertEqual(int(valid[b3.CLIMATE_VARIABLES].isna().sum().sum()), 0)
        for variable in b3.CLIMATE_VARIABLES:
            self.assertTrue(np.isfinite(valid[variable].to_numpy(dtype=float)).all())
        self.assertEqual(int((valid["RAIN_MM"] < 0).sum()), 0)
        self.assertEqual(int((valid["TMIN_C"] > valid["TMAX_C"]).sum()), 0)

    def test_09_no_silent_renormalization_and_weight_invariants(self):
        weighted = self.df[self.df["EXPECTED_WEIGHT"].notna()]
        self.assertTrue((weighted["EXPECTED_WEIGHT"] == 1.0).all())
        self.assertTrue(((weighted["SUPPORTED_WEIGHT"] >= -1e-12) & (weighted["SUPPORTED_WEIGHT"] <= 1 + 1e-12)).all())
        self.assertTrue(((weighted["MISSING_WEIGHT"] >= -1e-12) & (weighted["MISSING_WEIGHT"] <= 1 + 1e-12)).all())
        self.assertTrue((weighted["SUPPORTED_WEIGHT"].add(weighted["MISSING_WEIGHT"]).sub(1.0).abs() <= 1e-12).all())
        valid = self.df[self.df["CAMPAIGN_WEIGHTED_EXPOSURE_VALID"]]
        self.assertTrue((valid["COHORT_WEIGHT_SUM"].sub(1.0).abs() <= 1e-12).all())
        self.assertTrue((valid["SUPPORTED_WEIGHT"].sub(1.0).abs() <= 1e-12).all())
        self.assertTrue((valid["MISSING_WEIGHT"].abs() <= 1e-12).all())
        self.assertTrue((valid["UNAMBIGUOUS_COHORT_COUNT"] >= 1).all())
        self.assertTrue((valid["AMBIGUOUS_COHORT_COUNT"] == 0).all())

    def test_10_failure_reason_vocabulary_and_left_boundary(self):
        allowed_atoms = set(b3.FAILURE_ORDER + ["NONE"])
        for reason in self.df["FAILURE_REASON"].unique():
            for atom in reason.split("|"):
                self.assertIn(atom, allowed_atoms)
        left = self.df[self.df["CAMPAIGN_ID"] == "2015/2016"]
        self.assertGreater(len(left), 0)
        self.assertTrue(left["FAILURE_REASON"].str.contains("STRUCTURAL_LEFT_TRUNCATION", regex=False).all())

    def test_11_independent_valid_recomputation_cases(self):
        result = self._independent_cases()
        self.assertEqual(result["status"], "PASS", result)

    def test_12_static_outcome_firewall(self):
        read_csv_calls = [call for call in self._reader_calls("read_csv")]
        read_parquet_calls = [call for call in self._reader_calls("read_parquet")]
        self.assertEqual(len(read_csv_calls), 1)
        self.assertEqual(len(read_parquet_calls), 1)
        self.assertEqual(self._first_arg_name(read_csv_calls[0]), "PANEL")
        self.assertEqual(self._first_arg_name(read_parquet_calls[0]), "B1_COHORTS")
        self.assertEqual(self._literal_keyword(read_csv_calls[0], "usecols"), b3.PANEL_USECOLS)
        self.assertEqual(self._literal_keyword(read_parquet_calls[0], "columns"), b3.B1_COLUMNS)
        forbidden_source_reads = ["temporal_structure_monthly", "climate_anomalies", "panel_balanceado", "icen"]
        for call in read_csv_calls + read_parquet_calls:
            call_dump = ast.dump(call).lower()
            for token in forbidden_source_reads:
                self.assertNotIn(token, call_dump)
        forbidden_outcome_tokens = [
            "produccion",
            "cosecha",
            "harvest_area",
            "sown_area",
            "precio",
            "precio_chacra",
            "yield_raw",
            "yield_unit",
            "verde_actual",
            "area_ha",
            "regression",
            "optimization",
        ]
        for token in forbidden_outcome_tokens:
            self.assertNotIn(token, self.source.lower())

    def test_13_forbidden_unified_absent(self):
        self.assertEqual(b3.forbidden_artifact_check()["status"], "PASS")

    def test_14_report_is_lf_and_no_absolute_workspace_path(self):
        data = (ROOT / "outputs" / "climate_exposure" / "B3_TRANSIENT_CAMPAIGN_STRICT_REPORT.md").read_bytes()
        self.assertNotIn(b"\r", data)
        self.assertTrue(data.endswith(b"\n"))
        self.assertFalse(data.endswith(b"\n\n"))
        self.assertNotIn(str(ROOT).encode("utf-8"), data)

    def _independent_cases(self) -> dict[str, object]:
        cohorts = b3.read_b1_cohorts()
        index = {
            (str(row.UBIGEO), str(row.COD_CULTIVO), int(row.ANCHOR_YYYYMM), str(row.WINDOW_ID)): row._asdict()
            for row in cohorts.itertuples(index=False)
        }
        selected = pd.concat(
            [
                self.df[(self.df["COD_CULTIVO"] == "14010020000") & self.df["CAMPAIGN_WEIGHTED_EXPOSURE_VALID"]].head(1),
                self.df[(self.df["COD_CULTIVO"] == "14010020000") & self.df["CAMPAIGN_WEIGHTED_EXPOSURE_VALID"]].tail(1),
                self.df[(self.df["COD_CULTIVO"] == "14010070000") & self.df["CAMPAIGN_WEIGHTED_EXPOSURE_VALID"]].head(1),
                self.df[(self.df["COD_CULTIVO"] == "14010070000") & self.df["CAMPAIGN_WEIGHTED_EXPOSURE_VALID"]].tail(1),
            ]
        )
        results = []
        for _, row in selected.iterrows():
            domains = self._strict_domains(str(row["COD_CULTIVO"]), int(row["CAMPAIGN_START_YEAR"]))
            window_id = str(row["WINDOW_ID"])
            u = [index[(row["UBIGEO"], row["COD_CULTIVO"], month, window_id)] for month in domains["U"]]
            denominator = sum(float(item["SIEMBRA"]) for item in u)
            positive = [item for item in u if float(item["SIEMBRA"]) > 0]
            weights = [(float(item["SIEMBRA"]) / denominator, item) for item in positive]
            expected = {
                variable: sum(weight * float(item[variable]) for weight, item in weights)
                for variable in b3.CLIMATE_VARIABLES
            }
            ok = all(math.isclose(float(row[variable]), value, rel_tol=1e-12, abs_tol=1e-12) for variable, value in expected.items())
            results.append(ok)
        structural = [
            not self.df[self.df["FAILURE_REASON"].str.contains("AMBIGUOUS_COHORT_SIEMBRA_NONZERO", regex=False)].empty,
            not self.df[self.df["FAILURE_REASON"].str.contains("NO_POSITIVE_UNAMBIGUOUS_SIEMBRA", regex=False)].empty,
            not self.df[self.df["FAILURE_REASON"].str.contains("STRUCTURAL_LEFT_TRUNCATION", regex=False)].empty,
            not self.df[self.df["FAILURE_REASON"].str.contains("|", regex=False)].empty,
        ]
        return {"status": "PASS" if all(results) and all(structural) else "FAIL", "valid_cases": len(results)}

    def _strict_domains(self, crop_code: str, campaign_start_year: int) -> dict[str, list[int]]:
        if crop_code == "14010020000":
            return {
                "U": [campaign_start_year * 100 + month for month in range(5, 13)]
                + [(campaign_start_year + 1) * 100 + month for month in (1, 2)],
                "A": [campaign_start_year * 100 + month for month in (3, 4)]
                + [(campaign_start_year + 1) * 100 + month for month in (3, 4)],
            }
        return {
            "U": [campaign_start_year * 100 + month for month in range(5, 13)]
            + [(campaign_start_year + 1) * 100 + 1],
            "A": [campaign_start_year * 100 + month for month in (2, 3, 4)]
            + [(campaign_start_year + 1) * 100 + month for month in (2, 3, 4)],
        }

    def _reader_calls(self, name: str):
        for node in ast.walk(self.tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if isinstance(func, ast.Attribute) and func.attr == name:
                yield node

    def _first_arg_name(self, call: ast.Call) -> str:
        self.assertGreaterEqual(len(call.args), 1)
        self.assertIsInstance(call.args[0], ast.Name)
        return call.args[0].id

    def _literal_keyword(self, call: ast.Call, keyword_name: str) -> list[str]:
        for keyword in call.keywords:
            if keyword.arg == keyword_name:
                if isinstance(keyword.value, ast.Name):
                    return list(getattr(b3, keyword.value.id))
                return list(ast.literal_eval(keyword.value))
        return []


if __name__ == "__main__":
    unittest.main()
