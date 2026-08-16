# C0B.0 Decision Feasibility Evidence Reconnaissance

FINAL_C0B0_VERDICT: PASS_TO_C0B1_WITH_CRITICAL_GAPS

## 1. Executive verdict

C0B.0 finds enough official and frozen-repository evidence to continue into a C0B.1 evidence-design phase, but not enough to declare a district-level crop-area optimizer feasible. The defensible interpretation is NORMATIVE_REGIONAL_DECISION_SUPPORT for district-level strategic planning. CENTRALIZED_COMMAND_AUTHORITY over farmer crop allocations is not supported.

No optimizer is built. No variables, objective function, CVaR, linear programming, MILP, scenario generation, regression, weather-yield estimation, GVP, profit, return, or crop-allocation recommendation is created.

## 2. Frozen repository identity

Required branch: phase/c0b-decision-feasibility-v1.

Required HEAD: 144cb679186b8fdfe5b821aad635a7f805b7de28.

Frozen upstream tag: v0.4.0-climate-exposure-freeze, target 144cb679186b8fdfe5b821aad635a7f805b7de28.

C0B is independent from C0A. No C0A artifact is imported.

## 3. Decision-maker/governance assessment

The strongest official evidence supports a regional technical planning process coordinated through DRAP, Agencias Agrarias, ANA, SENAMHI, SENASA, INIA, PECHP, Juntas de Usuarios and Comisiones de Usuarios. The DRAP crop-calendar note states that the 2025-2026 calendar was adopted after a PCR committee technical session and that Comisiones de Usuarios communicate the approved technical calendar to associates.

PCR 2025-2026 and PCR 2024-2025 resolutions approve regional plans, but they do not prove that DRAP or any single actor can command all farmer crop allocations. The future model, if any, must be described as strategic regional planning or policy decision support.

DECISION_MAKER_STATUS=SUPPORTED_PRIMARY_OFFICIAL.

DECISION_MAKER_INTERPRETATION=NORMATIVE_REGIONAL_DECISION_SUPPORT.

## 4. Land evidence

The local frozen file data/processed/land_physical.csv contains 61 district rows and 706379.292651 ha. The source field states interpretation of Planet and Google Earth imagery by DGESEP-MIDAGRI 2024. MIDAGRI's MNSA 2024 material says the MNSA includes permanent crops, transient crops, fallow/rest, cultivated and uncultivated agricultural lands and is a referential statistical instrument for SIEA.

Therefore AREA_HA is a district physical agricultural footprint. It cannot be interpreted as currently cultivated area, irrigated area, available expansion area, freely reallocable land, campaign sown area, harvested area, or simultaneous land occupancy.

DISTRICT_LAND_CAPACITY_STATUS=UNRESOLVED_PENDING_DECISION_VARIABLE_ONTOLOGY; PHYSICAL_FOOTPRINT_ONLY.

REALLOCABLE_LAND_STATUS=UNRESOLVED; EXCLUDE_FROM_HARD_CONSTRAINTS.

### Decision-variable ontology blocker

Decision-variable ontology is currently the highest-priority gap.

AREA_HA is PHYSICAL_AGRICULTURAL_FOOTPRINT only.

PHYSICAL_AGRICULTURAL_FOOTPRINT, CURRENTLY_CULTIVATED_AREA, REALLOCABLE_AREA, CAMPAIGN_SOWN_AREA, HARVESTED_AREA and SIMULTANEOUS_LAND_OCCUPANCY are distinct concepts and must not be used interchangeably.

Cumulative campaign planted hectares cannot automatically be constrained by physical footprint.

Sequential/multiple cropping cannot be assumed absent.

A future decision variable may require separate treatment for transient crop-area flows and perennial/semipermanent installed-area stocks.

No such architecture is authorized or frozen in C0B.0B.

C0B.1 must adjudicate the ontology before the hydraulic crosswalk becomes the primary construction task.

No optimizer is currently authorized.

## 5. Baseline crop-stock evidence

The frozen panel has target-crop rows by district and year for 2016-2023: rice 340 rows across 46 districts, maize amarillo duro 405 across 55, mango 255 across 36, limon sutil 311 across 44 and banana 390 across 54. This is useful historical evidence.

For rice and maize, SIEMBRA and COSECHA can inform baseline transient flow behavior. For mango, limon and banana, perennial or semipermanent installed stock is a separate problem. VERDE_ACTUAL is present but C0B.0 does not certify it as hectares and does not import C0A adjudications.

BASELINE_TRANSIENT_AREA_STATUS=SUPPORTED_FOR_HISTORICAL_SOFT_BASELINES.

BASELINE_PERENNIAL_STOCK_STATUS=UNRESOLVED.

## 6. PCR evidence

PCR 2025-2026 reports 259690 programmed hectares: 73927 permanent, 59925 semipermanent and 125838 transient. The annex is agency-level and identifies the five target crops, including rice 51527 ha, maize amarillo duro 15384 ha, mango 30842 ha, limon sutil 18555 ha, platano organico 8115 ha and platano convencional 5694 ha.

