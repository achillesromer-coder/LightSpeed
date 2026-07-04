import pandas as pd
import json

# Load elements database
def load_elements_database(file_path="data/elements.json"):
    """
    Loads element data (protons, neutrons, electrons, etc.) from a JSON file.
    """
    with open(file_path, "r") as file:
        elements = json.load(file)
    return elements

# Load fractal presets database
def load_fractal_presets(file_path="data/fractal_presets.csv"):
    """
    Loads fractal expansion presets for atomic structures or eco-rehabilitation nodes.
    """
    return pd.read_csv(file_path)

# Load eco-rehabilitation parameters
def load_eco_rehabilitation_params(file_path="data/eco_params.json"):
    """
    Loads eco-rehabilitation parameters such as resource types, biodiversity nodes, etc.
    """
    with open(file_path, "r") as file:
        eco_params = json.load(file)
    return eco_params

# Save custom user datasets
def save_custom_dataset(data, file_path):
    """
    Saves custom datasets to a specified file path in JSON or CSV format.
    """
    if file_path.endswith(".json"):
        with open(file_path, "w") as file:
            json.dump(data, file, indent=4)
    elif file_path.endswith(".csv"):
        pd.DataFrame(data).to_csv(file_path, index=False)
    else:
        raise ValueError("Unsupported file format. Use .json or .csv.")

# Example usage
if __name__ == "__main__":
    elements = load_elements_database("data/elements.json")
    print("Loaded Elements Database:", elements)

    fractal_presets = load_fractal_presets("data/fractal_presets.csv")
    print("Loaded Fractal Presets:", fractal_presets.head())

    eco_params = load_eco_rehabilitation_params("data/eco_params.json")
    print("Loaded Eco-Rehabilitation Parameters:", eco_params)
