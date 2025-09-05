# Intent-Driven Chatbot with LangGraph Flow

This system implements an intent-driven chatbot that uses a LangGraph flow to process user requests. The flow integrates JointBERT for intent recognition and slot filling, an LLM for parameter validation and completion, and the MCP server for tool execution.

## Architecture

The system consists of the following components:

1. **JointBERT Service** (`jointbert_service.py`): An external service that loads the SNIPS model and provides intent recognition and slot filling.

2. **LangGraph Flow** (`langgraph_flow.py`): A flow that orchestrates the processing of user requests through the following steps:
   - Intent recognition using JointBERT
   - Parameter validation and extraction
   - Parameter completion using LLM if needed
   - Tool execution via MCP server
   - Response generation

3. **Main Application** (`intent_driven_chatbot.py`): The main entry point that initializes the flow and provides a simple chat interface.

## Flow Diagram

```
User Input
    |
    v
JointBERT (Intent Recognition)
    |
    v
Parameter Validation
    |\________
    |         \
    v          v
Parameter     Tool Execution
Completion     |
    |          |
    |          v
    |      Response Generation
    |          |
    v          v
Parameter     User
Validation
```

## How It Works

1. The user provides input text.
2. JointBERT analyzes the text to determine the intent and extract entities.
3. The system maps the intent to an appropriate MCP tool and the entities to tool parameters.
4. The system validates that all required parameters for the tool are present.
5. If parameters are missing, the LLM is used to extract them from the user input or ask the user for them.
6. Once all parameters are available, the MCP tool is executed.
7. The LLM generates a natural language response based on the tool result.

## Usage

### Prerequisites

- Python 3.8+
- BERT model trained on SNIPS dataset
- MCP server running
- OpenAI API key (or other LLM provider)

### Installation

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. Set up environment variables in a `.env` file:

```
OPENAI_API_KEY=your_api_key_here
```

### Running the Chatbot

```bash
python intent_driven_chatbot.py
```

## Example Interactions

### Complete Information

```
You: Play some music by Coldplay
Bot: I've started playing music by Coldplay for you. Enjoy!
```

### Missing Parameters

```
You: Book a restaurant
Bot: What restaurant would you like to book?

You: Olive Garden
Bot: What date and time would you like to book Olive Garden for?

You: Tomorrow at 7pm
Bot: I've booked a table at Olive Garden for tomorrow at 7pm. Your reservation is confirmed!
```

## Extending the System

### Adding New Intents

To add new intents, you need to:

1. Train the JointBERT model with the new intent and its slots.
2. Update the `_map_intent_to_tool` method in `langgraph_flow.py` to map the new intent to an MCP tool.
3. Update the `_map_entities_to_parameters` method to map the new intent's entities to tool parameters.

### Adding New Tools

To add new tools, you need to:

1. Add the tool to the MCP server.
2. Update the `_map_intent_to_tool` method in `langgraph_flow.py` to map an intent to the new tool.
3. Update the `_map_entities_to_parameters` method to map entities to the new tool's parameters.

## Troubleshooting

### JointBERT Model Loading Issues

If the JointBERT model fails to load, check that:

- The model directory path is correct
- The model files are present in the directory
- The BERT directory is in the Python path

### MCP Server Connection Issues

If the MCP server connection fails, check that:

- The MCP server is running
- The server command is correct
- The server is accessible from the client