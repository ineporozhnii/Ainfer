"""
 Authors: Vlad Smetanskyi, Ihor Neporozhnii, Oleksandra Ostapenko
 Status: In development
 Date: Feb 03 2023
"""

from typing import Tuple

from ainfer.types.files import ParsedFile

RankedParagraph = Tuple[ParsedFile, str, float]
