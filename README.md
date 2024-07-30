# Cold Region Deep Percolation: Characterization, Drivers, and Modeling Challenges

## Overview

This repository documents the PhD research of Alireza Amani, focused on understanding and modeling deep percolation (potential groundwater recharge) in cold regions. The research addresses the unique challenges posed by soil freezing, snow accumulation, and rain-on-snow events in these environments.

**Key Research Questions:**

*   What are the distinct patterns and drivers of deep percolation in cold versus warm seasons?
*   Can the SVS land surface model accurately simulate deep percolation in a cold climate, and what are its limitations?

**Research Approach:**

1.  **Experimental Investigation:** Direct measurement of deep percolation using lysimeters in a cold environment.
2.  **Process-Based Model Evaluation:** Assessment of the SVS land surface model's ability to simulate deep percolation under complex cold region conditions.

## Repository Structure

*   **Manuscript 1 (Analyzing deep percolation dynamics: a lysimeter-based study in a cold environment):**
    *   **Data:** Raw and processed lysimeter data, meteorological observations.
    *   **Code:** Scripts for data analysis and figure generation.
    *   **Manuscript:** Drafts and final version of the manuscript.
    *   **Figures:** Figures and visualizations for the manuscript.

*   **Manuscript 2 (Cold Climates, Complex Hydrology: Can A Land Surface Model Accurately Simulate Deep Percolation?):**
    *   **Data:** Raw and processed lysimeter data, meteorological observations, model input/output.
    *   **Code:** Scripts for model setup, simulation, and evaluation.
    *   **Manuscript:** Drafts and final version of the manuscript.
    *   **Figures:** Figures and visualizations for the manuscript.
    *   **SVS_Source_Code:** Modified source code for the SVS model. This must be compiled to provide the executable for simulations.
*   **Thesis:**
    *   **Thesis_AlirezaAmani.pdf:** The complete PhD thesis document.
    *   **Thesis_Alireza_Amani**: The Keynote presentation for the thesis defense.

## Project Timeline

*   **Start Date:** August 2019
*   **End Date:** July 2024


## Key Resources

*   **External Data Repositories:**
    *   [Historical Climate Data - Environment and Climate Change Canada](https://climate.weather.gc.ca/climate_data/hourly_data_e.html?hlyRange=2008-10-06%7C2021-05-29&dlyRange=2008-10-06%7C2021-05-29&mlyRange=%7C&StationID=47587&Prov=QC&urlExtension=_e.html&searchType=stnProx&optLimit=specDate&StartYear=1840&EndYear=2016&selRowPerPage=25&Line=0&txtRadius=25&optProxType=navLink&txtLatDecDeg=45.883333333333&txtLongDecDeg=-72.483333333333&timeframe=1&time=LST&time=LST&Year=2019&Month=9&Day=1#): For meteorological data.
    *   [ERA5](https://cds.climate.copernicus.eu/cdsapp#!/dataset/reanalysis-era5-land?tab=overview): For reanalysis data.
    *   [Zenodo](https://zenodo.org/records/10582140): Integrated Lysimeter Study (Deep Percolation) Data from Saint-Nicéphore, Quebec
*   **Software and Tools:**
    *   [The SVS Land Surface Model](https://research-groups.usask.ca/hydrology/modelling/mesh.php): For simulating deep percolation.
    *   [svspyed](https://github.com/Alireza-Amani/svspyed): A Python package for working with SVS model input/output files.
    *   [CRPSnb](https://github.com/Alireza-Amani/CRPSnb): Neighborhood-Based Continuous Ranked Probability Score (CRPS)

## Acknowledgements

*   **Supervisors:** Prof. Marie-Amélie Boucher, Prof. Alexandre R. Cabral
*   **Collaborators:** Vincent Vionnet, Étienne Gaborit
*   **Jury Members:** Prof. Vanessa Di Battista, Prof. Audrey Maheu, Dr. Marco Carrera
*   **Funding:** Natural Sciences and Engineering Research Council of Canada (NSERC)

## Contact

*   **Alireza Amani:** alireza.amani101@gmail.com
