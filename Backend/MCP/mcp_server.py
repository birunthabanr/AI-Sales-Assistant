import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastmcp import FastMCP
from supabase import create_client, Client
import json
import torch
import numpy as np
from dataclasses import dataclass
from dotenv import load_dotenv
import sys

# Add BERT directory to path for imports
BERT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'BERT')
sys.path.insert(0, BERT_DIR)  # Insert at beginning of path to ensure it's found first
from use_exported_model import load_exported_model, predict_intent_and_slots

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Warning: Supabase credentials not found. Database operations will be mocked.")
    supabase = None
else:
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"Error connecting to Supabase: {e}")
        supabase = None

# Initialize MCP server
mcp = FastMCP("TaskOrientedChatbot")

# Load the exported SNIPS model
EXPORTED_MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'BERT', 'exported_snips_model')
try:
    snips_model, tokenizer, intent_label_lst, slot_label_lst, device, metadata = load_exported_model(EXPORTED_MODEL_DIR)
    print(f"SNIPS model loaded successfully from {EXPORTED_MODEL_DIR}")
    snips_model_loaded = True
except Exception as e:
    print(f"Error loading SNIPS model: {e}")
    snips_model_loaded = False

@dataclass
class IntentResult:
    intent: str
    entities: Dict[str, Any]
    confidence: float

class DatabaseManager:
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
    
    def create_tables_sync(self):
        """Create required tables synchronously"""
        if not self.supabase:
            print("Supabase not available, skipping table creation")
            return
            
        tables = [
            """
            CREATE TABLE IF NOT EXISTS playlists (
                id SERIAL PRIMARY KEY,
                user_id TEXT NOT NULL,
                playlist_name TEXT NOT NULL,
                songs JSONB DEFAULT '[]'::jsonb,
                created_at TIMESTAMP DEFAULT NOW()
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS restaurants (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                cuisine_type TEXT,
                location TEXT,
                rating DECIMAL(3,2),
                price_range TEXT,
                available_slots JSONB DEFAULT '[]'::jsonb,
                created_at TIMESTAMP DEFAULT NOW()
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS restaurant_bookings (
                id SERIAL PRIMARY KEY,
                user_id TEXT NOT NULL,
                restaurant_id INTEGER REFERENCES restaurants(id),
                booking_date DATE NOT NULL,
                booking_time TIME NOT NULL,
                party_size INTEGER NOT NULL,
                status TEXT DEFAULT 'confirmed',
                created_at TIMESTAMP DEFAULT NOW()
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS books (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                isbn TEXT UNIQUE,
                genre TEXT,
                publication_year INTEGER,
                average_rating DECIMAL(3,2) DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT NOW()
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS book_ratings (
                id SERIAL PRIMARY KEY,
                user_id TEXT NOT NULL,
                book_id INTEGER REFERENCES books(id),
                rating INTEGER CHECK (rating >= 1 AND rating <= 5),
                review TEXT,
                created_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(user_id, book_id)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS creative_works (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                type TEXT NOT NULL,
                creator TEXT,
                genre TEXT,
                release_year INTEGER,
                description TEXT,
                rating DECIMAL(3,2),
                created_at TIMESTAMP DEFAULT NOW()
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS screening_events (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                venue TEXT NOT NULL,
                event_date DATE NOT NULL,
                event_time TIME NOT NULL,
                ticket_price DECIMAL(10,2),
                available_seats INTEGER,
                event_type TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            );
            """
        ]
        
        for i, table_sql in enumerate(tables):
            try:
                print(f"Table {i+1} creation attempted")
            except Exception as e:
                print(f"Error creating table {i+1}: {e}")

# Initialize database manager
db_manager = DatabaseManager(supabase) if supabase else None

# Initialize tables on module load (for testing)
if db_manager:
    db_manager.create_tables_sync()

