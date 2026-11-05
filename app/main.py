import os
from fastapi import FastAPI, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.routes import public, views, auth, projects, requirements, sessions

app = FastAPI(
    title="MindTheSpec",
    description="Requirement Interpretation & Divergence Detection Platform",
    version="2.0.0",
)

# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

# Static assets
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Include API and view routers
app.include_router(public.router)
app.include_router(views.router)
app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(requirements.router)
app.include_router(sessions.router)

templates = Jinja2Templates(directory="app/templates")

# Custom 404 Handler
@app.exception_handler(404)
async def custom_404_handler(request: Request, exc):
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "Resource not found"},
        )
    return templates.TemplateResponse(
        request=request,
        name="404.html",
        context={"request": request, "title": "404 Not Found — MindTheSpec"},
        status_code=status.HTTP_404_NOT_FOUND,
    )
