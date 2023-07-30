#!/usr/bin/env python3

"""LibriSpeechMix data preparation.

Authors
 * Luca Della Libera 2023
"""

import argparse
import json
import logging
import os
from collections import defaultdict
from typing import Sequence

import torchaudio


__all__ = ["prepare_librispeech_mix"]


# Logging configuration
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(funcName)s - %(message)s",
)

_LOGGER = logging.getLogger(__name__)

_DEFAULT_SPLITS = (
    "dev-clean-1mix",
    "dev-clean-2mix",
    "dev-clean-3mix",
    "test-clean-1mix",
    "test-clean-2mix",
    "test-clean-3mix",
)


def prepare_librispeech_mix(
    data_folder: "str", splits: "Sequence[str]" = _DEFAULT_SPLITS,
) -> "None":
    """Prepare data manifest JSON files for LibriSpeechMix dataset
    (see https://github.com/NaoyukiKanda/LibriSpeechMix).

    Arguments
    ---------
    data_folder:
        The path to the dataset folder.
    splits:
        The dataset splits to load.
        Splits with the same prefix are merged into a single
        JSON file (e.g. "dev-clean-1mix" and "dev-clean-2mix").
        Default to all the available splits.

    Raises
    ------
    ValueError
        If an invalid argument value is given.
    RuntimeError
        If the data folder's structure does not match the expected one.

    Examples
    --------
    >>> prepare_librispeech_mix( "LibriSpeechMix", ["dev-clean-2mix", "test-clean-2mix"])

    """
    if not splits:
        raise ValueError(f"`splits` ({splits}) must be non-empty")

    # Grouping
    groups = defaultdict(list)
    for split in splits:
        if split.startswith("dev"):
            groups["dev"].append(split)
        elif split.startswith("test"):
            groups["test"].append(split)
        else:
            raise ValueError(
                f'`split` ({split}) must start with either "dev" or "test"'
            )

    # Write output JSON for each group
    for group_name, group in groups.items():
        _LOGGER.info(
            "----------------------------------------------------------------------",
        )

        output_entries = {}
        for split in group:
            _LOGGER.info(f"Split: {split}")

            # Read input JSONL
            input_jsonl = os.path.join(data_folder, "list", f"{split}.jsonl")
            if not os.path.exists(input_jsonl):
                raise RuntimeError(
                    f'"{input_jsonl}" JSONL not found. '
                    f"Download the data generation scripts from https://github.com/NaoyukiKanda/LibriSpeechMix "
                    f"and follow the readme to generate the data"
                )
            with open(input_jsonl, "r", encoding="utf-8") as fr:
                for input_line in fr:
                    input_entry = json.loads(input_line)
                    ID = input_entry["id"]
                    mixed_wav = input_entry["mixed_wav"]
                    texts = input_entry["texts"]
                    speaker_profile = input_entry["speaker_profile"]
                    speaker_profile_index = input_entry["speaker_profile_index"]
                    # wavs = input_entry["wavs"]
                    # delays = input_entry["delays"]
                    # speakers = input_entry["speakers"]
                    # durations = input_entry["durations"]
                    # genders = input_entry["genders"]

                    info = torchaudio.info(os.path.join(data_folder, "data", mixed_wav))
                    duration = info.num_frames / info.sample_rate

                    mixed_wav = os.path.join("{DATA_ROOT}", "data", mixed_wav)
                    for i, (text, idx) in enumerate(zip(texts, speaker_profile_index)):
                        ID_text = f"{ID}_text-{i}"
                        enroll_wavs = speaker_profile[idx]
                        for enroll_wav in enroll_wavs:
                            ID_enroll = f"{ID_text}_{enroll_wav}"
                            enroll_wav = os.path.join("{DATA_ROOT}", "data", enroll_wav)
                            output_entry = {
                                "mixed_wav": mixed_wav,
                                "enroll_wav": enroll_wav,
                                "transcription": text,
                                "duration": duration,
                            }
                            output_entries[ID_enroll] = output_entry

        # Write output JSON
        output_json = os.path.join(data_folder, f"{group_name}.json")
        _LOGGER.info(f"Writing output JSON file ({output_json})...")
        with open(output_json, "w", encoding="utf-8") as fw:
            json.dump(output_entries, fw, ensure_ascii=False, indent=4)

    _LOGGER.info("Done!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare LibriSpeechMix dataset")
    parser.add_argument(
        "data_folder", help="path to the dataset folder",
    )
    parser.add_argument(
        "-s",
        "--splits",
        nargs="+",
        default=_DEFAULT_SPLITS,
        help=(
            "dataset splits to load. Splits with the same prefix are merged into a "
            'single JSON file (e.g. "dev-clean-1mix" and "dev-clean-2mix").'
        ),
    )

    args = parser.parse_args()
    prepare_librispeech_mix(args.data_folder, args.splits)