from pydantic import BaseModel, Field
from typing import Optional
from app.schemas.user_schemas import UserResponse

class ProviderBase(BaseModel):
    location: Optional[str] = Field(None, max_length=200)

# 1. Naudojama kuriant teikėjo profilį
class ProviderCreate(ProviderBase):
    user_id: int

# 2. Naudojama atsakymuose (pvz., kai klientas ieško teikėjų sąrašo)
class ProviderResponse(ProviderBase):
    id: int
    user_id: int
    # Ryšio magija: galime įdėti UserResponse schemą! 
    # FastAPI automatiškai ištrauks teikėjo vardą/pavardę iš susijusios users lentelės
    user: UserResponse 

    class Config:
        from_attributes = True