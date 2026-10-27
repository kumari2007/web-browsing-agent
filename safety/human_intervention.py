"""
Human-in-the-loop intervention manager.
Detects obstacles like CAPTCHA, Cloudflare challenges, login barriers, and coordinates pause/resume flows.
"""

from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
import time


class ObstacleType(str, Enum):
    CAPTCHA = "CAPTCHA"
    CLOUDFLARE_CHALLENGE = "CLOUDFLARE_CHALLENGE"
    LOGIN_WALL = "LOGIN_WALL"
    COOKIE_CONSENT = "COOKIE_CONSENT"
    BOT_DETECTED = "BOT_DETECTED"
    CONSEQUENTIAL_CONFIRMATION = "CONSEQUENTIAL_CONFIRMATION"
    NONE = "NONE"


class InterventionRequest(BaseModel):
    obstacle_type: ObstacleType
    url: str
    message: str
    timestamp: float = Field(default_factory=time.time)
    resolved: bool = False
    details: Dict[str, Any] = Field(default_factory=dict)


class HumanInterventionManager:
    """Coordinates detection and resolution of human-required obstacles."""

    # Heuristic keywords in page title or content indicating barriers
    CAPTCHA_INDICATORS = [
        "recaptcha", "g-recaptcha", "hcaptcha", "cf-turnstile",
        "verify you are human", "robot check", "are you a robot",
        "enter the characters you see below", "security check",
        "access to this page has been denied", "bot detection"
    ]

    LOGIN_INDICATORS = [
        "sign in to continue", "log in to continue", "please log in",
        "enter your password", "create an account or sign in"
    ]

    def __init__(self):
        self._current_intervention: Optional[InterventionRequest] = None
        self._intervention_history: List[InterventionRequest] = []

    def detect_obstacle(self, title: str, text_sample: str, url: str) -> ObstacleType:
        """Analyze page text and metadata to identify obstacles."""
        combined = f"{title.lower()} {text_sample[:1000].lower()}"

        if "cloudflare" in combined and ("challenge" in combined or "turnstile" in combined or "verify" in combined):
            return ObstacleType.CLOUDFLARE_CHALLENGE

        for indicator in self.CAPTCHA_INDICATORS:
            if indicator in combined:
                return ObstacleType.CAPTCHA

        for indicator in self.LOGIN_INDICATORS:
            if indicator in combined:
                return ObstacleType.LOGIN_WALL

        return ObstacleType.NONE

    def request_intervention(
        self,
        obstacle_type: ObstacleType,
        url: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> InterventionRequest:
        """Create and track an active intervention request."""
        req = InterventionRequest(
            obstacle_type=obstacle_type,
            url=url,
            message=message,
            details=details or {}
        )
        self._current_intervention = req
        self._intervention_history.append(req)
        return req

    def is_paused(self) -> bool:
        """Return True if an active intervention is pending resolution."""
        return self._current_intervention is not None and not self._current_intervention.resolved

    def get_current_intervention(self) -> Optional[InterventionRequest]:
        """Retrieve the currently active intervention request, if any."""
        return self._current_intervention

    def resolve_intervention(self, resolution_notes: str = "") -> bool:
        """Mark the active intervention as resolved so execution can safely resume."""
        if self._current_intervention and not self._current_intervention.resolved:
            self._current_intervention.resolved = True
            self._current_intervention.details["resolution_notes"] = resolution_notes
            self._current_intervention.details["resolved_at"] = time.time()
            self._current_intervention = None
            return True
        return False

    def get_history(self) -> List[InterventionRequest]:
        """Retrieve all recorded human intervention requests."""
        return self._intervention_history

    def clear(self) -> None:
        """Reset intervention status."""
        self._current_intervention = None
