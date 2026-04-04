# import json
# import os
# from core.script_generator import generate_selenium_script, save_script

# # -------------------------------
# # Load Test Cases JSON
# # -------------------------------

# def load_test_cases(file_path):
#     with open(file_path, "r", encoding="utf-8") as f:
#         return json.load(f)

# # -------------------------------
# # Create Output Folder
# # -------------------------------

# def create_output_folder(json_file):
#     base_name = os.path.splitext(json_file)[0]
#     folder = f"{base_name}_generated_tests"

#     if not os.path.exists(folder):
#         os.makedirs(folder)

#     return folder

# # -------------------------------
# # Generate Scripts
# # -------------------------------

# def generate_all_scripts(json_file):
#     data = load_test_cases(json_file)
#     output_folder = create_output_folder(json_file)

#     total = 0

#     for category in ["positive", "negative", "edge"]:
#         test_cases = data.get(category, [])

#         for tc in test_cases:
#             try:
#                 print(f"🔄 Generating {tc['id']} ({category})...")

#                 test_case_text = f"""
#                 Title: {tc.get('title')}

#                 Steps:
#                 {chr(10).join(tc.get('steps', []))}

#                 Expected Result:
#                 {tc.get('expected_result')}
#                 """

#                 script = generate_selenium_script(test_case_text)

#                 filename = f"{tc['id']}_{category}.py"
#                 filepath = os.path.join(output_folder, filename)

#                 save_script(script, filepath)

#                 total += 1

#             except Exception as e:
#                 print(f"❌ Error in {tc.get('id', 'UNKNOWN')}: {e}")

#     print(f"\n✅ Done! Generated {total} test scripts in '{output_folder}' folder.")

# # -------------------------------
# # Run Pipeline
# # -------------------------------

# if __name__ == "__main__":
#     json_file = "As_a_user,_I_want_to_add_and_remove_objects_from_m.json"  # from your first project
#     generate_all_scripts(json_file)



import json
import os
from core.schemas import TestSuite
from core.script_generator import generate_selenium_script, save_script
from core.prompt_strategies import PromptStrategy, get_system_prompt, get_user_prompt
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def generate_test_cases(user_story: str, strategy: PromptStrategy = PromptStrategy.ZERO_SHOT) -> dict:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": get_system_prompt(strategy)},
            {"role": "user",   "content": get_user_prompt(strategy, user_story)},
        ],
        response_format={"type": "json_object"}
    )
    raw = json.loads(response.choices[0].message.content)
    validated = TestSuite(**raw)
    return validated.model_dump()


def load_test_cases(file_path: str) -> dict:
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def create_output_folder(json_file: str) -> str:
    base_name = os.path.splitext(json_file)[0]
    folder = f"{base_name}_generated_tests"
    os.makedirs(folder, exist_ok=True)
    return folder


def generate_all_scripts(json_file: str):
    data = load_test_cases(json_file)
    output_folder = create_output_folder(json_file)
    total = 0

    for category in ["positive", "negative", "edge"]:
        for tc in data.get(category, []):
            try:
                print(f"Generating {tc['id']} ({category})...")
                test_case_text = f"""
Title: {tc.get('title')}
Steps:
{chr(10).join(tc.get('steps', []))}
Expected Result:
{tc.get('expected_result')}
"""
                script = generate_selenium_script(test_case_text)
                filepath = os.path.join(output_folder, f"{tc['id']}_{category}.py")
                save_script(script, filepath)
                total += 1
            except Exception as e:
                print(f"Error in {tc.get('id', 'UNKNOWN')}: {e}")

    print(f"Done. Generated {total} scripts in '{output_folder}'.")