from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from app.schemas.user_schemas import UserBase
from typing import Optional


class ReservationBase(BaseModel):
    provider_id: int
    reservation_time: datetime
    reservation_type: str = Field(min_length=3, max_length=150)
    duration_minutes: int = Field(gt=0, le=480)

    @field_validator("reservation_time")
    @classmethod
    def ensure_date_not_in_past(cls, value: datetime):
        if value < datetime.now():
            raise ValueError("Reservation cannot be done in the past")
        return value


class ReservationCreate(ReservationBase):
    # client_id čia nerašome, nes jį backend'as paims automatiškai iš prisijungusio vartotojo JWT žetono!
    pass


class ReservationResponse(ReservationBase):
    id: int
    client_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ProviderDashboardResponse(BaseModel):
    id: int
    reservation_time: datetime
    reservation_type: str
    duration_minutes: int

    # Štai čia įvyksta magija: vietoj client_id, mes įdedame UserResponse schemą.
    # Kadangi tavo modeliuose yra ryšys `client = relationship("User")`,
    # SQLAlchemy fone pati ištrauks kliento vardą ir el. paštą!
    client: UserBase

    class Config:
        from_attributes = True


class ProviderPublicResponse(BaseModel):
    id: int
    location: str
    # Per ryšį provider.user ištraukiame teikėjo asmeninius duomenis
    user: UserBase

    class Config:
        from_attributes = True


class AdminDashboardResponse(BaseModel):
    id: int
    reservation_time: datetime
    reservation_type: str
    duration_minutes: int

    # Matome ir klientą, ir teikėją!
    client: UserBase
    provider: ProviderPublicResponse

    class Config:
        from_attributes = True


class ReservationUpdate(BaseModel):
    reservation_time: Optional[datetime] = None
    reservation_type: Optional[str] = Field(None, min_length=3, max_length=150)
    duration_minutes: Optional[int] = Field(None, gt=0, le=480)

    class Config:
        from_attributes = True
