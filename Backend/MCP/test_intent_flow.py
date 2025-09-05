import os
import sys
import asyncio
from dotenv import load_dotenv

# Import the LangGraph flow
from langgraph_flow import IntentDrivenChatbotFlow

# Load environment variables
load_dotenv()

# Sample test queries with expected intents and parameters
TEST_QUERIES = [
    {
        "query": "Play some music by Coldplay",
        "expected_intent": "PlayMusic",
        "expected_params": {"artist": "Coldplay"}
    },
    {
        "query": "Book a table at Olive Garden for tomorrow at 7pm",
        "expected_intent": "BookRestaurant",
        "expected_params": {"restaurant": "Olive Garden", "time": "tomorrow at 7pm"}
    },
    {
        "query": "What's the weather like in New York?",
        "expected_intent": "GetWeather",
        "expected_params": {"location": "New York"}
    }
]

async def run_test():
    # Configuration
    BERT_MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'BERT', 'exported_snips_model')
    MCP_SERVER_COMMAND = "python Backend/MCP/mcp_server.py"
    
    print("🧪 Starting Intent Flow Test")
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
    
    # Run test queries
    print("\n🧪 Running test queries...")
    for i, test in enumerate(TEST_QUERIES):
        print(f"\n📝 Test {i+1}: {test['query']}")
        print(f"  Expected intent: {test['expected_intent']}")
        print(f"  Expected params: {test['expected_params']}")
        
        # Process the query
        print("  ⏳ Processing...")
        try:
            # Get the state for debugging
            state = await chatbot.debug_process(test['query'])
            
            # Print the results
            print(f"  🔍 Detected intent: {state.get('intent', 'Unknown')}")
            print(f"  🔍 Extracted params: {state.get('parameters', {})}")
            print(f"  💬 Response: {state.get('response', 'No response')}")
            
            # Check if the intent matches
            intent_match = state.get('intent') == test['expected_intent']
            
            # Check if all expected parameters are present
            params_match = True
            for param, value in test['expected_params'].items():
                if param not in state.get('parameters', {}):
                    params_match = False
                    break
            
            # Print the result
            if intent_match and params_match:
                print("  ✅ Test passed!")
            else:
                print("  ❌ Test failed!")
                if not intent_match:
                    print(f"    Intent mismatch: Expected {test['expected_intent']}, got {state.get('intent', 'Unknown')}")
                if not params_match:
                    print(f"    Parameters mismatch: Expected {test['expected_params']}, got {state.get('parameters', {})}")
        
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    print("\n🏁 Test completed!")

if __name__ == "__main__":
    try:
        asyncio.run(run_test())
    except KeyboardInterrupt:
        print("\n👋 Test terminated by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")