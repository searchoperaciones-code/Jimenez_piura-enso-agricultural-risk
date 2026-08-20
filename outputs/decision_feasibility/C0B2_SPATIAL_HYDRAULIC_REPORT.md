# C0B2 Final Provenance and Temporal-Ontology Correction Report

## 1. Executive verdict

`PASS_FOR_FINAL_NOTARIAL_C0B2_FREEZE_AUDIT`. C0B2RD incorporates the independent C0B2RC corrections without reopening C0B0 or C0B1. Its scientific endstate is `SPATIAL_MEMBERSHIP_RECOVERED_BUT_SERVICE_PARTITION_INSUFFICIENT`: official hydraulic presence now covers all 55 model districts, but general numerical water constraints remain unsupported.

## 2. Frozen C0B1 identity

The immutable base is branch `phase/c0b-decision-feasibility-v1`, HEAD `59e0dacd432998682713fbfca6347de33111012e`, parent `77526c9cb41b20062a5fa61a95167af5859295f2`, subject `Freeze C0B1 decision variable ontology`. The protected C0B0 and C0B1 bytes are unchanged.

## 3. Canonical model district universe

The frozen target-crop panel defines 55 unique UBIGEO districts in seven provinces. Province plus district remains the mandatory GeoSNIRH key, including separate SALITRAL/MORROPON (`200406`) and SALITRAL/SULLANA (`200608`) records. No fuzzy unresolved match is accepted.

## 4. Agency architecture

The agency crosswalk retains 56 relations for 55 districts because Sapillica (`200208`) has an official historical Ayabaca assignment and a later San Lorenzo assignment. This is a temporal institutional many-to-many relation, not a duplicate.

## 5. Agency-to-UBIGEO reconstruction

Thirty-one districts have some agency evidence and 19 have supported, nonexhaustive jurisdiction evidence. No agency relation is classified as current exhaustive jurisdiction.

## 6. PCR implications

`PCR_DISTRICT_DISAGGREGATION_AUTHORIZED=FALSE`. No equal split, area-share split, historical crop-share split, population allocation, or residual assignment may convert an agency PCR total into district hectares.

## 7. Hydraulic institutional hierarchy

The ontology keeps `MAJOR_OPERATIONAL_HYDRAULIC_SYSTEM`, `CURRENT_CANONICAL_JUNTA`, `HISTORICAL_JUNTA_LABEL`, `COMMISSION_OR_SUBSECTOR`, `CROSS_TEMPORAL_COMMISSION_INVENTORY`, `CURRENT_EXHAUSTIVE_ROSTER`, `IRRIGATION_BLOCK`, `NAMED_SERVICE_UNIT`, and `FORMALIZATION_ENTITY` separate. Chira and Medio y Bajo Piura are minor-sector/Junta scopes inside the broader Chira-Piura common system; they are not additional major systems. Sechura is a distinct minor-sector/Junta scope and is not promoted to a fourth major system.

## 8. Chira system

`Sistema Hidraulico Chira Piura` is one major operational system. Chira Junta evidence and canal relations in Paita and Sullana are organizational or service records at their exact supported strengths; none creates an exhaustive district partition.

## 9. San Lorenzo system

`Sistema Hidraulico San Lorenzo` is one major operational system. RA 0354-2024 supplies the only verified current exhaustive commission roster in the package: 16 San Lorenzo commissions, including Somate Alto, Somate Bajo, and exact current source spelling `Quebrada Tototal`. The separately sourced 2020 label `Quebrada Totoral` is retained only as a spelling alias and does not create a seventeenth entity. Las Lomas records remain L2 institutional membership unless a separate exact service source exists.

## 10. Medio y Bajo Piura system

Medio y Bajo Piura is a minor-sector/Junta organizational scope within Chira-Piura, not a separate major system. RD 1218-2022 preserves `PMBP-05-B025` only as the referenced 2006 antecedent and uses `PMBP-05-B03` for the operative 2022 assignment and Article 2. The active Piura relation therefore uses `PIURA_SERVICE_UNIT_CANONICAL_FOR_2022_RELATION=PMBP-05-B03`; both source strings remain explicitly provenance-scoped and do not create two active relations. Canal Narihuala provides nonexhaustive L3 service relations in Catacaos and Cura Mori.

