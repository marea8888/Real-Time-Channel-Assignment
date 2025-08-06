import streamlit as st
import pandas as pd
import gdown
import plotly.graph_objects as go
import plotly.express as px

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

col_bx       = "Attributed Frequency TX (MHz)"   # frequenza in MHz
col_ao       = "Channel Bandwidth (kHz)"         # ampiezza in kHz
col_aq       = "Transmission Power (W)"          # potenza in W
col_venue    = "Venue Code"                       # codice venue
col_stake    = "Stakeholder ID"                   # organizzazione
# ——————————————————————————————

@st.cache_data(ttl=60)
def load_data():
    url = f"https://drive.google.com/uc?id={FILE_ID}"
    gdown.download(url, OUTPUT_FILE, quiet=True)
    return pd.read_excel(OUTPUT_FILE, sheet_name=SHEET)

# Carica dati
df = load_data()

# Sidebar: selezione venue e stakeholder
with st.sidebar:
    st.header(":satellite: Seleziona Venue")
    venues = sorted(df[col_venue].dropna().unique().tolist())
    venue_sel = st.selectbox("Venue:", ["All"] + venues)
    
    df_venue = df if venue_sel == "All" else df[df[col_venue] == venue_sel]

    st.markdown("---")
    st.header(":busts_in_silhouette: Seleziona Organizzazione")
    stakeholders = sorted(df_venue[col_stake].dropna().unique().tolist())
    stake_sel = st.selectbox("Stakeholder:", ["All"] + stakeholders)

# Filtra dati in base alle selezioni
df_filtered = df_venue if stake_sel == "All" else df_venue[df_venue[col_stake] == stake_sel]

# Verifica colonne necessarie
required = {col_bx, col_ao, col_aq}
missing = required - set(df_filtered.columns)
if missing:
    st.error(f"Mancano colonne nel foglio '{SHEET}': {missing}")
    st.stop()

# Prepara dati numeric
df_clean = df_filtered.dropna(subset=[col_bx, col_ao, col_aq]).copy()
df_clean["center"] = pd.to_numeric(df_clean[col_bx], errors="coerce")
df_clean["width_mhz"] = pd.to_numeric(df_clean[col_ao], errors="coerce") / 1000.0
df_clean["height_w"] = pd.to_numeric(df_clean[col_aq], errors="coerce")
plot_df = df_clean.dropna(subset=["center","width_mhz","height_w"])

if plot_df.empty:
    st.error("Nessun dato valido per il plotting.")
else:
    # Calcola limiti dinamici
    left_edges = plot_df["center"] - plot_df["width_mhz"]/2
    right_edges = plot_df["center"] + plot_df["width_mhz"]/2
    min_x, max_x = left_edges.min(), right_edges.max()
    max_y = plot_df["height_w"].max()
    dx = (max_x - min_x) * 0.05
    dy = max_y * 0.05

    # Palette di colori per stakeholder
    uniq_stakes = plot_df[col_stake].astype(str).unique().tolist()
    colors = px.colors.qualitative.Plotly

    # Crea figura con tracce separate per stakeholder
    fig = go.Figure()
    for i, stake in enumerate(uniq_stakes):
        group = plot_df[plot_df[col_stake].astype(str) == stake]
        fig.add_trace(go.Bar(
            x=group["center"],
            y=group["height_w"],
            width=group["width_mhz"],
            name=stake,
            marker_color=colors[i % len(colors)],
            opacity=0.7,
            marker_line_color="White",
            marker_line_width=1
        ))

    # Layout
    fig.update_layout(
        barmode='overlay',
        xaxis=dict(range=[min_x-dx, max_x+dx], title=dict(text="Frequenza (MHz)", font=dict(size=18)), tickfont=dict(size=14)),
        yaxis=dict(range=[0, max_y+dy], title=dict(text="Potenza (W)", font=dict(size=18)), tickfont=dict(size=14)),
        plot_bgcolor="#111111", paper_bgcolor="#111111", font_color="#EEEEEE",
        margin=dict(l=40, r=40, t=20, b=40), dragmode="zoom"
    )

    # Mostra grafico
    st.plotly_chart(fig, use_container_width=True, theme="streamlit")
