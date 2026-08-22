# C0B5 Decision Domain Rescue and Scope Adjudication

## 1. Executive adjudication

`SELECTED_DECISION_ARCHITECTURE=ROUTE_B_FINITE_PRESPECIFIED_EMPIRICALLY_REALIZED_REFERENCE_CONFIGURATION_ANALYSIS`.

The hierarchy was applied without preference scoring. Route A fails because no public official evidence supplies both a Piura district-crop numerical baseline and a model-admissible adjustment envelope. Route B passes with two source-complete, prespecified empirical reference configurations on one common 13-district scope. Route C remains the valid fallback but is not required because Route B passes.

The short analytical label is `RISK_AWARE_FINITE_REFERENCE_CONFIGURATION_ANALYSIS`. C0B5 performs no ranking, scenario evaluation, economic calculation, objective construction, or optimization.

## 2. Frozen C0B4 constraints

C0B4 is frozen at `c7ac7b870cf76d6ed2d199d5619e07f6bb32f6cb`. Its seven artifacts remain byte-identical. The binding state is:

- `PHYSICAL_LAND_CAPACITY_MODEL_FEASIBILITY=NOT_FEASIBLE`
- `AREA_HA_STATUS=PHYSICAL_AGRICULTURAL_FOOTPRINT_ONLY`
- `REALLOCABLE_TRANSIENT_LAND_STATUS=NOT_OBSERVED`
- `LAND_HARD_CAP_STATUS=NOT_AUTHORIZED`
- `BASELINE_YEAR_STATUS=NOT_YET_FROZEN`
- `HISTORICAL_CONVEX_HULL_AUTHORIZED=FALSE`
- `FIXED_TOTAL_RICE_MAD_COMPOSITION_MODEL_STATUS=NOT_SUPPORTED`
- `MODEL_AUTHORIZED_LAND_PARAMETERS_N=0`
- `MODEL_AUTHORIZED_ADJUSTMENT_BOUNDS_N=0`
- `CONTINUOUS_NUMERICAL_OPTIMIZATION=NOT_AUTHORIZED`

C0B5 does not reinterpret or modify those findings.

## 3. Why continuous allocation currently fails

A continuous Rice/MAD policy domain requires an operational numerical region before an objective can exist. The repository has no observed reallocable transient land, no physical hard cap, no source-supported Rice-MAD fixed total, no frozen district-crop baseline, and no admissible numerical adjustment rule. Historical minima, maxima, quantiles, correlations, and convex hulls remain descriptive only.

`AREA_HA != REALLOCABLE_TRANSIENT_CAPACITY`. No physical-capacity invention rescues the original architecture.

## 4. Route A evidence test

Route A was tested first against A1-A8. The official planning search was limited to MIDAGRI/SIEA, GORE Piura/DRAP, official campaign-planning instruments, and competent Peruvian public agricultural sources. No downstream outcome entered the search or adjudication.

`ROUTE_A_STATUS=NOT_SUPPORTED`.

## 5. Prospective planning evidence

MIDAGRI's 3 May 2026 release establishes that ENIS 2026/2027 collected intended planting information for 23 transient crops, including Rice and MAD, in agricultural districts. The 15 July 2026 official results release reports a national operation covering 1,804 districts and gives national or department summaries.

The public materials reviewed do not expose a numeric Piura district-by-crop table for both Rice and MAD, do not provide multiple district programming alternatives, and do not provide permitted district adjustment ranges. Piura department values cannot be disaggregated to districts. Survey design coverage is not the same as publicly available numerical coverage.

- `PROSPECTIVE_DISTRICT_RICE_PLANNING_AVAILABLE=NO_PUBLIC_NUMERIC_DISTRICT_TABLE_IDENTIFIED`
- `PROSPECTIVE_DISTRICT_MAD_PLANNING_AVAILABLE=NO_PUBLIC_NUMERIC_DISTRICT_TABLE_IDENTIFIED`
- `OFFICIAL_PROSPECTIVE_BASELINE_STATUS=OFFICIAL_NON_DISTRICT_BASELINE_NOT_USABLE`
- `OFFICIAL_ADJUSTMENT_ENVELOPE_STATUS=NOT_AVAILABLE`

A planting intention is not physical capacity, a hard upper bound, a minimum commitment, reallocable area, or a permitted adjustment range.

