# ER2 R2 Standardized-Anomaly Comparability v1

R2_INITIAL_EXECUTION_VERDICT=ER2_R2_PASS_RESULTS_LOCKED_READY_FOR_DIRECTOR_REVIEW
FINAL_VERDICT=ER2_R2R_PASS_REPORTING_HARDENED_READY_FOR_R2_FREEZE_DECISION

## Frozen authorization and predecessor

R1_FREEZE_SHA=b5614bb02bad3a40d90ca55688e19d71ee272877
ER2P_FREEZE_SHA=3fd1f657e79d7e0ae93903239fd3690dcade56a4
PREVIOUS_TIER_LOCK_SHA256=d035e999b213b7e8af8d7c26c7246bd7a17d30eeb75a79667e4e00e3810869b8
R2_TIER_CONTRACT_SHA256=22d27c741ad28f1be971c63a9eafdbf2e88ae16644645c2ece0970150323b0fd
The original Director instruction authorized R2 execution. R2R authorizes reporting clarification only, with no re-estimation and no further tier execution.

## Standardization provenance audited before estimation

The provenance CSV records all 21 exact source columns, frozen source hashes and upstream formula references.
Monthly Z = (district-month climate - 1991-2020 district/calendar-month mean) / the corresponding sample SD (ddof=1, 30 annual values).
All frozen reference scales are positive. R2 reads existing frozen exposures; it does not recalculate Z-scores or use Y, residuals or results to select a reference population.
Perennial exposures average monthly Z over the frozen window. E1 transient exposures first average monthly Z per cohort, then use positive observed unambiguously assigned SIEMBRA weights.
The final window/cohort exposure is not asserted to have unit SD in the analytical sample. A unit is defined by the upstream local monthly climate standardization and aggregation, not by a newly calculated sample SD.

R2_STANDARDIZATION_RECOMPUTED=FALSE
ED1_ORIGINAL_INTERPRETATION_LABEL=ONE_LOCAL_CLIMATE_SD_CHANGE_IN_NATIVE_CROP_YIELD_UNITS
R2R_CORRECTED_INTERPRETATION=ONE_UNIT_INCREASE_IN_PHENOLOGY_ALIGNED_STANDARDIZED_ANOMALY_EXPOSURE_INDEX_IN_NATIVE_CROP_YIELD_UNITS

## Exact sample and model architecture

| CROP | N | NOMINAL_DISTRICTS | EFFECTIVE_DISTRICTS | PERIODS | ORDERED_KEYS_IDENTICAL | Y_IDENTICAL | FE_IDENTICAL |
|---|---|---|---|---|---|---|---|
| RICE | 281 | 44 | 43 | 7 | True | True | True |
| MAIZ_AMARILLO_DURO | 318 | 54 | 52 | 7 | True | True | True |
| MANGO | 255 | 36 | 35 | 8 | True | True | True |
| LIMON_SUTIL | 311 | 44 | 43 | 8 | True | True | True |
| PLATANOS_Y_BANANAS | 390 | 54 | 50 | 8 | True | True | True |

Ordered keys are checked against the unchanged ER1 construction and the ER1 key records committed in R1. No row deletion, addition, trimming, winsorization, imputation or campaign redefinition.
Unweighted linear additive yield-level TM/ha models retain district and period FE and district-clustered CR2/Satterthwaite inference. Lemon and Banana retain a single joint t plus t-1 model each.

## All 21 R2 coefficient results

