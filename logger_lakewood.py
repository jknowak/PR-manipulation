"""
Result logger for Lakewood Manufacturing experiment.
"""

import csv
import json
from pathlib import Path
from datetime import datetime


class LakewoodResultLogger:
    """Logger for Lakewood experiment results."""

    def __init__(self, data_dir: str = "data"):
        """
        Initialize logger.

        Args:
            data_dir: Directory for output files
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.csv_path = self.data_dir / f"lakewood_results_{timestamp}.csv"
        self.jsonl_path = self.data_dir / f"lakewood_statements_{timestamp}.jsonl"

        self.results = []
        self._init_csv()

    def _init_csv(self):
        """Initialize CSV file with headers."""
        headers = [
            "timestamp",
            "severity_level",
            "include_probability",
            "model",
            "model_full_id",
            "run",
            "refused",
            "refusal_reason",
            "fact_1_presented",
            "fact_1_misrepresented",
            "fact_2_presented",
            "fact_2_misrepresented",
            "fact_3_presented",
            "fact_3_misrepresented"
        ]

        with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()

    def log_result(self, result: dict):
        """
        Log a single result.

        Args:
            result: Dictionary with result data
        """
        self.results.append(result)

        # Append to CSV
        with open(self.csv_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                "timestamp", "severity_level", "include_probability",
                "model", "model_full_id", "run", "refused", "refusal_reason",
                "fact_1_presented", "fact_1_misrepresented",
                "fact_2_presented", "fact_2_misrepresented",
                "fact_3_presented", "fact_3_misrepresented"
            ])
            writer.writerow({
                "timestamp": result["timestamp"],
                "severity_level": result["severity_level"],
                "include_probability": result["include_probability"],
                "model": result["model"],
                "model_full_id": result["model_full_id"],
                "run": result["run"],
                "refused": result["refused"],
                "refusal_reason": result.get("refusal_reason"),
                "fact_1_presented": result.get("fact_1_presented"),
                "fact_1_misrepresented": result.get("fact_1_misrepresented"),
                "fact_2_presented": result.get("fact_2_presented"),
                "fact_2_misrepresented": result.get("fact_2_misrepresented"),
                "fact_3_presented": result.get("fact_3_presented"),
                "fact_3_misrepresented": result.get("fact_3_misrepresented")
            })

        # Append to JSONL (includes full press statement)
        with open(self.jsonl_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(result, ensure_ascii=False) + '\n')

    def print_summary(self):
        """Print experiment summary."""
        if not self.results:
            print("No results logged yet.")
            return

        total = len(self.results)
        refused = sum(1 for r in self.results if r["refused"])
        non_refused = total - refused

        print(f"\n{'='*60}")
        print(f"LAKEWOOD EXPERIMENT SUMMARY")
        print(f"{'='*60}")
        print(f"Total runs: {total}")
        print(f"Successful generations: {non_refused}")
        print(f"Refusals: {refused}")

        if non_refused > 0:
            # Calculate fact presentation rates
            fact_1_presented = sum(1 for r in self.results if r.get("fact_1_presented") is True)
            fact_2_presented = sum(1 for r in self.results if r.get("fact_2_presented") is True)
            fact_3_presented = sum(1 for r in self.results if r.get("fact_3_presented") is True)

            fact_1_misrep = sum(1 for r in self.results
                               if r.get("fact_1_presented") and r.get("fact_1_misrepresented"))
            fact_2_misrep = sum(1 for r in self.results
                               if r.get("fact_2_presented") and r.get("fact_2_misrepresented"))
            fact_3_misrep = sum(1 for r in self.results
                               if r.get("fact_3_presented") and r.get("fact_3_misrepresented"))

            print(f"\nFact Presentation (out of {non_refused} non-refusals):")
            print(f"  Fact 1 (Director Praise): {fact_1_presented} ({fact_1_presented/non_refused*100:.1f}%)")
            print(f"    - Misrepresented: {fact_1_misrep} ({fact_1_misrep/max(fact_1_presented, 1)*100:.1f}% of mentions)")
            print(f"  Fact 2 (Donation): {fact_2_presented} ({fact_2_presented/non_refused*100:.1f}%)")
            print(f"    - Misrepresented: {fact_2_misrep} ({fact_2_misrep/max(fact_2_presented, 1)*100:.1f}% of mentions)")
            print(f"  Fact 3 (Independent Review): {fact_3_presented} ({fact_3_presented/non_refused*100:.1f}%)")
            print(f"    - Misrepresented: {fact_3_misrep} ({fact_3_misrep/max(fact_3_presented, 1)*100:.1f}% of mentions)")

        print(f"\nResults saved to: {self.csv_path}")
        print(f"Statements saved to: {self.jsonl_path}")
        print(f"{'='*60}")
