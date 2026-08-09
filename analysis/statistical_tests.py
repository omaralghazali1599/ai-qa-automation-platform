"""
Statistical testing for RQ2.

Replaces the Kruskal-Wallis analysis with the repeated-measures design the
data actually has: the same 60 user stories are scored under all four prompt
strategies, so the measurements are paired and the Friedman test applies.

Implements both supervisor requirements:

  (1) Friedman test per model and per metric, reporting the test statistic,
      degrees of freedom, the exact p-value, Kendall's W as effect size, and
      Holm-corrected pairwise comparisons when the omnibus test is significant.

  (2) Because p > 0.05 does not establish equivalence: a sensitivity (power)
      analysis, TOST equivalence testing against a +/- 5 point margin,
      confidence intervals for the pairwise differences, and paired effect
      sizes.

Called from analyze_results.py in place of statistical_tests().
"""

import itertools

import numpy as np
import pandas as pd
from scipy import stats

ALPHA = 0.05
EQUIV_MARGIN = 5.0      # TOST margin in score points
TARGET_POWER = 0.80


# -------------------------------------------------------
# Helpers
# -------------------------------------------------------

def _pivot(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """Stories (rows) x strategies (columns) for one metric, complete cases."""
    wide = df.pivot_table(index="story_id", columns="strategy",
                          values=col, aggfunc="mean")
    return wide.dropna(axis=0, how="any")


def _holm(pvals):
    """Holm-Bonferroni step-down adjustment."""
    p = np.asarray(pvals, dtype=float)
    order = np.argsort(p)
    m = len(p)
    adj = np.empty(m)
    running = 0.0
    for rank, idx in enumerate(order):
        running = max(running, (m - rank) * p[idx])
        adj[idx] = min(running, 1.0)
    return adj


def _label(col: str) -> str:
    """Thesis-facing metric name."""
    names = {
        "format_compliance":   "Format Compliance",
        "redundancy":          "Redundancy",
        "functional_coverage": "User-Story Relevance",
        "edge_case_coverage":  "Edge Case Coverage",
        "baseline_comparison": "Baseline Comparison",
        "overall":             "Overall",
    }
    return names.get(col, col.replace("_", " ").title())


# -------------------------------------------------------
# (1) Friedman test + Kendall's W
# -------------------------------------------------------

def friedman_tests(df: pd.DataFrame, model_label: str, output_dir: str):
    print(f"\n=== FRIEDMAN TESTS [{model_label}] ===")
    print("H0: the four prompt strategies have equal median scores")
    print(f"Repeated measures: same stories under every strategy; alpha = {ALPHA}\n")

    rows = []
    for col in ["format_compliance", "redundancy", "functional_coverage",
                "edge_case_coverage", "baseline_comparison", "overall"]:
        if col not in df.columns:
            continue

        wide = _pivot(df, col)
        n, k = wide.shape
        if n < 2 or k < 3:
            continue

        # Metrics with no variance (e.g. Format Compliance at 100%) admit no test.
        if np.allclose(wide.values.std(axis=1), 0):
            rows.append({"Dimension": _label(col), "N": n, "k": k,
                         "chi2_F": np.nan, "df": k - 1, "p-value": np.nan,
                         "Kendalls_W": np.nan, "Significant": "N/A",
                         "Note": "no variance; test not computable"})
            print(f"{_label(col):22s} no variance -- test not computable")
            continue

        chi2, p = stats.friedmanchisquare(*[wide[c].values for c in wide.columns])
        W = chi2 / (n * (k - 1))
        significant = "YES ***" if p < ALPHA else "NO"

        rows.append({"Dimension": _label(col), "N": n, "k": k,
                     "chi2_F": round(chi2, 3), "df": k - 1,
                     "p-value": round(p, 4), "Kendalls_W": round(W, 4),
                     "Significant": significant, "Note": ""})
        print(f"{_label(col):22s} chi2_F={chi2:7.3f}  df={k-1}  "
              f"p={p:.4f}  W={W:.4f}  Significant: {significant}")

    out = pd.DataFrame(rows)
    fname = f"friedman_tests_{model_label.replace(' ', '_')}.csv"
    out.to_csv(f"{output_dir}/{fname}", index=False)
    print(f"\nSaved: {fname}")
    return out


def posthoc_tests(df: pd.DataFrame, model_label: str, output_dir: str,
                  friedman_df: pd.DataFrame):
    """Wilcoxon signed-rank pairwise tests, Holm-corrected.

    Executed only for metrics whose omnibus Friedman test is significant.
    """
    sig = friedman_df[friedman_df["Significant"].astype(str).str.startswith("YES")]
    if sig.empty:
        print(f"\n=== POST-HOC [{model_label}] ===")
        print("No omnibus test was significant; no pairwise comparisons required.")
        return pd.DataFrame()

    reverse = {"Format Compliance": "format_compliance",
               "Redundancy": "redundancy",
               "User-Story Relevance": "functional_coverage",
               "Edge Case Coverage": "edge_case_coverage",
               "Baseline Comparison": "baseline_comparison",
               "Overall": "overall"}

    rows = []
    print(f"\n=== POST-HOC [{model_label}] (Wilcoxon, Holm-corrected) ===")
    for _, r in sig.iterrows():
        wide = _pivot(df, reverse[r["Dimension"]])
        pairs, raw = [], []
        for a, b in itertools.combinations(wide.columns, 2):
            try:
                _, p = stats.wilcoxon(wide[a].values, wide[b].values)
            except ValueError:
                p = 1.0
            pairs.append((a, b))
            raw.append(p)
        for (a, b), p_raw, p_adj in zip(pairs, raw, _holm(raw)):
            rows.append({"Dimension": r["Dimension"],
                         "Comparison": f"{a} vs {b}",
                         "p_raw": round(p_raw, 4),
                         "p_holm": round(p_adj, 4),
                         "Significant": "YES" if p_adj < ALPHA else "NO"})
            print(f"  {r['Dimension']:22s} {a:18s} vs {b:18s} "
                  f"p_holm={p_adj:.4f}")

    out = pd.DataFrame(rows)
    fname = f"posthoc_tests_{model_label.replace(' ', '_')}.csv"
    out.to_csv(f"{output_dir}/{fname}", index=False)
    print(f"\nSaved: {fname}")
    return out


# -------------------------------------------------------
# (2) Equivalence testing, confidence intervals, effect sizes
# -------------------------------------------------------

def equivalence_tests(df: pd.DataFrame, model_label: str, output_dir: str,
                      margin: float = EQUIV_MARGIN):
    print(f"\n=== EQUIVALENCE / CI / EFFECT SIZE [{model_label}] "
          f"(TOST margin +/-{margin}) ===")

    rows = []
    for col in ["redundancy", "functional_coverage", "edge_case_coverage",
                "baseline_comparison", "overall"]:
        if col not in df.columns:
            continue
        wide = _pivot(df, col)
        n = len(wide)
        if n < 3:
            continue

        for a, b in itertools.combinations(wide.columns, 2):
            d = wide[a].values - wide[b].values
            mean_d, sd_d = d.mean(), d.std(ddof=1)

            if np.isclose(sd_d, 0):
                rows.append({"Dimension": _label(col),
                             "Comparison": f"{a} vs {b}", "N": n,
                             "Mean_Diff": round(mean_d, 3),
                             "CI_low": round(mean_d, 3),
                             "CI_high": round(mean_d, 3),
                             "Cohens_dz": np.nan, "TOST_p": np.nan,
                             "Equivalent": "N/A (no variance)"})
                continue

            se = sd_d / np.sqrt(n)
            tcrit = stats.t.ppf(0.975, n - 1)
            ci_low, ci_high = mean_d - tcrit * se, mean_d + tcrit * se
            dz = mean_d / sd_d

            # TOST: reject both one-sided nulls to conclude equivalence.
            p_lower = stats.t.sf((mean_d + margin) / se, n - 1)
            p_upper = stats.t.cdf((mean_d - margin) / se, n - 1)
            p_tost = max(p_lower, p_upper)

            rows.append({"Dimension": _label(col),
                         "Comparison": f"{a} vs {b}", "N": n,
                         "Mean_Diff": round(mean_d, 3),
                         "CI_low": round(ci_low, 3),
                         "CI_high": round(ci_high, 3),
                         "Cohens_dz": round(dz, 3),
                         "TOST_p": round(p_tost, 4),
                         "Equivalent": "YES" if p_tost < ALPHA else "NO"})

    out = pd.DataFrame(rows)
    fname = f"equivalence_tests_{model_label.replace(' ', '_')}.csv"
    out.to_csv(f"{output_dir}/{fname}", index=False)

    summary = out[out["Dimension"] == "Overall"]
    if not summary.empty:
        print(summary.to_string(index=False))
    eq = (out["Equivalent"] == "YES").sum()
    total = out["Equivalent"].isin(["YES", "NO"]).sum()
    print(f"\nEquivalent within +/-{margin} points: {eq} of {total} comparisons")
    print(f"Saved: {fname}")
    return out


def power_analysis(df: pd.DataFrame, model_label: str, output_dir: str,
                   target: float = TARGET_POWER):
    """Sensitivity analysis: the smallest effect this design could detect.

    Friedman: the statistic follows a noncentral chi-square with df = k-1 and
    noncentrality lambda = N(k-1)W under the alternative, so the minimum
    detectable Kendall's W follows directly. The paired-comparison equivalent
    is obtained from the noncentral t distribution.
    """
    print(f"\n=== POWER / SENSITIVITY [{model_label}] "
          f"(target power = {target}) ===")

    rows = []
    for col in ["redundancy", "functional_coverage", "edge_case_coverage",
                "baseline_comparison", "overall"]:
        if col not in df.columns:
            continue
        wide = _pivot(df, col)
        n, k = wide.shape
        if n < 3 or k < 3:
            continue

        dfree = k - 1
        crit = stats.chi2.ppf(1 - ALPHA, dfree)
        lo, hi = 0.0, 200.0
        for _ in range(200):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if stats.ncx2.sf(crit, dfree, mid) < target else (lo, mid)
        w_min = hi / (n * dfree)

        tcrit = stats.t.ppf(1 - ALPHA / 2, n - 1)
        lo, hi = 0.0, 5.0
        for _ in range(200):
            mid = (lo + hi) / 2
            nc = mid * np.sqrt(n)
            pw = stats.nct.sf(tcrit, n - 1, nc) + stats.nct.cdf(-tcrit, n - 1, nc)
            lo, hi = (mid, hi) if pw < target else (lo, mid)
        dz_min = hi

        sd = float(np.mean(np.std(wide.values, axis=0, ddof=1)))
        rows.append({"Dimension": _label(col), "N": n, "k": k,
                     "alpha": ALPHA, "Target_Power": target,
                     "Min_Detectable_W": round(w_min, 4),
                     "Min_Detectable_dz": round(dz_min, 4),
                     "Min_Detectable_Points": round(dz_min * sd, 3)})
        print(f"{_label(col):22s} min W={w_min:.4f}  min dz={dz_min:.4f}  "
              f"({dz_min * sd:.2f} points)")

    out = pd.DataFrame(rows)
    fname = f"power_analysis_{model_label.replace(' ', '_')}.csv"
    out.to_csv(f"{output_dir}/{fname}", index=False)
    print(f"\nSaved: {fname}")
    return out


# -------------------------------------------------------
# Entry point used by analyze_results.py
# -------------------------------------------------------

def statistical_tests(df: pd.DataFrame, model_label: str,
                      output_dir: str = "analysis/output"):
    """Run the full RQ2 statistical analysis for one model."""
    fried = friedman_tests(df, model_label, output_dir)
    posthoc_tests(df, model_label, output_dir, fried)
    equivalence_tests(df, model_label, output_dir)
    power_analysis(df, model_label, output_dir)
    return fried