"""
 Authors: Vlad Smetanskyi, Ihor Neporozhnii, Oleksandra Ostapenko
 Status: In development
 Date: Feb 03 2023
"""

import base64
import time
import os
import logging
from operator import itemgetter
from typing import Sequence

import cohere
import streamlit as st
import numpy as np
from PIL import Image

from ainfer.client import file_uploader, file_memorizer
from ainfer.memory import memorize_files
from ainfer.types.ranking import RankedParagraph
from ainfer.files.highlight_file import highlight_paragraphs_in_files
from ainfer.files.display_file import display_files
from ainfer.files.parse_file import parse_files
from ainfer.ranking import rank_paragraphs, choose_paragraphs_for_context
from ainfer.cache import cache_files, get_files_from_cache, cache_answer, get_answer_from_cache, build_answer_cache_key, answer_is_cached

logging.basicConfig(level=logging.INFO)

LOGGER = logging.getLogger(__name__)


def build_context(paragraphs_for_context: Sequence[RankedParagraph]) -> str:
    LOGGER.info(f"Number of paragraphs chosen for context: {len(paragraphs_for_context)}")

    LOGGER.info(f"Similarities of chosen paragraphs: {list(map(itemgetter(-1), paragraphs_for_context))}")

    return "\n".join(map(itemgetter(1), paragraphs_for_context))


def trim_stop_sequences(s, stop_sequences):
    for stop_sequence in stop_sequences:
        if s.endswith(stop_sequence):
            return s[:-len(stop_sequence)]
    return s