## 11. Sechura system

Sechura remains a distinct Junta/minor-sector scope. The Cristo Nos Valga canonical relation is `Junta de Usuarios del Sector Hidraulico Menor Sechura - Clase A` -> `Comision de Usuarios del Subsector Hidraulico San Andres`. The earlier Medio y Bajo Piura parent is `REJECTED_INCORRECT_SEED` and is not a current canonical relation.

## 12. Alto Piura context

`Sistema Hidraulico Alto Piura` is the third major operational system. `Junta de Usuarios Alto Piura` is also one of the six source-supported current/canonical Piura Juntas, but the system and Junta remain different ontology levels. GeoSNIRH points within its administrative contexts support L1 official presence only unless independently strengthened.

## 13. Other relevant systems/highland/rainfed contexts

Chinchipe Chamaya and Motupe Olmos La Leche remain ALA or hydrographic/administrative contexts, not operational hydraulic systems. Missing service evidence is not classified as rainfed. Every district retains `RAINFED_STATUS=UNRESOLVED_NOT_ASSUMED_RAINFED`.

## 14. Irrigation-block evidence

The cross-temporal evidence inventory contains eight valid named irrigation blocks: four district-resolved service units (Piura, San Miguel de El Faique, Sondorillo, and Salitral/Sullana) plus four Chira registry-only blocks lacking an exact district assignment. El Molle L3 is supported independently by ANA RD 1417-2016; GeoSNIRH feature `Formalizacion.9358` remains L1 corroboration only. A named block is a named service unit, not an official geometric or area partition and not a numeric district fraction.

## 15. District linkage

The hydraulic crosswalk contains 79 nonexhaustive relations and all 55 model districts have explicit official hydraulic adjudication. The ten formerly unresolved districts are corrected by exact official records: Amotape, Arenal, Colan, La Huaca, Tamarindo, Vichayal, Miguel Checa, Querecotillo, Salitral/Sullana, and Cristo Nos Valga.

## 16. Many-to-many relationships

Only Sondorillo is confirmed multi-service. Nine districts have conditional distinct relations pending service adjudication: Piura, Las Lomas, Tambo Grande, Frias, Huancabamba, El Carmen de la Frontera, Huarmaca, San Miguel de El Faique, and Sullana. Catacaos, Cura Mori, and Sondor are not counted as multi merely because one underlying relation appears at different evidence-ladder levels; no one-to-one simplification is made where distinct relations genuinely remain.

## 17. Double-counting risk

Agricultural activity in a confirmed or conditionally multi-related district must not be inserted into every system-level water constraint. Sondorillo requires an official exclusive partition or district x hydraulic-unit subindex. The nine conditional districts require service adjudication before that necessity can be finalized.

## 18. Irrigated/rainfed limitations

GeoSNIRH point locations, formalization entities, licenses, canals, blocks, and maintenance records do not establish total irrigated land. All-land-irrigated assumptions are forbidden. No district is labelled rainfed and no partial relation is treated as complete.

## 19. District-only versus hydraulic-subindex requirement

The audited classification is one `SUBINDEX_REQUIRED_BY_CONFIRMED_MULTI_SERVICE`, nine `SUBINDEX_OR_PARTITION_REQUIRED_PENDING_SERVICE_EVIDENCE`, and 45 `POTENTIAL_SUBINDEX_ONLY`. District indexing remains conceptually usable for the nonwater strategic model. Future system constraints require official service-area partitioning or a district x hydraulic service unit subindex where distinct service relations warrant it.

## 20. Spatial coverage diagnostics

| Diagnostic | Corrected result |
|---|---:|
| Model districts | 55 |
| Provinces | 7 |
| Districts with any agency evidence | 31 (56.4%) |
| Districts with supported agency jurisdiction evidence | 19 (34.5%) |
| Districts with any official hydraulic evidence | 55 (100.0%) |
| Strongest evidence L1 presence only | 36 |
| Strongest evidence L2 institutional membership | 3 |
| Districts with L3 service-level evidence | 16 |
| Districts with named service-unit evidence | 4 |
| Confirmed multi-service districts | 1 |
| Conditional distinct-relation districts | 9 |
| Hydraulically unresolved districts | 0 |
| Geometric service partitions | 0 |
| Official area partitions | 0 |
| Official numeric service fractions | 0 |