## 6. Baseline test

`ROUTE_A_BASELINE_STATUS=OFFICIAL_NON_DISTRICT_BASELINE_NOT_USABLE`. ENIS is genuine prospective planning evidence, but the public result available to this audit does not supply the required Piura district Rice/MAD numerical baseline. No regional, agency, hydraulic-system, or province value is converted to a district value. C0B5 does not invent a latest-year, median, PCR, or researcher percentage baseline.

## 7. Adjustment-envelope test

`ROUTE_A_ADJUSTMENT_RULE_STATUS=NOT_AVAILABLE`. No official policy envelope or prospectively justified soft numerical rule was identified. Arbitrary plus/minus percentages are forbidden. Historical extrema, quantiles, and changes remain sensitivity diagnostics and are not promoted to bounds.

## 8. Route A verdict

`ROUTE_A_BLOCKER=NO_PUBLIC_DISTRICT_CROP_NUMERIC_BASELINE_AND_NO_MODEL_ADMISSIBLE_NUMERICAL_ADJUSTMENT_RULE`.

Route A therefore fails before objective-function construction. This does not prevent a prespecified finite reference-configuration comparison.

## 9. Route B conceptual test

Route B does not claim a continuous feasible land region. It freezes a finite set `A={a_1,a_2}` of fully specified, empirically realized reference configurations. Membership is determined before downstream outcomes by source-row presence, numeric completeness, common spatial coverage, and a deterministic tie rule.

The primary rule is `MAXIMIZE_COMMON_DISTRICT_COVERAGE_SUBJECT_TO_AT_LEAST_TWO_SOURCE_COMPLETE_CONFIGURATIONS`. The secondary priority is `MAXIMIZE_CONFIGURATION_COUNT_AT_MAXIMUM_COMMON_SUPPORT`; the final technical tie-break is `LEXICOGRAPHIC_ONLY_IF_NEEDED`.

This rule yields the unique maximum common scope of 13 districts and admits campaigns 2020/2021 and 2023/2024. `LEXICOGRAPHIC_TIEBREAK_ACTUALLY_INVOKED=FALSE`. The coverage-first rule is `PROSPECTIVELY_RESEARCHER_DEFINED_BUT_OUTCOME_INDEPENDENT`: it is not source-mandated, does not prove that 13 districts are scientifically optimal, and does not inspect yield, production, prices, climate response, ENSO impacts, economic outcomes, risk measures, or optimizer performance.

The independently reproduced coverage frontier is:

- `K2:D13`: 2020/2021 + 2023/2024.
- `K3:D9`: 2017/2018 + 2019/2020 + 2020/2021; 2019/2020 + 2020/2021 + 2023/2024.
- `K4:D7`: 2017/2018 + 2019/2020 + 2020/2021 + 2023/2024.
- `K5:D5`: 2016/2017 + 2017/2018 + 2019/2020 + 2020/2021 + 2023/2024.
- `K6:D3`: 2015/2016 + 2016/2017 + 2017/2018 + 2019/2020 + 2020/2021 + 2023/2024; 2016/2017 + 2017/2018 + 2019/2020 + 2020/2021 + 2021/2022 + 2023/2024.
- `K7:D2`: 2016/2017 + 2017/2018 + 2018/2019 + 2019/2020 + 2020/2021 + 2021/2022 + 2023/2024.
- `K8:D0`: nine tied subsets; empty support is infeasible.
- `K9:D0`: one subset; empty support is infeasible.

`WHY_EXACTLY_TWO=ONLY_TWO_CONFIGURATIONS_SATISFY_THE_UNIQUE_MAXIMUM_13_DISTRICT_COMMON_SUPPORT`. K=2 is therefore not an arbitrary researcher choice after viewing outcomes.

## 10. Historical configuration universe

The immutable DRAP source covers nine complete August-July campaign candidates from 2015/2016 through 2023/2024. Every candidate is audited. None is selected because it is a favorable year. Seven are excluded solely because one or more required Rice or MAD district-month values are missing or blank on the authorized common scope.

