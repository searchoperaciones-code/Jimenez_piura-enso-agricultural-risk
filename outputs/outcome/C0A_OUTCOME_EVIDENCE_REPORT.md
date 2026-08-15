# C0A Outcome Evidence and Unit Adjudication Report

## 1. Executive verdict

FACT: C0A is an evidence-adjudication phase only. It does not build transient outcomes, perennial outcomes, regressions, climate-yield correlations, ENSO scenarios, economic returns, or optimization artifacts.

OFFICIAL SOURCE STATEMENT: The exact GORE Piura metadata define the source package as "Campana agricola de los principales cultivos de la region Piura" from Gobierno Regional Piura and the Oficina de Estadistica - Direccion Regional de Agricultura.

OFFICIAL SOURCE STATEMENT: Three independent DRAP official publications from the same regional statistical authority express agricultural production in tonnes or metric tonnes while jointly reporting hectares and yield units.

PROJECT INFERENCE: C0A.1 upgrades PRODUCCION unit from UNRESOLVED to CERTIFIED_INSTITUTIONAL_CONVERGENCE as METRIC_TONNE. This is not CERTIFIED_EXACT_SOURCE because the exact supplied dictionary still omits the physical unit.

PROJECT INFERENCE: Since frozen YIELD_RAW is PRODUCCION / COSECHA and COSECHA is exact-source certified as hectares, YIELD_RAW is adjudicated as TM_PER_HA for evidence purposes only.

Final C0A.1 status: PASS_UNIT_CERTIFIED_BY_INSTITUTIONAL_CONVERGENCE.

## 2. Frozen upstream identity

FACT: Required branch is phase/c0a-outcome-evidence-v1.

FACT: Required base commit is 144cb679186b8fdfe5b821aad635a7f805b7de28.

FACT: Stage B frozen tag is v0.4.0-climate-exposure-freeze.

FACT: DATASET MASTER v1, CLIMATE MASTER v1.1, PHENOLOGY MASTER v1, and CLIMATE EXPOSURE MASTER v1 are immutable for C0A.

FACT: C0A.1 does not rewrite YIELD_RAW or YIELD_UNIT in frozen upstream files.

## 3. Source inventory

FACT: Local exact source files inspected:

- data/raw/Formato_dataset_productos_dra__ (2).csv
- data/raw/Formato_DiccionarioDatos_productos_dra_.xlsx
- data/raw/Formato_Metadatos_productos_dra_.docx

FACT: Local QA and project evidence inspected:

- outputs/qa/Q1_data_readiness.md
- outputs/qa/dictionary_forensic_audit.json
- outputs/qa/source_dictionary_inconsistencies.csv
- outputs/qa/independent_yield_price_checks.csv
- outputs/qa/data_sources.csv
- outputs/qa/manuscript_data_provenance.md
- outputs/qa/dataset_schema.json
- outputs/qa/raw_agricultural_audit.json
- outputs/qa/domain_checks.json
- outputs/qa/missing_zero_semantics.csv
- outputs/qa/missing_zero_blank_samples.csv
- scientific_annotations.md

OFFICIAL SOURCE STATEMENT: The exact metadata identify the source URL as https://www.datosabiertos.gob.pe/dataset/campa%C3%B1a-agr%C3%ADcola-de-los-principales-cultivos-de-la-regi%C3%B3n-piura-gobierno-regional-piura-grp.

FACT: The external open-data page returned a WAF 418 response during C0A.1 local access, so exact dataset authority linkage relies on the local supplied metadata and dictionary rather than a live page scrape.

## 4. Evidence hierarchy

FACT: Tier 1 evidence is the exact supplied raw file, dictionary, metadata, and exact-source QA artifacts.

FACT: Tier 2 evidence is official DRAP / Gobierno Regional Piura publication evidence from the same statistical system.

FACT: Tier 3 evidence is MIDAGRI/SIEA national statistical-system evidence and is supporting only.

FACT: No Tier 4 source is used to certify PRODUCCION unit.

## 5. Variable-by-variable adjudication

### PRODUCCION

OFFICIAL SOURCE STATEMENT: The exact dictionary defines PRODUCCION as the total volume obtained of primary product when harvesting a determined area.

FACT: The supplied dictionary does not explicitly state tonnes, kilograms, quintals, or another physical unit for PRODUCCION.

OFFICIAL SOURCE STATEMENT: DRAP rice 2025 reports production in metric tonnes, harvested hectares, and kg/ha yield.

OFFICIAL SOURCE STATEMENT: DRAP lemon 2025 reports production in tonnes, harvested hectares, TM/ha yield, and S/kg farm-gate price.

OFFICIAL SOURCE STATEMENT: DRAP mango 2025 reports production in metric tonnes, harvested hectares, and metric tonnes per hectare.

Decision: semantics CERTIFIED_EXACT_SOURCE; unit CERTIFIED_INSTITUTIONAL_CONVERGENCE as METRIC_TONNE.

