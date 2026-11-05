from typing import Optional
from fastapi import APIRouter, Depends, Request, Response, Form, status, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.config import SESSION_COOKIE_NAME, SESSION_EXPIRE_HOURS
from app.database import get_db
from app.models.user import User
from app.models.project import Project, ProjectMember
from app.models.requirement import Requirement, RequirementVersion
from app.models.session import InterpretationSession, Interpretation
from app.models.divergence import Divergence
from app.models.resolution import Resolution
from app.services.auth_service import (
    authenticate_user,
    register_user,
    create_session_token,
    get_current_user_optional,
)
from app.services.project_service import ProjectService
from app.services.requirement_service import RequirementService
from app.services.session_service import SessionService
from app.services.divergence_service import DivergenceService
from app.services.resolution_service import ResolutionService
from app.services.audit_service import AuditService

router = APIRouter(tags=["Web Views"])
templates = Jinja2Templates(directory="app/templates")

def require_auth(request: Request, db: Session) -> User:
    user = get_current_user_optional(request, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": f"/login?next={request.url.path}"},
        )
    return user

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, next: Optional[str] = "/app", error: Optional[str] = None):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"request": request, "next": next, "error": error, "title": "Sign In — MindTheSpec"},
    )

@router.post("/login")
def login_action(
    request: Request,
    response: Response,
    email: str = Form(...),
    password: str = Form(...),
    next: Optional[str] = "/app",
    db: Session = Depends(get_db),
):
    user = authenticate_user(db, email, password)
    if not user:
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={"request": request, "next": next, "error": "Invalid email or password", "title": "Sign In — MindTheSpec"},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    token = create_session_token(user.user_id)
    redirect_target = next if next and next.startswith("/") else "/app"
    res = RedirectResponse(url=redirect_target, status_code=status.HTTP_303_SEE_OTHER)
    res.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=SESSION_EXPIRE_HOURS * 3600,
        httponly=True,
        samesite="lax",
    )
    return res

@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request, error: Optional[str] = None):
    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={"request": request, "error": error, "title": "Register — MindTheSpec"},
    )

@router.post("/register")
def register_action(
    request: Request,
    email: str = Form(...),
    name: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        user = register_user(db, email, name, password)
        token = create_session_token(user.user_id)
        res = RedirectResponse(url="/app", status_code=status.HTTP_303_SEE_OTHER)
        res.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=token,
            max_age=SESSION_EXPIRE_HOURS * 3600,
            httponly=True,
            samesite="lax",
        )
        return res
    except HTTPException as e:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={"request": request, "error": e.detail, "title": "Register — MindTheSpec"},
            status_code=e.status_code,
        )

@router.get("/logout")
def logout_action():
    res = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    res.delete_cookie(SESSION_COOKIE_NAME)
    return res

@router.get("/app", response_class=HTMLResponse)
def dashboard_view(request: Request, db: Session = Depends(get_db)):
    """FR-08: Real metrics derived from database counts. No fake numbers."""
    user = require_auth(request, db)
    projects = ProjectService.list_accessible_projects(db, user.user_id)
    project_ids = [p.project_id for p in projects]

    # Real DB counts
    active_projects_count = len(projects)
    total_requirements_count = (
        db.query(Requirement).filter(Requirement.project_id.in_(project_ids)).count() if project_ids else 0
    )
    open_sessions_count = (
        db.query(InterpretationSession)
        .join(RequirementVersion, InterpretationSession.requirement_version_id == RequirementVersion.version_id)
        .join(Requirement, RequirementVersion.requirement_id == Requirement.requirement_id)
        .filter(Requirement.project_id.in_(project_ids), InterpretationSession.status == "collecting")
        .count()
        if project_ids
        else 0
    )
    unresolved_divergences_count = (
        db.query(Divergence)
        .join(InterpretationSession, Divergence.session_id == InterpretationSession.session_id)
        .join(RequirementVersion, InterpretationSession.requirement_version_id == RequirementVersion.version_id)
        .join(Requirement, RequirementVersion.requirement_id == Requirement.requirement_id)
        .filter(Requirement.project_id.in_(project_ids), Divergence.review_status == "open")
        .count()
        if project_ids
        else 0
    )

    return templates.TemplateResponse(
        request=request,
        name="app/dashboard.html",
        context={
            "request": request,
            "current_user": user,
            "projects": projects,
            "stats": {
                "active_projects": active_projects_count,
                "total_requirements": total_requirements_count,
                "open_sessions": open_sessions_count,
                "unresolved_divergences": unresolved_divergences_count,
            },
            "title": "Dashboard — MindTheSpec",
        },
    )

@router.get("/app/projects/{project_id}", response_class=HTMLResponse)
def project_detail_view(project_id: int, request: Request, db: Session = Depends(get_db)):
    user = require_auth(request, db)
    project, role = ProjectService.require_member(db, project_id, user.user_id)
    requirements = RequirementService.list_requirements(db, project_id, user.user_id)
    members = db.query(ProjectMember).filter(ProjectMember.project_id == project_id).all()
    history = AuditService.get_project_history(db, project_id, limit=5)

    return templates.TemplateResponse(
        request=request,
        name="app/project_detail.html",
        context={
            "request": request,
            "current_user": user,
            "project": project,
            "role": role,
            "requirements": requirements,
            "members": members,
            "recent_history": history,
            "title": f"{project.project_name} — MindTheSpec",
        },
    )

