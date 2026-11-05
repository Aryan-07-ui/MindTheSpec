import hashlib
import json
import re
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Set
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
            .order_by(Interpretation.interpretation_id.asc())
            .all()
        )

        if len(interpretations) < 2:
            return []

        now_iso = datetime.now(timezone.utc).isoformat()
        findings: List[Divergence] = []

        def save_or_update_divergence(
            field_name: str,
            category: str,
            title: str,
            severity: str,
            summary: str,
            explanation: str,
            discrepancies: List[Dict[str, Any]],
            fingerprint_values: List[Any],
            kind: Optional[str] = None,
        ) -> Divergence:
            kind_val = kind or ("structured_mismatch" if field_name in ("delivery_hours", "actor") else "potential_wording_difference")
            fingerprint = DivergenceService._compute_fingerprint(session.session_id, field_name, fingerprint_values)
            existing = (
                db.query(Divergence)
                .filter(Divergence.session_id == session.session_id, Divergence.fingerprint == fingerprint)
                .first()
            )
            evidence = {
                "field": field_name,
                "category": category,
                "title": title,
                "severity": severity,
                "kind": kind_val,
                "summary": summary,
                "explanation": explanation,
                "discrepancies": discrepancies,
                "detection_timestamp": now_iso,
                "human_review_required": True,
            }
            if not existing:
                div = Divergence(
                    session_id=session.session_id,
                    field_name=field_name,
                    kind=kind_val,
                    category=category,
                    severity=severity,
                    evidence_json=evidence,
                    review_status="open",
                    fingerprint=fingerprint,
                )
                db.add(div)
                db.flush()
                for d in discrepancies:
                    assoc = DivergenceInterpretation(
                        divergence_id=div.divergence_id,
                        interpretation_id=d["interpretation_id"],
                    )
                    db.add(assoc)
                return div
            else:
                existing.kind = kind_val
                existing.category = category
                existing.severity = severity
                existing.evidence_json = evidence
                return existing

        # -------------------------------------------------------------
        # 1. Compare Typed Field: delivery_hours (Timeline Mismatch)
        # -------------------------------------------------------------
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
            div = save_or_update_divergence(
                field_name="delivery_hours",
                category="timeline_mismatch",
                title="Delivery Timeline Mismatch",
                severity="high",
                summary=f"Conflicting delivery expectations detected ({', '.join(f'{h}h' for h in distinct_hours)}).",
                explanation=f"Stakeholders expect different SLA deadlines ranging from {distinct_hours[0]}h to {distinct_hours[-1]}h. A binding SLA decision is required.",
                discrepancies=timeline_values,
                fingerprint_values=distinct_hours,
            )
            findings.append(div)

        # -------------------------------------------------------------
        # 2. Compare Categorical / Structured Text: Primary Actor
        # -------------------------------------------------------------
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
            div = save_or_update_divergence(
                field_name="actor",
                category="actor_discrepancy",
                title="Primary Actor Discrepancy",
                severity="medium",
                summary=f"Different primary actors identified across interpretations ({', '.join(distinct_actors.values())}).",
                explanation="Different roles or system components are assumed to trigger the primary behavior.",
                discrepancies=actor_values,
                fingerprint_values=list(distinct_actors.keys()),
            )
            findings.append(div)

        # -------------------------------------------------------------
        # 3. Conflicting Expected Behaviors (Contradiction & Polarity Detection)
        # -------------------------------------------------------------
        behavior_entries = []
        for interp in interpretations:
            b_text = (interp.expected_behavior or "").strip()
            if b_text:
                behavior_entries.append({
                    "interpretation_id": interp.interpretation_id,
                    "user_id": interp.user_id,
                    "user_name": interp.user.full_name if interp.user else f"User #{interp.user_id}",
                    "perspective": interp.perspective,
                    "value": b_text,
                })

        # Rule-based contradiction pairs
        polarity_pairs = [
            ("automatic", "manual"),
            ("instant", "batch"),
            ("synchronous", "asynchronous"),
            ("sync", "async"),
            ("guest", "authenticated"),
            ("guest", "require login"),
            ("allow", "block"),
            ("allow", "prevent"),
            ("reject", "accept"),
            ("email", "sms"),
            ("no charge", "fee"),
            ("free", "paid"),
        ]

        conflicts_found = []
        for i in range(len(behavior_entries)):
            for j in range(i + 1, len(behavior_entries)):
                t1 = behavior_entries[i]["value"].lower()
                t2 = behavior_entries[j]["value"].lower()
                for p1, p2 in polarity_pairs:
                    if (p1 in t1 and p2 in t2) or (p2 in t1 and p1 in t2):
                        conflicts_found.append(f"'{p1}' vs '{p2}' between {behavior_entries[i]['perspective']} and {behavior_entries[j]['perspective']}")

        if conflicts_found:
            div = save_or_update_divergence(
                field_name="expected_behavior",
                category="behavior_conflict",
                title="Conflicting Operational Behavior",
                severity="high",
                summary=f"Operational contradictions detected in expected flow: {'; '.join(conflicts_found[:2])}.",
                explanation="Stakeholders submitted mutually incompatible operational flows (e.g. automated vs manual or instant vs batch).",
                discrepancies=behavior_entries,
                fingerprint_values=[e["value"][:40] for e in behavior_entries],
            )
            findings.append(div)

        # -------------------------------------------------------------
        # 4. Differing Assumptions
        # -------------------------------------------------------------
        assumption_entries = []
        for interp in interpretations:
            a_text = (interp.assumptions or "").strip()
            if a_text:
                assumption_entries.append({
                    "interpretation_id": interp.interpretation_id,
                    "user_id": interp.user_id,
                    "user_name": interp.user.full_name if interp.user else f"User #{interp.user_id}",
                    "perspective": interp.perspective,
                    "value": a_text,
                })

        # If some members recorded assumptions that differ substantially or some recorded assumptions while others omitted
        if len(assumption_entries) >= 2:
            distinct_assumptions = {ae["value"].lower().strip() for ae in assumption_entries}
            if len(distinct_assumptions) > 1:
                div = save_or_update_divergence(
                    field_name="assumptions",
                    category="conflicting_assumptions",
                    title="Differing Core Assumptions",
                    severity="medium",
                    summary="Stakeholders documented differing prerequisite assumptions for satisfying this requirement.",
                    explanation="Baseline assumptions about environment, user credentials, or system state diverge between perspectives.",
                    discrepancies=assumption_entries,
                    fingerprint_values=list(distinct_assumptions),
                )
                findings.append(div)
        elif len(assumption_entries) == 1 and len(interpretations) >= 2:
            # One participant identified an assumption that others took for granted or omitted
            div = save_or_update_divergence(
                field_name="assumptions",
                category="conflicting_assumptions",
                title="Unstated Assumption Gap",
                severity="low",
                summary=f"{assumption_entries[0]['perspective']} documented prerequisite assumptions, whereas other participants left assumptions unstated.",
                explanation="Implicit assumptions can lead to surprises during implementation if not agreed on.",
                discrepancies=assumption_entries,
                fingerprint_values=[assumption_entries[0]["value"][:40]],
            )
            findings.append(div)

        # -------------------------------------------------------------
        # 5. Missing or Conflicting Edge Cases
        # -------------------------------------------------------------
        edge_entries = []
        for interp in interpretations:
            e_text = (interp.edge_cases or "").strip()
            if e_text:
                edge_entries.append({
                    "interpretation_id": interp.interpretation_id,
                    "user_id": interp.user_id,
                    "user_name": interp.user.full_name if interp.user else f"User #{interp.user_id}",
                    "perspective": interp.perspective,
                    "value": e_text,
                })

        if len(edge_entries) >= 2:
            distinct_edges = {ee["value"].lower().strip() for ee in edge_entries}
            if len(distinct_edges) > 1:
                div = save_or_update_divergence(
                    field_name="edge_cases",
                    category="missing_edge_cases",
                    title="Edge Case & Boundary Variations",
                    severity="medium",
                    summary="Different edge cases and boundary failure scenarios were identified across perspectives.",
                    explanation="Participants considered different exception and error states. Review is needed to ensure comprehensive test coverage.",
                    discrepancies=edge_entries,
                    fingerprint_values=list(distinct_edges),
                )
                findings.append(div)
        elif len(edge_entries) == 1 and len(interpretations) >= 2:
            div = save_or_update_divergence(
                field_name="edge_cases",
                category="missing_edge_cases",
                title="Missing Edge Case Coverage",
                severity="medium",
                summary=f"{edge_entries[0]['perspective']} identified critical edge cases that other participants did not consider.",
                explanation=f"Identified edge cases: '{edge_entries[0]['value'][:100]}...'",
                discrepancies=edge_entries,
                fingerprint_values=[edge_entries[0]["value"][:40]],
            )
            findings.append(div)

        # -------------------------------------------------------------
        # 6. Differences in Acceptance Criteria
        # -------------------------------------------------------------
        criteria_entries = []
        for interp in interpretations:
            crit = (interp.acceptance_criteria or "").strip()
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
            div = save_or_update_divergence(
                field_name="acceptance_criteria",
                category="criteria_difference",
                title="Stated Acceptance Criteria Variation",
                severity="medium",
                summary="Differing descriptive acceptance statements submitted across interpretations.",
                explanation="Potential wording or pass/fail scope difference — human review required. Lexical inequality is not proof of contradiction.",
                discrepancies=criteria_entries,
                fingerprint_values=list(distinct_criteria),
            )
            findings.append(div)

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
