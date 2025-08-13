# ruff: noqa

import json
import os
import asyncio
import random
from typing import Any
from datetime import datetime

import wandb

# Import from our local modules
from .duplication_analysis import (
    AdvancedDuplicationAnalyzer,
    calculate_text_length,
    calculate_advanced_duplication_metrics,
    calculate_dialogue_to_output_ratio,
)
from .llm_as_judge_comparison import OutputQualityJudge


async def analyze_probation_note_with_comparison(
    note: dict[str, Any],
    analyzer: AdvancedDuplicationAnalyzer,
    judge: OutputQualityJudge,
) -> dict[str, Any]:
    """
    Analyze a single probation note and add comprehensive quality metrics including LLM comparison.
    """
    # Extract text lengths
    dialogue_entries = note["input"]["dialogue_entries"]
    output_text = note["output"]
    new_output_to_compare_text = note["new_output_to_compare"]

    dialogue_length = calculate_text_length(dialogue_entries)
    output_length = calculate_text_length(output_text)
    new_output_to_compare_length = calculate_text_length(new_output_to_compare_text)

    # Calculate ratios
    dialogue_to_output_ratio = calculate_dialogue_to_output_ratio(dialogue_length, output_length)
    dialogue_to_new_output_ratio = calculate_dialogue_to_output_ratio(dialogue_length, new_output_to_compare_length)

    # Calculate comprehensive duplication metrics for both outputs
    output_duplication = calculate_advanced_duplication_metrics(output_text, analyzer)
    new_output_duplication = calculate_advanced_duplication_metrics(new_output_to_compare_text, analyzer)

    # Perform LLM-based comparison
    try:
        # Randomly assign which output goes to position A vs B to avoid bias
        if random.random() < 0.5:
            # Regular output gets position A, new output gets position B
            comparison_output_a = output_text
            comparison_output_b = new_output_to_compare_text
            a_is_regular = True
        else:
            # New output gets position A, regular gets position B
            comparison_output_a = new_output_to_compare_text
            comparison_output_b = output_text
            a_is_regular = False
        llm_comparison = await judge.compare_outputs(
            dialogue_entries=dialogue_entries,
            date_of_meeting=note["date"],
            output_a=comparison_output_a,
            output_b=comparison_output_b,
        )

        # Map results back based on the randomization
        if llm_comparison.better_output == "A":
            mapped_better_output = "output" if a_is_regular else "new_output_to_compare"
        elif llm_comparison.better_output == "B":
            mapped_better_output = "new_output_to_compare" if a_is_regular else "output"
        else:  # "draw"
            mapped_better_output = "draw"

        comparison_data = {
            "better_output": mapped_better_output,
            "confidence": llm_comparison.confidence,
            "reasoning": llm_comparison.reasoning,
            "key_differences": llm_comparison.key_differences,
            "position_randomization": {
                "regular_output_position": "A" if a_is_regular else "B",
                "new_output_to_compare_position": "B" if a_is_regular else "A",
            },
        }
    except Exception as e:
        print(f"Error in LLM comparison: {e}")
        comparison_data = {
            "better_output": "error",
            "confidence": 0,
            "reasoning": f"Processing failed: {e}",
            "key_differences": [],
            "position_randomization": {
                "regular_output_position": "unknown",
                "new_output_to_compare_position": "unknown",
            },
        }

    # Add quality metrics to the note
    enhanced_note = note.copy()
    enhanced_note["quality_metrics"] = {
        "text_lengths": {
            "dialogue_entries_chars": dialogue_length,
            "output_chars": output_length,
            "new_output_to_compare_chars": new_output_to_compare_length,
        },
        "dialogue_to_output_ratios": {
            "dialogue_to_output_ratio": dialogue_to_output_ratio,
            "dialogue_to_new_output_ratio": dialogue_to_new_output_ratio,
        },
        "output_duplication_metrics": output_duplication,
        "new_output_duplication_metrics": new_output_duplication,
        "llm_comparison": comparison_data,
    }

    return enhanced_note


