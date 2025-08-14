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

# Nomi colonne (devono combaciare con il file)
COL_BX       = "Attributed Frequency TX (MHz)"   # frequenza centrale
COL_AO       = "Channel Bandwidth (kHz)"         # larghezza canale
COL_AQ       = "Transmission Power (W)"          # potenza
COL_VENUE    = "Venue Code"
COL_STAKE    = "Stakeholder ID"
COL_REQUEST  = "Request ID"
COL_PERIOD   = "License Period"
COL_FINAL    = "FINAL Status"  # opzionale

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

    left  = data["center"] - data["width_mhz"]/2
    right = data["center"] + data["width_mhz"]/2
    min_x, max_x = float(left.min()), float(right.max())
    min_y, max_y = float(data["power_dBm"].min()), float(data["power_dBm"].max())
    dx = max((max_x - min_x) * 0.05, 1.0)
    dy = max((max_y - min_x) * 0.05, 1.0) if (max_y - min_y) != 0 else 1.0

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
        fig.add_trace(go.Bar(
            x=data["center"], y=data["power_dBm"], width=data["width_mhz"], name="Assignments",
            opacity=0.85, marker_line_color='white', marker_line_width=1
        ))

    fig.update_layout(
        template='plotly_dark', barmode='overlay', dragmode='zoom',
        plot_bgcolor='#111', paper_bgcolor='#111', font_color='#FFF',
        xaxis=dict(range=[min_x - dx, max_x + dx], showgrid=True, gridcolor='rgba(255,255,255,0.5)', gridwidth=1,
                   minor=dict(showgrid=True, gridcolor='rgba(255,255,255,0.2)', gridwidth=1),
                   title=dict(text='<b>Frequency (MHz)</b>', font=dict(size=18, color='#FFF'))),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.5)', gridwidth=1,
                   minor=dict(showgrid=True, gridcolor='rgba(255,255,255,0.2)', gridwidth=1),
                   title=dict(text='<b>Power (dBm)</b>', font=dict(size=18, color='#FFF'))),
        legend=dict(font=dict(color='#FFF'))
    )
    return fig

def make_status_pies(df):
    """Primo pie: Assigned vs Not Assigned.
       Secondo pie: FINAL Status calcolato SOLO sui NOT ASSIGNED.
    """
    if df.empty:
        return None, None

    # Pie principale: Assigned vs Not Assigned
    assigned_count     = int(df[COL_BX].notna().sum()) if available(df, COL_BX) else 0
    not_assigned_count = int(df.shape[0] - assigned_count)

    stats = pd.DataFrame(
        {"Status": ["ASSIGNED", "NOT ASSIGNED"], "Count": [assigned_count, not_assigned_count]}
    )

    pie = px.pie(
        stats, names="Status", values="Count", hole=0.6, template="plotly",
        color="Status", color_discrete_map={"ASSIGNED": "#2ECC71", "NOT ASSIGNED": "#E74C3C"}
    )
    pie.update_traces(
        textinfo='percent', texttemplate='%{percent:.1%} (%{value})',
        textfont=dict(size=16), textposition='outside',
        marker=dict(line=dict(color='#FFF', width=2))
    )
    pie.update_layout(
        margin=dict(l=20, r=20, t=20, b=20),
        legend=dict(title='', orientation='h', x=0.5, xanchor='center', y=1.15, yanchor='bottom', font=dict(size=14)),
        showlegend=True
    )

    # Secondo pie: SOLO per NOT ASSIGNED
    final_pie = None
    if available(df, COL_FINAL) and available(df, COL_BX):
        not_assigned_df = df[df[COL_BX].isna()].copy()
        if not not_assigned_df.empty:
            not_assigned_df[COL_FINAL] = not_assigned_df[COL_FINAL].fillna("Not Analysed")
            counts = not_assigned_df[COL_FINAL].value_counts()
            final_stats = pd.DataFrame({"Status": counts.index, "Count": counts.values})

            palette = px.colors.qualitative.Set1
            cmap = {status: palette[i % len(palette)] for i, status in enumerate(final_stats["Status"].unique())}

            final_pie = px.pie(
                final_stats, names="Status", values="Count", hole=0.6, template="plotly",
                color="Status", color_discrete_map=cmap
            )
            final_pie.update_traces(
                textinfo='percent', texttemplate='%{percent:.1%} (%{value})',
                textfont=dict(size=16), textposition='outside',
                marker=dict(line=dict(color='#FFF', width=2))
            )
            final_pie.update_layout(
                margin=dict(l=20, r=20, t=20, b=20),
                legend=dict(title='', orientation='h', x=0.5, xanchor='center', y=1.15, yanchor='bottom', font=dict(size=14)),
                showlegend=True
            )

    return pie, final_pie

