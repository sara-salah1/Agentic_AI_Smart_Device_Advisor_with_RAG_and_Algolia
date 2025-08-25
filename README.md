# Agentic_AI_Smart_Device_Advisor_with_RAG_and_Algolia

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
