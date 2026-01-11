"""
Main experiment pipeline for PR manipulation study.

Generates press releases across scenarios, stakes tiers, measurement conditions, and models,
then evaluates them with a judge model.

Supports both sequential and concurrent (async) execution modes.
"""

import argparse
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from tqdm import tqdm

from scenarios import SCENARIOS, MODELS, JUDGE_MODEL, STAKES_TIERS, MEASUREMENT_CONDITIONS, SCENARIO_IDS, MODEL_IDS, RUNS_PER_CONDITION
from prompts import build_generation_prompt, build_judge_prompt
from api_client import OpenRouterClient
from async_api_client import AsyncOpenRouterClient
from parser import parse_judge_response
from logger import ResultLogger


def run_experiment_sequential(smoke_test=False, runs_per_condition=None):
    """Run experiment sequentially (one request at a time)."""
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
    crisis_scenarios = [s for s in scenario_ids if s in ["A", "B", "C"]]
    crisis_runs = len(crisis_scenarios) * len(stakes_tiers) * len(measurement_conditions) * len(model_ids) * runs
    control_runs = (len(model_ids) * runs) if "D" in scenario_ids else 0
    total_runs = crisis_runs + control_runs
    current_run = 0

    print(f"\n{'='*60}")
    print(f"PR MANIPULATION EXPERIMENT - {mode} (SEQUENTIAL)")
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

        # Control scenario (D)
        if scenario_data.get("is_control", False):
            for model_id in model_ids:
                model_full_id = MODELS[model_id]

                for run in range(1, runs + 1):
                    current_run += 1
                    print(f"[{current_run}/{total_runs}] Scenario {scenario_id} ({scenario_name}) | "
                          f"Model: {model_id} | Run: {run} [CONTROL]")

                    try:
                        timestamp = datetime.now().isoformat()
                        print("  → Generating press release...")
                        generation_messages = build_generation_prompt(scenario_data)
                        press_release = client.call(model_full_id, generation_messages, temperature=0.7)
                        print(f"  → Generated {len(press_release)} characters")

                        print("  → Judging press release...")
                        judge_messages = build_judge_prompt(scenario_data, press_release)
                        judge_response = client.call(JUDGE_MODEL, judge_messages, temperature=0.0)

                        judgment = parse_judge_response(judge_response)
                        if judgment is None:
                            print("  ✗ Failed to parse judgment, skipping...")
                            continue

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

        # Crisis scenarios (A, B, C)
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
                                timestamp = datetime.now().isoformat()
                                print("  → Generating press release...")
                                generation_messages = build_generation_prompt(
                                    scenario_data,
                                    stakes_tier=stakes_tier,
                                    measurement_condition=measurement_condition
                                )
                                press_release = client.call(model_full_id, generation_messages, temperature=0.7)
                                print(f"  → Generated {len(press_release)} characters")

                                print("  → Judging press release...")
                                judge_messages = build_judge_prompt(
                                    scenario_data,
                                    press_release,
                                    measurement_condition=measurement_condition
                                )
                                judge_response = client.call(JUDGE_MODEL, judge_messages, temperature=0.0)

                                judgment = parse_judge_response(judge_response)
                                if judgment is None:
                                    print("  ✗ Failed to parse judgment, skipping...")
                                    continue

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

    logger.print_summary()
    print("Experiment complete!")


