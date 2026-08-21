# C0B4 Transient Land Occupancy and Adjustment Feasibility Master

## 1. Executive verdict

`C0B4_DECISION_ENDSTATE=DECISION_MODEL_NOT_YET_FEASIBLE`.

Rice and MAD remain the transient endogenous crop set under frozen Architecture F, but C0B4 does not recover a defensible hard land capacity, model-admissible occupancy kernel, district adjustment bound, future baseline year, or frozen T3 share rule. Historical behavior supports descriptive and sensitivity envelopes only. This negative operational result is scientifically informative and does not exclude either crop from climate-response, economic-outcome, or risk analysis.

`PHYSICAL_LAND_CAPACITY_MODEL_FEASIBILITY=NOT_FEASIBLE` and `STRATEGIC_TRANSIENT_DECISION_DOMAIN_FEASIBILITY=POTENTIALLY_RECOVERABLE_BUT_NOT_CURRENTLY_MODEL_ADMISSIBLE`. These are different findings: failure of a physical-capacity model does not prove that every future policy or empirical decision domain is impossible, but C0B4 authorizes no alternative domain.

## 2. Frozen upstream identity

- Branch: `phase/c0b4-land-adjustment-feasibility-v1`.
- C0B3 freeze and C0B4 base: `ed5543da18ce3a1a5e72a2ab2519b8e2f2363893`.
- Frozen architecture: `ARCH_F_TRANSIENT_ENDOGENOUS_PERENNIAL_EXOGENOUS`.
- Frozen endogeneity set: `SET_3`.
- Frozen perennial resolution: `P3_FIXED_STOCK_NEAR_TERM_HORIZON`.
- Future time-varying exogenous perennial paths remain `NOT_YET_AUTHORIZED`.

All seven C0B3 artifacts are pinned by SHA-256 in the C0B4 preflight. C0B4 does not alter C0B3 or any earlier frozen scientific output.

## 3. Physical land ontology

C0B4 keeps distinct `PHYSICAL_AGRICULTURAL_FOOTPRINT`, `CURRENTLY_CULTIVATED_AREA`, `PERENNIAL_INSTALLED_STOCK`, `TRANSIENT_CAMPAIGN_SOWN_AREA`, `TRANSIENT_MONTHLY_SOWN_FLOW`, `HARVESTED_AREA`, `SIMULTANEOUS_TRANSIENT_OCCUPANCY`, `OTHER_CROP_OCCUPANCY`, `UNUSED_OR_FALLOW_AGRICULTURAL_AREA`, `REALLOCABLE_TRANSIENT_AREA`, and `SEQUENTIAL_REUSE`.

No identity among these objects is assumed merely because each may be measured in hectares.

## 4. AREA_HA interpretation

`AREA_HA_STATUS=PHYSICAL_AGRICULTURAL_FOOTPRINT_ONLY`.

The MNSA footprint includes permanent and transient crops, fallow or rest, and cultivated and uncultivated agricultural land. It is a static 2024 statistical reference. It is not current cultivated area, crop-specific capacity, irrigated area, simultaneous occupancy, or land that a regional planner can freely reassign.

The direct expression `RICE_CAMPAIGN_HA + MAD_CAMPAIGN_HA <= AREA_HA` remains forbidden. `AREA_HA` can become hard-cap compatible only after both a simultaneous-occupancy mapping and an available physical-capacity mapping are certified.

## 5. Five-crop vs full agricultural universe

`OTHER_CROP_OCCUPANCY_RELEVANT=TRUE`.

The complete DRAP source contains 96 crop codes. Five belong to the decision universe and 91 do not. During 2016-2023, 429 of 440 model district-years contain positive `SIEMBRA` for at least one non-target crop; 68 distinct other crop codes have positive sowing in that analytical interval. The median model district-year has seven other positively sown crop codes.

The independent C0B4A audit reproduces `OTHER_CROP_CODES_N=91`, `DISTRICT_YEAR_UNIVERSE_N=440`, `DISTRICT_YEARS_WITH_OTHER_CROP_CODES_N=429`, and `MEDIAN_OTHER_CROP_CODES_PER_RELEVANT_DISTRICT_YEAR=7`.

These facts reject five-crop exhaustiveness. Annual or campaign sums for the 91 other crops are not interpreted as simultaneous occupancy because they can include temporal reuse.

## 6. Fixed perennial-stock implications

C0B3 certifies `VERDE_ACTUAL` as installed stock hectares for mango, limon, and banana and fixes those stocks exogenously in the current architecture. That permits baseline stock characterization but not this identity:

`AVAILABLE_TRANSIENT_LAND = AREA_HA - MANGO_STOCK - LEMON_STOCK - BANANA_STOCK`.