The source inventory contains three major operational systems and six source-supported `CURRENT_OR_CANONICAL_JUNTA_ENTITIES`: Chira, Sechura, Huancabamba, Medio y Bajo Piura, Alto Piura, and San Lorenzo. `Junta de Usuarios Valle Andino Huancabamba` is one separately sourced `HISTORICAL_OR_ALIAS_JUNTA_LABEL` mapped to the Huancabamba lineage; it is not a second current Junta. `Junta de Usuarios del Canal Chicope` is retained only as one `NON_JUNTA_HYDRAULIC_LABEL`; Canal Chicope-Cajunga is infrastructure and does not count as a Junta.

`CROSS_TEMPORAL_COMMISSION_SUBSECTOR_INVENTORY_N=50` describes a mixed-temporal contextual inventory, not a current exhaustive Piura roster. `CURRENT_EXHAUSTIVE_COMMISSION_ROSTER_VERIFIED_SCOPE=SAN_LORENZO_ONLY` and `CURRENT_EXHAUSTIVE_SAN_LORENZO_COMMISSION_N=16`. Fourteen Commission/Subsector labels are district-resolved, and eight named irrigation blocks are retained. GeoSNIRH contains 1,504 byte-distinct raw `Nombre` values and 1,500 after whitespace trimming; these are `FORMALIZATION_ENTITIES_NOT_IRRIGATION_BLOCKS`.

## 21. Future system-level constraint eligibility

Spatial membership feasibility is supported, but numerical water-constraint feasibility is not. `WATER_HARD_CONSTRAINT_CURRENTLY_AUTHORIZED=FALSE`. Later water modelling would require service partitions, service fractions or justified district x hydraulic indexing, crop-water coefficients, irrigation-efficiency and loss rules, compatible available-water quantities, and temporal alignment.

## 22. Districts/areas requiring scope reduction

No automatic scope reduction is declared. `SPATIAL_SCOPE_REDUCTION_CURRENTLY_AUTHORIZED=NO`. Presence across all districts does not imply uniform service strength, and service insufficiency does not justify automatic exclusion.

## 23. Forbidden interpretations

- Poechos supplies all Piura agriculture: FALSE / NOT AUTHORIZED.
- A GeoSNIRH point is a service polygon: FALSE / NOT AUTHORIZED.
- A formalization name is an irrigation block: FALSE / NOT AUTHORIZED.
- A named service unit is a district service partition: FALSE / NOT AUTHORIZED.
- Chira, Medio y Bajo Piura, or Sechura is an additional major system: FALSE / NOT AUTHORIZED.
- Missing service evidence proves rainfed production: FALSE / NOT AUTHORIZED.
- PCR agency totals may be allocated to districts: FALSE / NOT AUTHORIZED.
- `SERVICE_FRACTIONS_INVENTED=0`.
- C0B2 authorizes no optimizer and does not authorize an optimizer indirectly.

## 24. Remaining evidence gaps

The principal gaps are exhaustive service-area polygons, official district x service-unit area partitions, numeric service fractions, comprehensive irrigated/rainfed classification, crop-water requirements, time-compatible available-water quantities, conveyance/efficiency losses, and allocation rules. The official-presence gap is closed; the general numerical-service gap is not.

## 25. Final C0B2 verdict

`PASS_FOR_FINAL_NOTARIAL_C0B2_FREEZE_AUDIT`. The package is a final targeted correction candidate, not a scientific freeze until the Director acts. `C0B2_SCIENTIFIC_ENDSTATE=SPATIAL_MEMBERSHIP_RECOVERED_BUT_SERVICE_PARTITION_INSUFFICIENT`, `WATER_HARD_CONSTRAINT_CURRENTLY_AUTHORIZED=FALSE`, and `NO_OPTIMIZATION` remain binding.

