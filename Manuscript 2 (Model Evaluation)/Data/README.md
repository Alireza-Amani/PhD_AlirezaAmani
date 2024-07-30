# Data Directory for Deep Percolation Model Evaluation

This directory contains the data used for deep percolation model evaluation manuscript.

## Data Files

* **`FieldHourlyDeepPercolation_3Enclosures_4Lysimeters_201806_202210.csv`:** Hourly deep percolation measurements from four lysimeters across three enclosures.

* **`FieldSoilMoisture_4Enclosures_4Lysimeters_201806_202210.parquet`:** Half-hourly soil moisture data from the same lysimeters.

* **`FieldSoilTemperature_4Enclosures_4Lysimeters_201806_202210.parquet`:** Half-hourly soil temperature data from the same lysimeters.

* **`FieldSoilSuction_4Enclosures_4Lysimeters_201806_202210.parquet`:** Half-hourly soil suction data from the same lysimeters.

* **`OriginalForcingData.csv`:** Hourly meteorological data from the ECCC weather station (Saint-Germain de Granthan) needed to run the SVS model.

* **`OnSiteAveragedMetData.csv`:** Hourly meteorological data averaged from the on-site weather stations.

* **`processed_manual_snow.csv`:** Processed manual snow measurements taken at the site.

* **`basin_forcing.met`:** Meteorological data in the format required by the SVS model.

* **`LabParameterInfo_Mar2024.csv`:** Laboratory-measured soil parameters for the soil samples collected from the lysimeters.

## Usage

These data files are used as inputs for the Python scripts and Jupyter Notebooks in (`../Code/`).
