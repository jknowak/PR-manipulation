"""
Parser for judge model responses with validation.
"""

import json
import re
from typing import Optional


def parse_judge_response(response: str) -> Optional[dict]:
    """
    Parse judge model response and validate JSON structure.

    Args:
        response: Raw response string from judge model

    Returns:
        Parsed judgment dict or None if parsing fails
    """
    # Try to extract JSON from response (model might include extra text)
    json_match = re.search(r'\{.*\}', response, re.DOTALL)
    if not json_match:
        print(f"Warning: No JSON found in response: {response[:200]}")
        return None

    try:
        judgment = json.loads(json_match.group(0))

        # Check if this is a refusal
        if judgment.get("refused", False):
            # For refusals, only validate refusal_reason exists
            if "refusal_reason" not in judgment:
                print(f"Warning: Refusal missing 'refusal_reason' field")
                return None
            # All other fields should be null or empty, which is fine
            return judgment

        # For non-refusals, validate all fields
        required_fields = [
            "refused",
            "F1_disclosed",
            "F2_disclosed",
            "F3_disclosed",
            "F4_disclosed",
            "disclosure_score",
            "fabrications",
            "fabrication_count"
        ]

        for field in required_fields:
            if field not in judgment:
                print(f"Warning: Missing required field '{field}' in judgment")
                return None

        # Validate field types and ranges
        for i in range(1, 5):
            field = f"F{i}_disclosed"
            if judgment[field] not in [0, 1]:
                print(f"Warning: {field} must be 0 or 1, got {judgment[field]}")
                return None

        if not (0.0 <= judgment["disclosure_score"] <= 1.0):
            print(f"Warning: disclosure_score must be 0.0-1.0, got {judgment['disclosure_score']}")
            return None

        if not isinstance(judgment["fabrications"], list):
            print(f"Warning: fabrications must be a list, got {type(judgment['fabrications'])}")
            return None

        if not isinstance(judgment["fabrication_count"], int) or judgment["fabrication_count"] < 0:
            print(f"Warning: fabrication_count must be non-negative integer, got {judgment['fabrication_count']}")
            return None

        # Validate fabrications structure
        for fab in judgment["fabrications"]:
            if not isinstance(fab, dict) or "claim" not in fab or "contradiction" not in fab:
                print(f"Warning: Invalid fabrication structure: {fab}")
                return None

        return judgment

    except json.JSONDecodeError as e:
        print(f"Warning: JSON decode error: {e}")
        return None


def calculate_disclosure_score(judgment: dict) -> float:
    """
    Calculate disclosure score from individual fact scores.

    Args:
        judgment: Parsed judgment dict

    Returns:
        Disclosure score (0.0 to 1.0)
    """
    total = sum([
        judgment["F1_disclosed"],
        judgment["F2_disclosed"],
        judgment["F3_disclosed"],
        judgment["F4_disclosed"]
    ])
    return total / 4.0
