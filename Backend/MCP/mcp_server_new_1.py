import asyncio
import os
import json
from typing import Any, Dict, List, Optional
import aiohttp
from supabase import create_client
from dotenv import load_dotenv
from fastmcp import FastMCP
import uuid
from datetime import datetime, timedelta
import requests

# Load environment variables
load_dotenv()

# Initialize MCP server
mcp = FastMCP("AI System")

# Load Supabase credentials
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Ollama API configuration
OLLAMA_API = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3"

# OpenWeatherMap API
OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY")

# SerpAPI Key
SERPAPI_KEY = os.environ.get("SERPAPI_KEY")


# =====================================================
# 1. Media
# =====================================================

@mcp.tool()
def play_music(
    song: str = "",
    artist: str = "",
    genre: str = "",
    playlist_name: str = "",
) -> str:
    """Play music based on song, artist, genre, or playlist from the database"""
    try:
        if song:
            query = (
                supabase.table("songs")
                .select("id, title, genre, release_year, artist_id")
                .ilike("title", f"%{song}%")
            )
            if artist:
                artist_result = supabase.table("artists").select("id").ilike("name", f"%{artist}%").execute()
                if artist_result.data:
                    artist_id = artist_result.data[0]["id"]
                    query = query.eq("artist_id", artist_id)

            song_result = query.execute()
            if song_result.data:
                song_data = song_result.data[0]
                artist_result = supabase.table("artists").select("name").eq("id", song_data["artist_id"]).execute()
                artist_name = artist_result.data[0]["name"] if artist_result.data else "Unknown Artist"
                return f"Now playing: '{song_data['title']}' by {artist_name}"
            else:
                return f"Song '{song}' not found in library."

        elif playlist_name:
            playlist_result = (
                supabase.table("playlists")
                .select("id, name")
                .ilike("name", f"%{playlist_name}%")
                .execute()
            )
            if not playlist_result.data:
                return f"Playlist '{playlist_name}' not found."

            playlist_id = playlist_result.data[0]["id"]
            items_result = (
                supabase.table("playlist_items")
                .select("song_id")
                .eq("playlist_id", playlist_id)
                .execute()
            )
            if not items_result.data:
                return f"Playlist '{playlist_name}' is empty."

            song_id = items_result.data[0]["song_id"]
            song_result = supabase.table("songs").select("title, artist_id").eq("id", song_id).execute()
            if not song_result.data:
                return f"Playlist '{playlist_name}' has no valid songs."

            song_data = song_result.data[0]
            artist_result = supabase.table("artists").select("name").eq("id", song_data["artist_id"]).execute()
            artist_name = artist_result.data[0]["name"] if artist_result.data else "Unknown Artist"

            return f"Now playing playlist '{playlist_name}': first track '{song_data['title']}' by {artist_name}"

        elif genre:
            song_result = (
                supabase.table("songs")
                .select("title, artist_id")
                .ilike("genre", f"%{genre}%")
                .limit(1)
                .execute()
            )
            if song_result.data:
                song_data = song_result.data[0]
                artist_result = supabase.table("artists").select("name").eq("id", song_data["artist_id"]).execute()
                artist_name = artist_result.data[0]["name"] if artist_result.data else "Unknown Artist"
                return f"Now playing {genre} music: '{song_data['title']}' by {artist_name}"
            else:
                return f"No songs found for genre '{genre}'."

        else:
            return "Playing your recently played music"

    except Exception as e:
        return f"Error playing music: {str(e)}"

# tool to rate a book
@mcp.tool()
def rate_book(
    book: str,
    rating: int,
    review: str = ""
) -> str:
    """Rate a book by title and save to database"""
    try:
        user_id = str(uuid.uuid4())
        book_result = supabase.table("books").select("id, title").ilike("title", f"%{book}%").execute()
        if not book_result.data:
            return f"Book '{book}' not found in library."

        book_id = book_result.data[0]["id"]
        insert_result = supabase.table("book_reviews").insert({
            "user_id": user_id,
            "book_id": book_id,
            "rating": rating,
            "review": review
        }).execute()

        if insert_result.data:
            return f"✅ You rated '{book}' with {rating}/5 stars. Review saved under user ID {user_id}."
        else:
            return f"⚠️ Could not save rating for '{book}'."

    except Exception as e:
        return f"❌ Error rating book: {str(e)}"


# =====================================================
# 2. Restaurant
# =====================================================

@mcp.tool()
def book_restaurant(
    restaurant: str,
    time: str,
    party_size: int
) -> str:
    """Book a restaurant by name, time, and party size."""
    try:
        parsed = dateparser.parse(time)
        if not parsed:
            return f"❌ Could not understand time '{time}'."

        booking_time_str = parsed.strftime("%Y-%m-%d %H:%M:%S")
        booking_id = str(uuid.uuid4())

        restaurant_result = supabase.table("restaurants").select("id, name").ilike("name", f"%{restaurant}%").execute()
        if not restaurant_result.data:
            return f"❌ Restaurant '{restaurant}' not found."

        restaurant_id = restaurant_result.data[0]["id"]
        insert_result = supabase.table("bookings").insert({
            "user_id": booking_id,
            "restaurant_id": restaurant_id,
            "party_size": party_size,
            "booking_time": booking_time_str
        }).execute()

        if insert_result.data:
            return f"✅ Booking confirmed at '{restaurant}' for {party_size} people on {booking_time_str}."
        else:
            return f"⚠️ Could not save booking for '{restaurant}'."

    except Exception as e:
        return f"❌ Error booking restaurant: {str(e)}"


# =====================================================
# 3. Weather
# =====================================================

@mcp.tool()
def get_weather(location: str) -> str:
    """Get the current weather condition for a given location."""
    try:
        if not OPENWEATHER_API_KEY:
            return "❌ No OpenWeather API key found. Please set OPENWEATHER_API_KEY in your .env."

        url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={OPENWEATHER_API_KEY}&units=metric"
        resp = requests.get(url, timeout=10)
        data = resp.json()

        if resp.status_code != 200 or "weather" not in data:
            return f"❌ Could not fetch weather for '{location}'."

        condition = data["weather"][0]["description"]
        temp = data["main"]["temp"]
        feels_like = data["main"]["feels_like"]

        return f"🌤️ Weather in {location}: {condition}, {temp}°C (feels like {feels_like}°C)."

    except Exception as e:
        return f"❌ Error fetching weather: {str(e)}"


# =====================================================
# 4. Search Screening Event
# =====================================================

@mcp.tool()
def search_screening_event(query: str, location: str = "", date: str = "") -> str:
    """
    Search for movie screening events using Google (via SerpAPI).
    """
    try:
        if not SERPAPI_KEY:
            return "❌ No SERPAPI_KEY found. Please set it in your .env."

        # Normalize date
        if date:
            if date.lower() == "tomorrow":
                date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            elif date.lower() == "today":
                date = datetime.now().strftime("%Y-%m-%d")

        query = f"{query} screening showtimes"
        if location:
            query += f" in {location}"
        if date:
            query += f" on {date}"

        url = "https://serpapi.com/search"
        params = {"q": query, "api_key": SERPAPI_KEY, "engine": "google"}
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()

        results = []
        for item in data.get("organic_results", []):
            results.append(f"🎬 {item.get('title')} - {item.get('link')}")

        return "\n".join(results) if results else f"No screenings found for {query}."

    except Exception as e:
        return f"❌ Error searching events: {str(e)}"


# =====================================================
# Run MCP Server
# =====================================================
if __name__ == "__main__":
    mcp.run(transport="sse", host="127.0.0.1", port=8000)