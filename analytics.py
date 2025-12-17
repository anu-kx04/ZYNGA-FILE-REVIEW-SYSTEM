import plotly.express as px
import pandas as pd

def create_status_distribution_chart(df):
    """
    Creates a horizontal bar chart showing the count of documents per status.
    """
    if df.empty:
        return None
        
    # Aggregate data
    if 'Status' in df.columns:
        status_counts = df['Status'].value_counts().reset_index()
        status_counts.columns = ['Status', 'Count']
    else:
        return None
    
    # Custom color map for status
    color_map = {
        'Pending': '#FFA726',       # Orange
        'In Review': '#29B6F6',     # Light Blue
        'Approved': '#66BB6A',      # Green
        'Needs Changes': '#EF5350', # Red
        'Completed': '#AB47BC',     # Purple
        'Archived': '#BDBDBD'       # Grey
    }

    fig = px.bar(
        status_counts, 
        x="Count", 
        y="Status", 
        orientation='h',
        color="Status",
        text="Count",
        title="<b>Document Status Distribution</b>",
        color_discrete_map=color_map,
        template="plotly_dark"
    )
    
    fig.update_layout(
        showlegend=False,
        xaxis_title="Number of Documents",
        yaxis_title="",
        hovermode="y"
    )
    return fig

def create_priority_timeline(df):
    """
    Scatter plot showing when documents were created vs. their current priority score.
    Size indicates age (stagnation).
    """
    if df.empty or 'priority_score' not in df.columns:
        return None

    # 1. Ensure dates are datetime for plotting
    df['Created Date'] = pd.to_datetime(df['Created Date'], errors='coerce')
    
    # 2. Fix "Days Old" for the bubble size (CRITICAL FIX)
    # Convert to numeric, turn NaNs to 0, and clip negatives to 0
    if 'Days Old' in df.columns:
        df['Clean_Days'] = pd.to_numeric(df['Days Old'], errors='coerce').fillna(0)
        # Ensure no negative values (caused by Today() - Time formulas)
        df['Clean_Days'] = df['Clean_Days'].clip(lower=0)
        # Add +1 base size so 0-day-old docs are still visible bubbles
        df['Bubble_Size'] = df['Clean_Days'] + 1
    else:
        df['Bubble_Size'] = 1

    fig = px.scatter(
        df,
        x="Created Date",
        y="priority_score",
        color="urgency_level",
        size="Bubble_Size", # Use the sanitized positive value
        hover_data=["Document Name", "Owner"],
        title="<b>Priority vs. Timeline Analysis</b>",
        color_discrete_map={
            "🔴 CRITICAL": "#FF5252",
            "🟡 HIGH": "#FFD740",
            "🟢 NORMAL": "#69F0AE"
        },
        template="plotly_dark"
    )

    fig.update_layout(
        xaxis_title="Date Created",
        yaxis_title="Priority Score (Age + Dormancy)",
        legend_title="Urgency Level"
    )
    return fig

def create_owner_workload_chart(df):
    """
    Stacked bar chart showing documents per owner, broken down by status.
    """
    if df.empty:
        return None
        
    # Group by Owner and Status
    if 'Owner' in df.columns and 'Status' in df.columns:
        workload = df.groupby(['Owner', 'Status']).size().reset_index(name='Count')
    else:
        return None
    
    fig = px.bar(
        workload,
        x="Owner",
        y="Count",
        color="Status",
        title="<b>Architect Workload Distribution</b>",
        text="Count",
        template="plotly_dark"
    )
    
    fig.update_layout(
        xaxis_title="Architect",
        yaxis_title="Active Documents",
        legend_title="Status",
        barmode='stack'
    )
    return fig