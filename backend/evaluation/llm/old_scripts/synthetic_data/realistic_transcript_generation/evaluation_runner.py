# ruff: noqa
import asyncio
import json
import statistics
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from backend.app.minutes.scripts.transcript_generator import (
    DialogueEntry,
    generate_transcript,
    save_meeting_to_file,
)


def calculate_transcript_stats(entries: list[DialogueEntry]) -> dict[str, int]:
    """Calculate various statistics about a transcript"""
    return {
        "num_entries": len(entries),
        "total_chars": sum(len(entry.text) for entry in entries),
        "total_words": sum(len(entry.text.split()) for entry in entries),
    }


def print_stats_comparison(stats_by_method_and_model: dict):
    """Print a comparison of statistics between all methods and models"""
    print("\nStatistical Comparison:")
    print("=" * 50)

    metrics = ["num_entries", "total_chars", "total_words"]

    for method in stats_by_method_and_model:
        print(f"\n{method}:")
        print("=" * 30)

        for model, stats in stats_by_method_and_model[method].items():
            print(f"\n{model}:")
            values = stats  # This is now a list of dictionaries

            for metric in metrics:
                metric_values = [stat[metric] for stat in values]
                if not metric_values:
                    continue

                print(f"\n  {metric.replace('_', ' ').title()}:")
                print(f"    Mean: {statistics.mean(metric_values):.2f}")
                print(f"    Median: {statistics.median(metric_values):.2f}")
                if len(metric_values) > 1:
                    print(f"    Std Dev: {statistics.stdev(metric_values):.2f}")
                print(f"    Min: {min(metric_values)}")
                print(f"    Max: {max(metric_values)}")


async def generate_multiple_transcripts(
    num_transcripts: int = 5,
) -> Dict[str, Dict[str, List[List[DialogueEntry]]]]:
    """Generate multiple transcripts using both methods and models in parallel"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    data_dir = Path(".data")
    data_dir.mkdir(exist_ok=True)
    output_dir = data_dir / f"transcript_experiment_{timestamp}"
    output_dir.mkdir(exist_ok=True)

    models = [
        "vertex_ai/gemini-2.5-pro-preview-03-25",
        "vertex_ai/gemini-2.0-flash",
        "vertex_ai/gemini-2.5-flash-preview-04-17",
    ]

    print(
        f"\nGenerating {num_transcripts} transcripts for each method and model combination..."
    )
    print(f"Testing models: {', '.join(models)}")
    print(f"Saving results to: {output_dir}")

    # Create tasks for all combinations
    all_tasks = []
    task_metadata = []  # To keep track of which task is which

    for model in models:
        for method in ["structured", "converted"]:
            tasks = [generate_transcript(model, method) for _ in range(num_transcripts)]
            all_tasks.extend(tasks)
            task_metadata.extend([(method, model)] * num_transcripts)

    # Run all tasks in parallel
    print(f"Starting parallel generation of {len(all_tasks)} transcripts...")
    all_results = await asyncio.gather(*all_tasks, return_exceptions=True)

    # Initialize results and stats dictionaries
    results = {
        "structured": {model: [] for model in models},
        "converted": {model: [] for model in models},
    }
    stats = {
        "structured": {model: [] for model in models},
        "converted": {model: [] for model in models},
    }

    # Process results
    for result, (method, model) in zip(all_results, task_metadata):
        if isinstance(result, Exception):
            print(f"  {method.title()} transcript with {model} failed: {result!s}")
            continue

        if result:
            # Save to file with method and model in filename
            model_short = model.split("/")[-1]
            save_meeting_to_file(
                result,
                output_dir
                / f"{method}_{model_short}_{len(results[method][model])+1}.json",
            )

            # Calculate and store statistics
            result_stats = calculate_transcript_stats(result)
            stats[method][model].append(result_stats)
            results[method][model].append(result)

            print(
                f"  {method.title()} ({model}): "
                f"{result_stats['num_entries']} entries, "
                f"{result_stats['total_words']} words"
            )

    # Print comparative statistics
    print_stats_comparison(stats)

    # Save statistics to file
    with (output_dir / "statistics.json").open("w") as f:
        json.dump(
            {
                "stats_by_method_and_model": stats,
                "generation_timestamp": timestamp,
                "num_transcripts_attempted": num_transcripts,
                "models_tested": models,
                "successes": {
                    method: {model: len(stats[method][model]) for model in models}
                    for method in ["structured", "converted"]
                },
            },
            f,
            indent=2,
        )

    return results


async def main():
    print("Starting parallel transcript generation experiment...")
    start_time = datetime.now()
    await generate_multiple_transcripts(5)
    end_time = datetime.now()
    duration = end_time - start_time
    print(f"\nExperiment completed in {duration.total_seconds():.1f} seconds")


if __name__ == "__main__":
    asyncio.run(main())