| CROP | VARIABLE | WINDOW | BETA | CR2_SE | SATTERTHWAITE_DF | T | P_TWO_SIDED | CI95_LOWER | CI95_UPPER | HOLM_P |
|---|---|---|---|---|---|---|---|---|---|---|
| RICE | RAIN_Z | RICE_FLOWERING_95_110_DAS | -0.0900557895594 | 0.131336951295 | 21.3956410289 | -0.685685092209 | 0.500274640261 | -0.362878726409 | 0.18276714729 | 1 |
| RICE | TMAX_Z | RICE_FLOWERING_95_110_DAS | -0.0988224059421 | 0.146591718953 | 25.3057558344 | -0.674133618514 | 0.506338303558 | -0.400548844607 | 0.202904032723 | 1 |
| RICE | TMIN_Z | RICE_FLOWERING_95_110_DAS | 0.11951972828 | 0.126033019258 | 22.4619168115 | 0.948320757403 | 0.353058195064 | -0.14154546486 | 0.380584921421 | 1 |
| MAIZ_AMARILLO_DURO | RAIN_Z | MAD_MPLUS1_MPLUS3 | 0.0633198389165 | 0.0871354657223 | 24.7270736971 | 0.726682739246 | 0.474244073165 | -0.116239502523 | 0.242879180356 | 0.94848814633 |
| MAIZ_AMARILLO_DURO | TMAX_Z | MAD_MPLUS1_MPLUS3 | 0.175961927299 | 0.0796398032766 | 29.4202530751 | 2.2094721491 | 0.0350752444763 | 0.0131812446888 | 0.33874260991 | 0.105225733429 |
| MAIZ_AMARILLO_DURO | TMIN_Z | MAD_MPLUS1_MPLUS3 | -0.0974333951287 | 0.160193752555 | 28.6476545895 | -0.608222190785 | 0.547832463852 | -0.425241530763 | 0.230374740505 | 0.94848814633 |
| MANGO | RAIN_Z | MANGO_MAY_JUN_CURRENT_YEAR | 1.57800763549 | 0.688984353505 | 16.7186120361 | 2.29033885524 | 0.0352885873939 | 0.122511766687 | 3.03350350428 | 0.105865762182 |
| MANGO | TMAX_Z | MANGO_MAY_JUN_CURRENT_YEAR | 1.21841145434 | 0.778097818011 | 20.4586044544 | 1.56588468203 | 0.132713151372 | -0.402342867033 | 2.83916577572 | 0.132713151372 |
| MANGO | TMIN_Z | MANGO_MAY_JUN_CURRENT_YEAR | 2.88960960865 | 1.36466266332 | 19.9626338993 | 2.11745340906 | 0.0469713464833 | 0.0426315511152 | 5.73658766619 | 0.105865762182 |
| LIMON_SUTIL | RAIN_Z__T | LEMON_FULL_YEAR_T | 3.86520785435 | 2.43161637809 | 30.7399182281 | 1.58956317665 | 0.122166856806 | -1.09580765474 | 8.82622336344 | 0.488667427225 |
| LIMON_SUTIL | TMAX_Z__T | LEMON_FULL_YEAR_T | 0.272721215433 | 0.957565771038 | 30.4980359829 | 0.284806771171 | 0.777717273938 | -1.68155069608 | 2.22699312694 | 1 |
| LIMON_SUTIL | TMIN_Z__T | LEMON_FULL_YEAR_T | -1.42183649373 | 1.20101182437 | 18.5960121635 | -1.18386552478 | 0.251378933274 | -3.93928438438 | 1.09561139693 | 0.754136799823 |
| LIMON_SUTIL | RAIN_Z__T_MINUS_1 | LEMON_FULL_YEAR_T_MINUS_1 | -5.13291583152 | 1.91141503498 | 29.2665965842 | -2.68540099224 | 0.0118100890773 | -9.04065229215 | -1.2251793709 | 0.0708605344636 |
| LIMON_SUTIL | TMAX_Z__T_MINUS_1 | LEMON_FULL_YEAR_T_MINUS_1 | -0.37777161168 | 0.982386493024 | 26.0571649499 | -0.384544794093 | 0.703695318524 | -2.39688038027 | 1.64133715691 | 1 |
| LIMON_SUTIL | TMIN_Z__T_MINUS_1 | LEMON_FULL_YEAR_T_MINUS_1 | -2.52114639352 | 1.06911315527 | 15.3198880333 | -2.35816609412 | 0.0320465094517 | -4.7957698972 | -0.24652288984 | 0.160232547259 |
| PLATANOS_Y_BANANAS | RAIN_Z__T | BANANA_FULL_YEAR_T | 2.90229388001 | 2.10951608941 | 38.4883590857 | 1.37581026027 | 0.176834313015 | -1.36641944316 | 7.17100720318 | 0.884171565073 |
| PLATANOS_Y_BANANAS | TMAX_Z__T | BANANA_FULL_YEAR_T | 0.149696478002 | 0.937978107161 | 34.616377425 | 0.159594852864 | 0.874127821593 | -1.75525495482 | 2.05464791082 | 1 |
| PLATANOS_Y_BANANAS | TMIN_Z__T | BANANA_FULL_YEAR_T | -0.734307597123 | 1.19175831382 | 23.4857882831 | -0.616154792972 | 0.543718714226 | -3.19682886783 | 1.72821367359 | 1 |
| PLATANOS_Y_BANANAS | RAIN_Z__T_MINUS_1 | BANANA_FULL_YEAR_T_MINUS_1 | -6.71227030557 | 1.8454732946 | 36.3487640439 | -3.63715385382 | 0.000848589444382 | -10.4538170756 | -2.9707235355 | 0.00509153666629 |
| PLATANOS_Y_BANANAS | TMAX_Z__T_MINUS_1 | BANANA_FULL_YEAR_T_MINUS_1 | 1.01569520121 | 1.45296929163 | 30.4442444719 | 0.699047947583 | 0.489828610443 | -1.94984930171 | 3.98123970414 | 1 |
| PLATANOS_Y_BANANAS | TMIN_Z__T_MINUS_1 | BANANA_FULL_YEAR_T_MINUS_1 | 0.363553033485 | 0.924926887028 | 19.7852638385 | 0.393061374454 | 0.698477236757 | -1.56715393342 | 2.29426000039 | 1 |

