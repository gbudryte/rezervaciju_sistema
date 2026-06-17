# app/routers/reservation_router.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.schemas.reservation_schemas import ReservationCreate, ReservationResponse
from app.services.reservation_service import ReservationService

router = APIRouter(prefix="/reservations", tags=["Reservations"])

@router.post("", response_model=ReservationResponse)
def create_new_reservation(
    reservation_in: ReservationCreate, 
    client_id: int = Query(..., description="Laikinai paduodame rankiniu būdu, kol neturime JWT"), 
    db: Session = Depends(get_db)
):
    """Naujos rezervacijos sukūrimas."""
    return ReservationService.create_reservation(db, reservation_data=reservation_in, client_id=client_id)

@router.get("", response_model=List[ReservationResponse])
def get_all_reservations(
    search_query: Optional[str] = Query(None, description="Dalinė paieška pagal paslaugos tipą"),
    client_id: Optional[int] = Query(None, description="Filtruoti pagal konkretų klientą"),
    provider_id: Optional[int] = Query(None, description="Filtruoti pagal konkretų teikėją"),
    skip: int = Query(0, ge=0, description="Kiek įrašų praleisti (Puslapiavimas)"),
    limit: int = Query(10, ge=1, le=100, description="Kiek įrašų grąžinti puslapyje"),
    db: Session = Depends(get_db)
):
    """
    Rezervacijų sąrašas su pažangiu filtravimu, daline paieška ir puslapiavimu.
    """
    # Suorganizuojame papildomus filtrus į kwargs dėžutę, kaip mokėmės!
    filters = {}
    if client_id is not None:
        filters["client_id"] = client_id
    if provider_id is not None:
        filters["provider_id"] = provider_id

    # Iškviečiame mūsų pažangų servisą
    reservations = ReservationService.get_reservations_advanced(
        db, 
        search_query=search_query, 
        skip=skip, 
        limit=limit, 
        **filters
    )
    return reservations