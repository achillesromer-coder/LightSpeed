import pandas as pd
import json

def save_simulation_state(data, filename):
    """
    Saves simulation state to a JSON file.
    """
    with open(filename, 'w') as f:
        json.dump(data, f)

def load_simulation_state(filename):
    """
    Loads simulation state from a JSON file.
    """
    with open(filename, 'r') as f:
        data = json.load(f)
    return data

def export_simulation_data(dataframe, filename):
    """
    Exports data to a CSV file.
    """
    dataframe.to_csv(filename, index=False)

def import_simulation_data(filename):
    """
    Imports data from a CSV file.
    """
    return pd.read_csv(filename)