Intervals are unadjusted 95% CR2/Satterthwaite intervals. Holm is applied separately to 3, 3, 3, 6 and 6 R2 coefficient p-values. No adjusted confidence intervals or global 21-coefficient FWER claim.

## Five complete crop-level AHT/HTZ tests

| CROP | NULL | NUMERATOR_DF | DENOMINATOR_DF | F | P |
|---|---|---|---|---|---|
| RICE | RAIN_Z=TMAX_Z=TMIN_Z=0 | 3 | 24.8476800247 | 0.310435954139 | 0.817622556084 |
| MAIZ_AMARILLO_DURO | RAIN_Z=TMAX_Z=TMIN_Z=0 | 3 | 27.0318920439 | 1.57203331448 | 0.219062951556 |
| MANGO | RAIN_Z=TMAX_Z=TMIN_Z=0 | 3 | 21.8391787372 | 7.52235058624 | 0.00123098162909 |
| LIMON_SUTIL | RAIN_Z__T=TMAX_Z__T=TMIN_Z__T=RAIN_Z__T_MINUS_1=TMAX_Z__T_MINUS_1=TMIN_Z__T_MINUS_1=0 | 6 | 20.0744712294 | 3.19937516997 | 0.0227449506449 |
| PLATANOS_Y_BANANAS | RAIN_Z__T=TMAX_Z__T=TMIN_Z__T=RAIN_Z__T_MINUS_1=TMAX_Z__T_MINUS_1=TMIN_Z__T_MINUS_1=0 | 6 | 26.202137697 | 2.22338298457 | 0.0725750453013 |

## ER1 versus R2 descriptive signs

