from multiprocessing import Pool
import concurrent.futures
from copy import deepcopy
import random
import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error
import datetime
from pathlib import Path
import gzip
import dask.dataframe as dd
from dask import delayed
from pyarrow.feather import write_feather
from statsmodels.tsa.arima.model import ARIMA
from metpy.units import units
from metpy.calc import specific_humidity_from_dewpoint


def bc_theta(psi_m2ho: float, theta_s: float, psi_ae: float, b: float) -> float:
    '''
    Calculate the volumetric water content from the matric potential.

    Parameters
    ----------
    psi_m2ho : float
        Matric potential in mH2O.
    theta_s : float
        Saturated volumetric water content in m3.m-3.
    psi_ae : float
        Air entry potential in mH2O.
    b : float
        Hornberger parameter.

    Returns
    -------
    float
        Volumetric water content in m3.m-3.
    '''

    theta = theta_s * ((psi_m2ho / psi_ae) ** (-1/b))

    return theta


def compare_dataframe_columns(df1: pd.DataFrame, df2: pd.DataFrame):
    """
    Compares the columns of two DataFrames and prints information about matching
      and non-matching columns.

    Parameters:
    ----------
    df1 : DataFrame
        The first DataFrame to compare.

    df2 : DataFrame
        The second DataFrame to compare.

    Returns:
    -------
    None
    """

    # Get sets of column names for efficient comparison
    col_set1 = set(df1.columns)
    col_set2 = set(df2.columns)

    # Find intersection (common columns)
    common_columns = col_set1.intersection(col_set2)

    # Find differences (non-matching columns)
    df1_unique_cols = col_set1.difference(col_set2)
    df2_unique_cols = col_set2.difference(col_set1)

    # Print the results in a readable format
    print("\nColumns present in both DataFrames:")
    if common_columns:
        for col in common_columns:
            print(f"- {col}")
    else:
        print("- None")

    print("\nColumns present only in df1:")
    if df1_unique_cols:
        for col in df1_unique_cols:
            print(f"- {col}")
    else:
        print("- None")

    print("\nColumns present only in df2:")
    if df2_unique_cols:
        for col in df2_unique_cols:
            print(f"- {col}")
    else:
        print("- None")


def calc_bias_std(
    compare_variables: list, df_source_1: pd.DataFrame, df_source_2: pd.DataFrame,
) -> dict:
    '''
    Calculate the bias and standard deviation of the difference between two
    dataframes.

    bias = (df_source_1 - df_source_2).mean() for the variables
    std = (df_source_1 - df_source_2).std() for the variables

    Parameters
    ----------
    compare_variables : list
        List of variables to compare.

    df_source_1 : pandas.DataFrame
        Dataframe containing the variables to compare.

    df_source_2 : pandas.DataFrame
        Dataframe containing the variables to compare.

    Returns
    -------
    dict
        Dictionary containing the bias and standard deviation of the difference
        between the two dataframes for each variable.

    Conditions
    ----------
    The two dataframes must have a datetime index with a UTC timezone and
    the same frequency.
    '''

    # assertions --------------------------------------------------------------
    assert df_source_1.index.tz in (
        'UTC', datetime.timezone.utc), 'df_source_1 must have a UTC timezone'
    assert df_source_2.index.tz in (
        'UTC', datetime.timezone.utc), 'df_source_2 must have a UTC timezone'
    assert (df_source_1.index.freq == df_source_2.index.freq), (
        'df_source_1 and df_source_2 must have the same frequency'
    )
    assert all([var in df_source_1.columns for var in compare_variables]), (
        'Some variables to compare are not in df_source_1'
    )
    assert all([var in df_source_2.columns for var in compare_variables]), (
        'Some variables to compare are not in df_source_2'
    )
    # -------------------------------------------------------------------------

    # collect bias and std in a dictionary for each variable
    bias_std = {key_var: {'bias': None, 'std': None}
                for key_var in compare_variables}

    # collect the variable values and the associated bias
    var_info = {}

    for kvar in compare_variables:

        # extract the variables from the respective dataframes
        var_1 = df_source_1[kvar]
        var_2 = df_source_2[kvar]

        # merge the two variables into a dataframe - mutual index
        merged_df = pd.merge(var_1, var_2, how="inner",
                             left_index=True, right_index=True)
        # remove NaNs
        merged_df = merged_df.dropna()

        # calculate the bias and std
        bias_std[kvar]['bias'] = (
            merged_df[kvar + '_x'] - merged_df[kvar + '_y']).mean()
        bias_std[kvar]['std'] = (
            merged_df[kvar + '_x'] - merged_df[kvar + '_y']).std()

        # collect the variable values and the associated bias
        var_info[kvar] = {
            'var_1': merged_df[kvar + '_x'],
            'var_2': merged_df[kvar + '_y'],
            'bias': merged_df[kvar + '_x'] - merged_df[kvar + '_y'],
        }

    return bias_std, var_info


