import asyncio
import json
import subprocess
import sys
from typing import Any, Dict, List
import ollama
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class TaskOrientedChatbotClient:
    def __init__(self, server_script_path: str, model_name: str = "llama3.1"):
        self.server_script_path = server_script_path
        self.model_name = model_name
        self.session = None
        self.available_tools = {}
        self.read = None
        self.write = None
        
    async def start_server_and_connect(self):
        """Start the MCP server and establish connection"""
        try:
            # Create server parameters for stdio connection
            server_params = StdioServerParameters(
                command="python",
                args=[self.server_script_path],
                env=None
            )
            
            # Use async context manager properly
            async with stdio_client(server_params) as (read, write):
                self.read = read
                self.write = write
                self.session = ClientSession(read, write)
                
                # Initialize the session
                await self.session.initialize()
                
                # List available tools
                tools_result = await self.session.list_tools()
                self.available_tools = {tool.name: tool for tool in tools_result.tools}
                
                print("Connected to MCP server successfully!")
                print(f"Available tools: {list(self.available_tools.keys())}")
                
                return True
                
        except Exception as e:
            print(f"Error connecting to server: {e}")
            return False
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Call an MCP tool with given arguments"""
        try:
            result = await self.session.call_tool(tool_name, arguments)
            if result.content:
                return result.content[0].text if result.content[0].text else str(result.content[0])
            return "Tool executed successfully but returned no content"
        except Exception as e:
            return f"Error calling tool {tool_name}: {str(e)}"
    
    async def chat_with_llm(self, user_message: str, conversation_history: List[Dict] = None) -> str:
        """Send message to local Llama model via Ollama"""
        if conversation_history is None:
            conversation_history = []
        
        # Create system prompt with available tools
        tools_description = "\n".join([
            f"- {name}: {tool.description}" 
            for name, tool in self.available_tools.items()
        ])
        
        system_prompt = f"""You are a helpful task-oriented chatbot with access to the following tools:

{tools_description}

When a user requests something that can be accomplished with these tools, respond with a JSON object in this format:
{{
    "action": "call_tool",
    "tool_name": "tool_name_here",
    "arguments": {{
        "param1": "value1",
        "param2": "value2"
    }}
}}

If no tool is needed, just respond normally with:
{{
    "action": "respond",
    "message": "your response here"
}}

