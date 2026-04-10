# Cold Climates, Complex Hydrology: Can A Land Surface Model Accurately Simulate Deep Percolation?

## Overview

This folder contains all materials related to **Manuscript 2** of the PhD research by Alireza Amani. The study evaluates the ability of the **SVS (Soil-Vegetation-Snow) land surface model** to simulate deep percolation in a cold region, using an inverse modelling and ensemble simulation framework calibrated against lysimeter observations from Saint-Nicéphore, Québec, Canada.

Model performance in cold environments is challenged by soil freezing dynamics, snowmelt infiltration, and the high sensitivity of percolation to soil hydraulic parameters. This work quantifies model accuracy, identifies key sources of uncertainty, and assesses the structural limitations of the SVS model under cold-region conditions.

**Key Research Questions:**

*   Can the SVS land surface model accurately simulate deep percolation in a cold climate?
*   What soil hydraulic parameters most strongly control model performance?
*   How do parameter uncertainty and meteorological forcing uncertainty affect simulation results?

---

## Folder Structure

```
Manuscript 2 (Model Evaluation)/
├── Data/                  # Field data and model forcing files
│   ├── FieldHourlyDeepPercolation_3Enclosures_4Lysimeters_201806_202210.csv
│   ├── FieldSoilMoisture_4Enclosures_4Lysimeters_201806_202210.parquet
│   ├── FieldSoilTemperature_4Enclosures_4Lysimeters_201806_202210.parquet
│   ├── FieldSoilSuction_4Enclosures_4Lysimeters_201806_202210.parquet
│   ├── OriginalForcingData.csv
│   ├── OnSiteAveragedMetData.csv
│   ├── processed_manual_snow.csv
│   ├── basin_forcing.met
│   └── LabParameterInfo_Mar2024.csv
│
└── Code/                  # Analysis scripts and notebooks
    ├── Inverse_modelling_run.ipynb          # Initial wide-range ensemble simulation
    ├── Inverse_modelling_analysis.ipynb     # R² and RMSE calculation per scenario
    ├── inverse_modelling_ranges.ipynb       # Identify best-performing scenarios
    ├── create_ens.ipynb                     # Latin Hypercube Sampling for parameter sets
    ├── generate_meteo_ensemble.ipynb        # Meteorological forcing perturbation
    ├── run_ensemble.ipynb                   # Main ensemble simulation execution
    ├── evaluation.ipynb                     # Performance metric calculation
    ├── helpers.py                           # Shared helper functions
    └── README.md                            # Code documentation
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
| Original Forcing Data | Hourly | Meteorological data from ECCC station (Saint-Germain de Granthan) |
| On-Site Meteorological Data | Hourly | Averaged data from on-site weather stations |
| Manual Snow Measurements | Event-based | Processed snow depth observations from the site |
| Laboratory Parameters | — | Measured soil hydraulic parameters from lysimeter samples |

The raw lysimeter data are publicly available on **Zenodo**:  
📦 [Integrated Lysimeter Study (Deep Percolation) Data — Saint-Nicéphore, Québec](https://zenodo.org/records/10582140)

---

## Code

The analysis workflow is implemented in **Python** using Jupyter Notebooks.

A key component of this work is the **`svspyed`** package — a Python wrapper for the SVS (Soil-Vegetation-Snow) land surface model, developed by Alireza Amani. This wrapper handles all model input/output operations and enables seamless integration of the SVS model executable within Python-based ensemble workflows. See [GitHub](https://github.com/Alireza-Amani/svspyed) for the source code.

Ensemble performance evaluation relies on the **Continuous Ranked Probability Score (CRPS)**, which was implemented in Python from scratch by Alireza Amani as part of the **`CRPSnb`** package. This implementation supports neighborhood-based CRPS computation tailored to the needs of this study. See [GitHub](https://github.com/Alireza-Amani/CRPSnb) for the source code.

### Workflow

| Step | Notebook / Script | Purpose |
|---|---|---|
| 1 | `Inverse_modelling_run.ipynb` | Runs an initial ensemble with a wide range of soil hydraulic parameter values |
| 2 | `Inverse_modelling_analysis.ipynb` | Calculates R² and RMSE for each parameter scenario |
| 3 | `inverse_modelling_ranges.ipynb` | Identifies the best-performing parameter scenarios and refines ranges |
| 4 | `create_ens.ipynb` | Generates an ensemble of parameter sets using Latin Hypercube Sampling |
| 5 | `generate_meteo_ensemble.ipynb` | Creates perturbed meteorological forcing datasets |
| 6 | `run_ensemble.ipynb` | Executes the full ensemble simulation combining parameter and forcing ensembles |
| 7 | `evaluation.ipynb` | Computes final performance metrics and generates evaluation figures |
| — | `helpers.py` | Shared functions for data processing, model setup, and analysis |

### Dependencies

*   Python 3.x
*   `pandas`, `numpy`, `scipy`, `scikit-learn`
*   `matplotlib`, `seaborn`
*   `svspyed` — Python wrapper for SVS model I/O, developed by Alireza Amani ([GitHub](https://github.com/Alireza-Amani/svspyed))
*   `CRPSnb` — Python implementation of neighborhood-based CRPS, developed by Alireza Amani ([GitHub](https://github.com/Alireza-Amani/CRPSnb))
*   `jupyter`
*   **SVS model executable** — must be compiled separately

Install Python dependencies with:
```bash
pip install pandas numpy scipy scikit-learn matplotlib seaborn svspyed jupyter
```

### How to Run

1. Download the data from [Zenodo](https://zenodo.org/records/10582140) and place files in `Data/`.
2. Ensure the SVS model executable is compiled and its path is correctly set in the notebooks.
3. Run notebooks in the order listed in the Workflow table above.
4. Each notebook contains inline comments to guide you through each step.

---

## Key Findings

*   The SVS model can reproduce the general seasonal patterns of deep percolation in a cold climate, but struggles with cold-season episodic events driven by snowmelt and rain-on-snow.
*   Soil hydraulic parameters (particularly saturated hydraulic conductivity and van Genuchten shape parameters) are the dominant sources of uncertainty in model output.
*   Meteorological forcing uncertainty contributes additional variance, particularly during transitional seasons.
*   Ensemble-based inverse modelling effectively constrains parameter ranges and improves simulation performance relative to default parameter sets.

---

## Related Resources

*   📄 **Manuscript 1** — Lysimeter-based characterization of deep percolation dynamics: [`../Manuscript 1 (Deep Percolation)/`](../Manuscript%201%20(Deep%20Percolation)/)
*   📄 **Published Paper** — Amani et al. (2025), *Hydrology and Earth System Sciences*, 29, 2445: [https://hess.copernicus.org/articles/29/2445/2025/](https://hess.copernicus.org/articles/29/2445/2025/)
*   🌐 **Climate Data** — [Environment and Climate Change Canada](https://climate.weather.gc.ca/)
*   🌐 **ERA5 Reanalysis** — [Copernicus Climate Data Store](https://cds.climate.copernicus.eu/cdsapp#!/dataset/reanalysis-era5-land?tab=overview)
*   🛠 **svspyed** — [Python wrapper for SVS model I/O, developed by Alireza Amani](https://github.com/Alireza-Amani/svspyed)
*   🛠 **CRPSnb** — [Python implementation of neighborhood-based CRPS, developed by Alireza Amani](https://github.com/Alireza-Amani/CRPSnb)

---

## Citation

If you use this data or code, please cite the associated manuscript and dataset:

**Manuscript:**  
Amani, A., Boucher, M.-A., & Cabral, A. R. (2025). Cold Climates, Complex Hydrology: Can A Land Surface Model Accurately Simulate Deep Percolation? *Hydrology and Earth System Sciences*, 29, 2445.  
🔗 [https://hess.copernicus.org/articles/29/2445/2025/](https://hess.copernicus.org/articles/29/2445/2025/)

**Dataset:**  
📦 [Integrated Lysimeter Study (Deep Percolation) Data — Saint-Nicéphore, Québec](https://zenodo.org/records/10582140)

---

## Contact

**Alireza Amani** — alireza.amani101@gmail.com  
*Supervised by Prof. Marie-Amélie Boucher & Prof. Alexandre R. Cabral*  
*Université de Sherbrooke, Québec, Canada*