### C0B2A under-retrieval finding

C0B2A under-retrieved both agency and hydraulic evidence. C0B2R recovered a much broader official source surface, and C0B2RA then identified ten remaining false unresolved classifications plus semantic overstatements in partition, commission, and multi-relation terminology.

### C0B2RA independent audit correction

C0B2RD implements only the targeted C0B2RC provenance and temporal-ontology corrections. It does not initiate another broad recovery phase, redesign schemas, reduce the model universe, or reopen frozen upstream artifacts.

### GeoSNIRH master-source recovery

The official `SERV_Formalizacion` WFS yielded 1,674 Piura agricultural points; strict district plus province matching retained 1,669 points in 44 model districts and 54 district-ALA families. Hash provenance and deterministic ordering remain registered.

### GeoSNIRH layer semantics

The semantic class is `FORMALIZATION_LICENSE_POINT`, the geometry is `POINT_EPSG4326`, and exhaustiveness is `NONEXHAUSTIVE_PRESENCE_ONLY`. Point presence cannot imply service area, exclusive membership, irrigated fraction, service fraction, or rainfed status.

### Agency jurisdiction recovery

Agency planning group, historical office structure, supported jurisdiction, liaison office, and activity presence remain separate evidence classes. Sapillica's two relations preserve temporal institutional evidence and remain nonexhaustive.

### Junta / Commission recovery

`CURRENT_CANONICAL_PIURA_JUNTAS_N=6`. The exact set is Chira, Sechura, Huancabamba, Medio y Bajo Piura, Alto Piura, and San Lorenzo. Valle Andino Huancabamba is a historical source label mapped explicitly to the Huancabamba lineage; historical labels do not increase the current count. The unsupported `DISTRITO_DE_RIEGO_HUANCABAMBA` alias is absent. Canal Chicope-Cajunga is infrastructure, not a Junta, and Comité Chajapampa/Canal Las Pampas remains committee context rather than Commission/Subsector.

The 50 Commission/Subsector names form a `CROSS_TEMPORAL_CONTEXTUAL_COMMISSION_SUBSECTOR_INVENTORY`. No global current exhaustive Piura total is claimed. The only current exhaustive roster verified here is San Lorenzo with 16 entities; Somate Alto and Somate Bajo are present, and `Quebrada Tototal` preserves RA 0354-2024's exact spelling.

### Irrigation-block / formalization-unit recovery

`NAMED_IRRIGATION_BLOCKS_N=8` and `NAMED_SERVICE_UNIT_N=4`. Salitral/Bolsanada supplies the eighth block and fourth district-resolved named unit. El Molle uses independent ANA resolution provenance for L3; its GeoSNIRH point is only corroborating presence. The 1,504 byte-distinct GeoSNIRH names remain formalization entities, not irrigation blocks.

### Hydraulic entity ontology reclassification

The prior L4 label collapsed a named unit into a partition. C0B2RD retains the corrected `L3_NAMED_SERVICE_UNIT` ontology and preserves separate zero counts for geometric partition, official area partition, and official numeric fraction.

### Evidence-level ladder: presence to partition

L1 is official nonexhaustive presence; L2 is institutional membership; L3 is a partial service relation; `L3_NAMED_SERVICE_UNIT` additionally names a block or service unit. An official service partition and an official numeric service fraction are stronger categories and are absent here.

### 55-district search completeness

Every model district has one eligibility row with strongest hydraulic evidence, service status, multi-service status, subindex status, rainfed non-assumption, future water role, and evidence IDs. Any hydraulic evidence is not treated as service-level evidence.

### Former unresolved ten correction

Each former unresolved district has a separate exact official source and L3 nonexhaustive service relation. `HYD021_SOURCE_DATE=2016-10-03` and `HYD022_SOURCE_DATE=2025-04-08` preserve the exact publication dates. Salitral additionally has a named service unit. Their evidence strengths are not promoted to exhaustive service coverage.

### Why complete presence does not authorize numerical water constraints

Political presence and named service evidence do not provide mutually exclusive service geography or compatible quantities. Thus C0B2 supports spatial membership feasibility only; it does not support a general numerical water model.
