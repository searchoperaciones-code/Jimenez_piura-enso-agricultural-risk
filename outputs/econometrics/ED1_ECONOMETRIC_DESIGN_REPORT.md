# ED1H Econometric Design Master v1 - Targeted pre-freeze hardening

## 1. ED1 verdict

`ED1H_PASS_HARDENED_DESIGN_READY_FOR_DIRECTOR_FREEZE_DECISION`. The substantive ED1 design is preserved. This is not authorization to estimate real outcomes or freeze. `ED1H_FREEZE_AUTHORIZED=NO`.

## 2. E1 / upstream preflight

E1 HEAD, `origin/phase/e1-primary-transient-exposure-v1`, and `e1-primary-transient-exposure-v1-freeze` resolve to `cdeb14bdda8bdebf33afdebcf0e135179bd2f485`. All pinned E1, D0/S1-linked, phenology, perennial exposure, B3, boundary, and support artifacts pass SHA-256 verification.

## 3. Outcome-blindness audit

`REAL_OUTCOME_VALUES_READ=FALSE`; `REAL_REGRESSIONS=0`. ED1H reads only climate X, frozen validity flags, structural keys, and aggregate support counts. Synthetic responses are SHA-256 functions of district and period keys only; all computed coefficients, residuals, test statistics, and p-values are implementation diagnostics without scientific interpretation.

## 4. Five crop analytical support

| Crop | Observations | Districts | Periods | Climate coefficients | Geometry |
|---|---:|---:|---:|---:|---|
| RICE | 281 | 44 | 7 | 3 | PASS |
| MAIZ_AMARILLO_DURO | 318 | 54 | 7 | 3 | PASS |
| MANGO | 255 | 36 | 8 | 3 | PASS |
| LIMON_SUTIL | 311 | 44 | 8 | 6 | PASS |
| PLATANOS_Y_BANANAS | 390 | 54 | 8 | 6 | PASS |

## 5. Outcome-scale adjudication

`YIELD_LEVEL_TM_PER_HA` is primary. Frozen metadata certifies the physical unit but not strict positivity, so a log design would require opening outcome support and a retransformation rule. Level yield preserves additive physical and later scenario interpretation. Log yield is not authorized in ED1 v1 absent a separate pre-estimation gate.

## 6. Climate-family adjudication

`PHYSICAL_ANOMALY=PRIMARY` and `STANDARDIZED_ANOMALY=SECONDARY_COMPARABILITY`. Exact required-FE analysis makes `LEVEL` a distinct robustness family only for Rice/MAD; for Mango/Lemon/Banana it is an FE-equivalent diagnostic, not a distinct robustness specification.

| Crop | Max transformed-X discrepancy | Combined rank | FE-equivalent | LEVEL role |
|---|---:|---:|---|---|
| RICE | 72.840084175532 | 6 | NO | DISTINCT_CLIMATE_FAMILY_ROBUSTNESS |
| MAIZ_AMARILLO_DURO | 502.377875073874 | 6 | NO | DISTINCT_CLIMATE_FAMILY_ROBUSTNESS |
| MANGO | 0.0 | 3 | YES | FE_EQUIVALENT_DIAGNOSTIC_NOT_DISTINCT_ROBUSTNESS |
| LIMON_SUTIL | 4e-12 | 6 | YES | FE_EQUIVALENT_DIAGNOSTIC_NOT_DISTINCT_ROBUSTNESS |
| PLATANOS_Y_BANANAS | 6e-12 | 6 | YES | FE_EQUIVALENT_DIAGNOSTIC_NOT_DISTINCT_ROBUSTNESS |

## 7. Fixed-effect contract

District FE and period FE are required. Period means agricultural campaign for Rice/MAD and calendar year for perennials. District-specific trends are prohibited. Identification is the remaining within-district/cross-district climate variation conditional on region-wide period shocks.

## 8. Transient model contract

Rice and MAD are separate unweighted linear models on the frozen D0-valid and E1-valid intersection. Each contains three physical-anomaly regressors, district FE, campaign FE, and no pooled crop coefficient.

## 9. Mango model contract

Mango uses `MANGO_MAY_JUN_CURRENT_YEAR`, three physical-anomaly regressors, district FE, and calendar-year FE in a separate crop model.

## 10. Lemon t / t-1 adjudication

`P1_JOINT_T_AND_T_MINUS_1_LINEAR` passes X-only geometry: rank 6/6, condition number 2.223403539903, maximum VIF 1.609280256563, and implied residual df 254. Both frozen windows remain; no winner is selected.

## 11. Banana t / t-1 adjudication

