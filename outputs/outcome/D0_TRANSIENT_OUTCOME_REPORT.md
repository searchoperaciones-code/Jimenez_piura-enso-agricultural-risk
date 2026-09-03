# D0 Transient Campaign Outcome Master

## 1. Executive verdict

`D0_STATUS=PASS_FOR_INDEPENDENT_D0_OUTCOME_MASTER_AUDIT`; `D0_FREEZE_STATUS=UNFROZEN_CANDIDATE`; `D0_SCIENTIFIC_CONTRACT_VERSION=v1`; `D0_LINEAGE_CONTRACT_VERSION=R0H_COMPAT_V1`. The complete 707-row outcome universe is materialized with 646 valid and 61 preserved invalid rows.

## 2. Scientific and execution lineage

Joint C0 `fca5d6e519cdff764d1ca53791ae1829ef29aa00` is the frozen scientific base. R0H `a50702dbf6a2dc0037e28e0b5ae4ddd8a9c182e5` is its sole direct child and the exact authorized D0 execution parent. Its diff is limited to `scripts/audit_phenology_stage_a.py, scripts/phenology_stage_a.py, tests/test_phenology_json_serialization.py` and `SCIENTIFIC_CONTENT_CHANGE=FALSE`. All seven Joint C0 files pass their frozen SHA-256 gate.

## 3. Outcome contract

`TRANSIENT_CAMPAIGN_YIELD_RAW = SUM(PRODUCCION within Aug-Jul campaign) / SUM(COSECHA within Aug-Jul campaign)` with unit `TM_PER_HA` and observation unit district x crop x agricultural campaign.

## 4. Source-data semantics

PRODUCCION is metric tonnes. COSECHA is monthly harvested-area flow in hectares. Numeric zero is observed; source absence and blank numeric data are not zero.

## 5. Agricultural campaign calendar

Each campaign runs from August of the start year through July of the end year. Every potential row records 12 expected months independently of source-row presence.

## 6. Rice universe

Rice uses 46 frozen districts across seven campaigns: 322 potential, 294 valid, and 28 invalid rows.

## 7. MAD universe

MAD uses 55 frozen districts across seven campaigns: 385 potential, 352 valid, and 33 invalid rows.

## 8. Complete 707-row master construction

The Cartesian product of each frozen crop-specific district universe and the seven campaigns is retained. No valid-only reduction is used.

## 9. Production aggregation

CAMPAIGN_PRODUCCION_TM is the sum of observed monthly PRODUCCION values within the Aug-Jul campaign. All-missing remains missing.

## 10. Harvested-area aggregation

CAMPAIGN_COSECHA_HA is the sum of observed monthly COSECHA flows within the same Aug-Jul campaign. It is not a stock variable.

## 11. Yield calculation

Yield is calculated only after numerator and denominator presence checks and only when campaign harvested area is strictly positive. No monthly yield is constructed.

## 12. Zero denominator treatment

The 8 Rice and 11 MAD zero-denominator rows remain in the master with missing yield and `ZERO_DENOMINATOR` exclusion status. No epsilon is used.

## 13. No-source-row treatment

The 20 Rice and 22 MAD no-source rows remain in the master with missing aggregates and yield. Source absence is never encoded as numeric zero.

## 14. Missing vs zero firewall

Observed numeric zero is preserved as data. Missing numerator and missing denominator are explicit supported exclusions; both current counts are zero.

## 15. Exclusion ledger

The exclusion ledger contains exactly 61 rows and no valid observation.

## 16. Rice reconciliation

`322 = 294 + 28`; invalid reasons are {"INCOMPLETE_CAMPAIGN_NO_SOURCE_ROWS": 20, "ZERO_DENOMINATOR": 8}.

## 17. MAD reconciliation

`385 = 352 + 33`; invalid reasons are {"INCOMPLETE_CAMPAIGN_NO_SOURCE_ROWS": 22, "ZERO_DENOMINATOR": 11}.

## 18. 2017/2023 preservation

Campaigns ending 2017 and 2023 retain all 101 potential rows each, with 95 and 97 valid outcomes respectively. No extreme-year deletion occurs.

## 19. No outcome-driven selection

Yield magnitude, outliers, extreme years, ENSO, climate, and future model performance do not alter campaigns, districts, validity, or exclusions.

## 20. No climate/exposure linkage

No climate field or exposure artifact is read or merged. The primary transient econometric exposure remains not yet selected.

## 21. No price/economic linkage

No price, GVP, deflator, monetary value, or A1/A2 economic quantity is read or produced.

## 22. No model fitting

D0 creates no regression, coefficient, standard error, p-value, R-squared, model selection, cross-validation, forecast, scenario, prediction, VaR, CVaR, or optimization result.

## 23. Remaining pre-estimation gates

Primary transient exposure selection and cohort-to-campaign mapping remain separate outcome-independent gates, followed by econometric design freeze. Sown-to-harvested mapping remains downstream of econometric design and before production stress testing.

## 24. Final D0 verdict

`D0_STATUS=PASS_FOR_INDEPENDENT_D0_OUTCOME_MASTER_AUDIT`; `D0_FREEZE_STATUS=UNFROZEN_CANDIDATE`; `AUTHORIZED_D0_PARENT_SHA=a50702dbf6a2dc0037e28e0b5ae4ddd8a9c182e5`; `D0_LINEAGE_CONTRACT_VERSION=R0H_COMPAT_V1`; `NEXT_GATE=INDEPENDENT_D0_OUTCOME_MASTER_AUDIT_BEFORE_FREEZE`. Artifact SHA-256: master `9cae62fb1417fa41274f6d504515571abd428b71fecaa0d138d3b786aa538760`, ledger `6f7efe29c49b6a1edfaf47743f0b10639a9f56995f742e7513046aff63e814d8`, audit `7c6d5b0bbae359bf38cf1113adb507d7eeca2d09de03bd9f232806bef5ce2597`, config `b41b96bf307e066b819365e59a93c59050b3151293ac36a72303401bd00766ba`.
