# ER2P Prespecified Robustness Execution Protocol Master v1

## Status and temporal disclosure

Candidate protocol only; no ER2P freeze or robustness execution is authorized.
ER1 primary results are known. Robustness results are not known.
The hierarchy was frozen before outcomes in ED1. These operational details are formalized
after primary results and before robustness results. Do not describe all details as pre-outcome.
ER1 remains the sole PRIMARY specification. No primary numerical values are copied here.

ER1_FREEZE_SHA=43de46ecd46248f1e4e2822a30e69cfadbc8260f
ED1_FREEZE_SHA=ed1c7cb79e7842356abd41f7a7af60d2fac1b5a6
ER1_NUMERICAL_RESULTS_IDENTITY=40e0f58269dda309e83a1fa3da17ef4d5dc5523efc72a666f734d0ebacb76b24
ER1_REPORTING_LOCK_SHA256=83eea5e179b5e3504bd1144d744dcdbeddbbdf6a554f4d10ab03b92a30278841
PROTOCOL_SHA256=13519fb5c86fdf690d233c54dd45c3242ba348f3c7f66587238e6965ed1c49ff
TIER_CONTRACTS_CSV_SHA256=2ff57eadb872ca6aa10cb84aa4fdf9b7250715df5ca77d2f3e9d22621e7d762a

## Fixed architecture and ordered locks

Order: R1 -> lock R1 -> R2 -> lock R2 -> R3 -> lock R3 -> R4 -> lock R4 -> R5 -> lock R5 -> R6 -> lock R6.
Outcome level TM/ha, frozen crop windows, linear additive form, district and period FE, and
unweighted estimation are retained. Only the designated tier component may change.
All future result tables must reference the immutable ER1 numerical identity.
No smaller p-value, preferred sign, narrower interval, model fit, or biological narrative
may replace ER1 or change a later-tier contract. Cross-tier contamination is prohibited.

## R1_LEVEL_CLIMATE_FAMILY

Protocol fields below are requirements, not computed results.

```json
{
  "claim_ceiling": "EMPIRICAL_ASSOCIATION_CLIMATE_RESPONSE_ONLY",
  "confidence_intervals": "UNADJUSTED_95_PERCENT_CR2_SATTERTHWAITE",
  "diagnostic_crops": [
    "13010210000",
    "13010170102",
    "15010040000"
  ],
  "diagnostics_not_distinct_models": 3,
  "distinct_coefficients": 6,
  "distinct_crops": [
    "14010020000",
    "14010070000"
  ],
  "distinct_models": 2,
  "district_fe": "REQUIRED",
  "er1_numerical_results_identity": "40e0f58269dda309e83a1fa3da17ef4d5dc5523efc72a666f734d0ebacb76b24",
  "execution_authorized": false,
  "family": "LEVEL",
  "functional_form": "LINEAR_ADDITIVE",
  "global_five_crop_fwer": "NOT_CLAIMED",
  "inference": "CR2_SATTERTHWAITE_AND_CROP_AHT",
  "multiplicity": "HOLM_STEP_DOWN_WITHIN_CROP_R1_COEFFICIENT_P_VALUES",
  "multiplicity_adjusted_confidence_intervals": "NOT_CONSTRUCTED_NOT_CLAIMED",
  "next_tier": "R2",
  "order": 1,
  "outcome_scale": "YIELD_LEVEL_TM_PER_HA",
  "perennial_equivalence": {
    "distinct_robustness_count_contribution": 0,
    "ed1_design_absolute_tolerance": 1e-09,
    "exact_coefficient_and_fitted_value_equality_required_for_status": true,
    "on_nonexact_equality": "HOLD_FOR_ADJUDICATION_NO_DISTINCT_ROBUSTNESS_PROMOTION",
    "record_exact_equality_separately_from_tolerance_diagnostic": true,
    "transformed_design_check": "ED1_FROZEN_GEOMETRY_TOLERANCE"
  },
  "perennial_status_on_exact_equivalence": "FE_EQUIVALENT_DIAGNOSTIC_NOT_DISTINCT_MODEL",
  "period_fe": "REQUIRED",
  "previous_tier": null,
  "primary_replacement": "PROHIBITED",
  "regressors": [
    "RAIN_MM",
    "TMAX_C",
    "TMIN_C"
  ],
  "role": "CROP_SPECIFIC_LEVEL_ROBUSTNESS_AND_FE_EQUIVALENCE_DIAGNOSTIC",
  "same_primary_sample": true,
  "status": "NOT_EXECUTED",
  "tier": "R1",
  "tier_id": "R1_LEVEL_CLIMATE_FAMILY",
  "weighting": "UNWEIGHTED_PRIMARY_ESTIMATION",
  "windows": "EXACT_ED1_FROZEN"
}
```

