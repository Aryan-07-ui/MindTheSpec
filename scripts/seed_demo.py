import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import SessionLocal, engine
from app.models.base import Base
from app.models.user import User
from app.models.project import Project, ProjectMember
from app.models.requirement import Requirement, RequirementVersion
from app.models.session import InterpretationSession, Interpretation
from app.services.auth_service import hash_password
from app.services.session_service import SessionService
from app.services.divergence_service import DivergenceService
from app.services.resolution_service import ResolutionService

def seed_demo_data(lock_and_resolve: bool = False):
    """
    Populates authentic, reproducible demo data for the golden path evaluation:
    - 3 authentic stakeholder accounts (Owner, Developer, Tester)
    - 1 project: 'Online Shopping System'
    - 1 requirement: 'REQ-001 - Fast Delivery Support'
    - 2 blind interpretations with delivery_hours = 24 and delivery_hours = 48
    Non-destructive: safe to run multiple times without corrupting existing records.
    """
    # Create tables if using SQLite or if user granted DDL
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"[Note] create_all skipped: {e}")

    db = SessionLocal()
    try:
        print("--- MindTheSpec Demo Seed ---")

        # 1. Seed Users
        users_def = [
            ("owner@example.com", "Alex Owner", "Owner123!"),
            ("dev@example.com", "Dave Developer", "Dev123!"),
            ("test@example.com", "Tina Tester", "Test123!"),
        ]
        user_map = {}
        for email, name, pwd in users_def:
            u = db.query(User).filter(User.email == email).first()
            if not u:
                u = User(
                    email=email,
                    full_name=name,
                    password_hash=hash_password(pwd),
                )
                db.add(u)
                db.flush()
                print(f"Created demo user: {name} ({email})")
            else:
                print(f"Existing demo user: {name} ({email})")
            user_map[email] = u

        owner = user_map["owner@example.com"]
        dev = user_map["dev@example.com"]
        tester = user_map["test@example.com"]

        # 2. Seed Project
        project = db.query(Project).filter(Project.project_name == "Online Shopping System").first()
        if not project:
            project = Project(
                project_name="Online Shopping System",
                description="E-commerce ordering, fulfillment, and expedited logistics platform.",
                owner_id=owner.user_id,
                status="active",
            )
            db.add(project)
            db.flush()

            # Add memberships
            db.add(ProjectMember(project_id=project.project_id, user_id=owner.user_id, role="owner"))
            db.add(ProjectMember(project_id=project.project_id, user_id=dev.user_id, role="developer"))
            db.add(ProjectMember(project_id=project.project_id, user_id=tester.user_id, role="tester"))
            db.flush()
            print(f"Created demo project: '{project.project_name}' (ID: {project.project_id})")
        else:
            print(f"Existing demo project: '{project.project_name}' (ID: {project.project_id})")

        # 3. Seed Requirement REQ-001
        req = (
            db.query(Requirement)
            .filter(Requirement.project_id == project.project_id, Requirement.req_code == "REQ-001")
            .first()
        )
        if not req:
            req = Requirement(
                project_id=project.project_id,
                req_code="REQ-001",
                title="Fast Delivery Support",
                description="The system must support fast delivery for qualifying customer orders.",
                status="active",
                version=1,
            )
            db.add(req)
            db.flush()

            v1 = RequirementVersion(
                requirement_id=req.requirement_id,
                version_no=1,
                body=req.description,
                acceptance_notes="Must clarify whether fast delivery implies 24 hours or 48 hours.",
                created_by=owner.user_id,
            )
            db.add(v1)
            db.flush()
            req.current_version_id = v1.version_id
            print(f"Created requirement: {req.req_code} - {req.title}")
        else:
            print(f"Existing requirement: {req.req_code}")

        # 4. Seed Blind Session
        session = (
            db.query(InterpretationSession)
            .filter(InterpretationSession.requirement_version_id == req.current_version_id)
            .first()
        )
        if not session:
            session = InterpretationSession(
                requirement_version_id=req.current_version_id,
                created_by=owner.user_id,
                status="collecting",
                mode="standard",
            )
            db.add(session)
            db.flush()
            print(f"Opened blind interpretation session #{session.session_id}")

            # 5. Developer submission (24h)
            interp_dev = Interpretation(
                session_id=session.session_id,
                requirement_id=req.requirement_id,
                user_id=dev.user_id,
                perspective="Developer",
                actor="Order Processing Service",
                expected_behavior="Order is packaged and dispatched within 24 hours of online checkout.",
                trigger_conditions="Customer selects Expedited Checkout before 2 PM local time.",
                delivery_hours=24,
                acceptance_criteria="Delivery within one day (24h) from payment confirmation.",
            )
            db.add(interp_dev)

            # 6. Tester submission (48h)
            interp_test = Interpretation(
                session_id=session.session_id,
                requirement_id=req.requirement_id,
                user_id=tester.user_id,
                perspective="Tester",
                actor="Fulfillment Center & Carrier",
                expected_behavior="Customer receives shipment at doorstep within 48 hours of dispatch.",
                trigger_conditions="Standard logistics carrier batch pickup.",
                delivery_hours=48,
                acceptance_criteria="Delivery within two days (48h) under standard carrier SLA.",
            )
            db.add(interp_test)
            db.flush()
            print("Submitted blind interpretations: Developer (24h) and Tester (48h).")

            if lock_and_resolve:
                # Lock and analyze
                session.status = "locked"
                findings = DivergenceService.analyze_session(db, session)
                session.status = "analyzed"
                print(f"Locked session #{session.session_id}. Generated {len(findings)} divergence findings.")

                # Record resolution
                ResolutionService.record_resolution(
                    db=db,
                    session_id=session.session_id,
                    user_id=owner.user_id,
                    statement="Delivery within 48 hours for eligible orders.",
                    rationale="Business and carrier operations confirmed that reliable next-day 24h delivery is not universally guaranteed; 48h committed SLA adopted.",
                )
                print(f"Recorded resolution for session #{session.session_id}.")

        db.commit()
        print("--- Demo Seed Completed Successfully ---")

    except Exception as e:
        db.rollback()
        print(f"Seed failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    lock_flag = "--locked" in sys.argv
    seed_demo_data(lock_and_resolve=lock_flag)
