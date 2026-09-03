# S1 Scientific Identity Reframing Master v1

## 1. Executive verdict

`S1_STATUS=PASS_REFINED_CANDIDATE_FOR_DIRECTOR_FREEZE_DECISION`. This package prespecifies the paper's scientific identity before primary transient exposure selection, econometric design, estimation, scenario generation, economic translation, risk measurement, or reference-configuration comparison. `S1_FREEZE_AUTHORIZED=NO`.

## 2. Repository and freeze identity

The candidate was constructed at D0 freeze `1598a09c9a871d81834164d7ee4383e25988d8a5` on `phase/d0-transient-campaign-outcome-master-v1`. Local HEAD, the remote D0 branch, and annotated tag `d0-transient-outcome-v1-freeze` were identical before construction. Joint C0 `fca5d6e...` is followed by R0H `a50702d...` and D0 `1598a09...` without ancestry divergence.

## 3. Historical working identity

The earliest meaningful repository title is preserved verbatim from `README.md` at commit `e4710b1429ed54c557e6c0a88212a24a6fdd7d47`:

> Optimizing Agricultural Economic Value under El Niño 2026–2027 Risk in Piura, Peru: District-Level Climate-Yield Estimation and Spatial Mean-CVaR Crop Allocation

No formal historical problem statement, research question, general objective, or objective list was found as repository text. The following are therefore explicitly classified as reconstructions, not quotations: the paper sought to estimate district climate-yield relationships, generate prospective El Niño 2026-2027 outcomes, translate them into economic value, measure Mean-CVaR, and optimize a continuous spatial crop allocation. The implied Mean-CVaR role was central and prescriptive; ENSO supplied the prospective scenario context; crop allocation was interpreted as an optimized future decision.

## 4. Why the historical identity is no longer valid

| Gate | Original element | Blocking evidence | Current status | Required rewording |
|---|---|---|---|---|
| C0B4 | Continuous Rice-MAD land adjustment | No admissible land cap, adjustment envelope, reallocable area, or district water constraint | `ABANDONED` | Use finite historical references |
| C0B5 | Continuous allocation optimizer | Only two outcome-independent historical configurations on 13 common districts passed | `FINITE_REFERENCE_ARCHITECTURE` | Stress test, not optimization |
| C0B6 | Five-crop A1/A2 portfolio | Common perennial initialization failed; nonlinear tail risk cannot assume cancellation | `NOT_AUTHORIZED` | Keep perennials outside A1/A2 |
| Joint C0 | One homogeneous model | Crop-specific timing and an associational identification ceiling were frozen | `TWO_LINKED_NONMERGED_LAYERS` | Separate temporal contracts and estimands |
| D0 | Unspecified transient outcome | Seven Aug-Jul campaigns, 646 usable and 61 invalid-preserved outcomes are frozen | `PASS_FROZEN` | State exact campaign outcome support |

## 5. Current scientific problem

District-level agricultural climate-risk assessment in Piura requires a prespecified and reproducible design that respects crop-specific phenology and temporal outcome contracts while linking historical climate–yield associations to prospective ENSO 2026–2027 yield risk, a conditional secondary economic extension, and a common-scenario stress test of two historically observed Rice–MAD configurations. The current evidence identifies neither a continuous land-reallocation domain nor a five-crop portfolio, water-allocation model, or optimal future crop allocation.

`LITERATURE_GAP_CLAIM_STATUS=NOT_YET_ADJUDICATED`. The problem statement is literature-neutral: it does not assert absence, firstness, or prior-study coverage. `TARGET_CROP_IMPORTANCE_RANKING_STATUS=NOT_ESTABLISHED_NOT_REQUIRED_FOR_DESIGN`; the five crops are focal crops selected by frozen scope, not an asserted ranking of regional importance.

## 6. Current two-layer architecture

Layer 1 is five-crop climate–yield and conditional economic-risk characterization for Rice, Maíz Amarillo Duro, Mango, Limón Sutil, and Plátanos y Bananas. Its internal name is `FIVE_CROP_CLIMATE_YIELD_AND_CONDITIONAL_ECONOMIC_RISK_CHARACTERIZATION`. Each crop retains its own frozen outcome and phenology-aligned exposure architecture. Layer 1 is not a portfolio and is not aggregated into A1/A2.

