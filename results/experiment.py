import os
import subprocess
import re
import csv
import sys

def run_experiment(output_dir, base_command, rates):
    raw_dir = os.path.join(output_dir, "raw")
    os.makedirs(raw_dir, exist_ok=True)

    summary_data = []

    for rate in rates:
        print(f"Running experiment with rate={rate}...")
        command = f"{base_command} --poisson-rate {rate}"
        raw_file = os.path.join(raw_dir, f"{rate}.txt")
        
        with open(raw_file, "w") as f:
            try:
                # Run the command and capture the output
                output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
                f.write(output.decode())
                print(f"Saved raw output for rate {rate} in {raw_file}")
            except subprocess.CalledProcessError as e:
                print(f"Error running command for rate {rate}: {e}")
                f.write(e.output.decode())
        
        # Parse the result to extract metrics
        metrics = parse_metrics(raw_file)
        if metrics:
            summary_data.append({"rate": rate, **metrics})
    
    return summary_data

def parse_metrics(raw_file):
    """Parse required metrics from the raw output."""
    with open(raw_file, "r") as f:
        data = f.read()
    
    # Extract the required metrics using regex
    metrics = {}
    metrics["agg_throughput"] = extract_metric(r"agg_throughput:\s*([\d.]+)", data)
    metrics["avg_per_core_throughput"] = extract_metric(r"avg_per_core_throughput:\s*([\d.]+)", data)
    metrics["avg_latency"] = extract_metric(r"avg_latency:\s*([\d.]+)", data)
    metrics["p99_latency"] = extract_metric(r"p99_latency \(end_to_end\):\s*([\d.]+)", data)

    # Ensure all metrics were parsed successfully
    if all(value is not None for value in metrics.values()):
        return metrics
    else:
        print(f"Warning: Missing metrics in {raw_file}")
        return None

def extract_metric(pattern, data):
    """Helper function to extract a single metric using regex."""
    match = re.search(pattern, data)
    return float(match.group(1)) if match else None

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
    
    # Command template
    base_command = "../out-perf.masstree/benchmarks/dbtest --verbose --bench tpcc --num-threads 7 --scale-factor 1 --runtime 30 --numa-memory 4G"
    
    # Generate rate list
    rates = list(range(1000, 20001, 1000)) + list(range(22000, 40001, 2000))
    # rates = list(range(1000, 2001, 1000))
    
    # Run experiments
    summary_data = run_experiment(output_dir, base_command, rates)
    
    # Save summary
    if summary_data:
        save_summary(summary_data, output_dir)
    else:
        print("No valid results to save.")

if __name__ == "__main__":
    main()
