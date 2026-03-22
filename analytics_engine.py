import json
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from datetime import datetime

def run_sales_prediction():
    df = pd.read_csv('data/nk_sales_data_2022_2026_feb.csv')
    df['date'] = pd.to_datetime(df['date'])
    
    # Calculate MoM growth for top performing and worst performing products
    df['MonthYear'] = df['date'].dt.to_period('M')
    monthly_sales = df.groupby(['product_name', 'MonthYear'])['revenue'].sum().reset_index()
    
    results = {}
    chart_data = {}
    
    for product in monthly_sales['product_name'].unique():
        prod_data = monthly_sales[monthly_sales['product_name'] == product].copy()
        prod_data['MonthNum'] = np.arange(len(prod_data))
        
        # Linear Regression
        X = prod_data[['MonthNum']]
        y = prod_data['revenue']
        
        if len(X) > 1:
            model = LinearRegression()
            model.fit(X, y)
            r2 = model.score(X, y)
            
            # Predict next 3 months
            future_X = pd.DataFrame({'MonthNum': [len(X), len(X)+1, len(X)+2]})
            future_preds = model.predict(future_X)
            
            # Calculate average growth percentage based on slope vs mean
            mean_sales = y.mean()
            growth_pct = (model.coef_[0] / mean_sales) * 100 if mean_sales else 0
            
            results[product] = {
                'growth_pct': round(growth_pct, 2),
                'r2': round(r2, 2),
                'future_avg_month': float(future_preds.mean()),
                'current_trend': 'up' if growth_pct > 0 else 'down'
            }
            
            if product == "Tirupati Cottonseed Oil 1L":
                chart_data['labels'] = [str(m) for m in prod_data['MonthYear']] + ['M+1', 'M+2', 'M+3']
                chart_data['historical'] = [float(val) for val in y.tolist()]
                chart_data['forecast'] = [None] * len(y) + [float(val) for val in future_preds.tolist()]
                chart_data['forecast'][len(y)-1] = float(y.iloc[-1]) # connect line
                
    # Calculate pie chart breakdown
    product_totals = df.groupby('product_name')['revenue'].sum()
    chart_data['pie_labels'] = product_totals.index.tolist()
    chart_data['pie_data'] = [float(x) for x in product_totals.values.tolist()]
    
    # Find best and worst
    best_prod = max(results.keys(), key=lambda k: results[k]['growth_pct'])
    worst_prod = min(results.keys(), key=lambda k: results[k]['growth_pct'])
    
    raw_math = f"Linear regression output summary for all products: {json.dumps(results)}"
    return raw_math, {
        "best_product": best_prod,
        "best_growth": float(results[best_prod]['growth_pct']),
        "worst_product": worst_prod,
        "worst_growth": float(results[worst_prod]['growth_pct']),
        "chart_data": chart_data
    }

