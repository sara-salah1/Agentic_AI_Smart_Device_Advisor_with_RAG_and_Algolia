import json
import logging
from typing import List, Dict, Any, Tuple
from openai import OpenAI
from openai import OpenAIError

from .config import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = OpenAI(api_key=settings.OPENAI_API_KEY)


def generate(user_text: str, slots: Dict[str, Any], top_hits: List[Dict[str, Any]], messages: List[Dict[str, str]] = None) -> Tuple[Dict[str, Any], bool, str]:
    """
    Use OpenAI LLM to generate conversational response based on query, slots, and retrieved hits.
    Custom prompt logic for RAG, education, and clarifying questions.
    Returns: gen_out dict, used_fallback (False if LLM succeeds), conversational_response str
    """
    if not settings.OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY not set in environment.")
        raise ValueError("OPENAI_API_KEY not set in environment.")

    # Trim conversation history to avoid token limit (e.g., keep last 5 messages)
    conversation_history = ""
    if messages:
        messages = messages[-5:]  # Limit to last 5 messages to avoid token overflow
        conversation_history = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
        logger.info(f"Conversation history trimmed to {len(messages)} messages")

    # Simplify hits for prompt (avoid overwhelming token limit)
    simplified_hits = []
    for hit in top_hits[:10]:
        simplified_hits.append({
            "title": hit.get("title") or hit.get("name") or "Unknown Product",
            "price": hit.get("price"),
            "url": hit.get("url"),
            "brand": hit.get("brand"),
            "os": hit.get("os"),
            "ram": hit.get("ram"),
            "camera": hit.get("camera"),
            "description": hit.get("shortDescription") or hit.get("description") or "",
            "score": hit.get("_advisorScore", 0.0)
        })

    prompt = f"""
You are a helpful AI advisor recommending electronic devices based on user needs.
User query: {user_text}
Extracted slots: {json.dumps(slots, indent=2)}
Conversation history (if any): {conversation_history}

Available products from search (top relevant hits):
{json.dumps(simplified_hits, indent=2)}

Instructions:
- If the user asks for an explanation (e.g., 'what is RAM?'), explain the term simply in 1-2 sentences, then relate it to device recommendations (e.g., suggest minimum specs like 8GB RAM for daily use).
- Recommend 3-5 top products that best match the slots and query. For each:
  - Provide title, price, url.
  - List 2-3 reasons why it matches, citing specific attributes (e.g., 'High RAM: 16GB' or 'Great camera: 48MP with OIS').
- Be conversational, engaging, and adapt to the conversation history (e.g., refine based on prior user inputs).
- If information is missing (e.g., no OS preference), ask 1-3 relevant clarifying questions (e.g., 'Do you prefer Windows or macOS?').
- If no good matches, suggest alternatives or ask for more details.
- Output in JSON: {{"recommendations": [{{"title": str, "price": float, "url": str, "reasons": [str], "citations": [str]}}], "clarifying_questions": [str]}}
- Follow with a conversational response (after a separator '---') incorporating the recommendations and questions in natural language.
- Do not use hardcoded responses; base everything on the provided data.
"""

    if len(prompt) > 12000:
        logger.warning("Prompt too long, truncating hits")
        simplified_hits = simplified_hits[:5]
        prompt = prompt.replace(json.dumps(simplified_hits, indent=2), json.dumps(simplified_hits[:5], indent=2))

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a device recommendation expert."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        llm_output = response.choices[0].message.content.strip()
        logger.info("LLM response received successfully")

    except OpenAIError as e:
        logger.error(f"OpenAI API error: {str(e)}")
        gen_out = {
            "recommendations": [],
            "clarifying_questions": ["Could you clarify your requirements or try again later?"]
        }
        conversational_response = f"Sorry, I ran into an issue connecting to the recommendation engine. Could you clarify your requirements, like {' or '.join(gen_out['clarifying_questions'])}"
        return gen_out, True, conversational_response

    # Parse LLM output
    try:
        if "```json" in llm_output and "```" in llm_output:
            json_part = llm_output.split("```json")[1].split("```")[0].strip()
            conversational_response = llm_output.split("---")[1].strip() if "---" in llm_output else ""
        else:
            json_part = llm_output
            conversational_response = ""
        gen_out = json.loads(json_part)
        logger.info("LLM JSON output parsed successfully")

        # Validate gen_out structure
        if not isinstance(gen_out, dict) or "recommendations" not in gen_out or "clarifying_questions" not in gen_out:
            raise ValueError("Invalid JSON structure from LLM")

        # Generate conversational response if not provided by LLM
        if not conversational_response:
            conv = f"Got it! Based on your request for '{user_text}', here are my recommendations:\n"
            for rec in gen_out["recommendations"][:5]:
                price = rec.get('price', 'N/A')
                conv += f"- {rec['title']} (${price}): {'; '.join(rec.get('reasons', []))}\n"
            if gen_out["clarifying_questions"]:
                conv += "To make these suggestions even better: " + " ".join(gen_out["clarifying_questions"][:3])
            conversational_response = conv

        return gen_out, False, conversational_response

    except (json.JSONDecodeError, ValueError, IndexError) as e:
        logger.error(f"Error parsing LLM output: {str(e)}")
        gen_out = {
            "recommendations": [],
            "clarifying_questions": ["Could you provide more details to help me find the right device?"]
        }
        conversational_response = f"Sorry, I couldn't process the recommendations properly for '{user_text}'. Could you provide more details, like {' or '.join(gen_out['clarifying_questions'])}"
        return gen_out, True, conversational_response