async def process_note_with_semaphore(
    semaphore: asyncio.Semaphore,
    note: dict[str, Any],
    analyzer: AdvancedDuplicationAnalyzer,
    judge: OutputQualityJudge,
    index: int,
    total: int,
) -> dict[str, Any]:
    """Process a single note with semaphore-controlled concurrency."""
    async with semaphore:
        try:
            enhanced_note = await analyze_probation_note_with_comparison(note, analyzer, judge)
            print(f"Processed note {index + 1}/{total}")
            return enhanced_note
        except Exception as e:
            print(f"Error processing note {index + 1}: {e}")
            # Add the original note with empty metrics in case of error
            error_note = note.copy()
            error_note["quality_metrics"] = {
                "error": str(e),
                "text_lengths": {
                    "dialogue_entries_chars": 0,
                    "output_chars": 0,
                    "new_output_to_compare_chars": 0,
                },
                "dialogue_to_output_ratios": {
                    "dialogue_to_output_ratio": 0,
                    "dialogue_to_new_output_ratio": 0,
                },
                "output_duplication_metrics": {},
                "new_output_duplication_metrics": {},
                "llm_comparison": {
                    "better_output": "error",
                    "confidence": 0,
                    "reasoning": f"Processing failed: {e}",
                    "key_differences": [],
                },
            }
            return error_note


