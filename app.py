import streamlit as st
import pandas as pd
import plotly.express as px
from scrapper import ProfileScraper
from storage import save_run
from analytics import (
    process_results_dataframe, 
    calculate_campaign_health, 
    generate_outreach_templates, 
    TARGET_BADGES
)

st.set_page_config(
    page_title="SkillTrack | GDG Campaign Manager",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ SkillTrack — Smart GDG Campaign Tracker")
st.caption("Organiser Dashboard for Google Skills Learn With Communities Campaign")

# Sidebar - Controls
st.sidebar.header("📁 Campaign Control")
uploaded_file = st.sidebar.file_uploader("Upload Profile CSV", type=["csv"])
recheck_btn = st.sidebar.button("Run Profile Verification")

if uploaded_file is not None:
    try:
        df_raw = pd.read_csv(uploaded_file)
    except Exception as e:
        st.error(f"Error reading CSV file: {e}")
        st.stop()

    url_col = "Google Skills Profile URL"
    
    if url_col not in df_raw.columns:
        st.error(f"Missing required column: `{url_col}` in uploaded CSV.")
    else:
        urls = df_raw[url_col].dropna().unique().tolist()
        st.sidebar.success(f"Loaded {len(urls)} profile URLs")

        if recheck_btn or "analysis_df" not in st.session_state:
            scraper = ProfileScraper(delay_seconds=0.3)
            progress_bar = st.progress(0)
            
            with st.spinner("Verifying profiles and analyzing skill badges..."):
                results = scraper.batch_process(urls, progress_callback=lambda p: progress_bar.progress(p))
                save_run(results)
                st.session_state["analysis_df"] = process_results_dataframe(results)
            progress_bar.empty()

        df = st.session_state["analysis_df"]
        health_info = calculate_campaign_health(df)
        templates = generate_outreach_templates(df)

        # TAB LAYOUT
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Campaign Dashboard", 
            "🎯 Smart Action & Priority", 
            "📢 Broadcast Templates",
            "🔍 Badge Gap Analyzer", 
            "📑 Report Generator"
        ])

        # TAB 1: OVERVIEW DASHBOARD (Features Health Score)
        with tab1:
            st.subheader("Campaign Performance & Health Overview")
            
            # Health Score Callout Box
            st.info(f"**Campaign Health Score:** {health_info['health_score']}% — Status: **{health_info['health_status']}**")

            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Total Participants", health_info["total"])
            c2.metric("Verified Profiles", len(df[df["Verification Status"] == "Verified"]))
            c3.metric("Completed (10/10)", health_info["completed"])
            c4.metric("Almost Completed (8-9)", health_info["almost"])
            c5.metric("Completion Rate", f"{health_info['completion_rate']}%")

            st.divider()
            
            ch1, ch2 = st.columns(2)
            with ch1:
                fig_status = px.pie(
                    df, names="Campaign Status", 
                    title="Participant Category Breakdown",
                    color_discrete_sequence=px.colors.qualitative.Set2
                )
                st.plotly_chart(fig_status, use_container_width=True)
                
            with ch2:
                verified_df = df[df["Verification Status"] == "Verified"].copy()
                fig_dist = px.histogram(
                    verified_df, x="Badges Earned", nbins=11,
                    title="Badge Distribution (0 to 10)",
                    labels={"Badges Earned": "Badges Count"},
                    color_discrete_sequence=["#4285F4"]
                )
                st.plotly_chart(fig_dist, use_container_width=True)

        # TAB 2: SMART ACTION & PRIORITY CENTRE
        with tab2:
            st.subheader("🎯 Smart Action & Priority Centre")
            st.markdown("Rule-based participant prioritization and action recommendations.")
            
            prio_filter = st.selectbox(
                "Filter Outreach Priority",
                ["All", "HIGH (Quick Win)", "HIGH (Broken / Private)", "MEDIUM (Onboarding Needed)", "MEDIUM (Encouragement Needed)", "LOW (Completed)"]
            )
            
            filtered_df = df if prio_filter == "All" else df[df["Outreach Priority"] == prio_filter]
            
            st.dataframe(
                filtered_df[[
                    "Google Skills Profile URL", 
                    "Outreach Priority",
                    "Campaign Status", 
                    "Badges Earned", 
                    "Recommended Action"
                ]],
                use_container_width=True
            )

        # TAB 3: BROADCAST TEMPLATES (New Feature 2)
        with tab3:
            st.subheader("📢 Copy-Paste Intervention Templates")
            st.markdown("Pre-calculated messaging templates ready to send to student groups.")

            for title, template_text in templates.items():
                st.markdown(f"#### {title}")
                st.code(template_text, language="markdown")

        # TAB 4: BADGE GAP ANALYZER
        with tab4:
            st.subheader("🔍 Badge Gap Analyzer")
            st.markdown("Pinpoint exactly how many badges participants are missing.")

            verified_only = df[df["Verification Status"] == "Verified"].copy()
            verified_only["Badges Remaining"] = pd.to_numeric(
                verified_only["Badges Remaining"], errors="coerce"
            ).fillna(0)

            selected_gap = st.slider("Filter by Remaining Badges", 0, TARGET_BADGES, (1, 3))
            
            gap_df = verified_only[
                (verified_only["Badges Remaining"] >= selected_gap[0]) & 
                (verified_only["Badges Remaining"] <= selected_gap[1])
            ]
            
            st.dataframe(
                gap_df[["Google Skills Profile URL", "Outreach Priority", "Badges Earned", "Badges Remaining", "Campaign Status"]],
                use_container_width=True
            )

        # TAB 5: REPORT GENERATOR
        with tab5:
            st.subheader("📑 Campaign Report & Export")
            st.markdown("Export complete campaign analytics for record-keeping or reporting.")

            csv_export = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Detailed CSV Report",
                data=csv_export,
                file_name="gdg_skilltrack_report.csv",
                mime="text/csv"
            )

            st.divider()
            st.subheader("Full Data View")
            st.dataframe(df, use_container_width=True)

else:
    st.info("👈 Please upload the organiser CSV file in the sidebar to begin processing.")