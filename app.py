import streamlit as st
import pandas as pd
import plotly.express as px
import time
from datetime import datetime

# --- Custom Modules ---
from sheets_db import get_all_documents, upsert_documents
from priority_engine import enrich_documents_with_priority

# --- 1. Page Configuration ---
st.set_page_config(
    page_title="Architect Review Dashboard",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Modern UI & Status Colors
st.markdown("""
<style>
    /* Critical Status Highlight */
    .stDataFrame { border-radius: 10px; overflow: hidden; }
    div[data-testid="stMetricValue"] { font-size: 24px; }
</style>
""", unsafe_allow_html=True)

# --- 2. Sidebar Controls & Metrics ---
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Configuration Inputs
    sheet_id_input = st.text_input("Google Sheet ID", value="", type="password", help="Enter ID to override config")
    
    if st.button("🔄 Refresh Data Now", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.divider()

    # Load Data safely
    try:
        raw_df = get_all_documents()
        if not raw_df.empty:
            df = enrich_documents_with_priority(raw_df)
            
            # --- FIX ADDED HERE ---
            # Create a 'link' column for internal ID usage, copied from 'Google Doc Link'
            if 'Google Doc Link' in df.columns:
                df['link'] = df['Google Doc Link']
            else:
                df['link'] = "" # Fallback to prevent crash if empty
            # ----------------------
            
        else:
            df = pd.DataFrame()
            st.warning("Database empty.")
    except Exception as e:
        st.error(f"Connection Error: {e}")
        st.stop()

    # Dynamic Filters
    st.subheader("🔍 Filters")
    
    # 1. Status Filter
    all_statuses = df['Status'].unique().tolist() if 'Status' in df.columns else []
    selected_status = st.multiselect("Status", all_statuses, default=all_statuses)
    
    # 2. Owner Filter
    all_owners = df['Owner'].unique().tolist() if 'Owner' in df.columns else []
    selected_owners = st.multiselect("Owner", all_owners, default=all_owners)
    
    # 3. Urgency Filter
    all_urgency = df['urgency_level'].unique().tolist() if 'urgency_level' in df.columns else []
    selected_urgency = st.multiselect("Urgency", all_urgency, default=all_urgency)

    # Apply Filters
    if not df.empty:
        filtered_df = df[
            (df['Status'].isin(selected_status)) &
            (df['Owner'].isin(selected_owners)) &
            (df['urgency_level'].isin(selected_urgency))
        ]
    else:
        filtered_df = pd.DataFrame()

    st.divider()

    # Sidebar Metrics
    st.subheader("📈 Quick Stats")
    if not filtered_df.empty:
        total_docs = len(filtered_df)
        critical_count = len(filtered_df[filtered_df['urgency_level'].str.contains("CRITICAL")])
        avg_wait = filtered_df['priority_score'].mean()
        
        c1, c2 = st.columns(2)
        c1.metric("Total Docs", total_docs)
        c2.metric("Critical", critical_count, delta_color="inverse")
        st.metric("Avg Urgency Score", f"{avg_wait:.1f}")

# --- 3. Main View - Priority Queue Table ---
st.title("🏗️ Architect Review Dashboard")

if filtered_df.empty:
    st.info("No documents match your filters. Adjust the sidebar to see results.")
else:
    # Prepare Data for Editor
    # Now 'link' exists, so this selection will work!
    display_df = filtered_df[[
        "urgency_level", "Document Name", "Owner", "Status", 
        "priority_score", "Days Old", "Google Doc Link", "link"
    ]].copy()

    # Rename for cleaner UI
    display_df.rename(columns={
        "urgency_level": "Urgency", 
        "priority_score": "Score",
        "Google Doc Link": "Doc Link"
    }, inplace=True)

    st.subheader("📋 Priority Queue")
    
    # Interactive Table (st.data_editor)
    edited_df = st.data_editor(
        display_df,
        column_config={
            "Doc Link": st.column_config.LinkColumn("Document", display_text="Open Doc"),
            "Status": st.column_config.SelectboxColumn(
                "Status",
                help="Change status and click Update",
                width="medium",
                options=[
                    "Pending", "In Review", "Approved", 
                    "Needs Changes", "Completed", "Archived"
                ],
                required=True
            ),
            "Score": st.column_config.ProgressColumn(
                "Priority Score",
                format="%d",
                min_value=0,
                max_value=30,
            ),
            # Hide the raw link used for ID
            "link": None 
        },
        hide_index=True,
        use_container_width=True,
        disabled=["Urgency", "Document Name", "Owner", "Score", "Days Old", "Doc Link"]
    )

    # --- Update Logic ---
    if st.button("💾 Update Status Changes", type="primary"):
        try:
            # Detect changes (rows where Status differs)
            changes = []
            
            # Reset index to ensure alignment
            original_reset = display_df.reset_index(drop=True)
            edited_reset = edited_df.reset_index(drop=True)
            
            for index, row in edited_reset.iterrows():
                original_status = original_reset.at[index, 'Status']
                new_status = row['Status']
                
                if original_status != new_status:
                    # Construct payload
                    change_payload = {
                        'topic': row['Document Name'],
                        'architect': row['Owner'],
                        'link': row['link'], # This now correctly grabs the hidden ID
                        'modified_time': datetime.now(),
                        'created_time': datetime.now(),
                        'status_override': new_status
                    }
                    changes.append(change_payload)
            
            if changes:
                with st.spinner(f"Updating {len(changes)} documents..."):
                    upsert_documents(changes)
                st.success("✅ Status updated successfully!")
                time.sleep(1)
                st.rerun()
            else:
                st.info("No changes detected.")
                
        except Exception as e:
            st.error(f"Update Failed: {e}")

# --- 4. Analytics Panel ---
st.divider()
st.subheader("📊 Analytics Overview")

if not filtered_df.empty:
    col1, col2, col3 = st.columns(3)

    with col1:
        st.caption("Documents by Status")
        status_counts = filtered_df['Status'].value_counts().reset_index()
        status_counts.columns = ['Status', 'Count']
        st.bar_chart(status_counts, x="Status", y="Count", color="#FF4B4B")

    with col2:
        st.caption("Average Days Old by Status")
        # Ensure numeric for calculation
        filtered_df['Days Old'] = pd.to_numeric(filtered_df['Days Old'], errors='coerce')
        avg_days = filtered_df.groupby('Status')['Days Old'].mean().reset_index()
        st.line_chart(avg_days, x="Status", y="Days Old")

    with col3:
        st.caption("Key Performance Indicators")
        
        # KPI 1: Critical Documents
        crit_len = len(filtered_df[filtered_df['urgency_level'].str.contains("CRITICAL")])
        st.metric("🚨 Critical Docs", crit_len)
        
        # KPI 2: Pending > 7 Days
        stagnant = len(filtered_df[
            (filtered_df['Status'] == 'Pending') & 
            (filtered_df['Days Old'] > 7)
        ])
        st.metric("🐢 Stagnant (>7 Days)", stagnant)
        
        # KPI 3: Avg Turnaround
        st.metric("⚡ Avg Priority Score", f"{filtered_df['priority_score'].mean():.1f}")

# --- 5. Real-time Updates ---
if 'last_refresh' not in st.session_state:
    st.session_state['last_refresh'] = time.time()

if time.time() - st.session_state['last_refresh'] > 60:
    st.session_state['last_refresh'] = time.time()
    st.rerun()