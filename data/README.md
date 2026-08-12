# Data Directory

`data/raw/` is intentionally ignored by Git. It contains local copies of raw institutional inputs and large downloaded climate rasters used for full scientific reproduction. Do not commit raw inputs.

## Required Agricultural Raw Inputs

The DATASET MASTER v1 certified evidence expects these local input paths:

| Path | Certified SHA-256 status |
| --- | --- |
| `data/raw/Formato_dataset_productos_dra__ (2).csv` | `7953e95f532b97f3db1ad42dfb517dc0b5f6e98a80b1f1b0954fc1b52419c489` |
| `data/raw/Formato_DiccionarioDatos_productos_dra_.xlsx` | `9df8aedf987a7a882d265ffc629d105f8058a5208738d5dcd1b213b30d347ce0` |
| `data/raw/Formato_Metadatos_productos_dra_.docx` | `a66ede624b8d2f502df65620c84233dd04a9ebcc29ae9969c38e2272ec812ea7` |
| `data/raw/superficie_agricola_nacional_2024.xlsx` | `36f9f5d41489df4c4e19b8108c339088dd6ee2f240669d47683163077e1d9b7c`, expected hash not provided in upstream certification |
| `data/raw/ICEN.txt` | `53e82d90ad26335b081ddebf67f9293477cf6f80e3d7d9de17ddfe33fab8c03f`, expected hash not provided in upstream certification |

The certified evidence for these paths is retained in `outputs/qa/data_manifest.csv` and `outputs/qa/data_sources.csv`.

## Climate Raw Inputs

`data/raw/climate/` contains large raster inputs during CLIMATE MASTER reproduction and is intentionally excluded from Git. The certified climate raster manifest is `outputs/qa/climate/climate_data_manifest.csv`; it records source URLs, product versions, file sizes, SHA-256 hashes and validation status.

Do not copy raw climate GeoTIFFs, archives, NetCDF files, GRIB files or institutional raw files into Git.

## Processed Data

Certified processed outputs are retained under `data/processed/`. DATASET MASTER v1 and CLIMATE MASTER v1.1 processed outputs are frozen at commit `38e957e3c01fbffef242c386099b0a219d83ca70`.
