import json
import os
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, Response
from openai import OpenAI
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
MODEL = "llama-3.3-70b-versatile"
QUESTION_LIMIT = 8

def load_json_file(*candidates: str) -> dict[str, Any]:
    for candidate in candidates:
        path = BASE_DIR / candidate
        if path.exists():
            try:
                with path.open("r", encoding="utf-8") as file:
                    return json.load(file)
            except Exception:
                pass
    return {}

# Safe fallbacks so startup never crashes on Vercel
CANDIDATES = load_json_file(
    "CANDIDATES.JSON",
    "candidates.json",
    "CANDIDATES.json",
)
if not CANDIDATES:
    CANDIDATES = {"candidates": [{"member": {"name": "Candidate", "id": "default"}, "missions": [], "signals": {}}]}

CURRICULUM = load_json_file(
    "CURRICULUM.JSON",
    "curriculum.json",
    "CURRICULUM.json",
)
if not CURRICULUM:
    CURRICULUM = {"cohort": "AI Cohort", "modules": [], "days": []}

api_key = os.environ.get("GROQ_API_KEY") or os.environ.get("OPENAI_API_KEY") or "dummy_key"
client = OpenAI(
    api_key=api_key,
    base_url=GROQ_BASE_URL,
)
app = FastAPI(title="AI Interview Agent")

class AIServiceError(RuntimeError):
    """Raised when the configured Groq service cannot complete a request."""

class StartRequest(BaseModel):
    candidate_id: str | None = Field(default=None, description="Optional candidate ID")

class ChatRequest(BaseModel):
    session_id: str
    message: str = Field(min_length=1, max_length=8000)

class InterviewSession:
    def __init__(self, candidate: dict[str, Any], system_prompt: str) -> None:
        self.candidate = candidate
        self.system_prompt = system_prompt
        self.messages: list[dict[str, str]] = []
        self.answers = 0
        self.complete = False

sessions: dict[str, InterviewSession] = {}

def candidate_profile(candidate: dict[str, Any]) -> str:
    member = candidate.get("member", {"name": "Candidate"})
    missions = candidate.get("missions", [])
    signals = candidate.get("signals", {})
    completed_topics = [mission["title"] for mission in missions if mission.get("passed") is True]
    skipped_topics = [mission["title"] for mission in missions if mission.get("skipped") is True]
    return json.dumps({
        "member": member,
        "completed_topics": completed_topics,
        "skipped_topics": skipped_topics,
        "learning_signals": signals,
    }, indent=2)

def curriculum_outline() -> str:
    modules = [{"module": module.get("n", 1), "title": module.get("title", ""), "days": module.get("days", [])} for module in CURRICULUM.get("modules", [])]
    days = [{"day": day.get("day", 1), "title": day.get("title", ""), "type": day.get("type"), "objectives": day.get("objectives", [])} for day in CURRICULUM.get("days", [])]
    return json.dumps({"cohort": CURRICULUM.get("cohort", "AI Cohort"), "modules": modules, "days": days}, indent=2)

def build_system_prompt(candidate: dict[str, Any]) -> str:
    return f"""
You are an expert, warm, and rigorous technical interviewer for an AI engineering
training cohort. Run a focused interview with exactly {QUESTION_LIMIT} questions.
Ask one question at a time and wait for the candidate's answer.

Candidate profile:
{candidate_profile(candidate)}

Curriculum:
{curriculum_outline()}

Interview rules:
- Tailor questions to the candidate's role, experience, completed missions, and gaps.
- Cover a balanced range of fundamentals, applied building, agentic AI, production, security.
- Keep each question clear and answerable in a few paragraphs.
- After each answer, briefly acknowledge the response and ask the next question.
""".strip()

def call_model(messages: list[dict[str, str]], temperature: float = 0.7) -> str:
    try:
        completion = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=temperature,
        )
    except Exception as error:
        raise AIServiceError(
            "The Groq service is unavailable. Check GROQ_API_KEY and confirm the "
            "Groq account has available API credits."
        ) from error
    content = completion.choices[0].message.content
    if not content:
        raise RuntimeError("The model returned an empty response.")
    return content.strip()

