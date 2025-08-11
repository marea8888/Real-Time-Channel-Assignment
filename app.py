import streamlit as st
import pandas as pd
import numpy as np
import gdown
import plotly.graph_objects as go
import plotly.express as px

# Page config
st.set_page_config(
    page_title="Realtime Frequency Plot",
    layout="wide",
    initial_sidebar_state="expanded"
)

# File & columns
FILE_ID_PREV = "1YRKlzJAfHfrcfzZyX2GnN35v1eSV4Mg-"  # previous version
FILE_ID_NEW  = "1TD2YStCrV79DrKz0GODaEpsZtyHb85uH"  # new version

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
def load_data(FILE_ID):
    url = f"https://drive.google.com/uc?id={FILE_ID}"
    gdown.download(url, OUTPUT_FILE, quiet=True)
    return pd.read_excel(OUTPUT_FILE, sheet_name=SHEET)

@st.cache_data(ttl=60)
def load_capacity():
    return pd.read_excel(OUTPUT_FILE, sheet_name=CAP_SHEET)

# Custom CSS
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

_df_NEW = load_data(FILE_ID_NEW)
_df_PREV = load_data(FILE_ID_PREV)
cap_df = load_capacity()

# Sidebar filters
with st.sidebar:
    st.header("🗓️ Select Period")
    st.selectbox("", ["Olympic", "Paralympic"], key="period_sel", index=0, label_visibility="collapsed")
    st.markdown("---")

    st.header("👥 Select Stakeholder")
    df_period = _df_NEW[_df_NEW[col_period] == st.session_state.period_sel]
    stakeholders = sorted(df_period[col_stake].dropna().astype(str).unique())
    st.selectbox("", ["All"] + stakeholders, key="stake_sel", index=0, label_visibility="collapsed")

    st.markdown("---")
    st.header("🎫 Select Ticket")
    df_stake = df_period if st.session_state.stake_sel == "All" else df_period[df_period[col_stake] == st.session_state.stake_sel]
    tickets = sorted(df_stake[col_ticket].dropna().astype(str).unique()) if col_ticket in df_stake.columns else []
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

# Apply filters for the new data version
filtered = _df_NEW[_df_NEW[col_period] == st.session_state.period_sel]
if st.session_state.stake_sel != "All":
    filtered = filtered[filtered[col_stake] == st.session_state.stake_sel]
if "ticket_sel" in st.session_state and st.session_state.ticket_sel != "All":
    filtered = filtered[filtered[col_ticket].astype(str) == st.session_state.ticket_sel]
if st.session_state.service_sel:
    filtered = filtered[filtered[col_service].astype(str).isin(st.session_state.service_sel)]
if st.session_state.venue_sel:
    filtered = filtered[filtered[col_venue].isin(st.session_state.venue_sel)]

# Apply filters for the previous data version
filtered_prev = _df_PREV[_df_PREV[col_period] == st.session_state.period_sel]
if st.session_state.stake_sel != "All":
    filtered_prev = filtered_prev[filtered_prev[col_stake] == st.session_state.stake_sel]
if "ticket_sel" in st.session_state and st.session_state.ticket_sel != "All":
    filtered_prev = filtered_prev[filtered_prev[col_ticket].astype(str) == st.session_state.ticket_sel]
if st.session_state.service_sel:
    filtered_prev = filtered_prev[filtered_prev[col_service].astype(str).isin(st.session_state.service_sel)]
if st.session_state.venue_sel:
    filtered_prev = filtered_prev[filtered_prev[col_venue].isin(st.session_state.venue_sel)]

# Prepare data
required = {col_bx, col_ao, col_aq, col_request}
if required - set(filtered.columns):
    st.error(f"Missing columns: {required - set(filtered.columns)}")
    st.stop()

clean = filtered.dropna(subset=[col_ao, col_aq, col_request]).copy()
clean['center'] = pd.to_numeric(clean[col_bx], errors='coerce')
clean['width_mhz'] = pd.to_numeric(clean[col_ao], errors='coerce') / 1000.0
clean['power_dBm'] = 10 * np.log10(pd.to_numeric(clean[col_aq], errors='coerce') * 1000)
clean['req_id'] = clean[col_request].astype(str)

# Calculate assigned and not assigned counts for both versions
assigned_count_prev = int(filtered_prev[col_bx].notna().sum())
assigned_count_new = int(filtered[col_bx].notna().sum())
not_assigned_count_prev = int(filtered_prev[col_bx].isna().sum())
not_assigned_count_new = int(filtered[col_bx].isna().sum())

