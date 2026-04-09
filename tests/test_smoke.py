import pytest
import allure
import json
from core.pipeline import generate_test_cases
from core.prompt_strategies import PromptStrategy
from evaluation.scorers import run_all_scorers


@allure.epic("Smoke Test")
@allure.title("Smoke test — single story, zero-shot only")
def test_smoke_single_story():
    story = (
        "As a new user, I want to register with my name, "
        "email, and password so that I can create an account."
    )

    with allure.step("Generate test cases"):
        generated = generate_test_cases(story, PromptStrategy.ZERO_SHOT)
        allure.attach(
            json.dumps(generated, indent=2),
            name="Generated suite",
            attachment_type=allure.attachment_type.JSON
        )

    with allure.step("Score generated suite"):
        scores = run_all_scorers(generated, story)
        allure.attach(
            json.dumps(scores, indent=2),
            name="Scores",
            attachment_type=allure.attachment_type.JSON
        )

    allure.dynamic.parameter("overall_score", scores["overall_score"])
    assert scores["overall_score"] >= 0