| CROP | ER1_VARIABLE | VARIABLE | ER1_BETA_REFERENCE | BETA | ER1_SIGN | R2_SIGN | SIGN_AGREEMENT |
|---|---|---|---|---|---|---|---|
| RICE | RAIN_ANOM_MM | RAIN_Z | 0.00110373942188 | -0.0900557895594 | 1 | -1 | False |
| RICE | TMAX_ANOM_C | TMAX_Z | 0.00897648919204 | -0.0988224059421 | 1 | -1 | False |
| RICE | TMIN_ANOM_C | TMIN_Z | 0.0914371214701 | 0.11951972828 | 1 | 1 | True |
| MAIZ_AMARILLO_DURO | RAIN_ANOM_MM | RAIN_Z | 0.000125645224716 | 0.0633198389165 | 1 | 1 | True |
| MAIZ_AMARILLO_DURO | TMAX_ANOM_C | TMAX_Z | 0.236996163413 | 0.175961927299 | 1 | 1 | True |
| MAIZ_AMARILLO_DURO | TMIN_ANOM_C | TMIN_Z | -0.087388917881 | -0.0974333951287 | -1 | -1 | True |
| MANGO | RAIN_ANOM_MM | RAIN_Z | -0.00174754987824 | 1.57800763549 | -1 | 1 | False |
| MANGO | TMAX_ANOM_C | TMAX_Z | 0.556341505832 | 1.21841145434 | 1 | 1 | True |
| MANGO | TMIN_ANOM_C | TMIN_Z | 0.658341915612 | 2.88960960865 | 1 | 1 | True |
| LIMON_SUTIL | RAIN_ANOM_MM__T | RAIN_Z__T | -0.00378088338214 | 3.86520785435 | -1 | 1 | False |
| LIMON_SUTIL | TMAX_ANOM_C__T | TMAX_Z__T | -0.0224561005874 | 0.272721215433 | -1 | 1 | False |
| LIMON_SUTIL | TMIN_ANOM_C__T | TMIN_Z__T | 0.597626337067 | -1.42183649373 | 1 | -1 | False |
| LIMON_SUTIL | RAIN_ANOM_MM__T_MINUS_1 | RAIN_Z__T_MINUS_1 | 5.01932016883e-06 | -5.13291583152 | 1 | -1 | False |
| LIMON_SUTIL | TMAX_ANOM_C__T_MINUS_1 | TMAX_Z__T_MINUS_1 | -0.931456772547 | -0.37777161168 | -1 | -1 | True |
| LIMON_SUTIL | TMIN_ANOM_C__T_MINUS_1 | TMIN_Z__T_MINUS_1 | -4.085713249 | -2.52114639352 | -1 | -1 | True |
| PLATANOS_Y_BANANAS | RAIN_ANOM_MM__T | RAIN_Z__T | -0.00210234208261 | 2.90229388001 | -1 | 1 | False |
| PLATANOS_Y_BANANAS | TMAX_ANOM_C__T | TMAX_Z__T | -0.325349465981 | 0.149696478002 | -1 | 1 | False |
| PLATANOS_Y_BANANAS | TMIN_ANOM_C__T | TMIN_Z__T | -0.0362081975061 | -0.734307597123 | -1 | -1 | True |
| PLATANOS_Y_BANANAS | RAIN_ANOM_MM__T_MINUS_1 | RAIN_Z__T_MINUS_1 | 0.00277608124998 | -6.71227030557 | 1 | -1 | False |
| PLATANOS_Y_BANANAS | TMAX_ANOM_C__T_MINUS_1 | TMAX_Z__T_MINUS_1 | -1.36242300224 | 1.01569520121 | -1 | 1 | False |
| PLATANOS_Y_BANANAS | TMIN_ANOM_C__T_MINUS_1 | TMIN_Z__T_MINUS_1 | -6.56455869177 | 0.363553033485 | -1 | 1 | False |

These are descriptive sign comparisons. Physical and standardized predictor units differ; raw beta magnitudes are not same-unit comparisons. No percentage improvement, significance voting, selected coefficient or primary replacement.

## Exposure-only transformation diagnostic

