"""
Pipe Detection with Data Analysis
==================================
Mock project demonstrating GPR (Ground Penetrating Radar) signal processing
for underground pipe detection using Python.

Pipeline:
    Read CSV → Trim Range → Extract Average Waveform → Noise Reduction
    → Peak Extraction → Histogram Analysis → Visualisation

Author  : Azrul
Purpose : Portfolio / mock demonstration of signal processing workflow
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy.signal import find_peaks

# ── Reproducibility ──────────────────────────────────────────────────────────
np.random.seed(42)

# ═════════════════════════════════════════════════════════════════════════════
# 1. GENERATE SYNTHETIC GPR DATA  (replaces real CSV in a live deployment)
# ═════════════════════════════════════════════════════════════════════════════

def generate_synthetic_gpr(n_traces: int = 200, n_samples: int = 512) -> pd.DataFrame:
    """
    Simulate a 2-D GPR B-scan containing:
      • Random background clutter (simulates soil reflections)
      • A hyperbolic reflection arch (simulates a buried pipe)

    In a real project this function is replaced by pd.read_csv().
    """
    time_ns   = np.linspace(0, 50, n_samples)   # two-way travel time [ns]
    traces    = np.arange(n_traces)              # horizontal scan position

    data = np.random.normal(0, 0.15, (n_samples, n_traces))

    # --- pipe hyperbola parameters ---
    pipe_depth_ns = 20       # apex at 20 ns
    pipe_center   = 100      # apex at trace 100
    velocity      = 0.1      # wave velocity [ns / trace²]

    for tr in traces:
        offset         = tr - pipe_center
        arrival_ns     = pipe_depth_ns + velocity * offset ** 2
        arrival_sample = int(np.interp(arrival_ns, time_ns,
                                       np.arange(n_samples)))
        # Gaussian pulse at the arrival sample
        pulse_width = 8
        for s in range(n_samples):
            data[s, tr] += 0.9 * np.exp(
                -((s - arrival_sample) ** 2) / (2 * pulse_width ** 2)
            )

    df = pd.DataFrame(data, index=time_ns, columns=traces)
    df.index.name   = "time_ns"
    df.columns.name = "trace"
    return df


# ═════════════════════════════════════════════════════════════════════════════
# 2. PROCESSING PIPELINE
# ═════════════════════════════════════════════════════════════════════════════

def load_data(filepath: str | None = None) -> pd.DataFrame:
    """Step 1 – Read CSV.  Falls back to synthetic data if no file is given."""
    if filepath:
        df = pd.read_csv(filepath, index_col=0)
        df.index   = df.index.astype(float)
        df.columns = df.columns.astype(int)
        print(f"[INFO] Loaded real data from {filepath}")
    else:
        df = generate_synthetic_gpr()
        print("[INFO] Using synthetic GPR data (demo mode)")
    return df


def trim_data(df: pd.DataFrame,
              t_start: float = 0,
              t_end: float   = 40) -> pd.DataFrame:
    """Step 2 – Trim to the time range of interest [ns]."""
    return df.loc[(df.index >= t_start) & (df.index <= t_end)]


def extract_average_waveform(df: pd.DataFrame) -> pd.Series:
    """Step 3 – Average across all traces to obtain background waveform."""
    return df.mean(axis=1)


def subtract_average(df: pd.DataFrame,
                     avg: pd.Series) -> pd.DataFrame:
    """Step 4 – Noise reduction: subtract background from every trace."""
    return df.subtract(avg, axis=0)


def extract_peaks(df_sub: pd.DataFrame,
                  height_threshold: float = 0.3) -> dict:
    """
    Step 5 – Peak extraction.
    Find the sample index of the strongest positive peak in each trace.
    Returns a dict {trace_index: peak_time_ns}.
    """
    time_ns    = df_sub.index.values
    peak_times = {}

    for col in df_sub.columns:
        trace  = df_sub[col].values
        peaks, props = find_peaks(trace, height=height_threshold, distance=10)
        if len(peaks) > 0:
            dominant = peaks[np.argmax(props["peak_heights"])]
            peak_times[col] = time_ns[dominant]

    return peak_times


# ═════════════════════════════════════════════════════════════════════════════
# 3. VISUALISATION  (5 subplots)
# ═════════════════════════════════════════════════════════════════════════════

def plot_results(df_raw:    pd.DataFrame,
                 df_trim:   pd.DataFrame,
                 avg:       pd.Series,
                 df_sub:    pd.DataFrame,
                 peak_dict: dict) -> None:

    fig = plt.figure(figsize=(16, 18))
    fig.suptitle("Pipe Detection with Data Analysis\n"
                 "GPR Signal Processing — Mock Portfolio Project",
                 fontsize=15, fontweight="bold", y=0.98)

    gs = gridspec.GridSpec(3, 2, figure=fig,
                           hspace=0.45, wspace=0.35)

    time   = df_trim.index.values
    traces = df_trim.columns.values

    # ── Plot 1 : Raw data 2-D heatmap ─────────────────────────────────────
    ax1 = fig.add_subplot(gs[0, 0])
    im1 = ax1.imshow(df_trim.values,
                     aspect="auto", cmap="seismic",
                     vmin=-1, vmax=1,
                     extent=[traces[0], traces[-1], time[-1], time[0]])
    fig.colorbar(im1, ax=ax1, label="Amplitude")
    ax1.set_title("Plot 1 — Raw GPR Data (B-scan)", fontweight="bold")
    ax1.set_xlabel("Trace number")
    ax1.set_ylabel("Two-way travel time [ns]")

    # ── Plot 2 : Average waveform ──────────────────────────────────────────
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.plot(avg.values, avg.index, color="#2E86AB", linewidth=1.8)
    ax2.axvline(0, color="gray", linewidth=0.8, linestyle="--")
    ax2.invert_yaxis()
    ax2.set_title("Plot 2 — Extracted Average Waveform", fontweight="bold")
    ax2.set_xlabel("Amplitude")
    ax2.set_ylabel("Two-way travel time [ns]")
    ax2.grid(True, alpha=0.3)

    # ── Plot 3 : Noise-reduced B-scan ─────────────────────────────────────
    ax3 = fig.add_subplot(gs[1, 0])
    im3 = ax3.imshow(df_sub.values,
                     aspect="auto", cmap="seismic",
                     vmin=-1, vmax=1,
                     extent=[traces[0], traces[-1], time[-1], time[0]])
    fig.colorbar(im3, ax=ax3, label="Amplitude")
    ax3.set_title("Plot 3 — After Background Removal\n"
                  "(Raw − Average Waveform)", fontweight="bold")
    ax3.set_xlabel("Trace number")
    ax3.set_ylabel("Two-way travel time [ns]")

    # ── Plot 4 : Peak extraction overlay ──────────────────────────────────
    ax4 = fig.add_subplot(gs[1, 1])
    im4 = ax4.imshow(df_sub.values,
                     aspect="auto", cmap="seismic",
                     vmin=-1, vmax=1,
                     extent=[traces[0], traces[-1], time[-1], time[0]])
    fig.colorbar(im4, ax=ax4, label="Amplitude")

    if peak_dict:
        pk_traces = list(peak_dict.keys())
        pk_times  = list(peak_dict.values())
        ax4.scatter(pk_traces, pk_times, color="yellow",
                    s=10, linewidths=0.3, label="Detected peaks",
                    zorder=5)
        ax4.legend(loc="lower right", fontsize=8)

    ax4.set_title("Plot 4 — Peak Extraction", fontweight="bold")
    ax4.set_xlabel("Trace number")
    ax4.set_ylabel("Two-way travel time [ns]")

    # ── Plot 5 : Histogram of peak depth distribution ─────────────────────
    ax5 = fig.add_subplot(gs[2, :])
    if peak_dict:
        peak_times_list = list(peak_dict.values())
        ax5.hist(peak_times_list, bins=40,
                 color="#A23B72", edgecolor="white",
                 linewidth=0.5, alpha=0.85)
        ax5.axvline(np.mean(peak_times_list),
                    color="#F18F01", linewidth=2,
                    linestyle="--", label=f"Mean ≈ {np.mean(peak_times_list):.1f} ns")
        ax5.legend(fontsize=10)
    ax5.set_title("Plot 5 — Histogram of Peak Depth Distribution\n"
                  "(Concentration indicates a detected object e.g. buried pipe)",
                  fontweight="bold")
    ax5.set_xlabel("Two-way travel time [ns]  →  depth")
    ax5.set_ylabel("Count")
    ax5.grid(True, alpha=0.3, axis="y")

    plt.savefig("gpr_pipe_detection_results.png",
                dpi=150, bbox_inches="tight")
    print("[INFO] Plot saved → gpr_pipe_detection_results.png")
    plt.show()


# ═════════════════════════════════════════════════════════════════════════════
# 4. MAIN
# ═════════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("  GPR Pipe Detection — Signal Processing Pipeline")
    print("=" * 60)

    # Step 1 – Load (pass a filepath string to load a real CSV)
    df_raw = load_data(filepath=None)

    # Step 2 – Trim to region of interest
    df_trim = trim_data(df_raw, t_start=0, t_end=40)
    print(f"[INFO] Data trimmed → shape {df_trim.shape}  "
          f"(samples × traces)")

    # Step 3 – Average waveform
    avg = extract_average_waveform(df_trim)
    print(f"[INFO] Average waveform extracted  ({len(avg)} samples)")

    # Step 4 – Background subtraction
    df_sub = subtract_average(df_trim, avg)
    print("[INFO] Background removed via average subtraction")

    # Step 5 – Peak extraction
    peaks = extract_peaks(df_sub, height_threshold=0.3)
    print(f"[INFO] Peaks detected in {len(peaks)} / {df_sub.shape[1]} traces")

    # Step 6 – Plot all results
    plot_results(df_raw, df_trim, avg, df_sub, peaks)

    print("\n[DONE] Pipeline complete.")


if __name__ == "__main__":
    main()
