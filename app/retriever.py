import json, httpx
from typing import Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential

from .config import settings

ALGOLIA_HOST_TMPL = "https://{app_id}-dsn.algolia.net/1/indexes/{index}/query"


class AlgoliaRetriever:
    def __init__(self):
        self.app_id = settings.ALGOLIA_APP_ID
        self.api_key = settings.ALGOLIA_API_KEY
        self.index = settings.ALGOLIA_INDEX_NAME
        self.timeout = settings.ALGOLIA_TIMEOUT

    def _endpoint(self):
        return ALGOLIA_HOST_TMPL.format(app_id=self.app_id, index=self.index)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.2, min=0.2, max=2))
    def search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        hits_per_page: Optional[int] = None
    ) -> Dict[str, Any]:
        if settings.USE_LOCAL_JSON or not (self.app_id and self.api_key):
            return self._search_local(query, filters, hits_per_page or settings.HITS_PER_PAGE)

        headers = {
            "X-Algolia-Application-Id": self.app_id,
            "X-Algolia-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        params = {
            "query": query,
            "hitsPerPage": hits_per_page or settings.HITS_PER_PAGE,
            "attributesToRetrieve": [
                "name","title","price","brand","categories","image","url",
                "objectID","description","shortDescription","rating","weight",
                "os","ram","storage","camera","cpu","gpu"
            ],
            "getRankingInfo": True
        }
        if filters:
            filter_clauses = []
            numeric_filters = []
            if filters.get("brand"):
                filter_clauses.append(f'brand:"{filters["brand"]}"')
            if filters.get("os"):
                filter_clauses.append(f'os:"{filters["os"]}"')
            if filters.get("device_type"):
                filter_clauses.append(f'categories:"{filters["device_type"]}"')
            if filters.get("budget_min") is not None or filters.get("budget_max") is not None:
                mn = filters.get("budget_min", 0)
                mx = filters.get("budget_max", 10**9)
                numeric_filters.append(f"price>={mn}")
                numeric_filters.append(f"price<={mx}")
            if filter_clauses:
                params["filters"] = " AND ".join(filter_clauses)
            if numeric_filters:
                params["numericFilters"] = numeric_filters  # Now flat list

        url = self._endpoint()
        with httpx.Client(timeout=self.timeout) as client:
            r = client.post(url, json={"params": _encode_params(params)})
            r.raise_for_status()
            return r.json()

    def _search_local(
        self,
        query: str,
        filters: Optional[Dict[str, Any]],
        hits_per_page: int
    ) -> Dict[str, Any]:
        with open(settings.LOCAL_JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        query_l = query.lower()
        hits = []
        for item in data:
            text = " ".join([
                str(item.get(k, ""))
                for k in ["name","title","brand","categories","description","shortDescription"]
            ]).lower()
            score = 0
            for token in query_l.split():
                if token in text:
                    score += 1
            ok = True
            if filters:
                bmin = filters.get("budget_min")
                bmax = filters.get("budget_max")
                price = item.get("price")
                if price is not None:
                    if bmin is not None and price < bmin: ok = False
                    if bmax is not None and price > bmax: ok = False
            if ok and score > 0:
                hits.append({"_highlightResult": {}, **item, "_score": score})

        hits.sort(key=lambda x: x.get("_score", 0), reverse=True)
        return {"hits": hits[:hits_per_page], "nbHits": len(hits)}


def _encode_params(d: Dict[str, Any]) -> str:
    parts = []
    for k, v in d.items():
        if v is None:
            continue
        if isinstance(v, list) or isinstance(v, dict):
            from json import dumps
            parts.append(f"{k}={dumps(v)}")
        else:
            from urllib.parse import quote_plus
            parts.append(f"{k}={quote_plus(str(v))}")
    return "&".join(parts)