| CROP_CODE | VARIABLE | STANDARDIZATION_RELATION_TO_PHYSICAL_ANOMALY | PROJECTION_RELATIVE_L2_RESIDUAL |
|---|---|---|---|
| 14010020000 | RAIN_Z | LOCALLY_VARYING_STANDARDIZATION_TRANSFORMATION | 0.783858591889 |
| 14010020000 | TMAX_Z | LOCALLY_VARYING_STANDARDIZATION_TRANSFORMATION | 0.219641558738 |
| 14010020000 | TMIN_Z | LOCALLY_VARYING_STANDARDIZATION_TRANSFORMATION | 0.265223566753 |
| 14010070000 | RAIN_Z | LOCALLY_VARYING_STANDARDIZATION_TRANSFORMATION | 0.477857163758 |
| 14010070000 | TMAX_Z | LOCALLY_VARYING_STANDARDIZATION_TRANSFORMATION | 0.227974202134 |
| 14010070000 | TMIN_Z | LOCALLY_VARYING_STANDARDIZATION_TRANSFORMATION | 0.232127083847 |
| 13010210000 | RAIN_Z | LOCALLY_VARYING_STANDARDIZATION_TRANSFORMATION | 0.838326467114 |
| 13010210000 | TMAX_Z | LOCALLY_VARYING_STANDARDIZATION_TRANSFORMATION | 0.119724281776 |
| 13010210000 | TMIN_Z | LOCALLY_VARYING_STANDARDIZATION_TRANSFORMATION | 0.278273339438 |
| 13010170102 | RAIN_Z__T | LOCALLY_VARYING_STANDARDIZATION_TRANSFORMATION | 0.680027454336 |
| 13010170102 | TMAX_Z__T | LOCALLY_VARYING_STANDARDIZATION_TRANSFORMATION | 0.138962923791 |
| 13010170102 | TMIN_Z__T | LOCALLY_VARYING_STANDARDIZATION_TRANSFORMATION | 0.235314623403 |
| 13010170102 | RAIN_Z__T_MINUS_1 | LOCALLY_VARYING_STANDARDIZATION_TRANSFORMATION | 0.616373869239 |
| 13010170102 | TMAX_Z__T_MINUS_1 | LOCALLY_VARYING_STANDARDIZATION_TRANSFORMATION | 0.134838121286 |
| 13010170102 | TMIN_Z__T_MINUS_1 | LOCALLY_VARYING_STANDARDIZATION_TRANSFORMATION | 0.24555272128 |
| 15010040000 | RAIN_Z__T | LOCALLY_VARYING_STANDARDIZATION_TRANSFORMATION | 0.669964654933 |
| 15010040000 | TMAX_Z__T | LOCALLY_VARYING_STANDARDIZATION_TRANSFORMATION | 0.138215430514 |
| 15010040000 | TMIN_Z__T | LOCALLY_VARYING_STANDARDIZATION_TRANSFORMATION | 0.238518194598 |
| 15010040000 | RAIN_Z__T_MINUS_1 | LOCALLY_VARYING_STANDARDIZATION_TRANSFORMATION | 0.611694890976 |
| 15010040000 | TMAX_Z__T_MINUS_1 | LOCALLY_VARYING_STANDARDIZATION_TRANSFORMATION | 0.134855785647 |
| 15010040000 | TMIN_Z__T_MINUS_1 | LOCALLY_VARYING_STANDARDIZATION_TRANSFORMATION | 0.24222802638 |

The positive-scalar diagnostic is a projection of frozen Z onto frozen physical X through the origin, without Y. Its 128*epsilon source-representation bound is fixed before results; it never cancels or changes R2.

## Interpretation and execution firewalls

Y_STANDARDIZED=FALSE
FULLY_STANDARDIZED_EFFECT=FALSE
CROSS_CROP_COEFFICIENT_MAGNITUDE_RANKING=NOT_AUTHORIZED
CROSS_CROP_SIGNIFICANCE_RANKING=NOT_AUTHORIZED
Associations remain in crop-specific native TM/ha units. There is no causal claim, cross-crop sensitivity ranking or vulnerability ranking.
R3-R6, bootstrap, Conley, LOO, B3, scenarios, GVP, VaR/CVaR, A1/A2 and optimization are NOT_EXECUTED. The R3 adapter is not implemented.
NEXT_TIER_AUTHORIZATION_STATUS=NOT_AUTHORIZED

## Numerical verification

Frozen ED1 main and independent full-design SVD paths reproduce beta, CR2 covariance, coefficient-specific df and complete AHT. The frozen R1A envelope was adopted before R2 fits: beta relative L2 <=1e-10; covariance Frobenius, df L2/componentwise and AHT relative errors <=1e-6. Full-rank and zero extra CR2 singularities must agree.
The lock preserves all absolute discrepancies and the unchanged ED1 absolute 1e-8 alarm separately. No solver, engine or tolerance is changed after results.

13010170102: PASS; ED1 absolute alarm=PASS
Absolute: {"aht_delta_abs": 1.1102230246251565e-16, "aht_denominator_df_abs": 1.7763568394002505e-14, "aht_f_statistic_abs": 4.4853010194856324e-14, "aht_numerator_df_abs": 0.0, "aht_p_value_abs": 1.3426759704060487e-15, "aht_wald_chi_square_abs": 3.339550858072471e-13, "beta_max_abs": 1.1546319456101628e-14, "covariance_max_abs": 3.010369731271112e-13, "satterthwaite_df_max_abs": 3.943512183468556e-13}
Relative: {"aht_denominator_df_symmetric_relative": 8.848835015877235e-16, "aht_f_statistic_symmetric_relative": 1.4019303086399206e-14, "aht_p_value_symmetric_relative": 5.903182606837049e-14, "beta_relative_l2": 2.782494719006839e-15, "cr2_covariance_relative_frobenius": 1.1009008940796728e-13, "satterthwaite_df_max_component_relative": 1.795842478863275e-14, "satterthwaite_df_relative_l2": 9.000261129487597e-15}

