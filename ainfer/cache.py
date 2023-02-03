"""
 Authors: Vlad Smetanskyi, Ihor Neporozhnii, Oleksandra Ostapenko
 Status: In development
 Date: Feb 03 2023
"""

from typing import List
from itertools import chain

import streamlit as st

from ainfer.types.files import File, ParsedFile


def cache_files(files: List[File]):
    for file in files:
        cache_file(file)


def cache_file(file: File):
    st.session_state[file.name] = file.value


def get_files_from_cache(names: List[str]) -> List[File]:
    return [get_file_from_cache(name) for name in names]


def get_file_from_cache(name: str) -> File:
    return File(name=name, value=st.session_state[name])


def cache_parsed_file_embeddings(parsed_file: ParsedFile, embeddings: List[float]):
    st.session_state[f'{parsed_file.name}_embeddings'] = embeddings


def get_parsed_file_embeddings_from_cache(parsed_file: ParsedFile):
    return st.session_state[f'{parsed_file.name}_embeddings']


def parsed_file_embeddings_are_cached(parsed_file: ParsedFile) -> bool:
    return f'{parsed_file.name}_embeddings' in st.session_state


def cache_answer(answer_cache_key: str, answer: str):
    st.session_state[answer_cache_key] = answer


def answer_is_cached(answer_cache_key: str) -> bool:
    return answer_cache_key in st.session_state


def get_answer_from_cache(answer_cache_key: str) -> str:
    return st.session_state[answer_cache_key]


def build_answer_cache_key(names: List[str], question: str):
    return ''.join(chain(names, (question,)))
