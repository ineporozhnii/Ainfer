"""
 Authors: Vlad Smetanskyi, Ihor Neporozhnii, Oleksandra Ostapenko
 Status: In development
 Date: Feb 03 2023
"""

import logging
from itertools import islice, chain
from collections import deque
from operator import itemgetter
from statistics import stdev
from typing import Sequence, Deque, List, Optional
import streamlit as st

import numpy as np

from ainfer.cache import (
    parsed_file_embeddings_are_cached,
    get_parsed_file_embeddings_from_cache,
    cache_parsed_file_embeddings)
from ainfer.types.files import ParsedFile
from ainfer.types.ranking import RankedParagraph

LOGGER = logging.getLogger(__name__)
PARAGRAPHS_IN_CONTEXT_MAX_COUNT = 10
STD_THRESHOLD = 0.01


def rank_paragraphs(parsed_files, question, co, model) -> Sequence[RankedParagraph]:
    files_and_paragraphs = tuple((file, paragraph) for file in parsed_files for paragraph in file.paragraphs)

    embeddings = get_embeddings(parsed_files, question, co, model)

    paragraph_embeddings, search_embedding = islice(embeddings, 0, len(embeddings) - 1), embeddings[-1]

    similarities = (get_similarity(paragraph_embedding, search_embedding)
                    for paragraph_embedding in paragraph_embeddings)

    files_paragraphs_similarities = ((*file_and_paragraph, similarity)
                                     for (file_and_paragraph, similarity) in
                                     zip(files_and_paragraphs, similarities))

    return list(sorted(files_paragraphs_similarities, key=itemgetter(-1)))


def choose_paragraphs_for_context(ranked_paragraphs: List[RankedParagraph]) -> Sequence[RankedParagraph]:
    paragraphs_for_context = deque((ranked_paragraphs.pop(),))

    for candidate in reversed(ranked_paragraphs):

        _, _, similarity = candidate

        current_similarities = map(itemgetter(-1), paragraphs_for_context)

        if stdev(chain((similarity,), current_similarities)) >= STD_THRESHOLD:
            break
        if len(paragraphs_for_context) >= PARAGRAPHS_IN_CONTEXT_MAX_COUNT:
            break
        paragraphs_for_context.appendleft(candidate)

    return paragraphs_for_context


def get_similarity(a, b):
    # TODO: Try BERT for similarity
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def get_embeddings(parsed_files, question, co, model):
    embeddings, parsed_files_without_embeddings = [], []
    for parsed_file in parsed_files:
        if parsed_file_embeddings_are_cached(parsed_file):
            embeddings.extend(get_parsed_file_embeddings_from_cache(parsed_file))
            LOGGER.info('Obtained embeddings from cache for %s.', parsed_file.name)
        else:
            # We want to preserve the order of embeddings, that's why we put None in place of missing embeddings
            embeddings.extend([None] * len(parsed_file.paragraphs))
            parsed_files_without_embeddings.append(parsed_file)

    paragraphs_without_embeddings = (paragraph for parsed_file in parsed_files_without_embeddings
                                     for paragraph in parsed_file.paragraphs)
    texts = tuple(chain(paragraphs_without_embeddings, (question,)))

    try:
        new_embeddings = co.embed(texts=texts, model=model).embeddings
    except Exception as e:
        warning_message = 'Sorry, we are experiencing high traffic. \n Please, try again in a minute or try a smaller file'
        st.sidebar.warning(warning_message, icon="⚠️")
        return None

    missing_embeddings = deque(islice(new_embeddings, 0, len(new_embeddings) - 1))
    question_embedding = new_embeddings[-1]

    _cache_missing_embeddings(parsed_files_without_embeddings, missing_embeddings.copy())
    _populate_with_missing_embeddings(embeddings, missing_embeddings.copy())
    embeddings.append(question_embedding)
    return embeddings


def _cache_missing_embeddings(parsed_files_without_embeddings: List[ParsedFile], missing_embeddings: Deque[float]):
    for parsed_file in parsed_files_without_embeddings:
        parsed_file_embeddings = []
        for _ in parsed_file.paragraphs:
            parsed_file_embeddings.append(missing_embeddings.popleft())
        cache_parsed_file_embeddings(parsed_file, parsed_file_embeddings)
        LOGGER.info('Cached embeddings for %s.', parsed_file.name)


def _populate_with_missing_embeddings(embeddings: List[Optional[float]], missing_embeddings: Deque[float]):
    for i, embedding in enumerate(embeddings):
        if embedding is None:
            embeddings[i] = missing_embeddings.popleft()
