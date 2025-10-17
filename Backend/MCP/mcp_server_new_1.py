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
import dateparser
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
    restaurant_name: str,
    time: str,
    party_size: int
) -> str:
    """Book a restaurant by restaurant_name, time, and party size."""
    try:
        parsed = dateparser.parse(time)
        if not parsed:
            return f"❌ Could not understand time '{time}'."

        booking_time_str = parsed.strftime("%Y-%m-%d %H:%M:%S")
        booking_id = str(uuid.uuid4())

        restaurant_result = supabase.table("restaurants").select("id, name").ilike("name", f"%{restaurant_name}%").execute()
        if not restaurant_result.data:
            return f"❌ Restaurant '{restaurant_name}' not found."

        restaurant_id = restaurant_result.data[0]["id"]
        insert_result = supabase.table("bookings").insert({
            "user_id": booking_id,
            "restaurant_id": restaurant_id,
            "party_size": party_size,
            "booking_time": booking_time_str
        }).execute()

        if insert_result.data:
            return f"✅ Booking confirmed at '{restaurant_name}' for {party_size} people on {booking_time_str}."
        else:
            return f"⚠️ Could not save booking for '{restaurant_name}'."

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
    

@mcp.tool()
def edit_account(account_id: str, email: str = "", full_name: str = "", phone: str = "") -> str:
    """
    Update account information for an existing user.
    
    Args:
        account_id (str): Unique identifier of the account to update.
        email (str, optional): New email address to update.
        full_name (str, optional): New full name to update.
        phone (str, optional): New phone number to update.
    
    Returns:
        str: Confirmation of account update or error message.
    
    Typical Usage:
        - "Update my email to newemail@domain.com for account ACC1234"
        - "Change name to John Smith and phone to 555-0123 for ACC5678"
    """
    if not supabase:
        return f"Mock: Account {account_id} updated successfully"
    
    try:
        update_data = {}
        if email: update_data["email"] = email
        if full_name: update_data["full_name"] = full_name
        if phone: update_data["phone"] = phone
        update_data["updated_at"] = datetime.now().isoformat()
        
        result = supabase.table("users").update(update_data).eq("account_id", account_id).execute()
        
        if result.data:
            return f"Account {account_id} updated successfully"
        else:
            return f"Account {account_id} not found"
            
    except Exception as e:
        return f"Error updating account: {str(e)}"

@mcp.tool()
def place_order(customer_id: str, items: str, shipping_address_id: str, payment_method_id: str) -> str:
    """
    Place a new order for a customer with specified items and details.
    
    Args:
        customer_id (str): Unique identifier of the customer placing the order.
        items (str): JSON string of items with SKUs and quantities [{"sku": "PROD123", "qty": 2}].
        shipping_address_id (str): ID of the shipping address to use.
        payment_method_id (str): ID of the payment method to charge.
    
    Returns:
        str: Order confirmation with order ID and total or error message.
    
    Typical Usage:
        - "Place order for customer CUST123 with 2x LAPTOP001 and 1x MOUSE002"
        - "Create order with items from my cart for address ADDR456"
    """
    if not supabase:
        import json
        items_list = json.loads(items)
        total = sum(item.get('qty', 1) * 29.99 for item in items_list)  # Mock pricing
        return f"Mock: Order ORD{hash(customer_id) % 10000} placed successfully. Total: ${total:.2f}"
    
    try:
        import json
        items_list = json.loads(items)
        
        # Calculate total (would query product prices in real implementation)
        total = sum(item.get('qty', 1) * 29.99 for item in items_list)
        
        result = supabase.table("orders").insert({
            "customer_id": customer_id,
            "items": items_list,
            "shipping_address_id": shipping_address_id,
            "payment_method_id": payment_method_id,
            "total_amount": total,
            "status": "placed",
            "created_at": datetime.now().isoformat()
        }).execute()
        
        return f"Order {result.data[0]['id']} placed successfully. Total: ${total:.2f}"
        
    except Exception as e:
        return f"Error placing order: {str(e)}"

