import json
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from datetime import datetime
import os

# --- NEW: Dynamic Schema Generation ---
DATASETS = {
    "sales": "data/nk_sales_data_2022_2026_feb.csv",
    "inventory": "data/nk_inventory_2022_2026_feb.csv",
    "receivables": "data/nk_receivables_2022_2026_feb.csv",
    "gst": "data/nk_gst_data_2022_2026_feb.csv"
}

def get_database_schema():
    """Reads the headers of the CSVs to provide context to the LLM."""
    schema = ""
    for name, path in DATASETS.items():
        try:
            # Read only the first row to get columns without loading heavy data
            df = pd.read_csv(path, nrows=0) 
            schema += f"- Dataset '{name}' (path: '{path}'): Columns: {', '.join(df.columns.tolist())}\n"
        except Exception as e:
            print(f"[Warning] Could not read schema for {path}: {e}")
    return schema


    rec_df = pd.read_csv('data/nk_receivables_2022_2026_feb.csv')
    overdue_cache = int(rec_df[rec_df['days_overdue'] > 0]['outstanding_amount'].sum())
    
    inv_df = pd.read_csv('data/nk_inventory_2022_2026_feb.csv')
    inv_df['snapshot_date'] = pd.to_datetime(inv_df['snapshot_date'])
    latest_inv_date = inv_df['snapshot_date'].max()
    recent_inv = inv_df[inv_df['snapshot_date'] == latest_inv_date]
    dead_stock_value = int(recent_inv[recent_inv['is_dead_stock'] == 1]['total_value_inr'].sum())
    
    total_blocked = overdue_cache + dead_stock_value
    
    breakdown = [
        {"category": "Overdue Receivables", "amount": overdue_cache, "risk": "High" if overdue_cache > 5000000 else "Medium"},
        {"category": "Dead Inventory", "amount": dead_stock_value, "risk": "High" if dead_stock_value > 2000000 else "Medium"}
    ]
    
    raw_math = f"Working Capital and Liquidity Snapshot: Total capital blocked is ₹{total_blocked}. Itemized breakdown into Overdue Receivables (₹{overdue_cache}) and Dead Inventory Stock (₹{dead_stock_value})."
    
    meta = {
        "total_blocked": total_blocked,
        "breakdown": breakdown,
        "chart_data": {
            "pie_type": "doughnut",
            "pie_labels": ["Receivables", "Inventory"],
            "pie_data": [float(overdue_cache), float(dead_stock_value)]
        }
    }
    return raw_math, meta