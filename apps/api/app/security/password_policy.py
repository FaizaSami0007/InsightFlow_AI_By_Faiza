"""Enterprise password policy enforcement and validation."""

import re
from typing import List, Tuple

COMMON_DISALLOWED_PASSWORDS = {
    "password",
    "password123",
    "12345678",
    "qwerty123",
    "admin123",
    "welcome1",
    "insightflow",
    "insightflow123",
    "letmein123",
    "changeme",
}


class PasswordPolicyValidator:
    """Enterprise-grade password security validator."""

    MIN_LENGTH = 8
    MAX_LENGTH = 128

    @classmethod
    def validate(cls, password: str) -> Tuple[bool, List[str]]:
        """
        Validate password complexity.
        Returns (is_valid, list_of_violations).
        """
        violations: List[str] = []

        if len(password) < cls.MIN_LENGTH:
            violations.append(f"Password must be at least {cls.MIN_LENGTH} characters long.")

        if len(password) > cls.MAX_LENGTH:
            violations.append(f"Password cannot exceed {cls.MAX_LENGTH} characters.")

        if not re.search(r"[A-Z]", password):
            violations.append("Password must contain at least one uppercase letter (A-Z).")

        if not re.search(r"[a-z]", password):
            violations.append("Password must contain at least one lowercase letter (a-z).")

        if not re.search(r"[0-9]", password):
            violations.append("Password must contain at least one numeric digit (0-9).")

        if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=~`[\]\\/]", password):
            violations.append("Password must contain at least one special character.")

        if password.lower() in COMMON_DISALLOWED_PASSWORDS:
            violations.append("Password is too common and easily guessable.")

        return len(violations) == 0, violations

    @classmethod
    def calculate_strength_score(cls, password: str) -> int:
        """Calculate password strength score from 0 (very weak) to 100 (very strong)."""
        score = 0
        if len(password) >= 8:
            score += 20
        if len(password) >= 12:
            score += 20
        if len(password) >= 16:
            score += 10
        if re.search(r"[A-Z]", password) and re.search(r"[a-z]", password):
            score += 20
        if re.search(r"[0-9]", password):
            score += 15
        if re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=~`[\]\\/]", password):
            score += 15
        return min(100, score)
