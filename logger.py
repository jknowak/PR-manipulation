"""
Result logging system for CSV and JSONL outputs.
"""

import csv
import json
import os
from typing import Any


class ResultLogger:
    """Logs experiment results to CSV and JSONL files."""

    def __init__(self, csv_path: str = "results.csv", jsonl_path: str = "press_releases.jsonl"):
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
            "model",
            "model_full_id",
            "run",
            "refused",
            "F1_disclosed",
            "F2_disclosed",
            "F3_disclosed",
            "F4_disclosed",
            "disclosure_score",
            "fabrication_count"
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
                "stakes_tier": result["stakes_tier"],
                "model": result["model"],
                "model_full_id": result.get("model_full_id", ""),
                "run": result["run"],
                "refused": result.get("refused", False),
                "F1_disclosed": result.get("F1_disclosed", ""),
                "F2_disclosed": result.get("F2_disclosed", ""),
                "F3_disclosed": result.get("F3_disclosed", ""),
                "F4_disclosed": result.get("F4_disclosed", ""),
                "disclosure_score": result.get("disclosure_score", ""),
                "fabrication_count": result.get("fabrication_count", "")
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

        # Count refusals
        refusals = sum(1 for r in results if r.get('refused', '').lower() == 'true')
        successful = len(results) - refusals

        print(f"\n{'='*60}")
        print(f"EXPERIMENT SUMMARY")
        print(f"{'='*60}")
        print(f"Total runs: {len(results)}")
        print(f"Successful generations: {successful}")
        print(f"Refusals: {refusals}")
        print(f"Results saved to: {self.csv_path}")
        print(f"Press releases saved to: {self.jsonl_path}")
        print(f"{'='*60}\n")
