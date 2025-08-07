import streamlit as st
import pandas as pd
import numpy as np
import gdown
import plotly.graph_objects as go
import plotly.express as px

# Configure page
st.set_page_config(
    page_title="Realtime Frequency Plot",
    layout="wide",
    initial_sidebar_state="expanded"
)

# File and column settings
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
col_service = "Service Tri Code"

@st.cache_data(ttl=60)
def load_data():
    url = f"https://drive.google.com/uc?id={FILE_ID}"
    gdown.download(url, OUTPUT_FILE, quiet=True)
    return pd.read_excel(OUTPUT_FILE, sheet_name=SHEET)

# Load data
_df = load_data()
df = _df.copy()

# Sidebar filters (in English)
with st.sidebar:
    st.header("🗓️ Select Period")
    periods = ["Olympic", "Paralympic"]
    st.selectbox("", periods, key="period_sel", index=0, label_visibility="collapsed")
    st.markdown("---")
    st.header("📍 Select Venue")
    df_period = _df[_df[col_period] == st.session_state.period_sel]
    venues = sorted(df_period[col_venue].dropna().unique())
    st.selectbox("", ["All"] + venues, key="venue_sel", index=0, label_visibility="collapsed")
    st.markdown("---")
    st.header("🔧 Select Service")
    df_ven = df_period if st.session_state.venue_sel == "All" else df_period[df_period[col_venue] == st.session_state.venue_sel]
    services = sorted(df_ven[col_service].dropna().astype(str).unique())
    st.selectbox("", ["All"] + services, key="service_sel", index=0, label_visibility="collapsed")
    st.markdown("---")
    st.header("👥 Select Stakeholder")
    df_serv = df_ven if st.session_state.service_sel == "All" else df_ven[df_ven[col_service].astype(str) == st.session_state.service_sel]
    stakeholders = sorted(df_serv[col_stake].dropna().astype(str).unique())
    st.selectbox("", ["All"] + stakeholders, key="stake_sel", index=0, label_visibility="collapsed")

# Apply filters
df = _df[_df[col_period] == st.session_state.period_sel]
if st.session_state.venue_sel != "All":
    df = df[df[col_venue] == st.session_state.venue_sel]
if st.session_state.service_sel != "All":
    df = df[df[col_service].astype(str) == st.session_state.service_sel]
if st.session_state.stake_sel != "All":
    df = df[df[col_stake] == st.session_state.stake_sel]

# Ensure necessary columns
required = {col_bx, col_ao, col_aq, col_request}
if required - set(df.columns):
    st.error(f"Missing columns: {required - set(df.columns)}")
    st.stop()

# Prepare data
clean = df.dropna(subset=[col_ao, col_aq, col_request]).copy()
clean['center']    = pd.to_numeric(clean[col_bx], errors='coerce')
clean['width_mhz'] = pd.to_numeric(clean[col_ao], errors='coerce') / 1000.0
clean['power_dBm'] = 10 * np.log10(pd.to_numeric(clean[col_aq], errors='coerce') * 1000)
clean['req_id']    = clean[col_request].astype(str)

# Main frequency spectrum plot
def make_fig(data):
    if data.empty:
        return None
    left = data['center'] - data['width_mhz'] / 2
    right = data['center'] + data['width_mhz'] / 2
    min_x, max_x = left.min(), right.max()
    min_y, max_y = data['power_dBm'].min(), data['power_dBm'].max()
    dx = max((max_x - min_x) * 0.05, 1)
    dy = max((max_y - min_y) * 0.05, 1)

    fig = go.Figure()
    palette = px.colors.qualitative.Dark24
    for i, stake in enumerate(sorted(data[col_stake].astype(str).unique())):
        grp = data[data[col_stake] == stake]
        fig.add_trace(go.Bar(
            x=grp['center'], y=grp['power_dBm'], width=grp['width_mhz'], name=stake,
            marker_color=palette[i % len(palette)], opacity=0.8,
            marker_line_color='white', marker_line_width=1,
            customdata=list(zip(grp['req_id'], grp[col_ao])),
            hovertemplate=(
                'Request ID: %{customdata[0]}<br>' +
                'Freq: %{x} MHz<br>' +
                'Bandwidth: %{customdata[1]} kHz<br>' +
                'Power: %{y:.1f} dBm<extra></extra>'
            )
        ))
    fig.update_layout(
        template='plotly_dark', barmode='overlay', dragmode='zoom',
        plot_bgcolor='#111111', paper_bgcolor='#111111', font_color='#FFFFFF',
        xaxis=dict(
            range=[min_x - dx, max_x + dx],
            title=dict(text='<b>Frequency (MHz)</b>', font=dict(size=20, color='#FFFFFF')),
            tickfont=dict(size=14, color='#FFFFFF'),
            showgrid=True, gridcolor='rgba(255,255,255,0.5)', gridwidth=1,
            minor=dict(showgrid=True, gridcolor='rgba(255,255,255,0.2)', gridwidth=1),
            tickmode='auto'
        ),
        yaxis=dict(
            range=[min_y - dy, max_y + dy],
            title=dict(text='<b>Power (dBm)</b>', font=dict(size=20, color='#FFFFFF')),
            tickfont=dict(size=14, color='#FFFFFF'),
            showgrid=True, gridcolor='rgba(255,255,255,0.5)', gridwidth=1,
            minor=dict(showgrid=True, gridcolor='rgba(255,255,255,0.2)', gridwidth=1),
            tickmode='auto'
        ),
        legend=dict(font=dict(color='#FFFFFF')), margin=dict(l=50, r=50, t=20, b=50)
    )
    return fig

# Pie chart ASSIGNED vs NOT ASSIGNED
def stats_fig(df_all):
    total = len(df_all)
    assigned = df_all[col_bx].notna().sum()
    not_assigned = total - assigned
    stats = pd.DataFrame({'Status': ['ASSIGNED', 'NOT ASSIGNED'], 'Count': [assigned, not_assigned]})
    color_map = {'ASSIGNED': '#2ECC71', 'NOT ASSIGNED': '#E74C3C'}
    fig = px.pie(
        stats,
        names='Status',
        values='Count',
        color='Status',
        hole=0.6,
        color_discrete_map=color_map,
        template='plotly'
    )
    # Show percent with absolute in parentheses, labels outside with connector lines
    fig.update_traces(
        textinfo='percent+value',
        texttemplate='%{percent:.1%} (%{value})',
        textfont=dict(size=18),
        textposition='outside',  # place labels outside
        pull=[0.1] * len(stats),
        marker=dict(line=dict(color='#FFFFFF', width=2))
    )
    # Legend above pie
    fig.update_layout(
        margin=dict(l=20, r=20, t=20, b=20),
        legend=dict(
            title='', orientation='h', x=0.5, xanchor='center', y=1.2, yanchor='bottom', font=dict(size=14)
        ),
        showlegend=True
    )
    return fig

# Display
def main_display():
    fig = make_fig(clean)
    if fig:
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(f"No data for {st.session_state.period_sel}")
    st.markdown("---")
    # Display pie chart on the left with space on the right
    col1, col2 = st.columns([1, 2])
    with col1:
        pie = stats_fig(df)
        st.plotly_chart(pie, use_container_width=True)
    with col2:
        st.empty()

# Run display
main_display() pie chart on the left with space on the right
    col1, col2 = st.columns([1, 2])
    with col1:
        pie = stats_fig(df)
        st.plotly_chart(pie, use_container_width=True)
    with col2:
        st.empty()

# Run display
main_display()
