import os
import sys
import asyncio
from dotenv import load_dotenv

# Import the LangGraph flow
from langgraph_flow import IntentDrivenChatbotFlow

# Load environment variables
load_dotenv()

async def main():
    # Configuration
    BERT_MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'BERT', 'exported_snips_model')
    MCP_SERVER_COMMAND = "python Backend/MCP/mcp_server.py"
    
    print("🚀 Starting Intent-Driven Chatbot")
    print(f"📁 BERT Model Directory: {BERT_MODEL_DIR}")
    print(f"🖥️  MCP Server Command: {MCP_SERVER_COMMAND}")
    
    # Initialize chatbot
    chatbot = IntentDrivenChatbotFlow(BERT_MODEL_DIR, MCP_SERVER_COMMAND)
    
    # Test connection
    print("🔌 Initializing connections...")
    success = await chatbot.initialize()
    if not success:
        print("❌ Failed to initialize. Please check your MCP server.")
        return
    
    print("\n✅ Intent-Driven Chatbot initialized successfully!")
    print("📋 Flow components:")
    print("  - JointBERT for intent recognition and slot filling")
    print("  - LLM for parameter validation and completion")
    print("  - MCP for tool execution")
    print("\n💬 Chat Interface:")
    print("  - Type your request and the system will:")
    print("    1. Recognize your intent using JointBERT")
    print("    2. Extract parameters from your request")
    print("    3. Ask for any missing parameters")
    print("    4. Execute the appropriate tool")
    print("    5. Return a natural language response")
    print("\nType 'quit' or 'exit' to end the session.\n")
    
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ['quit', 'exit']:
            print("👋 Goodbye!")
            break
        
        print("⏳ Processing...")
        response = await chatbot.process_message(user_input)
        print(f"\nBot: {response}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Session terminated by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")