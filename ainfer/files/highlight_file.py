"""
 Authors: Vlad Smetanskyi, Ihor Neporozhnii, Oleksandra Ostapenko
 Status: In development
 Date: Feb 03 2023
"""

import fitz
from typing import List
from collections import defaultdict
from collections.abc import Mapping

from ainfer.types.ranking import RankedParagraph
from ainfer.types.files import ParsedFile

STROKE_COLOR = (0, 0, 0)
HIGHLIGHT_COLOR = (0, 45 / 255, 1)


def highlight_paragraphs_in_files(ranked_paragraphs: List[RankedParagraph]) -> List[ParsedFile]:
    return [_highlight_paragraphs_in_file(file, paragraphs) for file, paragraphs in _group_paragraphs_by_file(ranked_paragraphs).items()]


def _highlight_paragraphs_in_file(file: ParsedFile, paragraphs: List[str]) -> ParsedFile:

    coords = (file.paragraphs_coordinates[file.paragraphs.index(p)] for p in paragraphs)

    with fitz.open(stream=file.value) as pdf:
        for paragraph_coords in coords:

            poycoords = [(paragraph_coords[0], paragraph_coords[1]), (paragraph_coords[2], paragraph_coords[1]),
                         (paragraph_coords[2], paragraph_coords[3]), (paragraph_coords[0], paragraph_coords[3])]

            page = pdf[paragraph_coords[-1]] # last coordinate is the page number

            shape = page.new_shape()
            shape.drawPolyline(poycoords)
            shape.finish(color=STROKE_COLOR, fill=HIGHLIGHT_COLOR, stroke_opacity=0.15, fill_opacity=0.15)
            shape.commit()

        return ParsedFile(
            name=file.name,
            value=pdf.write(),
            paragraphs=file.paragraphs,
            paragraphs_coordinates=file.paragraphs_coordinates)


def _group_paragraphs_by_file(ranked_paragraphs: List[RankedParagraph]) -> Mapping[ParsedFile, List[str]]:
    groups = defaultdict(list)
    for file, paragraph, _ in ranked_paragraphs:
        groups[file].append(paragraph)
    return groups