- `FINITE_CANDIDATE_CONFIGURATIONS_N=9`
- `FINITE_ADMISSIBLE_CONFIGURATIONS_N=2`
- `PRIMARY_REFERENCE_CONFIGURATIONS_N=2`
- `ALTERNATIVE_1_ID=C0B5-A2020-2021`; `ALTERNATIVE_1_SOURCE_CAMPAIGN=2020/2021`
- `ALTERNATIVE_2_ID=C0B5-A2023-2024`; `ALTERNATIVE_2_SOURCE_CAMPAIGN=2023/2024`
- `FINITE_ALTERNATIVE_SELECTION_RULE=OUTCOME_INDEPENDENT_COVERAGE_MAXIMIZATION`

The admitted objects are `EMPIRICALLY_REALIZED_REFERENCE_CONFIGURATIONS`. `HISTORICAL_REALIZATION_STATUS=CERTIFIED_BY_SOURCE_OBSERVATION`, meaning only that each configuration occurred in the source record.

## 11. Campaign completeness

An admissible alternative requires all 12 August-July `SIEMBRA` values for each of two crops in every authorized district. Row absence or blank `SIEMBRA` excludes the campaign. A present numeric zero remains an observed zero; missing is never converted to zero.

Each admitted campaign has 13 districts x 2 crops x 12 months = 312 source values. Every admitted district-crop campaign total is positive.

- `EXPECTED_NUMERIC_CELLS=52`
- `OBSERVED_COMPLETE_NUMERIC_CELLS=52`
- `MISSING_NUMERIC_CELLS=0`
- `SILENT_MISSING_TO_ZERO_USED=FALSE`
- `ALTERNATIVE_1_TIMING_PROFILES_COMPLETE=26/26`
- `ALTERNATIVE_2_TIMING_PROFILES_COMPLETE=26/26`

- 2020/2021: Rice 15,213 ha; MAD 5,704 ha; fingerprint `d9d1481588d73535716b71de732586d0acf9f12e7316358aafb996de9845bc93`.
- 2023/2024: Rice 22,592 ha; MAD 5,937 ha; fingerprint `9750808bed2848863a5a739ce1d9209f6f46df9b6375485a749a1930eb97144e`.

These totals describe the frozen references; they are not capacities, bounds, targets, or recommendations.

Across the 26 district-crop campaign-total cells, the two references have `ALTERNATIVE_L1_DISTANCE_HA=12100`, `ALTERNATIVE_DIFFERENT_CELLS_N=26`, and `ALTERNATIVE_EQUAL_CELLS_N=0`. Therefore `ALTERNATIVE_NUMERIC_DISTINCTNESS_STATUS=MATERIALLY_DISTINCT` and `ALTERNATIVE_TIMING_DISTINCTNESS_STATUS=BOTH_AREA_AND_TIMING_CONFIGURATIONS_DIFFER`. These are structural decision-data diagnostics without yield, profit, climate, ENSO, or risk interpretation.

## 12. Spatial coverage

`FINITE_REFERENCE_SPATIAL_SCOPE_STATUS=COVERAGE_BASED_SCOPE_REDUCTION_REQUIRED`. `COMMON_SUPPORT_DISTRICTS_N=13`. `SPATIAL_SCOPE_SEMANTICS=COVERAGE_QUALIFIED_COMMON_SUPPORT_SUBREGIONAL_SCOPE`. No campaign is complete for both crops across all 55 model districts. The authorized common scope contains exactly 13 districts:

`200101 PIURA; 200105 CATACAOS; 200108 EL TALLAN; 200111 LAS LOMAS; 200114 TAMBO GRANDE; 200201 AYABACA; 200205 MONTERO; 200304 HUARMACA; 200802 BELLAVISTA DE LA UNION; 200803 BERNAL; 200804 CRISTO NOS VALGA; 200805 VICE; 200806 RINCONADA LLICUAR`.

The other 42 model districts are outside this finite reference-configuration scope. `REPRESENTATIVENESS_STATUS=NOT_ESTABLISHED`; the 13 districts are neither a representative sample nor the full Piura region. No result may be generalized to all Piura districts without a new coverage gate.

## 13. Whole-configuration vs district mixing

`WHOLE_REGIONAL_CONFIGURATION_STATUS=NOT_SUPPORTED_NO_COMPLETE_55_DISTRICT_CAMPAIGN`.

`WHOLE_SUPPORTED_SCOPE_CONFIGURATION_STATUS=SUPPORTED_TWO_COMPLETE_CONFIGURATIONS`.