async def main_async(max_concurrent: int = 20):
    # Get run description from user
    run_description = input("Enter a description for this evaluation run: ").strip()
    if not run_description:
        run_description = "no_description"

    # Clean the description for use in filename (replace spaces and special chars)
    clean_description = run_description.replace(" ", "_").replace("/", "-").replace("\\", "-")[:50]

    # Initialize the advanced analyzer and LLM judge
    analyzer = AdvancedDuplicationAnalyzer()
    judge = OutputQualityJudge()

    # Load the input JSON file
    input_file = (
        "evaluation/llm/.outputs/crissa_generated_outputs/20250526_232738_concurrent10_start200_limit50_prompt_33.json"
    )

    # Generate output filename based on input filename
    input_basename = os.path.basename(input_file)
    name_without_ext = input_basename.replace(".json", "")
    output_filename = f"{name_without_ext}_with_quality_metrics.json"
    output_file = f"evaluation/llm/.outputs/crissa_generated_outputs_with_advanced_quality_metrics/{output_filename}"

    try:
        with open(input_file, encoding="utf-8") as f:
            data = json.load(f)

        print(f"Processing {len(data)} probation notes with advanced duplication analysis and LLM comparison...")
        print(f"Using {max_concurrent} concurrent workers for parallelization")

        # Create semaphore to limit concurrent operations
        semaphore = asyncio.Semaphore(max_concurrent)

        # Create tasks for all notes
        tasks = [
            process_note_with_semaphore(semaphore, note, analyzer, judge, i, len(data)) for i, note in enumerate(data)
        ]

        # Process all notes concurrently with semaphore control
        enhanced_data = await asyncio.gather(*tasks)

        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        # Save the enhanced data
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(enhanced_data, f, indent=2, ensure_ascii=False)

        print(f"\nAnalysis complete! Enhanced data saved to: {output_file}")

        # Print comprehensive summary statistics including LLM comparisons
        print("\n=== COMPREHENSIVE SUMMARY STATISTICS WITH LLM COMPARISON ===")

        dialogue_lengths = []
        output_lengths = []
        new_output_lengths = []
        output_ratios = []
        new_output_ratios = []

        # Duplication metrics
        output_exact_duplications = []
        new_output_exact_duplications = []
        output_fuzzy_duplications = []
        new_output_fuzzy_duplications = []
        output_semantic_duplications = []
        new_output_semantic_duplications = []

        # LLM comparison results
        regular_output_wins = 0
        new_output_wins = 0
        draws = 0
        comparison_errors = 0
        confidence_scores = []

        for note in enhanced_data:
            if "error" not in note["quality_metrics"]:
                metrics = note["quality_metrics"]
                dialogue_lengths.append(metrics["text_lengths"]["dialogue_entries_chars"])
                output_lengths.append(metrics["text_lengths"]["output_chars"])
                new_output_lengths.append(metrics["text_lengths"]["new_output_to_compare_chars"])
                output_ratios.append(metrics["dialogue_to_output_ratios"]["dialogue_to_output_ratio"])
                new_output_ratios.append(metrics["dialogue_to_output_ratios"]["dialogue_to_new_output_ratio"])

                # Duplication metrics
                output_dup = metrics["output_duplication_metrics"]
                new_output_dup = metrics["new_output_duplication_metrics"]

                output_exact_duplications.append(output_dup.get("exact_sentence_duplication_ratio", 0))
                new_output_exact_duplications.append(new_output_dup.get("exact_sentence_duplication_ratio", 0))
                output_fuzzy_duplications.append(output_dup.get("fuzzy_sentence_duplication_ratio", 0))
                new_output_fuzzy_duplications.append(new_output_dup.get("fuzzy_sentence_duplication_ratio", 0))
                output_semantic_duplications.append(output_dup.get("semantic_sentence_duplication_ratio", 0))
                new_output_semantic_duplications.append(new_output_dup.get("semantic_sentence_duplication_ratio", 0))

                # LLM comparison results
                comparison = metrics["llm_comparison"]
                if comparison["better_output"] == "output":
                    regular_output_wins += 1
                elif comparison["better_output"] == "new_output_to_compare":
                    new_output_wins += 1
                elif comparison["better_output"] == "draw":
                    draws += 1
                else:
                    comparison_errors += 1

                if comparison["confidence"] > 0:
                    confidence_scores.append(comparison["confidence"])

        if dialogue_lengths:
            print(f"Average dialogue length: {sum(dialogue_lengths) / len(dialogue_lengths):.0f} characters")
            print(f"Average output length: {sum(output_lengths) / len(output_lengths):.0f} characters")
            print(f"Average new output length: {sum(new_output_lengths) / len(new_output_lengths):.0f} characters")
            print(f"Average dialogue-to-output ratio: {sum(output_ratios) / len(output_ratios):.3f}")
            print(f"Average dialogue-to-new-output ratio: {sum(new_output_ratios) / len(new_output_ratios):.3f}")

            print("\n--- DUPLICATION ANALYSIS ---")
            print("EXACT DUPLICATES:")
            print(f"  Output: {sum(output_exact_duplications) / len(output_exact_duplications):.4f}")
            print(f"  New output: {sum(new_output_exact_duplications) / len(new_output_exact_duplications):.4f}")

            print("FUZZY DUPLICATES (similar but not exact):")
            print(f"  Output: {sum(output_fuzzy_duplications) / len(output_fuzzy_duplications):.4f}")
            print(f"  New output: {sum(new_output_fuzzy_duplications) / len(new_output_fuzzy_duplications):.4f}")

            if analyzer.semantic_enabled:
                print("SEMANTIC DUPLICATES (similar meaning):")
                print(f"  Output: {sum(output_semantic_duplications) / len(output_semantic_duplications):.4f}")
                print(
                    f"  New output: {sum(new_output_semantic_duplications) / len(new_output_semantic_duplications):.4f}"
                )

            print("\n--- LLM COMPARISON RESULTS ---")
            total_valid_comparisons = regular_output_wins + new_output_wins + draws
            if total_valid_comparisons > 0:
                regular_percentage = (regular_output_wins / total_valid_comparisons) * 100
                new_output_percentage = (new_output_wins / total_valid_comparisons) * 100
                draw_percentage = (draws / total_valid_comparisons) * 100

                print(f"Regular output wins: {regular_output_wins} ({regular_percentage:.1f}%)")
                print(f"New output wins: {new_output_wins} ({new_output_percentage:.1f}%)")
                print(f"Draws: {draws} ({draw_percentage:.1f}%)")
                print(f"Comparison errors: {comparison_errors}")

                if confidence_scores:
                    avg_confidence = sum(confidence_scores) / len(confidence_scores)
                    print(f"Average confidence score: {avg_confidence:.1f}/10")

        # Show examples of LLM reasoning
        print("\n=== LLM COMPARISON EXAMPLES ===")
        for i, note in enumerate(enhanced_data[:3]):  # Show first 3 notes as examples
            if "error" not in note["quality_metrics"]:
                comparison = note["quality_metrics"]["llm_comparison"]
                print(f"\nNote {i + 1}:")
                print(f"  Winner: {comparison['better_output']}")
                print(f"  Confidence: {comparison['confidence']}/10")
                print(f"  Reasoning: {comparison['reasoning'][:200]}...")
                if comparison["key_differences"]:
                    print(f"  Key differences: {', '.join(comparison['key_differences'][:2])}")

        # Initialize wandb run
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_name = f"evaluation_run_{timestamp}_{clean_description}"

        run = wandb.init(
            project="crissa-evaluation",
            name=run_name,
            config={
                "max_concurrent": max_concurrent,
                "input_file": input_file,
                "semantic_similarity_enabled": analyzer.semantic_enabled,
                "judge_model": str(judge.judge_model),
                "fuzzy_similarity_threshold": 0.8,
                "semantic_similarity_threshold": 0.85,
            },
        )

        # Log summary metrics
        length_metrics = {
            "avg_dialogue_length": sum(dialogue_lengths) / len(dialogue_lengths),
            "avg_output_length": sum(output_lengths) / len(output_lengths),
            "avg_new_output_length": sum(new_output_lengths) / len(new_output_lengths),
            "avg_dialogue_to_output_ratio": sum(output_ratios) / len(output_ratios),
            "avg_dialogue_to_new_output_ratio": sum(new_output_ratios) / len(new_output_ratios),
            "total_notes_processed": len(dialogue_lengths),
        }

        # Duplication metrics for regular outputs
        output_duplication_metrics = {
            "output_avg_exact_duplication_ratio": sum(output_exact_duplications) / len(output_exact_duplications),
            "output_avg_fuzzy_duplication_ratio": sum(output_fuzzy_duplications) / len(output_fuzzy_duplications),
            "output_avg_semantic_duplication_ratio": (
                sum(output_semantic_duplications) / len(output_semantic_duplications)
                if analyzer.semantic_enabled
                else 0
            ),
        }

        # Duplication metrics for new outputs
        new_output_duplication_metrics = {
            "new_output_avg_exact_duplication_ratio": sum(new_output_exact_duplications)
            / len(new_output_exact_duplications),
            "new_output_avg_fuzzy_duplication_ratio": sum(new_output_fuzzy_duplications)
            / len(new_output_fuzzy_duplications),
            "new_output_avg_semantic_duplication_ratio": (
                sum(new_output_semantic_duplications) / len(new_output_semantic_duplications)
                if analyzer.semantic_enabled
                else 0
            ),
        }

        # LLM comparison metrics
        comparison_metrics = {
            "regular_output_wins": regular_output_wins,
            "new_output_wins": new_output_wins,
            "draws": draws,
            "comparison_errors": comparison_errors,
            "total_valid_comparisons": total_valid_comparisons,
        }

        if total_valid_comparisons > 0:
            comparison_metrics.update(
                {
                    "regular_win_percentage": (regular_output_wins / total_valid_comparisons) * 100,
                    "new_output_win_percentage": (new_output_wins / total_valid_comparisons) * 100,
                    "draw_percentage": (draws / total_valid_comparisons) * 100,
                }
            )

        if confidence_scores:
            comparison_metrics["avg_confidence_score"] = sum(confidence_scores) / len(confidence_scores)

        # Log all metrics to wandb
        wandb.log(
            {
                **length_metrics,
                **output_duplication_metrics,
                **new_output_duplication_metrics,
                **comparison_metrics,
            }
        )

        # Create and log detailed comparison table
        comparison_data = []
        for i, note in enumerate(enhanced_data[:50]):  # Log first 50 as examples
            if "error" not in note["quality_metrics"]:
                comparison = note["quality_metrics"]["llm_comparison"]
                text_lengths = note["quality_metrics"]["text_lengths"]
                comparison_data.append(
                    [
                        i,
                        comparison["better_output"],
                        comparison["confidence"],
                        text_lengths["dialogue_entries_chars"],
                        text_lengths["output_chars"],
                        text_lengths["new_output_to_compare_chars"],
                        comparison["reasoning"],
                        len(comparison["key_differences"]),
                        note["output"],
                        note["new_output_to_compare"],
                        note["input"]["dialogue_entries"],
                    ]
                )

        comparison_table = wandb.Table(
            columns=[
                "note_id",
                "better_output",
                "confidence",
                "dialogue_entries_chars",
                "output_chars",
                "new_output_to_compare_chars",
                "reasoning",
                "num_key_differences",
                "output",
                "new_output_to_compare",
                "dialogue_entries",
            ],
            data=comparison_data,
        )
        wandb.log({"detailed_comparison_results": comparison_table})

        run.finish()

    except FileNotFoundError:
        print(f"Error: Could not find input file: {input_file}")
        print("Please make sure the file path is correct.")
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in file: {input_file}")
    except Exception as e:
        print(f"Unexpected error: {e}")


def main():
    # Update the main function to use the async version
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