`PERENNIAL_SUBTRACTION_AS_REALLOCABLE_TRANSIENT_LAND=NOT_AUTHORIZED`. The residual can include other crops, fallow, unsuitable or inaccessible land, infrastructure, institutional restrictions, other agricultural uses, and measurement incompatibility.

## 7. Rice occupancy evidence

The official SIEA methodology defines `SIEMBRA` as gross area installed by sowing or transplanting. DRAP and SENAMHI calendars show distinct nursery, direct-sowing, and transplant schedules across Piura valleys. MIDAGRI's official 2018-2022 timing summary shows Piura rice sowing concentrated in August and February-March and corresponding harvested area concentrated in December-January and June-July.

INIA 508 Tinajones reports 142 days to total grain maturity and documents Piura performance. INIA 502 Pitipo reports a 150-155 day vegetative period for northern-coast contexts outside Piura. These sources support `RICE_OCCUPANCY_DURATION_STATUS=SENSITIVITY_ONLY_RANGE` with `142-155 DAY`; they do not certify one crop-general field-release rule. No midpoint is selected.

## 8. MAD occupancy evidence

INIA 619 Megahibrido is an official hard-yellow-maize hybrid adapted to the coast. INIA reports a 140-150 day vegetative period in summer and 160-170 days in winter. DRAP separately documents current use of INIA 619 in a Tambogrande demonstration plot.

The evidence supports `MAD_OCCUPANCY_DURATION_STATUS=SENSITIVITY_ONLY_RANGE` with `140-170 DAY`. It does not establish the cultivar mix, season, harvest timing, or field-release endpoint for all Piura district records. No midpoint is selected.

## 9. Sequential-cropping limitation

The raw data are district-crop-month aggregates. They contain no parcel identifier, geometry, rotation, or crop-substitution link. Eighteen district-campaign Rice-plus-MAD sowing totals exceed their static `AREA_HA`; this is a warning against a direct campaign-hectare cap, not proof of parcel-level double cropping.

Two campaign hectares can be consistent with one physical hectare used sequentially, but parcel-level reuse cannot be identified from these aggregates. `PARCEL_SEQUENTIAL_CROPPING_INFERRED_FROM_DISTRICT_AGGREGATES=FALSE`.

## 10. Simultaneous occupancy mapping

The conceptual aggregate convolution is scientifically meaningful:

`OCCUPANCY[d,c,tau] = SUM_m SIEMBRA[d,c,m] * OCCUPANCY_KERNEL[c,tau-m]`.

However, `SIEMBRA_m != OCCUPANCY_m`, and the available duration ranges do not certify one field-release kernel. An aggregate sensitivity calculation could be performed without claiming parcel identities, but it is not a model constraint. For both crops, `SIMULTANEOUS_OCCUPANCY_MAPPING_STATUS=SENSITIVITY_ONLY_NOT_MODEL_AUTHORIZED`.

`CLIMATE_RESPONSE_WINDOW != PHYSICAL_LAND_OCCUPANCY_WINDOW`. No frozen phenology or climate-exposure window was used to define occupation.

## 11. Reallocable-land evidence

`REALLOCABLE_TRANSIENT_LAND_STATUS=NOT_OBSERVED`.

No official source in the frozen or recovered evidence gives exact reallocable hectares by district and crop. PCR programmed areas are reported at agency or broader planning scales and do not supply a certified district identity. Historical maxima describe observed sowing support; they do not identify current physical capacity.

## 12. Land-hard-cap adjudication

`LAND_HARD_CAP_STATUS=NOT_AUTHORIZED`.

Authorization requires defensible simultaneous occupancy and defensible available physical capacity. C0B4 has neither. The sensitivity-only crop-duration ranges cannot repair the missing capacity identity, and `AREA_HA` alone cannot satisfy both gates.

`LAND_HARD_CAP_NECESSARY_FOR_ANY_VALID_DECISION_MODEL=NO`. A physical hard cap is not logically required by every conceivable scientifically valid decision architecture: a later gate could instead define an independently defensible policy or empirical domain. This statement does not authorize a cap-free model, because no such alternative domain is currently verified.

## 13. Historical Rice adjustment diagnostics

The audit uses only complete August-July campaigns from 2015/2016 through 2023/2024. It produces 55 Rice district rows and 181 complete district-campaign periods. Thirty-four rows have at least two periods and are `SENSITIVITY_ONLY`; 21 remain `UNRESOLVED`.

Across 100 comparable consecutive changes, the absolute-change quartiles are 15, 145, and 329.25 ha. One zero entry and one zero exit occur. For the 2017 comparison, 19 matched districts increase by 5,302 ha in aggregate. For the 2023 comparison, only five matched districts are available and increase by 2,715 ha, so that diagnostic is explicitly coverage-limited. None of these values is a bound.

## 14. Historical MAD adjustment diagnostics

