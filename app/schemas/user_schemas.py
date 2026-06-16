# app/schemas/user_schemas.py
from pydantic import BaseModel, EmailStr, Field
from app.models.models import UserRole

class UserBase(BaseModel):
    name: str = Field(min_length=2, max_length=55)
    surname: str = Field(min_length=2, max_length=55)
    email: EmailStr

# Naudojama REGISTRACIJAI (POST /auth/register))
class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=100)

# Naudojama ATSAKYME (Response)
# Klientui JOKIU BŪDU negrąžiname slaptažodžio, bet grąžiname ID ir Rolę
class UserResponse(UserBase):
    id: int
    role: UserRole

    # Ši eilutė privaloma, kad Pydantic mokėtų perskaityti SQLAlchemy objektus
    class Config:
        from_attributes = True