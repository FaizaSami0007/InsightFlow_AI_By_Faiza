"""Tests for Core Security controls: Password policy, rate limiting, and configuration verifier."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.main import app
from app.security.config_check import ProductionSecurityVerifier
from app.security.password_policy import PasswordPolicyValidator
from app.security.rate_limiter import InMemoryRateLimiter


def test_password_policy_valid_strong():
    is_valid, violations = PasswordPolicyValidator.validate("InsightFlow#2026Secure!")
    assert is_valid is True
    assert len(violations) == 0
    score = PasswordPolicyValidator.calculate_strength_score("InsightFlow#2026Secure!")
    assert score >= 90


def test_password_policy_short():
    is_valid, violations = PasswordPolicyValidator.validate("Short1!")
    assert is_valid is False
    assert any("at least 8 characters" in v for v in violations)


def test_password_policy_missing_special_or_digit():
    is_valid, violations = PasswordPolicyValidator.validate("OnlyLettersPassword")
    assert is_valid is False
    assert any("numeric digit" in v for v in violations)
    assert any("special character" in v for v in violations)


def test_password_policy_common_dictionary():
    is_valid, violations = PasswordPolicyValidator.validate("password123")
    assert is_valid is False
    assert any("too common" in v for v in violations)


@pytest.mark.asyncio
async def test_in_memory_rate_limiter():
    limiter = InMemoryRateLimiter()
    key = "test_user_ip"

    # Allow 3 requests per 10 seconds
    for _ in range(3):
        limited = await limiter.is_rate_limited(key, max_requests=3, window_seconds=10)
        assert limited is False

    # 4th request should trigger rate limit
    limited = await limiter.is_rate_limited(key, max_requests=3, window_seconds=10)
    assert limited is True

    # Reset
    await limiter.reset(key)
    limited = await limiter.is_rate_limited(key, max_requests=3, window_seconds=10)
    assert limited is False


def test_production_security_verifier_audit():
    audit = ProductionSecurityVerifier.audit_configuration()
    assert "environment" in audit
    assert "issues" in audit
    assert "passed_checks" in audit
    assert audit["total_checks"] > 0


def test_security_scorecard_15_dimensions():
    scorecard = ProductionSecurityVerifier.get_security_scorecard()
    assert scorecard["total_dimensions"] == 15
    assert scorecard["overall_score"] >= 85
    assert len(scorecard["dimensions"]) == 15

    dim_ids = [d["id"] for d in scorecard["dimensions"]]
    assert "identity" in dim_ids
    assert "authorization" in dim_ids
    assert "tenant_isolation" in dim_ids
    assert "database_security" in dim_ids
    assert "ai_prompt_security" in dim_ids
    assert "connector_security" in dim_ids
    assert "audit_trail" in dim_ids
    assert "export_security" in dim_ids


@pytest.mark.asyncio
async def test_security_headers_present():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert "Content-Security-Policy" in response.headers
