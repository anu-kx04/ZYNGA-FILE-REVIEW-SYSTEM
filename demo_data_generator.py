import pandas as pd
import random
from datetime import datetime, timedelta
from sheets_db import upsert_documents

def generate_demo_data():
    print("🚀 Generating Demo Data...")
    
    architects = ["Arnab", "Anushka", "Rahul", "Priya", "Anu", "Lasya"]
    statuses = ["Pending", "In Review", "Needs Changes", "Approved", "Completed"]

    special_owners = ["Anu", "Anushka"]
    
    scenarios = [
        # 1. The Critical One (Old + Ignored) -> Should be RED
        {
            "name": "Legacy Auth System Migration",
            "days_old": 15,
            "status": "Pending",
            "owner": random.choice(special_owners)
        },
        
        # 2. The Urgent Fix
        {
            "name": "Hotfix: Payment Gateway Bug",
            "days_old": 1,
            "status": "Needs Changes",
            "owner": "Anushka"
        },
        
        # 3. The Stagnant Review
        {
            "name": "Q4 API Spec Proposal",
            "days_old": 8,
            "status": "Pending",
            "owner": "Rahul"
        },
        
        # 4. The Active One
        {
            "name": "New User Onboarding Flow",
            "days_old": 0,
            "status": "In Review",
            "owner": "Priya"
        },
        
        # 5. The Done Deal
        {
            "name": "Data Privacy Policy Update",
            "days_old": 3,
            "status": "Approved",
            "owner": random.choice(special_owners)
        },
    ]
    
    # Add 5 more random filler docs
    for i in range(5):
        scenarios.append({
            "name": f"Module {i+1} Architecture",
            "days_old": random.randint(0, 5),
            "status": random.choice(statuses),
            "owner": random.choice(architects)
        })

    documents = []
    base_url = "https://docs.google.com/document/d/demo_id_"
    
    for i, scen in enumerate(scenarios):
        created_dt = datetime.now() - timedelta(days=scen['days_old'])
        modified_dt = created_dt + timedelta(hours=random.randint(1, 24))
        
        documents.append({
            'topic': scen['name'],
            'architect': scen['owner'],
            'link': f"{base_url}{i}",
            'modified_time': modified_dt,
            'created_time': created_dt,
            'status_override': scen['status']
        })

    upsert_documents(documents)
    print("Successfully seeded 10 documents!")

if __name__ == "__main__":
    generate_demo_data()
