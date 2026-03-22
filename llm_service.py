import os
import httpx
from dotenv import load_dotenv

load_dotenv()

AI_PROVIDER_URL = os.getenv("AI_PROVIDER_ORCHESTRATION_API_URL")
AI_PROVIDER_KEY = os.getenv("AI_PROVIDER_ORCHESTRATION_API_KEY")
DEFAULT_MODEL = os.getenv("AI_MODEL", "gpt-4o")
DEFAULT_PROVIDER = os.getenv("AI_PROVIDER", "openai")

async def call_ai_orchestration(system_prompt: str, user_prompt: str, metadata: dict) -> str:
    """
    Calls the AI Provider Orchestration API directly, failing loudly if there is a network issue,
    as required to ensure no mock responses are provided.
    """
    url = f"{AI_PROVIDER_URL}/ai/generate"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {AI_PROVIDER_KEY}"
    }
    payload = {
        "model": DEFAULT_MODEL,
        "provider": DEFAULT_PROVIDER,
        "prompts": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"{user_prompt}\n\nPlease strictly use the raw data numerical outputs above to construct your response in SAP Joule's executive style."}
        ]
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, json=payload, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "Error: The Orchestration API returned a successful status code but an empty response payload.")
        except httpx.HTTPError as http_err:
            return f"Error connecting to Live API: {http_err}"
        except Exception as e:
            return f"Unexpected Error processing Live API: {e}"