13010210000: PASS; ED1 absolute alarm=PASS
Absolute: {"aht_delta_abs": 2.220446049250313e-16, "aht_denominator_df_abs": 5.684341886080802e-14, "aht_f_statistic_abs": 1.1546319456101628e-13, "aht_numerator_df_abs": 0.0, "aht_p_value_abs": 9.82287168271867e-17, "aht_wald_chi_square_abs": 3.872457909892546e-13, "beta_max_abs": 7.993605777301127e-15, "covariance_max_abs": 1.1102230246251565e-13, "satterthwaite_df_max_abs": 2.2737367544323206e-13}
Relative: {"aht_denominator_df_symmetric_relative": 2.6028185191782194e-15, "aht_f_statistic_symmetric_relative": 1.5349350344317952e-14, "aht_p_value_symmetric_relative": 7.979706155309928e-14, "beta_relative_l2": 3.152965004721558e-15, "cr2_covariance_relative_frobenius": 5.6056601614502844e-14, "satterthwaite_df_max_component_relative": 1.1389963698711069e-14, "satterthwaite_df_relative_l2": 7.1051900785593686e-15}

14010020000: PASS; ED1 absolute alarm=PASS
Absolute: {"aht_delta_abs": 0.0, "aht_denominator_df_abs": 3.197442310920451e-14, "aht_f_statistic_abs": 6.8833827526759706e-15, "aht_numerator_df_abs": 0.0, "aht_p_value_abs": 4.551914400963142e-15, "aht_wald_chi_square_abs": 2.220446049250313e-14, "beta_max_abs": 4.093947403305265e-15, "covariance_max_abs": 5.273559366969494e-16, "satterthwaite_df_max_abs": 6.394884621840902e-14}
Relative: {"aht_denominator_df_symmetric_relative": 1.286817243193701e-15, "aht_f_statistic_symmetric_relative": 2.2173278129999255e-14, "aht_p_value_symmetric_relative": 5.5672563912190066e-15, "beta_relative_l2": 2.9382328413327326e-14, "cr2_covariance_relative_frobenius": 1.6993582897391307e-14, "satterthwaite_df_max_component_relative": 2.9888726461595824e-15, "satterthwaite_df_relative_l2": 1.770421397843952e-15}

14010070000: PASS; ED1 absolute alarm=PASS
Absolute: {"aht_delta_abs": 1.1102230246251565e-16, "aht_denominator_df_abs": 3.907985046680551e-14, "aht_f_statistic_abs": 9.769962616701378e-15, "aht_numerator_df_abs": 0.0, "aht_p_value_abs": 2.248201624865942e-15, "aht_wald_chi_square_abs": 3.197442310920451e-14, "beta_max_abs": 2.2343238370581275e-15, "covariance_max_abs": 8.760353553682876e-17, "satterthwaite_df_max_abs": 2.4868995751603507e-14}
Relative: {"aht_denominator_df_symmetric_relative": 1.4456942341780289e-15, "aht_f_statistic_symmetric_relative": 6.2148572340658166e-15, "aht_p_value_symmetric_relative": 1.0262810798913012e-14, "beta_relative_l2": 1.1725380034946779e-14, "cr2_covariance_relative_frobenius": 4.1614110042579396e-15, "satterthwaite_df_max_component_relative": 8.45301897577729e-16, "satterthwaite_df_relative_l2": 7.185889537813469e-16}

15010040000: PASS; ED1 absolute alarm=PASS
Absolute: {"aht_delta_abs": 0.0, "aht_denominator_df_abs": 1.0658141036401503e-14, "aht_f_statistic_abs": 2.686739719592879e-13, "aht_numerator_df_abs": 0.0, "aht_p_value_abs": 2.9781732635569824e-14, "aht_wald_chi_square_abs": 1.9202417433916708e-12, "beta_max_abs": 1.865174681370263e-14, "covariance_max_abs": 5.293543381412746e-13, "satterthwaite_df_max_abs": 1.3393730569077889e-12}
Relative: {"aht_denominator_df_symmetric_relative": 4.067660875482119e-16, "aht_f_statistic_symmetric_relative": 1.2084016735940777e-13, "aht_p_value_symmetric_relative": 4.1035775467912227e-13, "beta_relative_l2": 3.770829388905272e-15, "cr2_covariance_relative_frobenius": 3.210553404261282e-13, "satterthwaite_df_max_component_relative": 5.702908672955769e-14, "satterthwaite_df_relative_l2": 2.4221225083182407e-14}

