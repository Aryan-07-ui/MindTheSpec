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
        .filter(Requirement.project_id.in_(project_ids), InterpretationSession.status.in_(["collecting", "open"]))
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

@router.post("/app/projects/create")
def project_create_action(
    request: Request,
    title: str = Form(...),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    user = require_auth(request, db)
    try:
        project = ProjectService.create_project(db, title=title, description=description, owner_id=user.user_id)
        return RedirectResponse(url=f"/app/projects/{project.project_id}", status_code=status.HTTP_303_SEE_OTHER)
    except HTTPException as e:
        return RedirectResponse(url="/app?error=" + str(e.detail), status_code=status.HTTP_303_SEE_OTHER)

@router.get("/app/projects/{project_id}/edit", response_class=HTMLResponse)
def project_edit_view(project_id: int, request: Request, error: Optional[str] = None, db: Session = Depends(get_db)):
    user = require_auth(request, db)
    project = ProjectService.require_owner(db, project_id, user.user_id)
    return templates.TemplateResponse(
        request=request,
        name="app/project_edit.html",
        context={
            "request": request,
            "current_user": user,
            "project": project,
            "error": error,
            "title": f"Edit {project.project_name} — MindTheSpec",
        },
    )

@router.post("/app/projects/{project_id}/edit")
def project_edit_action(
    project_id: int,
    request: Request,
    title: str = Form(...),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    user = require_auth(request, db)
    try:
        ProjectService.update_project(db, project_id, user.user_id, title=title, description=description)
        return RedirectResponse(url=f"/app/projects/{project_id}", status_code=status.HTTP_303_SEE_OTHER)
    except HTTPException as e:
        project, _ = ProjectService.require_member(db, project_id, user.user_id)
        return templates.TemplateResponse(
            request=request,
            name="app/project_edit.html",
            context={
                "request": request,
                "current_user": user,
                "project": project,
                "error": e.detail,
                "title": f"Edit {project.project_name} — MindTheSpec",
            },
            status_code=e.status_code,
        )

@router.post("/app/projects/{project_id}/delete")
def project_delete_action(
    project_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    user = require_auth(request, db)
    ProjectService.delete_project(db, project_id, user.user_id)
    return RedirectResponse(url="/app", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/app/projects/{project_id}/members/add")
def project_member_add_action(
    project_id: int,
    request: Request,
    email: str = Form(...),
    role: str = Form("developer"),
    db: Session = Depends(get_db),
):
    user = require_auth(request, db)
    try:
        ProjectService.add_member(db, project_id, user.user_id, email, role)
        return RedirectResponse(url=f"/app/projects/{project_id}", status_code=status.HTTP_303_SEE_OTHER)
    except HTTPException as e:
        return RedirectResponse(url=f"/app/projects/{project_id}?error={e.detail}", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/app/projects/{project_id}/members/remove")
def project_member_remove_action(
    project_id: int,
    request: Request,
    user_id: int = Form(...),
    db: Session = Depends(get_db),
):
    user = require_auth(request, db)
    try:
        ProjectService.remove_member(db, project_id, user.user_id, user_id)
        return RedirectResponse(url=f"/app/projects/{project_id}", status_code=status.HTTP_303_SEE_OTHER)
    except HTTPException as e:
        return RedirectResponse(url=f"/app/projects/{project_id}?error={e.detail}", status_code=status.HTTP_303_SEE_OTHER)

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

@router.get("/app/requirements/{requirement_id}/edit", response_class=HTMLResponse)
def requirement_edit_view(requirement_id: int, request: Request, error: Optional[str] = None, db: Session = Depends(get_db)):
    user = require_auth(request, db)
    req = RequirementService.get_requirement(db, requirement_id, user.user_id)
    role = ProjectService.get_user_role(db, req.project_id, user.user_id)
    if role not in ("owner", "analyst"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owners and analysts can edit requirements")
    return templates.TemplateResponse(
        request=request,
        name="app/requirement_edit.html",
        context={
            "request": request,
            "current_user": user,
            "requirement": req,
            "role": role,
            "error": error,
            "title": f"Edit {req.req_code} — MindTheSpec",
        },
    )

@router.post("/app/requirements/{requirement_id}/edit")
def requirement_edit_action(
    requirement_id: int,
    request: Request,
    title: str = Form(...),
    description: str = Form(...),
    acceptance_criteria: Optional[str] = Form(None),
    priority: Optional[str] = Form("medium"),
    status: Optional[str] = Form("active"),
    db: Session = Depends(get_db),
):
    user = require_auth(request, db)
    try:
        RequirementService.update_requirement(
            db=db,
            requirement_id=requirement_id,
            user_id=user.user_id,
            title=title,
            description=description,
            acceptance_criteria=acceptance_criteria,
            priority=priority,
            status_val=status,
        )
        return RedirectResponse(url=f"/app/requirements/{requirement_id}", status_code=status.HTTP_303_SEE_OTHER)
    except HTTPException as e:
        req = RequirementService.get_requirement(db, requirement_id, user.user_id)
        role = ProjectService.get_user_role(db, req.project_id, user.user_id)
        return templates.TemplateResponse(
            request=request,
            name="app/requirement_edit.html",
            context={
                "request": request,
                "current_user": user,
                "requirement": req,
                "role": role,
                "error": e.detail,
                "title": f"Edit {req.req_code} — MindTheSpec",
            },
            status_code=e.status_code,
        )

@router.post("/app/requirements/{requirement_id}/delete")
def requirement_delete_action(
    requirement_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    user = require_auth(request, db)
    req = RequirementService.get_requirement(db, requirement_id, user.user_id)
    project_id = req.project_id
    RequirementService.delete_requirement(db, requirement_id, user.user_id)
    return RedirectResponse(url=f"/app/projects/{project_id}", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/app/requirements/{requirement_id}/sessions/create")
def requirement_create_session_action(
    requirement_id: int,
    request: Request,
    mode: str = Form("standard"),
    db: Session = Depends(get_db),
):
    user = require_auth(request, db)
    session = SessionService.create_session(db, requirement_id, user.user_id, mode=mode)
    return RedirectResponse(url=f"/app/sessions/{session.session_id}", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/app/sessions/{session_id}", response_class=HTMLResponse)
def session_detail_view(session_id: int, request: Request, db: Session = Depends(get_db)):
    """FR-04: Blind interpretation collection view."""
    user = require_auth(request, db)
    session = SessionService.get_session(db, session_id, user.user_id)
    project_id = session.requirement_version.requirement.project_id
    role = ProjectService.get_user_role(db, project_id, user.user_id)

    # Safe participation summary (counts only)
    participation = SessionService.get_participation_summary(db, session_id)

    # Server-side filtered interpretations (own only before lock/reveal!)
    my_interpretations = SessionService.get_session_interpretations(db, session_id, user.user_id)

    # Project members for progress status
    members = db.query(ProjectMember).filter(ProjectMember.project_id == project_id).all()

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
            "members": members,
            "title": f"Session #{session.session_id} ({session.status.upper()}) — MindTheSpec",
        },
    )

@router.post("/app/sessions/{session_id}/submit")
def session_submit_action(
    session_id: int,
    request: Request,
    perspective: str = Form(...),
    expected_behavior: str = Form(...),
    assumptions: Optional[str] = Form(None),
    acceptance_criteria: Optional[str] = Form(None),
    edge_cases: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    actor: Optional[str] = Form(None),
    delivery_hours: Optional[str] = Form(None),
    trigger_conditions: Optional[str] = Form(None),
    constraints: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    user = require_auth(request, db)
    hours_int = int(delivery_hours) if delivery_hours and delivery_hours.strip().isdigit() else None
    try:
        SessionService.submit_interpretation(
            db=db,
            session_id=session_id,
            user_id=user.user_id,
            perspective=perspective,
            expected_behavior=expected_behavior,
            assumptions=assumptions,
            acceptance_criteria=acceptance_criteria,
            edge_cases=edge_cases,
            notes=notes,
            actor=actor,
            trigger_conditions=trigger_conditions,
            delivery_hours=hours_int,
            constraints=constraints,
        )
        return RedirectResponse(url=f"/app/sessions/{session_id}", status_code=status.HTTP_303_SEE_OTHER)
    except HTTPException as e:
        return RedirectResponse(url=f"/app/sessions/{session_id}?error={e.detail}", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/app/sessions/{session_id}/lock")
def session_lock_action(
    session_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    user = require_auth(request, db)
    try:
        SessionService.lock_session(db, session_id, user.user_id)
        return RedirectResponse(url=f"/app/sessions/{session_id}/compare", status_code=status.HTTP_303_SEE_OTHER)
    except HTTPException as e:
        return RedirectResponse(url=f"/app/sessions/{session_id}?error={e.detail}", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/app/sessions/{session_id}/reveal")
def session_reveal_action(
    session_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    user = require_auth(request, db)
    try:
        SessionService.reveal_session(db, session_id, user.user_id)
        return RedirectResponse(url=f"/app/sessions/{session_id}/compare", status_code=status.HTTP_303_SEE_OTHER)
    except HTTPException as e:
        return RedirectResponse(url=f"/app/sessions/{session_id}?error={e.detail}", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/app/sessions/{session_id}/compare", response_class=HTMLResponse)
def session_compare_view(session_id: int, request: Request, db: Session = Depends(get_db)):
    """FR-05: Side-by-side evidence & divergence findings view (locked/revealed sessions only)."""
    user = require_auth(request, db)
    session = SessionService.get_session(db, session_id, user.user_id)
    role = ProjectService.get_user_role(db, session.requirement_version.requirement.project_id, user.user_id)

    if session.status in ("draft", "open", "collecting"):
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

@router.post("/app/sessions/{session_id}/resolution")
def session_resolution_action(
    session_id: int,
    request: Request,
    statement: str = Form(...),
    rationale: str = Form(...),
    db: Session = Depends(get_db),
):
    user = require_auth(request, db)
    try:
        ResolutionService.record_resolution(db, session_id, user.user_id, statement, rationale)
        return RedirectResponse(url=f"/app/sessions/{session_id}/compare", status_code=status.HTTP_303_SEE_OTHER)
    except HTTPException as e:
        return RedirectResponse(url=f"/app/sessions/{session_id}/resolution?error={e.detail}", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/app/divergences/{divergence_id}/resolve")
def divergence_resolve_action(
    divergence_id: int,
    request: Request,
    next: Optional[str] = None,
    db: Session = Depends(get_db),
):
    user = require_auth(request, db)
    div = ResolutionService.resolve_divergence(db, divergence_id, user.user_id, "resolved")
    redirect_target = next if next and next.startswith("/") else f"/app/sessions/{div.session_id}/compare"
    return RedirectResponse(url=redirect_target, status_code=status.HTTP_303_SEE_OTHER)

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
