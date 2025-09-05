import asyncio
import json
import re
import requests
from typing import TypedDict, List, Dict, Any
from fastmcp import Client
from langgraph.graph import StateGraph, START, END
from langgraph import Command

# Config
OLLAMA_API = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.1"
FASTMCP_SERVER_URL = "http://localhost:8000/sse"

# --- Enhanced State Definition ---
class JointBERTSlotState(TypedDict):
    user_input: str
    intent: str
    slots: Dict[str, Any]
    missing_slots: List[str]
    slots_complete: bool
    available_tools: List[Any]
    tool_name: str
    tool_arguments: Dict[str, Any]
    tool_result: Any
    final_response: str
    needs_user_input: bool

# --- Intent to required slots mapping ---
intent_to_required_slots = {
    "BookRestaurant": ["restaurant", "time"],
    "AddToPlaylist": ["song_name", "playlist_name"],
    "GetWeather": ["location"],
    "PlayMusic": ["song_name"],
    "RateBook": ["book_name", "rating"],
    "SearchCreativeWork": ["work_name"],
    "SearchScreeningEvent": ["event_name"],
    "CalculateMath": [],  # No required slots for math
    "HotelBooking": ["hotel_name", "checkin_date", "checkout_date"],
    "UNK": []
}

def extract_json(text: str):
    """Try to extract the first {...} JSON object from text."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            return None
    return None

def query_llm(prompt: str) -> str:
    """Query Ollama LLM and return the complete response."""
    try:
        with requests.post(OLLAMA_API, json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
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
            
            return "".join(chunks).strip()
        
    except Exception as e:
        print(f"Error querying LLM: {e}")
        return ""

def predict_intent_and_slots(user_input: str) -> Dict[str, Any]:
    """Enhanced JointBERT-like prediction using Llama for intent and slot extraction."""
    
    prompt = f"""
You are an expert intent classifier and slot extractor for a multi-domain assistant.

User input: "{user_input}"

Extract the intent and slots from this user input. Return ONLY a JSON object in this exact format:
{{
  "intent": "INTENT_NAME",
  "slots": {{
    "slot_name": "slot_value"
  }}
}}

Available intents and their slots:
- BookRestaurant: restaurant, time
- HotelBooking: hotel_name, checkin_date, checkout_date
- GetWeather: location
- CalculateMath: expression
- PlayMusic: song_name
- AddToPlaylist: song_name, playlist_name
- RateBook: book_name, rating
- SearchCreativeWork: work_name
- SearchScreeningEvent: event_name
- UNK: (no specific slots)

Rules:
1. Choose the most specific intent that matches the user's request
2. Extract all available slot values from the user input
3. Only include slots that have clear values in the input
4. Use UNK for unclear requests
5. Return ONLY valid JSON, no extra text

Examples:
- "Book a table at Mario's for 7pm" → {{"intent": "BookRestaurant", "slots": {{"restaurant": "Mario's", "time": "7pm"}}}}
- "What's the weather like?" → {{"intent": "GetWeather", "slots": {{}}}}
- "Calculate 15 + 25" → {{"intent": "CalculateMath", "slots": {{"expression": "15 + 25"}}}}
"""

    response = query_llm(prompt)
    parsed = extract_json(response)
    
    if not parsed or "intent" not in parsed:
        return {"intent": "UNK", "slots": {}}
    
    return {
        "intent": parsed.get("intent", "UNK"),
        "slots": parsed.get("slots", {})
    }

def query_llm_for_tool_selection(user_input: str, intent: str, slots: Dict[str, Any], available_tools: List[Any]) -> Dict[str, Any]:
    """Select appropriate MCP tool based on intent and slots."""
    if not available_tools:
        return {"tool_name": "chat", "arguments": {}}
    
    tool_names = [tool.name for tool in available_tools]
    tool_descriptions = "\n".join([f"- {tool.name}: {tool.description}" for tool in available_tools])
    
    prompt = f"""
You are a tool selector for a multi-domain assistant.

User input: "{user_input}"
Detected intent: {intent}
Extracted slots: {json.dumps(slots)}

Available MCP tools:
{tool_descriptions}

Based on the intent and slots, select the most appropriate tool and generate arguments.
Return ONLY a JSON object in this format:
{{
  "tool_name": "TOOL_NAME" | "chat",
  "arguments": {{
    // tool-specific arguments
  }}
}}

