"""Regression tests for the C0B3 perennial feasibility package."""

from __future__ import annotations

import ast
import csv
import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import c0b3_perennial_preflight as preflight  # noqa: E402


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=ROOT, text=True, encoding="utf-8",
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    )
    return result.stdout.strip()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class C0B3PerennialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = read_csv(preflight.REGISTRY_PATH)
        cls.adjudications = read_csv(preflight.ADJUDICATION_PATH)
        cls.biology = read_csv(preflight.BIOLOGY_PATH)
        cls.config = json.loads(preflight.CONFIG_PATH.read_text(encoding="utf-8"))

    def test_01_exact_c0b2_freeze_ancestry(self) -> None:
        self.assertEqual(git("branch", "--show-current"), preflight.EXPECTED_BRANCH)
        self.assertEqual(git("rev-parse", "HEAD"), preflight.EXPECTED_HEAD)
        self.assertEqual(git("show", "-s", "--format=%s", "HEAD"), preflight.EXPECTED_SUBJECT)
        result = subprocess.run(
            ["git", "merge-base", "--is-ancestor", preflight.EXPECTED_HEAD, "HEAD"],
            cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        self.assertEqual(result.returncode, 0)

    def test_02_all_c0b2_frozen_files_unchanged(self) -> None:
        for relative, expected in preflight.C0B2_HASHES.items():
            actual = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
            self.assertEqual(actual, expected, relative)
        changed = set(filter(None, git("diff", "--name-only", "--", *preflight.C0B2_HASHES).splitlines()))
        changed |= set(filter(None, git("diff", "--cached", "--name-only", "--", *preflight.C0B2_HASHES).splitlines()))
        self.assertEqual(changed, set())

    def test_03_exact_seven_file_c0b3_scope(self) -> None:
        tracked = set(filter(None, git("diff", "--name-only").splitlines()))
        tracked |= set(filter(None, git("diff", "--cached", "--name-only").splitlines()))
        untracked = {line.replace("\\", "/") for line in git("ls-files", "--others", "--exclude-standard").splitlines() if line}
        self.assertEqual(tracked, set())
        self.assertEqual(untracked, preflight.AUTHORIZED_SCOPE)

    def test_04_three_exact_crop_codes(self) -> None:
        self.assertEqual(len(self.adjudications), 3)
        self.assertEqual({row["CROP_CODE"] for row in self.adjudications}, preflight.TARGET_CODES)
        self.assertFalse({row["CROP_CODE"] for row in self.adjudications} & preflight.TRANSIENT_CODES)

    def test_05_evidence_ids_resolve(self) -> None:
        registry_ids = {row["EVIDENCE_ID"] for row in self.registry}
        self.assertEqual(len(registry_ids), len(self.registry))
        for row in [*self.adjudications, *self.biology]:
            for evidence_id in filter(None, row["EVIDENCE_IDS"].split(";")):
                self.assertIn(evidence_id, registry_ids)

    def test_06_verde_actual_unit_has_independent_official_support(self) -> None:
        verde = [row for row in self.registry if row["RAW_TERM"] == "VERDE_ACTUAL"]
        self.assertEqual(len(verde), 3)
        self.assertTrue(all(row["UNIT"] == "" for row in verde))
        methodology = next(row for row in self.registry if row["EVIDENCE_ID"] == "C0B3-E026")
        self.assertEqual(methodology["UNIT"], "ha")
        self.assertEqual(methodology["SOURCE_URL"], preflight.SIEA_PRIMARY_PDF_URL)
        self.assertIn(f"PRIMARY_PDF_SHA256={preflight.SIEA_PRIMARY_PDF_SHA256}", methodology["NOTES"])
        self.assertIn("APPROVING_NORM=RESOLUCION_MINISTERIAL_N_0035-2013-AG", methodology["NOTES"])
        self.assertEqual(self.config["variable_adjudication"]["VERDE_ACTUAL"]["unit"], "ha")
        self.assertFalse(self.config["firewalls"]["verde_actual_unit_inferred"])
        self.assertTrue(self.config["firewalls"]["verde_actual_unit_certified_by_official_methodology"])

    def test_07_verde_actual_is_certified_installed_stock(self) -> None:
        verde = self.config["variable_adjudication"]["VERDE_ACTUAL"]
        self.assertEqual(verde["source_semantics"], "NUMERIC_MONTHLY_TOTAL_AREA_OF_INSTALLED_CROPS")
        self.assertEqual(verde["status"], "INSTALLED_STOCK_CERTIFIED")
        self.assertTrue(verde["may_be_used_as_numeric_installed_hectares"])
        self.assertTrue(all(row["INSTALLED_STOCK_CANDIDATE"] == "VERDE_ACTUAL" for row in self.adjudications))
        self.assertTrue(all(row["INSTALLED_STOCK_STATUS"] == "OBSERVED_AND_UNIT_CERTIFIED" for row in self.adjudications))
        self.assertTrue(all(row["INSTALLED_STOCK_UNIT"] == "ha" for row in self.adjudications))

    def test_08_cosecha_is_harvest_flow_not_stock(self) -> None:
        cosecha = self.config["variable_adjudication"]["COSECHA"]
        self.assertEqual(cosecha["source_semantics"], "HARVEST_FLOW_AREA")
        self.assertEqual(cosecha["unit"], "ha")
        for row in self.adjudications:
            self.assertEqual(row["PRODUCTIVE_STOCK_STATUS"], "HARVESTED_AREA_PROXY_ONLY")
            self.assertNotEqual(row["INSTALLED_STOCK_CANDIDATE"], row["PRODUCTIVE_STOCK_CANDIDATE"])
        self.assertFalse(cosecha["may_equal_installed_stock_automatically"])
        self.assertFalse(cosecha["may_equal_productive_stock_automatically"])

    def test_09_no_immediate_productivity_assumption(self) -> None:
        self.assertTrue(self.config["frozen_upstream"]["new_establishment_not_immediate_productive_stock"])
        self.assertFalse(self.config["firewalls"]["establishment_equals_immediate_productivity_assumed"])
        self.assertFalse(self.config["biological_parameter_policy"]["first_harvest_equals_economically_productive_stock"])

    def test_10_establishment_and_removal_identity_logic(self) -> None:
        siembra = self.config["variable_adjudication"]["SIEMBRA"]
        self.assertEqual(siembra["source_semantics"], "MONTHLY_GROSS_AREA_INSTALLED_BY_SOWING_OR_TRANSPLANTING")
        self.assertTrue(siembra["gross_establishment_observed"])
        self.assertFalse(siembra["is_total_stock"])
        self.assertFalse(siembra["is_campaign_cumulative_stock"])
        self.assertFalse(siembra["is_net_stock_expansion"])
        self.assertTrue(all(row["ESTABLISHMENT_FLOW_STATUS"] == "DIRECTLY_OBSERVED" for row in self.adjudications))
        self.assertTrue(all(row["STOCK_FLOW_IDENTITY_STATUS"] == "APPROXIMATE_ONLY" for row in self.adjudications))
        self.assertTrue(all(row["REMOVAL_FLOW_STATUS"] == "NOT_OBSERVED" for row in self.adjudications))
        self.assertTrue(all(row["REMOVAL_DERIVABILITY"] == "NOT_DERIVABLE_WITHOUT_ASSUMPTION" for row in self.adjudications))
        residual = self.config["variable_adjudication"]["stock_difference"]
        self.assertTrue(residual["accounting_residual_diagnostic_only"])
        self.assertFalse(residual["may_equal_observed_removal"])
        self.assertFalse(residual["model_authorized"])

    def test_11_maturity_values_require_admissibility(self) -> None:
        quantitative_context = [row for row in self.biology if row["SOURCE_VALUE"]]
        self.assertTrue(quantitative_context)
        for row in self.biology:
            if row["MODEL_VALUE_AUTHORIZED"] == "TRUE":
                self.assertEqual(row["PARAMETER_ADMISSIBILITY"], "MODEL_ADMISSIBLE")
                self.assertTrue(row["EVIDENCE_IDS"])
        self.assertTrue(all(row["MODEL_VALUE_AUTHORIZED"] == "FALSE" for row in self.biology))

    def test_12_no_midpoint_inference(self) -> None:
        self.assertFalse(self.config["biological_parameter_policy"]["midpoint_inference_allowed"])
        for row in self.biology:
            self.assertEqual(row["AUTHORIZED_VALUE"], "")
            self.assertEqual(row["AUTHORIZED_LOWER"], "")
            self.assertEqual(row["AUTHORIZED_UPPER"], "")

    def test_13_no_cultivar_overgeneralization(self) -> None:
        self.assertFalse(self.config["biological_parameter_policy"]["cultivar_or_system_generalization_allowed"])
        mango_contexts = [row["CULTIVAR_OR_SYSTEM"] for row in self.registry if row["CROP_STD"] == "MANGO"]
        self.assertTrue(any("Kent" in context for context in mango_contexts))
        mango_lag = next(row for row in self.biology if row["PARAMETER_CONCEPT"] == "FIRST_PRODUCTION_AFTER_GRAFT")
        self.assertEqual(mango_lag["PARAMETER_ADMISSIBILITY"], "CONTEXT_ONLY")

    def test_14_banana_has_separate_ontology(self) -> None:
        banana = next(row for row in self.adjudications if row["CROP_STD"] == "PLATANOS Y BANANAS")
        self.assertEqual(banana["CROP_CLASS"], "SEMIPERMANENT_CONTINUOUS_STAND_WITH_MOTHER_SUCKER_SUCCESSION")
        self.assertEqual(banana["INSTALLED_STOCK_STATE"], "CONTINUOUS_SEMIPERMANENT_INSTALLED_STAND_AREA")
        self.assertEqual(banana["ESTABLISHMENT_FLOW_STATUS"], "DIRECTLY_OBSERVED")
        self.assertIn("NOT_INTERNAL_SUCKER_SUCCESSION", banana["ESTABLISHMENT_FLOW_QUALIFICATION"])
        self.assertNotIn("WOODY", banana["CROP_CLASS"])
        ontology = self.config["banana_state_ontology"]
        self.assertEqual(ontology["status"], "CONTINUOUS_MOTHER_DAUGHTER_GRANDDAUGHTER_STAND")
        self.assertEqual(ontology["woody_perennial_ontology"], "REJECTED")
        self.assertFalse(ontology["internal_sucker_succession_is_new_district_area_establishment"])
        self.assertFalse(self.config["firewalls"]["banana_forced_to_woody_orchard_ontology"])

    def test_15_crop_specific_p2_adjudication_is_deterministic(self) -> None:
        self.assertTrue(all(row["P2_OPERATIONAL_STATUS"] == "NOT_SUPPORTED_USE_P3" for row in self.adjudications))
        self.assertTrue(all(row["LAG_STATUS"] == "CONTEXT_ONLY" for row in self.adjudications))
        self.assertTrue(all(row["NEAR_TERM_ESTABLISHMENT_OUTPUT_RELEVANCE"] == "UNRESOLVED" for row in self.adjudications))
        self.assertEqual(self.config["decision_horizon"]["status"], "QUALITATIVELY_NEAR_TERM_ONLY")
        self.assertFalse(self.config["decision_horizon"]["numeric_horizon_frozen"])

    def test_16_p3_fallback_is_deterministic(self) -> None:
        self.assertTrue(all(row["P3_FALLBACK_REQUIRED"] == "TRUE" for row in self.adjudications))
        self.assertEqual(set(self.config["p3_required_crops"]), preflight.TARGET_NAMES)
        self.assertEqual(self.config["architecture_status"]["ARCH_F_SET3_STATUS"], "REQUIRED")
        p3 = self.config["p3_interpretation"]
        self.assertEqual(p3["resolution"], "P3_FIXED_STOCK_NEAR_TERM_HORIZON")
        self.assertEqual(p3["perennial_decision_endogeneity"], "EXOGENOUS_FIXED_WITHIN_CURRENT_NEAR_TERM_ARCHITECTURE")
        self.assertEqual(p3["future_time_varying_exogenous_perennial_path_status"], "NOT_YET_AUTHORIZED")
        self.assertEqual(p3["perennial_installed_stocks"], "OBSERVED_BUT_EXOGENOUS_TO_NEAR_TERM_OPTIMIZER")
        self.assertTrue(p3["historical_characterization_authorized"])
        self.assertTrue(p3["district_crop_baseline_measurement_authorized"])
        self.assertTrue(p3["baseline_initialization_authorized"])
        self.assertTrue(p3["descriptive_historical_stock_trajectories_authorized"])
        self.assertFalse(p3["historical_observed_variation_authorizes_future_modeled_variation"])
        self.assertFalse(p3["scenario_specific_perennial_area_reallocation_authorized"])
        self.assertFalse(p3["optimizer_chosen_perennial_adjustment_authorized"])
        self.assertFalse(p3["endogenous_perennial_establishment_authorized"])
        self.assertFalse(p3["endogenous_perennial_removal_authorized"])
        self.assertFalse(p3["exogenous_means_unobserved"])
        self.assertFalse(p3["arbitrary_optimizer_area_adjustment_authorized"])

    def test_17_architecture_matches_crop_results(self) -> None:
        self.assertEqual(self.config["architecture_adjudication"], preflight.ARCHITECTURE)
        self.assertEqual(self.config["architecture_status"]["ARCH_E_SET2_STATUS"], "NOT_SUPPORTED")
        self.assertTrue(self.config["p2_failure_independent_of_current_horizon"])
        self.assertTrue(all(row["P2_OPERATIONAL_STATUS"] == "NOT_SUPPORTED_USE_P3" for row in self.adjudications))
        rationale = self.config["architecture_rationale"]
        self.assertIn("INSTALLED_STOCK_AND_GROSS_ESTABLISHMENT_ARE_OBSERVED", rationale)
        self.assertIn("PRODUCTIVE_STATE_REMOVAL_REPLACEMENT", rationale)

    def test_18_no_optimizer_artifacts(self) -> None:
        self.assertFalse(self.config["authorizations"]["optimizer"])
        untracked = git("ls-files", "--others", "--exclude-standard").lower()
        self.assertNotIn("optimization", untracked)
        modules = set()
        for path in (preflight.SCRIPT_PATH, preflight.TEST_PATH):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    modules.update(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    modules.add(node.module)
        self.assertTrue(modules.isdisjoint({"pulp", "cvxpy", "pyomo", "scipy.optimize"}))

    def test_19_no_water_hard_constraint_artifacts(self) -> None:
        self.assertFalse(self.config["frozen_upstream"]["water_hard_constraint_authorized"])
        self.assertFalse(self.config["authorizations"]["water_model"])
        self.assertFalse(self.config["authorizations"]["water_hard_constraint"])

    def test_20_report_has_all_required_sections(self) -> None:
        report = preflight.REPORT_PATH.read_text(encoding="utf-8")
        for number in range(1, 22):
            self.assertIn(f"## {number}.", report)

    def test_21_preflight_passes(self) -> None:
        self.assertEqual(preflight.run_preflight(), [])

    def test_22_crop_specific_installed_stock_states(self) -> None:
        by_crop = {row["CROP_STD"]: row for row in self.adjudications}
        self.assertEqual(by_crop["MANGO"]["INSTALLED_STOCK_STATE"], "INSTALLED_PERENNIAL_STOCK_AREA")
        self.assertEqual(by_crop["LIMON SUTIL"]["INSTALLED_STOCK_STATE"], "INSTALLED_PERENNIAL_STOCK_AREA")
        self.assertEqual(
            by_crop["PLATANOS Y BANANAS"]["INSTALLED_STOCK_STATE"],
            "CONTINUOUS_SEMIPERMANENT_INSTALLED_STAND_AREA",
        )
        self.assertTrue(all(row["INSTALLED_STOCK_STATUS"] == "OBSERVED_AND_UNIT_CERTIFIED" for row in by_crop.values()))

    def test_23_exact_official_semantic_provenance(self) -> None:
        provenance = self.config["official_source_provenance"]
        self.assertEqual(
            provenance["data_dictionary"]["sha256"],
            "9df8aedf987a7a882d265ffc629d105f8058a5208738d5dcd1b213b30d347ce0",
        )
        self.assertEqual(
            provenance["metadata"]["sha256"],
            "a66ede624b8d2f502df65620c84233dd04a9ebcc29ae9969c38e2272ec812ea7",
        )
        siea = provenance["siea_methodology"]
        self.assertEqual(
            siea["evidence_domain"],
            "VARIABLE_AND_STATE_SEMANTICS_ONLY_NOT_BIOLOGICAL_PARAMETER",
        )
        self.assertEqual(siea["primary_source_authority"], "MIDAGRI_SIEA")
        self.assertEqual(
            siea["primary_source_title"],
            "Lineamientos Metodológicos de la Actividad Estadística del Sistema Integrado de Estadística Agraria - SIEA",
        )
        self.assertEqual(siea["primary_requested_url"], preflight.SIEA_PRIMARY_PDF_URL)
        self.assertTrue(siea["primary_final_resolved_url"].startswith("https://siea.midagri.gob.pe/"))
        self.assertEqual(siea["primary_http_status"], "HTTP_200_APPLICATION_PDF")
        self.assertEqual(siea["primary_pdf_sha256"], preflight.SIEA_PRIMARY_PDF_SHA256)
        self.assertRegex(siea["primary_pdf_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(siea["primary_pdf_pages"], 491)

    def test_24_identity_diagnostics_are_exact_and_nonparametric(self) -> None:
        diagnostics = self.config["empirical_identity_diagnostics"]
        expected = {
            "MANGO": (4111, 4111, 0, 4076, 3, 32, -100, 40, -0.155254),
            "LIMON SUTIL": (4730, 4730, 0, 4699, 0, 31, -683, 0, -0.274841),
            "PLATANOS Y BANANAS": (5576, 5574, 2, 5481, 2, 91, -470, 50, -0.751525),
        }
        keys = ("total_candidate_pairs", "nonmissing_analyzable_pairs", "missing_pairs", "exact_identity_pairs", "positive", "negative", "minimum", "maximum", "mean")
        for crop, values in expected.items():
            self.assertEqual(tuple(diagnostics[crop][key] for key in keys), values)
            self.assertEqual(
                diagnostics[crop]["total_candidate_pairs"],
                diagnostics[crop]["nonmissing_analyzable_pairs"] + diagnostics[crop]["missing_pairs"],
            )
            self.assertEqual(
                diagnostics[crop]["nonmissing_analyzable_pairs"],
                diagnostics[crop]["exact_identity_pairs"] + diagnostics[crop]["positive"] + diagnostics[crop]["negative"],
            )
        self.assertEqual(
            diagnostics["admissibility"],
            "ACCOUNTING_RESIDUAL_DIAGNOSTIC_ONLY_NOT_MODEL_AUTHORIZED",
        )

    def test_25_removal_is_neither_derived_nor_zero(self) -> None:
        removal = self.config["removal_adjudication"]
        self.assertEqual(removal["published_extract_status"], "NOT_OBSERVED_IN_PUBLISHED_EXTRACT")
        self.assertEqual(removal["derivability"], "NOT_DERIVABLE_WITHOUT_ASSUMPTION")
        self.assertFalse(removal["c0b1_requires_freely_endogenous_removal"])
        self.assertTrue(removal["observed_or_externally_fixed_removal_could_qualify"])
        self.assertFalse(removal["zero_removal_allowed"])

    def test_26_biological_rows_remain_context_only(self) -> None:
        self.assertEqual(len(self.biology), 9)
        self.assertTrue(all(row["PARAMETER_ADMISSIBILITY"] == "CONTEXT_ONLY" for row in self.biology))
        self.assertTrue(all(row["MODEL_VALUE_AUTHORIZED"] == "FALSE" for row in self.biology))
        self.assertEqual(self.config["biological_parameter_policy"]["model_authorized_values"], 0)

    def test_27_p2_matrix_fails_after_corrected_passes(self) -> None:
        matrix = self.config["p2_necessary_condition_matrix"]
        for crop in preflight.TARGET_NAMES:
            self.assertEqual(matrix[crop]["installed_stock"], "PASS")
            self.assertEqual(matrix[crop]["unit"], "PASS")
            self.assertEqual(matrix[crop]["productive_stock"], "FAIL_PROXY_ONLY")
            self.assertEqual(matrix[crop]["removal_replacement"], "FAIL_NOT_OBSERVED")
            self.assertEqual(matrix[crop]["model_admissible_productivity_lag"], "FAIL_CONTEXT_ONLY")
            self.assertEqual(matrix[crop]["numeric_horizon_compatibility"], "UNRESOLVED")
            self.assertEqual(matrix[crop]["p2"], "NOT_SUPPORTED_USE_P3")
        self.assertEqual(matrix["PLATANOS Y BANANAS"]["gross_establishment"], "PASS_WITH_BIOLOGICAL_QUALIFICATION")

    def test_28_report_records_falsification_history(self) -> None:
        report = preflight.REPORT_PATH.read_text(encoding="utf-8")
        self.assertIn("initial C0B3 had underclassified `VERDE_ACTUAL` and `SIEMBRA`", report)
        self.assertIn("Exogenous does not mean unobserved", report)
        self.assertIn("Architecture F survives for the stronger reason", report)
        self.assertIn("| P2 | FAIL | FAIL | FAIL |", report)
        self.assertIn("| P3 | REQUIRED | REQUIRED | REQUIRED |", report)

    def test_29_report_freezes_exact_p3_semantics(self) -> None:
        report = preflight.REPORT_PATH.read_text(encoding="utf-8")
        self.assertIn("P3_RESOLUTION=P3_FIXED_STOCK_NEAR_TERM_HORIZON", report)
        self.assertIn("PERENNIAL_DECISION_ENDOGENEITY=EXOGENOUS_FIXED_WITHIN_CURRENT_NEAR_TERM_ARCHITECTURE", report)
        self.assertIn("FUTURE_TIME_VARYING_EXOGENOUS_PERENNIAL_PATH_STATUS=NOT_YET_AUTHORIZED", report)
        self.assertIn("P2_FAILURE_INDEPENDENT_OF_CURRENT_HORIZON=TRUE", report)

    def test_30_banana_registry_uses_explicit_pair_denominators(self) -> None:
        banana = next(row for row in self.registry if row["EVIDENCE_ID"] == "C0B3-E013")
        self.assertIn("total_candidate_pairs=5576", banana["EXACT_FINDING"])
        self.assertIn("nonmissing_analyzable_pairs=5574", banana["EXACT_FINDING"])
        self.assertIn("missing_pairs=2", banana["EXACT_FINDING"])
        self.assertIn("exact_identity_pairs=5481", banana["EXACT_FINDING"])
        self.assertNotIn("N=5574", banana["EXACT_FINDING"])

    def test_31_final_status_is_notarial_audit_ready(self) -> None:
        self.assertEqual(self.config["final_status"], "PASS_FOR_FINAL_NOTARIAL_C0B3_FREEZE_AUDIT")

    def test_32_private_mirror_is_not_canonical(self) -> None:
        siea = self.config["official_source_provenance"]["siea_methodology"]
        historical = siea["historical_official_locator"]
        self.assertEqual(historical["requested_url"], preflight.SIEA_HISTORICAL_URL)
        self.assertEqual(historical["status"], "OBSOLETE_REDIRECTS_TO_OFFICIAL_SIEA_HOME_HTML_NOT_PDF")
        self.assertFalse(historical["canonical_primary_source"])
        mirror = siea["auxiliary_private_mirror"]
        self.assertEqual(mirror["status"], preflight.SIEA_PRIVATE_MIRROR_STATUS)
        self.assertTrue(mirror["not_primary_source"])
        self.assertTrue(mirror["no_scientific_claim_depends_solely_on_copy"])
        self.assertNotIn("normaslegalesonline.pe", siea["primary_requested_url"])
        official_rows = [row for row in self.registry if row["EVIDENCE_ID"] in {"C0B3-E026", "C0B3-E027", "C0B3-E028", "C0B3-E029"}]
        self.assertTrue(all(row["SOURCE_URL"] == preflight.SIEA_PRIMARY_PDF_URL for row in official_rows))

    def test_33_legal_and_methodological_roles_are_distinct(self) -> None:
        siea = self.config["official_source_provenance"]["siea_methodology"]
        legal = siea["legal_approval_source"]
        definitions = siea["methodological_definition_source"]
        rm_0194 = siea["rm_0194_2016"]
        self.assertEqual(legal["document_role"], "LEGAL_APPROVAL_SOURCE")
        self.assertEqual(legal["requested_url"], preflight.SIEA_LEGAL_PDF_URL)
        self.assertEqual(legal["pdf_sha256"], preflight.SIEA_LEGAL_PDF_SHA256)
        self.assertRegex(legal["pdf_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(legal["approving_norm"], "RESOLUCION_MINISTERIAL_N_0035-2013-AG")
        self.assertEqual(legal["approving_norm_date"], "2013-02-01")
        self.assertEqual(legal["approving_norm_role"], "APPROVES_SIEA_METHODOLOGICAL_GUIDELINES")
        self.assertEqual(definitions["document_role"], "METHODOLOGICAL_DEFINITION_SOURCE")
        self.assertEqual(definitions["pages"], "61-65")
        self.assertTrue(definitions["definitions_verified_in_primary_pdf"])
        self.assertEqual(rm_0194["role"], preflight.RM_0194_2016_ROLE)
        self.assertFalse(rm_0194["is_original_guidelines_approving_norm"])
        self.assertFalse(rm_0194["is_primary_methodological_source"])
        self.assertEqual(rm_0194["authentication_source_sha256"], preflight.RM_0194_ROLE_SOURCE_SHA256)
        self.assertEqual(siea["legal_vs_methodological_source_firewall"], "PASS_DISTINCT_SOURCE_ROLES_RECORDED")


if __name__ == "__main__":
    unittest.main()