@mcp.tool()
def track_order(order_id: str) -> str:
    """
    Get tracking information and status updates for an order.
    
    Args:
        order_id (str): Unique identifier of the order to track.
    
    Returns:
        str: Order status, tracking number, and delivery updates or error message.
    
    Typical Usage:
        - "Track my order ORD12345"
        - "What's the status of order ORD67890"
    """
    if not supabase:
        return f"Mock: Order {order_id} is in transit. Tracking: TRK{hash(order_id) % 100000}. Expected delivery: 2-3 days"
    
    try:
        result = supabase.table("orders").select("*").eq("order_id", order_id).execute()
        
        if result.data:
            order = result.data[0]
            status = order.get('status', 'unknown')
            tracking = order.get('tracking_number', 'Not assigned')
            return f"Order {order_id}: Status is '{status}'. Tracking number: {tracking}"
        else:
            return f"Order {order_id} not found"
            
    except Exception as e:
        return f"Error tracking order: {str(e)}"

@mcp.tool()
def cancel_order(order_id: str, reason: str = "") -> str:
    """
    Cancel an existing order if cancellation is allowed.
    
    Args:
        order_id (str): Unique identifier of the order to cancel.
        reason (str, optional): Reason for cancellation for customer service records.
    
    Returns:
        str: Cancellation confirmation, potential fees, or rejection message.
    
    Typical Usage:
        - "Cancel order ORD12345"
        - "Cancel my order ORD67890 because I changed my mind"
    """
    if not supabase:
        return f"Mock: Order {order_id} cancelled successfully. No cancellation fee applied"
    
    try:
        # Check if order can be cancelled
        result = supabase.table("orders").select("*").eq("order_id", order_id).execute()
        
        if not result.data:
            return f"Order {order_id} not found"
            
        order = result.data[0]
        status = order.get('status', '')
        
        if status in ['shipped', 'delivered', 'cancelled']:
            return f"Order {order_id} cannot be cancelled (current status: {status})"
        
        # Cancel the order
        supabase.table("orders").update({
            "status": "cancelled",
            "cancellation_reason": reason,
            "cancelled_at": datetime.now().isoformat()
        }).eq("order_id", order_id).execute()
        
        return f"Order {order_id} has been cancelled successfully"
        
    except Exception as e:
        return f"Error cancelling order: {str(e)}"

@mcp.tool()
def check_payment_methods(customer_id: str) -> str:
    """
    List all available payment methods for a customer.
    
    Args:
        customer_id (str): Unique identifier of the customer.
    
    Returns:
        str: List of payment methods with details or error message.
    
    Typical Usage:
        - "Show my payment methods"
        - "What cards do I have on file for customer CUST123"
    """
    if not supabase:
        return f"Mock: Customer {customer_id} has 2 payment methods: Visa ending 4567, PayPal account"
    
    try:
        result = supabase.table("payment_methods").select("*").eq("customer_id", customer_id).execute()
        
        if result.data:
            methods = []
            for method in result.data:
                method_type = method.get('type', 'unknown')
                last4 = method.get('last4', 'N/A')
                label = method.get('label', 'Unnamed')
                methods.append(f"{method_type.title()} {label} ending {last4}")
            
            return f"Available payment methods: {', '.join(methods)}"
        else:
            return f"No payment methods found for customer {customer_id}"
            
    except Exception as e:
        return f"Error retrieving payment methods: {str(e)}"