Rules:
1. Choose from available tools: {', '.join(tool_names)}
2. Use "chat" if no MCP tool is appropriate for this intent
3. Map slots to tool arguments appropriately
4. Return ONLY valid JSON, no extra text

Examples:
- CalculateMath intent → use math calculation tool
- HotelBooking intent → use hotel booking tool if available
- Weather intent → use weather tool if available
"""

    response = query_llm(prompt)
    parsed = extract_json(response)
    
    if not parsed:
        return {"tool_name": "chat", "arguments": {}}
    
    return {
        "tool_name": parsed.get("tool_name", "chat"),
        "arguments": parsed.get("arguments", {})
    }

def generate_slot_question(intent: str, missing_slots: List[str]) -> str:
    """Generate natural language question for missing slots using Llama."""
    
    slot_descriptions = {
        "restaurant": "restaurant name",
        "time": "preferred time",
        "hotel_name": "hotel name",
        "checkin_date": "check-in date",
        "checkout_date": "check-out date",
        "location": "location",
        "song_name": "song name",
        "playlist_name": "playlist name",
        "book_name": "book title",
        "rating": "rating (1-5)",
        "work_name": "work title",
        "event_name": "event name"
    }
    
    missing_descriptions = [slot_descriptions.get(slot, slot) for slot in missing_slots]
    
    prompt = f"""
Generate a natural, friendly question to ask the user for missing information.

Intent: {intent}
Missing information needed: {', '.join(missing_descriptions)}

Create a single, conversational question that asks for the missing information naturally.
Be polite and specific about what you need.

Example: "I'd be happy to help you book a restaurant! Which restaurant would you like, and what time would you prefer?"

