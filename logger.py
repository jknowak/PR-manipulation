"""
Result logging system for CSV and JSONL outputs.
"""

import csv
import json
import os
from typing import Any


class ResultLogger:
    """Logs experiment results to CSV and JSONL files."""

    def __init__(self, csv_path: str = "data/results.csv", jsonl_path: str = "data/press_releases.jsonl"):
        """
        Initialize result logger.

        Args:
            csv_path: Path to CSV results file
            jsonl_path: Path to JSONL press releases file
        """
        self.csv_path = csv_path
        self.jsonl_path = jsonl_path
        self.csv_initialized = False

        # CSV column headers
        self.csv_headers = [
            "timestamp",
            "scenario",
            "scenario_name",
            "stakes_tier",
            "measurement_condition",
            "model",
            "model_full_id",
            "run",
            "classification",
            "measurement_mentioned",
            "measurement_accurate",
            "refusal_reason"
        ]

    def log_result(self, result: dict):
        """
        Log a single experiment result to CSV and JSONL.

        Args:
            result: Dictionary containing experiment results
        """
        # Log to CSV
        self._log_csv(result)

        # Log to JSONL
        self._log_jsonl(result)

    def _log_csv(self, result: dict):
        """Write result to CSV file."""
        file_exists = os.path.exists(self.csv_path)

        with open(self.csv_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.csv_headers)

            # Write header if new file
            if not file_exists or not self.csv_initialized:
                writer.writeheader()
                self.csv_initialized = True

            # Write row
            row = {
                "timestamp": result.get("timestamp", ""),
                "scenario": result["scenario"],
                "scenario_name": result["scenario_name"],
                "stakes_tier": result.get("stakes_tier", ""),
                "measurement_condition": result.get("measurement_condition", ""),
                "model": result["model"],
                "model_full_id": result.get("model_full_id", ""),
                "run": result["run"],
                "classification": result.get("classification", ""),
                "measurement_mentioned": result.get("measurement_mentioned", ""),
                "measurement_accurate": result.get("measurement_accurate", ""),
                "refusal_reason": result.get("refusal_reason", "")
            }
            writer.writerow(row)

    def _log_jsonl(self, result: dict):
        """Write result to JSONL file (one JSON object per line)."""
        with open(self.jsonl_path, 'a', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False)
            f.write('\n')

    def print_summary(self):
        """Print summary of logged results."""
        if not os.path.exists(self.csv_path):
            print("No results logged yet.")
            return

        with open(self.csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            results = list(reader)

        if not results:
            print("No results logged yet.")
            return

        # Count classifications
        classification_counts = {}
        for r in results:
            classification = r.get('classification', 'unknown')
            classification_counts[classification] = classification_counts.get(classification, 0) + 1

        print(f"\n{'='*60}")
        print(f"EXPERIMENT SUMMARY")
        print(f"{'='*60}")
        print(f"Total runs: {len(results)}")
        print(f"\nClassification breakdown:")
        for classification, count in sorted(classification_counts.items()):
            print(f"  {classification}: {count}")
        print(f"\nResults saved to: {self.csv_path}")
        print(f"Press releases saved to: {self.jsonl_path}")
        print(f"{'='*60}\n")
