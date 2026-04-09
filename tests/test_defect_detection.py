import pytest
import allure
import json
from evaluation.defect_detection import run_defect_detection, DEFECTS


@allure.epic("LLM Test Case Generation Evaluation")
@allure.feature("Defect Detection")
@allure.story("All apps")
@allure.title("Defect detection rate across all 3 test applications")
def test_defect_detection_all_apps():
    with allure.step("Run defect detection against all 3 apps"):
        results = run_defect_detection()
        allure.attach(
            json.dumps(results, indent=2),
            name="Defect detection results",
            attachment_type=allure.attachment_type.JSON
        )

    with allure.step("Log detection rate per app"):
        for app in ["auth", "task", "booking"]:
            app_results = [
                r for r in results["results"] if r["app"] == app
            ]
            caught = sum(1 for r in app_results if r["detected"])
            total = len(app_results)
            rate = round((caught / total) * 100, 2) if total > 0 else 0
            allure.dynamic.parameter(f"{app}_detection_rate", rate)

    allure.dynamic.parameter("overall_detection_rate", results["score"])
    allure.attach(
        f"Overall detection rate: {results['score']}%\n"
        f"Caught: {results['caught']}/{results['total_defects']}",
        name="Detection summary",
        attachment_type=allure.attachment_type.TEXT
    )

    assert results["score"] >= 0, "Defect detection scorer failed"


@pytest.mark.parametrize(
    "app", ["auth", "task", "booking"],
    ids=["auth_app", "task_app", "booking_api"]
)
@allure.epic("LLM Test Case Generation Evaluation")
@allure.feature("Defect Detection")
def test_defect_detection_per_app(app):
    allure.dynamic.story(app)
    allure.dynamic.title(f"Defect detection — {app} app")

    with allure.step(f"Run defect detection for {app} app"):
        results = run_defect_detection(app_filter=app)
        allure.attach(
            json.dumps(results, indent=2),
            name=f"{app} defect results",
            attachment_type=allure.attachment_type.JSON
        )

    allure.dynamic.parameter("detection_rate", results["score"])
    allure.dynamic.parameter("caught", results["caught"])
    allure.dynamic.parameter("missed", results["missed"])

    for r in results["results"]:
        status = "CAUGHT" if r["detected"] else "MISSED"
        allure.attach(
            f"{status}: {r['description']}",
            name=r["defect_id"],
            attachment_type=allure.attachment_type.TEXT
        )

    assert results["score"] >= 0