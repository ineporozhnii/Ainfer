"""
 Authors: Vlad Smetanskyi, Ihor Neporozhnii, Oleksandra Ostapenko
 Status: In development
 Date: Feb 03 2023
"""

import logging
from typing import Sequence
from pathlib import Path
import streamlit as st

from cachetools.func import ttl_cache
import gdown

from ainfer.types.files import File

LOGGER = logging.getLogger(__name__)
DEFAULT_DOWNLOAD_FOLDER = '/tmp/ainfer/google_drive_files'


# test url: https://drive.google.com/drive/folders/1k2vQrn3WbvIBH4klVSzxAKRTKgYZvpwa?usp=share_link
@ttl_cache(ttl=60 * 10)  # cache for 10 minutes, not to download the same files over and over again
def download_files_from_google_drive(google_drive_folder_url: str) -> Sequence[File]:
    # gdown saves files from the Google Drive folder to the local DEFAULT_DOWNLOAD_FOLDER folder
    # and returns complete paths to the downloaded files like DEFAULT_DOWNLOAD_FOLDER/somefile.pdf
    warning_message = 'Please, provide a valid Google Drive folder link or check permissions'
    try:
        filenames = gdown.download_folder(google_drive_folder_url, output=DEFAULT_DOWNLOAD_FOLDER, quiet=True)
        if type(filenames) is not list:
            st.sidebar.warning(warning_message, icon="⚠️")
            filenames = []
    except Exception as e:
        st.sidebar.warning(warning_message, icon="⚠️")
        filenames = []

    # TODO: read files in parallel
    return tuple(_pop_file(filename) for filename in filenames)


# read file and delete it
def _pop_file(filename: str) -> File:
    file_path = Path(filename)
    try:
        file_contents = file_path.open('rb').read()
        return File(name=file_path.name, value=file_contents)
    except Exception as e:
        LOGGER.warning(f'Failed reading file: {file_path}.', e)
    finally:
        file_path.unlink(missing_ok=True)  # delete the file after reading it
