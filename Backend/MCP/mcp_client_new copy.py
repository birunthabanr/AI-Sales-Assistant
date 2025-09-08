import asyncio
import json
import re
import requests
import os
import sys
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from fastmcp import Client


# Config
OLLAMA_API = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "deepseek-r1:7b"
FASTMCP_SERVER_URL = "http://localhost:8000/sse"


# Add BERT directory to path for imports
BERT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'BERT')
sys.path.insert(0, BERT_DIR)
from use_exported_model import load_exported_model, predict_intent_and_slots


# Load the exported SNIPS model
EXPORTED_MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'BERT', 'exported_snips_model')
try:
    snips_model, tokenizer, intent_label_lst, slot_label_lst, device, metadata = load_exported_model(EXPORTED_MODEL_DIR)
    print(f"✅ SNIPS JointBERT model loaded successfully from {EXPORTED_MODEL_DIR}")
    snips_model_loaded = True
except Exception as e:
    print(f"❌ Error loading SNIPS model: {e}")
    snips_model_loaded = False


@dataclass
class IntentResult:
    intent: str
    entities: Dict[str, Any]


@dataclass
class PendingToolCall:
    tool_name: str
    original_args: Dict[str, Any]
    user_prompt: str
    intent: str
    slots: Dict[str, Any]
    error_message: str


def process_intent_slots(text: str) -> Optional[IntentResult]:
    """Process the text using the SNIPS JointBERT model and return a structured IntentResult object"""
    if not snips_model_loaded:
        return None
    
    try:
        result = predict_intent_and_slots(text, snips_model, tokenizer, intent_label_lst, slot_label_lst, device, metadata)
        
        # Format the slots as a dictionary
        slots_dict = {}
        for word, slot in result['slots']:
            if slot != 'O':  # Skip tokens with 'O' (Outside) label
                # Extract the entity type from BIO format (B-entity_type or I-entity_type)
                entity_type = slot[2:] if slot.startswith('B-') or slot.startswith('I-') else slot
                
                if entity_type in slots_dict:
                    # Append to existing entity if it's a continuation
                    if slot.startswith('I-') or (not slot.startswith('B-') and not slot.startswith('I-')):
                        slots_dict[entity_type] += f" {word}"
                    else:
                        # If it's a new entity of the same type, create a list
                        if isinstance(slots_dict[entity_type], list):
                            slots_dict[entity_type].append(word)
                        else:
                            slots_dict[entity_type] = [slots_dict[entity_type], word]
                else:
                    slots_dict[entity_type] = word

        return IntentResult(intent=result['intent'], entities=slots_dict)
    except Exception as e:
        print(f"❌ Error processing intent: {e}")
        return None


def extract_json(text: str):
    """Try to extract the first {...} JSON object from text."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            return None
    return None


def query_llm_for_tool_with_jointbert_context(user_prompt: str, intent: str, slots: Dict[str, Any], available_tools: list):
    """Enhanced tool selection using JointBERT intent and slots."""
    if not available_tools:
        return {"tool_name": "chat", "arguments": {}}
    
    tool_names = [tool.name for tool in available_tools]
    tool_descriptions = "\n".join([f"- {tool.name}: {tool.description}" for tool in available_tools])
    
    # Build context based on whether JointBERT provided useful information
    jointbert_context = ""
    if intent and intent != "UNK" and slots:
        jointbert_context = f"""
JointBERT Analysis:
- Detected intent: {intent}
- Extracted slots: {json.dumps(slots)}
"""
    elif intent == "UNK":
        jointbert_context = "\nJointBERT Analysis: Unable to classify intent (UNK)\n"
    
    system_prompt = f"""
You are an intelligent tool selector for a multi-domain assistant.

User request: "{user_prompt}"
{jointbert_context}

Available MCP tools:
{tool_descriptions}

Based on the user request and any available JointBERT analysis, select the most appropriate tool and generate arguments.
Return ONLY a JSON object in this format:
{{
  "tool_name": "TOOL_NAME" | "chat",
  "arguments": {{
    // tool-specific arguments
  }}
}}

Rules:
- Choose from available tools: {', '.join(tool_names)}
- Use "chat" if no MCP tool is appropriate
- If JointBERT provided slots, use them to create accurate arguments
- If JointBERT analysis is unavailable or unclear, rely on the user request text
- Return ONLY valid JSON, no extra text

Examples:
- Restaurant booking with restaurant_name="Mario's", timeRange="7pm" → use booking tool
- Weather request with location_name="New York" → use weather tool
- Music request → use music/playlist tool if available
"""

    try:
        with requests.post(OLLAMA_API, json={
            "model": OLLAMA_MODEL,
            "prompt": c_prompt,
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
        print(f"❌ Error querying LLM for tool selection: {e}")
        return {"tool_name": "chat", "arguments": {}}


def ask_for_missing_tool_parameters(pending_call: PendingToolCall):
    """Generate a natural question asking for missing tool parameters based on the error."""
    
    c_prompt = f"""
