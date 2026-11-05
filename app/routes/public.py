import os
from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.responses import HTMLResponse, PlainTextResponse, Response
from fastapi.templating import Jinja2Templates

from app.database import test_connection
from app.services.auth_service import get_current_user_optional

router = APIRouter(tags=["Public Pages"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
def home_page(request: Request, current_user = Depends(get_current_user_optional)):
    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={
            "request": request,
            "current_user": current_user,
            "title": "MindTheSpec — Requirement Interpretation & Divergence Detection",
            "meta_description": "Catch conflicting software requirement interpretations before development begins using structured blind reviews and deterministic divergence detection.",
        },
    )

@router.get("/about", response_class=HTMLResponse)
def about_page(request: Request, current_user = Depends(get_current_user_optional)):
    return templates.TemplateResponse(
        request=request,
        name="about.html",
        context={
            "request": request,
            "current_user": current_user,
            "title": "About MindTheSpec — Evidence-Based Requirement Analysis",
            "meta_description": "Learn how MindTheSpec prevents development mistakes through blind interpretation collection and deterministic discrepancy detection.",
        },
    )

@router.get("/privacy", response_class=HTMLResponse)
def privacy_page(request: Request, current_user = Depends(get_current_user_optional)):
    return templates.TemplateResponse(
        request=request,
        name="privacy.html",
        context={
            "request": request,
            "current_user": current_user,
            "title": "Privacy Policy — MindTheSpec",
            "meta_description": "Truthful privacy policy describing local and prototype data handling, role-based isolation, and session security.",
        },
    )

@router.get("/terms", response_class=HTMLResponse)
def terms_page(request: Request, current_user = Depends(get_current_user_optional)):
    return templates.TemplateResponse(
        request=request,
        name="terms.html",
        context={
            "request": request,
            "current_user": current_user,
            "title": "Terms of Service — MindTheSpec",
            "meta_description": "Terms of service and prototype software evaluation agreement for MindTheSpec.",
        },
    )

@router.get("/health")
def health_check():
    """Public health endpoint. Strictly does not leak database credentials or internal stack details."""
    try:
        db_status = test_connection()
        return {
            "status": "healthy",
            "database": "connected" if db_status else "disconnected",
            "version": "2.0.0",
        }
    except Exception:
        return Response(
            content='{"status":"degraded","database":"unavailable"}',
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            media_type="application/json",
        )

@router.get("/robots.txt", response_class=PlainTextResponse)
def robots_txt():
    """Directs crawlers to public indexable pages, excluding private app workspace paths."""
    return (
        "User-agent: *\n"
        "Allow: /\n"
        "Allow: /about\n"
        "Allow: /privacy\n"
        "Allow: /terms\n"
        "Disallow: /app/\n"
        "Disallow: /api/\n"
        "Disallow: /login\n"
        "Disallow: /register\n"
        "\n"
        "Sitemap: https://mindthespec.local/sitemap.xml\n"
    )

@router.get("/sitemap.xml")
def sitemap_xml():
    """Valid XML sitemap containing only public indexable URLs."""
    content = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://mindthespec.local/</loc>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>https://mindthespec.local/about</loc>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://mindthespec.local/privacy</loc>
    <changefreq>monthly</changefreq>
    <priority>0.3</priority>
  </url>
  <url>
    <loc>https://mindthespec.local/terms</loc>
    <changefreq>monthly</changefreq>
    <priority>0.3</priority>
  </url>
</urlset>
"""
    return Response(content=content, media_type="application/xml")