### COSECHA

OFFICIAL SOURCE STATEMENT: The dictionary defines COSECHA as the surface in hectares of land harvested in a determined month.

Decision: semantics CERTIFIED_EXACT_SOURCE; unit CERTIFIED_EXACT_SOURCE as ha; stock-flow status is monthly flow area.

### SIEMBRA

OFFICIAL SOURCE STATEMENT: The dictionary defines SIEMBRA as the surface in hectares of land sown in a determined month.

Decision: semantics CERTIFIED_EXACT_SOURCE; unit CERTIFIED_EXACT_SOURCE as ha; stock-flow status is monthly flow area.

### VERDE_ACTUAL

OFFICIAL SOURCE STATEMENT: The dictionary defines VERDE_ACTUAL as total installed crop area from sowing or installation until before harvest for transient crops and during production for perennial crops.

PROJECT INFERENCE: This is a stock or snapshot area variable, not a monthly flow to be summed.

UNRESOLVED: The exact dictionary does not repeat "hectareas" for VERDE_ACTUAL. The area nature is certified, but hectare unit certification is supported, not exact-source certified.

### PRECIO_CHACRA

OFFICIAL SOURCE STATEMENT: The dictionary defines PRECIO_CHACRA as the monetary value received by the agricultural producer at the farm unit. It states the price is per unit weight "S/ x Kg" and excludes IGV.

Decision: semantics CERTIFIED_EXACT_SOURCE; unit CERTIFIED_EXACT_SOURCE as S/ per kg.

### ANO

OFFICIAL SOURCE STATEMENT: The dictionary defines ANO as the year in which the agricultural campaign occurred.

FACT: QA reports zero ANO-MES mismatches in the exact raw source.

PROJECT INFERENCE: ANO is best treated as the calendar observation-year component associated with MES for C0A provenance. It is not certified as agricultural campaign start year or campaign end year.

Decision: temporal status SUPPORTED_NOT_CERTIFIED.

### MES

OFFICIAL SOURCE STATEMENT: The dictionary defines MES as the month in which the agricultural campaign occurred.

FACT: The field is numeric size 6 and exact raw values form a YYYYMM monthly sequence with no ANO-MES mismatch in QA.

Decision: calendar month encoded YYYYMM is CERTIFIED_EXACT_SOURCE.

## 6. PRODUCCION unit adjudication

FACT: Condition A is met. The exact dataset metadata identify Gobierno Regional Piura and Oficina de Estadistica - Direccion Regional de Agricultura as the source system.

FACT: Condition B is met. Multiple independent primary official DRAP publications from that same authority use tonnes or metric tonnes for agricultural production.

FACT: Condition C is met. No reliable source inspected contradicts metric tonne interpretation.

FACT: Condition D is met. Metric tonnes are dimensionally consistent with COSECHA in hectares and PRECIO_CHACRA in soles per kg.

FACT: Condition E is met conservatively. No incompatible numerical comparison is forced.

Decision: PRODUCCION_UNIT_STATUS=CERTIFIED_INSTITUTIONAL_CONVERGENCE; PRODUCCION_UNIT_DECISION=METRIC_TONNE.

## 7. COSECHA/SIEMBRA/VERDE_ACTUAL area adjudication

FACT: COSECHA unit is certified as hectares from exact dictionary text.

FACT: SIEMBRA unit is certified as hectares from exact dictionary text.

FACT: VERDE_ACTUAL semantics are certified as installed crop area.

UNRESOLVED: VERDE_ACTUAL hectare unit is supported by area context but not explicitly certified in the exact dictionary wording.

## 8. PRECIO_CHACRA adjudication

FACT: PRECIO_CHACRA is certified as farm-gate price received by the producer.

FACT: PRECIO_CHACRA unit is certified as S/ per kg and excludes IGV.

FACT: DRAP lemon publication independently reports farm-gate price in S per kilogram.

## 9. ANO/MES temporal semantics

FACT: MES is certified as standard calendar month encoded YYYYMM.

FACT: ANO matches the year component of MES in exact-source QA.

UNRESOLVED: Exact documentation does not certify ANO as campaign start year or campaign end year.

PROJECT INFERENCE: C0A should treat ANO as calendar observation year for source-record provenance while preserving the already frozen Aug-Jul climate exposure architecture.

## 10. Dimensional analysis of PRODUCCION / COSECHA

FACT: PRODUCCION is adjudicated as metric tonnes by institutional convergence.

FACT: COSECHA is exact-source certified as hectares.

PROJECT INFERENCE: PRODUCCION / COSECHA is therefore metric tonnes per harvested hectare.

Decision: YIELD_UNIT_DECISION=TM_PER_HA.

## 11. Numerical concordance checks

FACT: outputs/qa/independent_yield_price_checks.csv records 20 of 20 arithmetic checks passing for annual production over harvested area and production-weighted price.