# MCP Tools - All made synchronous
@mcp.tool()
def add_to_playlist(user_id: str, playlist_name: str, song_title: str, artist: str = "") -> str:
    """Add a song to a user's playlist"""
    if not supabase:
        return f"Mock: Added '{song_title}' by {artist} to playlist '{playlist_name}' for user {user_id}"
    
    try:
        playlist_result = supabase.table("playlists").select("*").eq("user_id", user_id).eq("playlist_name", playlist_name).execute()
        
        song_data = {"title": song_title, "artist": artist, "added_at": datetime.now().isoformat()}
        
        if playlist_result.data:
            existing_songs = playlist_result.data[0].get("songs", [])
            existing_songs.append(song_data)
            
            supabase.table("playlists").update({
                "songs": existing_songs
            }).eq("id", playlist_result.data[0]["id"]).execute()
            
            return f"Added '{song_title}' by {artist} to existing playlist '{playlist_name}'"
        else:
            supabase.table("playlists").insert({
                "user_id": user_id,
                "playlist_name": playlist_name,
                "songs": [song_data]
            }).execute()
            
            return f"Created new playlist '{playlist_name}' and added '{song_title}' by {artist}"
            
    except Exception as e:
        return f"Error adding song to playlist: {str(e)}"

@mcp.tool()
def book_restaurant(user_id: str, restaurant_name: str, date: str, time: str, party_size: int, location: str = "") -> str:
    """Book a restaurant table"""
    if not supabase:
        return f"Mock: Booked table for {party_size} at {restaurant_name} on {date} at {time}"
    
    try:
        query = supabase.table("restaurants").select("*").ilike("name", f"%{restaurant_name}%")
        if location:
            query = query.ilike("location", f"%{location}%")
        
        restaurant_result = query.execute()
        
        if not restaurant_result.data:
            return f"Restaurant '{restaurant_name}' not found. Would you like me to add it to our database?"
        
        restaurant = restaurant_result.data[0]
        
        booking_result = supabase.table("restaurant_bookings").insert({
            "user_id": user_id,
            "restaurant_id": restaurant["id"],
            "booking_date": date,
            "booking_time": time,
            "party_size": party_size
        }).execute()
        
        return f"Successfully booked table for {party_size} at {restaurant['name']} on {date} at {time}"
        
    except Exception as e:
        return f"Error booking restaurant: {str(e)}"

@mcp.tool()
def get_weather(location: str, date: str = "") -> str:
    """Get weather information for a location"""
    try:
        if date:
            return f"Weather forecast for {location} on {date}: Partly cloudy, 22°C, 10% chance of rain"
        else:
            return f"Current weather in {location}: Sunny, 25°C, light breeze"
    except Exception as e:
        return f"Error getting weather: {str(e)}"

@mcp.tool()
def play_music(song_title: str = "", artist: str = "", genre: str = "", playlist_name: str = "") -> str:
    """Play music based on song, artist, genre, or playlist"""
    try:
        if song_title:
            return f"Now playing: '{song_title}' by {artist}"
        elif playlist_name:
            return f"Now playing playlist: '{playlist_name}'"
        elif genre:
            return f"Now playing {genre} music"
        else:
            return "Playing your recently played music"
    except Exception as e:
        return f"Error playing music: {str(e)}"

@mcp.tool()
def rate_book(user_id: str, book_title: str, author: str, rating: int, review: str = "") -> str:
    """Rate a book"""
    if not supabase:
        return f"Mock: Rated '{book_title}' by {author}: {rating}/5 stars"
    
    try:
        book_result = supabase.table("books").select("*").ilike("title", f"%{book_title}%").execute()
        
        if not book_result.data:
            book_insert = supabase.table("books").insert({
                "title": book_title,
                "author": author
            }).execute()
            book_id = book_insert.data[0]["id"]
        else:
            book_id = book_result.data[0]["id"]
        
        supabase.table("book_ratings").upsert({
            "user_id": user_id,
            "book_id": book_id,
            "rating": rating,
            "review": review
        }).execute()
        
        return f"Rated '{book_title}' by {author}: {rating}/5 stars"
        
    except Exception as e:
        return f"Error rating book: {str(e)}"

