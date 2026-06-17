from sqlalchemy.orm import Session
from app.models.models import Reservation
from app.schemas.reservation_schemas import ReservationCreate
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

    @staticmethod
    def get_filtered_reservations(
        db: Session, 
        type_filter: Optional[str] = None, 
        search_query: Optional[str] = None, 
        skip: int = 0, 
        limit: int = 10
    ):
        """
        Gražina rezervacijas su paieška, filtravimu ir puslapiavimu.
        skip = kiek įrašų praleisti (puslapio pradžia)
        limit = kiek daugiausiai įrašų grąžinti (puslapio dydis)
        """
        # Pradedame nuo bazinės užklausos: SELECT * FROM reservations
        query = db.query(Reservation)

        # 1. FILTRAVIMAS: Jei nurodytas tipas, pridedame WHERE taisyklę
        if type_filter:
            query = query.filter(Reservation.reservation_type == type_filter)

        # 2. PAIEŠKA: Jei nurodytas paieškos tekstas, ieškome dalinio sutapimo (LIKE %text%)
        if search_query:
            query = query.filter(Reservation.reservation_type.ilike(f"%{search_query}%"))

        # RŪŠIAVIMAS: Naujausios rezervacijos viršuje
        query = query.order_by(Reservation.reservation_time.asc())

        # 3. PUSLAPIAVIMAS (Pagination)
        results = query.offset(skip).limit(limit).all()
        
        return results
    
    # app/services/reservation_service.py

    @staticmethod
    def get_reservations_advanced(
        db: Session, 
        search_query: Optional[str] = None, 
        skip: int = 0, 
        limit: int = 10, 
        **kwargs
    ):
        # Pradedame nuo bazinio SELECT * FROM reservations
        query = db.query(Reservation)

        # 1. Čia panaudojome tavo norėtą DALINĘ PAIEŠKĄ (LIKE)
        if search_query:
            query = query.filter(Reservation.reservation_type.ilike(f"%{search_query}%"))

        # 2. Čia sukamės per kwargs TIKSLIAM FILTRAVIMUI (client_id, provider_id)
        for key, value in kwargs.items():
            if hasattr(Reservation, key) and value is not None:
                query = query.filter(getattr(Reservation, key) == value)

        # Rūšiuojame ir pritaikome puslapiavimą
        query = query.order_by(Reservation.reservation_time.asc())
        return query.offset(skip).limit(limit).all()