@mcp.tool()
def diagnose_payment_issue(order_id: str = "", error_code: str = "", payment_method_id: str = "") -> str:
    """
    Diagnose and provide solutions for payment-related issues.
    
    Args:
        order_id (str, optional): Order ID where payment failed.
        error_code (str, optional): Error code from payment processor.
        payment_method_id (str, optional): Payment method that failed.
    
    Returns:
        str: Diagnosis of the payment issue and recommended solutions.
    
    Typical Usage:
        - "My payment failed for order ORD12345 with error DECLINED"
        - "Payment method PM123 is not working"
    """
    if not supabase:
        diagnosis_map = {
            "DECLINED": "Card was declined. Try a different payment method or contact your bank.",
            "EXPIRED": "Payment method has expired. Please update your card information.",
            "INSUFFICIENT": "Insufficient funds. Check your account balance or use a different card."
        }
        return f"Mock: {diagnosis_map.get(error_code, 'Payment issue detected. Please contact support or try a different payment method.')}"
    
    try:
        # In a real implementation, would query payment logs and error details
        diagnosis_map = {
            "DECLINED": "Your card was declined by the bank. This could be due to insufficient funds, incorrect card details, or fraud protection. Contact your bank or try a different payment method.",
            "EXPIRED": "The payment method has expired. Please update your card information in your account settings.",
            "INSUFFICIENT": "Insufficient funds available. Please check your account balance or use a different payment method.",
            "NETWORK": "Network error occurred during payment processing. Please try again in a few minutes.",
            "INVALID": "Invalid payment information provided. Please check your card details and try again."
        }
        
        diagnosis = diagnosis_map.get(error_code, "Payment issue detected. Please contact customer support for assistance.")
        
        return f"Payment Issue Diagnosis: {diagnosis}"
        
    except Exception as e:
        return f"Error diagnosing payment issue: {str(e)}"

@mcp.tool()
def get_refund(order_id: str, items: str = "", reason: str = "") -> str:
    """
    Process a refund request for an order or specific items.
    
    Args:
        order_id (str): Order ID to process refund for.
        items (str, optional): JSON string of specific items to refund [{"sku": "PROD123", "qty": 1}].
        reason (str, optional): Reason for the refund request.
    
    Returns:
        str: Refund confirmation with refund ID and expected amount or rejection message.
    
    Typical Usage:
        - "Request refund for order ORD12345"
        - "Refund 1x LAPTOP001 from order ORD67890 because it's defective"
    """
    if not supabase:
        return f"Mock: Refund initiated for order {order_id}. Refund ID: REF{hash(order_id) % 10000}. Expected amount: $59.98"
    
    try:
        # Check if order exists and is eligible for refund
        order_result = supabase.table("orders").select("*").eq("order_id", order_id).execute()
        
        if not order_result.data:
            return f"Order {order_id} not found"
        
        order = order_result.data[0]
        order_status = order.get('status', '')
        
        if order_status in ['cancelled', 'refunded']:
            return f"Order {order_id} is not eligible for refund (status: {order_status})"
        
        # Calculate refund amount (simplified)
        refund_amount = order.get('total_amount', 0)
        if items:
            # In real implementation, calculate partial refund based on items
            refund_amount = refund_amount * 0.5  # Mock partial refund
        
        # Create refund record
        refund_result = supabase.table("refunds").insert({
            "order_id": order_id,
            "customer_id": order.get('customer_id'),
            "amount": refund_amount,
            "reason": reason,
            "status": "initiated",
            "created_at": datetime.now().isoformat()
        }).execute()
        
        return f"Refund initiated successfully. Refund ID: {refund_result.data[0]['id']}. Amount: ${refund_amount:.2f}. Processing time: 5-7 business days"
        
    except Exception as e:
        return f"Error processing refund: {str(e)}"

