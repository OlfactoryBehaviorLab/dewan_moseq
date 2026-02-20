import logging
import pathlib
import h5py
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)
keys = ['centroid', 'heading', 'latent_state', 'syllable']

def readh5(path: pathlib.Path) -> dict[str, pd.DataFrame]:
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")

    all_data = {}

    with h5py.File(path, "r") as f:
        for experiment in f.keys():
            animal_df = pd.DataFrame(columns=keys)
            for key in keys:
                raw_data = f[experiment][key][:]
                if len(raw_data.shape) > 1:
                    _data = [tuple(data) for data in raw_data]
                    animal_df[key] = _data
                else:
                    animal_df[key] = raw_data
            all_data[experiment] = animal_df
        return all_data


def relabel_data_dict(all_data: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    data_with_new_labels = {}

    for key, value in all_data.items():
        animal, _, new_key = decode_trial_name(key)

        if animal not in data_with_new_labels.keys():
            data_with_new_labels[animal] = {}
            # If the animal dict does not exist, make it

        data_with_new_labels[animal][new_key] = value

    return data_with_new_labels



def decode_trial_name(key_name: str) -> tuple[str, str, int]:
    """
    Decode trial key into its constituent pieces

    key is in the form [Animal]-[Experiment]-trial-[Trial_Number]DLC-[DLC_MODEL_INFORMATION]
    Parameters
    ----------
    key_name : str
        Trial key name

    Returns
    -------
        Parsed String: tuple[str, str, int]
            index 0: Animal, index 1: Experiment, index 2: Trial_Number
    """
    pieces = key_name.split("DLC")[0].split("-")

    return pieces[0], pieces[1], int(pieces[3])