from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    ALGOLIA_APP_ID: Optional[str] = os.getenv("ALGOLIA_APP_ID")
    ALGOLIA_API_KEY: Optional[str] = os.getenv("ALGOLIA_API_KEY")
    ALGOLIA_INDEX_NAME: str = os.getenv("ALGOLIA_INDEX_NAME", "electronics")
    ALGOLIA_TIMEOUT: float = float(os.getenv("ALGOLIA_TIMEOUT", "6.0"))

    USE_LOCAL_JSON: bool = os.getenv("USE_LOCAL_JSON", "false").lower() in {"1", "true", "yes"}
    LOCAL_JSON_PATH: str = os.getenv("LOCAL_JSON_PATH", "data/bestbuy_seo.json")

    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")

    MAX_HITS: int = int(os.getenv("MAX_HITS", "24"))
    HITS_PER_PAGE: int = int(os.getenv("HITS_PER_PAGE", "24"))
    RERANK_TOP_K: int = int(os.getenv("RERANK_TOP_K", "10"))
    RETURN_TOP_N: int = int(os.getenv("RETURN_TOP_N", "5"))


settings = Settings()
