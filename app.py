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
col_venue = "Venue Code"                    # codice venue
# ——————————————————————————————

@st.cache_data(ttl=60)
def load_data():
    url = f"https://drive.google.com/uc?id={FILE_ID}"
    gdown.download(url, OUTPUT_FILE, quiet=True)
    return pd.read_excel(OUTPUT_FILE, sheet_name=SHEET)

# Carica dati originali
df = load_data()

# Selezione venue
overall_venues = df[col_venue].dropna().unique().tolist()
overall_venues.sort()
selection = st.selectbox("Select Venue", ["All"] + overall_venues)

# Filtra in base alla selezione
if selection != "All":
    df = df[df[col_venue] == selection]

# Controllo colonne
missing = {col_bx, col_ao, col_aq} - set(df.columns)
if missing:
    st.error(f"Mancano queste colonne nel foglio '{SHEET}': {missing}")
    st.stop()

# Conversioni
# Frequenza centrale in MHz
freq = pd.to_numeric(df[col_bx], errors="coerce")
# Ampiezza in MHz (AO in kHz)
width = pd.to_numeric(df[col_ao], errors="coerce") / 1000.0
# Potenza in W
height = pd.to_numeric(df[col_aq], errors="coerce")

plot_df = pd.DataFrame({"center": freq, "width": width, "height": height}).dropna()

if plot_df.empty:
    st.error("Nessun dato valido per il plotting dopo le conversioni.")
else:
    max_bx = plot_df["center"].max()
    max_aq = plot_df["height"].max()

    fig, ax = plt.subplots(figsize=(16, 9))
    for _, row in plot_df.iterrows():
        c = row["center"]
        w = row["width"]
        h = row["height"]
        left = c - w / 2
        ax.add_patch(plt.Rectangle((left, 0), w, h, alpha=0.6))

    ax.set_xlim(0, max_bx * 1.05)
    ax.set_ylim(0, max_aq * 1.1)
    ax.set_xlabel("Frequenza (MHz)")
    ax.set_ylabel("Potenza (W)")

    # Mostra il grafico senza titoli
    st.pyplot(fig, use_container_width=True)