PCR 2024-2025 reports 291633 programmed hectares: 78946 permanent, 62288 semipermanent and 150399 transient. It documents that coastal agency plans were supported by water-balance analysis, while sierra agency crop installation/growth is tied to rainfall.

PCR_STATUS=CERTIFIED_EXACT_OFFICIAL_FOR_AGENCY_PROGRAMS.

PCR_SPATIAL_RESOLUTION=AGENCIA_AGRARIA; CROSSWALK_REQUIRED_FOR_DISTRICT_MODEL.

## 7. Water-availability architecture

ANA's Chira-Piura PADH 2025-2026 source reports projected availability of 3630.69 Hm3, consumptive demand of 2149.53 Hm3 and agrarian allocation of 2073.14 Hm3 for the Sistema Hidraulico Chira Piura. This is credible official system-level evidence.

It must not be converted into district-level water constraints in C0B.0. No area-share, crop-share, population-share or equal-division allocation rule is authorized.

WATER_AVAILABILITY_STATUS=CERTIFIED_EXACT_OFFICIAL_AT_SYSTEM_LEVEL_ONLY.

## 8. Hydraulic systems in Piura

The CRHC Chira-Piura page identifies three systems in its area: Chira Piura, San Lorenzo and Alto Piura. PCR 2025-2026 also refers to PADH approvals for Alto Piura, Chira Piura and San Lorenzo. ANA's San Lorenzo source confirms a distinct San Lorenzo reservoir and PADH planning process.

HYDRAULIC_SYSTEMS_STATUS=SUPPORTED_PRIMARY_OFFICIAL_MULTIPLE_SYSTEMS_CONFIRMED.

Poechos or Chira-Piura must not be treated as the water source for all Piura districts.

## 9. Water-to-district crosswalk feasibility

C0B.0 did not identify a reproducible official crosswalk from hydraulic system, Junta, sector, commission, canal or irrigation area to UBIGEO district. PCR is agency-level; PADH is system-level; the local model data are district-level. The relationship is UNKNOWN and likely not one-to-one.

WATER_DISTRICT_CROSSWALK_STATUS=UNRESOLVED_CRITICAL_GAP.

No district water allocation weights are invented.

## 10. Crop water-requirement evidence

FAO56 and FAO crop-water-need training material provide technical method evidence for evapotranspiration and crop water needs. They distinguish climate, crop type, growth stage and growing-period duration, and contain generic examples for rice, maize, banana and citrus-like crops.

This is not a Piura operational allocation rule. No crop-water coefficients are built or frozen in C0B.0.

CROP_WATER_REQUIREMENT_STATUS=SUPPORTED_TECHNICAL_FOR_SENSITIVITY_ONLY.

## 11. Irrigated/rainfed evidence

PCR 2024-2025 explicitly distinguishes coastal agencies supported by hydric-balance analysis from sierra agencies where crop installation and growth depend on rainfall. MNSA provides agricultural surface but not an irrigated/rainfed split in the local land file.

IRRIGATION_STATUS_EVIDENCE=PARTIAL_AGENCY_LEVEL; DISTRICT_CROP_SPLIT_UNRESOLVED.

All agricultural land in Piura is irrigated is not an authorized assumption.

## 12. Perennial and semipermanent inertia

PCR 2025-2026 classifies mango and limon sutil as permanent crops and platano convencional/organico as semipermanent crops. The frozen phenology architecture separately classifies mango as seasonal perennial, limon as recurrent perennial broad and banana as multistage continuous.

This supports qualitative inertia. It does not support free annual reallocation, removal rates, replanting rates, establishment lags, productive lifetimes or delta bounds.

No delta_P or delta_A is set in C0B.0.

PERENNIAL_INERTIA_STATUS=SUPPORTED_QUALITATIVE; NUMERIC_BOUNDS_UNRESOLVED.

## 13. Adjustment-capacity evidence

Historical district-crop area changes and PCR campaign-to-campaign program changes could support future empirical calibration or sensitivity ranges. C0B.0 does not estimate adjustment bounds and does not set delta_P or delta_A.

ADJUSTMENT_BOUND_EVIDENCE=SENSITIVITY_ONLY_OR_EMPIRICALLY_CALIBRATED_LATER.

## 14. Economic-cost evidence

The frozen panel contains price information and production/area fields, but no production costs, establishment costs, maintenance costs, harvest costs, irrigation costs, gross margins, net returns or profits. C0B.0 did not establish a complete reproducible official cost-budget source for all five crops at Piura district scale.

ECONOMIC_COST_EVIDENCE=UNRESOLVED_FOR_PROFIT_OR_NET_RETURN.

No GVP, gross revenue, returns or profit dataset is built.

## 15. Spatial-scale adjudication

