"""
Analysis script for table "Evaluation of database (DB) ingestion throughput and API response times across
different file volume stages" in the CellRex paper.
"""

# %%
import json

import pandas as pd

# %%
# load your JSON data
with open(
    "./performance_results/performance_results_20250604_155958360224.json",
    "r",
    encoding="utf-8",
) as file:
    raw_json_data = json.load(file)


# %%
def extract_stage_metrics(json_data):
    """Extract stage-level metrics into a pandas DataFrame"""
    stage_data = []

    for result in json_data["results"]:
        stage_data.append(
            {
                "stage": result["stage"],
                "timestamp": pd.to_datetime(result["timestamp"]),
                "files_in_stage": result["files_in_stage"],
                "files_processed_in_stage": result["files_processed_in_stage"],
                "processing_time_seconds": result["processing_time_seconds"],
                "processing_files_per_second": result["processing_files_per_second"],
                "success_rate": result["success_rate"],
                "success_boolean": result["success_rate"] == 1.0,
                "stage_total_time": result["additional_metrics"]["stage_total_time"],
                "cumulative_total_files": result["cumulative_metrics"]["total_files"],
                "overall_files_per_second": result["cumulative_metrics"][
                    "overall_files_per_second"
                ],
            }
        )

    return pd.DataFrame(stage_data)


def extract_api_response_metrics(json_data):
    """Extract API response times into a pandas DataFrame"""
    api_data = []

    for result in json_data["results"]:
        for api_call in result["additional_metrics"]["api_response_times"]:
            api_data.append(
                {
                    "stage": api_call["stage"],
                    "timestamp": pd.to_datetime(api_call["timestamp"]),
                    "operation_type": api_call["operation_type"],
                    "endpoint": api_call["endpoint"],
                    "response_time_seconds": api_call["response_time_seconds"],
                    "response_length": api_call["response_length"],
                    "success": api_call["success"],
                    "error": api_call["error"],
                }
            )

    return pd.DataFrame(api_data)


# %%
# create DataFrames
stage_df = extract_stage_metrics(raw_json_data)
api_df = extract_api_response_metrics(raw_json_data)

# %%
# analysis
print("=== STAGE PERFORMANCE ANALYSIS ===")
print(
    stage_df[
        [
            "stage",
            "files_in_stage",
            "processing_time_seconds",
            "processing_files_per_second",
            "success_boolean",
        ]
    ]
    .round(2)
    .to_string()
)

# print("\n=== API RESPONSE TIME ANALYSIS ===")
# print(
#     api_df[
#         ["stage", "endpoint", "response_time_seconds", "response_length", "success"]
#     ].to_string()
# )

# endpoint performance summary
print("\n=== ENDPOINT PERFORMANCE SUMMARY ===")
api_df_aggregated = api_df.copy()
api_df_aggregated["endpoint_aggregated"] = api_df_aggregated["endpoint"].apply(
    lambda x: "biofiles/id/*" if "/id/" in x else x
)

endpoint_stats = (
    api_df_aggregated.groupby("endpoint_aggregated")["response_time_seconds"]
    .agg(["count", "mean", "min", "max", "std"])
    .round(3)
)
print(endpoint_stats)

endpoint_stats_extended = (
    api_df_aggregated[["stage", "endpoint_aggregated", "response_time_seconds"]]
    .pivot(index="stage", columns=["endpoint_aggregated"])
    .sort_index(key=lambda x: x.str.split("_").str[1].astype(int))
    .round(3)
)
print("\n=== ENDPOINT PERFORMANCE EXTENDED ===")
print(endpoint_stats_extended)


# %%
# export functionality
def export_to_csv(stage_df, api_df, prefix="performance_test"):
    """Export DataFrames to CSV files"""
    stage_filename = f"{prefix}_stage_metrics.csv"
    api_filename = f"{prefix}_api_metrics.csv"

    stage_df.to_csv(stage_filename, index=False)
    api_df.to_csv(api_filename, index=False)

    print(f"Exported stage metrics to: {stage_filename}")
    print(f"Exported API metrics to: {api_filename}")


# uncomment to export
# export_to_csv(stage_df, api_df)
