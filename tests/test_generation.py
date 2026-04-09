import pytest
import allure
import json
from core.pipeline import generate_test_cases
from core.prompt_strategies import PromptStrategy
from evaluation.scorers import run_all_scorers
from tests.conftest import load_baseline

# All 4 prompt strategies
STRATEGIES = [
    PromptStrategy.ZERO_SHOT,
    PromptStrategy.FEW_SHOT,
    PromptStrategy.CHAIN_OF_THOUGHT,
    PromptStrategy.ROLE_COT,
]

# Load stories at module level for parametrize
import os, json as _json

def _get_stories():
    stories = []
    dirs = {
        "auth":    "dataset/user_stories/auth_app",
        "task":    "dataset/user_stories/task_app",
        "booking": "dataset/user_stories/booking_api",
    }
    baselines = {
        "auth":    "dataset/human_baselines/auth_app",
        "task":    "dataset/human_baselines/task_app",
        "booking": "dataset/human_baselines/booking_api",
    }
    for app, folder in dirs.items():
        if not os.path.exists(folder):
            continue
        for fname in sorted(os.listdir(folder)):
            if not fname.endswith(".txt"):
                continue
            story_id = fname.replace(".txt", "")
            with open(os.path.join(folder, fname), "r", encoding="utf-8") as f:
                story_text = f.read().strip()
            bp = os.path.join(baselines[app], f"{story_id}.json")
            baseline_path = bp if os.path.exists(bp) else None
            stories.append((story_id, app, story_text, baseline_path))
    return stories


ALL_STORIES = _get_stories()

# Build parametrize list: one entry per (story, strategy) combination
PARAMS = [
    (story_id, app, story_text, baseline_path, strategy)
    for (story_id, app, story_text, baseline_path) in ALL_STORIES
    for strategy in STRATEGIES
]


@pytest.mark.parametrize(
    "story_id, app, story_text, baseline_path, strategy",
    PARAMS,
    ids=[f"{p[0]}__{p[4].value}" for p in PARAMS]
)
@allure.epic("LLM Test Case Generation Evaluation")
@allure.feature("Prompt Strategy Comparison")
def test_generation_quality(
    story_id, app, story_text, baseline_path, strategy
):
    # --- Allure metadata ---
    allure.dynamic.story(app)
    allure.dynamic.title(f"{story_id} — {strategy.value}")
    allure.dynamic.parameter("story_id", story_id)
    allure.dynamic.parameter("app", app)
    allure.dynamic.parameter("strategy", strategy.value)

    # --- Step 1: Generate test cases ---
    with allure.step(f"Generate test cases using {strategy.value}"):
        generated = generate_test_cases(story_text, strategy)
        allure.attach(
            json.dumps(generated, indent=2),
            name="Generated test suite",
            attachment_type=allure.attachment_type.JSON
        )

    # --- Step 2: Load baseline if available ---
    baseline = load_baseline(baseline_path)
    if baseline:
        with allure.step("Load human baseline"):
            allure.attach(
                json.dumps(baseline, indent=2),
                name="Human baseline",
                attachment_type=allure.attachment_type.JSON
            )

    # --- Step 3: Run all scorers ---
    with allure.step("Run evaluation scorers"):
        scores = run_all_scorers(generated, story_text, baseline)
        allure.attach(
            json.dumps(scores, indent=2),
            name="Evaluation scores",
            attachment_type=allure.attachment_type.JSON
        )

    # --- Step 4: Log individual scores as Allure parameters ---
    with allure.step("Log quality dimension scores"):
        for dimension, result in scores.items():
            if dimension == "overall_score":
                allure.dynamic.parameter("overall_score", result)
            elif isinstance(result, dict) and result.get("score") is not None:
                allure.dynamic.parameter(dimension, result["score"])

    # --- Step 5: Save result to disk ---
    with allure.step("Save result to evaluation/results"):
        import os
        os.makedirs("evaluation/results", exist_ok=True)
        result_path = f"evaluation/results/{story_id}__{strategy.value}.json"
        with open(result_path, "w", encoding="utf-8") as f:
            json.dump({
                "story_id": story_id,
                "app": app,
                "strategy": strategy.value,
                "user_story": story_text,
                "generated_suite": generated,
                "scores": scores
            }, f, indent=2, ensure_ascii=False)

    # --- Assertion: overall score must be above minimum threshold ---
    assert scores["overall_score"] >= 0, \
        f"Overall score is negative — scorer error for {story_id}"
    assert scores["format_compliance"]["score"] is not None, \
        f"Format compliance scorer failed for {story_id}"