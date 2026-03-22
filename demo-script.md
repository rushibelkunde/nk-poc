# DEMO SCRIPT: AI-Driven Executive Command Center (NK Protein)

**Context for the CMD:**
"We have processed 2 years of your historical SAP data across Sales, Receivables, Inventory, and Tax. This is not just a report—it is a prescriptive engine that *backtested* its predictions against your history to ensure maximum accuracy for this quarter."

---

## Step 1: The Macro View (Predictive Sales)
**CMD (User):** "Give me a health check on next quarter’s sales."

**System Action:** WOs hits the `get-sales-prediction` skill. The API runs linear regression on the 24-month `historical_sales.csv`.

**WOs Response:** "Accessing SAP Joule... Based on historical SAP data, I predict a 12% growth in Tirupati Cottonseed Oil sales, but a 30% drop in Olixir Olive Oil. Would you like to see which regions are driving this?"

---

## Step 2: The Predictive Action (Inventory & Product Strategy)
**CMD (User):** "Which products should we discontinue or liquidate?"

**System Action:** WOs hits the `get-inventory-opt` skill. The backend scans `inventory_snapshots.csv` and finds the 'De Oiled Cake' dead stock (0 movement in 120 days).

**WOs Response:** "Based on declining margins and high storage costs (Dead Stock), I recommend liquidating De Oiled Cake. We have 50,000 kg that haven't moved in 120 days. This will free up significant working capital."

**UI Action:** "Action Button" appears dynamically: `[Schedule Liquidation]` | `[Stop Production]`

---

## Step 3: Immediate Liquidity (Receivables)
**CMD (User):** "Where is my cash trapped?"

**System Action:** WOs hits the `get-liquidity-risk` skill assessing `receivables_ledger.csv`.

**WOs Response:** "Action Required: There is ₹70,00,000 stuck with Gujarat Supermarkets, past 60 days overdue. I've calculated a high liquidity risk score based on their historical payment speed."

**UI Action:** The UI highlights this in the "Critical Alerts" component. "Action Button" appears: `[Draft Legal Notice]` | `[Send Reminder]`

---

## Step 4: The Integration (Tax Anomaly Check)
**CMD (User):** "What is my tax liability if we hit these targets, and are there any GST mismatches I should worry about?"

**System Action:** WOs hits the `get-tax-delta` skill scanning `gst_compliance_log.csv`.

**WOs Response:** "Predictive GST liability for Q3 is ₹12 Crore. I’ve also noted a ₹15,00,000 mismatch in current GSTR-2B records that needs immediate reconciliation."
