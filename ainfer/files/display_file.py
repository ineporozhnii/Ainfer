"""
 Authors: Vlad Smetanskyi, Ihor Neporozhnii, Oleksandra Ostapenko
 Status: In development
 Date: Feb 03 2023
"""

import base64
from typing import List
import streamlit as st

from ainfer.types.files import File, FileFormat


def display_files(files: List[File], display_file_index):
    files_count = len(files)

    if files_count > 1:
        if display_file_index is not None:
            st.session_state.file_to_display_n = display_file_index + 1
        file_to_display_number = st.selectbox('Choose file to display', range(1, files_count + 1), format_func=lambda i: f'{i}. {files[i - 1].name}', key='file_to_display_n')
    else:
        file_to_display_number = 1

    file_to_display = files[file_to_display_number - 1]

    display_file(file_to_display)


def display_file(file: File):
    if FileFormat.is_pdf(file.name):
        _display_pdf(file.value)
    elif FileFormat.is_docx(file.name):
        _display_docx(file)
    else:
        _display_txt(file)


def _display_pdf(value: bytes):
    base64_pdf = base64.b64encode(value).decode('utf-8')
    pdf_display = f'<object data="data:application/pdf;base64,{base64_pdf}" width="100%" height="1000" type="application/pdf"></object>'
    st.markdown(pdf_display, unsafe_allow_html=True)


def _display_docx(value: bytes):
    raise NotImplementedError


def _display_txt(value: bytes):
    raise NotImplementedError
