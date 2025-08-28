import requests
import json
import re


# Config
MCP_SERVER_URL = "http://localhost:3000"   # Flask MCP server
OLLAMA_API = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3"  


# Extract JSON from text
def extract_json(text: str):
    """Try to extract the first {...} JSON object from text."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            return None
    return None


# Ask LLM for intent
def query_llm_for_intent(user_prompt: str):
    """
    Send the user prompt to Ollama and force it to return structured JSON
    indicating which action to take. Handles streaming JSON lines.
    """
    system_prompt = f"""
You are an intent parser for a hotel booking assistant.

User request: "{user_prompt}"

Respond ONLY in JSON with this format:
{{
  "action": "get_customers" | "create_booking" | "chat",
  "args": {{
    "customer_id": int,
    "room_no": int,
    "start_date": "YYYY-MM-DD",
    "end_date": "YYYY-MM-DD",
    "num_people": int,
    "price": float
  }}
}}

Rules:
- Use "get_customers" if the user asks to see customers.
- Use "create_booking" if the user wants to book a room.
- Otherwise, use "chat".
- Always return valid JSON. Do not add extra text.
"""

    with requests.post(OLLAMA_API, json={
        "model": OLLAMA_MODEL,
        "prompt": system_prompt,
        "stream": True   # ensure streaming mode
    }, stream=True) as resp:

        resp.raise_for_status()
        chunks = []
        for line in resp.iter_lines():
            if not line:
                continue
            try:
                data = json.loads(line.decode("utf-8"))
                if "response" in data:
                    chunks.append(data["response"])
            except json.JSONDecodeError:
                continue

        raw = "".join(chunks).strip()

    # Try parsing final accumulated string as JSON
    parsed = extract_json(raw)
    if not parsed:
        parsed = {"action": "chat", "args": {"response": raw}}

    return parsed


# Main loop
def run_client():
    print("Welcome to Hotel Assistant 🏨 (type 'quit' to exit)")
    while True:
        user_prompt = input("\nYou: ")
        if user_prompt.lower() in ["quit", "exit"]:
            break

        intent = query_llm_for_intent(user_prompt)
        action = intent.get("action", "chat")
        args = intent.get("args", {})

        # Handle actions
        if action == "get_customers":
            res = requests.get(f"{MCP_SERVER_URL}/customers")
            print("👉 Customers:", res.json())

        elif action == "create_booking":
            # fallback defaults if args are incomplete
            booking_data = {
                "customer_id": args.get("customer_id", 1),
                "room_no": args.get("room_no", 101),
                "start_date": args.get("start_date", "2025-09-10"),
                "end_date": args.get("end_date", "2025-09-12"),
                "num_people": args.get("num_people", 2),
                "price": args.get("price", 500)
            }
            res = requests.post(f"{MCP_SERVER_URL}/bookings", json=booking_data)
            print("👉 Booking Result:", res.json())

        else:  # Just chat normally with LLM
            chat_resp = requests.post(OLLAMA_API, json={
                "model": OLLAMA_MODEL,
                "prompt": user_prompt,
                "stream": True
            }, stream=True)

            reply_chunks = []
            for line in chat_resp.iter_lines():
                if not line:
                    continue
                try:
                    data = json.loads(line.decode("utf-8"))
                    if "response" in data:
                        reply_chunks.append(data["response"])
                except json.JSONDecodeError:
                    continue

            reply = "".join(reply_chunks).strip()
            print(f"LLM: {reply}")


if __name__ == "__main__":
    run_client()
