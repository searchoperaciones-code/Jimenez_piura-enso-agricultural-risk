# E1 Primary Transient Econometric Exposure Adjudication v1

## 1. Verdict

`E1_PASS_PRIMARY_TRANSIENT_EXPOSURE_READY_FOR_DIRECTOR_FREEZE_DECISION`

`E1_FREEZE_AUTHORIZED=NO`.

## 2. Outcome-blind Stage A

Stage A used B1, B3, frozen phenology, and only the structural D0 grid columns recorded in the decision file. No outcome value or D0 validity field was loaded before the decision record was written and hashed.

`STAGE_A_DECISION_SHA256=283d57a21ba23c30c43f63e4c5327496ab59d760d8ca44a609b365151222a285`

## 3. Candidate inventory

| ID | Architecture | Overall status | Reason |
|---|---|---|---|
| E1-C1 | EXISTING_B3_STRICT_CAMPAIGN_WEIGHTED_EXPOSURE | REJECT_PRIMARY_RETAIN_STRICT_SENSITIVITY | Identification is strict, but validity depends on complete expected SIEMBRA observation and zero ambiguous weight, producing sparse and selectively supported keys. |
| E1-C2 | UNAMBIGUOUS_ASSIGNED_COHORT_CONDITIONAL_SIEMBRA_WEIGHTED_EXPOSURE | SELECTED_PRIMARY_WITH_LIMITATIONS | It produces an identified point exposure from already assigned cohorts while preserving unresolved and missing weight diagnostics and making no full-campaign exposure claim. |
| E1-C3 | AMBIGUITY_PRESERVING_PARTIAL_IDENTIFICATION_WITHOUT_ASSIGNMENT | REJECT_AS_POINT_PRIMARY_NOT_IDENTIFIED | Frozen evidence supports preserving ambiguous mass but not allocating it to one campaign or converting it into one point exposure. |
| E1-C4 | NO_ADDITIONAL_FROZEN_ARCHITECTURE | NOT_AVAILABLE | No other point architecture is authorized by frozen evidence without inventing assignment, splitting, imputation, or interpolation. |

## 4. Domain adjudication

