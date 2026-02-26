import itertools
import logging
import pathlib
from collections import defaultdict
from typing import Any

import h5py
import numpy as np
import pandas as pd
from tqdm import tqdm

logger = logging.getLogger(__name__)
KEYS = ['centroid', 'heading', 'latent_state', 'syllable']


class DewanKPM:
    def __init__(self, path: pathlib.Path):
        self.filepath: pathlib.Path = path

        self.animal: str | None = None
        self.experiment: str | None = None
        self.raw_trial_data: dict[str, pd.DataFrame] | None = None
        self.trial_data: dict[int, pd.DataFrame] | None = None

        self.trial_stats: dict[int, pd.DataFrame] | None = None

    def load(self):
        self.read_moseqh5()
        self.parse_trial_data()


    def read_moseqh5(self):
        if not self.filepath.exists() or not self.filepath.is_file():
            raise FileNotFoundError(f"File not found: {self.filepath}")

        with h5py.File(self.filepath, "r") as f:
            logger.debug(f"Reading {self.filepath}")
            for trial in f.keys():
                trial_df = pd.DataFrame(columns=KEYS)
                for key in KEYS:
                    raw_data = f[trial][key][:]
                    if len(raw_data.shape) > 1:
                        _data = [tuple(data) for data in raw_data]
                        trial_df[key] = _data
                    else:
                        trial_df[key] = raw_data
                self.raw_trial_data[trial] = trial_df


    def parse_trial_data(self):
        for key, value in self.raw_trial_data.items():
            self.animal, self.experiment, new_key = self._decode_trial_name(key)
            self.trial_data[new_key] = value


    def process_experiment(self):
        for trial_num, trial_data in self.trial_data.items():
            self.trial_stats[trial_num] = self._process_trial(trial_data)


    def write_to_excel(self, output_path: pathlib.Path):
        excel_path = output_path.with_name(f"{self.animal}-{self.experiment}-KPM-trial_stats.xlsx")

        if not output_path.exists():
            raise FileNotFoundError(f"Save directory does not exist!: {output_path}")

        with pd.ExcelWriter(excel_path) as writer:
            for trial_num, trial_data in tqdm(self.trial_stats.items(), desc="Writing trials to disk:"):
                trial_data.to_excel(writer, sheet_name=str(trial_num))

    def _process_trial(self, trial_data: pd.DataFrame) -> pd.DataFrame:
        trial_stats = pd.DataFrame(
            columns=['occurrences', 'occurrence_times', 'median_time', 'mean_time', 'median_percentage',
                     'mean_percentage']
        )
        syllables = trial_data["syllable"]
        num_frames = syllables.shape[0]

        syllable_groups = self.get_syllable_groups(syllables)

        for syllable, syllable_occurrences in syllable_groups.items():
            # occurrences, times, median_time, mean_time, median_percentage, mean_percentage = self.get_syllable_stats(
            #     syllable_occurrences, num_frames
            # )
            trial_stats.loc[syllable] = self.get_syllable_stats(syllable_occurrences, num_frames)
        trial_stats = trial_stats.sort_index()
        return trial_stats

    @staticmethod
    def _decode_trial_name(key_name: str) -> tuple[str, str, int]:
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

    @staticmethod
    def get_syllable_groups(all_syllables: np.ndarray) -> dict:
        groups_dict = defaultdict(list)
        groups = itertools.groupby(all_syllables)

        for group_name, group in groups:
            groups_dict[group_name].append(list(group))

        return groups_dict

    @staticmethod
    def get_syllable_stats(syllable_occurrences: list, num_frames: int) -> tuple[
        int, list[int], np.floating[Any], np.floating[Any], np.floating[Any], np.floating[Any]
    ]:
        occurrence_lengths = [len(occurrence) for occurrence in syllable_occurrences]
        median_length: np.floating[Any] = np.median(occurrence_lengths)
        mean_length: np.floating[Any] = np.mean(occurrence_lengths)
        median_percentage = median_length / num_frames
        mean_percentage = mean_length / num_frames

        return (
            len(syllable_occurrences),
            occurrence_lengths,
            median_length,
            mean_length,
            median_percentage,
            mean_percentage
        )
