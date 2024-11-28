import os
import subprocess
import re
import csv
import sys
import pandas as pd

def run_experiment(output_dir, base_command, rates, num_runs=5):
    raw_dir = os.path.join(output_dir, "raw")
    os.makedirs(raw_dir, exist_ok=True)

    summary_data = []

    for rate in rates:
        print(f"Running experiment with rate={rate} for {num_runs} runs...")
        run_results = []

        for run_id in range(1, num_runs + 1):
            run_file = os.path.join(raw_dir, f"{rate}_run_{run_id}.txt")
            command = f"{base_command} --poisson-rate {rate}"

            with open(run_file, "w") as f:
                try:
                    # Run the command and capture the output
                    output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
                    f.write(output.decode())
                    print(f"Saved raw output for rate {rate}, run {run_id} in {run_file}")
                except subprocess.CalledProcessError as e:
                    print(f"Error running command for rate {rate}, run {run_id}: {e}")
                    f.write(e.output.decode())

            # Parse metrics from the raw file
            metrics = parse_metrics(run_file)
            if metrics:
                run_results.append(metrics)

        # Average metrics after excluding max/min p99_latency
        if run_results:
            avg_metrics = average_metrics(run_results)
            summary_data.append({"rate": rate, **avg_metrics})

    return summary_data

def parse_metrics(raw_file):
    """Parse required metrics from the raw output."""
    with open(raw_file, "r") as f:
        data = f.read()

    metrics = {
        "agg_throughput": extract_metric(r"agg_throughput:\s*([\d.]+)", data),
        "avg_per_core_throughput": extract_metric(r"avg_per_core_throughput:\s*([\d.]+)", data),
        "avg_latency": extract_metric(r"avg_latency:\s*([\d.]+)", data),
        "p99_latency": extract_metric(r"p99_latency \(end_to_end\):\s*([\d.]+)", data),
    }

    # Ensure all metrics are present
    if all(value is not None for value in metrics.values()):
        return metrics
    else:
        print(f"Warning: Missing metrics in {raw_file}")
        return None

def extract_metric(pattern, data):
    """Helper function to extract a single metric using regex."""
    match = re.search(pattern, data)
    return float(match.group(1)) if match else None

def average_metrics(run_results):
    """Average metrics after excluding the runs with the highest and lowest p99_latency."""
    df = pd.DataFrame(run_results)
    df = df.sort_values(by="p99_latency")

    if len(df) > 2:
        df = df.iloc[1:-1]  # Exclude the smallest and largest p99_latency

    # Calculate averages for the remaining runs
    return df.mean().to_dict()

def save_summary(summary_data, output_dir):
    """Save the parsed metrics to a CSV file."""
    summary_file = os.path.join(output_dir, "summary.csv")
    with open(summary_file, "w", newline="") as csvfile:
        fieldnames = ["rate", "agg_throughput", "avg_per_core_throughput", "avg_latency", "p99_latency"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(summary_data)

    print(f"Summary saved to {summary_file}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 experiment.py <output_dir>")
        sys.exit(1)

    output_dir = sys.argv[1]
    base_command = "../out-perf.masstree/benchmarks/dbtest --verbose --bench tpcc --num-threads 7 --scale-factor 1 --runtime 30 --numa-memory 4G"
    rates = list(range(1000, 20001, 1000)) + list(range(22000, 30001, 2000))
    # rates = list(range(1000,2001, 1000))

    summary_data = run_experiment(output_dir, base_command, rates, num_runs=5)

    if summary_data:
        save_summary(summary_data, output_dir)
    else:
        print("No valid results to save.")

if __name__ == "__main__":
    main()
