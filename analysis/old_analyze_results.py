import os
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats
from scipy.stats import kruskal
import warnings
warnings.filterwarnings("ignore")

RESULTS_DIR = "evaluation/results"
OUTPUT_DIR  = "analysis/output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

DIMENSIONS = [
    "format_compliance",
    "redundancy",
    "functional_coverage",
    "edge_case_coverage",
]

STRATEGY_LABELS = {
    "zero_shot":        "Zero-Shot",
    "few_shot":         "Few-Shot",
    "chain_of_thought": "Chain-of-Thought",
    "role_cot":         "Role + CoT",
}

APP_LABELS = {
    "auth":    "Auth App",
    "task":    "Task App",
    "booking": "Booking API",
}

# -------------------------------------------------------
# LOAD ALL RESULTS
# -------------------------------------------------------

def load_results() -> pd.DataFrame:
    records = []
    for fname in os.listdir(RESULTS_DIR):
        if not fname.endswith(".json"):
            continue
        with open(os.path.join(RESULTS_DIR, fname),
                  "r", encoding="utf-8") as f:
            data = json.load(f)

        scores = data.get("scores", {})
        row = {
            "story_id": data.get("story_id"),
            "app":      data.get("app"),
            "strategy": data.get("strategy"),
            "overall":  scores.get("overall_score"),
        }
        for dim in DIMENSIONS:
            dim_data = scores.get(dim, {})
            row[dim] = dim_data.get("score") if isinstance(
                dim_data, dict) else None

        records.append(row)

    df = pd.DataFrame(records)
    df = df.dropna(subset=["overall"])
    return df


# -------------------------------------------------------
# TABLE 1 — Average scores per prompt strategy
# -------------------------------------------------------

def table_strategy_averages(df: pd.DataFrame) -> pd.DataFrame:
    cols = DIMENSIONS + ["overall"]
    agg = df.groupby("strategy")[cols].mean().round(2)
    agg.index = [STRATEGY_LABELS.get(s, s) for s in agg.index]
    agg.columns = [c.replace("_", " ").title() for c in agg.columns]
    agg = agg.sort_values("Overall", ascending=False)

    print("\n=== TABLE 1: Average scores per prompt strategy ===")
    print(agg.to_string())

    agg.to_csv(f"{OUTPUT_DIR}/table1_strategy_averages.csv")
    print(f"Saved: {OUTPUT_DIR}/table1_strategy_averages.csv")
    return agg


# -------------------------------------------------------
# TABLE 2 — Average scores per app category
# -------------------------------------------------------

def table_app_averages(df: pd.DataFrame) -> pd.DataFrame:
    cols = DIMENSIONS + ["overall"]
    agg = df.groupby("app")[cols].mean().round(2)
    agg.index = [APP_LABELS.get(a, a) for a in agg.index]
    agg.columns = [c.replace("_", " ").title() for c in agg.columns]
    agg = agg.sort_values("Overall", ascending=False)

    print("\n=== TABLE 2: Average scores per app category ===")
    print(agg.to_string())

    agg.to_csv(f"{OUTPUT_DIR}/table2_app_averages.csv")
    print(f"Saved: {OUTPUT_DIR}/table2_app_averages.csv")
    return agg


# -------------------------------------------------------
# TABLE 3 — Strategy × App cross-table (overall score)
# -------------------------------------------------------

def table_strategy_x_app(df: pd.DataFrame) -> pd.DataFrame:
    pivot = df.pivot_table(
        values="overall",
        index="strategy",
        columns="app",
        aggfunc="mean"
    ).round(2)

    pivot.index = [STRATEGY_LABELS.get(s, s) for s in pivot.index]
    pivot.columns = [APP_LABELS.get(a, a) for a in pivot.columns]

    print("\n=== TABLE 3: Overall score — Strategy × App ===")
    print(pivot.to_string())

    pivot.to_csv(f"{OUTPUT_DIR}/table3_strategy_x_app.csv")
    print(f"Saved: {OUTPUT_DIR}/table3_strategy_x_app.csv")
    return pivot


# -------------------------------------------------------
# STATISTICAL TEST — Kruskal-Wallis across strategies
# -------------------------------------------------------

