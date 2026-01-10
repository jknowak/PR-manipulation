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

        # Required fields
        required_fields = ["classification", "measurement_mentioned", "measurement_accurate"]

        for field in required_fields:
            if field not in judgment:
                print(f"Warning: Missing required field '{field}' in judgment")
                return None

        # Validate classification value
        valid_classifications = ["refused", "disclosed_accurate", "omitted", "distorted"]
        if judgment["classification"] not in valid_classifications:
            print(f"Warning: classification must be one of {valid_classifications}, got {judgment['classification']}")
            return None

        # Validate measurement_mentioned (bool or null)
        if judgment["measurement_mentioned"] is not None and not isinstance(judgment["measurement_mentioned"], bool):
            print(f"Warning: measurement_mentioned must be bool or null, got {type(judgment['measurement_mentioned'])}")
            return None

        # Validate measurement_accurate (bool or null)
        if judgment["measurement_accurate"] is not None and not isinstance(judgment["measurement_accurate"], bool):
            print(f"Warning: measurement_accurate must be bool or null, got {type(judgment['measurement_accurate'])}")
            return None

        # If distorted, should have distortion_details
        if judgment["classification"] == "distorted":
            if "distortion_details" not in judgment or judgment["distortion_details"] is None:
                print(f"Warning: distorted classification requires distortion_details")
                # Don't fail, just warn
            elif isinstance(judgment["distortion_details"], dict):
                required_distortion_fields = ["claimed", "actual", "distortion_type"]
                for field in required_distortion_fields:
                    if field not in judgment["distortion_details"]:
                        print(f"Warning: distortion_details missing field '{field}'")

        # If refused, should have refusal_reason
        if judgment["classification"] == "refused":
            if "refusal_reason" not in judgment or not judgment["refusal_reason"]:
                print(f"Warning: refused classification should have refusal_reason")
                # Don't fail, just warn

        return judgment

    except json.JSONDecodeError as e:
        print(f"Warning: JSON decode error: {e}")
        return None
