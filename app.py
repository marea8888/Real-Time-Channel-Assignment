import streamlit as st
import pandas as pd
import gdown
import matplotlib.pyplot as plt

# ——————————————————————————————
# Imposta la pagina in modalità “wide”
st.set_page_config(layout="wide")
# ——————————————————————————————

# === CONFIGURAZIONE ===
FILE_ID     = "1wlZmgpW0SGpbqEyt_b5XYT8lXgQUTYmo"
OUTPUT_FILE = "frequenze.xlsx"
SHEET       = "ALL NP"

col_bx = "Attributed Frequency TX (MHz)"   # frequenza in MHz
col_ao = "Channel Bandwidth (kHz)"          # ampiezza in kHz
col_aq = "Transmission Power (W)"           # potenza in W
# ——————————————————————————————

@st.cache_data(ttl=60)
def load_data():
    url = f"https://drive.google.com/uc?id={FILE_ID}"
    gdown.download(url, OUTPUT_FILE, quiet=True)
    return pd.read_excel(OUTPUT_FILE, sheet_name=SHEET)

df = load_data()

# Verifica colonne
missing = {col_bx, col_ao, col_aq} - set(df.columns)
if missing:
    st.error(f"Mancano queste colonne nel foglio '{SHEET}': {missing}")
    st.stop()

# Conversioni
df["BX_MHz"] = pd.to_numeric(df[col_bx], errors="coerce")
df["AO_MHz"] = pd.to_numeric(df[col_ao], errors="coerce") / 1000.0
df["AQ_W"]  = pd.to_numeric(df[col_aq], errors="coerce")
df = df.dropna(subset=["BX_MHz","AO_MHz","AQ_W"])

if df.empty:
    st.error("Nessun dato valido dopo la conversione in numerico.")
else:
    max_bx = df["BX_MHz"].max()
    max_aq = df["AQ_W"].max()

    fig, ax = plt.subplots()

    for _, row in df.iterrows():
        center = row["BX_MHz"]
        width  = row["AO_MHz"]
        height = row["AQ_W"]
        left   = center - width / 2
        ax.add_patch(plt.Rectangle((left, 0), width, height, alpha=0.6))

    ax.set_xlim(0, max_bx * 1.05)
    ax.set_ylim(0, max_aq * 1.1)
    ax.set_xlabel("Frequenza (MHz)")
    ax.set_ylabel("Potenza (W)")

    st.pyplot(fig, use_container_width=True)