@mcp.tool()
def track_refund(refund_id: str) -> str:
    """
    Track the status and progress of a refund request.
    
    Args:
        refund_id (str): Unique identifier of the refund to track.
    
    Returns:
        str: Current refund status and estimated completion time.
    
    Typical Usage:
        - "Track my refund REF12345"
        - "What's the status of refund REF67890"
    """
    if not supabase:
        return f"Mock: Refund {refund_id} is being processed. Status: In Progress. ETA: 3-5 business days"
    
    try:
        result = supabase.table("refunds").select("*").eq("refund_id", refund_id).execute()
        
        if result.data:
            refund = result.data[0]
            status = refund.get('status', 'unknown')
            amount = refund.get('amount', 0)
            created_date = refund.get('created_at', '')
            
            status_messages = {
                'initiated': 'Refund request received and is being reviewed',
                'approved': 'Refund approved and being processed',
                'processing': 'Refund is being processed by payment processor',
                'completed': 'Refund has been completed and funds returned',
                'rejected': 'Refund request was rejected'
            }
            
            status_msg = status_messages.get(status, f'Status: {status}')
            return f"Refund {refund_id}: {status_msg}. Amount: ${amount:.2f}"
        else:
            return f"Refund {refund_id} not found"
            
    except Exception as e:
        return f"Error tracking refund: {str(e)}"

@mcp.tool()
def contact_customer_service(topic: str, preferred_channel: str = "email", phone: str = "", email: str = "") -> str:
    """
    Create a customer service request and schedule callback or response.
    
    Args:
        topic (str): Description of the issue or topic for customer service.
        preferred_channel (str): Preferred contact method - phone, email, or chat.
        phone (str, optional): Phone number for callback if preferred_channel is phone.
        email (str, optional): Email address for response if preferred_channel is email.
    
    Returns:
        str: Service ticket confirmation with ticket ID and estimated response time.
    
    Typical Usage:
        - "I need help with my order, please call me at 555-0123"
        - "Contact me via email about billing issue at john@email.com"
    """
    if not supabase:
        return f"Mock: Support ticket TKT{hash(topic) % 10000} created. We'll contact you via {preferred_channel} within 24 hours"
    
    try:
        ticket_result = supabase.table("support_tickets").insert({

            "topic": topic,
            "preferred_channel": preferred_channel,
            "contact_phone": phone,
            "contact_email": email,
            "status": "open",
            "priority": "normal",
            "created_at": datetime.now().isoformat()
        }).execute()
    
        ticket_id = ticket_result.data[0]['id']
        
        eta_map = {
            "phone": "within 4 hours",
            "email": "within 24 hours",  
            "chat": "within 1 hour"
        }
        
        eta = eta_map.get(preferred_channel, "within 24 hours")
        return f"Support ticket {ticket_id} created successfully. We'll contact you via {preferred_channel} {eta}"
        
    except Exception as e:
        return f"Error creating support ticket: {str(e)}"

@mcp.tool()
def transfer_to_human_agent(context: str, priority: str = "normal") -> str:
    """
    Transfer the current conversation to a human customer service agent.
    
    Args:
        context (str): Summary of the conversation and issue for agent handoff.
        priority (str): Priority level - normal or urgent.
    
    Returns:
        str: Transfer confirmation with session ID and expected wait time.
    
    Typical Usage:
        - "I need to speak to a human about my billing dispute"
        - "Transfer me to an agent urgently about order cancellation"
    """
    if not supabase:
        wait_time = "2-3 minutes" if priority == "urgent" else "5-10 minutes"
        return f"Mock: Transferring to human agent. Session ID: SES{hash(context) % 10000}. Estimated wait: {wait_time}"
    
    try:
        session_result = supabase.table("agent_sessions").insert({
            "context": context,
            "priority": priority,
            "status": "queued",
            "created_at": datetime.now().isoformat()
        }).execute()
        
        session_id = session_result.data[0]['id']
        
        wait_times = {
            "urgent": "1-2 minutes",
            "normal": "5-8 minutes"
        }
        
        wait_time = wait_times.get(priority, "5-8 minutes")
        return f"Transferring you to a human agent. Session ID: {session_id}. Estimated wait time: {wait_time}"
        
    except Exception as e:
        return f"Error transferring to agent: {str(e)}"


# =====================================================
# Run MCP Server
# =====================================================
if __name__ == "__main__":
    mcp.run(transport="sse", host="127.0.0.1", port=0)