import streamlit as st
import pandas as pd
import numpy as np
import gdown
import plotly.graph_objects as go
import plotly.express as px

# Page config
st.set_page_config(
    page_title="LAN Assignment",
    layout="wide",
    initial_sidebar_state="expanded"
)

# File & columns
FILE_ID     = "1y2VzcB93oEJlGxwjBvEIhIdStFooP9O_"
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
#col_ticket  = "FG"
#col_pnrf    = "PNRF"
#col_new_venue = "New venue code for OTH"
#col_new_service = "New service code for OTH"

@st.cache_data(ttl=60)
def load_data():
    url = f"https://drive.google.com/uc?id={FILE_ID}"
    gdown.download(url, OUTPUT_FILE, quiet=True)
    return pd.read_excel(OUTPUT_FILE, sheet_name=SHEET)

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

_df = load_data()

# Sidebar filters
with st.sidebar:
    st.header("🗓️ Select Period")
    period_sel = st.selectbox("", ["Olympic", "Paralympic"], key="period_sel", index=0, label_visibility="collapsed")
    st.markdown("---")

    st.header("👥 Select Stakeholder")
    df_period = _df[_df[col_period] == period_sel]
    stakeholders = sorted(df_period[col_stake].dropna().astype(str).unique())
    stake_sel = st.selectbox("", ["All"] + stakeholders, key="stake_sel", index=0, label_visibility="collapsed")

    st.markdown("---")
    st.header("📍 Select Venue")
    df_service = df_ticket if not service_sel else df_ticket[df_ticket[col_service].astype(str).isin(service_sel)]
    venues = sorted(df_service[col_venue].dropna().unique())
    venue_sel = st.multiselect("", venues, default=venues, key="venue_sel", label_visibility="collapsed")

# Apply filters
filtered = _df[_df[col_period] == period_sel]
if stake_sel != "All":
    filtered = filtered[filtered[col_stake] == stake_sel]
if venue_sel:
    filtered = filtered[filtered[col_venue].isin(venue_sel)]

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

def make_fig(data):
    if data.empty:  # Verifica che i dati non siano vuoti prima di creare il grafico
        return None
    left = data['center'] - data['width_mhz']/2
    right = data['center'] + data['width_mhz']/2
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
            hovertemplate='Request ID: %{customdata[0]}<br>Freq: %{x} MHz<br>Bandwidth: %{customdata[1]} kHz<br>Power: %{y:.1f} dBm<extra></extra>'
        ))
    fig.update_layout(
        template='plotly_dark', barmode='overlay', dragmode='zoom',
        plot_bgcolor='#111', paper_bgcolor='#111', font_color='#FFF',
        xaxis=dict(range=[min_x - dx, max_x + dx], showgrid=True, gridcolor='rgba(255,255,255,0.5)', gridwidth=1,
                   minor=dict(showgrid=True, gridcolor='rgba(255,255,255,0.2)', gridwidth=1),
                   title=dict(text='<b>Frequency (MHz)</b>', font=dict(size=20, color='#FFF'))),
        yaxis=dict(range=[min_y, max_y], showgrid=True, gridcolor='rgba(255,255,255,0.5)', gridwidth=1,
                   minor=dict(showgrid=True, gridcolor='rgba(255,255,255,0.2)', gridwidth=1),
                   title=dict(text='<b>Power (dBm)</b>', font=dict(size=20, color='#FFF'))),
        legend=dict(font=dict(color='#FFF'))
    )
    return fig

def stats_fig(df_all):
    fig = None
    FINAL_status_fig = None
    
    # Verifica se ci sono dati disponibili prima di generare i grafici
    if df_all.empty:
        return None, None  # Se i dati sono vuoti, non restituire grafici
    
    # Filtraggio delle righe "NOT ASSIGNED" per il diagramma principale
    is_mod = df_all[col_pnrf].astype(str).str.strip().eq("MoD") if col_pnrf in df_all.columns else pd.Series(False, index=df_all.index)
    mod_coord_count = int(is_mod.sum())
    base = df_all.loc[~is_mod]
    
    # Righe "NOT ASSIGNED" per il diagramma principale
    not_assigned_base = base[base[col_bx].isna()]
    
    assigned_count     = int(base[col_bx].notna().sum())
    not_assigned_count = int(not_assigned_base[col_bx].isna().sum())

    stats = pd.DataFrame({
        'Status': ['ASSIGNED', 'NOT ASSIGNED'],
        'Count':  [assigned_count, not_assigned_count]
    })

    fig = px.pie(
        stats,
        names='Status', values='Count', color='Status', hole=0.6, template='plotly',
        color_discrete_map={
            'ASSIGNED': '#2ECC71',
            'NOT ASSIGNED': '#E74C3C'
        }
    )
    fig.update_traces(
        textinfo='percent',
        texttemplate='%{percent:.1%} (%{value})',
        textfont=dict(size=18),
        textposition='outside',
        pull=[0.1]*len(stats),
        marker=dict(line=dict(color='#FFF', width=2))
    )
    fig.update_layout(
        margin=dict(l=20, r=20, t=20, b=20),
        legend=dict(title='', orientation='h', x=0.5, xanchor='center', y=1.2, yanchor='bottom', font=dict(size=14)),
        showlegend=True
    )

    # Second pie chart for FINAL Status of NOT ASSIGNED
    if not not_assigned_base.empty and 'FINAL Status' in not_assigned_base.columns:
        # Sostituire i NaN con "Not Analysed" per il FINAL Status
        not_assigned_base['FINAL Status'] = not_assigned_base['FINAL Status'].fillna('Not Analysed')
        
        # Calcolare la frequenza delle voci in FINAL Status per le righe "NOT ASSIGNED"
        FINAL_status_counts = not_assigned_base['FINAL Status'].value_counts()
        FINAL_status_stats = pd.DataFrame({
            'Status': FINAL_status_counts.index,
            'Count': FINAL_status_counts.values
        })

        FINAL_status_fig = px.pie(
            FINAL_status_stats,
            names='Status', values='Count', hole=0.6, template='plotly',
            color='Status', 
            color_discrete_map={status: px.colors.qualitative.Set1[i % len(FINAL_status_stats['Status'])] for i, status in enumerate(FINAL_status_stats['Status'].unique())}
        )
        FINAL_status_fig.update_traces(
            textinfo='percent',
            texttemplate='%{percent:.1%} (%{value})',
            textfont=dict(size=18),
            textposition='outside',
            marker=dict(line=dict(color='#FFF', width=2))
        )
        FINAL_status_fig.update_layout(
            margin=dict(l=20, r=20, t=20, b=20),
            legend=dict(title='', orientation='h', x=0.5, xanchor='center', y=1.2, yanchor='bottom', font=dict(size=14)),
            showlegend=True
        )

    return fig, FINAL_status_fig

def main_display():
    # First row: Spectrum plot
    fig = make_fig(clean)
    if fig is not None:
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(f"No data for {st.session_state.period_sel}")

    # Second row: Pie chart for main status on the left, FINAL Status pie chart on the right
    st.markdown("---")
    col1, col_sep, col2 = st.columns([3, 0.02, 3])  # Larger columns for the pie charts

    with col1:
        pie, FINAL_status_pie = stats_fig(filtered)
        if pie is not None:
            st.plotly_chart(pie, use_container_width=True)
        else:
            st.info("No data available for the selected filters.")

    with col2:
        if FINAL_status_pie is not None:
            st.plotly_chart(FINAL_status_pie, use_container_width=True)
        else:
            st.info("No FINAL Status data for the selected filters.")
        
if __name__ == "__main__":
    main_display()