def get_ar1_param(bias):
    """
    Fit an AR(1) model to the bias and return the value of the AR(1) parameter.

    Parameters
    ----------
    bias : pandas.Series
        A pandas Series containing the bias.

    Returns
    -------
    float
        The value of the AR(1) parameter.

    Assumptions
    -----------
    The bias is a pandas Series with a datetime index and a UTC timezone and
    a frequency of 1 hour.

    If the time period is not fully covered by the
    bias, the bias is reindexed with a full range of time.

    Constraints
    -----------
    The intercept of the AR(1) model is fixed to 0.
    """

    # assertions --------------------------------------------------------------
    assert isinstance(bias, pd.Series), 'bias must be a pandas Series'
    assert bias.index.tz in (
        'UTC', datetime.timezone.utc), 'bias must have a UTC timezone'
    # -------------------------------------------------------------------------

    # make a copy of the bias
    bias = bias.copy()

    # turn to numeric
    bias = pd.to_numeric(bias, errors='coerce')

    # get the start and end time of the bias
    t1 = bias.index[0]
    t2 = bias.index[-1]

    # create a full range of time
    full_range = pd.date_range(t1, t2, freq='h')

    # reindex the bias with the full range of time
    # remove duplicates first
    bias = bias[~bias.index.duplicated(keep='first')]
    bias = bias.reindex(full_range, fill_value=np.nan)

    # fit AR(1) model- fix the intercept to 0
    autor1 = ARIMA(bias, order=(1, 0, 0), freq='h')

    with autor1.fix_params({'const': 0}):
        autor1_fit = autor1.fit()

    return autor1_fit.params['ar.L1']


def perturb_var(
    data, var_label, phi, var_std, additive,
    plimit_u=0.2, plimit_l=-0.2,
    seed=None, var_max=None, var_min=None,
):
    """
    Create a perturbed variable from the original variable using the AR1 model


    Parameters
    ----------
    data : pandas.DataFrame
        The dataframe containing the original variable.

    var_label : str
        The column label of the variable.

    phi : float
        The auto-regressive (AR1) model parameter.

    var_std : float
        The standard deviation of the differences between the original variable
        and the variable from the other source.

    additive : bool
        True if the perturbation is additive, False if it is multiplicative.

    plimit_u : float, optional
        The upper limit for the multiplicative perturbation. The default is 0.25.

    plimit_l : float, optional
        The lower limit for the multiplicative perturbation. The default is -0.25.

    seed : int, optional
        The seed for the random number generator. The default is None.

    var_max : float, optional
        The maximum value of the variable. The default is None.

    var_min : float, optional
        The minimum value of the variable. The default is None.


    Returns
    -------
    addvar_pert : pandas.Series
        The perturbed variable.

    """

    # calculate sigma-2
    sigma2 = (1 - phi**2) * var_std

    # create a random number generator
    drng = np.random.default_rng(seed)

    white_noise = drng.normal(0, sigma2**0.5, len(data))

    # create the perturbation values for the variable
    perturb = np.zeros(len(data))

    for i in range(1, len(data)):
        perturb[i] = (phi * perturb[i-1]) + white_noise[i]

    # create the perturbed variable
    if additive:
        addvar_pert = data[var_label] + perturb
    else:
        # limit the perturbation
        perturb = np.clip(perturb, plimit_l, plimit_u)
        addvar_pert = data[var_label] * (1 + perturb)

    if var_max is not None:
        addvar_pert = np.clip(addvar_pert, None, var_max)

    if var_min is not None:
        addvar_pert = np.clip(addvar_pert, var_min, None)

    return addvar_pert


def calc_specific_humidity(pressure, dewpoint):
    """
    Calculate the specific humidity from the pressure and dewpoint temperature.

    Parameters
    ----------
    pressure : pandas.Series
        The pressure.

    dewpoint : pandas.Series
        The dewpoint temperature.

    Returns
    -------
    pandas.Series
        The specific humidity.

    Assumptions
    -----------
    The pressure and dewpoint temperature are pandas Series in units of kPa and
    degC, respectively.

    """

    # make them unit aware
    pressure = pressure.to_numpy() * units.Pa
    dewpoint = dewpoint.to_numpy() * units.degC

    # calculate the specific humidity
    spech = specific_humidity_from_dewpoint(pressure, dewpoint)

    return spech.magnitude