`P1_JOINT_T_AND_T_MINUS_1_LINEAR` passes X-only geometry: rank 6/6, condition number 2.150899653983, maximum VIF 1.558168978851, and implied residual df 323. Both frozen windows remain; no winner is selected.

## 12. X-only geometry / collinearity

The support matrix contains 29 prespecified X-only rows across all climate families, separate and joint perennial candidates, and B3. Every primary row has full within rank, nonzero within variance, condition number below 30, maximum VIF below 10, positive residual df, and feasible computation. Leverage is disclosed, never used to delete observations.

| Crop | Nominal clusters | Effective clusters | Zero contribution | Singletons | CR2 extra singularities |
|---|---:|---:|---:|---:|---:|
| RICE | 44 | 43 | 1 | 1 | 0 |
| MAIZ_AMARILLO_DURO | 54 | 52 | 2 | 2 | 0 |
| MANGO | 36 | 35 | 1 | 1 | 0 |
| LIMON_SUTIL | 44 | 43 | 1 | 1 | 0 |
| PLATANOS_Y_BANANAS | 54 | 50 | 4 | 4 | 0 |

## 13. Complexity budget

Rice, MAD, and Mango use exactly three climate coefficients. Lemon and Banana use exactly six in the joint-window architecture. No interaction, quadratic, spline, threshold, bin, GDD, or event transformation is authorized.

## 14. Primary sample contract

The transient primary sample is exactly 599 frozen joint-valid observations: Rice 281 and MAD 318. Perennial structural samples are Mango 255, Lemon 311, and Banana 390. No outcome, residual, influence, or significance restriction is added.

## 15. Identified-weight rule

`IDENTIFIED_WEIGHT_USAGE=DIAGNOSTIC_ONLY_NOT_REGRESSION_WEIGHT_NOT_PRIMARY_FILTER`. All E1-valid primary observations remain. No cutoff is introduced; B3 is the only prespecified attribution-quality sensitivity.

## 16. Regression-weighting rule

`UNWEIGHTED_PRIMARY_ESTIMATION`. Harvest, production, price, outcome-derived precision, and identified-fraction weights are prohibited in the primary design.

## 17. Primary inference contract

The executable path is project-local Python 3.11.7 with NumPy 2.3.5 and SciPy 1.16.3: `fit_two_way_fe_cr2` performs SVD two-way-FE absorption, OLS, identity-target CR2, coefficient Satterthwaite df, and `_aht_htz` joint tests. Float64, `rcond=1e-12` Moore-Penrose inverses, symmetric eigen pseudoinverse roots, and district clusters are fixed conventions.

Independent full-design SVD validation is `PASS` at tolerance 1e-09: coefficient, CR2 covariance, Satterthwaite df, AHT F, and AHT denominator-df maximum discrepancies are {"aht_denominator_df_max_abs_difference":0.0,"aht_f_max_abs_difference":0.0,"coefficient_max_abs_difference":0.0,"cr2_covariance_max_abs_difference":0.0,"satterthwaite_df_max_abs_difference":0.0}.

| Crop | Satterthwaite df min | Satterthwaite df max | AHT denominator df | Non-finite |
|---|---:|---:|---:|---:|
| RICE | 4.919993824254 | 20.757481078568 | 13.669073909695 | 0 |
| MAIZ_AMARILLO_DURO | 25.033294856014 | 33.668899333873 | 27.897829152252 | 0 |
| MANGO | 11.297143280447 | 20.485841446325 | 17.886323560203 | 0 |
| LIMON_SUTIL | 21.074213238521 | 29.81409391343 | 23.648451534646 | 0 |
| PLATANOS_Y_BANANAS | 28.151260680063 | 33.098150195914 | 29.959140522382 | 0 |

## 18. Wild cluster bootstrap contract

Restricted null-imposed wild cluster bootstrap-t is mandatory where computationally valid: district clusters, Rademacher weights, 9,999 replications, seed 20260903, and `(1+exceedances)/(B+1)`. The actual engine ran all 9,999 synthetic replications twice for an individual coefficient and a joint climate restriction with `PASS`, zero invalid replications, coefficient digest `bb9e44414892945054b45d5d046b4251a59ea51f49db453ee5162a0d8aded4a5`, and joint digest `b38de51dcef23e2dee2006da760984e797be750fdbd95ea7ebf9371d58177b27`. Future execution covers each primary climate coefficient and the prespecified omnibus climate test and cannot select variables.

## 19. Spatial dependence contract

`SPATIAL_HAC_ROLE=ROBUSTNESS_ONLY`. `conley_covariance` constructed finite synthetic-residual covariance matrices for all five crops at 50, 100, and 150 km (`PASS_ALL_FIVE_CROPS_ALL_THREE_BANDWIDTHS`). It uses EPSG:32717 district centroids, Bartlett distance weights, and same-period pairs. None is selected by residuals or outcomes.

