# app.py
import streamlit as st
import pandas as pd
import numpy as np
import gdown
import plotly.graph_objects as go
import plotly.express as px

# ----------------------------
# Page config
# ----------------------------
st.set_page_config(
    page_title="LAN Assignment",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------------------
# Config: File & Columns
# ----------------------------
FILE_ID     = "1y2VzcB93oEJlGxwjBvEIhIdStFooP9O_"
OUTPUT_FILE = "frequenze.xlsx"
SHEET       = "ALL NP"

# Nomi colonne (usa quelli reali del file)
COL_BX       = "Attributed Frequency TX (MHz)"   # frequenza centrale
COL_AO       = "Channel Bandwidth (kHz)"         # larghezza canale
COL_AQ       = "Transmission Power (W)"          # potenza
COL_VENUE    = "Venue Code"
COL_STAKE    = "Stakeholder ID"
COL_REQUEST  = "Request ID"
COL_PERIOD   = "License Period"
COL_SERVICE  = "Service Tri Code"
COL_FINAL    = "FINAL Status"  # opzionale, se presente la uso per secondo pie

# ----------------------------
# Data loading
# ----------------------------
@st.cache_data(ttl=60)
def load_data():
    url = f"https://drive.google.com/uc?id={FILE_ID}"
    gdown.download(url, OUTPUT_FILE, quiet=True)
    df = pd.read_excel(OUTPUT_FILE, sheet_name=SHEET)
    return df

# ----------------------------
# Helpers
# ----------------------------
def available(df, col):
    return col in df.columns

def coerce_numeric(series):
    return pd.to_numeric(series, errors="coerce")

def compute_chart_df(df):
    """Prepara colonne numeriche per il grafico spettro, ignorando righe non valide."""
    req = [COL_BX, COL_AO, COL_AQ, COL_REQUEST]
    missing = [c for c in req if c not in df.columns]
    if missing:
        return pd.DataFrame(), missing

    tmp = df.dropna(subset=[COL_AO, COL_AQ, COL_REQUEST]).copy()
    tmp["center"]     = coerce_numeric(tmp[COL_BX])
    tmp["width_mhz"]  = coerce_numeric(tmp[COL_AO]) / 1000.0
    tmp["power_dBm"]  = 10 * np.log10(coerce_numeric(tmp[COL_AQ]) * 1000)
    tmp["req_id"]     = tmp[COL_REQUEST].astype(str)
    tmp = tmp.dropna(subset=["center", "width_mhz", "power_dBm"])
    return tmp, []

def make_spectrum_fig(data, color_by=COL_STAKE):
    if data.empty:
        return None
    # Range sicuri
    left  = data["center"] - data["width_mhz"]/2
    right = data["center"] + data["width_mhz"]/2
    min_x, max_x = float(left.min()), float(right.max())
    min_y, max_y = float(data["power_dBm"].min()), float(data["power_dBm"].max())
    dx = max((max_x - min_x) * 0.05, 1.0)
    dy = max((max_y - min_y) * 0.05, 1.0)

    fig = go.Figure()
    palette = px.colors.qualitative.Dark24

    if available(data, color_by):
        groups = sorted(data[color_by].astype(str).fillna("Unknown").unique())
        for i, g in enumerate(groups):
            grp = data[data[color_by].astype(str).fillna("Unknown") == g]
            fig.add_trace(go.Bar(
                x=grp["center"], y=grp["power_dBm"], width=grp["width_mhz"], name=str(g),
                marker_color=palette[i % len(palette)], opacity=0.85,
                marker_line_color='white', marker_line_width=1,
                customdata=list(zip(grp["req_id"], grp[COL_AO] if available(grp, COL_AO) else [None]*len(grp))),
                hovertemplate=(
                    'Request ID: %{customdata[0]}'
                    '<br>Freq: %{x} MHz'
                    '<br>Bandwidth: %{customdata[1]} kHz'
                    '<br>Power: %{y:.1f} dBm<extra></extra>'
                )
            ))
    else:
        # Nessun colore per gruppo
        fig.add_trace(go.Bar(
            x=data["center"], y=data["power_dBm"], width=data["width_mhz"], name="Assignments",
            opacity=0.85, marker_line_color='white', marker_line_width=1
        ))

    fig.update_layout(
        template='plotly_dark', barmode='overlay', dragmode='zoom',
        plot_bgcolor='#111', paper_bgcolor='#111', font_color='#FFF',
        xaxis=dict(range=[min_x - dx, max_x + dx], showgrid=True, gridcolor='rgba(255,255,255,0.5)', gridwidth=1,
                   minor=dict(showgrid=True, gridcolor='rgba(255,255,255,
