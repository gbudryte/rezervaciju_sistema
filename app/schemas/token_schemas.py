from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str  # Visada bus "bearer"

class TokenData(BaseModel):
    # Ši schema skirta iškoduotų duomenų saugojimui sistemos viduje
    user_id: int
    role: str