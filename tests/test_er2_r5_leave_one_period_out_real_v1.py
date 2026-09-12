from __future__ import annotations

import ast
import csv
import io
import json
import statistics
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import er2_r5_leave_one_period_out_real_v1 as r5


class PreResultContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = r5.plan_record()

    def fixture(self):
        frame, columns, y = r5.r5p.synthetic_fixture()
        frame["YIELD"] = y
        period = "SYNTHETIC_PERIOD"
        frame = frame.sort_values(["UBIGEO", period], kind="mergesort").reset_index(drop=True)
        sample = {"frame": frame, "columns": columns, "period": period,
                  "keys": frame[["UBIGEO", period]].astype(str).values.tolist()}
        omission = {"REFIT_ORDER": "1", "CROP": "SYNTHETIC", "CROP_CODE": "SYNTHETIC",
                    "MODEL_ID": "SYNTHETIC", "PERIOD_ID_COLUMN": period, "OMITTED_PERIOD_ID": "P01",
                    "MANDATORY_NAMED_CASE": "NONE", "RETAINED_PERIODS": "4"}
        return sample, omission

    def test_exact_parent_and_tag(self):
        r5.verify_parent(remote=False)

    def test_raw_predecessor_hashes(self):
        self.assertEqual(self.plan["r5p_preflight_lock_sha256"], r5.PREFLIGHT_SHA)
        for path, digest in r5.R5P_HASHES.items():
            self.assertEqual(r5.sha(r5.blob(path)), digest)

    def test_exact_contract(self):
        self.assertEqual(r5.sha(r5.json_bytes(self.plan["r5_tier_contract"])), r5.r5p.R5_TIER_CONTRACT_SHA)
        self.assertEqual(self.plan["r5_tier_contract"]["family"], "PHYSICAL_ANOMALY")

    def test_temporal_lock(self):
        self.assertFalse(self.plan["temporal_governance"]["REAL_R5_RESULTS_KNOWN_BEFORE_EXECUTION"])
        self.assertEqual(self.plan["temporal_governance"]["REAL_R5_REFITS_AT_LOCK"], 0)
        self.assertTrue(self.plan["temporal_governance"]["R5P_FROZEN_BEFORE_REAL_R5"])

    def test_exact_omission_plan(self):
        self.assertEqual(self.plan["omissions"], r5.frozen_csv(r5.r5p.OMISSION_PLAN))
        self.assertEqual(len(self.plan["omissions"]), 38)

    def test_exact_mapping(self):
        self.assertEqual(self.plan["coefficient_omission_map"], r5.frozen_csv(r5.r5p.COEFFICIENT_MAP))
        self.assertEqual(len(self.plan["coefficient_omission_map"]), 162)

    def test_21_targets(self):
        self.assertEqual(len({(r["CROP_CODE"], r["VARIABLE"]) for r in self.plan["summary_targets"]}), 21)

    def test_period_inventory(self):
        for c in r5.r5p.CROP_ORDER:
            self.assertEqual(tuple(r["OMITTED_PERIOD_ID"] for r in self.plan["omissions"] if r["CROP_CODE"] == c), r5.r5p.EXPECTED_PERIODS[c])

    def test_nine_candidate_paths(self):
        self.assertEqual(len(set(self.plan["artifact_names"])), 9)

    def test_frozen_schemas(self):
        lock = r5.frozen_json(r5.r5p.PREFLIGHT_LOCK)
        self.assertEqual(list(r5.DETAIL_FIELDS), lock["future_real_r5_detail_schema"])
        self.assertEqual(list(r5.SUMMARY_FIELDS), lock["future_real_r5_summary_schema"])

    def test_estimator_identity(self):
        identity = r5.estimator_identity()
        self.assertEqual(identity["source_sha256"], r5.r5p.FIT_SOURCE_SHA)
        self.assertEqual(identity["body_sha256"], r5.r5p.FIT_BODY_SHA)

    def test_plan_contains_code_identity(self):
        self.assertEqual(self.plan["executor_sha256"], r5.sha((ROOT / r5.SCRIPT).read_bytes()))
        self.assertEqual(self.plan["tests_sha256"], r5.sha((ROOT / r5.TEST).read_bytes()))

    def test_modified_plan_fails_closed(self):
        mutated = dict(self.plan, row_order="REVERSED")
        with self.assertRaisesRegex(RuntimeError, "HOLD_POST_RESULT_CODE_CHANGE"):
            r5.verify_plan(r5.json_bytes(mutated))

    def test_exact_difference_and_order(self):
        sample, omission = self.fixture()
        kept = r5.exact_retained(sample["frame"].iloc[::-1], sample["period"], omission["OMITTED_PERIOD_ID"], sample["keys"])
        self.assertEqual(kept[["UBIGEO", sample["period"]]].values.tolist(), [k for k in sample["keys"] if k[1] != "P01"])

    def test_extra_row_removal_fails_closed(self):
        sample, omission = self.fixture()
        sample["frame"] = sample["frame"].iloc[1:]
        with self.assertRaisesRegex(RuntimeError, "HOLD_INVALID_LOO_REFIT"):
            r5.refit(sample, omission)

    def test_two_period_removal_fails_closed(self):
        sample, omission = self.fixture()
        omission["OMITTED_PERIOD_ID"] = ["P01", "P02"]
        with self.assertRaisesRegex(RuntimeError, "HOLD_INVALID_LOO_REFIT"):
            r5.refit(sample, omission)

    def test_absent_period_fails_closed(self):
        sample, omission = self.fixture()
        omission["OMITTED_PERIOD_ID"] = "P99"
        with self.assertRaisesRegex(RuntimeError, "HOLD_INVALID_LOO_REFIT"):
            r5.refit(sample, omission)

    def test_missing_key_fails_closed(self):
        sample, omission = self.fixture()
        sample["frame"].loc[0, sample["period"]] = None
        with self.assertRaisesRegex(RuntimeError, "HOLD_INVALID_LOO_REFIT"):
            r5.refit(sample, omission)

    def test_duplicate_key_fails_closed(self):
        sample, omission = self.fixture()
        sample["frame"] = pd.concat([sample["frame"], sample["frame"].iloc[:1]])
        with self.assertRaisesRegex(RuntimeError, "HOLD_INVALID_LOO_REFIT"):
            r5.refit(sample, omission)

    def test_empty_retained_fails_closed(self):
        sample, omission = self.fixture()
        sample["frame"] = sample["frame"][sample["frame"][sample["period"]] == "P01"]
        sample["keys"] = sample["frame"][["UBIGEO", sample["period"]]].values.tolist()
        with self.assertRaisesRegex(RuntimeError, "HOLD_INVALID_LOO_REFIT"):
            r5.refit(sample, omission)

    def test_mechanical_district_disappearance_is_allowed(self):
        sample, _ = self.fixture()
        frame = sample["frame"]
        frame = frame[(frame.UBIGEO != "D06") | (frame[sample["period"]] == "P01")].copy()
        keys = frame[["UBIGEO", sample["period"]]].values.tolist()
        kept = r5.exact_retained(frame, sample["period"], "P01", keys)
        self.assertEqual(kept.UBIGEO.nunique(), frame.UBIGEO.nunique() - 1)
        self.assertEqual(kept[["UBIGEO", sample["period"]]].values.tolist(), [k for k in keys if k[1] != "P01"])

    def test_rank_deficiency_fails_closed(self):
        sample, omission = self.fixture()
        sample["frame"]["X3"] = sample["frame"]["X1"]
        with self.assertRaisesRegex(RuntimeError, "HOLD_INVALID_LOO_REFIT"):
            r5.refit(sample, omission)

    def test_nonfinite_input_fails_closed(self):
        sample, omission = self.fixture()
        sample["frame"]["X1"] = np.nan
        with self.assertRaisesRegex(RuntimeError, "HOLD_INVALID_LOO_REFIT"):
            r5.refit(sample, omission)

    def test_missing_coefficient_fails_closed(self):
        sample, omission = self.fixture()
        sample["columns"] = ["X1", "ABSENT"]
        with self.assertRaisesRegex(RuntimeError, "HOLD_INVALID_LOO_REFIT"):
            r5.refit(sample, omission)

    def test_bad_estimator_beta_fails_closed(self):
        sample, omission = self.fixture()
        for invalid in ([np.nan, 1, 2], [1, 2]):
            with self.subTest(beta=invalid), patch.object(r5.ed1, "fit_two_way_fe_cr2", return_value={"beta": invalid}):
                with self.assertRaisesRegex(RuntimeError, "HOLD_INVALID_LOO_REFIT"):
                    r5.refit(sample, omission)

    def test_same_frozen_estimator_and_fe(self):
        sample, omission = self.fixture()
        with patch.object(r5.ed1, "fit_two_way_fe_cr2", wraps=r5.ed1.fit_two_way_fe_cr2) as estimator:
            betas, audit = r5.refit(sample, omission)
        estimator.assert_called_once()
        kept, columns, period, response = estimator.call_args.args
        self.assertNotIn("P01", set(kept[period]))
        self.assertEqual(columns, sample["columns"])
        np.testing.assert_array_equal(response, kept["YIELD"].values)
        self.assertEqual(list(betas), columns)
        self.assertEqual(audit["FULL_DESIGN_RANK"], audit["FULL_DESIGN_COLUMNS"])
        self.assertEqual(audit["WITHIN_CLIMATE_RANK"], len(columns))
        self.assertEqual(audit["DISTRICT_FE"], audit["REMAINING_PERIOD_FE"])
        self.assertEqual(audit["RETAINED_ORDERED_KEY_SHA256"], audit["EXPECTED_RETAINED_KEY_SHA256"])

    def test_synthetic_independent_reference(self):
        sample, omission = self.fixture()
        betas, _ = r5.refit(sample, omission)
        reference = r5.r5p.reference_loo_beta(sample["frame"], sample["columns"], sample["period"], sample["frame"]["YIELD"].values, "P01")
        np.testing.assert_allclose(list(betas.values()), list(reference.values()), rtol=0, atol=1e-10)

    def test_sign_and_zero(self):
        self.assertEqual([r5.r5p.classify_sign(x) for x in (1e-100, -1e-100, 0, -0.0)], ["POSITIVE", "NEGATIVE", "ZERO", "ZERO"])

    def test_strict_reversal(self):
        for primary, beta, expected in ((1, -1, True), (-1, 1, True), (0, -1, False), (-1, 0, False), (1, 1, False)):
            self.assertEqual(r5.r5p.sign_reversal(primary, beta), expected)

    def test_summary_formulas_zero_and_exact_ties(self):
        result = r5.r5p.summarize_loo(1, [("P03", 2), ("P01", 0), ("P02", 1)])
        self.assertEqual((result["MIN_LOO_BETA"], result["MAX_LOO_BETA"], result["MEDIAN_LOO_BETA"], result["BETA_RANGE"]), (0, 2, 1, 2))
        self.assertEqual(result["ZERO_COUNT"], 1)
        self.assertEqual(result["PERIODS_CAUSING_MAX_ABSOLUTE_DEVIATION"], ["P01", "P03"])
        self.assertEqual(result["MAX_ABSOLUTE_BETA_DEVIATION"], 1)

    def test_no_inference_schema(self):
        forbidden = {"P_VALUE", "HOLM_P", "SE", "T", "DF", "SIGNIFICANT", "ROBUSTNESS_SCORE"}
        for schema in (r5.DETAIL_FIELDS, r5.SUMMARY_FIELDS, r5.AUDIT_FIELDS):
            self.assertFalse(forbidden & set(schema))

    def test_no_result_specific_estimation_branch(self):
        source = (ROOT / r5.SCRIPT).read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name in ("refit", "calculate", "exact_retained", "summarize"):
                literals = {n.value for n in ast.walk(node) if isinstance(n, ast.Constant) and isinstance(n.value, str)}
                self.assertFalse(literals & {"Banana", "Lemon", "15010040000", "13010170102"})
        self.assertNotIn("read_b3_sensitivity(", source)
        self.assertNotIn("restricted_wild_cluster_bootstrap_t(", source)

    def test_named_cases_prespecified(self):
        for code in r5.r5p.CROP_ORDER:
            periods = r5.r5p.EXPECTED_PERIODS[code]
            self.assertEqual(r5.r5p.mandatory_named_case(code, periods[0] if code in r5.r5p.TRANSIENT_CODES else "2017"), "LEAVE_2017_OUT")
            self.assertEqual(r5.r5p.mandatory_named_case(code, periods[-1]), "LEAVE_2023_OUT")

    def test_r6_firewall(self):
        self.assertEqual(self.plan["r6_authorization_status"], "NOT_AUTHORIZED")
        self.assertFalse(self.plan["r6_executed"])

    def test_complete_pipeline_with_synthetic_y_x_only(self):
        generator = np.random.default_rng(20260911)
        samples = {}
        for code in r5.r5p.CROP_ORDER:
            period = r5.ed1.CROPS[code]["period_column"]
            keys = self.plan["sample_identity"][code]
            frame = pd.DataFrame(keys, columns=["UBIGEO", period])
            columns = [t["VARIABLE"] for t in self.plan["summary_targets"] if t["CROP_CODE"] == code]
            x = generator.normal(size=(len(keys), len(columns)))
            y = generator.normal(size=len(keys))
            frame[columns] = x
            frame["YIELD"] = y
            samples[code] = {"frame": frame, "columns": columns, "period": period, "keys": keys,
                             "ordered_key_sha256": r5.sha(r5.compact(keys)),
                             "y_float64_sha256": r5.r4.array_sha(y), "x_float64_sha256": r5.r4.array_sha(x),
                             "actual": {"n": len(keys)}, "synthetic_only": True}
        with patch.object(r5.r4, "prepare_real_samples", return_value=(samples, {"synthetic_only": True})) as loader:
            data = r5.calculate(r5.json_bytes(self.plan))
        loader.assert_called_once()
        self.assertEqual(tuple(len(data[k]) for k in ("audits", "detail", "summary", "concordance")), (38, 162, 21, 21))
        first = r5.render(data, r5.json_bytes(self.plan), {"status": "PENDING_FULL_SUITE_ADJUDICATION"})
        second = r5.render(json.loads(r5.json_bytes(data)), r5.json_bytes(self.plan), {"status": "PENDING_FULL_SUITE_ADJUDICATION"})
        self.assertEqual(first, second)
        self.assertEqual(tuple(first), r5.GENERATED)
        for payload in first.values():
            self.assertNotIn(b"\r", payload)
            self.assertTrue(payload.endswith(b"\n") and not payload.endswith(b"\n\n"))


class RealArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan_payload = (ROOT / r5.PLAN).read_bytes()
        cls.plan = r5.verify_plan(cls.plan_payload)
        cls.lock = json.loads((ROOT / r5.LOCK).read_bytes())
        cls.detail, cls.summary, cls.audits, cls.concordance = [cls.lock[k] for k in ("detail", "summary", "refit_audit", "concordance")]

    def test_plan_lock_identity(self):
        self.assertEqual(self.lock["execution_plan_lock_sha256"], r5.sha(self.plan_payload))

    def test_no_post_result_code_change(self):
        self.assertEqual(self.plan["executor_sha256"], r5.sha((ROOT / r5.SCRIPT).read_bytes()))
        self.assertEqual(self.plan["tests_sha256"], r5.sha((ROOT / r5.TEST).read_bytes()))

    def test_38_valid_refits(self):
        self.assertEqual(len(self.audits), 38)
        self.assertEqual(len({(r["CROP_CODE"], r["OMITTED_PERIOD_ID"]) for r in self.audits}), 38)
        self.assertTrue(all(r["MODEL_VALID"] for r in self.audits))
        self.assertEqual(self.lock["invalid_refit_inventory"], [])

    def test_162_detail_rows_exact_order(self):
        fields = ["CROP", "CROP_CODE", "MODEL_ID", "VARIABLE", "OMITTED_PERIOD_ID", "OMITTED_PERIOD_ORDER", "MANDATORY_NAMED_CASE"]
        self.assertEqual(len(self.detail), 162)
        self.assertEqual([[r[f] for f in fields] for r in self.detail], [[r[f] for f in fields] for r in self.plan["coefficient_omission_map"]])

    def test_21_summaries_exact_order(self):
        self.assertEqual(len(self.summary), 21)
        self.assertEqual([(r["CROP_CODE"], r["VARIABLE"]) for r in self.summary], [(r["CROP_CODE"], r["VARIABLE"]) for r in self.plan["summary_targets"]])

    def test_21_concordance_rows(self):
        self.assertEqual(len(self.concordance), 21)
        self.assertEqual([set(r) for r in self.concordance], [set(r5.CONCORDANCE_FIELDS)] * 21)

    def test_exact_primary_beta(self):
        frozen = {(r["CROP_CODE"], r["CLIMATE_VARIABLE"]): float(r["BETA"]) for r in r5.frozen_csv(r5.r4.ER1_COEFFICIENTS)}
        for row in self.detail + self.summary + self.concordance:
            self.assertEqual(row["PRIMARY_BETA_REFERENCE"], frozen[(row["CROP_CODE"], row["VARIABLE"])])

    def test_independent_sample_difference_audit(self):
        for row in self.audits:
            full = self.plan["sample_identity"][row["CROP_CODE"]]
            kept = [k for k in full if k[1] != row["OMITTED_PERIOD_ID"]]
            self.assertEqual(row["FULL_SAMPLE_N"], len(full))
            self.assertEqual(row["RETAINED_N"], len(kept))
            self.assertEqual(row["OMITTED_ROWS"], len(full)-len(kept))
            self.assertEqual(row["RETAINED_DISTRICTS"], len({k[0] for k in kept}))
            self.assertEqual(row["RETAINED_ORDERED_KEY_SHA256"], r5.sha(r5.compact(kept)))
            self.assertEqual(row["EXTRA_ROWS_REMOVED"], 0)
            self.assertEqual(row["OMITTED_PERIOD_ROWS_REMAINING"], 0)

    def test_ranks_and_fixed_effects(self):
        for row in self.audits:
            self.assertEqual(row["FULL_DESIGN_RANK"], row["FULL_DESIGN_COLUMNS"])
            self.assertEqual(row["WITHIN_CLIMATE_RANK"], len(row["REGRESSORS"].split("|")))
            self.assertEqual(row["DISTRICT_FE"], "REQUIRED_ACTIVE")
            self.assertEqual(row["REMAINING_PERIOD_FE"], "REQUIRED_ACTIVE")
            self.assertTrue(row["FULL_DESIGN_RANK_VALID"] and row["WITHIN_CLIMATE_RANK_VALID"])

    def test_finite_betas(self):
        self.assertTrue(all(np.isfinite(r["LOO_BETA"]) for r in self.detail))

    def test_exact_difference(self):
        for r in self.detail:
            self.assertEqual(r["BETA_DIFFERENCE"], r["LOO_BETA"]-r["PRIMARY_BETA_REFERENCE"])

    def test_exact_absolute_deviation(self):
        for r in self.detail:
            self.assertEqual(r["ABS_BETA_DEVIATION"], abs(r["LOO_BETA"]-r["PRIMARY_BETA_REFERENCE"]))

    def test_exact_signs_and_reversals(self):
        for r in self.detail:
            b, p = r["LOO_BETA"], r["PRIMARY_BETA_REFERENCE"]
            self.assertEqual(r["LOO_SIGN"], "POSITIVE" if b > 0 else "NEGATIVE" if b < 0 else "ZERO")
            self.assertEqual(r["PRIMARY_SIGN"], "POSITIVE" if p > 0 else "NEGATIVE" if p < 0 else "ZERO")
            self.assertEqual(r["SIGN_REVERSAL"], b*p < 0)

    def test_independent_summary_formulas_and_named_years(self):
        for s in self.summary:
            rows = [r for r in self.detail if (r["CROP_CODE"], r["VARIABLE"]) == (s["CROP_CODE"], s["VARIABLE"])]
            values = [r["LOO_BETA"] for r in rows]
            self.assertEqual(s["MIN_LOO_BETA"], min(values))
            self.assertEqual(s["MAX_LOO_BETA"], max(values))
            self.assertEqual(s["MEDIAN_LOO_BETA"], statistics.median(values))
            self.assertEqual(s["BETA_RANGE"], max(values)-min(values))
            self.assertEqual(s["POSITIVE_COUNT"], sum(v > 0 for v in values))
            self.assertEqual(s["NEGATIVE_COUNT"], sum(v < 0 for v in values))
            self.assertEqual(s["ZERO_COUNT"], sum(v == 0 for v in values))
            self.assertEqual(s["SIGN_REVERSAL_COUNT"], sum(v*s["PRIMARY_BETA_REFERENCE"] < 0 for v in values))
            deviation = max(abs(v-s["PRIMARY_BETA_REFERENCE"]) for v in values)
            self.assertEqual(s["MAX_ABSOLUTE_BETA_DEVIATION"], deviation)
            self.assertEqual(s["PERIODS_CAUSING_MAX_ABSOLUTE_DEVIATION"], "|".join(sorted(r["OMITTED_PERIOD_ID"] for r in rows if abs(r["LOO_BETA"]-s["PRIMARY_BETA_REFERENCE"]) == deviation)))
            for year in (2017, 2023):
                self.assertEqual(s[f"LEAVE_{year}_OUT_BETA"], next(r["LOO_BETA"] for r in rows if r["MANDATORY_NAMED_CASE"] == f"LEAVE_{year}_OUT"))

    def test_historical_concordance_copied_only(self):
        expected = r5.concordance(self.summary)
        self.assertEqual(self.concordance, expected)
        for s, c in zip(self.summary, self.concordance):
            self.assertEqual(c["R5_BETA_RANGE"], s["BETA_RANGE"])
            self.assertEqual(c["R5_SIGN_REVERSAL_COUNT"], s["SIGN_REVERSAL_COUNT"])

    def test_exact_artifact_schemas_and_csv_roundtrip(self):
        for path, rows, schema in ((r5.DETAIL, self.detail, r5.DETAIL_FIELDS), (r5.SUMMARY, self.summary, r5.SUMMARY_FIELDS), (r5.AUDIT, self.audits, r5.AUDIT_FIELDS), (r5.CONCORDANCE, self.concordance, r5.CONCORDANCE_FIELDS)):
            self.assertEqual((ROOT / path).read_bytes(), r5.csv_bytes(rows, schema))
            reader = csv.DictReader(io.StringIO((ROOT / path).read_text(encoding="utf-8")))
            self.assertEqual(reader.fieldnames, list(schema))

    def test_artifact_hashes_and_byte_contract(self):
        for path in r5.CANDIDATES:
            b = (ROOT / path).read_bytes()
            b.decode("utf-8")
            self.assertNotIn(b"\r", b)
            self.assertFalse(b.startswith(b"\xef\xbb\xbf"))
            self.assertTrue(b.endswith(b"\n") and not b.endswith(b"\n\n"))
            if path != r5.LOCK:
                self.assertEqual(r5.sha(b), self.lock["artifact_sha256"][path.as_posix()])

    def test_calculation_digest(self):
        payload = {"audits": self.audits, "detail": self.detail, "summary": self.summary}
        self.assertEqual(r5.sha(r5.compact(payload)), self.lock["calculation_sha256"])

    def test_two_run_render_reproduction_without_refitting(self):
        data = {"audits": self.audits, "detail": self.detail, "summary": self.summary, "concordance": self.concordance,
                "calculation_sha256": self.lock["calculation_sha256"], "primary_coefficient_identities": self.lock["primary_coefficient_identities"], "sample_identity": self.lock["sample_identity"]}
        first = r5.render(data, self.plan_payload, self.lock["full_suite_adjudication"])
        second = r5.render(json.loads(r5.json_bytes(data)), self.plan_payload, self.lock["full_suite_adjudication"])
        self.assertEqual(first, second)
        self.assertTrue(all((ROOT / p).read_bytes() == b for p, b in first.items()))
        self.assertEqual(self.lock["two_run_reproducibility"]["independent_processes"], 2)

    def test_no_inference_or_primary_replacement(self):
        self.assertEqual(self.lock["r5_loo_inference_outputs"], "NOT_AUTHORIZED")
        self.assertEqual(self.lock["primary_replacement"], "PROHIBITED")
        self.assertEqual(self.lock["result_specific_r5_branches"], 0)

    def test_r6_not_executed(self):
        self.assertFalse(self.lock["r6_executed"])
        self.assertEqual(self.lock["r6_authorization_status"], "NOT_AUTHORIZED")


if __name__ == "__main__":
    unittest.main()
