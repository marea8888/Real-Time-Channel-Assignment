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
FILE_ID     = "1YRKlzJAfHfrcfzZyX2GnN35v1eSV4Mg-"
OUTPUT_FILE = "frequenze.xlsx"
SHEET       = "ALL NP"
CAP_SHEET   = "Capacity NP-OLY"

col_bx      = "Attributed Frequency TX (MHz)"
col_ao      = "Channel Bandwidth (kHz)"
col_aq      = "Transmission Power (W)"
col_venue   = "Venue Code"
col_stake   = "Stakeholder ID"
col_request = "Request ID"
col_period  = "License Period"
col_service = "Service Tri Code"
col_ticket  = "FG"
col_pnrf    = "PNRF"

@st.cache_data(ttl=60)
def load_data():
    url = f"https://drive.google.com/uc?id={FILE_ID}"
    gdown.download(url, OUTPUT_FILE, quiet=True)
    return pd.read_excel(OUTPUT_FILE, sheet_name=SHEET)

_df = load_data()

# Sidebar filters
with st.sidebar:
    st.header("🗓️ Select Period")
    st.selectbox("", ["Olympic", "Paralympic"], key="period_sel", index=0, label_visibility="collapsed")
    st.markdown("---")

    st.header("👥 Select Stakeholder")
    df_period = _df[_df[col_period] == st.session_state.period_sel]
    stakeholders = sorted(df_period[col_stake].dropna().astype(str).unique())
    st.selectbox("", ["All"] + stakeholders, key="stake_sel", index=0, label_visibility="collapsed")
    st.markdown("---")

    st.header("🎫 Select Ticket")
    df_stake = df_period if st.session_state.stake_sel == "All" else df_period[df_period[col_stake] == st.session_state.stake_sel]
    tickets = sorted(df_stake[col_ticket].dropna().astype(str).unique())
    st.selectbox("", ["All"] + tickets, key="ticket_sel", index=0, label_visibility="collapsed")
    st.markdown("---")

    st.header("🔧 Select Service")
    df_ticket = df_stake if st.session_state.ticket_sel == "All" else df_stake[df_stake[col_ticket].astype(str) == st.session_state.ticket_sel]
    services = sorted(df_ticket[col_service].dropna().astype(str).unique())
    st.multiselect("", services, default=services, key="service_sel", label_visibility="collapsed")
    st.markdown("---")

    st.header("📍 Select Venue")
    df_service = df_ticket if not st.session_state.service_sel else df_ticket[df_ticket[col_service].astype(str).isin(st.session_state.service_sel)]
    venues = sorted(df_service[col_venue].dropna().unique())
    st.multiselect("", venues, default=venues, key="venue_sel", label_visibility="collapsed")

# Apply filters
filtered = _df[_df[col_period] == st.session_state.period_sel]
if st.session_state.stake_sel != "All":
    filtered = filtered[filtered[col_stake] == st.session_state.stake_sel]
if st.session_state.ticket_sel != "All":
    filtered = filtered[filtered[col_ticket].astype(str) == st.session_state.ticket_sel]
if st.session_state.service_sel:
    filtered = filtered[filtered[col_service].astype(str).isin(st.session_state.service_sel)]
if st.session_state.venue_sel:
    filtered = filtered[filtered[col_venue].isin(st.session_state.venue_sel)]

# Pie chart calculation
assigned_count = filtered[col_bx].notna().sum()
not_assigned_df = filtered[filtered[col_bx].isna()]
not_assigned_count = len(not_assigned_df)
mod_coord_count = not_assigned_df[not_assigned_df[col_pnrf] == "MoD"].shape[0]

stats_df = pd.DataFrame({
    'Status': ['ASSIGNED', 'NOT ASSIGNED', 'MoD COORDINATION'],
    'Count': [assigned_count, not_assigned_count - mod_coord_count, mod_coord_count]
})

fig_pie = px.pie(
    stats_df,
    names='Status',
    values='Count',
    color='Status',
    color_discrete_map={
        'ASSIGNED': '#2ECC71',
        'NOT ASSIGNED': '#E74C3C',
        'MoD COORDINATION': '#F1C40F'
    },
    hole=0.6,
    template='plotly'
)

fig_pie.update_traces(
    textinfo='percent',
    texttemplate='%{percent:.1%} (%{value})',
    textfont=dict(size=18),
    textposition='outside',
    pull=[0.1]*len(stats_df),
    marker=dict(line=dict(color='#FFF', width=2))
)

st.plotly_chart(fig_pie, use_container_width=True)
