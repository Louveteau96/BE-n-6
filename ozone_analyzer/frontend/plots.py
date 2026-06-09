"""Matplotlib renderers for the live plots.

Both renderers use the 'timestamp' column when present so the x-axis shows
real wall-clock time. They fall back to the dataframe index for empty/legacy
frames.
"""

import matplotlib.dates as mdates


def _x_axis(df):
    return df["timestamp"] if "timestamp" in df.columns else df.index


def _format_time_axis(ax, df):
    if "timestamp" in df.columns and not df.empty:
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
        ax.figure.autofmt_xdate()


def create_single_plot(ax, df, config):
    ax.clear()
    col = config["col"]
    if not df.empty and col in df.columns:
        x = _x_axis(df)
        ax.plot(x, df[col], color=config["color"], linewidth=2, marker="o", markersize=4)
        ax.fill_between(x, df[col], alpha=0.2, color=config["color"])
        ax.set_ylabel(config["ylabel"])
        _format_time_axis(ax, df)
    else:
        ax.text(0.5, 0.5, "En attente de données...",
                ha="center", va="center", fontsize=14)

    ax.set_title(config["title"], fontsize=14, fontweight="bold")
    ax.grid(True, alpha=0.7)


def create_dual_plot(ax, df, config):
    ax.clear()
    if not df.empty:
        x = _x_axis(df)
        for i, col in enumerate(config["cols"]):
            if col in df.columns:
                ax.plot(x, df[col], color=config["colors"][i],
                        linewidth=2, marker="o", label=col, alpha=0.9)
                #ax.fill_between(x, df[col], alpha=0.15, color=config["colors"][i])
        ax.legend(loc="upper left", bbox_to_anchor=(1, 1), borderaxespad=0)
        _format_time_axis(ax, df)
    else:
        ax.text(0.5, 0.5, "En attente de données...",
                ha="center", va="center", fontsize=14)

    ax.set_title(config["title"], fontsize=14, fontweight="bold")
    ax.grid(True, alpha=0.7)
