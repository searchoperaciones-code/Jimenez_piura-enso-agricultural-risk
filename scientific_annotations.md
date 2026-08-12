# Scientific annotations — DATASET MASTER v1

## 1. Propósito

Este documento acompaña a `build_dataset_master.py` y registra el fundamento científico, documental y de reproducibilidad de las decisiones utilizadas para construir el panel agrícola `UBIGEO × COD_CULTIVO × AÑO` de Piura.

La función de esta fase es **curar y auditar datos**, no estimar relaciones causales, generar escenarios climáticos ni ejecutar optimización Mean-CVaR. La separación entre construcción del dataset y modelización evita que decisiones de limpieza se adapten ex post a resultados econométricos u objetivos de optimización.

## 2. Matriz de respaldo científico

| Componente del pipeline | Decisión implementada | Respaldo científico / documental | Fuente |
|---|---|---|---|
| Provenance e integridad | Conservar raw inputs, registrar SHA-256, tamaño, timestamps y versión del dataset | Los principios FAIR enfatizan metadatos, trazabilidad y reutilización. El hash identifica exactamente los bytes procesados y permite detectar sustituciones de archivos. | Wilkinson et al. (2016). https://doi.org/10.1038/sdata.2016.18 |
| Fuente agrícola | Utilizar el dataset mensual del Gobierno Regional Piura como fuente primaria | La Plataforma Nacional de Datos Abiertos publica el dataset, el diccionario y los metadatos; la licencia declarada es Open Data Commons Attribution License. | GORE Piura. https://www.datosabiertos.gob.pe/dataset/campa%C3%B1a-agr%C3%ADcola-de-los-principales-cultivos-de-la-regi%C3%B3n-piura-gobierno-regional-piura-grp |
| Semántica de missing/zero | Mantener blanks como `NaN` y ceros como actividad nula | Los metadatos GORE señalan explícitamente que cero indica ausencia de actividad y blank indica dato aún no registrado; esta distinción es especialmente relevante para permanentes/semi-permanentes desde 2024. | `Formato_Metadatos_productos_dra_.docx`; GORE Piura |
| Identificadores | Mantener `UBIGEO` y `COD_CULTIVO` como strings | Son identificadores categóricos, no cantidades. Además, el diccionario GORE presenta una inconsistencia documental en el tipo/tamaño de `COD_CULTIVO`, por lo que la evidencia observada del archivo tiene prioridad para preservar la clave. | `Formato_DiccionarioDatos_productos_dra_.xlsx`; dataset GORE |
| Clave temporal | Validar `MES=AAAAMM`, verificar consistencia `ANO`–`MES` y detener ante claves mensuales duplicadas | La unicidad de la clave fuente es necesaria para impedir doble contabilización al agregar producción/áreas. Esta es una regla de integridad de datos, no una selección econométrica. | Dataset GORE; principios de provenance de Wilkinson et al. (2016) |
| Unidad analítica | Construir un panel `distrito × cultivo × año` | Los diseños county-year/district-year son estándar para relacionar variación meteorológica espacial y temporal con rendimiento agrícola. | Schauberger et al. (2017); Kukal & Irmak (2018); Schlenker & Roberts (2009) |
| Periodo principal | Usar 2016–2023 para rendimiento | 2015 está truncado en agosto en el archivo disponible. Los metadatos indican desde 2024 una lógica de blanks de `COSECHA` para permanentes/semi-permanentes hasta el cierre de campaña. Por ello el corte es una decisión de cobertura de fuente, no un recorte inducido por resultados. | GORE Piura metadata |
| Agregación anual | Sumar flujos mensuales de `PRODUCCION`, `COSECHA` y `SIEMBRA` preservando all-missing como `NaN` | FAOSTAT construye estadísticas de rendimiento a partir de producción y área cosechada y advierte que la interpretación del área en permanentes merece cautela. La agregación anual evita cocientes mensuales artificiales cuando la cosecha se registra al cierre. | FAO/FAOSTAT methodology. https://files-faostat.fao.org/production/QCL/QCL_methodology_e.pdf |
| Rendimiento | `YIELD_RAW = ΣPRODUCCION / ΣCOSECHA` solo si ambas sumas son positivas | La razón producción/área cosechada corresponde al concepto estadístico convencional de rendimiento. Se usa el cociente de sumas anuales, no la media de cocientes mensuales. | FAO/FAOSTAT methodology; literatura de climate–yield |
| Unidad de rendimiento | Mantener `YIELD_UNIT="UNRESOLVED"` | El diccionario GORE confirma que `COSECHA` es superficie cosechada, pero no explicita la unidad física de `PRODUCCION`. La plausibilidad numérica no reemplaza evidencia documental. | Diccionario GORE |
| Precio anual | Usar precio en chacra ponderado por producción mensual | La ponderación evita que meses con producción mínima tengan el mismo peso que meses de alta producción. El script no usa el precio contemporáneo como control biológico; queda preparado para un módulo económico posterior. | GORE Piura metadata; diseño económico del proyecto |
| `VERDE_ACTUAL` | Tomar el último valor no nulo del año | Se trata como variable stock/snapshot, no como flujo. Sumar valores mensuales repetiría el mismo stock a lo largo del año. | Diccionario/metadatos GORE |
| Superficie física | Incorporar `AREA_HA` de MIDAGRI y verificar cobertura espacial | La superficie agrícola 2024 se usa para comprobar cobertura y como futuro techo físico. No se interpreta como superficie actualmente activa ni libremente reasignable. | MIDAGRI-SIEA. https://siea.midagri.gob.pe/files/informativos/superficie_agricola/superficie_agricola_nacional_2024.xlsx |
| ICEN | Limpiar y validar la serie mensual; no combinarla todavía con filas distritales | ICEN es el índice oficial para El Niño Costero. Repetir un shock temporal común por distrito no crea variación ENSO independiente; su identificación se resolverá en la fase econométrica/escenarios. | IGP/ENFEN. http://met.igp.gob.pe/datos/ICEN.txt |
| Retención de extremos | Identificar `|z|>3` solo como flag, sin eliminar | La literatura clima-rendimiento estudia precisamente no linealidades y daños en extremos; eliminar observaciones extremas reales sesgaría el objeto de estudio. | Schlenker & Roberts (2009); Schauberger et al. (2017); Dhaliwal & Williams (2022) |
| Panel balanceado | Derivarlo algorítmicamente para robustez | La muestra balanceada es una especificación de robustez predefinida, no la muestra principal. Los distritos no se eligen manualmente ni en función de resultados. | Decisión de diseño pre-especificada del proyecto |
| Gate N>300 | Exigir `N>300` para panel principal y balanceado | **Decisión de diseño del proyecto**, no un umbral universal de la literatura. Su valor está en que fue fijado antes de la modelización y no se ajusta para alcanzar significancia. | Protocolo del proyecto |
| Gate espacial >99% | Exigir alta correspondencia entre panel y superficie MIDAGRI | **Decisión de diseño del proyecto**, no estándar universal. Busca evitar que el posterior vínculo con rasters o restricciones territoriales descanse en una muestra geográficamente sesgada. | Protocolo del proyecto |
| Precipitación futura | PISCO como producto peruano de referencia; CHIRPS como producto alternativo/robustez | PISCO combina información pluviométrica nacional y covariables espaciales; CHIRPS es una serie grillada de precipitación ampliamente validada. Esta fase aún no descarga rasters. | Aybar et al. (2020); SENAMHI PISCO; Funk et al. (2015); CHIRPS v3 |
| Temperatura futura | CHIRTS-ERA5 para Tmax/Tmin | El CHC documenta una serie de alta resolución que combina información CHIRTS con ERA5 para temperaturas máximas y mínimas. No se procesa en DATASET MASTER v1. | Climate Hazards Center. https://www.chc.ucsb.edu/data/chirts-era5 |
| Ventanas fenológicas futuras | No seleccionar ventanas según significancia | Estudios de clima-rendimiento muestran que el estrés durante etapas reproductivas puede ser decisivo; las ventanas se documentarán agronómicamente antes de estimar modelos. | Dhaliwal & Williams (2022) |
| Escenarios futuros | Cópulas/bootstrap fuera del alcance de este script | Las cópulas se han usado en riesgo agrícola para representar dependencias no normales y estimar CVaR. La referencia respalda la fase futura, no modifica la limpieza actual. | Nguyen-Huy et al. (2018) |
| Optimización futura | Mean-CVaR / programación estocástica fuera del alcance de este script | Existen precedentes de optimización agrícola bajo riesgo y diversificación; la fase actual solo prepara datos. | Czettritz et al. (2026); Rosa et al. (2019) |

