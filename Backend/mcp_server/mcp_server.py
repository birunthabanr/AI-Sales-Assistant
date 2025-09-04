from flask import Flask, request, jsonify
from supabase import create_client
import os
import requests
from dotenv import load_dotenv 
from mcp_clients.llm import handle_prompt
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
load_dotenv()

# Load Supabase credentials
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Ollama API endpoint
OLLAMA_API = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3"  

# ROUTE 1: Retrieve all customers
@app.route('/customers', methods=['GET'])
def get_customers():
    try:
        # Match table name exactly
        response = supabase.table("customer").select("*").execute()
        return jsonify(response.data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ROUTE 2: Create new booking
@app.route('/bookings', methods=['POST'])
def create_booking():
    try:
        data = request.get_json()
        customer_id = data.get("customer_id")
        room_no = data.get("room_no")
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        num_people = data.get("num_people", 1)
        price = data.get("price", 0)

        if not customer_id or not room_no or not start_date or not end_date:
            return jsonify({"error": "Missing required fields: customer_id, room_no, start_date, end_date"}), 400

        # Column names must match Supabase table exactly
        response = supabase.table("booking").insert({
            "customerid": customer_id,
            "roomno": room_no,
            "start_date": start_date,
            "end_date": end_date,
            "numpeople": num_people,
            "price": price
        }).execute()

        return jsonify(response.data), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/chat',methods =['POST'])
def chat_response():
    print("try to get response")
    try:
        print("try block")
        data = request.get_json()
        print("this is a data")
        user_prompt = data.get("prompt")
        print(user_prompt)
        if not user_prompt:
            return jsonify({"error": "Missing 'prompt'"}), 400
        result = handle_prompt(user_prompt)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# ROUTE 3: Query via LLM (Ollama)
@app.route('/query', methods=['POST'])
def query_llm():
    try:
        user_prompt = request.json.get("prompt")

        # Send the prompt to Ollama LLM
        ollama_response = requests.post(OLLAMA_API, json={
            "model": OLLAMA_MODEL,
            "prompt": user_prompt
        })

        if ollama_response.status_code != 200:
            return jsonify({"error": "LLM request failed", "details": ollama_response.text}), 500

        llm_text = ollama_response.json().get("response", "")

        # Basic intent detection
        lower_prompt = user_prompt.lower()
        if "show customers" in lower_prompt or "all customers" in lower_prompt:
            return get_customers()

        if "book appointment" in lower_prompt or "booking" in lower_prompt:
            # Example: parse LLM output later
            booking_data = {
                "customer_id": 1,   # Default demo
                "room_no": 1,       # Default demo
                "start_date": "2025-09-10",
                "end_date": "2025-09-12",
                "num_people": 2,
                "price": 500
            }
            with app.test_request_context(json=booking_data):
                return create_booking()

        # Default: return LLM response
        return jsonify({"llm_response": llm_text}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Start Flask server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
