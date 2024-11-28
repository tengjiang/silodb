import os
import pandas as pd
import matplotlib.pyplot as plt
import sys

def plot_summary(directory):
    # Initialize the plot
    plt.figure()
    plt.title("Aggregate Throughput vs. p99 Latency")
    plt.xlabel("Aggregate Throughput (ops/sec)")
    plt.ylabel("p99 Latency (ms)")
    plt.grid(True)
    
    found_csv = False
    
    # Traverse subdirectories
    for subdir in os.listdir(directory):
        subpath = os.path.join(directory, subdir)
        if os.path.isdir(subpath):
            summary_path = os.path.join(subpath, "summary.csv")
            if os.path.exists(summary_path):
                found_csv = True
                print(f"Found summary.csv in {subdir}, adding to plot...")
                
                # Load the CSV data
                data = pd.read_csv(summary_path)
                
                # Ensure required columns exist
                if "agg_throughput" in data.columns and "p99_latency" in data.columns:
                    # Plot the data
                    plt.plot(
                        data["agg_throughput"],
                        data["p99_latency"],
                        label=subdir,
                        marker="o",
                        linestyle="-"
                    )
                else:
                    print(f"Warning: Missing required columns in {summary_path}")
    
    if not found_csv:
        print("No summary.csv files found in the subdirectories.")
        return
    
    # Add legend and save the plot
    plt.legend()
    plot_file = os.path.join(directory, "throughput_vs_latency.png")
    plt.savefig(plot_file)
    print(f"Plot saved to {plot_file}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 plot.py <directory>")
        sys.exit(1)
    
    directory = sys.argv[1]
    if not os.path.exists(directory):
        print(f"Directory {directory} does not exist.")
        sys.exit(1)
    
    plot_summary(directory)

if __name__ == "__main__":
    main()
