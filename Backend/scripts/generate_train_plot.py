from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "data" / "train.csv"
OUTPUT_DIR = BASE_DIR / "plots"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def create_train_distribution_plot():
    df = pd.read_csv(DATA_PATH)
    context_lengths = df["Context"].astype(str).str.split().str.len()
    response_lengths = df["Response"].astype(str).str.split().str.len()

    plt.style.use("seaborn-v0_8")
    fig, axes = plt.subplots(2, 1, figsize=(12, 10), tight_layout=True)

    axes[0].hist(context_lengths, bins=30, color="#2563eb", edgecolor="#ffffff", alpha=0.85)
    axes[0].set_title("Context Length Distribution")
    axes[0].set_xlabel("Word count")
    axes[0].set_ylabel("Examples")

    axes[1].hist(response_lengths, bins=30, color="#14b8a6", edgecolor="#ffffff", alpha=0.85)
    axes[1].set_title("Response Length Distribution")
    axes[1].set_xlabel("Word count")
    axes[1].set_ylabel("Examples")

    output_path = OUTPUT_DIR / "train_data_distribution.png"
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    print(f"Saved plot to {output_path}")


if __name__ == "__main__":
    create_train_distribution_plot()
