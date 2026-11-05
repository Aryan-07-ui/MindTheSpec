import hashlib
import json
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.models.session import InterpretationSession, Interpretation
from app.models.divergence import Divergence, DivergenceInterpretation

class DivergenceService:
    @staticmethod
    def _compute_fingerprint(session_id: int, field_name: str, values: List[Any]) -> str:
        """Generates a stable, reproducible sha256 fingerprint for a divergence."""
        raw_key = f"{session_id}:{field_name}:" + ":".join(sorted(str(v) for v in values))
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    @staticmethod
    def analyze_session(db: Session, session: InterpretationSession) -> List[Divergence]:
        """
        Runs deterministic divergence detection across submitted interpretations in a locked session.
        Never fabricates AI confidence. Structured fields yield structured mismatches;
        differing text prompts human review.
        """
        interpretations: List[Interpretation] = (
            db.query(Interpretation)
            .filter(Interpretation.session_id == session.session_id)
            .all()
        )

        # PRD Section 6.2: If fewer than 2 interpretations, insufficient comparisons
        if len(interpretations) < 2:
            return []

        findings: List[Divergence] = []

        # 1. Compare Typed Field: delivery_hours (FR-05 core golden path)
        timeline_values = []
        for interp in interpretations:
            if interp.delivery_hours is not None:
                timeline_values.append({
                    "interpretation_id": interp.interpretation_id,
                    "user_id": interp.user_id,
                    "user_name": interp.user.full_name if interp.user else f"User #{interp.user_id}",
                    "perspective": interp.perspective,
                    "value": interp.delivery_hours,
                })

        distinct_hours = sorted(list({tv["value"] for tv in timeline_values}))
        if len(distinct_hours) > 1:
            fingerprint = DivergenceService._compute_fingerprint(session.session_id, "delivery_hours", distinct_hours)
            existing = (
                db.query(Divergence)
                .filter(Divergence.session_id == session.session_id, Divergence.fingerprint == fingerprint)
                .first()
            )
            evidence = {
                "field": "delivery_hours",
                "title": "Delivery Timeline Mismatch",
                "kind": "structured_mismatch",
                "summary": f"Conflicting delivery expectations detected ({', '.join(f'{h}h' for h in distinct_hours)}). A binding business decision is required.",
                "discrepancies": timeline_values,
                "human_review_required": True,
            }
            if not existing:
                div = Divergence(
                    session_id=session.session_id,
                    field_name="delivery_hours",
                    kind="structured_mismatch",
                    evidence_json=evidence,
                    review_status="open",
                    fingerprint=fingerprint,
                )
                db.add(div)
                db.flush()
                # Link interpretations
                for tv in timeline_values:
                    assoc = DivergenceInterpretation(
                        divergence_id=div.divergence_id,
                        interpretation_id=tv["interpretation_id"],
                    )
                    db.add(assoc)
                findings.append(div)
            else:
                existing.evidence_json = evidence
                findings.append(existing)

        # 2. Compare Categorical / Structured Text: actor
        actor_values = []
        for interp in interpretations:
            act = (interp.actor or "").strip()
            if act:
                actor_values.append({
                    "interpretation_id": interp.interpretation_id,
                    "user_id": interp.user_id,
                    "user_name": interp.user.full_name if interp.user else f"User #{interp.user_id}",
                    "perspective": interp.perspective,
                    "value": act,
                })
        distinct_actors = {av["value"].lower(): av["value"] for av in actor_values}
        if len(distinct_actors) > 1:
            fingerprint = DivergenceService._compute_fingerprint(session.session_id, "actor", list(distinct_actors.keys()))
            existing = (
                db.query(Divergence)
                .filter(Divergence.session_id == session.session_id, Divergence.fingerprint == fingerprint)
                .first()
            )
            evidence = {
                "field": "actor",
                "title": "Primary Actor Discrepancy",
                "kind": "structured_mismatch",
                "summary": f"Different primary actors identified across interpretations ({', '.join(distinct_actors.values())}).",
                "discrepancies": actor_values,
                "human_review_required": True,
            }
            if not existing:
                div = Divergence(
                    session_id=session.session_id,
                    field_name="actor",
                    kind="structured_mismatch",
                    evidence_json=evidence,
                    review_status="open",
                    fingerprint=fingerprint,
                )
                db.add(div)
                db.flush()
                for av in actor_values:
                    assoc = DivergenceInterpretation(
                        divergence_id=div.divergence_id,
                        interpretation_id=av["interpretation_id"],
                    )
                    db.add(assoc)
                findings.append(div)
            else:
                existing.evidence_json = evidence
                findings.append(existing)

        # 3. Descriptive Acceptance Criteria / Text Variation (Flagged for human review without false AI certainty)
        criteria_entries = []
        for interp in interpretations:
            crit = (interp.acceptance_criteria or interp.expected_behavior or "").strip()
            if crit:
                criteria_entries.append({
                    "interpretation_id": interp.interpretation_id,
                    "user_id": interp.user_id,
                    "user_name": interp.user.full_name if interp.user else f"User #{interp.user_id}",
                    "perspective": interp.perspective,
                    "value": crit,
                })
        distinct_criteria = {ce["value"].strip().lower() for ce in criteria_entries}
        if len(distinct_criteria) > 1:
            fingerprint = DivergenceService._compute_fingerprint(session.session_id, "acceptance_criteria", list(distinct_criteria))
            existing = (
                db.query(Divergence)
                .filter(Divergence.session_id == session.session_id, Divergence.fingerprint == fingerprint)
                .first()
            )
            evidence = {
                "field": "acceptance_criteria",
                "title": "Stated Acceptance Criteria Variation",
                "kind": "potential_wording_difference",
                "summary": "Differing descriptive acceptance statements submitted. Potential wording or scope difference — human review required. Lexical inequality is not proof of contradiction.",
                "discrepancies": criteria_entries,
                "human_review_required": True,
            }
            if not existing:
                div = Divergence(
                    session_id=session.session_id,
                    field_name="acceptance_criteria",
                    kind="potential_wording_difference",
                    evidence_json=evidence,
                    review_status="open",
                    fingerprint=fingerprint,
                )
                db.add(div)
                db.flush()
                for ce in criteria_entries:
                    assoc = DivergenceInterpretation(
                        divergence_id=div.divergence_id,
                        interpretation_id=ce["interpretation_id"],
                    )
                    db.add(assoc)
                findings.append(div)
            else:
                existing.evidence_json = evidence
                findings.append(existing)

        db.commit()
        return findings

    @staticmethod
    def get_session_divergences(db: Session, session_id: int) -> List[Divergence]:
        """Returns all recorded divergence rows for a session."""
        return (
            db.query(Divergence)
            .filter(Divergence.session_id == session_id)
            .order_by(Divergence.divergence_id.asc())
            .all()
        )
