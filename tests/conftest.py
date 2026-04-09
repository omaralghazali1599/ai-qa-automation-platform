import pytest
import os
import json

STORIES_DIRS = {
    "auth":    "dataset/user_stories/auth_app",
    "task":    "dataset/user_stories/task_app",
    "booking": "dataset/user_stories/booking_api",
}

BASELINES_DIRS = {
    "auth":    "dataset/human_baselines/auth_app",
    "task":    "dataset/human_baselines/task_app",
    "booking": "dataset/human_baselines/booking_api",
}


def load_all_stories():
    """Returns list of (story_id, app, story_text, baseline_path) tuples."""
    stories = []
    for app, folder in STORIES_DIRS.items():
        if not os.path.exists(folder):
            continue
        for fname in sorted(os.listdir(folder)):
            if not fname.endswith(".txt"):
                continue
            story_id = fname.replace(".txt", "")
            story_path = os.path.join(folder, fname)
            with open(story_path, "r", encoding="utf-8") as f:
                story_text = f.read().strip()

            baseline_path = os.path.join(
                BASELINES_DIRS[app], f"{story_id}.json"
            )
            baseline_path = baseline_path if os.path.exists(baseline_path) else None
            stories.append((story_id, app, story_text, baseline_path))
    return stories


def load_baseline(baseline_path: str):
    if not baseline_path:
        return None
    with open(baseline_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def all_stories():
    return load_all_stories()