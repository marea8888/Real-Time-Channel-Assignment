import streamlit as st
import pandas as pd
import gdown
import matplotlib.pyplot as plt

# ID del file su Google Drive e nome di output
FILE_ID = "1wlZmgpW0SGpbqEyt_b5XYT8lXgQUTYmo"
OUTPUT_FILE = "frequenze.xlsx"

@st.cache_data(ttl=60)
def load_data():
    # Scarica Excel
    url = f"https://drive.google.com/uc?id={FILE_ID}"
    gdown.download(url, OUTPUT_FILE, quiet=True)
    # Leggi solo il foglio ALL NP
    return pd.read_excel(OUTPUT_FILE, sheet_name="ALL NP")

# Titolo
st.title("Grafico Frequenze (Foglio ALL NP)")

# Carica i dati
df = load_data()

# Estrai la colonna BX e calcola il max
freqs = pd.to_numeric(df["BX"], errors="coerce").dropna()
if freqs.empty:
    st.error("Colonna BX vuota o non numerica.")
else:
    max_freq = freqs.max()
    
    # Crea la figura
    fig, ax = plt.subplots()
    # Istogramma
    ax.hist(freqs, bins=50, range=(0, max_freq), edgecolor='black')
    ax.set_xlim(0, max_freq)
    ax.set_xlabel("Frequenza (MHz)")
    ax.set_ylabel("Conteggio")
    ax.set_title(f"Distribuzione Frequenze (0 – {max_freq:.1f} MHz)")

    # Mostra con Streamlit
    st.pyplot(fig)
