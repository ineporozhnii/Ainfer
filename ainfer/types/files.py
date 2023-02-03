"""
 Authors: Vlad Smetanskyi, Ihor Neporozhnii, Oleksandra Ostapenko
 Status: In development
 Date: Feb 03 2023
"""

from enum import Enum
from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class File:
    name: str  # may be used to fetch highlighted version of file from session data
    value: bytes


@dataclass(frozen=True)
class ParsedFile(File):
    paragraphs: Tuple[str]
    paragraphs_coordinates: Tuple[Tuple[float, float, float, float, int]]  # last coord is page number


class FileFormat(str, Enum):
    PDF = 'pdf'
    DOCX = 'docx'
    TXT = 'txt'

    def dotted(self):
        return '.' + self.value

    @staticmethod
    def is_pdf(filename: str) -> bool:
        return filename.endswith(FileFormat.PDF.dotted())

    @staticmethod
    def is_docx(filename: str) -> bool:
        return filename.endswith(FileFormat.DOCX.dotted())

    @staticmethod
    def is_txt(filename: str) -> bool:
        return filename.endswith(FileFormat.TXT.dotted())
