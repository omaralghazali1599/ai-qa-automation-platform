import json
import os
from core.pipeline import generate_test_cases
from core.prompt_strategies import PromptStrategy
from evaluation.scorers import run_all_scorers
from evaluation.defect_detection import run_defect_detection

RESULTS_DIR = "evaluation/results"
os.makedirs(RESULTS_DIR, exist_ok=True)


def load_user_story(story_path: str) -> str:
    with open(story_path, "r", encoding="utf-8") as f:
        return f.read().strip()


def load_baseline(baseline_path: str) -> dict:
    if not os.path.exists(baseline_path):
        return None
    with open(baseline_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_result(result: dict, story_id: str, strategy: str):
    filename = f"{RESULTS_DIR}/{story_id}_{strategy}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"Saved: {filename}")


def run_single(
    story_id: str,
    story_path: str,
    strategy: PromptStrategy,
    baseline_path: str = None
) -> dict:
    user_story = load_user_story(story_path)
    baseline = load_baseline(baseline_path) if baseline_path else None

    print(f"Generating: {story_id} | strategy: {strategy.value}")
    generated = generate_test_cases(user_story, strategy)

    print(f"Scoring: {story_id} | strategy: {strategy.value}")
    scores = run_all_scorers(generated, user_story, baseline)

    result = {
        "story_id": story_id,
        "strategy": strategy.value,
        "user_story": user_story,
        "generated_suite": generated,
        "scores": scores
    }

    save_result(result, story_id, strategy.value)
    return result


def run_all(stories_dir: str, baselines_dir: str = None):
    """
    Run all user stories in a directory through all 4 strategies.
    """
    all_results = []

    story_files = sorted([
        f for f in os.listdir(stories_dir) if f.endswith(".txt")
    ])

    for story_file in story_files:
        story_id = story_file.replace(".txt", "")
        story_path = os.path.join(stories_dir, story_file)

        baseline_path = None
        if baselines_dir:
            candidate = os.path.join(baselines_dir, f"{story_id}.json")
            if os.path.exists(candidate):
                baseline_path = candidate

        for strategy in PromptStrategy:
            result = run_single(
                story_id, story_path, strategy, baseline_path
            )
            all_results.append(result)

    return all_results