| Candidate | Domain | Status | Reason |
|---|---|---|---|
| E1-C1 | BIOLOGICAL_ALIGNMENT | PASS | Uses the frozen crop-specific windows. |
| E1-C1 | CAMPAIGN_ATTRIBUTION_IDENTIFICATION | PASS | Only strictly unambiguous campaign weight contributes. |
| E1-C1 | MEASUREMENT_INTERPRETABILITY | PASS | Valid rows represent a full strict unambiguous weighting domain. |
| E1-C1 | SIEMBRA_WEIGHT_INTEGRITY | PASS | No ambiguous positive weight or missing required SIEMBRA is accepted. |
| E1-C1 | CLIMATE_WINDOW_COMPLETENESS | PASS | Every positive contributing cohort must be complete. |
| E1-C1 | TEMPORAL_BOUNDARY_INTEGRITY | PASS | The excluded 2015/2016 layer is explicitly left truncated. |
| E1-C1 | DISTRICT_CAMPAIGN_SUPPORT | FAIL | Only 38 of 707 D0 structural keys are strict-valid. |
| E1-C1 | SUSCEPTIBILITY_TO_SELECTION | FAIL | Validity selects keys with complete monthly records and no positive ambiguous mass. |
| E1-C1 | FUTURE_SCENARIO_COMPATIBILITY | PASS_WITH_LIMITATION | Construction is reproducible, but strict support is too selective for a primary layer. |
| E1-C1 | REPRODUCIBILITY | PASS | The frozen B3 artifact is byte-deterministic. |
| E1-C2 | BIOLOGICAL_ALIGNMENT | PASS | Uses the frozen Rice and MAD windows without modification. |
| E1-C2 | CAMPAIGN_ATTRIBUTION_IDENTIFICATION | PASS | Only cohorts already unambiguously assigned by frozen harvest bounds enter the point exposure. |
| E1-C2 | MEASUREMENT_INTERPRETABILITY | PASS_WITH_LIMITATION | The estimand is conditional on identified observed SIEMBRA, not the entire campaign. |
| E1-C2 | SIEMBRA_WEIGHT_INTEGRITY | PASS_WITH_LIMITATION | The conditional denominator is explicit; ambiguous mass and absent expected rows remain visible. |
| E1-C2 | CLIMATE_WINDOW_COMPLETENESS | PASS | All positive contributing assigned weight must have all nine climate metrics. |
| E1-C2 | TEMPORAL_BOUNDARY_INTEGRITY | PASS | Only the seven D0 campaigns are constructed; 2015/2016 is excluded. |
| E1-C2 | DISTRICT_CAMPAIGN_SUPPORT | PASS_WITH_LIMITATION | 608 of 707 structural keys have positive complete assigned weight, with limitations disclosed by key. |
| E1-C2 | SUSCEPTIBILITY_TO_SELECTION | PASS_WITH_LIMITATION | Identification fractions vary and must be retained in later design and reporting. |
| E1-C2 | FUTURE_SCENARIO_COMPATIBILITY | PASS_WITH_LIMITATION | Historical weights can be held fixed; future-calendar assumptions require a later scenario gate. |
| E1-C2 | REPRODUCIBILITY | PASS | The rule is deterministic from frozen B1 and structural D0 keys. |
| E1-C3 | BIOLOGICAL_ALIGNMENT | PASS | Frozen windows are retained. |
| E1-C3 | CAMPAIGN_ATTRIBUTION_IDENTIFICATION | NOT_IDENTIFIED | Ambiguous weight has no frozen single-campaign assignment. |
| E1-C3 | MEASUREMENT_INTERPRETABILITY | NOT_IDENTIFIED | No unique campaign-level point exposure follows. |
| E1-C3 | SIEMBRA_WEIGHT_INTEGRITY | PASS_WITH_LIMITATION | Ambiguous mass can be retained only as unresolved QA. |
| E1-C3 | CLIMATE_WINDOW_COMPLETENESS | PASS | Cohort climate values are available when windows are complete. |
| E1-C3 | TEMPORAL_BOUNDARY_INTEGRITY | PASS | Campaign boundaries remain unchanged. |
| E1-C3 | DISTRICT_CAMPAIGN_SUPPORT | NOT_IDENTIFIED | Point-exposure support is undefined without an attribution rule. |
| E1-C3 | SUSCEPTIBILITY_TO_SELECTION | PASS_WITH_LIMITATION | No assignment is induced, but no point estimand exists. |
| E1-C3 | FUTURE_SCENARIO_COMPATIBILITY | NOT_IDENTIFIED | A scenario point exposure would require a new ambiguity rule. |
| E1-C3 | REPRODUCIBILITY | PASS | The blocked determination is reproducible. |
| E1-C4 | BIOLOGICAL_ALIGNMENT | NOT_IDENTIFIED | No additional frozen candidate exists. |
| E1-C4 | CAMPAIGN_ATTRIBUTION_IDENTIFICATION | NOT_IDENTIFIED | No additional frozen candidate exists. |
| E1-C4 | MEASUREMENT_INTERPRETABILITY | NOT_IDENTIFIED | No additional frozen candidate exists. |
| E1-C4 | SIEMBRA_WEIGHT_INTEGRITY | NOT_IDENTIFIED | No additional frozen candidate exists. |
| E1-C4 | CLIMATE_WINDOW_COMPLETENESS | NOT_IDENTIFIED | No additional frozen candidate exists. |
| E1-C4 | TEMPORAL_BOUNDARY_INTEGRITY | NOT_IDENTIFIED | No additional frozen candidate exists. |
| E1-C4 | DISTRICT_CAMPAIGN_SUPPORT | NOT_IDENTIFIED | No additional frozen candidate exists. |
| E1-C4 | SUSCEPTIBILITY_TO_SELECTION | NOT_IDENTIFIED | No additional frozen candidate exists. |
| E1-C4 | FUTURE_SCENARIO_COMPATIBILITY | NOT_IDENTIFIED | No additional frozen candidate exists. |
| E1-C4 | REPRODUCIBILITY | NOT_IDENTIFIED | No additional frozen candidate exists. |

## 5. Selected architecture

`UNAMBIGUOUS_ASSIGNED_COHORT_CONDITIONAL_SIEMBRA_WEIGHTED_EXPOSURE` is selected with limitations. It is a conditional mean over positive observed SIEMBRA already assigned without ambiguity. It is not a full-campaign exposure claim.

## 6. Ambiguity and SIEMBRA rules

`AMBIGUOUS_COHORT_RULE=EXCLUDE_FROM_POINT_EXPOSURE_PRESERVE_WEIGHT_AND_COUNTS_NO_ASSIGNMENT`

`SIEMBRA_WEIGHT_RULE=NORMALIZE_ONLY_OVER_POSITIVE_OBSERVED_UNAMBIGUOUS_ASSIGNED_SIEMBRA_AS_EXPLICIT_CONDITIONAL_ESTIMAND_NO_FULL_CAMPAIGN_CLAIM`

Unresolved ambiguous weight is never assigned, split, interpolated, or silently discarded. It remains visible by key. Missing expected-cohort weight is not assumed to be zero.

## 7. B3 role