def run_liquidity_risk():
    df = pd.read_csv('data/nk_receivables_2022_2026_feb.csv')
    
    # Filter high risk (Outstanding amount > 0 and overdue > 60 days)
    high_risk = df[(df['days_overdue'] > 60) & (df['outstanding_amount'] > 0)]
    total_stuck = int(high_risk['outstanding_amount'].sum())
    
    if total_stuck > 0:
        top_defaulters_raw = high_risk.groupby('customer_name')['outstanding_amount'].sum().sort_values(ascending=False).head(10).to_dict()
        top_defaulter = list(top_defaulters_raw.keys())[0]
        top_defaulter_amt = int(top_defaulters_raw[top_defaulter])
        max_days = int(high_risk[high_risk['customer_name'] == top_defaulter]['days_overdue'].max())
        top_defaulters = {str(k): int(v) for k,v in top_defaulters_raw.items()}
    else:
        top_defaulter = "None"
        top_defaulter_amt = 0
        max_days = 0
        top_defaulters = {}
        
    total_receivables = float(df['invoice_amount'].sum())
    healthy_receivables = total_receivables - total_stuck
    
    # Predict next 30-90 days cash requirement using sales history proxy
    try:
        sales_df = pd.read_csv('data/nk_sales_data_2022_2026_feb.csv')
        recent_90_sales = sales_df.tail(900)['revenue'].sum() # Approximation
        cash_requirement_90_days = int(recent_90_sales * 0.75) # 75% operating cost proxy
    except:
        cash_requirement_90_days = int(total_receivables * 1.5)
        
    raw_math = f"Receivables Analysis: High risk tier > 60 days. Total: ₹{total_stuck}. Top 10 defaulters breakdown: {json.dumps(top_defaulters)}. Predicted 90-day cash requirement: ₹{cash_requirement_90_days}."
    return raw_math, {
        "total_stuck": total_stuck,
        "top_defaulter": top_defaulter,
        "top_defaulter_amount": top_defaulter_amt,
        "max_days": max_days,
        "cash_requirement_90_days": cash_requirement_90_days,
        "chart_data": {
            "type": "pie",
            "labels": ["Stuck (>60 Days)", "Healthy (<60 Days)"],
            "data": [float(total_stuck), float(healthy_receivables)]
        }
    }

def run_inventory_optimization():
    df = pd.read_csv('data/nk_inventory_2022_2026_feb.csv')
    df['snapshot_date'] = pd.to_datetime(df['snapshot_date'])
    
    # Identify dead stock (from pre-calculated 'is_dead_stock' flag)
    recent_records = df.sort_values('snapshot_date').groupby('product_name').tail(1)
    dead_stock_prods = recent_records[recent_records['is_dead_stock'] == 1]['product_name'].tolist()
    
    chart_data = {}
    if dead_stock_prods:
        dead_prod = dead_stock_prods[0]
        row = recent_records[recent_records['product_name'] == dead_prod].iloc[0]
        holding_amount = int(row['current_stock_kg'])
        
        raw_math = f"Inventory Analysis: Dead stock flag detected. Highlighted dead product: {dead_prod} with {holding_amount} kg currently. Blocking ₹{row.get('inventory_value', 0)} in capital."
        
        # Prepare chart data
        prod_data = df[df['product_name'] == dead_prod].sort_values('snapshot_date').tail(24)
        chart_data['labels'] = prod_data['snapshot_date'].dt.strftime('%Y-%m').tolist()
        chart_data['historical'] = [float(val) for val in prod_data['current_stock_kg'].tolist()]
        
        total_stock = float(recent_records['current_stock_kg'].sum())
        moving_stock = total_stock - float(holding_amount)
        chart_data['pie_type'] = 'doughnut'
        chart_data['pie_labels'] = [f"{dead_prod} (Dead)", "Moving Stock"]
        chart_data['pie_data'] = [float(holding_amount), moving_stock]
        
        meta = {
            "dead_product": dead_prod,
            "holding_amount": holding_amount,
            "days_stuck": int(row.get('days_since_last_movement', 120)),
            "chart_data": chart_data
        }
    else:
        raw_math = "Inventory Analysis: No dead stock detected over 16-week window."
        meta = {"dead_product": "None", "holding_amount": 0, "days_stuck": 0, "chart_data": {}}
        
    return raw_math, meta

