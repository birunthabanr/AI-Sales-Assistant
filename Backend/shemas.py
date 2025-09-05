from psutil import users
from pydantic import BaseModel

class MessageRequest(BaseModel):
    text: str
    role: str = "user"

class MessageResponse(BaseModel):
    text: str
    role: str = "bot"