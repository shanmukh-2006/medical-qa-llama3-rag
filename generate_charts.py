"""generate_charts.py — Generates publication-ready figures using matplotlib from results."""
import os
import csv
import json
import matplotlib.pyplot as plt
import numpy as np

# Create output directory
os.makedirs("results/figures", exist_ok=True)

# -------------------------------------------------------------
# Chart 1: Accuracy Bar Chart
# -------------------------------------------------------------
csv_path = "results/results_table.csv"
configs = []
accuracies = []

with open(csv_path, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        configs.append(row["configuration"])
        accuracies.append(float(row["accuracy"]))

# Set style
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 11,
    "axes.edgecolor": "#333333",
    "axes.linewidth": 1.0
})

fig, ax = plt.subplots(figsize=(7, 5), facecolor="white")
ax.set_facecolor("white")

colors = ["#4C72B0", "#DD8452", "#55A868"]
bars = ax.bar(configs, accuracies, color=colors, width=0.5, edgecolor="#222222", linewidth=1.0)

ax.set_ylim(0, 100)
ax.set_ylabel("Accuracy (%)", fontsize=12, labelpad=8)
ax.set_title("Accuracy on 300 MedQA test questions", fontsize=14, fontweight="bold", pad=12)
ax.grid(axis="y", linestyle="--", alpha=0.5, color="#cccccc")
ax.set_axisbelow(True)

# Add value labels
for bar in bars:
    height = bar.get_height()
    ax.annotate(f"{height:.2f}%",
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 5),
                textcoords="offset points",
                ha="center", va="bottom",
                fontsize=11, fontweight="bold")

plt.tight_layout()
png1_path = "results/figures/accuracy_bar_chart.png"
pdf1_path = "results/figures/accuracy_bar_chart.pdf"
fig.savefig(png1_path, dpi=300, bbox_inches="tight")
fig.savefig(pdf1_path, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {png1_path} and {pdf1_path}")

# -------------------------------------------------------------
# Chart 2: Stacked Bar Chart for Error Buckets
# -------------------------------------------------------------
with open("results/error_analysis.json", "r", encoding="utf-8") as f:
    err_v1 = json.load(f)["bucket_counts"]

with open("results/error_analysis_v2.json", "r", encoding="utf-8") as f:
    err_v2 = json.load(f)["bucket_counts"]

models = ["RAG v1", "RAG v2"]
categories = ["Parse failure", "Retrieval miss", "Model ignored context"]

counts_parse = [err_v1["Parse failure"], err_v2["Parse failure"]]
counts_retrieval = [err_v1["Retrieval miss"], err_v2["Retrieval miss"]]
counts_ignored = [err_v1["Model ignored context"], err_v2["Model ignored context"]]

fig, ax = plt.subplots(figsize=(7, 5), facecolor="white")
ax.set_facecolor("white")

width = 0.45
c_parse = "#D95F02"      # rust / orange
c_retrieval = "#7570B3"  # purple
c_ignored = "#1B9E77"    # teal / green

b1 = ax.bar(models, counts_parse, width=width, label="Parse failure", color=c_parse, edgecolor="#222222", linewidth=1.0)
b2 = ax.bar(models, counts_retrieval, width=width, bottom=counts_parse, label="Retrieval miss", color=c_retrieval, edgecolor="#222222", linewidth=1.0)

bottom_ignored = [counts_parse[i] + counts_retrieval[i] for i in range(len(models))]
b3 = ax.bar(models, counts_ignored, width=width, bottom=bottom_ignored, label="Model ignored context", color=c_ignored, edgecolor="#222222", linewidth=1.0)

ax.set_ylabel("Error Count", fontsize=12, labelpad=8)
ax.set_title("Error Breakdown by Category (Counts)", fontsize=14, fontweight="bold", pad=12)
ax.grid(axis="y", linestyle="--", alpha=0.5, color="#cccccc")
ax.set_axisbelow(True)

# Add data count labels inside the bar sections
for i in range(len(models)):
    # Parse failure label
    if counts_parse[i] > 0:
        ax.text(i, counts_parse[i] / 2, str(counts_parse[i]), ha="center", va="center", color="white", fontweight="bold", fontsize=10)
    # Retrieval miss label
    if counts_retrieval[i] > 0:
        y_pos = counts_parse[i] + counts_retrieval[i] / 2
        ax.text(i, y_pos, str(counts_retrieval[i]), ha="center", va="center", color="white", fontweight="bold", fontsize=10)
    # Model ignored context label
    if counts_ignored[i] > 0:
        y_pos = bottom_ignored[i] + counts_ignored[i] / 2
        ax.text(i, y_pos, str(counts_ignored[i]), ha="center", va="center", color="white", fontweight="bold", fontsize=10)
    
    # Total error count on top
    total_err = bottom_ignored[i] + counts_ignored[i]
    ax.annotate(f"Total: {total_err}",
                xy=(i, total_err),
                xytext=(0, 5),
                textcoords="offset points",
                ha="center", va="bottom",
                fontsize=11, fontweight="bold")

# Expand y-lim slightly for total labels
max_total = max(bottom_ignored[i] + counts_ignored[i] for i in range(len(models)))
ax.set_ylim(0, max_total * 1.15)

ax.legend(frameon=True, facecolor="white", edgecolor="#cccccc", fontsize=10, loc="upper right")

plt.tight_layout()
png2_path = "results/figures/error_buckets_stacked_bar.png"
pdf2_path = "results/figures/error_buckets_stacked_bar.pdf"
fig.savefig(png2_path, dpi=300, bbox_inches="tight")
fig.savefig(pdf2_path, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {png2_path} and {pdf2_path}")
