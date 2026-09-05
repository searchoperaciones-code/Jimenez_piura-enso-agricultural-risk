# ER2 R1 Level Climate-Family Results v1

FINAL_VERDICT=ER2_R1_FAIL_NUMERICAL_VERIFICATION

## Execution and governance

ER2P_FREEZE_SHA=3fd1f657e79d7e0ae93903239fd3690dcade56a4
ER1_FREEZE_SHA=43de46ecd46248f1e4e2822a30e69cfadbc8260f
ER1_NUMERICAL_RESULTS_IDENTITY=40e0f58269dda309e83a1fa3da17ef4d5dc5523efc72a666f734d0ebacb76b24
R1 alone is authorized. ER1 remains PRIMARY. R2-R6 are NOT_AUTHORIZED and NOT_EXECUTED.
Two distinct level models, six coefficients, two AHT tests and three perennial diagnostics.
No outcome-specific specification change, score, vote counting or primary replacement.

## Transient results

Exact ER1 sample: Rice 281 observations, 44 nominal/43 effective districts; MAD 318, 54/52. Seven campaigns each.
Yield remains TM/ha; unweighted linear additive models include district and campaign fixed effects.
All intervals are unadjusted 95% CR2/Satterthwaite intervals. Holm adjusts only the three R1 p-values within each crop.
No Holm-adjusted confidence intervals or global FWER claim.

| CROP | VARIABLE | WINDOW | BETA | CR2_SE | SATTERTHWAITE_DF | T | P_TWO_SIDED | CI95_LOWER | CI95_UPPER | HOLM_P |
|---|---|---|---|---|---|---|---|---|---|---|
| RICE | RAIN_MM | RICE_FLOWERING_95_110_DAS | 0.0009400944173 | 0.000737418660887 | 4.53787202223 | 1.2748448977 | 0.263732083344 | -0.00101506191919 | 0.00289525075379 | 0.791196250032 |
| RICE | TMAX_C | RICE_FLOWERING_95_110_DAS | 0.0933398346868 | 0.123334662817 | 21.4701319003 | 0.756801312419 | 0.457394058563 | -0.162807090174 | 0.349486759548 | 0.819953143624 |
| RICE | TMIN_C | RICE_FLOWERING_95_110_DAS | 0.117841098246 | 0.139857276291 | 18.941120673 | 0.842581103903 | 0.409976571812 | -0.174945145205 | 0.410627341697 | 0.819953143624 |
| MAIZ_AMARILLO_DURO | RAIN_MM | MAD_MPLUS1_MPLUS3 | 0.000228912328804 | 0.000230253648314 | 27.577487483 | 0.994174600404 | 0.328781572765 | -0.000243066653606 | 0.000700891311214 | 0.657563145531 |
| MAIZ_AMARILLO_DURO | TMAX_C | MAD_MPLUS1_MPLUS3 | 0.219483050222 | 0.123479157825 | 28.7554168425 | 1.77749066392 | 0.0860668631354 | -0.0331535205369 | 0.472119620982 | 0.258200589406 |
| MAIZ_AMARILLO_DURO | TMIN_C | MAD_MPLUS1_MPLUS3 | -0.0853466073113 | 0.116603298963 | 28.9543242837 | -0.731939902819 | 0.470088627957 | -0.323843472948 | 0.153150258325 | 0.657563145531 |

## Crop-level AHT/HTZ tests

| CROP | NULL | NUMERATOR_DF | DENOMINATOR_DF | F | P |
|---|---|---|---|---|---|
| RICE | RAIN_MM=TMAX_C=TMIN_C=0 | 3 | 12.6443210564 | 0.967405171369 | 0.438367684354 |
| MAIZ_AMARILLO_DURO | RAIN_MM=TMAX_C=TMIN_C=0 | 3 | 27.7186619883 | 1.92236109637 | 0.149113817573 |

## ER1 versus R1 descriptive comparison

| CROP | VARIABLE | ER1_BETA_REFERENCE | BETA | SIGN_AGREEMENT | R1_MINUS_ER1_BETA_DESCRIPTIVE_ONLY |
|---|---|---|---|---|---|
| RICE | RAIN_MM | 0.00110373942188 | 0.0009400944173 | True | -0.000163645004576 |
| RICE | TMAX_C | 0.00897648919204 | 0.0933398346868 | True | 0.0843633454947 |
| RICE | TMIN_C | 0.0914371214701 | 0.117841098246 | True | 0.0264039767758 |
| MAIZ_AMARILLO_DURO | RAIN_MM | 0.000125645224716 | 0.000228912328804 | True | 0.000103267104088 |
| MAIZ_AMARILLO_DURO | TMAX_C | 0.236996163413 | 0.219483050222 | True | -0.0175131131909 |
| MAIZ_AMARILLO_DURO | TMIN_C | -0.087388917881 | -0.0853466073113 | True | 0.0020423105697 |

