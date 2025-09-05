import os
import sys
import json
import torch
import logging
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass

# Add BERT directory to path for imports
BERT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'BERT')
sys.path.insert(0, BERT_DIR)  # Insert at beginning of path to ensure it's found first

# Import BERT model functions
from use_exported_model import load_exported_model, predict_intent_and_slots

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%m/%d/%Y %H:%M:%S",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

@dataclass
class IntentResult:
    intent: str
    entities: Dict[str, Any]
    confidence: float

class JointBERTService:
    """Service for JointBERT intent recognition and slot filling"""
    _instance = None
    
    def __new__(cls, model_dir: str):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, model_dir: str):
        if not getattr(self, '_initialized', False):
            self.model_dir = model_dir
            self.model = None
            self.tokenizer = None
            self.intent_label_lst = None
            self.slot_label_lst = None
            self.device = None
            self.metadata = None
            self._model_loaded = False
            self._initialized = True
            logger.info(f"JointBERTService initialized with model directory: {model_dir}")
    
    def load_model_if_needed(self):
        """Lazy loading - only load when actually needed"""
        if not self._model_loaded:
            try:
                logger.info(f"Loading JointBERT model from {self.model_dir}")
                self.model, self.tokenizer, self.intent_label_lst, self.slot_label_lst, self.device, self.metadata = load_exported_model(self.model_dir)
                self._model_loaded = True
                logger.info("✅ JointBERT model loaded successfully")
            except Exception as e:
                logger.error(f"❌ Error loading JointBERT model: {e}")
                raise e
    
    def process_text(self, text: str) -> IntentResult:
        """Process text to extract intent and slots"""
        self.load_model_if_needed()
        
        try:
            # Call the predict function from use_exported_model
            result = predict_intent_and_slots(
                text, self.model, self.tokenizer, 
                self.intent_label_lst, self.slot_label_lst, 
                self.device, self.metadata
            )
            
            # Format slots as dictionary
            slots_dict = {}
            for word, slot in result['slots']:
                if slot != 'O':
                    entity_type = slot[2:] if slot.startswith(('B-', 'I-')) else slot
                    
                    if entity_type in slots_dict:
                        if slot.startswith('I-'):
                            slots_dict[entity_type] += f" {word}"
                        else:
                            if isinstance(slots_dict[entity_type], list):
                                slots_dict[entity_type].append(word)
                            else:
                                slots_dict[entity_type] = [slots_dict[entity_type], word]
                    else:
                        slots_dict[entity_type] = word
            
            # Get confidence score (placeholder for now)
            confidence = 0.9  # In a real implementation, extract from model output
            
            logger.info(f"Processed text: '{text}' → Intent: {result['intent']}")
            return IntentResult(
                intent=result['intent'],
                entities=slots_dict,
                confidence=confidence
            )
        except Exception as e:
            logger.error(f"Error processing text with JointBERT: {e}")
            raise e

# Singleton instance for easy access
def get_jointbert_service(model_dir: str) -> JointBERTService:
    """Get or create a JointBERT service instance"""
    return JointBERTService(model_dir)

# Example usage
if __name__ == "__main__":
    # Test the service
    EXPORTED_MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'BERT', 'exported_snips_model')
    service = get_jointbert_service(EXPORTED_MODEL_DIR)
    
    test_texts = [
        "Play some music by Coldplay",
        "Book a table at Olive Garden for tomorrow at 7pm",
        "What's the weather like in New York?"
    ]
    
    for text in test_texts:
        result = service.process_text(text)
        print(f"\nText: {text}")
        print(f"Intent: {result.intent} (confidence: {result.confidence:.2f})")
        print("Entities:")
        for entity_type, value in result.entities.items():
            if isinstance(value, list):
                print(f"- {entity_type}: {', '.join(value)}")
            else:
                print(f"- {entity_type}: {value}")