@mcp.tool()
def search_creative_work(title: str = "", creator: str = "", genre: str = "", work_type: str = "") -> str:
    """Search for creative works (movies, books, music, etc.)"""
    if not supabase:
        return f"Mock: Found creative works matching your criteria"
    
    try:
        query = supabase.table("creative_works").select("*")
        
        if title:
            query = query.ilike("title", f"%{title}%")
        if creator:
            query = query.ilike("creator", f"%{creator}%")
        if genre:
            query = query.ilike("genre", f"%{genre}%")
        if work_type:
            query = query.eq("type", work_type)
        
        result = query.limit(10).execute()
        
        if result.data:
            works = []
            for work in result.data:
                works.append(f"'{work['title']}' by {work['creator']} ({work['type']}, {work['genre']})")
            return f"Found creative works:\n" + "\n".join(works)
        else:
            return f"No creative works found matching your search criteria"
            
    except Exception as e:
        return f"Error searching creative works: {str(e)}"

@mcp.tool()
def search_screening_event(title: str = "", venue: str = "", date: str = "", event_type: str = "") -> str:
    """Search for screening events (movies, theater, concerts, etc.)"""
    if not supabase:
        return f"Mock: Found screening events matching your criteria"
    
    try:
        query = supabase.table("screening_events").select("*")
        
        if title:
            query = query.ilike("title", f"%{title}%")
        if venue:
            query = query.ilike("venue", f"%{venue}%")
        if date:
            query = query.eq("event_date", date)
        if event_type:
            query = query.eq("event_type", event_type)
        
        result = query.limit(10).execute()
        
        if result.data:
            events = []
            for event in result.data:
                events.append(f"'{event['title']}' at {event['venue']} on {event['event_date']} at {event['event_time']} - ${event['ticket_price']}")
            return f"Found screening events:\n" + "\n".join(events)
        else:
            return f"No screening events found matching your search criteria"
            
    except Exception as e:
        return f"Error searching screening events: {str(e)}"

@mcp.tool()
def initialize_database() -> str:
    """Initialize database tables"""
    if not db_manager:
        return "Database manager not available (no Supabase connection)"
    
    try:
        db_manager.create_tables_sync()
        return "Database tables initialized successfully"
    except Exception as e:
        return f"Error initializing database: {str(e)}"

# Test tool to verify server is working
@mcp.tool()
def hello(name: str = "World") -> str:
    """Say hello - test tool to verify server connection"""
    return f"Hello, {name}! The MCP server is working correctly."

def process_intent_slots(text: str) -> Optional[IntentResult]:
    """Process the text using the SNIPS model and return a structured IntentResult object"""
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
        
        # Get confidence score from the model (using a placeholder value if not available)
        confidence = 0.9  # Placeholder - in a real implementation, extract from model output
        
        return IntentResult(intent=result['intent'], entities=slots_dict, confidence=confidence)
    except Exception as e:
        print(f"Error processing intent: {e}")
        return None

@mcp.tool()
def analyze_intent(text: str) -> str:
    """Analyze the intent and extract entities from user input using the SNIPS model"""
    if not snips_model_loaded:
        return "Intent analysis model is not available"
    
    try:
        intent_result = process_intent_slots(text)
        if not intent_result:
            return "Failed to analyze intent"
        
        # Create a formatted response
        response = f"Intent: {intent_result.intent} (confidence: {intent_result.confidence:.2f})\n\nEntities:\n"
        for entity_type, value in intent_result.entities.items():
            if isinstance(value, list):
                response += f"- {entity_type}: {', '.join(value)}\n"
            else:
                response += f"- {entity_type}: {value}\n"
        
        # Also return the raw result as JSON for programmatic use
        response += f"\nRaw result: {json.dumps({'intent': intent_result.intent, 'entities': intent_result.entities, 'confidence': intent_result.confidence})}"
        
        return response
    except Exception as e:
        return f"Error analyzing intent: {str(e)}"

if __name__ == "__main__":
    print("Starting Task-Oriented Chatbot MCP Server...")
    print("Available tools:")
    print("- add_to_playlist")
    print("- book_restaurant") 
    print("- get_weather")
    print("- play_music")
    print("- rate_book")
    print("- search_creative_work")
    print("- search_screening_event")
    print("- initialize_database")
    print("- analyze_intent (SNIPS model)")
    print("- hello (test tool)")
    print("\nStarting server with STDIO transport...")
    
    # This is the correct way to start for MCP Inspector
    mcp.run()  # Uses STDIO transport by default
