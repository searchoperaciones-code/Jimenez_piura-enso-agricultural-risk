from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config/scientific_identity/scientific_identity_v1.json"
REPORT_PATH = ROOT / "outputs/scientific_identity/S1_SCIENTIFIC_IDENTITY_REPORT.md"
CLAIMS_PATH = ROOT / "outputs/scientific_identity/S1_CLAIM_MATRIX.csv"
CROSSWALK_PATH = ROOT / "outputs/scientific_identity/S1_RQ_OBJECTIVE_CROSSWALK.csv"
TEST_PATH = ROOT / "tests/test_scientific_identity_v1.py"

D0_SHA = "1598a09c9a871d81834164d7ee4383e25988d8a5"
R0H_SHA = "a50702dbf6a2dc0037e28e0b5ae4ddd8a9c182e5"
JOINT_C0_SHA = "fca5d6e519cdff764d1ca53791ae1829ef29aa00"
EXPECTED_BRANCH = "phase/d0-transient-campaign-outcome-master-v1"
EXPECTED_SCOPE = {
    "config/scientific_identity/scientific_identity_v1.json",
    "outputs/scientific_identity/S1_SCIENTIFIC_IDENTITY_REPORT.md",
    "outputs/scientific_identity/S1_CLAIM_MATRIX.csv",
    "outputs/scientific_identity/S1_RQ_OBJECTIVE_CROSSWALK.csv",
    "tests/test_scientific_identity_v1.py",
}
ALLOWED_CLAIM_STATUSES = {
    "AUTHORIZED_NOW", "AUTHORIZED_IF_FUTURE_GATE_PASSES", "NOT_AUTHORIZED", "ABANDONED",
}


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


