import asyncio
import json
import re
import requests
from fastmcp import Client

# Config
OLLAMA_API = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "deepseek-r1:7b"

# Your FastMCP server SSE endpoint
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

def query_llm_for_intent(user_prompt: str, available_tools: list):
    """Send the user prompt to Ollama and get structured JSON response."""
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
"""

    try:
        with requests.post(OLLAMA_API, json={
            "model": OLLAMA_MODEL,
            "prompt": system_prompt,
            "stream": True
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

        parsed = extract_json(raw)
        if not parsed:
            parsed = {"tool_name": "chat", "arguments": {}}
        
        return parsed
        
    except Exception as e:
        print(f"Error querying LLM: {e}")
        return {"tool_name": "chat", "arguments": {}}

def chat_with_llm(user_prompt: str):
    """Simple chat with LLM without MCP tools."""
    try:
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

        return "".join(reply_chunks).strip()
    except Exception as e:
        return f"Error chatting with LLM: {e}"

async def run_client():
    print("Welcome to Hotel Assistant 🏨 with FastMCP SSE (type 'quit' to exit)")
    
    try:
        # Connect to FastMCP server via SSE
        client = Client(FASTMCP_SERVER_URL)
        
        async with client:
            print("✅ Connected to FastMCP server!")
            
            # List available tools
            tools = await client.list_tools()
            available_tools = tools if tools else []
            
            print(f"Found {len(available_tools)} tools:")
            for tool in available_tools:
                print(f"  - {tool.name}: {tool.description}")
            
            while True:
                user_prompt = input("\nYou: ")
                if user_prompt.lower() in ["quit", "exit"]:
                    break

                # Get intent from LLM
                intent = query_llm_for_intent(user_prompt, available_tools)
                tool_name = intent.get("tool_name", "chat")
                arguments = intent.get("arguments", {})

                # Handle MCP tool calls or chat
                if tool_name == "chat" or not available_tools:
                    reply = chat_with_llm(user_prompt)
                    print(f"🤖 LLM: {reply}")
                else:
                    # Check if tool exists
                    tool_exists = any(tool.name == tool_name for tool in available_tools)
                    
                    if not tool_exists:
                        print(f"⚠️ Tool '{tool_name}' not found. Available: {[t.name for t in available_tools]}")
                        reply = chat_with_llm(user_prompt)
                        print(f"🤖 LLM (fallback): {reply}")
                        continue
                    
                    print(f"🔧 Calling MCP tool: {tool_name} with args: {arguments}")
                    try:
                        result = await client.call_tool(tool_name, arguments)
                        
                        # Format the result for display
                        if hasattr(result, 'text'):
                            print(f"📋 Result: {result.text}")
                        elif hasattr(result, 'content'):
                            print(f"📋 Result: {result.content}")
                        else:
                            print(f"📋 Result: {result}")
                            
                    except Exception as e:
                        print(f"❌ Error calling MCP tool: {e}")
                        # Fallback to chat
                        reply = chat_with_llm(user_prompt)
                        print(f"🤖 LLM (fallback): {reply}")

    except Exception as e:
        print(f"❌ Failed to connect to FastMCP server: {e}")
        print("Troubleshooting steps:")
        print(f"1. Make sure your server is running: python mcp_server_new.py")
        print(f"2. Check that your server is accessible at: {FASTMCP_SERVER_URL}")
        print("3. Verify your server starts without errors")

if __name__ == "__main__":
    asyncio.run(run_client())
