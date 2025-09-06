import asyncio
import json
import re
import requests
from fastmcp import Client

# Config
OLLAMA_API = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3"
FASTMCP_SERVER_URL = "http://localhost:8000/sse"


def extract_json(text: str):
    """Try to extract the first {...} JSON object from text."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            return None
    return None


def _ollama_stream(prompt: str) -> str:
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


def chat_with_llm(user_prompt: str):
    """Simple chat with LLM without MCP tools."""
    return _ollama_stream(user_prompt)


def query_llm_for_intent(user_prompt: str, available_tools: list):
    """
    Ask LLM to pick a tool or 'chat'.
    """
    if not available_tools:
        return {"tool_name": "chat", "arguments": {}}

    tool_names = [tool.name for tool in available_tools]
    tool_descriptions = "\n".join([f"- {tool.name}: {tool.description}" for tool in available_tools])

    system_prompt = f"""
You are an intent parser for a hotel booking assistant using MCP tools.

Available MCP tools:
{tool_descriptions}

User request: "{user_prompt}"

Respond ONLY in JSON with this format:
{{
  "tool_name": "TOOL_NAME" | "chat",
  "arguments": {{
    // tool-specific arguments based on the tool's schema
  }}
}}

Rules:
- Choose the most appropriate MCP tool from: {', '.join(tool_names)}
- Use "chat" if no MCP tool is needed for a general conversation
- Always return valid JSON. Do not add extra text.
- Match arguments to the specific tool's expected parameters
- Respond ONLY in STRICT JSON (RFC 8259).
- Do NOT include comments like // or extra text.
- Use null (without quotes) for missing values, not "null".
- Always return valid JSON that can be parsed by json.loads in Python.

"""

    raw = _ollama_stream(system_prompt)
    print(f"🔎 Raw LLM intent output:\n{raw}\n")   # DEBUG: raw LLM output

    parsed = extract_json(raw)
    if not parsed:
        print("⚠️ Failed to parse JSON intent, defaulting to chat\n")  # DEBUG
        parsed = {"tool_name": "chat", "arguments": {}}
    return parsed


def _stringify_tool_result(result) -> str:
    """Convert FastMCP tool call result to string for feeding back into LLM."""
    if hasattr(result, "text") and result.text:
        return str(result.text)
    if hasattr(result, "content") and result.content:
        return str(result.content)
    try:
        return json.dumps(result, ensure_ascii=False, default=str)
    except Exception:
        return str(result)


def llm_followup(user_prompt: str, tool_name: str, arguments: dict, tool_result_text: str) -> str:
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
    print(f"🔄 Sending followup prompt to LLM:\n{followup_prompt}\n")  # DEBUG
    return _ollama_stream(followup_prompt)


async def run_client():
    print("Welcome to Hotel Assistant 🏨 with FastMCP SSE (type 'quit' to exit)")
    try:
        # Connect to FastMCP server
        client = Client(FASTMCP_SERVER_URL)

        async with client:
            print("✅ Connected to FastMCP server!")
            tools = await client.list_tools()
            available_tools = tools if tools else []

            print(f"Found {len(available_tools)} tools:")
            for tool in available_tools:
                print(f"  - {tool.name}: {tool.description}")

            while True:
                user_prompt = input("\nYou: ")
                if user_prompt.lower() in ["quit", "exit"]:
                    break

                # 1) Ask LLM for intent
                intent = query_llm_for_intent(user_prompt, available_tools)
                print(f"📦 Parsed intent: {intent}\n")   # DEBUG

                tool_name = intent.get("tool_name", "chat")
                arguments = intent.get("arguments", {}) or {}

                # 2) Normal chat if no tool
                if tool_name == "chat" or not available_tools:
                    print("💬 Falling back to direct chat\n")   # DEBUG
                    reply = chat_with_llm(user_prompt)
                    print(f"🤖 LLM: {reply}")
                    continue

                # 3) Tool call path
                tool_exists = any(tool.name.lower() == tool_name.lower() for tool in available_tools)
                if not tool_exists:
                    print(f"⚠️ Tool '{tool_name}' not found. Available: {[t.name for t in available_tools]}\n")
                    reply = chat_with_llm(user_prompt)
                    print(f"🤖 LLM (fallback): {reply}")
                    continue

                print(f"🔧 Calling MCP tool: {tool_name} with args: {arguments}\n")
                try:
                    result = await client.call_tool(tool_name, arguments)

                    # Show raw tool result
                    if hasattr(result, "text"):
                        print(f"📋 Raw MCP Result.text: {result.text}\n")
                    elif hasattr(result, "content"):
                        print(f"📋 Raw MCP Result.content: {result.content}\n")
                    else:
                        print(f"📋 Raw MCP Result: {result}\n")

                    # Feed back into LLM for natural reply
                    tool_result_text = _stringify_tool_result(result)
                    reply = llm_followup(user_prompt, tool_name, arguments, tool_result_text)
                    print(f"🤖 LLM: {reply}")

                except Exception as e:
                    print(f"❌ Error calling MCP tool: {e}\n")
                    reply = chat_with_llm(user_prompt)
                    print(f"🤖 LLM (fallback): {reply}")

    except Exception as e:
        print(f"❌ Failed to connect to FastMCP server: {e}\n")
        print("Troubleshooting steps:")
        print("1. Make sure your server is running")
        print(f"2. Check that your server is accessible at: {FASTMCP_SERVER_URL}")
        print("3. Verify your server starts without errors")


if __name__ == "__main__":
    asyncio.run(run_client())
