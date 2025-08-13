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
FILE_ID     = "1TD2YStCrV79DrKz0GODaEpsZtyHb85uH"
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
col_new_venue = "New venue code for OTH"
col_new_service = "New service code for OTH"

@st.cache_data(ttl=60)
def load_data():
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

_df = load_data()
cap_df = load_capacity()

# Step 1: Replace "OTH" values in "Venue Code" and "Service Tri Code" with their respective new values
_df[col_venue] = _df.apply(
    lambda row: row[col_new_venue] if row[col_venue] == "OTH" else row[col_venue],
    axis=1
)

_df[col_service] = _df.apply(
    lambda row: row[col_new_service] if row[col_service] == "OTH" else row[col_service],
    axis=1
)

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
    st.header("🎫 Select Ticket")
    df_stake = df_period if stake_sel == "All" else df_period[df_period[col_stake] == stake_sel]
    tickets = sorted(df_stake[col_ticket].dropna().astype(str).unique()) if col_ticket in df_stake.columns else []
    ticket_sel = st.selectbox("", ["All"] + tickets, key="ticket_sel", index=0, label_visibility="collapsed")

    st.markdown("---")
    st.header("🔧 Select Service")
    df_ticket = df_stake if ticket_sel == "All" else df_stake[df_stake[col_ticket].astype(str) == ticket_sel]
    services = sorted(df_ticket[col_service].dropna().astype(str).unique())
    service_sel = st.multiselect("", services, default=services, key="service_sel", label_visibility="collapsed")

    st.markdown("---")
    st.header("📍 Select Venue")
    df_service = df_ticket if not service_sel else df_ticket[df_ticket[col_service].astype(str).isin(service_sel)]
    venues = sorted(df_service[col_venue].dropna().unique())
    venue_sel = st.multiselect("", venues, default=venues, key="venue_sel", label_visibility="collapsed")

# Apply filters
filtered = _df[_df[col_period] == period_sel]
if stake_sel != "All":
    filtered = filtered[filtered[col_stake] == stake_sel]
if ticket_sel != "All":
    filtered = filtered[filtered[col_ticket].astype(str) == ticket_sel]
if service_sel:
    filtered = filtered[filtered[col_service].astype(str).isin(service_sel)]
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
        'Status': ['ASSIGNED', 'NOT ASSIGNED', 'MoD COORDINATION'],
        'Count':  [assigned_count, not_assigned_count, mod_coord_count]
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

    # Second pie chart for TMP Status of NOT ASSIGNED
    if not not_assigned_base.empty and 'TMP Status' in not_assigned_base.columns:
        # Sostituire i NaN con "Not Analysed" per il TMP Status
        not_assigned_base['TMP Status'] = not_assigned_base['TMP Status'].fillna('Not Analysed')
        
        # Calcolare la frequenza delle voci in TMP Status per le righe "NOT ASSIGNED"
        tmp_status_counts = not_assigned_base['TMP Status'].value_counts()
        tmp_status_stats = pd.DataFrame({
            'Status': tmp_status_counts.index,
            'Count': tmp_status_counts.values
        })

        tmp_status_fig = px.pie(
            tmp_status_stats,
            names='Status', values='Count', hole=0.6, template='plotly',
            color='Status', 
            color_discrete_map={status: px.colors.qualitative.Set1[i % len(tmp_status_stats['Status'])] for i, status in enumerate(tmp_status_stats['Status'].unique())}
        )
        tmp_status_fig.update_traces(
            textinfo='percent',
            texttemplate='%{percent:.1%} (%{value})',
            textfont=dict(size=18),
            textposition='outside',
            marker=dict(line=dict(color='#FFF', width=2))
        )
        tmp_status_fig.update_layout(
            margin=dict(l=20, r=20, t=20, b=20),
            legend=dict(title='', orientation='h', x=0.5, xanchor='center', y=1.2, yanchor='bottom', font=dict(size=14)),
            showlegend=True
        )

    return fig, tmp_status_fig

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

