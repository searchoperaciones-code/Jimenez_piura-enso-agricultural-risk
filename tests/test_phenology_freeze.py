from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
WINDOWS = ROOT / "data" / "processed" / "phenology" / "phenology_windows_frozen.csv"
GATE_REPORT = ROOT / "outputs" / "phenology" / "qa" / "phenology_freeze_gate_report.json"


def frozen_windows() -> pd.DataFrame:
    return pd.read_csv(WINDOWS, dtype={"COD_CULTIVO": "string"}, keep_default_na=False)


class PhenologyFreezeTests(unittest.TestCase):
    def test_01_exact_row_and_crop_counts(self):
        windows = frozen_windows()
        self.assertEqual(len(windows), 7)
        self.assertEqual(windows["COD_CULTIVO"].nunique(), 5)

    def test_02_exact_crop_codes(self):
        windows = frozen_windows()
        self.assertEqual(
            set(windows["COD_CULTIVO"].astype(str)),
            {"14010020000", "14010070000", "13010210000", "13010170102", "15010040000"},
        )

    def test_03_rice_transplant_proxy_and_das_window(self):
        windows = frozen_windows()
        rice = windows[windows["WINDOW_ID"] == "RICE_FLOWERING_95_110_DAS"].iloc[0]
        self.assertEqual(rice["COD_CULTIVO"], "14010020000")
        self.assertEqual(rice["ARCHITECTURE"], "SOWING_COHORT_WEIGHTED")
        self.assertEqual(rice["ANCHOR_VARIABLE"], "SIEMBRA")
        self.assertEqual(rice["ANCHOR_SEMANTICS"], "TRANSPLANT_ESTABLISHMENT_PROXY")
        self.assertEqual(int(rice["START_DAS"]), 95)
        self.assertEqual(int(rice["END_DAS"]), 110)
        self.assertEqual(int(rice["START_OFFSET_MONTH"]), 3)
        self.assertEqual(int(rice["END_OFFSET_MONTH"]), 4)
        self.assertIn("95-110 DAS is canonical", rice["NOTES"])

    def test_04_mad_mplus1_mplus3(self):
        windows = frozen_windows()
        mad = windows[windows["COD_CULTIVO"] == "14010070000"].iloc[0]
        self.assertEqual(mad["CROP_STD"], "MAIZ AMARILLO DURO")
        self.assertEqual(mad["ARCHITECTURE"], "SOWING_COHORT_WEIGHTED")
        self.assertEqual(mad["ANCHOR_VARIABLE"], "SIEMBRA")
        self.assertEqual(int(mad["START_OFFSET_MONTH"]), 1)
        self.assertEqual(int(mad["END_OFFSET_MONTH"]), 3)
        self.assertEqual(mad["COHORT_WEIGHTING"], "SIEMBRA_SHARE")

    def test_05_mango_may_june_current_year_only(self):
        windows = frozen_windows()
        mango_rows = windows[windows["COD_CULTIVO"] == "13010210000"]
        self.assertEqual(len(mango_rows), 1)
        mango = mango_rows.iloc[0]
        self.assertEqual(mango["ARCHITECTURE"], "SEASONAL_PERENNIAL")
        self.assertEqual(int(mango["CALENDAR_MONTH_START"]), 5)
        self.assertEqual(int(mango["CALENDAR_MONTH_END"]), 6)
        self.assertEqual(int(mango["YEAR_OFFSET"]), 0)
        self.assertEqual(mango["YEAR_RELATION"], "CURRENT_YEAR")

    def test_06_lemon_current_and_prior_year_windows(self):
        windows = frozen_windows()
        lemon = windows[windows["COD_CULTIVO"] == "13010170102"]
        self.assertEqual(len(lemon), 2)
        self.assertTrue((lemon["ARCHITECTURE"] == "RECURRENT_PERENNIAL_BROAD").all())
        self.assertEqual(set(lemon["WINDOW_ID"]), {"LEMON_FULL_YEAR_T", "LEMON_FULL_YEAR_T_MINUS_1"})
        self.assertEqual(set(lemon["YEAR_OFFSET"].astype(int)), {0, -1})
        self.assertTrue((lemon["CALENDAR_MONTH_START"].astype(int) == 1).all())
        self.assertTrue((lemon["CALENDAR_MONTH_END"].astype(int) == 12).all())

    def test_07_banana_current_and_prior_year_windows(self):
        windows = frozen_windows()
        banana = windows[windows["COD_CULTIVO"] == "15010040000"]
        self.assertEqual(len(banana), 2)
        self.assertTrue((banana["ARCHITECTURE"] == "MULTISTAGE_CONTINUOUS").all())
        self.assertEqual(set(banana["WINDOW_ID"]), {"BANANA_FULL_YEAR_T", "BANANA_FULL_YEAR_T_MINUS_1"})
        self.assertEqual(set(banana["YEAR_OFFSET"].astype(int)), {0, -1})
        self.assertTrue((banana["CALENDAR_MONTH_START"].astype(int) == 1).all())
        self.assertTrue((banana["CALENDAR_MONTH_END"].astype(int) == 12).all())

    def test_08_no_duplicate_window_id(self):
        windows = frozen_windows()
        self.assertFalse(windows["WINDOW_ID"].duplicated().any())

    def test_09_no_outcome_or_model_selection_tokens(self):
        text = WINDOWS.read_text(encoding="utf-8").upper()
        for token in ["YIELD_RAW", "PRECIO", "P_VALUE", "PVALUE", "P-VALUE", "REGRESSION"]:
            self.assertNotIn(token, text)

    def test_10_gate_report_uses_lf_only_with_one_final_newline(self):
        data = GATE_REPORT.read_bytes()
        self.assertNotIn(b"\r\n", data)
        self.assertNotIn(b"\r", data)
        self.assertTrue(data.endswith(b"\n"))
        self.assertFalse(data.endswith(b"\n\n"))


if __name__ == "__main__":
    unittest.main()
