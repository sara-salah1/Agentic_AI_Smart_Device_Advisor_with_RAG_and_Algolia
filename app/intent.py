import re
from typing import Dict, Union, List


def extract_slots(text: str) -> Dict[str, Union[str, float, None]]:
    """
    Lightweight rule-based intent/slot extraction.
    Returns dict fields that help build Algolia filters & boosts, plus educational query detection.
    """
    t = text.lower()

    education_query = None
    education_patterns = [
        r"what is ([a-zA-Z\s]+)\??",
        r"explain ([a-zA-Z\s]+)\??",
    ]
    for pattern in education_patterns:
        m = re.search(pattern, t)
        if m:
            education_query = m.group(1).strip()  
            break

    use_case = None
    if any(k in t for k in ["programming", "developer", "coding", "software dev"]):
        use_case = "programming"
    elif any(k in t for k in ["gaming", "gamer"]):
        use_case = "gaming"
    elif any(k in t for k in ["daily use", "everyday", "browsing", "office", "word", "excel"]):
        use_case = "everyday"
    elif "social media" in t or "tiktok" in t or "instagram" in t:
        use_case = "social_media"

    os_pref = None
    if "windows" in t:
        os_pref = "Windows"
    elif "mac" in t or "macos" in t or "macbook" in t or "ios" in t:
        os_pref = "Apple"
    elif "android" in t:
        os_pref = "Android"
    elif "chrome" in t or "chromebook" in t:
        os_pref = "ChromeOS"

    weight_pref = None
    if "lightweight" in t or "portable" in t or "thin" in t:
        weight_pref = "light"

    camera_pref = None
    if "camera" in t:
        camera_pref = "great_camera"
    if "video" in t:
        camera_pref = "video"

    ram = None
    m = re.search(r'(\d+)\s*gb\s*ram', t)
    if m:
        try:
            ram = int(m.group(1))
        except:
            pass

    budget_min = None
    budget_max = None
    m = re.search(r'under\s*\$?\s*(\d+)', t)
    if m:
        budget_max = float(m.group(1))
    m = re.search(r'between\s*\$?\s*(\d+)\s*and\s*\$?\s*(\d+)', t)
    if m:
        budget_min = float(m.group(1))
        budget_max = float(m.group(2))

    device_type = None
    if any(x in t for x in ["laptop", "notebook", "ultrabook", "macbook"]):
        device_type = "laptop"
    elif any(x in t for x in ["phone", "smartphone", "iphone", "android"]):
        device_type = "phone"
    elif any(x in t for x in ["tablet", "ipad", "galaxy tab"]):
        device_type = "tablet"

    return {
        "use_case": use_case,
        "os": os_pref,
        "weight": weight_pref,
        "camera": camera_pref,
        "ram": ram,
        "budget_min": budget_min,
        "budget_max": budget_max,
        "device_type": device_type,
        "education_query": education_query
    }


def propose_questions(slots: dict) -> List[str]:
    qs = []
    if slots.get("device_type") is None:
        qs.append("Are you looking for a laptop, phone, or tablet?")
    if slots.get("device_type") in {"laptop", "tablet"} and slots.get("os") is None:
        qs.append("Do you prefer Windows, macOS, or ChromeOS?")
    if slots.get("device_type") == "phone" and slots.get("os") is None:
        qs.append("Do you prefer iOS or Android?")
    if slots.get("device_type") == "laptop" and slots.get("use_case") == "programming":
        qs.append("Do you prioritize portability (lightweight) or screen size/performance?")
    if slots.get("device_type") == "phone" and slots.get("use_case") == "social_media":
        qs.append("Is video quality or photo sharpness more important?")
    if slots.get("budget_min") is None and slots.get("budget_max") is None:
        qs.append("Do you have a target budget range?")
    return qs
