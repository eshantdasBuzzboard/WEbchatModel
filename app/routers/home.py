from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import logging

from test_data import (
    main_payload_test_data,
    webpage_content_output_test_data,
    business_info,
)

router = APIRouter()
templates = Jinja2Templates(directory="templates")
logger = logging.getLogger(__name__)


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "main_payload_data": main_payload_test_data,
            "webpage_content_data": webpage_content_output_test_data,
            "business_info": business_info,
        },
    )
