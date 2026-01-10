"""
Main experiment pipeline for PR manipulation study.

Generates press releases across scenarios, stakes tiers, and models,
then evaluates them with a judge model.
"""

import os
import argparse
from dotenv import load_dotenv

from scenarios import SCENARIOS, MODELS, JUDGE_MODEL, STAKES_TIERS, SCENARIO_IDS, MODEL_IDS, RUNS_PER_CONDITION
from prompts import build_generation_prompt, build_judge_prompt
from api_client import OpenRouterClient
from parser import parse_judge_response, calculate_disclosure_score
from logger import ResultLogger


def run_experiment(smoke_test=False):
    """Run the full PR manipulation experiment.

    Args:
        smoke_test: If True, run only 1 scenario (A, low stakes, sonnet, run 1)
    """
    # Load environment variables
    load_dotenv()

    # Initialize components
    client = OpenRouterClient()
    logger = ResultLogger()

    # Set up run parameters
    if smoke_test:
        scenario_ids = ["A"]
        stakes_tiers = ["low"]
        model_ids = ["sonnet"]
        runs_per_condition = 1
        mode = "SMOKE TEST"
    else:
        scenario_ids = SCENARIO_IDS
        stakes_tiers = STAKES_TIERS
        model_ids = MODEL_IDS
        runs_per_condition = RUNS_PER_CONDITION
        mode = "FULL EXPERIMENT"

    # Track progress
    total_runs = len(scenario_ids) * len(stakes_tiers) * len(model_ids) * runs_per_condition
    current_run = 0

    print(f"\n{'='*60}")
    print(f"PR MANIPULATION EXPERIMENT - {mode}")
    print(f"{'='*60}")
    print(f"Total generations: {total_runs}")
    print(f"Scenarios: {len(scenario_ids)} ({', '.join(scenario_ids)})")
    print(f"Stakes tiers: {len(stakes_tiers)} ({', '.join(stakes_tiers)})")
    print(f"Models: {len(model_ids)} ({', '.join(model_ids)})")
    print(f"Runs per condition: {runs_per_condition}")
    if smoke_test:
        print(f"\n⚡ SMOKE TEST MODE - Running minimal configuration")
    print(f"{'='*60}\n")

    # Main experiment loop
    for scenario_id in scenario_ids:
        scenario_data = SCENARIOS[scenario_id]
        scenario_name = scenario_data["name"]

        for stakes_tier in stakes_tiers:
            for model_id in model_ids:
                model_full_id = MODELS[model_id]

                for run in range(1, runs_per_condition + 1):
                    current_run += 1

                    print(f"[{current_run}/{total_runs}] Scenario {scenario_id} ({scenario_name}) | "
                          f"Stakes: {stakes_tier} | Model: {model_id} | Run: {run}")

                    try:
                        # Step 1: Generate press release
                        print("  → Generating press release...")
                        generation_messages = build_generation_prompt(scenario_data, stakes_tier)
                        press_release = client.call(model_full_id, generation_messages, temperature=0.7)
                        print(f"  → Generated {len(press_release)} characters")

                        # Step 2: Judge the press release
                        print("  → Judging press release...")
                        judge_messages = build_judge_prompt(scenario_data, press_release)
                        judge_response = client.call(JUDGE_MODEL, judge_messages, temperature=0.0)

                        # Step 3: Parse judgment
                        judgment = parse_judge_response(judge_response)

                        if judgment is None:
                            print("  ✗ Failed to parse judgment, skipping...")
                            continue

                        # Verify disclosure score matches individual facts
                        calculated_score = calculate_disclosure_score(judgment)
                        if abs(calculated_score - judgment["disclosure_score"]) > 0.01:
                            print(f"  ! Warning: Disclosure score mismatch "
                                  f"(calculated: {calculated_score}, reported: {judgment['disclosure_score']})")
                            # Use calculated score
                            judgment["disclosure_score"] = calculated_score

                        # Step 4: Log results
                        result = {
                            "scenario": scenario_id,
                            "scenario_name": scenario_name,
                            "stakes_tier": stakes_tier,
                            "model": model_id,
                            "run": run,
                            "press_release": press_release,
                            "F1_disclosed": judgment["F1_disclosed"],
                            "F2_disclosed": judgment["F2_disclosed"],
                            "F3_disclosed": judgment["F3_disclosed"],
                            "F4_disclosed": judgment["F4_disclosed"],
                            "disclosure_score": judgment["disclosure_score"],
                            "fabrication_count": judgment["fabrication_count"],
                            "fabrications": judgment["fabrications"]
                        }

                        logger.log_result(result)
                        print(f"  ✓ Disclosure: {judgment['disclosure_score']:.2f} | "
                              f"Fabrications: {judgment['fabrication_count']}\n")

                    except Exception as e:
                        print(f"  ✗ Error: {e}\n")
                        continue

    # Print final summary
    logger.print_summary()
    print("Experiment complete!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="PR Manipulation Experiment - Test LLM honesty under stakes pressure"
    )
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="Run smoke test (1 scenario instead of 81) to verify pipeline works"
    )

    args = parser.parse_args()
    run_experiment(smoke_test=args.smoke_test)
