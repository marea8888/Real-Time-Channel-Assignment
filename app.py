import streamlit as st
import pandas as pd
import gdown
import matplotlib.pyplot as plt

# ——————————————————————————————
# === CONFIGURAZIONE ===
FILE_ID     = "1wlZmgpW0SGpbqEyt_b5XYT8lXgQUTYmo"
OUTPUT_FILE = "frequenze.xlsx"
SHEET       = "ALL NP"
# ——————————————————————————————

@st.cache_data(ttl=60)
def load_data():
    # Scarica e legge solo il foglio ALL NP
    url = f"https://drive.google.com/uc?id={FILE_ID}"
    gdown.download(url, OUTPUT_FILE, quiet=True)
    df = pd.read_excel(OUTPUT_FILE, sheet_name=SHEET)
    return df

st.title("Grafico Frequenze con Rettangoli")

# Carica i dati
df = load_data()

# Converte colonne in numerico (MHz e kHz → MHz)
df["BX_MHz"] = pd.to_numeric(df["BX"], errors="coerce")
# AO è in kHz: trasformalo in MHz per la larghezza
df["AO_MHz"] = pd.to_numeric(df["AO"], errors="coerce") / 1000.0
df["AQ_W"]  = pd.to_numeric(df["AQ"], errors="coerce")

# Elimina righe con dati mancanti
df = df.dropna(subset=["BX_MHz","AO_MHz","AQ_W"])

if df.empty:
    st.error("Nessun dato valido in BX/AO/AQ.")
else:
    # Calcola il massimo di BX per i limiti dell'asse X
    max_bx = df["BX_MHz"].max()

    # Costruisci il grafico
    fig, ax = plt.subplots()
    for _, row in df.iterrows():
        center = row["BX_MHz"]
        width  = row["AO_MHz"]
        height = row["AQ_W"]
        left   = center - width/2
        # Disegna un rettangolo pieno
        ax.add_patch(plt.Rectangle(
            (left, 0),        # (x,y) dell'angolo in basso a sinistra
            width,            # larghezza
            height,           # altezza
            alpha=0.6         # trasparenza
        ))

    # Impostazioni assi e titoli
    ax.set_xlim(0, max_bx * 1.05)   # 0 → 5% oltre il max
    # Altezza massima = max potenza + 10%
    ax.set_ylim(0, df["AQ_W"].max() * 1.1)
    ax.set_xlabel("Frequenza (MHz)")
    ax.set_ylabel("Potenza (W)")
    ax.set_title("Allocazioni di Frequenza (BX), Ampiezza AO, Altezza AQ")
    
    st.pyplot(fig)

