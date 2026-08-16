import csv
import subprocess
import unittest
from pathlib import Path

from scripts import c0b_decision_feasibility_preflight as c0b


ROOT = Path(__file__).resolve().parents[1]


def read_csv(path: Path):
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class C0BDecisionFeasibilityPreflightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = read_csv(c0b.REGISTRY_PATH)
        cls.candidates = read_csv(c0b.CANDIDATES_PATH)
        cls.report = c0b.REPORT_PATH.read_text(encoding="utf-8")

    def test_01_exact_branch(self):
        self.assertEqual(c0b.repository_identity()["branch"], c0b.EXPECTED_BRANCH)

    def test_02_exact_frozen_base(self):
        identity = c0b.repository_identity()
        self.assertEqual(identity["head"], c0b.EXPECTED_HEAD)
        self.assertEqual(identity["tag_target"], c0b.EXPECTED_HEAD)

    def test_03_exact_five_file_scope(self):
        scope = c0b.persistent_scope()
        self.assertEqual(scope["status"], "PASS")
        self.assertEqual(set(scope["observed"]), c0b.AUTHORIZED_SCOPE)

    def test_04_upstream_immutability(self):
        self.assertEqual(c0b.upstream_immutability()["status"], "PASS")

    def test_05_evidence_registry_schema(self):
        self.assertEqual(list(self.registry[0].keys()), c0b.REGISTRY_SCHEMA)

    def test_06_constraint_candidate_schema(self):
        self.assertEqual(list(self.candidates[0].keys()), c0b.CANDIDATE_SCHEMA)

    def test_07_deterministic_ids(self):
        self.assertEqual(
            [row["EVIDENCE_ID"] for row in self.registry],
            [f"C0B-E{i:03d}" for i in range(1, len(self.registry) + 1)],
        )
        self.assertEqual(
            [row["CONSTRAINT_ID"] for row in self.candidates],
            [f"C0B-C{i:03d}" for i in range(1, len(self.candidates) + 1)],
        )

    def test_08_allowed_decision_roles_only(self):
        self.assertTrue(all(row["DECISION_ROLE"] in c0b.ALLOWED_DECISION_ROLES for row in self.candidates))

    def test_09_allowed_spatial_fit_states_only(self):
        self.assertTrue(all(row["SPATIAL_FIT"] in c0b.ALLOWED_SPATIAL_FIT for row in self.candidates))

    def test_10_allowed_evidence_statuses_only(self):
        self.assertTrue(all(row["EVIDENCE_STATUS"] in c0b.ALLOWED_EVIDENCE_STATUSES for row in self.registry))
        self.assertTrue(all(row["EVIDENCE_STATUS"] in c0b.ALLOWED_EVIDENCE_STATUSES for row in self.candidates))

    def test_11_no_optimizer_model_file_exists(self):
        self.assertEqual(c0b.no_optimization_artifacts()["status"], "PASS")

    def test_12_no_c0a_files_were_imported(self):
        self.assertEqual(c0b.no_c0a_contamination()["status"], "PASS")

    def test_13_physical_land_not_reallocable(self):
        row = next(row for row in self.candidates if row["CONSTRAINT_ID"] == "C0B-C002")
        self.assertEqual(row["DECISION_ROLE"], "EXCLUDE_FROM_MODEL")
        self.assertIn("reallocable", row["CANDIDATE_CONSTRAINT"].lower())
        self.assertIn("MIDAGRI physical agricultural area equals freely reallocable land: FALSE", self.report)

    def test_13a_c001_downgraded_pending_decision_variable_ontology(self):
        row = next(row for row in self.candidates if row["CONSTRAINT_ID"] == "C0B-C001")
        self.assertNotEqual(row["DECISION_ROLE"], "HARD_CONSTRAINT_CANDIDATE")
        self.assertEqual(row["DECISION_ROLE"], "UNRESOLVED")
        self.assertIn("DECISION_VARIABLE_ONTOLOGY_NOT_FROZEN", row["CRITICAL_GAP"])
        self.assertIn("DISTRICT_LAND_CAPACITY_STATUS=UNRESOLVED_PENDING_DECISION_VARIABLE_ONTOLOGY", self.report)

    def test_13b_land_ontology_distinguishes_footprint_and_campaign_flows(self):
        required_terms = [
            "PHYSICAL_AGRICULTURAL_FOOTPRINT",
            "CURRENTLY_CULTIVATED_AREA",
            "REALLOCABLE_AREA",
            "CAMPAIGN_SOWN_AREA",
            "HARVESTED_AREA",
            "SIMULTANEOUS_LAND_OCCUPANCY",
        ]
        c001 = next(row for row in self.candidates if row["CONSTRAINT_ID"] == "C0B-C001")
        combined = self.report + "\n" + c001["NOTES"] + "\n" + c001["CRITICAL_GAP"]
        for term in required_terms:
            self.assertIn(term, combined)
        self.assertIn("Cumulative campaign planted hectares cannot automatically be constrained by physical footprint", self.report)
        self.assertIn("Sequential/multiple cropping cannot be assumed absent", self.report)

    def test_13c_next_gate_and_candidate_architecture_are_documented_without_freeze(self):
        self.assertIn("OPTIMAL_NEXT_GATE=DECISION_VARIABLE_ONTOLOGY_GATE", self.report)
        self.assertIn("transient crop-area flows and perennial/semipermanent installed-area stocks", self.report)
        self.assertIn("No such architecture is authorized or frozen in C0B.0B", self.report)
        self.assertIn("No optimizer is currently authorized", self.report)

    def test_13d_c009_c018_are_structural_interpretive_not_numeric_constraints(self):
        c009 = next(row for row in self.candidates if row["CONSTRAINT_ID"] == "C0B-C009")
        c018 = next(row for row in self.candidates if row["CONSTRAINT_ID"] == "C0B-C018")
        self.assertEqual(c009["DECISION_ROLE"], "HARD_CONSTRAINT_CANDIDATE")
        self.assertEqual(c018["DECISION_ROLE"], "HARD_CONSTRAINT_CANDIDATE")
        self.assertIn("hard structural rule", self.report)
        self.assertIn("hard interpretive rule", self.report)
        self.assertIn("not numerical feasible-region constraints", self.report)

    def test_14_system_water_not_district_hard_constraint_without_crosswalk(self):
        row = next(row for row in self.candidates if row["CONSTRAINT_ID"] == "C0B-C007")
        self.assertEqual(row["DECISION_ROLE"], "EXCLUDE_FROM_MODEL")
        self.assertEqual(row["SPATIAL_FIT"], "AGGREGATE_ONLY")
        self.assertIn("NOT_AUTHORIZED", self.report)

    def test_15_pcr_agency_areas_not_district_constraints_without_adjudication(self):
        pcr_rows = [row for row in self.candidates if row["CONSTRAINT_ID"] in {"C0B-C005", "C0B-C006"}]
        self.assertTrue(all(row["SPATIAL_FIT"] == "CROSSWALK_REQUIRED" for row in pcr_rows))
        self.assertIn("PCR programmed hectares are legal district-level maxima: UNRESOLVED", self.report)

    def test_16_multiple_hydraulic_systems_investigated(self):
        domains = {row["DOMAIN"] for row in self.registry}
        self.assertIn("HYDRAULIC_SYSTEM", domains)
        self.assertIn("Chira Piura, San Lorenzo and Alto Piura", self.report)
        self.assertIn("Poechos represents water availability for all Piura districts: FALSE", self.report)

    def test_17_perennial_inertia_investigated(self):
        rows = [row for row in self.registry if row["DOMAIN"] == "PERENNIAL_INERTIA"]
        self.assertGreaterEqual(len(rows), 3)
        self.assertIn("No delta_P or delta_A is set", self.report)

    def test_18_decision_maker_governance_investigated(self):
        rows = [row for row in self.registry if row["DOMAIN"] == "DECISION_MAKER"]
        self.assertGreaterEqual(len(rows), 3)
        self.assertIn("NORMATIVE_REGIONAL_DECISION_SUPPORT", self.report)
        self.assertIn("CENTRALIZED_COMMAND_AUTHORITY", self.report)

    def test_19_parcel_level_claims_forbidden(self):
        row = next(row for row in self.candidates if row["CONSTRAINT_ID"] == "C0B-C017")
        self.assertEqual(row["DECISION_ROLE"], "EXCLUDE_FROM_MODEL")
        self.assertIn("PARCEL_LEVEL_MODEL_STATUS=EXCLUDE_FROM_MODEL", self.report)

    def test_20_gvp_profit_returns_not_built(self):
        self.assertIn("No GVP, gross revenue, returns or profit dataset is built", self.report)
        self.assertNotIn("C0B_GVP", self.report)

    def test_21_preflight_script_passes(self):
        result = subprocess.run(
            ["python", "scripts/c0b_decision_feasibility_preflight.py"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("C0B_0_STATUS=PASS_TO_C0B1_WITH_CRITICAL_GAPS", result.stdout)


if __name__ == "__main__":
    unittest.main()