## R2_STANDARDIZED_ANOMALY_COMPARABILITY

Protocol fields below are requirements, not computed results.

```json
{
  "claim_ceiling": "EMPIRICAL_ASSOCIATION_CLIMATE_RESPONSE_ONLY",
  "coefficient_count": 21,
  "confidence_intervals": "UNADJUSTED_95_PERCENT_CR2_SATTERTHWAITE",
  "cross_crop_magnitude_ranking": "PROHIBITED",
  "cross_crop_significance_ranking": "PROHIBITED",
  "district_fe": "REQUIRED",
  "er1_numerical_results_identity": "40e0f58269dda309e83a1fa3da17ef4d5dc5523efc72a666f734d0ebacb76b24",
  "execution_authorized": false,
  "family": "STANDARDIZED_ANOMALY",
  "fully_standardized_effect_sizes": "NOT_CLAIMED",
  "functional_form": "LINEAR_ADDITIVE",
  "global_five_crop_fwer": "NOT_CLAIMED",
  "inference": "CR2_SATTERTHWAITE_AND_CROP_AHT",
  "interpretation": "ONE_LOCAL_CLIMATE_SD_CHANGE_IN_NATIVE_CROP_YIELD_UNITS",
  "models": 5,
  "multiplicity": "HOLM_STEP_DOWN_WITHIN_CROP_R2_COEFFICIENT_P_VALUES",
  "multiplicity_adjusted_confidence_intervals": "NOT_CONSTRUCTED_NOT_CLAIMED",
  "next_tier": "R3",
  "order": 2,
  "outcome_scale": "YIELD_LEVEL_TM_PER_HA",
  "period_fe": "REQUIRED",
  "previous_tier": "R1",
  "primary_replacement": "PROHIBITED",
  "regressors": [
    "RAIN_Z",
    "TMAX_Z",
    "TMIN_Z"
  ],
  "role": "STANDARDIZED_X_COMPARABILITY",
  "same_primary_sample": true,
  "status": "NOT_EXECUTED",
  "tier": "R2",
  "tier_id": "R2_STANDARDIZED_ANOMALY_COMPARABILITY",
  "time_variants": "EXACT_ED1_T_AND_T_MINUS_1_WHERE_APPLICABLE",
  "weighting": "UNWEIGHTED_PRIMARY_ESTIMATION",
  "windows": "EXACT_ED1_FROZEN"
}
```

## R3_RESTRICTED_WILD_CLUSTER_BOOTSTRAP

Protocol fields below are requirements, not computed results.

