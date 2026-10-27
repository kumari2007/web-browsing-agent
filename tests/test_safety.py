"""
Unit tests for safety components: URLValidator, RiskAssessor, HumanInterventionManager, and ExperienceMemory.
Tests SSRF prevention, scheme rejection, action risk classification, and SQLite persistence.
"""

from safety.url_validator import URLValidator
from safety.risk_assessor import RiskAssessor, RiskLevel
from safety.human_intervention import HumanInterventionManager, ObstacleType
from memory.experience_memory import ExperienceMemory


def test_url_validator_schemes_and_ssrf():
    validator = URLValidator(block_private_ips=True)

    # Allowed safe public URLs
    is_safe, _ = validator.is_safe_url("https://en.wikipedia.org/wiki/Python")
    assert is_safe is True

    # Blocked dangerous schemes
    assert validator.is_safe_url("javascript:alert(1)")[0] is False
    assert validator.is_safe_url("file:///etc/passwd")[0] is False
    assert validator.is_safe_url("data:text/html,<b>hi</b>")[0] is False

    # Blocked loopback and private subnets
    assert validator.is_safe_url("http://127.0.0.1:8080")[0] is False
    assert validator.is_safe_url("http://localhost:3000")[0] is False
    assert validator.is_safe_url("http://169.254.169.254/latest/meta-data/")[0] is False


def test_risk_assessor_classification():
    assessor = RiskAssessor(read_only_mode=True, require_confirmation_for_high=True)

    # Low risk
    low = assessor.assess_action("search", {"query": "python courses"})
    assert low.level == RiskLevel.LOW
    assert low.requires_confirmation is False

    # Medium risk
    med = assessor.assess_action("click", {"text": "View More Tutorials", "role": "link"})
    assert med.level == RiskLevel.MEDIUM
    assert med.requires_confirmation is False

    # High risk - Purchase
    high_buy = assessor.assess_action("click", {"text": "Buy Now with 1-Click", "role": "button"})
    assert high_buy.level == RiskLevel.HIGH
    assert high_buy.requires_confirmation is True
    assert high_buy.is_permitted_in_read_only is False

    # High risk - Password input
    high_input = assessor.assess_action("fill", {"field": "user_password", "value": "secret"})
    assert high_input.level == RiskLevel.HIGH
    assert high_input.requires_confirmation is True


def test_human_intervention_lifecycle():
    manager = HumanInterventionManager()

    # Detect obstacle
    obs = manager.detect_obstacle("Security Check", "Please solve the hcaptcha puzzle", "https://example.com/protected")
    assert obs == ObstacleType.CAPTCHA

    # Request intervention
    req = manager.request_intervention(obs, "https://example.com/protected", "Solve CAPTCHA to continue")
    assert manager.is_paused() is True
    assert manager.get_current_intervention() == req

    # Resolve intervention
    resolved = manager.resolve_intervention("User completed CAPTCHA manually")
    assert resolved is True
    assert manager.is_paused() is False


def test_experience_memory_sqlite_persistence(tmp_path):
    db_file = tmp_path / "test_memory.db"
    mem = ExperienceMemory(db_path=db_file)

    # Record success
    mem.record_experience("python.org", "search", "success", {"results": 5})
    # Record failure
    mem.record_experience("example-broken.com", "navigation", "failure", {"error": "Timeout"})

    advice = mem.get_advice("python.org")
    assert len(advice["recommended"]) == 1

    all_exp = mem.get_all_experiences()
    assert len(all_exp) == 2

    mem.clear_memory()
    assert len(mem.get_all_experiences()) == 0