Layer 2 is a finite Rice-MAD stress test of `C0B5-A2020-2021` and `C0B5-A2023-2024` on 13 common districts. Both are historically observed reference configurations. Neither is optimal, recommended, interpolable, or certified as physically or institutionally feasible for the future.

## 7. Temporal outcome architecture

Rice and MAD use district by crop by August-July agricultural campaign outcomes for seven campaigns from 2016/2017 through 2022/2023. Rice contributes 294 usable outcomes across 46 districts; MAD contributes 352 across 55 districts. Mango, Lemon, and Banana retain their frozen crop-specific calendar-year outcome/exposure contracts. The five crops are not forced into one temporal model.

## 8. Identification ceiling

The maximum current interpretation is `EMPIRICAL_ASSOCIATION_CLIMATE_RESPONSE_ONLY`. Permitted terms include association, empirical response, sensitivity, exposure-outcome relationship, and climate-related yield risk. Causal effect, treatment effect, impact caused by, and structural climate effect are prohibited unless a later identification design is separately authorized.

`CROSS_CROP_COMPARABILITY_STATUS=REQUIRES_ECONOMETRIC_DESIGN_GATE`. `RAW_COEFFICIENT_MAGNITUDE_COMPARISON_WITHOUT_COMMON_ESTIMAND_OR_SCALE=NOT_AUTHORIZED`. Any cross-crop comparison must be prespecified and respect differences in estimand, scale, sample support, climate channel, phenological window, and temporal architecture.

## 9. ENSO role

Historical estimation uses local phenology-aligned precipitation and temperature exposures and does not automatically treat ICEN as a direct district-yield regressor. ENSO state provides large-scale context under a future frozen design. `ENSO_2026_2027_INTERPRETATION=PROSPECTIVE_SCENARIO_STRESS_CONTEXT_NOT_REALIZED_FORECAST`. Prospective 2026–2027 scenarios must be built separately after estimation and diagnostics; the realization is unknown and no scenario result exists. Only then may a common authorized scenario bank propagate through crop response, conditional economic translation, and separately specified risk metrics.

## 10. Economic and risk dimensions

The dimensional identity `TM/ha × ha × 1000 kg/TM × S/kg = S` is valid. `GVP_ROLE=CONDITIONAL_SECONDARY_EXTENSION_NOT_CORE_PRIMARY_RQ`. `GVP_STATUS=NOT_YET_BUILT_REQUIRES_PRICE_MAPPING_AND_MONETARY_TREATMENT_GATE`. GVP has not been built, and price timing plus nominal monetary treatment remain gated. GVP must never be labeled profit because no cost or margin evidence is available.

Expected outcomes, downside risk, and potentially CVaR may be studied only after post-estimation risk specification. Continuous Mean-CVaR optimization is abandoned. Any later A1/A2 CVaR scope is the Rice-MAD transient block only.

## 11. Primary research-question candidates

| ID | Candidate | Adjudication |
|---|---|---|
| RQ-C1 | How do phenology-aligned climate exposures shape agricultural and conditional economic risk across focal crops in Piura under prospective ENSO 2026–2027 scenarios? | Economic scope remains too prominent |
| RQ-C2 | How are phenology-aligned climate exposures associated with yields of five focal crops in Piura under historical and prospective ENSO-related conditions? | Layer 2 is absent |
| RQ-C3 | How do two historically observed Rice–MAD configurations compare under prospective ENSO 2026–2027 yield and conditionally authorized economic risk? | Layer 1 is too narrow |
| RQ-C4 | How are phenology-aligned climate exposures associated with district-level yields across five focal crops in Piura, and what prospective ENSO 2026–2027 yield risks do these associations imply for crop-specific outcomes and for two historically observed Rice–MAD reference configurations evaluated under a common scenario bank? | Recommended |

RQ-C4 is scientifically precise, compatible with frozen support, explicitly two-layer, causally neutral, prospective rather than predictive-by-assertion, and testable. It keeps GVP outside the primary question as a conditional secondary extension.

## 12. Recommended primary research question

**How are phenology-aligned climate exposures associated with district-level yields across five focal crops in Piura, and what prospective ENSO 2026–2027 yield risks do these associations imply for crop-specific outcomes and for two historically observed Rice–MAD reference configurations evaluated under a common scenario bank?**

## 13. Subquestions

