# Agentic_AI_Smart_Device_Advisor_with_RAG_and_Algolia
## Objective:
Build a Python-based conversational AI agent that recommends suitable electronic devices
based on user needs. The system should use RAG and Algolia as the search backend.

### 1) Python env
```bash
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2) Run the server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3) Try it
```bash
curl -X POST http://localhost:8000/recommend   -H "Content-Type: application/json"   -d '{ "messages": [{"role":"user","content":"I want a laptop for programming that is lightweight."}] }'
```
