# chatbot.py
import asyncio
import os
from typing import Dict, Any
import ollama
from intent_classifier import intent_classifier
from mcp_server import INTENT_HANDLERS

class TaskOrientedChatbot:
    def __init__(self, model_name: str = "llama3.1"):
        self.model_name = model_name
        self.conversation_history = []
        
    async def process_message(self, user_message: str, user_id: str = "default_user") -> str:
        """Process user message and return response"""
        
        # Step 1: Classify intent
        intent, confidence = intent_classifier.classify_intent(user_message)
        
        print(f"Detected intent: {intent} (confidence: {confidence:.2f})")
        
        # Step 2: Extract entities
        entities = intent_classifier.extract_entities(user_message, intent)
        entities["user_id"] = user_id
        
        print(f"Extracted entities: {entities}")
        
        # Step 3: Execute appropriate action
        if intent in INTENT_HANDLERS:
            try:
                if intent == "UNK":
                    # Use LLM for unknown intents
                    response = await self._generate_llm_response(user_message)
                else:
                    # Execute specific intent handler
                    handler = INTENT_HANDLERS[intent]
                    response = handler(**entities)
                    
                    # Enhance response with LLM if needed
                    enhanced_response = await self._enhance_response(response, user_message)
                    return enhanced_response
                    
            except Exception as e:
                response = f"I encountered an error while processing your request: {str(e)}"
        else:
            response = await self._generate_llm_response(user_message)
        
        return response
    
    async def _generate_llm_response(self, message: str) -> str:
        """Generate response using local LLM"""
        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a helpful task-oriented assistant. Be concise and helpful."
                    },
                    {"role": "user", "content": message}
                ]
            )
            return response['message']['content']
        except Exception as e:
            return f"Sorry, I couldn't process your request: {str(e)}"
    
    async def _enhance_response(self, base_response: str, original_message: str) -> str:
        """Enhance the response with LLM for better conversational flow"""
        try:
            prompt = f"""
            User said: "{original_message}"
            System response: "{base_response}"
            
            Please provide a natural, conversational response that incorporates the system response.
            Keep it concise and friendly.
            """
            
            response = ollama.chat(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}]
            )
            return response['message']['content']
        except Exception as e:
            return base_response  # Fallback to original response

# Example usage
async def main():
    chatbot = TaskOrientedChatbot()
    
    print("Task-Oriented Chatbot is ready!")
    print("Supported intents:", list(INTENT_HANDLERS.keys()))
    print("-" * 50)
    
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ['quit', 'exit', 'bye']:
            print("Goodbye!")
            break
            
        response = await chatbot.process_message(user_input)
        print(f"Bot: {response}")

if __name__ == "__main__":
    asyncio.run(main())