def main_display():
    # First row: Spectrum plot
    fig = make_fig(clean)
    if fig is not None:
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(f"No data for {st.session_state.period_sel}")

    # Second row: Pie chart for main status on the left, TMP Status pie chart on the right
    st.markdown("---")
    col1, col_sep, col2 = st.columns([3, 0.02, 3])  # Larger columns for the pie charts

    with col1:
        pie, tmp_status_pie = stats_fig(filtered)
        if pie is not None:
            st.plotly_chart(pie, use_container_width=True)
        else:
            st.info("No data available for the selected filters.")

    with col2:
        if tmp_status_pie is not None:
            st.plotly_chart(tmp_status_pie, use_container_width=True)
        else:
            st.info("No TMP Status data for the selected filters.")
    
    # Third row: Capacity plot
    st.markdown("---")
    occ_fig = build_occupancy_chart(clean, cap_df)
    if occ_fig is None:
        st.info("No capacity/occupancy data for the current filters.")
    else:
        st.plotly_chart(occ_fig, use_container_width=True)

    # Fourth row: KO table
    st.markdown("---")
    st.subheader("Failed Assignments")

    # After the charts, add the filter for TMP Status
    tmp_status_options = ['All'] + clean['TMP Status'].dropna().unique().tolist()
    selected_status = st.selectbox("", tmp_status_options)

    # Filter KO table based on TMP Status
    ko_df = filtered[filtered[col_bx].isna() & ~filtered[col_pnrf].str.strip().eq("MoD")].copy()

    if selected_status != 'All':
        ko_df = ko_df[ko_df['TMP Status'] == selected_status]

    # Selecting only the specified columns
    ko_df = ko_df[['Request ID', 'Service Tri Code', 'Venue Code', 'Usage Type', 'Transmission Type', 'Is Simplex',
                   'Tuning Range From', 'Tuning Range To', 'Channel Bandwidth (kHz)', 'Tuning Step (kHz)',
                   'Transmission Power (W)', 'Notes', 'Note ottimizzazione', 'IMD step', 'MiCo Comments']]

    if ko_df.empty:
        st.info("No failed assignments for the current filters.")
    else:
        st.dataframe(ko_df, use_container_width=True)

    # --- Static Stats on raw data ---
    st.markdown("---")
    
    # Filtriamo i KO
    ko_df = filtered[filtered[col_bx].isna() & ~filtered[col_pnrf].str.strip().eq("MoD")].copy()
    
    # Totale richieste per priorità
    total_per_priority = filtered.groupby('Priority Indicator per Stakeholder').size().reset_index(name='Total')
    
    # Conteggio KO per priorità
    ko_counts = ko_df['Priority Indicator per Stakeholder'].value_counts().reset_index()
    ko_counts.columns = ['Priority', 'Count']
    
    # Uniamo e calcoliamo la percentuale
    ko_counts = ko_counts.merge(total_per_priority, left_on='Priority', right_on='Priority Indicator per Stakeholder', how='left')
    ko_counts['Percentage'] = (ko_counts['Count'] / ko_counts['Total'] * 100).round(2)
    
    # Palette colori diversa per ogni barra
    palette = px.colors.qualitative.Set3
    colors = {p: palette[i % len(palette)] for i, p in enumerate(ko_counts['Priority'])}
    
    # Creiamo il grafico a barre senza colorbar
    fig_ko_priority = px.bar(
        ko_counts,
        x='Priority',
        y='Percentage',
        text='Count',  # numero assoluto sopra la barra
        labels={
            'Priority': 'Priority',
            'Percentage': '% NOT ASSIGNED'
        },
    )
    
    # Applichiamo colori diversi manualmente
    fig_ko_priority.update_traces(marker_color=[colors[p] for p in ko_counts['Priority']],
                                  texttemplate='%{text}', textposition='outside')
    
    # Layout
    fig_ko_priority.update_layout(
        xaxis_title='Priority',
        yaxis_title='% NOT ASSIGNED (per Priority)',
        showlegend=False  # niente legenda/colorbar
    )
    
    # Mostriamo il plot
    st.plotly_chart(fig_ko_priority, use_container_width=True)

if __name__ == "__main__":
    main_display()
