import sys
import os

# Ensure the root directory is in the python path so it can find analytics_engine.py and llm_service.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the FastAPI app from main.py
from main import app

# Export for Vercel
application = app
