from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from supabase import create_client
import os
import requests
from dotenv import load_dotenv
import uvicorn

# Load environment variables
# =======
# from dotenv import load_dotenv 
# from mcp_clients.llm import handle_prompt
# from flask import Flask, request, jsonify
# from flask_cors import CORS

# app = Flask(__name__)
# CORS(app)
# >>>>>>> main
load_dotenv()

# Initialize FastAPI
app = FastAPI()

# Load Supabase credentials
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Ollama API endpoint
OLLAMA_API = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3"

# Pydantic model for booking
class BookingRequest(BaseModel):
    customer_id: int | None = None
    room_no: int | None = None
    start_date: str | None = None
    end_date: str | None = None
    num_people: int | None = 1


# ROUTE 1: Retrieve all customers
@app.get("/customers")
async def get_customers():
    try:
        response = supabase.table("customer").select("*").execute()
        return JSONResponse(content=response.data, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ROUTE 2: Create new booking
@app.post("/bookings")
async def create_booking(booking: BookingRequest):
    try:
        data = booking.dict()

        # Collect missing fields using LLM if any required fields are missing
        missing_fields = [
            field for field in ["customer_id", "room_no", "start_date", "end_date", "num_people"] if not data.get(field)
        ]

        if missing_fields:
            prompt = f"Please provide the following booking details: {', '.join(missing_fields)}."
            llm_payload = {
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False
            }
            llm_response = requests.post(OLLAMA_API, json=llm_payload)
            llm_data = llm_response.json()
            llm_output = llm_data.get("response", "")

            return JSONResponse(
                content={
                    "error": "Missing required fields",
                    "missing_fields": missing_fields,
                    "llm_prompt": prompt,
                    "llm_response": llm_output
                },
                status_code=400
            )

        # Default values if not provided
        num_people = data.get("num_people") if data.get("num_people") is not None else 1

        response = supabase.table("booking").insert({
            "customer_id": data["customer_id"],
            "room_no": data["room_no"],
            "start_date": data["start_date"],
            "end_date": data["end_date"],
            "num_people": num_people
        }).execute()

        return JSONResponse(content=response.data, status_code=201)
    except Exception as e:

        raise HTTPException(status_code=500, detail=str(e))


# Run with: uvicorn filename:app --host 0.0.0.0 --port 3000 --reload
# =======
#         return jsonify({"error": str(e)}), 500
    
# @app.route('/chat',methods =['POST'])
# def chat_response():
#     print("try to get response")
#     try:
#         print("try block")
#         data = request.get_json()
#         print("this is a data")
#         user_prompt = data.get("prompt")
#         print(user_prompt)
#         if not user_prompt:
#             return jsonify({"error": "Missing 'prompt'"}), 400
#         result = handle_prompt(user_prompt)
#         return jsonify(result), 200
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500
    
# # ROUTE 3: Query via LLM (Ollama)
# @app.route('/query', methods=['POST'])
# def query_llm():
#     try:
#         user_prompt = request.json.get("prompt")

#         # Send the prompt to Ollama LLM
#         ollama_response = requests.post(OLLAMA_API, json={
#             "model": OLLAMA_MODEL,
#             "prompt": user_prompt
#         })

#         if ollama_response.status_code != 200:
#             return jsonify({"error": "LLM request failed", "details": ollama_response.text}), 500

#         llm_text = ollama_response.json().get("response", "")

#         # Basic intent detection
#         lower_prompt = user_prompt.lower()
#         if "show customers" in lower_prompt or "all customers" in lower_prompt:
#             return get_customers()

#         if "book appointment" in lower_prompt or "booking" in lower_prompt:
#             # Example: parse LLM output later
#             booking_data = {
#                 "customer_id": 1,   # Default demo
#                 "room_no": 1,       # Default demo
#                 "start_date": "2025-09-10",
#                 "end_date": "2025-09-12",
#                 "num_people": 2,
#                 "price": 500
#             }
#             with app.test_request_context(json=booking_data):
#                 return create_booking()

#         # Default: return LLM response
#         return jsonify({"llm_response": llm_text}), 200
# >>>>>>> main


if __name__ == "__main__":
    uvicorn.run("mcp_server:app", host="0.0.0.0", port=3000, reload=True)


# =======
#     app.run(host="0.0.0.0", port=5000)
# >>>>>>> main