def run_tax_delta():
    df = pd.read_csv('data/nk_gst_data_2022_2026_feb.csv')
    df['invoice_date'] = pd.to_datetime(df['invoice_date'])
    df['MonthYear'] = df['invoice_date'].dt.to_period('M')
    
    # Calculate ITC at risk per row (where mismatch_flag is 1)
    df['itc_at_risk'] = df.apply(lambda row: row['total_tax_amount'] if row['mismatch_flag'] == 1 else 0, axis=1)
    
    # Group by month
    monthly_stats = df.groupby('MonthYear').agg({
        'total_tax_amount': 'sum',
        'itc_at_risk': 'sum',
        'mismatch_flag': 'sum'
    }).reset_index()
    
    latest_month = monthly_stats.iloc[-1]
    mismatch_amt = float(latest_month['itc_at_risk'])
    
    # Project liability using linear regression on monthly tax value
    monthly_stats['MonthNum'] = np.arange(len(monthly_stats))
    X = monthly_stats[['MonthNum']]
    y = monthly_stats['total_tax_amount']
    model = LinearRegression()
    model.fit(X, y)
    
    # Predict next 3 months
    future_X = pd.DataFrame({'MonthNum': [len(X), len(X)+1, len(X)+2]})
    q3_liability = int(model.predict(future_X).sum())
    
    recent_mismatches = monthly_stats.tail(6)
    mismatches_dict = {str(row['MonthYear']): float(row['itc_at_risk']) for _, row in recent_mismatches.iterrows()}
    
    raw_math = f"Tax Analysis: Latest month ITC at risk is ₹{mismatch_amt}. Previous 6 months ITC risks: {json.dumps(mismatches_dict)}. Predicted Q3 liability: ₹{q3_liability}."
    return raw_math, {
        "mismatch": mismatch_amt,
        "q3_liability": q3_liability,
        "latest_month": str(latest_month['MonthYear']),
        "chart_data": {
            "type": "bar",
            "labels": [str(m) for m in monthly_stats.tail(6)['MonthYear']],
            "data": [float(v) for v in monthly_stats.tail(6)['total_tax_amount']]
        }
    }

def run_customer_health():
    df = pd.read_csv('data/nk_receivables_2022_2026_feb.csv')
    pending = df[df['outstanding_amount'] > 0]
    
    # Calculate total outstanding per customer
    customer_debt = pending.groupby('customer_name')['outstanding_amount'].sum().sort_values(ascending=False)
    
    # Calculate max days overdue per customer
    customer_delay = pending.groupby('customer_name')['days_overdue'].max()
    
    health_profiles = {}
    for cust in customer_debt.index:
        health_profiles[str(cust)] = {
            'outstanding_inr': int(customer_debt[cust]),
            'max_days_overdue': int(customer_delay[cust]),
            'risk_status': 'critical' if customer_delay[cust] > 60 else 'warning' if customer_delay[cust] > 30 else 'healthy'
        }
        
    raw_math = f"Customer Health Analysis: Total outstanding debt by customer and their max days overdue: {json.dumps(health_profiles)}."
    
    if len(customer_debt) > 0:
        top_cust = customer_debt.index[0]
        meta = {
            "top_debtor": str(top_cust),
            "top_debt_amount": int(customer_debt[top_cust]),
            "chart_data": {
                "type": "bar",
                "labels": [str(c) for c in customer_debt.index[:5]],
                "data": [int(v) for v in customer_debt.values[:5]]
            }
        }
    else:
        meta = {"top_debtor": "None", "top_debt_amount": 0, "chart_data": {}}
        
    return raw_math, meta

def run_margin_velocity():
    df = pd.read_csv('data/nk_sales_data_2022_2026_feb.csv')
    df['date'] = pd.to_datetime(df['date'])
    
    # Calculate moving average quantity sold over last 30 entries
    recent_sales = df.sort_values('date').groupby('product_name').tail(30)
    velocity = recent_sales.groupby('product_name')['quantity_sold'].mean().sort_values(ascending=False)
    
    velocity_profile = {str(k): round(float(v), 2) for k, v in velocity.items()}
    best_velocity_prod = velocity.index[0] if len(velocity) > 0 else "None"
    
    raw_math = f"Sales Velocity Analysis (recent entries average of units sold): {json.dumps(velocity_profile)}."
    
    meta = {
        "fastest_moving_product": str(best_velocity_prod),
        "top_velocity": float(velocity.iloc[0]) if len(velocity) > 0 else 0.0,
        "chart_data": {
            "type": "bar",
            "labels": [str(p) for p in velocity.index[:5]],
            "data": [float(v) for v in velocity.values[:5]]
        }
    }
    return raw_math, meta