The available repository evidence is strongest at district UBIGEO for land and historical crop variables. PCR is at Agencias Agrarias. Water evidence is at hydraulic systems, Juntas, sectors, commissions or reservoir/system level. No parcel geometries, farmer choice data, irrigation-turn data or parcel-level planting layouts are present.

DISTRICT_DECISION_SCALE_STATUS=SUPPORTED_AS_STRATEGIC_DECISION_SUPPORT_WITH_CROSSWALKS.

PARCEL_LEVEL_MODEL_STATUS=EXCLUDE_FROM_MODEL.

## 16. Candidate hard constraints

The remaining hard candidates are structural or interpretive rules, not numerical feasible-region constraints:

- C0B-C009: hard structural rule. Future modelling must preserve the existence of multiple hydraulic systems and may not collapse all Piura water into one fictitious district-level budget.
- C0B-C018: hard interpretive rule. Future modelling must preserve the normative regional decision-support interpretation and may not claim centralized command over individual farmer crop allocations.

C0B-C001 is no longer a hard constraint candidate. It is UNRESOLVED until the decision-variable ontology determines whether a future land variable is compatible with simultaneous physical land occupancy rather than cumulative campaign hectares.

## 17. Candidate soft/sensitivity constraints

Soft candidates:

- C0B-C003: historical transient baseline area for rice and maize.
- C0B-C005: PCR agency total programmed area after crosswalk.
- C0B-C006: PCR agency crop-specific programs after crosswalk.
- C0B-C012: mango/limon qualitative inertia.
- C0B-C013: banana qualitative inertia.

Sensitivity-only candidates:

- C0B-C010: crop water requirements from technical standards after local adaptation.
- C0B-C014: adjustment bounds from empirical or PCR program changes.
- C0B-C016: gross-revenue sensitivity after separate economic translation.

## 18. Constraints that must be excluded

Excluded in C0B.0:

- Freely reallocable land from MNSA physical area.
- System-level PADH Hm3 divided to districts by area share.
- Blanket assumption that all agricultural land is irrigated.
- Net-return/profit objective.
- Parcel-level spatial layout.

## 19. Critical unresolved gaps

Critical gaps:

- Decision-variable ontology for physical footprint versus cumulative campaign area.
- Official water-to-district crosswalk.
- Agency-to-UBIGEO PCR crosswalk.
- Irrigated/rainfed district-crop split.
- Certified current installed perennial/semipermanent stock.
- Perennial replacement/removal/replanting cycles and establishment-to-production lags.
- Local crop-water requirement and irrigation-efficiency evidence.
- Complete official cost budgets for the five target crops.
- Governance documentation that avoids command-authority overclaim.

## 20. Requirements for C0B.1

C0B.1 must remain an evidence-design phase unless explicitly authorized otherwise. Required next evidence:

- Decision-variable ontology gate before crosswalk construction becomes the primary task.
- Official service-area GIS or administrative crosswalk linking hydraulic systems, Juntas, sectors, commissions and districts.
- Official agency-to-district PCR crosswalk or district-level PCR annex.
- Irrigated/rainfed district-crop evidence.
- Independent unit support for any installed-stock variable used as hectares.
- Agronomic evidence for perennial and semipermanent adjustment mechanisms.
- Crop water requirement evidence tailored to Piura climate, soils and irrigation systems.
- Official production-cost/budget evidence if any economic objective is proposed.

## 21. Explicit forbidden interpretations

MIDAGRI physical agricultural area equals freely reallocable land: FALSE.

PCR programmed hectares are legal district-level maxima: UNRESOLVED; not authorized by C0B.0.

Chira-Piura PADH agrarian Hm3 can be divided among districts by area share: NOT_AUTHORIZED.

Poechos represents water availability for all Piura districts: FALSE.

All agricultural land in Piura is irrigated: UNRESOLVED as evidence, FALSE as a blanket assumption.

Mango, lemon and banana can be freely reallocated within one planning period: UNRESOLVED; not authorized.

One regional planner directly controls all farmer crop allocations: UNRESOLVED; not supported by current evidence.

District-level strategic recommendations are equivalent to parcel-level planting layouts: FALSE.

GAP_PRIORITY_1=FATAL_IF_UNRESOLVED: decision-variable ontology.

GAP_PRIORITY_2=CRITICAL: water/hydraulic spatial crosswalk.

GAP_PRIORITY_3=CRITICAL: perennial/semipermanent installed stock.

GAP_PRIORITY_4=MAJOR: agency-to-UBIGEO PCR crosswalk and irrigated/rainfed evidence.

OPTIMAL_NEXT_GATE=DECISION_VARIABLE_ONTOLOGY_GATE.

## 22. Final C0B.0 verdict

C0B_0_STATUS=PASS_TO_C0B1_WITH_CRITICAL_GAPS.

C0B.0 does not declare the optimizer feasible. It authorizes only a later C0B.1 evidence-crosswalk and feasibility-design phase, subject to the critical gaps above.