# ----------------------------
# Custom CSS (sidebar tags)
# ----------------------------
st.markdown("""
    <style>
    .stSidebar [data-baseweb="tag"] {
        background-color: #e0f7fa !important;
        color: #000 !important;
        border-radius: 4px !important;
        padding: 2px 6px !important;
        margin: 2px !important;
    }
    .stSidebar [data-baseweb="tag"][role="button"] svg { fill: #000 !important; }
    </style>
""", unsafe_allow_html=True)

# ----------------------------
# Load
# ----------------------------
_df = load_data()

# ----------------------------
# Sidebar filters (ONLY Period → Venue → Stakeholder)
# ----------------------------
with st.sidebar:
    st.header("🗓️ Select Period")
    period_options = ["Olympic", "Paralympic"] if available(_df, COL_PERIOD) else []
    if period_options:
        default_idx = 0 if "Olympic" in period_options else 0
        period_sel = st.selectbox("", period_options, index=default_idx, key="period_sel", label_visibility="collapsed")
    else:
        period_sel = None
        st.info("Colonna 'License Period' non trovata. Mostro tutti i periodi.")

    st.markdown("---")

    # Venue FIRST
    venue_sel = None
    if available(_df, COL_VENUE):
        st.header("📍 Venue")
        df_scoped = _df.copy()
        if period_sel and available(df_scoped, COL_PERIOD):
            df_scoped = df_scoped[df_scoped[COL_PERIOD] == period_sel]
        venues = sorted(df_scoped[COL_VENUE].dropna().astype(str).unique())
        venue_sel = st.multiselect("", venues, default=venues, key="venue_sel", label_visibility="collapsed")

    st.markdown("---")

    # Stakeholder SECOND
    if available(_df, COL_STAKE):
        st.header("👥 Stakeholder")
        df_scoped = _df.copy()
        if period_sel and available(df_scoped, COL_PERIOD):
            df_scoped = df_scoped[df_scoped[COL_PERIOD] == period_sel]
        if venue_sel and available(df_scoped, COL_VENUE):
            df_scoped = df_scoped[df_scoped[COL_VENUE].astype(str).isin([str(x) for x in venue_sel])]
        stakeholders = sorted(df_scoped[COL_STAKE].dropna().astype(str).unique())
        stake_sel = st.multiselect("", stakeholders, default=stakeholders, key="stake_sel", label_visibility="collapsed")
    else:
        stake_sel = None

# ----------------------------
# Apply filters
# ----------------------------
filtered = _df.copy()

if period_sel and available(filtered, COL_PERIOD):
    filtered = filtered[filtered[COL_PERIOD] == period_sel]

if venue_sel and available(filtered, COL_VENUE):
    filtered = filtered[filtered[COL_VENUE].astype(str).isin([str(x) for x in venue_sel])]

if stake_sel and available(filtered, COL_STAKE):
    filtered = filtered[filtered[COL_STAKE].astype(str).isin([str(x) for x in stake_sel])]

# ----------------------------
# Dashboard order: Status → Map → Table → Spectrum
# ----------------------------
st.subheader("Dashboard")

tab_status, tab_map, tab_table, tab_spectrum = st.tabs(
    ["📊 Status", "🗺️ Map", "📋 Table", "📡 Spectrum"]
)

with tab_status:
    pie, final_pie = make_status_pies(filtered)
    c1, c2 = st.columns([1, 1])
    with c1:
        if pie is not None:
            st.plotly_chart(pie, use_container_width=True)
        else:
            st.info("Nessun dato per generare lo stato principale.")
    with c2:
        if final_pie is not None:
            st.plotly_chart(final_pie, use_container_width=True)
        else:
            st.info("Nessun dato 'FINAL Status' (solo per NOT ASSIGNED) disponibile.")

with tab_map:
    st.info("🗺️ Mappa in preparazione...")

with tab_table:
    st.markdown("### Dati filtrati")
    if filtered.empty:
        st.info("Nessuna riga corrisponde ai filtri selezionati.")
    else:
        st.dataframe(filtered, use_container_width=True, hide_index=True)
        csv = filtered.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Scarica CSV filtrato",
            data=csv,
            file_name="lan_assignments_filtered.csv",
            mime="text/csv",
            use_container_width=True
        )

with tab_spectrum:
    chart_df, missing = compute_chart_df(filtered)
    if missing:
        st.error(f"Colonne mancanti per lo spettro: {missing}")
    elif chart_df.empty:
        st.info("Nessun dato disponibile per i filtri selezionati.")
    else:
        fig = make_spectrum_fig(chart_df, color_by=COL_STAKE)
        st.plotly_chart(fig, use_container_width=True)
