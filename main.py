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
# --- UPDATED: Code Generation Prompt to enforce detailed Markdown tables ---
CODE_GENERATION_PROMPT = """
You are a Senior Data Scientist for NK Protein.
Your goal is to write a valid Python script using `pandas` to answer the user's specific business query.

Here are the available CSV datasets and their exact columns:
{schema}

REQUIREMENTS:
1. Import necessary libraries (import pandas as pd, import numpy as np, import json).
2. Load the relevant CSV files using pd.read_csv() with the exact paths provided in the schema.
3. Perform the necessary calculations. 
   - IMPORTANT: If the user asks for a PREDICTION (e.g. "Predict next quarter"), provide focusing on the forecast. Display only 4-6 most recent historical points for context in the table, NOT the full 4-year history.
   - If the user explicitly asks for "trends", "history", or "since 2022", then include the FULL date range. 
   - If the user uses "now" or "recently", filter the data to the most recent year/quarter relative to Feb 2026.
   - For "Which [entities]", PREFER GROUPING AND AGGREGATING (e.g. `df.groupby('customer_name')`).
4. DETERMINE THE OPTIMAL CHART TYPE based on the user's intent and the shape of the resulting data:
   - "line": Use for continuous time-series data, historical trends, and forecasting.
   - "bar": Use for categorical comparisons, discrete rankings (e.g., top 10 customers), or cross-sectional data.
   - "pie": Use ONLY for composition, market share, or parts-of-a-whole where percentages sum to 100%.
   - "scatter": Use for correlation, variance, or comparing two independent numeric variables.
5. You MUST create a final Python dictionary named exactly `dynamic_result` at the global scope of your script.
6. The `dynamic_result` dictionary MUST strictly follow this structure:
{{
    "raw_math": "A detailed explanation of findings. IMPORTANT: Include concise tables. Use `to_markdown(index=False)`.",
    "action_type": "sales_view", 
    "chart_data": {{
        "type": "<INSERT_DYNAMIC_CHART_TYPE_HERE>", # E.g., "line", "bar", "pie", or "scatter" based on Rule 4
        "title": "A concise title for the chart",
        "labels": ["Label1", "Label2"], # X-axis items, pie slices, etc. Ensure these are lists of native Python strings/ints.
        "data": [10.5, 20.2] # Y-axis values. Ensure these are native Python floats/ints, NOT Pandas Series.
    }}
}}

OUTPUT FORMAT:
Output ONLY the raw Python code. Do NOT wrap it in markdown block quotes (e.g., no ```python). Do not include any text before or after the code.
"""

# --- UPDATED: Synthesis Prompt to stop restricting column counts ---
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
   - Provide RICH, COMPREHENSIVE tables. Do NOT restrict the table to 2-3 columns. Ensure all informative headers from the raw data (e.g., Region, Category, Invoice No, Quantity, Margin %, Days Stuck, Status) are included to give maximum context.
   - Always include the header separator line (e.g., |---|---|---|).
   - Format large currency numbers nicely (e.g., ₹1.5L or ₹1,50,000).
   - For Risk Status, use categorical tags: **High**, **Medium**, or **Low** where applicable.
5. TONE: No conversational filler. Be cold, analytical, and prescriptive.
6. ANTI-HALLUCINATION: Extract ALL metrics EXCLUSIVELY from the provided Raw Data context. Do NOT invent dates, numbers, or products.

EXAMPLE STRUCTURE:
### ⚡ Accessing NK AI...

| Product / Customer | Region | Category | Amount/Value | Days Overdue/Stuck | Risk Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| FreshMart Vadodara | Gujarat | Retail Chain | ₹50,867 | 45 Days | **Medium** |

**Executive Summary**: [Summary text based on data]

**Strategic Recommendation**: [Action text based on data]
"""
@router.post("/ask-nk-ai", response_model=AIResponse)
async def ask_nk_ai(req: QueryRequest):
    print(f"[NK-AI] Received Dynamic Query: {req.query}")
    
    # 1. Fetch Schema Context
    schema_context = analytics_engine.get_database_schema()
    print(schema_context)
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


app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=6969)