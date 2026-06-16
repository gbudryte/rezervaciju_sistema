from datetime import datetime
from pydantic import BaseModel, Field, field_validator

class ReservationBase(BaseModel):
    provider_id: int
    reservation_time: datetime
    reservation_type: str = Field(min_length=3, max_length=150)
    duration_minutes: int = Field(gt=0, le=480)
    @field_validator("reservation_time")
    @classmethod
    def ensure_date_not_in_past(cls, value:datetime):
        if value<datetime.now():
            raise ValueError('Reservation cannot be done in the past')
        return value


class ReservationResponse(ReservationBase):
    id: int
    client_id: int
    created_at: datetime

    class Config:
        from_attributes = True