def catch_efficiency_solid(wind_speed_mps):
    '''
    Calculate the catch efficiency of the solid precipitation gauge.

    Parameters
    ----------
    wind_speed_mps : ndarray
        Wind speed in m/s.

    Returns
    -------
    ce : float
        Catch efficiency of the precipitation gauge.

    Reference
    ---------
    [1] Kochendorfer, John, Roy Rasmussen, Mareile Wolff, Bruce Baker,
         Mark E. Hall, Tilden Meyers, Scott Landolt et al.
        "The quantification and correction of wind-induced precipitation measurement errors."
        Hydrology and Earth System Sciences 21, no. 4 (2017): 1973-1989.

    '''
    # parameters
    a1, b1, c1, umax = 0.886, 0.143, 0.25, 8

    # calculate catch efficiency
    ce = a1 * (
        np.exp(-b1 * np.minimum(wind_speed_mps, umax)) + c1
    )

    return ce


def create_perturbed_data(
        original_data, compare_vars, not_perturbed, prec_mult_fac, bias_std,
        longwave_add_pert,
        seed=None,
        precipitation_label="Precipitation (mm) corrected",
        pressure_label="Atmospheric pressure (kPa)",
        dew_point_label="Dew point temperature (°C)",
        longwave_label="Longwave radiation (W.m-2)",
):
    """
    Creates a perturbed dataframe based on the original data.

    Parameters
    ----------
    original_data : pandas.DataFrame
        The original dataframe.

    compare_vars : dict
        A dictionary of the variables to compare between the original dataframe
        and the perturbed dataframe. The keys are the variable names and the
        values are dictionaries containing the perturbation parameters.

    not_perturbed : list
        A list of the variables that are not perturbed.

    PREC_FACT : float
        The perturbation factor for precipitation. The perturbation is
        calculated as a uniform distribution between 1-PREC_FACT and
        1+PREC_FACT.

    bias_std : dict
        A dictionary containing the bias and standard deviation of the
        difference between the original dataframe and the perturbed dataframe
        for each variable.
        It also contains the AR1 parameter for each variable.

    seed : int, optional
        The seed to use for the random number generator. If None, the seed is
        not set.

    precipitation_label : str, optional
        The label of the precipitation variable in the original dataframe.

    pressure_label : str, optional
        The label of the atmospheric pressure variable in the original
        dataframe.

    dew_point_label : str, optional
        The label of the dew point temperature variable in the original
        dataframe.

    longwave_label : str, optional
        The label of the longwave radiation variable in the original dataframe.

    Returns
    -------
    df_pert : pandas.DataFrame
        The perturbed dataframe.
    """

    # make a copy of the original dataframe with the `not_perturbed` variables
    df_pert = original_data.loc[:, not_perturbed].copy()

    # perturb the precipitation data with a uniform distribution
    dfrng = np.random.default_rng(seed=seed)
    pert_factors = dfrng.uniform(
        1-prec_mult_fac, 1+prec_mult_fac, size=len(df_pert))
    df_pert[precipitation_label] = (
        original_data[precipitation_label] * pert_factors
    )

    # perturb the longwave radiation with an additive perturbation, uniform
    pert_factors = dfrng.uniform(-longwave_add_pert,
                                 longwave_add_pert, size=len(df_pert))
    df_pert[longwave_label] = (
        original_data[longwave_label] + pert_factors
    )

    # perturb the other variables
    for var_name, var_dict in compare_vars.items():
        df_pert[var_name] = perturb_var(
            data=original_data, var_label=var_name, phi=bias_std[var_name]['phi'],
            var_std=bias_std[var_name]['std'], seed=seed,
            # var_bias=bias_std[var_name]["bias"],
            **var_dict
        )

    # calculate specific humidity
    df_pert["Specific Humidity (kg/kg)"] = calc_specific_humidity(
        df_pert.loc[:, pressure_label],
        df_pert.loc[:, dew_point_label]
    )

    return df_pert


