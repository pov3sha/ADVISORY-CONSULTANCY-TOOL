from pydantic import BaseModel
from typing import Dict, Any, List, Optional, Literal

class StartCaseReq(BaseModel):
    company_name: str
    industry: str = ""
    region: str = ""
    size: str = ""
    revenue: str = ""
    users: str = ""
    problem_statement: str
    provider: Optional[Literal["ollama", "gemini", "groq"]] = None  # optional override

class FollowupAnswers(BaseModel):
    case_id: str
    answers: Dict[str, str]
    provider: Optional[Literal["ollama", "gemini", "groq"]] = None  # optional override

class AskReq(BaseModel):
    prompt: str
    provider: Optional[Literal["ollama", "gemini", "groq"]] = None
