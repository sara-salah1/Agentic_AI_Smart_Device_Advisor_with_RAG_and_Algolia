from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from .schemas import RecommendRequest, RecommendResponse, Recommendation, Hit, Message
from .config import settings
from .intent import extract_slots, propose_questions
from .retriever import AlgoliaRetriever
from .ranker import rerank
from typing import List, Dict, Any, Tuple

app = FastAPI(title="Agentic Device Advisor", version="1.0.0")


@app.get("/health")
def health():
    return {"status": "ok"}


def get_context(req: RecommendRequest) -> Tuple[str, List[Dict[str, str]]]:
    if req.query:
        return req.query, None
    if req.messages:
        last_user = ""
        for m in reversed(req.messages):
            if m.role == "user":
                last_user = m.content
                break
        return last_user, [{"role": m.role, "content": m.content} for m in req.messages]
    raise HTTPException(status_code=400, detail="No user text provided. Send 'query' or 'messages'.")


@app.post("/recommend")
def recommend(req: RecommendRequest, response_format: str = "json"):
    user_text, messages = get_context(req)
    print("the user text is: ", user_text)
    slots = extract_slots(user_text)
    print("the slots are: ", slots)

    if req.budget_min is not None:
        slots["budget_min"] = req.budget_min
    if req.budget_max is not None:
        slots["budget_max"] = req.budget_max

    filters = {
        "os": slots.get("os"),
        "device_type": slots.get("device_type"),
        "budget_min": slots.get("budget_min"),
        "budget_max": slots.get("budget_max"),
    }

    retriever = AlgoliaRetriever()
    results = retriever.search(user_text, filters=filters, hits_per_page=settings.MAX_HITS)
    hits = results.get("hits", [])

    reranked = rerank(hits, slots, user_text, top_k=settings.RERANK_TOP_K)
    top_hits = reranked[:max(3, min(settings.RERANK_TOP_K, settings.RETURN_TOP_N*3))]

    from .generator import generate
    gen_out, used_fallback, conversational_response = generate(user_text, slots, top_hits, messages)
    print("the conversational response: ", conversational_response)
    print("the gen out: ", gen_out)
    print("the used fallback: ", used_fallback)

    if response_format == "text":
        return conversational_response

    recommendations = []
    for rec in gen_out.get("recommendations", [])[:req.top_n]:
        recommendations.append(Recommendation(
            title=rec.get("title"),
            price=rec.get("price"),
            url=rec.get("url"),
            score=0.0,
            reasons=rec.get("reasons", []),
            citations=rec.get("citations", [])
        ))

    clarifying = gen_out.get("clarifying_questions") or propose_questions(slots)

    debug = {
        "slots": slots,
        "filters": filters,
        "nbHits": results.get("nbHits"),
        "used_local_json": settings.USE_LOCAL_JSON,
        "index": settings.ALGOLIA_INDEX_NAME
    }

    return RecommendResponse(
        recommendations=recommendations,
        clarifying_questions=clarifying[:3],
        used_fallback_generator=used_fallback,
        debug=debug
    )