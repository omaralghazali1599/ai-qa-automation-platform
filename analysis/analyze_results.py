import os
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scipy.stats import kruskal
import warnings
warnings.filterwarnings("ignore")

RESULTS_DIR     = "evaluation/results"
MINI_RESULTS_DIR = "evaluation/results_gpt4o_mini"
OUTPUT_DIR      = "analysis/output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

DIMENSIONS = [
    "format_compliance",
    "redundancy",
    "functional_coverage",
    "edge_case_coverage",
    "baseline_comparison"
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
# LOAD RESULTS
# -------------------------------------------------------

def load_results(results_dir: str, model_label: str) -> pd.DataFrame:
    records = []
    if not os.path.exists(results_dir):
        print(f"Warning: {results_dir} not found, skipping.")
        return pd.DataFrame()

    for fname in os.listdir(results_dir):
        if not fname.endswith(".json"):
            continue
        with open(os.path.join(results_dir, fname),
                  "r", encoding="utf-8") as f:
            data = json.load(f)

        scores = data.get("scores", {})
        row = {
            "story_id": data.get("story_id"),
            "app":      data.get("app"),
            "strategy": data.get("strategy"),
            "model":    model_label,
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
# TABLE 1 — Strategy averages per model
# -------------------------------------------------------

def table_strategy_averages(df: pd.DataFrame, model_label: str):
    cols = DIMENSIONS + ["overall"]
    agg = df.groupby("strategy")[cols].mean().round(2)
    agg.index = [STRATEGY_LABELS.get(s, s) for s in agg.index]
    agg.columns = [c.replace("_", " ").title() for c in agg.columns]
    agg = agg.sort_values("Overall", ascending=False)

    print(f"\n=== TABLE 1 [{model_label}]: Strategy averages ===")
    print(agg.to_string())

    fname = f"table1_strategy_averages_{model_label.replace(' ', '_')}.csv"
    agg.to_csv(f"{OUTPUT_DIR}/{fname}")
    print(f"Saved: {fname}")
    return agg


# -------------------------------------------------------
# TABLE 2 — App averages per model
# -------------------------------------------------------

def table_app_averages(df: pd.DataFrame, model_label: str):
    cols = DIMENSIONS + ["overall"]
    agg = df.groupby("app")[cols].mean().round(2)
    agg.index = [APP_LABELS.get(a, a) for a in agg.index]
    agg.columns = [c.replace("_", " ").title() for c in agg.columns]
    agg = agg.sort_values("Overall", ascending=False)

    print(f"\n=== TABLE 2 [{model_label}]: App averages ===")
    print(agg.to_string())

    fname = f"table2_app_averages_{model_label.replace(' ', '_')}.csv"
    agg.to_csv(f"{OUTPUT_DIR}/{fname}")
    print(f"Saved: {fname}")
    return agg


# -------------------------------------------------------
# TABLE 3 — Model comparison side by side
# -------------------------------------------------------

def table_model_comparison(df_mini: pd.DataFrame, df_4o: pd.DataFrame):
    cols = DIMENSIONS + ["overall"]

    avg_mini = df_mini[cols].mean().round(2)
    avg_4o   = df_4o[cols].mean().round(2)
    diff     = (avg_4o - avg_mini).round(2)

    comparison = pd.DataFrame({
        "GPT-4o-mini": avg_mini,
        "GPT-4o":      avg_4o,
        "Difference":  diff
    })
    comparison.index = [
        c.replace("_", " ").title() for c in comparison.index
    ]

    print("\n=== TABLE 3: Model comparison (GPT-4o-mini vs GPT-4o) ===")
    print(comparison.to_string())

    comparison.to_csv(f"{OUTPUT_DIR}/table3_model_comparison.csv")
    print(f"Saved: table3_model_comparison.csv")
    return comparison


# -------------------------------------------------------
# TABLE 4 — Strategy x App per model
# -------------------------------------------------------

def table_strategy_x_app(df: pd.DataFrame, model_label: str):
    pivot = df.pivot_table(
        values="overall",
        index="strategy",
        columns="app",
        aggfunc="mean"
    ).round(2)

    pivot.index   = [STRATEGY_LABELS.get(s, s) for s in pivot.index]
    pivot.columns = [APP_LABELS.get(a, a) for a in pivot.columns]

    print(f"\n=== TABLE 4 [{model_label}]: Strategy × App ===")
    print(pivot.to_string())

    fname = f"table4_strategy_x_app_{model_label.replace(' ', '_')}.csv"
    pivot.to_csv(f"{OUTPUT_DIR}/{fname}")
    print(f"Saved: {fname}")
    return pivot


# -------------------------------------------------------
# STATISTICAL TESTS
# -------------------------------------------------------

def statistical_tests(df: pd.DataFrame, model_label: str):
    print(f"\n=== STATISTICAL TESTS [{model_label}] (Kruskal-Wallis) ===")
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

        try:
            h_stat, p_val = kruskal(*groups)
            significant = "YES ***" if p_val < 0.05 else "NO"
        except Exception:
            h_stat, p_val, significant = float("nan"), float("nan"), "N/A"

        results.append({
            "Dimension":   col.replace("_", " ").title(),
            "H-statistic": round(h_stat, 3),
            "p-value":     round(p_val, 4),
            "Significant": significant
        })
        print(f"{col:30s} H={h_stat:.3f}  p={p_val:.4f}  "
              f"Significant: {significant}")

    stats_df = pd.DataFrame(results)
    fname = f"statistical_tests_{model_label.replace(' ', '_')}.csv"
    stats_df.to_csv(f"{OUTPUT_DIR}/{fname}", index=False)
    print(f"\nSaved: {fname}")
    return stats_df


# -------------------------------------------------------
# CHART 1 — Overall score comparison: mini vs 4o
# -------------------------------------------------------

def chart_model_comparison_overall(
    df_mini: pd.DataFrame, df_4o: pd.DataFrame
):
    data = pd.DataFrame([
        {
            "Model": "GPT-4o-mini",
            "Strategy": STRATEGY_LABELS.get(s, s),
            "Overall": df_mini[df_mini["strategy"] == s]["overall"].mean()
        }
        for s in df_mini["strategy"].unique()
    ] + [
        {
            "Model": "GPT-4o",
            "Strategy": STRATEGY_LABELS.get(s, s),
            "Overall": df_4o[df_4o["strategy"] == s]["overall"].mean()
        }
        for s in df_4o["strategy"].unique()
    ])

    fig = px.bar(
        data,
        x="Strategy",
        y="Overall",
        color="Model",
        barmode="group",
        color_discrete_sequence=["#185FA5", "#D85A30"],
        labels={"Overall": "Average Overall Score (%)"},
        title="GPT-4o-mini vs GPT-4o — Overall Score by Strategy",
        text=data["Overall"].round(1).astype(str) + "%"
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        yaxis_range=[0, 115],
        plot_bgcolor="white",
        yaxis=dict(gridcolor="#eeeeee"),
        font=dict(family="Arial", size=13),
    )
    fig.write_image(
        f"{OUTPUT_DIR}/chart1_model_comparison_overall.png", scale=2
    )
    fig.write_html(
        f"{OUTPUT_DIR}/chart1_model_comparison_overall.html"
    )
    print("Saved: chart1_model_comparison_overall.png")


# -------------------------------------------------------
# CHART 2 — Dimension comparison: mini vs 4o
# -------------------------------------------------------

def chart_model_comparison_dimensions(
    df_mini: pd.DataFrame, df_4o: pd.DataFrame
):
    cols = DIMENSIONS + ["overall"]

    rows = []
    for col in cols:
        rows.append({
            "Dimension": col.replace("_", " ").title(),
            "Model": "GPT-4o-mini",
            "Score": round(df_mini[col].mean(), 2)
        })
        rows.append({
            "Dimension": col.replace("_", " ").title(),
            "Model": "GPT-4o",
            "Score": round(df_4o[col].mean(), 2)
        })

    data = pd.DataFrame(rows)

    fig = px.bar(
        data,
        x="Dimension",
        y="Score",
        color="Model",
        barmode="group",
        color_discrete_sequence=["#185FA5", "#D85A30"],
        labels={"Score": "Average Score (%)"},
        title="GPT-4o-mini vs GPT-4o — Score by Quality Dimension",
        text=data["Score"].astype(str) + "%"
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        yaxis_range=[0, 120],
        plot_bgcolor="white",
        yaxis=dict(gridcolor="#eeeeee"),
        font=dict(family="Arial", size=12),
    )
    fig.write_image(
        f"{OUTPUT_DIR}/chart2_model_comparison_dimensions.png", scale=2
    )
    fig.write_html(
        f"{OUTPUT_DIR}/chart2_model_comparison_dimensions.html"
    )
    print("Saved: chart2_model_comparison_dimensions.png")


# -------------------------------------------------------
# CHART 3 — Box plots per model
# -------------------------------------------------------

def chart_boxplots_both_models(
    df_mini: pd.DataFrame, df_4o: pd.DataFrame
):
    df_mini_copy = df_mini.copy()
    df_4o_copy   = df_4o.copy()
    df_mini_copy["model_label"] = "GPT-4o-mini"
    df_4o_copy["model_label"]   = "GPT-4o"
    df_mini_copy["strategy_label"] = df_mini_copy["strategy"].map(
        STRATEGY_LABELS
    )
    df_4o_copy["strategy_label"] = df_4o_copy["strategy"].map(
        STRATEGY_LABELS
    )

    combined = pd.concat([df_mini_copy, df_4o_copy])

    fig = px.box(
        combined,
        x="strategy_label",
        y="overall",
        color="model_label",
        color_discrete_sequence=["#185FA5", "#D85A30"],
        labels={
            "strategy_label": "Prompt Strategy",
            "overall":        "Overall Score (%)",
            "model_label":    "Model"
        },
        title="Score Distribution — GPT-4o-mini vs GPT-4o by Strategy",
        points="all"
    )
    fig.update_layout(
        plot_bgcolor="white",
        yaxis=dict(gridcolor="#eeeeee"),
        font=dict(family="Arial", size=12),
    )
    fig.write_image(
        f"{OUTPUT_DIR}/chart3_boxplots_both_models.png", scale=2
    )
    fig.write_html(
        f"{OUTPUT_DIR}/chart3_boxplots_both_models.html"
    )
    print("Saved: chart3_boxplots_both_models.png")


# -------------------------------------------------------
# CHART 4 — Radar per model
# -------------------------------------------------------

def chart_radar_both_models(
    df_mini: pd.DataFrame, df_4o: pd.DataFrame
):
    cols       = DIMENSIONS
    categories = [c.replace("_", " ").title() for c in cols]

    mini_vals = [round(df_mini[c].mean(), 2) for c in cols]
    fo_vals   = [round(df_4o[c].mean(), 2) for c in cols]

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=mini_vals + [mini_vals[0]],
        theta=categories + [categories[0]],
        fill="toself",
        name="GPT-4o-mini",
        line=dict(color="#185FA5"),
        opacity=0.6
    ))
    fig.add_trace(go.Scatterpolar(
        r=fo_vals + [fo_vals[0]],
        theta=categories + [categories[0]],
        fill="toself",
        name="GPT-4o",
        line=dict(color="#D85A30"),
        opacity=0.6
    ))

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        title="Quality Dimension Profiles — GPT-4o-mini vs GPT-4o",
        font=dict(family="Arial", size=13),
        legend=dict(title="Model"),
    )
    fig.write_image(
        f"{OUTPUT_DIR}/chart4_radar_both_models.png", scale=2
    )
    fig.write_html(
        f"{OUTPUT_DIR}/chart4_radar_both_models.html"
    )
    print("Saved: chart4_radar_both_models.png")


