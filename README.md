# ADVISORY-CONSULTANCY-TOOL
🤖 SmartConsult AI: Your Personal AI Strategy Consultant
SmartConsult AI is a powerful, self-hosted consulting platform that leverages multiple large language models (Ollama, Google Gemini, Groq) to provide high-level business analysis and strategic recommendations. It features a sleek, modern dashboard for managing analyses and viewing detailed, visualized reports.

✨ Core Features
Multi-Analysis Engine: Go beyond simple prompts. Generate three distinct types of high-level consulting reports:

Autonomous Case Analysis: Provide a problem statement, and the AI will perform its own internal reasoning to deliver a comprehensive strategic plan, complete with a diagnosis, a 30-60-90 day timeline, and success metrics.

SWOT Analysis: Get a detailed breakdown of a company's Strengths, Weaknesses, Opportunities, and Threats.

PESTLE Analysis: Understand the macro-environmental factors (Political, Economic, Social, Technological, Legal, Environmental) affecting an entire industry.

Multi-Provider LLM Backend: You're in control. Seamlessly switch between different LLM providers based on your needs for speed, cost, or local hosting. Supports:

Ollama (for running local models like Llama 3.1)

Google Gemini (for powerful, cloud-based analysis)

Groq (for incredibly high-speed responses)

Professional Dashboard UI: A clean, intuitive, and beautiful dark-mode interface for creating new analyses, viewing your case history, and examining reports.

Persistent Storage: All your cases and reports are saved permanently in a local SQLite database, so your work is never lost.

Dynamic Report Generation: Reports are generated as standalone HTML files, complete with interactive timeline visualizations for 30-60-90 day plans powered by ApexCharts.js.

🛠️ Technology Stack
Backend: Python, FastAPI, Uvicorn

Database: SQLite

Frontend: HTML, Tailwind CSS, Vanilla JavaScript

Charting: ApexCharts.js

AI Integration: Ollama, Google Gemini API, Groq API

🚀 Getting Started
Follow these steps to get the SmartConsult AI platform running on your local machine.

1. Prerequisites
Python 3.8+

(Optional but Recommended) Ollama installed and running on your machine for local model support.

2. Installation
Clone the repository:

git clone [https://github.com/your-username/smartconsult-ai.git](https://github.com/your-username/smartconsult-ai.git)
cd smartconsult-ai

Navigate to the backend directory:

cd backend

Create and activate a virtual environment (recommended):

python -m venv venv
# On Windows
.\venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate

Install the required dependencies:

pip install -r requirements.txt

3. Configuration
Create your environment file:
In the backend directory, make a copy of .env.example and name it .env.

Add your API Keys:
Open the .env file and fill in your API keys for the services you want to use. You can get them here:

Google Gemini: Google AI Studio

Groq: Groq Console

Set up Ollama (for local models):
If you have Ollama installed, pull your desired model from the terminal. The default is Llama 3.1.

ollama pull llama3.1

4. Running the Application
Start the server:
From the AI CONSULT/backend directory, run the following command:

uvicorn main:app --reload

Open the dashboard:
Open your web browser and navigate to http://127.0.0.1:8000.

You are now ready to start generating high-level consulting reports!

📈 Usage
Dashboard: The main view provides a summary of your past analyses.

New Analysis: Use the sidebar to select the type of analysis you want to perform (Autonomous Case Study, SWOT, or PESTLE). Fill in the required details and click the button to generate the report.

Case History: View a complete list of all the reports you have generated. You can click on any case to view the report directly within the dashboard.

Open Full Report: From the report view, you can open the standalone HTML file in a new tab for a focused view or for saving and sharing.
