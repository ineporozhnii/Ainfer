"""
 Authors: Vlad Smetanskyi, Ihor Neporozhnii, Oleksandra Ostapenko
 Status: In development
 Date: Feb 03 2023
"""

from typing import List

import streamlit as st

from ainfer.files.download_file import download_files_from_google_drive
from ainfer.memory import get_files_from_memory
from ainfer.types.files import File

# TODO: Move all the client interaction code from `entrypoint.py` here.

NO_LABEL = ''


def file_uploader() -> List[File]:
    upload_expander = st.sidebar.expander('Upload PDFs')
    with upload_expander:
        uploaded_files = [
            File(name=uploaded_file.name, value=uploaded_file.getvalue())
            for uploaded_file in st.file_uploader('From local storage', type=['pdf'], accept_multiple_files=True)
        ]

        google_drive_folder_link = st.text_input(
            'From Google Drive', placeholder='Your Google Drive folder', key='google_drive_folder_link')

        if google_drive_folder_link:
            google_drive_files = download_files_from_google_drive(google_drive_folder_link)
            uploaded_files.extend(google_drive_files)

        return uploaded_files, upload_expander


def file_memorizer(upload_expander) -> List[File]:
    with upload_expander:
        use_memory = st.checkbox("Use memory", help="Cache uploaded files to improve the performance", value=False)
        if not use_memory:
            return []
        return get_files_from_memory()