@router.get("/app/requirements/{requirement_id}", response_class=HTMLResponse)
def requirement_detail_view(requirement_id: int, request: Request, db: Session = Depends(get_db)):
    user = require_auth(request, db)
    req = RequirementService.get_requirement(db, requirement_id, user.user_id)
    role = ProjectService.get_user_role(db, req.project_id, user.user_id)
    sessions = (
        db.query(InterpretationSession)
        .join(RequirementVersion, InterpretationSession.requirement_version_id == RequirementVersion.version_id)
        .filter(RequirementVersion.requirement_id == requirement_id)
        .order_by(InterpretationSession.created_at.desc())
        .all()
    )

    return templates.TemplateResponse(
        request=request,
        name="app/requirement_detail.html",
        context={
            "request": request,
            "current_user": user,
            "requirement": req,
            "role": role,
            "sessions": sessions,
            "title": f"{req.req_code}: {req.title} — MindTheSpec",
        },
    )

@router.get("/app/sessions/{session_id}", response_class=HTMLResponse)
def session_detail_view(session_id: int, request: Request, db: Session = Depends(get_db)):
    """FR-04: Blind interpretation collection view."""
    user = require_auth(request, db)
    session = SessionService.get_session(db, session_id, user.user_id)
    role = ProjectService.get_user_role(db, session.requirement_version.requirement.project_id, user.user_id)

    # Safe participation summary (counts only)
    participation = SessionService.get_participation_summary(db, session_id)

    # Server-side filtered interpretations (own only before lock!)
    my_interpretations = SessionService.get_session_interpretations(db, session_id, user.user_id)

    return templates.TemplateResponse(
        request=request,
        name="app/session_detail.html",
        context={
            "request": request,
            "current_user": user,
            "session": session,
            "role": role,
            "participation": participation,
            "my_interpretations": my_interpretations,
            "title": f"Session #{session.session_id} ({session.status.upper()}) — MindTheSpec",
        },
    )

@router.get("/app/sessions/{session_id}/compare", response_class=HTMLResponse)
def session_compare_view(session_id: int, request: Request, db: Session = Depends(get_db)):
    """FR-05: Side-by-side evidence & divergence findings view (locked sessions only)."""
    user = require_auth(request, db)
    session = SessionService.get_session(db, session_id, user.user_id)
    role = ProjectService.get_user_role(db, session.requirement_version.requirement.project_id, user.user_id)

    if session.status in ("draft", "collecting"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Session is still collecting interpretations. Divergence analysis is confidential until session lock.",
        )

    all_interpretations = SessionService.get_session_interpretations(db, session_id, user.user_id)
    divergences = DivergenceService.get_session_divergences(db, session_id)
    resolution = ResolutionService.get_resolution(db, session_id, user.user_id)

    return templates.TemplateResponse(
        request=request,
        name="app/session_compare.html",
        context={
            "request": request,
            "current_user": user,
            "session": session,
            "role": role,
            "interpretations": all_interpretations,
            "divergences": divergences,
            "resolution": resolution,
            "title": f"Divergence Report #{session.session_id} — MindTheSpec",
        },
    )

@router.get("/app/sessions/{session_id}/resolution", response_class=HTMLResponse)
def session_resolution_view(session_id: int, request: Request, db: Session = Depends(get_db)):
    """FR-06: Resolution recording / viewing screen."""
    user = require_auth(request, db)
    session = SessionService.get_session(db, session_id, user.user_id)
    role = ProjectService.get_user_role(db, session.requirement_version.requirement.project_id, user.user_id)
    divergences = DivergenceService.get_session_divergences(db, session_id)
    resolution = ResolutionService.get_resolution(db, session_id, user.user_id)

    return templates.TemplateResponse(
        request=request,
        name="app/session_resolution.html",
        context={
            "request": request,
            "current_user": user,
            "session": session,
            "role": role,
            "divergences": divergences,
            "resolution": resolution,
            "title": f"Resolution: Session #{session.session_id} — MindTheSpec",
        },
    )

@router.get("/app/projects/{project_id}/history", response_class=HTMLResponse)
def project_history_view(project_id: int, request: Request, db: Session = Depends(get_db)):
    """FR-07: Full chronological audit trail."""
    user = require_auth(request, db)
    project, role = ProjectService.require_member(db, project_id, user.user_id)
    logs = AuditService.get_project_history(db, project_id, limit=200)

    return templates.TemplateResponse(
        request=request,
        name="app/project_history.html",
        context={
            "request": request,
            "current_user": user,
            "project": project,
            "role": role,
            "logs": logs,
            "title": f"Audit History: {project.project_name} — MindTheSpec",
        },
    )
