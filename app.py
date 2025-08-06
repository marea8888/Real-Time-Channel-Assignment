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

col_bx       = "Attributed Frequency TX (MHz)"
col_ao       = "Channel Bandwidth (kHz)"
col_aq       = "Transmission Power (W)"
col_venue    = "Venue Code"
col_stake    = "Stakeholder ID"
# ——————————————————————————————

@st.cache_data(ttl=60)
def load_data():
    url = f'https://drive.google.com/uc?id={FILE_ID}'
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

# Filtra dati
filtered = df_venue if stake_sel == "All" else df_venue[df_venue[col_stake] == stake_sel]

# Verifica colonne
required = {col_bx, col_ao, col_aq}
missing = required - set(filtered.columns)
if missing:
    st.error(f"Mancano colonne: {missing}")
    st.stop()

# Prepara dati numeric
clean = filtered.dropna(subset=[col_bx, col_ao, col_aq]).copy()
clean['center'] = pd.to_numeric(clean[col_bx], errors='coerce')
clean['width_mhz'] = pd.to_numeric(clean[col_ao], errors='coerce') / 1000.0
clean['height_w'] = pd.to_numeric(clean[col_aq], errors='coerce')
plot_df = clean.dropna(subset=['center', 'width_mhz', 'height_w'])

if plot_df.empty:
    st.error("Nessun dato valido per il plotting.")
else:
    # Calcola limiti dinamici
    left = plot_df['center'] - plot_df['width_mhz'] / 2
    right = plot_df['center'] + plot_df['width_mhz'] / 2
    min_x, max_x = left.min(), right.max()
    max_y = plot_df['height_w'].max()
    dx = (max_x - min_x) * 0.05
    dy = max_y * 0.05

    # Palette di colori
    stakes = plot_df[col_stake].astype(str).unique().tolist()
    colors = px.colors.qualitative.Plotly

    # Figura
    fig = go.Figure()
    for idx, stake in enumerate(stakes):
        grp = plot_df[plot_df[col_stake].astype(str) == stake]
        fig.add_trace(go.Bar(
            x=grp['center'],
            y=grp['height_w'],
            width=grp['width_mhz'],
            name=stake,
            marker_color=colors[idx % len(colors)],
            opacity=0.7,
            marker_line_color='white',
            marker_line_width=1
        ))

    # Layout\    
    fig.update_layout(
        barmode='overlay',
        xaxis=dict(range=[min_x - dx, max_x + dx],
                   title=dict(text='Frequenza (MHz)', font=dict(size=20)),
                   tickfont=dict(size=16)),
        yaxis=dict(range=[0, max_y + dy],
                   title=dict(text='Potenza (W)', font=dict(size=20)),
                   tickfont=dict(size=16)),
        legend=dict(font=dict(color='white')),
        plot_bgcolor='#111111', paper_bgcolor='#111111', font_color='#EEEEEE',
        margin=dict(l=50, r=50, t=20, b=50),
        dragmode='zoom'
    )

    st.plotly_chart(fig, use_container_width=True)
