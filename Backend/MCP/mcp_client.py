# pip install llama-index llama-index-llms-ollama llama-index-tools-mcp
import asyncio
import sys
import os
from llama_index.tools.mcp import SubprocessMCPClient, McpToolSpec
from llama_index.core.agent.workflow import ReActAgent
from llama_index.llms.ollama import Ollama

# Configuration variables
MODEL_NAME = os.environ.get("LLM_MODEL", "llama3.1")
TEMPERATURE = float(os.environ.get("LLM_TEMPERATURE", "0.7"))

# System prompt for the task-oriented chatbot
SYSTEM_PROMPT = """
You are a helpful task-oriented chatbot assistant. You have access to various tools to help users with:
- Music management (playlists, playing music)
- Restaurant bookings
- Weather information
- Book ratings and reviews
- Creative work searches
- Screening event searches

Use the available tools to fulfill user requests. Be conversational and helpful.
When users ask for something, determine which tool(s) would be most appropriate and use them.
Always provide clear, friendly responses based on the tool results.
"""

async def setup_agent():
    """Setup and return the task-oriented chatbot agent"""
    try:
        # For STDIO MCP server, we need to use subprocess connection
        print("Connecting to local MCP server via subprocess...")
        
        # Create MCP client that connects to your server via subprocess
        mcp_client = SubprocessMCPClient(
            command=["python", "mcp_server.py"],  # Replace with your server file name
            env=os.environ.copy()
        )
        
        # Get tools list
        print("Fetching available tools...")
        tools = await McpToolSpec(client=mcp_client).to_tool_list_async()
        print(f"Found {len(tools)} tools:")
        for tool in tools:
            print(f"  - {tool.metadata.name}: {tool.metadata.description}")
        
        # Initialize Ollama LLM
        print(f"Initializing Ollama with model {MODEL_NAME}...")
        llm = Ollama(model=MODEL_NAME, temperature=TEMPERATURE)
        
        # Create agent
        agent = ReActAgent(
            name="TaskOrientedChatbot", 
            llm=llm, 
            tools=tools,
            system_prompt=SYSTEM_PROMPT,
            temperature=TEMPERATURE
        )
        
        return agent, mcp_client
        
    except Exception as e:
        print(f"Error setting up agent: {str(e)}")
        raise

async def main():
    """Main function to run the task-oriented chatbot"""
    print("\n🤖 Task-Oriented Chatbot Assistant 🤖")
    print("-" * 50)
    print("I can help you with:")
    print("  • Music: Add songs to playlists, play music")
    print("  • Restaurants: Book tables")
    print("  • Weather: Get weather information")
    print("  • Books: Rate and review books")
    print("  • Entertainment: Search movies, books, events")
    print("\nType 'exit' or 'quit' to end the session.")
    print("-" * 50)
    
    try:
        # Set up the agent
        agent, mcp_client = await setup_agent()
        print("\nReady to help! What can I do for you?")
        
        # Start conversation loop
        while True:
            user_query = input("\n💬 You: ")
            
            if user_query.lower() in ['exit', 'quit', 'q']:
                print("\nThank you for using the Task-Oriented Chatbot. Goodbye!")
                break
            
            if user_query.strip():
                print("🤔 Thinking...")
                try:
                    response = await agent.run(user_query)
                    print(f"\n🤖 Assistant: {response}")
                except Exception as e:
                    print(f"Error processing query: {e}")
                
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure your MCP server file is in the same directory and properly configured.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