`B3_ROLE=STRICT_SENSITIVITY`. B3 remains the strict-identification sensitivity because its strict-valid keys are sparse and selected by complete expected SIEMBRA observation plus zero ambiguous positive weight.

## 8. Outcome-blind support

The structural grid contains 707 keys. The selected architecture has 608 valid exposure rows; B3 has 38 strict-valid rows. These are exposure-feasibility facts, not outcome support or a numerical selection objective.

## 9. Climate-family firewall

`CLIMATE_FAMILY_ROLE_SELECTION=DEFERRED_TO_ECONOMETRIC_DESIGN_MASTER`. All nine frozen metrics are preserved without fit-based designation.

## 10. Measurement-error assessment

| Mechanism | Classification | Treatment |
|---|---|---|
| MONTHLY_SIEMBRA_COHORT_WEIGHTS | AGGREGATION_AND_RECORDING_ERROR_DIRECTION_NOT_QUANTIFIED | Preserve observed, assigned, ambiguous, and missingness diagnostics by key. |
| RICE_TRANSPLANT_ESTABLISHMENT_PROXY | ANCHOR_TIMING_PROXY_ERROR_DIRECTION_NOT_QUANTIFIED | Retain the frozen operational semantics and do not reinterpret SIEMBRA as a precise biological date. |
| BROAD_ATTRIBUTION_LAG_INTERVAL | CAMPAIGN_CLASSIFICATION_UNCERTAINTY | Only frozen unambiguous assignments enter the point exposure. |
| CROSS_CAMPAIGN_AMBIGUITY | UNRESOLVED_ATTRIBUTION_MASS | Exclude it from the point numerator and denominator while preserving its mass and counts as QA. |
| DISTRICT_LEVEL_CLIMATE_AGGREGATION | WITHIN_DISTRICT_SPATIAL_SMOOTHING_DIRECTION_NOT_QUANTIFIED | Retain the frozen whole-district climate geography. |
| MONTHLY_PHENOLOGICAL_EXPOSURE | WITHIN_MONTH_TIMING_COARSENING_DIRECTION_NOT_QUANTIFIED | Retain the frozen monthly windows; no daily or threshold transformation is introduced. |

## 11. Scenario compatibility

The architecture is compatible with common scenario propagation when historical campaign-specific SIEMBRA weights are held fixed. Any future calendar assumption requires a later scenario gate. Neither historical reference configuration is privileged.

## 12. Stage-B support overlay

`POST_DECISION_DIAGNOSTIC_NOT_SELECTION_EVIDENCE`

D0 grid rows: 707. D0-valid rows: 646. Exposure-valid rows: 608. Joint valid intersection: 599. D0-valid rows lacking valid exposure: 47.

| Crop code | D0 grid | D0 valid | Exposure valid | Joint valid |
|---|---:|---:|---:|---:|
| 14010020000 | 322 | 294 | 285 | 281 |
| 14010070000 | 385 | 352 | 323 | 318 |

District and campaign detail is preserved row by row in `E1_SUPPORT_OVERLAY.csv`; campaign summaries are retained in the deterministic Stage-B summary.

## 13. Nonrevision audit

`DECISION_CHANGED_AFTER_D0_OVERLAY=FALSE`. Stage B did not modify the decision record, candidate matrix, exposure artifact, ambiguity rule, weighting rule, exclusion rule, or B3 role.

## 14. Candidate artifact

`transient_econometric_exposures_v1.parquet` contains 707 rows and 608 exposure-valid rows. It contains identifiers, nine climate metrics, and explicit QA fields only.

## 15. Deterministic hashes

- `config/exposure_adjudication/primary_transient_exposure_v1.json=283d57a21ba23c30c43f63e4c5327496ab59d760d8ca44a609b365151222a285`
- `data/processed/phenology/transient_econometric_exposures_v1.parquet=ed90c70a7538318234a0390176b468a66f8a24a99fa59717efe5e8974cf09a67`
- `outputs/exposure_adjudication/E1_CANDIDATE_MATRIX.csv=09bca9fb778759fc0b66656e6057d0f99daf0c9265be1f2b2eb1eb688e226e73`
- `outputs/exposure_adjudication/E1_SUPPORT_OVERLAY.csv=b59894c59485b6c4c92de8be0424f1f6c6211b333ea7609696874b457ac567a8`

## 16. Scientific limitations

The primary point exposure is conditional on identifiable observed cohort weight. Cross-campaign mass remains unresolved, expected monthly SIEMBRA records are incomplete for many keys, and monthly district-level aggregation introduces timing and spatial measurement error whose direction is not quantified.

## 17. Next action

`RETURN_TO_SCIENTIFIC_DIRECTOR_FOR_E1_FREEZE_DECISION_OR_REDESIGN`