## 20. Driscoll-Kraay / two-way cluster status

`DRISCOLL_KRAAY=NOT_AUTHORIZED_T_7_OR_8` and `TWO_WAY_CLUSTERING=NOT_AUTHORIZED_FEW_PERIOD_CLUSTERS`. Neither enters an estimator tournament or substitutes for primary district CR2 inference.

## 21. Extreme-year influence contract

2017 and 2023 remain in primary samples without trimming or winsorization. `LEAVE_ONE_PERIOD_OUT_ALL_PERIODS` is required later, including named leave-2017-out and leave-2023-out reporting. No omission becomes primary.

## 22. B3 econometric sensitivity contract

Rice B3 is estimable only as a severe-support-limitation sensitivity (31 observations, 12 districts, rank 3/3, residual df 10). MAD B3 is `B3_ECONOMETRIC_SENSITIVITY_NOT_ESTIMABLE_UNDER_PRIMARY_DESIGN` (7 observations, rank 1/3, residual df 0). Required FE are not weakened.

## 23. Cross-crop comparability contract

Standardized-anomaly secondary models are the comparison channel. Their exact interpretation is `ONE_LOCAL_CLIMATE_SD_CHANGE_IN_NATIVE_CROP_YIELD_UNITS`; the yield outcome remains unstandardized. Direction, uncertainty, qualitative pattern, channel consistency, and native-yield response to a local one-SD climate perturbation may be compared. `CROSS_CROP_COEFFICIENT_MAGNITUDE_RANKING=NOT_AUTHORIZED`.

## 24. Robustness hierarchy

The exact order is `PRIMARY`, `R1_LEVEL_CLIMATE_FAMILY`, `R2_STANDARDIZED_ANOMALY_COMPARABILITY`, `R3_RESTRICTED_WILD_CLUSTER_BOOTSTRAP`, `R4_SPATIAL_HAC`, `R5_LEAVE_ONE_PERIOD_OUT_ALL_PERIODS`, and `R6_B3_STRICT_EXPOSURE`. R1 has a crop-specific role: distinct robustness for Rice/MAD and FE-equivalent diagnostic for perennials. No result may reorder or replace this hierarchy.

Within each crop, Holm step-down applies to primary climate coefficients and unadjusted results remain reported. `GLOBAL_FIVE_CROP_FAMILYWISE_ERROR_CONTROL=NOT_CLAIMED`; `CROSS_CROP_SIGNIFICANCE_RANKING=PROHIBITED`.

## 25. Future scenario-propagation covenant

No scenario is built. A later gate must separate the climate-response component, district historical baseline, climate-scenario uncertainty, coefficient/inference uncertainty, and residual/process uncertainty. It must not invent or forecast a future period FE.

## 26. Created candidate artifacts

- `config/econometrics/econometric_design_master_v1.json`: `feaddf35700a84592ba024ae1fb9e4c9419e00672828fdb7cb29f2775d933c6d`
- `outputs/econometrics/ED1_MODEL_CONTRACTS.csv`: `7dcd316c7b47b3a2e15939ed25dea8e034f1ca7c5076013c7640ef11da74cbcf`
- `outputs/econometrics/ED1_X_GEOMETRY.csv`: `08d569170ebc5bc3a5a4a35cdc702807be46a34df371e9363af510d7d0cca962`
- `outputs/econometrics/ED1_INFERENCE_MATRIX.csv`: `5cabcf5ab6d7cba1b6bf765e7727f9de1f090cc9b8a503364582a539701c7fab`
- `outputs/econometrics/ED1_ROBUSTNESS_HIERARCHY.csv`: `87959f394c3b6d486523e216dc61a0a7fca29a99d2e688ac5e80317162a4c3e1`

The generator and tests are `scripts/econometric_design_master_v1.py` and `tests/test_econometric_design_master_v1.py`. No coefficient or result table exists.

## 27. ED1 test results

The ED1 test contract is extended without removing prior tests. It now executes the concrete inference path, structural-key synthetic-response firewall, effective-cluster accounting, CR2/Satterthwaite/AHT feasibility, 9,999-replication WCR determinism, Conley finiteness, FE equivalence, cross-crop interpretation, multiplicity firewalls, and exact prior error adjudication.

## 28. Full-suite adjudication

