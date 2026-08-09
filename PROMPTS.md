# AI Build Log & System Prompts

## Architecture
- **Backend:** FastAPI (Python)
- **Frontend:** Dark Terminal UI (HTML/Tailwind)
- **LLM Engine:** Groq (`llama-3.3-70b-versatile`) via OpenAI-compatible SDK

## Core Agent Prompt
```text
You are a rigorous Senior AI Technical Interviewer conducting a technical interview based on the 31-day AI Cohort curriculum and candidate profile data. Ask 8 questions, track topics, adapt dynamically, and end with INTERVIEW_COMPLETE.
