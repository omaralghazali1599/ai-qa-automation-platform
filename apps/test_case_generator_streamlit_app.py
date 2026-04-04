import os
import json
import re
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
from core.schemas import TestSuite



# -------------------------------
# Configuration & Setup
# -------------------------------

def save_json_locally(data, filename):
    """Save JSON file in current project folder"""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="AI Test Case Generator", layout="wide", page_icon="🧪")

# Initialize OpenAI Client
if not OPENAI_API_KEY:
    st.error("❌ OpenAI API key not found. Please set OPENAI_API_KEY in your .env file.")
    st.stop()

client = OpenAI(api_key=OPENAI_API_KEY)

# -------------------------------
# Helper Functions
# -------------------------------
def sanitize_filename(text):
    """Creates a filesystem-safe filename from the user story."""
    filename = re.sub(r'[\\/*?:"<>|]', "", text)
    filename = filename.strip().replace(" ", "_")
    return (filename[:50] or "test_cases") + ".json"

def clean_json_response(text):
    """Removes markdown code blocks if the AI includes them."""
    return re.sub(r"```json|```", "", text).strip()

def generate_test_cases(user_story):
    """Calls OpenAI API to generate structured test cases."""
    system_prompt = "You are a professional QA Engineer. You must return ONLY valid JSON."
    user_prompt = f"""
    Generate all the possible comprehensive test cases for this user story that covers all positive, negative, and edge cases.:
    "{user_story}"

    Return the response in this EXACT JSON structure:
    {{
      "positive": [
        {{ "id": "TC-P01", "title": "Description", "steps": ["Step 1", "Step 2"], "expected_result": "Result" }}
      ],
      "negative": [
        {{ "id": "TC-N01", "title": "Description", "steps": [], "expected_result": "" }}
      ],
      "edge": [
        {{ "id": "TC-E01", "title": "Description", "steps": [], "expected_result": "" }}
      ]
    }}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini", # Changed from 4.1-mini
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={ "type": "json_object" } # Ensures JSON output
        )

        result_text = response.choices[0].message.content
        raw = json.loads(clean_json_response(result_text))
        validated = TestSuite(**raw)
        return validated.model_dump()

    except Exception as e:
        st.error(f"❌ Error generating test cases: {e}")
        return None

# -------------------------------
# Streamlit UI
# -------------------------------
st.title("🧪 AI Test Case Generator")
st.markdown("Enter your User Story below to generate Positive, Negative, and Edge Case tests.")

user_story = st.text_area("User Story", placeholder="As a [role], I want to [action] so that [benefit]...", height=120)

if st.button("Generate Test Cases", type="primary"):
    if not user_story.strip():
        st.warning("Please enter a user story first.")
    else:
        with st.spinner("Analyzing and generating tests..."):
            result = generate_test_cases(user_story)
            
            if result:
                st.success("Test Cases Generated!")
                
              

                # Save locally
                filename = sanitize_filename(user_story)
                save_json_locally(result, filename)
                st.info(f"📁 Saved locally as: {filename}")

                # Layout with Tabs for better UX
                tab1, tab2, tab3, tab4 = st.tabs(["✅ Positive", "❌ Negative", "⚠️ Edge Cases", "📄 Raw JSON"])
                
                with tab1:
                    for tc in result.get("positive", []):
                        with st.expander(f"{tc['id']}: {tc['title']}"):
                            st.write("**Steps:**")
                            for step in tc['steps']: st.write(f"- {step}")
                            st.write(f"**Expected:** {tc['expected_result']}")

                with tab2:
                    for tc in result.get("negative", []):
                        with st.expander(f"{tc['id']}: {tc['title']}"):
                            st.write("**Steps:**")
                            for step in tc['steps']: st.write(f"- {step}")
                            st.write(f"**Expected:** {tc['expected_result']}")

                with tab3:
                    for tc in result.get("edge", []):
                        with st.expander(f"{tc['id']}: {tc['title']}"):
                            st.write("**Steps:**")
                            for step in tc['steps']: st.write(f"- {step}")
                            st.write(f"**Expected:** {tc['expected_result']}")

                with tab4:
                    st.json(result)

                # Download Button
                json_data = json.dumps(result, indent=4)
                st.download_button(
                    label="📥 Download JSON",
                    data=json_data,
                    file_name=filename,
                    mime="application/json"
                )       
