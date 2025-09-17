from psutil import users
from pydantic import BaseModel

class MessageRequest(BaseModel):
    text: str
    role: str = "user"

class MessageResponse(BaseModel):
    text: str
    role: str = "bot"

class BookingRequest(BaseModel):
    customer_id: int | None = None
    room_no: int | None = None
    start_date: str | None = None
    end_date: str | None = None
    num_people: int = 1  # default = 1