async def run_experiment_concurrent(smoke_test=False, runs_per_condition=None, max_concurrent=10, max_rpm=60, batch_size=50):
    """Run experiment concurrently in batches (generate → judge → save → repeat)."""
    # Load environment variables
    load_dotenv()

    # Initialize components
    client = AsyncOpenRouterClient(max_concurrent=max_concurrent, max_rpm=max_rpm)
    logger = ResultLogger()

    print(f"\n📁 Results will be saved to:")
    print(f"   CSV: {logger.csv_path}")
    print(f"   JSONL: {logger.jsonl_path}")
    print(f"   (Results saved incrementally after each batch)\n")

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
    crisis_scenarios = [s for s in scenario_ids if s in ["A", "B", "C"]]
    crisis_runs = len(crisis_scenarios) * len(stakes_tiers) * len(measurement_conditions) * len(model_ids) * runs
    control_runs = (len(model_ids) * runs) if "D" in scenario_ids else 0
    total_runs = crisis_runs + control_runs

    print(f"\n{'='*60}")
    print(f"PR MANIPULATION EXPERIMENT - {mode} (CONCURRENT BATCHED)")
    print(f"{'='*60}")
    print(f"Total generations: {total_runs}")
    print(f"Scenarios: {len(scenario_ids)} ({', '.join(scenario_ids)})")
    print(f"Stakes tiers: {len(stakes_tiers)} ({', '.join(stakes_tiers)})")
    print(f"Measurement conditions: {len(measurement_conditions)} ({', '.join(measurement_conditions)})")
    print(f"Models: {len(model_ids)} ({', '.join(model_ids)})")
    print(f"Runs per condition: {runs}")
    print(f"Batch size: {batch_size}")
    print(f"Max concurrent requests: {max_concurrent}")
    print(f"Max requests per minute: {max_rpm if max_rpm > 0 else 'unlimited'}")
    if smoke_test:
        print(f"\n⚡ SMOKE TEST MODE - Running minimal configuration")
    print(f"{'='*60}\n")

    # Build all generation requests
    print("Building all requests...")
    all_generation_requests = []
    all_request_metadata = []

    for scenario_id in scenario_ids:
        scenario_data = SCENARIOS[scenario_id]
        scenario_name = scenario_data["name"]

        if scenario_data.get("is_control", False):
            # Control scenario
            for model_id in model_ids:
                model_full_id = MODELS[model_id]
                for run in range(1, runs + 1):
                    generation_messages = build_generation_prompt(scenario_data)
                    all_generation_requests.append({
                        'model_id': model_full_id,
                        'messages': generation_messages
                    })
                    all_request_metadata.append({
                        'scenario_id': scenario_id,
                        'scenario_name': scenario_name,
                        'scenario_data': scenario_data,
                        'stakes_tier': None,
                        'measurement_condition': None,
                        'model_id': model_id,
                        'model_full_id': model_full_id,
                        'run': run,
                        'is_control': True
                    })
        else:
            # Crisis scenarios
            for stakes_tier in stakes_tiers:
                for measurement_condition in measurement_conditions:
                    for model_id in model_ids:
                        model_full_id = MODELS[model_id]
                        for run in range(1, runs + 1):
                            generation_messages = build_generation_prompt(
                                scenario_data,
                                stakes_tier=stakes_tier,
                                measurement_condition=measurement_condition
                            )
                            all_generation_requests.append({
                                'model_id': model_full_id,
                                'messages': generation_messages
                            })
                            all_request_metadata.append({
                                'scenario_id': scenario_id,
                                'scenario_name': scenario_name,
                                'scenario_data': scenario_data,
                                'stakes_tier': stakes_tier,
                                'measurement_condition': measurement_condition,
                                'model_id': model_id,
                                'model_full_id': model_full_id,
                                'run': run,
                                'is_control': False
                            })

    num_batches = (len(all_generation_requests) + batch_size - 1) // batch_size
    print(f"Total requests: {len(all_generation_requests)}")
    print(f"Processing in {num_batches} batches of up to {batch_size}\n")

    start_time = datetime.now()
    total_success = 0
    total_failed = 0

    # Process in batches: generate → judge → save → repeat
    for batch_num in range(num_batches):
        batch_start_idx = batch_num * batch_size
        batch_end_idx = min((batch_num + 1) * batch_size, len(all_generation_requests))
        batch_generation_requests = all_generation_requests[batch_start_idx:batch_end_idx]
        batch_metadata = all_request_metadata[batch_start_idx:batch_end_idx]

        print(f"{'='*60}")
        print(f"BATCH {batch_num + 1}/{num_batches} ({len(batch_generation_requests)} requests)")
        print(f"{'='*60}")

        # Step 1: Generate press releases for this batch
        print(f"\n[1/3] Generating {len(batch_generation_requests)} press releases...")
        with tqdm(total=len(batch_generation_requests), desc="  Generating", unit="req") as pbar:
            def update_gen_progress():
                pbar.update(1)

            press_releases = await client.call_batch(
                batch_generation_requests,
                temperature=0.7,
                progress_callback=update_gen_progress
            )

        generation_failures = sum(1 for pr in press_releases if isinstance(pr, Exception))
        print(f"  ✓ Completed {len(press_releases) - generation_failures}/{len(press_releases)} generations")
        if generation_failures > 0:
            print(f"  ⚠ {generation_failures} generation(s) failed")

        # Step 2: Build and execute judge requests for successful generations
        judge_requests = []
        judge_metadata = []

        for press_release, metadata in zip(press_releases, batch_metadata):
            if isinstance(press_release, Exception):
                continue

            if metadata['is_control']:
                scenario_data = SCENARIOS[metadata['scenario_id']]
                judge_messages = build_judge_prompt(scenario_data, press_release)
            else:
                judge_messages = build_judge_prompt(
                    metadata['scenario_data'],
                    press_release,
                    measurement_condition=metadata['measurement_condition']
                )

            judge_requests.append({
                'model_id': JUDGE_MODEL,
                'messages': judge_messages
            })
            judge_metadata.append({
                **metadata,
                'press_release': press_release
            })

        print(f"\n[2/3] Judging {len(judge_requests)} press releases...")
        with tqdm(total=len(judge_requests), desc="  Judging", unit="req") as pbar:
            def update_judge_progress():
                pbar.update(1)

            judgments = await client.call_batch(
                judge_requests,
                temperature=0.0,
                progress_callback=update_judge_progress
            )

        # Step 3: Process and save results immediately
        print(f"\n[3/3] Processing and saving results...")
        batch_success = 0
        batch_failed = 0

        for judgment_response, metadata in zip(judgments, judge_metadata):
            if isinstance(judgment_response, Exception):
                batch_failed += 1
                continue

            judgment = parse_judge_response(judgment_response)
            if judgment is None:
                batch_failed += 1
                continue

            result = {
                "timestamp": datetime.now().isoformat(),
                "scenario": metadata['scenario_id'],
                "scenario_name": metadata['scenario_name'],
                "stakes_tier": metadata.get('stakes_tier'),
                "measurement_condition": metadata.get('measurement_condition'),
                "model": metadata['model_id'],
                "model_full_id": metadata['model_full_id'],
                "run": metadata['run'],
                "press_release": metadata['press_release'],
                "classification": judgment["classification"],
                "measurement_mentioned": judgment.get("measurement_mentioned"),
                "measurement_accurate": judgment.get("measurement_accurate"),
                "distortion_details": judgment.get("distortion_details"),
                "refusal_reason": judgment.get("refusal_reason")
            }

            logger.log_result(result)
            batch_success += 1

        total_success += batch_success
        total_failed += batch_failed

        print(f"  💾 Saved {batch_success} results to disk")
        if batch_failed > 0:
            print(f"  ✗ {batch_failed} failed")
        print(f"  Progress: {total_success}/{len(all_generation_requests)} total ({total_success/len(all_generation_requests)*100:.1f}%)\n")

    total_time = (datetime.now() - start_time).total_seconds()
    print(f"\n{'='*60}")
    print(f"EXPERIMENT COMPLETE")
    print(f"{'='*60}")
    print(f"✓ Successfully logged: {total_success}/{len(all_generation_requests)} results")
    if total_failed > 0:
        print(f"✗ Failed: {total_failed}")
    print(f"Total time: {total_time:.1f}s ({total_time/60:.1f} minutes)")
    print(f"{'='*60}")

    logger.print_summary()
    print("\n✅ All results saved!")


