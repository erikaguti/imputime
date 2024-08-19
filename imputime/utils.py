import pandas as pd

def filter_data(dataset, start_date, end_date, inclusive):
    """
    Filters the dataset based on the given date range and inclusivity.
    
    Parameters:
    - dataset (pd.DataFrame): The dataset to filter.
    - start_date (str or pd.Timestamp): The start date for the filter.
    - end_date (str or pd.Timestamp): The end date for the filter.
    - inclusive (bool): Whether to include the start and end dates in the filter.
    
    Returns:
    - pd.DataFrame: The filtered dataset.
    """
    # Convert start and end dates to datetime objects
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
        
    # Filter dataset based on inclusivity
    if inclusive:
        dataset = dataset[(dataset['date'] >= start_date) & (dataset['date'] <= end_date)]
    else:
        dataset = dataset[(dataset['date'] > start_date) & (dataset['date'] < end_date)]
    
    return dataset

def gap_check(dataset, time_units):
    """
    Checks for gaps in the dataset based on the specified time units.
    
    Parameters:
    - dataset (pd.DataFrame): The dataset to check for gaps.
    - time_units (str): The time units to use for checking gaps (e.g., 'days', 'months', 'years').
    
    Raises:
    - ValueError: If gaps are found in the data.
    """
    if time_units == 'days':
        # Calculate the difference between consecutive dates
        delta = dataset['date'].diff().dropna()
        # Find gaps larger than 1 day
        gaps = [x for x in delta if x > pd.Timedelta(days=1)]
    elif time_units == 'months':
        # Convert dates to periods and calculate the difference between consecutive periods
        periods = dataset['date'].dt.to_period('M')
        delta = periods.diff().dropna()
        month_diffs = delta.apply(lambda x: x.n)
        # Find gaps larger than 1 month
        gaps = [x for x in month_diffs if x > 1]
    elif time_units == 'years':
        # Convert dates to periods and calculate the difference between consecutive periods
        periods = dataset['date'].dt.to_period('Y')
        delta = periods.diff().dropna()
        year_diffs = delta.apply(lambda x: x.n)
        # Find gaps larger than 1 year
        gaps = [x for x in year_diffs if x > 1]
    else:
        raise ValueError("Unsupported time unit. Choose from 'days', 'months', or 'years'.")
    
    # Raise an error if any gaps are found
    if gaps:
        raise ValueError('There are gaps in your data. Please use the fill_gaps function to make your dataset complete before proceeding.')

def add_bounds(dataset, value_column):
    """
    Adds boundary columns to the dataset indicating the start and end of each period.
    
    Parameters:
    - dataset (pd.DataFrame): The dataset to which bounds will be added.
    - value_column (str): The column containing the values to interpolate.
    
    Returns:
    - pd.DataFrame: The dataset with added boundary columns.
    """
    # Shift the date and value columns to get the end date and end value
    dataset['end_date'] = dataset.date.shift(-1)
    dataset[f'end_{value_column}'] = dataset[f'{value_column}'].shift(-1)
    dataset.dropna(subset='end_date', inplace=True)
    # Rename columns for clarity
    dataset.rename({'date': 'start_date', f'{value_column}': f'start_{value_column}'}, inplace=True, axis=1)
    return dataset

def add_timesteps(dataset):
    """
    Adds a column to the dataset indicating the number of timesteps in each period.
    
    Parameters:
    - dataset (pd.DataFrame): The dataset to which timesteps will be added.
    
    Returns:
    - pd.DataFrame: The dataset with the added timesteps column.
    """
    dataset['timesteps'] = dataset.apply(lambda x: len(x['date_range']), axis=1)
    return dataset

def add_daterange(dataset, time_units):
    """
    Adds a column to the dataset with the date range for each period based on the specified time units.
    
    Parameters:
    - dataset (pd.DataFrame): The dataset to which date ranges will be added.
    - time_units (str): The time units for generating the date range (e.g., 'days', 'months', 'years').
    
    Returns:
    - pd.DataFrame: The dataset with the added date_range column.
    """
    if time_units == 'days':
        dataset['date_range'] = dataset.apply(lambda x: pd.date_range(start=x['start_date'], end=x['end_date'], freq='D', inclusive='left'), axis=1)
    elif time_units == 'months':
        dataset['date_range'] = dataset.apply(lambda x: pd.date_range(start=x['start_date'], end=x['end_date'], freq='M', inclusive='left'), axis=1)
    elif time_units == 'years':
        dataset['date_range'] = dataset.apply(lambda x: pd.date_range(start=x['start_date'], end=x['end_date'], freq='Y', inclusive='left'), axis=1)
    return dataset

def date_delta(time_units, date, timesteps):
    """
    Calculates the date after adding a specified number of timesteps to the given date.
    
    Parameters:
    - time_units (str): The time units for adding (e.g., 'days', 'months', 'years').
    - date (pd.Timestamp): The starting date.
    - timesteps (int): The number of timesteps to add.
    
    Returns:
    - pd.Timestamp: The resulting date after adding the timesteps.
    """
    if time_units == 'days':
        edge_date = date + pd.Timedelta(days=timesteps)
    elif time_units == 'months':
        edge_date = date + pd.DateOffset(months=timesteps)
    elif time_units == 'years':
        edge_date = date + pd.DateOffset(years=timesteps)
    return edge_date

def add_rate(dataset, rate_type, value_column):
    """
    Adds a column to the dataset with the calculated rate based on the specified rate type.
    
    Parameters:
    - dataset (pd.DataFrame): The dataset to which rates will be added.
    - rate_type (str): The type of rate to calculate (e.g., 'linear', 'exponential').
    - value_column (str): The column containing the values for rate calculation.
    
    Returns:
    - pd.DataFrame: The dataset with the added rate columns.
    """
    if rate_type == 'linear':
        # Calculate the linear rate
        dataset[f'linear_rate_{value_column}'] = dataset.apply(lambda x: (x[f'end_{value_column}'] - x[f'start_{value_column}']) / x['timesteps'], axis=1)
   
    elif rate_type == 'exponential':
        # Calculate the exponential rate
        dataset[f'exponential_rate_{value_column}'] = dataset.apply(lambda x: (x[f'end_{value_column}'] / x[f'start_{value_column}']) ** (1 / x['timesteps']), axis=1)
    
    return dataset

def add_interpolated_values(dataset, rate_type, value_column):
    """
    Adds a column to the dataset with interpolated values based on the specified rate type.
    
    Parameters:
    - dataset (pd.DataFrame): The dataset to which interpolated values will be added.
    - rate_type (str): The type of rate used for interpolation (e.g., 'linear', 'exponential').
    - value_column (str): The column containing the values to interpolate.
    
    Returns:
    - pd.DataFrame: The dataset with the added interpolated values column.
    """
    if rate_type == 'linear':
        # Generate linear interpolated values
        dataset[f'interpolated_linear_{value_column}'] = dataset.apply(lambda x: [x[f'start_{value_column}'] + n * x[f'linear_rate_{value_column}'] for n in range(x['timesteps'])], axis=1)
   
    elif rate_type == 'exponential':
        # Generate exponential interpolated values
        dataset[f'interpolated_exponential_{value_column}'] = dataset.apply(lambda x: [x[f'start_{value_column}'] * x[f'exponential_rate_{value_column}'] ** n for n in range(x['timesteps'])], axis=1)
    
    return dataset
