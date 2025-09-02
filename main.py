# backend/main.py
import os
import time
import uuid
import json
import sqlite3
import re
from typing import Dict, Any, List, Optional, Literal
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import requests
from jinja2 import Template

print("--- RUNNING CONSULTANT ENGINE v1.5 (FINAL REPORT FORMATTING) ---")

# -------------------------
# Lifespan and Database Setup
# -------------------------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS cases (
            case_id TEXT PRIMARY KEY, provider TEXT, title TEXT, analysis_type TEXT, 
            company_name TEXT, industry TEXT, region TEXT, problem_statement TEXT, 
            created_at REAL, final_recommendation TEXT, report_html TEXT
        )
    ''')
    conn.commit()
    conn.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

# -------------------------
# App Initialization & Config
# -------------------------
app = FastAPI(title="SmartConsult AI Dashboard v2.3", lifespan=lifespan)

load_dotenv()
DB_NAME = "consulting.db"
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

# Provider config
DEFAULT_PROVIDER = os.getenv("DEFAULT_PROVIDER", "ollama").lower()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash").strip()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile").strip()
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").strip()
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1").strip()

# -------------------------
# Middleware & Static Files
# -------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)
app.mount("/reports", StaticFiles(directory=REPORTS_DIR), name="reports")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# -------------------------
# Pydantic Models
# -------------------------
class StandardCaseReq(BaseModel):
    company_name: str; industry: str = ""; problem_statement: str
class SwotReq(BaseModel):
    company_name: str
class PestleReq(BaseModel):
    industry: str

# -------------------------
# AI & API Helpers
# -------------------------
def get_db_connection():
    conn = sqlite3.connect(DB_NAME); conn.row_factory = sqlite3.Row; return conn

def llm_generate(prompt: str, provider: Optional[str] = DEFAULT_PROVIDER) -> str:
    timeout = 300 
    if provider == "gemini":
        if not GEMINI_API_KEY: return "[ERROR] GEMINI_API_KEY missing."
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
        headers = {"Content-Type": "application/json"}; params = {"key": GEMINI_API_KEY}
        payload = {"contents": [{"parts": [{"text": prompt}]}],"generationConfig": {"temperature": 0.4, "maxOutputTokens": 8192}}
        try:
            r = requests.post(url, params=params, headers=headers, json=payload, timeout=timeout); r.raise_for_status(); data = r.json()
            return data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        except Exception as e: return f"[ERROR] Gemini call failed: {str(e)}"
    if provider == "groq":
        if not GROQ_API_KEY: return "[ERROR] GROQ_API_KEY missing."
        url = "https://api.groq.com/openai/v1/chat/completions"; headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        payload = {"model": GROQ_MODEL, "messages": [{"role": "system", "content": "You are a world-class senior management consultant AI."}, {"role": "user", "content": prompt}], "temperature": 0.4, "max_tokens": 8192}
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=timeout); r.raise_for_status(); data = r.json()
            return data.get("choices", [{}])[0].get("message", {}).get("content", "")
        except Exception as e: return f"[ERROR] Groq call failed: {str(e)}"
    # Default to Ollama
    url = f"{OLLAMA_HOST}/api/generate"; payload = {"model": OLLAMA_MODEL, "prompt": prompt, "options": {"temperature": 0.4}, "stream": False}
    try:
        r = requests.post(url, json=payload, timeout=timeout); r.raise_for_status(); data = r.json()
        return data.get("response", "")
    except Exception as e: return f"[ERROR] Ollama call failed: {str(e)}"

def parse_json_from_llm(text: str) -> Dict[str, Any]:
    try:
        json_start = text.find('{')
        if json_start == -1: return {"raw": text}
        brace_count = 0; json_end = -1
        for i, char in enumerate(text[json_start:]):
            if char == '{': brace_count += 1
            elif char == '}': brace_count -= 1
            if brace_count == 0:
                json_end = json_start + i + 1
                break
        if json_end == -1: return {"raw": text}
        json_str = text[json_start:json_end]
        return json.loads(json_str)
    except (json.JSONDecodeError, IndexError):
        return {"raw": text}

# -------------------------
# Report Generation
# -------------------------
REPORT_TEMPLATE = Template("""
<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Consulting Report - {{ title }}</title>
<script src="https://cdn.jsdelivr.net/npm/apexcharts"></script>
<style>
    body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;line-height:1.6;color:#333;max-width:900px;margin:2rem auto;padding:0 1rem;background-color:#f9f9f9}
    h1,h2,h3,h4{color:#222; margin-top: 1.5em;}h1{border-bottom:2px solid #eee;padding-bottom:.5rem; margin-top: 0;}
    .section{background-color:#fff;border:1px solid #ddd;border-radius:8px;padding:1.5rem 2rem;margin-bottom:2rem; box-shadow: 0 2px 4px rgba(0,0,0,0.05);}
    ul{padding-left:20px; list-style: none;} li{margin-bottom: 1rem;}
    .analysis-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; }
    .analysis-card { padding: 1.5rem; background-color: #fafafa; border: 1px solid #eee; border-radius: 8px; }
    .analysis-card h4 { margin-top: 0; color: #007bff; border-bottom: 1px solid #ddd; padding-bottom: 0.5rem; margin-bottom: 1rem; }
    .empty-item { color: #999; font-style: italic; }
    #timeline-chart { min-height: 350px; }
    .list-item-title { font-weight: bold; color: #333; }
    .list-item-desc { color: #555; font-size: 0.95em; }
    .list-item-example { color: #777; font-size: 0.9em; font-style: italic; border-left: 3px solid #eee; padding-left: 10px; margin-top: 5px;}
</style>
</head><body><h1>{{ title }}</h1>
{% macro render_list(items) %}
    <ul>
        {% if items %}
            {% for item in items %}
                <li>
                    {% if item is mapping and item.name %}
                        <div class="list-item-title">{{ item.name }}</div>
                        {% if item.description %}<div class="list-item-desc">{{ item.description }}</div>{% endif %}
                        {% if item.example %}<div class="list-item-example">e.g., {{ item.example }}</div>{% endif %}
                    {% elif item is string %}
                        {{ item }}
                    {% else %}
                        {{ item | tojson }}
                    {% endif %}
                </li>
            {% endfor %}
        {% else %}
            <li class="empty-item">No specific items identified.</li>
        {% endif %}
    </ul>
{% endmacro %}

{% if analysis_type == 'standard' and recommendation.executive_summary %}
    <div class="section"><h2>Executive Summary</h2><p>{{ recommendation.executive_summary }}</p></div>
    <div class="section"><h2>Diagnosis</h2>{{ render_list(recommendation.diagnosis) }}</div>
    <div class="section"><h4>30-60-90 Day Plan</h4><div id="timeline-chart"></div></div>
    <div class="section"><h2>Metrics for Success</h2>{{ render_list(recommendation.metrics) }}</div>
    <div class="section"><h2>Quick Wins</h2>{{ render_list(recommendation.quick_wins) }}</div>
{% elif analysis_type == 'swot' %}
    <div class="section analysis-grid">
        <div class="analysis-card"><h4>Strengths</h4>{{ render_list(recommendation.strengths) }}</div>
        <div class="analysis-card"><h4>Weaknesses</h4>{{ render_list(recommendation.weaknesses) }}</div>
        <div class="analysis-card"><h4>Opportunities</h4>{{ render_list(recommendation.opportunities) }}</div>
        <div class="analysis-card"><h4>Threats</h4>{{ render_list(recommendation.threats) }}</div>
    </div>
{% elif analysis_type == 'pestle' %}
    <div class="section analysis-grid">
        <div class="analysis-card"><h4>Political</h4>{{ render_list(recommendation.political) }}</div>
        <div class="analysis-card"><h4>Economic</h4>{{ render_list(recommendation.economic) }}</div>
        <div class="analysis-card"><h4>Social</h4>{{ render_list(recommendation.social) }}</div>
        <div class="analysis-card"><h4>Technological</h4>{{ render_list(recommendation.technological) }}</div>
        <div class="analysis-card"><h4>Legal</h4>{{ render_list(recommendation.legal) }}</div>
        <div class="analysis-card"><h4>Environmental</h4>{{ render_list(recommendation.environmental) }}</div>
    </div>
{% else %}
    <div class="section"><pre>{{ recommendation.raw or "Could not generate a valid report." }}</pre></div>
{% endif %}
<script>
    document.addEventListener("DOMContentLoaded", function() {
        const planData = {{ plan_json | safe }};
        if (planData && Object.keys(planData).length > 0) {
            const seriesData = [
                { name: 'First 30 Days', data: (planData['30'] || []).map(task => ({ x: (task.name || task), y: [new Date().getTime(), new Date(new Date().getTime() + 30 * 24 * 60 * 60 * 1000).getTime()] })) },
                { name: 'Next 60 Days', data: (planData['60'] || []).map(task => ({ x: (task.name || task), y: [new Date(new Date().getTime() + 30 * 24 * 60 * 60 * 1000).getTime(), new Date(new Date().getTime() + 60 * 24 * 60 * 60 * 1000).getTime()] })) },
                { name: 'Next 90 Days', data: (planData['90'] || []).map(task => ({ x: (task.name || task), y: [new Date(new Date().getTime() + 60 * 24 * 60 * 60 * 1000).getTime(), new Date(new Date().getTime() + 90 * 24 * 60 * 60 * 1000).getTime()] })) }
            ];
            var options = {
                series: seriesData, chart: { type: 'rangeBar', height: 400, toolbar: { show: false } },
                plotOptions: { bar: { horizontal: true, barHeight: '80%', borderRadius: 5 } },
                xaxis: { type: 'datetime' }, stroke: { width: 1 }, fill: { type: 'solid', opacity: 0.6 },
                legend: { position: 'top', horizontalAlign: 'left' }, tooltip: { x: { format: 'dd MMM' } }
            };
            var chart = new ApexCharts(document.querySelector("#timeline-chart"), options);
            chart.render();
        }
    });
</script>
</body></html>
""")

def save_and_get_path(case_obj: Dict[str, Any]) -> str:
    recommendation = json.loads(case_obj.get("final_recommendation") or '{}')
    html = REPORT_TEMPLATE.render(
        title=case_obj["title"],
        analysis_type=case_obj["analysis_type"],
        recommendation=recommendation,
        plan_json=json.dumps(recommendation.get("plan_30_60_90", {}))
    )
    filename = f"report_{case_obj['case_id']}.html"
    path = os.path.join(REPORTS_DIR, filename)
    with open(path, "w", encoding="utf-8") as f: f.write(html)
    return path

# -------------------------
# API Endpoints
# -------------------------
@app.get("/", include_in_schema=False)
async def read_index(): return FileResponse(os.path.join(STATIC_DIR, 'index.html'))

@app.get("/cases")
def get_all_cases():
    try:
        conn = get_db_connection()
        cases_rows = conn.execute('SELECT case_id, title, analysis_type, company_name, created_at, report_html FROM cases ORDER BY created_at DESC').fetchall()
        conn.close()
        return [dict(row) for row in cases_rows]
    except Exception as e:
        print(f"!!! DATABASE ERROR fetching cases: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch cases from database.")

@app.post("/start_case")
def start_case(payload: StandardCaseReq):
    case_id = str(uuid.uuid4())
    title = f"Case Study for {payload.company_name}"
    
    prompt1 = f"Given the problem '{payload.problem_statement}' for the company '{payload.company_name}', generate 3-4 critical diagnostic questions a consultant would ask to understand the root cause. Just return the questions, each on a new line."
    internal_questions = llm_generate(prompt1)

    prompt2 = f"You are a senior consultant analyzing a problem for '{payload.company_name}': '{payload.problem_statement}'. Your internal diagnostic questions are: '{internal_questions}'. Provide concise, expert answers to your own questions based on common business scenarios to build a context for your final analysis."
    internal_answers = llm_generate(prompt2)

    prompt3 = f"You are a Partner-level management consultant synthesizing a final report. Based on the deep context below, produce a comprehensive and actionable strategic plan.\n\nContext:\n- Company: {payload.company_name}\n- Stated Problem: {payload.problem_statement}\n- Your Internal Analysis & Reasoning:\n{internal_answers}\n\nYour final output must be a strategic document of the highest quality. For each key in the JSON, provide detailed and insightful content. The 30-60-90 day plan must contain specific, actionable steps. Return ONLY valid, minified JSON with the following structure: {{\"executive_summary\":\"...\",\"diagnosis\":[...],\"plan_30_60_90\":{{\"30\":[...],\"60\":[...],\"90\":[...]}},\"metrics\":[...],\"quick_wins\":[...]}}"
    raw_rec = llm_generate(prompt3)
    
    rec = parse_json_from_llm(raw_rec)

    case_obj = { "case_id": case_id, "title": title, "analysis_type": "standard", "final_recommendation": json.dumps(rec) }
    html_path = save_and_get_path(case_obj)
    
    conn = get_db_connection()
    conn.execute('INSERT INTO cases (case_id, title, analysis_type, company_name, problem_statement, final_recommendation, report_html, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
        (case_id, title, "standard", payload.company_name, payload.problem_statement, json.dumps(rec), html_path, time.time()))
    conn.commit(); conn.close()
    return {"report_html": html_path}

@app.post("/analyze/swot")
def analyze_swot(payload: SwotReq):
    case_id = str(uuid.uuid4()); title = f"SWOT Analysis for {payload.company_name}"
    prompt = f"You are a top-tier management consultant from a McKinsey / BCG / Bain level firm. Your career depends on the quality of this report. Conduct a comprehensive SWOT analysis for the company '{payload.company_name}'. For each of the four categories (Strengths, Weaknesses, Opportunities, Threats), provide at least 4-6 detailed, insightful bullet points. Each bullet point should be a JSON object with 'name', 'description', and 'example' keys. Your analysis must be sharp, specific, and actionable. Return ONLY valid, minified JSON with keys: {{\"strengths\":[...],\"weaknesses\":[...],\"opportunities\":[...],\"threats\":[...]}}"
    raw_rec = llm_generate(prompt)
    rec = parse_json_from_llm(raw_rec)

    case_obj = {"case_id": case_id, "title": title, "analysis_type": "swot", "final_recommendation": json.dumps(rec)}
    html_path = save_and_get_path(case_obj)

    conn = get_db_connection()
    conn.execute('INSERT INTO cases (case_id, title, analysis_type, company_name, final_recommendation, report_html, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
        (case_id, title, "swot", payload.company_name, json.dumps(rec), html_path, time.time()))
    conn.commit(); conn.close()
    return {"report_html": html_path}

@app.post("/analyze/pestle")
def analyze_pestle(payload: PestleReq):
    case_id = str(uuid.uuid4()); title = f"PESTLE Analysis for {payload.industry} industry"
    prompt = f"You are a senior geopolitical and economic analyst from a world-renowned think tank. Your reputation is on the line. Conduct a comprehensive PESTLE analysis for the '{payload.industry}' industry. For each of the six categories (Political, Economic, Social, Technological, Legal, Environmental), provide at least 4-6 detailed, specific factors. Each factor should be a JSON object with 'name' and 'description' keys, explaining its potential impact. Return ONLY valid, minified JSON with keys: {{\"political\":[...],\"economic\":[...],\"social\":[...],\"technological\":[...],\"legal\":[...],\"environmental\":[...]}}"
    raw_rec = llm_generate(prompt)
    rec = parse_json_from_llm(raw_rec)

    case_obj = {"case_id": case_id, "title": title, "analysis_type": "pestle", "final_recommendation": json.dumps(rec)}
    html_path = save_and_get_path(case_obj)

    conn = get_db_connection()
    conn.execute('INSERT INTO cases (case_id, title, analysis_type, industry, final_recommendation, report_html, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
        (case_id, title, "pestle", payload.industry, json.dumps(rec), html_path, time.time()))
    conn.commit(); conn.close()
    return {"report_html": html_path}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
