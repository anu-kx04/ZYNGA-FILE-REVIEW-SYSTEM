import pandas as pd
from datetime import datetime, timedelta, timezone
from priority_engine import enrich_documents_with_priority

def run_test():
    print("--- 🧪 Testing Priority Engine Logic ---")

    # 1. Setup Mock Data (Simulating what comes from Google Sheets)
    # We create dates relative to "Now" to ensure the test always works, regardless of when you run it.
    now = datetime.now(timezone.utc)
    
    mock_data = [
        {
            "Document Name": "Fresh Doc (Low Priority)",
            "Created Date": (now - timedelta(days=1)).isoformat(),      # 1 day old
            "Last Modified": (now - timedelta(days=0)).isoformat()      # Edited today
            # Exp Score: 1 + 0 = 1 (🟢 NORMAL)
        },
        {
            "Document Name": "Stale Doc (High Priority)",
            "Created Date": (now - timedelta(days=4)).isoformat(),      # 4 days old
            "Last Modified": (now - timedelta(days=2)).isoformat()      # Edited 2 days ago
            # Exp Score: 4 + 2 = 6 (🟡 HIGH)
        },
        {
            "Document Name": "Forgotten Doc (Critical)",
            "Created Date": (now - timedelta(days=10)).isoformat(),     # 10 days old
            "Last Modified": (now - timedelta(days=5)).isoformat()      # Edited 5 days ago
            # Exp Score: 10 + 5 = 15 (🔴 CRITICAL)
        },
        {
            "Document Name": "Legacy Spec (Critical)",
            "Created Date": (now - timedelta(days=30)).isoformat(),     # 30 days old
            "Last Modified": (now - timedelta(days=1)).isoformat()      # Edited 1 day ago
            # Exp Score: 30 + 1 = 31 (🔴 CRITICAL)
        }
    ]

    # Convert to DataFrame (just like app.py does)
    df_raw = pd.DataFrame(mock_data)

    print(f"\n📥 Input Data ({len(df_raw)} docs):")
    print(df_raw[['Document Name']])

    # 2. Run the Engine
    print("\n⚙️ Running Enrichment...")
    df_enriched = enrich_documents_with_priority(df_raw)

    # 3. Verify Output
    print("\n📤 Final Output (Sorted by Urgency):")
    
    # Select only relevant columns for display
    display_cols = ['Document Name', 'priority_score', 'urgency_level']
    print(df_enriched[display_cols].to_string(index=False))

    # 4. Check Sort Order
    first_score = df_enriched.iloc[0]['priority_score']
    last_score = df_enriched.iloc[-1]['priority_score']
    
    if first_score >= last_score:
        print("\n✅ TEST PASSED: Documents are correctly sorted (Critical first).")
    else:
        print("\n❌ TEST FAILED: Sorting is incorrect.")

if __name__ == "__main__":
    run_test()