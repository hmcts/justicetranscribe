# ruff: noqa

import json


def join_files(user_edit_json_path, crissa_json_path, output_file_path):
    """
    Join JSON files by trace_id, adding llm_diff_summary from user-edit data to Crissa observations.

    Args:
        user_edit_json_path: Path to the JSON file containing user-edit data
        crissa_json_path: Path to the JSON file containing Crissa observations array
        output_file_path: Path for the output JSON file
    """

    # Step 1: Read the user-edit JSON file and create a mapping from traceId to llm_diff_summary
    print("Reading user-edit JSON file...")
    trace_id_to_summary = {}

    try:
        with open(user_edit_json_path, encoding="utf-8") as f:
            user_edit_data = json.load(f)

        # Extract the mapping from the data array
        for item in user_edit_data.get("data", []):
            trace_id = item.get("traceId")
            llm_diff_summary = item.get("llm_diff_summary")

            if trace_id and llm_diff_summary:
                trace_id_to_summary[trace_id] = llm_diff_summary

        print(f"Found {len(trace_id_to_summary)} trace IDs with diff summaries")

    except FileNotFoundError:
        print(f"Error: User-edit JSON file not found at {user_edit_json_path}")
        return
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in user-edit file {user_edit_json_path}")
        return

    # Step 2: Read the Crissa observations JSON file
    print("Reading Crissa observations JSON file...")

    try:
        with open(crissa_json_path, encoding="utf-8") as f:
            crissa_data = json.load(f)

        if not isinstance(crissa_data, list):
            print("Error: Crissa JSON file should contain an array of observations")
            return

        print(f"Found {len(crissa_data)} Crissa observations")

    except FileNotFoundError:
        print(f"Error: Crissa JSON file not found at {crissa_json_path}")
        return
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in Crissa file {crissa_json_path}")
        return

    # Step 3: Process each observation and add llm_diff_summary where there's a match
    print("Processing observations...")

    matched_count = 0

    for observation in crissa_data:
        # Get the trace_id from the observation
        trace_id = observation.get("trace_id")

        if trace_id and trace_id in trace_id_to_summary:
            # Add the llm_diff_summary to the observation
            observation["llm_diff_summary"] = trace_id_to_summary[trace_id]
            matched_count += 1

    # Step 4: Write the updated data to output file
    try:
        with open(output_file_path, "w", encoding="utf-8") as f:
            json.dump(crissa_data, f, indent=2, ensure_ascii=False)

        print("Processing complete!")
        print(f"Total observations processed: {len(crissa_data)}")
        print(f"Observations with matched diff summaries: {matched_count}")
        print(f"Output written to: {output_file_path}")

    except Exception as e:
        print(f"Error writing output file: {e}")
        return


if __name__ == "__main__":
    # File paths
    user_edit_json = "evaluation/llm/.outputs/user-edit-raw-data.json"
    crissa_json = "evaluation/llm/.outputs/generate_full_crissa_observations_20250523_131601.json"
    output_file = "evaluation/llm/.outputs/generate_full_crissa_observations_with_diff_summary.json"

    # Run the join operation
    join_files(user_edit_json, crissa_json, output_file)
