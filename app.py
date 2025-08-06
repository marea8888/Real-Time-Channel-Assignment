import streamlit as st
import pandas as pd
import gdown
import plotly.graph_objects as go
import plotly.express as px

# Configura pagina e tema
st.set_page_config(
    page_title="Realtime Frequency Plot",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Personalizzazione CSS dark e stile sidebar
dark_css = '''<style>
/* Sfondo pagina */
.reportview-container, .main, header, footer { background-color: #111111; color: #EEEEEE; }
/* Sidebar */
.stSidebar { background-color: #1f1f1f; }
/* Sidebar testi */
.stSidebar label, .stSidebar div, .stSidebar h2, .stSidebar h3 { color: #FFFFFF; }
/* Selectbox placeholder (selected) */
div[data-baseweb="select"] span {
    color: #FFFFFF;
}
/* Dropdown options */
div[role="option"] {
    background-color: #FFFFFF !important;
    color: #000000 !important;
}
/* Focused option */
div[role="option"][aria-selected="true"], div[role="option"]:hover {
    background-color: #ddd !important;
}
</style>'''
st.markdown(dark_css, unsafe_allow_html=True)

# Configurazione
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

# Sidebar selezioni
with st.sidebar:
    st.header(":calendar: Seleziona Periodo")
    periods = sorted(df[col_period].dropna().unique().tolist())
    default_idx = periods.index("Olympic") if "Olympic" in periods else 0
    period_sel = st.selectbox("License Period", periods, index=default_idx)

    st.markdown("---")
    st.header(":satellite: Seleziona Venue")
    df_period = df[df[col_period] == period_sel]
    venues = sorted(df_period[col_venue].dropna().unique().tolist())
    venue_sel = st.selectbox("Venue", ["All"] + venues)

    st.markdown("---")
    st.header(":busts_in_silhouette: Seleziona Stakeholder")
    df_venue = df_period if venue_sel == 'All' else df_period[df_period[col_venue] == venue_sel]
    stakeholders = sorted(df_venue[col_stake].dropna().unique().tolist())
    stake_sel = st.selectbox("Stakeholder", ["All"] + stakeholders)

# Filtro dati
df_filtered = df_venue if stake_sel == 'All' else df_venue[df_venue[col_stake] == stake_sel]

# Verifica colonne
required = {col_bx, col_ao, col_aq, col_request, col_period}
missing = required - set(df_filtered.columns)
if missing:
    st.error(f"Mancano colonne: {missing}")
    st.stop()

# Prepara dati
df_clean = df_filtered.dropna(subset=[col_bx, col_ao, col_aq, col_request]).copy()
df_clean['center'] = pd.to_numeric(df_clean[col_bx], errors='coerce')
df_clean['width_mhz'] = pd.to_numeric(df_clean[col_ao], errors='coerce') / 1000.0
df_clean['height_w'] = pd.to_numeric(df_clean[col_aq], errors='coerce')
df_clean['req_id'] = df_clean[col_request].astype(str)

# Funzione plot
def make_fig(data):
    left = data['center'] - data['width_mhz']/2
    right = data['center'] + data['width_mhz']/2
    min_x, max_x = left.min(), right.max()
    max_y = data['height_w'].max()
    dx, dy = (max_x-min_x)*0.05, max_y*0.05
    fig = go.Figure()
    stakes = data[col_stake].astype(str).unique()
    colors = px.colors.qualitative.Plotly
    for i, stkh in enumerate(stakes):
        grp = data[data[col_stake] == stkh]
        fig.add_trace(go.Bar(
            x=grp['center'], y=grp['height_w'], width=grp['width_mhz'], name=stkh,
            marker_color=colors[i % len(colors)], opacity=0.7, marker_line_color='white', marker_line_width=1,
            customdata=grp['req_id'], hovertemplate='Request ID: %{customdata}<br>Freq: %{x} MHz<br>Power: %{y} W<extra></extra>'
        ))
    fig.update_layout(
        barmode='overlay', dragmode='zoom',
        xaxis=dict(range=[min_x-dx, max_x+dx], title=dict(text='Frequenza (MHz)', font=dict(size=20)), tickfont=dict(size=16)),
        yaxis=dict(range=[0, max_y+dy], title=dict(text='Potenza (W)', font=dict(size=20)), tickfont=dict(size=16)),
        legend=dict(font=dict(color='white')), plot_bgcolor='#111111', paper_bgcolor='#111111', font_color='#EEEEEE',
        margin=dict(l=40, r=40, t=20, b=40)
    )
    return fig

# Visualizza grafico
if df_clean.empty:
    st.info("Nessun dato disponibile per la selezione.")
else:
    fig = make_fig(df_clean)
    st.plotly_chart(fig, use_container_width=True)
