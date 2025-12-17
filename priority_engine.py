import pandas as pd
from datetime import datetime, timezone
from dateutil import parser

def calculate_priority(created_date, modified_date):
    """
    Calculates a priority score based on document age and dormancy.
    
    Formula: Days since creation + Days since last edit
    
    Args:
        created_date (str or datetime): ISO format date string or datetime object
        modified_date (str or datetime): ISO format date string or datetime object
        
    Returns:
        int: The calculated priority score
        
    Examples:
        >>> calculate_priority('2023-12-01T10:00:00Z', '2023-12-05T10:00:00Z')
        # Assuming today is 2023-12-10:
        # Age (9 days) + Latency (5 days) = 14
    """
    now = datetime.now(timezone.utc)
    
    # Ensure inputs are datetime objects
    if isinstance(created_date, str):
        created_date = parser.parse(created_date)
    if isinstance(modified_date, str):
        modified_date = parser.parse(modified_date)
        
    # Ensure inputs are timezone aware (assume UTC if not)
    if created_date.tzinfo is None:
        created_date = created_date.replace(tzinfo=timezone.utc)
    if modified_date.tzinfo is None:
        modified_date = modified_date.replace(tzinfo=timezone.utc)

    # Calculate differences in days
    age_days = (now - created_date).days
    latency_days = (now - modified_date).days
    
    # Return valid positive integer
    return max(0, age_days + latency_days)

def get_urgency_level(score):
    """
    Determines the urgency label and emoji based on the score.
    
    Args:
        score (int): The priority score
        
    Returns:
        str: Formatted string (e.g., "🔴 CRITICAL")
    """
    if score >= 10:
        return "🔴 CRITICAL"
    elif score >= 5:
        return "🟡 HIGH"
    else:
        return "🟢 NORMAL"

def enrich_documents_with_priority(df):
    """
    Takes a raw DataFrame, adds priority metrics, and sorts by urgency.
    
    Args:
        df (pd.DataFrame): DataFrame with 'Created Date' and 'Last Modified' columns.
        
    Returns:
        pd.DataFrame: Enriched and sorted DataFrame.
    """
    if df.empty:
        return df

    # 1. Create a copy to avoid SettingWithCopy warnings
    df = df.copy()

    # 2. Calculate Priority Score using the scalar function
    # We use a lambda to apply the logic row-by-row
    df['priority_score'] = df.apply(
        lambda row: calculate_priority(row['Created Date'], row['Last Modified']), 
        axis=1
    )

    # 3. Add Urgency Level
    df['urgency_level'] = df['priority_score'].apply(get_urgency_level)

    # 4. Add Color Code for UI (Streamlit helper)
    def get_color(score):
        if score >= 10: return "#ffcccc" # Red tint
        if score >= 5:  return "#fff4cc" # Yellow tint
        return "#ccffcc"                 # Green tint
    
    df['urgency_color'] = df['priority_score'].apply(get_color)

    # 5. Sort: Highest priority (Critical) at the top
    df = df.sort_values(by='priority_score', ascending=False)

    return df