# -------------------------------------------------------
# CHART 5 — App comparison per model
# -------------------------------------------------------

def chart_app_comparison_both_models(
    df_mini: pd.DataFrame, df_4o: pd.DataFrame
):
    df_mini_copy = df_mini.copy()
    df_4o_copy   = df_4o.copy()
    df_mini_copy["model_label"] = "GPT-4o-mini"
    df_4o_copy["model_label"]   = "GPT-4o"
    df_mini_copy["app_label"] = df_mini_copy["app"].map(APP_LABELS)
    df_4o_copy["app_label"]   = df_4o_copy["app"].map(APP_LABELS)

    combined = pd.concat([df_mini_copy, df_4o_copy])
    agg = combined.groupby(
        ["app_label", "model_label"]
    )["overall"].mean().reset_index()

    fig = px.bar(
        agg,
        x="app_label",
        y="overall",
        color="model_label",
        barmode="group",
        color_discrete_sequence=["#185FA5", "#D85A30"],
        labels={
            "app_label":   "Application",
            "overall":     "Average Overall Score (%)",
            "model_label": "Model"
        },
        title="GPT-4o-mini vs GPT-4o — Score by Application",
        text=agg["overall"].round(1).astype(str) + "%"
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        yaxis_range=[0, 115],
        plot_bgcolor="white",
        yaxis=dict(gridcolor="#eeeeee"),
        font=dict(family="Arial", size=12),
    )
    fig.write_image(
        f"{OUTPUT_DIR}/chart5_app_comparison_both_models.png", scale=2
    )
    fig.write_html(
        f"{OUTPUT_DIR}/chart5_app_comparison_both_models.html"
    )
    print("Saved: chart5_app_comparison_both_models.png")