def save_csv_as_met(save_path: str, col_names, dfmet, catch_corr=True, compress=False):
    '''
    Create `basin_forcing.met` file for SVS by having the hourly meteo data
    in a CSV file.

    Parameters
    ----------
    save_path : str
        The full path to save the `basin_forcing.met` file, including the
        file name.

    col_names : dict
        A dictionary containing the names of the columns in the CSV file.

    dfmet : pandas.DataFrame
        A dataframe containing the hourly meteo data.

    catch_corr : bool, optional
        If True, the catch efficiency of the solid precipitation gauge will be

    Returns
    -------
    None

    '''

    # Ensure save_path is a Path object
    save_path = Path(save_path)

    # copy the dataframe
    dfmet = dfmet.copy()

    # check whether the required columns are present in the dictionary
    check_meteo_colnames_dict(col_names)

    # check units of the variables
    check_metvar_units(dfmet, col_names)

    # if `utc_dtime` is not among the columns, check if it is in the index
    if col_names["utc_dtime"] not in dfmet.columns:
        if dfmet.index.name == col_names["utc_dtime"]:
            # if it is in the index, reset the index and make it a column
            dfmet.reset_index(inplace=True)

    # add the required time columns in the dataframes
    dfmet, not_used, not_used_2 = create_dtime_vars(
        dfmet, col_names["utc_dtime"]
    )

    # process the precipitation for the dataframe
    dfmet = process_pcpn(
        dfmet, col_names["precipitation"],
        catch_corr=catch_corr, wind_label_mps=col_names["wind_speed"],
        func_psnow=calc_psnow,
        **dict(air_temp=dfmet.loc[:, col_names["air_temperature"]],
               rel_humidity=dfmet.loc[:, col_names["relative_humidity"]]
               )
    )

    # order the dataframe columns
    dfmet = order_dfmet(dfmet, col_names)

    # let the instance own the text file
    met_file = dfmet.to_string(
        header=False, col_space=4, index=False)

    # # save the file
    # with open(save_path, "w", encoding="utf-8") as mfile:
    #     mfile.write(met_file)

    # Compression (optional)
    if compress:
        save_path = save_path.with_suffix('.met.gz')
        with gzip.open(save_path, 'wt', encoding='utf-8') as mfile:
            mfile.write(met_file)
    else:
        with open(save_path, 'w', encoding='utf-8') as mfile:
            mfile.write(met_file)


def check_metvar_units(dfmet, col_names: dict) -> None:
    '''
    Check the hourly meteorological data to ensure they have the correct
    units before creating the .met file

    Parameters
    ----------
    dfmet : pandas Dataframe
        The dataframe that contains the meteo variables for SVS.

    col_names : dict
        A dict that contains the names of the relevant columns in the dataframe
        that contains the hourly meteorological variables required to create
        the .met file for SVS. Please define and provide values for the
        following keys:
        ['utc_dtime', 'air_temperature', 'precipitation', 'wind_speed',
        'atmospheric_pressure', 'shortwave_radiation', 'longwave_radiation',
        'specific_humidity', 'relative_humidity']
        Relative humidity will be used in the precipitation phase discrimination.

    '''

    dfmet = dfmet.loc[:, :]

    # extract the variables of interest
    air_temp = dfmet.loc[:, col_names["air_temperature"]].to_numpy()
    shortwave_rad = dfmet.loc[:, col_names["shortwave_radiation"]].to_numpy()
    longwave_rad = dfmet.loc[:, col_names["longwave_radiation"]].to_numpy()
    wind_speed = dfmet.loc[:, col_names["wind_speed"]].to_numpy()
    atms_press = dfmet.loc[:, col_names["atmospheric_pressure"]].to_numpy()
    precipitation = dfmet.loc[:, col_names["precipitation"]].to_numpy()
    shumidity = dfmet.loc[:, col_names["specific_humidity"]].to_numpy()
    relhumidity = dfmet.loc[:, col_names["relative_humidity"]].to_numpy()
#     date_utc = dfmet.loc[:, col_names["utc_dtime"]].to_numpy()

    # check the values of the meteo variables for their unit and potential invalid
    # values.
    assert (np.all(air_temp > -50) and np.all(air_temp < 60)), (
        "Please check the values of the air temperature column."
    )
    assert (np.all(shortwave_rad >= 0) and np.all(shortwave_rad < 2000)), (
        "Please check the values of the shortwave radiation column."
    )
    assert (np.all(longwave_rad >= 0) and np.all(longwave_rad < 2000)), (
        "Please check the values of the longwave radiation column."
    )
    assert (np.all(wind_speed >= 0) and np.all(wind_speed < 200)), (
        "Please check the values of the wind speed column."
    )
    assert (np.all(atms_press >= 70000) and np.all(atms_press < 110000)), (
        "Please check the values of the atmospheric pressure column.\n"
        "Make sure that the values are in Pascal."
    )
    assert (np.all(precipitation >= 0) and np.all(precipitation < 500)), (
        "Please check the values of the precipitation column."
    )
    assert (np.all(shumidity >= 0.0000001) and np.all(shumidity < 0.1)), (
        "Please check the values of the specific humidity column."
    )
    assert (np.all(relhumidity >= 0) and np.all(relhumidity <= 100)), (
        "Please check the values of the relative humidity column."
    )


