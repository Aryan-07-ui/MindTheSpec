import sys
import os

proj_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, proj_dir)

from app.database import engine
from sqlalchemy import text, inspect

def run_migration():
    insp = inspect(engine)
    req_cols = [c['name'] for c in insp.get_columns('requirements')]
    interp_cols = [c['name'] for c in insp.get_columns('interpretations')]
    div_cols = [c['name'] for c in insp.get_columns('divergences')]

    with engine.begin() as conn:
        # Requirements table additions
        if 'priority' not in req_cols:
            conn.execute(text("ALTER TABLE requirements ADD COLUMN priority VARCHAR(20) NOT NULL DEFAULT 'medium';"))
            print("[DB] Added priority to requirements")
        if 'acceptance_criteria' not in req_cols:
            conn.execute(text("ALTER TABLE requirements ADD COLUMN acceptance_criteria TEXT NULL;"))
            print("[DB] Added acceptance_criteria to requirements")
        if 'created_by' not in req_cols:
            conn.execute(text("ALTER TABLE requirements ADD COLUMN created_by INT NULL;"))
            try:
                conn.execute(text("ALTER TABLE requirements ADD CONSTRAINT fk_req_creator FOREIGN KEY (created_by) REFERENCES users(user_id) ON DELETE SET NULL;"))
            except Exception as e:
                print("[DB] Constraint note:", e)
            print("[DB] Added created_by to requirements")

        # Interpretations table additions
        if 'edge_cases' not in interp_cols:
            conn.execute(text("ALTER TABLE interpretations ADD COLUMN edge_cases TEXT NULL;"))
            print("[DB] Added edge_cases to interpretations")
        if 'notes' not in interp_cols:
            conn.execute(text("ALTER TABLE interpretations ADD COLUMN notes TEXT NULL;"))
            print("[DB] Added notes to interpretations")

        # Session table status type alignment
        try:
            conn.execute(text("ALTER TABLE interpretation_sessions MODIFY COLUMN status VARCHAR(20) NOT NULL DEFAULT 'open';"))
            print("[DB] Modified interpretation_sessions.status to VARCHAR(20)")
        except Exception as e:
            print("[DB] Note on session status:", e)

        # Divergences table additions
        if 'category' not in div_cols:
            conn.execute(text("ALTER TABLE divergences ADD COLUMN category VARCHAR(50) NULL;"))
            print("[DB] Added category to divergences")
        if 'severity' not in div_cols:
            conn.execute(text("ALTER TABLE divergences ADD COLUMN severity VARCHAR(20) NOT NULL DEFAULT 'medium';"))
            print("[DB] Added severity to divergences")

    print("[DB] Migration 002 applied successfully!")

if __name__ == "__main__":
    run_migration()
