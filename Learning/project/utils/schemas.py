from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    password: str
    
class RefreshTokenRequest(BaseModel):
    refresh_token: str