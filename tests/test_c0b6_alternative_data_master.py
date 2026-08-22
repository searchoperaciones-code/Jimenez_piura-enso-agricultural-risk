"""Regression tests for the adjudicated C0B6 transient data master."""

from __future__ import annotations

import ast
import csv
import hashlib
import inspect
import json
import subprocess
import sys
import unittest
from collections import Counter
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import c0b6_alternative_data_master as master  # noqa: E402


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=ROOT, text=True, encoding="utf-8",
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    )
    return result.stdout.strip()


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class C0B6AlternativeDataMasterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.transient_columns, cls.transient = read_csv(master.TRANSIENT_PATH)
        cls.scope_columns, cls.scope = read_csv(master.SCOPE_PATH)
        cls.audit_columns, cls.audit = read_csv(master.AUDIT_PATH)
        cls.config = json.loads(master.CONFIG_PATH.read_text(encoding="utf-8"))
        cls.report = master.REPORT_PATH.read_text(encoding="utf-8")

    def test_01_exact_c0b5_freeze_ancestry(self) -> None:
        self.assertEqual(git("branch", "--show-current"), master.EXPECTED_BRANCH)
        self.assertEqual(git("rev-parse", "HEAD"), master.EXPECTED_HEAD)
        self.assertEqual(git("show", "-s", "--format=%s", "HEAD"), master.EXPECTED_SUBJECT)
        result = subprocess.run(
            ["git", "merge-base", "--is-ancestor", master.EXPECTED_HEAD, "HEAD"],
            cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        self.assertEqual(result.returncode, 0)

    def test_02_c0b5_and_frozen_inputs_are_byte_identical(self) -> None:
        expected_hashes = {**master.C0B5_HASHES, **master.FROZEN_INPUT_HASHES}
        for relative, expected in expected_hashes.items():
            self.assertEqual(sha256(ROOT / relative), expected, relative)
        protected = list(expected_hashes)
        changed = set(filter(None, git("diff", "--name-only", "--", *protected).splitlines()))
        changed |= set(filter(None, git("diff", "--cached", "--name-only", "--", *protected).splitlines()))
        self.assertEqual(changed, set())

    def test_03_exact_seven_file_c0b6_scope(self) -> None:
        tracked = set(filter(None, git("diff", "--name-only").splitlines()))
        tracked |= set(filter(None, git("diff", "--cached", "--name-only").splitlines()))
        untracked = {
            line.replace("\\", "/")
            for line in git("ls-files", "--others", "--exclude-standard").splitlines()
            if line
        }
        self.assertEqual(tracked, set())
        self.assertEqual(untracked, master.AUTHORIZED_SCOPE)

    def test_04_failed_perennial_artifact_is_absent(self) -> None:
        self.assertFalse(master.LEGACY_PERENNIAL_PATH.exists())
        self.assertNotIn(
            master.LEGACY_PERENNIAL_PATH.relative_to(ROOT).as_posix(),
            master.AUTHORIZED_SCOPE,
        )
        self.assertFalse(hasattr(master, "build_perennial_rows"))

    def test_05_output_schemas_are_exact(self) -> None:
        self.assertEqual(self.transient_columns, master.TRANSIENT_COLUMNS)
        self.assertEqual(self.scope_columns, master.SCOPE_COLUMNS)
        self.assertEqual(self.audit_columns, master.AUDIT_COLUMNS)

    def test_06_selected_scope_is_exact_s1(self) -> None:
        self.assertEqual(self.config["selected_scope_architecture"], master.SELECTED_SCOPE_ARCHITECTURE)
        adjudication = self.config["scope_adjudication"]
        self.assertEqual(adjudication["s1_status"], "SCIENTIFICALLY_ADMISSIBLE_AND_SELECTED")
        self.assertTrue(adjudication["s2_status"].startswith("REJECTED_"))
        self.assertTrue(adjudication["s3_status"].startswith("REJECTED_"))
        self.assertFalse(adjudication["c0b5_reopen_required"])
        self.assertTrue(adjudication["preserves_13_districts"])

    def test_07_dual_analytical_layers_are_separated(self) -> None:
        layers = self.config["dual_analytical_layers"]
        self.assertEqual(layers["status"], master.DUAL_LAYER_STATUS)
        self.assertEqual(layers["layer_1"]["name"], "FIVE_CROP_CLIMATE_ECONOMIC_RISK_CHARACTERIZATION")
        self.assertFalse(layers["layer_1"]["materialized_in_c0b6"])
        self.assertEqual(layers["layer_2"]["name"], "RICE_MAD_FINITE_REFERENCE_CONFIGURATION_STRESS_TEST")
        self.assertTrue(layers["layer_2"]["materialized_in_c0b6"])
        self.assertFalse(layers["layer_1_aggregation_into_layer_2_authorized"])

    def test_08_alternative_ids_and_campaigns_are_exact(self) -> None:
        observed = sorted({(row["ALTERNATIVE_ID"], row["SOURCE_CAMPAIGN"]) for row in self.transient})
        expected = sorted((alternative_id, campaign) for alternative_id, campaign, _ in master.ALTERNATIVES)
        self.assertEqual(observed, expected)
        configured = [
            (item["alternative_id"], item["source_campaign"])
            for item in self.config["reference_configurations"]
        ]
        self.assertEqual(configured, expected)

    def test_09_exact_common_support(self) -> None:
        observed = {(row["UBIGEO"], row["DISTRICT_NAME"]) for row in self.transient}
        self.assertEqual(observed, set(master.DISTRICTS))
        self.assertEqual(len(observed), 13)
        self.assertEqual(self.config["common_support_districts_n"], 13)

    def test_10_reference_configuration_scope_is_rice_mad_only(self) -> None:
        self.assertEqual({row["CROP_CODE"] for row in self.transient}, set(master.TRANSIENT_CROPS))
        self.assertEqual(self.config["reference_configuration_crop_scope"], "RICE_MAD_TRANSIENT_ONLY")
        self.assertEqual(set(self.config["transient_comparator_crop_codes"]), set(master.TRANSIENT_CROPS))
        self.assertTrue(all(
            item["comparator_crop_scope"] == "RICE_MAD_TRANSIENT_ONLY"
            for item in self.config["reference_configurations"]
        ))

    def test_11_broader_analysis_retains_all_five_crops(self) -> None:
        expected = set(master.TRANSIENT_CROPS) | set(master.PERENNIAL_CROPS)
        self.assertEqual(set(self.config["broader_analysis_crop_codes"]), expected)
        self.assertEqual(set(self.config["perennial_broader_analysis_crop_codes"]), set(master.PERENNIAL_CROPS))
        self.assertEqual(set(self.config["dual_analytical_layers"]["layer_1"]["crop_codes"]), expected)

    def test_12_transient_monthly_row_count(self) -> None:
        self.assertEqual(len(self.transient), 624)
        self.assertEqual(self.config["transient_master"]["expected_monthly_rows"], 624)
        self.assertEqual(self.config["transient_master"]["observed_monthly_rows"], 624)

    def test_13_transient_key_is_unique(self) -> None:
        keys = [
            (row["ALTERNATIVE_ID"], row["UBIGEO"], row["CROP_CODE"], row["CAMPAIGN_MONTH_ORDER"])
            for row in self.transient
        ]
        self.assertEqual(len(keys), len(set(keys)))

    def test_14_campaign_calendar_mapping_is_exact(self) -> None:
        starts = {alternative_id: start for alternative_id, _, start in master.ALTERNATIVES}
        for row in self.transient:
            order = int(row["CAMPAIGN_MONTH_ORDER"])
            month = master.CAMPAIGN_MONTHS[order - 1]
            year = starts[row["ALTERNATIVE_ID"]] if month >= 8 else starts[row["ALTERNATIVE_ID"]] + 1
            self.assertEqual(int(row["CALENDAR_YEAR"]), year)
            self.assertEqual(int(row["CALENDAR_MONTH"]), month)
            self.assertEqual(int(row["YEAR_MONTH"]), year * 100 + month)

    def test_15_exact_52_complete_transient_cells(self) -> None:
        counts = Counter((row["ALTERNATIVE_ID"], row["UBIGEO"], row["CROP_CODE"]) for row in self.transient)
        self.assertEqual(len(counts), 52)
        self.assertEqual(set(counts.values()), {12})
        transient = self.config["transient_master"]
        self.assertEqual(transient["observed_complete_district_crop_alternative_cells"], 52)
        self.assertEqual(transient["missing_district_crop_alternative_cells"], 0)

    def test_16_frozen_transient_totals_recompute(self) -> None:
        totals = Counter()
        for row in self.transient:
            totals[(row["ALTERNATIVE_ID"], row["CROP_CODE"])] += Decimal(row["SIEMBRA_HA"])
        self.assertEqual(totals[("C0B5-A2020-2021", "14010020000")], Decimal(15213))
        self.assertEqual(totals[("C0B5-A2020-2021", "14010070000")], Decimal(5704))
        self.assertEqual(totals[("C0B5-A2023-2024", "14010020000")], Decimal(22592))
        self.assertEqual(totals[("C0B5-A2023-2024", "14010070000")], Decimal(5937))

    def test_17_campaign_totals_reconcile_per_profile(self) -> None:
        groups: dict[tuple[str, str, str], list[dict[str, str]]] = {}
        for row in self.transient:
            key = (row["ALTERNATIVE_ID"], row["UBIGEO"], row["CROP_CODE"])
            groups.setdefault(key, []).append(row)
        for key, rows in groups.items():
            total = sum((Decimal(row["SIEMBRA_HA"]) for row in rows), Decimal(0))
            self.assertEqual({Decimal(row["CAMPAIGN_TOTAL_HA"]) for row in rows}, {total}, key)

    def test_18_shares_normalize_exactly(self) -> None:
        groups: dict[tuple[str, str, str], list[Decimal]] = {}
        for row in self.transient:
            key = (row["ALTERNATIVE_ID"], row["UBIGEO"], row["CROP_CODE"])
            groups.setdefault(key, []).append(Decimal(row["WITHIN_CAMPAIGN_SHARE"]))
        self.assertEqual(len(groups), 52)
        for key, shares in groups.items():
            self.assertTrue(all(share >= 0 for share in shares), key)
            self.assertEqual(sum(shares, Decimal(0)), Decimal(1), key)

    def test_19_timing_profiles_are_26_of_26_each(self) -> None:
        counts = Counter((row["ALTERNATIVE_ID"], row["UBIGEO"], row["CROP_CODE"]) for row in self.transient)
        by_alternative = Counter(alternative_id for alternative_id, _, _ in counts)
        self.assertEqual(by_alternative, {"C0B5-A2020-2021": 26, "C0B5-A2023-2024": 26})
        self.assertEqual(set(self.config["transient_master"]["timing_profiles_complete"].values()), {26})
        self.assertEqual(set(self.config["transient_master"]["timing_profiles_normalized"].values()), {26})

    def test_20_zero_and_missing_semantics(self) -> None:
        zeros = Counter(row["ALTERNATIVE_ID"] for row in self.transient if row["OBSERVED_ZERO_FLAG"] == "TRUE")
        self.assertEqual(zeros, {"C0B5-A2020-2021": 197, "C0B5-A2023-2024": 166})
        self.assertTrue(all(row["SOURCE_MISSING_FLAG"] == "FALSE" for row in self.transient))
        self.assertFalse(self.config["transient_master"]["silent_missing_to_zero_used"])

    def test_21_transient_rows_reproduce_from_source(self) -> None:
        records, _ = master.load_source()
        self.assertEqual(self.transient, master.build_transient_rows(records))

    def test_22_no_profile_mixing_or_generic_t3(self) -> None:
        allowed = {alternative_id: campaign for alternative_id, campaign, _ in master.ALTERNATIVES}
        self.assertTrue(all(row["SOURCE_CAMPAIGN"] == allowed[row["ALTERNATIVE_ID"]] for row in self.transient))
        transient = self.config["transient_master"]
        self.assertFalse(transient["generic_t3_rule_authorized"])
        self.assertFalse(transient["pooled_timing_shares_created"])
        self.assertFalse(transient["district_mix_and_match_detected"])
        self.assertFalse(transient["crop_year_mixing_detected"])
        self.assertFalse(transient["timing_profile_mixing_detected"])

    def test_23_reference_role_is_exact(self) -> None:
        self.assertEqual({row["REFERENCE_CONFIGURATION_ROLE"] for row in self.transient}, {master.REFERENCE_ROLE})
        self.assertTrue(all(row["EMPIRICALLY_REALIZED"] == "TRUE" for row in self.transient))
        self.assertEqual(self.config["transient_master"]["reference_configuration_role"], master.REFERENCE_ROLE)

    def test_24_no_common_complete_perennial_month_exists(self) -> None:
        records, months = master.load_source()
        trail, selected = master.build_perennial_coverage_trail(records, months)
        self.assertIsNone(selected)
        self.assertEqual(len(trail), 113)
        self.assertTrue(all(item["complete_cells"] < 39 for item in trail))
        perennial = self.config["perennial_scope_adjudication"]
        self.assertFalse(perennial["common_complete_perennial_month_exists"])
        self.assertEqual(perennial["candidate_months_audited_n"], 113)

    def test_25_maximum_perennial_coverage_is_exact(self) -> None:
        perennial = self.config["perennial_scope_adjudication"]
        self.assertEqual(perennial["max_complete_perennial_cells_any_month"], 38)
        self.assertEqual(perennial["perennial_expected_common_cells"], 39)
        self.assertEqual(perennial["best_perennial_coverage_months"], [202303, 202407])

    def test_26_best_month_missing_cells_are_exact(self) -> None:
        observed = self.config["perennial_scope_adjudication"]["best_month_missing_cells"]
        expected = [
            {
                "year_month": 202303,
                "ubigeo": "200108",
                "district_name": "EL TALLAN",
                "crop_code": "15010040000",
                "crop_std": "PLATANOS Y BANANAS",
            },
            {
                "year_month": 202407,
                "ubigeo": "200804",
                "district_name": "CRISTO NOS VALGA",
                "crop_code": "15010040000",
                "crop_std": "PLATANOS Y BANANAS",
            },
        ]
        self.assertEqual(observed, expected)

    def test_27_crop_specific_perennial_coverage_is_exact(self) -> None:
        coverage = self.config["perennial_scope_adjudication"]["crop_coverage"]
        self.assertTrue(coverage["13010210000"]["any_13_of_13_month"])
        self.assertTrue(coverage["13010170102"]["any_13_of_13_month"])
        self.assertFalse(coverage["15010040000"]["any_13_of_13_month"])
        self.assertEqual(coverage["15010040000"]["best_complete_districts_n"], 12)

    def test_28_perennial_missingness_and_external_evidence_are_frozen(self) -> None:
        perennial = self.config["perennial_scope_adjudication"]
        self.assertEqual(
            perennial["perennial_source_missingness_typology"],
            ["INTERMITTENT_REPORTING_MISSINGNESS", "ASYNCHRONOUS_CROP_REPORTING"],
        )
        self.assertEqual(perennial["externally_certifiable_perennial_completion_cells_n"], 0)
        self.assertFalse(perennial["missing_reinterpreted_as_zero"])

    def test_29_perennials_are_outside_a1_a2_but_remain_in_study(self) -> None:
        perennial = self.config["perennial_scope_adjudication"]
        self.assertFalse(perennial["perennials_in_a1_a2_reference_configurations"])
        self.assertTrue(perennial["perennials_remain_in_broader_analysis"])
        self.assertEqual(perennial["perennial_comparator_role"], "NONE")
        self.assertFalse(perennial["common_perennial_block_materialized"])
        self.assertTrue(all("perennial_block" not in item for item in self.config["reference_configurations"]))

    def test_30_reference_manifest_contains_transient_blocks_only(self) -> None:
        manifest = self.config["reference_configuration_manifest"]
        self.assertEqual(manifest["alternative_1"], ["TRANSIENT_BLOCK_A1"])
        self.assertEqual(manifest["alternative_2"], ["TRANSIENT_BLOCK_A2"])
        self.assertEqual(manifest["status"], "READY_TRANSIENT_REFERENCE_CONFIGURATIONS")

    def test_31_scope_adjudication_csv_is_complete_and_frozen(self) -> None:
        self.assertEqual(len(self.scope), 16)
        self.assertEqual({row["CHECK_ID"] for row in self.scope}, {f"C0B6S-{number:03d}" for number in range(1, 17)})
        self.assertEqual({row["FROZEN_STATUS"] for row in self.scope}, {"PASS_FROZEN"})
        adjudications = {row["ADJUDICATION"] for row in self.scope}
        self.assertTrue({"S1_SELECTED", "S2_REJECTED", "S3_REJECTED"} <= adjudications)

    def test_32_five_crop_aggregation_and_cvar_cancellation_are_forbidden(self) -> None:
        aggregation = self.config["aggregation_firewalls"]
        self.assertEqual(aggregation["five_crop_a1_a2_aggregation_status"], "NOT_AUTHORIZED")
        self.assertFalse(aggregation["common_perennial_random_component_can_be_assumed_to_cancel_in_cvar"])
        self.assertEqual(aggregation["later_a1_a2_risk_metrics_scope"], "TRANSIENT_BLOCK_ONLY")
        self.assertEqual(len(aggregation["forbidden_outputs"]), 7)

    def test_33_c0b3_architecture_and_p3_resolution_are_preserved(self) -> None:
        architecture = self.config["frozen_architecture_firewalls"]
        self.assertEqual(architecture["decision_architecture"], "ARCH_F_TRANSIENT_ENDOGENOUS_PERENNIAL_EXOGENOUS")
        self.assertEqual(architecture["perennial_resolution"], master.P3_STATUS)
        c0b3 = json.loads(master.C0B3_CONFIG_PATH.read_text(encoding="utf-8"))
        verde = c0b3["variable_adjudication"]["VERDE_ACTUAL"]
        self.assertEqual(verde["status"], "INSTALLED_STOCK_CERTIFIED")
        self.assertEqual(verde["unit"], "ha")

    def test_34_future_feasibility_firewall(self) -> None:
        firewalls = self.config["firewalls"]
        self.assertEqual(firewalls["historical_realization_status"], "CERTIFIED_BY_SOURCE_OBSERVATION")
        self.assertEqual(firewalls["prospective_physical_feasibility_status"], "NOT_CERTIFIED")
        self.assertEqual(firewalls["prospective_institutional_feasibility_status"], "NOT_CERTIFIED")

    def test_35_land_capacity_firewall(self) -> None:
        architecture = self.config["frozen_architecture_firewalls"]
        firewalls = self.config["firewalls"]
        manifest = self.config["reference_configuration_manifest"]
        self.assertEqual(architecture["area_ha_status"], "PHYSICAL_AGRICULTURAL_FOOTPRINT_ONLY")
        self.assertEqual(architecture["model_authorized_land_parameters_n"], 0)
        self.assertEqual(architecture["model_authorized_adjustment_bounds_n"], 0)
        self.assertEqual(firewalls["land_hard_cap_status"], "NOT_AUTHORIZED")
        self.assertEqual(firewalls["reallocable_transient_land_status"], "NOT_OBSERVED")
        self.assertFalse(firewalls["area_ha_feasibility_test_used"])
        self.assertFalse(manifest["components_are_physical_total_land_occupancy"])
        self.assertFalse(manifest["components_are_regional_capacity"])
        self.assertFalse(manifest["components_are_reallocable_land"])

    def test_36_no_water_optimization_or_downstream_outputs(self) -> None:
        firewalls = self.config["firewalls"]
        self.assertEqual(firewalls["water_model_status"], "NOT_AUTHORIZED")
        self.assertFalse(firewalls["outcome_leakage_used"])
        self.assertEqual(firewalls["continuous_optimization_status"], "NOT_AUTHORIZED")
        self.assertFalse(firewalls["economic_or_climate_output_created"])
        self.assertFalse(firewalls["configuration_ranking_executed"])

    def test_37_source_reader_has_no_outcome_leakage(self) -> None:
        tree = ast.parse(inspect.getsource(master.load_source))
        keys = {
            node.slice.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Subscript)
            and isinstance(node.slice, ast.Constant)
            and isinstance(node.slice.value, str)
        }
        self.assertEqual(keys, {"MES", "COD_CULTIVO", "UBIGEO", "SIEMBRA", "VERDE_ACTUAL"})
        forbidden = {"YIELD_RAW", "PRECIO", "P_VALUE", "CVAR", "OBJECTIVE"}
        self.assertTrue(forbidden.isdisjoint(self.transient_columns))

    def test_38_audit_is_all_pass_and_covers_critical_domains(self) -> None:
        self.assertEqual(len(self.audit), 29)
        self.assertEqual({row["STATUS"] for row in self.audit}, {"PASS"})
        domains = {row["DOMAIN"] for row in self.audit}
        required = {
            "SELECTED_SCOPE_ARCHITECTURE", "PERENNIAL_BASELINE_UNAVAILABLE",
            "PERENNIALS_EXCLUDED_FROM_COMPARATOR", "FIVE_CROP_A1_A2_AGGREGATION",
            "COMMON_PERENNIAL_CVAR_CANCELLATION", "NO_OUTCOME_LEAKAGE",
            "NO_LAND_CAPACITY_INFERENCE", "NO_WATER_MODEL", "NO_OPTIMIZATION",
        }
        self.assertTrue(required <= domains)

    def test_39_report_has_23_required_sections(self) -> None:
        sections = [f"## {number}." for number in range(1, 24)]
        positions = [self.report.index(section) for section in sections]
        self.assertEqual(positions, sorted(positions))
        self.assertEqual(self.report.count("\n## "), 23)
        self.assertIn(f"C0B6_STATUS={master.FINAL_STATUS}", self.report)

    def test_40_report_does_not_claim_regional_or_five_crop_representativeness(self) -> None:
        lower = self.report.lower()
        self.assertNotIn("representative of piura", lower)
        self.assertNotIn("five-crop reference configuration", lower)
        self.assertIn("may not be described as five-crop", lower)
        master.validate_report_scope(self.report)
        with self.assertRaisesRegex(AssertionError, "representative-Piura"):
            master.validate_report_scope("This configuration is representative of Piura. May not be described as five-crop.")

    def test_41_artifact_hashes_are_consistent(self) -> None:
        expected_paths = {
            master.TRANSIENT_PATH.relative_to(ROOT).as_posix(),
            master.SCOPE_PATH.relative_to(ROOT).as_posix(),
            master.AUDIT_PATH.relative_to(ROOT).as_posix(),
        }
        self.assertEqual(set(self.config["artifact_sha256"]), expected_paths)
        for relative, expected in self.config["artifact_sha256"].items():
            self.assertEqual(sha256(ROOT / relative), expected, relative)

    def test_42_outputs_reproduce_byte_for_byte(self) -> None:
        expected, config = master.build_output_bytes()
        self.assertEqual(
            set(expected),
            {master.TRANSIENT_PATH, master.SCOPE_PATH, master.AUDIT_PATH, master.CONFIG_PATH, master.REPORT_PATH},
        )
        for path, payload in expected.items():
            self.assertEqual(path.read_bytes(), payload, path.name)
        self.assertEqual(self.config, config)

    def test_43_c0b6_files_are_utf8_lf_with_one_final_lf(self) -> None:
        for relative in master.AUTHORIZED_SCOPE:
            raw = (ROOT / relative).read_bytes()
            self.assertFalse(raw.startswith(b"\xef\xbb\xbf"), relative)
            self.assertNotIn(b"\r", raw, relative)
            self.assertTrue(raw.endswith(b"\n"), relative)
            self.assertFalse(raw.endswith(b"\n\n"), relative)

    def test_44_preflight_reports_rebuild_pass(self) -> None:
        lines = master.run_preflight()
        self.assertIn("C0B5_IMMUTABILITY_GATE=PASS", lines)
        self.assertIn("PERSISTENT_SCOPE_GATE=PASS", lines)
        self.assertIn("DETERMINISM_GATE=PASS", lines)
        self.assertIn("TRANSIENT_DATA_MASTER_GATE=PASS", lines)
        self.assertIn("S1_SCOPE_ADJUDICATION_GATE=PASS", lines)
        self.assertIn("FIXED_PERENNIAL_BASELINE_FILE_PRESENT=FALSE", lines)
        self.assertIn(f"C0B6_PREFLIGHT={master.FINAL_STATUS}", lines)

    def test_45_default_and_check_only_modes_are_read_only(self) -> None:
        paths = [master.TRANSIENT_PATH, master.SCOPE_PATH, master.AUDIT_PATH, master.CONFIG_PATH, master.REPORT_PATH]
        before = {path: sha256(path) for path in paths}
        for arguments in ([], ["--check-only"]):
            result = subprocess.run(
                [sys.executable, "-B", str(master.SCRIPT_PATH), *arguments],
                cwd=ROOT, text=True, encoding="utf-8",
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(f"C0B6_PREFLIGHT={master.FINAL_STATUS}", result.stdout)
        self.assertEqual({path: sha256(path) for path in paths}, before)


if __name__ == "__main__":
    unittest.main()
