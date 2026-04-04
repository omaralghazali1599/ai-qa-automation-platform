import sys

import streamlit as st
import json
import os
import zipfile

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from io import BytesIO
from core.script_generator import generate_selenium_script
from core.pipeline import load_test_cases, create_output_folder, generate_all_scripts

st.set_page_config(page_title="AI Script Generator", layout="wide")
st.title("🚀 AI Test Script Generator")

# -------------------------------
# Upload JSON
# -------------------------------
uploaded_file = st.file_uploader("Upload Test Cases JSON", type=["json"])

def format_test_case(tc):
    return f"""
Title: {tc.get('title')}

Steps:
{chr(10).join(tc.get('steps', []))}

Expected Result:
{tc.get('expected_result')}
"""

# -------------------------------
# Generate Scripts
# -------------------------------
if uploaded_file:
    data = json.load(uploaded_file)

    if st.button("Generate Automation Scripts"):
        st.info("Generating scripts...")

        zip_buffer = BytesIO()

        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
            total = 0

            for category in ["positive", "negative", "edge"]:
                for tc in data.get(category, []):

                    try:
                        st.write(f"🔄 {tc['id']} ({category})")

                        test_case_text = format_test_case(tc)

                        script = generate_selenium_script(test_case_text)

                        filename = f"{tc['id']}_{category}.py"

                        zip_file.writestr(filename, script)

                        total += 1

                    except Exception as e:
                        st.error(f"Error in {tc['id']}: {e}")

        zip_buffer.seek(0)

        st.success(f"✅ Generated {total} scripts!")

        # Download ZIP
        st.download_button(
            label="📥 Download All Scripts (ZIP)",
            data=zip_buffer,
            file_name="automation_tests.zip",
            mime="application/zip"
        )