import streamlit as st
import pandas as pd
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

# Carica dati originali
df = load_data()

df = df.copy()

# Sidebar di selezione
with st.sidebar:
    st.header("Seleziona Periodo")
    periods = ["Olympic", "Paralympic"]
    default_idx = 0
    period_sel = st.selectbox("License Period", periods, index=default_idx)

    st.markdown("---")
    st.header("Seleziona Venue")
    df = df[df[col_period] == period_sel]
    venues = sorted(df[col_venue].dropna().unique().tolist())
    venue_sel = st.selectbox("Venue", ["All"] + venues)
    if venue_sel != "All":
        df = df[df[col_venue] == venue_sel]

    st.markdown("---")
    st.header("Seleziona Stakeholder")
    stakeholders = sorted(df[col_stake].dropna().unique().tolist())
    stake_sel = st.selectbox("Stakeholder", ["All"] + stakeholders)
    if stake_sel != "All":
        df = df[df[col_stake] == stake_sel]

# Verifica colonne essenziali
required = {col_bx, col_ao, col_aq, col_request}
missing = required - set(df.columns)
if missing:
    st.error(f"Colonne mancanti: {missing}")
    st.stop()

# Prepara dati numerici
clean = df.dropna(subset=[col_bx, col_ao, col_aq, col_request]).copy()
clean['center'] = pd.to_numeric(clean[col_bx], errors='coerce')
clean['width_mhz'] = pd.to_numeric(clean[col_ao], errors='coerce') / 1000.0
clean['height_w'] = pd.to_numeric(clean[col_aq], errors='coerce')
clean['req_id'] = clean[col_request].astype(str)

# Funzione per generare il grafico dark con Plotly
def make_fig(data):
    # Calcolo dei bordi
    left = data['center'] - data['width_mhz'] / 2
    right = data['center'] + data['width_mhz'] / 2
    if left.empty or right.empty:
        return None
    min_x = left.min()
    max_x = right.max()
    max_y = data['height_w'].max()
    # Margini dinamici con fallback
    if max_x > min_x:
        dx = (max_x - min_x) * 0.05
    else:
        dx = 1
    if max_y > 0:
        dy = max_y * 0.05
    else:
        dy = 1

    fig = go.Figure()
    stakes = data[col_stake].astype(str).unique()
    palette = px.colors.qualitative.Dark24
    for i, stkh in enumerate(stakes):
        grp = data[data[col_stake] == stkh]
        fig.add_trace(go.Bar(
            x=grp['center'],
            y=grp['height_w'],
            width=grp['width_mhz'],
            name=stkh,
            marker_color=palette[i % len(palette)],
            opacity=0.8,
            marker_line_color='white',
            marker_line_width=1,
            customdata=grp['req_id'],
            hovertemplate='Request ID: %{customdata}<br>Freq: %{x} MHz<br>Power: %{y} W<extra></extra>'
        ))

    # Layout completamente dark
    fig.update_layout(
        template='plotly_dark',
        barmode='overlay',
        dragmode='zoom',
        plot_bgcolor='#111111',
        paper_bgcolor='#111111',
        font_color='#EEEEEE',
        xaxis=dict(
            range=[min_x - dx, max_x + dx],
            title='<b>Frequenza (MHz)</b>',
            title_font=dict(size=18),
            tickfont=dict(size=14),
            gridcolor='gray'
        ),
            tickfont=dict(size=14),
            gridcolor='gray'
        ),
        yaxis=dict(
            range=[0, max_y + dy],
            title='<b>Potenza (W)</b>',
            title_font=dict(size=18),
            tickfont=dict(size=14),
            gridcolor='gray'
        )',
            title_font=dict(size=18),
            tickfont=dict(size=14),
            gridcolor='gray'
        ),
        legend=dict(font=dict(color='#FFFFFF')),
        margin=dict(l=50, r=50, t=20, b=50)
    )
    return fig

# Visualizza grafico
def main():
    fig = make_fig(clean)
    if fig is None or clean.empty:
        st.info(f"Nessun dato disponibile per il periodo {period_sel}.")
    else:
        st.plotly_chart(fig, use_container_width=True)

main()
