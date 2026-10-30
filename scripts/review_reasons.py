#!/usr/bin/env python3
"""Stable reason taxonomy for REVIEW_REQUIRED outcomes."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReviewReason:
    """One machine-readable reason behind a REVIEW_REQUIRED result."""

    code: str
    category: str
    details: str


RULES: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("SPEC_MISSING", "contract", ("missing SPEC.md:",)),
    ("SPEC_INCOMPLETE", "contract", ("SPEC.md missing concepts:",)),
    ("VERIFY_REVIEW_REQUESTED", "evidence", ("VERIFY.md requests REVIEW_REQUIRED",)),
    (
        "STRUCTURED_EVIDENCE_INVALID",
        "evidence",
        (
            "structured evidence JSON is invalid",
            "structured evidence section must contain",
            "structured evidence JSON root must be",
            "schema_version must be",
            "checks must be a non-empty array",
            "duplicate check id:",
            "structured verification evidence",
        ),
    ),
    (
        "COMPATIBILITY_UNCERTAIN",
        "compatibility",
        (
            "compatibility probe requirement is missing or unresolved",
            "compatibility probes are REQUIRED",
            "baseline probe has missing Probe ID",
            "duplicate baseline Probe ID:",
            "missing baseline fields:",
            "baseline result is not PASS",
            "verification contains undeclared Probe ID",
            "duplicate verification Probe ID:",
            "missing post-change evidence",
            "missing verification fields:",
            "result is REVIEW_REQUIRED",
            "has invalid result:",
        ),
    ),
    (
        "VERIFICATION_STALE",
        "freshness",
        ("verification is stale because repository state changed",),
    ),
    (
        "VERIFICATION_FRESHNESS_UNESTABLISHED",
        "freshness",
        (
            "verification freshness guard unavailable",
            "verification freshness:",
            "freshness could not be established",
            "missing snapshot commit",
            "missing workspace fingerprint",
        ),
    ),
    (
        "DIFF_BUDGET_INCOMPLETE",
        "change_control",
        (
            "diff budget requirement is missing or unresolved",
            "ENFORCED diff budget missing field",
        ),
    ),
    (
        "DIFF_BUDGET_UNMEASURABLE",
        "change_control",
        (
            "unable to inspect diff line counts",
            "unable to parse git numstat output",
            "invalid added-line count",
            "unable to read untracked file for line budget",
            "added-line budget cannot be established",
        ),
    ),
    (
        "DIFF_BUDGET_EXCEEDED",
        "change_control",
        ("budget exceeded:",),
    ),
    (
        "TEST_SENSITIVITY_SURVIVED",
        "test_integrity",
        (
            "injected fault survived the targeted test",
            "test failed, but not for the expected protected behavior",
        ),
    ),
    (
        "TEST_SENSITIVITY_UNESTABLISHED",
        "test_integrity",
        ("test sensitivity:",),
    ),
    (
        "PROTECTED_PATH_CHANGED",
        "change_control",
        ("protected path touched:",),
    ),
    (
        "TESTS_CHANGED",
        "change_control",
        ("tests changed:",),
    ),
    (
        "FIXTURE_DATA_CHANGED",
        "change_control",
        ("fixture/data changed:",),
    ),
    (
        "DEPENDENCIES_CHANGED",
        "dependency",
        ("dependencies changed:",),
    ),
)


def classify_review_reason(details: str) -> ReviewReason:
    """Classify one review message without changing the underlying decision."""
    lowered = details.lower()
    for code, category, needles in RULES:
        if any(needle.lower() in lowered for needle in needles):
            return ReviewReason(code=code, category=category, details=details)
    return ReviewReason(
        code="UNCLASSIFIED_REVIEW",
        category="other",
        details=details,
    )


def classify_review_reasons(details: list[str]) -> list[ReviewReason]:
    """Classify review messages in order, preserving duplicates and detail text."""
    return [classify_review_reason(item) for item in details]
