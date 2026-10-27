"""
Risk-aware action classification system.
Enforces read-only browsing constraints and requires human confirmation for high-risk operations.
"""

from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ActionRisk(BaseModel):
    level: RiskLevel
    reason: str
    requires_confirmation: bool = False
    is_permitted_in_read_only: bool = True


class RiskAssessor:
    """Classifies browser and agent actions to guard against consequential operations."""

    CONSEQUENTIAL_KEYWORDS = {
        "buy", "purchase", "pay", "order", "checkout", "subscribe",
        "delete", "remove", "destroy", "cancel", "terminate",
        "transfer", "wire", "submit order", "confirm order",
        "change password", "update email", "authorize"
    }

    FORM_INPUT_SUSPICIOUS_NAMES = {
        "password", "credit_card", "cardnumber", "cvv", "ssn",
        "pin", "secret", "token", "auth_code", "otp"
    }

    def __init__(self, read_only_mode: bool = True, require_confirmation_for_high: bool = True):
        self.read_only_mode = read_only_mode
        self.require_confirmation_for_high = require_confirmation_for_high

    def assess_action(self, action_type: str, details: Optional[Dict[str, Any]] = None) -> ActionRisk:
        """
        Evaluate the risk profile of an intended action.
        """
        details = details or {}
        action_type = action_type.lower()

        # Read-only safe operations
        if action_type in {"search", "navigate", "scroll", "extract", "observe", "wait", "screenshot"}:
            url = details.get("url", "")
            if any(k in url.lower() for k in ["cart", "checkout", "payment"]):
                return ActionRisk(
                    level=RiskLevel.MEDIUM,
                    reason=f"Navigating to transaction-related URL '{url}'",
                    requires_confirmation=False,
                    is_permitted_in_read_only=True
                )
            return ActionRisk(
                level=RiskLevel.LOW,
                reason=f"Safe read-only operation: {action_type}",
                requires_confirmation=False,
                is_permitted_in_read_only=True
            )

        # Typing / Filling form inputs
        if action_type in {"type", "fill"}:
            field_name = str(details.get("field", "")).lower()
            value = str(details.get("value", ""))
            
            for sensitive in self.FORM_INPUT_SUSPICIOUS_NAMES:
                if sensitive in field_name:
                    return ActionRisk(
                        level=RiskLevel.HIGH,
                        reason=f"Attempting to fill sensitive input field '{field_name}'",
                        requires_confirmation=True,
                        is_permitted_in_read_only=False
                    )

            return ActionRisk(
                level=RiskLevel.MEDIUM,
                reason=f"Inputting text into search or non-sensitive field '{field_name}'",
                requires_confirmation=False,
                is_permitted_in_read_only=True
            )

        # Clicks / Button presses
        if action_type in {"click", "press"}:
            target_text = str(details.get("text", "")).lower()
            target_role = str(details.get("role", "")).lower()
            selector = str(details.get("selector", "")).lower()
            combined = f"{target_text} {selector} {target_role}"

            for keyword in self.CONSEQUENTIAL_KEYWORDS:
                if keyword in combined:
                    return ActionRisk(
                        level=RiskLevel.HIGH,
                        reason=f"Action contains consequential trigger word '{keyword}'",
                        requires_confirmation=self.require_confirmation_for_high,
                        is_permitted_in_read_only=False
                    )

            # Default click is medium risk
            return ActionRisk(
                level=RiskLevel.MEDIUM,
                reason=f"Interacting with element: {target_text or selector}",
                requires_confirmation=False,
                is_permitted_in_read_only=True
            )

        # Catch-all
        return ActionRisk(
            level=RiskLevel.MEDIUM,
            reason=f"Unclassified action: {action_type}",
            requires_confirmation=False,
            is_permitted_in_read_only=True
        )
