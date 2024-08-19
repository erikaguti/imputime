from .utils import * 
import pandas as pd
import numpy as np


def fill_gaps(dataset, rate_type, value_column, time_units):
    """
    Fills gaps in a dataset by interpolating missing values based on a specified rate type.
    
    Parameters:
    - dataset (pd.DataFrame): The dataset containing time-series data.
    - rate_type (str): The type of rate to apply for interpolation (e.g., 'linear', 'exponential').
    - value_column (str): The name of the column that contains the values to interpolate.
    - time_units (str): The time units for interpolation (e.g., 'days', 'months', 'years').
    
    Returns:
    - pd.DataFrame: The dataset with interpolated values and original data.
    """
    last_row = dataset[dataset['date'] == dataset['date'].max()]  # Save the last row to append later
    add_bounds(dataset, value_column)
    add_daterange(dataset, time_units)
    add_timesteps(dataset)
    add_rate(dataset, rate_type, value_column)
    add_interpolated_values(dataset, rate_type, value_column)
    filled_in_data = interpolated_dataset(dataset, rate_type, value_column)
    filled_in_data = pd.concat([filled_in_data, last_row])
    return filled_in_data

def yearly_to_monthly(dataset, rate_type, value_column):
    """
    Converts yearly data to monthly data by interpolating missing values.
    
    Parameters:
    - dataset (pd.DataFrame): The dataset containing yearly data.
    - value_column (str): The name of the column that contains the values to interpolate.
    - rate_type (str): The type of rate to apply for interpolation (e.g., 'linear', 'exponential').
    
    Returns:
    - pd.DataFrame: The dataset converted to monthly data.
    """
    gap_check(dataset, 'months')
    data = dataset.copy()
    last_row = data[data['date'] == data['date'].max()]  # Save the last row to append later
    add_bounds(data, value_column)
    add_daterange(data, 'months')
    add_timesteps(data)
    add_rate(data, rate_type, value_column)
    add_interpolated_values(data, rate_type, value_column)
    filled_in_data = interpolated_dataset(data, rate_type, value_column)
    filled_in_data = pd.concat([filled_in_data, last_row])
    return filled_in_data

def monthly_to_daily(dataset, rate_type, value_column):
    """
    Converts monthly data to daily data by interpolating missing values.
    
    Parameters:
    - dataset (pd.DataFrame): The dataset containing monthly data.
    - value_column (str): The name of the column that contains the values to interpolate.
    - rate_type (str): The type of rate to apply for interpolation (e.g., 'linear', 'exponential').
    
    Returns:
    - pd.DataFrame: The dataset converted to daily data.
    """
    gap_check(dataset, 'months')
    data = dataset.copy()
    last_row = data[data['date'] == data['date'].max()]  # Save the last row to append later
    add_bounds(data, value_column)
    add_daterange(data, 'days')
    add_timesteps(data)
    add_rate(data, rate_type, value_column)
    add_interpolated_values(data, rate_type, value_column)
    filled_in_data = interpolated_dataset(data, rate_type, value_column)
    filled_in_data = pd.concat([filled_in_data, last_row])
    return filled_in_data

def interpolated_dataset(dataset, rate_type, value_column):
    """
    Creates a dataset with interpolated values based on the rate type.
    
    Parameters:
    - dataset (pd.DataFrame): The dataset containing the time-series data with interpolated values.
    - value_column (str): The name of the column that contains the values to interpolate.
    - rate_type (str): The type of rate applied for interpolation (e.g., 'linear', 'exponential').
    
    Returns:
    - pd.DataFrame: A new DataFrame containing the interpolated dates and values.
    """
    exploded_df_dates = dataset['date_range'].explode('date_range')  # Expand the date range
    exploded_interpolated_values = dataset[f'interpolated_{rate_type}_{value_column}'].explode(f'interpolated_{rate_type}_{value_column}')  # Expand interpolated values
    result_df = pd.DataFrame({'date': exploded_df_dates.values, f'{value_column}': exploded_interpolated_values.values})
    
    return result_df

def extrapolate(dataset, rate_type, value_column, time_units, start_date, future_timesteps, past_timesteps):
    """
    Extrapolates data into the future based on past rates and values.
    
    Parameters:
    - dataset (pd.DataFrame): The dataset containing historical time-series data.
    - start_date (str): The date from which to start extrapolating.
    - future_timesteps (int): The number of future timesteps to extrapolate.
    - past_timesteps (int): The number of past timesteps to calculate the rate.
    - rate_type (str): The type of rate to apply for extrapolation (e.g., 'linear', 'exponential').
    - value_column (str): The name of the column that contains the values to extrapolate.
    - time_units (str): The time units for extrapolation (e.g., 'days', 'months', 'years').
    
    Returns:
    - pd.DataFrame: The dataset containing extrapolated values into the future.
    """
    extrapolate_data = dataset.copy()
    
    extrapolate_start_date = pd.to_datetime(start_date)
    extrapolate_start_value = extrapolate_data[extrapolate_data['date'] == extrapolate_start_date][value_column].values[0]
    rate_start_date = date_delta(time_units, extrapolate_start_date, past_timesteps)

    extrapolate_data = filter_data(extrapolate_data, rate_start_date, extrapolate_start_date, inclusive=True)
    gap_check(extrapolate_data, time_units)
    
    extrapolate_data = add_bounds(extrapolate_data, value_column)
    extrapolate_data['timesteps'] = 1
    extrapolate_data = add_rate(extrapolate_data, rate_type, value_column)
    
    average_rate = np.mean(extrapolate_data[f'{rate_type}_rate_{value_column}'])
    
    extrapolated_data = extrapolated_dataset(rate_type, value_column, time_units, average_rate, extrapolate_start_date, extrapolate_start_value, future_timesteps)

    return extrapolated_data

def extrapolated_dataset(rate_type, value_column, time_units, rate, start_date, start_value, future_timesteps):
    """
    Generates a dataset with extrapolated values into the future based on a specified rate.
    
    Parameters:
    - rate (float): The average rate to use for extrapolation.
    - start_date (str): The date from which to start extrapolating.
    - start_value (float): The value at the start date.
    - rate_type (str): The type of rate to apply for extrapolation (e.g., 'linear', 'exponential').
    - future_timesteps (int): The number of future timesteps to extrapolate.
    - time_units (str): The time units for extrapolation (e.g., 'days', 'months', 'years').
    - value_column (str): The name of the column that contains the values to extrapolate.
    
    Returns:
    - pd.DataFrame: A new DataFrame containing extrapolated dates and values.
    """
    time_units_dict = {'days': 'D', 'months': 'M', 'years': 'Y'}
    dates = pd.date_range(start_date, periods=future_timesteps + 1, freq=time_units_dict[time_units], inclusive='both')
    
    if rate_type == 'linear':
        values = [start_value + (rate * n) for n in range(future_timesteps + 1)]
    elif rate_type == 'exponential':
        values = [start_value * (rate ** n) for n in range(future_timesteps + 1)]
    
    return pd.DataFrame({'date': dates, f'{value_column}': values})
