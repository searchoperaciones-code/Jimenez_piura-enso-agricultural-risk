from __future__ import annotations

import hashlib
import json
import sys
import unittest
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import audit_climate_exposure_spec as spec_audit  # noqa: E402


SPEC = ROOT / "config" / "climate_exposure" / "climate_exposure_spec_v1.json"


def read_spec():
    return json.loads(SPEC.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class ClimateExposureSpecTests(unittest.TestCase):
    def test_01_final_frozen_statuses(self):
        spec = read_spec()
        self.assertEqual(spec["SPEC_STATUS"], "PASS_FROZEN")
        self.assertEqual(spec["DIRECTOR_FREEZE_DECISION"], "PASS")
        self.assertEqual(spec["EXPOSURE_DATA_BUILD"], "READY_FROM_FROZEN_SPEC")
        self.assertEqual(
            spec["CLIMATE_EXPOSURE_BUILD_CONFORMANCE"],
            "MUST_CONFORM_EXACTLY_TO_THIS_FROZEN_CONTRACT",
        )
        self.assertEqual(spec["econometric_status"]["ECONOMETRICS"], "BLOCKED")
        self.assertEqual(spec["future_transient_outcome_contract"]["belongs_to"], "TRANSIENT_OUTCOME_MASTER")
        self.assertEqual(spec["future_transient_outcome_contract"]["status"], "DEFINED_NOT_BUILT")

    def test_02_frozen_hashes(self):
        spec = read_spec()
        self.assertEqual(spec["UPSTREAM_BASE_SHA"], spec_audit.EXPECTED_BASE_SHA)
        self.assertEqual(spec["PHENOLOGY_FREEZE_SHA"], spec_audit.EXPECTED_BASE_SHA)
        self.assertEqual(
            sha256_file(ROOT / "data" / "processed" / "phenology" / "phenology_windows_frozen.csv"),
            spec["PHENOLOGY_WINDOWS_SHA256"],
        )
        self.assertEqual(
            sha256_file(ROOT / "outputs" / "phenology" / "PHENOLOGY_MASTER_V1_FREEZE.md"),
            spec["PHENOLOGY_CERTIFICATE_SHA256"],
        )
        self.assertEqual(
            sha256_file(ROOT / "data" / "processed" / "climate" / "climate_anomalies.parquet"),
            spec["CLIMATE_CANONICAL_SHA256"],
        )

    def test_03_campaign_boundary_dates(self):
        self.assertEqual(spec_audit.campaign_for_date(date(2020, 7, 31)), "2019/2020")
        self.assertEqual(spec_audit.campaign_for_date(date(2020, 8, 1)), "2020/2021")

    def test_04_rice_campaign_calendar_arithmetic(self):
        cases = {
            1: ("UNAMBIGUOUS_AGRONOMIC_CAMPAIGN", "2019/2020"),
            2: ("UNAMBIGUOUS_AGRONOMIC_CAMPAIGN", "2019/2020"),
            3: ("AMBIGUOUS_CROSS_CAMPAIGN", None),
            4: ("AMBIGUOUS_CROSS_CAMPAIGN", None),
            5: ("UNAMBIGUOUS_AGRONOMIC_CAMPAIGN", "2020/2021"),
            7: ("UNAMBIGUOUS_AGRONOMIC_CAMPAIGN", "2020/2021"),
            12: ("UNAMBIGUOUS_AGRONOMIC_CAMPAIGN", "2020/2021"),
        }
        for month, (status, campaign) in cases.items():
            with self.subTest(month=month):
                result = spec_audit.transient_attribution("14010020000", 2020, month)
                self.assertEqual(result["CAMPAIGN_ATTRIBUTION_STATUS"], status)
                self.assertEqual(result["ASSIGNED_CAMPAIGN_ID"], campaign)
        feb = spec_audit.transient_attribution("14010020000", 2020, 2)
        self.assertEqual(feb["ANCHOR_DATE_MAX"], "2020-02-29")
        self.assertEqual(feb["HARVEST_DATE_MAX"], "2020-07-16")
        dec = spec_audit.transient_attribution("14010020000", 2020, 12)
        self.assertEqual(dec["HARVEST_DATE_MIN"], "2021-03-21")

    def test_05_mad_campaign_calendar_arithmetic(self):
        cases = {
            1: ("UNAMBIGUOUS_AGRONOMIC_CAMPAIGN", "2019/2020"),
            2: ("AMBIGUOUS_CROSS_CAMPAIGN", None),
            4: ("AMBIGUOUS_CROSS_CAMPAIGN", None),
            5: ("UNAMBIGUOUS_AGRONOMIC_CAMPAIGN", "2020/2021"),
            7: ("UNAMBIGUOUS_AGRONOMIC_CAMPAIGN", "2020/2021"),
            12: ("UNAMBIGUOUS_AGRONOMIC_CAMPAIGN", "2020/2021"),
        }
        for month, (status, campaign) in cases.items():
            with self.subTest(month=month):
                result = spec_audit.transient_attribution("14010070000", 2020, month)
                self.assertEqual(result["CAMPAIGN_ATTRIBUTION_STATUS"], status)
                self.assertEqual(result["ASSIGNED_CAMPAIGN_ID"], campaign)
        feb = spec_audit.transient_attribution("14010070000", 2020, 2)
        self.assertEqual(feb["ANCHOR_DATE_MAX"], "2020-02-29")
        self.assertEqual(feb["HARVEST_DATE_MAX"], "2020-08-17")
        dec = spec_audit.transient_attribution("14010070000", 2020, 12)
        self.assertEqual(dec["HARVEST_DATE_MIN"], "2021-03-31")

    def test_06_exact_u_a_domains(self):
        self.assertEqual(
            spec_audit.strict_domains("14010020000", 2016),
            {
                "U": [201605, 201606, 201607, 201608, 201609, 201610, 201611, 201612, 201701, 201702],
                "A": [201603, 201604, 201703, 201704],
            },
        )
        self.assertEqual(
            spec_audit.strict_domains("14010070000", 2016),
            {
                "U": [201605, 201606, 201607, 201608, 201609, 201610, 201611, 201612, 201701],
                "A": [201602, 201603, 201604, 201702, 201703, 201704],
            },
        )

    def test_07_no_outcome_fields_in_exposure_schemas(self):
        spec = read_spec()
        self.assertFalse(spec_audit.exposure_schema_fields(spec) & spec_audit.FORBIDDEN_EXPOSURE_SCHEMA_FIELDS)

    def test_08_stage_b_roles_remain_non_econometric(self):
        spec = read_spec()
        strict = spec["stage_b_artifacts"]["transient_campaign_exposures_strict"]
        cohort = spec["stage_b_artifacts"]["transient_cohort_exposures"]
        self.assertFalse(strict["is_primary_econometric_exposure"])
        self.assertNotIn("PRIMARY", strict["artifact_role"])
        self.assertEqual(cohort["artifact_role"], "PRIMARY_STAGE_B_DATA_PRODUCT")
        self.assertEqual(spec["econometric_status"]["PRIMARY_TRANSIENT_ECONOMETRIC_EXPOSURE"], "NOT_YET_SELECTED")

    def test_09_campaign_weight_tolerance(self):
        spec = read_spec()
        self.assertEqual(spec["strict_campaign_identification"]["weight_sum_tolerance_abs"], 1e-12)

    def test_10_auditor_passes(self):
        report = spec_audit.evaluate()
        self.assertEqual(report["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