@st.cache(allow_output_mutation=True)
def get_base64_of_bin_file(bin_file):
    with open(bin_file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()


@st.cache(allow_output_mutation=True)
def get_img_with_href(local_img_path, target_url, align):
    img_format = os.path.splitext(local_img_path)[-1].replace(".", "")
    bin_str = get_base64_of_bin_file(local_img_path)
    html_code = f"""
    <a href="{target_url}">
            <img align={align} src="data:image/{img_format};base64,{bin_str}" style="width:30px; height:30px" />
        </a>"""
    return html_code


def create_response(question, context, co, model, chat_history=""):
    prompt = (
        f'Read the paragraphs from the context below and answer the question, if the question cannot be answered based on the context alone, write "sorry i had trouble answering this question, based on the provided information \n'
        f"\n"
        f"Context:\n"
        f"{ context }\n"
        f"\n"
        f"Question: { question }\n"
        "Answer:")
    stop_sequences = []

    num_generations = 2
    prompt = "".join(co.tokenize(text=prompt).token_strings[-1900:])
    
    LOGGER.info(f'Generating response for the question: "{question}".')

    prediction = co.generate(
        model=model,
        prompt=prompt,
        max_tokens=500,
        temperature=0.3,
        stop_sequences=stop_sequences,
        num_generations=num_generations,
        return_likelihoods="GENERATION")

    generations = prediction.generations

    LOGGER.info('Generated response. Doing some post-processing.')

    return generations[np.argmax(map(lambda g: g.likelihood, generations))].text.strip()


def get_summary(context, co, model):
    prompt = (
        f'Read the paragraph below and summarize it in a few sentences, if the context can not be summarized, write "Sorry, I could not come up with a good summary \n'
        f"\n"
        f"Paragraph:\n"
        f"{ context }\n"
        f"\n"
        "Summary:")

    num_generations = 2
    prompt = "".join(co.tokenize(text=prompt).token_strings[-1900:])

    stop_sequences = []

    prediction = co.generate(
        model=model,
        prompt=prompt,
        max_tokens=100,
        temperature=0.3,
        stop_sequences=stop_sequences,
        num_generations=num_generations,
        return_likelihoods="GENERATION")

    generations = prediction.generations

    return generations[np.argmax(map(lambda g: g.likelihood, generations))].text.strip()

def main():

    app_logo = Image.open('assets/ainfer_logo.png')
    tab_icon = Image.open("assets/favicon.png")
    st.set_page_config(page_title="Aїnfer | Chat with Papers", page_icon=tab_icon, layout="wide")

    st.sidebar.image(app_logo)
    cohere_api_key = ""
    co = cohere.Client(cohere_api_key)

    st.markdown("""
    <style>
        .css-6wvkk3.egzxvld4 {
        margin-top: -75px;
        }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <style>
        .css-k1ih3n.egzxvld4 {
        margin-top: -75px;
        }
    </style>
    """, unsafe_allow_html=True)

    st.sidebar.header("Chat with Papers")

    

    uploaded_files, upload_expander = file_uploader()

    if not uploaded_files:
        st.markdown(" ### :arrow_left: Use the sidebar to upload files and ask questions")

    uploaded_file_names = [file.name for file in uploaded_files]

    memorized_files = file_memorizer(upload_expander)

    memorize_files(uploaded_files)

    raw_files = uploaded_files + list(filter(lambda mf: mf.name not in uploaded_file_names, memorized_files))

    raw_file_names = [file.name for file in raw_files]

    cache_files(raw_files)
    display_file_index = None

    if raw_files:
        parsed_files = parse_files(raw_files)

    with st.sidebar.expander("Get Answer"):
        question = st.text_input('Ask a question:', placeholder=None, key="input")

        answer = None
        answer_key = build_answer_cache_key(raw_file_names, question)
        if question and answer_is_cached(answer_key):
            LOGGER.info(answer_key)
            answer = get_answer_from_cache(answer_key)

        if question and raw_files and not answer:
            bar = st.progress(0.0)

            ranked_paragraphs = rank_paragraphs(
                parsed_files, question, co, model="multilingual-22-12")
            
            if ranked_paragraphs is not None:
                try:
                    display_file_index = uploaded_file_names.index(ranked_paragraphs[-1][0].name)
                except ValueError:
                    display_file_index = None

                paragraphs_for_context = choose_paragraphs_for_context(ranked_paragraphs)

                cache_files(raw_files) # to clear existing highlight
                cache_files(highlight_paragraphs_in_files(paragraphs_for_context))

                context = build_context(paragraphs_for_context)

                bar.progress(0.5)
                
                answer = create_response(question=question, context=context, co=co, model='command-medium-nightly')
                cache_answer(answer_key, answer)
                
                bar.progress(1.0)
            
                response_window = st.empty()
                for i in range(len(answer) + 1):
                    response_window.text_area(label="Response: ", value=answer[0:i], height=200, disabled=False)
                    time.sleep(0.02)
                bar.empty()
            else:
                bar.empty()
        # TODO: if the answer is present, but the user checked use_memory, then we should recompute the answer
        elif question and raw_files and answer:
            response_window = st.empty()
            response_window.text_area(label="Response: ", value=answer, height=200, disabled=False)

    if uploaded_files:
        display_files(get_files_from_cache(uploaded_file_names), display_file_index=display_file_index)


    with st.sidebar.expander("Get Summary"):
        summary_col1, summary_col2 = st.columns(2)
        
        summary_request = summary_col1.button(label="Summarize text below", help="Paste text to the window below and press this button to get the summary")
        
        text_to_sum_window = st.empty()
        summary_window = st.empty()
        
        text_to_sum = text_to_sum_window.text_area(label="Text for Summary: ", value="", height=200, disabled=False, key="sum_window")

        summary = None
        summary_key = build_answer_cache_key(raw_file_names, 'summary')
        if summary_request and answer_is_cached(summary_key):
            summary = get_answer_from_cache(summary_key)

        if summary_request:
            with summary_col2:
                st.write("")
            sum_bar = summary_col2.progress(0.0)
            summary = get_summary(context=text_to_sum, co=co, model='command-medium-nightly')
            cache_answer(summary_key, summary)
            summary.replace("\n", " ")
            sum_bar.progress(1.0)
            for i in range(len(summary) + 1):
                summary_window.text_area(label="Summary: ", value=summary[0:i], height=200, disabled=False)
                time.sleep(0.02)
            sum_bar.empty()

    st.sidebar.write("\n")
    column1, column2 = st.sidebar.columns(2)

    html_code_linkedin = get_img_with_href("assets/linkedin_logo.png", "https://www.linkedin.com/in/ihor-neporozhnii/", align="left")
    html_code_twitter = get_img_with_href("assets/twitter_logo.png", "https://twitter.com/ineporozhnii", align="right")
    column1.markdown(html_code_twitter, unsafe_allow_html=True)
    column2.markdown(html_code_linkedin, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