Generate only the question, no extra text:
"""

    return query_llm(prompt).strip()

# --- Node Functions ---
async def jointbert_node(state: JointBERTSlotState) -> Dict[str, Any]:
    """Extract intent and slots using Llama-based JointBERT."""
    user_input = state["user_input"]
    result = predict_intent_and_slots(user_input)
    
    print(f"🧠 Intent detected: {result['intent']}")
    print(f"📝 Slots extracted: {result['slots']}")
    
    return {
        "intent": result["intent"],
        "slots": result["slots"]
    }

async def slot_checker_node(state: JointBERTSlotState) -> Command[str]:
    """Check for missing required slots."""
    intent = state["intent"]
    slots = state["slots"]
    required = intent_to_required_slots.get(intent, [])
    missing = [s for s in required if s not in slots or not slots[s]]
    
    print(f"🔍 Required slots for {intent}: {required}")
    print(f"❌ Missing slots: {missing}")
    
    if missing:
        return Command(
            update={
                "missing_slots": missing,
                "slots_complete": False
            },
            goto="ask_for_slots"
        )
    else:
        return Command(
            update={
                "slots_complete": True,
                "missing_slots": []
            },
            goto="tool_selector"
        )

async def ask_for_slots_node(state: JointBERTSlotState) -> Dict[str, Any]:
    """Ask user for missing slots and stop for input."""
    intent = state["intent"]
    missing_slots = state["missing_slots"]
    
    question = generate_slot_question(intent, missing_slots)
    
    print(f"❓ {question}")
    
    return {
        "final_response": question,
        "needs_user_input": True
    }

async def tool_selector_node(state: JointBERTSlotState) -> Dict[str, Any]:
    """Select appropriate MCP tool based on intent and slots."""
    user_input = state["user_input"]
    intent = state["intent"]
    slots = state["slots"]
    available_tools = state["available_tools"]
    
    tool_selection = query_llm_for_tool_selection(user_input, intent, slots, available_tools)
    
    print(f"🔧 Selected tool: {tool_selection['tool_name']}")
    print(f"📋 Tool arguments: {tool_selection['arguments']}")
    
    return {
        "tool_name": tool_selection["tool_name"],
        "tool_arguments": tool_selection["arguments"]
    }

async def mcp_tool_node(state: JointBERTSlotState) -> Dict[str, Any]:
    """Execute MCP tool or chat with LLM."""
    tool_name = state["tool_name"]
    tool_arguments = state["tool_arguments"]
    user_input = state["user_input"]
    available_tools = state["available_tools"]
    
    if tool_name == "chat" or not available_tools:
        # Use LLM for general conversation
        response = query_llm(f"Please respond helpfully to this user request: {user_input}")
        return {
            "tool_result": {"type": "chat", "content": response},
            "final_response": response
        }
    else:
        # Use MCP tool
        try:
            # Note: This requires the MCP client to be passed in state or initialized here
            # For now, returning a mock result - you'll need to integrate your actual MCP client
            
            print(f"🚀 Executing MCP tool: {tool_name}")
            
            # Mock result - replace with actual MCP call
            result = f"Mock result from {tool_name} with args {tool_arguments}"
            
            return {
                "tool_result": {"type": "mcp", "tool": tool_name, "result": result},
                "final_response": result
            }
            
        except Exception as e:
            # Fallback to chat on error
            fallback_response = query_llm(f"There was an issue with the tool. Please respond to: {user_input}")
            return {
                "tool_result": {"type": "error", "error": str(e)},
                "final_response": fallback_response
            }

# --- Build the Graph ---
def create_enhanced_joint_bert_graph():
    """Create the enhanced LangGraph workflow."""
    builder = StateGraph(JointBERTSlotState)
    
    # Add nodes
    builder.add_node("jointbert", jointbert_node)
    builder.add_node("slot_checker", slot_checker_node)
    builder.add_node("ask_for_slots", ask_for_slots_node)
    builder.add_node("tool_selector", tool_selector_node)
    builder.add_node("mcp_tool", mcp_tool_node)
    
    # Add edges
    builder.add_edge(START, "jointbert")
    builder.add_edge("jointbert", "slot_checker")
    # slot_checker uses Command for conditional routing
    builder.add_edge("ask_for_slots", END)  # Stop for user input
    builder.add_edge("tool_selector", "mcp_tool")
    builder.add_edge("mcp_tool", END)
    
    return builder.compile()

# --- Enhanced Main Function ---
async def run_enhanced_client():
    """Run the enhanced client with JointBERT slot filling."""
    print("🏨 Enhanced Hotel Assistant with JointBERT + MCP (type 'quit' to exit)")
    
    try:
        # Connect to FastMCP server
        client = Client(FASTMCP_SERVER_URL)
        
        async with client:
            print("✅ Connected to FastMCP server!")
            
            # Get available tools
            tools = await client.list_tools()
            available_tools = tools if tools else []
            
            print(f"Found {len(available_tools)} MCP tools:")
            for tool in available_tools:
                print(f"  - {tool.name}: {tool.description}")
            
            # Create the graph
            graph = create_enhanced_joint_bert_graph()
            
            while True:
                user_input = input("\n👤 You: ").strip()
                if user_input.lower() in ["quit", "exit"]:
                    break
                
                # Run the graph
                try:
                    result = await graph.ainvoke({
                        "user_input": user_input,
                        "available_tools": available_tools,
                        "intent": "",
                        "slots": {},
                        "missing_slots": [],
                        "slots_complete": False,
                        "tool_name": "",
                        "tool_arguments": {},
                        "tool_result": None,
                        "final_response": "",
                        "needs_user_input": False
                    })
                    
                    final_response = result.get("final_response", "I couldn't process your request.")
                    needs_input = result.get("needs_user_input", False)
                    
                    if needs_input:
                        print(f"🤖 Assistant: {final_response}")
                        print("💡 Please provide the missing information above.")
                    else:
                        print(f"🤖 Assistant: {final_response}")
                    
                except Exception as e:
                    print(f"❌ Error processing request: {e}")
                    # Fallback to simple chat
                    fallback = query_llm(f"Please respond helpfully to: {user_input}")
                    print(f"🤖 Assistant (fallback): {fallback}")

    except Exception as e:
        print(f"❌ Failed to connect to FastMCP server: {e}")
        print("🔧 Troubleshooting:")
        print("1. Make sure your server is running")
        print(f"2. Check server accessibility at: {FASTMCP_SERVER_URL}")

if __name__ == "__main__":
    # You can also test individual components
    print("🧪 Testing intent extraction...")
    
    test_inputs = [
        "Book me a table at Mario's for 7pm",
        "What's the weather in New York?", 
        "Calculate 15 * 8 + 12",
        "I want to book a hotel",
        "Play some jazz music"
    ]
    
    for test_input in test_inputs:
        result = predict_intent_and_slots(test_input)
        print(f"Input: {test_input}")
        print(f"Result: {result}")
        print("-" * 50)
    
    # Run the main client
    asyncio.run(run_enhanced_client())