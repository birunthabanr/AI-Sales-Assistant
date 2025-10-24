import asyncio
import json
import re
import requests
from fastmcp import Client
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse


app = FastAPI(title="Chat Backend")

# intents = [
#     "cancel_order", "change_order", "change_shipping_address", "check_cancellation_fee",
#     "check_invoice", "check_payment_methods", "check_refund_policy", "complaint",
#     "contact_customer_service", "contact_human_agent", "create_account", "delete_account",
#     "delivery_options", "delivery_period", "edit_account", "get_invoice", "get_refund",
#     "newsletter_subscription", "payment_issue", "place_order", "recover_password",
#     "registration_problems", "review", "set_up_shipping_address", "switch_account",
#     "track_order", "track_refund"
# ]

# Allow frontend (React) to call the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ In production, replace with your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Config
OLLAMA_API = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3"
FASTMCP_SERVER_URL = "http://localhost:8000/sse"


async def extract_json(text: str):
    """Try to extract the first {...} JSON object from text."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            return None
    return None


async def _ollama_stream(prompt: str) -> str:
    """
    Call Ollama /api/generate with streaming and return the concatenated response text.
    """
    try:
        with requests.post(
            OLLAMA_API,
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": True},
            stream=True,
            timeout=None,
        ) as resp:
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
                    # ignore partial/heartbeat lines
                    continue
            return "".join(chunks).strip()
    except Exception as e:
        return f"Error chatting with LLM: {e}"


async def chat_with_llm(user_prompt: str):
    """Simple chat with LLM without MCP tools."""
    return await _ollama_stream(user_prompt)


async def query_llm_for_intent(user_prompt: str, available_tools: list):
    """
    Ask LLM to pick a tool or 'chat'.
    """
    if not available_tools:
        return {"tool_name": "chat", "arguments": {}}

    tool_names = [tool.name for tool in available_tools]
    tool_descriptions = "\n".join([f"- {tool.name}: {tool.description}" for tool in available_tools])

    system_prompt = f"""
You are an intent parser for a multidomain customer assistant using MCP tools.

The assistant supports multiple domains such as customer support, sales, billing, technical support, account management, product information, returns/exchanges, and scheduling.

Available MCP tools:
{tool_descriptions}

User request: "{user_prompt}"

Respond ONLY in JSON with this exact format:
{{
  "tool_name": "TOOL_NAME" | "chat",
  "arguments": {{}}
}}

Rules:
- Choose a single MCP tool from: {', '.join(tool_names)}
- Use "chat" when a general conversational reply or a clarifying question is needed.
- Return strictly valid JSON (RFC 8259) with no extra text before or after.
- Do NOT include comments, explanatory text, or trailing commas.
- Use null (without quotes) for missing values.
- Match argument names and expected types to the tool's schema; if unsure, include fields with null.
- If multiple intents or domains are present, pick the primary intent/tool; if required information is missing, prefer "chat" to request clarification.
- Keep the "arguments" object minimal and relevant.

Always ensure the output can be parsed by json.loads in Python.
"""

    raw = await _ollama_stream(system_prompt)
    parsed = await extract_json(raw)
    if not parsed:
        print("⚠️ Failed to parse JSON intent, defaulting to chat\n")
        parsed = {"tool_name": "chat", "arguments": {}}
    return parsed


async def _stringify_tool_result(result) -> str:
    """Convert FastMCP tool call result to string for feeding back into LLM."""
    if hasattr(result, "text") and result.text:
        return str(result.text)
    if hasattr(result, "content") and result.content:
        return str(result.content)
    try:
        return json.dumps(result, ensure_ascii=False, default=str)
    except Exception:
        return str(result)


async def llm_followup(user_prompt: str, tool_name: str, arguments: dict, tool_result_text: str) -> str:
    """Feed tool output back into the LLM for a natural reply."""
    followup_prompt = f"""
The user asked: {user_prompt}

I used this MCP tool:
- name: {tool_name}
- arguments: {json.dumps(arguments, ensure_ascii=False)}

The tool returned this data (verbatim):
{tool_result_text}

Now, write a clear, concise answer to the user based on the tool result.
If the tool result is a list or JSON, summarize it helpfully.
If next steps are obvious (e.g., ask for missing fields), mention them briefly.
"""
    return await _ollama_stream(followup_prompt)


@app.post("/chat")
async def run_client(request: Request):
    body = await request.json()
    user_prompt = body.get("prompt", "").strip()

    if not user_prompt:
        return JSONResponse({"action": "chat", "result": "⚠️ Empty message"})
    try:
        # Connect to FastMCP server
        client = Client(FASTMCP_SERVER_URL)

        async with client:
            tools = await client.list_tools()
            available_tools = tools if tools else []

            while True:
                # 1) Ask LLM for intent
                intent = await query_llm_for_intent(user_prompt, available_tools)

                tool_name = intent.get("tool_name", "chat")
                arguments = intent.get("arguments", {}) or {}

                # 2) Normal chat if no tool
                if tool_name == "chat" or not available_tools:
                    reply = await chat_with_llm(user_prompt)
                    return JSONResponse({"action": "chat", "result": reply})

                # 3) Tool call path
                tool_exists = any(tool.name.lower() == tool_name.lower() for tool in available_tools)
                if not tool_exists:
                    reply = await chat_with_llm(user_prompt)
                    return JSONResponse({"action": "chat", "result": reply})

                try:
                    result = await client.call_tool(tool_name, arguments)
                    tool_result_text = await _stringify_tool_result(result)

                    reply = await llm_followup(user_prompt, tool_name, arguments, tool_result_text)
                    return JSONResponse({"action": tool_name, "result": reply})

                except Exception as e:
                    reply = await chat_with_llm(user_prompt)
                    return JSONResponse({"action": "chat", "result": reply})

    except Exception as e:
        return JSONResponse({
            "action": "error",
            "result": f"❌ Failed to connect to FastMCP server: {e}"
        })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