def create_dtime_vars(dfmet, dtime_col_name: str):
    '''
    Create the four date-time variables used in the .met file for SVS.

    Parameters
    ----------
    dfmet : pandas Dataframe
        The dataframe that contains the meteo variables for SVS plus a column
        named `dtime_col_name` that is convertible to pd.Timestamp.

    dtime_col_name : str
        The name of the date-time (utc) column in `dfmet`.

    Returns
    -------
    dfmet : pandas Dataframe

    first_tstep : str
        The first time-step in `dfmet` with the format of YYYYMMDDHH.
        This will be used in the creation of `MESH_input_run_options.ini`.

    last_tstep : str
        The last time-step in `dfmet` with the format of YYYYMMDDHH.

    '''

    dfmet = dfmet.copy()

    # create columns for HOUR, MINS, JDAY, YEAR
    # first convert the datetime column into a proper dtype
    dfmet[dtime_col_name] = pd.to_datetime(
        dfmet[dtime_col_name], utc=True
    )

    # now create the required columns
    dfmet["HOUR"] = dfmet[dtime_col_name].dt.hour
    dfmet["MINS"] = dfmet[dtime_col_name].dt.minute
    dfmet["JDAY"] = dfmet[dtime_col_name].dt.dayofyear
    dfmet["YEAR"] = dfmet[dtime_col_name].dt.year

    # extract the first(/last) time step in the appropriate format to be used in the
    # creation process of `MESH_input_run_options.ini`
    first_tstep = dfmet.loc[dfmet.index[0], dtime_col_name]
    last_tstep = dfmet.loc[dfmet.index[-1], dtime_col_name]

    # convert it into string: YYYYMMDDHH
    first_tstep = (
        F"{first_tstep.year}{first_tstep.month:02d}{first_tstep.day:02d}"
        F"{first_tstep.hour:02d}"
    )
    last_tstep = (
        F"{last_tstep.year}{last_tstep.month:02d}{last_tstep.day:02d}"
        F"{last_tstep.hour:02d}"
    )

    return dfmet, first_tstep, last_tstep


def process_pcpn(dfmet, pcpn_col_name, catch_corr, wind_label_mps, func_psnow, **func_psnow_kwargs):
    '''
    Converts the precipitation values from mm/hour to mm/s and applies phase
    discrimination.
    This will create a new column for precipitation rate, and two columns
    for rainfall and snowfall.

    Parameters
    ----------
    dfmet : pandas Dataframe
        The dataframe that contains the meteo variables for SVS plus a column
        named `dtime_col_name` that is convertible to pd.Timestamp.

    pcpn_col_name : str
        The name of the precipitation column in `dfmet`.

    func_psnow : function
        The function that can calculate the probability of snowfall at each
        time step.

    **func_psnow_kwargs : dict
        Keyword argument to be passed to `func_psnow`.

    Returns
    -------
    dfmet : pandas Dataframe
    '''

    # convert the precipitation values from mm/hour to mm/second
    # (Total precipitation rate at the surface)
    dfmet["Precipitation rate (mm/s)"] = np.divide(dfmet[pcpn_col_name], 3600)
    pcpn_rate = dfmet.loc[:, "Precipitation rate (mm/s)"].to_numpy()

    # calc the probability of snowfall
    psnow = func_psnow(**func_psnow_kwargs)

    # apply phase discrimination
    # if psnow < 0.5, then we will have liquid precipitation
    dfmet["Rainfall rate (mm/s)"] = np.multiply(psnow < 0.5, pcpn_rate)
    dfmet["Snowfall rate (mm/s)"] = np.multiply(psnow >= 0.5, pcpn_rate)

    # calculate the catch efficiency of the solid precipitation gauge
    if catch_corr:
        ce = catch_efficiency_solid(dfmet.loc[:, wind_label_mps].to_numpy())
        dfmet["Snowfall rate (mm/s)"] = dfmet["Snowfall rate (mm/s)"] / ce

    return dfmet


def calc_psnow(
    air_temp, rel_humidity, coeff_1=-10.04, coeff_2=1.41, coeff_3=0.09
):
    '''
    Calculate the probablity of snowfall using air temperature and relative
    humidity data.

    ref: https://www.nature.com/articles/s41467-018-03629-7
    The default coefficients are included in the supplementary file of the ref.

    Parameter
    ---------
    air_temp : ndarray
        The air temperature in deg Celcius.

    rel_humidity : ndarray
        The relative humidity in %.

    coeff_1, coeff_2, coeff_3 : float
        The fitting coefficients.

    Returns
    -------
    psnow : ndarray
        The probability of the precipitation phase being solid.
    '''

    # calculate psnow using the bivariate logistic equation
    psnow = np.exp(coeff_1 + (coeff_2 * air_temp) + (coeff_3 * rel_humidity))
    psnow = np.power(1 + psnow, -1)

    return psnow


