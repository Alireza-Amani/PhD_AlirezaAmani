# Code for Inverse Modeling and Ensemble Simulations of Deep Percolation in Cold Climates (Manuscript 2)

This folder contains the code necessary to reproduce the inverse modeling and ensemble simulation experiments described in the second manuscript of Alireza Amani's PhD research.

## Workflow Overview

1. **Parameter Sensitivity Analysis and Range Refinement:**
   - `Inverse_modelling_run.ipynb`: Conducts an initial ensemble simulation using a wide range of parameter values.
   - `Inverse_modelling_analysis.ipynb`: Calculates R2 and RMSE values for each scenario.
   - `inverse_modelling_ranges.ipynb`: Find the scenario with the best performance.

2. **Input Data Perturbation:**
   - `create_ens.ipynb`: Generates an ensemble of soil hydraulic parameter sets using Latin Hypercube Sampling within the refined parameter ranges.
   - `generate_meteo_ensemble.ipynb`: Creates an ensemble of meteorological forcing datasets by perturbing observed data to account for meteorological uncertainty.

3. **Ensemble Simulation and Evaluation:**
   - `run_ensemble.ipynb`: Executes the main ensemble simulation, combining the perturbed parameter sets with the perturbed meteorological forcing data.
   - `evaluation.ipynb`: Calculates the performance metrics. 

## Dependencies

- **Python Libraries:** pandas, numpy, scipy, scikit-learn, matplotlib, seaborn, svspyed
- **SVS Model:** Ensure you have the SVS model executable in the specified location.
- **Helper Functions:** The `helpers.py` file (included in this folder) contains custom functions for data processing, model setup, and analysis.

## Usage

1. **Prepare Input Data:**
   - Place your observed meteorological data and soil properties in the appropriate `Data` subfolder.
   - Ensure the paths in the scripts are correctly set to your data locations.

2. **Run Notebooks:**
   - Follow the workflow outlined above, executing the notebooks in the specified order.
   - Each notebook contains instructions and comments to guide you through the process.

## Output

The code will generate the following outputs:

- **Parameter Scenarios:** CSV files (`./Results/dfscenarios_*.csv`) containing the parameter sets used in each simulation.
- **Simulation Results:** Feather files (in the `./runs/` directory) storing the hourly output of the SVS model for each simulation.
- **Analysis Results:** CSV files (in the `./Results/` directory) containing model evaluation metrics and identified optimal parameter sets.

## Note

- Refer to the comments within each notebook for more detailed explanations and instructions.
