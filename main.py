from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict
import analytics_engine
from llm_service import call_ai_orchestration
import json
import re
import traceback

app = FastAPI(
    title="NK Executive Command API",
    description="API for NK Protein POC that generates AI responses backed by dynamic Pandas execution.",
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
    alert_data: Dict[str, Any] = {} 

# --- NEW: Code Generation Prompt ---
CODE_GENERATION_PROMPT = """
You are a Senior Data Scientist for NK Protein.
Your goal is to write a valid Python script using `pandas` to answer the user's specific business query.

Here are the available CSV datasets and their exact columns:
{schema}

REQUIREMENTS:
1. Import necessary libraries (import pandas as pd, import numpy as np, import json).
2. Load the relevant CSV files using pd.read_csv() with the exact paths provided in the schema.
3. Perform the necessary calculations to answer the user's query. Handle any potential NaN values.
4. You MUST create a final Python dictionary named exactly `dynamic_result` at the global scope of your script.
5. The `dynamic_result` dictionary MUST strictly follow this structure:
{{
    "raw_math": "A detailed, plain-text explanation containing all your final calculated numbers, lists, or findings. Make it comprehensive.",
    "action_type": "sales_view", # Options: "sales_view", "liquidate_stock", "legal_notice", or "reconcile_tax" based on the context.
    "chart_data": {{
        # Choose ONE type of chart that best fits the data: "bar", "pie", or "line"
        "type": "bar",
        "labels": ["List", "of", "X-axis", "labels"],
        "data": [10, 20, 30] # Y-axis data
        # If choosing a pie chart, use "pie_labels" and "pie_data" instead.
    }}
}}

OUTPUT FORMAT:
Output ONLY the raw Python code. Do NOT wrap it in markdown block quotes (e.g., no ```python). Do not include any text before or after the code.
"""

# --- UPDATED: Synthesis Prompt (Removed CHART_SELECTION) ---
SYSTEM_PROMPT = """
You are NK AI, an authoritative executive AI assistant for NK Protein.

STRICT OUTPUT FORMATTING RULES:
1. Start with: "### ⚡ Accessing NK AI..."
2. Use DOUBLE NEWLINES (\n\n) between every section, header, and list item. 
3. If a list or table is requested (or if the raw data provides list-based data):
   - Provide the Table/List FIRST.
   - Follow with the 'Executive Summary'.
   - End with 'Strategic Recommendation'.
4. TABLE RULES: 
   - Always include the header separator line (e.g., |---|---|).
   - OMIT headers/columns that contain mostly "Not Available" or empty data.
   - For regular status queries, use headers like: "Product/Customer", "Current Value", "Risk Status", "Days Overdue/Stuck".
   - For Risk Status, use categorical tags: **High**, **Medium**, or **Low** where applicable.
5. TONE: No conversational filler. Be cold, analytical, and prescriptive.
6. ANTI-HALLUCINATION: Extract ALL metrics EXCLUSIVELY from the provided Raw Data context. Do NOT invent dates, numbers, or products.

EXAMPLE STRUCTURE:
### ⚡ Accessing NK AI...

| Item | Current | Risk |
| :--- | :--- | :--- |
| Item A | ₹10.5L | **Medium** |

**Executive Summary**: [Summary text based on data]

**Strategic Recommendation**: [Action text based on data]
"""

@router.post("/ask-nk-ai", response_model=AIResponse)
async def ask_nk_ai(req: QueryRequest):
    print(f"[NK-AI] Received Dynamic Query: {req.query}")
    
    # 1. Fetch Schema Context
    schema_context = analytics_engine.get_database_schema()
    prompt = CODE_GENERATION_PROMPT.format(schema=schema_context)
    
    # 2. Call LLM to generate Python Code
    generated_code_response = await call_ai_orchestration(prompt, f"User Query: {req.query}", {})
    
    # Clean up any potential markdown wrappers the LLM might hallucinate
    clean_code = generated_code_response.strip()
    clean_code = re.sub(r'^```[a-zA-Z]*\n', '', clean_code)
    clean_code = re.sub(r'\n```$', '', clean_code).strip()
    
    print("\n--- [NK-AI] EXECUTING DYNAMIC CODE ---")
    print(clean_code)
    print("--------------------------------------\n")
    
    # 3. Securely Execute Code (Sandbox Environment)
    local_vars = {}
    try:
        # Note: In a production environment, you would run this in an isolated Docker container
        exec(clean_code, globals(), local_vars)
        
        dynamic_result = local_vars.get('dynamic_result', {})
        if not dynamic_result:
             raise ValueError("The script did not produce a 'dynamic_result' dictionary.")
             
        raw_math = dynamic_result.get("raw_math", "Data processed successfully.")
        action_type = dynamic_result.get("action_type", "sales_view")
        chart_data = dynamic_result.get("chart_data", {})
        
    except Exception as e:
        print(f"[NK-AI] Code Execution Error: {e}")
        traceback.print_exc()
        
        # Fallback to standard sales function if dynamic execution fails
        raw_math, meta = analytics_engine.run_sales_prediction()
        action_type = "sales_view"
        chart_data = meta.get("chart_data", {})
        raw_math = f"Error in dynamic processing. Defaulting to general overview. Raw: {raw_math}"

    # 4. Final Synthesis Pass
    combined_context = f"User asked: {req.query}\n\nDynamically Synthesized Raw Data from Custom Script:\n{raw_math}"
    
    if "list" in req.query.lower() or "top" in req.query.lower() or "worst" in req.query.lower():
        combined_context += "\n\nIMPORTANT: Use a Markdown table for any comparisons, rankings, or lists, and ensure double spacing between sections."

    ai_resp = await call_ai_orchestration(SYSTEM_PROMPT, combined_context, {})
    formatted_resp = ai_resp.strip()
    
    return AIResponse(
        response=formatted_resp, 
        action_type=action_type, 
        alert_data=chart_data # Direct mapping of the generated chart data to UI alert_data
    )


# --- Existing Specific Endpoints (Kept for backwards compatibility) ---

@router.post("/get-sales-prediction", response_model=AIResponse)
async def get_sales_prediction(req: QueryRequest):
    raw_math, metadata = analytics_engine.run_sales_prediction()
    user_context = f"User asked: {req.query}\n\nRaw Core Engine Data: {raw_math}"
    if "list" in req.query.lower():
        user_context += "\n\nIMPORTANT: Use a Markdown table for the products and ensure double spacing between sections."
    ai_resp = await call_ai_orchestration(SYSTEM_PROMPT, user_context, metadata)
    return AIResponse(response=ai_resp.strip(), action_type="sales_view", alert_data=metadata)

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

@router.post("/get-profitability", response_model=AIResponse)
async def get_profitability(req: QueryRequest):
    raw_math, metadata = analytics_engine.run_profitability_analysis()
    ai_resp = await call_ai_orchestration(SYSTEM_PROMPT, f"User asked: {req.query}. Raw data: {raw_math}", metadata)
    return AIResponse(response=ai_resp, action_type="sales_view", alert_data=metadata)

@router.post("/get-working-capital", response_model=AIResponse)
async def get_working_capital(req: QueryRequest):
    raw_math, metadata = analytics_engine.run_working_capital_analysis()
    ai_resp = await call_ai_orchestration(SYSTEM_PROMPT, f"User asked: {req.query}. Raw data: {raw_math}", metadata)
    return AIResponse(response=ai_resp, action_type="liquidate_stock", alert_data=metadata)

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=6969)