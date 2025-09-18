import asyncio
import os
from typing import Any, Dict, List
import aiohttp
from datetime import datetime
from supabase import create_client
from dotenv import load_dotenv
from fastmcp import FastMCP

# Load environment variables
load_dotenv()

# Initialize MCP server
mcp = FastMCP("AI System")

# Load Supabase credentials
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
print(SUPABASE_URL,SUPABASE_KEY)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Ollama API configuration
OLLAMA_API = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3"

@mcp.tool()
async def get_all_customers() -> List[Dict[str, Any]]:
    """
    Retrieve all customers from the database.
    
    Returns:
        List of customer records with all their details.
    """
    try:
        response = supabase.table("customer").select("*").execute()
        return response.data
    except Exception as e:
        raise Exception(f"Failed to retrieve customers: {str(e)}")

# @mcp.tool()
# async def create_booking(
#     customer_id: int,
#     room_no: int, 
#     start_date: str,
#     end_date: str,
#     num_people: int = 1,
#     price: float = 0.0
# ) -> Dict[str, Any]:
#     """
#     Create a new booking for a customer.
    
#     Args:
#         customer_id: ID of the customer making the booking
#         room_no: Room number to book
#         start_date: Start date in YYYY-MM-DD format
#         end_date: End date in YYYY-MM-DD format
#         num_people: Number of people (default: 1)
#         price: Total price for the booking (default: 0.0)
    
#     Returns:
#         The created booking record.
#     """
#     try:
#         # Validate required fields
#         if not customer_id or not room_no or not start_date or not end_date:
#             raise ValueError("Missing required fields: customer_id, room_no, start_date, end_date")

#         # Insert booking into database
#         response = supabase.table("booking").insert({
#             "customerid": customer_id,
#             "roomno": room_no,
#             "start_date": start_date,
#             "end_date": end_date,
#             "numpeople": num_people,
#             "price": price
#         }).execute()

#         return response.data[0] if response.data else {}
#     except Exception as e:
#         raise Exception(f"Failed to create booking: {str(e)}")

# MCP Tools - All made synchronous
@mcp.tool()
def add_to_playlist(user_id: str, playlist_name: str, song_title: str, artist: str = "") -> str:
    """Add a song to a user's playlist"""
    if not supabase:
        return f"Mock: Added '{song_title}' by {artist} to playlist '{playlist_name}' for user {user_id}"
    
    try:
        playlist_result = supabase.table("playlists").select("*").eq("user_id", 123).eq("playlist_name", playlist_name).execute()
        
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
    """
    Book a restaurant table for a user.

    Args:
        user_id (str): Unique identifier of the user making the booking.
        restaurant_name (str): Name of the restaurant to reserve.
        date (str): Date of the booking in YYYY-MM-DD format.
        time (str): Time of the booking in HH:MM format.
        party_size (int): Number of people for the reservation.
        location (str, optional): City or area to help disambiguate restaurants with similar names.

    Returns:
        str: A confirmation message if the booking is successful, or an error/explanation otherwise.

    Typical Usage:
        - "Book a table for 4 at Olive Garden tomorrow at 7 PM"
        - "Reserve a dinner for 2 at Sushi Samba in New York next Friday at 8 PM"
    """
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
    print("Weather tool call")
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
    """
    Submit a rating and optional review for a book.

    Args:
        user_id (str): Unique identifier of the user submitting the rating.
        book_title (str): Title of the book being rated.
        author (str): Author of the book (used to help disambiguate titles).
        rating (int): User's rating for the book, on a scale of 1–5 stars.
        review (str, optional): An optional text review or comment about the book.

    Returns:
        str: A confirmation message if the rating is successfully recorded,
             or an error/explanation otherwise.

    Behavior:
        - If the book is not already in the database, it will be added automatically.
        - If the user has already rated the book, their rating and review will be updated.

    Typical Usage:
        - "Give 'The Hobbit' by J.R.R. Tolkien 5 stars and say it's a timeless classic."
        - "Rate 'Dune' by Frank Herbert 4 stars."
        - "I’d like to leave a review for '1984' by George Orwell: 5 stars, chilling and brilliant."
    """
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
async def get_bookings_by_customer(customer_id: int) -> List[Dict[str, Any]]:
    """
    Retrieve all bookings for a specific customer.
    
    Args:
        customer_id: ID of the customer
    
    Returns:
        List of booking records for the specified customer.
    """
    try:
        response = supabase.table("booking").select("*").eq("customer_id", customer_id).execute()
        return response.data
    except Exception as e:
        raise Exception(f"Failed to retrieve bookings for customer {customer_id}: {str(e)}")

@mcp.tool()
async def get_available_rooms(start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """
    Get available rooms for a given date range.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
    
    Returns:
        List of available rooms.
    """
    try:
        # This is a simplified version - you might need more complex logic
        # to check for overlapping bookings
        booked_rooms_response = supabase.table("booking").select("roomno").or_(
            f"and(start_date.lte.{end_date},end_date.gte.{start_date})"
        ).execute()
        
        booked_room_numbers = [booking["roomno"] for booking in booked_rooms_response.data]
        
        # Assuming you have a rooms table or predefined room numbers
        all_rooms_response = supabase.table("room").select("*").execute()
        available_rooms = [room for room in all_rooms_response.data 
                          if room["room_no"] not in booked_room_numbers]
        
        return available_rooms
    except Exception as e:
        raise Exception(f"Failed to get available rooms: {str(e)}")

# @mcp.tool()
# async def query_with_llm(prompt: str) -> str:
#     """
#     Query the local Ollama LLM with a prompt.
    
#     Args:
#         prompt: The question or prompt to send to the LLM
    
#     Returns:
#         The LLM's response as a string.
#     """
#     try:
#         async with aiohttp.ClientSession() as session:
#             payload = {
#                 "model": OLLAMA_MODEL,
#                 "prompt": prompt,
#                 "stream": False
#             }
            
#             async with session.post(OLLAMA_API, json=payload) as response:
#                 if response.status != 200:
#                     error_text = await response.text()
#                     raise Exception(f"LLM request failed: {error_text}")
                
#                 result = await response.json()
#                 return result.get("response", "")
#     except Exception as e:
#         raise Exception(f"Failed to query LLM: {str(e)}")

if __name__ == "__main__":
    mcp.run(transport="sse", host="127.0.0.1", port=8000)
    # mcp.run()