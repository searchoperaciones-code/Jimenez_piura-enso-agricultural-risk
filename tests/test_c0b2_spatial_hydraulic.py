import csv
import json
import re
import unittest
from pathlib import Path

from scripts import c0b2_spatial_hydraulic_preflight as c0b2


ROOT = Path(__file__).resolve().parents[1]


def read_csv(path: Path):
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class C0B2SpatialHydraulicTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = read_csv(c0b2.REGISTRY_PATH)
        cls.agency = read_csv(c0b2.AGENCY_PATH)
        cls.hydraulic = read_csv(c0b2.HYDRAULIC_PATH)
        cls.eligibility = read_csv(c0b2.ELIGIBILITY_PATH)
        cls.report = c0b2.REPORT_PATH.read_text(encoding="utf-8")
        cls.registry_by_id = {row["EVIDENCE_ID"]: row for row in cls.registry}
        cls.eligibility_by_id = {row["UBIGEO"]: row for row in cls.eligibility}

    def test_01_exact_c0b1_freeze_ancestor(self):
        self.assertEqual(c0b2.checkpoint_gate()["status"], "PASS")

    def test_02_all_c0b0_c0b1_files_unchanged(self):
        self.assertEqual(c0b2.immutable_gate()["status"], "PASS")

    def test_03_exact_seven_file_c0b2_scope(self):
        gate = c0b2.persistent_scope_gate()
        self.assertEqual(gate["status"], "PASS")
        self.assertEqual(set(gate["observed"]), c0b2.AUTHORIZED_SCOPE)

    def test_04_agency_schema(self):
        self.assertEqual(c0b2._schema(c0b2.AGENCY_PATH), c0b2.AGENCY_SCHEMA)

    def test_05_hydraulic_schema(self):
        self.assertEqual(c0b2._schema(c0b2.HYDRAULIC_PATH), c0b2.HYDRAULIC_SCHEMA)

    def test_06_district_eligibility_schema(self):
        self.assertEqual(c0b2._schema(c0b2.ELIGIBILITY_PATH), c0b2.ELIGIBILITY_SCHEMA)

    def test_07_evidence_registry_schema(self):
        self.assertEqual(c0b2._schema(c0b2.REGISTRY_PATH), c0b2.REGISTRY_SCHEMA)

    def test_08_deterministic_evidence_ids(self):
        self.assertEqual(c0b2.evidence_id_gate()["status"], "PASS")

    def test_09_valid_ubigeo_linkage(self):
        gate = c0b2.ubigeo_gate()
        self.assertEqual(gate["status"], "PASS")
        self.assertEqual(gate["model_n"], 55)

    def test_10_no_fuzzy_ambiguous_match_silently_accepted(self):
        notes = "\n".join(row["NOTES"] for row in self.registry)
        self.assertIn("no fuzzy unresolved match accepted", notes.lower())
        self.assertNotIn("FUZZY_ACCEPTED", notes)

    def test_11_all_service_fractions_require_exact_official_source(self):
        for row in self.hydraulic:
            self.assertEqual(row["SERVICE_FRACTION_AVAILABLE"], "FALSE")
            self.assertEqual(row["SERVICE_FRACTION_VALUE"], "")

    def test_12_absent_fractions_remain_blank(self):
        self.assertTrue(all(row["SERVICE_FRACTION_VALUE"] == "" for row in self.hydraulic))

    def test_13_no_pcr_agency_total_disaggregated_to_district(self):
        self.assertTrue(all(row["DISTRICT_PCR_DISAGGREGATION_AUTHORIZED"] == "FALSE" for row in self.agency))
        self.assertIn("No equal split, area-share split, historical crop-share split, population allocation", self.report)

    def test_14_presence_only_cannot_become_exact_service_relation(self):
        for row in self.hydraulic:
            if row["EXHAUSTIVENESS_STATUS"] == "NONEXHAUSTIVE_PRESENCE_ONLY":
                self.assertNotEqual(row["SERVICE_RELATION_STATUS"], "CERTIFIED_EXACT_SERVICE_RELATION")

    def test_15_one_water_record_cannot_establish_exhaustive_jurisdiction(self):
        self.assertTrue(all(row["EXHAUSTIVENESS_STATUS"] != "COMPLETE_EXHAUSTIVE" for row in self.hydraulic))

    def test_16_many_to_many_relationships_are_preserved(self):
        self.assertTrue(any(row["RELATIONSHIP_CLASS"] == "PARTIAL_UNKNOWN" for row in self.hydraulic))
        self.assertIn("no one-to-one simplification is made", self.report)

    def test_17_duplicate_water_demand_across_multiple_systems_blocked(self):
        self.assertIn("must not be inserted into every system-level water constraint", self.report)
        self.assertEqual(c0b2.relationship_gate()["status"], "PASS")

    def test_18_all_land_irrigated_assumption_forbidden(self):
        self.assertIn("All-land-irrigated assumptions are forbidden", self.report)

    def test_19_all_districts_have_explicit_hydraulic_adjudication(self):
        self.assertEqual({row["UBIGEO"] for row in self.hydraulic}, set(self.eligibility_by_id))
        self.assertFalse(any("UNRESOLVED" in row["HYDRAULIC_MAPPING_STATUS"] for row in self.eligibility))

    def test_20_no_district_water_budgets_exist(self):
        self.assertEqual(c0b2.firewall_gate()["status"], "PASS")
        self.assertNotIn("district water budget created", self.report.lower())

    def test_21_no_water_coefficients_exist(self):
        self.assertIn("crop-water coefficients", self.report)
        combined = json.dumps(self.registry + self.hydraulic + self.eligibility).lower()
        self.assertNotIn("water_coefficient_value", combined)

    def test_22_no_optimization_artifacts_exist(self):
        self.assertIn("does not authorize an optimizer", self.report)
        self.assertEqual(c0b2.firewall_gate()["status"], "PASS")

    def test_23_coverage_diagnostics_are_conservative(self):
        diag = c0b2.coverage_diagnostics()
        self.assertEqual(diag["model_n"], 55)
        self.assertEqual(diag["province_n"], 7)
        self.assertEqual(diag["agency_any"], 31)
        self.assertEqual(diag["agency_supported"], 19)
        self.assertEqual(diag["hyd_any"], 55)
        self.assertEqual(diag["institutional_membership"], 3)
        self.assertEqual(diag["service_level"], 16)
        self.assertEqual(diag["named_service_units"], 4)
        self.assertEqual(diag["partition_level"], 0)
        self.assertEqual(diag["presence_only"], 36)
        self.assertEqual(diag["confirmed_multi"], 1)
        self.assertEqual(diag["conditional_multi"], 9)
        self.assertEqual(diag["hyd_unresolved"], 0)

    def test_24_report_has_all_required_sections(self):
        self.assertEqual(c0b2.report_gate()["status"], "PASS")

    def test_25_c0b2_preflight_passes(self):
        failures = {name: gate for name, gate in c0b2.run_all_gates().items() if gate["status"] != "PASS"}
        self.assertEqual(failures, {})

    def test_26_under_retrieval_false_zeros_are_corrected(self):
        self.assertEqual(len(self.registry), 45)
        self.assertEqual(len(self.agency), 56)
        self.assertEqual(len(self.hydraulic), 79)
        self.assertEqual(len(self.eligibility), 55)
        self.assertGreater(sum(bool(row["AGENCY_NAME"]) for row in self.agency), 0)
        self.assertGreater(sum(bool(row["COMMISSION_OR_SUBSECTOR"]) for row in self.hydraulic), 0)
        self.assertGreater(sum(bool(row["IRRIGATION_BLOCK"]) for row in self.hydraulic), 0)
        self.assertEqual(c0b2.recovery_gate()["status"], "PASS")

    def test_27_geosnirh_provenance_and_geometry_are_explicit(self):
        self.assertTrue({"C0B2-GIS-001", "C0B2-GIS-002", "C0B2-GIS-003"}.issubset(self.registry_by_id))
        gis_text = "\n".join(" ".join(self.registry_by_id[eid].values()) for eid in sorted(self.registry_by_id) if eid.startswith("C0B2-GIS-"))
        self.assertIn("SERV_Formalizacion", gis_text)
        self.assertIn("esriGeometryPoint", gis_text)
        self.assertIn("EPSG:4326", gis_text)
        self.assertIn("RAW_WFS_CSV_SHA256=1bd3126343d9dd6e43d909e92a19a42696e0b2f94242aa0f76348d9fa1cb497a", gis_text)
        self.assertIn("CANONICAL_MATCHED_SUBSET_SHA256=e3fb61ea97f41c48a4db087899eff13061252b6bd53ae0b109a4bf15c9ef29e8", gis_text)

    def test_28_geosnirh_point_families_remain_l1_presence(self):
        rows = [row for row in self.hydraulic if row["EVIDENCE_IDS"] == "C0B2-GIS-001;C0B2-GIS-002;C0B2-GIS-003"]
        self.assertEqual(len(rows), 54)
        self.assertEqual(len({row["UBIGEO"] for row in rows}), 44)
        for row in rows:
            self.assertEqual(row["SERVICE_RELATION_STATUS"], "CERTIFIED_EXACT_POLITICAL_LOCATION")
            self.assertEqual(row["EXHAUSTIVENESS_STATUS"], "NONEXHAUSTIVE_PRESENCE_ONLY")
            self.assertFalse(row["HYDRAULIC_SYSTEM"] or row["JUNTA"] or row["COMMISSION_OR_SUBSECTOR"] or row["IRRIGATION_BLOCK"])
            self.assertIn("GEOMETRY=POINT", row["NOTES"])

    def test_29_ala_contexts_are_not_promoted_to_operational_systems(self):
        for row in self.hydraulic:
            if row["ALA"] in {"Chinchipe Chamaya", "Motupe Olmos La Leche"}:
                self.assertEqual(row["HYDRAULIC_SYSTEM"], "")
        systems = self.registry_by_id["C0B2-HYD-001"]
        self.assertEqual(set(systems["ENTITY_NAME"].split(";")), c0b2.OPERATIONAL_SYSTEMS)

    def test_30_all_55_districts_have_explicit_search_status(self):
        self.assertEqual(len(self.eligibility), 55)
        self.assertEqual(len({row["UBIGEO"] for row in self.eligibility}), 55)
        self.assertTrue(all(row["AGENCY_MAPPING_STATUS"] for row in self.eligibility))
        self.assertTrue(all(row["HYDRAULIC_MAPPING_STATUS"] for row in self.eligibility))

    def test_31_former_unresolved_ten_are_corrected_without_scope_reduction(self):
        observed = {
            row["UBIGEO"] for row in self.eligibility
            if row["HYDRAULIC_MAPPING_STATUS"] in {
                "L3_SERVICE_RELATION_PRESENT_NONEXHAUSTIVE",
                "L3_NAMED_SERVICE_UNIT_NONEXHAUSTIVE",
            }
        }
        self.assertTrue(c0b2.FORMER_UNRESOLVED_IDS.issubset(observed))
        self.assertIn("SPATIAL_SCOPE_REDUCTION_CURRENTLY_AUTHORIZED=NO", self.report)

    def test_32_exact_higher_levels_remain_nonexhaustive(self):
        exact = [row for row in self.hydraulic if row["SERVICE_RELATION_STATUS"] == "CERTIFIED_EXACT_SERVICE_RELATION"]
        self.assertGreater(len(exact), 0)
        self.assertEqual({row["UBIGEO"] for row in exact}, c0b2.SERVICE_LEVEL_IDS)
        self.assertTrue(all(row["EXHAUSTIVENESS_STATUS"] == "PARTIAL_KNOWN" for row in exact))
        self.assertTrue(all(row["SERVICE_FRACTION_AVAILABLE"] == "FALSE" and row["SERVICE_FRACTION_VALUE"] == "" for row in exact))

    def test_33_salitral_name_collision_uses_province_key(self):
        morropon = [row for row in self.hydraulic if row["DISTRICT_NAME"] == "SALITRAL" and row["PROVINCE_NAME"] == "MORROPON"]
        sullana = [row for row in self.eligibility if row["DISTRICT_NAME"] == "SALITRAL" and row["PROVINCE_NAME"] == "SULLANA"]
        self.assertTrue(morropon)
        self.assertEqual({row["UBIGEO"] for row in morropon}, {"200406"})
        self.assertEqual(len(sullana), 1)
        self.assertEqual(sullana[0]["UBIGEO"], "200608")
        self.assertEqual(sullana[0]["HYDRAULIC_MAPPING_STATUS"], "L3_NAMED_SERVICE_UNIT_NONEXHAUSTIVE")

    def test_34_recovery_status_is_not_a_freeze_or_scope_reduction(self):
        self.assertIn(c0b2.RECOVERY_STATUS, self.report)
        self.assertIn("No automatic scope reduction is declared", self.report)
        self.assertIn("not a scientific freeze", self.report)
        self.assertNotIn("PASS_WITH_SPATIAL_SCOPE_REDUCTION", self.report)

    def test_35_targeted_official_evidence_records_are_present(self):
        required = {f"C0B2-HYD-{n:03d}" for n in range(15, 29)}
        self.assertTrue(required.issubset(self.registry_by_id))
        for eid in required:
            self.assertTrue(self.registry_by_id[eid]["SOURCE_URL"].startswith("https://"))
        self.assertEqual(self.registry_by_id["C0B2-HYD-021"]["SOURCE_DATE"], "2016-10-03")
        self.assertEqual(self.registry_by_id["C0B2-HYD-022"]["SOURCE_DATE"], "2025-04-08")

    def test_36_cristo_nos_valga_parent_is_sechura(self):
        rows = [row for row in self.hydraulic if row["UBIGEO"] == "200804"]
        self.assertEqual(len(rows), 1)
        self.assertIn("Sechura", rows[0]["JUNTA"])
        self.assertIn("San Andres", rows[0]["COMMISSION_OR_SUBSECTOR"])
        self.assertNotIn("Medio y Bajo Piura", rows[0]["JUNTA"])
        self.assertIn("REJECTED_INCORRECT_SEED", rows[0]["NOTES"])

    def test_37_major_system_and_junta_scopes_are_not_conflated(self):
        self.assertEqual(len(c0b2.OPERATIONAL_SYSTEMS), 3)
        self.assertFalse({"Chira", "Medio y Bajo Piura", "Sechura"} & c0b2.OPERATIONAL_SYSTEMS)
        self.assertTrue(all(not row["HYDRAULIC_SYSTEM"] or row["HYDRAULIC_SYSTEM"] in c0b2.OPERATIONAL_SYSTEMS for row in self.hydraulic))

    def test_38_junta_raw_and_canonical_normalization(self):
        source_roster = set(self.registry_by_id["C0B2-HYD-028"]["ENTITY_NAME"].split(";"))
        self.assertEqual(source_roster, c0b2.CURRENT_CANONICAL_PIURA_JUNTAS)
        self.assertEqual(len(source_roster), 6)
        self.assertIn("Junta de Usuarios Alto Piura", source_roster)
        self.assertEqual(
            c0b2.JUNTA_SOURCE_LABEL_TO_CANONICAL["Junta de Usuarios Valle Andino Huancabamba"],
            "Junta de Usuarios de Huancabamba",
        )
        self.assertTrue(c0b2.HISTORICAL_JUNTA_LABELS.isdisjoint(source_roster))
        observed_raw = {row["JUNTA"] for row in self.hydraulic if row["JUNTA"]}
        self.assertTrue(observed_raw.issubset(c0b2.JUNTA_SOURCE_LABEL_TO_CANONICAL))
        combined_evidence_fields = "\n".join(
            [row["ENTITY_NAME"] for row in self.registry]
            + [row["JUNTA"] for row in self.hydraulic]
        )
        self.assertTrue(all(alias not in combined_evidence_fields for alias in c0b2.UNSUPPORTED_JUNTA_ALIASES))
        self.assertFalse(any("Canal Chicope" in row["JUNTA"] for row in self.hydraulic))
        chicope = self.registry_by_id["C0B2-HYD-014"]
        self.assertEqual(chicope["ENTITY_TYPE"], "CANAL_SERVICE_RELATION")
        self.assertIn("NOT_A_JUNTA", chicope["NOTES"])
        for eligibility in self.eligibility:
            normalized = {
                c0b2.JUNTA_SOURCE_LABEL_TO_CANONICAL[row["JUNTA"]]
                for row in self.hydraulic
                if row["UBIGEO"] == eligibility["UBIGEO"] and row["JUNTA"]
            }
            self.assertEqual(int(eligibility["JUNTA_COUNT"]), len(normalized))

    def test_39_commission_inventory_preserves_temporal_ontology(self):
        self.assertEqual(sum(len(values) for values in c0b2.CROSS_TEMPORAL_COMMISSION_INVENTORY.values()), 50)
        roster = set(self.registry_by_id["C0B2-HYD-015"]["ENTITY_NAME"].split(";"))
        self.assertEqual(roster, c0b2.CURRENT_EXHAUSTIVE_SAN_LORENZO_ROSTER)
        self.assertEqual(len(roster), 16)
        self.assertTrue({"Somate Alto", "Somate Bajo"}.issubset(roster))
        self.assertIn("Quebrada Tototal", roster)
        self.assertNotIn("Quebrada Totoral", roster)
        alias_target, alias_evidence = c0b2.COMMISSION_SOURCE_SPELLING_ALIASES["Quebrada Totoral"]
        self.assertEqual(alias_target, "Quebrada Tototal")
        self.assertIn("Quebrada Totoral", self.registry_by_id[alias_evidence]["ENTITY_NAME"])
        self.assertIn("SAN_LORENZO_ONLY", self.registry_by_id["C0B2-HYD-015"]["NOTES"])
        self.assertIn("CROSS_TEMPORAL_COMMISSION_SUBSECTOR_INVENTORY_N=50", self.report)
        self.assertNotIn("50 valid current canonical commission", self.report)

    def test_40_infrastructure_and_committee_are_not_commissions(self):
        commissions = {row["COMMISSION_OR_SUBSECTOR"] for row in self.hydraulic if row["COMMISSION_OR_SUBSECTOR"]}
        self.assertEqual(commissions, c0b2.DISTRICT_RESOLVED_COMMISSIONS)
        self.assertNotIn("Canal Chicope-Cajunga", commissions)
        self.assertNotIn("Comite de Usuarios de Agua Canal Chajapampa", commissions)
        self.assertNotIn("Comite de Usuarios de Agua Canal Las Pampas", commissions)
        self.assertIn("ENTITY_TYPE_CORRECTION=CANAL_CHICOPE_CAJUNGA_IS_INFRASTRUCTURE", "\n".join(row["NOTES"] for row in self.hydraulic))
        self.assertIn("NOT_A_COMMISSION_OR_SUBSECTOR", "\n".join(row["NOTES"] for row in self.hydraulic))

    def test_41_blocks_and_formalization_entities_are_distinct(self):
        combined = "\n".join(" ".join(row.values()) for row in self.registry)
        self.assertEqual(len(c0b2.NAMED_IRRIGATION_BLOCKS), 8)
        self.assertTrue(all(block in combined for block in c0b2.NAMED_IRRIGATION_BLOCKS))
        self.assertIn("1504 byte-distinct", combined)
        self.assertIn("FORMALIZATION_ENTITIES_NOT_IRRIGATION_BLOCKS", combined)

    def test_42_piura_service_unit_code_roles_match_source(self):
        combined = "\n".join(" ".join(row.values()) for row in self.registry + self.hydraulic)
        source = self.registry_by_id["C0B2-HYD-010"]
        active = [row for row in self.hydraulic if row["UBIGEO"] == "200101" and row["IRRIGATION_BLOCK"]]
        self.assertEqual(len(active), 1)
        self.assertEqual(c0b2.PIURA_ANTECEDENT_CODE, "PMBP-05-B025")
        self.assertEqual(c0b2.PIURA_OPERATIVE_2022_CODE, "PMBP-05-B03")
        self.assertIn(c0b2.PIURA_OPERATIVE_2022_CODE, active[0]["IRRIGATION_BLOCK"])
        self.assertNotIn(c0b2.PIURA_ANTECEDENT_CODE, active[0]["IRRIGATION_BLOCK"])
        self.assertIn(f"PIURA_SERVICE_UNIT_ANTECEDENT_CODE={c0b2.PIURA_ANTECEDENT_CODE}", source["NOTES"])
        self.assertIn(f"PIURA_SERVICE_UNIT_OPERATIVE_2022_CODE={c0b2.PIURA_OPERATIVE_2022_CODE}", source["NOTES"])
        self.assertIn(f"PIURA_SERVICE_UNIT_CANONICAL_FOR_2022_RELATION={c0b2.PIURA_OPERATIVE_2022_CODE}", source["NOTES"])
        documented = set(re.findall(r"PMBP-05-B\d+", combined))
        self.assertEqual(documented, {c0b2.PIURA_ANTECEDENT_CODE, c0b2.PIURA_OPERATIVE_2022_CODE})

    def test_43_multi_service_classification_is_exact(self):
        confirmed = {row["UBIGEO"] for row in self.eligibility if row["DOUBLE_COUNTING_RISK"] == "CONFIRMED_MULTI_SERVICE_DOUBLE_COUNTING_RISK"}
        conditional = {row["UBIGEO"] for row in self.eligibility if row["DOUBLE_COUNTING_RISK"] == "CONDITIONAL_MULTI_RELATION_REQUIRES_ADJUDICATION"}
        self.assertEqual(confirmed, c0b2.CONFIRMED_MULTI_IDS)
        self.assertEqual(conditional, c0b2.CONDITIONAL_MULTI_IDS)
        self.assertEqual(len(confirmed), 1)
        self.assertEqual(len(conditional), 9)

    def test_44_false_multi_from_evidence_ladder_is_zero(self):
        for ubigeo in c0b2.FALSE_LADDER_MULTI_IDS:
            self.assertEqual(self.eligibility_by_id[ubigeo]["DOUBLE_COUNTING_RISK"], "NO_CONFIRMED_MULTI_SERVICE")
        self.assertEqual(c0b2.coverage_diagnostics()["false_multi"], 0)

    def test_45_subindex_status_counts_are_exact(self):
        diag = c0b2.coverage_diagnostics()
        self.assertEqual(diag["subindex_confirmed"], 1)
        self.assertEqual(diag["subindex_conditional"], 9)
        self.assertEqual(diag["subindex_potential"], 45)

    def test_46_named_service_unit_is_not_partition(self):
        rows = [row for row in self.hydraulic if row["IRRIGATION_BLOCK"]]
        self.assertEqual({row["UBIGEO"] for row in rows}, c0b2.NAMED_SERVICE_UNIT_IDS)
        self.assertTrue(all("EVIDENCE_LEVEL=L3_NAMED_SERVICE_UNIT" in row["NOTES"] for row in rows))
        self.assertFalse(any("L4_OFFICIAL_PARTITION_OR_FRACTION" in row["NOTES"] for row in rows))

    def test_47_partition_and_fraction_counts_are_zero(self):
        diag = c0b2.coverage_diagnostics()
        self.assertEqual(diag["geometric_partition"], 0)
        self.assertEqual(diag["official_area_partition"], 0)
        self.assertEqual(diag["official_numeric_fraction"], 0)
        self.assertEqual(diag["service_fractions_invented"], 0)

    def test_48_service_level_evidence_set_is_exact(self):
        observed = {row["UBIGEO"] for row in self.hydraulic if row["SERVICE_RELATION_STATUS"] == "CERTIFIED_EXACT_SERVICE_RELATION"}
        self.assertEqual(observed, c0b2.SERVICE_LEVEL_IDS)
        self.assertEqual(len(observed), 16)
        for row in self.hydraulic:
            if row["SERVICE_RELATION_STATUS"] == "CERTIFIED_EXACT_SERVICE_RELATION":
                evidence = [self.registry_by_id[eid] for eid in row["EVIDENCE_IDS"].split(";")]
                independent_l3 = [
                    item for item in evidence
                    if item["EVIDENCE_STATUS"] == "CERTIFIED_EXACT_SERVICE_RELATION"
                    and item["SOURCE_DOCUMENT_TYPE"] != "OFFICIAL_WFS_CSV_RECORD"
                    and item["CLAIM_TYPE"].startswith("L3_")
                ]
                self.assertTrue(independent_l3, row)
        geosnirh_el_molle = self.registry_by_id["C0B2-HYD-013"]
        independent_el_molle = self.registry_by_id["C0B2-HYD-027"]
        self.assertTrue(geosnirh_el_molle["CLAIM_TYPE"].startswith("L1_"))
        self.assertEqual(geosnirh_el_molle["SOURCE_DOCUMENT_TYPE"], "OFFICIAL_WFS_CSV_RECORD")
        self.assertEqual(independent_el_molle["SOURCE_DATE"], "2016-10-03")
        self.assertEqual(independent_el_molle["UBIGEO"], "200308")
        self.assertIn("INDEPENDENT_NON_GEOSNIRH_L3_PROVENANCE", independent_el_molle["NOTES"])
        self.assertEqual(c0b2.coverage_diagnostics()["l3_geosnirh_only"], 0)

    def test_49_every_district_distinguishes_evidence_and_service(self):
        allowed = {
            "L1_OFFICIAL_PRESENCE_NONEXHAUSTIVE",
            "L2_INSTITUTIONAL_MEMBERSHIP_PRESENT_NONEXHAUSTIVE",
            "L3_SERVICE_RELATION_PRESENT_NONEXHAUSTIVE",
            "L3_NAMED_SERVICE_UNIT_NONEXHAUSTIVE",
        }
        self.assertTrue(all(row["HYDRAULIC_MAPPING_STATUS"] in allowed for row in self.eligibility))
        presence_only = [row for row in self.eligibility if row["HYDRAULIC_MAPPING_STATUS"].startswith("L1_")]
        self.assertTrue(all(row["IRRIGATION_SERVICE_STATUS"] == "HYDRAULIC_PRESENCE_ONLY_SERVICE_UNRESOLVED" for row in presence_only))

    def test_50_agency_metrics_and_sapillica_temporality(self):
        diag = c0b2.coverage_diagnostics()
        self.assertEqual(diag["agency_rows"], 56)
        self.assertEqual(diag["agency_any"], 31)
        self.assertEqual(diag["agency_supported"], 19)
        self.assertEqual(diag["agency_exhaustive"], 0)
        sapillica = [row for row in self.agency if row["UBIGEO"] == "200208"]
        self.assertEqual(len(sapillica), 2)
        self.assertTrue(all("temporal many-to-many" in row["NOTES"] for row in sapillica))

    def test_51_scientific_endstate_is_conservative(self):
        self.assertIn(c0b2.SCIENTIFIC_ENDSTATE, self.report)
        self.assertNotIn("FULL_MULTISCALE_SPATIAL_FEASIBILITY", self.report)
        self.assertIn("Spatial membership feasibility is supported", self.report)
        self.assertIn("numerical water-constraint feasibility is not", self.report)

    def test_52_scope_water_and_optimizer_firewalls_are_explicit(self):
        self.assertIn("SPATIAL_SCOPE_REDUCTION_CURRENTLY_AUTHORIZED=NO", self.report)
        self.assertIn("WATER_HARD_CONSTRAINT_CURRENTLY_AUTHORIZED=FALSE", self.report)
        self.assertIn("SERVICE_FRACTIONS_INVENTED=0", self.report)
        self.assertIn("NO_OPTIMIZATION", self.report)


if __name__ == "__main__":
    unittest.main()
