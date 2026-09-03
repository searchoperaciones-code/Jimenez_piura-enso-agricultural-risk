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

from scripts import d0_transient_campaign_outcome_master as d0


ROOT = Path(__file__).resolve().parents[1]


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=True, capture_output=True, text=True, encoding="utf-8",
    ).stdout.strip()


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class D0TransientCampaignOutcomeMasterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.master_columns, cls.master = read_csv(d0.MASTER_PATH)
        cls.ledger_columns, cls.ledger = read_csv(d0.LEDGER_PATH)
        cls.audit_columns, cls.audit = read_csv(d0.AUDIT_PATH)
        cls.config = json.loads(d0.CONFIG_PATH.read_text(encoding="utf-8"))
        cls.report = d0.REPORT_PATH.read_text(encoding="utf-8")
        cls.expected_outputs, cls.expected_config, cls.diagnostics = d0.build_output_bytes()

    def test_01_exact_authorized_d0_parent_identity(self) -> None:
        self.assertEqual(git("branch", "--show-current"), d0.EXPECTED_BRANCH)
        self.assertEqual(git("rev-parse", "HEAD"), d0.AUTHORIZED_D0_PARENT_SHA)
        self.assertEqual(
            git("show", "-s", "--format=%s", "HEAD"),
            "Harden Phenology JSON serialization to deterministic UTF-8 LF",
        )
        d0.validate_lineage_snapshot(d0.lineage_snapshot())

    def test_02_r0h_identity_direct_parent_and_diff_scope_are_exact(self) -> None:
        snapshot = d0.lineage_snapshot()
        self.assertEqual(snapshot["r0h_sha"], d0.R0H_HARDENING_SHA)
        self.assertEqual(snapshot["r0h_sha"], d0.AUTHORIZED_D0_PARENT_SHA)
        self.assertEqual(snapshot["r0h_parent_shas"], [d0.JOINT_C0_SCIENTIFIC_BASE_SHA])
        self.assertEqual(snapshot["r0h_diff_paths"], list(d0.R0H_EXPECTED_DIFF_PATHS))
        self.assertEqual(snapshot["r0h_scientific_paths"], [])

    def test_02a_old_joint_c0_head_is_rejected(self) -> None:
        snapshot = {**d0.lineage_snapshot(), "head": d0.JOINT_C0_SCIENTIFIC_BASE_SHA}
        with self.assertRaisesRegex(AssertionError, "exact authorized D0 execution parent"):
            d0.validate_lineage_snapshot(snapshot)

    def test_02b_arbitrary_joint_c0_child_identity_is_rejected(self) -> None:
        snapshot = {**d0.lineage_snapshot(), "head": "1111111111111111111111111111111111111111"}
        with self.assertRaisesRegex(AssertionError, "exact authorized D0 execution parent"):
            d0.validate_lineage_snapshot(snapshot)

    def test_02c_arbitrary_r0h_child_identity_is_rejected(self) -> None:
        snapshot = {**d0.lineage_snapshot(), "head": "2222222222222222222222222222222222222222"}
        with self.assertRaisesRegex(AssertionError, "exact authorized D0 execution parent"):
            d0.validate_lineage_snapshot(snapshot)

    def test_02d_unrelated_commit_identity_is_rejected(self) -> None:
        unrelated_sha = git("rev-parse", "origin/main")
        self.assertNotIn(unrelated_sha, {d0.JOINT_C0_SCIENTIFIC_BASE_SHA, d0.AUTHORIZED_D0_PARENT_SHA})
        snapshot = {**d0.lineage_snapshot(), "head": unrelated_sha}
        with self.assertRaisesRegex(AssertionError, "exact authorized D0 execution parent"):
            d0.validate_lineage_snapshot(snapshot)

    def test_03_joint_c0_files_are_immutable(self) -> None:
        self.assertEqual(
            {relative: sha256(ROOT / relative) for relative in d0.JOINT_C0_HASHES},
            d0.JOINT_C0_HASHES,
        )

    def test_04_exact_seven_file_d0_scope(self) -> None:
        self.assertEqual(set(filter(None, git("diff", "--name-only").splitlines())), set())
        self.assertEqual(set(filter(None, git("diff", "--cached", "--name-only").splitlines())), set())
        untracked = {
            line.replace("\\", "/")
            for line in git("ls-files", "--others", "--exclude-standard").splitlines()
            if line
        }
        self.assertEqual(untracked, d0.AUTHORIZED_SCOPE)

    def test_05_output_schemas_are_exact(self) -> None:
        self.assertEqual(self.master_columns, d0.MASTER_COLUMNS)
        self.assertEqual(self.ledger_columns, d0.LEDGER_COLUMNS)
        self.assertEqual(self.audit_columns, d0.AUDIT_COLUMNS)

    def test_06_crop_codes_and_names_are_exact(self) -> None:
        observed = {(row["CROP_CODE"], row["CROP_STD"]) for row in self.master}
        self.assertEqual(observed, {(code, crop["crop_std"]) for code, crop in d0.CROPS.items()})

    def test_07_seven_campaigns_are_exact(self) -> None:
        self.assertEqual(sorted({row["CAMPAIGN"] for row in self.master}), list(d0.CAMPAIGNS))
        self.assertEqual(len({row["CAMPAIGN"] for row in self.master}), 7)

    def test_08_campaign_calendar_fields_are_exact(self) -> None:
        for row in self.master:
            start = int(row["CAMPAIGN_START_YEAR"])
            self.assertEqual(row["CAMPAIGN"], f"{start}/{start + 1}")
            self.assertEqual(int(row["CAMPAIGN_END_YEAR"]), start + 1)
            self.assertEqual(int(row["CAMPAIGN_START_YEARMONTH"]), start * 100 + 8)
            self.assertEqual(int(row["CAMPAIGN_END_YEARMONTH"]), (start + 1) * 100 + 7)
            self.assertEqual(d0.campaign_months(start), tuple(
                list(range(start * 100 + 8, start * 100 + 13))
                + list(range((start + 1) * 100 + 1, (start + 1) * 100 + 8))
            ))

    def test_09_rice_district_universe_is_exact(self) -> None:
        observed = tuple(sorted({row["UBIGEO"] for row in self.master if row["CROP_CODE"] == "14010020000"}))
        self.assertEqual(observed, d0.RICE_DISTRICTS)
        self.assertEqual(len(observed), 46)

    def test_10_mad_district_universe_is_exact(self) -> None:
        observed = tuple(sorted({row["UBIGEO"] for row in self.master if row["CROP_CODE"] == "14010070000"}))
        self.assertEqual(observed, d0.MAD_DISTRICTS)
        self.assertEqual(len(observed), 55)

    def test_11_potential_row_counts_are_exact(self) -> None:
        counts = Counter(row["CROP_CODE"] for row in self.master)
        self.assertEqual(counts, {"14010020000": 322, "14010070000": 385})
        self.assertEqual(len(self.master), 707)

    def test_12_valid_row_counts_are_exact(self) -> None:
        valid = Counter(row["CROP_CODE"] for row in self.master if row["OUTCOME_VALID_FLAG"] == "TRUE")
        self.assertEqual(valid, {"14010020000": 294, "14010070000": 352})
        self.assertEqual(sum(valid.values()), 646)

    def test_13_invalid_row_counts_are_exact(self) -> None:
        invalid = Counter(row["CROP_CODE"] for row in self.master if row["OUTCOME_VALID_FLAG"] == "FALSE")
        self.assertEqual(invalid, {"14010020000": 28, "14010070000": 33})
        self.assertEqual(sum(invalid.values()), 61)

    def test_14_exclusion_reason_counts_are_exact(self) -> None:
        reasons = Counter(
            (row["CROP_CODE"], row["EXCLUSION_REASON"])
            for row in self.master if row["OUTCOME_VALID_FLAG"] == "FALSE"
        )
        self.assertEqual(reasons[("14010020000", "ZERO_DENOMINATOR")], 8)
        self.assertEqual(reasons[("14010020000", "INCOMPLETE_CAMPAIGN_NO_SOURCE_ROWS")], 20)
        self.assertEqual(reasons[("14010070000", "ZERO_DENOMINATOR")], 11)
        self.assertEqual(reasons[("14010070000", "INCOMPLETE_CAMPAIGN_NO_SOURCE_ROWS")], 22)
        self.assertEqual(len(reasons), 4)

    def test_15_missing_and_other_invalid_counts_are_zero(self) -> None:
        self.assertEqual(sum(row["MISSING_NUMERATOR_FLAG"] == "TRUE" for row in self.master), 0)
        self.assertEqual(sum(row["MISSING_DENOMINATOR_FLAG"] == "TRUE" for row in self.master), 0)
        self.assertEqual(sum(row["EXCLUSION_REASON"] == "OTHER" for row in self.master), 0)

    def test_16_ledger_contains_only_invalid_rows(self) -> None:
        self.assertEqual(len(self.ledger), 61)
        invalid_keys = {
            (row["CROP_CODE"], row["UBIGEO"], row["CAMPAIGN"])
            for row in self.master if row["OUTCOME_VALID_FLAG"] == "FALSE"
        }
        ledger_keys = {(row["CROP_CODE"], row["UBIGEO"], row["CAMPAIGN"]) for row in self.ledger}
        self.assertEqual(ledger_keys, invalid_keys)

    def test_17_every_invalid_row_is_preserved_once(self) -> None:
        ledger_keys = [(row["CROP_CODE"], row["UBIGEO"], row["CAMPAIGN"]) for row in self.ledger]
        self.assertEqual(len(ledger_keys), len(set(ledger_keys)))
        self.assertEqual(len(ledger_keys), 61)

    def test_18_invalid_yield_is_always_missing(self) -> None:
        invalid = [row for row in self.master if row["OUTCOME_VALID_FLAG"] == "FALSE"]
        self.assertTrue(all(row["TRANSIENT_CAMPAIGN_YIELD_RAW"] == "" for row in invalid))

    def test_19_no_source_rows_have_missing_aggregates(self) -> None:
        rows = [row for row in self.master if row["NO_SOURCE_ROWS_FLAG"] == "TRUE"]
        self.assertEqual(len(rows), 42)
        self.assertTrue(all(row["SOURCE_MONTHS_PRESENT_N"] == "0" for row in rows))
        self.assertTrue(all(row["SOURCE_ROWS_N"] == "0" for row in rows))
        self.assertTrue(all(row["CAMPAIGN_PRODUCCION_TM"] == "" for row in rows))
        self.assertTrue(all(row["CAMPAIGN_COSECHA_HA"] == "" for row in rows))

    def test_20_zero_denominator_rows_are_invalid_and_preserved(self) -> None:
        rows = [row for row in self.master if row["ZERO_DENOMINATOR_FLAG"] == "TRUE"]
        self.assertEqual(len(rows), 19)
        self.assertTrue(all(row["SOURCE_ROWS_N"] != "0" for row in rows))
        self.assertTrue(all(Decimal(row["CAMPAIGN_COSECHA_HA"]) == 0 for row in rows))
        self.assertTrue(all(row["OUTCOME_VALID_FLAG"] == "FALSE" for row in rows))

    def test_21_every_valid_denominator_is_positive(self) -> None:
        valid = [row for row in self.master if row["OUTCOME_VALID_FLAG"] == "TRUE"]
        self.assertTrue(all(Decimal(row["CAMPAIGN_COSECHA_HA"]) > 0 for row in valid))

    def test_22_formula_is_exact_for_every_valid_row(self) -> None:
        valid = [row for row in self.master if row["OUTCOME_VALID_FLAG"] == "TRUE"]
        for row in valid:
            expected = d0.divide_decimal(
                Decimal(row["CAMPAIGN_PRODUCCION_TM"]), Decimal(row["CAMPAIGN_COSECHA_HA"]),
            )
            self.assertEqual(Decimal(row["TRANSIENT_CAMPAIGN_YIELD_RAW"]), expected)

    def test_23_outcome_unit_and_contract_id_are_exact(self) -> None:
        self.assertEqual({row["OUTCOME_UNIT"] for row in self.master}, {"TM_PER_HA"})
        self.assertEqual({row["OUTCOME_CONTRACT_ID"] for row in self.master}, {d0.OUTCOME_CONTRACT_ID})

    def test_24_master_key_is_unique(self) -> None:
        keys = [(row["CROP_CODE"], row["UBIGEO"], row["CAMPAIGN"]) for row in self.master]
        self.assertEqual(len(keys), len(set(keys)))

    def test_25_expected_and_present_month_counts_are_auditable(self) -> None:
        self.assertEqual({row["EXPECTED_MONTHS_N"] for row in self.master}, {"12"})
        self.assertTrue(all(0 <= int(row["SOURCE_MONTHS_PRESENT_N"]) <= 12 for row in self.master))
        self.assertTrue(all(int(row["SOURCE_ROWS_N"]) == int(row["SOURCE_MONTHS_PRESENT_N"]) for row in self.master))

    def test_26_numeric_zero_production_is_not_missing(self) -> None:
        synthetic = {
            "rows": 1, "production_seen": True, "harvest_seen": True,
            "production": Decimal(0), "harvest": Decimal(1),
        }
        self.assertEqual(d0.exclusion_reason(synthetic), "")
        self.assertEqual(d0.divide_decimal(synthetic["production"], synthetic["harvest"]), Decimal(0))

    def test_27_no_silent_missing_to_zero(self) -> None:
        self.assertEqual({row["SILENT_MISSING_TO_ZERO_USED"] for row in self.master}, {"FALSE"})
        no_source = [row for row in self.master if row["NO_SOURCE_ROWS_FLAG"] == "TRUE"]
        self.assertTrue(all(not row["CAMPAIGN_PRODUCCION_TM"] and not row["CAMPAIGN_COSECHA_HA"] for row in no_source))

    def test_28_no_monthly_yield_averaging(self) -> None:
        contract = self.config["outcome_contract"]
        self.assertEqual(contract["formula"], d0.FORMULA)
        self.assertIn("MEAN_MONTHLY_YIELD", contract["forbidden_replacements"])
        self.assertFalse(self.config["firewalls"]["monthly_yield_averaging_used"])

    def test_29_produccion_is_not_divided_by_siembra(self) -> None:
        self.assertFalse(self.config["firewalls"]["produccion_divided_by_siembra_used"])
        self.assertEqual(self.config["outcome_contract"]["denominator"], "SUM(COSECHA within Aug-Jul campaign)")
        self.assertNotIn("SIEMBRA", self.master_columns)

    def test_30_extreme_2017_period_is_retained(self) -> None:
        rows = [row for row in self.master if row["CAMPAIGN_END_YEAR"] == "2017"]
        self.assertEqual(len(rows), 101)
        self.assertGreater(sum(row["OUTCOME_VALID_FLAG"] == "TRUE" for row in rows), 0)
        self.assertFalse(self.config["firewalls"]["extreme_2017_removed"])

    def test_31_extreme_2023_period_is_retained(self) -> None:
        rows = [row for row in self.master if row["CAMPAIGN_END_YEAR"] == "2023"]
        self.assertEqual(len(rows), 101)
        self.assertGreater(sum(row["OUTCOME_VALID_FLAG"] == "TRUE" for row in rows), 0)
        self.assertFalse(self.config["firewalls"]["extreme_2023_removed"])

    def test_32_no_climate_or_exposure_fields(self) -> None:
        forbidden = {field for field in self.master_columns if field.startswith(("RAIN", "TMAX", "TMIN"))}
        self.assertEqual(forbidden, set())
        self.assertFalse(self.config["firewalls"]["climate_exposure_linkage_used"])
        self.assertEqual(self.config["firewalls"]["primary_transient_econometric_exposure"], "NOT_YET_SELECTED")

    def test_33_no_price_or_economic_fields(self) -> None:
        forbidden = {field for field in self.master_columns if "PRICE" in field or "PRECIO" in field or field == "GVP"}
        self.assertEqual(forbidden, set())
        self.assertFalse(self.config["firewalls"]["price_or_monetary_linkage_used"])

    def test_34_no_a1_a2_dependency(self) -> None:
        self.assertFalse(self.config["firewalls"]["a1_a2_filtering_used"])
        self.assertFalse(any("A1" in field or "A2" in field for field in self.master_columns))
        self.assertEqual({row["CROP_CODE"] for row in self.master}, set(d0.CROPS))

    def test_35_no_model_water_or_optimization_outputs(self) -> None:
        result_fields = {"COEFFICIENT", "STANDARD_ERROR", "P_VALUE", "R_SQUARED", "FORECAST", "VAR", "CVAR"}
        self.assertTrue(result_fields.isdisjoint(self.master_columns))
        self.assertFalse(self.config["firewalls"]["model_fitting_executed"])
        self.assertEqual(self.config["firewalls"]["water_model_status"], "NOT_AUTHORIZED")
        self.assertEqual(self.config["firewalls"]["continuous_optimization_status"], "NOT_AUTHORIZED")

    def test_36_config_is_exact_and_complete(self) -> None:
        self.assertEqual(self.config, self.expected_config)
        self.assertEqual(self.config["schema_version"], "1.0.0")
        self.assertEqual(self.config["joint_c0_scientific_base_sha"], d0.JOINT_C0_SCIENTIFIC_BASE_SHA)
        self.assertEqual(self.config["authorized_d0_parent_sha"], d0.AUTHORIZED_D0_PARENT_SHA)
        self.assertEqual(self.config["r0h_hardening_sha"], d0.R0H_HARDENING_SHA)
        self.assertEqual(self.config["d0_scientific_contract_version"], d0.D0_SCIENTIFIC_CONTRACT_VERSION)
        self.assertEqual(self.config["d0_lineage_contract_version"], d0.D0_LINEAGE_CONTRACT_VERSION)
        self.assertEqual(self.config["joint_c0"]["scientific_base_sha"], d0.JOINT_C0_SCIENTIFIC_BASE_SHA)
        self.assertEqual(self.config["lineage_contract"]["current_head_requirement"], "EXACT_AUTHORIZED_D0_PARENT_ONLY")
        self.assertFalse(self.config["lineage_contract"]["r0h_scientific_content_change"])
        self.assertEqual(self.config["raw_source"]["sha256"], d0.RAW_SHA256)
        self.assertEqual(self.config["expected_counts"], {"potential_rows": 707, "valid_rows": 646, "invalid_rows": 61})
        self.assertEqual(self.config["next_gate"], d0.NEXT_GATE)

    def test_37_audit_is_complete_and_all_pass(self) -> None:
        expected_ids = {f"D0-{number:03d}" for number in range(2, 41)}
        expected_ids |= {f"D0-L{number:03d}" for number in range(1, 7)}
        self.assertEqual(len(self.audit), 45)
        self.assertEqual({row["CHECK_ID"] for row in self.audit}, expected_ids)
        self.assertEqual({row["STATUS"] for row in self.audit}, {"PASS"})

    def test_38_report_has_all_required_sections(self) -> None:
        required = [
            "Executive verdict", "Scientific and execution lineage", "Outcome contract", "Source-data semantics",
            "Agricultural campaign calendar", "Rice universe", "MAD universe",
            "Complete 707-row master construction", "Production aggregation", "Harvested-area aggregation",
            "Yield calculation", "Zero denominator treatment", "No-source-row treatment",
            "Missing vs zero firewall", "Exclusion ledger", "Rice reconciliation", "MAD reconciliation",
            "2017/2023 preservation", "No outcome-driven selection", "No climate/exposure linkage",
            "No price/economic linkage", "No model fitting", "Remaining pre-estimation gates",
            "Final D0 verdict",
        ]
        for number, title in enumerate(required, start=1):
            self.assertIn(f"## {number}. {title}", self.report)

    def test_39_config_artifact_hashes_are_exact(self) -> None:
        hashes = self.config["artifact_sha256"]
        self.assertEqual(hashes[d0.MASTER_PATH.relative_to(ROOT).as_posix()], sha256(d0.MASTER_PATH))
        self.assertEqual(hashes[d0.LEDGER_PATH.relative_to(ROOT).as_posix()], sha256(d0.LEDGER_PATH))
        self.assertEqual(hashes[d0.AUDIT_PATH.relative_to(ROOT).as_posix()], sha256(d0.AUDIT_PATH))

    def test_40_outputs_reproduce_in_memory_byte_for_byte(self) -> None:
        second, second_config, second_diagnostics = d0.build_output_bytes()
        self.assertEqual(self.expected_outputs, second)
        self.assertEqual(self.expected_config, second_config)
        self.assertEqual(self.diagnostics, second_diagnostics)
        for path, payload in second.items():
            self.assertEqual(path.read_bytes(), payload, path.name)

    def test_40a_scientific_master_and_ledger_hashes_are_frozen(self) -> None:
        self.assertEqual(sha256(d0.MASTER_PATH), d0.MASTER_SHA256)
        self.assertEqual(sha256(d0.LEDGER_PATH), d0.LEDGER_SHA256)
        self.assertEqual(hashlib.sha256(self.expected_outputs[d0.MASTER_PATH]).hexdigest(), d0.MASTER_SHA256)
        self.assertEqual(hashlib.sha256(self.expected_outputs[d0.LEDGER_PATH]).hexdigest(), d0.LEDGER_SHA256)

    def test_41_default_rebuild_is_deterministic(self) -> None:
        paths = [d0.MASTER_PATH, d0.LEDGER_PATH, d0.AUDIT_PATH, d0.REPORT_PATH, d0.CONFIG_PATH, d0.SCRIPT_PATH, d0.TEST_PATH]
        before = {path: sha256(path) for path in paths}
        result = subprocess.run(
            [sys.executable, "-B", str(d0.SCRIPT_PATH)], cwd=ROOT,
            text=True, encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f"D0_PREFLIGHT={d0.FINAL_STATUS}", result.stdout)
        self.assertEqual({path: sha256(path) for path in paths}, before)

    def test_41a_default_rebuild_does_not_rewrite_scientific_artifacts(self) -> None:
        paths = [d0.MASTER_PATH, d0.LEDGER_PATH]
        before = {path: (sha256(path), path.stat().st_mtime_ns) for path in paths}
        result = subprocess.run(
            [sys.executable, "-B", str(d0.SCRIPT_PATH)], cwd=ROOT,
            text=True, encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual({path: (sha256(path), path.stat().st_mtime_ns) for path in paths}, before)

    def test_42_check_only_is_strictly_read_only(self) -> None:
        paths = [d0.MASTER_PATH, d0.LEDGER_PATH, d0.AUDIT_PATH, d0.REPORT_PATH, d0.CONFIG_PATH, d0.SCRIPT_PATH, d0.TEST_PATH]
        before = {path: sha256(path) for path in paths}
        result = subprocess.run(
            [sys.executable, "-B", str(d0.SCRIPT_PATH), "--check-only"], cwd=ROOT,
            text=True, encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f"D0_PREFLIGHT={d0.FINAL_STATUS}", result.stdout)
        self.assertEqual({path: sha256(path) for path in paths}, before)

    def test_43_all_d0_files_are_utf8_lf_with_one_final_lf(self) -> None:
        for relative in d0.AUTHORIZED_SCOPE:
            payload = (ROOT / relative).read_bytes()
            self.assertFalse(payload.startswith(b"\xef\xbb\xbf"), relative)
            self.assertNotIn(b"\r", payload, relative)
            self.assertTrue(payload.endswith(b"\n"), relative)
            self.assertFalse(payload.endswith(b"\n\n"), relative)
            payload.decode("utf-8")

    def test_44_preflight_passes_all_material_gates(self) -> None:
        lines, diagnostics = d0.run_preflight()
        self.assertIn("D0_LINEAGE_CONTRACT_GATE=PASS", lines)
        self.assertIn("R0H_IDENTITY_GATE=PASS", lines)
        self.assertIn("R0H_DIRECT_PARENT_GATE=PASS", lines)
        self.assertIn("R0H_DIFF_SCOPE_GATE=PASS", lines)
        self.assertIn("R0H_SCIENTIFIC_CONTENT_CHANGE=FALSE", lines)
        self.assertIn("JOINT_C0_IMMUTABILITY_GATE=PASS", lines)
        self.assertIn("D0_SCIENTIFIC_ARTIFACT_IMMUTABILITY_GATE=PASS", lines)
        self.assertIn("PERSISTENT_SCOPE_GATE=PASS", lines)
        self.assertIn("DETERMINISM_GATE=PASS", lines)
        self.assertIn("NO_OUTCOME_DRIVEN_SELECTION_GATE=PASS", lines)
        self.assertIn("NO_EXPOSURE_LINKAGE_GATE=PASS", lines)
        self.assertIn("NO_PRICE_LINKAGE_GATE=PASS", lines)
        self.assertIn("NO_MODEL_FITTING_GATE=PASS", lines)
        self.assertIn("NO_WATER_MODEL_GATE=PASS", lines)
        self.assertIn("NO_OPTIMIZATION_GATE=PASS", lines)
        self.assertIn(f"D0_PREFLIGHT={d0.FINAL_STATUS}", lines)
        self.assertEqual(diagnostics["master_rows"], 707)

    def test_45_script_imports_no_modelling_or_optimization_library(self) -> None:
        tree = ast.parse(d0.SCRIPT_PATH.read_text(encoding="utf-8"))
        imported = {
            alias.name.split(".")[0]
            for node in ast.walk(tree) if isinstance(node, ast.Import)
            for alias in node.names
        } | {
            (node.module or "").split(".")[0]
            for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
        }
        self.assertTrue(imported.isdisjoint({"statsmodels", "sklearn", "linearmodels", "pymc", "cvxpy", "pyomo"}))

    def test_46_source_reader_uses_no_forbidden_scientific_fields(self) -> None:
        source = inspect.getsource(d0.load_source)
        self.assertNotIn('row["SIEMBRA"]', source)
        self.assertNotIn('row["PRECIO"]', source)
        self.assertNotIn('row["PRECIO_CHACRA"]', source)
        self.assertNotIn('row["YIELD_RAW"]', source)
        self.assertNotIn('row["RAIN', source)
        self.assertNotIn('row["TMAX', source)
        self.assertNotIn('row["TMIN', source)

    def test_47_exclusion_flags_are_mutually_consistent(self) -> None:
        flag_by_reason = {
            "ZERO_DENOMINATOR": "ZERO_DENOMINATOR_FLAG",
            "INCOMPLETE_CAMPAIGN_NO_SOURCE_ROWS": "NO_SOURCE_ROWS_FLAG",
            "MISSING_NUMERATOR": "MISSING_NUMERATOR_FLAG",
            "MISSING_DENOMINATOR": "MISSING_DENOMINATOR_FLAG",
        }
        flags = list(flag_by_reason.values())
        for row in self.master:
            true_flags = [flag for flag in flags if row[flag] == "TRUE"]
            if row["OUTCOME_VALID_FLAG"] == "TRUE":
                self.assertEqual(row["EXCLUSION_REASON"], "")
                self.assertEqual(true_flags, [])
            else:
                expected_flag = flag_by_reason.get(row["EXCLUSION_REASON"])
                self.assertEqual(true_flags, [] if expected_flag is None else [expected_flag])

    def test_48_raw_source_identity_is_exact(self) -> None:
        self.assertEqual(sha256(d0.RAW_PATH), d0.RAW_SHA256)
        self.assertEqual(self.config["raw_source"]["path"], d0.RAW_PATH.relative_to(ROOT).as_posix())


if __name__ == "__main__":
    unittest.main()
