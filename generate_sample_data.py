"""
generate_sample_data.py
Creates a realistic sample CDR Excel file for testing.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

def generate_cdr_data(n=500, output_path="data/sample_cdr.xlsx"):
    random.seed(42)
    np.random.seed(42)

    branches = ["Cairo HQ", "Alexandria", "Mansoura", "Giza", "Tanta"]
    extensions = [f"10{i:02d}" for i in range(1, 31)]  # 1001 - 1030
    call_types = ["Inbound", "Outbound", "Internal", "Missed"]
    type_weights = [0.35, 0.35, 0.20, 0.10]

    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 3, 31)
    date_range = (end_date - start_date).days

    records = []
    for _ in range(n):
        call_date = start_date + timedelta(days=random.randint(0, date_range))
        # Bias toward business hours
        hour = int(np.random.choice(range(8, 20), p=np.array([0.03,0.08,0.12,0.14,0.14,0.12,0.1,0.08,0.07,0.06,0.04,0.02])))
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        call_datetime = call_date.replace(hour=hour, minute=minute, second=second)

        call_type = random.choices(call_types, weights=type_weights)[0]
        duration = 0 if call_type == "Missed" else random.randint(10, 1800)
        extension = random.choice(extensions)
        branch = random.choice(branches)
        caller = f"+20{random.randint(1000000000, 1999999999)}"
        callee = f"+20{random.randint(1000000000, 1999999999)}"

        records.append({
            "CallID": f"CDR{_+1:05d}",
            "DateTime": call_datetime,
            "CallerNumber": caller,
            "CalleeNumber": callee,
            "Extension": extension,
            "Branch": branch,
            "CallType": call_type,
            "Duration_sec": duration,
            "Status": "Missed" if call_type == "Missed" else "Answered"
        })

    df = pd.DataFrame(records)
    df.to_excel(output_path, index=False)
    print(f"[+] Sample data saved to {output_path} ({n} records)")
    return df

if __name__ == "__main__":
    generate_cdr_data()