The same complete-campaign rule produces 55 MAD district rows and 229 complete district-campaign periods. Forty-four rows are `SENSITIVITY_ONLY`; 11 are `UNRESOLVED`.

Across 146 comparable consecutive changes, the absolute-change quartiles are 20.25, 57.5, and 185.75 ha. One zero entry and two zero exits occur. Fourteen matched districts decrease by 2,314 ha in the 2017 comparison; 18 matched districts decrease by 6,813 ha in the 2023 comparison. These are descriptive responses in the source record, not causal ENSO effects and not model limits.

## 15. Adjustment-bound adjudication

`RICE_ADJUSTMENT_BOUND_STATUS=SENSITIVITY_ONLY` and `MAD_ADJUSTMENT_BOUND_STATUS=SENSITIVITY_ONLY` at crop level. District rows with fewer than two complete periods remain unresolved.

Historical minima, maxima, quantiles, relative changes, and zero transitions are retained as diagnostics. No historical extreme is promoted to physical capacity; no arbitrary plus or minus percentage is selected; no lower or upper model rule is populated. `MODEL_AUTHORIZED_ADJUSTMENT_BOUNDS_N=0`.

`HISTORICAL_SUPPORT_AS_DECISION_DOMAIN_STATUS=EMPIRICAL_CONTEXT_ONLY` and `HISTORICAL_CONVEX_HULL_AUTHORIZED=FALSE`. Historical portfolios can support description, candidate generation for a later formal gate, and diagnostic sensitivity, but neither observed points nor interpolated convex-hull points certify future feasibility.

The independent joint audit finds 106 complete district-campaign Rice/MAD portfolios and 40 adjacent changes: 19 move in reciprocal directions, 18 move in the same direction, three leave at least one crop unchanged, and none preserves the exact combined total. The within-district level correlation is -0.041963. These facts do not establish substitution. `FIXED_TOTAL_RICE_MAD_COMPOSITION_MODEL_STATUS=NOT_SUPPORTED`.

`CROP_SPECIFIC_BASELINE_RELATIVE_DOMAIN_STATUS=SENSITIVITY_ONLY_NOT_MODEL_AUTHORIZED`. C0B1 conditionally permits the ontology of a later soft policy bound: `SOFT_POLICY_ADJUSTMENT_BOUND_ONTOLOGY_ALLOWED_BY_C0B1=YES_CONDITIONAL_ON_PROSPECTIVE_PRESPECIFIED_EVIDENCE_RULE`. No actual bound exists in C0B4.

## 16. Baseline status

`BASELINE_YEAR_STATUS=NOT_YET_FROZEN`.

Neither C0B1 nor C0B3 freezes a numeric future baseline year for Rice or MAD. C0B4 therefore does not select 2017, 2023, the latest year, a historical mean, or any outcome-favorable year. A later prospective gate must choose a baseline using only predecision information and coverage adequacy.

`LATEST_COMPLETE_PERIOD_BASELINE_STATUS=NOT_AVAILABLE_AS_COMMON_DISTRICT_CROP_BASELINE`: campaign 2023/2024 is complete for only 19 of 55 Rice districts and 26 of 55 MAD districts, while the source ends in December 2024 and contains no complete 2024/2025 district-crop campaign. A calendar-year substitution would conflict with the frozen August-July decision time base.

`MULTIYEAR_REFERENCE_BASELINE_STATUS=METHOD_DEFINED_BUT_NOT_SOURCE_MANDATED`. A median or rolling reference can be described mathematically, but no recovered source mandates the statistic or window. `DISTRICT_OFFICIAL_PLANNING_BASELINE_AVAILABLE=FALSE`; PCR hectares remain agency programs and cannot be silently disaggregated to districts.

## 17. T3 within-campaign share evidence

Using the official August-July campaign and only source `SIEMBRA`, C0B4 finds 175 complete positive Rice district-campaign profiles and 224 MAD profiles. Positive Rice histories cover 36 of 55 districts; positive MAD histories cover 48. Rice profiles have a median of four nonzero months and MAD profiles five.

Campaign timing varies materially within districts: median L1 distance from a district's historical mean profile is 0.517333 for Rice and 0.738429 for MAD. Nineteen Rice districts and seven MAD districts would require an explicit pooling or external-calendar rule. No yield, production, climate-response coefficient, p-value, ENSO result, profit, GVP, CVaR, or optimizer result participates in these diagnostics.

## 18. T3 share adjudication

`T3_SHARE_RULE_RICE=CANDIDATE_NOT_YET_AUTHORIZED` and `T3_SHARE_RULE_MAD=CANDIDATE_NOT_YET_AUTHORIZED`.

Observed timing is a valid provenance family, but C0B4 does not silently choose district-specific means, regional pooling, calendar substitution, or zero-month handling. No future fixed share vector is created. A later gate must prespecify pooling, coverage, zero-month, and robustness rules before exposure or optimization use.