These are descriptive level-family sensitivity comparisons, not votes for a best specification. Rainfall exposure constructions differ; raw beta magnitudes and arithmetic differences are not directly comparable effect sizes.
No causal robustness claim. Claim ceiling: EMPIRICAL_ASSOCIATION_CLIMATE_RESPONSE_ONLY.

## Perennial FE-equivalence diagnostics

The same diagnostic algorithm is applied to every perennial. Lemon and Banana each retain all six t and t-1 regressors.
Full transformed designs, ordered keys, array hashes and all discrepancies are in the lock. Byte equality uses little-endian float64 C-order arrays; tolerance is absolute 1e-9, without rounding.

### MANGO

STATUS=WITHIN_1E-9_TOLERANCE_BUT_NOT_EXACT
COLUMN_SPACE_EQUIVALENT_WITHIN_TOLERANCE=True

| quantity | max_abs_difference | numeric_exact | byte_exact | within_1e_9 |
|---|---|---|---|---|
| transformed_x | 1.75859327101e-13 | False | False | True |
| coefficients | 4.70734562441e-14 | False | False | True |
| fitted_values | 9.64561763794e-13 | False | False | True |
| residuals | 9.64561763794e-13 | False | False | True |
| cr2_covariance | 1.11275766379e-09 | False | False | False |
| satterthwaite_df | 5.39219513485e-09 | False | False | False |
| aht | 3.57771345882e-09 | False | False | False |
| coefficient_inference | 1.39842004643e-09 | False | False | False |

### LIMON_SUTIL

STATUS=WITHIN_1E-9_TOLERANCE_BUT_NOT_EXACT
COLUMN_SPACE_EQUIVALENT_WITHIN_TOLERANCE=True

| quantity | max_abs_difference | numeric_exact | byte_exact | within_1e_9 |
|---|---|---|---|---|
| transformed_x | 4.37694325228e-12 | False | False | True |
| coefficients | 1.92401650168e-13 | False | False | True |
| fitted_values | 1.4246381852e-11 | False | False | True |
| residuals | 1.4246381852e-11 | False | False | True |
| cr2_covariance | 7.06253564804e-05 | False | False | False |
| satterthwaite_df | 0.000144801592207 | False | False | False |
| aht | 1.06636907944e-05 | False | False | False |
| coefficient_inference | 5.16616002484e-05 | False | False | False |

### PLATANOS_Y_BANANAS

STATUS=WITHIN_1E-9_TOLERANCE_BUT_NOT_EXACT
COLUMN_SPACE_EQUIVALENT_WITHIN_TOLERANCE=True

| quantity | max_abs_difference | numeric_exact | byte_exact | within_1e_9 |
|---|---|---|---|---|
| transformed_x | 6.36646291241e-12 | False | False | True |
| coefficients | 1.26920696175e-12 | False | False | True |
| fitted_values | 4.70228300742e-11 | False | False | True |
| residuals | 4.70228300742e-11 | False | False | True |
| cr2_covariance | 3.18016963803e-05 | False | False | False |
| satterthwaite_df | 4.03480866069e-05 | False | False | False |
| aht | 2.4601733621e-05 | False | False | False |
| coefficient_inference | 1.43606569729e-05 | False | False | False |

Nonexact equality requires Director adjudication; no perennial is promoted to distinct robustness evidence.

## Independent numerical verification

