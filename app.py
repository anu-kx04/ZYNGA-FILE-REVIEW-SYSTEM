import streamlit as st
import pandas as pd
import time
from datetime import datetime

# --- Custom Modules ---
from sheets_db import get_all_documents, upsert_documents
from priority_engine import enrich_documents_with_priority
from analytics import (
    create_status_distribution_chart, 
    create_priority_timeline, 
    create_owner_workload_chart
)

# --- 1. Page Configuration ---
st.set_page_config(
    page_title="Keystone Review Dashboard",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Modern UI
st.markdown("""
<style>
    .stDataFrame { border-radius: 10px; overflow: hidden; }
    div[data-testid="stMetricValue"] { font-size: 24px; }
</style>
""", unsafe_allow_html=True)

# --- 2. Sidebar Controls & Metrics ---
with st.sidebar:
    st.header("⚙️ Configuration")
    
    if st.button("🔄 Refresh Now", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.divider()

    # Load Data safely
    try:
        raw_df = get_all_documents()
        if not raw_df.empty:
            df = enrich_documents_with_priority(raw_df)
            
            # Ensure hidden ID column exists
            if 'Google Doc Link' in df.columns:
                df['link'] = df['Google Doc Link']
            else:
                df['link'] = "" 
        else:
            df = pd.DataFrame()
            st.warning("Database empty.")
    except Exception as e:
        st.error(f"Connection Error: {e}")
        st.stop()

    # Dynamic Filters
    st.subheader("🔍 Filters")
    
    all_statuses = df['Status'].unique().tolist() if 'Status' in df.columns else []
    selected_status = st.multiselect("Status", all_statuses, default=all_statuses)
    
    all_owners = df['Owner'].unique().tolist() if 'Owner' in df.columns else []
    selected_owners = st.multiselect("Owner", all_owners, default=all_owners)
    
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
    st.subheader(" Quick Stats")
    if not filtered_df.empty:
        total_docs = len(filtered_df)
        critical_count = len(filtered_df[filtered_df['urgency_level'].str.contains("CRITICAL")])
        
        if 'priority_score' in filtered_df.columns:
             avg_wait = pd.to_numeric(filtered_df['priority_score'], errors='coerce').fillna(0).mean()
        else:
             avg_wait = 0
        
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
    display_df = filtered_df.copy()
    display_df.insert(0, "Select", False)

    # Select Columns
    display_cols = [
        "Select", "urgency_level", "Document Name", "Owner", "Status", 
        "Notes", "priority_score", "Days Old", "Google Doc Link", "link"
    ]
    display_df = display_df[[c for c in display_cols if c in display_df.columns]]

    # Rename for cleaner UI
    display_df.rename(columns={
        "urgency_level": "Urgency", 
        "priority_score": "Score",
        "Google Doc Link": "Doc Link"
    }, inplace=True)

    st.subheader("📋 Priority Queue & Actions")
    
    # --- INTERACTIVE TABLE ---
    edited_df = st.data_editor(
        display_df,
        column_config={
            "Doc Link": st.column_config.LinkColumn("Document"), 
            "Status": st.column_config.SelectboxColumn(
                "Status",
                width="medium",
                options=[
                    "Pending", "In Review", "Approved", 
                    "Needs Changes", "Completed", "Archived"
                ],
                required=True
            ),
            "Notes": st.column_config.TextColumn(
                "Notes",
                width="large",
                help="Add engineering notes here"
            ),
            "Score": st.column_config.ProgressColumn(
                "Priority Score",
                format="%d",
                min_value=0,
                max_value=30,
            ),
            "link": None # Hide ID
        },
        hide_index=True,
        use_container_width=True,
        disabled=["Urgency", "Document Name", "Owner", "Score", "Days Old", "Doc Link"]
    )

    # --- ACTION BAR (Bulk & Single) ---
    col_actions, col_bulk = st.columns([1, 2])
    
    # A. Standard Save Button
    with col_actions:
        st.write("##### Save Changes")
        if st.button("💾 Update Edits", type="primary", use_container_width=True):
            changes = []
            
            original_reset = display_df.reset_index(drop=True)
            edited_reset = edited_df.reset_index(drop=True)
            
            for index, row in edited_reset.iterrows():
                orig_status = original_reset.at[index, 'Status']
                new_status = row['Status']
                orig_notes = original_reset.at[index, 'Notes']
                new_notes = row['Notes']
                
                if orig_status != new_status or orig_notes != new_notes:
                    if new_status in ["Completed", "Needs Changes"] and orig_status != new_status:
                        print(f"🔔 NOTIFICATION: {row['Document Name']} is now {new_status}")
                        st.toast(f"🔔 Notification sent: {row['Document Name']} -> {new_status}")

                    changes.append({
                        'topic': row['Document Name'],
                        'architect': row['Owner'],
                        'link': row['link'], 
                        'modified_time': datetime.now(),
                        'created_time': datetime.now(),
                        'status_override': new_status,
                        'notes': new_notes
                    })
            
            if changes:
                with st.spinner(f"Updating {len(changes)} documents..."):
                    upsert_documents(changes)
                st.success("✅ Updates saved!")
                time.sleep(1)
                st.rerun()
            else:
                st.info("No changes detected.")

    # B. Bulk Update Section
    with col_bulk:
        st.write("##### Bulk Actions")
        b_col1, b_col2 = st.columns([2, 1])
        
        bulk_status_target = b_col1.selectbox(
            "Set Status for Selected", 
            ["In Review", "Approved", "Needs Changes", "Completed", "Archived"],
            label_visibility="collapsed"
        )
        
        if b_col2.button("Apply to Selected", use_container_width=True):
            selected_rows = edited_df[edited_df["Select"] == True]
            
            if selected_rows.empty:
                st.warning("⚠️ No documents selected.")
            else:
                bulk_changes = []
                for index, row in selected_rows.iterrows():
                    if bulk_status_target in ["Completed", "Needs Changes"]:
                         print(f"🔔 NOTIFICATION: {row['Document Name']} is now {bulk_status_target}")
                    
                    bulk_changes.append({
                        'topic': row['Document Name'],
                        'architect': row['Owner'],
                        'link': row['link'], 
                        'modified_time': datetime.now(),
                        'created_time': datetime.now(),
                        'status_override': bulk_status_target,
                        'notes': row['Notes']
                    })
                
                with st.spinner(f"Bulk updating {len(bulk_changes)} documents..."):
                    upsert_documents(bulk_changes)
                    st.toast(f"✅ Bulk updated {len(bulk_changes)} docs to '{bulk_status_target}'")
                
                time.sleep(1)
                st.rerun()

# --- 4. Analytics Panel (UPDATED) ---
st.divider()
st.subheader("Analytics Overview")

if not filtered_df.empty:
    # KPI Row
    k1, k2, k3 = st.columns(3)
    
    crit_len = len(filtered_df[filtered_df['urgency_level'].str.contains("CRITICAL")])
    k1.metric("🚨 Critical Attention Needed", f"{crit_len} Docs")

    if 'Days Old' in filtered_df.columns:
        filtered_df['Days Old'] = pd.to_numeric(filtered_df['Days Old'], errors='coerce').fillna(0)
        stagnant = len(filtered_df[(filtered_df['Status'] == 'Pending') & (filtered_df['Days Old'] > 7)])
        k2.metric("🐢 Stagnant (>7 Days)", f"{stagnant} Docs")
    
    if 'priority_score' in filtered_df.columns:
        avg_score = pd.to_numeric(filtered_df['priority_score'], errors='coerce').fillna(0).mean()
        k3.metric("⚡ Avg. Priority Score", f"{avg_score:.1f}")

    st.markdown("---")

    # Tabs for Visualizations (Plotly)
    tab1, tab2, tab3 = st.tabs(["📈 Status Overview", "⏳ Timeline Analysis", "👥 Team Workload"])
    
    with tab1:
        st.plotly_chart(create_status_distribution_chart(filtered_df), use_container_width=True)
        
    with tab2:
        st.plotly_chart(create_priority_timeline(filtered_df), use_container_width=True)
        st.caption("larger bubbles = older documents (stagnant)")
        
    with tab3:
        st.plotly_chart(create_owner_workload_chart(filtered_df), use_container_width=True)

# --- 5. Real-time Updates ---
if 'last_refresh' not in st.session_state:
    st.session_state['last_refresh'] = time.time()

if time.time() - st.session_state['last_refresh'] > 60:
    st.session_state['last_refresh'] = time.time()
    st.rerun()