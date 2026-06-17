from sqlalchemy.orm import Session
from app.models.models import Reservation
from app.schemas.reservation_schemas import ReservationCreate, ReservationUpdate
from typing import Optional

class ReservationService:

    @staticmethod
    def create_reservation(db: Session, reservation_data: ReservationCreate, client_id: int) -> Reservation:
        """Sukuria naują rezervaciją konkrečiam klientui."""
        
        # Ar tas laikas jau nėra užimtas? (Time conflict validation)

        db_reservation = Reservation(
            client_id=client_id,
            provider_id=reservation_data.provider_id,
            reservation_time=reservation_data.reservation_time,
            reservation_type=reservation_data.reservation_type,
            duration_minutes=reservation_data.duration_minutes
        )
        
        db.add(db_reservation)
        db.commit()
        db.refresh(db_reservation)
        return db_reservation


    def get_reservations_advanced(
        db: Session, 
        search_query: Optional[str] = None, 
        skip: int = 0, 
        limit: int = 10, 
        sort_order: str = "asc",  # <-- Naujas parametras ("asc" arba "desc")
        **kwargs
    ):
        query = db.query(Reservation)

        if search_query:
            query = query.filter(Reservation.reservation_type.ilike(f"%{search_query}%"))

        for key, value in kwargs.items():
            if hasattr(Reservation, key) and value is not None:
                query = query.filter(getattr(Reservation, key) == value)

        # DINAMINIS RŪŠIAVIMAS:
        if sort_order.lower() == "desc":
            query = query.order_by(Reservation.reservation_time.desc())
        else:
            query = query.order_by(Reservation.reservation_time.asc())

        return query.offset(skip).limit(limit).all()

    @staticmethod
    def update_reservation(db: Session, reservation_id: int, update_data: ReservationUpdate) -> Optional[Reservation]:
        """Atnaujina rezervacijos duomenis DB."""
        db_reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
        if not db_reservation:
            return None

        # Paverčiame pydantic modelį į žodyną, ignoruodami neatsiųstus (None) laukus
        update_dict = update_data.model_dump(exclude_unset=True)
        
        for key, value in update_dict.items():
            setattr(db_reservation, key, value)

        db.commit()
        db.refresh(db_reservation)
        return db_reservation

    @staticmethod
    def delete_reservation(db: Session, reservation_id: int) -> bool:
        """Ištrina rezervaciją iš DB."""
        db_reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
        if not db_reservation:
            return False
        
        db.delete(db_reservation)
        db.commit()
        return True