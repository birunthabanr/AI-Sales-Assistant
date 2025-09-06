import requests
import json
import re

# Config
MCP_SERVER_URL = "http://localhost:3000"   # FastAPI MCP server
OLLAMA_API = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3"


# Extract JSON from text
def extract_json(text: str):
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            return None
    return None


# Ask LLM for intent
def query_llm_for_intent(user_prompt: str):
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
    "num_people": int
  }}
}}

Rules:
- Use "get_customers" if the user asks to see customers.
- Use "create_booking" if the user wants to book a room.
- Otherwise, use "chat".
- Always return valid JSON. Do not add extra text.
"""
    try:
        with requests.post(
            OLLAMA_API,
            json={"model": OLLAMA_MODEL, "prompt": system_prompt, "stream": True},
            stream=True,
            timeout=30
        ) as resp:
            resp.raise_for_status()

            chunks = []
            for line in resp.iter_lines():
                if not line:
                    continue
                decoded = line.decode("utf-8")
                
                try:
                    data = json.loads(decoded)
                    if "response" in data:
                        chunks.append(data["response"])
                except json.JSONDecodeError:
                    continue

            raw = "".join(chunks).strip()

    except Exception as e:
        print("❌ Ollama call failed:", e)
        return {"action": "chat", "args": {"response": f"Ollama error: {e}"}}

    # Try parsing accumulated response
    parsed = extract_json(raw)
    if not parsed:
        parsed = {"action": "chat", "args": {"response": raw}}

    return parsed


def handle_prompt(user_prompt: str):
    print("this is handle_prompt()")
    """Process a single user prompt and return structured response."""
    intent = query_llm_for_intent(user_prompt)
    action = intent.get("action", "chat")
    args = intent.get("args", {})

    if action == "get_customers":
        res = requests.get(f"{MCP_SERVER_URL}/customers")
        return {"action": "get_customers", "result": res.json()}

    elif action == "create_booking":
        booking_data = {
            "customer_id": args.get("customer_id", 1),
            "room_no": args.get("room_no", 101),
            "start_date": args.get("start_date", "2025-09-10"),
            "end_date": args.get("end_date", "2025-09-12"),
            "num_people": args.get("num_people", 2),
            "price": args.get("price", 500)
        }
        res = requests.post(f"{MCP_SERVER_URL}/bookings", json=booking_data)
        return {"action": "create_booking", "result": res.json()}

    else:
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

        raw = "".join(reply_chunks).strip()

    parsed = extract_json(raw)
    if not parsed:
        parsed = {"action": "chat", "args": {"response": raw}}

    return parsed


# Main loop
def run_client():
    print("Welcome to Hotel Assistant 🏨 (type 'quit' to exit)")
    while True:
        user_prompt = input("\nyou: ")
        if user_prompt.lower() in ["quit", "exit"]:
            break

        intent = query_llm_for_intent(user_prompt)
        action = intent.get("action", "chat")
        args = intent.get("args", {})

        # Handle actions
        if action == "get_customers":
            try:
                res = requests.get(f"{MCP_SERVER_URL}/customers")
                res.raise_for_status()
                print("👉 Customers:", res.json())
            except requests.exceptions.RequestException as e:
                print("❌ Error fetching customers:", str(e))

        elif action == "create_booking":
            required_fields = ["customer_id", "room_no", "start_date", "end_date", "num_people"]
            missing_fields = [field for field in required_fields if args.get(field) is None]

            # Prompt user for missing fields
            for field in missing_fields:
                value = input(f"Please enter {field.replace('_', ' ')}: ")
                if field in ["customer_id", "room_no", "num_people"]:
                    try:
                        value = int(value)
                    except ValueError:
                        print(f"Invalid input for {field}, using default 1.")
                        value = 1
                args[field] = value

            booking_data = {
                "customer_id": args["customer_id"],
                "room_no": args["room_no"],
                "start_date": args["start_date"],
                "end_date": args["end_date"],
                "num_people": args["num_people"]
            }

            try:
                res = requests.post(f"{MCP_SERVER_URL}/bookings", json=booking_data)
                res.raise_for_status()
                print("👉 Booking Result:", res.json())
            except Exception as e:
                print("❌ Error creating booking:", str(e))

        else:  # Just chat normally with LLM
            assistant_prompt = f"""
You are a helpful hotel assistant. Answer the user's question or help with hotel-related tasks.

User: {user_prompt}
"""
            chat_resp = requests.post(OLLAMA_API, json={
                "model": OLLAMA_MODEL,
                "prompt": assistant_prompt,
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
