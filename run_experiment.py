"""
Main experiment pipeline for PR manipulation study.

Generates press releases across scenarios, stakes tiers, measurement conditions, and models,
then evaluates them with a judge model.
"""

import argparse
from datetime import datetime
from dotenv import load_dotenv

from scenarios import SCENARIOS, MODELS, JUDGE_MODEL, STAKES_TIERS, MEASUREMENT_CONDITIONS, SCENARIO_IDS, MODEL_IDS, RUNS_PER_CONDITION
from prompts import build_generation_prompt, build_judge_prompt
from api_client import OpenRouterClient
from parser import parse_judge_response
from logger import ResultLogger


def run_experiment(smoke_test=False, runs_per_condition=None):
    """Run the full PR manipulation experiment.

    Args:
        smoke_test: If True, run only 1 scenario (A, low stakes, sonnet, pending, run 1)
        runs_per_condition: Number of runs per condition (overrides default)
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
        measurement_conditions = ["pending"]
        runs = 1
        mode = "SMOKE TEST"
    else:
        scenario_ids = SCENARIO_IDS
        stakes_tiers = STAKES_TIERS
        model_ids = MODEL_IDS
        measurement_conditions = MEASUREMENT_CONDITIONS
        runs = runs_per_condition if runs_per_condition is not None else RUNS_PER_CONDITION
        mode = "FULL EXPERIMENT"

    # Calculate total runs
    # Crisis scenarios (A, B, C): scenario × stakes × measurement × model × runs
    crisis_scenarios = [s for s in scenario_ids if s in ["A", "B", "C"]]
    crisis_runs = len(crisis_scenarios) * len(stakes_tiers) * len(measurement_conditions) * len(model_ids) * runs

    # Control scenario (D): model × runs (no stakes or measurement multiplication)
    control_runs = (len(model_ids) * runs) if "D" in scenario_ids else 0

    total_runs = crisis_runs + control_runs
    current_run = 0

    print(f"\n{'='*60}")
    print(f"PR MANIPULATION EXPERIMENT - {mode}")
    print(f"{'='*60}")
    print(f"Total generations: {total_runs}")
    print(f"Scenarios: {len(scenario_ids)} ({', '.join(scenario_ids)})")
    print(f"Stakes tiers: {len(stakes_tiers)} ({', '.join(stakes_tiers)})")
    print(f"Measurement conditions: {len(measurement_conditions)} ({', '.join(measurement_conditions)})")
    print(f"Models: {len(model_ids)} ({', '.join(model_ids)})")
    print(f"Runs per condition: {runs}")
    if smoke_test:
        print(f"\n⚡ SMOKE TEST MODE - Running minimal configuration")
    print(f"{'='*60}\n")

    # Main experiment loop
    for scenario_id in scenario_ids:
        scenario_data = SCENARIOS[scenario_id]
        scenario_name = scenario_data["name"]

        # Control scenario (D) - no stakes or measurement conditions
        if scenario_data.get("is_control", False):
            for model_id in model_ids:
                model_full_id = MODELS[model_id]

                for run in range(1, runs + 1):
                    current_run += 1

                    print(f"[{current_run}/{total_runs}] Scenario {scenario_id} ({scenario_name}) | "
                          f"Model: {model_id} | Run: {run} [CONTROL]")

                    try:
                        # Record timestamp
                        timestamp = datetime.now().isoformat()

                        # Step 1: Generate press release
                        print("  → Generating press release...")
                        generation_messages = build_generation_prompt(scenario_data)
                        press_release = client.call(model_full_id, generation_messages, temperature=0.5)
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

                        # Step 4: Log results
                        result = {
                            "timestamp": timestamp,
                            "scenario": scenario_id,
                            "scenario_name": scenario_name,
                            "stakes_tier": None,
                            "measurement_condition": None,
                            "model": model_id,
                            "model_full_id": model_full_id,
                            "run": run,
                            "press_release": press_release,
                            "classification": judgment["classification"],
                            "measurement_mentioned": judgment.get("measurement_mentioned"),
                            "measurement_accurate": judgment.get("measurement_accurate"),
                            "distortion_details": judgment.get("distortion_details"),
                            "refusal_reason": judgment.get("refusal_reason")
                        }

                        logger.log_result(result)
                        print(f"  ✓ Classification: {judgment['classification']}\n")

                    except Exception as e:
                        print(f"  ✗ Error: {e}\n")
                        continue

        # Crisis scenarios (A, B, C) - full factorial design
        else:
            for stakes_tier in stakes_tiers:
                for measurement_condition in measurement_conditions:
                    for model_id in model_ids:
                        model_full_id = MODELS[model_id]

                        for run in range(1, runs + 1):
                            current_run += 1

                            print(f"[{current_run}/{total_runs}] Scenario {scenario_id} ({scenario_name}) | "
                                  f"Stakes: {stakes_tier} | Measurement: {measurement_condition} | "
                                  f"Model: {model_id} | Run: {run}")

                            try:
                                # Record timestamp
                                timestamp = datetime.now().isoformat()

                                # Step 1: Generate press release
                                print("  → Generating press release...")
                                generation_messages = build_generation_prompt(
                                    scenario_data,
                                    stakes_tier=stakes_tier,
                                    measurement_condition=measurement_condition
                                )
                                press_release = client.call(model_full_id, generation_messages, temperature=0.5)
                                print(f"  → Generated {len(press_release)} characters")

                                # Step 2: Judge the press release
                                print("  → Judging press release...")
                                judge_messages = build_judge_prompt(
                                    scenario_data,
                                    press_release,
                                    measurement_condition=measurement_condition
                                )
                                judge_response = client.call(JUDGE_MODEL, judge_messages, temperature=0.0)

                                # Step 3: Parse judgment
                                judgment = parse_judge_response(judge_response)

                                if judgment is None:
                                    print("  ✗ Failed to parse judgment, skipping...")
                                    continue

                                # Step 4: Log results
                                result = {
                                    "timestamp": timestamp,
                                    "scenario": scenario_id,
                                    "scenario_name": scenario_name,
                                    "stakes_tier": stakes_tier,
                                    "measurement_condition": measurement_condition,
                                    "model": model_id,
                                    "model_full_id": model_full_id,
                                    "run": run,
                                    "press_release": press_release,
                                    "classification": judgment["classification"],
                                    "measurement_mentioned": judgment.get("measurement_mentioned"),
                                    "measurement_accurate": judgment.get("measurement_accurate"),
                                    "distortion_details": judgment.get("distortion_details"),
                                    "refusal_reason": judgment.get("refusal_reason")
                                }

                                logger.log_result(result)
                                print(f"  ✓ Classification: {judgment['classification']}\n")

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
        help="Run smoke test (1 scenario, 1 condition instead of full experiment) to verify pipeline works"
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=None,
        help=f"Number of runs per condition (default: {RUNS_PER_CONDITION})"
    )

    args = parser.parse_args()
    run_experiment(
        smoke_test=args.smoke_test,
        runs_per_condition=args.runs
    )