`DISTRICT_MIX_AND_MATCH_STATUS=NOT_AUTHORIZED`. `DISTRICT_MIX_AND_MATCH_DETECTED=FALSE`, `CROP_YEAR_MIXING_DETECTED=FALSE`, and `TIMING_PROFILE_MIXING_DETECTED=FALSE`. Each reference configuration copies one campaign's entire Rice/MAD monthly vector for all 13 supported districts. No district, crop year, or timing profile is borrowed from another campaign, and no synthetic combination is created. Interpolation is forbidden.

## 14. Timing-profile test

`OBSERVED_ALTERNATIVE_TIMING_PROFILE_STATUS=SUPPORTED_ALTERNATIVE_SPECIFIC_ONLY_NO_GENERIC_T3_RULE`.

Each alternative carries its own 12-month source-observed `SIEMBRA` profile. Because every district-crop total is positive, shares can be reproduced by dividing each monthly value by its own campaign total. This removes the need to invent a generic T3 share for these two alternatives only. It does not authorize a generic future T3 rule for arbitrary totals.

## 15. Fixed-perennial compatibility

Mango, Limon and Banana remain `P3_FIXED_STOCK_NEAR_TERM_HORIZON`. The transient alternatives contain only Rice and MAD `SIEMBRA`; they do not import historical perennial changes and cannot alter future perennial stocks.

`PERENNIAL_BASELINE_NUMERIC_STATUS=NOT_YET_NUMERICALLY_FROZEN_SEPARATE_INITIALIZATION_GATE`. C0B3 allows baseline measurement and initialization, but C0B5 does not choose a numerical perennial baseline.

`PERENNIAL_INITIALIZATION_BLOCKS_C0B5_ARCHITECTURE_FREEZE=FALSE`. `PERENNIAL_INITIALIZATION_BLOCKS_FULL_REFERENCE_CONFIGURATION_SCENARIO_EVALUATION=TRUE`.

## 16. Route B verdict

All conditions B1-B10 pass:

- membership is prespecified and outcome-independent;
- two distinct alternatives exist;
- both are numerically complete on one common authorized scope;
- missing is not zero;
- no convex interpolation or district mixing is used;
- historical realization is not labeled guaranteed future feasibility;
- perennials remain fixed;
- no water feasibility is claimed; and
- membership is frozen before any downstream evaluation.

`B1=PASS`; `B2=PASS`; `B3=PASS`; `B4=PASS`; `B5=PASS`; `B6=PASS`; `B7=PASS`; `B8=PASS`; `B9=PASS`; `B10=PASS`.

`ROUTE_B_STATUS=SUPPORTED` and `ROUTE_B_BLOCKER=NONE_AT_ARCHITECTURE_GATE`.

`ROUTE_B_ARCHITECTURE_STATUS=SUPPORTED`. `EXACT_2_CONFIGURATION_13_DISTRICT_SCOPE_STATUS=SUPPORTED`. `ROUTE_B_INFORMATION_DEPTH=THIN_BUT_USABLE`: K=2 supports a prespecified comparison but provides limited reference-set richness and no broad optimization frontier.

The feasibility firewall is exact:

- `HISTORICAL_REALIZATION_STATUS=CERTIFIED_BY_SOURCE_OBSERVATION`
- `PROSPECTIVE_PHYSICAL_FEASIBILITY_STATUS=NOT_CERTIFIED`
- `PROSPECTIVE_INSTITUTIONAL_FEASIBILITY_STATUS=NOT_CERTIFIED`
- `REFERENCE_CONFIGURATION_ROLE=EMPIRICALLY_REALIZED_COMPARATOR_FOR_PROSPECTIVE_RISK_STRESS_TESTING`

Historical occurrence does not guarantee that the same configuration can be reproduced under future physical, hydraulic, institutional, or market conditions.

## 17. Route C implications

`ROUTE_C_STATUS=NOT_REQUIRED_ROUTE_B_SUPPORTED`. Route C remains the required fallback if a later independent audit invalidates the finite set. Under Route C, the study could retain climate exposure, weather-yield analysis, ENSO scenarios, economic distributions, and district/crop risk characterization without an allocation recommendation.

## 18. Hierarchical route adjudication

The hierarchy is exact:

1. Route A tested first: `NOT_SUPPORTED`.
2. Route B tested independently: `SUPPORTED`.
3. Route C: `NOT_REQUIRED`.

