
from typing import List, Dict, Any
import math


def score_hit(hit: Dict[str, Any], slots: Dict[str, Any], query: str) -> float:
    # Heuristic scoring combining Algolia ranking info + slot alignment
    base = 0.0
    if "_rankingInfo" in hit:
        b = hit["_rankingInfo"].get("nbExactWords", 0) + hit["_rankingInfo"].get("typo", 0)
        base = 1 / (1 + b)
    elif "_score" in hit:
        base = min(1.0, hit["_score"] / 10.0)

    boost = 0.0
    title = (hit.get("title") or hit.get("name") or "").lower()
    cats = " ".join(hit.get("categories") or []).lower()

    if slots.get("device_type") == "laptop" and "laptop" in cats + " " + title:
        boost += 0.2
    if slots.get("device_type") == "phone" and ("phone" in cats or "iphone" in title or "android" in title):
        boost += 0.2
    if slots.get("os"):
        osv = (hit.get("os") or "").lower()
        if slots["os"].lower() in osv or slots["os"].lower() in title:
            boost += 0.2
    if slots.get("use_case") == "programming":
        if any(k in title for k in ["air","ultrabook","thin","light"]):
            boost += 0.1
        ram = hit.get("ram")
        try:
            if isinstance(ram, (int,float)) and ram >= 16:
                boost += 0.1
        except:
            pass
    if slots.get("use_case") == "social_media":
        cam = hit.get("camera") or title
        if any(k in str(cam).lower() for k in ["stabilization","4k","1080p","ois","pro camera","hdr"]):
            boost += 0.2

    price = hit.get("price")
    if price is not None:
        bmin = slots.get("budget_min")
        bmax = slots.get("budget_max")
        if bmin is not None and price < bmin: boost -= 0.3
        if bmax is not None and price > bmax: boost -= 0.3

    return max(0.0, min(1.0, base + boost))


def rerank(hits: List[Dict[str, Any]], slots: Dict[str, Any], query: str, top_k: int = 10) -> List[Dict[str, Any]]:
    scored = [(score_hit(h, slots, query), h) for h in hits]
    scored.sort(key=lambda x: x[0], reverse=True)
    out = []
    for s, h in scored[:top_k]:
        h["_advisorScore"] = s
        out.append(h)
    return out