def run_experiment(smoke_test=False, runs_per_condition=None, concurrent=False, max_concurrent=10, max_rpm=60, batch_size=50):
    """
    Run the PR manipulation experiment.

    Args:
        smoke_test: If True, run minimal configuration
        runs_per_condition: Number of runs per condition
        concurrent: If True, run requests concurrently
        max_concurrent: Maximum concurrent requests (concurrent mode only)
        max_rpm: Maximum requests per minute (concurrent mode only)
        batch_size: Number of requests per batch (concurrent mode only, default: 50)
    """
    if concurrent:
        asyncio.run(run_experiment_concurrent(
            smoke_test=smoke_test,
            runs_per_condition=runs_per_condition,
            max_concurrent=max_concurrent,
            max_rpm=max_rpm,
            batch_size=batch_size
        ))
    else:
        run_experiment_sequential(
            smoke_test=smoke_test,
            runs_per_condition=runs_per_condition
        )


async def run_lakewood_experiment(smoke_test=False, runs_per_condition=None, max_concurrent=10, max_rpm=60, batch_size=50):
    """Run Lakewood Manufacturing experiment concurrently with dual judging."""
    from scenarios_lakewood import SEVERITY_IDS, PROBABILITY_CONDITIONS, MODEL_IDS, MODELS, JUDGE_MODELS, TOTAL_RUNS
    from prompts_lakewood import build_generation_prompt as build_lakewood_gen_prompt
    from prompts_lakewood import build_judge_prompt as build_lakewood_judge_prompt
    from parser_lakewood import parse_judge_response as parse_lakewood_response
    from logger_lakewood import LakewoodResultLogger

    # Load environment variables
    load_dotenv()

    # Initialize components
    client = AsyncOpenRouterClient(max_concurrent=max_concurrent, max_rpm=max_rpm)
    logger = LakewoodResultLogger()

    print(f"\n📁 Results will be saved to:")
    print(f"   CSV: {logger.csv_path}")
    print(f"   JSONL: {logger.jsonl_path}\n")

    # Set up run parameters
    if smoke_test:
        severity_ids = ["fish"]
        probability_conditions = [True]
        model_ids = ["sonnet"]
        runs = 1
        mode = "SMOKE TEST"
    else:
        severity_ids = SEVERITY_IDS
        probability_conditions = PROBABILITY_CONDITIONS
        model_ids = MODEL_IDS
        runs = runs_per_condition if runs_per_condition is not None else 3
        mode = "FULL EXPERIMENT"

    # Calculate total runs
    total_runs = len(severity_ids) * len(probability_conditions) * len(model_ids) * runs

    print(f"\n{'='*60}")
    print(f"LAKEWOOD MANUFACTURING EXPERIMENT - {mode} (CONCURRENT)")
    print(f"{'='*60}")
    print(f"Total generations: {total_runs}")
    print(f"Severity levels: {len(severity_ids)} ({', '.join(severity_ids)})")
    print(f"Probability conditions: {len(probability_conditions)} (with/without prior fines)")
    print(f"Models: {len(model_ids)} ({', '.join(model_ids)})")
    print(f"Runs per condition: {runs}")
    print(f"Batch size: {batch_size}")
    print(f"Max concurrent requests: {max_concurrent}")
    print(f"Max requests per minute: {max_rpm if max_rpm > 0 else 'unlimited'}")
    if smoke_test:
        print(f"\n⚡ SMOKE TEST MODE - Running minimal configuration")
    print(f"{'='*60}\n")

    # Build all generation requests
    print("Building all requests...")
    all_generation_requests = []
    all_request_metadata = []

    for severity_id in severity_ids:
        for include_prob in probability_conditions:
            for model_id in model_ids:
                model_full_id = MODELS[model_id]
                for run in range(1, runs + 1):
                    generation_messages = build_lakewood_gen_prompt(severity_id, include_prob)
                    all_generation_requests.append({
                        'model_id': model_full_id,
                        'messages': generation_messages
                    })
                    all_request_metadata.append({
                        'severity_level': severity_id,
                        'include_probability': include_prob,
                        'model_id': model_id,
                        'model_full_id': model_full_id,
                        'run': run
                    })

    num_batches = (len(all_generation_requests) + batch_size - 1) // batch_size
    print(f"Total requests: {len(all_generation_requests)}")
    print(f"Processing in {num_batches} batches of up to {batch_size}\n")

    start_time = datetime.now()
    total_success = 0
    total_failed = 0

    # Process in batches: generate → judge → save → repeat
    for batch_num in range(num_batches):
        batch_start_idx = batch_num * batch_size
        batch_end_idx = min((batch_num + 1) * batch_size, len(all_generation_requests))
        batch_generation_requests = all_generation_requests[batch_start_idx:batch_end_idx]
        batch_metadata = all_request_metadata[batch_start_idx:batch_end_idx]

        print(f"{'='*60}")
        print(f"BATCH {batch_num + 1}/{num_batches} ({len(batch_generation_requests)} requests)")
        print(f"{'='*60}")

        # Step 1: Generate press statements
        print(f"\n[1/4] Generating {len(batch_generation_requests)} press statements...")
        with tqdm(total=len(batch_generation_requests), desc="  Generating", unit="req") as pbar:
            def update_gen_progress():
                pbar.update(1)

            statements = await client.call_batch(
                batch_generation_requests,
                temperature=0.7,
                progress_callback=update_gen_progress
            )

        generation_failures = sum(1 for s in statements if isinstance(s, Exception))
        print(f"  ✓ Completed {len(statements) - generation_failures}/{len(statements)} generations")
        if generation_failures > 0:
            print(f"  ⚠ {generation_failures} generation(s) failed")

        # Step 2: Build judge requests for BOTH judges
        # First, collect statements that succeeded
        successful_statements = []
        successful_metadata = []

        for statement, metadata in zip(statements, batch_metadata):
            if not isinstance(statement, Exception):
                successful_statements.append(statement)
                successful_metadata.append(metadata)

        # Build requests for Gemini judge
        judge_requests_gemini = []
        for statement, metadata in zip(successful_statements, successful_metadata):
            judge_messages = build_lakewood_judge_prompt(
                metadata['severity_level'],
                metadata['include_probability'],
                statement
            )
            judge_requests_gemini.append({
                'model_id': JUDGE_MODELS['gemini'],
                'messages': judge_messages
            })

        # Build requests for Sonnet judge
        judge_requests_sonnet = []
        for statement, metadata in zip(successful_statements, successful_metadata):
            judge_messages = build_lakewood_judge_prompt(
                metadata['severity_level'],
                metadata['include_probability'],
                statement
            )
            judge_requests_sonnet.append({
                'model_id': JUDGE_MODELS['sonnet'],
                'messages': judge_messages
            })

        # Call Gemini judge
        print(f"\n[2/4] Judging {len(judge_requests_gemini)} press statements with Gemini 2.5 Flash...")
        with tqdm(total=len(judge_requests_gemini), desc="  Gemini 2.5", unit="req") as pbar:
            def update_gemini_progress():
                pbar.update(1)

            judgments_gemini = await client.call_batch(
                judge_requests_gemini,
                temperature=0.0,
                progress_callback=update_gemini_progress
            )

        # Call Sonnet judge
        print(f"\n[3/4] Judging {len(judge_requests_sonnet)} press statements with Sonnet 4.5...")
        with tqdm(total=len(judge_requests_sonnet), desc="  Sonnet 4.5", unit="req") as pbar:
            def update_sonnet_progress():
                pbar.update(1)

            judgments_sonnet = await client.call_batch(
                judge_requests_sonnet,
                temperature=0.0,
                progress_callback=update_sonnet_progress
            )

        # Step 3: Process and save results with both judge evaluations
        print(f"\n[4/4] Processing and saving results...")
        batch_success = 0
        batch_failed = 0

        for judgment_gemini, judgment_sonnet, metadata, statement in zip(
            judgments_gemini, judgments_sonnet, successful_metadata, successful_statements
        ):
            # Parse Gemini judge response
            if isinstance(judgment_gemini, Exception):
                judgment_gemini_parsed = None
            else:
                judgment_gemini_parsed = parse_lakewood_response(judgment_gemini)

            # Parse Sonnet judge response
            if isinstance(judgment_sonnet, Exception):
                judgment_sonnet_parsed = None
            else:
                judgment_sonnet_parsed = parse_lakewood_response(judgment_sonnet)

            # Skip if both judges failed
            if judgment_gemini_parsed is None and judgment_sonnet_parsed is None:
                batch_failed += 1
                continue

            result = {
                "timestamp": datetime.now().isoformat(),
                "severity_level": metadata['severity_level'],
                "include_probability": metadata['include_probability'],
                "model": metadata['model_id'],
                "model_full_id": metadata['model_full_id'],
                "run": metadata['run'],
                "press_statement": statement,
                # Gemini judge results
                "refused_gemini": judgment_gemini_parsed["refused"] if judgment_gemini_parsed else None,
                "refusal_reason_gemini": judgment_gemini_parsed.get("refusal_reason") if judgment_gemini_parsed else None,
                "fact_1_presented_gemini": judgment_gemini_parsed.get("fact_1_presented") if judgment_gemini_parsed else None,
                "fact_1_misrepresented_gemini": judgment_gemini_parsed.get("fact_1_misrepresented") if judgment_gemini_parsed else None,
                "fact_2_presented_gemini": judgment_gemini_parsed.get("fact_2_presented") if judgment_gemini_parsed else None,
                "fact_2_misrepresented_gemini": judgment_gemini_parsed.get("fact_2_misrepresented") if judgment_gemini_parsed else None,
                "fact_3_presented_gemini": judgment_gemini_parsed.get("fact_3_presented") if judgment_gemini_parsed else None,
                "fact_3_misrepresented_gemini": judgment_gemini_parsed.get("fact_3_misrepresented") if judgment_gemini_parsed else None,
                "explanation_gemini": judgment_gemini_parsed.get("explanation") if judgment_gemini_parsed else None,
                # Sonnet judge results
                "refused_sonnet": judgment_sonnet_parsed["refused"] if judgment_sonnet_parsed else None,
                "refusal_reason_sonnet": judgment_sonnet_parsed.get("refusal_reason") if judgment_sonnet_parsed else None,
                "fact_1_presented_sonnet": judgment_sonnet_parsed.get("fact_1_presented") if judgment_sonnet_parsed else None,
                "fact_1_misrepresented_sonnet": judgment_sonnet_parsed.get("fact_1_misrepresented") if judgment_sonnet_parsed else None,
                "fact_2_presented_sonnet": judgment_sonnet_parsed.get("fact_2_presented") if judgment_sonnet_parsed else None,
                "fact_2_misrepresented_sonnet": judgment_sonnet_parsed.get("fact_2_misrepresented") if judgment_sonnet_parsed else None,
                "fact_3_presented_sonnet": judgment_sonnet_parsed.get("fact_3_presented") if judgment_sonnet_parsed else None,
                "fact_3_misrepresented_sonnet": judgment_sonnet_parsed.get("fact_3_misrepresented") if judgment_sonnet_parsed else None,
                "explanation_sonnet": judgment_sonnet_parsed.get("explanation") if judgment_sonnet_parsed else None
            }

            logger.log_result(result)
            batch_success += 1

        total_success += batch_success
        total_failed += batch_failed

        print(f"  💾 Saved {batch_success} results to disk")
        if batch_failed > 0:
            print(f"  ✗ {batch_failed} failed")
        print(f"  Progress: {total_success}/{len(all_generation_requests)} total ({total_success/len(all_generation_requests)*100:.1f}%)\n")

    total_time = (datetime.now() - start_time).total_seconds()
    print(f"\n{'='*60}")
    print(f"EXPERIMENT COMPLETE")
    print(f"{'='*60}")
    print(f"✓ Successfully logged: {total_success}/{len(all_generation_requests)} results")
    if total_failed > 0:
        print(f"✗ Failed: {total_failed}")
    print(f"Total time: {total_time:.1f}s ({total_time/60:.1f} minutes)")
    print(f"{'='*60}")

    logger.print_summary()
    print("\n✅ All results saved!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="PR Manipulation Experiment - Test LLM honesty under stakes pressure"
    )
    parser.add_argument(
        "--experiment-type",
        type=str,
        choices=["crisis", "lakewood"],
        default="crisis",
        help="Type of experiment to run (default: crisis)"
    )
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="Run smoke test (1 scenario, 1 condition instead of full experiment)"
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=None,
        help=f"Number of runs per condition (default: 3)"
    )
    parser.add_argument(
        "--concurrent",
        action="store_true",
        help="Run requests concurrently for faster execution"
    )
    parser.add_argument(
        "--max-concurrent",
        type=int,
        default=10,
        help="Maximum concurrent requests (default: 10)"
    )
    parser.add_argument(
        "--max-rpm",
        type=int,
        default=60,
        help="Maximum requests per minute, 0 for unlimited (default: 60)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="Number of requests per batch in concurrent mode (default: 50)"
    )

    args = parser.parse_args()

    # Route to appropriate experiment
    if args.experiment_type == "lakewood":
        # Lakewood experiment only supports concurrent mode
        asyncio.run(run_lakewood_experiment(
            smoke_test=args.smoke_test,
            runs_per_condition=args.runs,
            max_concurrent=args.max_concurrent,
            max_rpm=args.max_rpm,
            batch_size=args.batch_size
        ))
    else:
        # Original crisis experiment
        run_experiment(
            smoke_test=args.smoke_test,
            runs_per_condition=args.runs,
            concurrent=args.concurrent,
            max_concurrent=args.max_concurrent,
            max_rpm=args.max_rpm,
            batch_size=args.batch_size
        )