## Limitations

Finite district clusters, coefficient-specific effective degrees of freedom, conditional transient cohort support and observational associations remain limitations. Nonsignificance or a sign change is not failure of the R2 execution gate.

## Original R2 numerical reproduction (retained evidence; not rerun by R2R)

R2_TWO_RUN_REPRODUCIBILITY=PASS
Two separate Python worker processes each write and verify the provenance audit before fitting. Their complete serialized calculations and provenance bytes are compared, then both rendered output packages must match before publication.
UTF-8, LF only, no BOM, exactly one final LF, no timestamps or absolute local paths. The lock hash is computed externally; no circular self-hash.

## Exact next action

RETURN_TO_SCIENTIFIC_DIRECTOR_FOR_R2_FREEZE_DECISION_IF_PASS
R3_AUTHORIZATION_STATUS=NOT_AUTHORIZED

## R2R reporting certification

R2_INITIAL_RESULTS_LOCK_SHA256=117a3fe5da88f44d31b176495409f6e84189148f1020417f046b0df3dd4c5f6b
ORIGINAL_CANONICAL_REPORT_SHA256=7aba59037f2dcbe5712a923cfa8ff14f25c239a086b53cbc8da260e439bd858e
R2_NUMERICAL_RESULTS=PASS
R2_FREEZE_AUTHORIZED=NO
R2_MODELS_REESTIMATED_DURING_R2R=0
The original results lock and all four numerical/sample/provenance CSV files remain byte-identical. Their historical shorthand is retained as lineage, not silently relabeled as the corrected reporting interpretation.
The original lock continues to reference the original report and implementation hashes. This separate reporting certification does not overwrite or recertify those historical references as current bytes.

### Exact monthly and aggregation definitions

Z_(district,calendar_month,year) = (x - district_calendar_month_1991_2020_mean) / district_calendar_month_1991_2020_sample_SD
Reference population: each district x calendar-month, 1991-2020, 30 annual values; sample SD ddof=1. No outcome-based selection and no R2 recomputation.
PERENNIAL_FINAL_R2_X=ARITHMETIC_MEAN_OF_MONTHLY_LOCAL_Z_WITHIN_FROZEN_WINDOW
TRANSIENT_FINAL_R2_X=MONTHLY_LOCAL_Z_TO_COHORT_WINDOW_MEAN_Z_TO_POSITIVE_OBSERVED_UNAMBIGUOUS_SIEMBRA_WEIGHTED_AGGREGATION
MONTHLY_COMPONENTS_STANDARDIZED_LOCALLY=TRUE
FINAL_ANALYTICAL_EXPOSURE_STANDARD_DEVIATION_EQUALS_ONE=NOT_CLAIMED
FINAL_ANALYTICAL_X_UNIT_SD_CLAIMED=FALSE

Change in crop yield (TM/ha) associated with a one-unit increase in the phenology-aligned exposure index constructed from locally standardized monthly climate anomalies.
Each underlying monthly anomaly is standardized by its district x calendar-month 1991-2020 standard deviation; the aggregated crop/window exposure itself is not asserted to have standard deviation one.
A one-unit increase in final R2 X is not claimed to equal one empirical standard deviation of the final crop/window analytical exposure.
R2R_REPORTING_CLARIFICATION=FINAL_AGGREGATED_INDEX_IS_BUILT_FROM_LOCAL_SD_STANDARDIZED_MONTHLY_COMPONENTS_BUT_IS_NOT_ITSELF_ASSERTED_TO_HAVE_SD_ONE

### Transformation and sign-change interpretation

All 21 relationships remain LOCALLY_VARYING_STANDARDIZATION_TRANSFORMATION. R2 is not a global positive scalar re-expression of ER1. Sign, t-statistic and p-value invariance are therefore not expected.
ER1_R2_SIGN_CHANGES=12
ER1_R2_SIGN_AGREEMENTS=9
SIGN_CHANGE_INTERPRETATION=EXPOSURE_DEFINITION_SENSITIVITY_DESCRIPTIVE_ONLY
The 12 sign changes are descriptive sensitivity evidence, not robustness failures, a refutation of either specification or evidence that the standardized specification is superior.