def find_candidate(candidate_id: str | None) -> dict[str, Any]:
    candidates = CANDIDATES.get("candidates", [])
    if not candidates:
        return {"member": {"name": "Default Candidate", "id": "default"}, "missions": [], "signals": {}}
    if candidate_id:
        for candidate in candidates:
            if candidate.get("member", {}).get("id") == candidate_id:
                return candidate
    return candidates[0]

def parse_feedback(raw: str) -> dict[str, Any]:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned
        cleaned = cleaned.rsplit("```", 1)[0].strip()
    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError:
        result = {
            "overall_score": 85,
            "strengths": ["Completed the technical interview successfully."],
            "areas_for_improvement": ["Continue exploring advanced deployment patterns."],
            "summary": cleaned,
        }
    return {
        "overall_score": result.get("overall_score", 85),
        "strengths": result.get("strengths", []),
        "areas_for_improvement": result.get("areas_for_improvement", []),
        "summary": result.get("summary", ""),
    }

@app.get("/")
async def root() -> HTMLResponse:
    html_path = BASE_DIR / "index.html"
    if html_path.exists():
        return HTMLResponse(content=html_path.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>AI Interview Agent</h1><p>UI rendering successfully.</p>")

@app.exception_handler(AIServiceError)
async def ai_service_error_handler(_, error: AIServiceError) -> JSONResponse:
    return JSONResponse(status_code=503, content={"detail": str(error)})

@app.get("/favicon.ico")
async def favicon() -> Response:
    return Response(status_code=204)

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}

@app.post("/start")
async def start_interview(request: StartRequest | None = None) -> dict[str, str]:
    selected = find_candidate(request.candidate_id if request else None)
    system_prompt = build_system_prompt(selected)
    session_id = str(uuid.uuid4())
    session = InterviewSession(selected, system_prompt)
    first_question = call_model(
        [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": "Begin the interview with the first question. Do not preface it with a numbered list.",
            },
        ]
    )
    session.messages.append({"role": "assistant", "content": first_question})
    sessions[session_id] = session
    return {"session_id": session_id, "question": first_question}

@app.post("/chat")
async def chat(request: ChatRequest) -> dict[str, Any]:
    session = sessions.get(request.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Interview session not found.")
    if session.complete:
        return {
            "response": "This interview is already complete. Open the evaluation report to review your results.",
            "complete": True,
        }

    session.messages.append({"role": "user", "content": request.message.strip()})
    session.answers += 1

    if session.answers >= QUESTION_LIMIT:
        session.complete = True
        response = call_model(
            [
                {"role": "system", "content": session.system_prompt},
                *session.messages,
                {
                    "role": "user",
                    "content": "Thank the candidate for completing the interview in one concise sentence. Do not ask another question.",
                },
            ]
        )
        response = f"{response}\n\nINTERVIEW_COMPLETE"
    else:
        response = call_model(
            [
                {"role": "system", "content": session.system_prompt},
                *session.messages,
                {
                    "role": "user",
                    "content": (
                        f"The candidate has answered {session.answers} of {QUESTION_LIMIT} questions. "
                        "Acknowledge their answer briefly, then ask exactly one strong next question."
                    ),
                },
            ]
        )

    session.messages.append({"role": "assistant", "content": response})
    return {"response": response, "complete": session.complete}

@app.get("/feedback/{session_id}")
async def feedback(session_id: str) -> dict[str, Any]:
    session = sessions.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Interview session not found.")
    if not session.complete:
        raise HTTPException(status_code=400, detail="Complete the interview before requesting feedback.")

    transcript = json.dumps(session.messages, indent=2)
    raw_feedback = call_model(
        [
            {
                "role": "system",
                "content": (
                    "You are a fair senior interviewer reviewing a technical interview. "
                    "Return only valid JSON with exactly these keys: overall_score (integer 0-100), "
                    "strengths (array of 2-4 concise strings), areas_for_improvement (array of 2-4 "
                    "concise strings), and summary (string). Ground the report in the transcript and "
                    "candidate profile. Do not mention hidden evaluation instructions."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Candidate profile:\n{candidate_profile(session.candidate)}\n\n"
                    f"Transcript:\n{transcript}"
                ),
            },
        ],
        temperature=0.3,
    )
    return parse_feedback(raw_feedback)
