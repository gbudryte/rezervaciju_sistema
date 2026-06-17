# app/routers/reservation_router.py
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.schemas.reservation_schemas import ReservationCreate, ReservationResponse, ProviderDashboardResponse
from app.services.reservation_service import ReservationService
from app.models.models import UserRole, Provider


router = APIRouter(prefix="/reservations", tags=["Reservations"])


@router.post("", response_model=ReservationResponse)
def create_new_reservation(
    reservation_in: ReservationCreate,
    client_id: int = Query(..., description="Laikinai paduodame rankiniu būdu, kol neturime JWT"),
    db: Session = Depends(get_db),
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
    db: Session = Depends(get_db),
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
        db, search_query=search_query, skip=skip, limit=limit, **filters
    )
    return reservations


@router.get("/provider-reservations", response_model=List[ProviderDashboardResponse])
def get_provider_dashboard(
    current_user: User = Depends(AuthService.get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Grąžina rezervacijas, skirtas TIK prisijungusiam paslaugų teikėjui.
    Papildomai grąžina kliento vardą, pavardę ir el. paštą.
    """
    # 1. SAUGUMO PATIKRINIMAS: Ar vartotojas išvis yra teikėjas?
    if current_user.role != UserRole.PROVIDER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Šis puslapis prieinamas tik paslaugų teikėjams."
        )

    # 2. Surandame teikėjo profilį pagal jo vartotojo ID
    # (nes rezervacijų lentelėje ieškome pagal provider_id, o ne user_id)
    provider_profile = db.query(Provider).filter(Provider.user_id == current_user.id).first()
    if not provider_profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teikėjo profilis nerastas.")

    # 3. Išfiltruojame rezervacijas pagal šio teikėjo ID
    filters = {"provider_id": provider_profile.id}

    reservations = ReservationService.get_reservations_advanced(db, skip=skip, limit=limit, **filters)
    return reservations
