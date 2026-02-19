import logging
import pathlib
import h5py
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
