# ER1 Primary Real Estimation v1

## 1. Analytical sample

All five frozen ED1 samples were reproduced without silent row deletion, imputation, trimming, or winsorization.

| Crop | N | Districts | Effective districts | Periods | Missing Y | Missing X | Duplicate keys |
|---|---:|---:|---:|---:|---:|---:|---:|
| RICE | 281 | 44 | 43 | 7 | 0 | 0 | 0 |
| MAIZ_AMARILLO_DURO | 318 | 54 | 52 | 7 | 0 | 0 | 0 |
| MANGO | 255 | 36 | 35 | 8 | 0 | 0 | 0 |
| LIMON_SUTIL | 311 | 44 | 43 | 8 | 0 | 0 | 0 |
| PLATANOS_Y_BANANAS | 390 | 54 | 50 | 8 | 0 | 0 | 0 |

## 2. Primary coefficient estimates

These are conditional historical climate-yield associations under the frozen empirical-association claim ceiling.

All reported intervals are unadjusted coefficient-specific 95% CR2/Satterthwaite confidence intervals. Holm step-down adjusts coefficient p-values within each crop only. Multiplicity-adjusted confidence intervals were not constructed and are not claimed.

| Crop | Variable | Window | Beta | CR2 SE | Satterthwaite df | t | Unadjusted p | Unadjusted 95% CR2/Satterthwaite CI | Within-crop Holm p | Flag |
|---|---|---|---:|---:|---:|---:|---:|---|---:|---|
| RICE | RAIN_ANOM_MM | RICE_FLOWERING_95_110_DAS | 0.00110373942 | 0.000882394502 | 4.91999382 | 1.25084576 | 0.267179068 | [-0.00117566714, 0.00338314598] | 0.801537204 | VERY_LOW_EFFECTIVE_DF |
| RICE | TMAX_ANOM_C | RICE_FLOWERING_95_110_DAS | 0.00897648919 | 0.145329575 | 20.7574811 | 0.0617664312 | 0.951339714 | [-0.293468058, 0.311421037] | 0.951339714 | NONE |
| RICE | TMIN_ANOM_C | RICE_FLOWERING_95_110_DAS | 0.0914371215 | 0.125432601 | 19.8154417 | 0.728974133 | 0.474546109 | [-0.170367013, 0.353241256] | 0.949092217 | NONE |
| MAIZ_AMARILLO_DURO | RAIN_ANOM_MM | MAD_MPLUS1_MPLUS3 | 0.000125645225 | 0.000254584958 | 25.0332949 | 0.493529647 | 0.625940605 | [-0.000398646954, 0.000649937403] | 1 | NONE |
| MAIZ_AMARILLO_DURO | TMAX_ANOM_C | MAD_MPLUS1_MPLUS3 | 0.236996163 | 0.148787409 | 28.6338393 | 1.59285094 | 0.122174342 | [-0.0674773727, 0.5414697] | 0.366523027 | NONE |
| MAIZ_AMARILLO_DURO | TMIN_ANOM_C | MAD_MPLUS1_MPLUS3 | -0.0873889179 | 0.213855951 | 33.6688993 | -0.408634491 | 0.685395443 | [-0.522153982, 0.347376146] | 1 | NONE |
| MANGO | RAIN_ANOM_MM | MANGO_MAY_JUN_CURRENT_YEAR | -0.00174754988 | 0.0205368702 | 11.2971433 | -0.0850932913 | 0.933676565 | [-0.0468042645, 0.0433091647] | 1 | NONE |
| MANGO | TMAX_ANOM_C | MANGO_MAY_JUN_CURRENT_YEAR | 0.556341506 | 0.831073611 | 20.4858414 | 0.669425065 | 0.510699404 | [-1.17461575, 2.28729876] | 1 | NONE |
| MANGO | TMIN_ANOM_C | MANGO_MAY_JUN_CURRENT_YEAR | 0.658341916 | 0.903954364 | 19.7376567 | 0.728291097 | 0.474988026 | [-1.22888184, 2.54556567] | 1 | NONE |
| LIMON_SUTIL | RAIN_ANOM_MM__T | LEMON_FULL_YEAR_T | -0.00378088338 | 0.0032957959 | 21.5292982 | -1.14718371 | 0.263895025 | [-0.0106246204, 0.00306285363] | 1 | NONE |
| LIMON_SUTIL | TMAX_ANOM_C__T | LEMON_FULL_YEAR_T | -0.0224561006 | 1.76859166 | 29.8140939 | -0.0126971653 | 0.989953986 | [-3.63534681, 3.59043461] | 1 | NONE |
| LIMON_SUTIL | TMIN_ANOM_C__T | LEMON_FULL_YEAR_T | 0.597626337 | 1.390079 | 23.234445 | 0.429922571 | 0.671213099 | [-2.27636645, 3.47161912] | 1 | NONE |
| LIMON_SUTIL | RAIN_ANOM_MM__T_MINUS_1 | LEMON_FULL_YEAR_T_MINUS_1 | 5.01932017e-06 | 0.00240581967 | 21.0742132 | 0.00208632435 | 0.998354979 | [-0.00499708399, 0.00500712263] | 1 | NONE |
| LIMON_SUTIL | TMAX_ANOM_C__T_MINUS_1 | LEMON_FULL_YEAR_T_MINUS_1 | -0.931456773 | 1.43034519 | 25.2857965 | -0.651211176 | 0.520785049 | [-3.87562046, 2.01270692] | 1 | NONE |
| LIMON_SUTIL | TMIN_ANOM_C__T_MINUS_1 | LEMON_FULL_YEAR_T_MINUS_1 | -4.08571325 | 1.688541 | 25.6479794 | -2.41967074 | 0.0229341501 | [-7.55887897, -0.612547529] | 0.137604901 | NONE |
| PLATANOS_Y_BANANAS | RAIN_ANOM_MM__T | BANANA_FULL_YEAR_T | -0.00210234208 | 0.00237554148 | 28.8261733 | -0.884994895 | 0.38348222 | [-0.00696214285, 0.00275745869] | 1 | NONE |
| PLATANOS_Y_BANANAS | TMAX_ANOM_C__T | BANANA_FULL_YEAR_T | -0.325349466 | 1.48621476 | 33.0981502 | -0.218911475 | 0.82806334 | [-3.34873554, 2.69803661] | 1 | NONE |
| PLATANOS_Y_BANANAS | TMIN_ANOM_C__T | BANANA_FULL_YEAR_T | -0.0362081975 | 0.931828096 | 28.1512607 | -0.0388571644 | 0.969278528 | [-1.94450958, 1.87209318] | 1 | NONE |
| PLATANOS_Y_BANANAS | RAIN_ANOM_MM__T_MINUS_1 | BANANA_FULL_YEAR_T_MINUS_1 | 0.00277608125 | 0.00288794988 | 28.4409031 | 0.961263653 | 0.344521482 | [-0.00313548707, 0.00868764957] | 1 | NONE |
| PLATANOS_Y_BANANAS | TMAX_ANOM_C__T_MINUS_1 | BANANA_FULL_YEAR_T_MINUS_1 | -1.362423 | 2.3086114 | 29.2796044 | -0.590148262 | 0.55961875 | [-6.08210571, 3.35725971] | 1 | NONE |
| PLATANOS_Y_BANANAS | TMIN_ANOM_C__T_MINUS_1 | BANANA_FULL_YEAR_T_MINUS_1 | -6.56455869 | 1.73588592 | 29.7133812 | -3.78167633 | 0.000700983437 | [-10.1111452, -3.01797213] | 0.00420590062 | NONE |

