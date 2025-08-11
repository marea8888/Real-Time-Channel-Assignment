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
        pie = stats_fig(filtered)[0]
        st.plotly_chart(pie, use_container_width=True)

    with col2:
        tmp_status_pie = stats_fig(filtered)[1]
        if tmp_status_pie is not None:
            st.plotly_chart(tmp_status_pie, use_container_width=True)
        else:
            st.info("No TMP Status data for NOT ASSIGNED requests.")
    
    # Add visual connection between the two pie charts
    st.markdown("""
    <div style="display: flex; justify-content: center; align-items: center; position: relative; top: -20px;">
        <!-- Arrow pointing from the first pie to the second -->
        <svg width="80" height="80">
            <line x1="0" y1="40" x2="80" y2="40" style="stroke:#FFFFFF;stroke-width:4" />
            <polygon points="80,40 75,35 75,45" style="fill:#FFFFFF" />
        </svg>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""<div style="text-align: center; color: white; font-size: 18px; margin-top: -20px;">
        <strong>Analysis of "NOT ASSIGNED" Requests</strong>
    </div>""", unsafe_allow_html=True)

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

    # Add a dropdown for filtering by TMP Status
    tmp_status_options = ['All', 'No Spectrum within the requested range', 'To Be Investigated', 'Contact stakeholder', 'Not Analysed']
    selected_status = st.selectbox("Filter by TMP Status", tmp_status_options)

    # Filter KO table based on TMP Status
    ko_df = filtered[filtered[col_bx].isna() & ~filtered[col_pnrf].str.strip().eq("MoD")].copy()

    if selected_status != 'All':
        ko_df = ko_df[ko_df['TMP Status'] == selected_status]

    if ko_df.empty:
        st.info("No failed assignments for the current filters.")
    else:
        st.dataframe(ko_df, use_container_width=True)