def phase_disc(pcpn_rate, psnow):
    '''
    Apply phase discrimination on the precipitation rate data.

    Parameters
    ----------
    pcpn_rate : ndarray
        The precipitation rate data in mm/s.

    psnow : ndarray
        The probability of snowfall in each time step.

    Returns
    -------
    rainfall : ndarray
        The rainfall rate in mm/s.

    snowfall : ndarray
        The snowfall rate in mm/s.
    '''

    # if psnow < 0.5, then we will have liquid precipitation
    rainfall = np.multiply(psnow < 0.5, pcpn_rate)
    snowfall = np.multiply(psnow >= 0.5, pcpn_rate)

    return rainfall, snowfall


def order_dfmet(dfmet, col_names: dict):
    '''
    Order the `dfmet` dataframe per the ordering expected by SVS.
    Additionally, will round the values for some of the variables.

    Parameters
    ----------
    dfmet : pandas Dataframe
        The dataframe that contains the meteo variables for SVS plus a column
        named `dtime_col_name` that is convertible to pd.Timestamp.

    col_names : dict
        A dict that contains the names of the relevant columns in the dataframe
        that contains the hourly meteorological variables required to create
        the .met file for SVS. Please define and provide values for the
        following keys:
        ['utc_dtime', 'air_temperature', 'precipitation', 'wind_speed',
        'atmospheric_pressure', 'shortwave_radiation', 'longwave_radiation',
        'specific_humidity', 'relative_humidity']
        Relative humidity will be used in the precipitation phase discrimination.

    Returns
    -------
    dfmet : pandas Dataframe

    '''

    # order the dataframe as expected by SVS
    ordered_cols = [
        "HOUR", "MINS", "JDAY", "YEAR",
        col_names["shortwave_radiation"], col_names["longwave_radiation"],
        "Precipitation rate (mm/s)", col_names["air_temperature"],
        col_names["specific_humidity"], col_names["wind_speed"],
        col_names["atmospheric_pressure"],
        "Rainfall rate (mm/s)", "Snowfall rate (mm/s)"
    ]
    dfmet = dfmet.loc[:, ordered_cols]

    # adjust the digits and precision of the variables, to help writing a clean
    # .met file
    # radiation vars, temperature, wind speed and pressure
    #  two decimals vars
    twod_vars = [
        col_names["shortwave_radiation"], col_names["longwave_radiation"],
        col_names["air_temperature"], col_names["wind_speed"],
        col_names["atmospheric_pressure"]
    ]
    dfmet.loc[:, twod_vars] = np.round(dfmet.loc[:, twod_vars], 2)

    return dfmet


def check_meteo_colnames_dict(meteo_col_names: dict) -> None:
    '''
    Check if the `meteo_col_names` dict has the required keys.

    Parameter
    ---------
    meteo_col_names : dict
        A dict that contains the names of the relevant columns in the dataframe
        that contains the hourly meteorological variables required to create
        the .met file for SVS.

    '''

    set_dict_keys = set(meteo_col_names.keys())
    set_required_keys = set(['utc_dtime', 'air_temperature', 'precipitation',
                             'wind_speed', 'atmospheric_pressure', 'shortwave_radiation',
                             'longwave_radiation', 'specific_humidity', 'relative_humidity'
                             ])
    assert (set_required_keys.issubset(set_dict_keys)), (
        F"Make sure the `meteo_col_names` dict include the following keys: \n"
        F"{set_required_keys}\n"
        F"Missing key(s): {set_required_keys.difference(set_dict_keys)}\n"
    )


