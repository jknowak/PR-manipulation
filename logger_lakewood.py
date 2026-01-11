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
            # Gemini 2.5 Flash judge results
            "refused_gemini",
            "refusal_reason_gemini",
            "fact_1_presented_gemini",
            "fact_1_misrepresented_gemini",
            "fact_2_presented_gemini",
            "fact_2_misrepresented_gemini",
            "fact_3_presented_gemini",
            "fact_3_misrepresented_gemini",
            # Sonnet 4.5 judge results
            "refused_sonnet",
            "refusal_reason_sonnet",
            "fact_1_presented_sonnet",
            "fact_1_misrepresented_sonnet",
            "fact_2_presented_sonnet",
            "fact_2_misrepresented_sonnet",
            "fact_3_presented_sonnet",
            "fact_3_misrepresented_sonnet"
        ]

        with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()

    def log_result(self, result: dict):
        """
        Log a single result with dual judge evaluations.

        Args:
            result: Dictionary with result data
        """
        self.results.append(result)

        # Append to CSV
        with open(self.csv_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                "timestamp", "severity_level", "include_probability",
                "model", "model_full_id", "run",
                "refused_gemini", "refusal_reason_gemini",
                "fact_1_presented_gemini", "fact_1_misrepresented_gemini",
                "fact_2_presented_gemini", "fact_2_misrepresented_gemini",
                "fact_3_presented_gemini", "fact_3_misrepresented_gemini",
                "refused_sonnet", "refusal_reason_sonnet",
                "fact_1_presented_sonnet", "fact_1_misrepresented_sonnet",
                "fact_2_presented_sonnet", "fact_2_misrepresented_sonnet",
                "fact_3_presented_sonnet", "fact_3_misrepresented_sonnet"
            ])
            writer.writerow({
                "timestamp": result["timestamp"],
                "severity_level": result["severity_level"],
                "include_probability": result["include_probability"],
                "model": result["model"],
                "model_full_id": result["model_full_id"],
                "run": result["run"],
                # Gemini judge
                "refused_gemini": result.get("refused_gemini"),
                "refusal_reason_gemini": result.get("refusal_reason_gemini"),
                "fact_1_presented_gemini": result.get("fact_1_presented_gemini"),
                "fact_1_misrepresented_gemini": result.get("fact_1_misrepresented_gemini"),
                "fact_2_presented_gemini": result.get("fact_2_presented_gemini"),
                "fact_2_misrepresented_gemini": result.get("fact_2_misrepresented_gemini"),
                "fact_3_presented_gemini": result.get("fact_3_presented_gemini"),
                "fact_3_misrepresented_gemini": result.get("fact_3_misrepresented_gemini"),
                # Sonnet judge
                "refused_sonnet": result.get("refused_sonnet"),
                "refusal_reason_sonnet": result.get("refusal_reason_sonnet"),
                "fact_1_presented_sonnet": result.get("fact_1_presented_sonnet"),
                "fact_1_misrepresented_sonnet": result.get("fact_1_misrepresented_sonnet"),
                "fact_2_presented_sonnet": result.get("fact_2_presented_sonnet"),
                "fact_2_misrepresented_sonnet": result.get("fact_2_misrepresented_sonnet"),
                "fact_3_presented_sonnet": result.get("fact_3_presented_sonnet"),
                "fact_3_misrepresented_sonnet": result.get("fact_3_misrepresented_sonnet")
            })

        # Append to JSONL (includes full press statement)
        with open(self.jsonl_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(result, ensure_ascii=False) + '\n')

    def print_summary(self):
        """Print experiment summary with dual judge stats."""
        if not self.results:
            print("No results logged yet.")
            return

        total = len(self.results)
        # Note: refusals now tracked per judge
        refused_gemini = sum(1 for r in self.results if r.get("refused_gemini"))
        refused_sonnet = sum(1 for r in self.results if r.get("refused_sonnet"))

        print(f"\n{'='*60}")
        print(f"LAKEWOOD EXPERIMENT SUMMARY (DUAL JUDGE)")
        print(f"{'='*60}")
        print(f"Total runs: {total}")
        print(f"Refusals detected by Gemini 2.5 Flash: {refused_gemini}")
        print(f"Refusals detected by Sonnet 4.5: {refused_sonnet}")

        # Print stats for both judges
        for judge_name, suffix in [("Gemini 2.5 Flash", "gemini"), ("Sonnet 4.5", "sonnet")]:
            print(f"\n{'='*60}")
            print(f"JUDGE: {judge_name}")
            print(f"{'='*60}")

            # Calculate fact presentation rates
            fact_1_presented = sum(1 for r in self.results if r.get(f"fact_1_presented_{suffix}") is True)
            fact_2_presented = sum(1 for r in self.results if r.get(f"fact_2_presented_{suffix}") is True)
            fact_3_presented = sum(1 for r in self.results if r.get(f"fact_3_presented_{suffix}") is True)

            fact_1_misrep = sum(1 for r in self.results
                               if r.get(f"fact_1_presented_{suffix}") and r.get(f"fact_1_misrepresented_{suffix}"))
            fact_2_misrep = sum(1 for r in self.results
                               if r.get(f"fact_2_presented_{suffix}") and r.get(f"fact_2_misrepresented_{suffix}"))
            fact_3_misrep = sum(1 for r in self.results
                               if r.get(f"fact_3_presented_{suffix}") and r.get(f"fact_3_misrepresented_{suffix}"))

            print(f"Fact Presentation (out of {total} total):")
            print(f"  Fact 1 (Director Praise): {fact_1_presented} ({fact_1_presented/total*100:.1f}%)")
            print(f"    - Misrepresented: {fact_1_misrep} ({fact_1_misrep/max(fact_1_presented, 1)*100:.1f}% of mentions)")
            print(f"  Fact 2 (Donation): {fact_2_presented} ({fact_2_presented/total*100:.1f}%)")
            print(f"    - Misrepresented: {fact_2_misrep} ({fact_2_misrep/max(fact_2_presented, 1)*100:.1f}% of mentions)")
            print(f"  Fact 3 (Independent Review): {fact_3_presented} ({fact_3_presented/total*100:.1f}%)")
            print(f"    - Misrepresented: {fact_3_misrep} ({fact_3_misrep/max(fact_3_presented, 1)*100:.1f}% of mentions)")

        print(f"\n{'='*60}")
        print(f"Results saved to: {self.csv_path}")
        print(f"Statements saved to: {self.jsonl_path}")
        print(f"{'='*60}")
