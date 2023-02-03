"""
 Authors: Vlad Smetanskyi, Ihor Neporozhnii, Oleksandra Ostapenko
 Status: In development
 Date: Feb 03 2023
"""

import runpy

# As streamlit is not able to run modules, but we want modules, we need to do this magic here
runpy.run_module("ainfer.entrypoint", run_name="__main__", alter_sys=True)
