import os
import json
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Create client (IMPORTANT)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_test_cases(user_story):
    prompt = f"""
    You are a QA engineer.

    Generate test cases for the following user story:
    "{user_story}"

    Return the response in STRICT JSON format like this:

    {{
      "positive": [
        {{
          "id": "TC01",
          "title": "",
          "steps": [],
          "expected_result": ""
        }}
      ],
      "negative": [],
      "edge": []
    }}
    """



    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content

def save_to_file(data):
    try:
        parsed = json.loads(data)
        with open("test_cases.json", "w") as f:
            json.dump(parsed, f, indent=4)
        print("✅ Test cases saved to test_cases.json")
    except:
        print("❌ Failed to parse JSON. Raw output saved.")
        with open("raw_output.txt", "w") as f:
            f.write(data)


if __name__ == "__main__":
    user_story = input("Enter user story: ")
    result = generate_test_cases(user_story)

    print("\nGenerated Test Cases:\n")
    print(result)

    save_to_file(result)