# -------------------------------------------------------
# SUMMARY
# -------------------------------------------------------

def print_summary(df: pd.DataFrame, model_label: str):
    print(f"\n{'='*60}")
    print(f"SUMMARY — {model_label}")
    print(f"{'='*60}")
    print(f"Total results:        {len(df)}")
    print(f"Unique stories:       {df['story_id'].nunique()}")
    print(f"Strategies:           {df['strategy'].nunique()}")
    print(f"App categories:       {df['app'].nunique()}")
    print(f"Score range:          "
          f"{df['overall'].min():.1f}% — {df['overall'].max():.1f}%")
    print(f"Mean overall score:   {df['overall'].mean():.2f}%")
    print(f"Std deviation:        {df['overall'].std():.2f}%")

    best = df.groupby("strategy")["overall"].mean().idxmax()
    worst = df.groupby("strategy")["overall"].mean().idxmin()
    print(f"Best strategy:        {STRATEGY_LABELS.get(best, best)}")
    print(f"Worst strategy:       {STRATEGY_LABELS.get(worst, worst)}")

    best_app = df.groupby("app")["overall"].mean().idxmax()
    worst_app = df.groupby("app")["overall"].mean().idxmin()
    print(f"Best app:             {APP_LABELS.get(best_app, best_app)}")
    print(f"Hardest app:          {APP_LABELS.get(worst_app, worst_app)}")
    print(f"{'='*60}")

