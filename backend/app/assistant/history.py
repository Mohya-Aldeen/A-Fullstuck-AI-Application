"""Compact prior-turn context for the document agent."""

from __future__ import annotations


def format_prior_turns(
    turns: list[tuple[str, str]],
    *,
    max_turns: int = 6,
) -> str:
    """Format recent (role, text) pairs as plain context. Roles are ``user`` or ``assistant``."""
    if max_turns < 1 or not turns:
        return ""

    lines: list[str] = []
    for role, text in turns[-max_turns:]:
        collapsed = " ".join(text.split())
        if not collapsed:
            continue
        label = "User" if role == "user" else "Assistant"
        lines.append(f"{label}: {collapsed}")
    if not lines:
        return ""
    return "Previous conversation:\n" + "\n".join(lines)
