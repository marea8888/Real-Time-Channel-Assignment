import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ======================
# Load Data from Google Drive
# ======================
@st.cache_data
def load_data_from_gdrive(file_id):
    url = f"https://drive.google.com/uc?id={file_id}"
    return pd.read_excel(url)

# File IDs
FILE_ID_PREV = "1YRKlzJAfHfrcfzZyX2GnN35v1eSV4Mg-"  # previous version
FILE_ID_NEW  = "1TD2YStCrV79DrKz0GODaEpsZtyHb85uH"  # new version

# Load both versions
df_prev = load_data_from_gdrive(FILE_ID_PREV)
df_new  = load_data_from_gdrive(FILE_ID_NEW)

# ======================
# Sidebar Filters
# ======================
st.sidebar.header("Filters")

# Stakeholder filter
stakeholders = ["All"] + sorted(df_new["Stakeholder"].dropna().unique().tolist())
selected_stakeholder = st.sidebar.selectbox("Select Stakeholder", stakeholders)

# Ticket filter (FG column)
tickets = ["All"] + sorted(df_new["FG"].dropna().unique().tolist())
selected_ticket = st.sidebar.selectbox("Select Ticket (FG)", tickets)

def apply_filters(df):
    filtered = df.copy()
    if selected_stakeholder != "All":
        filtered = filtered[filtered["Stakeholder"] == selected_stakeholder]
    if selected_ticket != "All":
        filtered = filtered[filtered["FG"] == selected_ticket]
    return filtered

df_prev_f = apply_filters(df_prev)
df_new_f  = apply_filters(df_new)

# ======================
# Function to calculate counts from raw filtered data
# ======================
def calc_counts(df):
    mod_df = df[df["PNRF"] == "MoD"]
    non_mod_df = df[df["PNRF"] != "MoD"]
    assigned_count = len(non_mod_df[non_mod_df["Assigned Frequency"].notna()])
    not_assigned_count = len(non_mod_df[non_mod_df["Assigned Frequency"].isna()])
    mod_count = len(mod_df)
    return assigned_count, not_assigned_count, mod_count

assigned_prev, not_assigned_prev, mod_prev = calc_counts(df_prev_f)
assigned_new, not_assigned_new, mod_new    = calc_counts(df_new_f)

# ======================
# Calculate gaps
# ======================
gap_assigned = assigned_new - assigned_prev
gap_not_assigned = not_assigned_new - not_assigned_prev
gap_mod = mod_new - mod_prev

# ======================
# Pie Chart
# ======================
labels = ["Assigned", "Not Assigned", "MoD Coordination"]
values = [assigned_new, not_assigned_new, mod_new]
colors = ["#2ca02c", "#d62728", "#ffcc00"]  # green, red, yellow
gaps = [gap_assigned, gap_not_assigned, gap_mod]

custom_text = [
    f"{label}: {val} ({val/sum(values)*100:.1f}%)<br>Δ {gap:+d}"
    for label, val, gap in zip(labels, values, gaps)
]

fig_pie = go.Figure(data=[go.Pie(
    labels=labels,
    values=values,
    text=custom_text,
    textinfo="text",
    textposition="inside",
    marker=dict(colors=colors, line=dict(color="#000000", width=1)),
    hole=0.4
)])
fig_pie.update_layout(
    title="Assignment Status (New Version) with Gap vs Previous",
    title_x=0.5,
    font=dict(size=14),
    margin=dict(t=50, b=20, l=20, r=20),
    showlegend=False
)
st.plotly_chart(fig_pie, use_container_width=True)

# ======================
# Spectrum Plot
# ======================
if not df_new_f.empty:
    df_plot = df_new_f[df_new_f["PNRF"] != "MoD"].copy()
    df_plot["Assigned"] = df_plot["Assigned Frequency"].notna()

    fig_spectrum = px.scatter(
        df_plot,
        x="Assigned Frequency",
        y="Stakeholder",
        color="Assigned",
        color_discrete_map={True: "#2ca02c", False: "#d62728"},
        title="Spectrum View (New Version)",
        labels={"Assigned Frequency": "Frequency (MHz)", "Stakeholder": "Stakeholder"}
    )

    # Grid ON
    fig_spectrum.update_xaxes(showgrid=True, gridcolor="LightGray", zeroline=False)
    fig_spectrum.update_yaxes(showgrid=True, gridcolor="LightGray", zeroline=False)

    st.plotly_chart(fig_spectrum, use_container_width=True)
else:
    st.info("No data available for selected filters.")
