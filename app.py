import streamlit as st
import pandas as pd
import numpy as np
import gdown
import plotly.graph_objects as go
import plotly.express as px

# Configura pagina
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
_df = load_data()
df = _df.copy()

# Sidebar selezione con memoria tramite session_state
with st.sidebar:
    # Periodo con icona e senza label della selectbox
    st.header("🗓️ Seleziona Periodo")
    periods = ["Olympic", "Paralympic"]
    period_sel = st.selectbox(
        label="",
        options=periods,
        index=periods.index(st.session_state.get('period_sel', 'Olympic')),
        key='period_sel',
        label_visibility="collapsed"
    )

    st.markdown("---")
    # Venue con icona e senza label della selectbox
    st.header("📍 Seleziona Venue")
    venues = sorted(_df[_df[col_period] == period_sel][col_venue].dropna().unique().tolist())
    venue_sel = st.selectbox(
        label="",
        options=["All"] + venues,
        index=(["All"] + venues).index(st.session_state.get('venue_sel', 'All')),
        key='venue_sel',
        label_visibility="collapsed"
    )

    st.markdown("---")
    # Service con icona e senza label della selectbox
    st.header("🔧 Seleziona Service")
    base_df = _df[(_df[col_period] == period_sel)]
    if venue_sel != 'All':
        base_df = base_df[base_df[col_venue] == venue_sel]
    services = sorted(base_df['Service Tri Code'].dropna().astype(str).unique().tolist())
    service_sel = st.selectbox(
        label="",
        options=["All"] + services,
        index=(["All"] + services).index(st.session_state.get('service_sel', 'All')),
        key='service_sel',
        label_visibility="collapsed"
    )

    st.markdown("---")
    # Stakeholder con icona e senza label della selectbox
    st.header("👥 Seleziona Stakeholder")
    df_base = base_df.copy()
    if service_sel != 'All':
        df_base = df_base[df_base['Service Tri Code'].astype(str) == service_sel]
    stakeholders = sorted(df_base[col_stake].dropna().astype(str).unique().tolist())
    stake_sel = st.selectbox(
        label="",
        options=["All"] + stakeholders,
        index=(["All"] + stakeholders).index(st.session_state.get('stake_sel', 'All')),
        key='stake_sel',
        label_visibility="collapsed"
    )

# Applica filtri in sequenza
df = _df.copy()
# Periodo
df = df[df[col_period] == st.session_state.period_sel]
# Venue
if st.session_state.venue_sel != 'All':
    df = df[df[col_venue] == st.session_state.venue_sel]
# Service
if st.session_state.service_sel != 'All':
    df = df[df['Service Tri Code'].astype(str) == st.session_state.service_sel]
# Stakeholder
if st.session_state.stake_sel != 'All':
    df = df[df[col_stake] == st.session_state.stake_sel]

# Verifica colonne
required = {col_bx, col_ao, col_aq, col_request}
missing = required - set(df.columns)
if missing:
    st.error(f"Colonne mancanti: {missing}")
    st.stop()

# Prepara dati
df_clean = df.dropna(subset=[col_bx, col_ao, col_aq, col_request]).copy()
df_clean['center']    = pd.to_numeric(df_clean[col_bx], errors='coerce')
df_clean['width_mhz']  = pd.to_numeric(df_clean[col_ao], errors='coerce') / 1000.0
# Calcola potenza in dBm
# P_dBm = 10*log10(P_W*1000)
df_clean['power_dBm']  = 10 * np.log10(pd.to_numeric(df_clean[col_aq], errors='coerce') * 1000)
df_clean['req_id']     = df_clean[col_request].astype(str)

# Funzione per generare il grafico dark
def make_fig(data):
    if data.empty:
        return None
    # Calcolo range
    left  = data['center'] - data['width_mhz'] / 2
    right = data['center'] + data['width_mhz'] / 2
    min_x, max_x = left.min(), right.max()
    min_y, max_y = data['power_dBm'].min(), data['power_dBm'].max()
    # Margini
    dx = max((max_x - min_x) * 0.05, 1)
    dy = max((max_y - min_y) * 0.05, 1)

    x_range = (max_x + dx) - (min_x - dx)

    fig = go.Figure()
    palette = px.colors.qualitative.Dark24
    # Barre per stakeholder
    for i, stake in enumerate(sorted(data[col_stake].astype(str).unique().tolist())):
        grp = data[data[col_stake] == stake]
        fig.add_trace(go.Bar(
            x=grp['center'],
            y=grp['power_dBm'],
            width=grp['width_mhz'],
            name=stake,
            marker_color=palette[i % len(palette)],
            opacity=0.8,
            marker_line_color='white',
            marker_line_width=1,
            customdata=list(zip(grp['req_id'], grp[col_ao])),
            hovertemplate=(
                'Request ID: %{customdata[0]}<br>' +
                'Freq: %{x} MHz<br>' +
                'Bandwidth: %{customdata[1]} kHz<br>' +
                'Power: %{y:.1f} dBm<extra></extra>'
            )
        ))
    # Layout dark con griglia primaria e secondaria sfocata
    fig.update_layout(
        template='plotly_dark',
        barmode='overlay',
        dragmode='zoom',
        plot_bgcolor='#111111',
        paper_bgcolor='#111111',
        font_color='#FFFFFF',
        xaxis=dict(
            range=[min_x - dx, max_x + dx],
            title=dict(text='<b>Frequency (MHz)</b>', font=dict(size=20, color='#FFFFFF')),
            tickfont=dict(size=14, color='#FFFFFF'),
            showgrid=True,
            gridcolor='rgba(255,255,255,0.5)',
            gridwidth=1,
            minor=dict(showgrid=True, gridcolor='rgba(255,255,255,0.2)', gridwidth=1),
            tickmode='auto'
        ),
        yaxis=dict(
            range=[min_y - dy, max_y],
            title=dict(text='<b>Power (dBm)</b>', font=dict(size=20, color='#FFFFFF')),
            tickfont=dict(size=14, color='#FFFFFF'),
            showgrid=True,
            gridcolor='rgba(255,255,255,0.5)',
            gridwidth=1,
            minor=dict(showgrid=True, gridcolor='rgba(255,255,255,0.2)', gridwidth=1),
            tickmode='auto'
        ),
        legend=dict(font=dict(color='#FFFFFF')),
        margin=dict(l=50, r=50, t=20, b=50)
    )
    return fig

# Visualizza grafico
def main():
    fig = make_fig(df_clean)
    if fig is None:
        st.info(f"Nessun dato disponibile per il periodo {period_sel}.")
    else:
        st.plotly_chart(fig, use_container_width=True)

main()
