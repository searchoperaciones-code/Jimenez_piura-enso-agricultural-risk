# C0B1 Decision Variable Ontology Master

## 1. Executive verdict

`C0B1_STATUS=PASS_ONTOLOGY_MASTER`. The primary decision-variable ontology is `ARCH_E_MIXED_STOCK_FLOW_PLUS_MARGINAL_ADJUSTMENT`, with `ARCH_F_TRANSIENT_ENDOGENOUS_PERENNIAL_EXOGENOUS` as fallback. This freezes ontology only; it does not authorize an optimizer, objective, scenario set, economic outcome model, or numeric optimization parameter. `ARCH_E` is primary ontology only and its operational numerical implementation remains blocked pending C0B2, C0B3, and parameter gates.

## 2. Why the ontology gate was necessary

C0B.0 left C0B-C001 unresolved because physical agricultural footprint could not be used until the decision object distinguished physical hectares, campaign planted hectares, cohort establishment hectares, harvested hectares, hectare-month occupancy, installed perennial hectares, establishment, removal, reallocable hectares, and recommended versus commanded hectares. C0B1 resolves that semantic blocker without changing C0B0 evidence.

## 3. Physical land ontology

`AREA_HA` is physical agricultural footprint. It is not automatically current cultivated area, reallocable area, campaign planted area, harvested area, or simultaneous occupation. Its future role is `HARD_CAP_COMPATIBLE_AFTER_OCCUPANCY_MAPPING`.

## 4. Transient crop ontology

Rice (`14010020000`) and maize amarillo duro (`14010070000`) are transient campaign area-flow decisions. Their operational climate timing is not chosen by optimization; it is inherited from the frozen `SIEMBRA` cohort phenology architecture.

## 5. Perennial/semipermanent crop ontology

Mango (`13010210000`) and limon sutil (`13010170102`) are perennial installed-area stock objects. Platanos y bananas (`15010040000`) are semipermanent continuous installed-area stock objects. Any annual establishment or removal margin remains conditional on future C0B3 evidence.

## 6. Architecture A adjudication

Architecture A, homogeneous static area, is `REJECT`. It collapses transient campaign flows and perennial installed stocks into one annual area object.

## 7. Architecture B adjudication

Architecture B, campaign flow for all crops, is `REJECT`. It matches rice and maize better than A, but it makes mango, limon, and banana biologically incoherent annual planting flows without certified establishment logic.

## 8. Architecture C adjudication

Architecture C, physical stock for all crops, is `REJECT`. It can speak to physical occupancy, but it erases the transient sowing/cohort timing required by frozen rice and maize phenology.

## 9. Architecture D adjudication

Architecture D, mixed stock-flow, is `CONDITIONAL_CANDIDATE`. It is dimensionally coherent but incomplete if perennial or semipermanent marginal adjustment is policy-relevant.

## 10. Architecture E adjudication

Architecture E, mixed stock-flow plus marginal adjustment, is `PRIMARY_CANDIDATE`. It preserves stock-flow science while allowing future strategic marginal perennial decisions only after C0B3 evidence. It authorizes no adjustment bounds.

## 11. Architecture F adjudication

Architecture F, transient-endogenous and perennial-exogenous, is `FALLBACK_CANDIDATE`. It is defensible if C0B3 cannot certify installed-stock units or feasible establishment and removal processes.

## 12. Transient temporal-resolution adjudication

The primary transient resolution is `T3_CAMPAIGN_TOTAL_DECISION_WITH_FUTURE_PRESPECIFIED_EXOGENOUS_WITHIN_CAMPAIGN_SHARES`. Its status is `CONDITIONAL_PRIMARY`: the ontology is accepted, but numeric within-campaign share parameterization is not frozen in C0B1. The fallback remains `T2_MONTHLY_OR_COHORT_PLANTED_AREA_FLOWS` if later water timing evidence requires monthly decisions and governance evidence supports such granularity.

### T3 parameterization status

