import streamlit as st
import pandas as pd
import gdown

FILE_ID = "1wlZmgpW0SGpbqEyt_b5XYT8lXgQUTYmo"
OUTPUT_FILE = "frequenze.xlsx"

@st.cache_data(ttl=60)
def load_allnp():
    url = f"https://drive.google.com/uc?id={FILE_ID}"
    gdown.download(url, OUTPUT_FILE, quiet=True)
    return pd.read_excel(OUTPUT_FILE, sheet_name="ALL NP")

st.title("Foglio: ALL NP")
try:
    df = load_allnp()
    st.dataframe(df)
except Exception as e:
    st.error(f"Errore nel caricamento del foglio ALL NP: {e}")



