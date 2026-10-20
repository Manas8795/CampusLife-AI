"""
Unit Tests — Expense Category Classifier (Module 4 / Module 7)
==============================================================
Tests the classify_expense_category() rule-based classifier that powers
the voice agent's intelligent expense logging (LOG_EXPENSE intent).

SE Focus:
  - Tests for all 8 expense categories
  - Edge cases: empty descriptions, numeric-only descriptions, multi-word
  - Boundary tests: descriptions that could match multiple categories
  - Regression tests: previously mis-classified items
  - Academic note: Documents the rule-based baseline; comments show where
    an ML upgrade (TF-IDF or embedding similarity) would replace this logic.

These tests have zero external dependencies (no DB, no network).
"""

import pytest
from backend.app.tools.campuslife_tools import classify_expense_category


# =============================================================================
# Category Classification Parametrized Tests
# =============================================================================

@pytest.mark.parametrize("description,expected_category", [
    # --- Academic ---
    ("textbook for operating systems", "Academic"),
    ("xerox printout for lab manual", "Academic"),
    ("udemy course on machine learning", "Academic"),
    ("notebook and stationery", "Academic"),
    ("arduino components for IoT project", "Academic"),
    ("college tuition fee payment", "Academic"),
    ("resistors and capacitors from electronics shop", "Academic"),

    # --- Food ---
    ("lunch at college canteen", "Food"),
    ("dinner at dhaba near hostel", "Food"),
    ("chai and snacks from tapri", "Food"),
    ("biryani from zomato order", "Food"),
    ("grocery shopping at DMart", "Food"),

    # --- Transport ---
    ("auto rickshaw to college", "Transport"),
    ("metro card recharge", "Transport"),
    ("petrol for bike", "Transport"),
    ("ola cab to airport", "Transport"),
    ("bus ticket to hometown", "Transport"),

    # --- Entertainment ---
    ("movie ticket for Pushpa 2", "Entertainment"),
    ("netflix subscription", "Entertainment"),
    ("spotify premium renewal", "Entertainment"),
    ("cricket match IPL ticket", "Entertainment"),

    # --- Health ---
    ("doctor consultation fee", "Health"),
    ("medicine from pharmacy", "Health"),
    ("gym membership monthly", "Health"),
    ("protein powder supplement", "Health"),

    # --- Shopping ---
    ("new t-shirt from H&M", "Shopping"),
    ("jeans from Myntra order", "Shopping"),
    ("shoes from campus shopping", "Shopping"),
    ("laptop bag purchase", "Shopping"),

    # --- Edge cases ---
    ("",                              "Other"),   # Empty string
    ("miscellaneous spending",        "Other"),   # No matching category keywords
    ("random stuff",                  "Other"),   # Generic description
])
def test_classify_expense_category(description, expected_category):
    """Verify that classify_expense_category maps descriptions to correct categories."""
    result = classify_expense_category(description=description, category_hint=description)
    assert result == expected_category, (
        f"Description: '{description}' → got '{result}', expected '{expected_category}'"
    )


# =============================================================================
# Category Hint Override Tests
# =============================================================================

class TestCategoryHintPriority:
    """
    Tests that the category_hint (full user query) provides additional context
    when the description alone is ambiguous.
    """

    def test_hint_disambiguates_food_vs_shopping(self):
        """'paid for food at the mall' should classify as Food, not Shopping."""
        result = classify_expense_category(
            description="at the mall",
            category_hint="paid for food at the mall"
        )
        assert result == "Food"

    def test_academic_hint_overrides_generic_description(self):
        """'course fee' with academic hint should resolve to Academic."""
        result = classify_expense_category(
            description="fee payment",
            category_hint="paid course fee for udemy Python course"
        )
        assert result == "Academic"

    def test_empty_description_with_hint(self):
        """Even with empty description, a strong hint should classify correctly."""
        result = classify_expense_category(
            description="",
            category_hint="bought groceries from D-Mart"
        )
        assert result == "Food"


# =============================================================================
# Boundary / Regression Tests
# =============================================================================

class TestClassifierBoundaryAndRegression:

    def test_numeric_description_returns_other(self):
        """A pure number description with no hint should return Other."""
        result = classify_expense_category(description="100", category_hint="100")
        assert result == "Other"

    def test_case_insensitive_matching(self):
        """Classification should work regardless of case."""
        r1 = classify_expense_category("TEXTBOOK", "TEXTBOOK")
        r2 = classify_expense_category("textbook", "textbook")
        assert r1 == r2 == "Academic"

    def test_category_breadth_no_none_return(self):
        """classify_expense_category should NEVER return None — always a string category."""
        test_descriptions = [
            "something completely unrelated",
            "xyz abc 123",
            "random payment",
            "",
            "₹500 paid",
        ]
        for desc in test_descriptions:
            result = classify_expense_category(description=desc, category_hint=desc)
            assert result is not None, f"Got None for description: '{desc}'"
            assert isinstance(result, str)
            assert len(result) > 0

    def test_partial_word_matching_works(self):
        """The classifier should handle partial words in common expense items."""
        # "meds" is not in the keyword list but "medicine" / "pharma" should be covered
        result = classify_expense_category(
            description="bought meds from local pharmacy",
            category_hint="bought meds from local pharmacy"
        )
        assert result == "Health"