1. What crop-specific associations link prespecified phenology-aligned precipitation and temperature exposures to district-level yield outcomes within each frozen temporal contract?
2. How do crop-specific empirical climate–yield patterns and their uncertainty vary under prespecified comparison rules that respect differences in estimand, scale, sample support, climate channel, phenological window, and temporal architecture?
3. What prospective ENSO 2026–2027 yield-risk distributions arise from the separately specified scenario bank, and, if the price-mapping and monetary-treatment gates pass, what corresponding gross-production-value risk can be constructed?
4. How do the two historically observed Rice-MAD reference configurations compare on 13 common districts when evaluated with the same prospective scenario bank and prespecified risk criteria?

## 14. General objective

To characterize crop-specific associations between phenology-aligned climate exposures and district-level yields in Piura and, after separately frozen empirical-model and scenario designs, propagate those relationships through prospective ENSO 2026–2027 climate scenarios to characterize yield risk and compare two historically observed Rice–MAD reference configurations under a common scenario bank, with gross-production-value analysis retained only as a conditional extension subject to price-mapping and monetary-treatment gates.

## 15. Specific objectives

1. Characterize the crop-specific associations between prespecified phenology-aligned precipitation and temperature exposures and district-level yield outcomes within each frozen temporal contract.
2. Assess heterogeneity in crop-specific empirical climate–yield patterns and uncertainty using prespecified comparison rules that respect differences in estimand, scale, sample support, climate channel, phenological window, and temporal architecture.
3. Characterize prospective ENSO 2026–2027 yield-risk distributions and, only if the price-mapping and monetary-treatment gates pass, extend the authorized physical outcomes to corresponding gross-production-value risk.
4. Compare the prospective yield and conditionally authorized economic-risk profiles of C0B5-A2020-2021 and C0B5-A2023-2024 for Rice and MAD on their 13 common districts under an identical scenario bank and prespecified risk criteria.

## 16. Hypothesis policy

`HYPOTHESIS_ARCHITECTURE=CROP_SPECIFIC_MECHANISM_INFORMED_EXPECTATIONS`. A universal hypothesis that climate reduces yield is not justified. Any directional expectation must identify the crop, phenological stage, climate channel, functional form, and frozen evidence. Empirical coefficient signs remain results and cannot be inserted retrospectively into the hypothesis architecture.

## 17. Working-title candidates

Scores use 0-10, where higher is better except overclaim risk, where lower is better.

| ID | Candidate | Accuracy | Q1 | Specificity | Readability | Future | Overclaim risk |
|---|---|---:|---:|---:|---:|---:|---:|
| T1 | Phenology-Aligned Climate–Yield Associations and Prospective ENSO Risk in Piura, Peru: Five-Crop Evidence and Rice–Maize Reference Stress Tests | 10.0 | 9.5 | 9.5 | 8.5 | 9.5 | 0.5 |
| T2 | Climate–Yield Associations and Prospective El Niño Risk across Focal Crops in Piura, Peru | 9.0 | 8.5 | 7.5 | 9.5 | 9.0 | 1.5 |
| T3 | From Crop Phenology to Prospective ENSO Risk: District-Level Climate–Yield Associations and Rice–Maize Reference Configurations in Piura | 9.0 | 8.5 | 9.5 | 7.5 | 8.5 | 1.0 |
| T4 | Heterogeneous Climate–Yield Associations and Historical Configuration Stress Tests under Prospective ENSO Risk in Piura | 8.5 | 8.0 | 8.5 | 8.0 | 8.0 | 2.5 |
| T5 | District-Level Agricultural Climate Risk in Piura, Peru: Crop-Specific Associations and Finite Rice–Maize Comparisons | 9.0 | 8.0 | 8.5 | 9.0 | 8.5 | 1.0 |

## 18. Working title v2 for design

`WORKING_TITLE_V2_FOR_DESIGN=Phenology-Aligned Climate–Yield Associations and Prospective ENSO Risk in Piura, Peru: Five-Crop Evidence and Rice–Maize Reference Stress Tests`

`FINAL_PUBLICATION_TITLE_STATUS=PENDING_POST_RESULTS`.

## 19. Contribution architecture