FACT: outputs/qa/raw_agricultural_audit.json records 124514 raw rows, first month 2015-08, last month 2024-12, and zero ANO-MES mismatches.

FACT: C0A.1 searched official DRAP evidence for exact comparable production totals. The discovered primary DRAP statistics are 2025 calendar-year publications or a 2024-2025 agricultural-campaign publication.

FACT: The raw source ends at 2024-12. Therefore 2025 calendar totals and 2024-2025 campaign totals are not exactly comparable to the raw coverage without mixing periods or using incomplete coverage.

FACT: The mango 2025 note mentions 2023 and 2024 harvested area and yields, but it does not provide exact production totals for those years and cannot be used as an exact production-volume concordance case.

FACT: Export volume cannot be used as agricultural production-volume concordance. The lemon note reports export volume separately, and C0A.1 does not compare it to raw PRODUCCION.

### Rice 2025 published-yield aggregation caveat

OFFICIAL SOURCE STATEMENT: The DRAP rice 2025 publication reports production = 516,469 metric tonnes, harvested area = 51,711 hectares, and reported average yield = 9,581.68 kg/ha.

FACT: Direct arithmetic gives 516469 / 51711 = approximately 9.987604 TM/ha = approximately 9,987.604 kg/ha.

FACT: Therefore the reported average yield is not numerically equal to the simple quotient of those two published aggregate totals.

UNRESOLVED: The aggregation methodology behind the published average yield is not established by the available evidence. No inference about the official yield-aggregation procedure is invented in C0A.

FACT: This discrepancy must not be interpreted as a contradiction of the physical unit of PRODUCCION.

FACT: The rice 2025 publication remains valid Tier-2 evidence for institutional use of production in metric tonnes, harvested area in hectares, and yield in kg/ha.

FACT: The rice 2025 publication must not be treated as numerical validation of the project's frozen aggregate yield definition, YIELD_RAW = SUM(PRODUCCION) / SUM(COSECHA).

FACT: C0A therefore retains EXACT_NUMERICAL_CONCORDANCE = NO_EXACT_NUMERICAL_CONCORDANCE_AVAILABLE.

FACT: The lemon and mango 2025 arithmetic comparisons are external dimensional-consistency checks only. They are not exact raw-data concordance cases because 2025 lies outside the frozen raw agricultural coverage ending 2024-12.

Decision: C0A_1_NUMERICAL_CONCORDANCE_STATUS=NO_EXACT_NUMERICAL_CONCORDANCE_AVAILABLE.

## 12. Contradictions and unresolved issues

FACT: source_dictionary_inconsistencies.csv records dictionary conflicts for COD_CULTIVO and CULTIVO and notes that PRODUCCION unit is not explicitly stated in the supplied dictionary.

CONTRADICTIONS: No material contradiction was found for PRODUCCION metric tonne adjudication.

UNRESOLVED: No material PRODUCCION or YIELD_RAW unit claim remains unresolved after C0A.1. Residual non-certifications remain for ANO campaign-start/end identity and VERDE_ACTUAL exact hectare unit.

## 13. Implication for transient Outcome Master

PROJECT INFERENCE: A future transient outcome phase may use PRODUCCION as metric tonnes and YIELD_RAW as TM/ha for unit labeling, but C0A.1 is not authorized to build outcomes.

FACT: C0A.1 does not modify frozen upstream YIELD_UNIT values.

## 14. Implication for perennial Outcome Master

PROJECT INFERENCE: VERDE_ACTUAL should be treated as stock/snapshot area evidence, not a monthly flow, for any future perennial design.

UNRESOLVED: Exact hectare unit certification for VERDE_ACTUAL remains incomplete.

## 15. Implication for future monetary translation

FACT: PRECIO_CHACRA is S/ per kg.

FACT: PRODUCCION is adjudicated as metric tonnes by institutional convergence.

PROJECT INFERENCE: Future monetary translation is DIMENSIONALLY_AUTHORIZED_NOT_BUILT and requires 1 metric tonne = 1000 kg.

FACT: GVP construction is blocked in C0A.1 and no monetary dataset is built.

## 16. Explicit list of actions NOT authorized

FACT: C0A.1 does not authorize transient outcome construction.

FACT: C0A.1 does not authorize perennial outcome construction.

FACT: C0A.1 does not authorize econometric estimation, causal interpretation, model selection, climate-yield correlation, ENSO classification, scenario construction, economic-return construction, GVP construction, or optimization.

FACT: Causal interpretation is not authorized.

FACT: C0A.1 does not authorize modifying DATASET MASTER, CLIMATE MASTER, PHENOLOGY MASTER, or CLIMATE EXPOSURE MASTER artifacts.

## 17. Final C0A verdict

C0A_1_STATUS=PASS_UNIT_CERTIFIED_BY_INSTITUTIONAL_CONVERGENCE.

C0A.1 is ready for independent evidence review only. It does not freeze C0A, does not authorize C1/C2, and does not authorize econometrics or optimization.