# -------------------------------------------------------
# CHART 6 — Per-model individual charts
# -------------------------------------------------------

def chart_per_model(df: pd.DataFrame, model_label: str):
    safe_label = model_label.replace(" ", "_").replace("-", "_")

    # Bar chart — overall per strategy
    agg = df.groupby("strategy")["overall"].mean().reset_index()
    agg["strategy_label"] = agg["strategy"].map(STRATEGY_LABELS)
    agg = agg.sort_values("overall", ascending=False)

    fig = px.bar(
        agg,
        x="strategy_label",
        y="overall",
        color="strategy_label",
        color_discrete_sequence=["#185FA5","#1D9E75","#BA7517","#D85A30"],
        labels={"strategy_label": "Prompt Strategy",
                "overall": "Average Overall Score (%)"},
        title=f"[{model_label}] Average Overall Score by Strategy",
        text=agg["overall"].round(1).astype(str) + "%"
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        showlegend=False, yaxis_range=[0, 110],
        plot_bgcolor="white",
        yaxis=dict(gridcolor="#eeeeee"),
        font=dict(family="Arial", size=13)
    )
    fig.write_image(
        f"{OUTPUT_DIR}/chart_overall_{safe_label}.png", scale=2
    )
    fig.write_html(
        f"{OUTPUT_DIR}/chart_overall_{safe_label}.html"
    )
    print(f"Saved: chart_overall_{safe_label}.png")

    # Grouped bar — all dimensions per strategy
    cols = DIMENSIONS + ["overall"]
    agg2 = df.groupby("strategy")[cols].mean().reset_index()
    melted = agg2.melt(
        id_vars="strategy",
        value_vars=cols,
        var_name="dimension",
        value_name="score"
    )
    melted["strategy_label"] = melted["strategy"].map(STRATEGY_LABELS)
    melted["dimension_label"] = melted["dimension"].apply(
        lambda x: x.replace("_", " ").title()
    )

    fig2 = px.bar(
        melted,
        x="dimension_label",
        y="score",
        color="strategy_label",
        barmode="group",
        color_discrete_sequence=["#185FA5","#1D9E75","#BA7517","#D85A30"],
        labels={"dimension_label": "Quality Dimension",
                "score": "Average Score (%)",
                "strategy_label": "Strategy"},
        title=f"[{model_label}] Quality Scores by Dimension and Strategy"
    )
    fig2.update_layout(
        yaxis_range=[0, 115], plot_bgcolor="white",
        yaxis=dict(gridcolor="#eeeeee"),
        font=dict(family="Arial", size=12),
        legend=dict(title="Strategy")
    )
    fig2.write_image(
        f"{OUTPUT_DIR}/chart_dimensions_{safe_label}.png", scale=2
    )
    fig2.write_html(
        f"{OUTPUT_DIR}/chart_dimensions_{safe_label}.html"
    )
    print(f"Saved: chart_dimensions_{safe_label}.png")

    # Box plots
    df_copy = df.copy()
    df_copy["strategy_label"] = df_copy["strategy"].map(STRATEGY_LABELS)

    fig3 = px.box(
        df_copy,
        x="strategy_label",
        y="overall",
        color="strategy_label",
        color_discrete_sequence=["#185FA5","#1D9E75","#BA7517","#D85A30"],
        labels={"strategy_label": "Prompt Strategy",
                "overall": "Overall Score (%)"},
        title=f"[{model_label}] Score Distribution by Strategy",
        points="all"
    )
    fig3.update_layout(
        showlegend=False, plot_bgcolor="white",
        yaxis=dict(gridcolor="#eeeeee"),
        font=dict(family="Arial", size=13)
    )
    fig3.write_image(
        f"{OUTPUT_DIR}/chart_boxplot_{safe_label}.png", scale=2
    )
    fig3.write_html(
        f"{OUTPUT_DIR}/chart_boxplot_{safe_label}.html"
    )
    print(f"Saved: chart_boxplot_{safe_label}.png")

    # Radar
    cols_radar = DIMENSIONS
    categories = [c.replace("_", " ").title() for c in cols_radar]
    agg_radar = df.groupby("strategy")[cols_radar].mean()

    fig4 = go.Figure()
    colors = ["#185FA5","#1D9E75","#BA7517","#D85A30"]

    for i, (strategy, row) in enumerate(agg_radar.iterrows()):
        values = list(row.values) + [row.values[0]]
        cats   = categories + [categories[0]]
        fig4.add_trace(go.Scatterpolar(
            r=values, theta=cats,
            fill="toself",
            name=STRATEGY_LABELS.get(strategy, strategy),
            line=dict(color=colors[i % len(colors)]),
            opacity=0.6
        ))

    fig4.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        title=f"[{model_label}] Quality Dimension Profiles by Strategy",
        font=dict(family="Arial", size=13),
        legend=dict(title="Strategy")
    )
    fig4.write_image(
        f"{OUTPUT_DIR}/chart_radar_{safe_label}.png", scale=2
    )
    fig4.write_html(
        f"{OUTPUT_DIR}/chart_radar_{safe_label}.html"
    )
    print(f"Saved: chart_radar_{safe_label}.png")

    # App comparison
    df_copy2 = df.copy()
    df_copy2["app_label"]      = df_copy2["app"].map(APP_LABELS)
    df_copy2["strategy_label"] = df_copy2["strategy"].map(STRATEGY_LABELS)

    fig5 = px.bar(
        df_copy2.groupby(
            ["app_label", "strategy_label"]
        )["overall"].mean().reset_index(),
        x="app_label",
        y="overall",
        color="strategy_label",
        barmode="group",
        color_discrete_sequence=["#185FA5","#1D9E75","#BA7517","#D85A30"],
        labels={"app_label": "Application",
                "overall": "Average Overall Score (%)",
                "strategy_label": "Strategy"},
        title=f"[{model_label}] Overall Score by Application and Strategy"
    )
    fig5.update_layout(
        yaxis_range=[0, 115], plot_bgcolor="white",
        yaxis=dict(gridcolor="#eeeeee"),
        font=dict(family="Arial", size=12)
    )
    fig5.write_image(
        f"{OUTPUT_DIR}/chart_apps_{safe_label}.png", scale=2
    )
    fig5.write_html(
        f"{OUTPUT_DIR}/chart_apps_{safe_label}.html"
    )
    print(f"Saved: chart_apps_{safe_label}.png")