## 3. Limitaciones y supuestos explícitos

### 3.1 Unidad física de `PRODUCCION`

La principal incertidumbre documental es que el diccionario oficial no explicita la unidad física de `PRODUCCION`. Aunque los cocientes observados son compatibles con una interpretación agronómica plausible, el pipeline no utiliza esa plausibilidad para declarar toneladas.

Por ello:

- `YIELD_RAW` se calcula numéricamente;
- `YIELD_UNIT` permanece `UNRESOLVED`;
- no se realiza una conversión monetaria que requiera multiplicar toneladas por 1,000 kg;
- la unidad deberá resolverse mediante una fuente oficial adicional antes de publicar un rendimiento como `t/ha` o un GVP monetario definitivo.

### 3.2 Inconsistencias del diccionario GORE

Se documentan al menos dos contradicciones:

1. `COD_CULTIVO` aparece documentado con tipo/tamaño incompatibles con los códigos reales observados.
2. `CULTIVO` aparece tipado como numérico pese a contener nombres textuales.

El pipeline **no corrige el archivo fuente**. Preserva los datos raw y registra la inconsistencia en `source_dictionary_inconsistencies.csv`.

### 3.3 2015 y 2024

- 2015 no constituye un año completo en la base porque el periodo comienza en agosto.
- 2024 tiene una regla documental especial de blanks en `COSECHA` para permanentes y semi-permanentes.