def statistical_tests(df: pd.DataFrame):
    print("\n=== STATISTICAL TESTS (Kruskal-Wallis) ===")
    print("H0: No significant difference between prompt strategies")
    print("Significance level: p < 0.05\n")

    strategies = df["strategy"].unique()
    cols = DIMENSIONS + ["overall"]

    results = []
    for col in cols:
        groups = [
            df[df["strategy"] == s][col].dropna().values
            for s in strategies
        ]
        groups = [g for g in groups if len(g) > 0]

        if len(groups) < 2:
            continue

        h_stat, p_val = kruskal(*groups)
        significant = "YES ***" if p_val < 0.05 else "NO"

        results.append({
            "Dimension": col.replace("_", " ").title(),
            "H-statistic": round(h_stat, 3),
            "p-value": round(p_val, 4),
            "Significant": significant
        })

        print(f"{col:30s} H={h_stat:.3f}  p={p_val:.4f}  "
              f"Significant: {significant}")

    stats_df = pd.DataFrame(results)
    stats_df.to_csv(f"{OUTPUT_DIR}/statistical_tests.csv", index=False)
    print(f"\nSaved: {OUTPUT_DIR}/statistical_tests.csv")
    return stats_df


# -------------------------------------------------------
# CHART 1 — Bar chart: avg overall score per strategy
# -------------------------------------------------------

def chart_strategy_overall(df: pd.DataFrame):
    agg = df.groupby("strategy")["overall"].mean().reset_index()
    agg["strategy_label"] = agg["strategy"].map(STRATEGY_LABELS)
    agg = agg.sort_values("overall", ascending=False)

    fig = px.bar(
        agg,
        x="strategy_label",
        y="overall",
        color="strategy_label",
        color_discrete_sequence=["#185FA5", "#1D9E75", "#BA7517", "#D85A30"],
        labels={"strategy_label": "Prompt Strategy",
                "overall": "Average Overall Score (%)"},
        title="Average Overall Quality Score by Prompt Strategy",
        text=agg["overall"].round(1).astype(str) + "%"
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        showlegend=False,
        yaxis_range=[0, 110],
        plot_bgcolor="white",
        yaxis=dict(gridcolor="#eeeeee"),
        font=dict(family="Arial", size=13),
    )
    fig.write_image(f"{OUTPUT_DIR}/chart1_strategy_overall.png", scale=2)
    fig.write_html(f"{OUTPUT_DIR}/chart1_strategy_overall.html")
    print(f"Saved: chart1_strategy_overall.png")


# -------------------------------------------------------
# CHART 2 — Grouped bar: all dimensions per strategy
# -------------------------------------------------------

def chart_strategy_dimensions(df: pd.DataFrame):
    cols = DIMENSIONS + ["overall"]
    agg = df.groupby("strategy")[cols].mean().reset_index()

    melted = agg.melt(
        id_vars="strategy",
        value_vars=cols,
        var_name="dimension",
        value_name="score"
    )
    melted["strategy_label"] = melted["strategy"].map(STRATEGY_LABELS)
    melted["dimension_label"] = melted["dimension"].apply(
        lambda x: x.replace("_", " ").title()
    )

    fig = px.bar(
        melted,
        x="dimension_label",
        y="score",
        color="strategy_label",
        barmode="group",
        color_discrete_sequence=["#185FA5", "#1D9E75", "#BA7517", "#D85A30"],
        labels={"dimension_label": "Quality Dimension",
                "score": "Average Score (%)",
                "strategy_label": "Strategy"},
        title="Quality Scores by Dimension and Prompt Strategy",
    )
    fig.update_layout(
        yaxis_range=[0, 115],
        plot_bgcolor="white",
        yaxis=dict(gridcolor="#eeeeee"),
        font=dict(family="Arial", size=12),
        legend=dict(title="Prompt Strategy"),
    )
    fig.write_image(f"{OUTPUT_DIR}/chart2_strategy_dimensions.png", scale=2)
    fig.write_html(f"{OUTPUT_DIR}/chart2_strategy_dimensions.html")
    print(f"Saved: chart2_strategy_dimensions.png")


# -------------------------------------------------------
# CHART 3 — Box plots: score distribution per strategy
# -------------------------------------------------------

def chart_boxplots(df: pd.DataFrame):
    df_copy = df.copy()
    df_copy["strategy_label"] = df_copy["strategy"].map(STRATEGY_LABELS)

    fig = px.box(
        df_copy,
        x="strategy_label",
        y="overall",
        color="strategy_label",
        color_discrete_sequence=["#185FA5", "#1D9E75", "#BA7517", "#D85A30"],
        labels={"strategy_label": "Prompt Strategy",
                "overall": "Overall Score (%)"},
        title="Distribution of Overall Scores by Prompt Strategy",
        points="all"
    )
    fig.update_layout(
        showlegend=False,
        plot_bgcolor="white",
        yaxis=dict(gridcolor="#eeeeee"),
        font=dict(family="Arial", size=13),
    )
    fig.write_image(f"{OUTPUT_DIR}/chart3_boxplots.png", scale=2)
    fig.write_html(f"{OUTPUT_DIR}/chart3_boxplots.html")
    print(f"Saved: chart3_boxplots.png")


