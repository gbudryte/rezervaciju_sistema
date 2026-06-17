# app/routers/reservation_router.py
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.schemas.reservation_schemas import (
    ReservationCreate,
    ReservationResponse,
    ProviderDashboardResponse,
    AdminDashboardResponse,
    ReservationUpdate
)
from app.services.reservation_service import ReservationService
from app.models.models import UserRole, Provider
from app.services.auth_service import AuthService
from app.models.models import User, Reservation


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

@router.get("/my-reservations", response_model=List[ReservationResponse])
def get_my_reservations(
    # Ši eilutė reikalauja JWT žetono ir automatiškai ištraukia prisijungusį vartotoją!
    current_user: User = Depends(AuthService.get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Grąžina rezervacijas, skirtas TIK šiuo metu prisijungusiam vartotojui.
    """
    # Kadangi current_user jau yra ištrauktas iš žetono, mes saugiai žinome jo ID:
    filters = {"client_id": current_user.id}
    
    # Iškviečiame mūsų pažangų filtravimo servisą
    reservations = ReservationService.get_reservations_advanced(
        db, 
        skip=skip, 
        limit=limit, 
        **filters
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

@router.get("/admin/reservations", response_model=List[AdminDashboardResponse])
def get_admin_dashboard(
    current_user: User = Depends(AuthService.get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Grąžina VISAS sistemos rezervacijas. 
    Prieinama TIK vartotojams su ADMIN role.
    """
    # 1. SAUGUMO PATIKRINIMAS: Ar vartotojas yra administratorius?
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Šis puslapis prieinamas tik sistemos administratoriams."
        )

    # 2. Kadangi kwargs dėžutė tuščia, šis metodas tiesiog padarys SELECT * FROM reservations
    reservations = ReservationService.get_reservations_advanced(
        db, 
        skip=skip, 
        limit=limit
        # Čia jokių filtrų (kaip client_id ar provider_id) nededame!
    )
    return reservations

@router.put("/{reservation_id}", response_model=ReservationResponse)
def update_existing_reservation(
    reservation_id: int,
    payload: ReservationUpdate,
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """Rezervacijos redagavimas (su teisių patikra)."""
    db_res = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not db_res:
        raise HTTPException(status_code=404, detail="Rezervacija nerasta.")

    # TEISIŲ PATIKRA (Autorizacija):
    # Leidžiame redaguoti tik jei vartotojas yra Adminas ARBA tai yra paties kliento rezervacija
    if current_user.role != UserRole.ADMIN and db_res.client_id != current_user.id:
        raise HTTPException(status_code=403, detail="Neturite teisės redaguoti šios rezervacijos.")

    updated_res = ReservationService.update_reservation(db, reservation_id, payload)
    return updated_res


@router.delete("/{reservation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_reservation(
    reservation_id: int,
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """Rezervacijos šalinimas (su teisių patikra)."""
    db_res = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not db_res:
        raise HTTPException(status_code=404, detail="Rezervacija nerasta.")

    # TEISIŲ PATIKRA (Autorizacija):
    # Leidžiame trinti Adminui ARBA pačiam klientui
    if current_user.role != UserRole.ADMIN and db_res.client_id != current_user.id:
        raise HTTPException(status_code=403, detail="Neturite teisės ištrinti šios rezervacijos.")

    ReservationService.delete_reservation(db, reservation_id)
    return None # HTTP 204 reikalauja grąžinti tuščią turinį