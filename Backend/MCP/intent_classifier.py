# intent_classifier.py
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import json
from typing import Dict, Any, Tuple

class JointBERTClassifier:
    def __init__(self, model_path: str = "microsoft/DialoGPT-medium"):
        """Initialize the intent classifier"""
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Load your fine-tuned model here
        # self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        # self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
        
        # For demo, using rule-based classification
        self.intent_keywords = {
            "AddToPlaylist": ["add", "playlist", "song", "music", "track"],
            "BookRestaurant": ["book", "restaurant", "table", "reservation", "dine"],
            "GetWeather": ["weather", "temperature", "forecast", "rain", "sunny"],
            "PlayMusic": ["play", "music", "song", "listen", "start"],
            "RateBook": ["rate", "book", "review", "stars", "rating"],
            "SearchCreativeWork": ["search", "find", "movie", "film", "show", "creative"],
            "SearchScreeningEvent": ["screening", "event", "tickets", "show", "cinema", "theater"],
        }
    
    def classify_intent(self, text: str) -> Tuple[str, float]:
        """Classify intent from text"""
        text_lower = text.lower()
        
        # Simple keyword-based classification for demo
        scores = {}
        for intent, keywords in self.intent_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                scores[intent] = score / len(keywords)
        
        if scores:
            best_intent = max(scores, key=scores.get)
            confidence = scores[best_intent]
            return best_intent, confidence
        else:
            return "UNK", 0.0
    
    def extract_entities(self, text: str, intent: str) -> Dict[str, Any]:
        """Extract entities based on intent"""
        entities = {}
        text_lower = text.lower()
        
        if intent == "AddToPlaylist":
            # Extract song and playlist info
            if "to" in text_lower:
                parts = text_lower.split("to")
                if len(parts) > 1:
                    entities["playlist_name"] = parts[-1].strip()
            
        elif intent == "BookRestaurant":
            # Extract restaurant booking details
            words = text.split()
            for i, word in enumerate(words):
                if word.lower() in ["at", "restaurant"]:
                    if i + 1 < len(words):
                        entities["restaurant_name"] = words[i + 1]
                elif word.lower() == "for" and i + 1 < len(words):
                    try:
                        entities["party_size"] = int(words[i + 1])
                    except ValueError:
                        pass
        
        elif intent == "GetWeather":
            # Extract location
            if "in" in text_lower:
                parts = text_lower.split("in")
                if len(parts) > 1:
                    entities["location"] = parts[-1].strip()
        
        return entities

# Initialize classifier
intent_classifier = JointBERTClassifier()
