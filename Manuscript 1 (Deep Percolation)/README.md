# Analyzing Deep Percolation Dynamics: A Lysimeter-Based Study in a Cold Environment

## Overview

This folder contains all materials related to **Manuscript 1** of the PhD research by Alireza Amani. The study investigates deep percolation (potential groundwater recharge) dynamics in a cold region using direct lysimeter measurements, focusing on event characterization, seasonality, and the driving factors that govern water movement below the root zone.

Cold regions present distinct hydrological challenges — frozen soils, snow accumulation, snowmelt pulses, and rain-on-snow events — all of which can profoundly alter percolation patterns. This work quantifies these effects using a multi-year field dataset from Saint-Nicéphore, Québec, Canada.

**Key Research Questions:**

*   What are the temporal patterns and magnitudes of deep percolation in a cold environment across seasons?
*   What meteorological and soil factors drive deep percolation events in cold versus warm seasons?
*   How do events differ in timing, volume, and intensity between lysimeters and enclosures?

---

## Folder Structure

```
Manuscript 1 (Deep Percolation)/
├── Data/                  # Raw and processed field data
│   ├── DailyMeteo_201707_202212.csv
│   ├── HourlyMeteo_201707_202212.parquet
│   ├── FieldHourlyDeepPercolation_3Enclosures_4Lysimeters_201806_202210.csv
│   ├── FieldSoilMoisture_4Enclosures_4Lysimeters_201806_202210.parquet
│   ├── FieldSoilSuction_4Enclosures_4Lysimeters_201806_202210.parquet
│   ├── FieldSoilTemperature_4Enclosures_4Lysimeters_201806_202210.parquet
│   ├── InputWater_SVSoutput_ensAve.csv
│   ├── Lysimeter_Objects/     # Processed event objects (*.pkl per lysimeter)
│   └── Lit_Review/            # Scopus literature search results (CSV)
│
└── Code/                  # Analysis scripts and notebooks
    ├── event_identification.ipynb   # Identify and characterize percolation events
    ├── analysis.ipynb               # Statistical analysis and visualizations
    ├── plot_results.ipynb           # Generate manuscript figures
    ├── user_functions.py            # Shared helper functions
    └── README.md                    # Code documentation
```

---

## Data

Field data were collected at the **Saint-Nicéphore** experimental site in Québec, Canada, from **June 2018 to October 2022**. The dataset includes:

| Dataset | Temporal Resolution | Description |
|---|---|---|
| Deep Percolation | Hourly | Four lysimeters across three enclosures |
| Soil Moisture | Half-hourly | Volumetric water content at multiple depths |
| Soil Suction | Half-hourly | Matric potential at multiple depths |
| Soil Temperature | Half-hourly | Temperature at multiple depths |
| Meteorological | Hourly & Daily | Rainfall, snowfall, air temperature, snow depth, etc. |

The raw lysimeter data are publicly available on **Zenodo**:  
📦 [Integrated Lysimeter Study (Deep Percolation) Data — Saint-Nicéphore, Québec](https://zenodo.org/records/10582140)

---

## Code

The analysis is implemented in **Python** using Jupyter Notebooks:

| Notebook / Script | Purpose |
|---|---|
| `event_identification.ipynb` | Reads raw data and identifies discrete deep percolation events |
| `analysis.ipynb` | Statistical analysis: seasonal comparisons, correlation with drivers |
| `plot_results.ipynb` | Generates all manuscript figures |
| `user_functions.py` | Shared functions for data loading, event detection, and plotting |

### Dependencies

*   Python 3.x
*   `pandas`, `numpy`, `scipy`
*   `pingouin` (statistical testing)
*   `matplotlib`, `seaborn`, `plotly`
*   `jupyter`

Install dependencies with:
```bash
pip install pandas numpy scipy pingouin matplotlib seaborn plotly jupyter
```

### How to Run

1. Download the data from [Zenodo](https://zenodo.org/records/10582140) and place files in `Data/`.
2. Run `event_identification.ipynb` to process raw data and identify percolation events.
3. Run `analysis.ipynb` to perform statistical analysis.
4. Run `plot_results.ipynb` to reproduce manuscript figures.

---

## Key Findings

*   Deep percolation in cold regions is highly episodic, with distinct seasonal signatures.
*   Snowmelt and rain-on-snow events are dominant drivers of large percolation episodes in the cold season.
*   Soil temperature and frost depth strongly modulate the timing and volume of cold-season percolation.
*   Warm-season events are controlled primarily by rainfall intensity and antecedent soil moisture.

---

## Related Resources

*   📄 **Manuscript 2** — Evaluation of the SVS land surface model for simulating deep percolation: [`../Manuscript 2 (Model Evaluation)/`](../Manuscript%202%20(Model%20Evaluation)/)
*   🌐 **Climate Data** — [Environment and Climate Change Canada](https://climate.weather.gc.ca/)
*   🌐 **ERA5 Reanalysis** — [Copernicus Climate Data Store](https://cds.climate.copernicus.eu/cdsapp#!/dataset/reanalysis-era5-land?tab=overview)

---

## Citation

If you use this data or code, please cite the associated manuscript and dataset (details to be updated upon publication).

---

## Contact

**Alireza Amani** — alireza.amani101@gmail.com  
*Supervised by Prof. Marie-Amélie Boucher & Prof. Alexandre R. Cabral*  
*Université de Sherbrooke, Québec, Canada*
