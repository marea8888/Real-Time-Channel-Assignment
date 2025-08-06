import streamlit as st
import pandas as pd
import gdown
import plotly.graph_objects as go

# ——————————————————————————————
# Configura pagina e tema
st.set_page_config(
    page_title="Realtime Frequency Plot",
    layout="wide",
    initial_sidebar_state="expanded"
)
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

# Carica dati
df = load_data()

# Sidebar per selezione venue
with st.sidebar:
    st.header(":satellite: Venue Selection")
    venues = df[col_venue].dropna().unique().tolist()
    venues.sort()
    selection = st.selectbox("Choose Venue:", ["All"] + venues)

# Filtra dati
df_filtered = df if selection == "All" else df[df[col_venue] == selection]

# Verifica colonne
missing = {col_bx, col_ao, col_aq} - set(df_filtered.columns)
if missing:
    st.error(f"Mancano queste colonne nel foglio '{SHEET}': {missing}")
    st.stop()

# Prepara dati per il plot
df_clean = df_filtered.dropna(subset=[col_bx, col_ao, col_aq]).copy()
df_clean["center"] = pd.to_numeric(df_clean[col_bx], errors="coerce")
df_clean["width_mhz"] = pd.to_numeric(df_clean[col_ao], errors="coerce") / 1000.0
df_clean["height_w"] = pd.to_numeric(df_clean[col_aq], errors="coerce")
plot_df = df_clean.dropna(subset=["center", "width_mhz", "height_w"])

if plot_df.empty:
    st.error("Nessun dato valido per il plotting.")
else:
    # Calcola limiti dinamici
    left_edges = plot_df["center"] - plot_df["width_mhz"] / 2
    right_edges = plot_df["center"] + plot_df["width_mhz"] / 2
    min_x, max_x = left_edges.min(), right_edges.max()
    max_y = plot_df["height_w"].max()
    dx = (max_x - min_x) * 0.05
    dy = max_y * 0.05

    # Usa un trace Bar per prestazioni migliori rispetto a shapes
    fig = go.Figure(
        go.Bar(
            x=plot_df["center"],
            y=plot_df["height_w"],
            width=plot_df["width_mhz"],
            marker_color="RoyalBlue",
            opacity=0.7,
            marker_line_color="White",
            marker_line_width=1.5,
            base=0
        )
    )
    fig.update_layout(
        xaxis=dict(
            range=[min_x - dx, max_x + dx],
            title=dict(text="Frequenza (MHz)", font=dict(size=20)),
            tickfont=dict(size=16)
        ),
        yaxis=dict(
            range=[0, max_y + dy],
            title=dict(text="Potenza (W)", font=dict(size=20)),
            tickfont=dict(size=16)
        ),
        plot_bgcolor="#111111",
        paper_bgcolor="#111111",
        font_color="#EEEEEE",
        margin=dict(l=50, r=50, t=50, b=50),
        dragmode="zoom"
    )

    # Render interattivo con dimensioni adattive
    st.plotly_chart(fig, use_container_width=True, theme="streamlit")