El panel principal de rendimiento se restringe por ello a 2016–2023. Esto debe presentarse en el manuscrito como una decisión de cobertura y consistencia del dato.

### 3.4 Ceros versus valores faltantes

Un cero y un blank no son equivalentes según los metadatos GORE. Toda transformación debe conservar esta semántica. En especial, no se imputan blanks como cero.

### 3.5 `AREA_HA`

`AREA_HA` representa superficie agrícola física cartografiada. No demuestra que esa superficie esté simultáneamente cultivada ni disponible para reasignación. En la futura optimización será un techo físico, no el presupuesto operativo de hectáreas.

### 3.6 Precio en chacra

El precio anual se construye mediante ponderación por producción. No debe introducirse automáticamente como control contemporáneo en la función biológica de rendimiento, porque puede responder endógenamente a shocks de producción/oferta.

### 3.7 Outliers

El criterio `|z|>3` es únicamente un detector de revisión. No define errores. Una observación extrema se conserva salvo que una verificación independiente demuestre un problema de fuente o digitación.

### 3.8 Gates del proyecto

Los umbrales `N>300` y cobertura espacial `>99%` son gates pre-especificados de esta investigación. No deben presentarse en un artículo como estándares universales de suficiencia estadística.

### 3.9 ICEN e identificación

La serie ICEN se limpia pero no se fusiona aún en la base distrital. Un índice común a todos los distritos varía en el tiempo, no en el espacio; repetirlo por UBIGEO no multiplica el número de shocks ENSO independientes.

### 3.10 PISCO y CHIRPS

PISCO utiliza información satelital dentro de su construcción y sus distintas versiones deben identificarse expresamente. PISCO y CHIRPS no deben describirse automáticamente como validaciones completamente independientes. La fase climática deberá congelar versión, resolución, fechas de descarga y hash de los rasters utilizados.

## 4. Salidas reproducibles de esta fase

La ejecución auditada de DATASET MASTER v1 debe conservar:

- `panel_master.csv`
- `panel_balanceado.csv`
- `icen_clean.csv`
- `land_physical.csv`
- `data_manifest.csv`
- `data_sources.csv`
- `source_dictionary_inconsistencies.csv`
- `outliers_flag.csv`
- `coverage_report.txt`
- `gate_report.json`
- reportes auxiliares de missingness, cobertura, claves y valores inválidos.

`data_sources.csv` complementa al manifiesto criptográfico: registra procedencia, URL, hash, descripción y condiciones/licencia cuando están documentadas.

## 5. Referencias

Aybar, C., Fernández, C., Huerta, A., Lavado-Casimiro, W., Vega-Jácome, F., & Felipe-Obando, O. (2020). Construction of a high-resolution gridded rainfall dataset for Peru from 1981 to the present day. *Hydrological Sciences Journal*. https://doi.org/10.1080/02626667.2019.1649411

Climate Hazards Center. (2026). *CHIRPS v3: Climate Hazards Center InfraRed Precipitation with Stations*. University of California, Santa Barbara. https://www.chc.ucsb.edu/data/chirps3

