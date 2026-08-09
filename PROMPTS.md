# Development & AI Usage Log (PROMPTS.md)

This log records the chronological prompt history and iterative steps used during the development, styling, debugging, and deployment of the AI Technical Interview Agent.

---

### Prompt 1: Initial Project Scaffolding
> **Prompt:** "Let's build a FastAPI backend in Python for an AI interview agent. We need to load candidate profiles and cohort curriculum from local JSON files (`CANDIDATES.JSON` and `CURRICULUM.JSON`). Set up the OpenAI client pointing to Groq's base URL (`https://api.groq.com/openai/v1`) using the `llama-3.3-70b-versatile` model. Give me the basic FastAPI boilerplate with a health check endpoint."

---

### Prompt 2: Session & Chat Endpoint Logic
> **Prompt:** "Now add the core interview endpoints: `/start` to initialize a session with a unique UUID and generate the first question, and `/chat` to handle incoming candidate responses. Keep track of the message history in-memory using a dictionary, and cap the interview at 8 questions."

---

### Prompt 3: Frontend Terminal UI Design
> **Prompt:** "Let's create the frontend in `index.html` using Tailwind CSS via CDN. I want it to look like a high-tech developer terminal—dark background (`#030712`), emerald-500 glowing accents, monospace font. Include a header, a scrollable chat log container, a text input field, and a send button that stays disabled until the interview starts."

---

### Prompt 4: System Prompt Tuning & Question Flow
> **Prompt:** "The model is currently asking too many questions at once or breaking character. Refine the system prompt so it acts as a rigorous senior technical interviewer. It must read the candidate's profile and curriculum data dynamically, ask *only one* question at a time, wait for a response, briefly acknowledge it, and append an `INTERVIEW_COMPLETE` flag when it hits the 8th turn."

---

### Prompt 5: Implementing the Final Evaluation Report Card
> **Prompt:** "We need a feedback feature. Add a `/feedback/{session_id}` endpoint that analyzes the full chat transcript at the end of the interview. Have the LLM return a strict JSON payload with `overall_score`, `strengths`, `areas_for_improvement`, and `summary`. Also, update the frontend `index.html` to display a hidden report card grid that unlocks and populates once the chat finishes."

---

### Prompt 6: Fixing JSON Parsing on Model Responses
> **Prompt:** "Sometimes the model wraps the feedback JSON inside markdown code blocks like ````json ... ```` which breaks `json.loads()` on the backend. Write a helper function in python to strip out markdown fences cleanly before parsing the evaluation response."

---

### Prompt 7: Vercel Serverless Deployment Setup
> **Prompt:** "I want to deploy this app to Vercel. Create a `vercel.json` configuration file and a `requirements.txt` with `fastapi`, `uvicorn`, `openai`, and `pydantic`. Let's also use `pathlib.Path` to ensure `main.py` resolves `index.html` and the JSON files correctly using absolute paths."

---

### Prompt 8: Debugging Serverless Startup Crashes
> **Prompt:** "Vercel is throwing a `500 INTERNAL_SERVER_ERROR` with `FUNCTION_INVOCATION_FAILED` on startup. Fix the file loading logic so it uses try-except blocks and fallback empty dictionaries instead of crashing the server if a file path is slightly off. Also, replace `FileResponse` with `HTMLResponse` to serve `index.html` safely in serverless mode, and check for both `GROQ_API_KEY` and `OPENAI_API_KEY` environment variables."
