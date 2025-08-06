import streamlit as st
import pandas as pd
import gdown
import matplotlib.pyplot as plt

# ——————————————————————————————
# Imposta la pagina in modalità “wide”
st.set_page_config(layout="wide")
# Applica tema dark a Matplotlib
plt.style.use('dark_background')
# ——————————————————————————————

# === CONFIGURAZIONE ===
FILE_ID     = "1wlZmgpW0SGpbqEyt_b5XYT8lXgQUTYmo"
OUTPUT_FILE = "frequenze.xlsx"
SHEET       = "ALL NP"

col_bx    = "Attributed Frequency TX (MHz)"   # frequenza in MHz
col_ao    = "Channel Bandwidth (kHz)"         # ampiezza in kHz
col_aq    = "Transmission Power (W)"          # potenza in W
col_venue = "Venue Code"                       # codice venue
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
df['BX_MHz'] = pd.to_numeric(df[col_bx], errors="coerce")
df['AO_MHz'] = pd.to_numeric(df[col_ao], errors="coerce") / 1000.0
df['AQ_W']  = pd.to_numeric(df[col_aq], errors="coerce")
plot_df      = df.dropna(subset=['BX_MHz','AO_MHz','AQ_W'])

if plot_df.empty:
    st.error("Nessun dato valido per il plotting dopo le conversioni.")
else:
    # Calcola margini dinamici
    left_edges  = plot_df['BX_MHz'] - plot_df['AO_MHz'] / 2
    right_edges = plot_df['BX_MHz'] + plot_df['AO_MHz'] / 2
    min_x = left_edges.min()
    max_x = right_edges.max()
    min_y = plot_df['AQ_W'].min()
    max_y = plot_df['AQ_W'].max()

    dx = (max_x - min_x) * 0.05
    dy = (max_y - min_y) * 0.05

    # Figura compatta e dark
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor('#2a2a2a')
    ax.set_facecolor('#2a2a2a')

    for _, row in plot_df.iterrows():
        c = row['BX_MHz']
        w = row['AO_MHz']
        h = row['AQ_W']
        left = c - w / 2
        ax.add_patch(plt.Rectangle((left, 0), w, h, alpha=0.7, edgecolor='#ffffff'))

    ax.set_xlim(min_x - dx, max_x + dx)
    ax.set_ylim(0 if min_y >= 0 else min_y - dy, max_y + dy)

    # Styling assi
    ax.set_xlabel("Frequenza (MHz)", color='white')
    ax.set_ylabel("Potenza (W)", color='white')
    ax.tick_params(colors='white')
    for spine in ax.spines.values():
        spine.set_color('white')

    st.pyplot(fig, use_container_width=True)
