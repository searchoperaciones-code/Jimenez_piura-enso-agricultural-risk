# ER2 R3 Restricted Wild-Cluster Bootstrap Real Execution v1

FINAL_VERDICT=ER2_R3_PASS_RESULTS_LOCKED_READY_FOR_DIRECTOR_REVIEW

## Contract

R3 changes inference only. The five ER1 physical-anomaly models, samples, outcomes, regressors, windows, fixed effects, unweighted specification, and district clustering are unchanged.
Each restricted null-imposed test uses 9,999 PCG64/Rademacher draws, seed 20260903 reset per contrast and joint test, deterministic sorted clusters/rows, and batches 1000 x 9 + 999.
Finite p-values use (1+EXCEEDANCES)/10000. Invalid replications are zero. Coefficient WCR p-values receive Holm step-down only within crop; joint WCR p-values remain raw.

## Coefficient sensitivity

| Crop | Variable | ER1 beta | ER1 CR2 p | ER1 Holm p | WCR p | WCR Holm p | Comparison |
|---|---|---:|---:|---:|---:|---:|---|
| RICE | RAIN_ANOM_MM | 0.00110373942 | 0.267179068 | 0.801537204 | 0.1363 | 0.4089 | CONSISTENCY |
| RICE | TMAX_ANOM_C | 0.00897648919 | 0.951339714 | 0.951339714 | 0.9535 | 0.9582 | CONSISTENCY |
| RICE | TMIN_ANOM_C | 0.0914371215 | 0.474546109 | 0.949092217 | 0.4791 | 0.9582 | CONSISTENCY |
| MAIZ_AMARILLO_DURO | RAIN_ANOM_MM | 0.000125645225 | 0.625940605 | 1 | 0.6252 | 1 | CONSISTENCY |
| MAIZ_AMARILLO_DURO | TMAX_ANOM_C | 0.236996163 | 0.122174342 | 0.366523027 | 0.1418 | 0.4254 | CONSISTENCY |
| MAIZ_AMARILLO_DURO | TMIN_ANOM_C | -0.0873889179 | 0.685395443 | 1 | 0.6875 | 1 | CONSISTENCY |
| MANGO | RAIN_ANOM_MM | -0.00174754988 | 0.933676565 | 1 | 0.9333 | 1 | CONSISTENCY |
| MANGO | TMAX_ANOM_C | 0.556341506 | 0.510699404 | 1 | 0.5156 | 1 | CONSISTENCY |
| MANGO | TMIN_ANOM_C | 0.658341916 | 0.474988026 | 1 | 0.4715 | 1 | CONSISTENCY |
| LIMON_SUTIL | RAIN_ANOM_MM__T | -0.00378088338 | 0.263895025 | 1 | 0.2704 | 1 | CONSISTENCY |
| LIMON_SUTIL | TMAX_ANOM_C__T | -0.0224561006 | 0.989953986 | 1 | 0.9905 | 1 | CONSISTENCY |
| LIMON_SUTIL | TMIN_ANOM_C__T | 0.597626337 | 0.671213099 | 1 | 0.6738 | 1 | CONSISTENCY |
| LIMON_SUTIL | RAIN_ANOM_MM__T_MINUS_1 | 5.01932017e-06 | 0.998354979 | 1 | 0.9983 | 1 | CONSISTENCY |
| LIMON_SUTIL | TMAX_ANOM_C__T_MINUS_1 | -0.931456773 | 0.520785049 | 1 | 0.5244 | 1 | CONSISTENCY |
| LIMON_SUTIL | TMIN_ANOM_C__T_MINUS_1 | -4.08571325 | 0.0229341501 | 0.137604901 | 0.0213 | 0.1278 | CONSISTENCY |
| PLATANOS_Y_BANANAS | RAIN_ANOM_MM__T | -0.00210234208 | 0.38348222 | 1 | 0.38 | 1 | CONSISTENCY |
| PLATANOS_Y_BANANAS | TMAX_ANOM_C__T | -0.325349466 | 0.82806334 | 1 | 0.8398 | 1 | CONSISTENCY |
| PLATANOS_Y_BANANAS | TMIN_ANOM_C__T | -0.0362081975 | 0.969278528 | 1 | 0.9684 | 1 | CONSISTENCY |
| PLATANOS_Y_BANANAS | RAIN_ANOM_MM__T_MINUS_1 | 0.00277608125 | 0.344521482 | 1 | 0.3557 | 1 | CONSISTENCY |
| PLATANOS_Y_BANANAS | TMAX_ANOM_C__T_MINUS_1 | -1.362423 | 0.55961875 | 1 | 0.5916 | 1 | CONSISTENCY |
| PLATANOS_Y_BANANAS | TMIN_ANOM_C__T_MINUS_1 | -6.56455869 | 0.000700983437 | 0.00420590062 | 0.0008 | 0.0048 | CONSISTENCY |

## Crop-level joint sensitivity

| Crop | ER1 AHT p | Joint WCR p | Comparison |
|---|---:|---:|---|
| RICE | 0.621376821 | 0.5589 | CONSISTENCY |
| MAIZ_AMARILLO_DURO | 0.484294503 | 0.5145 | CONSISTENCY |
| MANGO | 0.778314276 | 0.7739 | CONSISTENCY |
| LIMON_SUTIL | 0.243010318 | 0.2038 | CONSISTENCY |
| PLATANOS_Y_BANANAS | 0.0232339987 | 0.0176 | CONSISTENCY |

## Interpretation firewall

Differences are reported as inferential sensitivity and are not resolved by selecting the method that yields significance. WCR does not replace ER1 CR2 inference. No cross-crop ranking, robustness score, vote count, global five-crop FWER, or global 21-coefficient Holm was calculated.
R4, R5, R6, ENSO scenarios, GVP, VaR/CVaR, A1/A2, and optimization were not executed.

NEXT_TIER_AUTHORIZATION_STATUS=NOT_AUTHORIZED
NEXT_ACTION=RETURN_TO_SCIENTIFIC_DIRECTOR_FOR_R3_REVIEW