## 3. Crop-level omnibus climate tests

| Crop | Numerator df | Denominator df | F | p |
|---|---:|---:|---:|---:|
| RICE | 3 | 13.6690739 | 0.607345731 | 0.621376821 |
| MAIZ_AMARILLO_DURO | 3 | 27.8978292 | 0.838445524 | 0.484294503 |
| MANGO | 3 | 17.8863236 | 0.366096529 | 0.778314276 |
| LIMON_SUTIL | 6 | 23.6484515 | 1.43550372 | 0.243010318 |
| PLATANOS_Y_BANANAS | 6 | 29.9591405 | 2.91512072 | 0.0232339987 |

## 4. Outcome support

| Crop | Finite | Nonfinite | Missing | Zero | Negative | Min | Median | Max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| RICE | 281 | 0 | 0 | 0 | 0 | 3.69230769 | 7.85483871 | 11.25 |
| MAIZ_AMARILLO_DURO | 318 | 0 | 0 | 0 | 0 | 0.6 | 4.45132928 | 8.84705882 |
| MANGO | 255 | 0 | 0 | 0 | 0 | 0.333333333 | 6.875 | 85 |
| LIMON_SUTIL | 311 | 0 | 0 | 0 | 0 | 0.0869565217 | 7.15957447 | 53.5 |
| PLATANOS_Y_BANANAS | 390 | 0 | 0 | 0 | 0 | 0.5 | 10.0685988 | 47.4487179 |

