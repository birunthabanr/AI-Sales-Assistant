from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from supabase import create_client
import os
import requests
from dotenv import load_dotenv
import uvicorn

# Load environment variables
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


if __name__ == "__main__":
    uvicorn.run("mcp_server:app", host="0.0.0.0", port=3000, reload=True)


