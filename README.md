# Context-First

Interactive business English training via situation logic.

The app presents a realistic scene, pauses at a crisis moment, evaluates the
user's immediate English response by intent and situational nuance, then returns
AI coach feedback.

## Core Flow

1. Scene transcript
2. Crisis pause
3. User response
4. AI Coach feedback

Feedback includes semantic score, nuance score, star rating, context
explanation, improvement suggestions, grammar feedback, and a better response.

## Scenarios

- `Hotel Lobby Crisis`
- `Airport Baggage Delay`
- `Video Meeting Delay`

Each scenario is stored as JSON in `scenarios/` with transcript, persona,
pause line, ideal intent, acceptable responses, and evaluation rubric.

## Tech

- Server: Python standard library `http.server`
- Frontend: plain HTML/CSS/JavaScript
- Embedding: `sentence-transformers` if installed, otherwise local fallback
- Evaluation: cosine similarity + scenario-specific rubric
- Generative feedback: optional OpenRouter
- Tests: Python `unittest`

## Run

```bash
python3 server.py
```

Open:

```text
http://127.0.0.1:8000
```

## Optional Embedding Model

Install local semantic embedding support:

```bash
python3 -m pip install -r requirements-optional.txt
```

Default model:

```text
sentence-transformers/all-MiniLM-L6-v2
```

Override:

```bash
export CONTEXT_FIRST_ST_MODEL="sentence-transformers/all-MiniLM-L6-v2"
```

## Optional OpenRouter Feedback

OpenRouter is used only for richer generative critique. The app still works
without it.

```bash
export OPENROUTER_API_KEY="sk-or-..."
export OPENROUTER_MODEL="openrouter/auto"
python3 server.py
```

## Test

```bash
python3 -m unittest
```

## API

```http
GET /api/scenarios
GET /api/scenarios/{scenario_id}
POST /api/evaluate
```

Example:

```http
POST /api/evaluate
Content-Type: application/json

{
  "scenario_id": "hotel_lobby_crisis",
  "response": "I have a reservation under Kim Ji-hoon. Could you please check again?"
}
```

## Roadmap

- STT voice input
- video context analysis
- multi-turn role-play
