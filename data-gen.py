import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os
import math

os.makedirs('data', exist_ok=True)

# 1. Historical Sales (1825 days / 5 years)
dates = [datetime.today() - timedelta(days=x) for x in range(1825)]
dates.reverse()

products = [
    "Tirupati Cottonseed Oil", "Tirupati Sunflower Oil", "Tirupati Groundnut Oil", "Tirupati Soybean Oil", 
    "Tirupati Mustard Oil", "Olixir Olive Oil", "Olixir Sesame Oil", "Castor Oil", "Refined Castor Oil", "De Oiled Cake"
]

sales_data = []
for d in dates:
    month = d.month
    q1_multiplier = 1.2 if month in [1, 2, 3] else 1.0
    
    # Base month index from 0 to 23
    month_idx = (d.year - dates[0].year) * 12 + d.month - dates[0].month
    
    for p in products:
        base_sales = random.randint(50000, 500000) # INR
        
        if p == "Tirupati Cottonseed Oil":
            # Linear combination (base trend) + Non-linear (Seasonality + Volatility)
            baseline_growth = (1.02) ** month_idx  # Soft 2% linear compound
            seasonality = 1.0 + 0.25 * math.sin(2 * math.pi * month_idx / 12) # Sine wave for yearly cycles
            volatility = random.uniform(0.8, 1.2) # Real world noise
            market_shock = 1.5 if month_idx % 14 == 0 else 1.0 # Random spikes
            
            base_sales = int(base_sales * baseline_growth * seasonality * volatility * market_shock)
        
        if p == "Olixir Olive Oil":
            # 30% drop in last 3 months
            if month_idx >= 57:
                base_sales = int(base_sales * 0.7)
                
        final_sales = int(base_sales * q1_multiplier)
        sales_data.append({
            "Date": d.strftime("%Y-%m-%d"),
            "Product": p,
            "Sales_INR": final_sales,
            "Quantity": int(final_sales / 1500) # Assuming avg 1500 INR per unit
        })

pd.DataFrame(sales_data).to_csv('data/historical_sales.csv', index=False)

# 2. Receivables Ledger
invoices = []
customers = ["Gujarat Supermarkets", "Mumbai Fresh Mart", "Delhi Mega Stores", "Rajasthan Traders", "Punjab Distributors"]
for i in range(10000):
    cust = random.choice(customers)
    amount = random.randint(20000, 500000) # INR
    days_overdue = random.randint(-10, 120)
    
    if cust == "Gujarat Supermarkets" and i < 20:
        # Inject ₹70,00,000 (7M INR) stuck at 60-90 days for Gujarat Supermarkets
        amount = 350000  # 7,000,000 / 20 = 350,000
        days_overdue = random.randint(65, 85)
        
    status = "Paid" if days_overdue <= 0 else "Pending"
    if status == "Pending" and cust == "Gujarat Supermarkets" and i < 20:
        pass # keep it exactly as we forced it
    elif status == "Pending":
       amount = random.randint(10000, 100000)
       
    invoices.append({
        "InvoiceID": f"INV-{10000+i}",
        "Customer": cust,
        "Amount_INR": amount,
        "DaysOverdue": days_overdue,
        "Status": status
    })

pd.DataFrame(invoices).to_csv('data/receivables_ledger.csv', index=False)

# 3. Inventory Snapshots (Weekly)
inventory_dates = [datetime.today() - timedelta(weeks=x) for x in range(260)]
inventory_dates.reverse()

inventory_data = []
for d in inventory_dates:
    for p in products:
        stock = random.randint(1000, 10000)
        if p == "De Oiled Cake":
            # Flat for 120 days (~17 weeks)
            weeks_ago = (datetime.today() - d).days // 7
            if weeks_ago <= 17:
                stock = 50000 # 50 tons
        inventory_data.append({
            "Date": d.strftime("%Y-%m-%d"),
            "Product": p,
            "Stock_Kg": stock
        })

pd.DataFrame(inventory_data).to_csv('data/inventory_snapshots.csv', index=False)

# 4. GST Compliance Log (Monthly)
gst_dates = [datetime.today() - timedelta(days=30*x) for x in range(60)]
gst_dates.reverse()

gst_data = []
for i, d in enumerate(gst_dates):
    internal = random.randint(5000000, 10000000) # INR
    gstr_2b = internal + random.randint(-50000, 50000)
    mismatch = internal - gstr_2b
    
    if i == 59: # Most recent month
        internal = 12000000
        gstr_2b = 10500000
        mismatch = 1500000 # 15 Lakhs mismatch
        
    gst_data.append({
        "Month": d.strftime("%Y-%m"),
        "Internal_Tax_INR": internal,
        "GSTR_2B_INR": gstr_2b,
        "Mismatch_INR": mismatch,
        "Status": "Reconciled" if abs(mismatch) < 100000 else "Pending"
    })

pd.DataFrame(gst_data).to_csv('data/gst_compliance_log.csv', index=False)

print("Mock data generated successfully in data/ folder.")