```json
{
  "claim_ceiling": "EMPIRICAL_ASSOCIATION_CLIMATE_RESPONSE_ONLY",
  "cluster": "DISTRICT",
  "coefficient_statistic": "ABSOLUTE_BOOTSTRAP_T",
  "coefficient_tests": 21,
  "coefficients": "EXACT_ER1_PRIMARY_UNCHANGED",
  "determinism": {
    "batch_size": 1000,
    "cluster_order": "SORTED_UBIGEO",
    "coefficient_order": "FROZEN_ED1_REGRESSOR_ORDER",
    "crop_order": [
      "14010020000",
      "14010070000",
      "13010210000",
      "13010170102",
      "15010040000"
    ],
    "exceedance": "GREATER_THAN_OR_EQUAL_TO_OBSERVED_STATISTIC",
    "rng": "NUMPY_GENERATOR_PCG64",
    "row_order": "SORTED_UBIGEO_THEN_FROZEN_PERIOD",
    "seed_reset": "EACH_CROP_CONTRAST_AND_JOINT_TEST",
    "weight_draw_layout": "N_CLUSTERS_BY_BATCH_INT8_ZERO_ONE_MAPPED_TO_MINUS_PLUS_ONE"
  },
  "district_fe": "REQUIRED",
  "er1_numerical_results_identity": "40e0f58269dda309e83a1fa3da17ef4d5dc5523efc72a666f734d0ebacb76b24",
  "execution_authorized": false,
  "family": "PHYSICAL_ANOMALY",
  "finite_replication_correction": "(1 + exceedances)/(B + 1)",
  "functional_form": "LINEAR_ADDITIVE",
  "global_five_crop_fwer": "NOT_CLAIMED",
  "implementation_requirement": "Frozen ED1 API targets FIRST_CLIMATE_COEFFICIENT or ALL_CLIMATE_COEFFICIENTS only. Future coefficient-target adapter must cover each named coefficient without changing the full model and must validate contrast/permutation equivalence on synthetic data before real R3 execution. No adapter or bootstrap is executed during ER2P.",
  "invalid_replications": "REQUIRE_ZERO_OTHERWISE_HOLD_NO_DROPPING_OR_REDRAWING_OR_DENOMINATOR_CHANGE",
  "joint_null": "ALL_PRIMARY_CLIMATE_COEFFICIENTS_EQUAL_ZERO_WITHIN_CROP",
  "joint_null_matches_aht": true,
  "joint_statistic": "BOOTSTRAP_WALD_F",
  "joint_tests": 5,
  "mixed_cr2_wcr_holm_family": "PROHIBITED",
  "multiplicity": "WITHIN_CROP_WCR_COEFFICIENT_P_VALUES",
  "multiplicity_adjusted_confidence_intervals": "NOT_CONSTRUCTED_NOT_CLAIMED",
  "next_tier": "R4",
  "null_imposed": true,
  "order": 3,
  "outcome_scale": "YIELD_LEVEL_TM_PER_HA",
  "period_fe": "REQUIRED",
  "previous_tier": "R2",
  "primary_replacement": "PROHIBITED",
  "replications": 9999,
  "reported_fields": [
    "ER1_BETA_REFERENCE",
    "ER1_CR2_P_REFERENCE",
    "WCR_P",
    "WITHIN_CROP_HOLM_WCR_P"
  ],
  "restricted": true,
  "role": "INFERENCE_ONLY",
  "same_primary_sample": true,
  "seed": 20260903,
  "status": "NOT_EXECUTED",
  "tier": "R3",
  "tier_id": "R3_RESTRICTED_WILD_CLUSTER_BOOTSTRAP",
  "weighting": "UNWEIGHTED_PRIMARY_ESTIMATION",
  "weights": "RADEMACHER",
  "windows": "EXACT_ED1_FROZEN"
}
```

## R4_SPATIAL_HAC

Protocol fields below are requirements, not computed results.

```json
{
  "bandwidth_selection": "PROHIBITED",
  "bandwidths_km": [
    50,
    100,
    150
  ],
  "claim_ceiling": "EMPIRICAL_ASSOCIATION_CLIMATE_RESPONSE_ONLY",
  "coefficient_bandwidth_rows": 63,
  "coefficients": "EXACT_ER1_PRIMARY_UNCHANGED",
  "coordinate_construction": "PROJECT_FROZEN_DISTRICT_GEOMETRY_THEN_CENTROID_AS_ED1",
  "coordinates": "EPSG:32717_DISTRICT_CENTROIDS",
  "distance": "EUCLIDEAN_PROJECTED_METRES_DIVIDED_BY_1000",
  "district_fe": "REQUIRED",
  "er1_numerical_results_identity": "40e0f58269dda309e83a1fa3da17ef4d5dc5523efc72a666f734d0ebacb76b24",
  "execution_authorized": false,
  "family": "PHYSICAL_ANOMALY",
  "functional_form": "LINEAR_ADDITIVE",
  "global_five_crop_fwer": "NOT_CLAIMED",
  "interval": "ER1_BETA_PLUS_MINUS_1.959963984540054_TIMES_CONLEY_SE",
  "kernel": "BARTLETT",
  "multiplicity": "DIAGNOSTIC_ROBUSTNESS_NO_NEW_CONFIRMATORY_FWER_CLAIM",
  "multiplicity_adjusted_confidence_intervals": "NOT_CONSTRUCTED_NOT_CLAIMED",
  "next_tier": "R5",
  "nonpositive_or_nonfinite_variance": "HOLD_NO_CLIPPING_OR_COVARIANCE_SUBSTITUTION",
  "normal_critical_value": 1.959963984540054,
  "order": 4,
  "outcome_scale": "YIELD_LEVEL_TM_PER_HA",
  "p_value": "2_TIMES_STANDARD_NORMAL_SURVIVAL_ABS_Z",
  "p_values": "RAW_ALL_THREE_BANDWIDTHS_NO_SEPARATE_HOLM_FAMILIES",
  "pairing": "SAME_PERIOD_ONLY",
  "period_fe": "REQUIRED",
  "previous_tier": "R3",
  "primary_replacement": "PROHIBITED",
  "replaces_primary_cr2": false,
  "reported_fields": [
    "ER1_BETA_REFERENCE",
    "CONLEY_SE",
    "Z",
    "TWO_SIDED_ASYMPTOTIC_P",
    "NORMAL_CI95_LOWER",
    "NORMAL_CI95_UPPER"
  ],
  "residual_specification": "EXACT_ER1_PRIMARY",
  "role": "ASYMPTOTIC_SPATIAL_HAC_ROBUSTNESS_DIAGNOSTIC",
  "same_primary_sample": true,
  "satterthwaite_df": "NOT_CLAIMED",
  "status": "NOT_EXECUTED",
  "tier": "R4",
  "tier_id": "R4_SPATIAL_HAC",
  "weighting": "UNWEIGHTED_PRIMARY_ESTIMATION",
  "windows": "EXACT_ED1_FROZEN"
}
```