You are helping a user complete a tool call that failed due to missing parameters.

Original user request: "{pending_call.user_prompt}"
Tool being called: {pending_call.tool_name}
Current arguments: {json.dumps(pending_call.original_args)}
Error message: {pending_call.error_message}

JointBERT context:
- Intent: {pending_call.intent}
- Extracted slots: {json.dumps(pending_call.slots)}

The tool call failed because of missing required parameters. Based on the error message, generate a natural, friendly question asking the user to provide the missing information.

Be specific about what parameter is needed and provide context from their original request.

Examples:
- If 'playlist_name' is required: "I can help add jazz music to your playlist! What would you like to call this playlist, or do you have an existing playlist name I should use instead of 'workout'?"
- If 'song_title' is required: "I'd be happy to add that to your playlist! Could you specify which jazz song you'd like me to add?"

Generate only the question, no extra text or explanations:
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
            
            return "".join(chunks).strip()
            
    except Exception as e:
        print(f"❌ Error generating question for missing parameters: {e}")
        return f"I need some additional information to complete your request. The error was: {pending_call.error_message}"


def update_tool_arguments_with_user_response(pending_call: PendingToolCall, user_response: str):
    """Update tool arguments based on user's response to the missing parameter question."""
    
    system_prompt = f"""
You are updating tool arguments based on a user's response to a missing parameter question.

Context:
- Original request: "{pending_call.user_prompt}"
- Tool: {pending_call.tool_name}
- Current arguments: {json.dumps(pending_call.original_args)}
- Previous error: {pending_call.error_message}
- User's response: "{user_response}"

JointBERT context:
- Intent: {pending_call.intent}
- Original slots: {json.dumps(pending_call.slots)}

Based on the user's response, update the tool arguments to include the missing required parameters.
Extract the relevant information from their response and map it to the appropriate parameter names.

Return ONLY a JSON object with the updated arguments:
{{
  "arguments": {{
    // updated tool arguments including the new information
  }}
}}

Examples:
- If user says "my workout playlist" and 'playlist_name' was missing → {{"arguments": {{"playlist_name": "workout", ...}}}}
- If user says "add Autumn Leaves" and 'song_title' was missing → {{"arguments": {{"song_title": "Autumn Leaves", ...}}}}

Return ONLY the JSON object, no extra text:
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
        if parsed and "arguments" in parsed:
            return parsed["arguments"]
        else:
            # Fallback: return original args
            return pending_call.original_args
            
    except Exception as e:
        print(f"❌ Error updating tool arguments: {e}")
        return pending_call.original_args


def chat_with_llm_enhanced(user_prompt: str, intent: str = None, slots: Dict[str, Any] = None):
    """Enhanced chat with structured context from JointBERT."""
    # Build context based on JointBERT results
    if intent and slots and intent != "UNK":
        context_prompt = f"""
User request: {user_prompt}

JointBERT Analysis:
- Detected intent: {intent}
- Extracted information: {json.dumps(slots)}

Please provide a helpful response based on this structured information.
If you have specific details from the extracted information, use them in your response.
"""
    elif intent == "UNK":
        context_prompt = f"""
User request: {user_prompt}

JointBERT Analysis: Unable to classify the intent of this request.