Climate Hazards Center. (n.d.). *CHIRTS-ERA5*. University of California, Santa Barbara. https://www.chc.ucsb.edu/data/chirts-era5

Czettritz, H. J. V., Hosseini-Yekani, S.-A., Yu, J., Reckling, M., & Zander, P. (2026). Diversification and policy options for risk management in arable farming. *Agricultural Systems, 234*, 104677. https://doi.org/10.1016/j.agsy.2026.104677

Dhaliwal, D. S., & Williams, M. M., II. (2022). Evidence of sweet corn yield losses from rising temperatures. *Scientific Reports, 12*, 18218. https://doi.org/10.1038/s41598-022-23237-2

Food and Agriculture Organization of the United Nations. (n.d.). *FAOSTAT agricultural production—Crops primary: Methodology*. https://files-faostat.fao.org/production/QCL/QCL_methodology_e.pdf

Funk, C., Peterson, P., Landsfeld, M., Pedreros, D., Verdin, J., Shukla, S., Husak, G., Rowland, J., Harrison, L., Hoell, A., & Michaelsen, J. (2015). The climate hazards infrared precipitation with stations—a new environmental record for monitoring extremes. *Scientific Data, 2*, 150066. https://doi.org/10.1038/sdata.2015.66

Gobierno Regional de Piura. (2025). *Campaña agrícola de los principales cultivos de la región Piura* [Dataset, diccionario y metadatos]. Plataforma Nacional de Datos Abiertos. https://www.datosabiertos.gob.pe/dataset/campa%C3%B1a-agr%C3%ADcola-de-los-principales-cultivos-de-la-regi%C3%B3n-piura-gobierno-regional-piura-grp

Instituto Geofísico del Perú / ENFEN. (2024). *Índice Costero El Niño (ICEN), versión oficial*. http://met.igp.gob.pe/datos/ICEN.txt

Kukal, M. S., & Irmak, S. (2018). Climate-driven crop yield and yield variability and climate change impacts on the U.S. Great Plains agricultural production. *Scientific Reports, 8*, 3450. https://doi.org/10.1038/s41598-018-21848-2

Ministerio de Desarrollo Agrario y Riego. (2024). *Superficie agrícola nacional 2024* [Dataset]. Sistema Integrado de Estadística Agraria. https://siea.midagri.gob.pe/files/informativos/superficie_agricola/superficie_agricola_nacional_2024.xlsx

Nguyen-Huy, T., Deo, R. C., Mushtaq, S., Kath, J., & Khan, S. (2018). Copula-based agricultural conditional value-at-risk modelling for geographical diversifications in wheat farming portfolio management. *Weather and Climate Extremes, 21*, 76–89. https://doi.org/10.1016/j.wace.2018.07.002

Rosa, F., Taverna, M., Nassivera, F., & Iseppi, L. (2019). Farm/crop portfolio simulations under variable risk: A case study from Italy. *Agricultural and Food Economics, 7*, 8. https://doi.org/10.1186/s40100-019-0127-7

Schauberger, B., Archontoulis, S., Arneth, A., Balkovic, J., Ciais, P., Deryng, D., Elliott, J., Folberth, C., Khabarov, N., Müller, C., Pugh, T. A. M., Rolinski, S., Schaphoff, S., Schmid, E., Wang, X., Schlenker, W., & Frieler, K. (2017). Consistent negative response of US crops to high temperatures in observations and crop models. *Nature Communications, 8*, 13931. https://doi.org/10.1038/ncomms13931

Schlenker, W., & Roberts, M. J. (2009). Nonlinear temperature effects indicate severe damages to U.S. crop yields under climate change. *Proceedings of the National Academy of Sciences, 106*(37), 15594–15598. https://doi.org/10.1073/pnas.0906865106

Servicio Nacional de Meteorología e Hidrología del Perú. (n.d.). *PISCO: Peruvian Interpolated data of SENAMHI's Climatological and Hydrological Observations—precipitation technical documentation*. https://web2.senamhi.gob.pe/load/file/01402SENA-8.pdf

Wilkinson, M. D., Dumontier, M., Aalbersberg, I. J., et al. (2016). The FAIR Guiding Principles for scientific data management and stewardship. *Scientific Data, 3*, 160018. https://doi.org/10.1038/sdata.2016.18
