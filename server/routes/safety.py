"""
Safety Center API endpoints.
Provides policy visibility, risk classification configuration, and human-in-the-loop intervention management.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from safety.human_intervention import HumanInterventionManager
from safety.risk_assessor import RiskAssessor
from safety.url_validator import URLValidator
from config import settings

router = APIRouter(prefix="/api/safety", tags=["Safety"])
intervention_mgr = HumanInterventionManager()
risk_assessor = RiskAssessor(
    read_only_mode=settings.read_only_mode,
    require_confirmation_for_high=settings.require_human_confirmation_on_high_risk
)
url_validator = URLValidator(block_private_ips=settings.block_private_ips)


class ResolveInterventionRequest(BaseModel):
    notes: Optional[str] = Field(default="", description="Operator resolution notes")


@router.get("")
async def get_safety_status():
    """Retrieve active safety policies, risk rules, and domain protections."""
    return {
        "read_only_mode": settings.read_only_mode,
        "block_private_ips": settings.block_private_ips,
        "require_human_confirmation_on_high_risk": settings.require_human_confirmation_on_high_risk,
        "allowed_schemes": list(URLValidator.ALLOWED_SCHEMES),
        "blocked_schemes": list(URLValidator.BLOCKED_SCHEMES),
        "tracking_parameters_filtered": list(URLValidator.TRACKING_PARAMS)[:10],
        "consequential_action_triggers": list(RiskAssessor.CONSEQUENTIAL_KEYWORDS)[:12],
        "sensitive_form_input_keywords": list(RiskAssessor.FORM_INPUT_SUSPICIOUS_NAMES),
        "captcha_detection_active": True,
        "is_paused_for_intervention": intervention_mgr.is_paused()
    }


@router.get("/interventions")
async def get_interventions():
    """List current and historical human intervention requests."""
    current = intervention_mgr.get_current_intervention()
    history = intervention_mgr.get_history()
    return {
        "current_active": current.model_dump() if current else None,
        "total_requests": len(history),
        "history": [req.model_dump() for req in history]
    }


@router.post("/interventions/resolve")
async def resolve_intervention(req: ResolveInterventionRequest):
    """Mark the active human intervention request as resolved so execution can safely resume."""
    success = intervention_mgr.resolve_intervention(resolution_notes=req.notes or "Resolved via Safety Center")
    if not success:
        raise HTTPException(status_code=400, detail="No active intervention pending resolution")
    return {"status": "resolved", "notes": req.notes}