class ScientificIdentityV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        cls.report = REPORT_PATH.read_text(encoding="utf-8")
        cls.claim_columns, cls.claims = read_csv(CLAIMS_PATH)
        cls.crosswalk_columns, cls.crosswalk = read_csv(CROSSWALK_PATH)

    def test_01_d0_freeze_identity_and_ancestry_are_exact(self) -> None:
        self.assertEqual(git("branch", "--show-current"), EXPECTED_BRANCH)
        self.assertEqual(git("rev-parse", "HEAD"), D0_SHA)
        self.assertEqual(git("rev-parse", "origin/phase/d0-transient-campaign-outcome-master-v1"), D0_SHA)
        self.assertEqual(git("rev-parse", "d0-transient-outcome-v1-freeze^{}"), D0_SHA)
        self.assertEqual(git("rev-parse", "HEAD^"), R0H_SHA)
        self.assertEqual(git("rev-parse", "HEAD^^"), JOINT_C0_SHA)

    def test_02_exact_five_file_candidate_scope(self) -> None:
        self.assertEqual(set(filter(None, git("diff", "--name-only").splitlines())), set())
        self.assertEqual(set(filter(None, git("diff", "--cached", "--name-only").splitlines())), set())
        untracked = {
            line.replace("\\", "/")
            for line in git("ls-files", "--others", "--exclude-standard").splitlines()
            if line
        }
        self.assertEqual(untracked, EXPECTED_SCOPE)

    def test_03_configuration_status_and_freeze_policy_are_exact(self) -> None:
        self.assertEqual(self.config["schema_version"], "1.0.0")
        self.assertEqual(self.config["phase"], "S1_SCIENTIFIC_IDENTITY_REFRAMING_MASTER_V1")
        self.assertEqual(self.config["status"], "PASS_REFINED_CANDIDATE_FOR_DIRECTOR_FREEZE_DECISION")
        self.assertFalse(self.config["freeze_authorized"])

    def test_04_historical_identity_is_not_silently_rewritten(self) -> None:
        historical = self.config["historical_working_identity"]
        self.assertEqual(historical["source_commit"], "e4710b1429ed54c557e6c0a88212a24a6fdd7d47")
        self.assertEqual(historical["source_path"], "README.md")
        self.assertEqual(historical["evidence_classification"], "TITLE_VERBATIM_OTHER_ELEMENTS_RECONSTRUCTED_NOT_VERBATIM")
        self.assertEqual(
            historical["title_verbatim"],
            "Optimizing Agricultural Economic Value under El Niño 2026–2027 Risk in Piura, Peru: District-Level Climate-Yield Estimation and Spatial Mean-CVaR Crop Allocation",
        )

    def test_05_exact_two_layer_architecture(self) -> None:
        architecture = self.config["scientific_architecture"]
        self.assertEqual(architecture["name"], "TWO_LAYER_FIVE_CROP_CHARACTERIZATION_PLUS_RICE_MAD_REFERENCE_STRESS_TEST")
        self.assertEqual(set(architecture) & {"layer_1", "layer_2"}, {"layer_1", "layer_2"})
        self.assertEqual(architecture["cross_layer_rule"], "LINKED_BUT_NOT_MERGED_NO_FIVE_CROP_A1_A2_AGGREGATION")

    def test_06_layer_1_has_exactly_five_crops(self) -> None:
        self.assertEqual(
            self.config["scientific_architecture"]["layer_1"]["crop_codes"],
            ["14010020000", "14010070000", "13010210000", "13010170102", "15010040000"],
        )
        self.assertEqual(len(self.config["scientific_architecture"]["layer_1"]["crop_names"]), 5)
        self.assertFalse(self.config["scientific_architecture"]["layer_1"]["portfolio_interpretation_authorized"])

    def test_07_layer_2_scope_is_exact(self) -> None:
        layer = self.config["scientific_architecture"]["layer_2"]
        self.assertEqual(layer["crop_codes"], ["14010020000", "14010070000"])
        self.assertEqual(layer["reference_configuration_ids"], ["C0B5-A2020-2021", "C0B5-A2023-2024"])
        self.assertEqual(layer["common_districts_n"], 13)
        self.assertIn("NOT_OPTIMAL", layer["reference_configuration_interpretation"])
        self.assertIn("NOT_RECOMMENDED", layer["reference_configuration_interpretation"])

    def test_08_temporal_architecture_preserves_distinct_contracts(self) -> None:
        temporal = self.config["temporal_outcome_architecture"]
        self.assertEqual(len(temporal["transient"]["campaigns"]), 7)
        self.assertEqual(temporal["transient"]["rice_usable_outcomes_n"], 294)
        self.assertEqual(temporal["transient"]["mad_usable_outcomes_n"], 352)
        self.assertEqual(temporal["perennial"]["time_basis"], "FROZEN_CROP_SPECIFIC_CALENDAR_YEAR_CONTRACTS")

    def test_09_d0_master_and_ledger_remain_frozen(self) -> None:
        master = ROOT / "data/processed/outcomes/transient_campaign_outcomes_master.csv"
        ledger = ROOT / "outputs/outcome/D0_TRANSIENT_OUTCOME_EXCLUSION_LEDGER.csv"
        self.assertEqual(sha256(master), "9cae62fb1417fa41274f6d504515571abd428b71fecaa0d138d3b786aa538760")
        self.assertEqual(sha256(ledger), "6f7efe29c49b6a1edfaf47743f0b10639a9f56995f742e7513046aff63e814d8")
        _, rows = read_csv(master)
        self.assertEqual(len(rows), 707)
        self.assertEqual(sum(row["OUTCOME_VALID_FLAG"] == "TRUE" for row in rows), 646)

    def test_10_no_optimization_or_recommendation_is_authorized(self) -> None:
        firewalls = self.config["firewalls"]
        self.assertFalse(firewalls["continuous_optimization_authorized"])
        self.assertFalse(firewalls["recommended_allocation_authorized"])
        current = self.config["current_authorized_identity"]
        text = json.dumps(current, ensure_ascii=False).lower()
        for forbidden in ("optimize crop", "optimal crop", "maximize profit", "recommended allocation"):
            self.assertNotIn(forbidden, text)

    def test_11_causal_ceiling_is_exact(self) -> None:
        self.assertEqual(self.config["identification_ceiling"], "EMPIRICAL_ASSOCIATION_CLIMATE_RESPONSE_ONLY")
        self.assertFalse(self.config["firewalls"]["causal_claim_authorized"])
        self.assertIn("associated with", self.config["current_authorized_identity"]["primary_research_question"].lower())

    def test_12_five_crop_a1_a2_is_forbidden(self) -> None:
        self.assertFalse(self.config["firewalls"]["five_crop_a1_a2_authorized"])
        self.assertEqual(self.config["scientific_architecture"]["layer_2"]["crop_codes"], ["14010020000", "14010070000"])
        claim = next(row for row in self.claims if row["CLAIM_ID"] == "S1-C09")
        self.assertEqual(claim["STATUS"], "NOT_AUTHORIZED")

    def test_13_economic_and_risk_statuses_are_truthful(self) -> None:
        economic = self.config["economic_dimension"]
        risk = self.config["risk_dimension"]
        self.assertTrue(economic["gross_production_value_status"].startswith("NOT_YET_BUILT"))
        self.assertEqual(economic["profit_status"], "NOT_AUTHORIZED_NO_COST_OR_MARGIN_EVIDENCE")
        self.assertEqual(risk["cvar_current_status"], "NOT_AUTHORIZED_YET")
        self.assertEqual(risk["continuous_mean_cvar_optimization_status"], "ABANDONED_NOT_AUTHORIZED")

    def test_14_no_exposure_scenario_model_or_result_has_been_selected(self) -> None:
        firewalls = self.config["firewalls"]
        self.assertFalse(firewalls["primary_transient_exposure_selected"])
        self.assertFalse(firewalls["exposure_performance_used"])
        self.assertFalse(firewalls["econometric_estimation_executed"])
        self.assertFalse(firewalls["model_fit_used"])
        self.assertFalse(firewalls["enso_scenario_result_used"])
        self.assertFalse(firewalls["a1_a2_results_used"])
        self.assertFalse(firewalls["cvar_result_used"])

    def test_15_five_titles_have_complete_scores_and_one_recommendation(self) -> None:
        titles = self.config["title_candidates"]
        expected_scores = {
            "scientific_accuracy", "q1_positioning", "methodological_specificity",
            "readability", "future_compatibility", "overclaim_risk",
        }
        self.assertEqual(len(titles), 5)
        self.assertEqual(sum(item["selection_status"] == "WORKING_TITLE_V2_FOR_DESIGN" for item in titles), 1)
        for item in titles:
            self.assertEqual(set(item["scores"]), expected_scores)
            self.assertTrue(all(0 <= score <= 10 for score in item["scores"].values()))
        selected = next(item["text"] for item in titles if item["selection_status"] == "WORKING_TITLE_V2_FOR_DESIGN")
        self.assertEqual(selected, self.config["current_authorized_identity"]["working_title_v2"])
        self.assertEqual(self.config["current_authorized_identity"]["final_publication_title_status"], "PENDING_POST_RESULTS")

    def test_16_rq_objective_crosswalk_is_complete(self) -> None:
        self.assertEqual(
            self.crosswalk_columns,
            ["RQ_ID", "RQ_TEXT", "OBJECTIVE_ID", "OBJECTIVE_TEXT", "ANALYTICAL_LAYER", "CROP_SCOPE", "TEMPORAL_SCOPE", "CURRENT_STATUS", "REQUIRED_FUTURE_GATE", "CAUSAL_CEILING", "TESTABILITY_CRITERION"],
        )
        self.assertEqual({row["RQ_ID"] for row in self.crosswalk}, {"PRQ", "SRQ1", "SRQ2", "SRQ3", "SRQ4"})
        self.assertEqual({row["OBJECTIVE_ID"] for row in self.crosswalk}, {"GO", "SO1", "SO2", "SO3", "SO4"})
        current = self.config["current_authorized_identity"]
        self.assertEqual(next(row["RQ_TEXT"] for row in self.crosswalk if row["RQ_ID"] == "PRQ"), current["primary_research_question"])
        self.assertEqual(next(row["OBJECTIVE_TEXT"] for row in self.crosswalk if row["OBJECTIVE_ID"] == "GO"), current["general_objective"])
        subquestions = {item["rq_id"]: item["text"] for item in current["subquestions"]}
        objectives = {item["objective_id"]: item["text"] for item in current["specific_objectives"]}
        self.assertEqual(
            {row["RQ_ID"]: row["RQ_TEXT"] for row in self.crosswalk if row["RQ_ID"] != "PRQ"},
            subquestions,
        )
        self.assertEqual(
            {row["OBJECTIVE_ID"]: row["OBJECTIVE_TEXT"] for row in self.crosswalk if row["OBJECTIVE_ID"] != "GO"},
            objectives,
        )
        self.assertEqual({row["CAUSAL_CEILING"] for row in self.crosswalk}, {"EMPIRICAL_ASSOCIATION_CLIMATE_RESPONSE_ONLY"})

    def test_17_claim_matrix_schema_statuses_and_coverage_are_exact(self) -> None:
        self.assertEqual(self.claim_columns, ["CLAIM_ID", "CLAIM", "STATUS", "EVIDENCE_OR_GATE", "ALLOWED_WORDING", "FORBIDDEN_WORDING"])
        self.assertEqual({row["STATUS"] for row in self.claims}, ALLOWED_CLAIM_STATUSES)
        self.assertEqual({row["CLAIM_ID"] for row in self.claims}, {f"S1-C{number:02d}" for number in range(1, 19)})
        self.assertTrue(all(row["EVIDENCE_OR_GATE"] and row["ALLOWED_WORDING"] and row["FORBIDDEN_WORDING"] for row in self.claims))

    def test_18_hypothesis_policy_avoids_generic_directional_claims(self) -> None:
        policy = self.config["hypothesis_policy"]
        self.assertEqual(policy["architecture"], "CROP_SPECIFIC_MECHANISM_INFORMED_EXPECTATIONS")
        self.assertFalse(policy["formal_universal_directional_hypothesis"])
        self.assertIn("crop", policy["prespecification_rule"].lower())
        self.assertIn("phenological stage", policy["prespecification_rule"].lower())

    def test_19_q1_positioning_distinguishes_potential_from_readiness(self) -> None:
        q1 = self.config["q1_positioning"]
        self.assertEqual(set(q1["scores"]), {
            "research_relevance", "data_contribution", "reproducibility", "climate_exposure_design",
            "phenology_integration", "econometric_potential", "enso_risk_relevance", "decision_relevance",
            "methodological_novelty", "overall_q1_potential",
        })
        self.assertGreater(q1["architectural_q1_potential"], q1["current_empirical_q1_readiness"])
        self.assertTrue(all(0 <= score <= 10 for score in q1["scores"].values()))

    def test_20_failure_modes_are_complete_and_actionable(self) -> None:
        modes = self.config["failure_modes"]
        self.assertEqual(len(modes), 10)
        self.assertEqual(len({item["failure_mode"] for item in modes}), 10)
        self.assertTrue(all(item["preventive_design_rule"] for item in modes))

    def test_21_pre_estimation_commitment_is_exact(self) -> None:
        self.assertEqual(self.config["pre_estimation_commitment"], [
            "NO COEFFICIENTS OBSERVED FOR THIS DECISION",
            "NO MODEL FIT USED",
            "NO EXPOSURE PERFORMANCE USED",
            "NO ENSO SCENARIO RESULT USED",
            "NO A1/A2 RESULT USED",
            "NO CVAR RESULT USED",
        ])

    def test_22_report_contains_all_design_sections_and_commitments(self) -> None:
        required = [
            "Historical working identity", "Current scientific problem", "Current two-layer architecture",
            "Identification ceiling", "ENSO role", "Primary research-question candidates",
            "Recommended primary research question", "General objective", "Specific objectives",
            "Hypothesis policy", "Working-title candidates", "Working title v2 for design",
            "Contribution architecture", "Novelty firewall", "Claim architecture", "Paper is and is not",
            "Q1 positioning assessment", "Principal failure modes and preventive rules",
            "Pre-estimation commitment", "Exact next gate",
        ]
        for title in required:
            self.assertIn(title, self.report)
        for commitment in self.config["pre_estimation_commitment"]:
            self.assertIn(commitment, self.report)

    def test_23_all_candidate_files_are_utf8_lf_with_one_final_lf(self) -> None:
        for relative in EXPECTED_SCOPE:
            payload = (ROOT / relative).read_bytes()
            self.assertFalse(payload.startswith(b"\xef\xbb\xbf"), relative)
            self.assertNotIn(b"\r", payload, relative)
            self.assertTrue(payload.endswith(b"\n"), relative)
            self.assertFalse(payload.endswith(b"\n\n"), relative)
            payload.decode("utf-8")

    def test_24_next_gate_is_exposure_adjudication_not_estimation(self) -> None:
        self.assertEqual(self.config["next_authorized_gate"], "PRIMARY_TRANSIENT_ECONOMETRIC_EXPOSURE_ADJUDICATION_V1")
        self.assertFalse(self.config["firewalls"]["econometric_estimation_executed"])

    def test_25_primary_rq_does_not_make_gvp_mandatory(self) -> None:
        primary_rq = self.config["current_authorized_identity"]["primary_research_question"].lower()
        for forbidden in ("gross-production", "gross production", "gvp", "economic"):
            self.assertNotIn(forbidden, primary_rq)

    def test_26_primary_rq_uses_focal_not_major(self) -> None:
        primary_rq = self.config["current_authorized_identity"]["primary_research_question"].lower()
        self.assertIn("five focal crops", primary_rq)
        self.assertNotIn("major crops", primary_rq)

    def test_27_selected_title_uses_associations_not_responses(self) -> None:
        title = self.config["current_authorized_identity"]["working_title_v2"]
        self.assertIn("Climate–Yield Associations", title)
        self.assertNotIn("Responses", title)

    def test_28_selected_title_is_explicitly_prospective(self) -> None:
        title = self.config["current_authorized_identity"]["working_title_v2"]
        self.assertIn("Prospective ENSO Risk", title)
        self.assertEqual(
            title,
            "Phenology-Aligned Climate–Yield Associations and Prospective ENSO Risk in Piura, Peru: Five-Crop Evidence and Rice–Maize Reference Stress Tests",
        )

    def test_29_problem_statement_is_literature_neutral(self) -> None:
        problem = self.config["current_authorized_identity"]["problem_statement"].lower()
        for forbidden in ("piura lacks", "no previous study", "first study", "no study exists"):
            self.assertNotIn(forbidden, problem)

    def test_30_literature_gap_status_is_not_yet_adjudicated(self) -> None:
        self.assertEqual(
            self.config["s1r_governance"]["LITERATURE_GAP_CLAIM_STATUS"],
            "NOT_YET_ADJUDICATED",
        )

    def test_31_gvp_is_a_conditional_secondary_extension(self) -> None:
        expected = "CONDITIONAL_SECONDARY_EXTENSION_NOT_CORE_PRIMARY_RQ"
        self.assertEqual(self.config["s1r_governance"]["GVP_ROLE"], expected)
        self.assertEqual(self.config["economic_dimension"]["gvp_role"], expected)
        self.assertEqual(
            self.config["economic_dimension"]["gross_production_value_status"],
            "NOT_YET_BUILT_REQUIRES_PRICE_MAPPING_AND_MONETARY_TREATMENT_GATE",
        )

    def test_32_raw_cross_crop_coefficient_comparison_is_not_authorized(self) -> None:
        governance = self.config["s1r_governance"]
        self.assertEqual(governance["CROSS_CROP_COMPARABILITY_STATUS"], "REQUIRES_ECONOMETRIC_DESIGN_GATE")
        self.assertEqual(
            governance["RAW_COEFFICIENT_MAGNITUDE_COMPARISON_WITHOUT_COMMON_ESTIMAND_OR_SCALE"],
            "NOT_AUTHORIZED",
        )
        srq2 = next(row for row in self.crosswalk if row["RQ_ID"] == "SRQ2")
        self.assertEqual(srq2["REQUIRED_FUTURE_GATE"], "ECONOMETRIC_DESIGN_FREEZE_AND_COMPARABILITY_RULES")

    def test_33_q1_scores_are_internal_design_heuristics(self) -> None:
        self.assertEqual(
            self.config["s1r_governance"]["Q1_POSITIONING_SCORE_STATUS"],
            "INTERNAL_DESIGN_HEURISTIC_NOT_MANUSCRIPT_CLAIM",
        )
        self.assertIn("internal design heuristics", self.config["q1_positioning"]["score_interpretation"].lower())

    def test_34_target_crop_importance_ranking_is_not_established(self) -> None:
        self.assertEqual(
            self.config["s1r_governance"]["TARGET_CROP_IMPORTANCE_RANKING_STATUS"],
            "NOT_ESTABLISHED_NOT_REQUIRED_FOR_DESIGN",
        )
        current_text = json.dumps(self.config["current_authorized_identity"], ensure_ascii=False).lower()
        self.assertNotIn("major crops", current_text)

    def test_35_enso_2026_2027_is_prospective_not_a_realized_forecast(self) -> None:
        self.assertEqual(
            self.config["s1r_governance"]["ENSO_2026_2027_INTERPRETATION"],
            "PROSPECTIVE_SCENARIO_STRESS_CONTEXT_NOT_REALIZED_FORECAST",
        )
        self.assertIn("future realization is unknown", self.config["enso_role"]["C_prospective_2026_2027_scenarios"])

    def test_36_identity_artifacts_are_exactly_consistent(self) -> None:
        current = self.config["current_authorized_identity"]
        for field in ("problem_statement", "primary_research_question", "general_objective", "working_title_v2"):
            self.assertIn(current[field], self.report, field)
        for item in current["subquestions"]:
            self.assertIn(item["text"], self.report, item["rq_id"])
        for item in current["specific_objectives"]:
            self.assertIn(item["text"], self.report, item["objective_id"])
        self.assertIn(self.config["identification_ceiling"], self.report)
        self.assertIn(self.config["next_authorized_gate"], self.report)
        self.assertIn(
            f"GVP_STATUS={self.config['economic_dimension']['gross_production_value_status']}",
            self.report,
        )
        self.assertIn(self.config["scientific_architecture"]["layer_1"]["name"], self.report)
        for key, value in self.config["s1r_governance"].items():
            self.assertIn(f"{key}={value}", self.report)
        governance_claims = {row["CLAIM_ID"]: row for row in self.claims if row["CLAIM_ID"] >= "S1-C15"}
        self.assertEqual(set(governance_claims), {"S1-C15", "S1-C16", "S1-C17", "S1-C18"})
        self.assertEqual(governance_claims["S1-C17"]["EVIDENCE_OR_GATE"], "ECONOMETRIC_DESIGN_FREEZE_AND_COMPARABILITY_RULES")


if __name__ == "__main__":
    unittest.main()