1. **Data and reproducibility:** the distinctive element is the frozen end-to-end Piura evidence chain; checksums and version control are established methods, not methodological inventions.
2. **Phenology-informed climate exposure:** the distinctive element is five-crop, crop-specific temporal alignment; phenology-based exposure construction itself is established.
3. **Crop-specific empirical response:** the distinctive element is a dual temporal architecture that avoids a false common model; associational estimation is established and not causal.
4. **ENSO scenario and risk propagation:** the potential contribution is the separated, auditable path from estimation to prospective stress; scenario simulation is not a new method and does not yet exist here.
5. **Finite decision relevance:** the distinctive element is common-scenario evaluation of two frozen historical Rice-MAD references; fixed-alternative stress testing is established and produces no allocation recommendation by itself.

## 20. Novelty firewall

The paper may not claim the first Mean-CVaR agricultural model, a new CVaR method, an optimal crop allocation, the first climate-yield model, causal effects of El Niño, or globally generalizable crop responses. Any contribution must arise from the integrated evidence and design architecture rather than an invented novelty label.

## 21. Claim architecture

The machine-readable claim matrix uses only `AUTHORIZED_NOW`, `AUTHORIZED_IF_FUTURE_GATE_PASSES`, `NOT_AUTHORIZED`, and `ABANDONED`. It covers the five-crop architecture, empirical sensitivity, causal inference, ENSO scenarios, conditional GVP, profit, CVaR, A1/A2 comparison, five-crop aggregation, continuous optimization, water constraints, recommendations, D0 outcomes, temporal contracts, literature-gap claims, target-crop ranking, cross-crop comparability, and Q1-score interpretation.

## 22. Paper is and is not

The paper is a district-level climate–yield association and prospective ENSO-risk study with five focal crops, crop-specific phenology, and a finite historical Rice–MAD reference comparison, subject to future analytical gates.

It is not a continuous land-allocation optimizer, water-allocation model, causal policy evaluation, profit-maximization model, five-crop portfolio optimizer, or biological crop-simulation model.

## 23. Q1 positioning assessment

| Dimension | Score |
|---|---:|
| Research relevance | 9.0 |
| Data contribution | 8.5 |
| Reproducibility | 9.5 |
| Climate-exposure design | 9.0 |
| Phenology integration | 9.0 |
| Econometric potential | 7.0 |
| ENSO-risk relevance | 8.5 |
| Decision relevance | 7.5 |
| Methodological novelty | 6.5 |
| Overall Q1 potential | 8.3 |

`Q1_POSITIONING_SCORE_STATUS=INTERNAL_DESIGN_HEURISTIC_NOT_MANUSCRIPT_CLAIM`. The scores in this section are internal governance heuristics only; they are not evidence, results, or manuscript claims. `ARCHITECTURAL_Q1_POTENTIAL=8.3/10`. `CURRENT_EMPIRICAL_Q1_READINESS=5.8/10`. The architecture is strong, but empirical readiness remains conditional on exposure adjudication, econometric design, estimation, scenarios, price mapping, and risk specification.

## 24. Principal failure modes and preventive rules

| Failure mode | Preventive design rule |
|---|---|
| Seven transient campaigns | Parsimonious models, explicit effective degrees of freedom, small-sample uncertainty, no long-panel claim |
| Eight perennial years | Crop-specific low-dimensional designs and no asymptotic overconfidence |
| Overparameterization | Freeze a complexity budget before estimation |
| Arbitrary exposure choice | Outcome-blind exposure adjudication based on phenology, support, completeness, interpretation, and measurement |
| Scenario extrapolation | Quantify support and flag out-of-support scenario cells |
| Weak ENSO linkage | Freeze the ENSO-to-local-climate scenario bridge before generation |
| Shallow economic translation | Freeze price timing and nominal treatment; distinguish GVP from profit |
| Only two A1/A2 references | No optimality, interpolation, representativeness, feasibility, or recommendation claim |
| Excessive novelty | Enforce the claim matrix |
| Unclear layers | Separate estimands, samples, outputs, and scope; prohibit five-crop A1/A2 aggregation |

## 25. Pre-estimation commitment

- `NO COEFFICIENTS OBSERVED FOR THIS DECISION`
- `NO MODEL FIT USED`
- `NO EXPOSURE PERFORMANCE USED`
- `NO ENSO SCENARIO RESULT USED`
- `NO A1/A2 RESULT USED`
- `NO CVAR RESULT USED`

These commitments protect the title, questions, objectives, claims, and contribution architecture against result-driven reframing.

## 26. Exact next gate

`PRIMARY_TRANSIENT_ECONOMETRIC_EXPOSURE_ADJUDICATION_V1`. This next gate must remain outcome-blind and must not estimate a model.