Please provide a helpful response based on the user's request.
"""
    else:
        context_prompt = user_prompt
    
    try:
        chat_resp = requests.post(OLLAMA_API, json={
            "model": OLLAMA_MODEL,
            "prompt": context_prompt,
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


async def run_enhanced_client():
    print("🤖 Enhanced Hotel Assistant with JointBERT + FastMCP SSE (type 'quit' to exit)")
    
    if not snips_model_loaded:
        print("⚠️ Warning: SNIPS model not loaded. Falling back to original behavior.")
    
    pending_tool_call = None  # Track pending tool calls that need more info
    
    try:
        client = Client(FASTMCP_SERVER_URL)
        
        async with client:
            print("✅ Connected to FastMCP server!")
            
            # List available tools
            tools = await client.list_tools()
            available_tools = tools if tools else []
            
            print(f"🔧 Found {len(available_tools)} tools:")
            for tool in available_tools:
                print(f"  - {tool.name}: {tool.description}")
            
            while True:
                user_prompt = input("\n👤 You: ")
                if user_prompt.lower() in ["quit", "exit"]:
                    break

                # Check if we're waiting for missing tool parameters
                if pending_tool_call:
                    print(f"🔄 Updating tool arguments based on your response...")
                    
                    # Update arguments with user response
                    updated_args = update_tool_arguments_with_user_response(pending_tool_call, user_prompt)
                    
                    print(f"🤖 Updated args: {updated_args}")
                    
                    # Try calling the tool again with updated arguments
                    try:
                        result = await client.call_tool(pending_tool_call.tool_name, updated_args)
                        
                        # Success! Clear pending call
                        pending_tool_call = None
                        
                        # Format the result for display
                        if hasattr(result, 'text'):
                            print(f"📋 Result: {result.text}")
                        elif hasattr(result, 'content'):
                            print(f"📋 Result: {result.content}")
                        else:
                            print(f"📋 Result: {result}")
                            
                    except Exception as e:
                        error_message = str(e)
                        print(f"❌ Tool call still failed: {error_message}")
                        
                        # Check if it's still a validation error - if so, ask again
                        if "required property" in error_message or "validation error" in error_message.lower():
                            # Update the pending call with new error and ask again
                            pending_tool_call.original_args = updated_args
                            pending_tool_call.error_message = error_message
                            
                            question = ask_for_missing_tool_parameters(pending_tool_call)
                            print(f"🤖 Assistant: {question}")
                        else:
                            # Different error, fall back to chat
                            pending_tool_call = None
                            reply = chat_with_llm_enhanced(user_prompt, pending_tool_call.intent if pending_tool_call else None, pending_tool_call.slots if pending_tool_call else {})
                            print(f"🤖 Assistant (fallback): {reply}")
                    
                    continue

                # Normal flow: Run JointBERT once for intent and slot extraction
                intent = None
                slots = {}
                
                if snips_model_loaded:
                    intent_result = process_intent_slots(user_prompt)
                    if intent_result:
                        intent = intent_result.intent
                        slots = intent_result.entities
                        print(f"🧠 JointBERT Intent: {intent}")
                        print(f"📝 JointBERT Slots: {slots}")
                    else:
                        intent = "UNK"
                        print(f"🧠 JointBERT: Failed to process")
                else:
                    print("⚠️ JointBERT not available")

                # Use LLM for tool selection with JointBERT context
                tool_selection = query_llm_for_tool_with_jointbert_context(user_prompt, intent, slots, available_tools)
                
                tool_name = tool_selection.get("tool_name", "chat")
                arguments = tool_selection.get("arguments", {})

                print(f"🤖 LLM Decision: {tool_name} with args: {arguments}")

                # Execute tool or enhanced chat
                if tool_name == "chat" or not available_tools:
                    reply = chat_with_llm_enhanced(user_prompt, intent, slots)
                    print(f"🤖 Assistant: {reply}")
                else:
                    # Check if tool exists
                    tool_exists = any(tool.name == tool_name for tool in available_tools)
                    
                    if not tool_exists:
                        print(f"⚠️ Tool '{tool_name}' not found. Available: {[t.name for t in available_tools]}")
                        reply = chat_with_llm_enhanced(user_prompt, intent, slots)
                        print(f"🤖 Assistant (fallback): {reply}")
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
                        error_message = str(e)
                        print(f"❌ Error calling MCP tool: {error_message}")
                        
                        # Check if it's a validation error for missing required properties
                        if "required property" in error_message or "validation error" in error_message.lower():
                            print("🔄 Detected missing required parameters. Asking user for more information...")
                            
                            # Create pending tool call
                            pending_tool_call = PendingToolCall(
                                tool_name=tool_name,
                                original_args=arguments,
                                user_prompt=user_prompt,
                                intent=intent or "UNK",
                                slots=slots or {},
                                error_message=error_message
                            )
                            
                            # Ask user for missing information
                            question = ask_for_missing_tool_parameters(pending_tool_call)
                            print(f"🤖 Assistant: {question}")
                            
                        else:
                            # Other types of errors, fall back to enhanced chat
                            reply = chat_with_llm_enhanced(user_prompt, intent, slots)
                            print(f"🤖 Assistant (fallback): {reply}")

    except Exception as e:
        print(f"❌ Failed to connect to FastMCP server: {e}")
        print("🔧 Troubleshooting steps:")
        print(f"1. Make sure your server is running: python mcp_server_new.py")
        print(f"2. Check that your server is accessible at: {FASTMCP_SERVER_URL}")
        print("3. Verify your server starts without errors")


if __name__ == "__main__":
    # Test JointBERT model first
    if snips_model_loaded:
        print("🧪 Testing JointBERT model...")
        test_inputs = [
            "Add some jazz music to my workout playlist",
            "Book a table at Mario's for tonight",
            "What's the weather in New York?",
            "Play some rock music",
            "Rate The Great Gatsby 4 stars"
        ]
        
        for test_input in test_inputs:
            result = process_intent_slots(test_input)
            if result:
                print(f"Input: {test_input}")
                print(f"Intent: {result.intent}")
                print(f"Slots: {result.entities}")
                print("-" * 50)
    
    # Run the enhanced client
    asyncio.run(run_enhanced_client())
