import sys
import os

# Mount templates with absolute path
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import logging

from .routers import home, api

# Configure logging
logging.basicConfig(level=logging.INFO)

app = FastAPI()


template_path = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "app", "templates"
)
templates = Jinja2Templates(directory=template_path)

# Include routers
app.include_router(home.router)
app.include_router(api.router, prefix="/api")
