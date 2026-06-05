import json
from typing import List, Dict
from pydantic import ValidationError
from core.schemas import TestSuite

# -------------------------------------------------------
# SCORER 1 — Format Compliance
# -------------------------------------------------------
# Checks that every test case has all required fields
# filled correctly. Uses Pydantic — fully automated.
# Score = % of test cases that pass schema validation.
# -------------------------------------------------------

def score_format_compliance(test_suite: dict) -> dict:
    total = 0
    passed = 0
    failures = []

    for category in ["positive", "negative", "edge"]:
        for tc in test_suite.get(category, []):
            total += 1
            issues = []

            if not tc.get("id", "").strip():
                issues.append("missing id")
            if not tc.get("title", "").strip():
                issues.append("missing title")
            if not tc.get("steps") or len(tc.get("steps", [])) == 0:
                issues.append("empty steps")
            if not tc.get("expected_result", "").strip():
                issues.append("missing expected_result")

            if issues:
                failures.append({"id": tc.get("id", "?"), "issues": issues})
            else:
                passed += 1

    score = round((passed / total) * 100, 2) if total > 0 else 0.0
    return {
        "scorer": "format_compliance",
        "score": score,
        "total_cases": total,
        "passed": passed,
        "failed": total - passed,
        "failures": failures
    }


# -------------------------------------------------------
# SCORER 2 — Redundancy
# -------------------------------------------------------
# Detects near-duplicate test cases using cosine
# similarity on sentence embeddings.
# Score = % of unique (non-redundant) test cases.
# Threshold: pairs with similarity > 0.85 are redundant.
# -------------------------------------------------------

def score_redundancy(test_suite: dict) -> dict:
    try:
        from sentence_transformers import SentenceTransformer
        from sklearn.metrics.pairwise import cosine_similarity
        import numpy as np
    except ImportError:
        return {"scorer": "redundancy", "score": None,
                "error": "sentence-transformers not installed"}

    all_cases = []
    for category in ["positive", "negative", "edge"]:
        for tc in test_suite.get(category, []):
            text = f"{tc.get('title', '')} {' '.join(tc.get('steps', []))}"
            all_cases.append({"id": tc.get("id"), "text": text})

    if len(all_cases) < 2:
        return {"scorer": "redundancy", "score": 100.0,
                "total_cases": len(all_cases), "redundant_pairs": []}

    model = SentenceTransformer("all-MiniLM-L6-v2")
    texts = [c["text"] for c in all_cases]
    embeddings = model.encode(texts)
    sim_matrix = cosine_similarity(embeddings)

    redundant_pairs = []
    threshold = 0.85

    for i in range(len(all_cases)):
        for j in range(i + 1, len(all_cases)):
            sim = float(sim_matrix[i][j])
            if sim > threshold:
                redundant_pairs.append({
                    "case_a": all_cases[i]["id"],
                    "case_b": all_cases[j]["id"],
                    "similarity": round(sim, 3)
                })

    redundant_ids = set()
    for pair in redundant_pairs:
        redundant_ids.add(pair["case_b"])

    unique = len(all_cases) - len(redundant_ids)
    score = round((unique / len(all_cases)) * 100, 2)

    return {
        "scorer": "redundancy",
        "score": score,
        "total_cases": len(all_cases),
        "unique_cases": unique,
        "redundant_pairs": redundant_pairs
    }


# -------------------------------------------------------
# SCORER 3 — Functional Coverage
# -------------------------------------------------------
# Measures how well the generated test cases cover
# the acceptance criteria implied by the user story.
# Uses semantic similarity between story + each test case.
# Score = % of test cases semantically relevant to story.
# -------------------------------------------------------

def score_functional_coverage(test_suite: dict, user_story: str) -> dict:
    try:
        from sentence_transformers import SentenceTransformer
        from sklearn.metrics.pairwise import cosine_similarity
    except ImportError:
        return {"scorer": "functional_coverage", "score": None,
                "error": "sentence-transformers not installed"}

    all_cases = []
    for category in ["positive", "negative", "edge"]:
        for tc in test_suite.get(category, []):
            text = f"{tc.get('title', '')} {tc.get('expected_result', '')}"
            all_cases.append({"id": tc.get("id"), "text": text,
                               "category": category})

    if not all_cases:
        return {"scorer": "functional_coverage", "score": 0.0,
                "total_cases": 0}

    model = SentenceTransformer("all-MiniLM-L6-v2")
    story_embedding = model.encode([user_story])
    case_texts = [c["text"] for c in all_cases]
    case_embeddings = model.encode(case_texts)

    similarities = cosine_similarity(story_embedding, case_embeddings)[0]
    threshold = 0.30
    covered = []
    not_covered = []

    for i, case in enumerate(all_cases):
        sim = float(similarities[i])
        case["similarity"] = round(sim, 3)
        if sim >= threshold:
            covered.append(case)
        else:
            not_covered.append(case)

    score = round((len(covered) / len(all_cases)) * 100, 2)

    return {
        "scorer": "functional_coverage",
        "score": score,
        "total_cases": len(all_cases),
        "covered": len(covered),
        "not_covered": len(not_covered),
        "low_relevance_cases": [
            {"id": c["id"], "similarity": c["similarity"]}
            for c in not_covered
        ]
    }


