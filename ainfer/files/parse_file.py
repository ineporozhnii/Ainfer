"""
 Authors: Vlad Smetanskyi, Ihor Neporozhnii, Oleksandra Ostapenko
 Status: In development
 Date: Feb 03 2023
"""

from typing import Iterable, List, Tuple

import fitz

from ainfer.types.files import File, ParsedFile, FileFormat


def parse_files(files: Iterable[File]) -> List[ParsedFile]:
    return [parse_file(file) for file in files]


def parse_file(file: File) -> ParsedFile:
    if FileFormat.is_pdf(file.name):
        return _parse_pdf(file)
    if FileFormat.is_docx(file.name):
        return _parse_docx(file)
    return _parse_txt(file)


def _parse_pdf(file: File) -> ParsedFile:
    with fitz.open(stream=file.value) as pdf:
        paragraphs = tuple(paragraph for paragraph, _ in _get_paragraph_data_from_pdf(pdf))
        paragraphs_coordinates = tuple(coordinates for _, coordinates in _get_paragraph_data_from_pdf(pdf))
        return ParsedFile(
            name=file.name,
            value=file.value,
            paragraphs=paragraphs,
            paragraphs_coordinates=paragraphs_coordinates)


def _get_paragraph_data_from_pdf(pdf: fitz.Document) -> Iterable[Tuple]:
    previous_block_id = 0
    for page_number, page in enumerate(pdf):
        for block in page.get_text('blocks'):
            if block[6] == 0:  # We only take the text
                # Compare the block number
                if previous_block_id != block[5]:
                    paragraph = block[4].replace('\n', ' ')
                    paragraphs_coordinates = (block[0], block[1], block[2], block[3], page_number)
                    yield paragraph, paragraphs_coordinates


def _parse_docx(file: File) -> ParsedFile:
    raise NotImplementedError


def _parse_txt(file: File) -> ParsedFile:
    raise NotImplementedError
