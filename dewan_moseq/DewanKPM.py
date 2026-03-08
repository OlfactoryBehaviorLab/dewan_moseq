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

class DewanKPMParser:
    def __init__(self, filepath: pathlib.Path):
        self.filepath = filepath

        self.raw_data: dict[str, dict] = {}
        self.sorted_data: dict[str, dict] = defaultdict(lambda: defaultdict(dict))
        self.parsed_and_sorted_data: dict[str, dict] = defaultdict(lambda: defaultdict(dict))

        self.read_moseqh5()
        self.sort_data()
        self.parse_data()


    def read_moseqh5(self):
        logger.info("Reading moseq h5 file...")
        if not self.filepath.exists() or not self.filepath.is_file():
            raise FileNotFoundError(f"File not found: {self.filepath}")

        with h5py.File(self.filepath, "r") as f:
            logger.debug(f"Reading {self.filepath}")
            for video in f.keys():
                video_dict = {}
                for key in KEYS:
                    raw_data = f[video][key][:]
                    if len(raw_data.shape) > 1:
                        _data = [tuple(data) for data in raw_data]
                        video_dict[key] = _data
                    else:
                        video_dict[key] = raw_data
                self.raw_data[video] = video_dict


    def sort_data(self):
        logger.info("Sorting KPM output by animal, experiment, and trial...")
        for key, data in self.raw_data.items():
            animal, experiment, trial_num, experiment_date = self._decode_trial_name(key)
            self.sorted_data[animal][experiment_date][trial_num] = data

    def parse_data(self):
        logger.info("Parsing KPM data by animal and date")
        for animal, animal_dict in self.sorted_data.items():
            for date, exp_data in animal_dict.items():
                self.parsed_and_sorted_data[animal][date] = DewanKPMExperiment(exp_data, animal, date)


    @staticmethod
    def _decode_trial_name(key_name: str) -> tuple[str, str, str, str]:
        """
        Decode trial key into its constituent pieces

        key is in the form [Animal]-[Experiment]-trial-[Trial_Number]-[Experiment_Date]DLC-[DLC_MODEL_INFORMATION]
        Parameters
        ----------
        key_name : str
            Trial key name

        Returns
        -------
            Parsed String: tuple[str, str, str, str]
                index 0: Animal, index 1: Experiment, index 2: Trial_Number, idnex 3: Experiment Date
        """
        pieces = key_name.split("DLC")[0].split("-")
        animal, experiment = pieces[0], pieces[1]
        trial_num = pieces[3]
        experiment_date = '-'.join(pieces[4:])



        return animal, experiment, trial_num, experiment_date


    def __repr__(self):
        return (f"DewanKPMParser({self.filepath})\n"
                f"Number of Videos: {len(self.raw_data)}")


class DewanKPMExperiment:
    def __init__(self, experiment_data: dict, animal: str, date: str):
        self.experiment_data: dict[str, dict] = experiment_data

        self.animal: str = animal
        self.experiment: str = date
        self.raw_trial_data: dict[str, pd.DataFrame] = {}
        self.pre_stim_stats: dict[int, pd.DataFrame] | None = {}
        self.stim_stats: dict[int, pd.DataFrame] | None = {}
        self.post_stim_stats: dict[int, pd.DataFrame] | None = {}

        self.pre_stim_syllables = {}
        self.stim_syllables = {}
        self.post_stim_syllables = {}

        self.preprocess_experiment()
        self.process_experiment()

    def preprocess_experiment(self):
        for trial, trial_data in self.experiment_data.items():
            trial_df = pd.DataFrame(trial_data, columns=KEYS)
            self.raw_trial_data[trial] = trial_df

    def process_experiment(self):
        pre_stim_df = pd.DataFrame()
        stim_df = pd.DataFrame()
        post_stim_df = pd.DataFrame()
        for trial_num, trial_data in self.raw_trial_data.items():
            pre_stim_data = trial_data.iloc[0:120]
            stim_data = trial_data.iloc[120:180]
            post_stim_data = trial_data.iloc[180:]

            pre_stim_syllables = pre_stim_data["syllable"]
            stim_syllables = stim_data["syllable"]
            post_stim_syllables = post_stim_data["syllable"]
            pre_stim_syllables.name=int(trial_num)
            stim_syllables.name=int(trial_num)
            post_stim_syllables.name=int(trial_num)

            pre_stim_df = pd.concat((pre_stim_df, pre_stim_syllables), axis=1)
            stim_df = pd.concat((stim_df, stim_syllables), axis=1)
            post_stim_df = pd.concat((post_stim_df, post_stim_syllables), axis=1)

            self.pre_stim_stats[int(trial_num)] = self._process_trial(pre_stim_data)
            self.stim_stats[int(trial_num)] = self._process_trial(stim_data)
            self.post_stim_stats[int(trial_num)] = self._process_trial(post_stim_data)

        self.pre_stim_syllables = pre_stim_df
        self.stim_syllables = stim_df
        self.post_stim_syllables = post_stim_df

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

    def __repr__(self):
        return f"DewanKPM Experiment: ({self.animal}-{self.experiment})"


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
