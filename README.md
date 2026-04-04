🤖 AI QA Automation Platform

An end-to-end AI-powered software testing platform that converts user stories into structured test cases and automatically generates executable Selenium test scripts.

-------------------------------
🚀 Features
-------------------------------
- 🧠 Generate test cases from user stories using AI
- 📊 Categorize into Positive, Negative, and Edge cases
- ⚙️ Convert test cases into Selenium automation scripts
- 📦 Download automation scripts as ZIP
- 🌐 Interactive UI using Streamlit

-------------------------------
🏗️ Architecture
-------------------------------
User Story  
→ AI Test Case Generator  
→ JSON Test Cases  
→ AI Script Generator  
→ Selenium Test Scripts  

-------------------------------
🛠️ Tech Stack
-------------------------------
- Python
- Streamlit
- OpenAI API
- Selenium

-------------------------------
▶️ How to Run
-------------------------------

1. Clone Repository:

  git clone https://github.com/omaralghazali1599/ai-qa-automation.git
  cd ai-qa-automation

2. Create Virtual Enviroment:

  python -m venv venv
  venv\Scripts\activate

3. Install Dependancies:

  pip install -r requirements.txt

4. Add API Key
  create a new .env file
  paste "OPENAI_API_KEY=your_api_key_here" and you API key in the file

5. Run the applications:
   App 1: Test Case Generator
   streamlit run apps/test_case_generator_app.py
   App 2: Script Generator
   streamlit run apps/streamlit_pipeline.py

-------------------------------
💼 Use Case
-------------------------------
This project demonstrates how AI can enhance software testing by automating:

-Test case generation
-Test script generation
-QA workflow optimization


📸 Screenshots

These are screenshots from the app, before generating, while generating, and after generating the test cases:
<img width="1920" height="1030" alt="TCG3" src="https://github.com/user-attachments/assets/8df9ac77-b4cc-47b2-9c91-ff4f5510ac96" />
<img width="1920" height="1030" alt="TCG2" src="https://github.com/user-attachments/assets/4cb3c628-6788-489d-912d-764657f5aff5" />
<img width="1920" height="1030" alt="TCG1" src="https://github.com/user-attachments/assets/2096eb4f-bf12-4c6d-aca8-7e24c5ae2b73" />

The following screenshots are from the script generator app they where took while the json file was being uploaded, generating scripts for each test case, and a screenshot from the .zip downloaded after the generation is done:
<img width="1676" height="788" alt="SG4" src="https://github.com/user-attachments/assets/3c67ee4c-6cc1-4f81-9ef9-df37825229ce" />
<img width="1920" height="1030" alt="SG3" src="https://github.com/user-attachments/assets/a689af96-cc84-4b88-a80a-6279923256b9" />
<img width="1920" height="1030" alt="SG2" src="https://github.com/user-attachments/assets/7cd6af4f-e24b-427d-bf7d-f70abdc57f3b" />
<img width="1920" height="1030" alt="SG1" src="https://github.com/user-attachments/assets/f5cba789-a523-48c7-8fb0-ab3765172228" />