## R5_LEAVE_ONE_PERIOD_OUT_ALL_PERIODS

Protocol fields below are requirements, not computed results.

```json
{
  "claim_ceiling": "EMPIRICAL_ASSOCIATION_CLIMATE_RESPONSE_ONLY",
  "crop_aht_range": "NOT_REQUESTED_OPTIONAL_EXTENSION_NOT_EXECUTED",
  "district_fe": "REQUIRED",
  "er1_numerical_results_identity": "40e0f58269dda309e83a1fa3da17ef4d5dc5523efc72a666f734d0ebacb76b24",
  "execution_authorized": false,
  "expected_models": 38,
  "expected_models_by_crop": {
    "13010170102": 8,
    "13010210000": 8,
    "14010020000": 7,
    "14010070000": 7,
    "15010040000": 8
  },
  "failed_omission": "RETAIN_STATUS_ROW_HOLD_FOR_ADJUDICATION_NO_REPLACEMENT_OR_PARTIAL_DISTRIBUTION_CLAIM",
  "family": "PHYSICAL_ANOMALY",
  "functional_form": "LINEAR_ADDITIVE",
  "global_five_crop_fwer": "NOT_CLAIMED",
  "influential_district_deletion": "PROHIBITED",
  "mandatory_named_reporting": [
    "LEAVE_2017_OUT",
    "LEAVE_2023_OUT"
  ],
  "max_deviation_tie_rule": "REPORT_ALL_TIED_PERIOD_IDS_SORTED_NO_POST_RESULT_TIE_SELECTION",
  "multiplicity": "DESCRIPTIVE_COEFFICIENT_DISTRIBUTIONS_NO_SIGNIFICANCE_VOTE_COUNTING",
  "multiplicity_adjusted_confidence_intervals": "NOT_CONSTRUCTED_NOT_CLAIMED",
  "named_perennial_mapping": {
    "LEAVE_2017_OUT": "2017",
    "LEAVE_2023_OUT": "2023"
  },
  "named_transient_mapping": {
    "LEAVE_2017_OUT": "2016/2017",
    "LEAVE_2023_OUT": "2022/2023"
  },
  "next_tier": "R6",
  "order": 5,
  "outcome_scale": "YIELD_LEVEL_TM_PER_HA",
  "period_fe": "REQUIRED",
  "period_id_by_regime": {
    "perennial": "REFERENCE_PERIOD_ID",
    "transient": "CAMPAIGN_ID"
  },
  "period_source": "SORTED_UNIQUE_PERIODS_OF_EACH_EXACT_ER1_ANALYTICAL_SAMPLE",
  "positive_negative_rule": "STRICTLY_GREATER_LESS_THAN_ZERO_REPORT_EXACT_ZERO_COUNT_SEPARATELY",
  "previous_tier": "R4",
  "primary_replacement": "PROHIBITED",
  "remaining_period_fe": "REQUIRED",
  "report_all_periods": true,
  "role": "ALL_PERIOD_INFLUENCE_DESCRIPTION",
  "same_regressors": true,
  "sample_change": "ONE_ENTIRE_PERIOD_OMITTED_PER_MODEL_ONLY",
  "second_period_omission": "PROHIBITED",
  "sign_reversal_rule": "PRODUCT_OF_LOO_AND_PRIMARY_BETA_STRICTLY_NEGATIVE",
  "stability_classification": "DESCRIPTIVE_NO_ARBITRARY_PASS_FAIL_THRESHOLD",
  "status": "NOT_EXECUTED",
  "summary_metrics": [
    "PRIMARY_BETA_REFERENCE",
    "MIN_LOO_BETA",
    "MAX_LOO_BETA",
    "MEDIAN_LOO_BETA",
    "POSITIVE_COUNT",
    "NEGATIVE_COUNT",
    "SIGN_REVERSALS_RELATIVE_TO_PRIMARY",
    "MAX_ABSOLUTE_BETA_DEVIATION",
    "PERIOD_CAUSING_MAX_ABSOLUTE_DEVIATION"
  ],
  "tier": "R5",
  "tier_id": "R5_LEAVE_ONE_PERIOD_OUT_ALL_PERIODS",
  "weighting": "UNWEIGHTED_PRIMARY_ESTIMATION",
  "windows": "EXACT_ED1_FROZEN",
  "zero_primary_sign_rule": "REVERSAL_COUNT_NULL_WITH_NOT_DEFINED_PRIMARY_ZERO_STATUS"
}
```