T3 means that the endogenous strategic decision is campaign-total transient crop area. The within-campaign temporal distribution is not an endogenous decision in the primary ontology. Numeric shares are not defined in C0B1, no numeric share vector exists, and no C0B1 artifact selects district-specific, crop-specific, campaign-specific, or scenario-specific share values.

A later gate must define the provenance rule before numerical implementation. That rule must be prespecified before examining weather-yield response estimates, econometric significance, ENSO scenario outcomes, economic optimization results, or model-fit results. Future shares must not be selected to improve yield, robustness, CVaR, profit, GVP, or model fit. Potential admissible evidence classes may include source-observed historical SIEMBRA timing, frozen Stage-B cohort structure, or official agricultural-calendar rules, but C0B1 does not select among them. Any future use of historical shares must be defined by a prespecified rule independent of downstream outcomes.

Planting-date adaptation remains `SENSITIVITY_CANDIDATE_OR_FUTURE_EXTENSION`. It is not required for C0B1 validity and is not made endogenous by this ontology.

## 13. Perennial temporal-resolution adjudication

The primary perennial resolution is `P2_INSTALLED_STOCK_PLUS_ANNUAL_ESTABLISHMENT_REMOVAL_FLOWS_CONDITIONAL_ON_C0B3`. C0B1 creates no baseline installed stocks, establishment rates, removal rates, maximum change percentages, replanting rates, or productive-lifetime parameters. The near-term fallback is `P3_FIXED_STOCK_NEAR_TERM_HORIZON`, which corresponds to architecture F and must remain explicit if C0B3 fails.

## 14. Sequential/multiple cropping assessment

Sequential or multiple cropping cannot be assumed absent. Aggregate district-month and district-year data can show repeated positive sowing months and multiple crop records in a district-year, but they cannot prove parcel-level double cropping or parcel-level crop sequence. In the frozen monthly temporal structure, rice has 313 district-years with more than one positive SIEMBRA month and maize has 349. In `panel_master.csv`, 320 district-years have positive sowing for at least two target crops and 13 district-years have cumulative target-crop sown area greater than `AREA_HA`; this is a warning against direct physical-footprint caps on cumulative campaign hectares, not proof of parcel-level double cropping.

## 15. Phenology compatibility

The ontology preserves the frozen Stage B phenology/exposure architecture. Rice remains `SOWING_COHORT_WEIGHTED` with the `RICE_FLOWERING_95_110_DAS` window. Maize remains `SOWING_COHORT_WEIGHTED` with the `MAD_MPLUS1_MPLUS3` window. Mango, limon, and banana retain their frozen calendar perennial or continuous windows without modification.

### Climate-response windows versus physical land occupancy

`CLIMATE_RESPONSE_WINDOW != PHYSICAL_LAND_OCCUPANCY_WINDOW`. A `CLIMATE_RESPONSE_WINDOW` is the prespecified phenological period used to construct climate exposures relevant to empirical weather-yield response. A `PHYSICAL_LAND_OCCUPANCY_WINDOW` is the period during which a physical hectare is occupied by a crop for purposes of future land-capacity accounting.

Frozen Stage-A and Stage-B climate exposure windows do not define physical occupancy duration. Climate exposure windows must not be reused as occupancy coefficients merely because they already exist. Physical occupancy mapping requires separate agronomic or temporal evidence, and that evidence must be adjudicated in a later parameter/evidence gate. No occupancy duration or occupancy coefficient is created in C0B1.

`AREA_HA` cannot become a numerical hard constraint until the transient flow-to-physical-occupancy mapping is independently supported. Sequential or multiple cropping remains `NOT_ASSUMED_ABSENT`, and aggregate monthly observations cannot establish parcel-level occupancy sequences.

## 16. Land-footprint compatibility

Direct `SUM campaign hectares <= AREA_HA` is not authorized. A physical footprint can become a hard cap only after simultaneous land-occupancy mapping distinguishes physical agricultural footprint, currently cultivated area, reallocable area, campaign sown area, harvested area, and simultaneous land occupancy.

## 17. Multiscale water compatibility

