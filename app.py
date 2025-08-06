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
plt_css = '''<style>
.reportview-container, .main, header, footer { background-color: #111111; color: #EEEEEE; }
.stSidebar { background-color: #1f1f1f; }
</style>'''
st.markdown(plt_css, unsafe_allow_html=True)

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
col_period  = "License Period"  # Olympic or Paralympic

@st.cache_data(ttl=60)
def load_data():
    url = f"https://drive.google.com/uc?id={FILE_ID}"
    gdown.download(url, OUTPUT_FILE, quiet=True)
    return pd.read_excel(OUTPUT_FILE, sheet_name=SHEET)

# Carica dati
df = load_data()

# Sidebar selezioni
with st.sidebar:
    st.header(":satellite: Seleziona Venue & Filtri")
    venues = sorted(df[col_venue].dropna().unique())
    venue_sel = st.selectbox("Venue:", ["All"] + venues)
    df_venue = df if venue_sel == 'All' else df[df[col_venue] == venue_sel]
    st.markdown("---")
    stakeholders = sorted(df_venue[col_stake].dropna().unique())
    stake_sel = st.selectbox(":busts_in_silhouette: Stakeholder:", ["All"] + stakeholders)

# Filtro base
df_base = df_venue if stake_sel == 'All' else df_venue[df_venue[col_stake] == stake_sel]

# Verifica colonne
required = {col_bx, col_ao, col_aq, col_request, col_period}
missing = required - set(df_base.columns)
if missing:
    st.error(f"Mancano colonne: {missing}")
    st.stop()

# Drop Na e conversione
df_clean = df_base.dropna(subset=[col_bx, col_ao, col_aq, col_request, col_period]).copy()
df_clean['center'] = pd.to_numeric(df_clean[col_bx], errors='coerce')
df_clean['width_mhz'] = pd.to_numeric(df_clean[col_ao], errors='coerce')/1000.0
df_clean['height_w'] = pd.to_numeric(df_clean[col_aq], errors='coerce')
df_clean['req_id'] = df_clean[col_request].astype(str)

# Funzione creazione plot
colors = px.colors.qualitative.Plotly
def make_fig(data):
    left = data['center'] - data['width_mhz']/2
    right = data['center'] + data['width_mhz']/2
    min_x, max_x = left.min(), right.max()
    max_y = data['height_w'].max()
    dx, dy = (max_x-min_x)*0.05, max_y*0.05
    fig = go.Figure()
    stakes = data[col_stake].astype(str).unique()
    for i, stkh in enumerate(stakes):
        grp = data[data[col_stake]==stkh]
        fig.add_trace(go.Bar(
            x=grp['center'], y=grp['height_w'], width=grp['width_mhz'], name=stkh,
            marker_color=colors[i%len(colors)], opacity=0.7, marker_line_color='white', marker_line_width=1,
            customdata=grp['req_id'], hovertemplate='Request ID: %{customdata}<br>Freq: %{x} MHz<br>Power: %{y} W<extra></extra>'
        ))
    fig.update_layout(
        barmode='overlay', dragmode='zoom',
        xaxis=dict(range=[min_x-dx, max_x+dx], title='Frequenza (MHz)', title_font=dict(size=18), tickfont=dict(size=14)),
        yaxis=dict(range=[0, max_y+dy], title='Potenza (W)', title_font=dict(size=18), tickfont=dict(size=14)),
        legend=dict(font=dict(color='white')), plot_bgcolor='#111111', paper_bgcolor='#111111', font_color='#EEEEEE',
        margin=dict(l=40,r=40,t=10,b=40)
    )
    return fig

# Split per periodo
df_olymp = df_clean[df_clean[col_period]=='Olympic']
df_para  = df_clean[df_clean[col_period]=='Paralympic']

# Display
col1, col2 = st.columns(2)
with col1:
    st.subheader('Spettro Olimpico')
    if not df_olymp.empty:
        st.plotly_chart(make_fig(df_olymp), use_container_width=True)
    else:
        st.info('Nessun dato Olympic')
with col2:
    st.subheader('Spettro Paralimpico')
    if not df_para.empty:
        st.plotly_chart(make_fig(df_para), use_container_width=True)
    else:
        st.info('Nessun dato Paralympic')