Always be helpful and try to use the appropriate tools when possible."""

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(conversation_history)
        messages.append({"role": "user", "content": user_message})
        
        try:
            response = ollama.chat(
                model=self.model_name,
                messages=messages,
                format="json"  # Request JSON format
            )
            
            return response['message']['content']
        except Exception as e:
            return f"Error communicating with LLM: {str(e)}"
    
    async def process_user_input(self, user_input: str, conversation_history: List[Dict] = None) -> tuple[str, List[Dict]]:
        """Process user input and return response with updated conversation history"""
        if conversation_history is None:
            conversation_history = []
        
        # Get LLM response
        llm_response = await self.chat_with_llm(user_input, conversation_history)
        
        try:
            # Parse JSON response
            response_data = json.loads(llm_response)
            
            if response_data.get("action") == "call_tool":
                # Execute the tool
                tool_name = response_data.get("tool_name")
                arguments = response_data.get("arguments", {})
                
                print(f"🔧 Calling tool: {tool_name} with arguments: {arguments}")
                
                tool_result = await self.call_tool(tool_name, arguments)
                
                # Update conversation history
                conversation_history.append({"role": "user", "content": user_input})
                conversation_history.append({"role": "assistant", "content": f"I'll help you with that. {tool_result}"})
                
                return tool_result, conversation_history
                
            elif response_data.get("action") == "respond":
                message = response_data.get("message", llm_response)
                conversation_history.append({"role": "user", "content": user_input})
                conversation_history.append({"role": "assistant", "content": message})
                return message, conversation_history
                
        except json.JSONDecodeError:
            # If JSON parsing fails, treat as regular response
            conversation_history.append({"role": "user", "content": user_input})
            conversation_history.append({"role": "assistant", "content": llm_response})
            return llm_response, conversation_history
        
        return "I'm not sure how to help with that.", conversation_history

# Alternative implementation using a different approach
class SimpleMCPClient:
    def __init__(self, server_script_path: str, model_name: str = "llama3.1"):
        self.server_script_path = server_script_path
        self.model_name = model_name
        self.available_tools = {}
        
    async def run_interactive_session(self):
        """Run an interactive session with the MCP server"""
        server_params = StdioServerParameters(
            command="python",
            args=[self.server_script_path],
            env=None
        )
        
        async with stdio_client(server_params) as (read, write):
            session = ClientSession(read, write)
            
            # Initialize the session
            await session.initialize()
            
            # List available tools
            tools_result = await session.list_tools()
            self.available_tools = {tool.name: tool for tool in tools_result.tools}
            
            print("Connected to MCP server successfully!")
            print(f"Available tools: {list(self.available_tools.keys())}")
            print("\n🤖 Task-Oriented Chatbot Client Started!")
            print("You can now interact with the chatbot. Type 'quit' to exit.\n")
            
            conversation_history = []
            
            while True:
                try:
                    user_input = input("You: ").strip()
                    
                    if user_input.lower() in ['quit', 'exit', 'bye']:
                        break
                        
                    if not user_input:
                        continue
                    
                    # Get LLM response
                    llm_response = await self.chat_with_llm(user_input, conversation_history)
                    
                    try:
                        # Parse JSON response
                        response_data = json.loads(llm_response)
                        
                        if response_data.get("action") == "call_tool":
                            # Execute the tool
                            tool_name = response_data.get("tool_name")
                            arguments = response_data.get("arguments", {})
                            
                            print(f"🔧 Calling tool: {tool_name} with arguments: {arguments}")
                            
                            result = await session.call_tool(tool_name, arguments)
                            tool_result = result.content[0].text if result.content and result.content[0].text else "Tool executed successfully"
                            
                            print(f"Bot: {tool_result}")
                            
                            # Update conversation history
                            conversation_history.append({"role": "user", "content": user_input})
                            conversation_history.append({"role": "assistant", "content": tool_result})
                            
                        elif response_data.get("action") == "respond":
                            message = response_data.get("message", llm_response)
                            print(f"Bot: {message}")
                            conversation_history.append({"role": "user", "content": user_input})
                            conversation_history.append({"role": "assistant", "content": message})
                            
                    except json.JSONDecodeError:
                        # If JSON parsing fails, treat as regular response
                        print(f"Bot: {llm_response}")
                        conversation_history.append({"role": "user", "content": user_input})
                        conversation_history.append({"role": "assistant", "content": llm_response})
                    
                    print()  # Extra line for readability
                    
                except KeyboardInterrupt:
                    print("\nShutting down...")
                    break
                except Exception as e:
                    print(f"Error: {e}")
    
    async def chat_with_llm(self, user_message: str, conversation_history: List[Dict] = None) -> str:
        """Send message to local Llama model via Ollama"""
        if conversation_history is None:
            conversation_history = []
        
        # Create system prompt with available tools
        tools_description = "\n".join([
            f"- {name}: {tool.description}" 
            for name, tool in self.available_tools.items()
        ])
        
        system_prompt = f"""You are a helpful task-oriented chatbot with access to the following tools:

{tools_description}

When a user requests something that can be accomplished with these tools, respond with a JSON object in this format:
{{
    "action": "call_tool",
    "tool_name": "tool_name_here",
    "arguments": {{
        "param1": "value1",
        "param2": "value2"
    }}
}}

If no tool is needed, just respond normally with:
{{
    "action": "respond",
    "message": "your response here"
}}

Always be helpful and try to use the appropriate tools when possible."""

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(conversation_history)
        messages.append({"role": "user", "content": user_message})
        
        try:
            response = ollama.chat(
                model=self.model_name,
                messages=messages,
                format="json"  # Request JSON format
            )
            
            return response['message']['content']
        except Exception as e:
            return f"Error communicating with LLM: {str(e)}"

async def main():
    # Path to your MCP server script
    server_script = "MCP/mcp_server.py"  # Update this path
    
    # Initialize client
    client = SimpleMCPClient(server_script, "llama3.1")
    
    try:
        await client.run_interactive_session()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
