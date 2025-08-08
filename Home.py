import streamlit as st #pip install streamlit
import requests
import os
import queue
import io
import time
#from PIL import Image
#import PIL.Image
from streamlit.runtime.scriptrunner import get_script_run_ctx #for multi-threading in streamlit
from streamlit.runtime.scriptrunner import add_script_run_ctx #for multi-threading in streamlit
from google import genai
import threading

#keyload()

#Streamlit Styling
st.set_page_config(layout="wide")

with st.container(border=False):
    st.title("Google Cloud Media Studio")
    #st.markdown("Select from the menu.")
    st.markdown("""
                #### 1) Please note that these are rapid prototypes.
                #### 2) The prototypes leverage prompts to adjust how Gemini answers questions.
                #### 3) A full implementation can use grounding and custom trained models.""")
    #current_folder = os.path.basename(os.getcwd())
    st.markdown(f"Last update: 08.08.2025")
