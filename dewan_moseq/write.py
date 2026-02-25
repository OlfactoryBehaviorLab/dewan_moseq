import pathlib

import pandas as pd


def write_experiment(all_data: dict[str, pd.DataFrame], path: pathlib.Path, experiment_name: str):
    with pd.ExcelWriter('dewan_moseq.xlsx') as writer:
        pass