def perturb_and_save(
    imem, df_topert, compare_vars, bistd, save_dir, meteo_cols,
    prec_mult_fac=0.05, longwave_add_pert=25, seed=1915,
    save_as_parquet=False, save_as_feather=False,
    compress_met_file=False, catch_corr=True,
):
    '''
    Perturb the forcing data and save the perturbed data to a csv file.

    Parameters
    ----------
    imem : int
        The ensemble member number.

    df_topert : pandas.DataFrame
        The original forcing data.

    compare_vars : dict
        The variables to perturb and their perturbation type.

    bistd : dict
        The bias and standard deviation of the variables.

    save_dir : Path
        The paths to save the perturbed data.

    meteo_cols : dict
        The columns names for the meteo data.

    prec_mult_fac : float, optional
        The precipitation multiplicative factor. The default is 0.05.

    longwave_add_pert : float, optional
        The longwave radiation additive perturbation. The default is 25.

    seed : int, optional
        The seed for the random number generator. The default is 1915.

    Returns
    -------
    str
        A message indicating the status of the perturbation and saving.

    '''

    # Ensure save_dir is a Path object
    save_dir = Path(save_dir)

    df_imem = create_perturbed_data(
        original_data=df_topert,
        compare_vars=compare_vars,
        not_perturbed=['Longwave Radiation (W/m2)'],
        prec_mult_fac=prec_mult_fac,
        bias_std=bistd,
        longwave_add_pert=longwave_add_pert,  # W.m-2
        seed=seed + imem,  # Ensure different seed for each iteration
        precipitation_label=meteo_cols["precipitation"],
        pressure_label=meteo_cols["atmospheric_pressure"],
        dew_point_label=meteo_cols["dew_point"],
        longwave_label=meteo_cols["longwave_radiation"],
    )

    df_imem["dt_utc"] = df_imem.index.tz_convert("UTC")

    # save the perturbed data
    if save_as_parquet:
        df_imem.to_parquet(
            save_dir / f"perturbed_data_{imem}.parquet"
        )

    elif save_as_feather:
        write_feather(
            df_imem, save_dir / f"perturbed_data_{imem}.feather",
            compression="zstd",
        )

    else:
        df_imem.to_csv(
            save_dir / f"perturbed_data_{imem}.csv",
            index_label="time_utc"
        )

    save_csv_as_met(
        save_path=save_dir / f"basin_forcing_{imem}.met",
        col_names=meteo_cols,
        dfmet=df_imem, compress=compress_met_file, catch_corr=catch_corr,
    )

    return f"Data for member {imem} processed and saved."


def calc_r2_rmse_chunk(member_chunk, sim_data, obs_data, sim_col, obs_col, member_col, text_file):
    """Calculates R^2 and RMSE for a chunk of members."""
    obs_values = obs_data[obs_col].values

    for member in member_chunk:
        sim_values = sim_data[sim_data[member_col] ==
                              member].loc[obs_data.index, sim_col].values
        correlation = np.corrcoef(obs_values, sim_values)[0, 1]
        r2 = correlation ** 2
        rmse = np.sqrt(mean_squared_error(obs_values, sim_values))

        with open(text_file, "a", encoding="utf-8") as f:
            f.write(f"{member},{r2},{rmse}\n")

    return None


def calc_r2_rmse_parallel(sim_data, obs_data, sim_col, obs_col, text_file, member_col="member", num_processes=4):
    """Calculates R^2 and RMSE in parallel across member chunks."""
    members = sim_data[member_col].unique()
    chunk_size = len(members) // num_processes  # Base chunk size
    remainder = len(members) % num_processes

    member_chunks = []
    start_idx = 0
    for i in range(num_processes):
        # Adjust chunk size for remainder
        end_idx = start_idx + chunk_size + (1 if i < remainder else 0)
        member_chunks.append(members[start_idx:end_idx])
        start_idx = end_idx

    with Pool(num_processes) as pool:
        pool.starmap(
            calc_r2_rmse_chunk,
            [(member_chunk, sim_data, obs_data, sim_col, obs_col,
              member_col, text_file) for member_chunk in member_chunks]
        )

    return None


def calc_r2_rmse(sim_data, obs_data, sim_col, obs_col, member_col, text_file):
    """Calculates R^2 and RMSE for a chunk of members."""
    obs_values = obs_data[obs_col].values
    members = sim_data[member_col].unique()

    with open(text_file, "w", encoding="utf-8") as f:
        f.write("member,r2,rmse\n")

    for member in members:
        sim_values = sim_data[sim_data[member_col] ==
                              member].loc[obs_data.index, sim_col].values
        correlation = np.corrcoef(obs_values, sim_values)[0, 1]
        r2 = correlation ** 2
        rmse = np.sqrt(mean_squared_error(obs_values, sim_values))

        with open(text_file, "a", encoding="utf-8") as f:
            f.write(f"{member},{r2},{rmse}\n")

    return None


def swrc_model(psi_mh2o, theta_sat, psi_ae, bcoef):
    '''
    Get Theta from the SWRC model.

    Parameters
    ----------
    psi_mh2o : float
        Matric potential of the soil [m]

    theta_sat : float
        Saturation water content [m3 m-3]

    psi_ae : float
        Air entry matric potential [m]

    bcoef : float
        Slope of the water retention curve [-]

    Returns
    -------
    theta : float
        Volumetric water content [m3 m-3]

    '''

    theta = theta_sat * (psi_mh2o / psi_ae) ** (-1.0 / bcoef)

    return theta

# Function to map LHS samples to parameter range


def map_to_range(lhs_sample, param_range):
    '''
    Map LHS samples to parameter range.

    Parameters
    ----------
    lhs_sample : numpy.ndarray
        LHS samples

    param_range : scipy.stats._distn_infrastructure.rv_frozen
        Parameter range

    Returns
    -------
    param : numpy.ndarray
        Parameters

    '''
    return param_range.ppf(lhs_sample)