# -------------------------------------------------------
# SCORER 4 — Edge Case Coverage
# -------------------------------------------------------
# Checks whether edge case test cases cover the 6
# standard edge categories using keyword matching.
# Score = % of edge categories covered.
# -------------------------------------------------------

EDGE_CATEGORIES = {
    "empty_input":      ["empty", "blank", "missing", "no input", "required"],
    "max_length":       ["max", "maximum", "long", "exceed", "limit", "200", "300"],
    "special_chars":    ["special", "symbol", "character", "@", "#", "script", "sql"],
    "boundary_value":   ["boundary", "minimum", "maximum", "zero", "negative", "0 "],
    "invalid_format":   ["invalid", "format", "wrong", "incorrect", "bad"],
    "duplicate_action": ["duplicate", "twice", "again", "already", "existing", "reuse"]
}

def score_edge_case_coverage(test_suite: dict) -> dict:
    edge_cases = test_suite.get("edge", [])

    if not edge_cases:
        return {
            "scorer": "edge_case_coverage",
            "score": 0.0,
            "covered_categories": [],
            "missing_categories": list(EDGE_CATEGORIES.keys())
        }

    edge_text = " ".join([
        f"{tc.get('title', '')} {tc.get('expected_result', '')} "
        f"{' '.join(tc.get('steps', []))}"
        for tc in edge_cases
    ]).lower()

    covered = []
    missing = []

    for category, keywords in EDGE_CATEGORIES.items():
        if any(kw in edge_text for kw in keywords):
            covered.append(category)
        else:
            missing.append(category)

    score = round((len(covered) / len(EDGE_CATEGORIES)) * 100, 2)

    return {
        "scorer": "edge_case_coverage",
        "score": score,
        "total_edge_cases": len(edge_cases),
        "covered_categories": covered,
        "missing_categories": missing
    }


# -------------------------------------------------------
# SCORER 5 — Baseline Comparison
# -------------------------------------------------------
# Compares LLM-generated test suite against human
# baseline using semantic similarity.
# Score = avg similarity between LLM cases and their
# closest human baseline counterpart.
# -------------------------------------------------------

def score_baseline_comparison(
    generated_suite: dict,
    baseline_suite: dict
) -> dict:
    try:
        from sentence_transformers import SentenceTransformer
        from sklearn.metrics.pairwise import cosine_similarity
        import numpy as np
    except ImportError:
        return {"scorer": "baseline_comparison", "score": None,
                "error": "sentence-transformers not installed"}

    def extract_texts(suite):
        texts = []
        for category in ["positive", "negative", "edge"]:
            for tc in suite.get(category, []):
                text = (f"{tc.get('title', '')} "
                        f"{' '.join(tc.get('steps', []))} "
                        f"{tc.get('expected_result', '')}")
                texts.append(text)
        return texts

    gen_texts = extract_texts(generated_suite)
    base_texts = extract_texts(baseline_suite)

    if not gen_texts or not base_texts:
        return {"scorer": "baseline_comparison", "score": 0.0}

    model = SentenceTransformer("all-MiniLM-L6-v2")
    gen_embeddings = model.encode(gen_texts)
    base_embeddings = model.encode(base_texts)

    sim_matrix = cosine_similarity(gen_embeddings, base_embeddings)
    base_coverage = sim_matrix.max(axis=0)  # recall: for each baseline case, best generated match
    score = round(float(base_coverage.mean()) * 100, 2)

    return {
        "scorer": "baseline_comparison",
        "score": score,
        "generated_cases": len(gen_texts),
        "baseline_cases": len(base_texts),
        "avg_baseline_coverage": round(float(base_coverage.mean()), 3),
        "min_baseline_coverage": round(float(base_coverage.min()), 3),
        "max_baseline_coverage": round(float(base_coverage.max()), 3)
    }


# -------------------------------------------------------
# MASTER SCORER — runs all scorers and returns combined
# -------------------------------------------------------

def run_all_scorers(
    test_suite: dict,
    user_story: str,
    baseline_suite: dict = None
) -> dict:
    results = {
        "format_compliance":    score_format_compliance(test_suite),
        "redundancy":           score_redundancy(test_suite),
        "functional_coverage":  score_functional_coverage(test_suite, user_story),
        "edge_case_coverage":   score_edge_case_coverage(test_suite),
    }

    if baseline_suite:
        results["baseline_comparison"] = score_baseline_comparison(
            test_suite, baseline_suite
        )

    scores = [v["score"] for v in results.values()
              if v.get("score") is not None]
    results["overall_score"] = round(sum(scores) / len(scores), 2) if scores else 0.0

    return results