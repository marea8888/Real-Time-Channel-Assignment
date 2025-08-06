import streamlit as st
import pandas as pd
import gdown
import matplotlib.pyplot as plt

# ——————————————————————————————
# Configura pagina e tema
st.set_page_config(
    page_title="Realtime Frequency Plot",
    layout="wide",
    initial_sidebar_state="expanded"
)
# Applica tema dark a Matplotlib
plt.style.use('dark_background')

# CSS personalizzato per pagina più scura e menu a tendina cool
dark_css = '''
<style>
/* Sfondo pagina */
.reportview-container, .main, header, footer {
    background-color: #111111;
    color: #EEEEEE;
}
/* Card e sidebar */
.stSidebar, .css-1d391kg {
    background-color: #1f1f1f;
}
/* Selectbox stile */
.css-1emrehy .css-1hwfws3 {
    background-color: #2a2a2a;
    color: #ffffff;
    border: 1px solid #444444;
    border-radius: 8px;
}
.css-1emrehy .css-1hwfws3:hover {
    border-color: #888888;
}
</style>
'''
st.markdown(dark_css, unsafe_allow_html=True)
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

# Selectbox in sidebar con stile
with st.sidebar:
    st.header(":satellite: Venue Selection")
    overall_venues = df[col_venue].dropna().unique().tolist()
    overall_venues.sort()
    selection = st.selectbox("Choose Venue:", ["All"] + overall_venues)

# Filtra dati
filtered_df = df if selection == "All" else df[df[col_venue] == selection]

# Verifica colonne
missing = {col_bx, col_ao, col_aq} - set(filtered_df.columns)
if missing:
    st.error(f"Mancano queste colonne nel foglio '{SHEET}': {missing}")
    st.stop()

# Prepara dati per il plot
freq = pd.to_numeric(filtered_df[col_bx], errors="coerce")
width = pd.to_numeric(filtered_df[col_ao], errors="coerce") / 1000.0
height = pd.to_numeric(filtered_df[col_aq], errors="coerce")
plot_df = pd.DataFrame({"center": freq, "width": width, "height": height}).dropna()

if plot_df.empty:
    st.error("Nessun dato valido per il plotting.")
else:
    # Calcola range dinamico
    left_edges  = plot_df['center'] - plot_df['width'] / 2
    right_edges = plot_df['center'] + plot_df['width'] / 2
    min_x, max_x = left_edges.min(), right_edges.max()
    min_y, max_y = 0, plot_df['height'].max()
    dx = (max_x - min_x) * 0.05
    dy = max_y * 0.05

    # Crea figura più compatta
    fig, ax = plt.subplots(figsize=(12, 6))
    fig.patch.set_facecolor('#111111')
    ax.set_facecolor('#111111')

    # Disegna rettangoli
    for _, row in plot_df.iterrows():
        c, w, h = row['center'], row['width'], row['height']
        left = c - w/2
        rect = plt.Rectangle((left, 0), w, h,
                              facecolor='#1f77b4', edgecolor='#ffffff', alpha=0.8,
                              linewidth=1.5)
        ax.add_patch(rect)

    ax.set_xlim(min_x - dx, max_x + dx)
    ax.set_ylim(min_y, max_y + dy)
    ax.set_xlabel("Frequenza (MHz)", color='#cccccc')
    ax.set_ylabel("Potenza (W)", color='#cccccc')
    ax.tick_params(colors='#cccccc')
    for spine in ax.spines.values(): spine.set_color('#555555')

    # Sovrapponi testo con stile
    title = "All Venues" if selection == "All" else selection
    ax.text(0.02, 0.98, f"{title}", color='#ffffff', fontsize=14,
            transform=ax.transAxes, va='top', ha='left', backgroundcolor='#333333')

    # Visualizza grafico
    st.pyplot(fig, use_container_width=True)