### Complete individual Holm certification

Exactly one of all 21 R2 coefficients survives its prespecified within-crop Holm family at p < 0.05:
| CROP | VARIABLE | BETA | P_TWO_SIDED | HOLM_P |
|---|---|---|---|---|
| PLATANOS_Y_BANANAS | RAIN_Z__T_MINUS_1 | -6.71227030557 | 0.000848589444382 | 0.00509153666629 |
No other coefficient survives within-crop R2 Holm at 0.05. All 21 original coefficient rows and Holm p-values above are unchanged.

### Five AHT classifications and distinct hypotheses

| CROP | NUMERATOR_DF | DENOMINATOR_DF | F | P | P_LT_0_05 | WITHIN_CROP_HOLM_SURVIVORS |
|---|---|---|---|---|---|---|
| RICE | 3 | 24.8476800247 | 0.310435954139 | 0.817622556084 | False | 0 |
| MAIZ_AMARILLO_DURO | 3 | 27.0318920439 | 1.57203331448 | 0.219062951556 | False | 0 |
| MANGO | 3 | 21.8391787372 | 7.52235058624 | 0.00123098162909 | True | 0 |
| LIMON_SUTIL | 6 | 20.0744712294 | 3.19937516997 | 0.0227449506449 | True | 0 |
| PLATANOS_Y_BANANAS | 6 | 26.202137697 | 2.22338298457 | 0.0725750453013 | False | 1 |
AHT p-values are unchanged and unadjusted. No Holm adjustment to the five AHT tests and no new cross-crop AHT multiplicity family is authorized.
Mango and Lemon show crop-level joint AHT evidence under R2, while no individual Mango/Lemon coefficient survives within-crop Holm.
Banana shows one individual coefficient surviving within-crop Holm while its six-coefficient crop AHT has p > 0.05.
These outcomes are not logically contradictory: the complete climate-block null and individual-coefficient nulls with within-crop multiplicity control are different hypotheses and inference procedures.

### Banana component and primary-specification firewalls

ER1's strongest individual Banana signal is lagged Tmin; R2's sole Holm-surviving individual Banana signal is lagged rainfall. This is not confirmation of the same component.
BANANA_ALLOWED_STATEMENT=BANANA_CLIMATE_RESPONSE_EVIDENCE_APPEARS_UNDER_MULTIPLE_EXPOSURE_DEFINITIONS_BUT_COMPONENT_IDENTITY_IS_NOT_INVARIANT
SAME_BANANA_CHANNEL_ROBUSTLY_CONFIRMED=PROHIBITED
PRIMARY_SPECIFICATION=ER1_PHYSICAL_ANOMALY
R2_ROLE=SECONDARY_STANDARDIZED_EXPOSURE_SENSITIVITY
Y_STANDARDIZED=FALSE
FULLY_STANDARDIZED_EFFECT=FALSE
CROSS_CROP_EFFECT_SIZE_COMPARABILITY=NOT_AUTHORIZED
No cross-crop coefficient/significance ranking or significance-based replacement of ER1 is authorized.

### Reporting-only reproduction and next action

R2R_TWO_RUN_REPRODUCIBILITY=PASS
Two separate processes independently read the same immutable results and construct the reporting basis. Corrected report and reporting-lock bytes must match before publication. No model or numerical verification is rerun.
R2_NUMERICAL_RESULT_CHANGE=FALSE
R2_SAMPLE_CHANGE=FALSE
R2_STANDARDIZATION_CHANGE=FALSE
R2_MODEL_CHANGE=FALSE
R2_REPORTING_SEMANTICS_HARDENED=TRUE
NEXT_TIER_AUTHORIZATION_STATUS=NOT_AUTHORIZED
R3-R6 remain unauthorized and unexecuted. No adapter, bootstrap, Conley, LOO, B3, scenario, GVP, VaR/CVaR, A1/A2 or optimization execution.
RETURN_TO_SCIENTIFIC_DIRECTOR_FOR_R2_FREEZE_DECISION_IF_PASS
