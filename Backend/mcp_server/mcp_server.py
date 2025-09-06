from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from supabase import create_client
import os
import requests
from dotenv import load_dotenv
import uvicorn 
from fastapi import Request
from mcp_clients.llm import handle_prompt
from schemas import BookingRequest
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # or ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Supabase credentials
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("❌ Missing Supabase credentials. Check your .env file.")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Ollama API endpoint
OLLAMA_API = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3"  




# ROUTE 1: Retrieve all customers
@app.get("/customers")
async def get_customers():
    print("get customers api call success")
    try:
        response = supabase.table("customer").select("*").execute()
        print(response)
        if hasattr(response, "data") and response.data is not None:
            print("fetching data in supabase")
            return {
                "action": "get_customers",
                "result": response.data,
                "error": None
            }
        else:
            return {
                "action": "get_customers",
                "result": [],
                "error": "No data found"
            }
    except Exception as e:
        return {
            "action": "get_customers",
            "result": [],
            "error": str(e)
        }


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
            try:
                llm_response = requests.post(OLLAMA_API, json=llm_payload, timeout=30)
                llm_response.raise_for_status()
                llm_data = llm_response.json()
                llm_output = llm_data.get("response", "")
            except Exception as e:
                llm_output = f"Ollama error: {e}"

            return JSONResponse(
                content={
                    "error": "Missing required fields",
                    "missing_fields": missing_fields,
                    "llm_prompt": prompt,
                    "llm_response": llm_output
                },
                status_code=400
            )

        # Insert booking into Supabase
        response = supabase.table("booking").insert({
            "customer_id": data["customer_id"],
            "room_no": data["room_no"],
            "start_date": data["start_date"],
            "end_date": data["end_date"],
            "num_people": data["num_people"]
        }).execute()

        return JSONResponse(content=response.data, status_code=201)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    
@app.post("/chat")
async def chat_response(request: Request):
    try:
        data = await request.json()
        user_prompt = data.get("prompt")
        if not user_prompt:
            return JSONResponse(content={"action": "chat", "error": "Missing 'prompt'"}, status_code=400)

        result = handle_prompt(user_prompt)
        if not result:
            result = {"action": "chat", "error": "No response generated"}

        return JSONResponse(content=result, status_code=200)

    except Exception as e:
        return JSONResponse(content={"action": "chat", "error": str(e)}, status_code=500)

if __name__ == "__main__":
    uvicorn.run("mcp_server.mcp_server:app", host="0.0.0.0", port=3000, reload=True)