## R6_B3_STRICT_EXPOSURE

Protocol fields below are requirements, not computed results.

```json
{
  "claim_ceiling": "EMPIRICAL_ASSOCIATION_CLIMATE_RESPONSE_ONLY",
  "disagreement_proves_correct_exposure": false,
  "district_fe": "REQUIRED",
  "er1_numerical_results_identity": "40e0f58269dda309e83a1fa3da17ef4d5dc5523efc72a666f734d0ebacb76b24",
  "execution_authorized": false,
  "family": "PHYSICAL_ANOMALY",
  "functional_form": "LINEAR_ADDITIVE",
  "global_five_crop_fwer": "NOT_CLAIMED",
  "mad": {
    "crop_code": "14010070000",
    "estimate": false,
    "status": "NOT_ESTIMABLE_UNDER_PRIMARY_DESIGN",
    "substitute_model": "PROHIBITED"
  },
  "multiplicity": "DIAGNOSTIC_RAW_CR2_AND_AHT_NO_NEW_CONFIRMATORY_FWER_CLAIM",
  "multiplicity_adjusted_confidence_intervals": "NOT_CONSTRUCTED_NOT_CLAIMED",
  "next_tier": null,
  "order": 6,
  "outcome_scale": "YIELD_LEVEL_TM_PER_HA",
  "perennials": "NOT_APPLICABLE",
  "period_fe": "REQUIRED",
  "previous_tier": "R5",
  "primary_replacement": "PROHIBITED",
  "prominent_support_comparison_to_er1": true,
  "rice": {
    "admissibility": "FULL_WITHIN_RANK_VALID_CR2_ADJUSTMENTS_POSITIVE_FINITE_SE_AND_DF_VALID_FINITE_AHT",
    "campaign_fe": "REQUIRED",
    "coefficient_count": 3,
    "crop_code": "14010020000",
    "expected_districts": 12,
    "expected_observations": 31,
    "expected_periods": 7,
    "inference": "CR2_SATTERTHWAITE_AHT_ONLY_IF_NUMERICALLY_ADMISSIBLE",
    "may_weaken_fe": false,
    "on_inadmissibility": "R6_RICE_NOT_INFERENTIALLY_ADMISSIBLE",
    "required_within_rank": 3,
    "status": "ESTIMABLE_WITH_SEVERE_SUPPORT_LIMITATION"
  },
  "role": "STRICT_CAMPAIGN_ATTRIBUTION_SENSITIVITY_SEVERE_SUPPORT_LIMITATION",
  "sample_change": "EXACT_D0_OUTCOME_AND_B3_VALID_EXPOSURE_INTERSECTION",
  "status": "NOT_EXECUTED",
  "tier": "R6",
  "tier_id": "R6_B3_STRICT_EXPOSURE",
  "weighting": "UNWEIGHTED_PRIMARY_ESTIMATION",
  "windows": "EXACT_ED1_FROZEN"
}
```