# -------------------------------------------------------
# CHART 4 — Radar chart: strategy profiles
# -------------------------------------------------------

def chart_radar(df: pd.DataFrame):
    cols = DIMENSIONS
    agg = df.groupby("strategy")[cols].mean()

    categories = [c.replace("_", " ").title() for c in cols]

    fig = go.Figure()
    colors = ["#185FA5", "#1D9E75", "#BA7517", "#D85A30"]

    for i, (strategy, row) in enumerate(agg.iterrows()):
        values = list(row.values) + [row.values[0]]
        cats   = categories + [categories[0]]
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=cats,
            fill="toself",
            name=STRATEGY_LABELS.get(strategy, strategy),
            line=dict(color=colors[i % len(colors)]),
            opacity=0.6
        ))

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        title="Quality Dimension Profiles by Prompt Strategy",
        font=dict(family="Arial", size=13),
        legend=dict(title="Strategy"),
    )
    fig.write_image(f"{OUTPUT_DIR}/chart4_radar.png", scale=2)
    fig.write_html(f"{OUTPUT_DIR}/chart4_radar.html")
    print(f"Saved: chart4_radar.png")


# -------------------------------------------------------
# CHART 5 — Overall score per app category
# -------------------------------------------------------

def chart_app_comparison(df: pd.DataFrame):
    df_copy = df.copy()
    df_copy["app_label"] = df_copy["app"].map(APP_LABELS)
    df_copy["strategy_label"] = df_copy["strategy"].map(STRATEGY_LABELS)

    fig = px.bar(
        df_copy.groupby(["app_label", "strategy_label"])["overall"]
               .mean().reset_index(),
        x="app_label",
        y="overall",
        color="strategy_label",
        barmode="group",
        color_discrete_sequence=["#185FA5", "#1D9E75", "#BA7517", "#D85A30"],
        labels={"app_label": "Application",
                "overall": "Average Overall Score (%)",
                "strategy_label": "Strategy"},
        title="Overall Quality Score by Application and Strategy",
    )
    fig.update_layout(
        yaxis_range=[0, 115],
        plot_bgcolor="white",
        yaxis=dict(gridcolor="#eeeeee"),
        font=dict(family="Arial", size=12),
    )
    fig.write_image(f"{OUTPUT_DIR}/chart5_app_comparison.png", scale=2)
    fig.write_html(f"{OUTPUT_DIR}/chart5_app_comparison.html")
    print(f"Saved: chart5_app_comparison.png")


# -------------------------------------------------------
# SUMMARY REPORT
# -------------------------------------------------------

def print_summary(df: pd.DataFrame):
    print("\n" + "="*60)
    print("FULL EXPERIMENT SUMMARY")
    print("="*60)
    print(f"Total results loaded:     {len(df)}")
    print(f"Unique stories:           {df['story_id'].nunique()}")
    print(f"Prompt strategies:        {df['strategy'].nunique()}")
    print(f"App categories:           {df['app'].nunique()}")
    print(f"\nOverall score range:      "
          f"{df['overall'].min():.1f}% — {df['overall'].max():.1f}%")
    print(f"Overall score mean:       {df['overall'].mean():.2f}%")
    print(f"Overall score std dev:    {df['overall'].std():.2f}%")

    best_strategy = df.groupby("strategy")["overall"].mean().idxmax()
    worst_strategy = df.groupby("strategy")["overall"].mean().idxmin()
    print(f"\nBest strategy:            "
          f"{STRATEGY_LABELS.get(best_strategy, best_strategy)}")
    print(f"Worst strategy:           "
          f"{STRATEGY_LABELS.get(worst_strategy, worst_strategy)}")

    best_app = df.groupby("app")["overall"].mean().idxmax()
    worst_app = df.groupby("app")["overall"].mean().idxmin()
    print(f"\nBest app category:        "
          f"{APP_LABELS.get(best_app, best_app)}")
    print(f"Hardest app category:     "
          f"{APP_LABELS.get(worst_app, worst_app)}")
    print("="*60)


# -------------------------------------------------------
# MAIN
# -------------------------------------------------------

if __name__ == "__main__":
    print("Loading results...")
    df = load_results()
    print(f"Loaded {len(df)} results from {RESULTS_DIR}/")

    print_summary(df)
    table_strategy_averages(df)
    table_app_averages(df)
    table_strategy_x_app(df)
    statistical_tests(df)

    print("\nGenerating charts...")
    chart_strategy_overall(df)
    chart_strategy_dimensions(df)
    chart_boxplots(df)
    chart_radar(df)
    chart_app_comparison(df)

    print("\nAll analysis complete.")
    print(f"Outputs saved to: {OUTPUT_DIR}/")