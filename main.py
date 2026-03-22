from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict
import analytics_engine
from llm_service import call_ai_orchestration
import json
import re

app = FastAPI(
    title="NK Executive Command API",
    description="API for NK Protein POC that generates AI responses backed by heavy data analysis.",
    version="1.0.0"
)

router = APIRouter(prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str

class AIResponse(BaseModel):
    response: str
    action_type: str = "none"
    alert_data: Dict[str, Any] = {} # Holds the dynamic numbers to render on the UI

SYSTEM_PROMPT = """
You are NK AI, an authoritative executive AI assistant for NK Protein.

STRICT OUTPUT FORMATTING RULES:
1. Start with: "### ⚡ Accessing NK AI..."
2. Use DOUBLE NEWLINES (\n\n) between every section, header, and list item. 
3. If a list or table is requested:
   - Provide the Table/List FIRST.
   - Follow with the 'Executive Summary'.
   - End with 'Strategic Recommendation'.
4. TABLE RULES: Always include the header separator line (e.g., |---|---|).
5. TONE: No conversational filler. Be cold, analytical, and prescriptive.
6. ANTI-HALLUCINATION: Do NOT use the exact dummy products ('Product A') from the example below. Extract ALL metrics EXCLUSIVELY from the provided Raw Data.
7. DYNAMIC VISUALS: You will be provided with a list of "Available Chart IDs". You MUST choose exactly one main chart (line/bar) and exactly one pie chart (pie/doughnut) that best represent your textual analysis. You MUST place your selection at the very end of your response, formatted as raw JSON block under the exact header `### CHART_SELECTION`. Do not use markdown backticks for this JSON block.

EXAMPLE STRUCTURE:
### ⚡ Accessing NK AI...

| Product | Trend | R^2 |
| :--- | :--- | :--- |
| Product A | +1.5% | 0.85 |

**Executive Summary**: [Summary text]

**Strategic Recommendation**: [Action text]

### CHART_SELECTION
{"main": "sales_trend", "pie": "liquidity_risk_pie"}
"""

ROUTER_PROMPT = """
You are an intelligent API Router. Analyze the user's request and determine which internal analytical modules are required to answer it.
Modules available:
- "sales": Historical sales predictions, revenue trends, top/bottom performing products.
- "liquidity": Receivables ledger, defaulting customers, overdue cash, trapped cash.
- "inventory": Dead stock, holding amounts, variance, warehouse optimization.
- "tax": GST liability, GSTR-2B mismatches, external tax forecasting.
- "customer_health": Customer sales volume versus outstanding debt profiles.
- "margin_velocity": Sales velocity and product movement.

Respond EXCLUSIVELY with a valid JSON array of strings containing the required module IDs. Do NOT wrap the JSON in markdown code blocks or add any other text.
Example Output:
["sales", "liquidity"]
"""

@router.post("/ask-nk-ai", response_model=AIResponse)
async def ask_nk_ai(req: QueryRequest):
    print(f"[NK-AI] Received Query: {req.query}")
    
    # 1. Routing Pass
    route_response = await call_ai_orchestration(ROUTER_PROMPT, f"User Query: {req.query}", {})
    
    # Clean possible markdown from LLaMA response
    clean_json = re.sub(r'```[a-zA-Z]*\n', '', route_response)
    clean_json = re.sub(r'\n```', '', clean_json).strip()
    
    try:
        modules = json.loads(clean_json)
        if not isinstance(modules, list):
            modules = ["sales"]
    except Exception as e:
        print(f"[NK-AI] Failed to parse Router JSON: {e}")
        modules = ["sales"]
        
    print(f"[NK-AI] Executing Modules: {modules}")
        
    # 2. Execution Pass
    raw_math_synthesized = []
    available_charts = {}
    action_type = "sales_view" # Default fallback
    
    if "sales" in modules:
        m, md = analytics_engine.run_sales_prediction()
        raw_math_synthesized.append(m)
        if "chart_data" in md:
            cd = md["chart_data"]
            available_charts["sales_trend"] = {"labels": cd.get("labels"), "historical": cd.get("historical"), "forecast": cd.get("forecast")}
            available_charts["sales_distribution_pie"] = {"pie_labels": cd.get("pie_labels"), "pie_data": cd.get("pie_data")}
        action_type = "sales_view"
    
    if "liquidity" in modules:
        m, md = analytics_engine.run_liquidity_risk()
        raw_math_synthesized.append(m)
        if "chart_data" in md:
            cd = md["chart_data"]
            available_charts["liquidity_risk_pie"] = {"pie_labels": cd.get("labels"), "pie_data": cd.get("data")}
        action_type = "legal_notice"
        
    if "inventory" in modules:
        m, md = analytics_engine.run_inventory_optimization()
        raw_math_synthesized.append(m)
        if "chart_data" in md and md["chart_data"]:
            cd = md["chart_data"]
            available_charts["dead_stock_trend"] = {"labels": cd.get("labels"), "historical": cd.get("historical")}
            available_charts["inventory_health_pie"] = {"pie_labels": cd.get("pie_labels"), "pie_data": cd.get("pie_data"), "pie_type": cd.get("pie_type")}
        action_type = "liquidate_stock"
        
    if "tax" in modules:
        m, md = analytics_engine.run_tax_delta()
        raw_math_synthesized.append(m)
        if "chart_data" in md:
            available_charts["tax_delta_bar"] = md["chart_data"]
        action_type = "reconcile_tax"
        
    if "customer_health" in modules and hasattr(analytics_engine, 'run_customer_health'):
        m, md = analytics_engine.run_customer_health()
        raw_math_synthesized.append(m)
        if "chart_data" in md and md["chart_data"]:
            available_charts["customer_solvency_bar"] = md["chart_data"]
        action_type = "legal_notice"
        
    if "margin_velocity" in modules and hasattr(analytics_engine, 'run_margin_velocity'):
        m, md = analytics_engine.run_margin_velocity()
        raw_math_synthesized.append(m)
        if "chart_data" in md and md["chart_data"]:
            available_charts["sales_velocity_bar"] = md["chart_data"]
        action_type = "sales_view"
        
    # Ensure at least something fired
    if not raw_math_synthesized:
        m, md = analytics_engine.run_sales_prediction()
        raw_math_synthesized.append(m)
        cd = md["chart_data"]
        available_charts["sales_trend"] = {"labels": cd.get("labels"), "historical": cd.get("historical"), "forecast": cd.get("forecast")}
        available_charts["sales_distribution_pie"] = {"pie_labels": cd.get("pie_labels"), "pie_data": cd.get("pie_data")}

    combined_context = f"User asked: {req.query}\n\nSynthesized Raw Data from Multiple Cross-Domain Modules combined:\n" + "\n---\n".join(raw_math_synthesized)
    combined_context += f"\n\nAvailable Chart IDs for CHART_SELECTION: {list(available_charts.keys())}"
    
    if "list" in req.query.lower() or "top" in req.query.lower() or "worst" in req.query.lower():
        combined_context += "\n\nIMPORTANT: Use a Markdown table for any comparisons, rankings, or lists, and ensure double spacing between sections."

    # 3. Synthesis Pass
    ai_resp = await call_ai_orchestration(SYSTEM_PROMPT, combined_context, {})
    
    # 4. Extract CHART_SELECTION
    formatted_resp = ai_resp.strip()
    chart_selection = {"main": "sales_trend", "pie": "sales_distribution_pie"} # safe fallback
    
    if "### CHART_SELECTION" in formatted_resp:
        parts = formatted_resp.split("### CHART_SELECTION")
        formatted_resp = parts[0].strip()
        json_str = parts[1].strip()
        # Clean markdown wrappers if hallucinated
        json_str = re.sub(r'```[a-zA-Z]*\n', '', json_str)
        json_str = re.sub(r'\n```', '', json_str).strip()
        try:
            parsed = json.loads(json_str)
            if "main" in parsed: chart_selection["main"] = parsed["main"]
            if "pie" in parsed: chart_selection["pie"] = parsed["pie"]
        except Exception as e:
            print(f"[NK-AI] Warn: Failed to parse CHART_SELECTION json {e}")

    # Build final UI alert_data payload from the AI's selection
    final_alert_data = {}
    
    default_main = list(available_charts.keys())[0] if available_charts else None
    main_id = chart_selection.get("main", default_main)
    if main_id not in available_charts:
        main_id = default_main
        
    if main_id and main_id in available_charts:
        mc = available_charts[main_id]
        if "historical" in mc:
            final_alert_data["labels"] = mc["labels"]
            final_alert_data["historical"] = mc["historical"]
            if "forecast" in mc and mc["forecast"]:
                final_alert_data["forecast"] = mc["forecast"]
        elif "type" in mc:
            final_alert_data["type"] = mc["type"]
            final_alert_data["labels"] = mc["labels"]
            final_alert_data["data"] = mc["data"]
            
    pie_id = chart_selection.get("pie")
    if pie_id not in available_charts:
        pie_keys = [k for k in available_charts.keys() if "pie" in k]
        pie_id = pie_keys[0] if pie_keys else None
        
    if pie_id and pie_id in available_charts:
        pc = available_charts[pie_id]
        if "pie_labels" in pc:
            final_alert_data["pie_labels"] = pc["pie_labels"]
            final_alert_data["pie_data"] = pc["pie_data"]
            if "pie_type" in pc:
                final_alert_data["pie_type"] = pc["pie_type"]
    
    return AIResponse(response=formatted_resp, action_type=action_type, alert_data=final_alert_data)


@router.post("/get-sales-prediction", response_model=AIResponse)
async def get_sales_prediction(req: QueryRequest):
    raw_math, metadata = analytics_engine.run_sales_prediction()
    
    # Explicitly telling the AI how to handle "list" requests in the user prompt
    user_context = f"User asked: {req.query}\n\nRaw Core Engine Data: {raw_math}"
    if "list" in req.query.lower():
        user_context += "\n\nIMPORTANT: Use a Markdown table for the products and ensure double spacing between sections. Extract ALL product names directly from the Raw Core Engine Data."

    ai_resp = await call_ai_orchestration(SYSTEM_PROMPT, user_context, metadata)
    
    # Clean up: Ensure there are no weird trailing spaces that break Markdown
    formatted_resp = ai_resp.strip() 

    return AIResponse(
        response=formatted_resp, 
        action_type="sales_view", 
        alert_data=metadata
    )
@router.post("/get-liquidity-risk", response_model=AIResponse)
async def get_liquidity_risk(req: QueryRequest):
    raw_math, metadata = analytics_engine.run_liquidity_risk()
    ai_resp = await call_ai_orchestration(SYSTEM_PROMPT, f"User asked: {req.query}. Raw data: {raw_math}", metadata)
    return AIResponse(response=ai_resp, action_type="legal_notice", alert_data=metadata)

@router.post("/get-inventory-opt", response_model=AIResponse)
async def get_inventory_opt(req: QueryRequest):
    raw_math, metadata = analytics_engine.run_inventory_optimization()
    ai_resp = await call_ai_orchestration(SYSTEM_PROMPT, f"User asked: {req.query}. Raw data: {raw_math}", metadata)
    return AIResponse(response=ai_resp, action_type="liquidate_stock", alert_data=metadata)

@router.post("/get-tax-delta", response_model=AIResponse)
async def get_tax_delta(req: QueryRequest):
    raw_math, metadata = analytics_engine.run_tax_delta()
    ai_resp = await call_ai_orchestration(SYSTEM_PROMPT, f"User asked: {req.query}. Raw data: {raw_math}", metadata)
    return AIResponse(response=ai_resp, action_type="reconcile_tax", alert_data=metadata)

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