The previous full suite ran 693 tests: 642 pass, 50 fail, and 1 error. All 51 exact nonpasses are machine-readable in the config: 45 expected historical lifecycle states and 6 expected active-phase firewalls; real regression, environmental blocker affecting ED1, and unresolved counts are zero. The sole error is `tests/test_primary_transient_exposure_v1.py::PrimaryTransientExposureV1Tests.test_28_two_independent_builds_are_byte_identical`, a RuntimeError because the historical E1 rebuild guard requires S1 HEAD while ED1 runs at frozen E1 HEAD. Recreated at S1 HEAD with the exact seven-file E1 candidate scope and LF-preserving checkout, that test ran 1/1 OK; the temporary worktree was removed.

## 29. Findings by severity

Critical findings: 0. Major findings: 0. All primary inference-engine diagnostics pass. Design limitation: B3 strict sensitivity is sparse for Rice and not estimable for MAD under the required primary FE architecture.

## 30. Exact next action

`RETURN_TO_SCIENTIFIC_DIRECTOR_FOR_ED1_FREEZE_DECISION_IF_PASS`. Do not estimate real outcomes, stage, commit, push, or tag under this gate.

PROJECT =
ENSO_EL_NINO_2026_2027_AGRICULTURE_PIURA

GATE =
ED1H_TARGETED_PRE_FREEZE_ECONOMETRIC_DESIGN_HARDENING

E1_FREEZE_SHA =
cdeb14bdda8bdebf33afdebcf0e135179bd2f485

E1_STATUS =
PASS_FROZEN

REAL_OUTCOME_VALUES_READ =
FALSE

PRIMARY_MODELS =
FIVE_CROP_SPECIFIC_MODELS

DISTRICT_FE = REQUIRED

PERIOD_FE = REQUIRED

OUTCOME_SCALE = YIELD_LEVEL_TM_PER_HA

PRIMARY_CLIMATE_FAMILY = PHYSICAL_ANOMALY

SECONDARY_COMPARABILITY_FAMILY = STANDARDIZED_ANOMALY

TRANSIENT_LEVEL_ROLE = DISTINCT_CLIMATE_FAMILY_ROBUSTNESS

PERENNIAL_LEVEL_ROLE = FE_EQUIVALENT_DIAGNOSTIC_NOT_DISTINCT_ROBUSTNESS

PRIMARY_FUNCTIONAL_FORM = LINEAR_ADDITIVE

TRANSIENT_PRIMARY_SAMPLE = 599

PRIMARY_REGRESSION_WEIGHTING = UNWEIGHTED_PRIMARY_ESTIMATION

IDENTIFIED_WEIGHT_USAGE = DIAGNOSTIC_ONLY_NOT_REGRESSION_WEIGHT_NOT_PRIMARY_FILTER

LEMON_WINDOW_ARCHITECTURE = P1_JOINT_T_AND_T_MINUS_1_LINEAR

BANANA_WINDOW_ARCHITECTURE = P1_JOINT_T_AND_T_MINUS_1_LINEAR

PRIMARY_INFERENCE = DISTRICT_CLUSTERED_CR2_BRL_SATTERTHWAITE

WILD_CLUSTER_BOOTSTRAP = MANDATORY_RESTRICTED_DISTRICT_CLUSTERED_ROBUSTNESS

DRISCOLL_KRAAY = NOT_AUTHORIZED

TWO_WAY_CLUSTERING = NOT_AUTHORIZED

SPATIAL_HAC = ROBUSTNESS_ONLY_50_100_150_KM

B3_ECONOMETRIC_ROLE = CROP_SPECIFIC_RICE_LIMITED_MAD_NOT_ESTIMABLE

EXTREME_YEAR_POLICY = RETAIN_2017_AND_2023_LEAVE_ONE_PERIOD_OUT_ALL_PERIODS

STANDARDIZED_X_CROSS_CROP_INTERPRETATION = ONE_LOCAL_CLIMATE_SD_CHANGE_IN_NATIVE_CROP_YIELD_UNITS

CROSS_CROP_COEFFICIENT_MAGNITUDE_RANKING = NOT_AUTHORIZED

GLOBAL_FIVE_CROP_FWER_CONTROL = NOT_CLAIMED

SCENARIO_PERIOD_FE_POLICY = DO_NOT_INVENT_OR_PROPAGATE_FUTURE_PERIOD_FE

REAL_REGRESSIONS = 0

UNRESOLVED_FAILURES = 0

CRITICAL_FINDINGS = 0

MAJOR_FINDINGS = 0

FINAL_VERDICT = ED1H_PASS_HARDENED_DESIGN_READY_FOR_DIRECTOR_FREEZE_DECISION

ED1H_FREEZE_AUTHORIZED =
NO

NEXT_ACTION =
RETURN_TO_SCIENTIFIC_DIRECTOR_FOR_ED1_FREEZE_DECISION_IF_PASS
