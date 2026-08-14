import sys
import os

# Add the backend directory to the Python path so local imports resolve correctly
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend'))

# Import the FastAPI application
from app.main import app