The frozen ED1 main full-design path and independent SVD path are compared for beta, CR2 covariance, coefficient df and AHT at absolute tolerance 1e-8. Any exceedance fails numerical certification; estimates remain uncertified, even when differences are small.
The numerical reference is an independent implementation path, not a new climate family or robustness tier.
Method reference: [clubSandwich HTZ documentation](https://jepusto.github.io/clubSandwich/reference/Wald_test.html).

RICE: {"absolute_tolerance": 1e-08, "differences": {"aht_denominator_df_max_abs_difference": 2.1799451133119874e-11, "aht_f_max_abs_difference": 3.831810202470365e-09, "aht_p_max_abs_difference": 1.641895397419546e-09, "beta_max_abs_difference": 4.8155923693116165e-15, "cr2_covariance_max_abs_difference": 5.295131520755003e-11, "satterthwaite_df_max_abs_difference": 1.494845491833985e-08}, "main_aht": {"delta": 0.8634282878466184, "denominator_df": 12.644321056426605, "f_statistic": 0.9674051713685784, "numerator_df": 3.0, "p_value": 0.43836768435386764, "wald_chi_square": 3.361269899256871}, "main_beta": [0.0009400944173000858, 0.09333983468675183, 0.11784109824590483], "main_cr2_covariance": [[5.437862814248644e-07, 1.045894951631359e-05, 2.0098517504196522e-05], [1.0458949516313598e-05, 0.01521143905219631, -0.009214845929348247], [2.0098517504196515e-05, -0.009214845929348247, 0.019560057731475768]], "main_satterthwaite_df": [4.537872022230854, 21.470131900304832, 18.94112067303874], "reference_aht": {"delta": 0.8634282878468217, "denominator_df": 12.644321056448405, "f_statistic": 0.9674051752003886, "numerator_df": 3.0, "p_value": 0.43836768271197224, "wald_chi_square": 3.361269912569785}, "reference_beta": [0.0009400944172996862, 0.09333983468674702, 0.11784109824590715], "reference_cr2_covariance": [[5.437862811697563e-07, 1.0458949398320298e-05, 2.0098517486547347e-05], [1.0458949398320304e-05, 0.015211438999244995, -0.009214845939264362], [2.009851748654735e-05, -0.009214845939264367, 0.01956005773202318]], "reference_path": "INDEPENDENT_FULL_DESIGN_SVD_CALCULATION", "reference_satterthwaite_df": [4.537872020943742, 21.470131885356377, 18.941120673241244], "status": "FAIL"}

MAIZ_AMARILLO_DURO: {"absolute_tolerance": 1e-08, "differences": {"aht_denominator_df_max_abs_difference": 1.7073276126211567e-09, "aht_f_max_abs_difference": 1.1348567974245327e-07, "aht_p_max_abs_difference": 1.8368687348946366e-08, "beta_max_abs_difference": 2.5709989692757063e-13, "cr2_covariance_max_abs_difference": 6.254811460437715e-10, "satterthwaite_df_max_abs_difference": 1.6831963378649561e-07}, "main_aht": {"delta": 0.9327022192054103, "denominator_df": 27.718661988342813, "f_statistic": 1.922361096369782, "numerator_df": 3.0, "p_value": 0.14911381757299752, "wald_chi_square": 6.183198849920666}, "main_beta": [0.00022891232880428714, 0.21948305022246628, -0.0853466073113045], "main_cr2_covariance": [[5.301674256200075e-08, 1.808350535572115e-05, -1.651591846864001e-05], [1.8083505355721153e-05, 0.015247102417066139, -0.012648830057447305], [-1.6515918468640014e-05, -0.012648830057447304, 0.013596329329053853]], "main_satterthwaite_df": [27.577487482989408, 28.755416842473917, 28.954324283685285], "reference_aht": {"delta": 0.9327022192015441, "denominator_df": 27.718661986635485, "f_statistic": 1.9223612098554617, "numerator_df": 3.0, "p_value": 0.14911379920431017, "wald_chi_square": 6.183199214968521}, "reference_beta": [0.00022891232880427087, 0.21948305022263817, -0.0853466073115616], "reference_cr2_covariance": [[5.3016741876868575e-08, 1.8083504700773124e-05, -1.6515918131468944e-05], [1.808350470077314e-05, 0.015247101791584993, -0.012648829734844262], [-1.651591813146896e-05, -0.012648829734844264, 0.013596329163515185]], "reference_path": "INDEPENDENT_FULL_DESIGN_SVD_CALCULATION", "reference_satterthwaite_df": [27.577487314669774, 28.75541677824363, 28.95432432924134], "status": "FAIL"}

## Reproduction and lock

The lock contains the implementation/test hashes and exact table/report hashes. Its SHA-256 is computed externally; no self-hash is embedded.
Rebuilds only accept existing identical bytes; different locked artifacts are never overwritten.
Run the R1 unittest suite and two independent temporary-output builds; canonical equality is required.
Full repository lifecycle failures must be adjudicated separately and must not be represented as an all-green suite.
NEXT_TIER_AUTHORIZATION_STATUS=NOT_AUTHORIZED

NEXT_ACTION=RETURN_TO_SCIENTIFIC_DIRECTOR_FOR_R1_REVIEW
