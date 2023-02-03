"""
 Authors: Vlad Smetanskyi, Ihor Neporozhnii, Oleksandra Ostapenko
 Status: In development
 Date: Feb 03 2023
"""

import logging
from typing import List, Iterable

from ainfer.types.files import File

import streamlit as st

LOGGER = logging.getLogger(__name__)
MEMORIZED_FILE_SUFFIX = '_memorized_file'


def memorize_files(files: Iterable[File]):
    for file in files:
        memorized_file_key = _memorized_file_key_from_file(file)
        if memorized_file_key in st.session_state:
            del st.session_state[memorized_file_key]
        st.session_state[memorized_file_key] = file.value
        LOGGER.info(f'Memorized file {file.name}.')


def get_files_from_memory() -> List[File]:
    files = list(map(_file_from_memorized_file, filter(_is_memorized_file, st.session_state.items())))

    LOGGER.info(f'Got {len(files)} files from memory.')

    return files


def _memorized_file_key_from_file(file: File) -> str:
    return file.name + MEMORIZED_FILE_SUFFIX


def _is_memorized_file(memorized_file) -> bool:
    memorized_file_key, _ = memorized_file
    return memorized_file_key.endswith(MEMORIZED_FILE_SUFFIX)


def _file_name_from_memorized_file_key(memorized_file_key: str) -> str:
    return memorized_file_key[:-len(MEMORIZED_FILE_SUFFIX)]


def _file_from_memorized_file(memorized_file) -> File:
    memorized_file_key, memorized_file_value = memorized_file
    return File(
        name=_file_name_from_memorized_file_key(memorized_file_key),
        value=memorized_file_value)
