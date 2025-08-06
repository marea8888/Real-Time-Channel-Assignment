import streamlit as st
import pandas as pd
import gdown
import plotly.graph_objects as go
import plotly.express as px

# Configura pagina senza tema dark globale
st.set_page_config(
    page_title="Realtime Frequency Plot",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configurazione file e colonne
FILE_ID     = "1wlZmgpW0SGpbqEyt_b5XYT8lXgQUTYmo"
OUTPUT_FILE = "frequenze.xlsx"
SHEET       = "ALL NP"

col_bx      = "Attributed Frequency TX (MHz)"
col_ao      = "Channel Bandwidth (kHz)"
col_aq      = "Transmission Power (W)"
col_venue   = "Venue Code"
col_stake   = "Stakeholder ID"
col_request = "Request ID"
col_period  = "License Period"

@st.cache_data(ttl=60)
def load_data():
    url = f"https://drive.google.com/uc?id={FILE_ID}"
    gdown.download(url, OUTPUT_FILE, quiet=True)
    return pd.read_excel(OUTPUT_FILE, sheet_name=SHEET)

# Carica dati
 df = load_data()

# Sidebar di selezione (tema light di default)
with st.sidebar:
    st.header("Seleziona Periodo")
    periods = sorted(df[col_period].dropna().unique().tolist())
    default_idx = periods.index("Olympic") if "Olympic" in periods else 0
    period_sel = st.selectbox("License Period", periods, index=default_idx)

    st.markdown("---")
    st.header("Seleziona Venue")
    df_period = df[df[col_period] == period_sel]
    venues = sorted(df_period[col_venue].dropna().unique().tolist())
    venue_sel = st.selectbox("Venue", ["All"] + venues)

    st.markdown("---")
    st.header("Seleziona Stakeholder")
    df_venue = df_period if venue_sel == 'All' else df_period[df_period[col_venue] == venue_sel]
    stakeholders = sorted(df_venue[col_stake].dropna().unique().tolist())
    stake_sel = st.selectbox("Stakeholder", ["All"] + stakeholders)

# Filtro dati in base a selezioni
 df_filtered = df_venue if stake_sel == 'All' else df_venue[df_venue[col_stake] == stake_sel]

# Verifica colonne essenziali
 required = {col_bx, col_ao, col_aq, col_request}
 missing = required - set(df_filtered.columns)
 if missing:
     st.error(f"Colonne mancanti: {missing}")
     st.stop()

# Prepara dati numerici
 df_clean = df_filtered.dropna(subset=[col_bx, col_ao, col_aq, col_request]).copy()
 df_clean['center'] = pd.to_numeric(df_clean[col_bx], errors='coerce')
 df_clean['width_mhz'] = pd.to_numeric(df_clean[col_ao], errors='coerce') / 1000.0
 df_clean['height_w'] = pd.to_numeric(df_clean[col_aq], errors='coerce')
 df_clean['req_id'] = df_clean[col_request].astype(str)

# Funzione per generare il grafico dark con Plotly
def make_fig(data):
    left = data['center'] - data['width_mhz']/2
    right = data['center'] + data['width_mhz']/2
    min_x, max_x = left.min(), right.max()
    max_y = data['height_w'].max()
    dx, dy = (max_x-min_x)*0.05, max_y*0.05

    fig = go.Figure()
    stakes = data[col_stake].astype(str).unique()
    palette = px.colors.qualitative.Dark24

    for i, stkh in enumerate(stakes):
        grp = data[data[col_stake] == stkh]
        fig.add_trace(go.Bar(
            x=grp['center'], y=grp['height_w'], width=grp['width_mhz'], name=stkh,
            marker_color=palette[i % len(palette)], opacity=0.8,
            marker_line_color='white', marker_line_width=1,
            customdata=grp['req_id'],
            hovertemplate='Request ID: %{customdata}<br>Freq: %{x} MHz<br>Power: %{y} W<extra></extra>'
        ))

    # Layout dark specifico solo al grafico
    fig.update_layout(
        template='plotly_dark',
        barmode='overlay', dragmode='zoom',
        xaxis=dict(range=[min_x-dx, max_x+dx], title='Frequenza (MHz)', title_font=dict(size=18), tickfont=dict(size=14)),
        yaxis=dict(range=[0, max_y+dy], title='Potenza (W)', title_font=dict(size=18), tickfont=dict(size=14)),
        legend=dict(font=dict(color='#FFFFFF')), 
        margin=dict(l=50, r=50, t=20, b=50),
    )
    return fig

# Visualizza g