Water compatibility is `COMPATIBLE_IN_PRINCIPLE_AFTER_CROSSWALKS_AND_TEMPORAL_MAPPING`. A district decision variable can later interact with hydraulic-system, agency, junta, or commission constraints after crosswalks. No district hard water constraint, crop water coefficient, or allocation rule is authorized in C0B1.

## 18. Governance semantics

The decision maker is interpreted as normative regional decision support for recommended or planned strategic area. C0B1 does not claim command over farmer-level allocations.

## 19. Endogeneity-set adjudication

SET-1, all five crops endogenous, is `CONDITIONAL_ON_C0B3` and not primary. SET-2, rice and maize fully endogenous with perennials marginally endogenous only, is `SUPPORTED_IN_PRINCIPLE`. SET-3, rice and maize endogenous with perennial stocks exogenous, is `FALLBACK_ONLY`.

## 20. Primary architecture

The primary architecture is `ARCH_E_MIXED_STOCK_FLOW_PLUS_MARGINAL_ADJUSTMENT`. It separates transient crop-area flows from perennial and semipermanent installed stocks while leaving marginal perennial adjustment conditional on C0B3 evidence. It is ontology-primary but operationally blocked pending C0B2, C0B3, and parameter gates.

### Installed versus productive perennial stock

C0B1 distinguishes `INSTALLED_PERENNIAL_STOCK`, `PRODUCTIVE_OR_BEARING_PERENNIAL_STOCK`, `NEW_ESTABLISHMENT_FLOW`, and `REMOVAL_OR_REPLACEMENT_FLOW`. `INSTALLED_PERENNIAL_STOCK` means physical area occupied by an established perennial or semipermanent crop. `PRODUCTIVE_OR_BEARING_PERENNIAL_STOCK` means the subset or state of perennial area relevant to contemporaneous productive output, if that distinction is required by crop biology and source evidence. `NEW_ESTABLISHMENT_FLOW` means new area entering the installed-stock system. `REMOVAL_OR_REPLACEMENT_FLOW` means area leaving or being replaced within the installed-stock system.

`NEW_ESTABLISHMENT_FLOW` does not automatically imply `IMMEDIATE_PRODUCTIVE_OR_BEARING_STOCK`. `IMMEDIATE_PRODUCTIVITY_ASSUMPTION=NOT_AUTHORIZED_WITHOUT_C0B3_EVIDENCE`. C0B1 does not assert any positive lag of a particular duration and does not invent years to maturity, productive lifetime, age distribution, yield-age curves, or establishment-to-yield coefficients.

C0B3 must adjudicate separately for mango, lemon, and banana whether numerical implementation requires installed stock only, installed versus productive/bearing stock distinction, establishment-to-productivity lag, removal/replacement timing, and productive-age or lifecycle information. C0B1D prespecifies no answer to those questions.

For a near-term ENSO planning horizon, an increase in installed perennial area must not automatically be translated into immediate contemporaneous yield or economic return. Any such mapping requires separate C0B3 evidence. This is an ontology safeguard, not a claim about a specific crop maturity duration.

## 21. Fallback architecture

The fallback architecture is `ARCH_F_TRANSIENT_ENDOGENOUS_PERENNIAL_EXOGENOUS`. It keeps rice and maize as endogenous transient decisions and freezes mango, limon, and banana installed stocks as exogenous if future evidence cannot support marginal perennial adjustment. ARCH-F remains the explicit scope-reduction fallback.

If C0B3 cannot defensibly establish the perennial stock, productivity, or adjustment structure required for endogenous perennial decisions, the operational model may fall back from `ARCH_E + SET_2` to `ARCH_F + SET_3`. In that fallback, rice and maize remain endogenous strategic decisions, while mango, lemon, and banana remain exogenous/fixed productive or installed stocks according to the evidence ultimately available. This fallback does not require reopening Stage-A phenology, Stage-B exposures, or transient decision ontology.

## 22. Remaining blockers