def load_process_outfeather(
    fpath, cutoff_dt=None,
    index_label='date_utc', ens_member_label='member',
    selcols=None,
):
    '''
    Load and process output feather file.

    Parameters
    ----------
    fpath : str or Path
        Path to feather file.

    cutoff_dt : str or pd.Timestamp, optional
        Limit data to after this date. If None, limit to after 2019-09-01.

    index_label : str, optional
        Label of the datetime column.

    ens_member_label : str, optional
        Label of the ensemble member column.

    selcols : list, optional
        List of columns to include in the output DataFrame.

    Returns
    -------
    df : pd.DataFrame
        Processed output data.

    '''

    # load feather file
    if selcols is None:
        df = pd.read_feather(fpath)
    else:

        # make sure index_label and ens_member_label are included
        if index_label not in selcols:
            selcols.append(index_label)

        if ens_member_label not in selcols:
            selcols.append(ens_member_label)

        # add acc variables
        if "ET" in selcols:
            selcols = selcols + ["ACC_ET"]
        if "DRAI" in selcols:
            selcols = selcols + ["ACC_DRAI"]
        if "OVFLW" in selcols:
            selcols = selcols + ["ACC_OVFLW"]

        df = pd.read_feather(fpath, columns=selcols)

    # decumulate ACC_ET, ACC_DRAI, ACC_OVFLW
    if "ACC_ET" in df.columns:
        df["ET"] = df["ACC_ET"].diff()
        df = df.drop(columns=["ACC_ET"])

    if "ACC_DRAI" in df.columns:
        df["DRAI"] = df["ACC_DRAI"].diff()
        df = df.drop(columns=["ACC_DRAI"])

    if "ACC_OVFLW" in df.columns:
        df["OVFLW"] = df["ACC_OVFLW"].diff()
        df = df.drop(columns=["ACC_OVFLW"])

    # set `date_utc` as index
    df.set_index(index_label, inplace=True)

    # limit to after xxx
    if cutoff_dt is None:
        cutoff_dt = pd.to_datetime('2019-09-01 04:00:00', utc=True)

    df = df.loc[cutoff_dt:]

    return df


def get_ensemble_output(
    output_paht_list, variables, cutoff_dt=None,
    ave_cols: dict = None, sub_value: float = None,
):
    '''
    Load and process output feather files from ensemble run, using dask.

    Parameters
    ----------
    output_dir : list
        List of paths to output feather files.

    variables : list
        List of variables to include in the output DataFrame.

    cutoff_dt : str or pd.Timestamp, optional
        Limit data to after this date. If None, limit to after 2019-09-01.

    ave_cols : dict, optional
        Dictionary with new column names as keys and lists of columns to
        average as values.

    sub_value : float, optional
        Value to subtract from the averaged columns.

    Returns
    -------
    dfens : pd.DataFrame
        Processed output data from ensemble run.

    '''

    # make sure variables include `member`
    if 'member' not in variables:
        variables = ['member'] + variables

    dasked_dfs = [
        delayed(load_process_outfeather)(
            outf, selcols=variables, cutoff_dt=cutoff_dt,
        )  # Change here
        for outf in output_paht_list
    ]

    # compute dasked_dfs
    dasked_dfs = dd.from_delayed(dasked_dfs)
    dfens = dasked_dfs.compute()

    # average columns
    if ave_cols is not None:
        for new_col, cols in ave_cols.items():

            if sub_value is None:
                dfens[new_col] = dfens[cols].mean(axis=1)
            else:
                dfens[new_col] = dfens[cols].mean(axis=1).subtract(sub_value)

            dfens = dfens.drop(columns=cols)

    return dfens

def uniform_sample_from_obs(obs_series, add_value, n, drng, non_negative=False):
    '''
    Sample from observation vector.

    Parameters
    ----------
    obs_series : pd.Series
        Observation time series.

    add_value : float
        +/- Value to add to the observation.

    n : int
        Number of samples.

    drng : np.random.Generator
        Random number generator.

    Returns
    -------
    pd.DataFrame
        Dataframe with samples from the observation vector.
    '''

    # create dataframe to store samples
    data = pd.DataFrame(
        columns=[f'obs_{i}' for i in range(n)],
        index=obs_series.index
    )

    # sample from observation vector (vectorized)
    data.loc[:, :] = (
        obs_series.values[:, None] +
        drng.uniform(-add_value, add_value, (obs_series.shape[0], n))
    )

    if non_negative:
        ## make sure no negative values
        data = data.clip(lower=0)

    data = data.astype(np.float64)

    return data
