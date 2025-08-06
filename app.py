import streamlit as st
import pandas as pd
import gdown

FILE_ID     = "1wlZmgpW0SGpbqEyt_b5XYT8lXgQUTYmo"
OUTPUT_FILE = "frequenze.xlsx"
SHEET       = "ALL NP"

@st.cache_data(ttl=60)
def load_data():
    url = f"https://drive.google.com/uc?id={FILE_ID}"
    gdown.download(url, OUTPUT_FILE, quiet=True)
    return pd.read_excel(OUTPUT_FILE, sheet_name=SHEET)

st.title("Debug colonne e grafico rettangoli")

df = load_data()

# 1️⃣ Mostra le colonne per debugging
st.write("🔍 Colonne trovate nel foglio ALL NP:", df.columns.tolist())

# 2️⃣ Una volta che vedi il nome esatto, sostituisci qui sotto:
col_bx = "Attributed Frequency TX (MHz)"    # cambialo con il nome esatto
col_ao = "Channel Bandwidth (kHz)"    # idem
col_aq = "Transmission Power (W)"    # idem

# Verifica che ora esistano
if not {col_bx, col_ao, col_aq}.issubset(df.columns):
    missing = {col_bx, col_ao, col_aq} - set(df.columns)
    st.error(f"Mancano le colonne: {missing}")
else:
    # Conversioni
    df["BX_MHz"] = pd.to_numeric(df[col_bx], errors="coerce")
    df["AO_MHz"] = pd.to_numeric(df[col_ao], errors="coerce") / 1000.0
    df["AQ_W"]  = pd.to_numeric(df[col_aq], errors="coerce")
    df = df.dropna(subset=["BX_MHz","AO_MHz","AQ_W"])
    
    # Costruzione grafico come prima...
    import matplotlib.pyplot as plt
    max_bx = df["BX_MHz"].max()
    fig, ax = plt.subplots()
    for _, row in df.iterrows():
        c = row["BX_MHz"]
        w = row["AO_MHz"]
        h = row["AQ_W"]
        ax.add_patch(plt.Rectangle((c - w/2, 0), w, h, alpha=0.6))
    ax.set_xlim(0, max_bx * 1.05)
    ax.set_ylim(0, df["AQ_W"].max() * 1.1)
    ax.set_xlabel("Frequenza (MHz)")
    ax.set_ylabel("Potenza (W)")
    st.pyplot(fig)