## 5. Statistical limitations

Rice rainfall retains `VERY_LOW_EFFECTIVE_DF` with Satterthwaite df `4.919993824254409`. This is an inferential-precision limitation specific to that coefficient and does not alter the frozen model. Other coefficients retain their actual coefficient-specific df.

Inference precision is heterogeneous across crops and coefficients. Statistical evidence compatible with zero does not by itself imply limited effective degrees of freedom or invalid inference; p-values above 0.05 are not a basis for labeling a coefficient or model weak.

The panels contain only seven transient campaigns or eight perennial calendar years. Estimates remain empirical associations conditional on district and period fixed effects. No global five-crop familywise-error claim is made.

No robustness tier, model revision, scenario, GVP calculation, CVaR calculation, A1/A2 comparison, or optimization was executed.

Most coefficient-specific 95% CR2/Satterthwaite confidence intervals include zero. After the prespecified within-crop Holm adjustment of coefficient p-values, only Banana lagged Tmin remains below 0.05. Lemon lagged Tmin has an unadjusted p-value below 0.05 but does not remain below 0.05 after Holm adjustment.

Banana lagged Tmin has a negative estimated association. Its within-crop Holm result does not control multiplicity across all 21 coefficients in all five crops. The five prespecified AHT tests are reported separately.

## 6. Numerical verification and results lock

All five independent SVD reference calculations agree within absolute tolerance `1e-08`. `ER1_PRIMARY_RESULTS_LOCK_SHA256=83eea5e179b5e3504bd1144d744dcdbeddbbdf6a554f4d10ab03b92a30278841`.

`ER1_NUMERICAL_RESULTS_IDENTITY=40e0f58269dda309e83a1fa3da17ef4d5dc5523efc72a666f734d0ebacb76b24` is the SHA-256 of the UTF-8 JSON mapping of the three accepted numerical CSV hashes, with sorted keys and compact separators. It is separate from `ER1_REPORTING_LOCK_IDENTITY=83eea5e179b5e3504bd1144d744dcdbeddbbdf6a554f4d10ab03b92a30278841`, the SHA-256 of the complete reporting lock.

`PREVIOUS_ER1_PRIMARY_RESULTS_LOCK_SHA256=d2ceab1655ae3cb220e8adfe3be7fce56dc77c35121ad6a06350532c3cb7c118` is preserved. `NUMERICAL_RESULT_CHANGE=FALSE`; only reporting metadata and wording changed in ER1R.

`COEFFICIENT_CONFIDENCE_INTERVALS=UNADJUSTED_95_PERCENT_CR2_SATTERTHWAITE`

`MULTIPLICITY_ADJUSTMENT=HOLM_STEP_DOWN_WITHIN_CROP_P_VALUES`

`MULTIPLICITY_ADJUSTED_CONFIDENCE_INTERVALS=NOT_CONSTRUCTED_NOT_CLAIMED`

`GLOBAL_FIVE_CROP_FAMILYWISE_ERROR_CONTROL=NOT_CLAIMED`

`INFERENCE_PRECISION_STATUS=HETEROGENEOUS_ACROSS_CROPS_AND_COEFFICIENTS`

`FINAL_VERDICT=ER1R_PASS_REPORTING_CORRECTED_RESULTS_READY_FOR_FREEZE_DECISION`

`ER1_FREEZE_AUTHORIZED=NO`

`ER1R_FREEZE_AUTHORIZED=NO`
