from enum import Enum

class PromptStrategy(str, Enum):
    ZERO_SHOT = "zero_shot"
    FEW_SHOT = "few_shot"
    CHAIN_OF_THOUGHT = "chain_of_thought"
    ROLE_COT = "role_cot"

FEW_SHOT_EXAMPLES = """
Example 1:
User Story: "As a user, I want to log in with email and password so I can access my account."
Output:
{
  "positive": [{"id": "TC-P01", "title": "Login with valid credentials", "steps": ["Navigate to login page", "Enter valid email", "Enter valid password", "Click Login"], "expected_result": "User is redirected to dashboard"}],
  "negative": [{"id": "TC-N01", "title": "Login with wrong password", "steps": ["Navigate to login page", "Enter valid email", "Enter incorrect password", "Click Login"], "expected_result": "Error message shown, user stays on login page"}],
  "edge": [{"id": "TC-E01", "title": "Login with email exceeding max length", "steps": ["Navigate to login page", "Enter email with 300+ characters", "Click Login"], "expected_result": "Validation error shown"}]
}

Example 2:
User Story: "As a user, I want to reset my password via email so I can regain account access."
Output:
{
  "positive": [{"id": "TC-P01", "title": "Request reset link with valid email", "steps": ["Go to forgot password page", "Enter registered email", "Click Send Reset Link"], "expected_result": "Confirmation message shown and email sent"}],
  "negative": [{"id": "TC-N01", "title": "Request reset with unregistered email", "steps": ["Go to forgot password page", "Enter unregistered email", "Click Send Reset Link"], "expected_result": "Error message: email not found"}],
  "edge": [{"id": "TC-E01", "title": "Request reset with empty email field", "steps": ["Go to forgot password page", "Leave email blank", "Click Send Reset Link"], "expected_result": "Validation error: email is required"}]
}
"""

JSON_SCHEMA = """
Return ONLY valid JSON in this exact structure:
{
  "positive": [{"id": "TC-P01", "title": "...", "steps": ["step1", "step2"], "expected_result": "..."}],
  "negative": [{"id": "TC-N01", "title": "...", "steps": [], "expected_result": "..."}],
  "edge":     [{"id": "TC-E01", "title": "...", "steps": [], "expected_result": "..."}]
}
"""

def get_system_prompt(strategy: PromptStrategy) -> str:
    if strategy == PromptStrategy.ROLE_COT:
        return (
            "You are a senior QA engineer with 10 years of experience in Agile software projects. "
            "You specialise in writing exhaustive, unambiguous test cases that catch real defects. "
            "You must return ONLY valid JSON."
        )
    return "You are a professional QA Engineer. You must return ONLY valid JSON."


def get_user_prompt(strategy: PromptStrategy, user_story: str) -> str:
    if strategy == PromptStrategy.ZERO_SHOT:
        return f"""
Generate comprehensive test cases (positive, negative, and edge) for this user story:
"{user_story}"
{JSON_SCHEMA}
"""

    if strategy == PromptStrategy.FEW_SHOT:
        return f"""
Here are two examples of well-written test cases:
{FEW_SHOT_EXAMPLES}

Now generate comprehensive test cases for this user story:
"{user_story}"
{JSON_SCHEMA}
"""

    if strategy in (PromptStrategy.CHAIN_OF_THOUGHT, PromptStrategy.ROLE_COT):
        return f"""
Think step by step:

Step 1 — List every acceptance criterion implied by this user story.
Step 2 — For each criterion, identify: one positive scenario, one negative scenario, and one edge scenario.
Step 3 — Write a complete test case for every scenario you identified.

User Story: "{user_story}"
{JSON_SCHEMA}
"""