import os
import re
from dotenv import load_dotenv
from openai import OpenAI

# -------------------------------
# Load API
# -------------------------------
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# -------------------------------
# Helpers
# -------------------------------

def clean_code_output(text):
    """Remove markdown and clean AI output"""
    text = re.sub(r"```python|```", "", text)
    return text.strip()

def save_script(code, filename):
    """Save script to file"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(code)

# -------------------------------
# Main Generator
# -------------------------------

def generate_selenium_script(test_case):
    prompt = f"""
You are a SENIOR QA automation engineer.

Convert the following test case into CLEAN Python Selenium code.

STRICT RULES:
- Return ONLY Python code (NO markdown, NO ```python)
- No duplicate steps
- No repeated lines
- Use unittest framework
- Include setup() and teardown()
- Use Chrome WebDriver
- Use explicit waits (WebDriverWait)
- Add clear comments
- Keep code clean and minimal

Test Case:
{test_case}
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    raw_output = response.choices[0].message.content
    return clean_code_output(raw_output)