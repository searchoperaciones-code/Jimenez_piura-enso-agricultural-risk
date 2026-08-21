# C0B3 Perennial Stock, Productivity & Adjustment Master

## 1. Executive verdict

`ARCHITECTURE_ADJUDICATION=ARCH_F_SET3_REQUIRED_ALL_PERENNIALS`.

The targeted C0B3B correction changes the evidence basis without changing the architecture verdict. `VERDE_ACTUAL_STATUS=INSTALLED_STOCK_CERTIFIED`, its unit is `ha`, and `SIEMBRA` directly observes monthly gross area installed by sowing or transplanting. Installed stock is therefore observed and unit-certified, and gross establishment is substantially observed for mango, limón sutil, and plátanos/bananas.

P2 nevertheless remains unsupported. `COSECHA` is harvest-flow area rather than direct productive stock; the published extract omits removal, substitution, state-change, and revision components; all productivity lags remain context only; and C0B1 defines no numeric near-term horizon. Architecture F survives because the evidence does not identify a complete defensible endogenous perennial stock-transition architecture, not because installed stock is unobserved.

## 2. Frozen C0B1/C0B2 identity

- Required branch: `phase/c0b3-perennial-feasibility-v1`.
- C0B2 freeze commit and C0B3 base: `eee4cfae0556135dd7f26e553b29a8437498b6ea`.
- C0B2 freeze subject: `Freeze C0B2 spatial hydraulic crosswalk`.
- Frozen C0B1 primary: `ARCH_E_MIXED_STOCK_FLOW_PLUS_MARGINAL_ADJUSTMENT`.
- Frozen C0B1 fallback: `ARCH_F_TRANSIENT_ENDOGENOUS_PERENNIAL_EXOGENOUS`.
- Frozen P2: installed stock plus annual establishment and removal flows conditional on C0B3.
- `WATER_HARD_CONSTRAINT_CURRENTLY_AUTHORIZED=FALSE` remains unchanged.

The preflight pins every C0B1 and C0B2 artifact by SHA-256 and rejects tracked or staged modifications.

## 3. Why perennial stock-flow ontology matters

Installed stock is the physical area occupied by an established perennial or semipermanent crop. Productive stock is the subset or state relevant to contemporaneous productive output. Gross establishment is area installed during the period; it is not necessarily net expansion. Removal, replacement, or other exits are separate state transitions. Harvest-flow area is an activity measure and cannot silently replace any stock.

C0B1 does not require removal to be freely endogenous. An observed or defensibly fixed removal series could qualify, but no such published series exists. A P2 implementation still needs a complete and compatible transition system without invented exits, lags, or horizon assumptions.

## 4. Source hierarchy

The exact official package is published by Gobierno Regional de Piura / Dirección Regional de Agricultura:

- [Data dictionary XLSX](https://www.datosabiertos.gob.pe/sites/default/files/Formato_DiccionarioDatos_productos_dra_.xlsx), source date `2025-05-27`, SHA-256 `9df8aedf987a7a882d265ffc629d105f8058a5208738d5dcd1b213b30d347ce0`.
- [Metadata DOCX](https://www.datosabiertos.gob.pe/sites/default/files/Formato_Metadatos_productos_dra_.docx), source date `2025-05-27`, SHA-256 `a66ede624b8d2f502df65620c84233dd04a9ebcc29ae9969c38e2272ec812ea7`.
- The official [SIEA instruments page](https://siea.midagri.gob.pe/index.php/nosotros/instrumentos-de-gestion) publishes the current primary [methodological PDF](https://siea.midagri.gob.pe/media/documentos/Lineamientos_Metodologicos_SIEA.pdf). Redirect-following retrieval returned HTTP `200`, media type `application/pdf`, `491` pages, and SHA-256 `8fe81dcf74acc74803f9fa0c19ace73d54024133a527854e9f95e7d846df2230`. Its pp. `61-65` directly support the permanent-crop green-area, hectare, sown-area, harvested-area, loss, substitution, and accounting definitions used here.
- Legal approval is authenticated separately by the official [RM 0035-2013-AG PDF](https://siea.midagri.gob.pe/media/documentos/RM_035-2013-AG.pdf), SHA-256 `70d173d9a407e0fb205f1cbefa1e149f9a3a9f7167b9834e97c8d0846abca2de`. `RESOLUCION_MINISTERIAL_N_0035-2013-AG`, dated `2013-02-01`, `APPROVES_SIEA_METHODOLOGICAL_GUIDELINES`; the resolution is the legal approval source, while pp. `61-65` of the guidelines are the methodological definition source.
- `RM_0194-2016-MINAGRI` does not approve the original guidelines. Its role is `INCORPORATES_COMPLETE_AGRICULTURAL_STATISTICAL_SECTOR_REGISTER_INTO_F1`, authenticated by the official Diario Oficial El Peruano archive hosted by Congreso, SHA-256 `44b51dfc528a6352c9aa0189601c3c3e7f04c7d17afecab17aa8d5076fb15fb0`, p. `5`.
- The historical SIEA locator under `/portal/media/attachments/` now redirects to the official SIEA home page as HTML and is recorded as obsolete, not as a PDF. The `normaslegalesonline.pe` copy is retained only as `AUXILIARY_RETRIEVAL_COPY_NOT_CANONICAL_NOT_REQUIRED_FOR_SCIENTIFIC_CLAIMS`; no scientific claim depends solely on it.

- `SIEA_PRIMARY_SOURCE_AUTHORITY=MIDAGRI_SIEA`.
- `SIEA_PRIMARY_REQUESTED_URL=https://siea.midagri.gob.pe/media/documentos/Lineamientos_Metodologicos_SIEA.pdf`.
- `SIEA_PRIMARY_FINAL_RESOLVED_URL=https://siea.midagri.gob.pe/media/documentos/Lineamientos_Metodologicos_SIEA.pdf`.
- `SIEA_PRIMARY_HTTP_STATUS=HTTP_200_APPLICATION_PDF`.
- `SIEA_PRIMARY_PDF_SHA256=8fe81dcf74acc74803f9fa0c19ace73d54024133a527854e9f95e7d846df2230`.
- `SIEA_APPROVING_NORM=RESOLUCION_MINISTERIAL_N_0035-2013-AG`.
- `SIEA_APPROVING_NORM_DATE=2013-02-01`.
- `SIEA_APPROVING_NORM_ROLE=APPROVES_SIEA_METHODOLOGICAL_GUIDELINES`.
- `SIEA_LEGAL_VS_METHODOLOGICAL_SOURCE_FIREWALL=PASS_DISTINCT_SOURCE_ROLES_RECORDED`.

The official XLSX and DOCX are byte-identical to the repository raw copies. SIEA is used only for variable and source-system state semantics. It is not evidence for a biological maturity parameter. INIA, SENASA, SENAMHI, GORE Piura, and FAO crop sources remain context-only where specified in the evidence registry.

## 5. Dataset variable semantics

The DRAP dictionary defines `VERDE_ACTUAL` as a numeric monthly total area of installed crops: from installation until harvest for transients and from installation through production for permanent crops. The SIEA method certifies hectare units and defines permanent-crop green area as area in growth plus area in production.

`SIEMBRA` is monthly gross area installed by sowing or transplanting, measured in hectares. It is not total existing stock, campaign-cumulative stock, or net stock expansion.

`COSECHA` is harvest-flow area in hectares. For permanent crops, the same area may have repeated collections and is reported in the final production month; similar semipermanent crops follow year-end reporting. `COSECHA != INSTALLED_STOCK` and `COSECHA != DIRECT_PRODUCTIVE_STOCK`.

Zero means no activity and blank means not yet registered. `PRODUCCION`, `PRECIO`, `YIELD_RAW`, outcome estimates, and optimization results do not participate in state selection.

## 6. VERDE_ACTUAL adjudication

`VERDE_ACTUAL_STATUS=INSTALLED_STOCK_CERTIFIED` and `VERDE_ACTUAL_UNIT=ha`.

- Mango: `INSTALLED_PERENNIAL_STOCK_AREA`.
- Limón sutil: `INSTALLED_PERENNIAL_STOCK_AREA`.
- Plátanos/bananas: `CONTINUOUS_SEMIPERMANENT_INSTALLED_STAND_AREA`, not individual plant stock.

The exact dictionary establishes installed-area semantics; SIEA independently supplies the missing hectare and source-system state interpretation. The published DRAP extract does not expose SIEA's separate growth and production components, so installed-stock certification does not imply productive-stock or exact transition certification.

## 7. Mango state architecture

Mango remains `WOODY_PERENNIAL_ORCHARD`. `VERDE_ACTUAL` directly provides observed installed hectares, and `SIEMBRA` directly provides monthly gross installed hectares. `COSECHA/HARVEST_AREA` remains `HARVESTED_AREA_PROXY_ONLY` for productive stock.

The [INIA Kent manual](https://repositorio.inia.gob.pe/items/f420a985-8d1d-4199-991d-9cbf7b9cd9a1) documents age heterogeneity and renewal practices in Piura, but supplies no district-month removal flow or general transition to economically productive bearing stock. The regional five-year first-production statement remains `CONTEXT_ONLY`; first production after graft cannot substitute for the model-required installation-to-economically-productive transition.

## 8. Limón Sutil state architecture

Limón sutil remains `WOODY_PERENNIAL_ORCHARD`. `VERDE_ACTUAL` directly provides observed installed hectares, `SIEMBRA` directly provides monthly gross installed hectares, and `COSECHA/HARVEST_AREA` remains `HARVESTED_AREA_PROXY_ONLY`.

The [SENASA lemon guide](https://www.gob.pe/institucion/senasa/informes-publicaciones/924871-guia-de-buenas-practicas-agricolas-para-cultivo-de-limon) establishes rootstock-dependent precocity. The [SENAMHI Cartilla 12](https://www.ana.gob.pe/sites/default/files/normatividad/files/condiciones_agroclimaticas_limon_0.pdf) provides first-harvest context for limón sutil. Neither identifies an economically productive area state or an admissible general transition rule, so lag evidence remains `CONTEXT_ONLY`.

## 9. Plátanos/Bananas state architecture

`BANANA_STATE_ONTOLOGY=CONTINUOUS_MOTHER_DAUGHTER_GRANDDAUGHTER_STAND`. `WOODY_PERENNIAL_ONTOLOGY_FOR_BANANA=REJECTED`.

`VERDE_ACTUAL` observes continuing installed stand hectares. `SIEMBRA` observes gross stand installation or replant establishment, but does not represent internal mother-daughter-sucker succession inside an already installed stand. An installed stand may continue producing through succession without a new annual district-area establishment decision.

The [INIA plantain manual](https://repositorio.inia.gob.pe/items/6a74c3c1-995a-4748-94a9-51e668859188) supports mother-daughter-granddaughter management. [FAO banana material](https://www.fao.org/land-water/databases-and-software/crop-information/banana/en/) supports first-crop and ratoon distinctions. These sources remain context only because the target category aggregates systems and does not identify district-level productive-state or stand-exit flows.

## 10. Installed-stock evidence

All three installed-stock gates pass:

- `MANGO_INSTALLED_STOCK_STATUS=OBSERVED_AND_UNIT_CERTIFIED`.
- `LEMON_INSTALLED_STOCK_STATUS=OBSERVED_AND_UNIT_CERTIFIED`.
- `BANANA_INSTALLED_STOCK_STATUS=OBSERVED_AND_UNIT_CERTIFIED`.

The historical `VERDE_ACTUAL` series may be used for installed-stock characterization, district/crop baseline measurement, baseline initialization, and descriptive historical trajectories. Certification does not authorize arbitrary perennial area adjustment by an optimizer or any time-varying future perennial stock path.

## 11. Productive-stock evidence

`PRODUCTIVE_STOCK_STATUS=HARVESTED_AREA_PROXY_ONLY` for all three crops.

The source system conceptually distinguishes area in growth and area in production, but the published extract does not expose those fields. `COSECHA` records harvest-flow area and may aggregate repeated collection from continuing stands. It cannot identify juvenile area, temporarily nonbearing area, renewed canopy, rootstock-dependent bearing state, or the nonharvested successor components of banana stands.

## 12. Establishment evidence

`ESTABLISHMENT_FLOW_STATUS=DIRECTLY_OBSERVED` for mango, limón sutil, and plátanos/bananas.

The observed concept is monthly gross area installed by sowing or transplanting. It does not distinguish net expansion from replant establishment. For banana, it specifically does not count every internal sucker succession event in an already installed stand. New establishment still does not imply immediate productive stock.

## 13. Removal/replacement evidence

`STOCK_FLOW_IDENTITY_STATUS=APPROXIMATE_ONLY`. `REMOVAL_FLOW_STATUS=NOT_OBSERVED` and `REMOVAL_DERIVABILITY=NOT_DERIVABLE_WITHOUT_ASSUMPTION` for every crop.

SIEA separately handles lost area, permanent-crop substitution, growth-to-production change, and verification or rectification. The public DRAP extract omits these components. Therefore `VERDE_(t-1) + SIEMBRA_t - VERDE_t` is an `ACCOUNTING_RESIDUAL_DIAGNOSTIC`, not observed removal, and cannot enter the decision model. Removal is not set to zero.

Native monthly diagnostics are:

| Crop | Total candidate pairs | Nonmissing analyzable pairs | Missing pairs | Exact identity pairs | Positive | Negative | Min | Max | Mean |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Mango | 4111 | 4111 | 0 | 4076 | 3 | 32 | -100 | 40 | -0.155254 |
| Limón Sutil | 4730 | 4730 | 0 | 4699 | 0 | 31 | -683 | 0 | -0.274841 |
| Plátanos/Bananas | 5576 | 5574 | 2 | 5481 | 2 | 91 | -470 | 50 | -0.751525 |

High concordance supports internal coherence. It does not certify the omitted transition component or create a model parameter.

## 14. Maturity/productivity lag

All crop lag statuses remain `CONTEXT_ONLY`; `MODEL_AUTHORIZED_BIOLOGICAL_PARAMETERS_N=0`.

- Mango requires installation to economically productive or bearing stock, not first fruit or first production after graft.
- Limón sutil requires the same concept and cannot generalize one rootstock or management context.
- Banana requires separate initial stand establishment and ratoon/sucker succession concepts.

The nine biological evidence rows remain scientifically valid context. No midpoint, single maturity year, cultivar-generic value, immediate-productivity assumption, or numeric removal parameter is authorized.

## 15. Near-term ENSO relevance

`DECISION_HORIZON_STATUS=QUALITATIVELY_NEAR_TERM_ONLY` and `NO_FROZEN_NUMERIC_HORIZON`.

`NEAR_TERM_ESTABLISHMENT_OUTPUT_RELEVANCE=UNRESOLVED` for all three crops. A qualitative horizon is not compared with context-only lag values, and C0B3 creates no numeric horizon.

## 16. Crop-specific P2 verdicts

| Necessary condition | Mango | Limón | Banana |
|---|---|---|---|
| Installed stock | PASS | PASS | PASS |
| Unit | PASS | PASS | PASS |
| Establishment | PASS | PASS | PASS* |
| Productive stock | PROXY | PROXY | PROXY |
| Removal | FAIL | FAIL | FAIL |
| Lag | CONTEXT | CONTEXT | CONTEXT |
| Numeric horizon | NO | NO | NO |
| P2 | FAIL | FAIL | FAIL |
| P3 | REQUIRED | REQUIRED | REQUIRED |

`*` Banana passes gross stand establishment only; `SIEMBRA` is not internal sucker succession.

For every crop, `P2_OPERATIONAL_STATUS=NOT_SUPPORTED_USE_P3`. Installed stock and gross establishment passing cannot compensate for failed productive-state, removal, lag, and horizon conditions.

## 17. P3 fallback implications

`P3_RESOLUTION=P3_FIXED_STOCK_NEAR_TERM_HORIZON` and `PERENNIAL_DECISION_ENDOGENEITY=EXOGENOUS_FIXED_WITHIN_CURRENT_NEAR_TERM_ARCHITECTURE`. P3 means observed perennial installed stocks are fixed/exogenous within the current near-term optimizer. Exogenous does not mean unobserved.

`VERDE_ACTUAL` may support historical installed-stock characterization, district/crop baseline measurement, descriptive historical trajectories, and baseline initialization of the future decision problem. Historical observed variation does not authorize modeled future variation. `FUTURE_TIME_VARYING_EXOGENOUS_PERENNIAL_PATH_STATUS=NOT_YET_AUTHORIZED`; any later non-fixed exogenous future path requires a separate explicit scientific gate and ontology adjudication.

P3 does not authorize `ARBITRARY_TIME_VARYING_FUTURE_PERENNIAL_STOCK_PATH`, `SCENARIO_SPECIFIC_PERENNIAL_AREA_REALLOCATION`, `OPTIMIZER_CHOSEN_PERENNIAL_ADJUSTMENT`, `ENDOGENOUS_PERENNIAL_ESTABLISHMENT`, or `ENDOGENOUS_PERENNIAL_REMOVAL`. It also does not authorize setting perennial area to zero or discarding climate-response analysis.

## 18. Architecture adjudication

The independent C0B3A audit attempted to falsify architecture F. It found that initial C0B3 had underclassified `VERDE_ACTUAL` and `SIEMBRA`. The official data dictionary plus SIEA methodology establish installed hectares and gross establishment. Those corrections remove two former blockers but do not recover the complete P2 transition system.

- `ARCH_E_SET2_STATUS=NOT_SUPPORTED`.
- `ARCH_F_SET3_STATUS=REQUIRED`.
- `ARCHITECTURE_ADJUDICATION=ARCH_F_SET3_REQUIRED_ALL_PERENNIALS`.
- `P3_REQUIRED_CROPS=MANGO;LIMON SUTIL;PLATANOS Y BANANAS`.
- `P2_FAILURE_INDEPENDENT_OF_CURRENT_HORIZON=TRUE`.

Architecture F survives for the stronger reason that productive state, removal/replacement, model-admissible productivity timing, and numeric horizon compatibility remain insufficient.

## 19. Forbidden interpretations

The following remain forbidden:

- `COSECHA/HARVEST_AREA` as installed or directly observed productive stock.
- `SIEMBRA/SOWN_AREA` as total stock, cumulative stock, net expansion, or internal banana sucker succession.
- The stock accounting residual as observed removal.
- Unobserved removal as zero.
- New establishment as immediate productive stock.
- First harvest or first fruit as economically productive bearing stock.
- A context-only lag promoted to a model value.
- A numeric near-term horizon invented in C0B3.
- P2 supported merely because installed stock and gross establishment pass.
- P3 described as unobserved stock.
- An arbitrary time-varying future exogenous perennial stock path under P3.
- Scenario-specific or optimizer-chosen perennial area reallocation.
- Endogenous perennial establishment or removal in the current near-term architecture.
- Outcome, climate-response, profitability, water, or optimizer results used as ontology evidence.

## 20. Remaining gaps

The P2 blockers are:

1. Direct productive/bearing area or a certified derivation rule in the published analytical domain.
2. Observed or officially fixed removal/replacement and stand-exit flows compatible with C0B1 P2.
3. Crop-, cultivar-, system-, management-, and region-compatible productivity transitions.
4. A frozen numeric planning horizon for admissible lag compatibility.

The installed-stock unit and gross-establishment semantics are no longer gaps. Resolving either of the remaining gaps alone would still not operationalize P2.

## 21. Final C0B3 verdict

`C0B3_STATUS=PASS_FOR_FINAL_NOTARIAL_C0B3_FREEZE_AUDIT`.

This targeted patch is not a scientific freeze. P2 remains unsupported for all three crops, P3 remains required, and `ARCH_F_SET3_REQUIRED_ALL_PERENNIALS` remains the adjudication. No optimizer, water model, water hard constraint, biological model parameter, staging, commit, push, or tag is authorized.