# Function to create the pie chart comparing previous and new versions with delta
def stats_fig(df_all, assigned_count_prev, assigned_count_new, not_assigned_count_prev, not_assigned_count_new):
    is_mod = df_all[col_pnrf].astype(str).str.strip().eq("MoD") if col_pnrf in df_all.columns else pd.Series(False, index=df_all.index)
    mod_coord_count = int(is_mod.sum())
    base = df_all.loc[~is_mod]
    
    # Calculate the delta for "ASSIGNED" and "NOT ASSIGNED"
    delta_assigned = assigned_count_new - assigned_count_prev
    delta_not_assigned = not_assigned_count_new - not_assigned_count_prev

    stats = pd.DataFrame({
        'Status': ['ASSIGNED', 'NOT ASSIGNED', 'MoD COORDINATION'],
        'Count': [assigned_count_new, not_assigned_count_new, mod_coord_count],
        'Delta': [
            f"+{delta_assigned}" if delta_assigned > 0 else f"{delta_assigned}",
            f"+{delta_not_assigned}" if delta_not_assigned > 0 else f"{delta_not_assigned}",
            ""
        ]
    })

    fig = px.pie(
        stats,
        names='Status', values='Count', color='Status', hole=0.6, template='plotly',
        color_discrete_map={
            'ASSIGNED': '#2ECC71',
            'NOT ASSIGNED': '#E74C3C',
            'MoD COORDINATION': '#F1C40F'
        }
    )

    # Remove the text inside the figure and show only the percentages
    fig.update_traces(
        textinfo='percent',  # Only show percentages
        texttemplate='%{percent:.1%}',  # Show percentage only
        pull=[0.1] * len(stats),  # Add a little space between the slices
        marker=dict(line=dict(color='#FFF', width=2))  # White borders
    )

    # Layout configuration without the title and with the legend
    fig.update_layout(
        margin=dict(l=20, r=20, t=20, b=20),  # Remove margins
        legend=dict(
            title='',  # No title for the legend
            orientation='h',  # Horizontal legend
            x=0.5, xanchor='center',  # Center the legend
            y=1.1, yanchor='bottom',  # Place the legend above the chart
            font=dict(size=14)  # Set the font size for the legend
        ),
        showlegend=True,  # Show the legend
        plot_bgcolor='white',  # Set the plot background to white
        paper_bgcolor='white'  # Set the paper background to white
    )

    return fig

def build_occupancy_chart(clean_df, cap_df):
    assigned_bw = clean_df.groupby(col_venue)["width_mhz"].sum()
    venues_list = assigned_bw.index.tolist()
    usage_list = []
    cap_selected = cap_df[cap_df["Venue"].isin(venues_list)].copy()
    for _, r in cap_selected.iterrows():
        venue = r['Venue']
        f_from = float(r['Freq. From [MHz]'])
        f_to = float(r['Freq. To [MHz]'])
        tot = float(r['Tot MHz'])
        assigns = clean_df[clean_df[col_venue] == venue]
        overlaps = []
        for _, a in assigns.iterrows():
            left = a['center'] - a['width_mhz']/2
            right = a['center'] + a['width_mhz']/2
            start = max(left, f_from)
            end = min(right, f_to)
            if end > start:
                overlaps.append((start, end))
        overlaps_sorted = sorted(overlaps, key=lambda x: x[0])
        merged = []
        for interval in overlaps_sorted:
            if not merged or interval[0] > merged[-1][1]:
                merged.append(list(interval))
            else:
                merged[-1][1] = max(merged[-1][1], interval[1])
        assigned_overlap = sum(end - start for start, end in merged)
        occupancy_pct = (assigned_overlap / tot * 100) if tot > 0 else 0
        usage_list.append({'Venue': venue, 'Range': f"{f_from}-{f_to} MHz", 'Occupancy': occupancy_pct})
    usage_df = pd.DataFrame(usage_list)
    if not usage_df.empty and 'Occupancy' in usage_df.columns:
        usage_df = usage_df[usage_df['Occupancy'] > 0]
    if usage_df.empty:
        return None
    occ_values = usage_df['Occupancy'].astype(float).fillna(0).tolist()
    labels = [f"{row['Venue']} ({row['Range']})" for _, row in usage_df.iterrows()]
    fig2 = go.Figure(go.Bar(x=occ_values, y=labels, orientation='h',
                            marker=dict(color=occ_values, colorscale='RdYlGn_r', cmin=0, cmax=100,
                                        colorbar=dict(title='Occupancy %', thickness=15, lenmode='fraction', len=0.75)),
                            text=[f"{v:.1f}%" for v in occ_values], textposition='outside'))
    fig2.update_layout(xaxis=dict(visible=False), yaxis_title='', template='plotly',
                       plot_bgcolor='white', paper_bgcolor='white', font_color='black',
                       margin=dict(l=100, r=50, t=20, b=50))
    return fig2

def make_fig(data):
    if data.empty: return None
    left = data['center'] - data['width_mhz']/2