Exactly one route is selected. No preference score or compromise hybrid exists.

`FINAL_ARCHITECTURE_VERDICT=ROUTE_B_FINITE_PRESPECIFIED_EMPIRICALLY_REALIZED_REFERENCE_CONFIGURATION_ANALYSIS`.

## 19. Research-question compatibility

`CURRENT_RQ_COMPATIBILITY=CURRENT_RQ_REQUIRES_MATERIAL_REFRAMING`. The repository working title promises spatial Mean-CVaR crop allocation over Piura. That is incompatible with a two-alternative, 13-district finite reference set.

Future manuscript and research-question language must use a prospective risk stress test of two prespecified empirically realized reference configurations under ENSO uncertainty. It must state the 13-district coverage scope. `RQ_REWORDING_STATUS=REQUIRED_BEFORE_MANUSCRIPT_FREEZE`. C0B5 records this required action without editing frozen upstream files.

## 20. Implications for downstream econometrics/ENSO/risk

A later gate may apply the same climate-response model, prospective ENSO scenario generator, economic translation, and risk metrics to both frozen references. Those results may compare or rank references only under a separately prespecified rule. They may not retroactively change alternative identity, membership, spatial scope, timing profiles, or configuration values. No interpolation or optimization between references is authorized.

`FINITE_RISK_AWARE_REFERENCE_CONFIGURATION_ANALYSIS_STATUS=SUPPORTED_ARCHITECTURE_PENDING_DOWNSTREAM_GATES`.

`NEXT_REQUIRED_GATE_AFTER_C0B5=ALTERNATIVE_DATA_MASTER_AND_REFERENCE_CONFIGURATION_FREEZE_WITH_EXACT_IDS_13_DISTRICT_SCOPE_OBSERVED_TIMING_AND_NUMERIC_FIXED_PERENNIAL_INITIALIZATION_BEFORE_ECONOMIC_OR_RISK_COMPARISON`.

## 21. Forbidden interpretations

The following are forbidden:

- `AREA_HA` as rescued capacity or reallocable area.
- ENIS intentions as physical capacity, hard bounds, commitments, or district values when only regional values are public.
- Historical minima, maxima, arbitrary percentages, or a convex hull as a continuous feasible domain.
- Rice/MAD fixed-total substitution.
- District-by-district mix-and-match across campaigns.
- Historical realization as guaranteed future physical feasibility.
- Historical realization as proof of future institutional feasibility or implementability.
- The 13-district scope as representative of or equivalent to all Piura.
- Source-observed timing for two alternatives as a generic future T3 rule.
- Water feasibility, district water allocations, or hydraulic fractions.
- `FINITE_SCENARIO_EVALUATION == CONTINUOUS_CROP_ALLOCATION_OPTIMIZATION`.
- Route B selection as an executed ranking or recommendation.
- Interpolation between the two reference configurations.

## 22. Final architecture verdict

`ROUTE_A_STATUS=NOT_SUPPORTED`.

`ROUTE_B_STATUS=SUPPORTED`.

`ROUTE_C_STATUS=NOT_REQUIRED_ROUTE_B_SUPPORTED`.

`SELECTED_DECISION_ARCHITECTURE=ROUTE_B_FINITE_PRESPECIFIED_EMPIRICALLY_REALIZED_REFERENCE_CONFIGURATION_ANALYSIS`.

`SHORT_ANALYTICAL_LABEL=RISK_AWARE_FINITE_REFERENCE_CONFIGURATION_ANALYSIS`.

`CONTINUOUS_NUMERICAL_OPTIMIZATION_STATUS=NOT_AUTHORIZED`.

`WATER_MODEL=NOT_AUTHORIZED`.

`FINITE_RISK_AWARE_REFERENCE_CONFIGURATION_ANALYSIS_STATUS=SUPPORTED_ARCHITECTURE_PENDING_DOWNSTREAM_GATES`.

`NO_OUTCOME_LEAKAGE_GATE=PASS`.

`NO_INVENTED_CAPACITY_GATE=PASS`.

`NO_WATER_MODEL_GATE=PASS`.

`NO_OPTIMIZATION_EXECUTED_GATE=PASS`.

`C0B5_STATUS=PASS_FOR_FINAL_C0B5_NOTARIAL_FREEZE_AUDIT`.
