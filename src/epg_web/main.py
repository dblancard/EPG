"""FastAPI application entry point."""
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI(title="EPG Web Service", description="Electronic Program Guide Web Service")

# Mount static files and templates
static_path = Path(__file__).parent / "static"
templates_path = Path(__file__).parent / "templates"

app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
templates = Jinja2Templates(directory=str(templates_path))

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the main page."""
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "title": "EPG Web Service"}
    )

# Import and include API routers
from epg_web.api import routes as api_routes
app.include_router(api_routes.router, prefix="/api")