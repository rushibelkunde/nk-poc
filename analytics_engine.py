import json
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from datetime import datetime

def run_sales_prediction():
    df = pd.read_csv('data/historical_sales.csv')
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Calculate MoM growth for top performing and worst performing products
    df['MonthYear'] = df['Date'].dt.to_period('M')
    monthly_sales = df.groupby(['Product', 'MonthYear'])['Sales_INR'].sum().reset_index()
    
    results = {}
    chart_data = {}
    
    for product in monthly_sales['Product'].unique():
        prod_data = monthly_sales[monthly_sales['Product'] == product].copy()
        prod_data['MonthNum'] = np.arange(len(prod_data))
        
        # Linear Regression
        X = prod_data[['MonthNum']]
        y = prod_data['Sales_INR']
        
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
            
            if product == "Tirupati Cottonseed Oil":
                chart_data['labels'] = [str(m) for m in prod_data['MonthYear']] + ['M+1', 'M+2', 'M+3']
                chart_data['historical'] = [float(val) for val in y.tolist()]
                chart_data['forecast'] = [None] * len(y) + [float(val) for val in future_preds.tolist()]
                chart_data['forecast'][len(y)-1] = float(y.iloc[-1]) # connect line
                
    # Calculate pie chart breakdown
    product_totals = df.groupby('Product')['Sales_INR'].sum()
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
    df = pd.read_csv('data/receivables_ledger.csv')
    
    # Filter high risk
    high_risk = df[(df['DaysOverdue'] > 60) & (df['Status'] == 'Pending')]
    total_stuck = int(high_risk['Amount_INR'].sum())
    
    if total_stuck > 0:
        top_defaulters_raw = high_risk.groupby('Customer')['Amount_INR'].sum().sort_values(ascending=False).head(10).to_dict()
        top_defaulter = list(top_defaulters_raw.keys())[0]
        top_defaulter_amt = int(top_defaulters_raw[top_defaulter])
        max_days = int(high_risk[high_risk['Customer'] == top_defaulter]['DaysOverdue'].max())
        top_defaulters = {str(k): int(v) for k,v in top_defaulters_raw.items()}
    else:
        top_defaulter = "None"
        top_defaulter_amt = 0
        max_days = 0
        top_defaulters = {}
        
    total_receivables = float(df['Amount_INR'].sum())
    healthy_receivables = total_receivables - total_stuck
    
    # Predict next 30-90 days cash requirement using sales history proxy
    try:
        sales_df = pd.read_csv('data/historical_sales.csv')
        recent_90_sales = sales_df.head(90*10)['Sales_INR'].sum() # Assuming 10 products
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
    df = pd.read_csv('data/inventory_snapshots.csv')
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Identify dead stock (0 standard deviation in stock over last X weeks)
    recent_weeks = df.sort_values('Date').groupby('Product').tail(16)
    std_devs = recent_weeks.groupby('Product')['Stock_Kg'].std()
    dead_stock_prods = std_devs[std_devs == 0].index.tolist()
    
    chart_data = {}
    if dead_stock_prods:
        dead_prod = dead_stock_prods[0]
        holding_amount = int(recent_weeks[recent_weeks['Product'] == dead_prod]['Stock_Kg'].iloc[0])
        all_std = std_devs.fillna(0).to_dict()
        all_std_json = {str(k): float(v) for k,v in all_std.items()}
        raw_math = f"Inventory Analysis: Variance in Stock_Kg over last 16 weeks (0 variance = dead stock). Full product variance breakdown: {json.dumps(all_std_json)}. Highlighted dead product for charting: {dead_prod} holding {holding_amount} kg."
        
        # Prepare chart data
        prod_data = df[df['Product'] == dead_prod].sort_values('Date').tail(24)
        chart_data['labels'] = prod_data['Date'].dt.strftime('%Y-%m-%d').tolist()
        chart_data['historical'] = [float(val) for val in prod_data['Stock_Kg'].tolist()]
        
        total_stock = float(df.groupby('Product').tail(1)['Stock_Kg'].sum())
        moving_stock = total_stock - float(holding_amount)
        chart_data['pie_type'] = 'doughnut'
        chart_data['pie_labels'] = [f"{dead_prod} (Dead)", "Moving Stock"]
        chart_data['pie_data'] = [float(holding_amount), moving_stock]
        
        meta = {
            "dead_product": dead_prod,
            "holding_amount": holding_amount,
            "days_stuck": 120,
            "chart_data": chart_data
        }
    else:
        raw_math = "Inventory Analysis: No dead stock detected over 16-week window."
        meta = {"dead_product": "None", "holding_amount": 0, "days_stuck": 0, "chart_data": {}}
        
    return raw_math, meta

def run_tax_delta():
    df = pd.read_csv('data/gst_compliance_log.csv')
    df['Month'] = pd.to_datetime(df['Month'])
    df = df.sort_values('Month')
    
    latest_month = df.iloc[-1]
    mismatch = int(latest_month['Mismatch_INR'])
    
    # Project liability
    X = np.arange(len(df)).reshape(-1, 1)
    y = df['Internal_Tax_INR'].values
    model = LinearRegression()
    model.fit(X, y)
    
    # Predict next 3 months (Q3)
    future_X = np.array([[len(df)], [len(df)+1], [len(df)+2]])
    q3_liability = int(model.predict(future_X).sum())
    
    recent_mismatches = df.tail(6).copy()
    mismatches_dict = {row['Month'].strftime('%Y-%m'): int(row['Mismatch_INR']) for _, row in recent_mismatches.iterrows()}
    
    raw_math = f"Tax Analysis: Latest month mismatch is ₹{mismatch}. Previous 6 months mismatches: {json.dumps(mismatches_dict)}. Predicted Q3 liability: ₹{q3_liability} based on linear projection."
    return raw_math, {
        "mismatch": mismatch,
        "q3_liability": q3_liability,
        "latest_month": latest_month['Month'].strftime('%Y-%m'),
        "chart_data": {
            "type": "bar",
            "labels": ["Internal TaxCalc", "GSTR-2B Logged"],
            "data": [float(latest_month['Internal_Tax_INR']), float(latest_month['GSTR_2B_INR'])]
        }
    }

def run_customer_health():
    df = pd.read_csv('data/receivables_ledger.csv')
    pending = df[df['Status'] == 'Pending']
    
    # Calculate total outstanding per customer
    customer_debt = pending.groupby('Customer')['Amount_INR'].sum().sort_values(ascending=False)
    
    # Calculate max days overdue per customer
    customer_delay = pending.groupby('Customer')['DaysOverdue'].max()
    
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
    df = pd.read_csv('data/historical_sales.csv')
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Calculate moving average quantity sold over last 30 days
    recent_sales = df.sort_values('Date').groupby('Product').tail(30)
    velocity = recent_sales.groupby('Product')['Quantity'].mean().sort_values(ascending=False)
    
    velocity_profile = {str(k): round(float(v), 2) for k, v in velocity.items()}
    best_velocity_prod = velocity.index[0] if len(velocity) > 0 else "None"
    
    raw_math = f"Sales Velocity Analysis (30-day moving average of kg sold per day): {json.dumps(velocity_profile)}."
    
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
