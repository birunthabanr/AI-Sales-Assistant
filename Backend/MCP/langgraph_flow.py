import os
import sys
import json
import asyncio
from typing import Dict, Any, List, Optional, TypedDict, Literal, Tuple, Union
from dataclasses import dataclass, field

# LangGraph imports
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

# Local imports
from jointbert_service import get_jointbert_service, IntentResult
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Define the state for our LangGraph flow
class ChatbotState(TypedDict):
    messages: List[Any]  # Chat history
    user_input: str  # Current user input
    intent_result: Optional[IntentResult]  # Result from JointBERT
    required_parameters: Dict[str, Any]  # Required parameters for the tool
    missing_parameters: List[str]  # Parameters that are missing
    tool_to_call: Optional[str]  # The MCP tool to call
    tool_parameters: Dict[str, Any]  # Parameters for the tool
    tool_result: Optional[str]  # Result from the tool call
    llm_response: Optional[str]  # Response from the LLM
    user_id: str  # User identifier

# Define the LangGraph flow
class IntentDrivenChatbotFlow:
    def __init__(self, bert_model_dir: str, mcp_server_command: str):
        """Initialize the chatbot flow
        
        Args:
            bert_model_dir: Path to the JointBERT model directory
            mcp_server_command: Command to start the MCP server
        """
        self.bert_model_dir = bert_model_dir
        self.mcp_server_command = mcp_server_command
        
        # Initialize JointBERT service
        self.jointbert_service = get_jointbert_service(bert_model_dir)
        
        # Initialize LLM (using local Llama 3.1)
        self.llm = ChatOllama(
            model="llama3.1",
            temperature=0.7
        )
        
        # Build the graph
        self.graph = self._build_graph()
        
        # MCP server parameters
        self.server_params = None
        self.available_tools = []
        self.tool_parameters = {}
    
    async def initialize(self) -> bool:
        """Initialize connections and load required data"""
        try:
            # Initialize MCP connection
            print(f"🔌 Connecting to MCP server: {self.mcp_server_command}")
            self.server_params = StdioServerParameters(command=self.mcp_server_command.split())
            
            # Test connection and get available tools
            async with stdio_client(self.server_params) as (read, write):
                session = ClientSession(read, write)
                await session.initialize()
                
                tools = await session.list_tools()
                self.available_tools = [tool.name for tool in tools.tools]
                
                # Get tool parameters
                for tool_name in self.available_tools:
                    tool_info = await session.get_tool(tool_name)
                    self.tool_parameters[tool_name] = tool_info.parameters
                
                print(f"✅ MCP tools available: {self.available_tools}")
                return True
        except Exception as e:
            print(f"❌ Error connecting to MCP server: {e}")
            return False
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(ChatbotState)
        
        # Add nodes
        workflow.add_node("recognize_intent", self.recognize_intent)
        workflow.add_node("validate_parameters", self.validate_parameters)
        workflow.add_node("complete_parameters", self.complete_parameters)
        workflow.add_node("execute_tool", self.execute_tool)
        workflow.add_node("generate_response", self.generate_response)
        
        # Set entry point
        workflow.set_entry_point("recognize_intent")
        
        # Add edges
        workflow.add_edge("recognize_intent", "validate_parameters")
        
        # Conditional edge from validate_parameters
        workflow.add_conditional_edges(
            "validate_parameters",
            self.should_complete_parameters,
            {
                "complete_parameters": "complete_parameters",
                "execute_tool": "execute_tool"
            }
        )
        
        # Add edge from complete_parameters back to validate_parameters
        workflow.add_edge("complete_parameters", "validate_parameters")
        
        # Add edge from execute_tool to generate_response
        workflow.add_edge("execute_tool", "generate_response")
        
        # Add edge from generate_response to END
        workflow.add_edge("generate_response", END)
        
        return workflow.compile()
    
    def recognize_intent(self, state: ChatbotState) -> ChatbotState:
        """Recognize intent and extract entities using JointBERT"""
        user_input = state["user_input"]
        print(f"🔍 Recognizing intent for: {user_input}")
        
        try:
            # Process text with JointBERT
            intent_result = self.jointbert_service.process_text(user_input)
            state["intent_result"] = intent_result
            
            # Determine which tool to call based on intent
            tool_name = self._map_intent_to_tool(intent_result.intent)
            state["tool_to_call"] = tool_name
            
            # Initialize tool parameters with extracted entities
            state["tool_parameters"] = self._map_entities_to_parameters(
                tool_name, intent_result.entities
            )
            
            print(f"📊 Recognized intent: {intent_result.intent} → Tool: {tool_name}")
            print(f"📊 Extracted parameters: {state['tool_parameters']}")
            
            return state
        except Exception as e:
            print(f"❌ Error recognizing intent: {e}")
            state["intent_result"] = None
            state["tool_to_call"] = None
            state["tool_parameters"] = {}
            return state
    
    def validate_parameters(self, state: ChatbotState) -> ChatbotState:
        """Validate that all required parameters are present"""
        tool_name = state["tool_to_call"]
        if not tool_name or tool_name not in self.tool_parameters:
            state["missing_parameters"] = []
            state["required_parameters"] = {}
            return state
        
        # Get required parameters for the tool
        required_params = self._get_required_parameters(tool_name)
        state["required_parameters"] = required_params
        
        # Check which parameters are missing
        missing_params = []
        for param_name, param_info in required_params.items():
            if param_name not in state["tool_parameters"]:
                missing_params.append(param_name)
        
        state["missing_parameters"] = missing_params
        print(f"🔍 Missing parameters: {missing_params}")
        
        return state
    
    def should_complete_parameters(self, state: ChatbotState) -> Literal["complete_parameters", "execute_tool"]:
        """Decide whether to complete parameters or execute the tool"""
        if state["missing_parameters"]:
            return "complete_parameters"
        else:
            return "execute_tool"
    
    def complete_parameters(self, state: ChatbotState) -> ChatbotState:
        """Use LLM to complete missing parameters"""
        missing_params = state["missing_parameters"]
        if not missing_params:
            return state
        
        # Create a prompt for the LLM to extract missing parameters
        tool_name = state["tool_to_call"]
        required_params = state["required_parameters"]
        
        # Build a description of what we're looking for
        param_descriptions = []
        for param_name in missing_params:
            param_info = required_params.get(param_name, {})
            param_desc = param_info.get("description", param_name)
            param_descriptions.append(f"{param_name}: {param_desc}")
        
        # Create the prompt
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=f"""You are a helpful assistant that extracts specific parameters from user input.
            The user is trying to use the '{tool_name}' tool, but we're missing the following parameters:
            {', '.join(missing_params)}
            
            Parameter descriptions:
            {chr(10).join(param_descriptions)}
            
            Extract ONLY these parameters from the user's input. If you can't find a parameter, ask the user for it.
            Respond in JSON format with the extracted parameters and any questions for missing parameters.
            Example: {{
                "extracted_parameters": {{
                    "param1": "value1",
                    "param2": "value2"
                }},
                "questions": [
                    "What is the value for param3?"
                ]
            }}
            """),
            HumanMessage(content=state["user_input"])
        ])
        
        # Call the LLM
        llm_response = self.llm.invoke(prompt)
        print(f"🤖 LLM response: {llm_response.content}")
        
        try:
            # Parse the LLM response
            response_data = json.loads(llm_response.content)
            
            # Update tool parameters with extracted values
            extracted_params = response_data.get("extracted_parameters", {})
            for param_name, param_value in extracted_params.items():
                if param_name in missing_params and param_value:
                    state["tool_parameters"][param_name] = param_value
            
            # If there are questions, add them to the messages
            questions = response_data.get("questions", [])
            if questions:
                question_text = "\n".join(questions)
                state["messages"].append(AIMessage(content=question_text))
                state["llm_response"] = question_text
            
            # Update missing parameters
            still_missing = []
            for param_name in missing_params:
                if param_name not in state["tool_parameters"]:
                    still_missing.append(param_name)
            
            state["missing_parameters"] = still_missing
            
            return state
        except Exception as e:
            print(f"❌ Error parsing LLM response: {e}")
            # If we can't parse the response, just ask for the first missing parameter
            if missing_params:
                question = f"What is the {missing_params[0]}?"
                state["messages"].append(AIMessage(content=question))
                state["llm_response"] = question
            
            return state
    
    async def execute_tool(self, state: ChatbotState) -> ChatbotState:
        """Execute the MCP tool with the provided parameters"""
        tool_name = state["tool_to_call"]
        tool_params = state["tool_parameters"]
        
        if not tool_name or tool_name not in self.available_tools:
            state["tool_result"] = "No valid tool to execute"
            return state
        
        try:
            # Call the MCP tool
            print(f"🔧 Calling MCP tool: {tool_name} with {tool_params}")
            
            async with stdio_client(self.server_params) as (read, write):
                session = ClientSession(read, write)
                await session.initialize()
                
                result = await session.call_tool(tool_name, tool_params)
                state["tool_result"] = result
                print(f"✅ Tool result: {result}")
                
                return state
        except Exception as e:
            print(f"❌ Error executing tool: {e}")
            state["tool_result"] = f"Error executing tool: {str(e)}"
            return state
    
    def generate_response(self, state: ChatbotState) -> ChatbotState:
        """Generate a response based on the tool result"""
        tool_result = state.get("tool_result", "")
        intent_result = state.get("intent_result")
        
        # Create a prompt for the LLM to generate a response
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are a helpful assistant that generates natural responses based on tool results.
            The user's intent has been processed and a tool has been executed. Generate a natural, conversational response
            that incorporates the tool result. Be concise and friendly.
            """),
            HumanMessage(content=f"""User input: {state['user_input']}
            
            Intent: {intent_result.intent if intent_result else 'unknown'}
            Tool result: {tool_result}
            
            Generate a natural response:"""),
        ])
        
        # Call the LLM
        llm_response = self.llm.invoke(prompt)
        response_text = llm_response.content
        
        # Add the response to the messages
        state["messages"].append(AIMessage(content=response_text))
        state["llm_response"] = response_text
        
        return state
    
    def _map_intent_to_tool(self, intent: str) -> Optional[str]:
        """Map the intent to an MCP tool"""
        # Define mapping from intents to tools
        intent_to_tool = {
            "AddToPlaylist": "add_to_playlist",
            "BookRestaurant": "book_restaurant",
            "GetWeather": "get_weather",
            "PlayMusic": "play_music",
            "RateBook": "rate_book",
            "SearchCreativeWork": "search_creative_work",
            "SearchScreeningEvent": "search_screening_event"
        }
        
        return intent_to_tool.get(intent)
    
    def _map_entities_to_parameters(self, tool_name: Optional[str], entities: Dict[str, Any]) -> Dict[str, Any]:
        """Map extracted entities to tool parameters"""
        if not tool_name:
            return {}
        
        # Define mapping from entity types to parameter names for each tool
        entity_to_param = {
            "add_to_playlist": {
                "music_item": "song_name",
                "playlist": "playlist_name",
                "artist": "artist"
            },
            "book_restaurant": {
                "restaurant": "restaurant_name",
                "time": "time",
                "date": "date",
                "party_size": "party_size"
            },
            "get_weather": {
                "city": "location",
                "country": "location",
                "state": "location"
            },
            "play_music": {
                "music_item": "song_name",
                "artist": "artist",
                "playlist": "playlist_name"
            },
            "rate_book": {
                "rating_value": "rating",
                "object_name": "book_title"
            },
            "search_creative_work": {
                "object_name": "title"
            },
            "search_screening_event": {
                "movie_name": "movie_name",
                "object_location": "location"
            }
        }
        
        # Map entities to parameters
        params = {}
        if tool_name in entity_to_param:
            for entity_type, param_name in entity_to_param[tool_name].items():
                if entity_type in entities:
                    params[param_name] = entities[entity_type]
        
        return params
    
    def _get_required_parameters(self, tool_name: str) -> Dict[str, Any]:
        """Get the required parameters for a tool"""
        if tool_name not in self.tool_parameters:
            return {}
        
        tool_params = self.tool_parameters[tool_name]
        required_params = {}
        
        # Extract required parameters from the tool parameters
        if "properties" in tool_params:
            for param_name, param_info in tool_params["properties"].items():
                if "required" in tool_params and param_name in tool_params["required"]:
                    required_params[param_name] = param_info
        
        return required_params
    
    async def process_message(self, user_input: str, user_id: str = "default_user") -> str:
        """Process a user message through the graph"""
        initial_state: ChatbotState = {
            "messages": [HumanMessage(content=user_input)],
            "user_input": user_input,
            "intent_result": None,
            "required_parameters": {},
            "missing_parameters": [],
            "tool_to_call": None,
            "tool_parameters": {},
            "tool_result": None,
            "llm_response": None,
            "user_id": user_id
        }
        
        final_state = await self.graph.ainvoke(initial_state)
        
        # Return the LLM response
        return final_state.get("llm_response", "I'm sorry, I couldn't process your request.")

# Example usage
async def main():
    # Configuration
    BERT_MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'BERT', 'exported_snips_model')
    MCP_SERVER_COMMAND = "python Backend/MCP/mcp_server.py"
    
    # Initialize chatbot
    chatbot = IntentDrivenChatbotFlow(BERT_MODEL_DIR, MCP_SERVER_COMMAND)
    
    # Test connection
    success = await chatbot.initialize()
    if not success:
        print("❌ Failed to initialize. Please check your MCP server.")
        return
    
    print("\n✅ Intent-Driven Chatbot initialized!")
    print("- JointBERT for intent recognition")
    print("- LLM for parameter completion")
    print("- MCP for tool execution")
    print("Type 'quit' to exit.\n")
    
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ['quit', 'exit']:
            break
        
        response = await chatbot.process_message(user_input)
        print(f"\nBot: {response}")

if __name__ == "__main__":
    asyncio.run(main())