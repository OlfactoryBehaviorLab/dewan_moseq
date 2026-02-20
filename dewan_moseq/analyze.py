from collections import defaultdict
import logging
import itertools

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def process_experiment(experiment_data: dict[str, pd.DataFrame]):
    all_trial_stats = {}

    for trial_num, trial_data in experiment_data.items():
        all_trial_stats[trial_num] = process_trial(trial_data)

    print(all_trial_stats)

def process_trial(trial_data: pd.DataFrame) -> pd.DataFrame:
    trial_stats = pd.DataFrame(
        columns=['occurrences', 'occurrence_times', 'median_time', 'mean_time', 'median_percentage', 'mean_percentage']
    )
    syllables = trial_data["syllable"]
    num_frames = syllables.shape[0]

    syllable_groups = get_syllable_groups(syllables)

    for syllable, syllable_occurrences in syllable_groups.items():
        occurrences, times, median_time, mean_time, median_percentage, mean_percentage = get_syllable_stats(
            syllable_occurrences, num_frames
        )
        trial_stats.loc[syllable] = [occurrences, times, median_time, mean_time, median_percentage, mean_percentage]

    trial_stats = trial_stats.sort_index()
    return trial_stats


def get_syllable_groups(all_syllables: np.ndarray) -> dict:
    groups_dict = defaultdict(list)
    groups = itertools.groupby(all_syllables)

    for group_name, group in groups:
        groups_dict[group_name].append(list(group))

    return groups_dict


def get_syllable_stats(syllable_occurrences: list, num_frames: int) -> tuple[int, list[int], float, float, float, float]:
    occurrence_lengths = [len(occurrence) for occurrence in syllable_occurrences]
    median_length = np.median(occurrence_lengths)
    mean_length = np.mean(occurrence_lengths)
    median_percentage = median_length / num_frames
    mean_percentage = mean_length / num_frames

    return len(syllable_occurrences), occurrence_lengths, median_length, mean_length, median_percentage, mean_percentage