All 175 Rice and 224 MAD positive complete profiles contain at least one zero month, and coordinatewise historical medians do not generally sum to one without an additional normalization choice. Recovery of a T3 rule alone would not rescue numerical optimization because the campaign-total decision domain remains unidentified.

## 19. Implications for future decision model

The architecture remains conceptually coherent, but numerical optimization is not authorized after C0B4. The missing baseline and T3 rule are operational blockers even before later objective, economic, climate-scenario, and parameter gates.

The study can still use observed historical support, report sensitivity envelopes, narrow district scope prospectively, and characterize climate and economic risk. Those weaker uses must remain descriptive or sensitivity analysis until separately authorized.

### Decision-domain hierarchy

- `LEVEL_1_PHYSICAL_LAND_HARD_CAP=NOT_AUTHORIZED`.
- `LEVEL_2_CONTINUOUS_BASELINE_RELATIVE_DECISION_DOMAIN=NOT_AUTHORIZED`.
- `LEVEL_3_FIXED_TOTAL_RICE_MAD_COMPOSITION_DOMAIN=NOT_SUPPORTED`.
- `LEVEL_4_HISTORICAL_SUPPORT=CONTEXT_ONLY` and `LEVEL_4_HISTORICAL_CONVEX_HULL=NOT_AUTHORIZED`.
- `LEVEL_5_FINITE_PRESPECIFIED_OBSERVED_PORTFOLIOS=POTENTIAL_FUTURE_CANDIDATE_REQUIRING_FORMAL_SCOPE_ADJUDICATION`.

`MINIMUM_DEFENSIBLE_DECISION_SCOPE_CANDIDATE=FINITE_PRESPECIFIED_OBSERVED_PORTFOLIOS_FOR_SUPPORTED_DISTRICTS_REQUIRES_FORMAL_SCOPE_ADJUDICATION`. This is not a current feasible set, and C0B4 selects no historical portfolio.

`FINITE_PRESPECIFIED_DECISION_ALTERNATIVES_STATUS=POTENTIALLY_FEASIBLE_AS_SCENARIO_EVALUATION_REQUIRES_FORMAL_REFRAMING`. The firewall is exact: `FINITE_SCENARIO_EVALUATION != CONTINUOUS_CROP_ALLOCATION_OPTIMIZATION`.

Therefore `CONTINUOUS_NUMERICAL_OPTIMIZATION=NOT_AUTHORIZED`, while `POSSIBLE_FUTURE_DECISION_ANALYSIS=NOT_RULED_OUT`. `NEXT_DECISION_DOMAIN_GATE_REQUIRED=TRUE`.

## 20. Forbidden interpretations

- `AREA_HA` as a direct Rice-plus-MAD campaign-hectare cap.
- `AREA_HA` minus fixed perennial stock as reallocable transient land.
- All residual physical land as available, suitable, irrigated, or institutionally reallocable.
- `SIEMBRA_m` as `OCCUPANCY_m`.
- Climate-response windows as physical occupancy windows.
- Parcel double cropping, rotation, or substitution inferred from district aggregates.
- Historical maxima, minima, or arbitrary percentages as model bounds.
- A baseline year chosen from outcomes or downstream performance.
- T3 shares chosen from yield, production, climate coefficients, significance, ENSO results, profit, CVaR, or optimization.
- Hydraulic membership as district water entitlement or a water coefficient.

## 21. Remaining gaps

1. Crop- and system-general sowing-to-field-release evidence for Rice and MAD in Piura.
2. District current-use and physically available land evidence that distinguishes other crops, fallow, suitability, access, irrigation, and institutional restrictions.
3. Exact district-crop planning bounds or another prospective adjustment rule with official authority.
4. A frozen future baseline selected without outcome tuning.
5. A prespecified T3 share rule with explicit district pooling and sparse-history handling.
6. Later economic, scenario, and optimization gates, none of which is opened by C0B4.

## 22. Final C0B4 verdict

`MODEL_AUTHORIZED_LAND_PARAMETERS_N=0`.

`MODEL_AUTHORIZED_ADJUSTMENT_BOUNDS_N=0`.

`NUMERICAL_OPTIMIZATION_FEASIBILITY=NOT_AUTHORIZED` because no model-admissible continuous numerical Rice/MAD allocation domain is currently identified. This blocker precedes optimizer software, an objective function, and any Mean-CVaR formulation.

`C0B4_STATUS=PASS_FOR_FINAL_INDEPENDENT_C0B4_FREEZE_AUDIT`.

C0B4 closes land and adjustment feasibility with a conservative, reproducible negative operational finding. It creates no optimizer, objective function, water model, crop allocation, optimal hectares, future solution, staging, commit, push, or tag.
