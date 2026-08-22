# Joint C0 Outcome and Decision Architecture Integration Report

## 1. Executive verdict

`JOINT_C0_STATUS=PASS_WITH_TARGETED_PRE_ESTIMATION_GATES`. Econometric design is authorized with explicit gates; estimation and downstream calculation remain blocked.

## 2. Immutable frozen inputs

C0A sibling `5e2b32edba2e4b3eee471c669f427ef9a70fe4b6` is read only through Git objects and is not merged. C0B6 `cf99e30f2f6cfe686f760b2dd608d933e3918bc0` is the exact current frozen base.

## 3. C0A outcome semantics

PRODUCCION is `METRIC_TONNE`, YIELD_RAW is `TM_PER_HA` of harvested area, COSECHA and SIEMBRA are monthly hectare flows, and PRECIO_CHACRA is farm-gate `S_PER_KG`. VERDE_ACTUAL is an installed-area stock snapshot, not productive stock.

## 4. Transient outcome contract

Rice and MAD require `TRANSIENT_CAMPAIGN_YIELD_RAW = SUM(PRODUCCION Aug-Jul) / SUM(COSECHA Aug-Jul)`. This contract is coherent and defined but not built. Monthly-yield averaging, summation, maxima, and calendar-year substitution are forbidden.

## 5. Perennial outcome contracts

Mango, lemon, and banana use district-crop-calendar-year YIELD_RAW in TM/ha. Their valid outcome keys match the frozen calendar-year exposure keys. COSECHA is not installed stock and VERDE_ACTUAL is not productive stock.

## 6. Dual analytical layers

Layer 1 characterizes five crops without defining a combined portfolio. Layer 2 stress-tests only Rice/MAD alternatives on 13 districts and contains no perennial component.

## 7. Yield-area mapping gate

A future yield is TM per harvested hectare, while A1/A2 areas are SIEMBRA hectares. Multiplication is dimensionally tonnes but is not yet a certified physical-production mapping. `TRANSIENT_YIELD_AREA_MAPPING_STATUS=REQUIRES_SOWN_TO_HARVESTED_AREA_MAPPING_GATE` before Q = Y x A can be implemented.

## 8. Alternative timing and climate

Frozen A1/A2 monthly SIEMBRA profiles are compatible with cohort-weighted phenology windows. Future scenario exposure must be district x crop x alternative x scenario using alternative-specific weights. Generic T3 and pooled profiles remain forbidden.

## 9. Monetary dimensional identity

`TM/ha x ha x 1000 kg/TM x S/kg = S` passes dimensionally. This does not build GVP or authorize a numerical economic result.

## 10. Price temporal and nominal-value gate

No annual mean, harvest-month price, campaign-weighted price, constant future price, deflator, or normalization rule is frozen. Price mapping and monetary comparability require later explicit gates.

## 11. Aggregation and risk firewalls

Five-crop Layer 1 aggregation is not yet authorized. Five-crop A1/A2 aggregation is not authorized. `A1_A2_RISK_METRIC_SCOPE=TRANSIENT_BLOCK_ONLY`; a common perennial component cannot be assumed to cancel.

## 12. Prospective sample contracts

| Crop | Outcome unit | Exposure unit | Periods | Districts | Usable outcomes | Complete grid |
|---|---|---|---:|---:|---:|---:|
| RICE | DISTRICT_CROP_AGRICULTURAL_CAMPAIGN_AUG_JUL | DISTRICT_CROP_AGRICULTURAL_CAMPAIGN_PHENOLOGY_WEIGHTED | 7 | 46 | 294 | 322 |
| MAD | DISTRICT_CROP_AGRICULTURAL_CAMPAIGN_AUG_JUL | DISTRICT_CROP_AGRICULTURAL_CAMPAIGN_PHENOLOGY_WEIGHTED | 7 | 55 | 352 | 385 |
| MANGO | DISTRICT_CROP_CALENDAR_YEAR | DISTRICT_CROP_CALENDAR_YEAR_WINDOW | 8 | 36 | 255 | 288 |
| LEMON | DISTRICT_CROP_CALENDAR_YEAR | DISTRICT_CROP_CALENDAR_YEAR_WINDOW | 8 | 44 | 311 | 352 |
| BANANA | DISTRICT_CROP_CALENDAR_YEAR | DISTRICT_CROP_CALENDAR_YEAR_WINDOW | 8 | 54 | 390 | 432 |

Rice/MAD usable counts are prospective raw campaign-ratio candidates before model-specific exposure complete-case loss. Perennial counts are frozen annual YIELD_RAW keys and match valid exposure keys.

## 13. Short-T and extreme years

The support is short and unbalanced: seven non-left-truncated transient campaigns and eight perennial calendar years. No long-panel or causal claim is authorized. Years 2017 and 2023 are retained; later influence diagnostics are mandatory.

## 14. Identification ceiling

The maximum permissible interpretation is `EMPIRICAL_ASSOCIATION_CLIMATE_RESPONSE_ONLY`. Causal effects, structural production functions, and globally transferable biological responses are not authorized.

## 15. Empirical support and scenarios

An empirical support envelope is required before prospective prediction. Outcome contract, design, estimation, diagnostics, and support characterization must precede ENSO scenario construction.

## 16. Joint RQ architecture

The architecture supports two linked but nonmerged questions: five-crop phenology-aligned characterization and a 13-district Rice/MAD reference-configuration stress test.

## 17. Authorization matrix

The accompanying matrix distinguishes design authorization from estimation, economic translation, risk, scenario, water, and optimization authorization. No ambiguous status is used.

## 18. Targeted pre-estimation gates

Required before fitting Rice/MAD models: transient campaign Outcome Master construction and audit, primary transient econometric exposure selection, and a frozen econometric design. Perennial models may enter design now but cannot be estimated before that design is frozen.

## 19. Downstream mapping gates

Physical production requires sown-to-harvested-area mapping. Numerical value requires temporal price and monetary treatment. Scenario prediction requires a post-diagnostic empirical support envelope.

## 20. No-model-fitting certification

Joint C0 creates no coefficient, p-value, standard error, R-squared, model selection, lag optimization, cross-validation, forecast, ENSO scenario, economic result, risk metric, ranking, or optimization result.

## 21. Artifact hashes

- `outputs/joint_c0/C0_JOINT_EVIDENCE_REGISTRY.csv`: `ea9694aee2ac65f70b168b0893e091623b5b6bdb76cf4087f41ba44374d8a4a0`
- `outputs/joint_c0/C0_JOINT_COMPATIBILITY_MATRIX.csv`: `7bde825794ee80c111e45cc40715a3118295c09cdd876b34fc36c4c3afa98e4b`
- `outputs/joint_c0/C0_JOINT_AUTHORIZATION_MATRIX.csv`: `d33a24497625a5a2e9abd4991f5a67a3428fac5a7d269c849dc636a6b0d9abe3`
- `config/joint_c0/outcome_decision_integration_v1.json`: `53158bdb19d29de772f5061c0b110079500ff7a6d0b86e42b403879ed65b9899`

## 22. Final authorization

`ECONOMETRIC_DESIGN_PHASE_STATUS=AUTHORIZED_WITH_TARGETED_PRE_ESTIMATION_GATES`. Joint C0 does not authorize estimation.
