
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastmcp import Client
from mcp_client_new_2 import (
    query_llm_for_intent,
    chat_with_llm,
    llm_followup,
    _stringify_tool_result,
    FASTMCP_SERVER_URL,
)

app = FastAPI(title="Chat Backend")

# Allow frontend (React) to call the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ In production, replace with your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/chat")
async def chat_endpoint(request: Request):
    """
    Main chat endpoint.
    - Accepts user prompt from frontend
    - Uses MCP client to query tools or fallback to chat
    - Returns structured JSON response
    """
    print("📩 Chat function called...")

    # Get prompt from request body
    body = await request.json()
    print(body)
    user_prompt = body.get("prompt", "").strip()
    print(user_prompt)

    if not user_prompt:
        return JSONResponse({"action": "chat", "result": "⚠️ Empty message"})

    try:
        # Connect to MCP server
        async with Client(FASTMCP_SERVER_URL) as client:
            # Get available tools from MCP server
            tools = await client.list_tools()
            available_tools = tools or []

            # Decide intent (chat vs. tool call)
            intent = await query_llm_for_intent(user_prompt, available_tools)
            print(f"🎯 Intent: {intent}")

            tool_name = intent.get("tool_name", "chat")
            arguments = intent.get("arguments", {}) or {}

            # Case 1: Simple chat
            if tool_name == "chat" or not available_tools:
                reply = await chat_with_llm(user_prompt)  # ✅ async call
                return JSONResponse({"action": "chat", "result": reply})

            # Case 2: Tool execution
            tool_exists = any(tool.name.lower() == tool_name.lower() for tool in available_tools)
            if not tool_exists:
                reply = await chat_with_llm(user_prompt)  # ✅ async call
                return JSONResponse({"action": "chat", "result": reply})

            # Call the MCP tool
            result = await client.call_tool(tool_name, arguments)
            tool_result_text = _stringify_tool_result(result)

            # LLM follow-up after tool result
            reply = await llm_followup(user_prompt, tool_name, arguments, tool_result_text)

            return JSONResponse({"action": "tool", "result": reply})

    except Exception as e:
        error_message = f"❌ Error: {str(e)}"
        print(error_message)
        return JSONResponse({"action": "chat", "result": error_message})
