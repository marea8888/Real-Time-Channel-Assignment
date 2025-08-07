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
CAP_SHEET   = "Capacity NP-OLY"

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

@st.cache_data(ttl=60)
def load_capacity():
    return pd.read_excel(OUTPUT_FILE, sheet_name=CAP_SHEET)

# Custom CSS for multiselect chips
st.markdown(
    """
    <style>
    .stSidebar [data-baseweb="tag"] {
        background-color: #e0f7fa !important;
        color: #000 !important;
        border-radius: 4px !important;
        padding: 2px 6px !important;
        margin: 2px !important;
    }
    .stSidebar [data-baseweb="tag"][role="button"] svg {
        fill: #000 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Load dataframes
_df = load_data()
cap_df = load_capacity()

# Sidebar filters (English)
with st.sidebar:
    st.header("🗓️ Select Period")
    st.selectbox("", ["Olympic", "Paralympic"], key="period_sel", index=0, label_visibility="collapsed")
    st.markdown("---")
    st.header("👥 Select Stakeholder")
    df_period = _df[_df[col_period] == st.session_state.period_sel]
    stakeholders = sorted(df_period[col_stake].dropna().astype(str).unique())
    st.selectbox("", ["All"] + stakeholders, key="stake_sel", index=0, label_visibility="collapsed")
    st.markdown("---")
    st.header("🔧 Select Service")
    df_stake = df_period if st.session_state.stake_sel == "All" else df_period[df_period[col_stake] == st.session_state.stake_sel]
    services = sorted(df_stake[col_service].dropna().astype(str).unique())
    st.multiselect("", services, default=services, key="service_sel", label_visibility="collapsed")
    st.markdown("---")
    st.header("📍 Select Venue")
    df_service = df_stake if not st.session_state.service_sel else df_stake[df_stake[col_service].astype(str).isin(st.session_state.service_sel)]
    venues = sorted(df_service[col_venue].dropna().unique())
    st.multiselect("", venues, default=venues, key="venue_sel", label_visibility="collapsed")

# Apply filters
filtered = _df[_df[col_period] == st.session_state.period_sel]
if st.session_state.venue_sel:
    filtered = filtered[filtered[col_venue].isin(st.session_state.venue_sel)]
if st.session_state.service_sel:
    filtered = filtered[filtered[col_service].astype(str).isin(st.session_state.service_sel)]
if st.session_state.stake_sel != "All":
    filtered = filtered[filtered[col_stake] == st.session_state.stake_sel]

# Ensure columns
required = {col_bx, col_ao, col_aq, col_request}
if required - set(filtered.columns):
    st.error(f"Missing columns: {required - set(filtered.columns)}")
    st.stop()

# Prepare data
clean = filtered.dropna(subset=[col_ao, col_aq, col_request]).copy()
clean['center']    = pd.to_numeric(clean[col_bx], errors='coerce')
clean['width_mhz'] = pd.to_numeric(clean[col_ao], errors='coerce') / 1000
clean['power_dBm'] = 10 * np.log10(pd.to_numeric(clean[col_aq], errors='coerce') * 1000)
clean['req_id']    = clean[col_request].astype(str)

# Main plot

def make_fig(data):
    if data.empty: return None
    left = data['center'] - data['width_mhz']/2
    right = data['center'] + data['width_mhz']/2
    min_x, max_x = left.min(), right.max()
    min_y, max_y = data['power_dBm'].min(), data['power_dBm'].max()
    dx = max((max_x-min_x)*0.05,1)
    dy = max((max_y-min_y)*0.05,1)
    fig = go.Figure()
    palette = px.colors.qualitative.Dark24
    for i, stake in enumerate(sorted(data[col_stake].astype(str).unique())):
        grp = data[data[col_stake]==stake]
        fig.add_trace(go.Bar(
            x=grp['center'], y=grp['power_dBm'], width=grp['width_mhz'], name=stake,
            marker_color=palette[i%len(palette)], opacity=0.8,
            marker_line_color='white', marker_line_width=1,
            customdata=list(zip(grp['req_id'],grp[col_ao])),
            hovertemplate='Request ID: %{customdata[0]}<br>Freq: %{x} MHz<br>Bandwidth: %{customdata[1]} kHz<br>Power: %{y:.1f} dBm<extra></extra>'
        ))
    fig.update_layout(
        template='plotly_dark', barmode='overlay', dragmode='zoom',
        plot_bgcolor='#111', paper_bgcolor='#111', font_color='#FFF',
        xaxis=dict(range=[min_x-dx,max_x+dx],title=dict(text='<b>Frequency (MHz)</b>',font=dict(size=20,color='#FFF')),
                   tickfont=dict(size=14,color='#FFF'),showgrid=True,gridcolor='rgba(255,255,255,0.5)',gridwidth=1,
                   minor=dict(showgrid=True,gridcolor='rgba(255,255,255,0.2)',gridwidth=1),tickmode='auto'),
        yaxis=dict(range=[min_y-dy,max_y+dy],title=dict(text='<b>Power (dBm)</b>',font=dict(size=20,color='#FFF')),
                   tickfont=dict(size=14,color='#FFF'),showgrid=True,gridcolor='rgba(255,255,255,0.5)',gridwidth=1,
                   minor=dict(showgrid=True,gridcolor='rgba(255,255,255,0.2)',gridwidth=1),tickmode='auto'),
        legend=dict(font=dict(color='#FFF')),margin=dict(l=50,r=50,t=20,b=50)
    )
    return fig

# Stats pie

def stats_fig(df_all):
    total=len(df_all)
    ok=df_all[col_bx].notna().sum()
    ko=total-ok
    stats=pd.DataFrame({'Status':['ASSIGNED','NOT ASSIGNED'],'Count':[ok,ko]})
    fig=px.pie(stats,names='Status',values='Count',color='Status',hole=0.6,
               color_discrete_map={'ASSIGNED':'#2ECC71','NOT ASSIGNED':'#E74C3C'},template='plotly')
    fig.update_traces(textinfo='percent',texttemplate='%{percent:.1%} (%{value})',
                      textfont=dict(size=18),textposition='outside',pull=[0.1]*len(stats),
                      marker=dict(line=dict(color='#FFF',width=2)))
    fig.update_layout(margin=dict(l=20,r=20,t=20,b=20),
                      legend=dict(title='',orientation='h',x=0.5,xanchor='center',y=1.2,yanchor='bottom',font=dict(size=14)),
                      showlegend=True)
    return fig

# Display

def main_display():
    # Frequency spectrum
    fig = make_fig(clean)
    if fig:
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(f"No data for {st.session_state.period_sel}")
    st.markdown("---")
    # Layout: capacity chart 3/4 width, separator, pie chart 1/4 width
    assigned_bw = clean.groupby(col_venue)["width_mhz"].sum()
    venues_list = assigned_bw.index.tolist()
    col1, col_sep, col2 = st.columns([3, 0.02, 1])
    # Capacity chart on the left (3/4)
    with col1:
        usage_list = []
        cap_selected = cap_df[cap_df["Venue"].isin(venues_list)].copy()
        for _, r in cap_selected.iterrows():
            venue = r['Venue']
            f_from = float(r['Freq. From [MHz]'])
            f_to = float(r['Freq. To [MHz]'])
            tot = float(r['Tot MHz'])
            assigns = clean[clean[col_venue] == venue]
            # compute merged overlap length
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
        # Remove zero-occupancy entries
        if 'Occupancy' in usage_df.columns:
            usage_df = usage_df[usage_df['Occupancy'] > 0]
        # Build horizontal bar chart with gradient colors
        fig2 = go.Figure()
        # Compute color for each bar based on Usage%: 0%->green,100%->red
        colors = []
        for usage in usage_df['Occupancy']:
            r = int(255 * usage / 100)
            g = int(255 * (1 - usage / 100))
            colors.append(f'rgb({r},{g},0)')
        # Add bars with gradient colors
        for (idx, row), color in zip(usage_df.iterrows(), colors):
            fig2.add_trace(go.Bar(
                x=[row['Occupancy']],
                y=[f"{row['Venue']} ({row['Range']})"],
                orientation='h',
                text=f"{row['Occupancy']:.1f}%",
                textposition='outside',
                marker_color=color
            ))
        
        fig2.update_layout(
            xaxis_title='Occupancy (%)',
            yaxis_title='',
            template='plotly',
            plot_bgcolor='white', paper_bgcolor='white', font_color='black',
            margin=dict(l=100, r=50, t=20, b=50),
            barmode='stack',
            showlegend=False
        )
        st.plotly_chart(fig2, use_container_width=True)
        # Separator
    with col_sep:
        st.markdown(
            """
            <div style="width:1px; background-color:#888; height:600px; margin:0 auto;"></div>
            """,
            unsafe_allow_html=True
        )
    # Pie chart on the right (1/4) on the right (1/4)
    with col2:
        pie = stats_fig(filtered)
        st.plotly_chart(pie, use_container_width=True)

    # List KO assignments under the charts
    st.markdown("---")
    st.subheader("Failed Assignments")
    # KO entries: those without an attributed frequency
    ko_df = filtered[filtered[col_bx].isna()].copy()
    # Display relevant technical columns
    st.dataframe(
        ko_df[[col_request, col_stake, col_service, col_venue, col_period, col_ao, col_aq]],
        use_container_width=True
    )

# Run
if __name__ == "__main__":
    main_display()