## Lock schema and failure handling

Each future tier lock must contain the following required fields:

schema_version, er1_freeze_sha, ed1_freeze_sha, er1_numerical_results_identity, er1_reporting_lock_sha256, er2p_protocol_sha256, tier_id, tier_order, exact_input_sha256, exact_model_contract, tier_contract_sha256, implementation_sha256, environment, results, interpretation_firewall, previous_tier_lock_sha256, completion_status, next_tier_authorization_status

Serialize sorted-key JSON as UTF-8, LF only, exactly one final LF, no BOM, no NaN,
no timestamp or machine-specific runtime path. Record versions/backend metadata.
Compute the SHA-256 outside its own lock, then record it in the next tier's predecessor field.
R1 has no predecessor; R2-R6 must verify the immediately previous immutable lock, all input
and result hashes, complete inventory, unchanged protocol/contract hashes and authorization.
A hash alone is not authorization. A separate Director execution gate is required.
Unexpected failures produce an explicit status and halt progression; no silent substitutions.
Completed locks cannot be revised in response to later results. R6 MAD nonestimability and
declared Rice inferential inadmissibility are terminal reported outcomes, not weaker models.
One controlled future execution session is permitted; separate tier commits are not required.

## Concordance and result-specific firewalls

After all six locks, describe all 21 primary coefficient identities across sign, WCR, spatial
interval inclusion, complete LOO distributions and applicable strict-support sensitivity.
Do not compute a robustness score, count significant models, vote on a majority, or label
'5 of 7 robust'. Nonapplicability is an explicit status, never a zero or a negative vote.
Known Banana and Lemon results cannot create special tests, nonlinear terms, selected
bandwidths or selected omissions. Do not rank crops by standardized-X coefficient magnitude.

CLAIM_CEILING=EMPIRICAL_ASSOCIATION_CLIMATE_RESPONSE_ONLY
Use consistency, sensitivity, sign stability, inferential sensitivity, spatial-covariance
sensitivity or exposure-definition sensitivity. No causal robustness claim is authorized.

## Implementation boundaries and audit

This builder uses only the standard library: static contracts, hashes and Git identity checks.
It neither imports econometric engines nor fits primary or robustness models.
R3's future target-coefficient adapter is required because the frozen ED1 API exposes only
first-coefficient and all-coefficient contrasts. It must be validated before real R3 execution.
R1 exact numerical equality is not inferred from ED1's 1e-9 transformed-design tolerance.
Nonexact equality requires adjudication and cannot promote equivalent models to distinct evidence.
Repository baseline before the new tests: 655 run, 602 pass, 50 fail, 3 errors.
The 53 expected nonpasses are enumerated with reasons in the protocol: 47 lifecycle and 6 phase firewalls.
ED1 and ER1 class setup guards require E1 and ED1 authoring parents; the E1 rebuild requires S1.
Compare exact identifiers AND result types and review traceback causes after the full suite.
An unchanged historical inventory is not an all-green test suite. New or unexplained failures block ER2P.
Historical scientific inputs, historical tests, README, main and all Git refs must remain unchanged.

## Authorization

ROBUSTNESS_RESULTS_KNOWN=FALSE
ER2P_FREEZE_AUTHORIZED=NO
ROBUSTNESS_EXECUTION_AUTHORIZED=NO
ENSO_SCENARIOS=NOT_EXECUTED; GVP=NOT_EXECUTED; VAR_CVAR=NOT_EXECUTED; A1_A2=NOT_EXECUTED; OPTIMIZATION=NOT_EXECUTED
FINAL_VERDICT=ER2P_PASS_ROBUSTNESS_PROTOCOL_READY_FOR_DIRECTOR_FREEZE_DECISION
NEXT_ACTION=RETURN_TO_SCIENTIFIC_DIRECTOR_FOR_ER2P_FREEZE_DECISION_IF_PASS