No fatal gap blocks the ontology master itself. Critical gaps remain: C0B2 district-to-hydraulic-system and agency crosswalk evidence, C0B3 perennial installed-stock unit certification, C0B3 perennial establishment and removal feasibility evidence, T3 within-campaign share provenance before numerical implementation, and simultaneous land-occupancy mapping before any physical footprint hard cap.

## 23. Exact requirements for next gate

The next gate is `C0B2_SPATIAL_HYDRAULIC_AND_AGENCY_CROSSWALK_GATE`. It must adjudicate district-to-hydraulic-system mappings, agency and user-organization mappings, multiscale water compatibility, and the evidence boundary for later crop-time water constraints. C0B3 must separately certify perennial installed-stock units and any establishment or removal feasibility evidence.

## 24. Forbidden interpretations

C0B1 authorizes no optimizer, no objective function, no CVaR, no scenario set, no regression, no p-value decision rule, no economic outcome objective, no direct `SUM campaign hectares <= AREA_HA` constraint, and no parcel-level double-cropping inference. Parcel-level interpretation is forbidden. No numeric optimization parameters are authorized in C0B1.

C0B1 defines ontology. It does not define occupancy durations, crop maturity lags, yield-age relationships, numeric establishment rates, numeric removal rates, perennial adjustment bounds, water coefficients, land constraints, yield models, ENSO scenarios, GVP, profit, or optimal hectares.

## 25. Final verdict

`PASS_ONTOLOGY_MASTER`. Exactly one architecture is primary. At most one architecture is fallback. The C0B0 checkpoint files remain the evidentiary base. Stage B phenology remains frozen and unchanged.

### Lifecycle-state test adjudication

Raw full suite status is `FAIL_WITH_8_KNOWN_STATE_FAILURES`; adjudicated validation status is `PASS_WITH_ZERO_GENUINE_REGRESSIONS`. The failure ledger is not a general ignore rule. It is conditioned on descendants of checkpoint `77526c9cb41b20062a5fa61a95167af5859295f2`, byte-identical C0B0 checkpoint files, checkpoint ancestry, and no genuine scientific regression. Any different or ninth full-suite failure is an `UNEXPECTED_FAILURE` and blocks future gates.

The five known Stage-B historical state failures are:

1. `tests/test_climate_exposure_b0_preflight.py::test_02_base_commit_and_tag`
2. `tests/test_climate_exposure_b0_preflight.py::test_03_no_forbidden_exposure_output_exists`
3. `tests/test_climate_exposure_b0_preflight.py::test_16_no_stage_b_parquet_output_has_been_built`
4. `tests/test_perennial_exposures.py::test_12_forbidden_artifacts_absent`
5. `tests/test_transient_cohort_exposures.py::test_16_forbidden_artifacts_absent`

The three C0B0 expected post-checkpoint state failures are:

1. `tests/test_c0b_decision_feasibility_preflight.py::test_02_exact_frozen_base` = `EXPECTED_POST_CHECKPOINT_STATE_FAILURE`. The frozen C0B0 test certifies the pre-checkpoint state where HEAD was `144cb679186b8fdfe5b821aad635a7f805b7de28`; after the authorized checkpoint HEAD is `77526c9cb41b20062a5fa61a95167af5859295f2`.
2. `tests/test_c0b_decision_feasibility_preflight.py::test_03_exact_five_file_scope` = `EXPECTED_POST_CHECKPOINT_STATE_FAILURE`. The frozen C0B0 test certifies the pre-commit state where exactly five C0B0 files were untracked; after the checkpoint those files are tracked and exactly five C0B1 files are untracked.
3. `tests/test_c0b_decision_feasibility_preflight.py::test_21_preflight_script_passes` = `EXPECTED_POST_CHECKPOINT_STATE_FAILURE`. The frozen C0B0 preflight correctly rejects the descendant lifecycle because repository-identity and persistent-scope gates certify the earlier pre-checkpoint state, while upstream immutability, no-C0A, and no-optimization properties remain satisfied.

The complete known-state failure ledger after C0B1B contains exactly eight entries: five Stage-B historical failures plus three C0B0 expected post-checkpoint failures. Genuine regressions = 0 and unknown failures = 0.