# -------------------------------------------------------
# MAIN
# -------------------------------------------------------

if __name__ == "__main__":
    print("Loading gpt-4o-mini results...")
    df_mini = load_results(MINI_RESULTS_DIR, "GPT-4o-mini")

    print("Loading gpt-4o results...")
    df_4o = load_results(RESULTS_DIR, "GPT-4o")

    if df_mini.empty and df_4o.empty:
        print("No results found. Run the experiments first.")
        exit(1)

    # --- Per-model analysis ---
    if not df_mini.empty:
        print_summary(df_mini, "GPT-4o-mini")
        table_strategy_averages(df_mini, "GPT-4o_mini")
        table_app_averages(df_mini, "GPT-4o_mini")
        table_strategy_x_app(df_mini, "GPT-4o_mini")
        statistical_tests(df_mini, "GPT-4o_mini")

    if not df_4o.empty:
        print_summary(df_4o, "GPT-4o")
        table_strategy_averages(df_4o, "GPT-4o")
        table_app_averages(df_4o, "GPT-4o")
        table_strategy_x_app(df_4o, "GPT-4o")
        statistical_tests(df_4o, "GPT-4o")
    
    # --- Per-model charts ---
    if not df_mini.empty:
        chart_per_model(df_mini, "GPT-4o-mini")
    if not df_4o.empty:
        chart_per_model(df_4o, "GPT-4o")
        
    # --- Model comparison ---
    if not df_mini.empty and not df_4o.empty:
        print("\n=== MODEL COMPARISON ===")
        table_model_comparison(df_mini, df_4o)

        print("\nGenerating comparison charts...")
        chart_model_comparison_overall(df_mini, df_4o)
        chart_model_comparison_dimensions(df_mini, df_4o)
        chart_boxplots_both_models(df_mini, df_4o)
        chart_radar_both_models(df_mini, df_4o)
        chart_app_comparison_both_models(df_mini, df_4o)

    print(f"\nAll analysis complete. Outputs saved to: {OUTPUT_DIR}/")